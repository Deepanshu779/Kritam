"""Conversation Voice Controller for Kritam assistant.

Coordinates speech turn capture, STT transcription, assistant execution,
and conversational speech flow while ensuring TTS echo suppression.
"""

import threading
from typing import Callable, Optional
from voice.listener import VoiceListener
from voice.speech_to_text import SpeechToText
from voice.text_to_speech import TextToSpeech


class ConversationVoiceController:
    """Orchestrates natural voice conversation turns and state transitions."""

    STOP_PHRASES = {
        "stop listening",
        "stop listening kritam",
        "that's all",
        "thats all",
        "you can stop",
        "goodbye",
        "bye kritam",
        "band karo",
        "ruko",
        "chup",
    }

    def __init__(
        self,
        assistant,
        listener: Optional[VoiceListener] = None,
        speech_to_text: Optional[SpeechToText] = None,
        text_to_speech: Optional[TextToSpeech] = None,
    ):
        self.assistant = assistant
        self.listener = listener or assistant.listener
        self.speech_to_text = speech_to_text or assistant.speech_to_text
        self.text_to_speech = text_to_speech or assistant.text_to_speech

        # Link TTS to listener for echo suppression
        if self.listener and self.text_to_speech:
            self.listener.set_tts(self.text_to_speech)

    def capture_and_transcribe(self, stop_event: threading.Event) -> str:
        """Capture one speech turn and transcribe to text."""
        audio = self.listener.listen_until_stopped(stop_event)
        if audio is None or stop_event.is_set():
            return ""

        text = self.speech_to_text.convert(audio)
        return text or ""

    def is_stop_phrase(self, text: str) -> bool:
        """Check if user requested to end the voice conversation."""
        normalized = text.lower().strip(" ,.!?")
        return normalized in self.STOP_PHRASES
