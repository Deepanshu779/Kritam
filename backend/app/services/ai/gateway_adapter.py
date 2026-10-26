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

        device_id = device_id or f"win-{uuid.getnode():012x}"
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
        # 1. Obtain or refresh session token
        token = await self.get_or_create_session()
        if not token:
            yield (
                "Unable to connect to the **Kritam AI Gateway**.\n\n"
                "**Options:**\n"
                "- Check your internet connection.\n"
                "- Switch to **Offline Engine** in Settings for local commands.\n"
                "- Switch to **Local AI (Ollama)** to run models locally on your PC.\n"
                "- If you have personal API keys, enable **Developer Mode** in Settings."
            )
            return

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
                            yield "Your Kritam AI session expired and could not be renewed. Please check your connection."
                            return
                        # Re-stream with new token
                        headers["Authorization"] = f"Bearer {token}"
                        async with client.stream("POST", endpoint, headers=headers, json=payload) as retry_res:
                            if retry_res.status_code != 200:
                                yield f"Gateway returned status {retry_res.status_code}."
                                return
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
                        yield (
                            "You have reached your daily free limit for **Kritam AI**.\n\n"
                            "Your free quota will automatically refresh tomorrow. In the meantime, you can:\n"
                            "1. Switch to **Local AI via Ollama** (unlimited private local queries).\n"
                            "2. Switch to **Offline Engine** for local actions and assistance.\n"
                            "3. Add your own API key under **Developer Settings** in Settings."
                        )
                        return

                    # Service unavailable / Provider outage
                    if response.status_code >= 500:
                        yield (
                            "Kritam AI Cloud is momentarily undergoing maintenance or experiencing upstream provider delay. "
                            "Please try again shortly or use Offline mode."
                        )
                        return

                    if response.status_code != 200:
                        err_text = await response.aread()
                        yield f"Kritam Gateway error ({response.status_code}): {err_text.decode('utf-8', errors='ignore')}"
                        return

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
            yield (
                "Could not reach the Kritam AI Gateway. Please verify your internet connection or switch to Offline Mode."
            )
        except Exception as e:
            yield f"Error connecting to Kritam AI: {str(e)}"
