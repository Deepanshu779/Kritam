import pytest
from app.services.ai.offline_router import OfflineRouter

@pytest.mark.asyncio
async def test_offline_router_intents():
    router = OfflineRouter()
    
    # 1. Test app launch extraction
    intent = router.extract_desktop_intent("Hey Kritam, open Chrome")
    assert intent is not None
    assert intent["type"] == "launch_app"
    assert intent["target"] == "chrome"

    intent2 = router.extract_desktop_intent("open vs code")
    assert intent2 is not None
    assert intent2["type"] == "launch_app"
    assert intent2["target"] == "vs code"

    # 2. Test URL extraction
    intent3 = router.extract_desktop_intent("go to github.com")
    assert intent3 is not None
    assert intent3["type"] == "open_url"
    assert "github.com" in intent3["target"]

    # 3. Test calculation response
    chunks = []
    async for chunk in router.generate_stream([{"role": "user", "content": "calculate 25 * 4"}]):
        chunks.append(chunk)
    full_text = "".join(chunks)
    assert "100" in full_text

    # 4. Test time response
    chunks_time = []
    async for chunk in router.generate_stream([{"role": "user", "content": "what time is it"}]):
        chunks_time.append(chunk)
    time_text = "".join(chunks_time)
    assert "current time" in time_text.lower()

    # 5. Test deterministic query recognition
    assert router.is_deterministic_query("Open VS Code") is True
    assert router.is_deterministic_query("Open YouTube") is True
    assert router.is_deterministic_query("What date and time is it?") is True
    assert router.is_deterministic_query("Explain Python decorators") is False
