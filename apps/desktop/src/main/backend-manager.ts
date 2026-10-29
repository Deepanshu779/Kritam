import { ChildProcess, spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import crypto from 'crypto';
import http from 'http';
import { app } from 'electron';

export class BackendManager {
  private process: ChildProcess | null = null;
  public readonly port: number = 8765;
  public readonly host: string = '127.0.0.1';
  public readonly authToken: string;

  constructor() {
    this.authToken = crypto.randomBytes(24).toString('hex');
  }

  public get baseUrl(): string {
    return `http://${this.host}:${this.port}`;
  }

  private async isOwnedBackendHealthy(): Promise<boolean> {
    return new Promise((resolve) => {
      const req = http.get(`${this.baseUrl}/api/health/ping`, {
        timeout: 1200,
        headers: { 'X-Kritam-Auth-Token': this.authToken }
      }, (res) => {
        if (res.statusCode !== 200) {
          res.resume();
          resolve(false);
          return;
        }
        let body = '';
        res.setEncoding('utf8');
        res.on('data', (chunk: string) => {
          body += chunk;
          if (body.length > 4096) {
            req.destroy();
            resolve(false);
          }
        });
        res.on('end', () => {
          try {
            const health = JSON.parse(body);
            resolve(res.statusCode === 200 && health.status === 'healthy' && health.service === 'KRITAM AI');
          } catch {
            resolve(false);
          }
        });
      });
      req.on('error', () => resolve(false));
      req.on('timeout', () => {
        req.destroy();
        resolve(false);
      });
    });
  }

  public async start(): Promise<void> {
    if (this.process?.pid && await this.isOwnedBackendHealthy()) {
      console.log('[BackendManager] Owned backend is healthy at', this.baseUrl);
      return;
    }

    let projectRoot = path.resolve(__dirname, '../../../..');
    let venvPython = path.join(projectRoot, '.venv', 'Scripts', 'python.exe');
    let backendDir = path.join(projectRoot, 'backend');
    let dataDir = path.join(projectRoot, 'backend', 'data');
    let packagedBackendExecutable: string | null = null;

    if (app && app.isPackaged) {
      const resourcesDir = process.resourcesPath;
      backendDir = path.join(resourcesDir, 'backend');
      packagedBackendExecutable = path.join(backendDir, 'kritam-backend.exe');
      dataDir = path.join(app.getPath('userData'), 'data');
      if (!fs.existsSync(packagedBackendExecutable)) {
        throw new Error('The KRITAM backend runtime is missing from this installation. Rebuild the Windows package using the release build script.');
      }
    }

    if (!packagedBackendExecutable && !fs.existsSync(venvPython)) {
      venvPython = 'python';
    }

    if (!packagedBackendExecutable && !fs.existsSync(backendDir)) {
      throw new Error(`KRITAM backend source directory was not found at ${backendDir}.`);
    }
    fs.mkdirSync(dataDir, { recursive: true });

    console.log('[BackendManager] Spawning backend server with Python:', venvPython);

    const env = {
      ...process.env,
      KRITAM_BACKEND_HOST: this.host,
      KRITAM_BACKEND_PORT: this.port.toString(),
      KRITAM_AUTH_TOKEN: this.authToken,
      KRITAM_ENV: app?.isPackaged ? 'production' : (process.env.KRITAM_ENV || 'development'),
      KRITAM_DATA_DIR: dataDir,
      PYTHONPATH: backendDir
    };

    const backendCommand = packagedBackendExecutable || venvPython;
    const backendArgs = packagedBackendExecutable
      ? []
      : ['-m', 'uvicorn', 'app.main:app', '--host', this.host, '--port', this.port.toString(), '--no-access-log'];
    this.process = spawn(
      backendCommand,
      backendArgs,
      { cwd: backendDir, env, stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true }
    );
    const child = this.process;

    child.stdout?.on('data', (data) => console.log(`[Backend stdout]: ${data}`));
    child.stderr?.on('data', (data) => console.error(`[Backend stderr]: ${data}`));
    let spawnError: Error | null = null;
    child.on('error', (error) => { spawnError = error; });
    child.on('close', (code) => {
      console.log(`[BackendManager] Owned backend process exited with code ${code}`);
      if (this.process === child) this.process = null;
    });

    try {
      await this.waitForHealth(child, 15000, () => spawnError);
    } catch (err) {
      if (this.process === child) {
        child.kill();
        this.process = null;
      }
      const detail = err instanceof Error ? err.message : String(err);
      throw new Error(`Could not start the KRITAM backend: ${detail}`);
    }
  }

  private async waitForHealth(child: ChildProcess, timeoutMs: number, getSpawnError: () => Error | null): Promise<void> {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const spawnError = getSpawnError();
      if (spawnError) throw new Error(`Python could not be started: ${spawnError.message}`);
      if (child.exitCode !== null || child.signalCode !== null) {
        throw new Error('The backend process exited before becoming healthy. Check the Python backend dependencies and logs.');
      }
      const healthy = await this.isOwnedBackendHealthy();
      if (healthy) {
        console.log('[BackendManager] Owned backend is healthy at', this.baseUrl);
        return;
      }
      await new Promise((r) => setTimeout(r, 500));
    }
    throw new Error('The backend did not pass its authenticated health check within 15 seconds. The port may be occupied by another service.');
  }

  public async stop(): Promise<void> {
    const child = this.process;
    if (!child || child.exitCode !== null || child.signalCode !== null) return;

    console.log('[BackendManager] Terminating owned backend process...');
    await new Promise<void>((resolve) => {
      const timer = setTimeout(() => {
        child.kill();
        resolve();
      }, 2500);
      child.once('close', () => {
        clearTimeout(timer);
        resolve();
      });
      child.kill('SIGTERM');
    });
    if (this.process === child) this.process = null;
  }
}
