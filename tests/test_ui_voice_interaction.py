"""Unit tests for modern ChatGPT/Gemini-style voice input experience and UI state machine."""

import os
import sys
import unittest
import threading
from unittest.mock import MagicMock, patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

# Ensure QApplication singleton exists for PySide6 tests
APP = QApplication.instance() or QApplication([])

from app.ui.main_window import VoiceRecordingBar, Worker, MainWindow


class FakeAudioListener:
    def __init__(self, audio_data=b"dummy_pcm", should_raise=False):
        self.audio_data = audio_data
        self.should_raise = should_raise
        self.speech_callback_invoked = False

    def listen_until_stopped(self, stop_event, timeout=12.0, on_speech_detected=None):
        if self.should_raise:
            raise RuntimeError("Microphone device disconnected")
        if on_speech_detected:
            self.speech_callback_invoked = True
            on_speech_detected()
        if stop_event.is_set():
            return None
        return self.audio_data


class FakeSpeechToText:
    def __init__(self, text="Open Chrome"):
        self.text = text

    def convert(self, audio):
        return self.text


class FakeTextToSpeech:
    def __init__(self):
        self.on_start = None
        self.on_end = None
        self.spoken = []

    def speak(self, text, block=True):
        self.spoken.append(text)
        if callable(self.on_start):
            self.on_start(text)
        if callable(self.on_end):
            self.on_end()


class FakeAssistant:
    def __init__(self, audio_data=b"dummy_pcm", stt_text="Open Chrome", should_raise=False):
        self.listener = FakeAudioListener(audio_data=audio_data, should_raise=should_raise)
        self.speech_to_text = FakeSpeechToText(text=stt_text)
        self.text_to_speech = FakeTextToSpeech()
        self.settings = {"wake_word_enabled": False}

    def process_text(self, text, speak=True):
        if speak:
            self.text_to_speech.speak(f"Opening {text}.")
        return {"success": True, "response": f"Opening {text}."}

    def _speak(self, text):
        self.text_to_speech.speak(text)


class TestVoiceRecordingBar(unittest.TestCase):
    def setUp(self):
        self.bar = VoiceRecordingBar()

    def test_initial_state(self):
        self.assertEqual(self.bar.status_label.text(), "Listening...")
        self.assertIsNotNone(self.bar.wave)
        self.assertIsNotNone(self.bar.cancel_button)
        self.assertIsNotNone(self.bar.finish_button)

    def test_state_transitions(self):
        # LISTENING
        self.bar.set_state("LISTENING")
        self.assertEqual(self.bar.status_label.text(), "Listening...")
        self.assertTrue(self.bar.wave._timer.isActive())

        # SPEECH_DETECTED
        self.bar.set_state("SPEECH_DETECTED")
        self.assertEqual(self.bar.status_label.text(), "Listening...")
        self.assertTrue(self.bar.wave._timer.isActive())

        # PROCESSING
        self.bar.set_state("PROCESSING")
        self.assertEqual(self.bar.status_label.text(), "Thinking...")
        self.assertFalse(self.bar.wave._timer.isActive())

        # SPEAKING
        self.bar.set_state("SPEAKING")
        self.assertEqual(self.bar.status_label.text(), "Speaking...")
        self.assertTrue(self.bar.wave._timer.isActive())

        # ERROR
        self.bar.set_state("ERROR")
        self.assertEqual(self.bar.status_label.text(), "Something went wrong")
        self.assertFalse(self.bar.wave._timer.isActive())

        # IDLE
        self.bar.set_state("IDLE")
        self.assertEqual(self.bar.status_label.text(), "Click microphone to talk")
        self.assertFalse(self.bar.wave._timer.isActive())

    def test_buttons_emit_signals(self):
        cancel_called = []
        finish_called = []
        self.bar.cancel_requested.connect(lambda: cancel_called.append(True))
        self.bar.finish_requested.connect(lambda: finish_called.append(True))

        self.bar.cancel_button.click()
        self.assertEqual(len(cancel_called), 1)

        self.bar.finish_button.click()
        self.assertEqual(len(finish_called), 1)


