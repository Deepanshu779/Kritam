"""Conversation context tracker for Kritam assistant.

Tracks recent conversation turns, entity references, and previous intents
to support conversational corrections, pronoun resolution ("it", "that"),
and sequential multi-turn dialogue.
"""

from typing import Any, Dict, List, Optional


class ConversationContext:
    """Maintains dialog context and entity references across multiple turns."""

    def __init__(self, max_items: int = 8):
        self.max_items = max_items
        self.history: List[Dict[str, Any]] = []
        self.last_successful_intent: Optional[Dict[str, Any]] = None
        self.last_application: Optional[str] = None
        self.last_website: Optional[str] = None
        self.last_search_query: Optional[str] = None
        self.last_music_query: Optional[str] = None
        self.last_music_platform: Optional[str] = None

    def add_turn(self, user_text: str, intent: Optional[Dict[str, Any]] = None, success: bool = False):
        """Record a completed conversation turn."""
        self.history.append({
            "user": user_text,
            "intent": intent,
            "success": success,
        })

        if len(self.history) > self.max_items:
            self.history = self.history[-self.max_items:]

        if success and intent:
            self.last_successful_intent = dict(intent)
            itype = intent.get("type")
            if itype == "open_application":
                self.last_application = intent.get("application")
            elif itype == "open_website":
                self.last_website = intent.get("website")
            elif itype in {"search_web", "browser_search"}:
                self.last_search_query = intent.get("query")
            elif itype == "play_music":
                self.last_music_query = intent.get("query")
                self.last_music_platform = intent.get("platform", "youtube")

    def recent_summary(self) -> str:
        """Formatted summary of recent turns for LLM prompt context."""
        if not self.history:
            return "No previous conversation."

        lines = []
        for item in self.history[-4:]:
            intent = item.get("intent") or {}
            lines.append(
                f"User: {item['user']} | Intent: {intent.get('type', 'unknown')} "
                f"| Success: {item.get('success', False)}"
            )

        return "\n".join(lines)

    def repeat_last(self) -> Optional[Dict[str, Any]]:
        """Return the last successfully executed intent."""
        if not self.last_successful_intent:
            return None
        return dict(self.last_successful_intent)

    def last_intent_of_type(self, intent_type: str) -> Optional[Dict[str, Any]]:
        """Find the most recent successful intent matching a specific type."""
        for item in reversed(self.history):
            if item.get("success") and item.get("intent", {}).get("type") == intent_type:
                return dict(item["intent"])
        return None

    def get_last_intent(self) -> Optional[Dict[str, Any]]:
        """Return the most recent intent regardless of success."""
        if not self.history:
            return None
        return self.history[-1].get("intent")
