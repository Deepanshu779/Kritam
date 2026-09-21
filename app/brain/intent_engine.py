import json

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
        history = context.recent_summary() if context else "No previous conversation."
        prompt = f"""
Analyze the user's request and return ONLY one valid JSON object.

Allowed intent types:
- conversation: type, response
- open_application: type, application
- open_website: type, website
- search_web: type, query
- browser_search: type, query
- browser_open_result: type, number (1-5)
- browser_back: type
- open_folder: type, folder
- take_screenshot: type
- unknown: type

For browser_open_result, use it when the user asks to open a numbered
search result such as "open result 3" or "open the third result".
For browser_back, use it for "go back" or equivalent browser navigation.

Recent context:
{history}

User: {text}

Return ONLY JSON.
"""
        response = self.llm.ask(prompt)
        intent = self._extract_json(response)
        return intent if intent is not None else {"type": "unknown"}
