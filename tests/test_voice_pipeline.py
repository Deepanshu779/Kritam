"""Comprehensive test suite for Kritam's improved voice architecture.

Tests:
A. Clear speech: "Hey Kritam, open Chrome."
B. Natural speech: "Could you open Chrome for me?"
C. Hindi: "Kritam Chrome kholo."
D. Hinglish: "Google par Python search kar do."
E. Correction: "Open Chrome." -> "No, wait, open YouTube." & Music correction.
F. Background silence: Rejection of silent audio.
G. Background noise: Rejection of low-level ambient fan/room noise.
H. TTS echo: Suppression when assistant is speaking/settling.
I. Short command: "Stop."
J. Longer sentence: Task splitting and planning.
K. Pause: Standalone wake followed by command.
L. Mixed language: "Actually YouTube pe Haryanvi song chala do."
M. Repetition / hallucination filtering: Rejecting repeated loops without blacklisting legitimate terms.
"""

import sys
import time
import unittest
from pathlib import Path
import numpy as np

_root_dir = str(Path(__file__).resolve().parent.parent)
_app_dir = str(Path(__file__).resolve().parent.parent / "app")
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

import app
from voice.audio_processor import AudioProcessor
from voice.vad import SpeechActivityDetector
from voice.transcript_validator import TranscriptValidator
from voice.wake_word import WakeWordDetector
from voice.text_to_speech import TextToSpeech
from voice.listener import VoiceListener
from intelligence.fast_router import FastRouter
from core.context import ConversationContext
from core.task_planner import TaskPlanner


class TestAudioProcessor(unittest.TestCase):

    def setUp(self):
        self.processor = AudioProcessor()

    def test_mono_16k_pcm_conversion(self):
        # Test 16-bit PCM byte buffer conversion
        raw_int16 = (np.sin(np.linspace(0, 100, 16000)) * 10000).astype(np.int16).tobytes()
        samples = self.processor.to_mono_16k_pcm(raw_int16, sample_rate=16000, sample_width=2)
        self.assertEqual(len(samples), 16000)
        self.assertEqual(samples.dtype, np.float32)
        self.assertTrue(np.max(np.abs(samples)) <= 1.0)

    def test_silence_detection(self):
        # Case F: Silence rejection
        silent_audio = np.zeros(16000, dtype=np.float32)
        metrics = self.processor.calculate_metrics(silent_audio)
        self.assertTrue(metrics.is_silence)
        self.assertAlmostEqual(metrics.rms, 0.0)

    def test_background_noise_rejection(self):
        # Case G: Faint ambient noise (fan hum) rejection
        low_noise = np.random.normal(0, 0.0005, 16000).astype(np.float32)
        metrics = self.processor.calculate_metrics(low_noise)
        self.assertTrue(metrics.is_silence)

    def test_safe_normalization_no_aggressive_noise_amplification(self):
        # Ambient noise must NOT be amplified
        noise = np.full(16000, 0.001, dtype=np.float32)
        normalized = self.processor.safe_normalize(noise)
        self.assertAlmostEqual(float(np.max(normalized)), 0.001, places=4)

        # Clear voice signal should be normalized with a safe ceiling
        speech_signal = np.sin(np.linspace(0, 50, 16000)).astype(np.float32) * 0.3
        normalized_speech = self.processor.safe_normalize(speech_signal)
        self.assertTrue(np.max(np.abs(normalized_speech)) > 0.6)
        self.assertTrue(np.max(np.abs(normalized_speech)) <= 0.85)


