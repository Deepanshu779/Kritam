import re


class FastRouter:

    def route(self, text):
        command = text.lower().strip()

        words = command.split()
        if len(words) >= 4 and len(words) % 2 == 0:
            half = len(words) // 2
            if words[:half] == words[half:]:
                command = " ".join(words[:half])

        if command in {"repeat", "repeat that", "do that again", "again", "repeat last action"}:
            return {"type": "repeat_last_action"}

        application_patterns = [
            (r"^(open|launch|start) (notepad|notebook|note|text editor|text pad)$", "notepad"),
            (r"^(open|launch|start) (calculator|calc)$", "calculator"),
            (r"^(open|launch|start) paint$", "paint"),
            (r"^(open|launch|start) (chrome|google chrome)$", "chrome"),
            (r"^(open|launch|start) task manager$", "task manager"),
            (r"^(open|launch|start) (file explorer|explorer)$", "file explorer"),
            (r"^(open|launch|start) settings$", "settings"),
        ]

        for pattern, application in application_patterns:
            if re.fullmatch(pattern, command):
                return {"type": "open_application", "application": application}

        website_patterns = [
            (r"^(open|visit|go to) youtube$", "youtube"),
            (r"^(open|visit|go to) google$", "google"),
            (r"^(open|visit|go to) github$", "github"),
            (r"^(open|visit|go to) gmail$", "gmail"),
        ]

        for pattern, website in website_patterns:
            if re.fullmatch(pattern, command):
                return {"type": "open_website", "website": website}

        search_patterns = (
            r"^search(?: google)? for (.+)$",
            r"^search (.+) on google$",
            r"^google (.+)$",
        )

        for pattern in search_patterns:
            match = re.fullmatch(pattern, command)
            if match:
                query = match.group(1).strip()
                if query:
                    return {"type": "search_web", "query": query}

        folder_patterns = [
            (r"^(open|show) downloads?( folder)?$", "downloads"),
            (r"^(open|show) documents?( folder)?$", "documents"),
            (r"^(open|show) desktop( folder)?$", "desktop"),
            (r"^(open|show) pictures?( folder)?$", "pictures"),
        ]

        for pattern, folder in folder_patterns:
            if re.fullmatch(pattern, command):
                return {"type": "open_folder", "folder": folder}

        if re.fullmatch(r"(take )?(a )?(screenshot|screen capture)|(capture|save) (the )?screen", command):
            return {"type": "take_screenshot"}

        if command in {"hello", "hi", "hey", "hey kritam"}:
            return {"type": "conversation", "response": "Hello! How can I help?"}

        if command in {"how are you", "how are you doing"}:
            return {"type": "conversation", "response": "I'm doing good. How can I help?"}

        return None
