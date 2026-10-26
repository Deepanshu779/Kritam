import { contextBridge, ipcRenderer } from 'electron';

export interface BackendConfig {
  baseUrl: string;
  authToken: string;
}

export interface SystemInfo {
  platform: string;
  arch: string;
  version: string;
}

const kritamAPI = {
  getBackendConfig: (): Promise<BackendConfig> => ipcRenderer.invoke('kritam:get-backend-config'),
  getSystemInfo: (): Promise<SystemInfo> => ipcRenderer.invoke('kritam:get-system-info'),
  minimize: (): void => ipcRenderer.send('kritam:minimize'),
  maximize: (): void => ipcRenderer.send('kritam:maximize'),
  close: (): void => ipcRenderer.send('kritam:close')
};

contextBridge.exposeInMainWorld('kritamAPI', kritamAPI);

declare global {
  interface Window {
    kritamAPI: typeof kritamAPI;
  }
}
