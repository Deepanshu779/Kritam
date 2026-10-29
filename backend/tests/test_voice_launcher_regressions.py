from unittest.mock import patch

from app.services.ai.offline_router import OfflineRouter
from app.services.automation.app_launcher import AppLauncher


def test_composite_youtube_play_command_extracts_media_query():
    intent = OfflineRouter().extract_desktop_intent(
        "open youtube and ply arjit singh"
    )
    assert intent == {
        "type": "play_music",
        "target": "arjit singh on youtube",
    }


def test_direct_youtube_play_command_extracts_query():
    intent = OfflineRouter().extract_desktop_intent(
        "play Arijit Singh on YouTube"
    )
    assert intent == {
        "type": "play_music",
        "target": "arijit singh on youtube",
    }


def test_open_youtube_without_playback_opens_site():
    intent = OfflineRouter().extract_desktop_intent("open youtube")
    assert intent is not None
    assert intent["type"] == "open_url"
    assert intent["target"] == "youtube"


def test_chrome_resolver_uses_specific_windows_resolution():
    with patch.object(AppLauncher, "_resolve_chrome", return_value=r"C:\Program Files\Google\Chrome\Application\chrome.exe"):
        assert AppLauncher.resolve_app("Chrome").endswith("chrome.exe")


def test_unknown_app_not_falsely_resolved():
    with patch("app.services.automation.app_launcher.shutil.which", return_value=None):
        assert AppLauncher.resolve_app("this-app-does-not-exist") is None


def test_arbitrary_path_executable_is_not_launchable():
    with patch("app.services.automation.app_launcher.shutil.which", return_value=r"C:\Python\python.exe"):
        assert AppLauncher.resolve_app("python") is None
