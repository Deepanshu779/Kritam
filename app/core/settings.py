import json
import os


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
                    self.data.update(loaded)
        except (OSError, json.JSONDecodeError):
            self.data = dict(self.DEFAULTS)

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as file:
                json.dump(self.data, file, indent=2)
            return True
        except OSError as error:
            print(f"Settings save error: {error}")
            return False

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        if key not in self.DEFAULTS:
            return False
        self.data[key] = value
        return self.save()

    def reset(self):
        self.data = dict(self.DEFAULTS)
        return self.save()
