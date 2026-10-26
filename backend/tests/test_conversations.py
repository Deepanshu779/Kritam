import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_conversation_lifecycle():
    # 1. Create conversation
    create_res = client.post("/api/conversations", json={"title": "Test Chat", "model_used": "offline"})
    assert create_res.status_code == 201
    conv = create_res.json()
    conv_id = conv["id"]
    assert conv["title"] == "Test Chat"

    # 2. List conversations
    list_res = client.get("/api/conversations")
    assert list_res.status_code == 200
    conv_list = list_res.json()
    assert any(c["id"] == conv_id for c in conv_list)

    # 3. Patch conversation (pin and rename)
    patch_res = client.patch(f"/api/conversations/{conv_id}", json={"title": "Updated Title", "is_pinned": True})
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Updated Title"
    assert patch_res.json()["is_pinned"] is True

    # 4. Get conversation details
    get_res = client.get(f"/api/conversations/{conv_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Updated Title"

    # 5. Delete conversation
    del_res = client.delete(f"/api/conversations/{conv_id}")
    assert del_res.status_code == 204

    # 6. Verify 404
    get_after_del = client.get(f"/api/conversations/{conv_id}")
    assert get_after_del.status_code == 404
