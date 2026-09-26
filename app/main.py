import sys
from pathlib import Path

# Ensure the 'app' directory is always in sys.path
_app_dir = str(Path(__file__).resolve().parent)
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)


def main():
    if "--console" in sys.argv:
        from core.assistant import Kritam
        Kritam().start()
        return

    from ui.app import run
    raise SystemExit(run())


if __name__ == "__main__":
    main()
