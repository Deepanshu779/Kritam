from abc import ABC, abstractmethod
from typing import AsyncGenerator

class BaseAIProvider(ABC):
    """Abstract base class for AI providers in Kritam."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is currently reachable and configured."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens asynchronously."""
        yield ""
