import json

from brain.ai_provider_manager import AIProviderManager


class IntentEngine:

    def __init__(self):
        self.ai = AIProviderManager()

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

Language and conversation rules:
- Detect the language and style of the user's message automatically.
- Understand natural speech, incomplete phrases, corrections, filler words, code-switching and mixed-language speech.
- The user may switch languages between turns without changing settings.
- For conversation intents, respond naturally in the same language or mixed-language style used by the user.
- Keep spoken responses concise and human, usually one or two sentences.
- Do not force English when the user is speaking another language.
- Preserve names, song titles, application names, URLs and search terms exactly when useful.
- Resolve natural references such as "it", "that", "the first one", "the second result", "play that", "open it", and "go back" from recent conversation context when the context makes the reference clear.
- If a reference cannot be resolved safely, return {{"type":"conversation","response":"Could you clarify what you mean?"}} instead of inventing details.
- Treat "actually", "wait", "no", "instead", "I mean", and similar phrases as natural corrections to the previous request.
- Never claim an action was completed unless the application reports success.

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
- play_music: type, query, platform (platform must be youtube or spotify)
- open_folder: type, folder
- take_screenshot: type
- volume_up: type
- volume_down: type
- volume_mute: type
- media_play_pause: type
- minimize_window: type
- maximize_window: type
- memory_remember: type, key, value
- memory_summary: type
- memory_clear: type
- memory_recall: type, key
- memory_forget: type, key
- history_summary: type
- task_status: type
- ai_status: type
- set_setting: type, key, value
- unknown: type

Browser rules:
- "open result 3" or "open the third result" -> browser_open_result.
- "open the result about Python" -> browser_open_result_by_text with text "Python".
- "go back" -> browser_back.
- "new tab" -> browser_new_tab.
- "close tab" -> browser_close_tab.
Never invent a result number or result title.\n\nComputer security rules:\n- Never generate execute_shell or run_command intents.\n- Reading/listing/opening user files is allowed only when the requested path is clear.\n- Any create, write, copy, move, or delete operation must set confirmed=false unless the user explicitly and unambiguously confirms that exact change in the current turn.\n- Never request or expose passwords, tokens, private keys, browser cookies, credential stores, or protected system files.\n- If the user asks for broad computer control, choose a specific safe operation instead of inventing a shell command.

Recent context:
{history}

User: {text}

Return ONLY JSON.
"""
        response = self.ai.ask(prompt)
        intent = self._extract_json(response)
        return intent if intent is not None else {"type": "unknown"}
