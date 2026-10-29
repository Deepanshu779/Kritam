"""Lazy-loaded local Whisper transcription for microphone recordings."""
from __future__ import annotations

import os
import tempfile
import threading
from pathlib import Path

_model = None
_model_lock = threading.Lock()


class UnsupportedAudioError(ValueError):
    """Audio bytes are not a supported container or do not match their MIME type."""


def _audio_suffix_from_bytes(audio: bytes) -> str:
    if audio.startswith(b"\x1a\x45\xdf\xa3"):
        return ".webm"
    if len(audio) >= 12 and audio[:4] in {b"RIFF", b"RF64"} and audio[8:12] == b"WAVE":
        return ".wav"
    if audio.startswith(b"OggS"):
        return ".ogg"
    if len(audio) >= 12 and audio[4:8] == b"ftyp":
        return ".m4a" if b"M4A" in audio[8:32] else ".mp4"
    if audio.startswith(b"ID3") or (len(audio) >= 2 and audio[0] == 0xFF and (audio[1] & 0xE0) == 0xE0):
        return ".mp3"
    raise UnsupportedAudioError("The recording is not a supported WebM, WAV, OGG, MP4/M4A, or MP3 audio file.")


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


def transcribe_bytes(audio: bytes, suffix: str = "", language: str | None = None) -> dict:
    if not audio:
        raise ValueError("No audio was recorded.")
    if len(audio) > 40 * 1024 * 1024:
        raise ValueError("Recording is too large (40 MB limit).")
    detected_suffix = _audio_suffix_from_bytes(audio)
    declared_suffix = suffix.lower() if suffix else ""
    compatible_suffixes = {".mp4", ".m4a"} if detected_suffix in {".mp4", ".m4a"} else {detected_suffix}
    if declared_suffix and declared_suffix not in compatible_suffixes:
        raise UnsupportedAudioError("The recorded audio content does not match its declared media type.")
    safe_suffix = detected_suffix
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=safe_suffix, delete=False) as handle:
            handle.write(audio)
            temp_path = handle.name
        model = _get_model()
        segments, info = model.transcribe(
            temp_path,
            language=language,
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
