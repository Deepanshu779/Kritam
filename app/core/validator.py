class ActionValidator:

    ALLOWED_APPLICATIONS = {
        "notepad", "calculator", "paint", "chrome",
    }

    ALLOWED_WEBSITES = {
        "youtube", "google", "github", "gmail",
    }

    ALLOWED_FOLDERS = {
        "downloads", "documents", "desktop", "pictures",
    }

    ALLOWED_SYSTEM_ACTIONS = {
        "take_screenshot",
    }

    def validate(self, intent):
        if not isinstance(intent, dict):
            return False

        intent_type = intent.get("type")

        if intent_type == "conversation":
            return True

        if intent_type == "open_application":
            return intent.get("application", "").lower().strip() in self.ALLOWED_APPLICATIONS

        if intent_type == "open_website":
            return intent.get("website", "").lower().strip() in self.ALLOWED_WEBSITES

        if intent_type == "search_web":
            return bool(intent.get("query", "").strip())

        if intent_type == "open_folder":
            return intent.get("folder", "").lower().strip() in self.ALLOWED_FOLDERS

        if intent_type in self.ALLOWED_SYSTEM_ACTIONS:
            return True

        return False
