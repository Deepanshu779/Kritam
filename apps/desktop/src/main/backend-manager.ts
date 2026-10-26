import { ChildProcess, spawn } from 'child_process';
import path from 'path';
import crypto from 'crypto';
import http from 'http';

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

  public async isAlreadyRunning(): Promise<boolean> {
    return new Promise((resolve) => {
      // Check the root endpoint '/' which returns {service: "KRITAM AI", status: "online"} without auth headers
      const req = http.get(`${this.baseUrl}/`, { timeout: 1500 }, (res) => {
        // Any HTTP response from our port means a backend is listening
        if (res.statusCode && res.statusCode >= 200 && res.statusCode < 500) {
          resolve(true);
        } else {
          resolve(false);
        }
      });
      req.on('error', () => resolve(false));
      req.on('timeout', () => {
        req.destroy();
        resolve(false);
      });
    });
  }

  public async start(): Promise<void> {
    const running = await this.isAlreadyRunning();
    if (running) {
      console.log('[BackendManager] Backend is already running at', this.baseUrl);
      return;
    }

    const projectRoot = path.resolve(__dirname, '../../../..');
    const venvPython = path.join(projectRoot, '.venv', 'Scripts', 'python.exe');
    const backendDir = path.join(projectRoot, 'backend');

    console.log('[BackendManager] Spawning backend server with Python:', venvPython);

    const env = {
      ...process.env,
      KRITAM_BACKEND_HOST: this.host,
      KRITAM_BACKEND_PORT: this.port.toString(),
      KRITAM_AUTH_TOKEN: this.authToken,
      PYTHONPATH: backendDir
    };

    try {
      this.process = spawn(
        venvPython,
        ['-m', 'uvicorn', 'app.main:app', '--host', this.host, '--port', this.port.toString()],
        {
          cwd: backendDir,
          env,
          stdio: ['ignore', 'pipe', 'pipe']
        }
      );

      this.process.stdout?.on('data', (data) => {
        console.log(`[Backend stdout]: ${data}`);
      });

      this.process.stderr?.on('data', (data) => {
        console.error(`[Backend stderr]: ${data}`);
      });

      this.process.on('close', (code) => {
        console.log(`[BackendManager] Backend process exited with code ${code}`);
        this.process = null;
      });

      // Poll until healthy or 15s timeout
      await this.waitForHealth(15000);
    } catch (err) {
      console.error('[BackendManager] Failed to spawn backend process:', err);
    }
  }

  private async waitForHealth(timeoutMs: number): Promise<void> {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const healthy = await this.isAlreadyRunning();
      if (healthy) {
        console.log('[BackendManager] Backend is healthy at', this.baseUrl);
        return;
      }
      await new Promise((r) => setTimeout(r, 500));
    }
    console.warn('[BackendManager] Health check timed out, continuing anyway.');
  }

  public stop(): void {
    if (this.process) {
      console.log('[BackendManager] Terminating backend process...');
      this.process.kill('SIGINT');
      this.process = null;
    }
  }
}