class TestWorkerVoiceLifecycle(unittest.TestCase):
    def test_single_turn_natural_conversation(self):
        assistant = FakeAssistant(audio_data=b"valid_audio", stt_text="Open Chrome")
        worker = Worker(assistant, listen=True)

        states = []
        transcripts = []
        finished = []
        worker.state_changed.connect(states.append)
        worker.transcript_ready.connect(transcripts.append)
        worker.finished.connect(finished.append)

        worker.run()

        # Check state transitions
        self.assertIn("LISTENING", states)
        self.assertIn("SPEECH_DETECTED", states)
        self.assertIn("PROCESSING", states)
        self.assertIn("SPEAKING", states)

        # Transcribed user utterance posted before processing completes
        self.assertEqual(transcripts, ["Open Chrome"])

        # Finished signal with results
        self.assertEqual(len(finished), 1)
        self.assertEqual(finished[0]["kind"], "voice")
        self.assertEqual(finished[0]["text"], "Open Chrome")
        self.assertEqual(finished[0]["response"], "Opening Open Chrome.")

    def test_cancellation_during_listening(self):
        assistant = FakeAssistant(audio_data=b"valid_audio", stt_text="Open Chrome")
        worker = Worker(assistant, listen=True)

        finished = []
        transcripts = []
        worker.transcript_ready.connect(transcripts.append)
        worker.finished.connect(finished.append)

        # User cancels immediately
        worker.cancel()
        worker.run()

        # Cancellation must not transcribe or execute
        self.assertEqual(transcripts, [])
        self.assertEqual(len(finished), 1)
        self.assertEqual(finished[0]["kind"], "cancelled")
        self.assertEqual(assistant.text_to_speech.spoken, [])

    def test_no_speech_detected(self):
        assistant = FakeAssistant(audio_data=None)
        worker = Worker(assistant, listen=True)

        finished = []
        worker.finished.connect(finished.append)

        worker.run()

        self.assertEqual(len(finished), 1)
        self.assertEqual(finished[0]["kind"], "no_speech")

    def test_stop_phrase_handling(self):
        assistant = FakeAssistant(audio_data=b"valid_audio", stt_text="stop listening")
        worker = Worker(assistant, listen=True)

        transcripts = []
        finished = []
        worker.transcript_ready.connect(transcripts.append)
        worker.finished.connect(finished.append)

        worker.run()

        self.assertEqual(transcripts, ["stop listening"])
        self.assertEqual(len(finished), 1)
        self.assertEqual(finished[0]["kind"], "voice_end")
        self.assertIn("stop listening", assistant.text_to_speech.spoken[0])

    def test_multilingual_input_hinglish(self):
        assistant = FakeAssistant(audio_data=b"valid_audio", stt_text="Chrome kholo")
        worker = Worker(assistant, listen=True)

        transcripts = []
        finished = []
        worker.transcript_ready.connect(transcripts.append)
        worker.finished.connect(finished.append)

        worker.run()

        self.assertEqual(transcripts, ["Chrome kholo"])
        self.assertEqual(len(finished), 1)
        self.assertEqual(finished[0]["kind"], "voice")
        self.assertEqual(finished[0]["text"], "Chrome kholo")

    def test_microphone_exception_handling(self):
        assistant = FakeAssistant(should_raise=True)
        worker = Worker(assistant, listen=True)

        states = []
        errors = []
        worker.state_changed.connect(states.append)
        worker.error.connect(errors.append)

        worker.run()

        self.assertIn("ERROR", states)
        self.assertEqual(len(errors), 1)
        # Verify no traceback / raw exception leak to user
        self.assertEqual(errors[0], "Something went wrong. Please try again.")
        self.assertNotIn("RuntimeError", errors[0])
        self.assertNotIn("Traceback", errors[0])


