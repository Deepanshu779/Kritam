"""Voice model initialization stays lazy and fails without crashing text mode."""

import unittest
from unittest.mock import patch

from app.voice.speech_to_text import SpeechToText


class TestSpeechToTextModelLifecycle(unittest.TestCase):
    def test_constructor_does_not_load_whisper(self):
        with patch("faster_whisper.WhisperModel") as model:
            speech_to_text = SpeechToText()

        model.assert_not_called()
        self.assertIsNone(speech_to_text.model)

    def test_model_is_loaded_once_on_first_voice_use(self):
        expected = object()
        with patch("faster_whisper.WhisperModel", return_value=expected) as model:
            speech_to_text = SpeechToText()
            self.assertIs(speech_to_text._ensure_model(), expected)
            self.assertIs(speech_to_text._ensure_model(), expected)

        model.assert_called_once()

    def test_unavailable_model_is_not_retried_each_turn(self):
        with patch("faster_whisper.WhisperModel", side_effect=RuntimeError("offline")) as model:
            speech_to_text = SpeechToText()
            self.assertIsNone(speech_to_text._ensure_model())
            self.assertIsNone(speech_to_text._ensure_model())

        model.assert_called_once()
        self.assertIsInstance(speech_to_text._model_error, RuntimeError)


if __name__ == "__main__":
    unittest.main()

