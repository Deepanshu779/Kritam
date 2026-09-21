import re


class TaskPlanner:

    def split(self, text):
        text = text.strip()
        if not text:
            return []

        parts = re.split(
            r"\s+(?:and then|then|after that|and)\s+",
            text,
            flags=re.IGNORECASE,
        )
        return [part.strip(" ,.") for part in parts if part.strip(" ,.")]