import json
import re
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

@pytest.mark.asyncio
async def test_natural_variations_and_music():
    router = OfflineRouter()

    # 1. Natural phrasing with wake-word and politeness
    intent1 = router.extract_desktop_intent("Kritam, can you open YouTube for me?")
    assert intent1 is not None
    assert intent1["type"] == "open_url"
    assert "youtube" in intent1["target"]

    intent2 = router.extract_desktop_intent("Hey Kritam, please launch VS Code.")
    assert intent2 is not None
    assert intent2["type"] == "launch_app"
    assert "vs code" in intent2["target"].lower()

    # 2. Music command
    intent_music = router.extract_desktop_intent("Play some lo-fi music")
    assert intent_music is not None
    assert intent_music["type"] == "play_music"
    assert "lo-fi" in intent_music["target"]
    assert intent_music["target"].endswith("on youtube")
    assert router.extract_desktop_intent("play Chamma Chamma", "spotify")["target"] == "chamma chamma on spotify"
    assert router.extract_desktop_intent("play Believer on Spotify")["target"] == "believer on spotify"
    assert router.extract_desktop_intent("Hey Kritam, pause music")["type"] == "unsupported_media_control"
    assert router.extract_desktop_intent("Hey Kritam, resume music")["type"] == "unsupported_media_control"
    assert router.extract_desktop_intent("Hey Kritam, stop the music")["type"] == "unsupported_media_control"
    assert router.extract_desktop_intent("Hey Kritam, play the next song")["type"] == "unsupported_media_control"
    assert router.extract_desktop_intent("Hey Kritam, Chrome kholo")["target"] == "chrome"
    assert router.extract_desktop_intent("Hey Kritam, Chamma Chamma chalao")["target"] == "chamma chamma on youtube"
    assert router.extract_desktop_intent("Spotify par Believer bajao")["target"] == "believer on spotify"

    # 3. Search command
    intent_search = router.extract_desktop_intent("Search for C++ DSA tutorials")
    assert intent_search is not None
    assert intent_search["type"] == "open_url"
    assert "google.com" in intent_search["target"]

    # 4. Cancellation / stop speech
    intent_stop = router.extract_desktop_intent("Stop speaking")
    assert intent_stop is not None
    assert intent_stop["type"] == "cancel_speech"

    intent_cancel = router.extract_desktop_intent("Cancel that")
    assert intent_cancel is not None
    assert intent_cancel["type"] == "cancel_speech"

    # 5. Verify action payload format in streaming response
    chunks = []
    async for chunk in router.generate_stream([{"role": "user", "content": "open calculator"}]):
        chunks.append(chunk)
    stream_out = "".join(chunks)
    assert "```action" in stream_out
    assert '"executed": true' in stream_out.lower()
    assert '"status": "succeeded"' in stream_out.lower() or '"status": "failed"' in stream_out.lower()


@pytest.mark.asyncio
async def test_external_open_action_is_pending_until_confirmed(monkeypatch):
    from app.services.automation import policy_engine as policy_module

    opened_urls = []
    monkeypatch.setattr(policy_module.webbrowser, "open", lambda url: opened_urls.append(url) or True)
    chunks = []
    async for chunk in OfflineRouter().generate_stream([{"role": "user", "content": "open youtube"}]):
        chunks.append(chunk)

    response = "".join(chunks)
    match = re.search(r"```action\s*\n([\s\S]*?)\n```", response)
    assert match is not None
    payload = json.loads(match.group(1))
    assert payload["status"] == "pending"
    assert payload["executed"] is False
    assert opened_urls == []


@pytest.mark.asyncio
async def test_explicit_voice_music_request_opens_search_without_extra_confirmation(monkeypatch):
    from app.services.automation import policy_engine as policy_module

    opened_urls = []
    monkeypatch.setattr(policy_module.webbrowser, "open", lambda url: opened_urls.append(url) or True)
    chunks = []
    async for chunk in OfflineRouter().generate_stream(
        [{"role": "user", "content": "Hey Kritam, play Chamma Chamma"}],
        voice_command=True,
    ):
        chunks.append(chunk)
    response = "".join(chunks)
    payload = json.loads(re.search(r"```action\s*\n([\s\S]*?)\n```", response).group(1))
    assert payload["status"] == "succeeded"
    assert payload["executed"] is True
    assert "youtube.com/search" in payload["target"]
    assert "choose a result" in response.lower()
    assert len(opened_urls) == 1


@pytest.mark.asyncio
async def test_voice_opens_youtube_but_does_not_auto_confirm_arbitrary_sites(monkeypatch):
    from app.services.automation import policy_engine as policy_module

    opened_urls = []
    monkeypatch.setattr(policy_module.webbrowser, "open", lambda url: opened_urls.append(url) or True)
    youtube_chunks = []
    async for chunk in OfflineRouter().generate_stream(
        [{"role": "user", "content": "Hey Kritam, open YouTube"}], voice_command=True
    ):
        youtube_chunks.append(chunk)
    youtube_response = "".join(youtube_chunks)
    youtube_action = json.loads(re.search(r"```action\s*\n([\s\S]*?)\n```", youtube_response).group(1))
    assert youtube_action["status"] == "succeeded"
    assert opened_urls == ["https://www.youtube.com"]

    site_chunks = []
    async for chunk in OfflineRouter().generate_stream(
        [{"role": "user", "content": "Hey Kritam, open example.com"}], voice_command=True
    ):
        site_chunks.append(chunk)
    site_action = json.loads(re.search(r"```action\s*\n([\s\S]*?)\n```", "".join(site_chunks)).group(1))
    assert site_action["status"] == "pending"
    assert opened_urls == ["https://www.youtube.com"]

