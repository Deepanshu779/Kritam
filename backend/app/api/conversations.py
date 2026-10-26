from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.security import verify_auth_token
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListItem
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

@router.get("", response_model=list[ConversationListItem])
def list_conversations(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_auth_token)
):
    """Retrieve all non-archived conversations sorted by updated_at descending."""
    convs = (
        db.query(Conversation)
        .filter(Conversation.is_archived == False)
        .order_by(Conversation.is_pinned.desc(), Conversation.updated_at.desc())
        .all()
    )
    result = []
    for c in convs:
        last_msg = (
            db.query(Message.content)
            .filter(Message.conversation_id == c.id)
            .order_by(Message.created_at.desc())
            .first()
        )
        msg_count = db.query(Message).filter(Message.conversation_id == c.id).count()
        result.append(
            ConversationListItem(
                id=c.id,
                title=c.title,
                is_pinned=c.is_pinned,
                is_archived=c.is_archived,
                model_used=c.model_used,
                created_at=c.created_at,
                updated_at=c.updated_at,
                message_count=msg_count,
                last_message=last_msg[0] if last_msg else None
            )
        )
    return result

@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_auth_token)
):
    """Create a new conversation session."""
    conv = Conversation(
        title=payload.title,
        is_pinned=payload.is_pinned,
        is_archived=payload.is_archived,
        model_used=payload.model_used
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_auth_token)
):
    """Get conversation details with all historical messages."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.patch("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_auth_token)
):
    """Update title, pinned status, or archive status."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if payload.title is not None:
        conv.title = payload.title
    if payload.is_pinned is not None:
        conv.is_pinned = payload.is_pinned
    if payload.is_archived is not None:
        conv.is_archived = payload.is_archived

    db.commit()
    db.refresh(conv)
    return conv

@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_auth_token)
):
    """Delete a conversation and all its messages."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    db.delete(conv)
    db.commit()
    return None
