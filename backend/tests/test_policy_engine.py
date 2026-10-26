import pytest
from app.schemas.action import ActionRequest, RiskLevel
from app.services.automation.policy_engine import policy_engine

def test_policy_risk_tiers():
    # Low risk
    risk, req_conf, _ = policy_engine.evaluate_risk("launch_app", "calculator")
    assert risk == RiskLevel.LOW
    assert req_conf is False

    # Low risk safe URL
    risk, req_conf, _ = policy_engine.evaluate_risk("open_url", "https://google.com")
    assert risk == RiskLevel.LOW
    assert req_conf is False

    # Medium risk
    risk, req_conf, _ = policy_engine.evaluate_risk("create_file", "test.txt")
    assert risk == RiskLevel.MEDIUM
    assert req_conf is True

    # High risk
    risk, req_conf, _ = policy_engine.evaluate_risk("delete_file", "important.db")
    assert risk == RiskLevel.HIGH
    assert req_conf is True

def test_high_risk_confirmation_gate():
    # Unconfirmed delete must be blocked and return requires_confirmation
    req = ActionRequest(action_type="delete_file", target="data.txt", confirmed=False)
    res = policy_engine.execute_action(req)
    assert res.success is False
    assert res.requires_confirmation is True
    assert res.plan is not None
    assert res.plan.risk_level == RiskLevel.HIGH

def test_invalid_url_scheme_blocked():
    req = ActionRequest(action_type="open_url", target="javascript:alert(1)", confirmed=False)
    res = policy_engine.execute_action(req)
    assert res.success is False
    assert "Invalid or untrusted URL scheme" in res.message
