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
            yield (
                f"No API key configured for {self.provider.upper()}.\n\n"
                "Please open **Settings** (gear icon) and add your API key to enable cloud intelligence."
            )
            return

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
                        yield f"Authentication failed (401 Unauthorized) for {self.provider.upper()}. Please verify your API key in Settings."
                        return
                    if response.status_code == 429:
                        yield f"Rate limit reached (429) for {self.provider.upper()}. Please try again in a moment."
                        return
                    if response.status_code != 200:
                        error_text = await response.aread()
                        yield f"Cloud API error ({response.status_code}): {error_text.decode('utf-8', errors='ignore')}"
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
                                choices = parsed.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {}).get("content", "")
                                    if delta:
                                        yield delta
                            except json.JSONDecodeError:
                                continue
        except httpx.ConnectError:
            yield f"Could not reach {self.provider.upper()} API. Please check your internet connection."
        except Exception as e:
            yield f"Cloud provider error: {str(e)}"
