#!/usr/bin/env node
// Shared desktop bootstrap. No global installs or changes to the Git checkout.
const {spawnSync}=require('node:child_process');
const {existsSync,readFileSync,writeFileSync,mkdirSync}=require('node:fs');
const {resolve,join}=require('node:path');
const {createHash}=require('node:crypto');
const root=resolve(__dirname,'..');
function commandSpec(command,args,platform=process.platform){
  // Only fixed npm commands pass through cmd.exe; paths stay in cwd, not shell text.
  if(platform==='win32'&&command==='npm'){
    if(![['--version'],['ci'],['run','build']].some(allowed=>JSON.stringify(allowed)===JSON.stringify(args)))throw new Error('Comando npm no permitido');
    return {command:process.env.ComSpec||'cmd.exe',args:['/d','/s','/c',`npm ${args.join(' ')}`]};
  }
  return {command,args};
}
function run(command,args,cwd=root,capture=false){
 const spec=commandSpec(command,args);
 const result=spawnSync(spec.command,spec.args,{cwd,stdio:capture?'pipe':'inherit',encoding:'utf8',windowsHide:true});
 if(result.error||result.status!==0)throw new Error(`${command} ${args.join(' ')}: ${result.error?.message||result.stderr?.trim()||`salida ${result.status}`}`);
 return result.stdout?.trim();
}
function fingerprint(directory){
 return createHash('sha256').update(readFileSync(join(directory,'package.json'))).update(readFileSync(join(directory,'package-lock.json'))).update(process.platform).update(process.arch).update(process.versions.node.split('.')[0]).digest('hex');
}
function needsInstall(directory,stamp,hash){
 return !existsSync(join(directory,'node_modules','electron','cli.js'))||!existsSync(join(directory,'node_modules','.bin',process.platform==='win32'?'tsc.cmd':'tsc'))||!existsSync(stamp)||readFileSync(stamp,'utf8').trim()!==hash;
}
function main(){
 if(Number(process.versions.node.split('.')[0])<22)throw new Error('Instala Node.js 22 o posterior: https://nodejs.org/');
 console.log('\nQuantlabs · preparando el escritorio\n');
 console.log(`Node ${process.versions.node}`);
 try{console.log(run('uv',['--version'],root,true));}catch{throw new Error('Falta uv en PATH. Instálalo desde https://docs.astral.sh/uv/getting-started/installation/ y vuelve a abrir el arrancador.');}
 console.log(`npm ${run('npm',['--version'],root,true)}`);
 if(process.argv.includes('--check')){console.log('Requisitos disponibles. No se han instalado dependencias ni abierto ventanas.');return;}
 const desktop=join(root,'apps','desktop');
 console.log('\n1/4 Preparar Python 3.12 y dependencias bloqueadas…');
 run('uv',['sync','--frozen','--python','3.12']);
 const python=join(root,'.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python');
 if(!existsSync(python))throw new Error('No se encontró el Python del proyecto después de uv sync.');
 const stamp=join(root,'.cache','launcher','desktop.sha256'),hash=fingerprint(desktop);
 console.log('\n2/4 Comprobar dependencias del escritorio…');
 if(needsInstall(desktop,stamp,hash)){
  run('npm',['ci'],desktop);
  mkdirSync(join(root,'.cache','launcher'),{recursive:true});writeFileSync(stamp,hash+'\n');
 }
 if(process.argv.includes('--dev')){
  // Modo desarrollo: sin compilar; Vite recarga la interfaz y el supervisor cierra todo al salir.
  console.log('\n3/3 Abrir Quantlabs en modo desarrollo (recarga en caliente).\n');
  run(process.execPath,[join(__dirname,'desktop-dev.cjs')],desktop);
  return;
 }
 console.log('\n3/4 Construir la interfaz actual…');run('npm',['run','build'],desktop);
 console.log('\n4/4 Abrir Quantlabs. Cierra la aplicación con «Salir por completo».\n');
 run(process.execPath,[join(desktop,'node_modules','electron','cli.js'),'.'],desktop);
}
if(require.main===module){try{main();}catch(error){console.error(`\nNo se pudo arrancar Quantlabs.\n${error.message}\nComprueba la conexión y los requisitos del README. Tus proyectos se conservan.\n`);process.exitCode=1;}}
module.exports={commandSpec,fingerprint,needsInstall};
