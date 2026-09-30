"""Fast pattern-matching router for Kritam assistant.

Routes common commands instantly without requiring slow LLM calls, supporting:
- English, Hindi, and Hinglish / code-switching
- Conversational corrections ("No, wait...", "Actually...", "Instead...")
- Natural polite phrasing ("Could you please open Chrome?", "Kritam Chrome khol do")
- Contextual pronoun and reference resolution ("it", "that", "the second result", "go back")
- Preserves exact casing for names, search terms, and song titles
"""

import re
from typing import Any, Dict, Optional


class FastRouter:
    """High-speed intent router with multilingual and conversational context awareness."""

    WAKE_PREFIX = re.compile(
        r"^(?:(?:hey|hi|hello|ok|okay|arre|namaste)?\s*kritam[,.]?\s*)+",
        re.IGNORECASE,
    )

    CORRECTION_PREFIX = re.compile(
        r"^(?:no[,.]?\s+wait[,.]?\s*|wait[,.]?\s*|no[,.]?\s+i meant[,.]?\s*|no[,.]?\s*|actually[,.]?\s*|i meant[,.]?\s*|instead[,.]?\s*)",
        re.IGNORECASE,
    )

    POLITE_PREFIX = re.compile(
        r"^(?:please\s+|can you\s+(?:please\s+)?|could you\s+(?:please\s+)?|mujhe\s+|kripya\s+|mere liye\s+)+",
        re.IGNORECASE,
    )

    POLITE_SUFFIX = re.compile(
        r"\s+(?:for me|please|kripya|bhi|yaar|na)+$",
        re.IGNORECASE,
    )

    def route(self, text: str, context: Any = None) -> Optional[Dict[str, Any]]:
        raw = text.strip()
        if not raw:
            return None

        # Clean outer punctuation
        clean_raw = re.sub(r"^[^\w]+|[^\w]+$", "", raw).strip()
        if not clean_raw:
            return None

        # Deduplicate speech repeating halves (Whisper artifact or echo)
        words = clean_raw.split()
        if len(words) >= 4 and len(words) % 2 == 0:
            half = len(words) // 2
            if [w.lower() for w in words[:half]] == [w.lower() for w in words[half:]]:
                clean_raw = " ".join(words[:half])

        # Strip leading wake words ("Hey Kritam, open Chrome" -> "open Chrome")
        command = self.WAKE_PREFIX.sub("", clean_raw).strip()
        command = re.sub(r"^[^\w]+|[^\w]+$", "", command).strip()
        if not command:
            return {"type": "conversation", "response": "Yes, I'm listening."}

        command_lower = command.lower()

        # Check for conversational stops/pauses
        if command_lower in {"wait", "stop", "pause", "ruko", "ruk jao", "hold on"}:
            return {"type": "conversation", "response": "Waiting."}

        # Check for conversational corrections
        is_correction = bool(self.CORRECTION_PREFIX.match(command))
        clean_command = self.CORRECTION_PREFIX.sub("", command).strip()
        clean_command = re.sub(r"\s+(?:instead|please)$", "", clean_command, flags=re.IGNORECASE).strip()
        clean_command = re.sub(r"^[^\w]+|[^\w]+$", "", clean_command).strip()

        # Route the core command first
        intent = self._route_direct(clean_command, context)

        if intent is not None:
            return intent

        # If it was a correction and direct match didn't find an intent, check context
        if is_correction and context:
            # Did user correct a music request? e.g. "No, play Haryanvi songs" or "Haryanvi songs instead"
            last_music = context.last_intent_of_type("play_music")
            if last_music:
                query_candidate = clean_command
                query_candidate = re.sub(r"^(?:play|chalao|bajao|lagao)\s+", "", query_candidate, flags=re.IGNORECASE).strip()
                query = self._clean_music_query(query_candidate)
                if query:
                    return {
                        "type": "play_music",
                        "query": query,
                        "platform": last_music.get("platform", "youtube"),
                    }

            # Did user correct a search query? e.g. "No, search Python 3.12 tutorials"
            last_search = context.last_intent_of_type("search_web")
            if last_search:
                search_cand = clean_command
                search_cand = re.sub(r"^(?:search|google|find)\s+(?:for\s+)?", "", search_cand, flags=re.IGNORECASE).strip()
                if search_cand:
                    return {"type": "search_web", "query": search_cand}

        return None

    def _route_direct(self, command: str, context: Any = None) -> Optional[Dict[str, Any]]:
        # Strip polite prefixes and suffixes
        command_core = self.POLITE_PREFIX.sub("", command).strip()
        command_core = self.POLITE_SUFFIX.sub("", command_core).strip()
        command_core = re.sub(r"^[^\w]+|[^\w]+$", "", command_core).strip()

        command_lower = command_core.lower()

        # System & conversational commands
        if command_lower in {"repeat", "repeat that", "do that again", "again", "repeat last action"}:
            return {"type": "repeat_last_action"}

        if command_lower in {"what did i do recently", "show recent commands", "show command history", "what have i done recently"}:
            return {"type": "history_summary"}

        if command_lower in {"task status", "what is the task status", "how is the task going", "what are you doing"}:
            return {"type": "task_status"}

        if command_lower in {"ai status", "ai health", "is ai available", "is the ai working", "check ai"}:
            return {"type": "ai_status"}

        match = re.fullmatch(r"(?:change|set) (?:your )?name to (.+)", command_core, re.IGNORECASE)
        if match:
            return {"type": "set_setting", "key": "assistant_name", "value": match.group(1).strip()}

        match = re.fullmatch(r"(?:change|set) language to (english|hindi|hinglish)", command_core, re.IGNORECASE)
        if match:
            return {"type": "set_setting", "key": "language", "value": match.group(1).strip().lower()}

        # Memory commands
        if command_lower in {"what do you remember", "show my memories", "show memories", "what do you know about me"}:
            return {"type": "memory_summary"}

        match = re.fullmatch(r"(?:what is|what\'s|tell me) my (.+)", command_core, re.IGNORECASE)
        if match:
            return {"type": "memory_recall", "key": match.group(1).strip()}

        if command_lower in {"clear memory", "forget everything you remember", "delete saved memories"}:
            return {"type": "memory_clear"}

        match = re.fullmatch(r"forget\s+(?:my\s+)?(.+)", command_core, re.IGNORECASE)
        if match:
            return {"type": "memory_forget", "key": match.group(1).strip()}

        match = re.fullmatch(r"remember (?:that )?my (.+?) is (.+)", command_core, re.IGNORECASE)
        if match:
            return {
                "type": "memory_remember",
                "key": match.group(1).strip(),
                "value": match.group(2).strip(),
            }

        if command_lower in {"search that again", "repeat the search", "search again", "repeat last search"}:
            previous = context.last_intent_of_type("search_web") if context else None
            if previous:
                return dict(previous)
            return {"type": "unknown"}

        # Volume control (English & Hindi/Hinglish)
        if (
            command_lower in {"volume up", "increase volume", "turn volume up", "louder"}
            or re.search(r"\b(?:volume|awaaz|awaj)\b.*\b(?:badhao|badha|badha do|tez karo|thoda badha do)\b", command_lower)
            or re.fullmatch(r"(?:volume\s+)?thoda\s+(?:volume\s+)?badha\s+do", command_lower)
        ):
            return {"type": "volume_up"}

        if (
            command_lower in {"volume down", "decrease volume", "turn volume down", "quieter"}
            or re.search(r"\b(?:volume|awaaz|awaj)\b.*\b(?:kam|kam karo|kam kar do|dheema karo|ghatao)\b", command_lower)
            or re.fullmatch(r"(?:volume\s+)?(?:thoda\s+)?(?:volume\s+)?kam\s+kar\s+do", command_lower)
        ):
            return {"type": "volume_down"}

        if command_lower in {"mute", "mute volume", "turn volume off", "awaaz band karo"}:
            return {"type": "volume_mute"}

        if command_lower in {"play pause", "play or pause", "pause music", "resume music", "toggle play pause"}:
            return {"type": "media_play_pause"}

        # Screenshots (English, Hindi, Hinglish: "Take a screenshot", "Ek screenshot le lo")
        if (
            re.search(r"\b(?:take|capture|click|save)\b.*\b(?:screenshot|screen shot|screen capture)\b", command_lower)
            or re.search(r"\b(?:screenshot|screen shot)\b.*\b(?:le|lo|kar|karo|lena|lelo|le do|le lena)\b", command_lower)
            or re.fullmatch(r"(?:ek\s+)?screenshot(?:\s+le\s+lo|\s+lo|\s+kheecho)?", command_lower)
            or re.fullmatch(r"(take )?(a )?(screenshot|screen capture)|(capture|save) (the )?screen", command_lower)
        ):
            return {"type": "take_screenshot"}

        # Natural app-opening requests (Chrome, Notepad, Calc, etc. in English and Hindi)
        app_match = re.fullmatch(
            r"(?:open|launch|start|kholo|khol|chalao|shuru karo)\s+"
            r"(?:the\s+|my\s+)?(google chrome|chrome|calculator|calc|notepad|"
            r"paint|file explorer|explorer|task manager|settings)(?:\s+(?:kholo|khol do|open karo|chala do))?",
            command_core,
            re.IGNORECASE,
        )
        if not app_match:
            app_match = re.fullmatch(
                r"(?:the\s+|my\s+)?(google chrome|chrome|calculator|calc|notepad|"
                r"paint|file explorer|explorer|task manager|settings)\s+"
                r"(?:kholo|khol do|khol de|open karo|open kar do|start karo)",
                command_core,
                re.IGNORECASE,
            )

        if app_match:
            raw_app = app_match.group(1).strip().lower()
            aliases = {
                "google chrome": "chrome",
                "chrome": "chrome",
                "calculator": "calculator",
                "calc": "calculator",
                "notepad": "notepad",
                "paint": "paint",
                "file explorer": "file explorer",
                "explorer": "file explorer",
                "task manager": "task manager",
                "settings": "settings",
            }
            return {"type": "open_application", "application": aliases[raw_app]}

        # Pronoun & Reference resolution: "open it", "open that"
        if command_lower in {"open it", "open that", "launch it", "launch that"}:
            if context and getattr(context, "last_application", None):
                return {"type": "open_application", "application": context.last_application}
            if context and getattr(context, "last_website", None):
                return {"type": "open_website", "website": context.last_website}

        # Website patterns ("open youtube", "open google", "visit github")
        website_patterns = [
            (r"^(open|visit|go to) youtube$", "youtube"),
            (r"^(open|visit|go to) google$", "google"),
            (r"^(open|visit|go to) github$", "github"),
            (r"^(open|visit|go to) gmail$", "gmail"),
            (r"^youtube\s+(kholo|khol do|open karo)$", "youtube"),
            (r"^google\s+(kholo|khol do|open karo)$", "google"),
            (r"^github\s+(kholo|khol do|open karo)$", "github"),
        ]
        for pattern, website in website_patterns:
            if re.fullmatch(pattern, command_lower):
                return {"type": "open_website", "website": website}

        # Specific Hindi/Hinglish search: "Google par Python search kar do"
        match = re.fullmatch(
            r"(?:google|the web|internet)\s+(?:par|pe|pr|on)\s+(.+?)\s+"
            r"(?:search|dhoondo|dhundo|find)(?:\s+(?:karo|kar do|kardo))?",
            command_core,
            re.IGNORECASE,
        )
        if match:
            return {"type": "search_web", "query": match.group(1).strip()}

        # Music requests (English, Hindi, Hinglish)
        # 1. Platform first: "youtube pe arijit singh ke gaane chala do"
        match = re.fullmatch(
            r"(?:youtube|spotify)\s+(?:par|pe|pr|on)\s+(.+?)\s+"
            r"(?:bajao|chalao|lagao|play|chala do|baja do|laga do)",
            command_core,
            re.IGNORECASE,
        )
        if match:
            platform = "spotify" if "spotify" in command_lower else "youtube"
            query = self._clean_music_query(match.group(1).strip())
            return {"type": "play_music", "query": query, "platform": platform}

        # 2. Query first: "arijit singh ke gaane youtube par chala do"
        match = re.fullmatch(
            r"(.+?)\s+(?:on\s+|in\s+)?(?:youtube|spotify)\s+(?:par|pe|pr|on)?\s*"
            r"(?:bajao|chalao|lagao|play|chala do|baja do|laga do)",
            command_core,
            re.IGNORECASE,
        )
        if match:
            platform = "spotify" if "spotify" in command_lower else "youtube"
            query = self._clean_music_query(match.group(1).strip())
            return {"type": "play_music", "query": query, "platform": platform}

        # 3. Action first: "play some haryanvi music on youtube", "play arijit singh on spotify"
        match = re.fullmatch(
            r"(?:play|play the song|chalao|bajao|lagao)\s+(?:some\s+)?(.+?)\s+"
            r"(?:on|in|par|pe)\s+(youtube|spotify)",
            command_core,
            re.IGNORECASE,
        )
        if match:
            platform = match.group(2).strip().lower()
            query = self._clean_music_query(match.group(1).strip())
            return {"type": "play_music", "query": query, "platform": platform}

        # 4. Action and song without explicit platform: "play arijit singh", "play haryanvi songs"
        match = re.fullmatch(r"^(?:play|chalao|bajao|lagao)\s+(?:some\s+)?(.+)$", command_core, re.IGNORECASE)
        if match and not any(k in command_lower for k in ["game", "video", "pause"]):
            platform = "youtube"
            if context and getattr(context, "last_music_platform", None):
                platform = context.last_music_platform
            query = self._clean_music_query(match.group(1).strip())
            return {"type": "play_music", "query": query, "platform": platform}

        # General Web search
        search_match = re.fullmatch(
            r"(?:search|google|find|look up|dhundo|dhoondo)\s+(?:for\s+)?(.+?)"
            r"(?:\s+(?:on|in|par|pe)\s+(?:google|the web|internet))?(?:\s+(?:karo|kar do))?$",
            command_core,
            re.IGNORECASE,
        )
        if search_match:
            query = search_match.group(1).strip()
            query = re.sub(r"\s+(?:on|in|par|pe)\s+(?:google|the web|internet)$", "", query, flags=re.IGNORECASE).strip()
            if query:
                return {"type": "search_web", "query": query}

        # Browser result navigation ("Open the second result", "second result kholo", "second wala kholo", "open that one")
        if command_lower in {
            "open the second result",
            "open second result",
            "the second result",
            "second result kholo",
            "second result",
            "second wala kholo",
        }:
            return {"type": "browser_open_result", "number": 2}

        if command_lower in {
            "open the first result",
            "open first result",
            "the first result",
            "first result kholo",
            "first result",
            "first wala kholo",
            "the first one",
            "open first search result",
        }:
            return {"type": "browser_open_result", "number": 1}

        if command_lower in {
            "open that one",
            "open that",
            "ye wala open karo",
            "ye wala kholo",
            "wo wala open karo",
            "wo wala kholo",
            "that one",
        }:
            return {"type": "browser_open_result", "number": 1}

        match = re.fullmatch(r"open (?:the )?(?:result )?(?:number )?([1-5])", command_lower)
        if match:
            return {"type": "browser_open_result", "number": int(match.group(1))}

        match = re.fullmatch(r"(?:open|show) (?:the )?result (?:about|for) (.+)", command_core, re.IGNORECASE)
        if match:
            return {"type": "browser_open_result_by_text", "text": match.group(1).strip()}

        # Browser navigation: "go back", "browser back", "wapas jao", "piche jao"
        if command_lower in {"go back", "browser back", "go back in browser", "back", "wapas jao", "piche jao"}:
            return {"type": "browser_back"}

        if command_lower in {"new tab", "open new tab", "create new tab"}:
            return {"type": "browser_new_tab"}

        if command_lower in {"close tab", "close this tab", "close current tab"}:
            return {"type": "browser_close_tab"}

        if command_lower in {"minimize window", "minimize this window", "minimize"}:
            return {"type": "minimize_window"}

        if command_lower in {"maximize window", "maximize this window", "maximize"}:
            return {"type": "maximize_window"}

        # Folders
        folder_patterns = [
            (r"^(open|show) downloads?( folder)?$", "downloads"),
            (r"^(open|show) documents?( folder)?$", "documents"),
            (r"^(open|show) desktop( folder)?$", "desktop"),
            (r"^(open|show) pictures?( folder)?$", "pictures"),
        ]
        for pattern, folder in folder_patterns:
            if re.fullmatch(pattern, command_lower):
                return {"type": "open_folder", "folder": folder}

        # Conversational greetings & status
        if command_lower in {"hello", "hi", "hey", "good morning", "good afternoon", "good evening"}:
            return {"type": "conversation", "response": "Hello! I'm Kritam. How can I help?"}

        if command_lower in {"how are you", "how are you doing"}:
            return {"type": "conversation", "response": "I'm doing good. How can I help?"}

        if command_lower in {"who are you", "what are you", "tell me about yourself", "what is kritam"}:
            return {
                "type": "conversation",
                "response": "I'm Kritam, your personal desktop assistant. I can open apps, search the web, manage folders, control media and help with everyday tasks.",
            }

        if command_lower in {"what can you do", "what can you do for me", "show me what you can do", "help"}:
            return {
                "type": "conversation",
                "response": "I can open apps and websites, search Google, open folders, take screenshots, control volume and media, remember information, and handle simple multi-step tasks.",
            }

        if command_lower in {"thanks", "thank you", "thank you kritam", "shukriya", "dhanyawad"}:
            return {"type": "conversation", "response": "You're welcome!"}

        if command_lower in {"what time is it", "what is the time", "kitne baje hain", "time kya hua hai"}:
            from datetime import datetime
            return {"type": "conversation", "response": datetime.now().strftime("It is %I:%M %p.")}

        return None

    def _clean_music_query(self, query: str) -> str:
        """Strip filler phrases and format proper name/query."""
        cleaned = re.sub(
            r"\b(?:ke\s+gaane|ke\s+song|songs|song|gaane|gana|music)\b",
            "",
            query,
            flags=re.IGNORECASE,
        ).strip()
        cleaned = re.sub(r"^[^\w]+|[^\w]+$", "", cleaned).strip()
        return cleaned.title() if cleaned else query.title()
