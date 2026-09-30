import os
import re
import speech_recognition as sr
import numpy as np
from faster_whisper import WhisperModel


class SpeechToText:

    def __init__(self):
        self.recognizer = sr.Recognizer()
        model_name = os.getenv("KRITAM_WHISPER_MODEL", "base")
        self.model = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8",
            cpu_threads=4,
            num_workers=1,
        )

    def _clean(self, text):
        text = re.sub(r"\s+", " ", text).strip()
        words = text.lower().split()

        if len(words) >= 4 and len(words) % 2 == 0:
            half = len(words) // 2
            if words[:half] == words[half:]:
                return " ".join(words[:half])

        return text

    def convert(self, audio):
        if audio is None:
            return ""

        try:
            raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

            if samples.size == 0:
                return ""

            peak = float(np.max(np.abs(samples)))
            rms = float(np.sqrt(np.mean(np.square(samples))))

            # Very quiet recordings are usually ambient noise or speaker
            # bleed, not a deliberate command.
            if rms < 0.0012 or peak < 0.004:
                print("Kritam STT: audio level too low; ignoring.")
                return ""

            if peak > 0.003:
                samples = samples * min(0.85 / peak, 6.0)
                samples = np.clip(samples, -1.0, 1.0)

            print(
                f"Kritam STT: audio={len(samples) / 16000:.1f}s "
                f"peak={peak:.4f} rms={rms:.4f}"
            )

            segments, _ = self.model.transcribe(
                samples,
                language=None,
                beam_size=5,
                best_of=5,
                temperature=0.0,
                condition_on_previous_text=False,
                no_speech_threshold=0.6,
                log_prob_threshold=-1.0,
                compression_ratio_threshold=2.4,
            )

            parts = [segment.text.strip() for segment in segments if segment.text.strip()]
            text = " ".join(parts)

            if text:
                print(f"Kritam STT recognized: {text}")
            else:
                print("Kritam STT: Whisper returned no text.")

            return self._clean(text)

        except Exception as error:
            print(f"Local STT error: {error}")
            return ""
