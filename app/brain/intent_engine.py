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
- browser_open_result_by_text: type, text
- browser_back: type
- browser_new_tab: type
- browser_close_tab: type
- open_folder: type, folder
- take_screenshot: type
- memory_remember: type, key, value
- memory_summary: type
- memory_clear: type
- memory_recall: type, key
- memory_forget: type, key
- history_summary: type
- unknown: type

Browser rules:
- "open result 3" or "open the third result" -> browser_open_result.
- "open the result about Python" -> browser_open_result_by_text with text "Python".
- "go back" -> browser_back.
- "new tab" -> browser_new_tab.
- "close tab" -> browser_close_tab.
Never invent a result number or result title.

Recent context:
{history}

User: {text}

Return ONLY JSON.
"""
        response = self.llm.ask(prompt)
        intent = self._extract_json(response)
        return intent if intent is not None else {"type": "unknown"}
