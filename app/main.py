import sys


def main():
    if "--console" in sys.argv:
        from core.assistant import Kritam
        Kritam().start()
        return

    from ui.app import run
    raise SystemExit(run())


if __name__ == "__main__":
    main()
