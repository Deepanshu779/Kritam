"""Local account authentication for Kritam.

Accounts are stored only on the local computer. Passwords are never stored
as plaintext; PBKDF2-HMAC with a per-account salt is used for verification.
"""

import base64
import hashlib
import hmac
import json
import os


class LocalAuth:
    ITERATIONS = 300_000

    def __init__(self, path=None):
        self.path = path or os.path.join(
            os.path.expanduser("~"),
            ".kritam",
            "account.json",
        )

    def _load(self):
        try:
            if os.path.isfile(self.path):
                with open(self.path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}
        return {}

    def _save(self, data):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
            return True
        except OSError:
            return False

    def _hash_password(self, password, salt=None):
        salt = salt or os.urandom(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self.ITERATIONS,
            dklen=32,
        )
        return (
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(digest).decode("ascii"),
        )

    def account_exists(self):
        return bool(self._load().get("account"))

    def signup(self, name, email, password):
        name = name.strip()
        email = email.strip().lower()

        if not name:
            return False, "Please enter your name."
        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            return False, "Please enter a valid email address."
        if len(password) < 6:
            return False, "Password must be at least 6 characters."
        if self.account_exists():
            return False, "An account already exists on this computer."

        salt, digest = self._hash_password(password)
        data = {
            "account": {
                "name": name,
                "email": email,
                "salt": salt,
                "password_hash": digest,
            }
        }
        if not self._save(data):
            return False, "I couldn't save the account locally."
        return True, "Account created."

    def login(self, email, password):
        email = email.strip().lower()
        account = self._load().get("account")
        if not account:
            return False, "No Kritam account exists yet. Please sign up first."

        if email != account.get("email", "").lower():
            return False, "Email or password is incorrect."

        try:
            salt = base64.b64decode(account["salt"])
            expected = base64.b64decode(account["password_hash"])
            actual = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                self.ITERATIONS,
                dklen=32,
            )
        except (KeyError, ValueError, TypeError):
            return False, "The local account data is invalid."

        if not hmac.compare_digest(actual, expected):
            return False, "Email or password is incorrect."

        return True, {
            "name": account.get("name", "User"),
            "email": account.get("email", ""),
        }

    def current_account(self):
        account = self._load().get("account")
        if not account:
            return None
        return {
            "name": account.get("name", "User"),
            "email": account.get("email", ""),
        }
