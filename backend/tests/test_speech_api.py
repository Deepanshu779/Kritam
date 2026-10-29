from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_speech_endpoint_requires_model_download_consent():
    response = client.post(
        "/api/speech/transcribe",
        files={"audio": ("recording.webm", b"invalid audio", "audio/webm")},
    )
    assert response.status_code == 428
    assert "Explicit consent is required" in response.json()["detail"]


def test_speech_endpoint_rejects_invalid_audio_container():
    response = client.post(
        "/api/speech/transcribe",
        files={"audio": ("recording.webm", b"invalid audio", "audio/webm")},
        data={"allow_model_download": "true", "language": "auto"},
    )
    assert response.status_code == 415
    assert "not a supported" in response.json()["detail"]


def test_speech_endpoint_rejects_unavailable_model_choice():
    response = client.post(
        "/api/speech/transcribe",
        files={"audio": ("recording.webm", b"invalid audio", "audio/webm")},
        data={"allow_model_download": "true", "language": "auto", "model": "large-v3"},
    )
    assert response.status_code == 422
    assert "base and small" in response.json()["detail"]
