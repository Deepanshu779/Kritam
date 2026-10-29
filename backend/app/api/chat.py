import asyncio
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

    user_message_id = payload.user_message_id or str(uuid.uuid4())
    existing_user = db.query(Message).filter(Message.id == user_message_id).first()
    if existing_user and (
        existing_user.conversation_id != conv.id
        or existing_user.role != "user"
        or existing_user.content != payload.message
    ):
        raise HTTPException(status_code=409, detail="The supplied user message ID is already in use.")

    assistant_msg_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"kritam:assistant:{user_message_id}"))
    existing_assistant = db.query(Message).filter(Message.id == assistant_msg_id).first()
    if existing_assistant and existing_assistant.status == "completed":
        async def replay_completed_response():
            yield f"data: {json.dumps({'message_id': assistant_msg_id, 'delta': '', 'done': False})}\n\n"
            yield f"data: {json.dumps({'message_id': assistant_msg_id, 'delta': '', 'done': True, 'content': existing_assistant.content})}\n\n"
        return StreamingResponse(replay_completed_response(), media_type="text/event-stream")

    # Load settings and validate the requested provider before persisting a message.
    settings_records = db.query(Setting).all()
    user_settings = {}
    for setting in settings_records:
        try:
            user_settings[setting.key] = json.loads(setting.value)
        except (TypeError, json.JSONDecodeError):
            user_settings[setting.key] = setting.value

    if ai_router.offline_router.is_deterministic_query(payload.message):
        provider_adapter = ai_router.offline_router
        active_provider = "offline"
    else:
        active_provider = payload.provider or user_settings.get("default_provider", "kritam")
        try:
            provider_adapter = ai_router.get_provider(
                provider_name=active_provider,
                model=payload.model,
                api_keys=user_settings
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not existing_user:
        db.add(Message(
            id=user_message_id,
            conversation_id=conv.id,
            role="user",
            content=payload.message,
            status="completed"
        ))
        if conv.title == "New Conversation":
            auto_title = payload.message[:35].strip()
            if len(payload.message) > 35:
                auto_title += "..."
            conv.title = auto_title
        conv.updated_at = datetime.utcnow()
        db.commit()

    # Gather conversation history
    history_records = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .filter(Message.status == "completed")
        .order_by(Message.created_at.asc())
        .all()
    )
    messages_payload = [{"role": m.role, "content": m.content} for m in history_records]

    async def event_generator():
        accumulated_content: list[str] = []

        def persist_assistant(content: str, status: str) -> None:
            save_db = SessionLocal()
            try:
                asst_msg = save_db.query(Message).filter(Message.id == assistant_msg_id).first()
                if asst_msg:
                    asst_msg.content = content
                    asst_msg.status = status
                    asst_msg.created_at = datetime.utcnow()
                else:
                    save_db.add(Message(
                        id=assistant_msg_id,
                        conversation_id=payload.conversation_id,
                        role="assistant",
                        content=content,
                        status=status
                    ))
                if status == "completed":
                    c = save_db.query(Conversation).filter(Conversation.id == payload.conversation_id).first()
                    if c:
                        c.updated_at = datetime.utcnow()
                        c.model_used = active_provider
                save_db.commit()
            finally:
                save_db.close()
        
        # Send initial event with assistant message ID
        yield f"data: {json.dumps({'message_id': assistant_msg_id, 'delta': '', 'done': False})}\n\n"

        try:
            async for token in provider_adapter.generate_stream(messages_payload, model=payload.model):
                accumulated_content.append(token)
                yield f"data: {json.dumps({'message_id': assistant_msg_id, 'delta': token, 'done': False})}\n\n"

            final_text = "".join(accumulated_content)
            if not final_text.strip():
                raise RuntimeError("The selected AI provider returned an empty response. Check its connection, model, and credentials, then try again.")

            # Commit before announcing completion so a successful UI response is durable.
            persist_assistant(final_text, "completed")

            yield f"data: {json.dumps({'message_id': assistant_msg_id, 'delta': '', 'done': True, 'content': final_text})}\n\n"

        except asyncio.CancelledError:
            partial_text = "".join(accumulated_content)
            if partial_text:
                persist_assistant(partial_text, "cancelled")
            raise
        except Exception as e:
            partial_text = "".join(accumulated_content)
            if partial_text:
                persist_assistant(partial_text, "failed")
            error_text = str(e).strip() or "The provider did not complete the response. Try again."
            yield f"data: {json.dumps({'message_id': assistant_msg_id, 'delta': '', 'done': True, 'error': error_text})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
