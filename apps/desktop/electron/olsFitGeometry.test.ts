import test from 'node:test';
import assert from 'node:assert/strict';
import {niceTicks,residualHistogram} from '../src/olsFitGeometry.ts';

test('las marcas son redondas y cubren el rango',()=>{
 assert.deepEqual(niceTicks(0,10,5),[0,2,4,6,8,10]);
 assert.deepEqual(niceTicks(-0.37,0.41,4),[-0.4,-0.2,0,0.2,0.4,0.6]);
 const big=niceTicks(1.2e12,9.7e12,5);assert.ok(big[0]<=1.2e12&&big[big.length-1]>=9.7e12-1);
 assert.deepEqual(niceTicks(3,3),[3]);
});

test('el histograma cuenta todos los residuos y ordena de +limit a −limit',()=>{
 const {counts,width}=residualHistogram([1.9,1.1,-0.1,-1.9,2,-2,Number.NaN],2,4);
 assert.equal(width,1);
 assert.deepEqual(counts,[3,0,1,2]);
});
