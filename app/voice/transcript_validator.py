"""Transcript confidence and hallucination validation module for Kritam assistant.

Validates STT transcripts against audio characteristics and Whisper metrics:
- Rejects noise-induced hallucinations and phantom transcripts
- Detects repetitive word loops and phrase repetitions
- Validates plausible speech rate vs audio duration
- Filters subtitle/silence artifacts
- NEVER blacklists legitimate application names or user commands (e.g. 'YouTube', 'Microsoft', 'Google', 'Chrome')
"""

from dataclasses import dataclass
import re
from typing import List, Optional, Tuple


@dataclass
class ValidationResult:
    is_valid: bool
    cleaned_text: str
    rejection_reason: Optional[str] = None


class TranscriptValidator:
    """Validates STT transcripts to eliminate Whisper hallucinations and repetitions."""

    SUBTITLE_ARTIFACTS = re.compile(
        r"^(?:\[.*?\]|\(.*?\)|[\s*._~–—-])+$",
        re.IGNORECASE,
    )

    CLEAN_ARTIFACTS = re.compile(r"\[.*?\]|\(.*?\)")

    def __init__(
        self,
        max_words_per_second: float = 6.2,
        min_avg_logprob: float = -1.25,
        max_no_speech_prob: float = 0.68,
        max_consecutive_repeated_words: int = 2,
    ):
        self.max_words_per_second = max_words_per_second
        self.min_avg_logprob = min_avg_logprob
        self.max_no_speech_prob = max_no_speech_prob
        self.max_consecutive_repeated_words = max_consecutive_repeated_words

    def validate(
        self,
        raw_text: str,
        audio_duration_s: float,
        avg_logprob: Optional[float] = None,
        no_speech_prob: Optional[float] = None,
        compression_ratio: Optional[float] = None,
    ) -> ValidationResult:
        """Validate transcript against audio duration and Whisper confidence metrics."""
        if not raw_text or not raw_text.strip():
            return ValidationResult(is_valid=False, cleaned_text="", rejection_reason="Empty transcript")

        # Strip bracketed subtitle artifacts like [Music] or (applause)
        text = self.CLEAN_ARTIFACTS.sub("", raw_text).strip()
        text = re.sub(r"\s+", " ", text).strip()

        if not text or self.SUBTITLE_ARTIFACTS.match(text):
            return ValidationResult(
                is_valid=False,
                cleaned_text="",
                rejection_reason="Contains only non-speech artifacts or subtitle tags",
            )

        # Confidence checks from Whisper metadata
        if no_speech_prob is not None and no_speech_prob > self.max_no_speech_prob:
            return ValidationResult(
                is_valid=False,
                cleaned_text="",
                rejection_reason=f"High no-speech probability ({no_speech_prob:.2f})",
            )

        if avg_logprob is not None and avg_logprob < self.min_avg_logprob:
            # Low confidence decoding
            if no_speech_prob is not None and no_speech_prob > 0.4:
                return ValidationResult(
                    is_valid=False,
                    cleaned_text="",
                    rejection_reason=f"Low speech confidence (logprob: {avg_logprob:.2f})",
                )

        words = text.split()
        num_words = len(words)

        # Duration vs word count plausibility check
        if audio_duration_s > 0:
            if audio_duration_s < 0.4 and num_words > 3:
                return ValidationResult(
                    is_valid=False,
                    cleaned_text="",
                    rejection_reason=f"Implausibly many words ({num_words}) for {audio_duration_s:.2f}s audio",
                )

            words_per_sec = num_words / audio_duration_s
            if words_per_sec > self.max_words_per_second and num_words > 4:
                return ValidationResult(
                    is_valid=False,
                    cleaned_text="",
                    rejection_reason=f"Implausible speech rate ({words_per_sec:.1f} words/s)",
                )

        # Repetition and hallucination loop detection
        repetition_detected, cleaned_after_dedup = self._check_repetition(words)
        if repetition_detected:
            return ValidationResult(
                is_valid=False,
                cleaned_text="",
                rejection_reason="Excessive word/phrase repetition detected",
            )

        # Compression ratio check from Whisper
        if compression_ratio is not None and compression_ratio > 2.5:
            # Unusually high compression ratio indicates repetitive looping
            return ValidationResult(
                is_valid=False,
                cleaned_text="",
                rejection_reason=f"Excessive compression ratio ({compression_ratio:.2f})",
            )

        return ValidationResult(is_valid=True, cleaned_text=cleaned_after_dedup)

    def _check_repetition(self, words: List[str]) -> Tuple[bool, str]:
        """Detect excessive identical word loops or repetitive phrase cycles."""
        if not words:
            return False, ""

        lower_words = [w.lower().strip(".,!?;:") for w in words]

        # 1. Consecutive word repetition check (e.g. "word word word word")
        consecutive_count = 1
        for i in range(1, len(lower_words)):
            if lower_words[i] and lower_words[i] == lower_words[i - 1]:
                consecutive_count += 1
                if consecutive_count > self.max_consecutive_repeated_words:
                    # 3 or more consecutive identical words
                    return True, ""
            else:
                consecutive_count = 1

        # 2. Phrase-level repeating loop check (e.g. "open chrome open chrome")
        if len(lower_words) >= 4 and len(lower_words) % 2 == 0:
            half = len(lower_words) // 2
            if lower_words[:half] == lower_words[half:]:
                # User or Whisper repeated identical phrase
                return False, " ".join(words[:half])

        # 3. Overall single-word dominance check (e.g. "the the cat the the the the")
        if len(lower_words) >= 6:
            from collections import Counter
            counts = Counter(lower_words)
            most_common_word, freq = counts.most_common(1)[0]
            if freq / len(lower_words) > 0.65:
                return True, ""

        return False, " ".join(words)
