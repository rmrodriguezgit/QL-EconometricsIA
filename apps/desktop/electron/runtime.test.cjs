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
test('grupo de procesos: reutiliza Python, atiende en paralelo y se recupera si un proceso muere',async()=>{
 const engine=createEngine(root,{workers:3,warm:1});
 try{
  const health={jsonrpc:'2.0',method:'engine.health',params:{}};
  await engine.request({...health,id:1});await engine.request({...health,id:2});
  assert.equal(engine.workers(),1,'dos solicitudes seguidas usan el mismo proceso');
  const [first]=engine.pids();
  const replies=await Promise.all([1,2,3].map(id=>engine.request({...health,id})));
  assert.deepEqual(replies.map(reply=>reply.id),[1,2,3]);
  assert.equal(engine.workers(),3,'tres solicitudes simultáneas abren tres procesos');
  assert.equal(engine.active(),0);
  process.kill(first,'SIGKILL');
  await new Promise(done=>setTimeout(done,300));
  assert.ok(!engine.pids().includes(first));
  const again=await engine.request({...health,id:9});assert.equal(again.id,9);
  engine.reload();await new Promise(done=>setTimeout(done,300));
  assert.ok(engine.pids().every(pid=>pid!==first));
  assert.equal((await engine.request({...health,id:10})).id,10);
 }finally{await engine.stop();}
 assert.equal(engine.workers(),0);
});
test('warm carga las librerías antes del primer cálculo',async()=>{
 const engine=createEngine(root,{workers:2,warm:2});
 try{const results=await engine.warm();assert.equal(results.length,2);assert.ok(results.every(item=>item.status==='fulfilled'&&item.value.result.ready));assert.equal(engine.workers(),2);}finally{await engine.stop();}
});
