import test from 'node:test';
import assert from 'node:assert/strict';
import {axisModes,axisScale,scientificValue,superscript} from '../src/axisFormat.ts';
import {retainResults} from '../src/flowUi.ts';

test('notación científica ×10ⁿ con mantisas legibles',()=>{
 const scale=axisScale([1.2e12,3.4e12],'cientifica');
 assert.equal(scale.factor,'×10¹²');
 assert.equal(scale.tick(3.4e12),'3.4');
 assert.equal(scale.label('fin_cons'),'fin_cons (×10¹²)');
 assert.equal(axisScale([0.0002,0.0009],'cientifica').factor,'×10⁻⁴');
 assert.equal(superscript(-12),'⁻¹²');
});
test('automático solo usa ×10ⁿ con valores muy grandes o pequeños; normal nunca',()=>{
 assert.equal(axisScale([2,95],'auto').factor,'');
 assert.equal(axisScale([1e5,9e5],'auto').factor,'×10⁵');
 assert.equal(axisScale([0.001,0.004],'auto').factor,'×10⁻³');
 assert.equal(axisScale([1e12,2e12],'normal').factor,'');
 assert.equal(axisScale([3,8],'cientifica').factor,'',"sin factor cuando el exponente es 0");
 assert.equal(scientificValue(2.5e9,'auto'),'2.5×10⁹');
 assert.deepEqual(axisModes({y_axis:'cientifica',x_axis:'otra'}),{x:'auto',y:'cientifica'});
});
test('marcas cercanas no se confunden al escalar',()=>{
 const scale=axisScale([1.00e9,1.05e9],'cientifica');
 assert.notEqual(scale.tick(1.0e9),scale.tick(1.025e9));
});
test('cambiar el formato del eje conserva los resultados calculados',()=>{
 const base={schema_version:'1.0.0',app_version:'0',title:'t',edges:[],nodes:[{id:'a',type:'scatter',node_version:'1.0.0',parameters:{x:'x',y:'y',y_axis:'auto'},position:{x:0,y:0}}]};
 const run={run_id:'r',status:'succeeded',nodes:{a:{status:'succeeded',result:{}}},manifest:{}} as any;
 const display={...base,nodes:[{...base.nodes[0],parameters:{x:'x',y:'y',y_axis:'cientifica'}}]};
 assert.ok(retainResults(base as any,display as any,run)?.nodes.a);
 const changed={...base,nodes:[{...base.nodes[0],parameters:{x:'x',y:'z',y_axis:'auto'}}]};
 assert.equal(retainResults(base as any,changed as any,run),null);
});
