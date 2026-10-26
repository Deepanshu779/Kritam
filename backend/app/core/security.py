from fastapi import Header, HTTPException, status
from app.core.config import settings

def verify_auth_token(x_kritam_auth_token: str | None = Header(None)) -> bool:
    """
    Verify the local session authentication token sent from Electron main process.
    If no AUTH_TOKEN was configured (e.g. standalone test mode), bypass check.
    """
    if not settings.AUTH_TOKEN:
        return True
    
    if not x_kritam_auth_token or x_kritam_auth_token != settings.AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Kritam authorization token"
        )
    return True
