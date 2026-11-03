import nodeCatalog from '../../../packages/contracts/nodeCatalog.json';
export type Kind = keyof typeof nodeCatalog;
export type Parameters = Record<string, string | number>;
export type ProjectNode = { id: string; type: Kind; node_version: '1.0.0'; parameters: Parameters; position: { x: number; y: number } };
export type LessonStep = { node_id: string; title: string; instruction: string; expected: string; question: string };
export type Lesson = { module: string; title: string; objective: string; references: string[]; steps: LessonStep[]; missing_tools: string[] };
export type Project = { lesson?: Lesson; schema_version: '1.0.0'; app_version: string; title: string; nodes: ProjectNode[]; edges: { id: string; source: string; target: string; source_port: string; target_port: string }[] };
export type NodeResult = { status: 'succeeded' | 'failed' | 'skipped'; result?: Record<string, unknown>; error?: { code: string; message: string }; message?: string };
export type Run = { run_id: string; status: string; nodes: Record<string, NodeResult>; manifest: { graph_sha256: string; [key: string]: unknown } };
export const version = '0.7.3';
export type ToolDefinition = { label: string; detail: string; category: string; color: string; references: string; explanation: string; defaults: Parameters; inputs: Record<string,string>; outputs: Record<string,string>; choices?: Record<string,string[]>; choice_labels?: Record<string,Record<string,string>> };
export const catalog = Object.fromEntries(Object.entries(nodeCatalog).map(([key,value]) => [key,{...value,references:value.references.join(' · ')}])) as unknown as Record<Kind,ToolDefinition>;

export function starter(): Project {
  return { schema_version: '1.0.0', app_version: version, title: 'Ingreso y consumo', nodes: [
    { id: 'data', type: 'simulate', node_version: '1.0.0', parameters: { ...catalog.simulate.defaults }, position: { x: 30, y: 150 } },
    { id: 'summary', type: 'describe', node_version: '1.0.0', parameters: {}, position: { x: 350, y: 15 } },
    { id: 'model', type: 'ols', node_version: '1.0.0', parameters: { ...catalog.ols.defaults }, position: { x: 350, y: 160 } },
    { id: 'chart', type: 'scatter', node_version: '1.0.0', parameters: { ...catalog.scatter.defaults }, position: { x: 350, y: 305 } },
  ], edges: ['summary', 'model', 'chart'].map(target => ({ id: `data-${target}`, source: 'data', target, source_port: 'data', target_port: 'data' })) };
}
export function parseProject(text: string): Project {
  if (new TextEncoder().encode(text).length > 3_000_000) throw new Error('El proyecto supera 3 MB.');
  let value;
  try { value = JSON.parse(text); } catch (reason) { throw new Error(`JSON inválido: ${reason instanceof Error ? reason.message : String(reason)}`); }
  if (!value || value.schema_version !== '1.0.0' || typeof value.title !== 'string' || value.title.length > 120 || !Array.isArray(value.nodes) || !Array.isArray(value.edges) || value.nodes.length > 100 || value.edges.length > 400) throw new Error('Formato o versión de proyecto no compatible.');
  for (const node of value.nodes) {
    if (!node || typeof node.id !== 'string' || !Object.hasOwn(catalog, node.type) || node.node_version !== '1.0.0' || !node.parameters || Array.isArray(node.parameters) || typeof node.parameters !== 'object' || !Object.values(node.parameters).every(v => typeof v === 'string' || (typeof v === 'number' && Number.isFinite(v))) || !Number.isFinite(node.position?.x) || !Number.isFinite(node.position?.y)) throw new Error('El proyecto contiene un nodo inválido.');
  }
  for (const edge of value.edges) {
    if (!edge || !['id', 'source', 'target', 'source_port', 'target_port'].every(key => typeof edge[key] === 'string')) throw new Error('El proyecto contiene una conexión inválida.');
  }
  if(value.lesson!==undefined){
    const lesson=value.lesson;
    if(!lesson||typeof lesson!=='object'||!['module','title','objective'].every(key=>typeof lesson[key]==='string')||!Array.isArray(lesson.steps)||lesson.steps.length<1||lesson.steps.length>100||!['references','missing_tools'].every(key=>Array.isArray(lesson[key])&&lesson[key].length<=100&&lesson[key].every((text:unknown)=>typeof text==='string')))throw new Error('La guía paso a paso no es válida.');
    const seen=new Set<string>();
    for(const step of lesson.steps){if(!step||!['node_id','title','instruction','expected','question'].every(key=>typeof step[key]==='string')||!value.nodes.some((node:ProjectNode)=>node.id===step.node_id)||seen.has(step.node_id))throw new Error('La guía contiene un paso inválido.');seen.add(step.node_id);}
  }
  return value as Project;
}
export async function rpc<T>(method: string, params = {}): Promise<T> {
  const request = { jsonrpc: '2.0', id: crypto.randomUUID(), method, params };
  let response;
  if (window.quantlabsDesktop) {
    response = await window.quantlabsDesktop.request(request);
  } else if ('__TAURI_INTERNALS__' in window) {
    const { invoke } = await import('@tauri-apps/api/core');
    response = await invoke('engine_request', { request });
  } else {
    const http = await fetch('/api/rpc', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request) });
    if (!http.ok) throw new Error(await http.text());
    response = await http.json();
  }
  if (response.error) throw new Error(response.error.message);
  return response.result as T;
}
export function download(name: string, value: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }));
  const a = document.createElement('a'); a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
