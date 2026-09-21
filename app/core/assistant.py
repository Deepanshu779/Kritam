from voice.listener import VoiceListener
from voice.speech_to_text import SpeechToText
from voice.text_to_speech import TextToSpeech

from brain.intent_engine import IntentEngine
from intelligence.fast_router import FastRouter
from core.context import ConversationContext
from core.validator import ActionValidator
from core.memory import PersistentMemory
from core.settings import Settings
from core.task_planner import TaskPlanner
from core.history import CommandHistory
from core.task_manager import TaskManager

from actions.applications import ApplicationManager
from actions.browser import BrowserManager
from actions.files import FileManager
from actions.system import SystemManager
from actions.registry import ActionRegistry


class Kritam:

    def __init__(self):
        self.settings = Settings()
        self.name = self.settings.get("assistant_name", "Kritam")
        self.memory = PersistentMemory()
        self.history = CommandHistory()
        self.planner = TaskPlanner()
        self.task_manager = TaskManager()
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

    def _handle_intent(self, text, intent):
        if intent.get("type") == "repeat_last_action":
            intent = self.context.repeat_last()
            if intent is None:
                self.text_to_speech.speak("There is no previous successful action to repeat.")
                return False

        if not self.validator.validate(intent):
            self.text_to_speech.speak("I can't perform that action yet.")
            self.context.add_turn(text, intent, False)
            self.history.add(text, intent, False)
            return False

        t = intent["type"]

        if t == "ai_status":\n            status = self.intent_engine.ai.status_text()\n            self.text_to_speech.speak(status)\n            self.context.add_turn(text, intent, True)\n            self.history.add(text, intent, True)\n            return True\n\n        if t == "memory_remember":
            success = self.memory.remember(intent["key"], intent["value"])
            self.context.add_turn(text, intent, success)
            self.history.add(text, intent, success)
            self.text_to_speech.speak("I'll remember that." if success else "I couldn't save that memory.")
            return success

        if t == "memory_recall":
            result = self.memory.find(intent["key"])
            self.context.add_turn(text, intent, True)
            self.history.add(text, intent, True)
            if result:
                self.text_to_speech.speak(f"Your {result['key']} is {result['value']}.")
            else:
                self.text_to_speech.speak("I don't have that saved.")
            return True

        if t == "memory_forget":
            key = intent["key"].strip().lower()
            facts = self.memory.all_facts()
            matched = next((k for k in facts if key in k), None)
            success = False
            if matched:
                self.memory.data["facts"].pop(matched, None)
                success = self.memory._save()
            self.context.add_turn(text, intent, success)
            self.history.add(text, intent, success)
            self.text_to_speech.speak("I've forgotten that." if success else "I don't have that saved.")
            return success

        if t == "set_setting":
            success = self.settings.set(intent["key"], intent["value"])
            if success and intent["key"] == "assistant_name":
                self.name = intent["value"]
            self.context.add_turn(text, intent, success)
            self.history.add(text, intent, success)
            self.text_to_speech.speak(
                "Setting updated." if success else "I couldn't update that setting."
            )
            return success

        if t == "task_status":
            self.text_to_speech.speak(self.task_manager.status_text())
            self.context.add_turn(text, intent, True)
            self.history.add(text, intent, True)
            return True

        if t == "history_summary":
            recent = self.history.recent(5)
            if not recent:
                response = "There is no command history yet."
            else:
                response = "Recently: " + ". ".join(
                    item["command"] for item in recent
                )
            self.text_to_speech.speak(response)
            self.context.add_turn(text, intent, True)
            return True

        if t == "memory_summary":
            self.text_to_speech.speak(self.memory.summary())
            self.context.add_turn(text, intent, True)
            self.history.add(text, intent, True)
            return True

        if t == "memory_clear":
            success = self.memory.clear()
            self.context.add_turn(text, intent, success)
            self.history.add(text, intent, success)
            self.text_to_speech.speak("Saved memory cleared." if success else "I couldn't clear saved memory.")
            return success

        if t == "conversation":
            self.text_to_speech.speak(intent.get("response", "How can I help?"))
            self.context.add_turn(text, intent, True)
            self.history.add(text, intent, True)
            return True

        success = self.action_registry.execute(intent)
        self.context.add_turn(text, intent, success)
        self.history.add(text, intent, success)

        if success:
            messages = {
                "open_application": f"Opening {intent['application']}.",
                "open_website": f"Opening {intent['website']}.",
                "search_web": "Searching the web.",
                "browser_search": "Search results are ready.",
                "browser_open_result": f"Opening result {intent['number']}.",
                "browser_back": "Going back.",
                "browser_open_result_by_text": "Opening the matching result.",
                "browser_new_tab": "New tab opened.",
                "browser_close_tab": "Tab closed.",
                "open_folder": f"Opening {intent['folder']}.",
                "take_screenshot": "Screenshot saved.",
                "volume_up": "Volume increased.",
                "volume_down": "Volume decreased.",
                "volume_mute": "Volume muted.",
                "media_play_pause": "Playback toggled.",
                "minimize_window": "Window minimized.",
                "maximize_window": "Window maximized.",
            }
            self.text_to_speech.speak(messages.get(t, "Done."))
        else:
            self.text_to_speech.speak("I couldn't complete that action.")
        return success

    def _process_command(self, text):
        intent = self.fast_router.route(text, context=self.context)
        if intent is None:
            print("Kritam: Using AI...")
            intent = self.intent_engine.understand(text, context=self.context)
        print(f"Kritam Intent: {intent}")
        return self._handle_intent(text, intent)

    def start(self):
        print(f"{self.name} is starting...")
        self.text_to_speech.speak(f"Hello. {self.name} is ready.")

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

            tasks = self.planner.split(text)
            self.task_manager.start(text, len(tasks))
            print(f"Kritam Plan: {self.planner.describe(tasks)}")

            for task in tasks:
                if task.lower() in {"exit", "quit", "stop"}:
                    self.text_to_speech.speak("Okay. See you later.")
                    return

                success = self._process_command(task)
                self.task_manager.complete(success)
                if not success and len(tasks) > 1:
                    self.task_manager.fail()
                    self.text_to_speech.speak("The task stopped because a step failed.")
                    break
            else:
                self.task_manager.finish()
