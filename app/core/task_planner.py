import re


class TaskPlanner:

    CONNECTORS = r"\s+(?:and then|then|after that|and|also)\s+"

    def split(self, text):
        text = text.strip()
        if not text:
            return []

        parts = re.split(self.CONNECTORS, text, flags=re.IGNORECASE)
        return [part.strip(" ,.") for part in parts if part.strip(" ,.")]

    def describe(self, tasks):
        if not tasks:
            return "No steps."
        return " → ".join(f"{index + 1}. {task}" for index, task in enumerate(tasks))