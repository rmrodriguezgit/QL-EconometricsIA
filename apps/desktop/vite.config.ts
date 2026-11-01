import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url));
function engineBridge(): Plugin {
  return {
    name: 'quantlabs-local-engine',
    configureServer(server) {
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
          const python = resolve(root, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
          if (!existsSync(python)) { res.writeHead(503).end('Ejecuta uv sync en la raíz del proyecto.'); return; }
          const child = spawn(python, ['-m', 'quantlabs'], {
            cwd: root, env: { ...process.env, PYTHONPATH: resolve(root, 'engine'), PYTHONUTF8: '1', WBDATA_CACHE_PATH: resolve(root, '.cache/wbdata/cache') },
          });
          let output = '';
          const timer = setTimeout(() => { child.kill(); res.writeHead(504).end('El motor superó 60 segundos.'); }, 60_000);
          child.stdout.setEncoding('utf8').on('data', (chunk: string) => {
            output += chunk;
            if (output.length > 12_000_000) child.kill();
          });
          child.stderr.on('data', (chunk: Buffer) => process.stderr.write(chunk));
          child.on('error', () => { clearTimeout(timer); if (!res.writableEnded) res.writeHead(503).end('No se pudo iniciar Python.'); });
          child.on('close', (code) => {
            clearTimeout(timer);
            if (res.writableEnded) return;
            if (code !== 0 || !output.trim()) { res.writeHead(500).end('El motor se detuvo.'); return; }
            res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' });
            res.end(output.trim());
          });
          res.on('close', () => { if (!child.killed) child.kill(); clearTimeout(timer); });
          child.stdin.end(Buffer.concat(chunks).toString('utf8') + '\n');
        });
      });
    },
  };
}
export default defineConfig({ plugins: [react(), engineBridge()], server: { port: 1420, strictPort: true }, clearScreen: false });
