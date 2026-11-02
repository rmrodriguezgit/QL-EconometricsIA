import {test} from 'node:test';
import assert from 'node:assert/strict';
import {chooseRegression,regressionData,fittedEquation} from '../src/regressions.ts';
import type {Project,ProjectNode,NodeResult} from '../src/model.ts';
const node=(id:string,type:string)=>({id,type,node_version:'1.0.0',parameters:{},position:{x:0,y:0}} as ProjectNode);
const simple=node('simple','ols'),multiple=node('multiple','multiple_ols');
const project={nodes:[simple,multiple,node('hist','histogram')]} as Project;
test('selección múltiple y selección recordada coinciden con la ecuación',()=>{
 assert.equal(chooseRegression(project,'multiple')?.id,'multiple');
 assert.equal(chooseRegression(project,'hist','multiple')?.id,'multiple');
 assert.equal(chooseRegression(project,'hist','deleted')?.id,'simple');
 assert.equal(chooseRegression({nodes:[]} as unknown as Project,'none'),undefined);
});
test('normaliza simple sin modificar su salida y rechaza resultados pendientes',()=>{
 const result={y:'consumo',x:'ingreso',coefficients:[{term:'const',estimate:2},{term:'ingreso',estimate:.8}]};
 const data=regressionData(simple,{status:'succeeded',result} as NodeResult)!;
 assert.deepEqual(data.features,['ingreso']);assert.equal('features' in result,false);
 assert.equal(regressionData(simple,{status:'failed',result} as NodeResult),undefined);
 assert.equal(fittedEquation(data)?.terms[0].value,.8);
});
test('ecuación múltiple incluye todos los términos y rechaza estimaciones incompletas',()=>{
 const regression={y:'wage',features:['educ','exper','tenure'],coefficients:[{term:'const',estimate:-2.87},{term:'educ',estimate:.59},{term:'exper',estimate:.02},{term:'tenure',estimate:-.16}]};
 const data=regressionData(multiple,{status:'succeeded',result:{regression}} as NodeResult)!;
 assert.deepEqual(fittedEquation(data),{intercept:-2.87,terms:[{name:'educ',value:.59},{name:'exper',value:.02},{name:'tenure',value:-.16}]});
 assert.equal(fittedEquation({...data,coefficients:data.coefficients.slice(0,3)}),undefined);
 assert.equal(fittedEquation({...data,coefficients:[{term:'const',estimate:NaN}]}),undefined);
});
