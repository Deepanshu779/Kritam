import React, { useState, useEffect } from 'react';
import { Copy, Check, Volume2, Square, Sparkles, User, Play, AlertCircle } from 'lucide-react';
import { marked } from 'marked';
import { Message } from '../../types/chat';
import { speechService, useSpeechService } from '../../services/speech-service';

interface MessageItemProps {
  message: Message;
  onExecuteAction?: (actionType: string, target: string) => void;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message, onExecuteAction }) => {
  const [copied, setCopied] = useState(false);
  const [isSpeakingThis, setIsSpeakingThis] = useState(false);
  const speech = useSpeechService();
  const isAssistant = message.role === 'assistant';

  useEffect(() => {
    if (speech.ttsState === 'idle') {
      setIsSpeakingThis(false);
    }
  }, [speech.ttsState]);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSpeak = () => {
    if (isSpeakingThis && speech.ttsState === 'speaking') {
      speechService.stopSpeaking();
      setIsSpeakingThis(false);
    } else {
      setIsSpeakingThis(true);
      speechService.speak(message.content, {
        onStart: () => setIsSpeakingThis(true),
        onEnd: () => setIsSpeakingThis(false)
      });
    }
  };

  // Check if content has an embedded action command like ```action\n{...}\n```
  let actionData: { action_type: string; target: string } | null = null;
  const actionMatch = message.content.match(/```action\s*\n([\s\S]*?)\n```/);
  if (actionMatch) {
    try {
      actionData = JSON.parse(actionMatch[1]);
    } catch (e) {
      // Ignore parse failure
    }
  }

  // Sanitize and render markdown
  const cleanMarkdown = message.content.replace(/```action[\s\S]*?```/g, '');
  const htmlContent = marked.parse(cleanMarkdown, { breaks: true }) as string;

  return (
    <div className={`message-row ${message.role}`}>
      {isAssistant && (
        <div className="avatar-circle assistant">
          <Sparkles size={18} />
        </div>
      )}

      <div className={`message-content`}>
        <div className={`message-bubble ${message.role}`}>
          {isAssistant ? (
            <>
              <div
                dangerouslySetInnerHTML={{ __html: htmlContent }}
                style={{ wordBreak: 'break-word' }}
              />

              {actionData && (
                <div className="action-card">
                  <div>
                    <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      Desktop Action
                    </div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', marginTop: 2 }}>
                      <strong>{actionData.action_type.replace('_', ' ').toUpperCase()}</strong>: {actionData.target}
                    </div>
                  </div>
                  <button
                    className="btn-primary"
                    style={{ fontSize: '0.8rem', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 6 }}
                    onClick={() => onExecuteAction?.(actionData!.action_type, actionData!.target)}
                  >
                    <Play size={13} /> Run Action
                  </button>
                </div>
              )}
            </>
          ) : (
            <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
          )}
        </div>

        {isAssistant && message.content && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6, paddingLeft: 4 }}>
            <button
              className="icon-btn-subtle"
              onClick={handleCopy}
              title={copied ? 'Copied to clipboard' : 'Copy response'}
            >
              {copied ? <Check size={14} style={{ color: 'var(--success)' }} /> : <Copy size={14} />}
            </button>
            <button
              className="icon-btn-subtle"
              onClick={handleSpeak}
              title={isSpeakingThis ? 'Stop speaking' : 'Read aloud'}
              style={{ color: isSpeakingThis ? 'var(--accent-primary)' : 'inherit' }}
            >
              {isSpeakingThis ? <Square size={14} /> : <Volume2 size={14} />}
            </button>
          </div>
        )}
      </div>

      {!isAssistant && (
        <div className="avatar-circle user">
          <User size={16} />
        </div>
      )}
    </div>
  );
};
