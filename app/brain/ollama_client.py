from brain.ai_provider import OllamaProvider


class OllamaClient:

    def __init__(self, model=None):
        self.provider = OllamaProvider(model=model)

    def ask(self, prompt):
        return self.provider.ask(prompt)

    def is_available(self):
        return self.provider.is_available()

    def status(self):
        return self.provider.status()
