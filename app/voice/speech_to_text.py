import os
import re
import speech_recognition as sr
import numpy as np
from faster_whisper import WhisperModel


class SpeechToText:

    def __init__(self):
        self.recognizer = sr.Recognizer()

        model_name = os.getenv("KRITAM_WHISPER_MODEL", "tiny.en")
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

        # Remove accidental duplicated phrases.
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

            segments, _ = self.model.transcribe(
                samples,
                language="en",
                beam_size=1,
                best_of=1,
                temperature=0.0,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=150,
                    speech_pad_ms=150,
                ),
                condition_on_previous_text=False,
                initial_prompt="Kritam, open Chrome, YouTube, Spotify, Google, Calculator, Notepad, play music.",
            )

            text = " ".join(segment.text for segment in segments)
            return self._clean(text)

        except Exception as error:
            print(f"Local STT error: {error}")
            return ""

        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
