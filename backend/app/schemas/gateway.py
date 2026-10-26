from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class GatewaySessionRequest(BaseModel):
    """Device/guest registration request to Kritam Cloud Gateway."""
    device_id: str
    platform: str = "windows"
    app_version: str = "1.0.0"

class GatewaySessionResponse(BaseModel):
    """Authenticated session returned by the gateway."""
    session_token: str
    expires_at: datetime
    plan: str = "free"
    daily_quota: int = 50
    used_quota: int = 0
    model_config = ConfigDict(from_attributes=True)

class GatewayUsageInfo(BaseModel):
    """Usage limits and remaining quota info."""
    plan: str = "free"
    daily_quota: int
    used_quota: int
    remaining_quota: int
    reset_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

class GatewayChatRequest(BaseModel):
    """Chat completion request routed through the gateway."""
    session_token: str
    messages: list[dict]
    model: str | None = None
    stream: bool = True

class GatewayErrorResponse(BaseModel):
    """Structured error payload from Kritam Cloud Gateway."""
    error_code: str # AUTH_FAILED, QUOTA_EXCEEDED, RATE_LIMITED, PROVIDER_UNAVAILABLE, SERVICE_UNAVAILABLE
    message: str
    retry_after: int | None = None
