import { app, BrowserWindow, dialog, ipcMain, shell, session, IpcMainEvent, IpcMainInvokeEvent } from 'electron';
import path from 'path';
import http from 'http';
import { fileURLToPath } from 'url';
import { BackendManager } from './backend-manager';

const backendManager = new BackendManager();
let mainWindow: BrowserWindow | null = null;
let shutdownInProgress = false;

function isTrustedSender(event: IpcMainEvent | IpcMainInvokeEvent): boolean {
  const contents = mainWindow?.webContents;
  const frame = event.senderFrame;
  if (!contents || event.sender !== contents || !frame || frame !== contents.mainFrame) return false;
  try {
    const current = new URL(frame.url);
    if (current.origin === 'http://127.0.0.1:5173') return true;
    if (current.protocol !== 'file:') return false;
    const expected = path.resolve(__dirname, '../renderer/index.html');
    return path.resolve(fileURLToPath(current)) === expected;
  } catch {
    return false;
  }
}

function isTrustedRendererUrl(url: string, isDev: boolean): boolean {
  try {
    const current = new URL(url);
    if (isDev && current.origin === 'http://127.0.0.1:5173') return true;
    if (current.protocol !== 'file:') return false;
    return path.resolve(fileURLToPath(current)) === path.resolve(__dirname, '../renderer/index.html');
  } catch {
    return false;
  }
}

async function createWindow(): Promise<void> {
  const isDev = process.env.NODE_ENV !== 'production' && !app.isPackaged;

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 820,
    minWidth: 800,
    minHeight: 600,
    title: 'KRITAM',
    frame: true,
    titleBarStyle: 'default',
    backgroundColor: '#0f1117',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true
    }
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  // Handle external link clicks safely in system browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const parsed = new URL(url);
      if (!parsed.username && !parsed.password && (parsed.protocol === 'https:' || parsed.protocol === 'http:')) {
        void shell.openExternal(parsed.toString());
      }
    } catch { /* Malformed URLs are denied. */ }
    return { action: 'deny' };
  });
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (isTrustedRendererUrl(url, isDev)) return;
    event.preventDefault();
    try {
      const parsed = new URL(url);
      if (!parsed.username && !parsed.password && ['https:', 'http:'].includes(parsed.protocol)) {
        void shell.openExternal(parsed.toString());
      }
    } catch { /* Invalid navigation is denied. */ }
  });
  mainWindow.webContents.on('will-redirect', (event, url) => {
    if (!isTrustedRendererUrl(url, isDev)) event.preventDefault();
  });

  // IPC handlers
  ipcMain.handle('kritam:get-backend-config', (event) => {
    if (!isTrustedSender(event)) throw new Error('Untrusted renderer');
    return {
      baseUrl: backendManager.baseUrl,
      authToken: backendManager.authToken
    };
  });

  ipcMain.handle('kritam:get-system-info', (event) => {
    if (!isTrustedSender(event)) throw new Error('Untrusted renderer');
    return {
      platform: process.platform,
      arch: process.arch,
      version: app.getVersion()
    };
  });

  ipcMain.on('kritam:minimize', (event) => {
    if (!isTrustedSender(event)) return;
    mainWindow?.minimize();
  });

  ipcMain.on('kritam:maximize', (event) => {
    if (!isTrustedSender(event)) return;
    if (mainWindow?.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow?.maximize();
    }
  });

  ipcMain.on('kritam:close', (event) => {
    if (!isTrustedSender(event)) return;
    mainWindow?.close();
  });

  if (isDev) {
    const devUrl = 'http://127.0.0.1:5173';
    let isViteUp = false;

    // Silent socket probe without triggering Electron network error dialogs
    for (let i = 0; i < 15; i++) {
      isViteUp = await new Promise<boolean>((resolve) => {
        const req = http.get(devUrl, { timeout: 800 }, (res) => {
          resolve(res.statusCode !== undefined && res.statusCode < 500);
        });
        req.on('error', () => resolve(false));
        req.on('timeout', () => {
          req.destroy();
          resolve(false);
        });
      });
      if (isViteUp) break;
      await new Promise((r) => setTimeout(r, 400));
    }

    if (isViteUp) {
      await mainWindow.loadURL(devUrl);
    } else {
      console.log('[Main] Dev server not reachable, loading built bundle');
      const indexPath = path.join(__dirname, '../renderer/index.html');
      await mainWindow.loadFile(indexPath);
    }
  } else {
    // Load built renderer index.html
    const indexPath = path.join(__dirname, '../renderer/index.html');
    await mainWindow.loadFile(indexPath);
  }
}

app.whenReady().then(async () => {
  // Grant only microphone access requested by KRITAM's main frame. Deny camera
  // and media permissions from external or untrusted frames.
  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback, details) => {
    const isDevRenderer = process.env.NODE_ENV !== 'production' && !app.isPackaged;
    const trusted = webContents === mainWindow?.webContents && isTrustedRendererUrl(details.requestingUrl || webContents.getURL(), isDevRenderer);
    const mediaTypes = details.mediaTypes || [];
    const audioOnly = mediaTypes.includes('audio') && !mediaTypes.includes('video');
    callback(permission === 'media' && trusted && Boolean(audioOnly));
  });

  try {
    await backendManager.start();
    await createWindow();
  } catch (error) {
    const detail = error instanceof Error ? error.message : 'Unknown backend startup error.';
    await dialog.showMessageBox({
      type: 'error',
      title: 'KRITAM could not start',
      message: 'The local KRITAM service did not start.',
      detail: `${detail}\n\nCheck that Python and the backend dependencies are installed, and that port 8765 is available. KRITAM will not connect to an unrelated service on that port.`
    });
    app.quit();
    return;
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('before-quit', (event) => {
  if (shutdownInProgress) return;
  event.preventDefault();
  shutdownInProgress = true;
  void backendManager.stop().finally(() => app.exit(0));
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
