import os
import subprocess
import time

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
        if self.provider is None:
            return False

        if self.provider.is_available():
            return True

        # Start the local Ollama service automatically when it is installed.
        # This keeps natural-language commands usable without requiring the
        # user to manually open a terminal first.
        if self.provider_name == "ollama":
            try:
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=creationflags,
                )
                for _ in range(12):
                    time.sleep(0.25)
                    if self.provider.is_available():
                        return True
            except (OSError, FileNotFoundError):
                pass

        return False

    def ask(self, prompt):
        if not self.provider:
            return None
        if not self.available():
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
