import pytest
from fastapi import HTTPException

from app.core import security


def test_missing_token_is_only_allowed_in_development_or_test(monkeypatch):
    monkeypatch.setattr(security.settings, "AUTH_TOKEN", "")
    monkeypatch.setattr(security.settings, "ENVIRONMENT", "development")
    assert security.verify_auth_token(None) is True

    monkeypatch.setattr(security.settings, "ENVIRONMENT", "production")
    with pytest.raises(HTTPException) as exc:
        security.verify_auth_token(None)
    assert exc.value.status_code == 503


def test_session_token_must_match(monkeypatch):
    monkeypatch.setattr(security.settings, "AUTH_TOKEN", "session-token")
    monkeypatch.setattr(security.settings, "ENVIRONMENT", "production")
    assert security.verify_auth_token("session-token") is True
    with pytest.raises(HTTPException) as exc:
        security.verify_auth_token("wrong-token")
    assert exc.value.status_code == 401
