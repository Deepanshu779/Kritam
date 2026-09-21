import os


class ApplicationManager:

    def __init__(self):
        self.applications = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "chrome": "chrome.exe",
            "task manager": "taskmgr.exe",
            "file explorer": "explorer.exe",
            "settings": "ms-settings:",
        }

    def open_application(self, application_name):
        application_name = application_name.lower().strip()

        if application_name not in self.applications:
            return False

        try:
            os.startfile(self.applications[application_name])
            return True

        except (OSError, ValueError):
            return False

    def handle_open_application(self, intent):
        application = intent.get("application", "")
        return self.open_application(application)
