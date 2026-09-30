import sys
from pathlib import Path

_root_dir = str(Path(__file__).resolve().parent.parent)
_app_dir = str(Path(__file__).resolve().parent.parent / "app")
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)
