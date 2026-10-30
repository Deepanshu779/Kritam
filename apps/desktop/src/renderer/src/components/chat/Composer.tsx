import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Square, Mic, MicOff, AlertCircle, X, Loader2, VolumeX, Radio, Sparkles } from 'lucide-react';
import { speechService, useSpeechService } from '../../services/speech-service';
import { apiClient } from '../../services/api-client';

interface ComposerProps {
  onSend: (text: string, voiceCommand?: boolean) => void;
  isGenerating: boolean;
  onStop: () => void;
  sttModel?: 'base' | 'small';
  microphoneDeviceId?: string;
  transcriptionLanguage?: 'auto' | 'en' | 'hi' | 'en-IN' | 'en-US' | 'en-GB';
}

export const Composer: React.FC<ComposerProps> = ({ onSend, isGenerating, onStop, sttModel = 'base', microphoneDeviceId, transcriptionLanguage = 'auto' }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const speech = useSpeechService();
  const [isLocalRecording, setIsLocalRecording] = useState(false);
  const [isLocalTranscribing, setIsLocalTranscribing] = useState(false);
  const [hasModelDownloadConsent, setHasModelDownloadConsent] = useState(
    () => localStorage.getItem('kritam-whisper-download-consent') === 'accepted'
  );
  const [showModelDownloadConsent, setShowModelDownloadConsent] = useState(false);
  const [localMicError, setLocalMicError] = useState('');
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const recordingTimerRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const levelFrameRef = useRef<number | null>(null);
  const lastVoiceCommandRef = useRef<{ text: string; at: number } | null>(null);
  const transcriptionInFlightRef = useRef(false);
  const isUnmountedRef = useRef(false);
  const [micLevel, setMicLevel] = useState(0);
  const [micTrackInfo, setMicTrackInfo] = useState('');

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [text]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || isGenerating || isLocalRecording || isLocalTranscribing) return;

    // Interruption: Stop active speech playback if user sends new message
    if (speech.ttsState === 'speaking') {
      speechService.stopSpeaking();
    }

    // Stop single-shot push-to-talk listening if active
    if (speech.voiceState === 'listening' && !speech.isBackgroundListening) {
      speechService.stopListening();
    }

    onSend(trimmed);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const toggleMic = async () => {
    setLocalMicError('');
    if (isLocalRecording) {
      recorderRef.current?.stop();
      setIsLocalRecording(false);
      return;
    }
    if (isLocalTranscribing) return;
    if (!hasModelDownloadConsent && localStorage.getItem('kritam-whisper-download-consent') !== 'accepted') {
      setShowModelDownloadConsent(true);
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setLocalMicError('Audio recording is unavailable in this runtime.');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          ...(microphoneDeviceId ? { deviceId: { exact: microphoneDeviceId } } : {}),
          echoCancellation: true, noiseSuppression: true, autoGainControl: true,
        },
      });
      streamRef.current = stream;
      const track = stream.getAudioTracks()[0];
      const trackSettings = track?.getSettings();
      setMicTrackInfo(trackSettings ? `${trackSettings.sampleRate || 'default'} Hz · ${trackSettings.channelCount || 1} channel(s)` : 'Microphone active');
      try {
        const context = new AudioContext();
        audioContextRef.current = context;
        const analyser = context.createAnalyser();
        analyser.fftSize = 512;
        context.createMediaStreamSource(stream).connect(analyser);
        const samples = new Uint8Array(analyser.fftSize);
        let lastLevelUpdate = 0;
        const updateLevel = (timestamp: number) => {
          if (context.state === 'closed') return;
          analyser.getByteTimeDomainData(samples);
          let sum = 0;
          for (const sample of samples) { const value = (sample - 128) / 128; sum += value * value; }
          if (timestamp - lastLevelUpdate >= 100) {
            lastLevelUpdate = timestamp;
            setMicLevel(Math.min(1, Math.sqrt(sum / samples.length) * 3.5));
          }
          levelFrameRef.current = requestAnimationFrame(updateLevel);
        };
        void context.resume().then(updateLevel).catch(() => undefined);
      } catch { setMicLevel(0); }
      chunksRef.current = [];
      const mimeType = [
        'audio/webm;codecs=opus', 'audio/webm',
        'audio/mp4;codecs=mp4a.40.2', 'audio/mp4',
        'audio/ogg;codecs=opus', 'audio/ogg'
      ].find((candidate) => MediaRecorder.isTypeSupported(candidate));
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      recorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onerror = () => {
        if (recordingTimerRef.current !== null) window.clearTimeout(recordingTimerRef.current);
        recordingTimerRef.current = null;
        if (!isUnmountedRef.current) {
          setLocalMicError('Audio recording failed. Check microphone permission and try again.');
          setIsLocalRecording(false);
        }
        stream.getTracks().forEach(track => track.stop());
        streamRef.current = null;
        if (levelFrameRef.current !== null) cancelAnimationFrame(levelFrameRef.current);
        levelFrameRef.current = null;
        void audioContextRef.current?.close();
        audioContextRef.current = null;
        if (!isUnmountedRef.current) setMicLevel(0);
      };
      recorder.onstop = async () => {
        if (recordingTimerRef.current !== null) window.clearTimeout(recordingTimerRef.current);
        recordingTimerRef.current = null;
        if (!isUnmountedRef.current) setIsLocalRecording(false);
        stream.getTracks().forEach(track => track.stop());
        streamRef.current = null;
        if (levelFrameRef.current !== null) cancelAnimationFrame(levelFrameRef.current);
        levelFrameRef.current = null;
        void audioContextRef.current?.close();
        audioContextRef.current = null;
        if (!isUnmountedRef.current) setMicLevel(0);
        const firstChunkType = chunksRef.current.find((chunk) => chunk instanceof Blob && chunk.type)?.type;
        const audio = new Blob(chunksRef.current, { type: recorder.mimeType || firstChunkType || '' });
        chunksRef.current = [];
        if (isUnmountedRef.current) return;
        if (audio.size < 1200) {
          setLocalMicError('Recording was too short. Please speak for a moment and try again.');
          return;
        }
        if (transcriptionInFlightRef.current) return;
        transcriptionInFlightRef.current = true;
        setIsLocalTranscribing(true);
        try {
          const language = transcriptionLanguage === 'hi' || transcriptionLanguage === 'hi-IN'
            ? 'hi'
            : transcriptionLanguage === 'en' || transcriptionLanguage?.startsWith('en-') ? 'en' : 'auto';
          const result = await apiClient.transcribeAudio(audio, language, true, sttModel);
          if (isUnmountedRef.current) return;
          const transcript = result.text?.trim();
          if (!transcript) {
            setLocalMicError('No speech detected. Please try again a little closer to the microphone.');
            return;
          }
          const normalized = transcript.replace(
            /\b(?:hey|hi|hello|okay|ok)\s+(?:grum|krim|kritum|critt?am)\b(?=[, ]+\s*(?:please\s+)?(?:open|launch|start|run|play|listen|pause|resume|stop|next)\b)/ig,
            'Hey Kritam'
          );
          const commandLike = /^(?:(?:hey|hi|hello|ok|okay)\s+kritam\b[,.]?\s*)?(?:please\s+)?(?:open|launch|start|run|play|listen\s+to|pause|resume|stop|next|search\s+for|go\s+to|visit)\b/i.test(normalized)
            || /^(?:(?:hey|hi|hello|ok|okay)\s+kritam\b[,.]?\s*)?.+\s+(?:kholo|khol\s+do|chalao|bajao)$/i.test(normalized);
          if (commandLike) {
            if (result.command_confident !== true) {
              setText(normalized);
              setLocalMicError('I heard a possible command but the recognition was uncertain. Review the transcript and send it yourself if it is correct.');
            } else {
              const now = Date.now();
              const previous = lastVoiceCommandRef.current;
              if (!previous || previous.text.toLowerCase() !== normalized.toLowerCase() || now - previous.at > 4000) {
                lastVoiceCommandRef.current = { text: normalized, at: now };
                // Forward confident spoken turns even while generation is active.
                // App owns the bounded voice-turn queue; keep typed input untouched.
                onSend(normalized, true);
                setText('');
              }
            }
          } else {
            setText(prev => prev.trim() ? `${prev.trim()} ${normalized}` : normalized);
          }
          requestAnimationFrame(() => {
            if (textareaRef.current) {
              textareaRef.current.focus();
              textareaRef.current.selectionStart = textareaRef.current.value.length;
              textareaRef.current.selectionEnd = textareaRef.current.value.length;
            }
          });
        } catch (error: any) {
          console.error('[Composer] Local transcription failed:', error);
          if (!isUnmountedRef.current) setLocalMicError(error?.message || 'Local transcription failed. Check the KRITAM backend.');
        } finally {
          transcriptionInFlightRef.current = false;
          if (!isUnmountedRef.current) setIsLocalTranscribing(false);
        }
      };
      recorder.start(700);
      setIsLocalRecording(true);
      recordingTimerRef.current = window.setTimeout(() => {
        if (recorder.state !== 'inactive') recorder.stop();
      }, 5 * 60 * 1000);
    } catch (error: any) {
      streamRef.current?.getTracks().forEach(track => track.stop());
      streamRef.current = null;
      setLocalMicError(error?.name === 'NotAllowedError'
        ? 'Microphone permission denied. Allow microphone access for KRITAM.'
        : error?.message || 'Unable to access the microphone.');
    }
  };

  useEffect(() => {
    isUnmountedRef.current = false;
    return () => {
      isUnmountedRef.current = true;
      if (recordingTimerRef.current !== null) window.clearTimeout(recordingTimerRef.current);
      try { recorderRef.current?.state !== 'inactive' && recorderRef.current?.stop(); } catch {}
      streamRef.current?.getTracks().forEach(track => track.stop());
      if (levelFrameRef.current !== null) cancelAnimationFrame(levelFrameRef.current);
      void audioContextRef.current?.close();
    };
  }, []);

  const toggleBackgroundVoice = () => {
    if (speech.isBackgroundListening) {
      speechService.stopBackgroundListening();
    } else {
      speechService.clearError();
      speechService.startBackgroundListening(
        (transcript) => {
          // Treat hands-free speech as a conversational user turn, not a
          // one-off desktop command. This routes it through the same thread,
          // context, safety checks, and voice-response path as push-to-talk.
          const utterance = transcript.trim();
          if (utterance) onSend(utterance, true);
        },
        (error) => {
          console.warn('[Composer] Background voice error:', error);
        }
      );
    }
  };

  const isMicActive = isLocalRecording;
  const isMicProcessing = isLocalTranscribing;

  return (
    <div className="composer-wrapper">
      {showModelDownloadConsent && (
        <div className="modal-overlay" role="presentation" onClick={() => setShowModelDownloadConsent(false)}>
          <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="speech-download-title" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <h2 id="speech-download-title">Enable local speech transcription?</h2>
            </div>
            <div className="modal-body" style={{ lineHeight: 1.6 }}>
              KRITAM uses Faster Whisper on your device. On first use it may download model files from Hugging Face. Continue to allow this download and open microphone access?
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-secondary" onClick={() => setShowModelDownloadConsent(false)}>Not now</button>
              <button
                type="button"
                className="btn-primary"
                onClick={() => {
                  localStorage.setItem('kritam-whisper-download-consent', 'accepted');
                  setHasModelDownloadConsent(true);
                  setShowModelDownloadConsent(false);
                  void toggleMic();
                }}
              >
                Continue
              </button>
            </div>
          </div>
        </div>
      )}
      {(localMicError || speech.error) && (
        <div className="composer-voice-error" role="alert">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertCircle size={15} style={{ flexShrink: 0 }} />
            <span>{localMicError || speech.error}</span>
          </div>
          <button
            type="button"
            className="icon-btn-subtle"
            style={{ color: 'inherit', padding: 2 }}
            onClick={() => { speechService.clearError(); setLocalMicError(''); }}
            title="Dismiss error"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {speech.interimTranscript && (
        <div className="voice-live-banner">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, overflow: 'hidden' }}>
            <div className="voice-wave-animation">
              <span className="voice-wave-bar" />
              <span className="voice-wave-bar" />
              <span className="voice-wave-bar" />
            </div>
            <span style={{ fontStyle: 'italic', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
              "{speech.interimTranscript}"
            </span>
          </div>
          <span style={{ fontSize: '0.72rem', color: 'var(--accent-primary)', flexShrink: 0, fontWeight: 500 }}>
            Hearing speech...
          </span>
        </div>
      )}

      <div className="composer-box">
        <textarea
          ref={textareaRef}
          className="composer-input"
          placeholder="Ask Kritam anything, or give a desktop command... (Shift + Enter for newline)"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
        />

        <div className="composer-footer">
          <div className="composer-actions-left">
            <button
              type="button"
              className={`btn-icon btn-mic ${isMicActive && !speech.isBackgroundListening ? 'listening' : ''} ${isMicProcessing ? 'processing' : ''}`}
              onClick={toggleMic}
              disabled={isMicProcessing}
              title={isMicActive ? 'Recording locally. Click to finish and transcribe' : isMicProcessing ? 'Transcribing locally...' : 'Record voice locally (no browser recognition service)'}
            >
              {isMicProcessing ? (
                <Loader2 size={18} className="animate-spin" />
              ) : isMicActive && !speech.isBackgroundListening ? (
                <MicOff size={18} />
              ) : (
                <Mic size={18} />
              )}
            </button>

            <button
              type="button"
              className={`btn-handsfree ${speech.isBackgroundListening ? 'active' : ''}`}
              onClick={toggleBackgroundVoice}
              disabled
              title="Hands-free browser recognition is temporarily disabled while local speech mode is being introduced"
            >
              <Radio size={14} className={speech.isBackgroundListening ? 'animate-pulse' : ''} />
              <span>Hands-Free (coming soon)</span>
            </button>

            {isMicActive && (
              <div className="composer-voice-status listening">
                <span className="model-dot" style={{ backgroundColor: 'var(--danger)', width: 6, height: 6 }} />
                <span>Listening...</span>
              </div>
            )}

            {isMicProcessing && (
              <div className="composer-voice-status processing">
                <Loader2 size={12} className="animate-spin" />
                <span>Transcribing...</span>
              </div>
            )}
            {false && speech.isBackgroundListening && (
              <div className="composer-voice-status listening" role="status" aria-live="polite">
                <span className="model-dot" style={{ backgroundColor: 'var(--success)', width: 6, height: 6 }} />
                <span>Hands-free active · speak naturally; pause when finished</span>
              </div>
            )}
            {isMicActive && (
              <span className="composer-mic-hint" role="status" aria-live="polite">
                Recording · max 5 min · tap mic to finish {micTrackInfo}
                <span aria-label="Microphone level" style={{ display: 'inline-block', width: 42, height: 5, borderRadius: 5, marginLeft: 7, verticalAlign: 'middle', background: `linear-gradient(to right, var(--accent-primary) ${Math.round(micLevel * 100)}%, var(--border-subtle) ${Math.round(micLevel * 100)}%)` }} />
              </span>
            )}

            {speech.ttsState === 'speaking' && (
              <button
                type="button"
                className="btn-stop-speech-badge"
                onClick={() => speechService.stopSpeaking()}
                title="Stop current speech playback"
              >
                <VolumeX size={14} /> Stop Speech
              </button>
            )}
          </div>

          <div>
            {isGenerating ? (
              <button
                type="button"
                className="btn-icon"
                style={{ backgroundColor: 'var(--text-primary)', color: 'var(--bg-app)' }}
                onClick={onStop}
                title="Stop generation"
              >
                <Square size={16} />
              </button>
            ) : (
              <button
                type="button"
                className={`btn-icon btn-send ${text.trim() ? 'has-text' : 'assistant-idle'}`}
                disabled={!text.trim() || isLocalRecording || isLocalTranscribing}
                onClick={handleSend}
                title={text.trim() ? 'Send message (Enter)' : 'KRITAM assistant'}
                aria-label={text.trim() ? 'Send message' : 'KRITAM assistant'}
              >
                {text.trim() ? <ArrowUp size={18} /> : <Sparkles size={18} />}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
