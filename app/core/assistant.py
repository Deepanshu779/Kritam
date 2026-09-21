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
        self.action_registry.register("browser_search", self.browser_manager.handle_browser_search)
        self.action_registry.register("browser_open_result", self.browser_manager.handle_open_result)
        self.action_registry.register("browser_back", self.browser_manager.handle_go_back)
        self.action_registry.register("browser_open_result_by_text", self.browser_manager.handle_open_result_by_text)
        self.action_registry.register("browser_new_tab", self.browser_manager.handle_new_tab)
        self.action_registry.register("browser_close_tab", self.browser_manager.handle_close_tab)
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

            intent = self.fast_router.route(text, context=self.context)
            if intent is None:
                print("Kritam: Using AI...")
                intent = self.intent_engine.understand(text, context=self.context)
            print(f"Kritam Intent: {intent}")

            if intent.get("type") == "repeat_last_action":
                intent = self.context.repeat_last()
                if intent is None:
                    self.text_to_speech.speak("There is no previous successful action to repeat.")
                    continue

            if not self.validator.validate(intent):
                self.text_to_speech.speak("I can't perform that action yet.")
                self.context.add_turn(text, intent, False)
                continue

            if intent["type"] == "conversation":
                self.text_to_speech.speak(intent.get("response", "How can I help?"))
                self.context.add_turn(text, intent, True)
                continue

            success = self.action_registry.execute(intent)
            self.context.add_turn(text, intent, success)

            if success:
                t = intent["type"]
                if t == "open_application":
                    self.text_to_speech.speak(f"Opening {intent['application']}.")
                elif t == "open_website":
                    self.text_to_speech.speak(f"Opening {intent['website']}.")
                elif t == "search_web":
                    self.text_to_speech.speak("Searching the web.")
                elif t == "browser_search":
                    self.text_to_speech.speak("Search results are ready.")
                elif t == "browser_open_result":
                    self.text_to_speech.speak(f"Opening result {intent['number']}.")
                elif t == "browser_back":
                    self.text_to_speech.speak("Going back.")
                elif t == "browser_open_result_by_text":
                    self.text_to_speech.speak("Opening the matching result.")
                elif t == "browser_new_tab":
                    self.text_to_speech.speak("New tab opened.")
                elif t == "browser_close_tab":
                    self.text_to_speech.speak("Tab closed.")
                elif t == "open_folder":
                    self.text_to_speech.speak(f"Opening {intent['folder']}.")
                elif t == "take_screenshot":
                    self.text_to_speech.speak("Screenshot saved.")
                elif t == "volume_up":
                    self.text_to_speech.speak("Volume increased.")
                elif t == "volume_down":
                    self.text_to_speech.speak("Volume decreased.")
                elif t == "volume_mute":
                    self.text_to_speech.speak("Volume muted.")
                elif t == "media_play_pause":
                    self.text_to_speech.speak("Playback toggled.")
                elif t == "minimize_window":
                    self.text_to_speech.speak("Window minimized.")
                elif t == "maximize_window":
                    self.text_to_speech.speak("Window maximized.")
            else:
                self.text_to_speech.speak("I couldn't complete that action.")
