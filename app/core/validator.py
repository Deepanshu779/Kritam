class ActionValidator:

    BLOCKED_INTENTS = {"execute_shell", "run_command", "delete_file", "install_software", "shutdown", "restart"}

    ALLOWED_APPLICATIONS = {"notepad", "calculator", "paint", "chrome", "task manager", "file explorer", "settings"}
    ALLOWED_WEBSITES = {"youtube", "google", "github", "gmail"}
    ALLOWED_FOLDERS = {"downloads", "documents", "desktop", "pictures"}
    ALLOWED_SYSTEM_ACTIONS = {"take_screenshot", "volume_up", "volume_down", "volume_mute", "media_play_pause", "minimize_window", "maximize_window"}
    ALLOWED_BROWSER_ACTIONS = {
        "browser_search", "browser_open_result", "browser_open_result_by_text",
        "browser_back", "browser_new_tab", "browser_close_tab", "play_music",
    }
    ALLOWED_MEMORY_ACTIONS = {"memory_summary", "memory_clear", "memory_remember", "memory_recall", "memory_forget", "history_summary", "task_status", "set_setting", "ai_status"}

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
        if t in self.ALLOWED_SYSTEM_ACTIONS:
            return True
        if t in {"browser_back", "browser_new_tab", "browser_close_tab"}:
            return True
        if t == "play_music":
            return intent.get("platform", "").lower().strip() in {"youtube", "spotify"} and bool(intent.get("query", "").strip())
        if t == "browser_open_result":
            return isinstance(intent.get("number"), int) and 1 <= intent["number"] <= 5
        if t == "browser_open_result_by_text":
            return bool(intent.get("text", "").strip())
        if t in {"memory_summary", "memory_clear", "ai_status"}:
            return True
        if t == "set_setting":
            return intent.get("key") in {"assistant_name", "language"} and bool(intent.get("value", "").strip())
        if t == "memory_remember":
            return bool(intent.get("key", "").strip()) and bool(intent.get("value", "").strip())
        if t in {"memory_recall", "memory_forget"}:
            return bool(intent.get("key", "").strip())
        return False
