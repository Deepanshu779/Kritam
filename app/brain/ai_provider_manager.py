import os

from brain.ai_provider import OllamaProvider


class AIProviderManager:

    def __init__(self, provider=None):
        self.provider_name = provider or os.getenv("KRITAM_AI_PROVIDER", "ollama").lower()
        self.provider = self._create_provider(self.provider_name)

    def _create_provider(self, name):
        if name == "ollama":
            return OllamaProvider()
        return None

    def available(self):
        return self.provider is not None and self.provider.is_available()

    def ask(self, prompt):
        if not self.provider:
            return None
        return self.provider.ask(prompt)

    def status(self):
        if not self.provider:
            return {
                "provider": self.provider_name,
                "available": False,
                "reason": "Provider is not configured.",
            }
        return self.provider.status()

    def status_text(self):
        status = self.status()
        if not status.get("available"):
            return f"AI provider {status['provider']} is unavailable."
        model = status.get("model")
        if model and not status.get("model_available"):
            return f"{status['provider']} is running, but model {model} is not installed."
        return f"{status['provider']} is ready with {model}." if model else f"{status['provider']} is ready."
