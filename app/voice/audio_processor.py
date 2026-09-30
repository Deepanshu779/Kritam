"""Audio preprocessing module for Kritam assistant.

Ensures audio is consistently converted to 16 kHz mono float32 PCM,
calculates RMS/peak levels, filters out silence/low-level noise,
and performs safe, bounded normalization without aggressive noise amplification.
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class AudioMetrics:
    duration_s: float
    peak: float
    rms: float
    is_silence: bool


class AudioProcessor:
    """Preprocesses audio data for real-time speech processing and STT."""

    TARGET_SAMPLE_RATE = 16000

    def __init__(
        self,
        silence_rms_threshold: float = 0.003,
        silence_peak_threshold: float = 0.012,
        min_speech_duration_s: float = 0.35,
        target_peak: float = 0.75,
        max_gain: float = 2.5,
    ):
        self.silence_rms_threshold = silence_rms_threshold
        self.silence_peak_threshold = silence_peak_threshold
        self.min_speech_duration_s = min_speech_duration_s
        self.target_peak = target_peak
        self.max_gain = max_gain

    def to_mono_16k_pcm(self, audio_data, sample_rate: int = 16000, sample_width: int = 2) -> np.ndarray:
        """Convert input audio into 16 kHz mono float32 array in range [-1.0, 1.0]."""
        if audio_data is None:
            return np.empty(0, dtype=np.float32)

        # Handle speech_recognition AudioData
        if hasattr(audio_data, "get_raw_data"):
            raw_bytes = audio_data.get_raw_data(
                convert_rate=self.TARGET_SAMPLE_RATE,
                convert_width=2,
            )
            samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            return samples

        # Handle numpy arrays
        if isinstance(audio_data, np.ndarray):
            samples = audio_data
            if samples.ndim > 1:
                # Downmix multichannel to mono
                samples = np.mean(samples, axis=1)

            if samples.dtype == np.int16:
                samples = samples.astype(np.float32) / 32768.0
            elif samples.dtype != np.float32:
                samples = samples.astype(np.float32)

            if sample_rate != self.TARGET_SAMPLE_RATE and len(samples) > 0:
                try:
                    from scipy.signal import resample_poly
                    from math import gcd
                    g = gcd(self.TARGET_SAMPLE_RATE, sample_rate)
                    up = self.TARGET_SAMPLE_RATE // g
                    down = sample_rate // g
                    samples = resample_poly(samples, up, down).astype(np.float32)
                except Exception:
                    # Fallback linear interpolation
                    new_len = int(len(samples) * (self.TARGET_SAMPLE_RATE / sample_rate))
                    samples = np.interp(
                        np.linspace(0, len(samples), new_len, endpoint=False),
                        np.arange(len(samples)),
                        samples,
                    ).astype(np.float32)

            return np.clip(samples, -1.0, 1.0)

        # Handle raw byte buffer
        if isinstance(audio_data, (bytes, bytearray)):
            if sample_width == 2:
                samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            elif sample_width == 1:
                samples = (np.frombuffer(audio_data, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
            elif sample_width == 4:
                samples = np.frombuffer(audio_data, dtype=np.float32)
            else:
                samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            if sample_rate != self.TARGET_SAMPLE_RATE and len(samples) > 0:
                new_len = int(len(samples) * (self.TARGET_SAMPLE_RATE / sample_rate))
                samples = np.interp(
                    np.linspace(0, len(samples), new_len, endpoint=False),
                    np.arange(len(samples)),
                    samples,
                ).astype(np.float32)

            return np.clip(samples, -1.0, 1.0)

        return np.empty(0, dtype=np.float32)

    def calculate_metrics(self, samples: np.ndarray) -> AudioMetrics:
        """Compute duration, peak amplitude, and RMS energy."""
        if samples is None or len(samples) == 0:
            return AudioMetrics(duration_s=0.0, peak=0.0, rms=0.0, is_silence=True)

        duration_s = float(len(samples)) / float(self.TARGET_SAMPLE_RATE)
        peak = float(np.max(np.abs(samples)))
        rms = float(np.sqrt(np.mean(np.square(samples))))

        is_silence = (
            rms < self.silence_rms_threshold
            or peak < self.silence_peak_threshold
            or duration_s < self.min_speech_duration_s
        )

        return AudioMetrics(
            duration_s=duration_s,
            peak=peak,
            rms=rms,
            is_silence=is_silence,
        )

    def safe_normalize(self, samples: np.ndarray) -> np.ndarray:
        """Safely normalize audio without amplifying background noise into hiss.
        
        If peak is below noise floor threshold, leave unamplified.
        If a clear voice signal is present, apply moderate bounded gain.
        """
        if samples is None or len(samples) == 0:
            return samples

        peak = float(np.max(np.abs(samples)))

        # Do not amplify quiet ambient noise or true silence
        if peak < self.silence_peak_threshold:
            return samples

        # If already well-leveled, avoid changes
        if peak >= self.target_peak:
            return np.clip(samples, -1.0, 1.0)

        # Apply moderate, safe gain with ceiling
        gain = min(self.target_peak / peak, self.max_gain)
        normalized = samples * gain
        return np.clip(normalized, -1.0, 1.0)
