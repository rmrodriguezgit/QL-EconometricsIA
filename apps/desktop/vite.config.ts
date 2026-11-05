import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { watch } from 'node:fs';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url));
const { createEngine } = createRequire(import.meta.url)('./electron/runtime.cjs') as { createEngine: (root: string) => { request: (value: unknown) => Promise<unknown>; warm: () => Promise<unknown>; reload: () => void; stop: () => Promise<void> } };
function engineBridge(): Plugin {
  return {
    name: 'quantlabs-local-engine',
    configureServer(server) {
      // Mismo grupo de procesos Python persistentes que Electron (electron/runtime.cjs).
      // Sin precarga: en Electron la interfaz usa IPC y este puente queda sin uso; los procesos se abren al primer uso.
      const engine = createEngine(root);
      let pending: ReturnType<typeof setTimeout> | undefined;
      for (const folder of ['engine/quantlabs', 'packages/contracts']) {
        try { watch(resolve(root, folder), { recursive: true }, (_event, file) => { if (!file || !/\.(py|json)$/.test(String(file))) return; clearTimeout(pending); pending = setTimeout(() => engine.reload(), 300); }); } catch { /* sin vigilancia */ }
      }
      server.httpServer?.on('close', () => { void engine.stop(); });
      server.middlewares.use('/api/rpc', (req, res) => {
        // Development transport only. Desktop uses the Rust command and stdio.
        const allowed = new Set(['http://127.0.0.1:1420', 'http://localhost:1420']);
        if (req.method !== 'POST' || !allowed.has(req.headers.origin ?? '') ||
            !req.headers['content-type']?.startsWith('application/json')) {
          res.writeHead(403).end('Acceso local no autorizado.'); return;
        }
        let size = 0;
        const chunks: Buffer[] = [];
        req.on('data', (chunk: Buffer) => {
          size += chunk.length;
          if (size > 4_000_000) { res.writeHead(413).end('Proyecto demasiado grande.'); req.destroy(); }
          else chunks.push(chunk);
        });
        req.on('end', () => {
          if (size > 4_000_000) return;
          let value: unknown;
          try { value = JSON.parse(Buffer.concat(chunks).toString('utf8')); } catch { res.writeHead(400).end('JSON inválido.'); return; }
          engine.request(value).then(response => {
            if (res.writableEnded) return;
            res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
            res.end(JSON.stringify(response));
          }, (error: Error) => {
            if (res.writableEnded) return;
            const status = /superó/.test(error.message) ? 504 : /no permitida/.test(error.message) ? 403 : /Falta Python/.test(error.message) ? 503 : 500;
            res.writeHead(status).end(error.message);
          });
        });
      });
    },
  };
}
export default defineConfig({ plugins: [react(), engineBridge()], server: { port: 1420, strictPort: true, fs: { allow: [resolve(root,'apps/desktop'), resolve(root,'packages/contracts')] } }, clearScreen: false });
