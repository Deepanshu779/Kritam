"""Transcript confidence and hallucination validation module for Kritam.

Validation is deliberately conservative: discard obvious artifacts and
physically implausible outputs, but avoid rejecting real short commands based
on one uncertain Whisper metric.
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
    """Validates STT transcripts without blacklisting legitimate command words."""

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
        """Reject obvious artifacts while allowing short valid speech commands."""
        if not raw_text or not raw_text.strip():
            return ValidationResult(False, "", "Empty transcript")

        text = self.CLEAN_ARTIFACTS.sub("", raw_text).strip()
        text = re.sub(r"\s+", " ", text).strip()
        if not text or self.SUBTITLE_ARTIFACTS.fullmatch(text):
            return ValidationResult(False, "", "Contains only non-speech artifacts or subtitle tags")

        # A single high no-speech probability is a useful warning, not proof of
        # hallucination. Combine it with weak decoding confidence so short but
        # valid commands are not discarded solely due to this metric.
        if (
            no_speech_prob is not None
            and no_speech_prob > self.max_no_speech_prob
            and avg_logprob is not None
            and avg_logprob < self.min_avg_logprob
        ):
            return ValidationResult(
                False, "", f"Low-confidence non-speech output "
                f"(no_speech_prob={no_speech_prob:.2f}, avg_logprob={avg_logprob:.2f})"
            )

        words = text.split()
        num_words = len(words)

        if audio_duration_s > 0:
            if audio_duration_s < 0.4 and num_words > 3:
                return ValidationResult(
                    False, "", f"Implausibly many words ({num_words}) for {audio_duration_s:.2f}s audio"
                )
            words_per_sec = num_words / audio_duration_s
            if words_per_sec > self.max_words_per_second and num_words > 4:
                return ValidationResult(False, "", f"Implausible speech rate ({words_per_sec:.1f} words/s)")

        repetition_detected, cleaned = self._check_repetition(words)
        if repetition_detected:
            return ValidationResult(False, "", "Excessive word/phrase repetition detected")

        # Compression ratio can flag repetitive outputs, but use a less
        # aggressive threshold than Whisper's own decode setting to avoid
        # dropping natural multilingual text.
        if compression_ratio is not None and compression_ratio > 2.8:
            return ValidationResult(False, "", f"Excessive compression ratio ({compression_ratio:.2f})")

        return ValidationResult(True, cleaned)

    def _check_repetition(self, words: List[str]) -> Tuple[bool, str]:
        """Detect repeated loops and collapse an exact duplicated phrase once."""
        if not words:
            return False, ""

        normalize = lambda word: re.sub(r"[^\w']+", "", word.casefold())
        lower_words = [normalize(word) for word in words]

        consecutive_count = 1
        for i in range(1, len(lower_words)):
            if lower_words[i] and lower_words[i] == lower_words[i - 1]:
                consecutive_count += 1
                if consecutive_count > self.max_consecutive_repeated_words:
                    return True, ""
            else:
                consecutive_count = 1

        # Collapse a whole phrase repeated exactly twice (e.g. "open Chrome
        # open Chrome") rather than rejecting the entire transcript.
        if len(lower_words) >= 4 and len(lower_words) % 2 == 0:
            half = len(lower_words) // 2
            if lower_words[:half] == lower_words[half:]:
                return False, " ".join(words[:half])

        if len(lower_words) >= 6:
            from collections import Counter
            counts = Counter(word for word in lower_words if word)
            if counts:
                _, freq = counts.most_common(1)[0]
                if freq / len(lower_words) > 0.65:
                    return True, ""

        return False, " ".join(words)
