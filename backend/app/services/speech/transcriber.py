"""Lazy-loaded local Whisper transcription for microphone recordings."""
from __future__ import annotations

import os
import tempfile
import threading
from pathlib import Path

_model = None
_model_lock = threading.Lock()


def _get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from faster_whisper import WhisperModel
                # CPU int8 is the dependable baseline on Windows and avoids
                # consuming the user's limited 4 GB GPU VRAM.
                model_name = os.getenv("KRITAM_STT_MODEL", "base")
                _model = WhisperModel(
                    model_name,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=max(2, min(8, os.cpu_count() or 4)),
                )
    return _model


def transcribe_bytes(audio: bytes, suffix: str = ".webm") -> dict:
    if not audio:
        raise ValueError("No audio was recorded.")
    if len(audio) > 40 * 1024 * 1024:
        raise ValueError("Recording is too large (40 MB limit).")
    safe_suffix = suffix if suffix in {".webm", ".wav", ".ogg", ".mp4", ".m4a"} else ".webm"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=safe_suffix, delete=False) as handle:
            handle.write(audio)
            temp_path = handle.name
        model = _get_model()
        segments, info = model.transcribe(
            temp_path,
            beam_size=1,
            vad_filter=True,
            condition_on_previous_text=False,
            # Favor responsive interactive dictation over slower beam search.
        )
        text = " ".join(segment.text.strip() for segment in segments).strip()
        return {"text": text, "language": info.language,
                "language_probability": info.language_probability}
    finally:
        if temp_path:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except OSError:
                pass
