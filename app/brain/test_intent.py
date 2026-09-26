import sys
from pathlib import Path

# Ensure the 'app' directory is in sys.path
_app_dir = str(Path(__file__).resolve().parent.parent)
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

from brain.intent_engine import IntentEngine


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