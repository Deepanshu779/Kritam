import hmac
from fastapi import Header, HTTPException, status
from app.core.config import settings

def verify_auth_token(x_kritam_auth_token: str | None = Header(None)) -> bool:
    """
    Verify the local session authentication token sent from Electron main process.
    Local development/test runs may omit a token. Packaged/production runs fail closed.
    """
    if not settings.AUTH_TOKEN:
        if settings.ENVIRONMENT.lower() in {"development", "test"}:
            return True
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend session authentication is not configured"
        )
    
    if not x_kritam_auth_token or not hmac.compare_digest(x_kritam_auth_token, settings.AUTH_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Kritam authorization token"
        )
    return True
