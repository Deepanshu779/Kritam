class ActionValidator:
    BLOCKED_INTENTS = {"execute_shell", "run_command", "shutdown", "restart"}
    ALLOWED_APPLICATIONS = {"notepad", "calculator", "paint", "chrome", "task manager", "file explorer", "settings"}
    ALLOWED_WEBSITES = {"youtube", "google", "github", "gmail"}
    ALLOWED_FOLDERS = {"downloads", "documents", "desktop", "pictures"}
    ALLOWED_SYSTEM_ACTIONS = {"take_screenshot", "volume_up", "volume_down", "volume_mute", "media_play_pause", "minimize_window", "maximize_window"}
    ALLOWED_BROWSER_ACTIONS = {"browser_search", "browser_open_result", "browser_open_result_by_text", "browser_back", "browser_new_tab", "browser_close_tab", "play_music"}
    ALLOWED_MEMORY_ACTIONS = {"memory_summary", "memory_clear", "memory_remember", "memory_recall", "memory_forget", "history_summary", "task_status", "set_setting", "ai_status"}
    COMPUTER_ACTIONS = {"computer_list_directory", "computer_read_file", "computer_open_path", "computer_create_folder", "computer_write_file", "computer_copy_file", "computer_move_file", "computer_delete_file"}

    def validate(self, intent):
        if not isinstance(intent, dict):
            return False
        t = intent.get("type")
        if t in self.BLOCKED_INTENTS:
            return False
        if t == "conversation":
            return True
        if t == "open_application":
            return intent.get("application", "").lower().strip() in self.ALLOWED_APPLICATIONS
        if t == "open_website":
            return intent.get("website", "").lower().strip() in self.ALLOWED_WEBSITES
        if t in {"search_web", "browser_search"}:
            return bool(intent.get("query", "").strip())
        if t == "open_folder":
            return intent.get("folder", "").lower().strip() in self.ALLOWED_FOLDERS
        if t in self.ALLOWED_SYSTEM_ACTIONS or t in {"browser_back", "browser_new_tab", "browser_close_tab"}:
            return True
        if t == "play_music":
            return intent.get("platform", "").lower().strip() in {"youtube", "spotify"} and bool(intent.get("query", "").strip())
        if t == "browser_open_result":
            try:
                return 1 <= int(intent.get("number")) <= 5
            except (ValueError, TypeError):
                return False
        if t == "browser_open_result_by_text":
            return bool(intent.get("text", "").strip())
        if t in self.ALLOWED_MEMORY_ACTIONS:
            if t == "set_setting":
                return intent.get("key") in {"assistant_name", "language"} and bool(str(intent.get("value", "")).strip())
            if t == "memory_remember":
                return bool(intent.get("key", "").strip()) and bool(intent.get("value", "").strip())
            if t in {"memory_recall", "memory_forget"}:
                return bool(intent.get("key", "").strip())
            return True
        if t == "computer_list_directory":
            return True
        if t in {"computer_read_file", "computer_open_path"}:
            return bool(str(intent.get("path", "")).strip())
        if t in {"computer_create_folder", "computer_write_file", "computer_delete_file"}:
            return bool(str(intent.get("path", "")).strip()) and bool(intent.get("confirmed", False))
        if t in {"computer_copy_file", "computer_move_file"}:
            return bool(str(intent.get("source", "")).strip()) and bool(str(intent.get("destination", "")).strip()) and bool(intent.get("confirmed", False))
        return False
