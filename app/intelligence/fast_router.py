import re


class FastRouter:

    def route(self, text, context=None):
        command = text.lower().strip()

        words = command.split()
        if len(words) >= 4 and len(words) % 2 == 0:
            half = len(words) // 2
            if words[:half] == words[half:]:
                command = " ".join(words[:half])

        if command in {"repeat", "repeat that", "do that again", "again", "repeat last action"}:
            return {"type": "repeat_last_action"}

        if command in {"what did i do recently", "show recent commands", "show command history", "what have i done recently"}:
            return {"type": "history_summary"}

        if command in {"task status", "what is the task status", "how is the task going", "what are you doing"}:
            return {"type": "task_status"}

        match = re.fullmatch(r"(?:change|set) (?:your )?name to (.+)", command)
        if match:
            return {"type": "set_setting", "key": "assistant_name", "value": match.group(1).strip()}

        match = re.fullmatch(r"(?:change|set) language to (english|hindi|hinglish)", command)
        if match:
            return {"type": "set_setting", "key": "language", "value": match.group(1).strip()}


        if command in {"what do you remember", "show my memories", "show memories", "what do you know about me"}:
            return {"type": "memory_summary"}

        match = re.fullmatch(r"(?:what is|what\'s|tell me) my (.+)", command)
        if match:
            return {"type": "memory_recall", "key": match.group(1).strip()}

        if command in {"clear memory", "forget everything you remember", "delete saved memories"}:
            return {"type": "memory_clear"}

        match = re.fullmatch(r"(?:forget|forget my) (.+)", command)
        if match:
            return {"type": "memory_forget", "key": match.group(1).strip()}

        match = re.fullmatch(r"remember (?:that )?my (.+?) is (.+)", command)
        if match:
            return {
                "type": "memory_remember",
                "key": match.group(1).strip(),
                "value": match.group(2).strip(),
            }

        if command in {"search that again", "repeat the search", "search again", "repeat last search"}:
            previous = context.last_intent_of_type("search_web") if context else None
            if previous:
                return dict(previous)
            return {"type": "unknown"}

        if command in {"volume up", "increase volume", "turn volume up", "louder"}:
            return {"type": "volume_up"}

        if command in {"volume down", "decrease volume", "turn volume down", "quieter"}:
            return {"type": "volume_down"}

        if command in {"mute", "mute volume", "turn volume off"}:
            return {"type": "volume_mute"}

        if command in {"play pause", "play or pause", "pause music", "resume music", "toggle play pause"}:
            return {"type": "media_play_pause"}

        if command in {"minimize window", "minimize this window", "minimize"}:
            return {"type": "minimize_window"}

        if command in {"maximize window", "maximize this window", "maximize"}:
            return {"type": "maximize_window"}

        if command in {"new tab", "open new tab", "create new tab"}:
            return {"type": "browser_new_tab"}

        if command in {"close tab", "close this tab", "close current tab"}:
            return {"type": "browser_close_tab"}

        if command in {"open first result", "open the first result", "open first search result", "open the first search result"}:
            return {"type": "browser_open_result", "number": 1}

        if command in {"go back", "browser back", "go back in browser", "back"}:
            return {"type": "browser_back"}

        match = re.fullmatch(r"open (?:the )?(?:result )?(?:number )?([1-5])", command)
        if match:
            return {"type": "browser_open_result", "number": int(match.group(1))}

        match = re.fullmatch(r"(?:open|show) (?:the )?result (?:about|for) (.+)", command)
        if match:
            return {"type": "browser_open_result_by_text", "text": match.group(1).strip()}

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

        browser_patterns = (
            r"^(browse|browser|search in browser|search the browser) (.+)$",
            r"^(search and show|search with browser) (.+)$",
        )
        for pattern in browser_patterns:
            match = re.fullmatch(pattern, command)
            if match:
                return {"type": "browser_search", "query": match.group(2)}

        search_patterns = (
            r"^(now )?search(?: google)? for (.+)$",
            r"^search (.+) on google$",
            r"^google (.+)$",
        )
        for pattern in search_patterns:
            match = re.fullmatch(pattern, command)
            if match:
                query = match.group(1 if pattern.startswith("^google") else 2).strip()
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
