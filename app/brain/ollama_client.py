import ollama


class OllamaClient:

    def __init__(self, model="qwen2.5:7b"):
        self.model = model

    def ask(self, prompt):
        try:
            response = ollama.chat(
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

Do not claim to have performed an action unless the application
actually reports that the action succeeded.
""",
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return response["message"]["content"]

        except Exception as error:
            print(f"Ollama error: {error}")
            return None