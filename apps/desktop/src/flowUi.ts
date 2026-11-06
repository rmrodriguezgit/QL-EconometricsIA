// Parámetros solo de presentación (formato de ejes): cambiarlos no invalida resultados. Igual que DISPLAY_KEYS en axisFormat.tsx.
const DISPLAY_KEYS=new Set(['y_axis','x_axis']);
import type {Project,Run} from './model';
type Tool={label:string;inputs:Record<string,string>;outputs:Record<string,string>;detail?:string};
export function nextTools(registry:Record<string,Tool>,sourceKind:string,port:string){
 const type=registry[sourceKind]?.outputs[port];if(!type)return [];
 const priority=type==='Dataset'?['describe','histogram','scatter','ols','multiple_ols','split','log']:type==='FittedModel'?['diagnostics','evaluate','covariance','compare_models']:type==='Transformer'?['apply_scaler']:type==='Network'?['nn_layer','nn_output','nn_train']:['report'];
 return Object.entries(registry).flatMap(([kind,tool])=>{const input=Object.entries(tool.inputs).find(([,value])=>value===type);if(!input||(kind==='report'&&sourceKind==='report'))return [];return [{kind,label:tool.label,input:input[0],type,detail:tool.detail??'',remaining:Object.keys(tool.inputs).filter(key=>key!==input[0])}];}).sort((a,b)=>{const rank=(kind:string)=>priority.includes(kind)?priority.indexOf(kind):999;return rank(a.kind)-rank(b.kind)||a.label.localeCompare(b.label,'es');});
}
export function nodeSignature(project:Project,id:string){
 const ids=new Set<string>(),pending=[id];while(pending.length){const key=pending.pop()!;if(ids.has(key))continue;ids.add(key);project.edges.filter(edge=>edge.target===key).forEach(edge=>pending.push(edge.source));}
 return JSON.stringify({nodes:project.nodes.filter(node=>ids.has(node.id)).map(({id,type,parameters,node_version})=>({id,type,parameters:Object.fromEntries(Object.entries(parameters).filter(([key])=>!DISPLAY_KEYS.has(key))),node_version})).sort((a,b)=>a.id.localeCompare(b.id)),edges:project.edges.filter(edge=>ids.has(edge.target)).map(({source,target,source_port,target_port})=>({source,target,source_port,target_port})).sort((a,b)=>JSON.stringify(a).localeCompare(JSON.stringify(b)))});
}
export function retainResults(previous:Project,next:Project,run:Run|null):Run|null{
 if(!run)return null;
 const nodes=Object.fromEntries(Object.entries(run.nodes).filter(([id])=>next.nodes.some(node=>node.id===id)&&nodeSignature(previous,id)===nodeSignature(next,id)));
 if(!Object.keys(nodes).length)return null;
 const pending=next.nodes.filter(node=>!nodes[node.id]).map(node=>node.id);
 return {...run,status:pending.length?'partial':run.status,nodes,manifest:{...run.manifest,results_retained_for_unchanged_nodes:true,pending_node_ids:pending}};
}
