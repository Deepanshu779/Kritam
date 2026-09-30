"""Background wake-word listener for Kritam assistant.

Features:
- Minimal CPU idle state: audio is filtered by VAD before Whisper is ever invoked
- Prevents ambient noise, fan hum, or keyboard clicks from calling Whisper
- Supports both unified ("Hey Kritam, open Chrome") and split ("Hey Kritam" -> pause -> "Open Chrome") commands
- Echo / TTS self-triggering suppression
- Uses modular WakeWordDetector
"""

import time
import threading
from typing import Optional, Callable
import numpy as np
import pyaudio

from voice.vad import SpeechActivityDetector
from voice.wake_word import WakeWordDetector
from voice.audio_processor import AudioProcessor


class BackgroundVoiceListener:
    """Low-power background listener with wake-word detection."""

    SAMPLE_RATE = 16000
    CHANNELS = 1
    FRAME_MS = 30
    CHUNK_SIZE = int(SAMPLE_RATE * (FRAME_MS / 1000.0))  # 480 samples

    def __init__(self, speech_to_text, tts=None, assistant_name: str = "Kritam", on_wake: Optional[Callable] = None):
        self.speech_to_text = speech_to_text
        self.tts = tts
        self.on_wake = on_wake
        self.wake_detector = WakeWordDetector(assistant_name=assistant_name)
        self.audio_processor = AudioProcessor()
        self.vad = SpeechActivityDetector(
            sample_rate=self.SAMPLE_RATE,
            frame_duration_ms=self.FRAME_MS,
            onset_consecutive_frames=3,
            hangover_duration_s=0.75,
            min_speech_duration_s=0.35,
            pre_roll_duration_s=0.30,
        )
        self.stop_event = threading.Event()
        self.armed = False
        self.armed_time = 0.0
        self.pyaudio_instance: Optional[pyaudio.PyAudio] = None
        self._lock = threading.Lock()

    def set_assistant_name(self, name: str):
        self.wake_detector.set_assistant_name(name)

    def set_tts(self, tts):
        self.tts = tts

    def is_tts_speaking(self) -> bool:
        if self.tts and hasattr(self.tts, "is_active_or_settling"):
            return self.tts.is_active_or_settling()
        return False

    def stop(self):
        """Signal background listener to terminate."""
        self.stop_event.set()

    def listen_for_command(self) -> str:
        """Listen in background with low CPU consumption until a valid wake command is captured."""
        with self._lock:
            if self.pyaudio_instance is None:
                self.pyaudio_instance = pyaudio.PyAudio()
                print("[Kritam Voice] background listener initialized")

            stream = None
            try:
                stream = self.pyaudio_instance.open(
                    format=pyaudio.paInt16,
                    channels=self.CHANNELS,
                    rate=self.SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=self.CHUNK_SIZE,
                )
            except Exception as exc:
                print(f"[Kritam Voice] Background microphone stream error: {exc}")
                time.sleep(1.0)
                return ""

            try:
                self.vad.reset()

                while not self.stop_event.is_set():
                    # If armed state has timed out (e.g. user said 'Hey Kritam' and walked away for > 10s)
                    if self.armed and (time.time() - self.armed_time > 10.0):
                        print("[Kritam Voice] Armed wake state timed out.")
                        self.armed = False

                    # Check TTS echo suppression
                    if self.is_tts_speaking():
                        try:
                            stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                        except Exception:
                            pass
                        self.vad.reset()
                        time.sleep(0.03)
                        continue

                    # Capture frame
                    try:
                        raw_bytes = stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                    except Exception:
                        time.sleep(0.01)
                        continue

                    if not raw_bytes or len(raw_bytes) != self.CHUNK_SIZE * 2:
                        continue

                    frame = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

                    # Process frame through VAD: CPU remains very low during ambient silence
                    utterance = self.vad.process_frame(frame)

                    if utterance is None:
                        continue

                    # A complete speech turn was detected!
                    if self.is_tts_speaking():
                        continue

                    text, meta = self.speech_to_text.convert_with_metadata(utterance)
                    if not text:
                        continue

                    print(f"[Kritam Voice] background heard: \"{text}\"")

                    # Check for wake word
                    wake_res = self.wake_detector.detect(text)

                    if wake_res.detected:
                        print("[Kritam Voice] wake word detected")
                        if self.on_wake:
                            try:
                                self.on_wake()
                            except Exception:
                                pass

                        if wake_res.command_remainder:
                            # Immediate wake + command: "Hey Kritam, open Chrome"
                            self.armed = False
                            return wake_res.command_remainder
                        else:
                            # Wake word alone: "Hey Kritam." [pause]
                            self.armed = True
                            self.armed_time = time.time()
                            continue

                    # If already armed from a previous turn, any valid spoken utterance is the command!
                    if self.armed:
                        self.armed = False
                        return text

                    # Speech didn't contain wake word and wasn't armed; discard quietly
                    continue

                return ""

            finally:
                if stream:
                    try:
                        stream.stop_stream()
                        stream.close()
                    except Exception:
                        pass