import pyttsx3


class TextToSpeech:
    def __init__(self):
        self.engine = pyttsx3.init()

        self.engine.setProperty("rate", 160)
        self.engine.setProperty("volume", 1.0)

        self._select_female_voice()

    def _select_female_voice(self):
        voices = self.engine.getProperty("voices")

        for voice in voices:
            voice_name = voice.name.lower()

            if "female" in voice_name or "zira" in voice_name:
                self.engine.setProperty("voice", voice.id)
                break

    def speak(self, text):
        print(f"Kritam: {text}")

        self.engine.say(text)
        self.engine.runAndWait()