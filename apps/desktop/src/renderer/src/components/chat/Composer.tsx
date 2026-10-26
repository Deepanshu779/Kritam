import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Square, Mic, MicOff, AlertCircle, X, Loader2, VolumeX } from 'lucide-react';
import { speechService, useSpeechService } from '../../services/speech-service';

interface ComposerProps {
  onSend: (text: string) => void;
  isGenerating: boolean;
  onStop: () => void;
}

export const Composer: React.FC<ComposerProps> = ({ onSend, isGenerating, onStop }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const speech = useSpeechService();

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
    if (!trimmed || isGenerating) return;

    // Interruption: Stop active speech playback if user sends new message
    if (speech.ttsState === 'speaking') {
      speechService.stopSpeaking();
    }

    // Stop active listening if sending
    if (speech.voiceState === 'listening') {
      speechService.stopListening();
    }

    onSend(trimmed);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const toggleMic = () => {
    if (speech.voiceState === 'listening') {
      speechService.stopListening();
    } else if (speech.voiceState === 'processing') {
      speechService.abortListening();
    } else {
      // Clear any prior speech error
      speechService.clearError();

      speechService.startListening(
        (transcript) => {
          // Preserve existing text and append cleanly
          setText((prev) => {
            const cleanPrev = prev.trim();
            return cleanPrev ? `${cleanPrev} ${transcript}` : transcript;
          });
          // Focus textarea so user can review or immediately press Enter
          setTimeout(() => {
            if (textareaRef.current) {
              textareaRef.current.focus();
              textareaRef.current.selectionStart = textareaRef.current.value.length;
              textareaRef.current.selectionEnd = textareaRef.current.value.length;
            }
          }, 50);
        },
        (error) => {
          console.warn('[Composer] Speech error:', error);
        },
        () => {
          // On normal end
        }
      );
    }
  };

  const isMicActive = speech.voiceState === 'listening';
  const isMicProcessing = speech.voiceState === 'processing';

  return (
    <div className="composer-wrapper">
      {speech.error && (
        <div className="composer-voice-error" role="alert">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertCircle size={15} style={{ flexShrink: 0 }} />
            <span>{speech.error}</span>
          </div>
          <button
            type="button"
            className="icon-btn-subtle"
            style={{ color: 'inherit', padding: 2 }}
            onClick={() => speechService.clearError()}
            title="Dismiss error"
          >
            <X size={14} />
          </button>
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
              className={`btn-icon btn-mic ${isMicActive ? 'listening' : ''} ${isMicProcessing ? 'processing' : ''}`}
              onClick={toggleMic}
              disabled={!speech.isSTTSupported}
              title={
                !speech.isSTTSupported
                  ? 'Speech recognition not supported in this environment'
                  : isMicActive
                  ? 'Listening... Click to stop recording'
                  : isMicProcessing
                  ? 'Processing audio... Click to cancel'
                  : 'Voice input (Push to talk)'
              }
            >
              {isMicProcessing ? (
                <Loader2 size={18} className="animate-spin" />
              ) : isMicActive ? (
                <MicOff size={18} />
              ) : (
                <Mic size={18} />
              )}
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
                disabled={!text.trim()}
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
