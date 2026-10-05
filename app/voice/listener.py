"""Voice listener module for Kritam assistant.

Implements natural conversational speech capture with:
- Frame-level SpeechActivityDetector
- Pre-roll ring buffering for natural speech onsets
- Trailing pause (hangover) detection for natural conversational pauses
- TTS self-triggering / echo suppression
- Clean PyAudio streaming lifecycle
"""

import time
import threading
from typing import Optional
import numpy as np
import speech_recognition as sr
try:
    import pyaudio
except Exception:
    pyaudio = None

from voice.vad import SpeechActivityDetector
from voice.audio_processor import AudioProcessor
from voice.mic_guard import microphone_session


class VoiceListener:
    """Captures natural speech turns using real-time VAD streaming."""

    SAMPLE_RATE = 16000
    CHANNELS = 1
    FRAME_MS = 30
    CHUNK_SIZE = int(SAMPLE_RATE * (FRAME_MS / 1000.0))  # 480 samples = 30ms

    def __init__(self, tts=None):
        self.tts = tts
        self.audio_processor = AudioProcessor()
        self.vad = SpeechActivityDetector(
            sample_rate=self.SAMPLE_RATE,
            frame_duration_ms=self.FRAME_MS,
            onset_consecutive_frames=3,
            hangover_duration_s=1.0,
            min_speech_duration_s=0.5,
            max_utterance_duration_s=22.0,
            pre_roll_duration_s=0.45,
        )
        self.pyaudio_instance: Optional["pyaudio.PyAudio"] = None
        self._lock = threading.Lock()
        self._initialized = False

    def _ensure_pyaudio(self):
        if pyaudio is None:
            raise RuntimeError("PyAudio unavailable")
        if self.pyaudio_instance is None:
            self.pyaudio_instance = pyaudio.PyAudio()
            print(f"[Kritam Voice] microphone initialized sr={self.SAMPLE_RATE}Hz mono chunk={self.CHUNK_SIZE}")
            self._initialized = True

    def set_tts(self, tts):
        """Set or update TextToSpeech instance for echo suppression."""
        self.tts = tts

    def is_tts_speaking(self) -> bool:
        """Check if assistant TTS is active or in echo settling period."""
        if self.tts and hasattr(self.tts, "is_active_or_settling"):
            return self.tts.is_active_or_settling()
        return False

    def listen(self, timeout: float = 8.0, phrase_time_limit: float = 20.0) -> Optional[np.ndarray]:
        """Capture one speech turn within the given timeout window."""
        stop_event = threading.Event()
        return self._capture_stream(timeout=timeout, phrase_time_limit=phrase_time_limit, stop_event=stop_event)

    def listen_until_stopped(self, stop_event: threading.Event) -> Optional[np.ndarray]:
        """Capture one natural speech turn until speech ends or stop_event is triggered."""
        return self._capture_stream(timeout=None, phrase_time_limit=25.0, stop_event=stop_event)

    def _capture_stream(
        self,
        timeout: Optional[float],
        phrase_time_limit: float,
        stop_event: threading.Event,
    ) -> Optional[np.ndarray]:
        """Stream frames from PyAudio through SpeechActivityDetector."""
        with self._lock:
            with microphone_session() as acquired:
                if not acquired:
                    print("[Kritam Voice] microphone busy; capture skipped")
                    return None

                try:
                    self._ensure_pyaudio()
                except Exception as exc:
                    print(f"[Kritam Voice] PyAudio init failed: {exc}")
                    return self._fallback_listen(timeout, phrase_time_limit, stop_event)

                self.vad.reset()

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
                    print(f"[Kritam Voice] Failed to open microphone stream: {exc}")
                    return self._fallback_listen(timeout, phrase_time_limit, stop_event)

                start_time = time.time()
                speech_started_logged = False
                speech_start_time = None

                try:
                    while not stop_event.is_set():
                        # Check overall timeout before speech begins
                        if not self.vad.speech_active and timeout is not None:
                            if time.time() - start_time > timeout:
                                return None

                        # Prevent listening to assistant's own TTS output
                        if self.is_tts_speaking():
                            # Discard frames while TTS speaks or settles
                            try:
                                stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                            except Exception:
                                pass
                            self.vad.reset()
                            speech_started_logged = False
                            speech_start_time = None
                            time.sleep(0.02)
                            continue

                        # Read frame from mic
                        try:
                            raw_bytes = stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                        except Exception:
                            time.sleep(0.01)
                            continue

                        if not raw_bytes or len(raw_bytes) != self.CHUNK_SIZE * 2:
                            continue

                        frame = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                        utterance = self.vad.process_frame(frame)

                        if self.vad.speech_active and not speech_started_logged:
                            speech_started_logged = True
                            speech_start_time = time.time()
                            print(
                                f"[Kritam Voice] speech started (noise_floor={self.vad.noise_floor:.4f}, "
                                f"onset_frames={self.vad.onset_consecutive_frames}, "
                                f"hangover_frames={self.vad.hangover_frames})"
                            )

                        if self.vad.speech_active and speech_start_time is not None:
                            if (time.time() - speech_start_time) >= phrase_time_limit:
                                utterance = self.vad.force_finalize()
                                if utterance is None:
                                    speech_started_logged = False
                                    speech_start_time = None
                                    continue

                        if utterance is not None:
                            metrics = self.audio_processor.calculate_metrics(utterance)
                            print(
                                f"[Kritam Voice] speech ended duration={metrics.duration_s:.2f}s "
                                f"rms={metrics.rms:.4f} peak={metrics.peak:.4f}"
                            )
                            if metrics.is_silence:
                                print("[Kritam Voice] rejected capture (silence/too short)")
                                speech_started_logged = False
                                speech_start_time = None
                                continue
                            return self.audio_processor.safe_normalize(utterance)

                    return None

                finally:
                    if stream:
                        try:
                            stream.stop_stream()
                            stream.close()
                        except Exception:
                            pass

    def _fallback_listen(
        self,
        timeout: Optional[float],
        phrase_time_limit: float,
        stop_event: threading.Event,
    ) -> Optional[np.ndarray]:
        """Fallback capture using speech_recognition if PyAudio direct stream fails."""
        try:
            recognizer = sr.Recognizer()
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 0.8
            with sr.Microphone() as source:
                while not stop_event.is_set():
                    if self.is_tts_speaking():
                        time.sleep(0.05)
                        continue
                    try:
                        audio = recognizer.listen(
                            source,
                            timeout=timeout or 5,
                            phrase_time_limit=phrase_time_limit,
                        )
                        return self.audio_processor.to_mono_16k_pcm(audio)
                    except sr.WaitTimeoutError:
                        return None
        except Exception as error:
            print(f"[Kritam Voice] Fallback listener error: {error}")
            return None

    def close(self):
        """Release audio resources."""
        with self._lock:
            if self.pyaudio_instance:
                try:
                    self.pyaudio_instance.terminate()
                except Exception:
                    pass
                self.pyaudio_instance = None
                self._initialized = False