class TestSpeechActivityDetector(unittest.TestCase):

    def setUp(self):
        self.vad = SpeechActivityDetector(
            sample_rate=16000,
            frame_duration_ms=30,
            onset_consecutive_frames=2,
            hangover_duration_s=0.2,  # Shortened for unit test speed
            min_speech_duration_s=0.1,
        )

    def test_speech_onset_and_hangover(self):
        # 1. Feed silence frames
        silence_frame = np.zeros(480, dtype=np.float32)
        for _ in range(5):
            res = self.vad.process_frame(silence_frame)
            self.assertIsNone(res)
        self.assertFalse(self.vad.speech_active)

        # 2. Feed speech frames (onset)
        speech_frame = (np.sin(np.linspace(0, 10, 480)) * 0.4).astype(np.float32)
        for _ in range(3):
            self.vad.process_frame(speech_frame)
        self.assertTrue(self.vad.speech_active)

        # 3. Feed silence frames (trailing pause)
        utterance = None
        for _ in range(12):
            res = self.vad.process_frame(silence_frame)
            if res is not None:
                utterance = res
                break

        self.assertIsNotNone(utterance)
        self.assertTrue(len(utterance) > 0)


class TestTranscriptValidator(unittest.TestCase):

    def setUp(self):
        self.validator = TranscriptValidator()

    def test_repetition_rejection(self):
        # Case M: Reject excessive repetition loops
        result = self.validator.validate(
            raw_text="Microsoft Microsoft Microsoft Microsoft",
            audio_duration_s=2.0,
        )
        self.assertFalse(result.is_valid)
        self.assertIn("repetition", result.rejection_reason)

    def test_no_word_blacklist_for_legitimate_commands(self):
        # Legitimate commands mentioning "Microsoft", "YouTube", "Chrome" must NOT be blacklisted!
        for phrase in [
            "open Microsoft",
            "open YouTube",
            "search Google",
            "open Chrome",
        ]:
            res = self.validator.validate(raw_text=phrase, audio_duration_s=1.5)
            self.assertTrue(res.is_valid, f"Phrase '{phrase}' was unexpectedly rejected!")
            self.assertEqual(res.cleaned_text.lower(), phrase.lower())

    def test_subtitle_artifact_rejection(self):
        res = self.validator.validate(raw_text="[Music]", audio_duration_s=1.0)
        self.assertFalse(res.is_valid)

        res = self.validator.validate(raw_text="(applause)", audio_duration_s=1.0)
        self.assertFalse(res.is_valid)

    def test_implausible_speech_rate_rejection(self):
        # 10 words in 0.5s is physically impossible
        res = self.validator.validate(
            raw_text="one two three four five six seven eight nine ten",
            audio_duration_s=0.5,
        )
        self.assertFalse(res.is_valid)


class TestWakeWordDetector(unittest.TestCase):

    def setUp(self):
        self.detector = WakeWordDetector(assistant_name="Kritam")

    def test_unified_wake_and_command(self):
        # Case A: "Hey Kritam, open Chrome."
        res = self.detector.detect("Hey Kritam, open Chrome.")
        self.assertTrue(res.detected)
        self.assertEqual(res.command_remainder.lower(), "open chrome")

    def test_standalone_wake(self):
        # Case K: "Hey Kritam..." [pause]
        res = self.detector.detect("Hey Kritam")
        self.assertTrue(res.detected)
        self.assertEqual(res.command_remainder, "")

    def test_non_wake_speech(self):
        res = self.detector.detect("Open the browser")
        self.assertFalse(res.detected)


class TestTextToSpeechEchoSuppression(unittest.TestCase):

    def test_tts_active_and_settling_state(self):
        # Case H: TTS echo avoidance
        tts = TextToSpeech(settling_period_s=0.3)
        # Mock speaking state
        tts.is_speaking = True
        self.assertTrue(tts.is_active_or_settling())

        # Finish speaking -> enters settling window
        tts.is_speaking = False
        tts.last_spoke_time = time.time()
        self.assertTrue(tts.is_active_or_settling())

        # After settling window expires
        tts.last_spoke_time = time.time() - 0.4
        self.assertFalse(tts.is_active_or_settling())

        # Cleanup
        tts.stop()


