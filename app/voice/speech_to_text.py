"""Speech to text engine for Kritam AI Assistant using faster-whisper.

Features:
- Configurable Whisper model via KRITAM_WHISPER_MODEL (tiny, base, small, medium)
- Multilingual and code-switching support (English, Hindi, Hinglish)
- Built-in VAD pre-filtering to prevent hallucination during silence/noise
- Safe audio preprocessing without aggressive noise amplification
- Hallucination and repetition filtering through TranscriptValidator
- Detailed developer logging
"""

import os
import re
from typing import Optional, Tuple
import numpy as np
from faster_whisper import WhisperModel

from voice.audio_processor import AudioProcessor
from voice.transcript_validator import TranscriptValidator


class SpeechToText:
    """Production-grade Whisper STT engine with preprocessing and validation."""

    INITIAL_PROMPT = (
        "Kritam, open Chrome, YouTube, Google, calculator, screenshot, songs, "
        "gaane chala do, kholo, search karo, play music."
    )

    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.validator = TranscriptValidator()
        self.model_name = os.getenv("KRITAM_WHISPER_MODEL", "base").strip().lower()

        # Sanitize model name
        allowed_models = {"tiny", "base", "small", "medium"}
        if self.model_name not in allowed_models:
            self.model_name = "base"

        print(f"[Kritam STT] Initializing faster-whisper model '{self.model_name}' on CPU (int8)...")
        self.model = WhisperModel(
            self.model_name,
            device="cpu",
            compute_type="int8",
            cpu_threads=4,
            num_workers=1,
        )
        print(f"[Kritam STT] Model '{self.model_name}' loaded successfully.")

    def convert(self, audio) -> str:
        """Convert audio input (sr.AudioData, bytes, or numpy array) into validated text."""
        text, _ = self.convert_with_metadata(audio)
        return text

    def convert_with_metadata(self, audio) -> Tuple[str, dict]:
        """Convert audio and return both validated transcript and audio/confidence metadata."""
        if audio is None:
            return "", {}

        try:
            samples = self.audio_processor.to_mono_16k_pcm(audio)
            if samples.size == 0:
                return "", {}

            metrics = self.audio_processor.calculate_metrics(samples)

            # Silence rejection: do not waste Whisper CPU cycles on silence/ambient hum
            if metrics.is_silence:
                print(
                    f"[Kritam STT] audio rejected: silence/noise "
                    f"(duration={metrics.duration_s:.1f}s, RMS={metrics.rms:.4f}, peak={metrics.peak:.4f})"
                )
                return "", {"duration_s": metrics.duration_s, "rejected": "silence"}

            # Safe normalization (bounded gain, no noise amplification)
            processed_samples = self.audio_processor.safe_normalize(samples)

            print(
                f"[Kritam STT] audio duration: {metrics.duration_s:.1f}s | "
                f"RMS: {metrics.rms:.4f} | peak: {metrics.peak:.4f}"
            )

            # Transcribe with faster-whisper using integrated VAD filter
            segments, info = self.model.transcribe(
                processed_samples,
                language=None,  # Auto-detect English, Hindi, Hinglish
                initial_prompt=self.INITIAL_PROMPT,
                beam_size=5,
                best_of=5,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=450,
                    speech_pad_ms=200,
                ),
                no_speech_threshold=0.6,
                log_prob_threshold=-1.0,
                compression_ratio_threshold=2.4,
            )

            segment_list = list(segments)
            if not segment_list:
                print("[Kritam STT] Whisper returned no speech segments.")
                return "", {"duration_s": metrics.duration_s, "detected_language": info.language}

            # Aggregate segment texts and statistics
            text_parts = []
            logprobs = []
            no_speech_probs = []
            compression_ratios = []

            for seg in segment_list:
                t = seg.text.strip()
                if t:
                    text_parts.append(t)
                    if hasattr(seg, "avg_logprob") and seg.avg_logprob is not None:
                        logprobs.append(seg.avg_logprob)
                    if hasattr(seg, "no_speech_prob") and seg.no_speech_prob is not None:
                        no_speech_probs.append(seg.no_speech_prob)
                    if hasattr(seg, "compression_ratio") and seg.compression_ratio is not None:
                        compression_ratios.append(seg.compression_ratio)

            raw_transcript = " ".join(text_parts).strip()
            avg_logprob = float(np.mean(logprobs)) if logprobs else None
            avg_no_speech = float(np.mean(no_speech_probs)) if no_speech_probs else None
            avg_compression = float(np.mean(compression_ratios)) if compression_ratios else None

            # Validate transcript to guard against hallucinations and loops
            validation = self.validator.validate(
                raw_text=raw_transcript,
                audio_duration_s=metrics.duration_s,
                avg_logprob=avg_logprob,
                no_speech_prob=avg_no_speech,
                compression_ratio=avg_compression,
            )

            if not validation.is_valid:
                print(f"[Kritam Voice] transcript rejected: {validation.rejection_reason}")
                return "", {
                    "duration_s": metrics.duration_s,
                    "rejected": validation.rejection_reason,
                    "raw_text": raw_transcript,
                }

            final_text = validation.cleaned_text
            print(f"[Kritam STT] transcript: \"{final_text}\"")
            if avg_logprob is not None:
                no_sp = f"{avg_no_speech:.2f}" if avg_no_speech is not None else "N/A"
                print(
                    f"[Kritam STT] confidence/quality: "
                    f"avg_logprob={avg_logprob:.2f}, no_speech_prob={no_sp}"
                )

            metadata = {
                "duration_s": metrics.duration_s,
                "detected_language": info.language,
                "avg_logprob": avg_logprob,
                "no_speech_prob": avg_no_speech,
            }
            return final_text, metadata

        except Exception as error:
            print(f"[Kritam STT] Local STT error: {error}")
            return "", {"error": str(error)}