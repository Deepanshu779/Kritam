import os
from abc import ABC, abstractmethod


class AIProvider(ABC):

    name = "unknown"

    @abstractmethod
    def is_available(self):
        raise NotImplementedError

    @abstractmethod
    def ask(self, prompt):
        raise NotImplementedError

    def status(self):
        return {
            "provider": self.name,
            "available": self.is_available(),
        }


class OllamaProvider(AIProvider):

    name = "ollama"

    def __init__(self, model=None):
        self.model = model or os.getenv("KRITAM_OLLAMA_MODEL", "qwen2.5:7b")

    def _client(self):
        import ollama
        return ollama

    def is_available(self):
        try:
            self._client().list()
            return True
        except Exception:
            return False

    def model_available(self):
        try:
            response = self._client().list()
            models = response.get("models", []) if isinstance(response, dict) else getattr(response, "models", [])
            names = []
            for item in models or []:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("model")
                else:
                    name = getattr(item, "model", None) or getattr(item, "name", None)
                if name:
                    names.append(name)
            return self.model in names or any(name.split(":")[0] == self.model.split(":")[0] for name in names)
        except Exception:
            return False

    def ask(self, prompt):
        try:
            response = self._client().chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """
You are Kritam, a personal desktop AI assistant.

You are not Qwen and you must never introduce yourself as Qwen.

Your personality is:
- Natural and friendly
- Calm and helpful
- Conversational rather than robotic
- Concise when a short answer is enough
- Comfortable speaking in English, Hindi, and Hinglish
- Professional when the user is doing technical or academic work
- Friendly like a trusted companion, but never overly emotional or childish

Your primary purpose is to help the user with their computer,
information, productivity, and everyday tasks.

When returning structured intent JSON, follow the user's requested
schema exactly and return valid JSON only.

Do not claim to have performed an action unless the application
actually reports that the action succeeded.
""",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return response["message"]["content"]
        except Exception as error:
            print(f"Ollama error: {error}")
            return None

    def status(self):
        available = self.is_available()
        return {
            "provider": self.name,
            "available": available,
            "model": self.model,
            "model_available": self.model_available() if available else False,
        }
