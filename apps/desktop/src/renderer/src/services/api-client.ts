import { Conversation, HealthStatus, Message } from '../types/chat';
import { UserSettings } from '../types/settings';

class ApiClient {
  private baseUrl: string = 'http://127.0.0.1:8765';
  private authToken: string = '';
  private initialized: boolean = false;

  public async init(): Promise<void> {
    if (this.initialized) return;
    if (window.kritamAPI) {
      try {
        const config = await window.kritamAPI.getBackendConfig();
        if (config?.baseUrl) this.baseUrl = config.baseUrl;
        if (config?.authToken) this.authToken = config.authToken;
      } catch (e) {
        console.warn('[ApiClient] Failed to get backend config from Electron IPC:', e);
      }
    }
    this.initialized = true;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    await this.init();
    const headers = new Headers(options.headers || {});
    if (this.authToken) {
      headers.set('X-Kritam-Auth-Token', this.authToken);
    }
    headers.set('Content-Type', 'application/json');

    const res = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers
    });

    if (!res.ok) {
      const err = await res.text().catch(() => 'Unknown error');
      throw new Error(`API Error [${res.status}]: ${err}`);
    }

    if (res.status === 204) {
      return null as T;
    }
    return res.json();
  }

  public async getHealth(): Promise<HealthStatus> {
    return this.request<HealthStatus>('/api/health');
  }

  public async getConversations(): Promise<Conversation[]> {
    return this.request<Conversation[]>('/api/conversations');
  }

  public async createConversation(title: string = 'New Conversation', model_used: string = 'offline'): Promise<Conversation> {
    return this.request<Conversation>('/api/conversations', {
      method: 'POST',
      body: JSON.stringify({ title, model_used })
    });
  }

  public async getConversation(id: string): Promise<Conversation> {
    return this.request<Conversation>(`/api/conversations/${id}`);
  }

  public async updateConversation(id: string, updates: Partial<Conversation>): Promise<Conversation> {
    return this.request<Conversation>(`/api/conversations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates)
    });
  }

  public async deleteConversation(id: string): Promise<void> {
    return this.request<void>(`/api/conversations/${id}`, {
      method: 'DELETE'
    });
  }

  public async getSettings(): Promise<UserSettings> {
    return this.request<UserSettings>('/api/settings');
  }

  public async saveSettings(settings: Partial<UserSettings>): Promise<any> {
    return this.request('/api/settings', {
      method: 'POST',
      body: JSON.stringify(settings)
    });
  }

  public async executeAction(actionType: string, target: string, confirmed: boolean = false): Promise<any> {
    return this.request('/api/actions/execute', {
      method: 'POST',
      body: JSON.stringify({ action_type: actionType, target, confirmed })
    });
  }

  public async streamChat(
    conversationId: string,
    message: string,
    provider?: string,
    model?: string,
    onToken?: (token: string) => void,
    onDone?: (fullContent: string) => void,
    onError?: (err: Error) => void
  ): Promise<() => void> {
    await this.init();
    const controller = new AbortController();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    };
    if (this.authToken) {
      headers['X-Kritam-Auth-Token'] = this.authToken;
    }

    (async () => {
      try {
        const response = await fetch(`${this.baseUrl}/api/chat/stream`, {
          method: 'POST',
          headers,
          body: JSON.stringify({
            conversation_id: conversationId,
            message,
            provider,
            model,
            stream: true
          }),
          signal: controller.signal
        });

        if (!response.ok || !response.body) {
          throw new Error(`Failed to stream chat: status ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullContent = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const block of lines) {
            const line = block.trim();
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.substring(6));
                if (data.delta) {
                  fullContent += data.delta;
                  onToken?.(data.delta);
                }
                if (data.done) {
                  onDone?.(data.content || fullContent);
                  return;
                }
                if (data.error) {
                  onError?.(new Error(data.error));
                  return;
                }
              } catch (e) {
                // Ignore parse errors on partial chunks
              }
            }
          }
        }
        onDone?.(fullContent);
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          onError?.(err);
        }
      }
    })();

    return () => controller.abort();
  }
}

export const apiClient = new ApiClient();
