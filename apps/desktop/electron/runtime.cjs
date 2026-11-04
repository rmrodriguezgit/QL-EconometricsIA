const { spawn } = require('node:child_process');
const { resolve } = require('node:path');
const { existsSync } = require('node:fs');
const methods = new Set(['engine.health','system.audit','nodes.list','project.validate','worldbank.indicators','projects.list','projects.read','projects.save','projects.delete','projects.restore','examples.list','examples.read','run.start','brain.status','brain.plan','brain.history','brain.feedback','brain.gaps','brain.gaps.update']);
// El cerebro con Qwen local puede tardar más que un cálculo; el resto conserva 60 s.
const timeoutFor = method => method === 'brain.plan' ? 180_000 : 60_000;
function createEngine(root) {
  const children = new Set();
  let stopping = false;
  function request(value) {
    if (stopping) return Promise.reject(new Error('El motor se está cerrando.'));
    const payload = JSON.stringify(value);
    if (!value || value.jsonrpc !== '2.0' || !methods.has(value.method) || Buffer.byteLength(payload) > 4_000_000) return Promise.reject(new Error('Solicitud del motor no permitida.'));
    const python = resolve(root, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python');
    if (!existsSync(python)) return Promise.reject(new Error('Falta Python del proyecto. Ejecuta uv sync en la raíz.'));
    return new Promise((accept,reject) => {
      const child = spawn(python,['-m','quantlabs'],{cwd:root,windowsHide:true,env:{...process.env,PYTHONPATH:resolve(root,'engine'),PYTHONUTF8:'1',WBDATA_CACHE_PATH:resolve(root,'.cache/wbdata/cache')}});
      children.add(child);
      let output='',bytes=0,failure;
      const stop = message => { failure = new Error(message); child.kill(); hardTimer=setTimeout(()=>child.kill('SIGKILL'),1000); };
      const limit=timeoutFor(value.method);
      const timer = setTimeout(()=>stop(`El motor superó ${limit/1000} segundos.`),limit);
      let hardTimer;
      child.on('exit',()=>clearTimeout(hardTimer));
      child.stdout.setEncoding('utf8');
      child.stdout.on('data',chunk=>{bytes+=Buffer.byteLength(chunk);if(bytes>12_000_000){stop('Salida demasiado grande.');return;}output+=chunk.toString('utf8');});
      child.stderr.on('data',()=>{});
      child.stdin.on('error',()=>{});
      child.on('error',error=>{failure=error;});
      child.on('close',code=>{
        clearTimeout(timer);clearTimeout(hardTimer);children.delete(child);
        if(failure || code!==0) {reject(failure??new Error('El motor se detuvo.'));return;}
        try {accept(JSON.parse(output.trim()));} catch {reject(new Error('Respuesta inválida de Python.'));}
      });
      // A killed process cannot hold the application open indefinitely.
      child.stdin.end(payload+'\n');
    });
  }
  async function stop() {
    stopping=true;
    await Promise.all([...children].map(child=>new Promise(resolve=>{
      const timer=setTimeout(()=>child.kill('SIGKILL'),1000);
      child.once('close',()=>{clearTimeout(timer);resolve();});child.kill();
    })));
    stopping=false;
  }
  return {request,stop,active:()=>children.size};
}
function releaseInfo(value,current) {
  if(!value || typeof value.tag_name!=='string' || !/^v?\d+\.\d+\.\d+$/.test(value.tag_name)) throw new Error('Versión publicada no válida.');
  const latest=value.tag_name.replace(/^v/,'');
  const a=latest.split('.').map(Number),b=current.split('.').map(Number);
  let available=false;
  for(let i=0;i<3;i++){if(a[i]!==b[i]){available=a[i]>b[i];break;}}
  return {current,latest,available,url:'https://github.com/rmrodriguezgit/QL-EconometricsIA/releases'};
}
module.exports={createEngine,releaseInfo,timeoutFor};
