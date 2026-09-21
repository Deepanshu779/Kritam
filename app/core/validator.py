class ActionValidator:

    ALLOWED_APPLICATIONS = {
        "notepad",
        "calculator",
        "paint",
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

        return False