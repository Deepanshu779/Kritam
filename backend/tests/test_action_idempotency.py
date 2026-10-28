import pytest
from app.schemas.action import ActionRequest, RiskLevel
from app.services.automation.policy_engine import policy_engine
from app.services.ai.offline_router import OfflineRouter

def test_play_music_policy_execution():
    # 1. Play music risk level must be LOW
    risk, req_conf, desc = policy_engine.evaluate_risk("play_music", "lo-fi chill beats")
    assert risk == RiskLevel.LOW
    assert req_conf is False

    # 2. Execution of play_music generates valid response
    req = ActionRequest(action_type="play_music", target="lo-fi chill beats", confirmed=False)
    res = policy_engine.execute_action(req)
    assert res.success is True
    assert "YouTube Music" in res.message or "Spotify" in res.message

@pytest.mark.asyncio
async def test_offline_router_action_payload_idempotency():
    router = OfflineRouter()
    
    # Verify that stream yields a single explicit executed action payload
    chunks = []
    async for chunk in router.generate_stream([{"role": "user", "content": "open calculator"}]):
        chunks.append(chunk)
    full_output = "".join(chunks)
    
    assert "```action" in full_output
    assert '"executed": true' in full_output.lower()
    assert '"action_type": "launch_app"' in full_output
    assert '"target": "calculator"' in full_output

@pytest.mark.asyncio
async def test_natural_search_intent_routing():
    router = OfflineRouter()
    
    intent = router.extract_desktop_intent("Search for async python tutorials")
    assert intent is not None
    assert intent["type"] == "open_url"
    assert "google.com/search" in intent["target"]
    assert "async+python+tutorials" in intent["target"] or "async%20python%20tutorials" in intent["target"]
