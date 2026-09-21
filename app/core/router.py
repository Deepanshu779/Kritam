class CommandRouter:

    def process(self, text):

        command = text.lower().strip()

        # Conversation
        if command in ["hello", "hi", "hey"]:
            return "conversation", "Hello! How are you?"

        if "how are you" in command:
            return "conversation", "I'm doing good. What are you working on?"

        if "who are you" in command:
            return "conversation", "I'm Kritam, your personal assistant."

        # System
        if command in ["exit", "quit", "stop"]:
            return "system", "exit"

        # Applications
        if "open notepad" in command:
            return "application", "notepad"

        if "open calculator" in command:
            return "application", "calculator"

        if "open paint" in command:
            return "application", "paint"

        return "unknown", text