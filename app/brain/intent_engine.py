import json

from ollama_client import OllamaClient


class IntentEngine:

    def __init__(self):
        self.llm = OllamaClient()

    def understand(self, text):

        prompt = f"""
Analyze the user's request and return ONLY valid JSON.

Possible intent types:

1. conversation
2. open_application
3. unknown

For an application request, identify the application name.

Examples:

User: Hello
Output:
{{"type": "conversation", "response": "Hello!"}}

User: How are you?
Output:
{{"type": "conversation", "response": "I'm doing good. How can I help?"}}

User: Open Notepad
Output:
{{"type": "open_application", "application": "notepad"}}

User: Please open the calculator
Output:
{{"type": "open_application", "application": "calculator"}}

User: {text}

Return ONLY JSON.
"""

        response = self.llm.ask(prompt)

        if not response:
            return {
                "type": "unknown"
            }

        try:
            return json.loads(response)

        except json.JSONDecodeError:
            return {
                "type": "unknown"
            }