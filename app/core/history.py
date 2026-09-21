import json
import os
from datetime import datetime


class CommandHistory:

    def __init__(self, path=None, max_items=200):
        self.path = path or os.path.join(
            os.path.expanduser("~"),
            ".kritam",
            "history.json",
        )
        self.max_items = max_items

    def add(self, text, intent, success):
        record = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "command": text,
            "intent": intent,
            "success": bool(success),
        }
        records = self.all()
        records.append(record)
        records = records[-self.max_items:]
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as file:
                json.dump(records, file, indent=2, ensure_ascii=False)
            return True
        except OSError as error:
            print(f"History save error: {error}")
            return False

    def all(self):
        try:
            if not os.path.isfile(self.path):
                return []
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def recent(self, count=5):
        return self.all()[-count:]

    def clear(self):
        try:
            if os.path.isfile(self.path):
                os.remove(self.path)
            return True
        except OSError:
            return False