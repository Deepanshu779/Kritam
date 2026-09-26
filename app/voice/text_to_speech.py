import pyttsx3


class TextToSpeech:
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 160)
            self.engine.setProperty("volume", 1.0)
            self._select_female_voice()
        except Exception as error:
            print(f"TTS init error: {error}")
            self.engine = None

    def _select_female_voice(self):
        if not self.engine:
            return
        try:
            voices = self.engine.getProperty("voices") or []
            for voice in voices:
                voice_name = getattr(voice, "name", "").lower()
                if "female" in voice_name or "zira" in voice_name:
                    self.engine.setProperty("voice", voice.id)
                    break
        except Exception:
            pass

    def speak(self, text):
        if not text:
            return
        print(f"Kritam: {text}")
        if not self.engine:
            return
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as error:
            print(f"TTS error: {error}")