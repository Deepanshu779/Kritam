"""Validate model-produced intents before they reach action handlers.

Treat every field as untrusted input: an LLM response can be malformed even
when its top-level JSON is valid.
"""


class ActionValidator:
    BLOCKED_INTENTS = {"execute_shell", "run_command", "shutdown", "restart"}
    ALLOWED_APPLICATIONS = {"notepad", "calculator", "paint", "chrome", "task manager", "file explorer", "settings"}
    ALLOWED_WEBSITES = {"youtube", "google", "github", "gmail"}
    ALLOWED_FOLDERS = {"downloads", "documents", "desktop", "pictures"}
    ALLOWED_SYSTEM_ACTIONS = {"take_screenshot", "volume_up", "volume_down", "volume_mute", "media_play_pause", "minimize_window", "maximize_window"}
    ALLOWED_BROWSER_ACTIONS = {"browser_search", "browser_open_result", "browser_open_result_by_text", "browser_back", "browser_new_tab", "browser_close_tab", "play_music"}
    ALLOWED_MEMORY_ACTIONS = {"memory_summary", "memory_clear", "memory_remember", "memory_recall", "memory_forget", "history_summary", "task_status", "set_setting", "ai_status"}
    COMPUTER_ACTIONS = {"computer_list_directory", "computer_read_file", "computer_open_path", "computer_create_folder", "computer_write_file", "computer_copy_file", "computer_move_file", "computer_delete_file"}

    @staticmethod
    def _text(intent, key, *, default="", max_length=4096):
        value = intent.get(key, default)
        if not isinstance(value, str):
            return None
        value = value.strip()
        if len(value) > max_length:
            return None
        return value

    def validate(self, intent):
        if not isinstance(intent, dict):
            return False

        action = intent.get("type")
        if not isinstance(action, str) or action in self.BLOCKED_INTENTS:
            return False
        if action == "conversation":
            return isinstance(intent.get("response", ""), str)
        if action == "open_application":
            value = self._text(intent, "application", max_length=80)
            return value is not None and value.lower() in self.ALLOWED_APPLICATIONS
        if action == "open_website":
            value = self._text(intent, "website", max_length=80)
            return value is not None and value.lower() in self.ALLOWED_WEBSITES
        if action in {"search_web", "browser_search"}:
            value = self._text(intent, "query", max_length=500)
            return bool(value)
        if action == "open_folder":
            value = self._text(intent, "folder", max_length=80)
            return value is not None and value.lower() in self.ALLOWED_FOLDERS
        if action in self.ALLOWED_SYSTEM_ACTIONS or action in {"browser_back", "browser_new_tab", "browser_close_tab"}:
            return True
        if action == "play_music":
            platform = self._text(intent, "platform", max_length=40)
            query = self._text(intent, "query", max_length=500)
            return platform is not None and platform.lower() in {"youtube", "spotify"} and bool(query)
        if action == "browser_open_result":
            number = intent.get("number")
            return isinstance(number, int) and not isinstance(number, bool) and 1 <= number <= 5
        if action == "browser_open_result_by_text":
            return bool(self._text(intent, "text", max_length=500))
        if action in self.ALLOWED_MEMORY_ACTIONS:
            if action == "set_setting":
                key = self._text(intent, "key", max_length=80)
                value = self._text(intent, "value", max_length=200)
                return key in {"assistant_name", "language"} and bool(value)
            if action == "memory_remember":
                return bool(self._text(intent, "key", max_length=200)) and bool(self._text(intent, "value", max_length=1000))
            if action in {"memory_recall", "memory_forget"}:
                return bool(self._text(intent, "key", max_length=200))
            return True
        if action == "computer_list_directory":
            return True
        if action in {"computer_read_file", "computer_open_path"}:
            return bool(self._text(intent, "path"))
        if action in {"computer_create_folder", "computer_write_file", "computer_delete_file"}:
            return bool(self._text(intent, "path")) and intent.get("confirmed") is True
        if action in {"computer_copy_file", "computer_move_file"}:
            return bool(self._text(intent, "source")) and bool(self._text(intent, "destination")) and intent.get("confirmed") is True
        return False
