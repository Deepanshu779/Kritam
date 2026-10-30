# KRITAM Voice-First Restructure

**Status:** Proposed implementation plan  
**Branch:** `feature/voice-first-agent-foundation`  
**Product decision:** Voice-first personal companion; warm conversational personality + capable desktop assistant. Support both wake-word activation and explicit continuous conversation mode.

## Product contract

KRITAM should feel like a person is available to talk with—not like a command-line voice wrapper. People can speak naturally, ask questions, think aloud, request advice, correct themselves, interrupt, and ask follow-up questions. Typing remains available, but never required for ordinary interaction.

KRITAM is an AI assistant, not a human. It must be transparent about uncertainty, capabilities, microphone state, and action outcomes.

## Target interaction

1. **Idle / wake-word:** Optional, user-enabled local wake-word detector. Do not keep a cloud speech-recognition session running just to detect the wake phrase.
2. **Conversation:** After wake word or explicit Start Conversation, begin a visible session. Support multi-turn talk and configurable silence timeout.
3. **Capture:** Voice activity detection (VAD) identifies utterance boundaries. Keep a cancellable capture session and handle device changes.
4. **Understand:** Transcribe speech; retain user-approved conversation context. Classify utterance as chat, question, advice, desktop action, cancellation, or ambiguous.
5. **Respond:** Generate one assistant turn. Natural response text and spoken response should come from the same result, with speech-safe formatting.
6. **Act:** Route requested tools through existing allowlists and authorization checks. Confirm sensitive or destructive operations. Never infer permission from conversational tone.
7. **Turn-taking:** Allow barge-in: user speech stops TTS and cancels or safely pauses generation. Distinguish microphone input from KRITAM's own output.
8. **Close:** User can say “stop listening”, “goodbye Kritam”, or use a visible Stop control. Release microphone resources and clearly return to idle.

## Proposed module boundaries

Keep the existing Electron + React renderer and FastAPI backend. Refactor in-place in small, testable slices; avoid a speculative rewrite.

- `voice/VoiceSessionController`: owns the session state machine and start/stop lifecycle.
- `voice/AudioCapture`: microphone permissions, device selection, stream lifecycle, audio levels, VAD integration.
- `voice/SpeechRecognizer`: replaceable STT adapter interface; distinguish local transcription from browser/network recognition.
- `voice/WakeWord`: optional activation adapter, isolated from conversation capture and configurable by user.
- `voice/SpeechOutput`: TTS queue, cancellation, voice selection, speech-safe text.
- `conversation/ConversationOrchestrator`: connects user turns, chat streaming, action interpretation, and voice output without coupling the UI to recognition implementation.
- `actions/ActionPolicy`: preserve backend validation, allowlists, confirmations, and explicit outcome reporting.

These are target boundaries, not a claim that all modules already exist.

## Session state machine

`disabled → idle → activating → listening → transcribing → responding → speaking → listening`

Exit paths: any active state → `stopping → idle`; unrecoverable error → `error` with a clear recovery action.

Invariants:
- Only one active microphone session.
- Every async callback carries a session/generation ID; stale callbacks are ignored.
- Stop is idempotent and releases media tracks, timers, audio contexts, recognizers and pending playback.
- TTS playback is never interpreted as user input; use echo cancellation plus an explicit output/mute strategy.
- Temporary silence does not end a conversation immediately; apply a configurable timeout and let users resume.
- Duplicate utterances and automatic recognizer restarts must not dispatch a command twice.

## UX principles

- One clear microphone / conversation control with explicit Idle, Listening, Thinking, Speaking and Error states.
- Listening state is always visible. Include an immediate mute/stop control and microphone permission explanation.
- Show interim transcript subtly and final transcript in the conversation; allow correction when recognition is uncertain.
- No fake “always listening” promise when platform or recognition provider cannot support it.
- Settings group: activation mode (Wake word / Start manually / Both), language, microphone, voice, speech speed, local/cloud processing and privacy controls.
- Voice is primary, text input remains first-class and accessible.
- Avoid extra cards, provider badges, animated characters, or technical telemetry in the core conversation surface.

## Delivery sequence

### Phase 0 — Stabilize and baseline
- Inventory existing voice routes, action dispatch, settings and cleanup behavior.
- Record known STT/TTS limitations and current test/build commands.
- Define state-machine tests before changing the current listener.

