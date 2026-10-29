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
    "spotify": ["spotify:"],
    "settings": ["ms-settings:"]
}

class AppLauncher:
    """Safe Windows application launcher."""

    @staticmethod
    def _resolve_chrome() -> str | None:
        """Resolve Chrome from PATH, standard Windows locations, or App Paths."""
        found = shutil.which("chrome.exe") or shutil.which("chrome")
        if found:
            return found
        if os.name != "nt":
            return None

        roots = [os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"),
                 os.environ.get("LOCALAPPDATA")]
        relative = [
            ("Google", "Chrome", "Application", "chrome.exe"),
        ]
        for root in filter(None, roots):
            for parts in relative:
                candidate = Path(root).joinpath(*parts)
                if candidate.is_file():
                    return str(candidate)

        try:
            import winreg
            for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                for subkey in (
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
                ):
                    try:
                        with winreg.OpenKey(hive, subkey) as key:
                            candidate, _ = winreg.QueryValueEx(key, None)
                            if candidate and Path(candidate).is_file():
                                return candidate
                    except OSError:
                        continue
        except (ImportError, OSError):
            pass
        return None

    @staticmethod
    def _resolve_vscode() -> str | None:
        found = shutil.which("code.exe")
        if found:
            return found
        if os.name != "nt":
            return None
        roots = [os.environ.get("LOCALAPPDATA"), os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)")]
        for root in filter(None, roots):
            for relative in (
                Path("Programs") / "Microsoft VS Code" / "Code.exe",
                Path("Microsoft VS Code") / "Code.exe",
            ):
                candidate = Path(root) / relative
                if candidate.is_file():
                    return str(candidate)
        return None

    @staticmethod
    def resolve_app(target: str) -> str | None:
        target_clean = target.lower().strip()
        if target_clean in ("chrome", "google chrome"):
            return AppLauncher._resolve_chrome()
        if target_clean in ("code", "vs code", "vscode", "visual studio code"):
            return AppLauncher._resolve_vscode()
        candidates = KNOWN_APPS.get(target_clean)
        if candidates:
            for cmd in candidates:
                if cmd.endswith(":"): # Windows URI protocol
                    return cmd
                resolved = shutil.which(cmd)
                if resolved:
                    return resolved
            return candidates[0] # Return default candidate name for start-process

        # Only registered application names are launchable. Do not turn an
        # arbitrary model-produced string into a PATH executable.
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
