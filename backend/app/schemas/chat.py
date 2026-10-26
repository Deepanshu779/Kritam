from pydantic import BaseModel, Field

class ChatStreamRequest(BaseModel):
    conversation_id: str
    message: str
    provider: str | None = None # offline, ollama, openai, groq, openrouter
    model: str | None = None
    stream: bool = True

class ChatStreamChunk(BaseModel):
    conversation_id: str
    message_id: str
    delta: str
    done: bool = False
    model: str | None = None
    provider: str | None = None
    error: str | None = None

class ProviderStatus(BaseModel):
    provider: str
    available: bool
    model: str | None = None
    details: str | None = None
