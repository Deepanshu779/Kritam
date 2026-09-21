from voice.listener import VoiceListener
from voice.speech_to_text import SpeechToText
from voice.text_to_speech import TextToSpeech

from brain.intent_engine import IntentEngine
from intelligence.fast_router import FastRouter

from core.context import ConversationContext
from core.validator import ActionValidator

from actions.applications import ApplicationManager
from actions.browser import BrowserManager
from actions.files import FileManager
from actions.system import SystemManager
from actions.registry import ActionRegistry


class Kritam:

    def __init__(self):
        self.name = "Kritam"

        self.listener = VoiceListener()
        self.speech_to_text = SpeechToText()
        self.text_to_speech = TextToSpeech()

        self.fast_router = FastRouter()
        self.intent_engine = IntentEngine()
        self.context = ConversationContext()
        self.validator = ActionValidator()

        self.application_manager = ApplicationManager()
        self.browser_manager = BrowserManager()
        self.file_manager = FileManager()
        self.system_manager = SystemManager()

        self.action_registry = ActionRegistry()
        self._register_actions()

    def _register_actions(self):
        self.action_registry.register("open_application", self.application_manager.handle_open_application)
        self.action_registry.register("open_website", self.browser_manager.handle_open_website)
        self.action_registry.register("search_web", self.browser_manager.handle_search_web)
        self.action_registry.register("open_folder", self.file_manager.handle_open_folder)
        self.action_registry.register("take_screenshot", self.system_manager.handle_screenshot)
        self.action_registry.register("volume_up", self.system_manager.handle_volume_up)
        self.action_registry.register("volume_down", self.system_manager.handle_volume_down)
        self.action_registry.register("volume_mute", self.system_manager.handle_volume_mute)
        self.action_registry.register("media_play_pause", self.system_manager.handle_media_play_pause)
        self.action_registry.register("minimize_window", self.system_manager.handle_minimize_window)
        self.action_registry.register("maximize_window", self.system_manager.handle_maximize_window)

    def start(self):
        print(f"{self.name} is starting...")
        self.text_to_speech.speak("Hello. Kritam is ready.")

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
                self.text_to_speech.speak("Okay. See you later.")
                break

            intent = self.fast_router.route(text)

            if intent is not None:
                print(f"Kritam Fast Intent: {intent}")
            else:
                print("Kritam: Using AI...")
                intent = self.intent_engine.understand(text, context=self.context)
                print(f"Kritam AI Intent: {intent}")

            if intent.get("type") == "repeat_last_action":
                intent = self.context.repeat_last()

                if intent is None:
                    self.text_to_speech.speak(
                        "There is no previous successful action to repeat."
                    )
                    continue

                print(f"Kritam Repeat Intent: {intent}")

            if not self.validator.validate(intent):
                self.text_to_speech.speak("I can't perform that action yet.")
                self.context.add_turn(text, intent, False)
                continue

            if intent["type"] == "conversation":
                self.text_to_speech.speak(
                    intent.get("response", "How can I help?")
                )
                self.context.add_turn(text, intent, True)
                continue

            success = self.action_registry.execute(intent)
            self.context.add_turn(text, intent, success)

            if success:
                action_type = intent["type"]

                if action_type == "open_application":
                    self.text_to_speech.speak(f"Opening {intent['application']}.")
                elif action_type == "open_website":
                    self.text_to_speech.speak(f"Opening {intent['website']}.")
                elif action_type == "search_web":
                    self.text_to_speech.speak("Searching the web.")
                elif action_type == "open_folder":
                    self.text_to_speech.speak(f"Opening {intent['folder']}.")
                elif action_type == "take_screenshot":
                    self.text_to_speech.speak("Screenshot saved.")
                elif action_type == "volume_up":
                    self.text_to_speech.speak("Volume increased.")
                elif action_type == "volume_down":
                    self.text_to_speech.speak("Volume decreased.")
                elif action_type == "volume_mute":
                    self.text_to_speech.speak("Volume muted.")
                elif action_type == "media_play_pause":
                    self.text_to_speech.speak("Playback toggled.")
                elif action_type == "minimize_window":
                    self.text_to_speech.speak("Window minimized.")
                elif action_type == "maximize_window":
                    self.text_to_speech.speak("Window maximized.")
            else:
                self.text_to_speech.speak("I couldn't complete that action.")
