"""Safe Windows computer access primitives for Kritam.

No arbitrary shell execution is exposed here. Every filesystem operation is
checked by ComputerSecurityPolicy before it is performed.
"""

import os
import shutil
import subprocess
from pathlib import Path

from security.computer_security import ComputerSecurityPolicy


class ComputerManager:
    def __init__(self):
        self.security = ComputerSecurityPolicy()

    def _path(self, value):
        return Path(os.path.expandvars(os.path.expanduser(str(value)))).resolve()

    def list_directory(self, path):
        target = self._path(path or Path.home())
        ok, _ = self.security.allowed_read(target)
        if not ok or not target.is_dir():
            return None
        try:
            return [
                {
                    "name": item.name,
                    "path": str(item),
                    "type": "folder" if item.is_dir() else "file",
                }
                for item in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            ]
        except OSError:
            return None

    def read_file(self, path, max_bytes=262144):
        target = self._path(path)
        ok, _ = self.security.allowed_read(target)
        if not ok or not target.is_file():
            return None
        try:
            with target.open("r", encoding="utf-8", errors="replace") as handle:
                return handle.read(max_bytes)
        except (OSError, UnicodeError):
            return None

    def open_path(self, path):
        target = self._path(path)
        ok, _ = self.security.allowed_read(target)
        if not ok or not target.exists():
            return False
        try:
            os.startfile(str(target))
            return True
        except (OSError, ValueError):
            return False

    def launch_application(self, executable):
        # Application paths are resolved by the caller/registry. Never accept
        # a shell command or command-line string here.
        if not executable or any(ch in str(executable) for ch in "&|<>"):
            return False
        try:
            subprocess.Popen([str(executable)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except (OSError, ValueError, subprocess.SubprocessError):
            return False

    def create_folder(self, path, confirmed=False):
        target = self._path(path)
        ok, _ = self.security.authorize("computer_create_folder", target, confirmed)
        if not ok:
            return False
        try:
            target.mkdir(parents=True, exist_ok=True)
            return True
        except OSError:
            return False

    def write_file(self, path, content, confirmed=False):
        target = self._path(path)
        ok, _ = self.security.authorize("computer_write_file", target, confirmed)
        if not ok:
            return False
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(content), encoding="utf-8")
            return True
        except OSError:
            return False

    def copy_file(self, source, destination, confirmed=False):
        src = self._path(source)
        dst = self._path(destination)
        ok1, _ = self.security.authorize("computer_copy_file", dst, confirmed)
        ok2, _ = self.security.allowed_read(src)
        if not ok1 or not ok2 or not src.is_file():
            return False
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return True
        except OSError:
            return False

    def move_file(self, source, destination, confirmed=False):
        src = self._path(source)
        dst = self._path(destination)
        ok1, _ = self.security.authorize("computer_move_file", dst, confirmed)
        ok2, _ = self.security.allowed_read(src)
        if not ok1 or not ok2 or not src.exists():
            return False
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            return True
        except OSError:
            return False

    def delete_file(self, path, confirmed=False):
        target = self._path(path)
        ok, _ = self.security.authorize("computer_delete_file", target, confirmed)
        if not ok or not target.exists():
            return False
        try:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            return True
        except OSError:
            return False

    def handle(self, intent):
        action = intent.get("type")
        confirmed = bool(intent.get("confirmed", False))

        if action == "computer_list_directory":
            return self.list_directory(intent.get("path") or str(Path.home())) is not None
        if action == "computer_read_file":
            return self.read_file(intent.get("path")) is not None
        if action == "computer_open_path":
            return self.open_path(intent.get("path", ""))
        if action == "computer_create_folder":
            return self.create_folder(intent.get("path", ""), confirmed)
        if action == "computer_write_file":
            return self.write_file(intent.get("path", ""), intent.get("content", ""), confirmed)
        if action == "computer_copy_file":
            return self.copy_file(intent.get("source", ""), intent.get("destination", ""), confirmed)
        if action == "computer_move_file":
            return self.move_file(intent.get("source", ""), intent.get("destination", ""), confirmed)
        if action == "computer_delete_file":
            return self.delete_file(intent.get("path", ""), confirmed)
        return False
