# Known Limitations

These are current source-level limitations. Runtime verification is still pending where noted.

- No standalone Windows release can be claimed yet. A PyInstaller/electron-builder pipeline is present but has not been run; native dependency collection, install, launch, and clean-machine behavior remain unverified.
- The configured managed gateway URL is not evidence of a deployed gateway. Gateway uptime, authentication, quotas and billing are unverified. The default mode for a new profile is Offline.
- Ollama needs a separately installed service and locally downloaded model. No model is downloaded automatically by KRITAM.
- OpenAI, Groq and OpenRouter require user credentials. Keys are currently stored in plaintext in the local SQLite settings database.
- Local Whisper transcription requires Faster Whisper and its model files. Base is default and Small is selectable; KRITAM requests consent before model download. No real-device WER/latency or Hinglish benchmark is available. Decoder confidence values gate command dispatch conservatively but are not calibrated probabilities.
- Voice commands can open a registered application or a query-specific YouTube Music/Spotify search. They do not verify or start track playback; service login, result selection, and autoplay policy remain in control. Pause, resume, stop, and skip controls are unsupported.
- Hands-free recognition is intentionally disabled in the current composer.
- The action policy and file inspection boundaries have been tightened in source, but their regression tests and runtime behavior remain unverified before release.
- Backend and desktop automated tests/builds could not run in the initial environment because pytest and Vite were unavailable. Windows packaging, microphone hardware, local Ollama and external cloud providers have not been tested.
- Code signing, installer behavior, upgrade behavior and uninstall behavior have not been configured or validated.
