import os
import re

import numpy as np
import speech_recognition as sr
from faster_whisper import WhisperModel


class SpeechToText:
    """
    Multilingual local speech recognition.

    Important design rule:
    - Never force English/Hindi/etc. at the STT layer.
    - Whisper detects the spoken language automatically.
    - Transcription stays in the language the user actually spoke.
    - Language detection is metadata for the conversation layer; it does
      not change or translate the transcript.
    """

    def __init__(self):
        self.recognizer = sr.Recognizer()
        model_name = os.getenv("KRITAM_WHISPER_MODEL", "base")

        self.model = WhisperModel(
            model_name,
            device=os.getenv("KRITAM_WHISPER_DEVICE", "cpu"),
            compute_type=os.getenv("KRITAM_WHISPER_COMPUTE", "int8"),
            cpu_threads=int(os.getenv("KRITAM_WHISPER_THREADS", "4")),
            num_workers=1,
        )

        self.last_language = None
        self.last_language_probability = 0.0

    @staticmethod
    def _clean(text):
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return ""

        # Remove obvious Whisper duplication/hallucination such as:
        # "hello hello hello hello"
        words = text.split()
        if len(words) >= 4 and len(words) % 2 == 0:
            half = len(words) // 2
            if [w.lower() for w in words[:half]] == [
                w.lower() for w in words[half:]
            ]:
                return " ".join(words[:half])

        return text

    def convert(self, audio):
        if audio is None:
            return ""

        try:
            # The voice pipeline may provide either SpeechRecognition AudioData
            # or a NumPy waveform. Support both so STT stays independent of
            # the microphone/VAD implementation.
            if isinstance(audio, np.ndarray):
                samples = np.asarray(audio, dtype=np.float32).reshape(-1)

                # Normalize integer-style or unusually scaled waveforms.
                max_input = float(np.max(np.abs(samples))) if samples.size else 0.0
                if max_input > 1.0:
                    samples = samples / 32768.0
            elif hasattr(audio, "get_raw_data"):
                raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
                samples = (
                    np.frombuffer(raw, dtype=np.int16)
                    .astype(np.float32)
                    / 32768.0
                )
            else:
                print(
                    f"Kritam STT: unsupported audio type "
                    f"{type(audio).__name__}; ignoring."
                )
                return ""

            if samples.size == 0:
                return ""

            duration = samples.size / 16000.0
            peak = float(np.max(np.abs(samples)))
            rms = float(np.sqrt(np.mean(np.square(samples))))

            # Reject only genuinely silent/noisy input. Do not reject short
            # speech just because it is short; words like "yes", "stop",
            # "haan", "okay", etc. are valid conversational turns.
            if rms < 0.0010 or peak < 0.003:
                print("Kritam STT: audio level too low; ignoring.")
                return ""

            # Normalize quiet microphones while preserving the original
            # speech shape. Avoid aggressive amplification of background noise.
            if peak > 0.003:
                gain = min(0.85 / peak, 5.0)
                samples = np.clip(samples * gain, -1.0, 1.0)

            print(
                f"Kritam STT: audio={duration:.1f}s "
                f"peak={peak:.4f} rms={rms:.4f}"
            )

            # language=None is intentional. This is what lets Kritam accept
            # English, Hindi, Hinglish, and other languages without requiring
            # a language setting before every conversation.
            segments, info = self.model.transcribe(
                samples,
                language=None,
                task="transcribe",
                beam_size=3,
                best_of=3,
                temperature=0.0,
                condition_on_previous_text=False,
                no_speech_threshold=0.85,
                log_prob_threshold=-1.5,
                compression_ratio_threshold=2.8,
                vad_filter=False,
            )

            self.last_language = getattr(info, "language", None)
            self.last_language_probability = float(
                getattr(info, "language_probability", 0.0) or 0.0
            )

            if self.last_language:
                print(
                    f"Kritam STT: detected language={self.last_language} "
                    f"confidence={self.last_language_probability:.2f}"
                )

            parts = []
            quality_scores = []

            for segment in segments:
                segment_text = (segment.text or "").strip()
                if not segment_text:
                    continue

                parts.append(segment_text)
                quality_scores.append(
                    float(getattr(segment, "avg_logprob", 0.0) or 0.0)
                )

            text = self._clean(" ".join(parts))

            if text:
                average_quality = (
                    sum(quality_scores) / len(quality_scores)
                    if quality_scores
                    else 0.0
                )
                print(
                    f'Kritam STT: "{text}" '
                    f"(avg_logprob={average_quality:.2f})"
                )
            else:
                print("Kritam STT: Whisper returned no text.")

            return text

        except Exception as error:
            print(f"Local STT error: {error}")
            return ""
