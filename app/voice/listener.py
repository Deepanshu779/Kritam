import speech_recognition as sr


class VoiceListener:

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.9
        self.recognizer.phrase_threshold = 0.05
        self.recognizer.non_speaking_duration = 0.4
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.10
        self.recognizer.dynamic_energy_ratio = 1.15
        self.microphone = sr.Microphone()
        self._calibrated = False

    def _prepare(self):
        if self._calibrated:
            return
        try:
            with self.microphone as source:
                print("Calibrating microphone...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print(f"Kritam: microphone energy threshold = {self.recognizer.energy_threshold:.0f}")
            self._calibrated = True
        except Exception as error:
            print(f"Microphone calibration error: {error}")

    def listen(self, timeout=1, phrase_time_limit=30):
        try:
            self._prepare()
            with self.microphone as source:
                return self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
        except sr.WaitTimeoutError:
            return None
        except Exception as error:
            print(f"Microphone listen error: {error}")
            return None

    def listen_until_stopped(self, stop_event):
        """Capture one natural speech turn with a speech-sensitive threshold."""
        try:
            self._prepare()
            with self.microphone as source:
                print("Kritam: foreground recording started.")
                while not stop_event.is_set():
                    try:
                        audio = self.recognizer.listen(
                            source,
                            timeout=0.5,
                            phrase_time_limit=20,
                        )
                        if stop_event.is_set():
                            return None

                        print("Kritam: foreground recording stopped.")
                        return audio
                    except sr.WaitTimeoutError:
                        continue

                return None

        except Exception as exc:
            print(f"Kritam: foreground recording error: {exc}")
            return None
