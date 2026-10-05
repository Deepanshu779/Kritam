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
import threading
import unittest
from pathlib import Path
import numpy as np

_root_dir = str(Path(__file__).resolve().parent.parent)
_app_dir = str(Path(__file__).resolve().parent.parent / "app")
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

try:
    from app.voice.audio_processor import AudioProcessor
    from app.voice.vad import SpeechActivityDetector
    from app.voice.transcript_validator import TranscriptValidator
    from app.voice.wake_word import WakeWordDetector
    from app.voice.text_to_speech import TextToSpeech
    from app.voice.listener import VoiceListener
    from app.intelligence.fast_router import FastRouter
    from app.core.context import ConversationContext
    from app.core.task_planner import TaskPlanner
except ImportError:
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
            onset_consecutive_frames=3,
            hangover_duration_s=0.3,  # Shortened for unit test speed
            min_speech_duration_s=0.12,
            pre_roll_duration_s=0.15,
            max_utterance_duration_s=2.0,
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
        for _ in range(6):
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


class TestVoiceCaptureStateMachine(unittest.TestCase):

    def setUp(self):
        self.vad = SpeechActivityDetector(
            sample_rate=16000,
            frame_duration_ms=30,
            onset_consecutive_frames=3,
            hangover_duration_s=0.9,
            min_speech_duration_s=0.5,
            pre_roll_duration_s=0.45,
            max_utterance_duration_s=22.0,
        )
        self.frame_size = self.vad.frame_size

    def _silence(self):
        return np.zeros(self.frame_size, dtype=np.float32)

    def _speech(self, amp=0.08):
        return (np.sin(np.linspace(0, 18, self.frame_size)) * amp).astype(np.float32)

    def test_silence_does_not_trigger(self):
        for _ in range(80):
            self.assertIsNone(self.vad.process_frame(self._silence()))
        self.assertFalse(self.vad.speech_active)

    def test_short_noise_spike_does_not_trigger(self):
        spike = self._speech(amp=0.2)
        self.assertIsNone(self.vad.process_frame(spike))
        self.assertIsNone(self.vad.process_frame(self._silence()))
        self.assertIsNone(self.vad.process_frame(self._silence()))
        self.assertFalse(self.vad.speech_active)

    def test_pre_roll_preserved_on_speech_start(self):
        lead_in = np.full(self.frame_size, 0.004, dtype=np.float32)
        for _ in range(10):
            self.vad.process_frame(lead_in)
        for _ in range(25):
            self.vad.process_frame(self._speech())
        utterance = None
        for _ in range(40):
            utterance = self.vad.process_frame(self._silence())
            if utterance is not None:
                break
        self.assertIsNotNone(utterance)
        self.assertGreater(float(np.mean(np.abs(utterance[: self.frame_size * 8]))), 0.0015)

    def test_short_pause_within_speech_does_not_end(self):
        for _ in range(20):
            self.assertIsNone(self.vad.process_frame(self._speech()))
        for _ in range(10):  # 300ms pause < hangover
            self.assertIsNone(self.vad.process_frame(self._silence()))
        for _ in range(20):
            self.assertIsNone(self.vad.process_frame(self._speech()))
        self.assertTrue(self.vad.speech_active)

    def test_longer_silence_ends_speech(self):
        for _ in range(25):
            self.vad.process_frame(self._speech())
        utterance = None
        for _ in range(50):  # 1.5s silence > hangover
            utterance = self.vad.process_frame(self._silence())
            if utterance is not None:
                break
        self.assertIsNotNone(utterance)
        self.assertGreater(len(utterance), 0)

    def test_short_accidental_audio_is_rejected(self):
        for _ in range(4):
            self.vad.process_frame(self._speech())
        for _ in range(45):
            utterance = self.vad.process_frame(self._silence())
            self.assertIsNone(utterance)
        self.assertFalse(self.vad.speech_active)

    def test_long_natural_speech_not_cut_early(self):
        utterance = None
        for i in range(180):  # ~5.4s
            frame = self._silence() if (50 <= i < 58 or 120 <= i < 128) else self._speech()
            out = self.vad.process_frame(frame)
            if out is not None:
                utterance = out
                break
        self.assertIsNone(utterance, "speech should not end before final trailing silence")
        for _ in range(60):
            out = self.vad.process_frame(self._silence())
            if out is not None:
                utterance = out
                break
        self.assertIsNotNone(utterance)
        self.assertGreater(len(utterance) / 16000.0, 4.8)

    def test_max_utterance_limit_applies(self):
        utterance = None
        for _ in range(900):  # 27s > 22s limit
            out = self.vad.process_frame(self._speech())
            if out is not None:
                utterance = out
                break
        self.assertIsNotNone(utterance)
        self.assertGreater(len(utterance) / 16000.0, 20.0)
        self.assertLess(len(utterance) / 16000.0, 23.5)

    def test_multiple_utterances_are_independent(self):
        utterances = []
        for _ in range(2):
            for _ in range(30):
                self.vad.process_frame(self._speech())
            for _ in range(40):
                out = self.vad.process_frame(self._silence())
                if out is not None:
                    utterances.append(out)
                    break
        self.assertEqual(len(utterances), 2)
        self.assertFalse(self.vad.speech_active)

    def test_reset_clears_state(self):
        for _ in range(8):
            self.vad.process_frame(self._speech())
        self.vad.reset()
        self.assertFalse(self.vad.speech_active)
        self.assertEqual(self.vad.silence_counter, 0)
        self.assertEqual(self.vad.consecutive_speech_frames, 0)


