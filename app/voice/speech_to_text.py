import os
import re

import numpy as np
import speech_recognition as sr
from faster_whisper import WhisperModel

from voice.transcript_validator import TranscriptValidator
from voice.audio_processor import AudioProcessor


class SpeechToText:
    """Multilingual local speech recognition with hallucination validation."""

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
        self.validator = TranscriptValidator()
        self.audio_processor = AudioProcessor(min_speech_duration_s=0.45)
        self.last_language = None
        self.last_language_probability = 0.0
        self.last_metadata = {}

    @staticmethod
    def _clean(text):
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return ""
        words = text.split()
        if len(words) >= 4 and len(words) % 2 == 0:
            half = len(words) // 2
            if [w.lower() for w in words[:half]] == [w.lower() for w in words[half:]]:
                return " ".join(words[:half])
        return text

    @staticmethod
    def _audio_to_samples(audio):
        if isinstance(audio, np.ndarray):
            samples = np.asarray(audio, dtype=np.float32).reshape(-1)
            max_input = float(np.max(np.abs(samples))) if samples.size else 0.0
            if max_input > 1.0:
                samples = samples / 32768.0
            return samples
        if hasattr(audio, "get_raw_data"):
            raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
            return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        raise TypeError(f"unsupported audio type {type(audio).__name__}")

    def convert_with_metadata(self, audio):
        """Return (transcript, metadata) for every voice pipeline."""
        if audio is None:
            return "", {}
        try:
            samples = self._audio_to_samples(audio)
            if samples.size == 0:
                return "", {}

            samples = np.asarray(samples, dtype=np.float32).reshape(-1)
            metrics = self.audio_processor.calculate_metrics(samples)
            if metrics.is_silence:
                print("Kritam STT: rejected low-energy or too-short audio.")
                return "", {}

            samples = self.audio_processor.safe_normalize(samples)
            post_peak = float(np.max(np.abs(samples)))
            post_rms = float(np.sqrt(np.mean(np.square(samples))))

            print(
                f"Kritam STT: audio={metrics.duration_s:.2f}s peak={post_peak:.4f} "
                f"rms={post_rms:.4f}"
            )

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

            language = getattr(info, "language", None)
            language_probability = float(getattr(info, "language_probability", 0.0) or 0.0)

            parts = []
            logprobs = []
            no_speech_probs = []
            compression_ratios = []

            for segment in segments:
                segment_text = (segment.text or "").strip()
                if not segment_text:
                    continue
                parts.append(segment_text)
                logprobs.append(float(getattr(segment, "avg_logprob", 0.0) or 0.0))
                no_speech_probs.append(float(getattr(segment, "no_speech_prob", 0.0) or 0.0))
                compression_ratios.append(float(getattr(segment, "compression_ratio", 0.0) or 0.0))

            raw_text = self._clean(" ".join(parts))
            avg_logprob = sum(logprobs) / len(logprobs) if logprobs else None
            no_speech_prob = max(no_speech_probs) if no_speech_probs else None
            compression_ratio = max(compression_ratios) if compression_ratios else None

            result = self.validator.validate(
                raw_text,
                metrics.duration_s,
                avg_logprob=avg_logprob,
                no_speech_prob=no_speech_prob,
                compression_ratio=compression_ratio,
            )

            metadata = {
                "language": language,
                "language_probability": language_probability,
                "audio_duration": metrics.duration_s,
                "avg_logprob": avg_logprob,
                "no_speech_prob": no_speech_prob,
                "compression_ratio": compression_ratio,
                "valid": result.is_valid,
                "rejection_reason": result.rejection_reason,
            }
            self.last_language = language
            self.last_language_probability = language_probability
            self.last_metadata = metadata

            if language:
                print(f"Kritam STT: detected language={language} confidence={language_probability:.2f}")

            if not result.is_valid:
                print(f"Kritam STT: rejected transcript ({result.rejection_reason})")
                return "", metadata

            text = result.cleaned_text
            if text:
                quality = f"{avg_logprob:.2f}" if avg_logprob is not None else "n/a"
                print(f'Kritam STT: "{text}" (avg_logprob={quality})')
            else:
                print("Kritam STT: Whisper returned no text.")
            return text, metadata

        except Exception as error:
            print(f"Local STT error: {error}")
            self.last_metadata = {"valid": False, "error": str(error)}
            return "", self.last_metadata

    def convert(self, audio):
        """Compatibility wrapper returning only the transcript."""
        text, _ = self.convert_with_metadata(audio)
        return text
