from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class MessageBase(BaseModel):
    role: str
    content: str
    tool_calls: str | None = None
    tool_results: str | None = None
    status: str = "completed"

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: str
    conversation_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ConversationBase(BaseModel):
    title: str = "New Conversation"
    is_pinned: bool = False
    is_archived: bool = False
    model_used: str = "offline"

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(BaseModel):
    title: str | None = None
    is_pinned: bool | None = None
    is_archived: bool | None = None

class ConversationResponse(ConversationBase):
    id: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

class ConversationListItem(ConversationBase):
    id: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message: str | None = None
    model_config = ConfigDict(from_attributes=True)