class TestMainWindowVoiceStateMachine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("app.ui.main_window.BackgroundVoiceListener"):
            cls.win = MainWindow()

    def test_state_machine_idle(self):
        self.win._set_state("IDLE")
        self.assertEqual(self.win.current_state, "IDLE")
        self.assertTrue(self.win.voice_bar.isHidden())
        self.assertFalse(self.win.command_input.isHidden())
        self.assertIn("Ready", self.win.status_lbl.text())
        self.assertEqual(self.win.mic_btn.toolTip(), "Click microphone to talk")
        self.assertEqual(self.win.listen_btn.text(), "Start Listening")

    def test_state_machine_listening(self):
        self.win._set_state("LISTENING")
        self.assertEqual(self.win.current_state, "LISTENING")
        self.assertFalse(self.win.voice_bar.isHidden())
        self.assertTrue(self.win.command_input.isHidden())
        self.assertIn("Listening", self.win.status_lbl.text())
        self.assertEqual(self.win.voice_bar.status_label.text(), "Listening...")
        self.assertIn("cancel", self.win.mic_btn.toolTip().lower())
        self.assertEqual(self.win.listen_btn.text(), "Cancel Listening")

    def test_state_machine_speech_detected(self):
        self.win._set_state("SPEECH_DETECTED")
        self.assertEqual(self.win.current_state, "SPEECH_DETECTED")
        self.assertFalse(self.win.voice_bar.isHidden())
        self.assertEqual(self.win.voice_bar.status_label.text(), "Listening...")
        self.assertIn("Listening", self.win.status_lbl.text())

    def test_state_machine_processing(self):
        self.win._set_state("PROCESSING")
        self.assertEqual(self.win.current_state, "PROCESSING")
        self.assertFalse(self.win.voice_bar.isHidden())
        self.assertEqual(self.win.voice_bar.status_label.text(), "Thinking...")
        self.assertIn("Thinking", self.win.status_lbl.text())

    def test_state_machine_speaking(self):
        self.win._set_state("SPEAKING")
        self.assertEqual(self.win.current_state, "SPEAKING")
        self.assertFalse(self.win.voice_bar.isHidden())
        self.assertEqual(self.win.voice_bar.status_label.text(), "Speaking...")
        self.assertIn("Speaking", self.win.status_lbl.text())

    def test_state_machine_error(self):
        self.win._set_state("ERROR")
        self.assertEqual(self.win.current_state, "ERROR")
        self.assertEqual(self.win.voice_bar.status_label.text(), "Something went wrong")
        self.assertIn("Something went wrong", self.win.status_lbl.text())

    def test_toggle_voice_cancels_when_listening(self):
        self.win._set_state("LISTENING")
        with patch.object(self.win, "_cancel_voice_input") as mock_cancel:
            self.win._toggle_voice_input()
            mock_cancel.assert_called_once()

    def test_toggle_voice_starts_when_idle(self):
        self.win._set_state("IDLE")
        with patch.object(self.win, "_start_voice_input") as mock_start:
            self.win._toggle_voice_input()
            mock_start.assert_called_once()

    def test_worker_finished_returns_to_idle(self):
        self.win._set_state("PROCESSING")
        self.win._worker_finished({"kind": "voice", "response": "Done."})
        self.assertEqual(self.win.current_state, "IDLE")
        self.assertTrue(self.win.voice_bar.isHidden())

    def test_worker_finished_no_speech_message(self):
        self.win._set_state("LISTENING")
        with patch.object(self.win, "_add_message") as mock_msg:
            self.win._worker_finished({"kind": "no_speech"})
            mock_msg.assert_called_with("No speech detected. Try again.", False)
        self.assertEqual(self.win.current_state, "IDLE")

    def test_worker_error_does_not_expose_traceback(self):
        with patch.object(self.win, "_add_message") as mock_msg:
            self.win._worker_error("Traceback (most recent call last): RuntimeError: bad audio")
            mock_msg.assert_called_with("Something went wrong. Please try again.", False)
        self.assertEqual(self.win.current_state, "ERROR")


if __name__ == "__main__":
    unittest.main()
