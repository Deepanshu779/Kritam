from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class BrokenProvider:
    async def generate_stream(self, messages, model=None, **kwargs):
        if False:
            yield ""
        raise RuntimeError("Provider unavailable")


def test_unknown_provider_does_not_persist_a_user_message():
    created = client.post("/api/conversations", json={"title": "Provider validation"})
    assert created.status_code == 201
    conversation_id = created.json()["id"]

    response = client.post("/api/chat/stream", json={
        "conversation_id": conversation_id,
        "message": "Tell me a story",
        "provider": "unknown-provider"
    })
    assert response.status_code == 400
    assert "Unsupported AI provider" in response.json()["detail"]
    assert client.get(f"/api/conversations/{conversation_id}").json()["messages"] == []
    assert client.delete(f"/api/conversations/{conversation_id}").status_code == 204


def test_provider_stream_failure_is_sent_as_error_not_successful_answer():
    created = client.post("/api/conversations", json={"title": "Provider failure"})
    assert created.status_code == 201
    conversation_id = created.json()["id"]

    with patch("app.api.chat.ai_router.get_provider", return_value=BrokenProvider()):
        response = client.post("/api/chat/stream", json={
            "conversation_id": conversation_id,
            "message": "Tell me a story",
            "provider": "openai"
        })

    assert response.status_code == 200
    assert '"error": "Provider unavailable"' in response.text
    assert '"done": true' in response.text
    stored = client.get(f"/api/conversations/{conversation_id}").json()["messages"]
    assert [message["role"] for message in stored] == ["user"]
    assert client.delete(f"/api/conversations/{conversation_id}").status_code == 204
