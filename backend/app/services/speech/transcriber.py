"""Lazy-loaded local Whisper transcription for microphone recordings."""
from __future__ import annotations

import os
import tempfile
import threading
from pathlib import Path

_model = None
_model_name: str | None = None
_model_lock = threading.Lock()
_inference_lock = threading.Lock()


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


def _get_model(model_name: str | None = None):
    global _model, _model_name
    selected = model_name or os.getenv("KRITAM_STT_MODEL", "base")
    if selected not in {"base", "small"}:
        raise ValueError("Speech model must be 'base' or 'small'.")
    if _model is None or _model_name != selected:
        with _model_lock:
            if _model is None or _model_name != selected:
                from faster_whisper import WhisperModel
                _model = WhisperModel(
                    selected,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=max(2, min(8, os.cpu_count() or 4)),
                )
                _model_name = selected
    return _model


def transcribe_bytes(audio: bytes, suffix: str = "", language: str | None = None, model_name: str | None = None) -> dict:
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
        with _inference_lock:
            model = _get_model(model_name)
            segments, info = model.transcribe(
                temp_path,
                language=language,
                beam_size=5,
                best_of=5,
                vad_filter=True,
                vad_parameters={"threshold": 0.5, "min_silence_duration_ms": 500, "speech_pad_ms": 400},
                condition_on_previous_text=False,
                initial_prompt="Kritam. Hey Kritam. Google Chrome, YouTube, YouTube Music, Spotify, Visual Studio Code, File Explorer.",
            )
            decoded_segments = list(segments)
        text = " ".join(segment.text.strip() for segment in decoded_segments).strip()
        # These decoder diagnostics are only a conservative command gate, not
        # a calibrated word-confidence score. Low quality transcripts remain
        # available for review but must not trigger desktop actions.
        command_confident = bool(decoded_segments) and all(
            getattr(segment, "avg_logprob", -99) >= -0.8
            and getattr(segment, "no_speech_prob", 1) < 0.4
            and getattr(segment, "compression_ratio", 99) < 2.4
            for segment in decoded_segments
        )
        return {
            "text": text,
            "language": info.language,
            "language_probability": info.language_probability,
            "command_confident": command_confident,
        }
    finally:
        if temp_path:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except OSError:
                pass
