import re
import speech_recognition as sr


class SpeechToText:

    def __init__(self):
        self.recognizer = sr.Recognizer()

    def _remove_repeated_phrase(self, text):
        words = text.lower().split()

        if len(words) >= 4 and len(words) % 2 == 0:
            half = len(words) // 2

            if words[:half] == words[half:]:
                return " ".join(words[:half])

        return text

    def convert(self, audio):
        try:
            text = self.recognizer.recognize_google(
                audio,
                language="en-IN"
            )

            text = re.sub(r"\s+", " ", text).strip()
            return self._remove_repeated_phrase(text)

        except sr.UnknownValueError:
            return ""

        except sr.RequestError:
            return ""
