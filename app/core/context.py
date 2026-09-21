class ConversationContext:

    def __init__(self, max_items=6):
        self.max_items = max_items
        self.history = []
        self.last_successful_intent = None

    def add_turn(self, user_text, intent=None, success=False):
        self.history.append({
            "user": user_text,
            "intent": intent,
            "success": success,
        })

        if len(self.history) > self.max_items:
            self.history = self.history[-self.max_items:]

        if success and intent:
            self.last_successful_intent = dict(intent)

    def recent_summary(self):
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

    def repeat_last(self):
        if not self.last_successful_intent:
            return None

        return dict(self.last_successful_intent)

    def last_intent_of_type(self, intent_type):
        for item in reversed(self.history):
            if item.get("success") and item.get("intent", {}).get("type") == intent_type:
                return dict(item["intent"])
        return None
