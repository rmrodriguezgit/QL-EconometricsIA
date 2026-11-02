import wooldridge from '../../../packages/contracts/wooldridgeCatalog.json' with {type:'json'};
import type {ProjectNode} from './model';
export function knownSourceColumns(source:ProjectNode|undefined):string[]{
 if(!source)return [];
 if(source.type==='worldbank')return ['periodo','valor'];
 if(source.type==='simulate')return ['ingreso','consumo'];
 if(source.type==='wooldridge')return wooldridge.items.find(item=>item.id===source.parameters.dataset)?.columns.filter(column=>column.numeric).map(column=>column.name)??[];
 return [];
}
export function sourceName(source:ProjectNode|undefined){return !source?'Sin fuente':source.type==='wooldridge'?`Wooldridge · ${source.parameters.dataset}`:source.type==='worldbank'?'Banco Mundial':source.type==='csv'?'Archivo CSV':'Tabla conectada';}
