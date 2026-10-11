"""Regression tests for filesystem access boundaries."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.security.computer_security import ComputerSecurityPolicy


class TestComputerSecurityPolicy(unittest.TestCase):
    def test_read_access_is_limited_to_user_directory(self):
        with tempfile.TemporaryDirectory() as user_home, tempfile.TemporaryDirectory() as outside:
            home = Path(user_home)
            policy = ComputerSecurityPolicy()
            with patch.object(Path, "home", return_value=home):
                allowed, _ = policy.allowed_read(home / "Documents" / "notes.txt")
                denied, reason = policy.allowed_read(Path(outside) / "system.ini")

        self.assertTrue(allowed)
        self.assertFalse(denied)
        self.assertIn("user folder", reason)

    def test_credentials_and_browser_data_are_protected(self):
        with tempfile.TemporaryDirectory() as user_home:
            home = Path(user_home)
            policy = ComputerSecurityPolicy()
            protected_paths = (
                home / ".ssh" / "id_ed25519",
                home / "AppData" / "Browser" / "Cookies",
                home / "token.json",
            )
            with patch.object(Path, "home", return_value=home):
                results = [policy.allowed_read(path)[0] for path in protected_paths]

        self.assertEqual(results, [False, False, False])

    def test_mutations_require_confirmation_and_user_path(self):
        with tempfile.TemporaryDirectory() as user_home, tempfile.TemporaryDirectory() as outside:
            home = Path(user_home)
            policy = ComputerSecurityPolicy()
            with patch.object(Path, "home", return_value=home):
                unconfirmed = policy.authorize("computer_delete_file", home / "notes.txt")
                outside_write = policy.authorize(
                    "computer_write_file",
                    Path(outside) / "notes.txt",
                    confirmed=True,
                )
                allowed = policy.authorize(
                    "computer_write_file",
                    home / "notes.txt",
                    confirmed=True,
                )

        self.assertFalse(unconfirmed[0])
        self.assertFalse(outside_write[0])
        self.assertTrue(allowed[0])


if __name__ == "__main__":
    unittest.main()

