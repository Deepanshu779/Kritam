import speech_recognition as sr


class VoiceListener:

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.1
        self.recognizer.phrase_threshold = 0.1
        self.recognizer.non_speaking_duration = 0.5
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.35
        self.microphone = sr.Microphone()
        self._calibrated = False

    def _prepare(self):
        if self._calibrated:
            return
        try:
            with self.microphone as source:
                print("Calibrating microphone...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
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
        """Capture one natural speech turn for the foreground mic button.

        The button is push-to-start rather than push-to-talk: once speech is
        detected, normal pauses end the turn automatically. This avoids the
        old raw-stream loop that could feel stuck or require a second click.
        """
        try:
            self._prepare()
            with self.microphone as source:
                print("Kritam: foreground recording started.")
                audio = self.recognizer.listen(
                    source,
                    timeout=8,
                    phrase_time_limit=20,
                )
                if stop_event.is_set():
                    return None
                print("Kritam: foreground recording stopped.")
                return audio
        except sr.WaitTimeoutError:
            print("Kritam: no speech detected.")
            return None
        except Exception as exc:
            print(f"Kritam: foreground recording error: {exc}")
            return None
