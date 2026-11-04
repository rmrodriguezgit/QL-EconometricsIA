import type {Project,Run} from './model';
export type ColumnSchema={columns:string[];numeric_columns:string[];n:number;preview:Record<string,unknown>[]};
export function scatterInput(project:Project,nodeId:string){
 const links=project.edges.filter(edge=>edge.target===nodeId);
 const edge=links.find(edge=>edge.target_port==='data')??links.find(edge=>edge.target_port==='population');
 if(!edge)return null;
 const ids=new Set<string>();const pending=[edge.source];
 while(pending.length){const id=pending.pop()!;if(ids.has(id))continue;ids.add(id);project.edges.filter(link=>link.target===id).forEach(link=>pending.push(link.source));}
 const key=JSON.stringify({port:edge.source_port,source:edge.source,nodes:project.nodes.filter(node=>ids.has(node.id)).map(({id,type,parameters})=>({id,type,parameters})).sort((a,b)=>a.id.localeCompare(b.id)),edges:project.edges.filter(link=>ids.has(link.target)).map(({source,target,source_port,target_port})=>({source,target,source_port,target_port})).sort((a,b)=>JSON.stringify(a).localeCompare(JSON.stringify(b)))});
 return {edge,key,source:project.nodes.find(node=>node.id===edge.source)!};
}
export function inputSchema(run:Run,source:string,port:string):ColumnSchema|null{
 const node=run.nodes[source];if(node?.status!=='succeeded')return null;
 const preview=(node.result?.output_previews as Record<string,ColumnSchema>|undefined)?.[port];
 return preview&&Array.isArray(preview.numeric_columns)?preview:null;
}
export function initialScatterAxes(type:string,parameters:Record<string,string|number>){
 return type==='worldbank'&&parameters.x==='ingreso'&&parameters.y==='consumo'?{...parameters,x:'periodo',y:'valor'}:parameters;
}

export const singleColumnKeys=new Set(['x','y','column','value','nominal','index','population','returns','signal','before','after','error','entity']);
export const multipleColumnKeys=new Set(['columns','features','instruments']);
export const isColumnParameter=(key:string)=>singleColumnKeys.has(key)||multipleColumnKeys.has(key);

export function toggleColumns(value:string,column:string,checked:boolean,available:string[]){
 const selected=value.split(',').map(name=>name.trim()).filter(name=>available.includes(name));
 return [...new Set(checked?[...selected,column]:selected.filter(name=>name!==column))].filter(name=>available.includes(name)).join(',');
}
