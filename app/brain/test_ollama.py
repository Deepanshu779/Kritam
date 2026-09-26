import sys
from pathlib import Path

# Ensure the 'app' directory is in sys.path
_app_dir = str(Path(__file__).resolve().parent.parent)
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

from brain.ollama_client import OllamaClient


def main():
    brain = OllamaClient()

    response = brain.ask(
        "Introduce yourself in one short sentence."
    )

    print("\nKritam's local AI:")
    print(response)


if __name__ == "__main__":
    main()