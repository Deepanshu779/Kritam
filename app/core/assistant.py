from voice.listener import VoiceListener
from voice.speech_to_text import SpeechToText
from voice.text_to_speech import TextToSpeech

from brain.intent_engine import IntentEngine
from intelligence.fast_router import FastRouter

from core.validator import ActionValidator

from actions.applications import ApplicationManager
from actions.registry import ActionRegistry


class Kritam:

    def __init__(self):
        self.name = "Kritam"

        self.listener = VoiceListener()
        self.speech_to_text = SpeechToText()
        self.text_to_speech = TextToSpeech()

        self.fast_router = FastRouter()
        self.intent_engine = IntentEngine()

        self.validator = ActionValidator()

        self.application_manager = ApplicationManager()

        self.action_registry = ActionRegistry()
        self._register_actions()

    def _register_actions(self):
        self.action_registry.register(
            "open_application",
            self.application_manager.handle_open_application,
        )

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

            if command in {"exit", "quit", "stop"}:

                self.text_to_speech.speak(
                    "Okay. See you later."
                )

                break

            intent = self.fast_router.route(text)

            if intent is not None:

                print(f"Kritam Fast Intent: {intent}")

            else:

                print("Kritam: Using AI...")

                intent = self.intent_engine.understand(text)

                print(f"Kritam AI Intent: {intent}")

            if not self.validator.validate(intent):

                self.text_to_speech.speak(
                    "I can't perform that action yet."
                )

                continue

            if intent["type"] == "conversation":

                response = intent.get(
                    "response",
                    "How can I help?"
                )

                self.text_to_speech.speak(response)

                continue

            if intent["type"] == "open_application":

                application = intent["application"]

                self.text_to_speech.speak(
                    f"Opening {application}."
                )

            success = self.action_registry.execute(intent)

            if not success:

                self.text_to_speech.speak(
                    "I couldn't complete that action."
                )