### Phase 1 — Reliable conversation sessions
- Introduce a single session controller and explicit lifecycle.
- Route voice turns through the existing send/stream path.
- Add cancel/barge-in and resource-cleanup tests.
- Do not add wake-word claims until a real wake-word adapter is present and tested.

### Phase 2 — Natural speech and turn-taking
- VAD-based endpointing, silence handling, transcript confidence/correction, duplicate protection.
- Speech queue and speech-safe formatting; interrupt speech and response generation coherently.
- Validate real microphone, speaker, headset and laptop-speaker scenarios.

### Phase 3 — Activation
- Add optional local wake-word detection, opt-in onboarding, false-activation controls and a clear background indicator.
- If a reliable supported local detector isn't available, ship explicit activation rather than silently falling back to network listening.

### Phase 4 — Companion quality
- Tune conversational prompt/personality, short acknowledgments, clarifying questions and context carryover.
- Test Hindi/English and code-switching; avoid overconfident transcription or actions.

### Phase 5 — Release hardening
- Permission, privacy, resource-use, interruption, recovery, accessibility, packaging and end-to-end regression tests.

## Acceptance criteria

- User can start a conversation without typing and speak multiple turns.
- User can interrupt KRITAM while it speaks and receive a fresh turn.
- Natural questions and casual speech are not forced into a brittle command grammar.
- Commands are executed only through the protected action router and verified by their actual result.
- Background activation is optional, transparent and actually implemented—not simulated by a badge.
- Microphone tracks and timers are released after Stop, close, error, or session replacement.
- STT outage, missing device, permission denial, empty audio and provider failures produce actionable, honest feedback.
- Existing text chat, history, settings, and approved desktop actions continue to work.

## Current code observations

- The current app sends chat through `handleSendMessage` and optionally speaks completed output.
- `Composer` contains a separate MediaRecorder/transcription path and command-like regex routing.
- `speech-service.ts` exposes both single-shot recognition and background-listening logic.
- These parallel paths risk inconsistent session state and behavior. Phase 1 should consolidate orchestration carefully while preserving working paths until replacement passes tests.
- The renderer settings already include voice language, STT model, microphone selection, background voice, and auto-dispatch options. Reuse and migrate them deliberately; do not silently change existing preferences.
- The existing app has an action confirmation modal and result reporting. Preserve that security boundary.

## Validation gate

This plan does not imply the app has been built or runtime-tested. Before a user-facing release, run renderer and main-process builds, available backend tests, and hands-on microphone/speaker tests on the target Windows environment.


## Barge-in engineering decision (next implementation gate)

**Current behavior:** `speech-service.ts` pauses/aborts browser recognition while TTS plays. This intentionally suppresses echo, but it also means a user cannot genuinely interrupt spoken output. Calling `stopSpeaking()` from a button is cancellation, not microphone-driven barge-in.

**Do not ship an RMS-only interruption detector as speech recognition.** A loudness threshold can mistake KRITAM's speaker output, keyboard noise, or room noise for the user. The browser speech-recognition API does not expose reliable acoustic echo cancellation/reference audio or the already-spoken interruption transcript.

**Preferred implementation path:**
1. Add an explicit audio-capture adapter with one owned microphone stream and deterministic teardown.
2. Prefer a supported VAD + streaming STT pipeline that can continue capturing while TTS plays and expose partial transcripts. Reuse the configured local/cloud policy and disclose the selected processing route.
3. Use the platform's echo-cancellation constraints where available; treat them as best-effort, not a guarantee. Add a configurable headphones recommendation/fallback for poor acoustic environments.
4. Require speech evidence (VAD onset plus a short transcript/quality threshold) before interrupting. On confirmed onset, cancel TTS immediately, retain the captured speech frames, finalize transcription, then submit exactly one conversational turn. Never dispatch a desktop action based only on a partial transcript.
5. Give stop/cancel phrases a fast path only when recognized confidently; preserve authorization and confirmation for sensitive actions.
6. If the chosen STT path cannot capture during playback reliably, present a clear “Tap to interrupt” fallback instead of claiming hands-free barge-in.

**Test matrix before enabling by default:** laptop speakers at low/high volume; headphones; user speech during TTS; no speech; TV/music in room; echo/reverberant room; STT/network loss; repeated onset events; stop during transcription; app close and device unplug. Assert one transcript/turn at most and zero leaked tracks/timers.

**Status:** decision documented only. No interruption detector or VAD/STT pipeline has been implemented or validated yet.