class TestMicrophoneWorkerGuards(unittest.TestCase):

    def test_microphone_guard_blocks_duplicate_worker(self):
        from app.voice.mic_guard import microphone_session

        with microphone_session(timeout_s=0.05) as acquired_first:
            self.assertTrue(acquired_first)
            with microphone_session(timeout_s=0.05) as acquired_second:
                self.assertFalse(acquired_second)


def _frame_to_bytes(frame: np.ndarray) -> bytes:
    return np.clip(frame * 32767.0, -32768, 32767).astype(np.int16).tobytes()


class _FakeStream:
    def __init__(self, chunk_size, raw_frames):
        self.chunk_size = chunk_size
        self.frames = list(raw_frames)
        self.closed = False
        self.stopped = False

    def read(self, chunk_size, exception_on_overflow=False):
        if self.frames:
            return self.frames.pop(0)
        return (np.zeros(chunk_size, dtype=np.int16)).tobytes()

    def stop_stream(self):
        self.stopped = True

    def close(self):
        self.closed = True


class _FakePyAudioInstance:
    def __init__(self, chunk_size, stream_batches):
        self.chunk_size = chunk_size
        self.stream_batches = stream_batches
        self.open_calls = 0
        self.streams = []
        self.terminated = False

    def open(self, **kwargs):
        frames = self.stream_batches[self.open_calls] if self.open_calls < len(self.stream_batches) else []
        stream = _FakeStream(self.chunk_size, frames)
        self.streams.append(stream)
        self.open_calls += 1
        return stream

    def terminate(self):
        self.terminated = True


class _FakePyAudioModule:
    paInt16 = 8

    def __init__(self, chunk_size, stream_batches):
        self.instance = _FakePyAudioInstance(chunk_size, stream_batches)

    def PyAudio(self):
        return self.instance


class _FakeSpeechToText:
    def __init__(self, text):
        self.text = text

    def convert_with_metadata(self, audio):
        return self.text, {"valid": True}


class TestListenerLifecycle(unittest.TestCase):

    def _speech_frame(self, size, amp=0.08):
        return (np.sin(np.linspace(0, 18, size)) * amp).astype(np.float32)

    def _silence_frame(self, size):
        return np.zeros(size, dtype=np.float32)

    def test_foreground_listener_stop_restart_without_leak(self):
        import app.voice.listener as listener_module

        chunk = 480
        speech = _frame_to_bytes(self._speech_frame(chunk))
        silence = _frame_to_bytes(self._silence_frame(chunk))

        batches = [
            [silence] * 10 + [speech] * 35 + [silence] * 40,
            [silence] * 8 + [speech] * 32 + [silence] * 40,
        ]
        fake_pyaudio = _FakePyAudioModule(chunk, batches)
        original = listener_module.pyaudio
        listener_module.pyaudio = fake_pyaudio
        try:
            listener = listener_module.VoiceListener()
            audio_1 = listener.listen(timeout=2.0, phrase_time_limit=10.0)
            audio_2 = listener.listen(timeout=2.0, phrase_time_limit=10.0)
            self.assertIsNotNone(audio_1)
            self.assertIsNotNone(audio_2)
            self.assertEqual(fake_pyaudio.instance.open_calls, 2)
            self.assertTrue(all(stream.closed and stream.stopped for stream in fake_pyaudio.instance.streams))
            listener.close()
            self.assertTrue(fake_pyaudio.instance.terminated)
        finally:
            listener_module.pyaudio = original

    def test_background_listener_stop_restart(self):
        import app.voice.background_listener as bg_module

        chunk = 480
        speech = _frame_to_bytes(self._speech_frame(chunk))
        silence = _frame_to_bytes(self._silence_frame(chunk))
        fake_pyaudio = _FakePyAudioModule(chunk, [[silence] * 10 + [speech] * 30 + [silence] * 45])

        original = bg_module.pyaudio
        bg_module.pyaudio = fake_pyaudio
        try:
            listener = bg_module.BackgroundVoiceListener(
                speech_to_text=_FakeSpeechToText("hey kritam open chrome"),
                tts=None,
                assistant_name="Kritam",
            )
            command = listener.listen_for_command()
            self.assertEqual(command.lower(), "open chrome")
            listener.stop()
            self.assertTrue(fake_pyaudio.instance.terminated)

            fake_pyaudio_2 = _FakePyAudioModule(chunk, [[silence] * 8 + [speech] * 28 + [silence] * 45])
            bg_module.pyaudio = fake_pyaudio_2
            restarted = bg_module.BackgroundVoiceListener(
                speech_to_text=_FakeSpeechToText("hey kritam search python"),
                tts=None,
                assistant_name="Kritam",
            )
            command_2 = restarted.listen_for_command()
            self.assertEqual(command_2.lower(), "search python")
            restarted.stop()
        finally:
            bg_module.pyaudio = original


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
