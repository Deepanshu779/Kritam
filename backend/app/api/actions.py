from fastapi import APIRouter, Depends
from app.core.security import verify_auth_token
from app.schemas.action import ActionRequest, ActionResponse
from app.services.automation.policy_engine import policy_engine

router = APIRouter(prefix="/api/actions", tags=["actions"])

@router.post("/execute", response_model=ActionResponse)
def execute_desktop_action(
    request: ActionRequest,
    _: bool = Depends(verify_auth_token)
):
    """
    Execute desktop automation action validated against the three-tier policy engine.
    """
    return policy_engine.execute_action(request)
