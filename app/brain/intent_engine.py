import json
import re

from brain.ollama_client import OllamaClient


class IntentEngine:

    def __init__(self):
        self.llm = OllamaClient()

    def _extract_json(self, response):
        if not response:
            return None

        text = response.strip()
        fence = chr(96) * 3
        text = text.replace(fence + "json", "").replace(fence, "").strip()

        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end > start:
            text = text[start:end + 1]

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return None

        return data if isinstance(data, dict) else None

    def understand(self, text, context=None):
        command = text.lower().strip()

        aliases = {
            "open notepad": ("open_application", "notepad"),
            "open notebook": ("open_application", "notepad"),
            "open note": ("open_application", "notepad"),
            "open text editor": ("open_application", "notepad"),
            "open text pad": ("open_application", "notepad"),
            "open calculator": ("open_application", "calculator"),
            "open calc": ("open_application", "calculator"),
            "open paint": ("open_application", "paint"),
            "open chrome": ("open_application", "chrome"),
            "start chrome": ("open_application", "chrome"),
            "open youtube": ("open_website", "youtube"),
            "open google": ("open_website", "google"),
            "open github": ("open_website", "github"),
            "open gmail": ("open_website", "gmail"),
        }

        if command in aliases:
            intent_type, value = aliases[command]
            key = "application" if intent_type == "open_application" else "website"
            return {"type": intent_type, key: value}

        history = context.recent_summary() if context else "No previous conversation."

        prompt = f"""
Analyze the user's request and return ONLY one valid JSON object.

Allowed intent types:

1. conversation
   - Fields: type, response

2. open_application
   - Fields: type, application

3. open_website
   - Supported websites: youtube, google, github, gmail.
   - Fields: type, website

4. search_web
   - Fields: type, query

5. browser_search
   - Fields: type, query
   - Use when the user explicitly asks Kritam to search using the
     controlled browser and display or inspect search results.

6. browser_open_first_result
   - Fields: type
   - Use when the user asks to open the first result from the current
     browser search.

7. open_folder
   - Supported folders: downloads, documents, desktop, pictures.
   - Fields: type, folder

8. take_screenshot
   - Fields: type

9. unknown
   - Fields: type

Recent conversation context:
{history}

Use recent context only when the current request refers to something
previously discussed. Do not invent details.

User: {text}

Return ONLY JSON.
"""

        response = self.llm.ask(prompt)
        intent = self._extract_json(response)

        if intent is None:
            return {"type": "unknown"}

        return intent
