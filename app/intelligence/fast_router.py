class FastRouter:

    def route(self, text):
        command = text.lower().strip()

        # Open applications
        if command in {
            "open notepad",
            "open notebook",
            "open note",
            "open text editor",
        }:
            return {
                "type": "open_application",
                "application": "notepad"
            }

        if command in {
            "open calculator",
            "open calc",
        }:
            return {
                "type": "open_application",
                "application": "calculator"
            }

        if command == "open paint":
            return {
                "type": "open_application",
                "application": "paint"
            }

        # Simple conversation
        if command in {"hello", "hi", "hey"}:
            return {
                "type": "conversation",
                "response": "Hello! How can I help?"
            }

        if command in {
            "how are you",
            "how are you doing",
        }:
            return {
                "type": "conversation",
                "response": "I'm doing good. How can I help?"
            }

        return None