import test from 'node:test';
import assert from 'node:assert/strict';
import nodeCatalog from '../../../packages/contracts/nodeCatalog.json' with {type:'json'};
import {areaCount,areaGroups,areaOf,areas,isListed,searchTools} from '../src/libraryAreas.ts';
import {migrateNode,migrateParameters,migrations} from '../src/toolMigrations.ts';

const catalog=nodeCatalog as unknown as Record<string,{label:string;detail:string;explanation?:string;superseded_by?:string|null;legacy?:boolean;defaults:Record<string,string|number>;inputs:Record<string,string>;outputs:Record<string,string>}>;

test('cada herramienta ofrecida aparece en una sola área y las reemplazadas no aparecen',()=>{
 const listed=areas.flatMap(area=>areaGroups(area.id,catalog).flatMap(group=>group.tools));
 assert.equal(new Set(listed).size,listed.length);
 assert.deepEqual([...listed].sort(),Object.keys(catalog).filter(kind=>isListed(catalog[kind])).sort());
 for(const kind of ['paired_test','worldbank','mlp','time_plot','experiment'])assert.ok(!listed.includes(kind),kind);
 assert.equal(areas.reduce((total,area)=>total+areaCount(area.id,catalog),0),listed.length);
 assert.equal(areaOf('portfolio')?.id,'finanzas');
 assert.equal(areaOf('nn_layer')?.id,'deep');
});

test('búsqueda sin acentos, en todas las áreas y con el nombre primero',()=>{
 assert.equal(searchTools('regresion',catalog)[0],'ols');
 assert.ok(searchTools('markowitz',catalog).includes('portfolio'));
 assert.ok(searchTools('capa',catalog).includes('nn_input'));
 assert.ok(searchTools('volatilidad',catalog).includes('garch'));
 assert.ok(!searchTools('pareada',catalog).includes('paired_test'));
 assert.deepEqual(searchTools('',catalog),[]);
});

test('migración: parámetros y conexiones',()=>{
 assert.deepEqual(migrateParameters('paired_test',{before:'antes',after:'despues'}),{first:'antes',second:'despues',method:'paired'});
 assert.deepEqual(migrateParameters('worldbank',{country:'MEX',indicator:'NY.GDP.PCAP.KD',start:2000,end:2020}),{countries:'MEX',start:2000,end:2020,indicators:'NY.GDP.PCAP.KD: valor'});
 assert.equal(migrateParameters('mlp',{}),null);
 for(const [kind,rule] of Object.entries(migrations))assert.equal(catalog[kind].superseded_by,rule.to,kind);
 const project={nodes:[{id:'d',type:'synthetic',parameters:{}},{id:'t',type:'time_plot',parameters:{time:'periodo',value:'y'}}],edges:[{id:'e',source:'d',target:'t',source_port:'data',target_port:'data'}]};
 const out=migrateNode(project,'t',catalog);
 assert.ok(out);
 assert.equal(out.project.nodes[1].type,'series_plot');
 assert.equal(out.project.nodes[1].parameters.columns,'y');
 assert.equal(out.dropped,0);
});
