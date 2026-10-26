import { app, BrowserWindow, ipcMain, shell, session } from 'electron';
import path from 'path';
import http from 'http';
import { BackendManager } from './backend-manager';

const backendManager = new BackendManager();
let mainWindow: BrowserWindow | null = null;

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
    if (url.startsWith('https:') || url.startsWith('http:')) {
      shell.openExternal(url);
    }
    return { action: 'deny' };
  });

  // IPC handlers
  ipcMain.handle('kritam:get-backend-config', () => {
    return {
      baseUrl: backendManager.baseUrl,
      authToken: backendManager.authToken
    };
  });

  ipcMain.handle('kritam:get-system-info', () => {
    return {
      platform: process.platform,
      arch: process.arch,
      version: app.getVersion()
    };
  });

  ipcMain.on('kritam:minimize', () => {
    mainWindow?.minimize();
  });

  ipcMain.on('kritam:maximize', () => {
    if (mainWindow?.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow?.maximize();
    }
  });

  ipcMain.on('kritam:close', () => {
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
  // Allow microphone and audio capture for Web Speech API in renderer
  session.defaultSession.setPermissionRequestHandler((_webContents, permission, callback) => {
    if (permission === 'media') {
      callback(true);
      return;
    }
    callback(false);
  });

  session.defaultSession.setPermissionCheckHandler((_webContents, permission) => {
    return permission === 'media';
  });

  await backendManager.start();
  await createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('before-quit', () => {
  backendManager.stop();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    backendManager.stop();
    app.quit();
  }
});
