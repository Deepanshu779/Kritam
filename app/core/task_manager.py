class TaskManager:

    def __init__(self):
        self.current = None

    def start(self, command, total):
        self.current = {
            "command": command,
            "total": total,
            "completed": 0,
            "failed": 0,
            "status": "running",
        }

    def complete(self, success):
        if not self.current:
            return
        if success:
            self.current["completed"] += 1
        else:
            self.current["failed"] += 1

    def finish(self):
        if not self.current:
            return
        self.current["status"] = "completed" if self.current["failed"] == 0 else "completed_with_errors"

    def fail(self):
        if self.current:
            self.current["status"] = "failed"

    def status_text(self):
        if not self.current:
            return "No task is currently running."
        task = self.current
        return (
            f"Task status: {task['status']}. "
            f"{task['completed']} of {task['total']} steps completed, "
            f"{task['failed']} failed."
        )