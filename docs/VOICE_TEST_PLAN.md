# KRITAM Voice Command Test Plan

This plan separates repeatable parser/action tests from hardware- and service-dependent speech checks. Automated tests mock browser launches and never open external services.

## Automated tests

From `backend/`, run `python -m pytest tests/test_offline_router.py tests/test_voice_launcher_regressions.py tests/test_action_idempotency.py tests/test_policy_engine.py tests/test_speech_transcriber.py tests/test_speech_api.py`.

Coverage includes wake-word command parsing, default/explicit music platform routing, safe registered app resolution, no-confirmation handling only for an explicitly dispatched voice action, confirmation for typed external actions, mocked music search URL opening, speech model decoding options, model allowlisting, MIME validation, and command confidence gating. These tests do not measure acoustic accuracy, launch a real app, or verify playback.

## Manual Windows checks

1. In Settings → Voice & Audio, select the microphone, choose Auto/English/Hindi, choose Base or Small, choose the preferred music platform, and enable Auto-play voice responses if spoken replies are desired.
2. Press the microphone button, wait for the live input meter to move, say a complete command at a normal distance, then press the button again. Check the reported sample rate/channel count and ensure the first/last words are captured.
3. Check the exact transcript before each run. Test `Hey Kritam, open Chrome`, `Hey Kritam, open YouTube`, `Hey Kritam, play Chamma Chamma`, `Hey Kritam, play Believer on Spotify`, `Hey Kritam, open YouTube and play a relaxing song`, plus Hindi/Hinglish equivalents supported by the chosen language hint.
4. Confirm open-app actions show success only when the allowlisted app launch succeeds. Confirm a music command opens a query-specific service search, says that a result must be selected, and never labels the song as playing before playback is verified.
5. Test silence, incomplete phrases, background noise, the misheard wake-name variants, a repeated phrase, a disconnected microphone, a stale selected device, missing Chrome/Spotify, a browser that cannot open, and denied microphone permission. Uncertain speech must remain in the composer for review and must not launch anything.
6. Verify external opens, camera permission, untrusted IPC senders, and typed website/music actions retain their confirmation/security behavior. Verify spoken response does not keep the microphone listening or feed TTS audio back into transcription.

Use user-consented recordings only. Do not upload recordings as test data without separate consent.

## Recording measurements

No WER, command accuracy, false-execution rate, latency, or playback-initiation result is claimed yet. To measure WER, collect consented recordings with a manually checked reference transcript, transcribe with the same language/model settings, and calculate `(substitutions + deletions + insertions) / reference words` per language and noise condition. Record command accuracy as correctly routed commands divided by attempted commands; false execution as unintended actions divided by non-command or uncertain utterances; latency from stop-recording to transcript and action acknowledgement; playback initiation separately from opening a search page. Report sample counts and device/model settings with every result.

YouTube Music and Spotify search opening does not prove that playback began. Manual confirmation in the service is needed for playback initiation results. Pause/resume/stop/next are currently recognized as unsupported and must not report success.
