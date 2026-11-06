import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ReactFlow, Background, Controls, Handle, Position, addEdge, applyNodeChanges, applyEdgeChanges, useUpdateNodeInternals, type Node, type NodeProps, type Connection, type ReactFlowInstance } from '@xyflow/react';
import { ArrowDownToLine, ArrowUpFromLine, FolderOpen, Play, Plus, Search, FlaskConical, Database, ChartScatter, ChartNoAxesCombined, Sigma, BookOpen, ChevronRight, CircleCheck, RotateCcw, Undo2, Brain, Trash2, Unplug, Network, CircleAlert, Braces, LoaderCircle, Eye, EyeOff, X, Maximize2, Minimize2, Minus, Scan, Wrench } from 'lucide-react';
import OutputDashboard from './OutputDashboard';
import {nextTools,retainResults} from './flowUi';
import DataVariables from './DataVariables';
import BoxplotCondition from './BoxplotCondition';
import JoinSeriesVariables from './JoinSeriesVariables';
import TimePlotVariables from './TimePlotVariables';
import ScatterVariables from './ScatterVariables';
import {scatterInput,inputSchema,initialScatterAxes,isColumnParameter,type ColumnSchema} from './scatterInput';
import DesktopControls from './DesktopControls';
import RegressionPanel from './RegressionPanel';
import {chooseRegression,regressionData,isRegression} from './regressions';
import ModelEquation from './ModelEquation';
import WooldridgePicker from './WooldridgePicker';
import CountryPicker from './CountryPicker';
import IndicatorPicker from './IndicatorPicker';
import IndicatorListEditor from './IndicatorListEditor';
import FredSeriesEditor from './FredSeriesEditor';
import ErrorBoundary from './ErrorBoundary';
import exampleCatalog from '../../../examples/catalog.json';
import ProjectManager, { type SavedProject } from './ProjectManager';
import ExperimentReport from './ExperimentReport';
import LessonGuide from './LessonGuide';
import BrainPanel from './BrainPanel';
import RepairPanel from './RepairPanel';
import Scatter from './ScatterPlot';
import { catalog, download, extraInputCount, nodeInputs, parseProject, rpc, starter, version, type Kind, type Project, type Run, type NodeResult, type ToolDefinition } from './model';

const stageLabels: Record<string,string> = { 'Transformaciones': 'TRANSFORMACIÓN', 'Exploración': 'EXPLORACIÓN', 'Modelos': 'ESTIMACIÓN', 'Diagnósticos': 'DIAGNÓSTICO', 'Salidas': 'SALIDA', 'Experimentos': 'EXPERIMENTO' };
const icons = Object.fromEntries(Object.entries(catalog).map(([kind,item])=>[kind,item.category==='Fuentes de datos'?Database:item.category==='Modelos'?ChartNoAxesCombined:item.category==='Exploración'?ChartScatter:item.category==='Experimentos'?BookOpen:Sigma])) as Record<Kind,typeof BookOpen>;
const format = (v: unknown, digits = 3) => typeof v === 'number' ? new Intl.NumberFormat('es-MX', { maximumFractionDigits: digits }).format(v) : '—';
type CanvasNode = Node<{ kind: Kind; state?: NodeResult; index: number;visible:boolean;onVisibility:(id:string)=>void;onSuggest:(id:string,port:string,x:number,y:number)=>void;inputs:Record<string,string>;extra:number;onInputs:(id:string,delta:number)=>void }, 'econometric'>;

function EconometricNode({ id, data, selected }: NodeProps<CanvasNode>) {
  const item = catalog[data.kind]; const Icon = icons[data.kind]; const state = data.state;
  const definition=catalog[data.kind];
  const inputPorts=Object.entries(data.inputs);const variadic=definition.variadic;const outputPorts=Object.entries(definition.outputs);
  const isSource = !inputPorts.length;
  const updateInternals=useUpdateNodeInternals();
  useEffect(()=>{updateInternals(id);},[id,inputPorts.length,updateInternals]);
  const result = state?.result;
  return <div className={`flow-node ${selected ? 'selected' : ''} ${item.color}`}>
    {inputPorts.map(([port,type],i)=><Handle key={port} type="target" position={Position.Left} id={port} style={{top:`${100*(i+1)/(inputPorts.length+1)}%`}} aria-label={`Entrada ${port}: ${type}`} title={`${port}: ${type}`}/>)}
    <div className="node-top"><span className={`node-icon ${item.color}`}><Icon size={17} /></span><span className="node-type">{isSource ? 'DATOS' : (stageLabels[item.category] ?? item.category.toUpperCase())}</span><span className="node-number">0{data.index + 1}</span><button className={`node-eye nodrag nopan ${data.visible?'active':''}`} aria-label={`${data.visible?'Ocultar':'Mostrar'} salida de ${item.label}`} title={data.visible?'Salida visible en Resultados':'Salida oculta en Resultados'} aria-pressed={data.visible} onClick={event=>{event.stopPropagation();data.onVisibility(id);}}>{data.visible?<Eye size={15}/>:<EyeOff size={15}/>}</button></div>
    <strong>{item.label}</strong><p>{item.detail}</p>{variadic&&<div className="port-adder nodrag nopan"><button type="button" aria-label={`Añadir entrada: ${variadic.label.toLowerCase()} ${variadic.start+data.extra}`} title={`Añadir otra entrada (${variadic.type})`} disabled={data.extra>=variadic.max_extra} onClick={event=>{event.stopPropagation();data.onInputs(id,1);}}><Plus size={12}/></button>{data.extra>0&&<button type="button" aria-label={`Quitar la última entrada (${variadic.prefix}${variadic.start+data.extra-1})`} title="Quitar la última entrada añadida y su conexión" onClick={event=>{event.stopPropagation();data.onInputs(id,-1);}}><Minus size={12}/></button>}<span>{inputPorts.filter(([,type])=>type===variadic.type).length} entradas {variadic.type}</span></div>}
    <div className="port-names"><span>↓ {inputPorts.map(([port])=>port).join(', ')||'origen'}</span><span>↑ {outputPorts.map(([port])=>port).join(', ')||'sin salidas'}</span></div>
    <div className={`node-bottom ${state?.status ?? ''}`}>
      {state?.status === 'succeeded' ? <><CircleCheck size={12} />{data.kind === 'ols' ? `R² ${format(result?.r_squared)}` : data.kind === 'experiment' ? `${String(result?.topic)} · completado` : `${format(result?.n ?? result?.n_total)} observaciones`}</> : state?.status === 'failed' ? <><CircleAlert size={12} />Revisar parámetros</> : state?.status === 'skipped' ? 'Origen sin resultados' : <><span className="tiny-dot" /> Listo para conectar</>}
    </div>
    {outputPorts.map(([port,type],i)=><Handle key={port} type="source" position={Position.Right} id={port} style={{top:`${100*(i+1)/(outputPorts.length+1)}%`}} aria-label={`Salida ${port}: ${type}`} title={`${port}: ${type} · Doble clic para ver qué conectar después`} tabIndex={0} onClick={event=>event.stopPropagation()} onDoubleClick={event=>{event.stopPropagation();const rect=event.currentTarget.getBoundingClientRect();data.onSuggest(id,port,rect.right,rect.top);}} onKeyDown={event=>{if(event.key==='Enter'){event.preventDefault();event.stopPropagation();const rect=event.currentTarget.getBoundingClientRect();data.onSuggest(id,port,rect.right,rect.top);}}}/>)}
  </div>;
}
const nodeTypes = { econometric: EconometricNode };

