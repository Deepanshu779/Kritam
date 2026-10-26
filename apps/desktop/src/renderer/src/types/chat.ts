export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  tool_calls?: string | null;
  tool_results?: string | null;
  status?: 'completed' | 'generating' | 'failed' | 'cancelled';
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  is_pinned: boolean;
  is_archived: boolean;
  model_used: string;
  created_at: string;
  updated_at: string;
  message_count?: number;
  last_message?: string | null;
  messages?: Message[];
}

export interface StreamEvent {
  message_id: string;
  delta: string;
  done: boolean;
  content?: string;
  error?: string;
}

export interface ProviderInfo {
  available: boolean;
  name: string;
  details?: string;
  model?: string;
  models?: string[];
  endpoint?: string;
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  default_provider: string;
  providers: Record<string, ProviderInfo>;
}
