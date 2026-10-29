from typing import AsyncGenerator
from app.services.ai.base import BaseAIProvider
from app.services.ai.offline_router import OfflineRouter
from app.services.ai.ollama_adapter import OllamaAdapter
from app.services.ai.cloud_adapter import CloudAIAdapter
from app.services.ai.gateway_adapter import KritamGatewayAdapter
from app.core.config import settings

class AIRouter:
    """Master AI Router coordinating hybrid providers and fallback policy."""

    def __init__(self):
        self.offline_router = OfflineRouter()
        self.gateway_adapter = KritamGatewayAdapter()

    def get_provider(
        self,
        provider_name: str | None = None,
        model: str | None = None,
        api_keys: dict | None = None
    ) -> BaseAIProvider:
        provider = (provider_name or settings.DEFAULT_PROVIDER).strip().lower()
        api_keys = api_keys or {}

        if provider == "kritam":
            custom_gateway = api_keys.get("gateway_url")
            return KritamGatewayAdapter(gateway_url=custom_gateway) if custom_gateway else self.gateway_adapter
        elif provider == "ollama":
            return OllamaAdapter(model=model)
        elif provider in ["openai", "groq", "openrouter"]:
            key = api_keys.get(f"{provider}_api_key") or getattr(settings, f"{provider.upper()}_API_KEY", "")
            return CloudAIAdapter(provider=provider, api_key=key, model=model)
        elif provider == "offline":
            return self.offline_router
        raise ValueError(f"Unsupported AI provider '{provider}'. Choose Kritam Gateway, Ollama, Offline, OpenAI, Groq, or OpenRouter in Settings.")

    async def check_all_providers(self, api_keys: dict | None = None) -> dict:
        """Check status of each available provider."""
        api_keys = api_keys or {}
        
        ollama = OllamaAdapter()
        ollama_ok = await ollama.is_available()
        ollama_models = await ollama.get_installed_models() if ollama_ok else []

        gateway_ok = await self.gateway_adapter.is_available()
        openai_key = api_keys.get("openai_api_key") or settings.OPENAI_API_KEY
        groq_key = api_keys.get("groq_api_key") or settings.GROQ_API_KEY
        openrouter_key = api_keys.get("openrouter_api_key") or settings.OPENROUTER_API_KEY

        return {
            "kritam": {
                "available": gateway_ok,
                "name": "KRITAM Gateway",
                "model": "kritam-default",
                "details": "Configured remote gateway health check succeeded" if gateway_ok else "Configured gateway is unavailable; deployment and service terms are unverified"
            },
            "offline": {
                "available": True,
                "name": "Offline Engine",
                "details": "Deterministic local command and conversational router"
            },
            "ollama": {
                "available": ollama_ok,
                "name": "Local AI (Ollama)",
                "models": ollama_models,
                "endpoint": settings.OLLAMA_BASE_URL,
                "details": "Local inference on your GPU/CPU" if ollama_ok else "Ollama server not detected at 127.0.0.1:11434"
            },
            "openai": {
                "available": bool(openai_key and len(openai_key) > 5),
                "name": "OpenAI",
                "model": "gpt-4o-mini",
                "details": "API Key configured" if (openai_key and len(openai_key) > 5) else "API Key required"
            },
            "groq": {
                "available": bool(groq_key and len(groq_key) > 5),
                "name": "Groq (Fast Cloud)",
                "model": "llama-3.1-8b-instant",
                "details": "API Key configured" if (groq_key and len(groq_key) > 5) else "API Key required"
            },
            "openrouter": {
                "available": bool(openrouter_key and len(openrouter_key) > 5),
                "name": "OpenRouter",
                "model": "meta-llama/llama-3.1-8b-instruct:free",
                "details": "API Key configured" if (openrouter_key and len(openrouter_key) > 5) else "API Key required"
            }
        }

ai_router = AIRouter()
