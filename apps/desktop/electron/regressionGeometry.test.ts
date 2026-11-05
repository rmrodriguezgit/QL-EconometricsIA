import test from 'node:test';
import assert from 'node:assert/strict';
import {planeGeometry,type Plane3DData} from '../src/regressionGeometry.ts';

test('con tres regresores la distancia vertical al plano es exactamente el residuo',()=>{
 const beta={const:1,x:2,z:-0.5,w:0.3};
 const rows=[[1,2,3],[0.5,-1,2],[-2,0.4,-1],[3,1,0]].map(([x,z,w],i)=>{const fitted=beta.const+beta.x*x+beta.z*z+beta.w*w;const y=fitted+[0.4,-0.2,0.1,-0.7][i];return [x,z,w,y,fitted];});
 const means={x:rows.reduce((s,r)=>s+r[0],0)/4,z:rows.reduce((s,r)=>s+r[1],0)/4,w:rows.reduce((s,r)=>s+r[2],0)/4};
 const data:Plane3DData={features:['x','z','w'],y:'y',n:4,shown:4,coefficients:beta,means,rows};
 for(const [a,b] of [['x','z'],['z','w'],['x','w']]){
  const geometry=planeGeometry(data,a,b);
  for(const p of geometry.points)assert.ok(Math.abs((p.y-geometry.plane(p.xa,p.xb))-p.residual)<1e-12);
 }
 assert.deepEqual(planeGeometry(data,'x','z').others,['w']);
});
test('con dos regresores la respuesta no se ajusta',()=>{
 const data:Plane3DData={features:['x','z'],y:'y',n:1,shown:1,coefficients:{const:0,x:1,z:1},means:{x:0,z:0},rows:[[1,2,4,3]]};
 const geometry=planeGeometry(data,'x','z');
 assert.equal(geometry.points[0].y,4);assert.equal(geometry.points[0].residual,1);assert.equal(geometry.intercept,0);
});
