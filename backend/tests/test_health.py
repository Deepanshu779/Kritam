import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "KRITAM" in data["service"]

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "offline" in data["providers"]
    assert data["providers"]["offline"]["available"] is True

def test_authenticated_ping_reports_backend_identity():
    response = client.get("/api/health/ping")
    assert response.status_code == 200
    assert response.json()["service"] == "KRITAM AI"
