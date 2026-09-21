import os
import re
import tempfile

import speech_recognition as sr
from faster_whisper import WhisperModel


class SpeechToText:

    def __init__(self):
        self.recognizer = sr.Recognizer()

        # Small local model for a good balance between latency and accuracy.
        # The model is downloaded once and then runs locally.
        self.model = WhisperModel(
            "small.en",
            device="cpu",
            compute_type="int8",
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

        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False,
            ) as temp_file:
                temp_file.write(audio.get_wav_data())
                temp_path = temp_file.name

            segments, _ = self.model.transcribe(
                temp_path,
                language="en",
                beam_size=1,
                vad_filter=True,
                condition_on_previous_text=False,
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
