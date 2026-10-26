import json
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database.session import get_db, SessionLocal
from app.core.security import verify_auth_token
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.setting import Setting
from app.schemas.chat import ChatStreamRequest
from app.services.ai.router import ai_router

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/stream")
async def chat_stream(
    payload: ChatStreamRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_auth_token)
):
    """
    Real-time streaming chat endpoint using Server-Sent Events (SSE).
    """
    conv = db.query(Conversation).filter(Conversation.id == payload.conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Save user message
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        role="user",
        content=payload.message,
        status="completed"
    )
    db.add(user_msg)
    
    # Auto-generate title for first user message
    if conv.title == "New Conversation":
        auto_title = payload.message[:35].strip()
        if len(payload.message) > 35:
            auto_title += "..."
        conv.title = auto_title

    conv.updated_at = datetime.utcnow()
    db.commit()

    # Retrieve settings (API keys, provider preferences)
    settings_records = db.query(Setting).all()
    user_settings = {s.key: json.loads(s.value) for s in settings_records}

    # 1. Deterministic local commands & desktop actions (e.g. Open VS Code, Time, Date)
    if ai_router.offline_router.is_deterministic_query(payload.message):
        provider_adapter = ai_router.offline_router
        active_provider = "offline"
    else:
        active_provider = payload.provider or user_settings.get("default_provider", "kritam")
        provider_adapter = ai_router.get_provider(
            provider_name=active_provider,
            model=payload.model,
            api_keys=user_settings
        )

    # Gather conversation history
    history_records = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    messages_payload = [{"role": m.role, "content": m.content} for m in history_records]

    assistant_msg_id = str(uuid.uuid4())

    async def event_generator():
        accumulated_content = []
        
        # Send initial event with assistant message ID
        yield f"data: {json.dumps({'message_id': assistant_msg_id, 'delta': '', 'done': False})}\n\n"

        try:
            async for token in provider_adapter.generate_stream(messages_payload, model=payload.model):
                accumulated_content.append(token)
                yield f"data: {json.dumps({'message_id': assistant_msg_id, 'delta': token, 'done': False})}\n\n"

            # Final done event
            final_text = "".join(accumulated_content)
            yield f"data: {json.dumps({'message_id': assistant_msg_id, 'delta': '', 'done': True, 'content': final_text})}\n\n"

            # Persist assistant message in background session
            save_db = SessionLocal()
            try:
                asst_msg = Message(
                    id=assistant_msg_id,
                    conversation_id=payload.conversation_id,
                    role="assistant",
                    content=final_text,
                    status="completed"
                )
                save_db.add(asst_msg)
                
                # Update conversation updated_at
                c = save_db.query(Conversation).filter(Conversation.id == payload.conversation_id).first()
                if c:
                    c.updated_at = datetime.utcnow()
                    c.model_used = active_provider
                save_db.commit()
            finally:
                save_db.close()

        except Exception as e:
            err_msg = f"\n[Stream interrupted: {str(e)}]"
            yield f"data: {json.dumps({'message_id': assistant_msg_id, 'delta': err_msg, 'done': True, 'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
