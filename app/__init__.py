import sys
from pathlib import Path

# Ensure the 'app' directory is always in sys.path so submodules can import each other directly
_app_dir = str(Path(__file__).resolve().parent)
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)
