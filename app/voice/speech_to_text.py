import speech_recognition as sr


class SpeechToText:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def convert(self, audio):
        try:
            text = self.recognizer.recognize_google(audio)
            return text

        except sr.UnknownValueError:
            return ""

        except sr.RequestError:
            return ""