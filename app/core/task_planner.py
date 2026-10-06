import re


class TaskPlanner:

    CONNECTORS = r"\s+(?:and then|then|after that|and|also)\s+"
    SEQUENTIAL_CONNECTORS = re.compile(
        r"\s+(?:and then|then|after that|uske baad|phir)\s+",
        re.IGNORECASE,
    )
    ACTION_ANYWHERE = re.compile(
        r"\b(?:open|launch|start|kholo|khol|close|band karo|search|google|find|look up|dhoondo|dhundo|play|chalao|bajao|lagao|take|capture|mute|volume|unmute|minimize|maximize|remember|forget)\b",
        re.IGNORECASE,
    )

    def split(self, text):
        text = text.strip()
        if not text:
            return []

        chunks = [c.strip(" ,.") for c in self.SEQUENTIAL_CONNECTORS.split(text) if c.strip(" ,.")]
        if not chunks:
            return []

        tasks = []
        for chunk in chunks:
            parts = re.split(r"\s+(?:and|aur|also)\s+", chunk, flags=re.IGNORECASE)
            if len(parts) <= 1:
                tasks.append(chunk)
                continue

            can_split = True
            for part in parts[1:]:
                clean_part = part.strip(" ,.")
                if not self.ACTION_ANYWHERE.search(clean_part):
                    can_split = False
                    break

            if can_split:
                for part in parts:
                    if part.strip(" ,."):
                        tasks.append(part.strip(" ,."))
            else:
                tasks.append(chunk)

        return tasks

    def describe(self, tasks):
        if not tasks:
            return "No steps."
        return " → ".join(f"{index + 1}. {task}" for index, task in enumerate(tasks))