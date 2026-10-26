import pytest
import json
import httpx
from unittest.mock import patch, MagicMock
from app.services.ai.gateway_adapter import KritamGatewayAdapter

@pytest.mark.asyncio
async def test_gateway_session_creation():
    adapter = KritamGatewayAdapter(gateway_url="http://test-gateway.local")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "session_token": "test-session-token-xyz",
        "expires_at": "2026-10-26T22:00:00Z",
        "plan": "free",
        "daily_quota": 50,
        "used_quota": 5
    }

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        token = await adapter.get_or_create_session(device_id="test-win-device")
        assert token == "test-session-token-xyz"
        assert adapter.session_token == "test-session-token-xyz"
        assert adapter.quota_info is not None
        assert adapter.quota_info["daily_quota"] == 50

@pytest.mark.asyncio
async def test_gateway_streaming_success():
    adapter = KritamGatewayAdapter(gateway_url="http://test-gateway.local")
    adapter.session_token = "valid-token"
    adapter.session_expires_at = None

    class MockStreamContext:
        async def __aenter__(self):
            res = MagicMock()
            res.status_code = 200
            async def aiter_lines():
                yield "data: {\"delta\": \"Hello, \"}"
                yield "data: {\"delta\": \"I am Kritam!\"}"
                yield "data: [DONE]"
            res.aiter_lines = aiter_lines
            return res

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    with patch("httpx.AsyncClient.stream", return_value=MockStreamContext()):
        with patch.object(adapter, "get_or_create_session", return_value="valid-token"):
            chunks = []
            async for chunk in adapter.generate_stream([{"role": "user", "content": "hello"}]):
                chunks.append(chunk)

            full_text = "".join(chunks)
            assert full_text == "Hello, I am Kritam!"

@pytest.mark.asyncio
async def test_gateway_quota_exhausted():
    adapter = KritamGatewayAdapter(gateway_url="http://test-gateway.local")

    class MockQuotaContext:
        async def __aenter__(self):
            res = MagicMock()
            res.status_code = 429
            return res

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    with patch("httpx.AsyncClient.stream", return_value=MockQuotaContext()):
        with patch.object(adapter, "get_or_create_session", return_value="valid-token"):
            chunks = []
            async for chunk in adapter.generate_stream([{"role": "user", "content": "test"}]):
                chunks.append(chunk)

            text = "".join(chunks)
            assert "daily free limit" in text.lower()
            assert "ollama" in text.lower()
            assert "offline engine" in text.lower()

@pytest.mark.asyncio
async def test_gateway_network_down():
    adapter = KritamGatewayAdapter(gateway_url="http://unreachable-gateway.local")

    with patch.object(adapter, "get_or_create_session", return_value=None):
        chunks = []
        async for chunk in adapter.generate_stream([{"role": "user", "content": "test"}]):
            chunks.append(chunk)

        text = "".join(chunks)
        assert "unable to connect" in text.lower()
        assert "offline engine" in text.lower()
