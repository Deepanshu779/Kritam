from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from app.core.security import verify_auth_token
from app.services.speech.transcriber import transcribe_bytes

router = APIRouter(prefix="/api/speech", tags=["speech"])

@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    _: bool = Depends(verify_auth_token),
):
    allowed = {"audio/webm", "audio/wav", "audio/ogg", "audio/mp4", "audio/x-m4a", "application/octet-stream"}
    if audio.content_type and audio.content_type not in allowed:
        raise HTTPException(status_code=415, detail="Unsupported audio format.")
    payload = await audio.read(40 * 1024 * 1024 + 1)
    if len(payload) > 40 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Recording exceeds the 40 MB limit.")
    suffix = {
        "audio/webm": ".webm", "audio/wav": ".wav",
        "audio/ogg": ".ogg", "audio/mp4": ".mp4", "audio/x-m4a": ".m4a"
    }.get(audio.content_type, ".webm")
    try:
        result = transcribe_bytes(payload, suffix)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        # Log details server-side without leaking local paths or internals.
        import logging
        logging.getLogger(__name__).exception("Local speech transcription failed")
        raise HTTPException(status_code=503, detail="Local speech model could not transcribe this recording. Check backend dependencies and model download.") from exc
    finally:
        await audio.close()
