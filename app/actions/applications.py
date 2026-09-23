import os
import shutil
import subprocess


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

    def _chrome_candidates(self):
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        program_files = os.environ.get("PROGRAMFILES", "")
        program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "")

        return [
            shutil.which("chrome.exe"),
            os.path.join(local_app_data, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(program_files_x86, "Google", "Chrome", "Application", "chrome.exe"),
        ]

    def open_application(self, application_name):
        application_name = application_name.lower().strip()

        if application_name not in self.applications:
            return False

        target = self.applications[application_name]

        try:
            if application_name == "chrome":
                for candidate in self._chrome_candidates():
                    if candidate and os.path.isfile(candidate):
                        subprocess.Popen([candidate], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        return True
                return False

            if target == "ms-settings:":
                os.startfile(target)
                return True

            executable = shutil.which(target) or target
            subprocess.Popen([executable], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True

        except (OSError, ValueError, subprocess.SubprocessError):
            return False

    def handle_open_application(self, intent):
        application = intent.get("application", "")
        return self.open_application(application)
