"""Persistent, validated application settings stored on the local machine."""

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

    def _load(self):
        try:
            if os.path.isfile(self.path):
                with open(self.path, "r", encoding="utf-8") as file:
                    loaded = json.load(file)
                if isinstance(loaded, dict):
                    self.data.update(
                        {key: value for key, value in loaded.items() if key in self.DEFAULTS}
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
        if key not in self.DEFAULTS:
            return False
        previous = self.data[key]
        self.data[key] = value
        if self.save():
            return True
        self.data[key] = previous
        return False

    def reset(self):
        previous = self.data
        self.data = dict(self.DEFAULTS)
        if self.save():
            return True
        self.data = previous
        return False
