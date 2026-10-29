import React, { useState, useEffect } from 'react';
import { Copy, Check, Volume2, Square, Sparkles, User, Play, AlertCircle, CheckCircle2, RotateCcw } from 'lucide-react';
import { marked } from 'marked';
import { Message } from '../../types/chat';
import { speechService, useSpeechService } from '../../services/speech-service';

interface MessageItemProps {
  message: Message;
  onExecuteAction?: (actionType: string, target: string) => void;
  onRetry?: () => void;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message, onExecuteAction, onRetry }) => {
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
  let actionData: {
    action_id?: string;
    action_type: string;
    target: string;
    status?: 'succeeded' | 'failed' | 'pending' | 'running';
    executed?: boolean;
    message?: string;
  } | null = null;

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

  const isExecuted = actionData?.executed === true || actionData?.status === 'succeeded';
  const isFailed = actionData?.status === 'failed';

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
                <div
                  className={`action-card ${isExecuted ? 'executed' : isFailed ? 'failed' : ''}`}
                  style={{
                    borderLeft: isExecuted
                      ? '3px solid var(--success)'
                      : isFailed
                      ? '3px solid var(--danger)'
                      : '3px solid var(--accent-primary)'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, flex: 1 }}>
                    <div style={{ marginTop: 2 }}>
                      {isExecuted ? (
                        <CheckCircle2 size={18} style={{ color: 'var(--success)' }} />
                      ) : isFailed ? (
                        <AlertCircle size={18} style={{ color: 'var(--danger)' }} />
                      ) : (
                        <Play size={18} style={{ color: 'var(--accent-primary)' }} />
                      )}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div
                        style={{
                          fontSize: '0.78rem',
                          fontWeight: 600,
                          color: isExecuted ? 'var(--success)' : isFailed ? 'var(--danger)' : 'var(--accent-primary)',
                          textTransform: 'uppercase',
                          letterSpacing: '0.04em'
                        }}
                      >
                        {isExecuted ? 'Action Executed' : isFailed ? 'Action Failed' : 'Desktop Action'}
                      </div>
                      <div style={{ fontSize: '0.88rem', color: 'var(--text-primary)', marginTop: 2 }}>
                        <strong>{actionData.action_type.replace('_', ' ').toUpperCase()}</strong>: {actionData.target}
                      </div>
                      {actionData.message && (
                        <div style={{ fontSize: '0.78rem', color: isFailed ? 'var(--danger)' : 'var(--text-muted)', marginTop: 2 }}>
                          {actionData.message}
                        </div>
                      )}
                    </div>
                  </div>

                  {isExecuted ? (
                    <button
                      className="btn-secondary"
                      style={{ fontSize: '0.76rem', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 5 }}
                      onClick={() => onExecuteAction?.(actionData!.action_type, actionData!.target)}
                      title="Re-run this action if needed"
                    >
                      <RotateCcw size={12} /> Re-run
                    </button>
                  ) : isFailed ? (
                    <button
                      className="btn-secondary"
                      style={{ fontSize: '0.76rem', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 5, color: 'var(--danger)', borderColor: 'var(--danger)' }}
                      onClick={() => onExecuteAction?.(actionData!.action_type, actionData!.target)}
                      title="Retry this action"
                    >
                      <RotateCcw size={12} /> Retry
                    </button>
                  ) : (
                    <button
                      className="btn-primary"
                      style={{ fontSize: '0.8rem', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 6 }}
                      onClick={() => onExecuteAction?.(actionData!.action_type, actionData!.target)}
                    >
                      <Play size={13} /> Run Action
                    </button>
                  )}
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
        {isAssistant && message.status === 'failed' && onRetry && (
          <button className="btn-secondary" style={{ marginTop: 6, fontSize: '0.76rem', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 5 }} onClick={onRetry}>
            <RotateCcw size={12} /> Retry response
          </button>
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
