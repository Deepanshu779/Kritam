"""Wake word detection module for Kritam assistant.

Provides a clean interface for detecting wake phrases such as 'Kritam',
'Hey Kritam', 'Hi Kritam', 'Okay Kritam', etc., and separating any trailing command.
"""

from dataclasses import dataclass
import re
from typing import Optional


@dataclass
class WakeWordResult:
    detected: bool
    matched_phrase: str = ""
    command_remainder: str = ""


class WakeWordDetector:
    """Detects wake phrases and extracts trailing commands from speech transcripts."""

    WAKE_PATTERN = re.compile(
        r"^(?:(?:hey|hi|hello|ok|okay|arre|namaste)?\s*kritam|kreetam|critam)[,.]?\s*",
        re.IGNORECASE,
    )

    EMBEDDED_WAKE_PATTERN = re.compile(
        r"\b(?:hey|hi|hello|ok|okay|arre|namaste)?\s*(?:kritam|kreetam|critam)\b[,.]?\s*",
        re.IGNORECASE,
    )

    def __init__(self, assistant_name: str = "Kritam"):
        self.assistant_name = assistant_name
        self._update_patterns()

    def set_assistant_name(self, name: str):
        """Update wake patterns when assistant name is changed."""
        self.assistant_name = name.strip()
        self._update_patterns()

    def _update_patterns(self):
        escaped = re.escape(self.assistant_name)
        self.wake_regex = re.compile(
            rf"\b(?:hey|hi|hello|ok|okay|arre|namaste)?\s*(?:{escaped}|kritam|kreetam|critam)\b[,.]?\s*",
            re.IGNORECASE,
        )

    def detect(self, text: str) -> WakeWordResult:
        """Check if transcript contains the wake phrase and extract command remainder."""
        if not text:
            return WakeWordResult(detected=False)

        match = self.wake_regex.search(text)
        if not match:
            return WakeWordResult(detected=False)

        matched_phrase = match.group(0).strip(" ,.!?")
        
        # Split text around match
        prefix = text[:match.start()].strip(" ,.!?")
        suffix = text[match.end():].strip(" ,.!?")

        remainder = f"{prefix} {suffix}".strip() if prefix else suffix

        return WakeWordResult(
            detected=True,
            matched_phrase=matched_phrase,
            command_remainder=remainder,
        )
