"""Persistent application settings stored on the local machine."""

import json
import os
import tempfile


class Settings:
    DEFAULTS = {
        "assistant_name": "Kritam",
        "language": "en",
        "voice_rate": 170,
        "auto_start_browser": False,
        "wake_word_enabled": True,
        "start_with_windows": False,
    }

    def __init__(self, path=None):
        self.path = path or os.path.join(
            os.path.expanduser("~"),
            ".kritam",
            "settings.json",
        )
        self.data = dict(self.DEFAULTS)
        self._load()

    @classmethod
    def _is_valid(cls, key, value):
        if key not in cls.DEFAULTS:
            return False
        if key in {"assistant_name", "language"}:
            return isinstance(value, str) and bool(value.strip()) and len(value) <= 80
        if key == "voice_rate":
            return isinstance(value, int) and not isinstance(value, bool) and 80 <= value <= 300
        return isinstance(value, bool)

    def _load(self):
        try:
            if os.path.isfile(self.path):
                with open(self.path, "r", encoding="utf-8") as file:
                    loaded = json.load(file)
                if isinstance(loaded, dict):
                    self.data.update(
                        {
                            key: value
                            for key, value in loaded.items()
                            if self._is_valid(key, value)
                        }
                    )
        except (OSError, json.JSONDecodeError):
            self.data = dict(self.DEFAULTS)

    def save(self):
        directory = os.path.dirname(os.path.abspath(self.path))
        temporary_path = None
        try:
            os.makedirs(directory, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=directory,
                prefix=".settings-",
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary_path = file.name
                json.dump(self.data, file, indent=2, ensure_ascii=False)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.path)
            return True
        except OSError as error:
            print(f"Settings save error: {error}")
            if temporary_path:
                try:
                    os.unlink(temporary_path)
                except OSError:
                    pass
            return False

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        return self.update({key: value})

    def update(self, values):
        """Persist a group of settings as one validated, atomic change."""
        if not isinstance(values, dict) or any(
            not self._is_valid(key, value) for key, value in values.items()
        ):
            return False
        previous = dict(self.data)
        self.data.update(values)
        if self.save():
            return True
        self.data = previous
        return False

    def reset(self):
        previous = self.data
        self.data = dict(self.DEFAULTS)
        if self.save():
            return True
        self.data = previous
        return False


