import test from 'node:test';
import assert from 'node:assert/strict';
import {fredGroups,fredItems,looksLikeFredId,searchFred} from '../src/fredSearch.ts';
import {fredAlias,fredColumns} from '../src/sourceColumns.ts';

test('búsqueda en el catálogo FRED por ID, título sin acentos y tema',()=>{
 assert.equal(searchFred('DGS10')[0].id,'DGS10');
 assert.equal(searchFred('dgs1')[0].id,'DGS1');
 assert.ok(searchFred('peso dolar').some(item=>item.id==='DEXMXUS'));
 assert.ok(searchFred('inflacion mexico').some(item=>item.id==='FPCPITOTLZGMEX'));
 const texas=searchFred('texas','regional');
 assert.ok(texas.length>=3&&texas.every(item=>item.group==='regional'));
 assert.equal(searchFred('','vivienda').length,fredItems.filter(item=>item.group==='vivienda').length);
 assert.deepEqual(searchFred('zzzz no existe'),[]);
 assert.ok(Object.keys(fredGroups).every(group=>fredItems.some(item=>item.group===group)));
});

test('IDs escritos a mano y alias por defecto',()=>{
 assert.ok(looksLikeFredId('ttlcons')&&looksLikeFredId('A191RL1Q225SBEA'));
 assert.ok(!looksLikeFredId('peso dolar')&&!looksLikeFredId('../x'));
 assert.equal(fredAlias('dexmxus'),'tc_peso_dolar');
 assert.equal(fredAlias('XYZ.1'),'xyz_1');
 assert.deepEqual(fredColumns('TXUR\nDGS10: largo'),['periodo','desempleo_texas','largo']);
});
