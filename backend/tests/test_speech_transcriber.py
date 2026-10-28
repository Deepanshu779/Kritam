import pytest
from app.services.speech.transcriber import transcribe_bytes


def test_transcriber_rejects_empty_recording():
    with pytest.raises(ValueError, match="No audio"):
        transcribe_bytes(b"")


def test_transcriber_rejects_oversized_recording():
    with pytest.raises(ValueError, match="40 MB"):
        transcribe_bytes(b"x" * (40 * 1024 * 1024 + 1))