class TestNaturalLanguageAndConversationalContext(unittest.TestCase):

    def setUp(self):
        self.router = FastRouter()
        self.context = ConversationContext()

    def test_case_a_clear_speech(self):
        res = self.router.route("Hey Kritam, open Chrome.", self.context)
        self.assertEqual(res, {"type": "open_application", "application": "chrome"})

    def test_case_b_natural_speech(self):
        res = self.router.route("Could you open Chrome for me?", self.context)
        self.assertEqual(res, {"type": "open_application", "application": "chrome"})

    def test_case_c_hindi(self):
        # Case C: "Kritam Chrome kholo."
        res = self.router.route("Kritam Chrome kholo.", self.context)
        self.assertEqual(res, {"type": "open_application", "application": "chrome"})

        # Variations
        res2 = self.router.route("Kritam Chrome khol do", self.context)
        self.assertEqual(res2, {"type": "open_application", "application": "chrome"})

        res3 = self.router.route("Mere liye Chrome open kar do", self.context)
        self.assertEqual(res3, {"type": "open_application", "application": "chrome"})

    def test_case_d_hinglish_search(self):
        # Case D: "Google par Python search kar do."
        res = self.router.route("Google par Python search kar do.", self.context)
        self.assertEqual(res, {"type": "search_web", "query": "Python"})

        res2 = self.router.route("Google pe Python search karo", self.context)
        self.assertEqual(res2, {"type": "search_web", "query": "Python"})

    def test_case_e_corrections(self):
        # Case E: "Open Chrome." -> "No, wait, open YouTube."
        res1 = self.router.route("Open Chrome.", self.context)
        self.assertEqual(res1, {"type": "open_application", "application": "chrome"})
        self.context.add_turn("Open Chrome.", res1, success=True)

        res2 = self.router.route("No, wait, open YouTube.", self.context)
        self.assertEqual(res2, {"type": "open_website", "website": "youtube"})

        # Correction for music
        res_m1 = self.router.route("Play Arijit Singh on YouTube", self.context)
        self.assertEqual(res_m1, {"type": "play_music", "query": "Arijit Singh", "platform": "youtube"})
        self.context.add_turn("Play Arijit Singh", res_m1, success=True)

        # "No, play Haryanvi songs." updates the query with the previous platform!
        res_m2 = self.router.route("No, play Haryanvi songs.", self.context)
        self.assertEqual(res_m2, {"type": "play_music", "query": "Haryanvi", "platform": "youtube"})

    def test_case_i_short_command(self):
        # Case I: "Stop."
        res = self.router.route("Stop.", self.context)
        self.assertIsNotNone(res)
        self.assertEqual(res["type"], "conversation")

        res_wait = self.router.route("Wait.", self.context)
        self.assertEqual(res_wait["type"], "conversation")

    def test_case_j_longer_sentence(self):
        # Case J: "Hey Kritam, open Chrome and search for Python tutorials."
        planner = TaskPlanner()
        tasks = planner.split("open Chrome and search for Python tutorials")
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0], "open Chrome")
        self.assertEqual(tasks[1], "search for Python tutorials")

    def test_case_l_mixed_language(self):
        # Case L: "Actually YouTube pe Haryanvi song chala do."
        res = self.router.route("Actually YouTube pe Haryanvi song chala do.", self.context)
        self.assertEqual(res, {"type": "play_music", "query": "Haryanvi", "platform": "youtube"})

    def test_hindi_screenshot_and_volume(self):
        # Screenshot
        res = self.router.route("Ek screenshot le lo", self.context)
        self.assertEqual(res, {"type": "take_screenshot"})

        # Volume
        res_up = self.router.route("Volume thoda badha do", self.context)
        self.assertEqual(res_up, {"type": "volume_up"})

        res_down = self.router.route("Volume kam kar do", self.context)
        self.assertEqual(res_down, {"type": "volume_down"})

    def test_browser_references(self):
        # "Open the second result"
        res = self.router.route("Open the second result", self.context)
        self.assertEqual(res, {"type": "browser_open_result", "number": 2})

        # "Go back"
        res_back = self.router.route("Go back", self.context)
        self.assertEqual(res_back, {"type": "browser_back"})

        # "Open that one"
        res_that = self.router.route("Open that one", self.context)
        self.assertEqual(res_that, {"type": "browser_open_result", "number": 1})


if __name__ == "__main__":
    unittest.main()
