import os
import subprocess
import shutil
from pathlib import Path

KNOWN_APPS: dict[str, list[str]] = {
    "code": ["code", "code.cmd", "code.exe"],
    "vs code": ["code", "code.cmd", "code.exe"],
    "vscode": ["code", "code.cmd", "code.exe"],
    "visual studio code": ["code", "code.cmd", "code.exe"],
    "chrome": ["chrome", "chrome.exe"],
    "google chrome": ["chrome", "chrome.exe"],
    "firefox": ["firefox", "firefox.exe"],
    "edge": ["msedge", "msedge.exe"],
    "calculator": ["calc.exe", "calc"],
    "calc": ["calc.exe", "calc"],
    "notepad": ["notepad.exe", "notepad"],
    "explorer": ["explorer.exe", "explorer"],
    "file explorer": ["explorer.exe", "explorer"],
    "paint": ["mspaint.exe", "mspaint"],
    "terminal": ["wt.exe", "powershell.exe"],
    "powershell": ["powershell.exe"],
    "spotify": ["spotify.exe", "spotify"],
    "settings": ["ms-settings:"]
}

class AppLauncher:
    """Safe Windows application launcher."""

    @staticmethod
    def resolve_app(target: str) -> str | None:
        target_clean = target.lower().strip()
        candidates = KNOWN_APPS.get(target_clean)
        if candidates:
            for cmd in candidates:
                if cmd.endswith(":"): # Windows URI protocol
                    return cmd
                resolved = shutil.which(cmd)
                if resolved:
                    return resolved
            return candidates[0] # Return default candidate name for start-process

        # If not in known list, check if executable exists on PATH
        resolved = shutil.which(target_clean)
        if resolved:
            return resolved

        return None

    @classmethod
    def launch(cls, target: str) -> tuple[bool, str]:
        """Launch application safely without shell=True execution."""
        resolved = cls.resolve_app(target)
        if not resolved:
            return False, f"Could not find or resolve application '{target}'. Ensure it is installed and registered on Windows."

        try:
            if resolved.endswith(":"):
                # Protocol handler like ms-settings:
                os.startfile(resolved)
                return True, f"Opened Windows {target.title()} successfully."

            # Use subprocess without shell injection
            subprocess.Popen([resolved], shell=False)
            return True, f"Successfully launched {target.title()}."
        except Exception as e:
            return False, f"Failed to launch '{target}': {str(e)}"
