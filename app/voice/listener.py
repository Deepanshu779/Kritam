import speech_recognition as sr


class VoiceListener:

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.35
        self.recognizer.phrase_threshold = 0.15
        self.recognizer.non_speaking_duration = 0.55
        self.recognizer.dynamic_energy_threshold = True
        self.microphone = sr.Microphone()
        self._calibrated = False

    def _prepare(self):
        if self._calibrated:
            return
        with self.microphone as source:
            print("Calibrating microphone...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
        self._calibrated = True

    def listen(self, timeout=1, phrase_time_limit=30):
        self._prepare()
        with self.microphone as source:
            try:
                return self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
            except sr.WaitTimeoutError:
                return None

    def listen_until_stopped(self, stop_event):
        """Record continuously until the UI asks us to stop.

        This is used by the foreground mic button. Unlike listen(), it does
        not stop on a short pause, so the user can speak naturally and then
        click the mic button again to finish and send the recording.
        """
        self._prepare()
        with self.microphone as source:
            print("Kritam: foreground recording started.")
            chunks = []
            while not stop_event.is_set():
                try:
                    # SpeechRecognition MicrophoneStream.read() does not accept exception_on_overflow.
                    chunk = source.stream.read(source.CHUNK)
                except Exception as exc:
                    print(f"Kritam: microphone read stopped: {exc}")
                    break
                chunks.append(chunk)

            print("Kritam: foreground recording stopped.")
            if not chunks:
                return None

            return sr.AudioData(
                b"".join(chunks),
                source.SAMPLE_RATE,
                source.SAMPLE_WIDTH,
            )
