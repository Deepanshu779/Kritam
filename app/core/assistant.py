from voice.listener import VoiceListener
from voice.speech_to_text import SpeechToText
from voice.text_to_speech import TextToSpeech

from brain.intent_engine import IntentEngine
from intelligence.fast_router import FastRouter
from core.validator import ActionValidator

from actions.applications import ApplicationManager


class Kritam:

    def __init__(self):
        self.name = "Kritam"

        self.listener = VoiceListener()
        self.speech_to_text = SpeechToText()

        self.text_to_speech = TextToSpeech()

        # Fast local routing for simple commands.
        self.fast_router = FastRouter()

        # AI is used only when the fast router cannot handle a request.
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

            command = text.lower().strip()

            # Exit without using AI.
            if command in {"exit", "quit", "stop"}:

                self.text_to_speech.speak(
                    "Okay. See you later."
                )

                break

            # ==================================================
            # FAST PATH
            # ==================================================
            # Simple known commands never go through Ollama.
            intent = self.fast_router.route(text)

            if intent is not None:

                print(f"Kritam Fast Intent: {intent}")

            # ==================================================
            # AI PATH
            # ==================================================
            else:

                print("Kritam: Using AI...")

                intent = self.intent_engine.understand(text)

                print(f"Kritam AI Intent: {intent}")

            # ==================================================
            # VALIDATION
            # ==================================================

            if not self.validator.validate(intent):

                self.text_to_speech.speak(
                    "I can't perform that action yet."
                )

                continue

            # ==================================================
            # CONVERSATION
            # ==================================================

            if intent["type"] == "conversation":

                response = intent.get(
                    "response",
                    "How can I help?"
                )

                self.text_to_speech.speak(response)

            # ==================================================
            # APPLICATION
            # ==================================================

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
