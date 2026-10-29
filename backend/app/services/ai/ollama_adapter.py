import json
import httpx
from typing import AsyncGenerator
from app.services.ai.base import BaseAIProvider
from app.core.config import settings

class OllamaAdapter(BaseAIProvider):
    """Local inference adapter for Ollama."""

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.default_model = model or settings.OLLAMA_MODEL

    async def is_available(self) -> bool:
        """Check if local Ollama server is running and responding."""
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def get_installed_models(self) -> list[str]:
        """Fetch list of locally installed models."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []

    async def generate_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": True
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=3.0)) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    if response.status_code != 200:
                        raise RuntimeError(f"Ollama returned HTTP {response.status_code}. Check that the Ollama service is running and model '{target_model}' is installed.")

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            delta = data.get("message", {}).get("content", "")
                            if delta:
                                yield delta
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError:
            raise RuntimeError("Could not connect to Ollama. Start the local Ollama service and check its configured address.")
        except httpx.TimeoutException:
            raise RuntimeError("Ollama did not finish within the response timeout. Try a smaller model or ask a shorter question.")
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError("Ollama could not complete the response. Check its service and model, then try again.") from e
