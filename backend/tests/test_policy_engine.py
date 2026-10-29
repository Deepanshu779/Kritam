import pytest
from app.schemas.action import ActionRequest, RiskLevel
from app.services.automation.policy_engine import policy_engine

def test_policy_risk_tiers():
    # Low risk
    risk, req_conf, _ = policy_engine.evaluate_risk("launch_app", "calculator")
    assert risk == RiskLevel.LOW
    assert req_conf is False

    # Opening a destination can send data to the remote service, so confirmation is required.
    risk, req_conf, _ = policy_engine.evaluate_risk("open_url", "https://google.com")
    assert risk == RiskLevel.MEDIUM
    assert req_conf is True

    risk, req_conf, _ = policy_engine.evaluate_risk("play_music", "a song")
    assert risk == RiskLevel.MEDIUM
    assert req_conf is True

    # Medium risk
    risk, req_conf, _ = policy_engine.evaluate_risk("create_file", "test.txt")
    assert risk == RiskLevel.MEDIUM
    assert req_conf is True

    # High risk
    risk, req_conf, _ = policy_engine.evaluate_risk("delete_file", "important.db")
    assert risk == RiskLevel.HIGH
    assert req_conf is True

def test_unimplemented_destructive_action_is_rejected():
    req = ActionRequest(action_type="delete_file", target="data.txt", confirmed=False)
    res = policy_engine.execute_action(req)
    assert res.success is False
    assert res.requires_confirmation is False
    assert "not implemented and was not run" in res.message

def test_file_inspection_requires_confirmation_and_stays_in_user_folder(tmp_path, monkeypatch):
    from pathlib import Path

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    note = home / "notes.txt"
    note.write_text("private note", encoding="utf-8")

    blocked = policy_engine.execute_action(ActionRequest(action_type="inspect_file", target=str(note)))
    assert blocked.success is False
    assert blocked.requires_confirmation is True

    allowed = policy_engine.execute_action(ActionRequest(action_type="inspect_file", target=str(note), confirmed=True))
    assert allowed.success is True
    assert allowed.output == "private note"

    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    rejected = policy_engine.execute_action(ActionRequest(action_type="inspect_file", target=str(outside), confirmed=True))
    assert rejected.success is False
    assert "only inside your user folder" in rejected.message

    risk, requires_confirmation, _ = policy_engine.evaluate_risk("inspect_file", str(note))
    assert risk == RiskLevel.MEDIUM
    assert requires_confirmation is True

def test_invalid_url_scheme_blocked():
    req = ActionRequest(action_type="open_url", target="javascript:alert(1)", confirmed=False)
    res = policy_engine.execute_action(req)
    assert res.success is False
    assert "Invalid or untrusted URL scheme" in res.message

def test_url_with_credentials_or_invalid_port_is_rejected():
    credential_url = policy_engine.execute_action(ActionRequest(action_type="open_url", target="https://trusted.example@attacker.example"))
    assert credential_url.success is False
    assert "Invalid or untrusted URL" in credential_url.message

    invalid_port = policy_engine.execute_action(ActionRequest(action_type="open_url", target="https://example.com:bad"))
    assert invalid_port.success is False
    assert "Invalid URL port" in invalid_port.message
