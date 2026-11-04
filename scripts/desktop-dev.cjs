#!/usr/bin/env node
// Supervisor de desarrollo: Vite (en proceso) con recarga en caliente + Electron sobre 127.0.0.1:1420.
// - Cambios en src/ se aplican al instante (HMR); cambios en electron/*.cjs reinician Electron.
// - Al salir de Electron, con Ctrl+C o al cerrar la terminal se terminan Vite, Electron y el motor.
const {spawn}=require('node:child_process');
const {watch,existsSync}=require('node:fs');
const {join,resolve}=require('node:path');
const {pathToFileURL}=require('node:url');

const root=resolve(__dirname,'..');
const desktop=join(root,'apps','desktop');
const PORT=1420;
const RESTART_CODE=75; // Electron pide reinicio al supervisor (menú «Reiniciar aplicación»).
const MAIN_FILES=new Set(['main.cjs','runtime.cjs','preload.cjs']);
const posix=process.platform!=='win32';

let server,electron,closing=false,restartPending=false,debounce;

function start(command,args,extra={}){
  // En POSIX cada hijo encabeza su grupo de procesos para poder matar también a sus descendientes.
  return spawn(command,args,{cwd:desktop,stdio:'inherit',detached:posix,windowsHide:true,...extra});
}

function kill(child,signal='SIGTERM'){
  if(!child||child.exitCode!==null||child.signalCode!==null)return;
  try{
    if(posix)process.kill(-child.pid,signal);
    else spawn('taskkill',['/pid',String(child.pid),'/T','/F'],{windowsHide:true});
  }catch{/* ya terminó */}
}

function stopChild(child,timeout=3000){
  return new Promise(done=>{
    if(!child||child.exitCode!==null||child.signalCode!==null){done();return;}
    const timer=setTimeout(()=>kill(child,'SIGKILL'),timeout);
    child.once('exit',()=>{clearTimeout(timer);done();});
    kill(child);
  });
}

function launchElectron(){
  const cli=join(desktop,'node_modules','electron','cli.js');
  electron=start(process.execPath,[cli,'.','--dev'],{env:{...process.env,QL_DEV_SUPERVISOR:String(process.pid)}});
  const child=electron;
  child.on('exit',code=>{
    if(child!==electron||closing)return;
    if(restartPending||code===RESTART_CODE){restartPending=false;console.log('\n↻ Reiniciando Electron…\n');launchElectron();return;}
    // El usuario cerró la aplicación: no dejar nada en memoria.
    void shutdown(code??0);
  });
}

async function shutdown(code=0){
  if(closing)return;
  closing=true;
  clearTimeout(debounce);
  await stopChild(electron);
  await server?.close().catch(()=>{});
  console.log('\nQuantlabs cerrado: Vite, Electron y el motor terminados.');
  process.exit(code);
}

async function main(){
  for(const need of ['node_modules/electron/cli.js','node_modules/vite/dist/node/index.js']){
    if(!existsSync(join(desktop,need)))throw new Error('Faltan dependencias del escritorio: npm ci --prefix apps/desktop');
  }
  if(!existsSync(join(root,'.venv',posix?'bin/python':'Scripts/python.exe')))throw new Error('Falta el Python del proyecto: uv sync --frozen');
  for(const signal of ['SIGINT','SIGTERM','SIGHUP'])process.on(signal,()=>void shutdown(130));
  console.log('Quantlabs · modo desarrollo (recarga en caliente). Ctrl+C o «Salir por completo» cierran todo.\n');
  // Vite corre dentro de este proceso: si el supervisor muere, Vite muere con él.
  const {createServer}=await import(pathToFileURL(join(desktop,'node_modules','vite','dist','node','index.js')).href);
  server=await createServer({root:desktop,configFile:join(desktop,'vite.config.ts'),server:{host:'127.0.0.1',port:PORT,strictPort:true}});
  await server.listen();
  console.log(`Interfaz en http://127.0.0.1:${PORT} (HMR activo).`);
  launchElectron();
  // El proceso principal de Electron no admite HMR: reiniciarlo al editar sus archivos.
  watch(join(desktop,'electron'),(_event,file)=>{
    if(!file||!MAIN_FILES.has(String(file)))return;
    clearTimeout(debounce);
    debounce=setTimeout(()=>{if(closing)return;console.log(`\n✎ ${file} cambió.`);restartPending=true;kill(electron);},300);
  });
}

if(require.main===module)main().catch(error=>{console.error(`\nNo se pudo arrancar el modo desarrollo.\n${error.message}\n`);void shutdown(1);});
module.exports={RESTART_CODE};
