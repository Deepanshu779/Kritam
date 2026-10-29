import json
import httpx
from typing import AsyncGenerator
from app.services.ai.base import BaseAIProvider
from app.core.config import settings

class CloudAIAdapter(BaseAIProvider):
    """
    Adapter for cloud AI providers (OpenAI, Groq, OpenRouter, custom OpenAI-compatible).
    """

    ENDPOINTS = {
        "openai": "https://api.openai.com/v1/chat/completions",
        "groq": "https://api.groq.com/openai/v1/chat/completions",
        "openrouter": "https://openrouter.ai/api/v1/chat/completions"
    }

    DEFAULT_MODELS = {
        "openai": "gpt-4o-mini",
        "groq": "llama-3.1-8b-instant",
        "openrouter": "meta-llama/llama-3.1-8b-instruct:free"
    }

    def __init__(self, provider: str = "openai", api_key: str | None = None, model: str | None = None):
        self.provider = provider.lower()
        self.api_key = api_key or getattr(settings, f"{self.provider.upper()}_API_KEY", "")
        self.model = model or self.DEFAULT_MODELS.get(self.provider, "gpt-4o-mini")

    async def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    async def generate_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise RuntimeError(f"No API key is configured for {self.provider.upper()}. Add one in Settings or select a local provider.")

        endpoint = self.ENDPOINTS.get(self.provider, self.ENDPOINTS["openai"])
        target_model = model or self.model
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "https://kritam.local"
            headers["X-Title"] = "KRITAM Desktop"

        payload = {
            "model": target_model,
            "messages": messages,
            "stream": True,
            "temperature": 0.7
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=5.0)) as client:
                async with client.stream("POST", endpoint, headers=headers, json=payload) as response:
                    if response.status_code == 401:
                        raise RuntimeError(f"{self.provider.upper()} rejected the API key. Check the key in Settings.")
                    if response.status_code == 429:
                        raise RuntimeError(f"{self.provider.upper()} rate limit reached. Wait briefly and try again.")
                    if response.status_code != 200:
                        raise RuntimeError(f"{self.provider.upper()} returned HTTP {response.status_code}. Check the configured model and provider status.")

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            raw_chunk = line[6:].strip()
                            if raw_chunk == "[DONE]":
                                break
                            try:
                                parsed = json.loads(raw_chunk)
                                choices = parsed.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {}).get("content", "")
                                    if delta:
                                        yield delta
                            except json.JSONDecodeError:
                                continue
        except httpx.ConnectError:
            raise RuntimeError(f"Could not reach {self.provider.upper()}. Check your internet connection and try again.")
        except httpx.TimeoutException:
            raise RuntimeError(f"{self.provider.upper()} timed out before completing the response. Try again.")
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"{self.provider.upper()} could not complete the request. Check the provider settings and try again.") from e
