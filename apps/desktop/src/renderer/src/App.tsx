import React, { useState, useEffect, useRef } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { MessageItem } from './components/chat/MessageItem';
import { Composer } from './components/chat/Composer';
import { EmptyState } from './components/chat/EmptyState';
import { SettingsModal } from './components/settings/SettingsModal';
import { ConfirmationModal } from './components/common/ConfirmationModal';
import { CompanionAvatar, CompanionState } from './components/companion/CompanionAvatar';
import { apiClient } from './services/api-client';
import { speechService, useSpeechService } from './services/speech-service';
import { Conversation, HealthStatus, Message } from './types/chat';
import { UserSettings, ThemeMode } from './types/settings';
import { Sparkles, StopCircle, RefreshCw, Radio, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

export const App: React.FC = () => {
  const speech = useSpeechService();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  // Keep a synchronous source of truth for async sends and conversation switching.
  const activeConvIdRef = useRef<string | null>(null);
  const generationInFlightRef = useRef(false);
  const selectionRequestRef = useRef(0);
  const setActiveConversation = (id: string | null) => {
    activeConvIdRef.current = id;
    setActiveConvId(id);
  };
  const [messages, setMessages] = useState<Message[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isExecutingAction, setIsExecutingAction] = useState(false);
  const [lastTaskStatus, setLastTaskStatus] = useState<'completed' | 'needs_attention' | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [settings, setSettings] = useState<UserSettings>({
    theme: 'dark',
    default_provider: 'offline',
    enable_tts_auto: false,
    voice_response_enabled: true,
    tts_rate: 1.0,
    enable_companion: true,
    voice_language: 'auto'
  });
  
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    consequences?: string;
    isDestructive?: boolean;
    onConfirm: () => void;
  }>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {}
  });

  const [companionState, setCompanionState] = useState<CompanionState>('idle');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const stopStreamRef = useRef<(() => void) | null>(null);

  // Initial load
  useEffect(() => {
    loadHealth();
    loadSettings();
    loadConversations();
  }, []);

  // Theme application
  const applyTheme = (theme: ThemeMode) => {
    const root = document.documentElement;
    root.setAttribute('data-theme', theme);
    const meta = document.querySelector('meta[name="color-scheme"]');
    if (meta) {
      meta.setAttribute('content', theme === 'system' ? 'light dark' : theme);
    }
    localStorage.setItem('kritam-theme', theme);
  };

  const toggleTheme = () => {
    const next: ThemeMode = settings.theme === 'dark' ? 'light' : settings.theme === 'light' ? 'system' : 'dark';
    const updated = { ...settings, theme: next };
    setSettings(updated);
    applyTheme(next);
    apiClient.saveSettings({ theme: next });
  };

  const loadHealth = async () => {
    try {
      const h = await apiClient.getHealth();
      setHealth(h);
    } catch (e) {
      console.warn('[App] Health check failed:', e);
    }
  };

  const loadSettings = async () => {
    try {
      const s = await apiClient.getSettings();
      if (s) {
        setSettings((prev) => ({ ...prev, ...s }));
        if (s.theme) applyTheme(s.theme);
      }
    } catch (e) {
      console.warn('[App] Load settings error:', e);
    }
  };

  const loadConversations = async () => {
    try {
      const list = await apiClient.getConversations();
      setConversations(list);
      if (list.length > 0 && !activeConvIdRef.current) {
        selectConversation(list[0].id);
      }
    } catch (e) {
      console.warn('[App] Load conversations error:', e);
    }
  };

  const selectConversation = async (id: string) => {
    const requestId = ++selectionRequestRef.current;
    setActiveConversation(id);
    setMessages([]);
    try {
      const fullConv = await apiClient.getConversation(id);
      // Ignore stale responses if the user selected another conversation meanwhile.
      if (requestId !== selectionRequestRef.current || activeConvIdRef.current !== id) return;
      setMessages(fullConv.messages || []);
      scrollToBottom();
    } catch (e) {
      if (requestId === selectionRequestRef.current) {
        console.error('[App] Failed to load conversation:', e);
      }
    }
  };

  const handleNewChat = async () => {
    try {
      const created = await apiClient.createConversation('New Conversation', settings.default_provider);
      setConversations((prev) => [created, ...prev]);
      ++selectionRequestRef.current;
      setActiveConversation(created.id);
      setMessages([]);
    } catch (e) {
      console.error('[App] Failed to create new conversation:', e);
    }
  };

  const handleDeleteConversation = (id: string) => {
    setConfirmModal({
      isOpen: true,
      title: 'Delete Conversation',
      message: 'Are you sure you want to permanently delete this conversation and all its messages?',
      consequences: 'This action cannot be undone. Local messages will be removed from your database.',
      isDestructive: true,
      onConfirm: async () => {
        try {
          await apiClient.deleteConversation(id);
          setConversations((prev) => prev.filter((c) => c.id !== id));
          if (activeConvId === id) {
            ++selectionRequestRef.current;
            setActiveConversation(null);
            setMessages([]);
          }
        } catch (e) {
          console.error('[App] Failed to delete conversation:', e);
        }
        setConfirmModal((prev) => ({ ...prev, isOpen: false }));
      }
    });
  };

  const handleTogglePin = async (id: string, currentPin: boolean) => {
    try {
      await apiClient.updateConversation(id, { is_pinned: !currentPin });
      setConversations((prev) =>
        prev.map((c) => (c.id === id ? { ...c, is_pinned: !currentPin } : c))
      );
    } catch (e) {
      console.error('[App] Failed to pin conversation:', e);
    }
  };

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 50);
  };

  const handleSendMessage = async (text: string, retryUserMessageId?: string, retryAssistantMessageId?: string, voiceCommand = false) => {
    const cleanText = text.trim();
    if (!cleanText || generationInFlightRef.current) return;
    generationInFlightRef.current = true;

    speechService.stopSpeaking();

    let targetConvId = activeConvIdRef.current;
    try {
      if (!targetConvId) {
        const created = await apiClient.createConversation(cleanText.slice(0, 30), settings.default_provider);
        setConversations((prev) => [created, ...prev.filter((c) => c.id !== created.id)]);
        targetConvId = created.id;
        setActiveConversation(created.id);
        setMessages([]);
      }

      const userMsgId = retryUserMessageId || crypto.randomUUID();
      const assistantMsgId = `asst-${Date.now()}`;
      const tempUserMsg: Message = {
        id: userMsgId,
        conversation_id: targetConvId,
        role: 'user',
        content: cleanText,
        created_at: new Date().toISOString()
      };
      const tempAssistantMsg: Message = {
        id: assistantMsgId,
        conversation_id: targetConvId,
        role: 'assistant',
        content: '',
        status: 'generating',
        created_at: new Date().toISOString()
      };

      setMessages((prev) => retryUserMessageId
        ? [...prev.filter((msg) => msg.id !== retryAssistantMessageId), tempAssistantMsg]
        : [...prev, tempUserMsg, tempAssistantMsg]);
      setIsGenerating(true);
      setLastTaskStatus(null);
      setCompanionState('thinking');
      scrollToBottom();

      const stopFn = await apiClient.streamChat(
        targetConvId,
        cleanText,
        settings.default_provider,
        settings.default_provider === 'ollama' ? settings.ollama_model : undefined,
        (token) => {
          setCompanionState('speaking');
          setMessages((prev) => prev.map((msg) =>
            msg.id === assistantMsgId ? { ...msg, content: msg.content + token } : msg
          ));
          if (activeConvIdRef.current === targetConvId) scrollToBottom();
        },
        (fullContent) => {
          generationInFlightRef.current = false;
          setIsGenerating(false);
          setLastTaskStatus('completed');
          setCompanionState('idle');
          setMessages((prev) => prev.map((msg) =>
            msg.id === assistantMsgId ? { ...msg, content: fullContent, status: 'completed' } : msg
          ));
          const shouldSpeak = voiceCommand
            ? settings.voice_response_enabled !== false
            : settings.enable_tts_auto;
          if (shouldSpeak && fullContent && activeConvIdRef.current === targetConvId) {
            const spokenText = fullContent
              .replace(/```action[\s\S]*?```/g, '')
              .replace(/^Status:.*$/gim, '')
              .trim();
            speechService.speak(spokenText, { voiceName: settings.tts_voice, rate: settings.tts_rate });
          }
          // Refresh sidebar metadata only; do not implicitly change the selected chat.
          apiClient.getConversations().then(setConversations).catch((e) =>
            console.warn('[App] Conversation refresh failed:', e)
          );
        },
        (err) => {
          generationInFlightRef.current = false;
          setIsGenerating(false);
          setLastTaskStatus('needs_attention');
          setCompanionState('idle');
          setMessages((prev) => prev.map((msg) =>
            msg.id === assistantMsgId
              ? { ...msg, content: `${msg.content}\n\nError: ${err.message}`, status: 'failed' }
              : msg
          ));
        },
        userMsgId,
        voiceCommand
      );

      stopStreamRef.current = stopFn;
    } catch (e: any) {
      generationInFlightRef.current = false;
      setIsGenerating(false);
      setLastTaskStatus('needs_attention');
      setCompanionState('idle');
      console.error('[App] Failed to send message:', e);
      setMessages((prev) => [...prev, {
        id: `send-error-${Date.now()}`,
        conversation_id: targetConvId || '',
        role: 'system',
        content: `Message could not be sent: ${e?.message || 'Unknown error'}`,
        created_at: new Date().toISOString()
      }]);
    }
  };

  const handleStopGeneration = () => {
    // Interruption: stop generation and cancel any speech immediately
    speechService.stopSpeaking();
    if (stopStreamRef.current) {
      stopStreamRef.current();
      stopStreamRef.current = null;
    }
    generationInFlightRef.current = false;
    setIsGenerating(false);
    setMessages((prev) => prev.map((msg) => msg.status === 'generating' ? { ...msg, status: 'cancelled' } : msg));
    setLastTaskStatus(null);
    setCompanionState('idle');
  };

  const handleExecuteAction = async (actionType: string, target: string, confirmed: boolean = false) => {
    setIsExecutingAction(true);
    setLastTaskStatus(null);
    try {
      const res = await apiClient.executeAction(actionType, target, confirmed);
      if (res.requires_confirmation) {
        setLastTaskStatus('needs_attention');
        setConfirmModal({
          isOpen: true,
          title: `Confirm ${actionType.toUpperCase()}`,
          message: res.message,
          consequences: res.plan?.consequences,
          isDestructive: res.plan?.risk_level === 'high',
          onConfirm: async () => {
            setConfirmModal((prev) => ({ ...prev, isOpen: false }));
            await handleExecuteAction(actionType, target, true);
          }
        });
      } else {
        setLastTaskStatus(res.success ? 'completed' : 'needs_attention');
        const resultMsg: Message = {
          id: `tool-${Date.now()}`,
          conversation_id: activeConvId || '',
          role: 'system',
          content: `**${res.success ? 'Action Complete' : 'Action Failed'}**: ${res.message}${res.output ? `\n\n\`\`\`\n${res.output}\n\`\`\`` : ''}`,
          created_at: new Date().toISOString()
        };
        setMessages((prev) => [
          ...prev.map((message) => {
            if (message.role !== 'assistant') return message;
            const match = message.content.match(/```action\s*\n([\s\S]*?)\n```/);
            if (!match) return message;
            try {
              const action = JSON.parse(match[1]);
              if (action.action_type !== actionType || action.target !== target) return message;
              const updatedAction = {
                ...action,
                status: res.success ? 'succeeded' : 'failed',
                executed: Boolean(res.success),
                message: res.message
              };
              return { ...message, content: message.content.replace(match[0], `\`\`\`action\n${JSON.stringify(updatedAction)}\n\`\`\``) };
            } catch {
              return message;
            }
          }),
          resultMsg
        ]);
        scrollToBottom();
      }
    } catch (e: any) {
      setLastTaskStatus('needs_attention');
      setMessages((prev) => [...prev, {
        id: `action-error-${Date.now()}`,
        conversation_id: activeConvId || '',
        role: 'system',
        content: `**Action Failed**: ${e?.message || 'The action could not be completed.'}`,
        created_at: new Date().toISOString()
      }]);
    } finally {
      setIsExecutingAction(false);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        handleNewChat();
      }
      if (e.key === 'Escape') {
        if (isSettingsOpen) setIsSettingsOpen(false);
        if (isGenerating) handleStopGeneration();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSettingsOpen, isGenerating]);

  const activeConv = conversations.find((c) => c.id === activeConvId);

  // Compute live agent activity state: Listening -> Understanding -> Working -> Completed / Needs Attention
  let agentStatus: 'idle' | 'listening' | 'understanding' | 'working' | 'completed' | 'needs_attention' = 'idle';
  if (confirmModal.isOpen || speech.error) {
    agentStatus = 'needs_attention';
  } else if (speech.voiceState === 'listening') {
    agentStatus = 'listening';
  } else if (speech.voiceState === 'processing') {
    agentStatus = 'understanding';
  } else if (isGenerating || isExecutingAction) {
    agentStatus = 'working';
  } else if (lastTaskStatus === 'completed') {
    agentStatus = 'completed';
  } else if (lastTaskStatus === 'needs_attention') {
    agentStatus = 'needs_attention';
  }

  return (
    <div className="app-container">
      <Sidebar
        conversations={conversations}
        activeId={activeConvId}
        onSelect={selectConversation}
        onNewChat={handleNewChat}
        onDelete={handleDeleteConversation}
        onTogglePin={handleTogglePin}
        onOpenSettings={() => setIsSettingsOpen(true)}
        currentTheme={settings.theme}
        onToggleTheme={toggleTheme}
        health={health}
      />

      <main className="main-chat-area">
        <header className="chat-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontWeight: 600, fontSize: '0.96rem', color: 'var(--text-primary)' }}>
              {activeConv?.title || 'Kritam Assistant'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {speech.isBackgroundListening && (
              <button
                type="button"
                className="btn-handsfree active"
                style={{ fontSize: '0.74rem', padding: '3px 9px' }}
                onClick={() => speechService.stopBackgroundListening()}
                title="Hands-free listening is active. Click to pause."
              >
                <Radio size={12} className="animate-pulse" />
                <span>Hands-Free ({settings.voice_language || 'en-US'})</span>
              </button>
            )}

            {speech.ttsState === 'speaking' && (
              <button
                className="btn-secondary"
                style={{ fontSize: '0.78rem', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 6, color: 'var(--accent-primary)', borderColor: 'var(--accent-primary)' }}
                onClick={() => speechService.stopSpeaking()}
              >
                <StopCircle size={14} /> Stop Speech
              </button>
            )}
          </div>
        </header>

        {(!activeConvId || messages.length === 0) ? (
          <EmptyState
            onSelectPrompt={handleSendMessage}
            userName={settings.display_name}
          />
        ) : (
          <div className="messages-container">
            {messages.map((msg) => (
              <MessageItem
                key={msg.id}
                message={msg}
                onExecuteAction={handleExecuteAction}
                onRetry={msg.status === 'failed' ? () => {
                  const index = messages.findIndex((item) => item.id === msg.id);
                  const userMessage = messages.slice(0, index).reverse().find((item) => item.role === 'user');
                  if (userMessage) void handleSendMessage(userMessage.content, userMessage.id, msg.id);
                } : undefined}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}

        <Composer
          onSend={(text, voiceCommand) => handleSendMessage(text, undefined, undefined, voiceCommand)}
          isGenerating={isGenerating}
          onStop={handleStopGeneration}
          transcriptionLanguage={settings.voice_language}
          sttModel={settings.stt_model || 'base'}
          microphoneDeviceId={settings.microphone_device_id}
        />
      </main>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={settings}
        health={health}
        onSave={(updated) => {
          setSettings((prev) => ({ ...prev, ...updated }));
          apiClient.saveSettings(updated);
          if (updated.theme) applyTheme(updated.theme);
        }}
      />

      <ConfirmationModal
        isOpen={confirmModal.isOpen}
        title={confirmModal.title}
        message={confirmModal.message}
        consequences={confirmModal.consequences}
        isDestructive={confirmModal.isDestructive}
        onConfirm={confirmModal.onConfirm}
        onCancel={() => setConfirmModal((prev) => ({ ...prev, isOpen: false }))}
      />
    </div>
  );
};
