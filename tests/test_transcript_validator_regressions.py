"""Regression tests for transcript validation of real short commands."""

import unittest

from app.voice.transcript_validator import TranscriptValidator


class TestTranscriptValidatorRegressions(unittest.TestCase):
    def setUp(self):
        self.validator = TranscriptValidator()

    def test_short_command_survives_high_no_speech_probability_alone(self):
        result = self.validator.validate(
            "YouTube", 1.1, avg_logprob=-0.17, no_speech_prob=0.66
        )
        self.assertTrue(result.is_valid, result.rejection_reason)
        self.assertEqual(result.cleaned_text, "YouTube")

    def test_short_command_with_low_confidence_and_high_no_speech_is_rejected(self):
        result = self.validator.validate(
            "maybe something", 1.1, avg_logprob=-1.8, no_speech_prob=0.9
        )
        self.assertFalse(result.is_valid)

    def test_repeated_phrase_is_collapsed(self):
        result = self.validator.validate("open Chrome open Chrome", 2.0)
        self.assertTrue(result.is_valid, result.rejection_reason)
        self.assertEqual(result.cleaned_text, "open Chrome")

    def test_repeated_single_word_loop_is_rejected(self):
        result = self.validator.validate("YouTube YouTube YouTube YouTube", 2.0)
        self.assertFalse(result.is_valid)

    def test_normal_hinglish_command_is_preserved(self):
        phrase = "Google par Python search kar do"
        result = self.validator.validate(phrase, 2.5)
        self.assertTrue(result.is_valid, result.rejection_reason)
        self.assertEqual(result.cleaned_text, phrase)


if __name__ == "__main__":
    unittest.main()
