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


def test_transcriber_uses_vocabulary_prompt_beam_search_and_speech_padding(monkeypatch):
    import types
    import app.services.speech.transcriber as transcriber

    observed = {}

    class FakeModel:
        def transcribe(self, path, **kwargs):
            observed.update(kwargs)
            segment = types.SimpleNamespace(
                text=" Hey Kritam, open Chrome. ", avg_logprob=-0.2,
                no_speech_prob=0.01, compression_ratio=1.2,
            )
            info = types.SimpleNamespace(language="en", language_probability=0.98)
            return iter([segment]), info

    monkeypatch.setattr(transcriber, "_get_model", lambda model_name=None: FakeModel())
    result = transcriber.transcribe_bytes(b"\x1a\x45\xdf\xa3" + b"\x00" * 20, ".webm", model_name="small")
    assert result["text"] == "Hey Kritam, open Chrome."
    assert result["command_confident"] is True
    assert observed["beam_size"] == 5
    assert observed["best_of"] == 5
    assert observed["vad_parameters"]["speech_pad_ms"] == 400
    assert "Kritam" in observed["initial_prompt"]


def test_transcriber_rejects_unapproved_model_name():
    import pytest
    from app.services.speech.transcriber import _get_model

    with pytest.raises(ValueError, match="base.*small"):
        _get_model("large-v3")


def test_low_quality_decoder_output_cannot_auto_trigger_a_command(monkeypatch):
    import types
    import app.services.speech.transcriber as transcriber

    class LowConfidenceModel:
        def transcribe(self, path, **kwargs):
            segment = types.SimpleNamespace(
                text="Hey Kritam, open Chrome", avg_logprob=-1.1,
                no_speech_prob=0.55, compression_ratio=1.3,
            )
            info = types.SimpleNamespace(language="en", language_probability=0.75)
            return iter([segment]), info

    monkeypatch.setattr(transcriber, "_get_model", lambda model_name=None: LowConfidenceModel())
    result = transcriber.transcribe_bytes(b"\x1a\x45\xdf\xa3" + b"\x00" * 20, ".webm")
    assert result["text"].startswith("Hey Kritam")
    assert result["command_confident"] is False
