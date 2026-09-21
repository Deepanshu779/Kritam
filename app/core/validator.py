class ActionValidator:

    ALLOWED_APPLICATIONS = {
        "notepad",
        "calculator",
        "paint",
    }

    ALLOWED_WEBSITES = {
        "youtube",
        "google",
        "github",
        "gmail",
    }

    ALLOWED_FOLDERS = {
        "downloads",
        "documents",
        "desktop",
        "pictures",
    }

    def validate(self, intent):
        if not isinstance(intent, dict):
            return False

        intent_type = intent.get("type")

        if intent_type == "conversation":
            return True

        if intent_type == "open_application":
            application = intent.get("application", "").lower().strip()
            return application in self.ALLOWED_APPLICATIONS

        if intent_type == "open_website":
            website = intent.get("website", "").lower().strip()
            return website in self.ALLOWED_WEBSITES

        if intent_type == "search_web":
            return bool(intent.get("query", "").strip())

        if intent_type == "open_folder":
            folder = intent.get("folder", "").lower().strip()
            return folder in self.ALLOWED_FOLDERS

        return False
