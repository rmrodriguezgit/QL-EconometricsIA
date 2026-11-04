const {test}=require('node:test');
const assert=require('node:assert/strict');
const {resolve}=require('node:path');
const {createEngine,releaseInfo}=require('./runtime.cjs');
const root=resolve(__dirname,'../../..');
test('IPC permite solo métodos conocidos y solicitudes acotadas',async()=>{
 const engine=createEngine(root);
 await assert.rejects(engine.request({jsonrpc:'2.0',id:1,method:'shell.execute'}));
 await assert.rejects(engine.request({jsonrpc:'2.0',id:1,method:'engine.health',params:{value:'x'.repeat(4_000_001)}}));
 assert.equal(engine.active(),0);
});
test('el motor real devuelve JSON y libera el proceso al responder',async()=>{
 const engine=createEngine(root);
 try{const response=await engine.request({jsonrpc:'2.0',id:1,method:'engine.health',params:{}});assert.equal(response.result.version,require('../package.json').version);assert.equal(engine.active(),0);}finally{await engine.stop();}
});
test('cerrar cancela los procesos en ejecución y permite iniciar otro',async()=>{
 const engine=createEngine(root);
 const pending=engine.request({jsonrpc:'2.0',id:1,method:'engine.health',params:{}});
 const rejected=assert.rejects(pending);
 await engine.stop();await rejected;assert.equal(engine.active(),0);
 const response=await engine.request({jsonrpc:'2.0',id:2,method:'engine.health'});assert.ok(response.result);await engine.stop();
});
test('actualizaciones comparan números y no aceptan URLs del servidor',()=>{
 assert.equal(releaseInfo({tag_name:'v0.10.0'},'0.9.0').available,true);
 assert.equal(releaseInfo({tag_name:'v0.4.0'},'0.5.0').available,false);
 assert.equal(releaseInfo({tag_name:'v0.5.0'},'0.5.0').available,false);
 assert.throws(()=>releaseInfo({tag_name:'malicioso'},'0.5.0'));
 assert.equal(releaseInfo({tag_name:'v1.0.0',html_url:'https://evil.example'},'0.5.0').url,'https://github.com/rmrodriguezgit/QL-EconometricsIA/releases');
});
test('el segundo cerebro está permitido y solo brain.plan amplía el tiempo límite',async()=>{
 const {timeoutFor}=require('./runtime.cjs');
 assert.equal(timeoutFor('brain.plan'),180_000);
 assert.equal(timeoutFor('run.start'),60_000);
 const engine=createEngine(root);
 try{const response=await engine.request({jsonrpc:'2.0',id:2,method:'brain.gaps',params:{}});assert.ok(Array.isArray(response.result.items));}finally{await engine.stop();}
});
