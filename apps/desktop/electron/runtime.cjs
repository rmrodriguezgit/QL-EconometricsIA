const { spawn } = require('node:child_process');
const { resolve } = require('node:path');
const { existsSync } = require('node:fs');
const methods = new Set(['engine.health','system.audit','nodes.list','project.validate','worldbank.indicators','projects.list','projects.read','projects.save','projects.delete','projects.restore','examples.list','examples.read','run.start','brain.status','brain.plan','brain.repair','brain.history','brain.feedback','brain.gaps','brain.gaps.update']);
// El cerebro con Qwen local puede tardar más que un cálculo; el resto conserva 60 s.
const timeoutFor = method => method === 'brain.plan' || method === 'brain.repair' ? 180_000 : 60_000;
const os = require('node:os');
const MAX_OUTPUT = 12_000_000;
const RECYCLE_AFTER = 200;     // se reemplaza el proceso tras N solicitudes para acotar memoria
const IDLE_MS = 60_000;        // procesos extra ociosos se cierran tras este tiempo
/** Procesos simultáneos: QL_ENGINE_WORKERS o núcleos − 1, entre 1 y 4 (cada uno carga pandas/statsmodels). */
function defaultWorkers() {
  const raw = Number.parseInt(process.env.QL_ENGINE_WORKERS ?? '', 10);
  if (Number.isInteger(raw) && raw > 0) return Math.min(raw, 16);
  return Math.max(1, Math.min(4, (os.availableParallelism?.() ?? os.cpus().length) - 1));
}
/**
 * Grupo de procesos Python persistentes (multiproceso). Cada trabajador atiende una solicitud a la vez
 * por stdin/stdout (una línea JSON por respuesta); varias solicitudes corren en paralelo en procesos
 * distintos y ya no se paga el arranque de Python y la carga de librerías en cada clic.
 */
