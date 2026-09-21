from voice.listener import VoiceListener
from voice.speech_to_text import SpeechToText
from voice.text_to_speech import TextToSpeech

from brain.intent_engine import IntentEngine
from core.validator import ActionValidator

from actions.applications import ApplicationManager


class Kritam:

    def __init__(self):
        self.name = "Kritam"

        self.listener = VoiceListener()
        self.speech_to_text = SpeechToText()
        self.text_to_speech = TextToSpeech()

        self.intent_engine = IntentEngine()
        self.validator = ActionValidator()

        self.application_manager = ApplicationManager()

    def start(self):

        print(f"{self.name} is starting...")

        self.text_to_speech.speak(
            "Hello. Kritam is ready."
        )

        while True:

            audio = self.listener.listen()

            if audio is None:
                continue

            text = self.speech_to_text.convert(audio)

            if not text:
                continue

            print(f"You: {text}")

            intent = self.intent_engine.understand(text)

            print(f"Kritam Intent: {intent}")

            # Exit
            if text.lower().strip() in ["exit", "quit", "stop"]:

                self.text_to_speech.speak(
                    "Okay. See you later."
                )

                break

            # Validate
            if not self.validator.validate(intent):

                self.text_to_speech.speak(
                    "I can't perform that action yet."
                )

                continue

            # Conversation
            if intent["type"] == "conversation":

                response = intent.get(
                    "response",
                    "How can I help?"
                )

                self.text_to_speech.speak(response)

            # Open application
            elif intent["type"] == "open_application":

                application = intent["application"]

                self.text_to_speech.speak(
                    f"Opening {application}."
                )

                success = self.application_manager.open_application(
                    application
                )

                if not success:

                    self.text_to_speech.speak(
                        "I couldn't open that application."
                    )