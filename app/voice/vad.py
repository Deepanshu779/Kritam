"""Voice Activity Detection (VAD) module for Kritam assistant."""

import collections
from typing import List, Optional, Tuple
import numpy as np


class SpeechActivityDetector:
    """Frame-level voice activity detector with adaptive thresholding."""

    def __init__(
        self,
        sample_rate: int = 16000,
        frame_duration_ms: int = 30,
        onset_consecutive_frames: int = 3,
        hangover_duration_s: float = 1.0,
        min_speech_duration_s: float = 0.5,
        max_utterance_duration_s: float = 22.0,
        pre_roll_duration_s: float = 0.45,
        base_energy_threshold: float = 0.0025,
    ):
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(sample_rate * (frame_duration_ms / 1000.0))
        self.onset_consecutive_frames = onset_consecutive_frames
        self.hangover_frames = int(hangover_duration_s / (frame_duration_ms / 1000.0))
        self.min_speech_frames = int(min_speech_duration_s / (frame_duration_ms / 1000.0))
        self.max_utterance_frames = int(max_utterance_duration_s / (frame_duration_ms / 1000.0))
        self.pre_roll_max_frames = max(1, int(pre_roll_duration_s / (frame_duration_ms / 1000.0)))
        self.base_energy_threshold = base_energy_threshold

        # Pre-roll ring buffer
        self._pre_roll_buffer = collections.deque(maxlen=self.pre_roll_max_frames)

        # State tracking
        self.noise_floor = min(0.0015, self.base_energy_threshold * 0.6)
        self.alpha_noise = 0.05  # EMA smoothing factor for background noise
        self.speech_active = False
        self.consecutive_speech_frames = 0
        self.speech_frame_count = 0
        self.silence_counter = 0
        self.active_frames: List[np.ndarray] = []

    def reset(self):
        """Reset internal speech state for a new capture session."""
        self._pre_roll_buffer.clear()
        self.speech_active = False
        self.consecutive_speech_frames = 0
        self.speech_frame_count = 0
        self.silence_counter = 0
        self.active_frames.clear()

    def is_frame_speech(self, frame: np.ndarray) -> Tuple[bool, float]:
        """Classify a single frame as speech or non-speech based on energy."""
        if len(frame) == 0:
            return False, 0.0

        rms = float(np.sqrt(np.mean(np.square(frame))))
        peak = float(np.max(np.abs(frame)))

        # Laptop/headset microphones can produce quiet speech with RMS around
        # 0.004-0.010. Keep the absolute floor low and use the noise floor
        # relative to the live microphone signal.
        start_threshold = max(
            self.base_energy_threshold,
            self.noise_floor * 1.4 + 0.0006,
        )
        continue_threshold = max(
            self.base_energy_threshold * 0.8,
            self.noise_floor * 1.2 + 0.0004,
        )
        dynamic_threshold = continue_threshold if self.speech_active else start_threshold

        peak_gate = max(dynamic_threshold * 1.1, self.base_energy_threshold * 1.05)
        is_speech = (rms > dynamic_threshold) and (peak > peak_gate)

        # Update noise floor adaptively when non-speech is detected
        if not is_speech:
            self.noise_floor = (1.0 - self.alpha_noise) * self.noise_floor + self.alpha_noise * rms
            self.noise_floor = max(0.001, min(self.noise_floor, 0.05))

        return is_speech, rms

    def process_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Process an audio frame. Returns completed utterance array if speech turn ended, else None."""
        is_speech, _ = self.is_frame_speech(frame)

        if not self.speech_active:
            self._pre_roll_buffer.append(frame.copy())
            # Currently in idle / listening for speech onset
            if is_speech:
                self.consecutive_speech_frames += 1
                if self.consecutive_speech_frames >= self.onset_consecutive_frames:
                    # Speech turn started!
                    self.speech_active = True
                    self.silence_counter = 0
                    self.active_frames = list(self._pre_roll_buffer)
                    self.speech_frame_count = self.consecutive_speech_frames
                    self.consecutive_speech_frames = 0
            else:
                self.consecutive_speech_frames = 0
            return None

        # Speech is currently active
        self.active_frames.append(frame.copy())

        if is_speech:
            self.silence_counter = 0
            self.speech_frame_count += 1
        else:
            self.silence_counter += 1

        # Check if user reached trailing pause (turn completed)
        if self.silence_counter >= self.hangover_frames:
            utterance = self._finalize_utterance()
            self.reset()
            return utterance

        # Check max utterance limit
        if len(self.active_frames) >= self.max_utterance_frames:
            utterance = self._finalize_utterance()
            self.reset()
            return utterance

        return None

    def force_finalize(self) -> Optional[np.ndarray]:
        """Finalize the current utterance immediately."""
        if not self.active_frames:
            return None
        utterance = self._finalize_utterance()
        self.reset()
        return utterance

    def _finalize_utterance(self) -> Optional[np.ndarray]:
        """Concatenate frames and validate minimum duration."""
        if self.speech_frame_count < self.min_speech_frames:
            return None

        # Exclude trailing hangover silence frames from final audio
        trailing_trim = max(0, self.silence_counter - 3)
        cutoff = max(1, len(self.active_frames) - trailing_trim)
        frames_to_keep = self.active_frames[:cutoff]

        if not frames_to_keep:
            return None

        return np.concatenate(frames_to_keep, axis=0).astype(np.float32)
