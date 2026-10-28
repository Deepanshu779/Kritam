export type ThemeMode = 'dark' | 'light' | 'system';

export interface UserSettings {
  display_name?: string;
  theme: ThemeMode;
  default_provider: 'kritam' | 'offline' | 'ollama' | 'openai' | 'groq' | 'openrouter';
  gateway_url?: string;
  openai_api_key?: string;
  groq_api_key?: string;
  openrouter_api_key?: string;
  ollama_endpoint?: string;
  ollama_model?: string;
  enable_tts_auto?: boolean;
  tts_rate?: number;
  tts_voice?: string;
  enable_companion?: boolean;
  enable_developer_mode?: boolean;
  voice_language?: 'en-IN' | 'en-US' | 'en-GB';
  enable_background_voice?: boolean;
  auto_dispatch_voice?: boolean;
}
