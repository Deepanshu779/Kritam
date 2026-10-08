"""Security policy for Kritam's computer-control layer.

The policy deliberately separates:
- safe computer access (read/list/open/launch)
- protected locations (never accessed by the agent)
- mutating/destructive operations (explicit confirmation required)

This is a guardrail, not a sandbox. The agent must still route every computer
operation through this policy; it must never execute arbitrary shell commands.
"""

import os
from pathlib import Path


class ComputerSecurityPolicy:
    """Central allow/deny policy for computer and filesystem operations."""

    PROTECTED_NAMES = {
        ".ssh", ".aws", ".azure", ".gnupg", "credentials", "secrets",
    }

    PROTECTED_PREFIXES = (
        os.path.normcase(os.environ.get("WINDIR", r"C:\Windows")),
        os.path.normcase(os.environ.get("PROGRAMFILES", r"C:\Program Files")),
        os.path.normcase(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")),
        os.path.normcase(os.environ.get("PROGRAMDATA", r"C:\ProgramData")),
    )

    MUTATING_ACTIONS = {
        "computer_write_file",
        "computer_create_folder",
        "computer_move_file",
        "computer_copy_file",
        "computer_delete_file",
    }

    def _resolved(self, value):
        try:
            return Path(os.path.expandvars(os.path.expanduser(str(value)))).resolve()
        except (OSError, RuntimeError, ValueError):
            return None

    def is_protected(self, path):
        resolved = self._resolved(path)
        if resolved is None:
            return True

        normalized = os.path.normcase(str(resolved))
        parts = {p.lower() for p in resolved.parts}

        if any(normalized == prefix or normalized.startswith(prefix + os.sep)
               for prefix in self.PROTECTED_PREFIXES):
            return True

        if any(name in parts for name in self.PROTECTED_NAMES):
            return True

        # Never let computer control modify Kritam's own repository metadata.
        if ".git" in parts:
            return True

        return False

    def is_user_path(self, path):
        resolved = self._resolved(path)
        home = self._resolved(Path.home())
        if resolved is None or home is None:
            return False
        try:
            resolved.relative_to(home)
            return True
        except ValueError:
            return False

    def authorize(self, action_type, path=None, confirmed=False):
        if action_type in self.MUTATING_ACTIONS:
            if not confirmed:
                return False, "This change requires explicit confirmation."
            if path and self.is_protected(path):
                return False, "That location is protected."
            if path and not self.is_user_path(path):
                return False, "I can only modify files inside your user folder."
            return True, ""

        if path and self.is_protected(path):
            return False, "That location is protected."

        return True, ""

    def allowed_read(self, path):
        ok, reason = self.authorize("computer_read", path=path)
        return ok, reason
