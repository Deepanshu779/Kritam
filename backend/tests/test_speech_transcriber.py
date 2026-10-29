import pytest
from app.services.speech.transcriber import UnsupportedAudioError, transcribe_bytes


def test_transcriber_rejects_empty_recording():
    with pytest.raises(ValueError, match="No audio"):
        transcribe_bytes(b"")


def test_transcriber_rejects_oversized_recording():
    with pytest.raises(ValueError, match="40 MB"):
        transcribe_bytes(b"x" * (40 * 1024 * 1024 + 1))


def test_transcriber_rejects_unknown_container_before_loading_model():
    with pytest.raises(UnsupportedAudioError, match="not a supported"):
        transcribe_bytes(b"not an audio recording")


def test_transcriber_rejects_mime_suffix_that_does_not_match_content():
    webm_header = b"\x1a\x45\xdf\xa3" + b"\x00" * 16
    with pytest.raises(UnsupportedAudioError, match="does not match"):
        transcribe_bytes(webm_header, ".wav")
