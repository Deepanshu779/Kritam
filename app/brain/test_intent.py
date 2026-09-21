from intent_engine import IntentEngine


def main():

    engine = IntentEngine()

    tests = [
        "Hello Kritam",
        "How are you?",
        "Open Notepad",
        "Please open the calculator"
    ]

    for text in tests:

        print(f"\nUser: {text}")

        result = engine.understand(text)

        print("Intent:")
        print(result)


if __name__ == "__main__":
    main()