function createEngine(root, options = {}) {
  const size = Math.max(1, options.workers ?? defaultWorkers());
  const warmCount = Math.min(size, Math.max(1, options.warm ?? Math.min(2, size)));
  const python = resolve(root, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
  const workers = new Set(), queue = [];
  let stopping = false, generation = 0;
  function spawnWorker() {
    const child = spawn(python, ['-m', 'quantlabs'], { cwd: root, windowsHide: true, env: { ...process.env, PYTHONPATH: resolve(root, 'engine'), PYTHONUTF8: '1', WBDATA_CACHE_PATH: resolve(root, '.cache/wbdata/cache') } });
    const worker = { child, job: null, buffer: '', served: 0, idleTimer: null, generation, closed: false };
    workers.add(worker);
    child.stdout.setEncoding('utf8');
    child.stdout.on('data', chunk => {
      worker.buffer += chunk;
      if (worker.buffer.length > MAX_OUTPUT) { fail(worker, new Error('Salida demasiado grande.')); return; }
      let index;
      while ((index = worker.buffer.indexOf('\n')) >= 0) {
        const line = worker.buffer.slice(0, index); worker.buffer = worker.buffer.slice(index + 1);
        if (line.trim()) settle(worker, line);
      }
    });
    child.stderr.on('data', () => {});
    child.stdin.on('error', () => {});
    child.on('error', error => fail(worker, error));
    child.on('close', () => {
      worker.closed = true; workers.delete(worker); clearTimeout(worker.idleTimer);
      if (worker.job) { const job = worker.job; worker.job = null; clearTimeout(job.timer); job.reject(job.failure ?? new Error('El motor se detuvo.')); }
      pump();
    });
    return worker;
  }
  function kill(worker) {
    if (worker.closed) return;
    worker.child.kill();
    const hard = setTimeout(() => worker.child.kill('SIGKILL'), 1000);
    worker.child.once('close', () => clearTimeout(hard));
  }
  function fail(worker, error) { if (worker.job) worker.job.failure = error; kill(worker); }
  function settle(worker, line) {
    const job = worker.job; worker.job = null;
    if (!job) return;
    clearTimeout(job.timer); worker.served += 1;
    try { job.accept(JSON.parse(line)); } catch { job.reject(new Error('Respuesta inválida de Python.')); }
    if (worker.served >= RECYCLE_AFTER || worker.generation !== generation) { worker.child.stdin.end(); kill(worker); }
    else idle(worker);
    pump();
  }
  function idle(worker) {
    clearTimeout(worker.idleTimer);
    worker.idleTimer = setTimeout(() => { if (!worker.job && workers.size > warmCount) { worker.child.stdin.end(); kill(worker); } }, IDLE_MS);
    worker.idleTimer.unref?.();
  }
  function assign(worker, job) {
    clearTimeout(worker.idleTimer);
    worker.job = job;
    job.timer = setTimeout(() => fail(worker, new Error(`El motor superó ${job.limit / 1000} segundos.`)), job.limit);
    worker.child.stdin.write(job.payload + '\n');
  }
  function pump() {
    if (stopping) return;
    while (queue.length) {
      let worker = [...workers].find(item => !item.job && !item.closed);
      if (!worker && workers.size < size) worker = spawnWorker();
      if (!worker) break;
      assign(worker, queue.shift());
    }
  }
  function send(value, limit) {
    if (stopping) return Promise.reject(new Error('El motor se está cerrando.'));
    if (!existsSync(python)) return Promise.reject(new Error('Falta Python del proyecto. Ejecuta uv sync en la raíz.'));
    return new Promise((accept, reject) => { queue.push({ payload: JSON.stringify(value), limit, accept, reject }); pump(); });
  }
  function request(value) {
    const payload = JSON.stringify(value);
    if (!value || value.jsonrpc !== '2.0' || !methods.has(value.method) || Buffer.byteLength(payload) > 4_000_000) return Promise.reject(new Error('Solicitud del motor no permitida.'));
    return send(value, timeoutFor(value.method));
  }
  /** Arranca los procesos mínimos y carga las librerías antes del primer cálculo. */
  function warm() {
    if (stopping || !existsSync(python)) return Promise.resolve([]);
    const missing = Math.max(0, warmCount - workers.size);
    return Promise.allSettled(Array.from({ length: missing }, (_, i) => {
      const worker = spawnWorker();
      return new Promise((accept, reject) => assign(worker, { payload: JSON.stringify({ jsonrpc: '2.0', id: `warmup-${i}`, method: 'engine.warmup', params: {} }), limit: 60_000, accept, reject }));
    }));
  }
  /** Tras cambiar el código Python: los procesos actuales terminan su trabajo y se reemplazan. */
  function reload() {
    generation += 1;
    for (const worker of workers) if (!worker.job) { worker.child.stdin.end(); kill(worker); }
  }
  async function stop() {
    stopping = true;
    for (const job of queue.splice(0)) job.reject(new Error('El motor se cerró.'));
    await Promise.all([...workers].map(worker => new Promise(done => {
      if (worker.closed) { done(); return; }
      if (worker.job) worker.job.failure = new Error('El motor se cerró.');
      worker.child.once('close', done); kill(worker);
    })));
    stopping = false;
  }
  return { request, warm, reload, stop, active: () => queue.length + [...workers].filter(item => item.job).length, workers: () => workers.size, pids: () => [...workers].map(item => item.child.pid), size };
}
function releaseInfo(value,current) {
  if(!value || typeof value.tag_name!=='string' || !/^v?\d+\.\d+\.\d+$/.test(value.tag_name)) throw new Error('Versión publicada no válida.');
  const latest=value.tag_name.replace(/^v/,'');
  const a=latest.split('.').map(Number),b=current.split('.').map(Number);
  let available=false;
  for(let i=0;i<3;i++){if(a[i]!==b[i]){available=a[i]>b[i];break;}}
  return {current,latest,available,url:'https://github.com/rmrodriguezgit/QL-EconometricsIA/releases'};
}
module.exports={createEngine,releaseInfo,timeoutFor,defaultWorkers};
