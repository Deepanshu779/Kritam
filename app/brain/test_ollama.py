from ollama_client import OllamaClient


def main():
    brain = OllamaClient()

    response = brain.ask(
        "Introduce yourself in one short sentence."
    )

    print("\nKritam's local AI:")
    print(response)


if __name__ == "__main__":
    main()