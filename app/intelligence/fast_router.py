class FastRouter:

    def route(self, text):
        command = text.lower().strip()

        words = command.split()
        if len(words) >= 4 and len(words) % 2 == 0:
            half = len(words) // 2
            if words[:half] == words[half:]:
                command = " ".join(words[:half])

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
            return {"type": "open_application", "application": application_aliases[command]}

        website_aliases = {
            "open youtube": "youtube",
            "open google": "google",
            "open github": "github",
            "open gmail": "gmail",
        }

        if command in website_aliases:
            return {"type": "open_website", "website": website_aliases[command]}

        search_prefixes = ("search google for ", "search for ", "google ")
        for prefix in search_prefixes:
            if command.startswith(prefix):
                query = command[len(prefix):].strip()
                if query:
                    return {"type": "search_web", "query": query}

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
            return {"type": "open_folder", "folder": folder_aliases[command]}

        if command in {
            "take screenshot",
            "take a screenshot",
            "capture screen",
            "screenshot",
        }:
            return {"type": "take_screenshot"}

        if command in {"hello", "hi", "hey"}:
            return {"type": "conversation", "response": "Hello! How can I help?"}

        if command in {"how are you", "how are you doing"}:
            return {"type": "conversation", "response": "I'm doing good. How can I help?"}

        return None
