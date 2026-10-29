export {};

declare global {
  interface Window {
    kritamAPI?: {
      getBackendConfig: () => Promise<{ baseUrl: string; authToken: string }>;
      getSystemInfo: () => Promise<{ platform: string; arch: string; version: string }>;
      minimize: () => void;
      maximize: () => void;
      close: () => void;
    };
  }
}
