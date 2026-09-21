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
        text = re.sub(r"^\s*\`\`\`(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*\`\`\`\s*$", "", text)

        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end > start:
            text = text[start:end + 1]

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return None

        return data if isinstance(data, dict) else None

    def understand(self, text):
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

        prompt = f"""
Analyze the user's request and return ONLY one valid JSON object.

Allowed intent types:

1. conversation
   - Fields: type, response

2. open_application
   - Launch a desktop application.
   - Fields: type, application

3. open_website
   - Supported websites: youtube, google, github, gmail.
   - Fields: type, website

4. search_web
   - Fields: type, query

5. open_folder
   - Supported folders: downloads, documents, desktop, pictures.
   - Fields: type, folder

6. take_screenshot
   - Fields: type

7. unknown
   - Fields: type

Examples:

User: Hello
Output: {{"type":"conversation","response":"Hello! How can I help?"}}

User: How are you?
Output: {{"type":"conversation","response":"I'm doing good. How can I help?"}}

User: Open Chrome
Output: {{"type":"open_application","application":"chrome"}}

User: Open YouTube
Output: {{"type":"open_website","website":"youtube"}}

User: Search the web for Python decorators
Output: {{"type":"search_web","query":"Python decorators"}}

User: Open my Downloads folder
Output: {{"type":"open_folder","folder":"downloads"}}

User: Take a screenshot
Output: {{"type":"take_screenshot"}}

User: {text}

Return ONLY JSON.
"""

        response = self.llm.ask(prompt)
        intent = self._extract_json(response)

        if intent is None:
            return {"type": "unknown"}

        return intent
