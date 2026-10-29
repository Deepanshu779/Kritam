import os
import json
import uuid
import datetime
import httpx
from typing import AsyncGenerator
from app.services.ai.base import BaseAIProvider
from app.core.config import settings

class KritamGatewayAdapter(BaseAIProvider):
    """
    Adapter for the managed Kritam Cloud Gateway.
    Allows zero-configuration consumer access to online AI without demanding personal API keys.
    """

    def __init__(self, gateway_url: str | None = None):
        self.gateway_url = (gateway_url or settings.KRITAM_GATEWAY_URL).rstrip("/")
        self.session_token: str | None = None
        self.session_expires_at: datetime.datetime | None = None
        self.quota_info: dict | None = None

    async def is_available(self) -> bool:
        """Check if gateway service is reachable."""
        if not settings.KRITAM_GATEWAY_ENABLED:
            return False
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.gateway_url}/v1/health")
                return res.status_code == 200
        except Exception:
            return False

    async def get_or_create_session(self, device_id: str | None = None) -> str | None:
        """Obtain a valid guest/device session token from the gateway."""
        now = datetime.datetime.utcnow()
        if self.session_token and self.session_expires_at and self.session_expires_at > (now + datetime.timedelta(minutes=5)):
            return self.session_token

        # Use a per-process random identifier instead of deriving an identifier
        # from the network interface's hardware address.
        device_id = device_id or f"win-{uuid.uuid4().hex}"
        payload = {
            "device_id": device_id,
            "platform": "windows",
            "app_version": settings.VERSION
        }

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.post(f"{self.gateway_url}/v1/auth/session", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    self.session_token = data.get("session_token")
                    expires_str = data.get("expires_at")
                    if expires_str:
                        try:
                            self.session_expires_at = datetime.datetime.fromisoformat(expires_str.replace("Z", "+00:00")).replace(tzinfo=None)
                        except Exception:
                            self.session_expires_at = now + datetime.timedelta(hours=24)
                    else:
                        self.session_expires_at = now + datetime.timedelta(hours=24)

                    self.quota_info = {
                        "daily_quota": data.get("daily_quota", 50),
                        "used_quota": data.get("used_quota", 0)
                    }
                    return self.session_token
        except Exception as e:
            # Gateway unreachable
            return None

        return None

    async def generate_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        if not settings.KRITAM_GATEWAY_ENABLED:
            raise RuntimeError("The KRITAM Gateway is disabled. Choose Ollama, Offline, or configure another provider in Settings.")
        # 1. Obtain or refresh session token
        token = await self.get_or_create_session()
        if not token:
            raise RuntimeError("The KRITAM Gateway did not provide a session. Check your connection or select Ollama, Offline, or a configured cloud provider.")

        endpoint = f"{self.gateway_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": messages,
            "model": model or "kritam-default",
            "stream": True
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=5.0)) as client:
                async with client.stream("POST", endpoint, headers=headers, json=payload) as response:
                    # Authentication failure / expired token
                    if response.status_code == 401:
                        self.session_token = None
                        token = await self.get_or_create_session()
                        if not token:
                            raise RuntimeError("The KRITAM Gateway session expired and could not be renewed. Check your connection and retry.")
                        # Re-stream with new token
                        headers["Authorization"] = f"Bearer {token}"
                        async with client.stream("POST", endpoint, headers=headers, json=payload) as retry_res:
                            if retry_res.status_code != 200:
                                raise RuntimeError(f"The KRITAM Gateway retry returned HTTP {retry_res.status_code}. Try again later or select another provider.")
                            async for line in retry_res.aiter_lines():
                                if line.startswith("data: "):
                                    chunk = line[6:].strip()
                                    if chunk == "[DONE]":
                                        break
                                    try:
                                        delta = json.loads(chunk).get("delta", "")
                                        if delta:
                                            yield delta
                                    except Exception:
                                        pass
                        return

                    # Quota exceeded / rate limited
                    if response.status_code in [402, 429]:
                        raise RuntimeError(f"The KRITAM Gateway returned HTTP {response.status_code} (quota or rate limit). Try later or select another provider.")

                    # Service unavailable / Provider outage
                    if response.status_code >= 500:
                        raise RuntimeError("The KRITAM Gateway is temporarily unavailable. Try again later or select another provider.")

                    if response.status_code != 200:
                        raise RuntimeError(f"The KRITAM Gateway returned HTTP {response.status_code}. Check the gateway configuration or select another provider.")

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            raw_chunk = line[6:].strip()
                            if raw_chunk == "[DONE]":
                                break
                            try:
                                parsed = json.loads(raw_chunk)
                                delta = parsed.get("delta") or parsed.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                if delta:
                                    yield delta
                            except json.JSONDecodeError:
                                continue

        except httpx.ConnectError:
            raise RuntimeError("Could not reach the KRITAM Gateway. Check your internet connection or select another provider.")
        except httpx.TimeoutException:
            raise RuntimeError("The KRITAM Gateway timed out. Try again later or select another provider.")
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError("The KRITAM Gateway could not complete the request. Check gateway availability and try again.") from e
