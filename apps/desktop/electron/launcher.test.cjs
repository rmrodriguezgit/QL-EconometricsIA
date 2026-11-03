const {test}=require('node:test');
const assert=require('node:assert/strict');
const {mkdtempSync,mkdirSync,writeFileSync,rmSync}=require('node:fs');
const {join}=require('node:path');
const {tmpdir}=require('node:os');
const {commandSpec,fingerprint,needsInstall}=require('../../../scripts/launch.cjs');
test('Windows ejecuta npm por cmd; rutas y argumentos de otros procesos permanecen separados',()=>{
 assert.deepEqual(commandSpec('npm',['ci'],'win32').args,['/d','/s','/c','npm ci']);
 assert.deepEqual(commandSpec('uv',['sync','--frozen'],'win32'),{command:'uv',args:['sync','--frozen']});
 assert.deepEqual(commandSpec('node',['C:/Mi proyecto/electron/cli.js','.'],'win32').args,['C:/Mi proyecto/electron/cli.js','.']);
 assert.throws(()=>commandSpec('npm',['ci & otro'],'win32'),/no permitido/);
 assert.equal(commandSpec('npm',['ci'],'darwin').command,'npm');
});
test('la caché se invalida si faltan herramientas o cambia un lockfile',()=>{
 const dir=mkdtempSync(join(tmpdir(),'quantlabs launcher '));
 try{
  writeFileSync(join(dir,'package.json'),'{}');writeFileSync(join(dir,'package-lock.json'),'{}');
  const stamp=join(dir,'stamp'),hash=fingerprint(dir);assert.equal(needsInstall(dir,stamp,hash),true);
  mkdirSync(join(dir,'node_modules/electron'),{recursive:true});writeFileSync(join(dir,'node_modules/electron/cli.js'),'');
  mkdirSync(join(dir,'node_modules/.bin'),{recursive:true});writeFileSync(join(dir,'node_modules/.bin',process.platform==='win32'?'tsc.cmd':'tsc'),'');
  writeFileSync(stamp,hash+'\n');assert.equal(needsInstall(dir,stamp,hash),false);
  writeFileSync(join(dir,'package-lock.json'),'{"new":true}');assert.equal(needsInstall(dir,stamp,fingerprint(dir)),true);
  rmSync(join(dir,'node_modules/electron/cli.js'));assert.equal(needsInstall(dir,stamp,hash),true);
 }finally{rmSync(dir,{recursive:true,force:true});}
});
