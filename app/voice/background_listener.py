import re
import threading
import speech_recognition as sr


class BackgroundVoiceListener:

    WAKE_PATTERN = re.compile(r"\b(?:hey|hi|okay|ok)\s+kritam\b", re.IGNORECASE)

    def __init__(self, speech_to_text):
        self.speech_to_text = speech_to_text
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.55
        self.recognizer.phrase_threshold = 0.12
        self.recognizer.non_speaking_duration = 0.3
        self.recognizer.dynamic_energy_threshold = True
        self.microphone = sr.Microphone()
        self.stop_event = threading.Event()
        self.armed = False
        self._calibrated = False

    def _prepare(self):
        if self._calibrated:
            return
        with self.microphone as source:
            print("Kritam background listener: calibrating...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
        self._calibrated = True

    def stop(self):
        self.stop_event.set()

    def _listen_phrase(self):
        with self.microphone as source:
            try:
                return self.recognizer.listen(
                    source,
                    timeout=1,
                    phrase_time_limit=5,
                )
            except sr.WaitTimeoutError:
                return None

    def listen_for_command(self):
        self._prepare()

        while not self.stop_event.is_set():
            audio = self._listen_phrase()
            if audio is None:
                continue

            text = self.speech_to_text.convert(audio)
            if not text:
                continue

            match = self.WAKE_PATTERN.search(text)
            if match:
                remainder = text[match.end():].strip(" ,.!?")
                self.armed = True
                print(f"Wake word detected: {text}")
                if remainder:
                    self.armed = False
                    return remainder
                continue

            if self.armed:
                self.armed = False
                return text

        return ""
