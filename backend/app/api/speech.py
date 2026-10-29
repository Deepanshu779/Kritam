from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from app.core.security import verify_auth_token
from app.services.speech.transcriber import UnsupportedAudioError, transcribe_bytes

router = APIRouter(prefix="/api/speech", tags=["speech"])

@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str | None = Form(None),
    allow_model_download: bool = Form(False),
    _: bool = Depends(verify_auth_token),
):
    if not allow_model_download:
        raise HTTPException(status_code=428, detail="Explicit consent is required before local speech model files can be downloaded.")
    # MediaRecorder may send parameters (e.g. audio/webm;codecs=opus),
    # and Electron builds can expose WebM with a video/* MIME despite an audio track.
    raw_type = (audio.content_type or "application/octet-stream").lower().strip()
    mime = raw_type.split(";", 1)[0].strip()
    suffix_by_type = {
        "audio/webm": ".webm", "video/webm": ".webm",
        "audio/wav": ".wav", "audio/x-wav": ".wav",
        "audio/ogg": ".ogg", "application/ogg": ".ogg",
        "audio/mp4": ".mp4", "video/mp4": ".mp4",
        "audio/x-m4a": ".m4a", "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
    }
    suffix = suffix_by_type.get(mime, "" if mime == "application/octet-stream" else None)
    if suffix is None:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported audio format: {raw_type}. Supported: WebM, WAV, OGG, MP4/M4A, MP3.",
        )
    payload = await audio.read(40 * 1024 * 1024 + 1)
    if len(payload) > 40 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Recording exceeds the 40 MB limit.")
    language_hint = (language or "").strip().lower()
    if language_hint not in {"", "auto", "en", "hi"}:
        raise HTTPException(status_code=422, detail="Supported transcription language hints are auto, en, and hi.")
    try:
        result = transcribe_bytes(payload, suffix, language=None if language_hint in {"", "auto"} else language_hint)
        return result
    except UnsupportedAudioError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        # Log details server-side without leaking local paths or internals.
        import logging
        logging.getLogger(__name__).exception("Local speech transcription failed")
        raise HTTPException(status_code=503, detail="Local speech model could not transcribe this recording. Check backend dependencies and model download.") from exc
    finally:
        await audio.close()
