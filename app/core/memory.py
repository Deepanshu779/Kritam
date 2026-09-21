import json
import os


class PersistentMemory:

    def __init__(self, path=None, max_items=100):
        self.path = path or os.path.join(
            os.path.expanduser("~"),
            ".kritam",
            "memory.json",
        )
        self.max_items = max_items
        self.data = {"facts": {}, "notes": []}
        self._load()

    def _load(self):
        try:
            if os.path.isfile(self.path):
                with open(self.path, "r", encoding="utf-8") as file:
                    loaded = json.load(file)
                if isinstance(loaded, dict):
                    self.data.update(loaded)
        except (OSError, json.JSONDecodeError):
            self.data = {"facts": {}, "notes": []}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as file:
                json.dump(self.data, file, indent=2, ensure_ascii=False)
            return True
        except OSError as error:
            print(f"Memory save error: {error}")
            return False

    def remember(self, key, value):
        key = key.strip().lower()
        value = value.strip()
        if not key or not value:
            return False
        self.data["facts"][key] = value
        return self._save()

    def recall(self, key):
        return self.data["facts"].get(key.strip().lower())

    def find(self, phrase):
        phrase = phrase.strip().lower()
        if not phrase:
            return None
        for key, value in self.data["facts"].items():
            if phrase in key or phrase in value.lower():
                return {"key": key, "value": value}
        return None

    def all_facts(self):
        return dict(self.data.get("facts", {}))

    def add_note(self, note):
        note = note.strip()
        if not note:
            return False
        self.data.setdefault("notes", []).append(note)
        self.data["notes"] = self.data["notes"][-self.max_items:]
        return self._save()

    def clear(self):
        self.data = {"facts": {}, "notes": []}
        return self._save()

    def summary(self):
        facts = self.all_facts()
        notes = self.data.get("notes", [])
        if not facts and not notes:
            return "I don't have any saved memories yet."

        lines = []
        for key, value in facts.items():
            lines.append(f"{key}: {value}")
        for note in notes[-10:]:
            lines.append(f"note: {note}")
        return "\n".join(lines)
