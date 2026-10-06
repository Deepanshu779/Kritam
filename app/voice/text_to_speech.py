"""Text to Speech module for Kritam assistant.

Features:
- Asynchronous, non-blocking audio output
- Self-triggering / echo suppression: provides `is_speaking` state and settling period
- Barge-in / interruption support via `stop()`
- Thread-safe voice output
"""

import queue
import threading
import time
from typing import Optional
import pyttsx3


class TextToSpeech:
    """Asynchronous TTS engine with echo suppression and barge-in capability."""

    def __init__(self, settling_period_s: float = 0.5):
        self.settling_period_s = settling_period_s
        self.is_speaking = False
        self.last_spoke_time = 0.0
        self._lock = threading.Lock()
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self.on_start = None
        self.on_end = None

        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 160)
            self.engine.setProperty("volume", 1.0)
            self._select_female_voice()
        except Exception as error:
            print(f"[Kritam Voice] TTS init error: {error}")
            self.engine = None

        # Background playback thread
        self._worker_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self._worker_thread.start()

    def _select_female_voice(self):
        if not self.engine:
            return
        try:
            voices = self.engine.getProperty("voices") or []
            for voice in voices:
                voice_name = getattr(voice, "name", "").lower()
                if "female" in voice_name or "zira" in voice_name or "david" in voice_name:
                    self.engine.setProperty("voice", voice.id)
                    break
        except Exception:
            pass

    def is_active_or_settling(self) -> bool:
        """Returns True if TTS is currently speaking or in the post-speech echo settling window."""
        with self._lock:
            if self.is_speaking:
                return True
            elapsed = time.time() - self.last_spoke_time
            return elapsed < self.settling_period_s

    def stop(self):
        """Interrupt and stop speech immediately (barge-in support)."""
        self._stop_event.set()
        # Clear any pending queued speech
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break

        if self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass

        with self._lock:
            self.is_speaking = False
            self.last_spoke_time = time.time()

    def speak(self, text: str, block: bool = True):
        """Speak the text. By default blocks until finished to sequence turns naturally."""
        if not text or not text.strip():
            return

        text = text.strip()
        print(f"Kritam: {text}")

        if not self.engine:
            return

        done_event = threading.Event() if block else None
        self._queue.put((text, done_event))

        if block and done_event:
            done_event.wait(timeout=25.0)

    def _tts_worker(self):
        """Worker loop executing speech tasks sequentially."""
        while True:
            try:
                item = self._queue.get()
                if item is None:
                    break

                text, done_event = item
                self._stop_event.clear()

                with self._lock:
                    self.is_speaking = True

                print("[Kritam Voice] TTS started")
                if callable(self.on_start):
                    try:
                        self.on_start(text)
                    except Exception:
                        pass
                try:
                    if self.engine:
                        self.engine.say(text)
                        self.engine.runAndWait()
                except Exception as error:
                    print(f"[Kritam Voice] TTS error: {error}")
                finally:
                    with self._lock:
                        self.is_speaking = False
                        self.last_spoke_time = time.time()
                    print("[Kritam Voice] TTS finished")
                    if callable(self.on_end):
                        try:
                            self.on_end()
                        except Exception:
                            pass
                    if done_event:
                        done_event.set()
                    self._queue.task_done()

            except Exception as e:
                with self._lock:
                    self.is_speaking = False
                    self.last_spoke_time = time.time()
                time.sleep(0.05)