export default function App() {
  const [project, setProject] = useState<Project>(()=>{try {const saved=sessionStorage.getItem('quantlabs-draft');return saved?parseProject(saved):starter();}catch{return starter();}});
  useEffect(()=>{try{sessionStorage.setItem('quantlabs-draft',JSON.stringify(project));}catch{/* El canvas continúa disponible si se agota el almacenamiento. */}},[project]);
  const [outputVisibility,setOutputVisibility]=useState<Record<string,boolean>>({});
  const [suggestion,setSuggestion]=useState<{id:string;port:string;x:number;y:number}|null>(null);
  const isOutputVisible=(id:string)=>outputVisibility[id]??project.nodes.some(node=>node.id===id&&['ols','scatter','histogram','boxplot','correlation','covariance_matrix','time_plot','normality','residual_normality','impute_mean'].includes(node.type));
  const setOutputVisible=(id:string,visible:boolean)=>{setOutputVisibility(previous=>({...previous,[id]:visible}));setTab('Resultados');};
  const suggest=(id:string,port:string,x:number,y:number)=>setSuggestion({id,port,x,y});
  const [history, setHistory] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState('model');
  const [selectedEdgeId, setSelectedEdgeId] = useState('');
  const [run, setRun] = useState<Run | null>(null);
  const [schemas,setSchemas]=useState<Record<string,ColumnSchema>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [query, setQuery] = useState('');
  // Apartados de la biblioteca: todas, univariadas (una variable) o multivariadas (varias variables).
  const [libraryScope, setLibraryScope] = useState<'todas'|'univariada'|'multivariada'>('todas');
  const [tab, setTab] = useState('Resultados');
  const [activeRegressionId,setActiveRegressionId]=useState('');
  const [equationOpen, setEquationOpen] = useState(false);
  const [managerOpen, setManagerOpen] = useState(false);
  const [brainOpen, setBrainOpen] = useState(false);
  const [repairOpen, setRepairOpen] = useState(false);
  // Espacio de trabajo a pantalla completa para revisar el grafo; Esc vuelve al layout normal.
  const [focusMode, setFocusMode] = useState(false);
  // Área de resultados ampliada a toda la ventana para leer tablas y gráficos.
  const [resultsFocus, setResultsFocus] = useState(false);
  useEffect(() => {
    if (!focusMode && !resultsFocus) return;
    const onKey = (event: KeyboardEvent) => {
      // Esc cierra primero cualquier diálogo abierto; solo después sale del modo ampliado.
      if (event.key !== 'Escape' || document.querySelector('dialog[open]')) return;
      setFocusMode(false);
      setResultsFocus(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [focusMode, resultsFocus]);
  const [activeFile, setActiveFile] = useState<SavedProject | null>(null);
  const [stepIndex,setStepIndex]=useState(0);
  const [flow,setFlow]=useState<ReactFlowInstance<CanvasNode>|null>(null);
  const chooseStep=(index:number)=>{const step=project.lesson?.steps[index];if(!step)return;setStepIndex(index);setOutputVisible(step.node_id,true);setSelectedId(step.node_id);setSelectedEdgeId('');void flow?.fitView({nodes:[{id:step.node_id}],padding:.5,minZoom:.65,maxZoom:1,duration:250});};
  useEffect(()=>{if(project.lesson){setStepIndex(0);const id=project.lesson.steps[0]?.node_id??'';setSelectedId(id);const timer=requestAnimationFrame(()=>void flow?.fitView({nodes:[{id}],padding:.5,minZoom:.65,maxZoom:1,duration:250}));return()=>cancelAnimationFrame(timer);}},[project.lesson?.module,flow]);
  const dirty = JSON.stringify(project) !== JSON.stringify(activeFile?.project ?? starter());
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ''; };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [dirty]);
  const fileRef = useRef<HTMLInputElement>(null);
  const selected = project.nodes.find(n => n.id === selectedId);
  const item = selected && catalog[selected.type];
  const selectedEdge = project.edges.find(edge => edge.id === selectedEdgeId);
  const connections = selected ? project.edges.filter(edge => edge.source === selected.id || edge.target === selected.id) : [];
  const nodeLabel = (id: string) => { const node = project.nodes.find(node => node.id === id); return node ? catalog[node.type].label : id; };
  const disconnect = (id: string) => { update({ ...project, edges: project.edges.filter(edge => edge.id !== id) }); setSelectedEdgeId(''); };
  const equationNode=chooseRegression(project,selectedId,activeRegressionId);
  useEffect(()=>{if(selected&&isRegression(selected))setActiveRegressionId(selected.id);},[selectedId,selected?.type]);
  const update = useCallback((next: Project, remember = true) => {
    if (busy) return;
    if(next.lesson){const ids=new Set(next.nodes.map(node=>node.id));const steps=next.lesson.steps.filter(step=>ids.has(step.node_id));next={...next,lesson:steps.length?{...next.lesson,steps}:undefined};setStepIndex(index=>Math.max(0,Math.min(index,steps.length-1)));}
    if (remember) setHistory(h => [...h.slice(-29), project]);
    const kept=retainResults(project,next,run);setProject(next);setRun(kept);setSuggestion(null);setError('');setNotice(kept?.status==='partial'?'Flujo editado. Se conservan resultados de nodos sin cambios; ejecuta para calcular los pendientes.':'');
  }, [project, busy, run]);
  // Botón «+»/«−» de la tarjeta: añade o quita la última entrada variable (serie_3, modelo_3…).
  const changeInputs = (id: string, delta: number) => {
    const node = project.nodes.find(item => item.id === id), variadic = node && catalog[node.type].variadic;
    if (!node || !variadic) return;
    const count = extraInputCount(node), next = Math.max(0, Math.min(variadic.max_extra, count + delta));
    if (next === count) return;
    const port = `${variadic.prefix}${variadic.start + (delta > 0 ? count : count - 1)}`;
    const parameters: Record<string, string | number> = { ...node.parameters, extra_inputs: next };
    if (delta > 0 && node.type === 'join_series') Object.assign(parameters, { [`${port}_key`]: 'periodo', [`${port}_value`]: 'valor', [`${port}_name`]: port });
    if (delta < 0) for (const key of Object.keys(parameters)) if (key.startsWith(`${port}_`)) delete parameters[key];
    update({ ...project, nodes: project.nodes.map(item => item.id === id ? { ...item, parameters } : item), edges: delta < 0 ? project.edges.filter(edge => !(edge.target === id && edge.target_port === port)) : project.edges });
    setNotice(delta > 0 ? `Entrada ${port} añadida: conéctale ${variadic.type === 'Dataset' ? 'una tabla' : 'un modelo ajustado'}.` : `Entrada ${port} retirada junto con su conexión.`);
  };
  const nodes: CanvasNode[] = useMemo(() => project.nodes.map((node, index) => ({ id: node.id, type: 'econometric', position: node.position, selected: selectedId === node.id, data: { kind: node.type, state: run?.nodes[node.id], index,visible:isOutputVisible(node.id),onVisibility:(id:string)=>setOutputVisible(id,!isOutputVisible(id)),onSuggest:suggest,inputs:nodeInputs(node),extra:extraInputCount(node),onInputs:changeInputs } })), [project, selectedId, run,outputVisibility]);
  const edges = useMemo(() => project.edges.map(edge => ({ ...edge, sourceHandle: edge.source_port, targetHandle: edge.target_port, type: 'smoothstep', animated: busy, selected: edge.id === selectedEdgeId, style: { stroke: edge.id === selectedEdgeId ? '#b77748' : '#73a795', strokeWidth: edge.id === selectedEdgeId ? 2.8 : 1.6 } })), [project.edges, busy, selectedEdgeId]);
  const addNode = (kind: Kind) => {
    const id = crypto.randomUUID();
    const next:Project={ ...project, nodes: [...project.nodes, { id, type: kind, node_version: '1.0.0', parameters: { ...catalog[kind].defaults }, position: { x: project.nodes.length?Math.max(...project.nodes.map(node=>node.position.x))+320:30, y: project.nodes.at(-1)?.position.y??120 } }] };update(next);if(kind==='wooldridge'){setOutputVisible(id,true);void execute(next,id);}setSelectedId(id);setSelectedEdgeId('');requestAnimationFrame(()=>void flow?.fitView({nodes:[...(project.nodes.length?[{id:project.nodes.at(-1)!.id}]:[]),{id}],padding:.2,minZoom:.3,maxZoom:1,duration:250}));
  };
  const validConnection = (connection: {source: string;target: string;sourceHandle?: string|null;targetHandle?: string|null}) => {
    const source=project.nodes.find(node=>node.id===connection.source),target=project.nodes.find(node=>node.id===connection.target);
    if(!source||!target||source.id===target.id||!connection.sourceHandle||!connection.targetHandle)return false;
    if(catalog[source.type].outputs[connection.sourceHandle]!==nodeInputs(target)[connection.targetHandle]||!catalog[source.type].outputs[connection.sourceHandle])return false;
    if(project.edges.some(edge=>edge.target===target.id&&edge.target_port===connection.targetHandle))return false;
    const visited=new Set<string>();const stack=[target.id];
    while(stack.length){const id=stack.pop()!;if(id===source.id)return false;if(visited.has(id))continue;visited.add(id);project.edges.filter(edge=>edge.source===id).forEach(edge=>stack.push(edge.target));}
    return true;
  };
  const connect = (connection: Connection) => {
    if(!validConnection(connection)){setError('Conecta puertos del mismo tipo, sin ciclos ni entradas duplicadas.');return;}
    const next=addEdge(connection,edges);
    const source=project.nodes.find(node=>node.id===connection.source);
    update({...project,nodes:project.nodes.map(node=>node.id===connection.target&&['scatter','ols'].includes(node.type)?{...node,parameters:initialScatterAxes(source?.type??'',node.parameters)}:node),edges:next.map(edge=>({id:edge.id,source:edge.source,target:edge.target,source_port:edge.sourceHandle!,target_port:edge.targetHandle!}))});
  };

  const addRecommended = (kind:Kind,input:string) => {
    if(!suggestion||busy)return;
    const source=project.nodes.find(node=>node.id===suggestion.id);if(!source)return;
    const id=crypto.randomUUID();const parameters=['scatter','ols'].includes(kind)?initialScatterAxes(source.type,{...catalog[kind].defaults}):{...catalog[kind].defaults};
    update({...project,nodes:[...project.nodes,{id,type:kind,node_version:'1.0.0',parameters,position:{x:source.position.x+320,y:source.position.y+project.edges.filter(edge=>edge.source===source.id).length*150}}],edges:[...project.edges,{id:crypto.randomUUID(),source:source.id,source_port:suggestion.port,target:id,target_port:input}]});setSelectedId(id);setSelectedEdgeId('');setOutputVisible(id,true);setSuggestion(null);requestAnimationFrame(()=>void flow?.fitView({nodes:[{id:source.id},{id}],padding:.3,maxZoom:1,duration:250}));
  };
  const setParameter = (key: string, value: string | number) => {
    if (!selected) return;
    update({ ...project, nodes: project.nodes.map(n => n.id === selected.id ? { ...n, parameters: { ...n.parameters, [key]: value } } : n) });
  };
  const execute = async (target: Project = project, targetNode?:string) => {
    setBusy(true); setError(''); setNotice(''); if(!targetNode)setRun(null);
    try {
      const value = await rpc<Run>('run.start', { project: target, ...(targetNode?{target_node:targetNode}:{}) });
      setSchemas(previous=>{
        const next={...previous};for(const node of target.nodes){const input=scatterInput(target,node.id);if(!input)continue;const schema=inputSchema(value,input.edge.source,input.edge.source_port);if(schema)next[input.key]=schema;}
        // Only keep schemas matching this project's current inputs.
        const keys=new Set(target.nodes.map(node=>scatterInput(target,node.id)?.key));return Object.fromEntries(Object.entries(next).filter(([key])=>keys.has(key)));
      });
      setRun(previous=>{
        if(!targetNode||!previous||(previous.manifest.graph_sha256!==value.manifest.graph_sha256&&!previous.manifest.results_retained_for_unchanged_nodes))return value;
        const before=previous.manifest.sources as Record<string,{data_sha256:string}>;const after=value.manifest.sources as Record<string,{data_sha256:string}>;
        if(Object.entries(after).some(([id,source])=>previous.nodes[id]&&before[id]&&before[id].data_sha256!==source.data_sha256))return value;
        return {...value,nodes:{...previous.nodes,...value.nodes},manifest:{...value.manifest,sources:{...before,...after},guided_runs:[...((previous.manifest.guided_runs as string[]|undefined)??[previous.run_id]),value.run_id]}};
      });
      if(!targetNode&&target.lesson&&value.status!=='failed'){const last=target.lesson.steps.length-1;setStepIndex(last);setSelectedId(target.lesson.steps[last].node_id);}
      if (value.status === 'failed') setError('Hay nodos que necesitan revisión. Selecciónalos para consultar el error.');
      else setNotice(targetNode?'Paso calculado con sus dependencias. Revisa la salida y continúa.':'Flujo ejecutado. Resultados calculados con Python.');
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo ejecutar el flujo.'); }
    finally { setBusy(false); }
  };
  const openProject = async (file?: File) => {
    if (!file) return;
    try {
      if (file.size > 3_000_000) throw new Error('El proyecto supera 3 MB.');
      const value = parseProject(await file.text());
      await rpc('project.validate', { project: value, draft: true });
      update(value); setActiveFile(null); setSelectedId(value.nodes[0]?.id ?? ''); setNotice('Proyecto abierto. Ejecuta para recalcular los resultados.');
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo abrir el proyecto.'); }
  };
  const saveCurrent = async () => {
    setBusy(true); setError('');
    try {
      const next = { ...parseProject(JSON.stringify(project)), app_version: version };
      const saved = await rpc<SavedProject>('projects.save', { project: next, ...(activeFile ? { id: activeFile.id, expected_revision: activeFile.revision } : {}) });
      setProject(saved.project); setActiveFile(saved); setNotice(`Guardado en Mis proyectos: ${saved.title}.`);
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'No se pudo guardar el proyecto.'); }
    finally { setBusy(false); }
  };
  const newProject = () => {
    if (busy || (dirty && !window.confirm('Hay cambios sin guardar. ¿Crear un proyecto nuevo? Puedes cancelar y guardar primero.'))) return;
    update({schema_version:'1.0.0',app_version:version,title:'Nuevo proyecto',nodes:[],edges:[]});
    setActiveFile(null);setSelectedId('');setSelectedEdgeId('');setStepIndex(0);setTab('Resultados');
    setNotice('Proyecto nuevo. Ponle un nombre y añade una fuente de datos desde la biblioteca.');
  };
  const resultOf = (kind: Kind) => {
    const node = project.nodes.find(n => n.type === kind && run?.nodes[n.id]?.status === 'succeeded');
    return node && run?.nodes[node.id]?.result;
  };
  const model = resultOf('ols'), scatter = resultOf('scatter'), summary = resultOf('describe'), experiment = resultOf('experiment');
  const selectedResult = selected && run?.nodes[selected.id];
  const activeRegression=regressionData(equationNode,equationNode?run?.nodes[equationNode.id]:undefined);
  const coefficients = model?.coefficients as { term: string; estimate: number; std_error: number; p_value: number }[] | undefined;
  const suggestionSource=project.nodes.find(node=>node.id===suggestion?.id);
  const recommendations=suggestion&&suggestionSource?nextTools(catalog,suggestionSource.type,suggestion.port):[];
  const inScope = (value: ToolDefinition) => libraryScope === 'todas' || value.category === 'Fuentes de datos' || value.scope === libraryScope || value.scope === 'ambas';
  const visible = Object.entries(catalog).filter(([, value]) => inScope(value) && `${value.label} ${value.detail}`.toLocaleLowerCase().includes(query.toLocaleLowerCase()));
  const refit=()=>requestAnimationFrame(()=>requestAnimationFrame(()=>void flow?.fitView({padding:.12,minZoom:.1,maxZoom:1.2,duration:250})));
  const toggleFocus=(value=!focusMode)=>{setFocusMode(value);if(value)setResultsFocus(false);setSuggestion(null);refit();};
  return <div className={`app-shell${focusMode?' workspace-focus':''}${resultsFocus?' results-focus':''}`}>
    {suggestion&&suggestionSource&&<aside className="port-suggestions" aria-label="Qué conectar después" style={{left:Math.max(8,Math.min(suggestion.x+14,window.innerWidth-365)),top:Math.max(8,Math.min(suggestion.y,window.innerHeight-430))}}><header><div><strong>Después de {catalog[suggestionSource.type].label}</strong><small>{suggestion.port} · {catalog[suggestionSource.type].outputs[suggestion.port]}</small></div><button aria-label="Cerrar recomendaciones" onClick={()=>setSuggestion(null)}><X size={15}/></button></header><p>Elige para añadir y conectar una herramienta compatible.</p><div className="recommendation-list">{recommendations.map(option=><button disabled={busy} key={option.kind} onClick={()=>addRecommended(option.kind as Kind,option.input)}><strong>{option.label}<Plus size={13}/></strong><span>{option.detail}</span><small>Conecta a {option.input}{option.remaining.length?` · Completa también: ${option.remaining.join(', ')}`:' · Entrada lista'}</small></button>)}{!recommendations.length&&<p>Esta salida no tiene otra herramienta compatible. Usa el ojo del nodo para ver el resultado y Exportar para guardarlo.</p>}</div></aside>}
    <header className="app-header">
      <div className="brand"><span className="brand-mark"><Network size={21} /></span><span>Quantlabs<span className="brand-light"> / Econometrics</span></span><span className="alpha-tag">STUDIO</span></div>
      <div className="header-actions"><DesktopControls/><span className="local-badge"><span className="tiny-dot" />{window.quantlabsDesktop?'Electron · local':'Navegador · local'}</span><span className="header-version">v{version}</span></div>
    </header>
    <div className="studio-context"><span><BookOpen size={14}/> LABORATORIO DE ECONOMETRÍA <span className="studio-separator">/</span> {project.lesson?.module??'INICIO'}</span><button onClick={()=>setManagerOpen(true)}><FolderOpen size={14}/>{exampleCatalog.examples.length} ejemplos · aprender paso a paso<ChevronRight size={13}/></button></div>
    <main className="workbench">
      <aside className="library"><div className="section-heading"><h2>Biblioteca de nodos</h2><span>{Object.keys(catalog).length}</span></div><p className="subtle">Añade una pieza a tu análisis.</p><div className="search"><Search size={15} /><input aria-label="Buscar nodos" placeholder="Buscar un nodo…" value={query} onChange={e => setQuery(e.target.value)} /></div><div className="library-scope" role="tablist" aria-label="Apartados de herramientas">{([['todas','Todas'],['univariada','Univariadas'],['multivariada','Multivariadas']] as const).map(([key,label])=><button key={key} role="tab" aria-selected={libraryScope===key} className={libraryScope===key?'active':''} onClick={()=>setLibraryScope(key)}>{label}<small>{key==='todas'?Object.keys(catalog).length:Object.values(catalog).filter(value=>value.scope===key||value.scope==='ambas').length}</small></button>)}</div>{libraryScope!=='todas'&&<p className="subtle library-scope-note">{libraryScope==='univariada'?'Herramientas para una sola variable (distribución, serie, contraste de una media) y las que sirven para ambas.':'Herramientas para varias variables a la vez (relaciones, matrices, modelos con varios regresores, validación) y las que sirven para ambas.'}</p>}
        <div className="library-nodes">{['Fuentes de datos', 'Transformaciones', 'Exploración', 'Modelos', 'Diagnósticos', 'Salidas', 'Experimentos'].map(group => <section className="node-group" key={group}><h3>{group}</h3>{visible.filter(([, value]) => value.category === group).map(([kind, value]) => { const Icon = icons[kind as Kind]; return <button disabled={busy} className="library-node" key={kind} onClick={() => addNode(kind as Kind)} title={`Añadir ${value.label}`}><span className={`node-icon ${value.color}`}><Icon size={17} /></span><span><strong>{value.label}</strong><small>{kind === 'simulate' ? 'Empieza sin descargar datos' : kind === 'wooldridge' ? '115 conjuntos · sin conexión' : kind === 'worldbank' || kind === 'worldbank_multi' || kind === 'fred' ? 'Requiere conexión' : kind === 'ols' ? 'Mínimos cuadrados ordinarios' : kind === 'csv' ? 'Hasta 2 MB · CSV' : 'Explora tus observaciones'}</small></span><Plus size={14} /></button>; })}</section>)}</div>
        <div className="library-note"><span className="note-symbol">↗</span><strong>Aprende conectando</strong><p>Conecta la salida de una fuente con la entrada de un modelo o una visualización.</p><span>{Object.keys(catalog).length} herramientas · 29 recorridos conectados</span></div>
      </aside>
      <section className="center-pane">
        <div className="canvas-toolbar"><div className="project-title"><span className="project-dot" /><input aria-label="Nombre del proyecto" maxLength={120} disabled={busy} value={project.title} onChange={e => update({ ...project, title: e.target.value })} /><span className="draft-tag">{dirty ? "SIN GUARDAR" : activeFile ? "GUARDADO" : "LOCAL"}</span></div><div className="toolbar-buttons"><button className="new-project-button" aria-label="Nuevo proyecto" title="Empezar un flujo vacío" disabled={busy} onClick={newProject}><Plus size={15}/><span>Nuevo proyecto</span></button>
          <button className="equation-button brain-button" title="Segundo cerebro: construir un blueprint desde un enunciado" aria-label="Segundo cerebro" disabled={busy} onClick={() => setBrainOpen(true)}><Brain size={16} /><span>Cerebro IA</span></button>
          <button className="equation-button" title="Archivos y ejemplos" aria-label="Archivos y ejemplos" disabled={busy} onClick={() => setManagerOpen(true)}><FolderOpen size={16} /><span>Proyectos</span></button>
          {equationNode && <button className="equation-button" title="Ecuación del modelo" aria-label="Ecuación del modelo" onClick={() => setEquationOpen(true)}><Sigma size={16} /><span>Ecuación</span></button>}
          <button className="icon-button" title="Deshacer" aria-label="Deshacer" disabled={!history.length || busy} onClick={() => { const previous = history[history.length - 1]; setHistory(history.slice(0, -1)); setProject(previous);setRun(retainResults(project,previous,run)); }}><Undo2 size={16} /></button>
          <button className="icon-button" title="Abrir proyecto" aria-label="Abrir proyecto" disabled={busy} onClick={() => fileRef.current?.click()}><ArrowUpFromLine size={16} /></button>
          <button className="icon-button" title="Guardar proyecto" aria-label="Guardar proyecto" disabled={busy} onClick={() => void saveCurrent()}><ArrowDownToLine size={16} /></button>
          <button className="icon-button" title="Ampliar el espacio de trabajo a toda la pantalla" aria-label="Ampliar espacio de trabajo" aria-pressed={focusMode} onClick={() => toggleFocus(true)}><Maximize2 size={16} /></button>
          <button className="run-button" disabled={busy || !project.nodes.length} onClick={() => void execute()}>{busy ? <LoaderCircle className="spin" size={15} /> : <Play size={14} fill="currentColor" />}{busy ? 'Calculando…' : 'Ejecutar flujo'}</button>
        </div></div>
        <input ref={fileRef} type="file" accept=".json" hidden onChange={e => { void openProject(e.target.files?.[0]); e.target.value = ''; }} />
        {project.lesson&&<LessonGuide lesson={project.lesson} index={stepIndex} run={run} busy={busy} onChoose={chooseStep} onExecute={id=>{setSelectedId(id);void execute(project,id);}} onOverview={()=>void flow?.fitView({padding:.15,minZoom:.1,maxZoom:.8,duration:250})}/>}
        <div className="canvas-area">{focusMode&&<div className="focus-bar" role="toolbar" aria-label="Revisión a pantalla completa"><span className="focus-title"><span className="project-dot"/>{project.title}<small>{project.nodes.length} nodos · {project.edges.length} conexiones</small></span><button title="Encuadrar todo el grafo" onClick={refit}><Scan size={14}/>Encuadrar</button><button className="focus-run" disabled={busy || !project.nodes.length} onClick={() => void execute()}>{busy ? <LoaderCircle className="spin" size={14} /> : <Play size={13} fill="currentColor" />}{busy ? 'Calculando…' : 'Ejecutar'}</button><button className="focus-exit" title="Volver al layout normal (Esc)" aria-label="Volver al layout normal" onClick={() => toggleFocus(false)}><Minimize2 size={14}/>Volver al layout<kbd>Esc</kbd></button></div>}{!project.nodes.length&&<div className="empty-canvas"><Network size={30}/><h2>Empieza un proyecto nuevo</h2><p>1. Ponle un nombre arriba.<br/>2. Añade una fuente de datos.<br/>3. Conecta las herramientas y ejecuta.</p><button onClick={()=>addNode('simulate')} disabled={busy}><Plus size={15}/>Añadir datos simulados</button><small>También puedes cargar CSV, Wooldridge o Banco Mundial desde la biblioteca.</small></div>}{selectedEdge && <div className="edge-actions"><span>{nodeLabel(selectedEdge.source)} → {nodeLabel(selectedEdge.target)}</span><button disabled={busy} onClick={() => disconnect(selectedEdge.id)}><Unplug size={13} />Desconectar</button></div>}<div className="canvas-breadcrumb"><Network size={13} /> Espacio de trabajo <ChevronRight size={12} /> <strong>{project.title || 'Sin título'}</strong></div><ReactFlow<CanvasNode> nodes={nodes} edges={edges} nodeTypes={nodeTypes} onInit={setFlow} onConnect={connect} isValidConnection={validConnection} nodesDraggable={!busy} nodesConnectable={!busy} elementsSelectable={!busy}
          onNodeClick={(_, node) => { setTab('Resultados');setOutputVisible(node.id,true);setSelectedId(node.id);setSuggestion(null); setSelectedEdgeId('');const index=project.lesson?.steps.findIndex(step=>step.node_id===node.id);if(index!==undefined&&index>=0)setStepIndex(index); }} onEdgeClick={(_, edge) => { setSelectedEdgeId(edge.id); setSelectedId(''); }} onPaneClick={() => { setSuggestion(null);setSelectedId(''); setSelectedEdgeId(''); }}
          onNodeDragStart={() => setHistory(h => [...h.slice(-29), project])}
          onNodesChange={changes => { if (busy) return; const changed = applyNodeChanges(changes, nodes); if (changes.some(c => c.type === 'position')) setProject(p => ({ ...p, nodes: p.nodes.map(n => ({ ...n, position: changed.find(c => c.id === n.id)?.position ?? n.position })) })); const removed = changes.filter(c => c.type === 'remove').map(c => c.id); if (removed.length) update({ ...project, nodes: project.nodes.filter(n => !removed.includes(n.id)), edges: project.edges.filter(e => !removed.includes(e.source) && !removed.includes(e.target)) }); }}
          onEdgesChange={changes => { if (busy) return; if (changes.some(c => c.type === 'remove')) { const changed = applyEdgeChanges(changes, edges); update({ ...project, edges: project.edges.filter(e => changed.some(c => c.id === e.id)) }); } }}
          fitView fitViewOptions={{ padding: .25, maxZoom: 1 }} minZoom={.1} maxZoom={1.6} deleteKeyCode={['Backspace', 'Delete']}><Background gap={22} size={1} color="#283548" /><Controls showInteractive={false} /></ReactFlow>
          <div className="canvas-footer"><span>{project.nodes.length} nodos <span>·</span> {project.edges.length} conexiones</span><button disabled={busy} onClick={() => { update(starter()); setSelectedId('model'); }}><RotateCcw size={12} /> Restaurar ejemplo</button></div>
        </div>
        <section className="results"><div className="results-header"><div className="result-tabs">{['Resultados', 'Regresión', 'Descriptivos', 'Trazabilidad'].map(name => <button key={name} className={tab === name ? 'active' : ''} onClick={() => setTab(name)}>{name}</button>)}</div><div className="results-actions">{run && <button className="text-button" onClick={() => download('quantlabs-resultados.json', run)}><ArrowDownToLine size={13} /> Exportar</button>}{resultsFocus
            ? <button className="text-button results-zoom active" title="Volver al layout normal (Esc)" aria-label="Volver al layout normal" onClick={() => setResultsFocus(false)}><Minimize2 size={13} /> Volver al layout<kbd>Esc</kbd></button>
            : <button className="text-button results-zoom" title="Ampliar el área de resultados a toda la pantalla" aria-label="Ampliar resultados" onClick={() => { setFocusMode(false); setResultsFocus(true); }}><Maximize2 size={13} /> Ampliar</button>}</div></div>
          {equationNode&&<button className="regression-shortcut" onClick={()=>setTab('Regresión')}><ChartNoAxesCombined size={14}/>{activeRegression?`${catalog[equationNode.type].label} disponible · R² ${format(activeRegression.r_squared)} · ${format(activeRegression.n,0)} observaciones`:`${catalog[equationNode.type].label} · pendiente de calcular`}<ChevronRight size={13}/></button>}
          <div role={error ? 'alert' : 'status'} className={`status-message ${error ? 'error' : ''}`}>{error ? <><CircleAlert size={14} />{error}{!busy&&<button className="repair-button" onClick={()=>setRepairOpen(true)}><Wrench size={12}/>Reparar con Cerebro IA</button>}</> : notice ? <><CircleCheck size={14} />{notice}</> : <><span className="tiny-dot" />Ejecuta el flujo para calcular resultados con tu muestra.</>}</div>
          {tab==='Regresión'?<RegressionPanel project={project} node={equationNode} run={run} onChoose={id=>{setSelectedId(id);setActiveRegressionId(id);setSelectedEdgeId('');}} onEquation={()=>setEquationOpen(true)}/>:tab==='Resultados'?<OutputDashboard project={project} run={run} selectedId={selectedId} visible={isOutputVisible} onShow={id=>setOutputVisible(id,true)} onHide={id=>setOutputVisible(id,false)} onChoose={id=>{setSelectedId(id);setSelectedEdgeId('');}}/> : !run ? <div className="empty-results"><span className="empty-icon"><ChartNoAxesCombined size={25} /></span><strong>{project.nodes.length?'Tu primera pregunta empieza aquí':'Tu proyecto está vacío'}</strong><p>{project.nodes.length?'Conecta las herramientas y ejecuta el flujo para explorar los resultados.':'Añade datos desde la biblioteca para comenzar. Guarda el proyecto cuando quieras continuar después.'}</p>{!!project.nodes.length&&<button className="text-button" onClick={() => void execute()} disabled={busy}>{busy ? 'Calculando…' : 'Ejecutar mi primer experimento'} <ChevronRight size={14} /></button>}</div> : tab === 'Trazabilidad' ? <div className="manifest"><p>Versión, dependencias, semilla, consulta y huellas de datos de esta ejecución.</p><pre>{JSON.stringify(run.manifest, null, 2)}</pre></div> : tab === 'Descriptivos' ? summary ? <div className="table-wrap"><table><thead><tr><th>Variable</th><th>n</th><th>Faltantes</th><th>Media</th><th>Mediana</th><th>Desv. estándar</th><th>Mínimo</th><th>Máximo</th></tr></thead><tbody>{(summary.rows as Record<string, unknown>[]).map(row => <tr key={String(row.variable)}><td>{String(row.variable)}</td>{['n', 'missing', 'mean', 'median', 'std', 'min', 'max'].map(k => <td key={k}>{format(row[k])}</td>)}</tr>)}</tbody></table><p className="result-footnote">{String(summary.note)}</p></div> : <div className="empty-small">Añade y conecta un nodo de descriptivos para ver su tabla.</div> : experiment && tab!=='Regresión' ? <ExperimentReport result={experiment} /> : <div className="result-grid"><div className="model-result">{model && coefficients ? <><div className="result-title"><h3>Regresión lineal simple</h3><span>OLS · {String(model.covariance)}</span></div><div className="metrics"><div><span>R²</span><strong>{format(model.r_squared)}</strong></div><div><span>Observaciones</span><strong>{format(model.n, 0)}</strong></div><div><span>Filas excluidas</span><strong>{format(model.dropped, 0)}</strong></div></div><table><thead><tr><th>Coeficiente</th><th>Estimación</th><th>Error est.</th><th>p-valor</th></tr></thead><tbody>{coefficients.map(c => <tr key={c.term}><td>{c.term === 'const' ? 'Intercepto' : c.term}</td><td>{format(c.estimate)}</td><td>{format(c.std_error)}</td><td>{c.p_value < .001 ? '< 0.001' : format(c.p_value)}</td></tr>)}</tbody></table><p className="result-footnote">Asociación no implica causalidad. IC 95 % y residuos disponibles al exportar.</p></> : <div className="empty-small">Añade OLS para estimar una relación.<br />Selecciona cualquier nodo para inspeccionar su resultado.</div>}</div><div className="chart-result"><div className="result-title"><h3>La relación en los datos</h3>{scatter && <span>{format(scatter.n, 0)} puntos · {format(scatter.dropped, 0)} excluidos</span>}</div>{scatter ? <Scatter result={scatter} model={model || undefined} /> : <div className="empty-small">Conecta un nodo de dispersión para ver el gráfico.</div>}</div></div>}
        </section>
      </section>
      <aside className="inspector"><ErrorBoundary area="el inspector" resetKey={selectedId}><div className="section-heading"><h2>Inspector</h2><span><Braces size={15} /></span></div>{selected && item ? <><div className="inspector-title"><span className={`node-icon ${item.color}`}>{(() => { const Icon = icons[selected.type]; return <Icon size={20} />; })()}</span><div><h3>{item.label}</h3><p>Configuración del nodo</p></div></div><div className="inspector-divider" /><h4>PARÁMETROS</h4>
          {selected.type==='wooldridge'&&<WooldridgePicker value={String(selected.parameters.dataset??'wage1')} busy={busy} onChange={dataset=>{const next:Project={...project,nodes:project.nodes.map(node=>node.id===selected.id?{...node,parameters:{...node.parameters,dataset}}:node)};update(next);void execute(next,selected.id);}} onLoad={()=>void execute(project,selected.id)}/>}
          {['scatter','ols'].includes(selected.type)&&<ScatterVariables project={project} node={selected} schemas={schemas} busy={busy} onAxes={(x,y)=>update({...project,nodes:project.nodes.map(node=>node.id===selected.id?{...node,parameters:{...node.parameters,x,y}}:node)})} onLoad={id=>void execute(project,id)}/>}
          {selected.type==='boxplot'&&<BoxplotCondition node={selected} busy={busy} onChange={setParameter}/>}
          {selected.type==='join_series'&&<JoinSeriesVariables project={project} node={selected} run={run} busy={busy} onChange={setParameter} onLoad={id=>void execute(project,id)}/>}
          {selected.type==='time_plot'&&<TimePlotVariables project={project} node={selected} schemas={schemas} busy={busy} onChange={setParameter} onLoad={id=>void execute(project,id)}/>}
          {!['scatter','ols','time_plot'].includes(selected.type)&&<DataVariables project={project} node={selected} schemas={schemas} busy={busy} onChange={(key,value)=>setParameter(key,value)} onLoad={id=>void execute(project,id)} onPatch={parameters=>update({...project,nodes:project.nodes.map(node=>node.id===selected.id?{...node,parameters:{...node.parameters,...parameters}}:node)})}/>}
          {selected.type==='worldbank_multi'&&<IndicatorListEditor countries={String(selected.parameters.countries??'USA')} indicators={String(selected.parameters.indicators??'')} source={Number(selected.parameters.source??2)} disabled={busy} onPatch={parameters=>{update({...project,nodes:project.nodes.map(node=>node.id===selected.id?{...node,parameters:{...node.parameters,...parameters}}:node)});setNotice('Indicadores cambiados. Ejecuta el flujo para descargar las nuevas series.');}}/>}
          {selected.type==='fred'&&<FredSeriesEditor series={String(selected.parameters.series??'')} disabled={busy} onPatch={parameters=>{update({...project,nodes:project.nodes.map(node=>node.id===selected.id?{...node,parameters:{...node.parameters,...parameters}}:node)});setNotice('Series cambiadas. Ejecuta el flujo para descargarlas de FRED.');}}/>}
          {Object.entries(selected.parameters).filter(([key]) => selected.type!=='join_series' && !(selected.type==='fred'&&key==='series') && key!=='extra_inputs' && !(selected.type==='worldbank_multi'&&['countries','indicators'].includes(key)) && !(selected.type==='pairplot'&&key==='group') && !(selected.type==='boxplot'&&['operator','threshold'].includes(key)) && key !== 'content' && key !== 'source' && !(selected.type==='wooldridge'&&key==='dataset') && !['indicator_name','indicator_unit','indicator_source_name'].includes(key) && !(selected.type==='time_plot'&&['time','time_mode','color'].includes(key)) && !isColumnParameter(key)).map(([key, value]) => key === 'country' && selected.type === 'worldbank' ? <CountryPicker key={`${selected.id}-country`} value={String(value)} disabled={busy} onChange={country=>{setParameter('country',country);setNotice('País cambiado. Ejecuta el flujo para consultar sus datos.');}}/> : key === 'indicator' && selected.type === 'worldbank' ? <IndicatorPicker key={`${selected.id}-indicator`} value={String(value)} source={Number(selected.parameters.source ?? 2)} disabled={busy} name={String(selected.parameters.indicator_name??'')} unit={String(selected.parameters.indicator_unit??'')} onChange={(indicator, source,metadata) => {update({ ...project, nodes: project.nodes.map(node => node.id === selected.id ? { ...node, parameters: { ...node.parameters, indicator, source,indicator_name:metadata.name,indicator_unit:metadata.unit,indicator_source_name:metadata.source_name } } : node) });setNotice('Indicador cambiado. Ejecuta el flujo para descargar la nueva serie; los resultados anteriores se han retirado.');}} /> : <label className="field" key={`${selected.id}-${key}`}><span>{{ n: 'Observaciones', seed: 'Semilla aleatoria', intercept: 'Intercepto (β₀)', slope: 'Pendiente (β₁)', noise: 'Desviación del ruido', alpha:'Nivel de significancia (α)',color:'Color del gráfico', title:'Título del gráfico',x_label:'Etiqueta del eje horizontal',y_label:'Etiqueta del eje vertical', x: 'Variable explicativa (x)', y: 'Variable respuesta (y)', covariance: 'Errores estándar', delimiter: 'Separador CSV', country: 'País (ISO 3)', indicator: 'Código de indicador', scenario: 'Escenario de datos', columns: 'Columnas (separadas por coma)', column: 'Columna', features: 'Regresores (separados por coma)', instruments: 'Instrumentos', method: 'Método', fraction: 'Fracción de entrenamiento', confidence: 'Nivel de confianza', periods: 'Número de períodos', degree: 'Grado máximo', output: 'Nombre de la salida', population: 'Columna de población', value: 'Columna de valores', nominal: 'Columna nominal', index: 'Índice de precios', base: 'Base del índice', lookback: 'Ventana del pasado', returns: 'Retornos', signal: 'Señal', cost: 'Costo por cambio de posición', components: 'Componentes', clusters: 'Grupos', states: 'Estados', hidden: 'Neuronas ocultas', quantiles: 'Cuantiles', before: 'Antes', after: 'Después', prior: 'Probabilidad previa', sensitivity: 'Sensibilidad', false_positive: 'Probabilidad de falso positivo', sample_size: 'Tamaño de cada remuestra', replications: 'Número de remuestras', initial: 'Valor inicial', threshold: 'Umbral', evaluation: 'Muestra de evaluación', template: 'Plantilla registrada', note: 'Pregunta de interpretación', error: 'Error de equilibrio', bins: 'Intervalos', lags: 'Rezagos', topic: 'Tema del experimento (C01–C28)', start: 'Año inicial', end: 'Año final', start_date: 'Fecha inicial (AAAA-MM-DD)', end_date: 'Fecha final (vacía = hoy)', frequency: 'Frecuencia', aggregation: 'Agregación al convertir', target: 'Parámetro a estimar', margin: 'Margen de error (E)', sd: 'Desviación estándar (σ)', proportion: 'Proporción esperada (p)', population_size: 'Tamaño de población (0 = infinita)', mu: 'Valor bajo H₀ (μ₀)', break_fraction: 'Fracción de la muestra en el quiebre', period: 'Período estacional', model: 'Tipo de descomposición', p: 'Orden AR (p)', d: 'Diferencias (d)', q: 'Orden MA (q)', P: 'AR estacional (P)', D: 'Diferencias estacionales (D)', Q: 'MA estacional (Q)', s: 'Longitud estacional (s)', horizon: 'Horizonte de pronóstico', det_order: 'Término determinista (−1, 0, 1)', k_ar_diff: 'Rezagos en diferencias', folds: 'Pliegues de validación cruzada', max_k: 'Máximo número de grupos', vol: 'Modelo de volatilidad', dist: 'Distribución de los errores', o: 'Orden asimétrico (o)', direction: 'Dirección', criterion: 'Criterio', at: 'Evaluar en', statistic: 'Estadístico', max_points: 'Máximo de puntos dibujados', mode: 'Presentación', scale: 'Escala', orientation: 'Orientación', alternative: 'Hipótesis alternativa', condition_threshold: 'Umbral del índice de condición', cv: 'Tipo de validación', estimator: 'Estimador', alpha_min: 'α mínimo', alpha_max: 'α máximo', n_alphas: 'Número de valores de α', y_axis: 'Formato del eje Y', x_axis: 'Formato del eje X' }[key] ?? key}</span>{catalog[selected.type].choices?.[key] ? <select disabled={busy} value={value} onChange={event=>setParameter(key,event.target.value)}>{catalog[selected.type].choices![key].map(option=><option key={option} value={option}>{catalog[selected.type].choice_labels?.[key]?.[option]??option}</option>)}</select> : key === 'covariance' ? <select disabled={busy} value={value} onChange={e => setParameter(key, e.target.value)}><option value="HC3">Robustos · HC3</option><option value="nonrobust">Clásicos</option></select> : key === 'delimiter' ? <select disabled={busy} value={value} onChange={e => setParameter(key, e.target.value)}><option value=",">Coma (,)</option><option value=";">Punto y coma (;)</option><option value={'\t'}>Tabulación</option></select> : key==='color'?<input disabled={busy} aria-label="Color del gráfico" type="color" value={String(value)} onChange={event=>setParameter(key,event.target.value)}/>: <input disabled={busy} type={typeof value === 'number' ? 'number' : 'text'} step="any" value={Number.isNaN(value) ? '' : value} onChange={e => setParameter(key, typeof value === 'number' ? e.target.valueAsNumber : e.target.value)} />}</label>)}
          {selected.type === 'csv' && <label className="csv-upload"><ArrowUpFromLine size={18} />Seleccionar CSV<input disabled={busy} type="file" accept=".csv,.tsv,text/csv" onChange={async e => { const file = e.target.files?.[0]; if (!file) return; if (file.size > 2_000_000) { setError('El CSV supera 2 MB.'); return; } setParameter('content', await file.text()); }} /><small>{selected.parameters.content ? 'Archivo cargado en el proyecto' : 'Datos guardados dentro del proyecto local'}</small></label>}
          {!Object.keys(selected.parameters).length && <p className="subtle">Este nodo usa las columnas numéricas de la fuente conectada.</p>}
          <section className="node-connections"><h4>CONEXIONES</h4>{connections.length ? connections.map(edge => <div className="connection-row" key={edge.id}><span>{nodeLabel(edge.source)}<span> → </span>{nodeLabel(edge.target)}</span><button type="button" disabled={busy} title={`Desconectar ${nodeLabel(edge.source)} de ${nodeLabel(edge.target)}`} aria-label={`Desconectar ${nodeLabel(edge.source)} de ${nodeLabel(edge.target)}`} onClick={() => disconnect(edge.id)}><Unplug size={14} /><span>Desconectar</span></button></div>) : <p>Este nodo no tiene conexiones.</p>}<small>Desconecta un enlace sin eliminar los módulos. Puedes usar Deshacer para recuperarlo.</small></section>
          <div className="learning-card"><div><BookOpen size={15} /><strong>Detrás del nodo</strong></div>{selected.type === 'ols' && <div className="formula">y = β₀ + β₁x + ε</div>}<p>{item.explanation}</p><span>Referencias {item.references}</span></div>
          {selectedResult?.error && <div role="alert" className="node-error"><strong>{selectedResult.error.code}</strong><p>{selectedResult.error.message}</p><button className="repair-button" disabled={busy} onClick={()=>setRepairOpen(true)}><Wrench size={12}/>Que Cerebro IA lo arregle</button></div>}
          {selectedResult?.result && <details className="node-details"><summary>Ver resultado del nodo</summary><pre>{JSON.stringify(selectedResult.result, null, 2)}</pre></details>}
          <button className="delete-node" disabled={busy} onClick={() => { update({ ...project, nodes: project.nodes.filter(n => n.id !== selected.id), edges: project.edges.filter(e => e.source !== selected.id && e.target !== selected.id) }); setSelectedId(''); }}><Trash2 size={13} />Eliminar nodo</button>
        </> : <div className="inspector-empty"><Network size={28} /><p>Selecciona un nodo para explorar sus parámetros y fundamentos.</p></div>}</ErrorBoundary></aside>
    </main>{managerOpen && <ProjectManager project={project} active={activeFile} onOpen={(next, file) => { update(next); setActiveFile(file ?? null); setStepIndex(0); setSelectedId(next.nodes[0]?.id ?? ''); setSelectedEdgeId(''); }} onRun={(next, file) => { update(next); setActiveFile(file ?? null); setStepIndex(0); setSelectedId(next.nodes[0]?.id ?? ''); setManagerOpen(false); void execute(next); }} onDeleted={id => setActiveFile(file => file?.id === id ? null : file)} onClose={() => setManagerOpen(false)} />}{repairOpen && <RepairPanel project={project} onClose={() => setRepairOpen(false)} onApply={(next, andRun) => { update({ ...next, lesson: project.lesson }); setRepairOpen(false); setNotice('Cambios de Cerebro IA aplicados al flujo. Puedes deshacerlos con Deshacer.'); if (andRun) void execute({ ...next, lesson: project.lesson }); }} />}{brainOpen && <BrainPanel onRepair={() => { setBrainOpen(false); setRepairOpen(true); }} onOpen={next => { if (!dirty || window.confirm('El canvas tiene cambios sin guardar. ¿Reemplazarlo por el blueprint?')) { update(next); setActiveFile(null); setStepIndex(0); setSelectedId(next.nodes[0]?.id ?? ''); setSelectedEdgeId(''); setBrainOpen(false); } }} onRun={next => { if (!dirty || window.confirm('El canvas tiene cambios sin guardar. ¿Reemplazarlo por el blueprint?')) { update(next); setActiveFile(null); setStepIndex(0); setSelectedId(next.nodes[0]?.id ?? ''); setSelectedEdgeId(''); setBrainOpen(false); void execute(next); } }} onClose={() => setBrainOpen(false)} />}{equationOpen && <ModelEquation node={equationNode} result={equationNode ? run?.nodes[equationNode.id] : undefined} onClose={() => setEquationOpen(false)} />}<footer className="app-footer"><span><span className="tiny-dot" /> {Object.keys(catalog).length} herramientas · 29 recorridos · ejecución reproducible</span><span>Motor Python · {window.quantlabsDesktop?'Electron':'Web'} · v{version}</span></footer>
  </div>;
}
