import speech_recognition as sr


class VoiceListener:

    def __init__(self):
        self.recognizer = sr.Recognizer()

        # Don't stop listening too quickly
        self.recognizer.pause_threshold = 2.0

        # Minimum speech before considering it a phrase
        self.recognizer.phrase_threshold = 0.2

        # Keep a little silence around speech
        self.recognizer.non_speaking_duration = 0.8

        self.microphone = sr.Microphone()

    def listen(self):

        with self.microphone as source:

            print("Listening...")

            # Calibrate microphone
            self.recognizer.adjust_for_ambient_noise(
                source,
                duration=0.3
            )

            try:
                audio = self.recognizer.listen(
                    source,
                    timeout=5,
                    phrase_time_limit=10
                )

                return audio

            except sr.WaitTimeoutError:
                return None