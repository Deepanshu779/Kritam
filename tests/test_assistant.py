"""Unit tests for Kritam assistant core components."""

import os
import shutil
import tempfile
import unittest

# Ensure app is importable
import app
from core.validator import ActionValidator
from intelligence.fast_router import FastRouter
from core.task_planner import TaskPlanner
from core.memory import PersistentMemory
from core.settings import Settings
from core.auth import LocalAuth
from actions.registry import ActionRegistry


class TestValidator(unittest.TestCase):

    def setUp(self):
        self.validator = ActionValidator()

    def test_allowed_intents(self):
        self.assertTrue(self.validator.validate({"type": "history_summary"}))
        self.assertTrue(self.validator.validate({"type": "task_status"}))
        self.assertTrue(self.validator.validate({"type": "ai_status"}))
        self.assertTrue(self.validator.validate({"type": "memory_summary"}))
        self.assertTrue(self.validator.validate({"type": "memory_clear"}))
        self.assertTrue(self.validator.validate({"type": "conversation", "response": "Hello!"}))

    def test_application_validation(self):
        self.assertTrue(self.validator.validate({"type": "open_application", "application": "notepad"}))
        self.assertTrue(self.validator.validate({"type": "open_application", "application": "calculator"}))
        self.assertFalse(self.validator.validate({"type": "open_application", "application": "malware"}))

    def test_browser_results_validation(self):
        self.assertTrue(self.validator.validate({"type": "browser_open_result", "number": 3}))
        self.assertTrue(self.validator.validate({"type": "browser_open_result", "number": "3"}))
        self.assertFalse(self.validator.validate({"type": "browser_open_result", "number": 10}))
        self.assertFalse(self.validator.validate({"type": "browser_open_result", "number": "invalid"}))

    def test_blocked_intents(self):
        self.assertFalse(self.validator.validate({"type": "execute_shell"}))
        self.assertFalse(self.validator.validate({"type": "run_command"}))
        self.assertFalse(self.validator.validate({"type": "delete_file"}))


class TestFastRouter(unittest.TestCase):

    def setUp(self):
        self.router = FastRouter()

    def test_conversations(self):
        result = self.router.route("hello")
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "conversation")

        result = self.router.route("who are you")
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "conversation")

        result = self.router.route("what time is it")
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "conversation")

    def test_system_and_apps(self):
        result = self.router.route("open notepad")
        self.assertEqual(result, {"type": "open_application", "application": "notepad"})

        result = self.router.route("launch calculator")
        self.assertEqual(result, {"type": "open_application", "application": "calculator"})

        result = self.router.route("open youtube")
        self.assertEqual(result, {"type": "open_website", "website": "youtube"})

        result = self.router.route("take a screenshot")
        self.assertEqual(result, {"type": "take_screenshot"})

        result = self.router.route("volume up")
        self.assertEqual(result, {"type": "volume_up"})

    def test_history_and_task_status(self):
        result = self.router.route("show command history")
        self.assertEqual(result, {"type": "history_summary"})

        result = self.router.route("task status")
        self.assertEqual(result, {"type": "task_status"})

    def test_memory_commands(self):
        result = self.router.route("remember that my key is 12345")
        self.assertEqual(result, {"type": "memory_remember", "key": "key", "value": "12345"})

        result = self.router.route("what is my key")
        self.assertEqual(result, {"type": "memory_recall", "key": "key"})

        result = self.router.route("forget my key")
        self.assertEqual(result, {"type": "memory_forget", "key": "key"})

    def test_repeated_speech_deduplication(self):
        result = self.router.route("open notepad open notepad")
        self.assertEqual(result, {"type": "open_application", "application": "notepad"})


class TestTaskPlanner(unittest.TestCase):

    def setUp(self):
        self.planner = TaskPlanner()

    def test_splitting(self):
        tasks = self.planner.split("open notepad and then open paint")
        self.assertEqual(tasks, ["open notepad", "open paint"])

        tasks = self.planner.split("take a screenshot after that mute volume")
        self.assertEqual(tasks, ["take a screenshot", "mute volume"])

    def test_describe(self):
        tasks = ["open notepad", "open paint"]
        desc = self.planner.describe(tasks)
        self.assertIn("1. open notepad", desc)
        self.assertIn("2. open paint", desc)


class TestPersistentMemory(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.mem_path = os.path.join(self.test_dir, "test_memory.json")
        self.memory = PersistentMemory(path=self.mem_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_remember_recall_forget(self):
        self.assertTrue(self.memory.remember("favorite color", "blue"))
        self.assertEqual(self.memory.recall("favorite color"), "blue")

        found = self.memory.find("color")
        self.assertIsNotNone(found)
        self.assertEqual(found["value"], "blue")

        self.assertTrue(self.memory.forget("color"))
        self.assertIsNone(self.memory.recall("favorite color"))

    def test_clear(self):
        self.memory.remember("pet", "cat")
        self.assertTrue(self.memory.clear())
        self.assertIsNone(self.memory.recall("pet"))


class TestSettings(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.settings_path = os.path.join(self.test_dir, "test_settings.json")
        self.settings = Settings(path=self.settings_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_and_set(self):
        self.assertEqual(self.settings.get("assistant_name"), "Kritam")
        self.assertTrue(self.settings.set("assistant_name", "Maya"))
        self.assertEqual(self.settings.get("assistant_name"), "Maya")

        # Reload from disk
        reloaded = Settings(path=self.settings_path)
        self.assertEqual(reloaded.get("assistant_name"), "Maya")


class TestLocalAuth(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.auth_path = os.path.join(self.test_dir, "test_auth.json")
        self.auth = LocalAuth(path=self.auth_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_signup_and_login(self):
        ok, msg = self.auth.signup("Deepanshu", "test@example.com", "secret123")
        self.assertTrue(ok)

        # Duplicate signup fails
        dup_ok, _ = self.auth.signup("Deepanshu", "test@example.com", "secret123")
        self.assertFalse(dup_ok)

        # Login success
        login_ok, account = self.auth.login("test@example.com", "secret123")
        self.assertTrue(login_ok)
        self.assertEqual(account["name"], "Deepanshu")

        # Login failure
        fail_ok, _ = self.auth.login("test@example.com", "wrongpassword")
        self.assertFalse(fail_ok)


class TestAssistantProcessText(unittest.TestCase):

    def test_conversational_response_preserved(self):
        from core.assistant import Kritam
        assistant = Kritam()
        result = assistant.process_text("who are you", speak=False)
        self.assertTrue(result["success"])
        self.assertIn("Kritam", result["response"])
        self.assertNotIn("Task completed.", result["response"])

    def test_history_and_task_status_execution(self):
        from core.assistant import Kritam
        assistant = Kritam()
        result = assistant.process_text("show command history", speak=False)
        self.assertTrue(result["success"])
        self.assertTrue(len(result["response"]) > 0)


if __name__ == "__main__":
    unittest.main()

