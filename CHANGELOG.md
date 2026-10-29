# Changelog

## Unreleased

- Refined the welcome experience, suggestion controls, sidebar, and application styling.
- Added six organized settings sections with truthful provider, voice, privacy, automation, and about information.
- Hardened authenticated backend ownership, startup/shutdown feedback, renderer navigation/IPC, and audio-only permission handling.
- Changed the new-profile AI default to deterministic Offline; clarified that remote providers receive prompts.
- Added provider failure and interrupted-stream semantics, file/action safeguards, and audio container validation/language hints.
- Improved local speech decoding with beam search, command vocabulary context, VAD padding, selectable Base/Small models, microphone selection/level feedback, and conservative command-confidence gating.
- Added push-to-talk auto-dispatch for clear registered app and music search commands, preferred music platform and spoken command response settings, and a reproducible manual voice test plan. Playback and media transport controls remain unverified/unsupported.
- Added an experimental PyInstaller/electron-builder Windows packaging path and release audit documentation; it has not been built or verified.
