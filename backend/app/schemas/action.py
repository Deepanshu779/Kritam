from enum import Enum
from pydantic import BaseModel, Field

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ActionRequest(BaseModel):
    action_type: str # launch_app, open_url, open_folder, inspect_file, schedule_reminder
    target: str
    arguments: dict | None = Field(default_factory=dict)
    confirmed: bool = False

class ActionPlan(BaseModel):
    action_id: str
    action_type: str
    target: str
    description: str
    risk_level: RiskLevel
    requires_confirmation: bool
    consequences: str | None = None

class ActionResponse(BaseModel):
    success: bool
    action_type: str
    target: str
    message: str
    requires_confirmation: bool = False
    plan: ActionPlan | None = None
    output: str | None = None
