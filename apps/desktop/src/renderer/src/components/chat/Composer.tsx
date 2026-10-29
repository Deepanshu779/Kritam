import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Square, Mic, MicOff, AlertCircle, X, Loader2, VolumeX, Radio } from 'lucide-react';
import { speechService, useSpeechService } from '../../services/speech-service';
import { apiClient } from '../../services/api-client';

interface ComposerProps {
  onSend: (text: string) => void;
  isGenerating: boolean;
  onStop: () => void;
  transcriptionLanguage?: 'auto' | 'en' | 'hi' | 'en-IN' | 'en-US' | 'en-GB';
}

export const Composer: React.FC<ComposerProps> = ({ onSend, isGenerating, onStop, transcriptionLanguage = 'auto' }) => {
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
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      streamRef.current = stream;
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
        setLocalMicError('Audio recording failed. Check microphone permission and try again.');
        setIsLocalRecording(false);
        stream.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      };
      recorder.onstop = async () => {
        if (recordingTimerRef.current !== null) window.clearTimeout(recordingTimerRef.current);
        recordingTimerRef.current = null;
        setIsLocalRecording(false);
        stream.getTracks().forEach(track => track.stop());
        streamRef.current = null;
        const firstChunkType = chunksRef.current.find((chunk) => chunk instanceof Blob && chunk.type)?.type;
        const audio = new Blob(chunksRef.current, { type: recorder.mimeType || firstChunkType || '' });
        chunksRef.current = [];
        if (audio.size < 1200) {
          setLocalMicError('Recording was too short. Please speak for a moment and try again.');
          return;
        }
        setIsLocalTranscribing(true);
        try {
          const language = transcriptionLanguage === 'hi' || transcriptionLanguage === 'hi-IN'
            ? 'hi'
            : transcriptionLanguage === 'en' || transcriptionLanguage?.startsWith('en-') ? 'en' : 'auto';
          const result = await apiClient.transcribeAudio(audio, language, true);
          const transcript = result.text?.trim();
          if (!transcript) {
            setLocalMicError('No speech detected. Please try again a little closer to the microphone.');
            return;
          }
          setText(prev => prev.trim() ? `${prev.trim()} ${transcript}` : transcript);
          requestAnimationFrame(() => {
            if (textareaRef.current) {
              textareaRef.current.focus();
              textareaRef.current.selectionStart = textareaRef.current.value.length;
              textareaRef.current.selectionEnd = textareaRef.current.value.length;
            }
          });
        } catch (error: any) {
          console.error('[Composer] Local transcription failed:', error);
          setLocalMicError(error?.message || 'Local transcription failed. Check the KRITAM backend.');
        } finally {
          setIsLocalTranscribing(false);
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

  useEffect(() => () => {
    if (recordingTimerRef.current !== null) window.clearTimeout(recordingTimerRef.current);
    try { recorderRef.current?.state !== 'inactive' && recorderRef.current?.stop(); } catch {}
    streamRef.current?.getTracks().forEach(track => track.stop());
  }, []);

  const toggleBackgroundVoice = () => {
    if (speech.isBackgroundListening) {
      speechService.stopBackgroundListening();
    } else {
      speechService.clearError();
      speechService.startBackgroundListening(
        (transcript) => {
          // Auto-dispatch voice command directly to agent
          if (transcript.trim()) {
            onSend(transcript.trim());
          }
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
              <span className="composer-mic-hint">Recording · max 5 min · tap mic to finish</span>
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
                className="btn-icon btn-send"
              disabled={!text.trim() || isLocalRecording || isLocalTranscribing}
                onClick={handleSend}
                title="Send message (Enter)"
              >
                <ArrowUp size={18} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
