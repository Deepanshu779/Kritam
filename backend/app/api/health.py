from fastapi import APIRouter, Depends
from app.core.config import settings
from app.core.security import verify_auth_token
from app.services.ai.router import ai_router

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("")
async def get_health(_: bool = Depends(verify_auth_token)):
    """Health check endpoint providing backend status and AI providers availability."""
    providers = await ai_router.check_all_providers()
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "default_provider": settings.DEFAULT_PROVIDER,
        "providers": providers
    }
