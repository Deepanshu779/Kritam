import speech_recognition as sr


class VoiceListener:

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.65
        self.recognizer.phrase_threshold = 0.15
        self.recognizer.non_speaking_duration = 0.35
        self.recognizer.dynamic_energy_threshold = True
        self.microphone = sr.Microphone()
        self._calibrated = False

    def _prepare(self):
        if self._calibrated:
            return
        with self.microphone as source:
            print("Calibrating microphone...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
        self._calibrated = True

    def listen(self, timeout=1, phrase_time_limit=6):
        self._prepare()
        with self.microphone as source:
            try:
                return self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
            except sr.WaitTimeoutError:
                return None
