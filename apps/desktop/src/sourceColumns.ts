import wooldridge from '../../../packages/contracts/wooldridgeCatalog.json' with {type:'json'};
import type {ProjectNode} from './model';
export function knownSourceColumns(source:ProjectNode|undefined):string[]{
 if(!source)return [];
 if(source.type==='join_series')return ['periodo',String(source.parameters.left_name??'lending_rate'),String(source.parameters.right_name??'final_consumption'),...Array.from({length:Math.max(0,Math.min(6,Number(source.parameters.extra_inputs??0)||0))},(_,k)=>String(source.parameters[`serie_${k+3}_name`]??`serie_${k+3}`))];
 if(source.type==='worldbank')return ['periodo','valor'];
 if(source.type==='worldbank_multi')return ['periodo',...String(source.parameters.indicators??'').split(/[\n;,]+/).map(item=>item.trim()).filter(Boolean).map(item=>{const [code,...alias]=item.split(item.includes(':')?':':'=');return alias.join('').trim()||code.trim().toLowerCase().replace(/[^a-z0-9_]/g,'_');})];
 if(source.type==='simulate')return ['ingreso','consumo'];
 if(source.type==='wooldridge')return wooldridge.items.find(item=>item.id===source.parameters.dataset)?.columns.filter(column=>column.numeric).map(column=>column.name)??[];
 return [];
}
export function sourceName(source:ProjectNode|undefined){return !source?'Sin fuente':source.type==='wooldridge'?`Wooldridge · ${source.parameters.dataset}`:source.type==='worldbank'?'Banco Mundial':source.type==='worldbank_multi'?'Banco Mundial · varios indicadores':source.type==='csv'?'Archivo CSV':'Tabla conectada';}
