class FastRouter:

    def route(self, text):
        command = text.lower().strip()

        # Remove an accidental repeated command from STT.
        words = command.split()
        if len(words) >= 4 and len(words) % 2 == 0:
            half = len(words) // 2
            if words[:half] == words[half:]:
                command = " ".join(words[:half])

        # Applications
        application_aliases = {
            "open notepad": "notepad",
            "open notebook": "notepad",
            "open note": "notepad",
            "open text editor": "notepad",
            "open text pad": "notepad",
            "open calculator": "calculator",
            "open calc": "calculator",
            "open paint": "paint",
            "open chrome": "chrome",
            "start chrome": "chrome",
        }

        if command in application_aliases:
            return {
                "type": "open_application",
                "application": application_aliases[command],
            }

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
                    return {
                        "type": "search_web",
                        "query": query,
                    }

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
