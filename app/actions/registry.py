class ActionRegistry:

    def __init__(self):
        self._actions = {}

    def register(self, action_type, handler):
        if not action_type or not callable(handler):
            raise ValueError("Invalid action registration")

        self._actions[action_type] = handler

    def execute(self, intent):
        if not isinstance(intent, dict):
            return False

        action_type = intent.get("type")
        handler = self._actions.get(action_type)

        if handler is None:
            return False

        return bool(handler(intent))

    def has_action(self, action_type):
        return action_type in self._actions
