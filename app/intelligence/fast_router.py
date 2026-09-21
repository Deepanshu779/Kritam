class FastRouter:

    def route(self, text):
        command = text.lower().strip()

        # Applications
        if command in {
            "open notepad",
            "open notebook",
            "open note",
            "open text editor",
            "open text pad",
        }:
            return {"type": "open_application", "application": "notepad"}

        if command in {"open calculator", "open calc"}:
            return {"type": "open_application", "application": "calculator"}

        if command == "open paint":
            return {"type": "open_application", "application": "paint"}

        # Websites
        website_aliases = {
            "open youtube": "youtube",
            "open google": "google",
            "open github": "github",
            "open gmail": "gmail",
        }

        if command in website_aliases:
            return {
                "type": "open_website",
                "website": website_aliases[command],
            }

        # Web search
        search_prefixes = (
            "search google for ",
            "search for ",
            "google ",
        )

        for prefix in search_prefixes:
            if command.startswith(prefix):
                query = command[len(prefix):].strip()
                if query:
                    return {"type": "search_web", "query": query}

        # Common folders
        folder_aliases = {
            "open downloads": "downloads",
            "open download folder": "downloads",
            "open documents": "documents",
            "open documents folder": "documents",
            "open desktop": "desktop",
            "open desktop folder": "desktop",
            "open pictures": "pictures",
            "open pictures folder": "pictures",
        }

        if command in folder_aliases:
            return {
                "type": "open_folder",
                "folder": folder_aliases[command],
            }

        # Conversation
        if command in {"hello", "hi", "hey"}:
            return {
                "type": "conversation",
                "response": "Hello! How can I help?",
            }

        if command in {"how are you", "how are you doing"}:
            return {
                "type": "conversation",
                "response": "I'm doing good. How can I help?",
            }

        return None
