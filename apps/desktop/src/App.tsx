import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ReactFlow, Background, Controls, Handle, Position, addEdge, applyNodeChanges, applyEdgeChanges, type Node, type NodeProps, type Connection, type ReactFlowInstance } from '@xyflow/react';
import { ArrowDownToLine, ArrowUpFromLine, FolderOpen, Play, Plus, Search, FlaskConical, Database, ChartScatter, ChartNoAxesCombined, Sigma, BookOpen, ChevronRight, CircleCheck, RotateCcw, Undo2, Trash2, Unplug, Network, CircleAlert, Braces, LoaderCircle } from 'lucide-react';
import ModelEquation from './ModelEquation';
import IndicatorPicker from './IndicatorPicker';
import ProjectManager, { type SavedProject } from './ProjectManager';
import ExperimentReport from './ExperimentReport';
import LessonGuide from './LessonGuide';
import NodeOutput from './NodeOutput';
import Scatter from './ScatterPlot';
import { catalog, download, parseProject, rpc, starter, version, type Kind, type Project, type Run, type NodeResult } from './model';

const icons = Object.fromEntries(Object.entries(catalog).map(([kind,item])=>[kind,item.category==='Fuentes de datos'?Database:item.category==='Modelos'?ChartNoAxesCombined:item.category==='Exploración'?ChartScatter:item.category==='Experimentos'?BookOpen:Sigma])) as Record<Kind,typeof BookOpen>;
const format = (v: unknown, digits = 3) => typeof v === 'number' ? new Intl.NumberFormat('es-MX', { maximumFractionDigits: digits }).format(v) : '—';
type CanvasNode = Node<{ kind: Kind; state?: NodeResult; index: number }, 'econometric'>;

function EconometricNode({ data, selected }: NodeProps<CanvasNode>) {
  const item = catalog[data.kind]; const Icon = icons[data.kind]; const state = data.state;
  const definition=catalog[data.kind];
  const inputPorts=Object.entries(definition.inputs);const outputPorts=Object.entries(definition.outputs);
  const isSource = !inputPorts.length;
  const result = state?.result;
  return <div className={`flow-node ${selected ? 'selected' : ''} ${item.color}`}>
    {inputPorts.map(([port,type],i)=><Handle key={port} type="target" position={Position.Left} id={port} style={{top:`${100*(i+1)/(inputPorts.length+1)}%`}} aria-label={`Entrada ${port}: ${type}`} title={`${port}: ${type}`}/>)}
    <div className="node-top"><span className={`node-icon ${item.color}`}><Icon size={17} /></span><span className="node-type">{isSource ? 'DATOS' : data.kind === 'ols' ? 'ESTIMACIÓN' : 'EXPLORACIÓN'}</span><span className="node-number">0{data.index + 1}</span></div>
    <strong>{item.label}</strong><p>{item.detail}</p><div className="port-names"><span>↓ {inputPorts.map(([port])=>port).join(', ')||'origen'}</span><span>↑ {outputPorts.map(([port])=>port).join(', ')||'sin salidas'}</span></div>
    <div className={`node-bottom ${state?.status ?? ''}`}>
      {state?.status === 'succeeded' ? <><CircleCheck size={12} />{data.kind === 'ols' ? `R² ${format(result?.r_squared)}` : data.kind === 'experiment' ? `${String(result?.topic)} · completado` : `${format(result?.n ?? result?.n_total)} observaciones`}</> : state?.status === 'failed' ? <><CircleAlert size={12} />Revisar parámetros</> : state?.status === 'skipped' ? 'Origen sin resultados' : <><span className="tiny-dot" /> Listo para conectar</>}
    </div>
    {outputPorts.map(([port,type],i)=><Handle key={port} type="source" position={Position.Right} id={port} style={{top:`${100*(i+1)/(outputPorts.length+1)}%`}} aria-label={`Salida ${port}: ${type}`} title={`${port}: ${type}`}/>)}
  </div>;
}
const nodeTypes = { econometric: EconometricNode };

export default function App() {
  const [project, setProject] = useState<Project>(starter);
  const [history, setHistory] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState('model');
  const [selectedEdgeId, setSelectedEdgeId] = useState('');
  const [run, setRun] = useState<Run | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [query, setQuery] = useState('');
  const [tab, setTab] = useState('Resultados');
  const [equationOpen, setEquationOpen] = useState(false);
  const [managerOpen, setManagerOpen] = useState(false);
  const [activeFile, setActiveFile] = useState<SavedProject | null>(null);
  const [stepIndex,setStepIndex]=useState(0);
  const [flow,setFlow]=useState<ReactFlowInstance<CanvasNode>|null>(null);
  const chooseStep=(index:number)=>{const step=project.lesson?.steps[index];if(!step)return;setStepIndex(index);setSelectedId(step.node_id);setSelectedEdgeId('');void flow?.fitView({nodes:[{id:step.node_id}],padding:.5,minZoom:.65,maxZoom:1,duration:250});};
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
  const equationNode = selected?.type === 'ols' ? selected : project.nodes.find(node => node.type === 'ols');
  const update = useCallback((next: Project, remember = true) => {
    if (busy) return;
    if(next.lesson){const ids=new Set(next.nodes.map(node=>node.id));const steps=next.lesson.steps.filter(step=>ids.has(step.node_id));next={...next,lesson:steps.length?{...next.lesson,steps}:undefined};setStepIndex(index=>Math.max(0,Math.min(index,steps.length-1)));}
    if (remember) setHistory(h => [...h.slice(-29), project]);
    setProject(next); setRun(null); setError(''); setNotice('');
  }, [project, busy]);
  const nodes: CanvasNode[] = useMemo(() => project.nodes.map((node, index) => ({ id: node.id, type: 'econometric', position: node.position, selected: selectedId === node.id, data: { kind: node.type, state: run?.nodes[node.id], index } })), [project, selectedId, run]);
  const edges = useMemo(() => project.edges.map(edge => ({ ...edge, sourceHandle: edge.source_port, targetHandle: edge.target_port, type: 'smoothstep', animated: busy, selected: edge.id === selectedEdgeId, style: { stroke: edge.id === selectedEdgeId ? '#b77748' : '#73a795', strokeWidth: edge.id === selectedEdgeId ? 2.8 : 1.6 } })), [project.edges, busy, selectedEdgeId]);
  const addNode = (kind: Kind) => {
    const id = crypto.randomUUID();
    update({ ...project, nodes: [...project.nodes, { id, type: kind, node_version: '1.0.0', parameters: { ...catalog[kind].defaults }, position: { x: project.nodes.length?Math.max(...project.nodes.map(node=>node.position.x))+320:30, y: project.nodes.at(-1)?.position.y??120 } }] }); setSelectedId(id);setSelectedEdgeId('');requestAnimationFrame(()=>void flow?.fitView({nodes:[...(project.nodes.length?[{id:project.nodes.at(-1)!.id}]:[]),{id}],padding:.2,minZoom:.3,maxZoom:1,duration:250}));
  };
  const validConnection = (connection: {source: string;target: string;sourceHandle?: string|null;targetHandle?: string|null}) => {
    const source=project.nodes.find(node=>node.id===connection.source),target=project.nodes.find(node=>node.id===connection.target);
    if(!source||!target||source.id===target.id||!connection.sourceHandle||!connection.targetHandle)return false;
    if(catalog[source.type].outputs[connection.sourceHandle]!==catalog[target.type].inputs[connection.targetHandle]||!catalog[source.type].outputs[connection.sourceHandle])return false;
    if(project.edges.some(edge=>edge.target===target.id&&edge.target_port===connection.targetHandle))return false;
    const visited=new Set<string>();const stack=[target.id];
    while(stack.length){const id=stack.pop()!;if(id===source.id)return false;if(visited.has(id))continue;visited.add(id);project.edges.filter(edge=>edge.source===id).forEach(edge=>stack.push(edge.target));}
    return true;
  };
  const connect = (connection: Connection) => {
    if(!validConnection(connection)){setError('Conecta puertos del mismo tipo, sin ciclos ni entradas duplicadas.');return;}
    const next=addEdge(connection,edges);
    update({...project,edges:next.map(edge=>({id:edge.id,source:edge.source,target:edge.target,source_port:edge.sourceHandle!,target_port:edge.targetHandle!}))});
  };

  const setParameter = (key: string, value: string | number) => {
    if (!selected) return;
    update({ ...project, nodes: project.nodes.map(n => n.id === selected.id ? { ...n, parameters: { ...n.parameters, [key]: value } } : n) });
  };
  const execute = async (target: Project = project, targetNode?:string) => {
    setBusy(true); setError(''); setNotice(''); if(!targetNode)setRun(null);
    try {
      const value = await rpc<Run>('run.start', { project: target, ...(targetNode?{target_node:targetNode}:{}) });
      setRun(previous=>{
        if(!targetNode||!previous||previous.manifest.graph_sha256!==value.manifest.graph_sha256)return value;
        const before=previous.manifest.sources as Record<string,{data_sha256:string}>;const after=value.manifest.sources as Record<string,{data_sha256:string}>;
        if(Object.entries(after).some(([id,source])=>before[id]&&before[id].data_sha256!==source.data_sha256))return value;
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
  const resultOf = (kind: Kind) => {
    const node = project.nodes.find(n => n.type === kind && run?.nodes[n.id]?.status === 'succeeded');
    return node && run?.nodes[node.id]?.result;
  };
  const model = resultOf('ols'), scatter = resultOf('scatter'), summary = resultOf('describe'), experiment = resultOf('experiment');
  const selectedResult = selected && run?.nodes[selected.id];
  const coefficients = model?.coefficients as { term: string; estimate: number; std_error: number; p_value: number }[] | undefined;
  const visible = Object.entries(catalog).filter(([, value]) => `${value.label} ${value.detail}`.toLocaleLowerCase().includes(query.toLocaleLowerCase()));
  return <div className="app-shell">
    <header className="app-header">
      <div className="brand"><span className="brand-mark"><Network size={21} /></span><span>Quantlabs<span className="brand-light"> / Econometrics</span></span><span className="alpha-tag">ALPHA</span></div>
      <div className="header-actions"><span className="local-badge"><span className="tiny-dot" />Laboratorio local</span><span className="header-version">v{version}</span></div>
    </header>
    <div className="workbench-heading"><div><div className="eyebrow">TU ESPACIO DE EXPLORACIÓN</div><h1>Las ideas se conectan.<br className="mobile-break" /> Los datos, también.</h1><p>Construye un flujo. Haz una pregunta. Entiende el resultado.</p></div><div className="lesson-pill"><BookOpen size={17} /><div><strong>Primer experimento</strong><span>Ingreso, consumo y regresión</span></div><ChevronRight size={16} /></div></div>
    <main className="workbench">
      <aside className="library"><div className="section-heading"><h2>Biblioteca de nodos</h2><span>{Object.keys(catalog).length}</span></div><p className="subtle">Añade una pieza a tu análisis.</p><div className="search"><Search size={15} /><input aria-label="Buscar nodos" placeholder="Buscar un nodo…" value={query} onChange={e => setQuery(e.target.value)} /></div>
        <div className="library-nodes">{['Fuentes de datos', 'Transformaciones', 'Exploración', 'Modelos', 'Diagnósticos', 'Salidas', 'Experimentos'].map(group => <section className="node-group" key={group}><h3>{group}</h3>{visible.filter(([, value]) => value.category === group).map(([kind, value]) => { const Icon = icons[kind as Kind]; return <button disabled={busy} className="library-node" key={kind} onClick={() => addNode(kind as Kind)} title={`Añadir ${value.label}`}><span className={`node-icon ${value.color}`}><Icon size={17} /></span><span><strong>{value.label}</strong><small>{kind === 'simulate' ? 'Empieza sin descargar datos' : kind === 'worldbank' ? 'Requiere conexión' : kind === 'ols' ? 'Mínimos cuadrados ordinarios' : kind === 'csv' ? 'Hasta 2 MB · CSV' : 'Explora tus observaciones'}</small></span><Plus size={14} /></button>; })}</section>)}</div>
        <div className="library-note"><span className="note-symbol">↗</span><strong>Aprende conectando</strong><p>Conecta la salida de una fuente con la entrada de un modelo o una visualización.</p><span>{Object.keys(catalog).length} herramientas · 28 recorridos conectados</span></div>
      </aside>
      <section className="center-pane">
        <div className="canvas-toolbar"><div className="project-title"><span className="project-dot" /><input aria-label="Nombre del proyecto" maxLength={120} disabled={busy} value={project.title} onChange={e => update({ ...project, title: e.target.value })} /><span className="draft-tag">{dirty ? "SIN GUARDAR" : activeFile ? "GUARDADO" : "LOCAL"}</span></div><div className="toolbar-buttons">
          <button className="equation-button" title="Archivos y ejemplos" aria-label="Archivos y ejemplos" disabled={busy} onClick={() => setManagerOpen(true)}><FolderOpen size={16} /><span>Proyectos</span></button>
          {equationNode && <button className="equation-button" title="Ecuación del modelo" aria-label="Ecuación del modelo" onClick={() => setEquationOpen(true)}><Sigma size={16} /><span>Ecuación</span></button>}
          <button className="icon-button" title="Deshacer" aria-label="Deshacer" disabled={!history.length || busy} onClick={() => { const previous = history[history.length - 1]; setHistory(history.slice(0, -1)); setProject(previous); setRun(null); }}><Undo2 size={16} /></button>
          <button className="icon-button" title="Abrir proyecto" aria-label="Abrir proyecto" disabled={busy} onClick={() => fileRef.current?.click()}><ArrowUpFromLine size={16} /></button>
          <button className="icon-button" title="Guardar proyecto" aria-label="Guardar proyecto" disabled={busy} onClick={() => void saveCurrent()}><ArrowDownToLine size={16} /></button>
          <button className="run-button" disabled={busy} onClick={() => void execute()}>{busy ? <LoaderCircle className="spin" size={15} /> : <Play size={14} fill="currentColor" />}{busy ? 'Calculando…' : 'Ejecutar flujo'}</button>
        </div></div>
        <input ref={fileRef} type="file" accept=".json" hidden onChange={e => { void openProject(e.target.files?.[0]); e.target.value = ''; }} />
        {project.lesson&&<LessonGuide lesson={project.lesson} index={stepIndex} run={run} busy={busy} onChoose={chooseStep} onExecute={id=>{setSelectedId(id);void execute(project,id);}} onOverview={()=>void flow?.fitView({padding:.15,minZoom:.1,maxZoom:.8,duration:250})}/>}
        <div className="canvas-area">{selectedEdge && <div className="edge-actions"><span>{nodeLabel(selectedEdge.source)} → {nodeLabel(selectedEdge.target)}</span><button disabled={busy} onClick={() => disconnect(selectedEdge.id)}><Unplug size={13} />Desconectar</button></div>}<div className="canvas-breadcrumb"><Network size={13} /> Espacio de trabajo <ChevronRight size={12} /> <strong>{project.title || 'Sin título'}</strong></div><ReactFlow<CanvasNode> nodes={nodes} edges={edges} nodeTypes={nodeTypes} onInit={setFlow} onConnect={connect} isValidConnection={validConnection} nodesDraggable={!busy} nodesConnectable={!busy} elementsSelectable={!busy}
          onNodeClick={(_, node) => { setSelectedId(node.id); setSelectedEdgeId('');const index=project.lesson?.steps.findIndex(step=>step.node_id===node.id);if(index!==undefined&&index>=0)setStepIndex(index); }} onEdgeClick={(_, edge) => { setSelectedEdgeId(edge.id); setSelectedId(''); }} onPaneClick={() => { setSelectedId(''); setSelectedEdgeId(''); }}
          onNodeDragStart={() => setHistory(h => [...h.slice(-29), project])}
          onNodesChange={changes => { if (busy) return; const changed = applyNodeChanges(changes, nodes); if (changes.some(c => c.type === 'position')) setProject(p => ({ ...p, nodes: p.nodes.map(n => ({ ...n, position: changed.find(c => c.id === n.id)?.position ?? n.position })) })); const removed = changes.filter(c => c.type === 'remove').map(c => c.id); if (removed.length) update({ ...project, nodes: project.nodes.filter(n => !removed.includes(n.id)), edges: project.edges.filter(e => !removed.includes(e.source) && !removed.includes(e.target)) }); }}
          onEdgesChange={changes => { if (busy) return; if (changes.some(c => c.type === 'remove')) { const changed = applyEdgeChanges(changes, edges); update({ ...project, edges: project.edges.filter(e => changed.some(c => c.id === e.id)) }); } }}
          fitView fitViewOptions={{ padding: .25, maxZoom: 1 }} minZoom={.1} maxZoom={1.6} deleteKeyCode={['Backspace', 'Delete']}><Background gap={22} size={1} color="#cdd8d0" /><Controls showInteractive={false} /></ReactFlow>
          <div className="canvas-footer"><span>{project.nodes.length} nodos <span>·</span> {project.edges.length} conexiones</span><button disabled={busy} onClick={() => { update(starter()); setSelectedId('model'); }}><RotateCcw size={12} /> Restaurar ejemplo</button></div>
        </div>
        <section className="results"><div className="results-header"><div className="result-tabs">{['Resultados', 'Descriptivos', 'Trazabilidad'].map(name => <button key={name} className={tab === name ? 'active' : ''} onClick={() => setTab(name)}>{name}</button>)}</div>{run && <button className="text-button" onClick={() => download('quantlabs-resultados.json', run)}><ArrowDownToLine size={13} /> Exportar</button>}</div>
          <div role={error ? 'alert' : 'status'} className={`status-message ${error ? 'error' : ''}`}>{error ? <><CircleAlert size={14} />{error}</> : notice ? <><CircleCheck size={14} />{notice}</> : <><span className="tiny-dot" />Ejecuta el flujo para calcular resultados con tu muestra.</>}</div>
          {project.lesson && tab==='Resultados' ? <div className="guided-output"><h3>Salida: {selected?catalog[selected.type].label:'selecciona un paso'}</h3>{selectedResult?.status==='succeeded'&&selectedResult.result?<NodeOutput result={selectedResult.result}/>:selectedResult?.error?<div className="node-error">{selectedResult.error.message}</div>:<div className="empty-small">Ejecuta el paso seleccionado para inspeccionar su resultado real.</div>}</div> : !run ? <div className="empty-results"><span className="empty-icon"><ChartNoAxesCombined size={25} /></span><strong>Tu primera pregunta empieza aquí</strong><p>El ejemplo ya está conectado. Ejecuta el flujo para explorar<br />cómo se relacionan el ingreso y el consumo.</p><button className="text-button" onClick={() => void execute()} disabled={busy}>{busy ? 'Calculando…' : 'Ejecutar mi primer experimento'} <ChevronRight size={14} /></button></div> : tab === 'Trazabilidad' ? <div className="manifest"><p>Versión, dependencias, semilla, consulta y huellas de datos de esta ejecución.</p><pre>{JSON.stringify(run.manifest, null, 2)}</pre></div> : tab === 'Descriptivos' ? summary ? <div className="table-wrap"><table><thead><tr><th>Variable</th><th>n</th><th>Faltantes</th><th>Media</th><th>Mediana</th><th>Desv. estándar</th><th>Mínimo</th><th>Máximo</th></tr></thead><tbody>{(summary.rows as Record<string, unknown>[]).map(row => <tr key={String(row.variable)}><td>{String(row.variable)}</td>{['n', 'missing', 'mean', 'median', 'std', 'min', 'max'].map(k => <td key={k}>{format(row[k])}</td>)}</tr>)}</tbody></table><p className="result-footnote">{String(summary.note)}</p></div> : <div className="empty-small">Añade y conecta un nodo de descriptivos para ver su tabla.</div> : experiment ? <ExperimentReport result={experiment} /> : <div className="result-grid"><div className="model-result">{model && coefficients ? <><div className="result-title"><h3>Regresión lineal simple</h3><span>OLS · {String(model.covariance)}</span></div><div className="metrics"><div><span>R²</span><strong>{format(model.r_squared)}</strong></div><div><span>Observaciones</span><strong>{format(model.n, 0)}</strong></div><div><span>Filas excluidas</span><strong>{format(model.dropped, 0)}</strong></div></div><table><thead><tr><th>Coeficiente</th><th>Estimación</th><th>Error est.</th><th>p-valor</th></tr></thead><tbody>{coefficients.map(c => <tr key={c.term}><td>{c.term === 'const' ? 'Intercepto' : c.term}</td><td>{format(c.estimate)}</td><td>{format(c.std_error)}</td><td>{c.p_value < .001 ? '< 0.001' : format(c.p_value)}</td></tr>)}</tbody></table><p className="result-footnote">Asociación no implica causalidad. IC 95 % y residuos disponibles al exportar.</p></> : <div className="empty-small">Añade OLS para estimar una relación.<br />Selecciona cualquier nodo para inspeccionar su resultado.</div>}</div><div className="chart-result"><div className="result-title"><h3>La relación en los datos</h3>{scatter && <span>{format(scatter.n, 0)} puntos · {format(scatter.dropped, 0)} excluidos</span>}</div>{scatter ? <Scatter result={scatter} model={model || undefined} /> : <div className="empty-small">Conecta un nodo de dispersión para ver el gráfico.</div>}</div></div>}
        </section>
      </section>
      <aside className="inspector"><div className="section-heading"><h2>Inspector</h2><span><Braces size={15} /></span></div>{selected && item ? <><div className="inspector-title"><span className={`node-icon ${item.color}`}>{(() => { const Icon = icons[selected.type]; return <Icon size={20} />; })()}</span><div><h3>{item.label}</h3><p>Configuración del nodo</p></div></div><div className="inspector-divider" /><h4>PARÁMETROS</h4>
          {Object.entries(selected.parameters).filter(([key]) => key !== 'content' && key !== 'source').map(([key, value]) => key === 'indicator' && selected.type === 'worldbank' ? <IndicatorPicker key={`${selected.id}-indicator`} value={String(value)} source={Number(selected.parameters.source ?? 2)} disabled={busy} onChange={(indicator, source) => update({ ...project, nodes: project.nodes.map(node => node.id === selected.id ? { ...node, parameters: { ...node.parameters, indicator, source } } : node) })} /> : <label className="field" key={`${selected.id}-${key}`}><span>{{ n: 'Observaciones', seed: 'Semilla aleatoria', intercept: 'Intercepto (β₀)', slope: 'Pendiente (β₁)', noise: 'Desviación del ruido', x: 'Variable explicativa (x)', y: 'Variable respuesta (y)', covariance: 'Errores estándar', delimiter: 'Separador CSV', country: 'País (ISO 3)', indicator: 'Código de indicador', scenario: 'Escenario de datos', columns: 'Columnas (separadas por coma)', column: 'Columna', features: 'Regresores (separados por coma)', instruments: 'Instrumentos', method: 'Método', fraction: 'Fracción de entrenamiento', confidence: 'Nivel de confianza', periods: 'Número de períodos', degree: 'Grado máximo', output: 'Nombre de la salida', population: 'Columna de población', value: 'Columna de valores', nominal: 'Columna nominal', index: 'Índice de precios', base: 'Base del índice', lookback: 'Ventana del pasado', returns: 'Retornos', signal: 'Señal', cost: 'Costo por cambio de posición', components: 'Componentes', clusters: 'Grupos', states: 'Estados', hidden: 'Neuronas ocultas', quantiles: 'Cuantiles', before: 'Antes', after: 'Después', prior: 'Probabilidad previa', sensitivity: 'Sensibilidad', false_positive: 'Probabilidad de falso positivo', sample_size: 'Tamaño de cada remuestra', replications: 'Número de remuestras', initial: 'Valor inicial', threshold: 'Umbral', evaluation: 'Muestra de evaluación', template: 'Plantilla registrada', note: 'Pregunta de interpretación', error: 'Error de equilibrio', bins: 'Intervalos', lags: 'Rezagos', topic: 'Tema del experimento (C01–C28)', start: 'Año inicial', end: 'Año final' }[key] ?? key}</span>{catalog[selected.type].choices?.[key] ? <select disabled={busy} value={value} onChange={event=>setParameter(key,event.target.value)}>{catalog[selected.type].choices![key].map(option=><option key={option} value={option}>{catalog[selected.type].choice_labels?.[key]?.[option]??option}</option>)}</select> : key === 'covariance' ? <select disabled={busy} value={value} onChange={e => setParameter(key, e.target.value)}><option value="HC3">Robustos · HC3</option><option value="nonrobust">Clásicos</option></select> : key === 'delimiter' ? <select disabled={busy} value={value} onChange={e => setParameter(key, e.target.value)}><option value=",">Coma (,)</option><option value=";">Punto y coma (;)</option><option value={'\t'}>Tabulación</option></select> : <input disabled={busy} type={typeof value === 'number' ? 'number' : 'text'} step="any" value={Number.isNaN(value) ? '' : value} onChange={e => setParameter(key, typeof value === 'number' ? e.target.valueAsNumber : e.target.value)} />}</label>)}
          {selected.type === 'csv' && <label className="csv-upload"><ArrowUpFromLine size={18} />Seleccionar CSV<input disabled={busy} type="file" accept=".csv,.tsv,text/csv" onChange={async e => { const file = e.target.files?.[0]; if (!file) return; if (file.size > 2_000_000) { setError('El CSV supera 2 MB.'); return; } setParameter('content', await file.text()); }} /><small>{selected.parameters.content ? 'Archivo cargado en el proyecto' : 'Datos guardados dentro del proyecto local'}</small></label>}
          {!Object.keys(selected.parameters).length && <p className="subtle">Este nodo usa las columnas numéricas de la fuente conectada.</p>}
          <section className="node-connections"><h4>CONEXIONES</h4>{connections.length ? connections.map(edge => <div className="connection-row" key={edge.id}><span>{nodeLabel(edge.source)}<span> → </span>{nodeLabel(edge.target)}</span><button type="button" disabled={busy} title={`Desconectar ${nodeLabel(edge.source)} de ${nodeLabel(edge.target)}`} aria-label={`Desconectar ${nodeLabel(edge.source)} de ${nodeLabel(edge.target)}`} onClick={() => disconnect(edge.id)}><Unplug size={14} /><span>Desconectar</span></button></div>) : <p>Este nodo no tiene conexiones.</p>}<small>Desconecta un enlace sin eliminar los módulos. Puedes usar Deshacer para recuperarlo.</small></section>
          <div className="learning-card"><div><BookOpen size={15} /><strong>Detrás del nodo</strong></div>{selected.type === 'ols' && <div className="formula">y = β₀ + β₁x + ε</div>}<p>{item.explanation}</p><span>Referencias {item.references}</span></div>
          {selectedResult?.error && <div role="alert" className="node-error"><strong>{selectedResult.error.code}</strong><p>{selectedResult.error.message}</p></div>}
          {selectedResult?.result && <details className="node-details"><summary>Ver resultado del nodo</summary><pre>{JSON.stringify(selectedResult.result, null, 2)}</pre></details>}
          <button className="delete-node" disabled={busy} onClick={() => { update({ ...project, nodes: project.nodes.filter(n => n.id !== selected.id), edges: project.edges.filter(e => e.source !== selected.id && e.target !== selected.id) }); setSelectedId(''); }}><Trash2 size={13} />Eliminar nodo</button>
        </> : <div className="inspector-empty"><Network size={28} /><p>Selecciona un nodo para explorar sus parámetros y fundamentos.</p></div>}</aside>
    </main>{managerOpen && <ProjectManager project={project} active={activeFile} onOpen={(next, file) => { update(next); setActiveFile(file ?? null); setStepIndex(0); setSelectedId(next.nodes[0]?.id ?? ''); setSelectedEdgeId(''); }} onRun={(next, file) => { update(next); setActiveFile(file ?? null); setStepIndex(0); setSelectedId(next.nodes[0]?.id ?? ''); setManagerOpen(false); void execute(next); }} onDeleted={id => setActiveFile(file => file?.id === id ? null : file)} onClose={() => setManagerOpen(false)} />}{equationOpen && <ModelEquation node={equationNode} result={equationNode ? run?.nodes[equationNode.id] : undefined} onClose={() => setEquationOpen(false)} />}<footer className="app-footer"><span><span className="tiny-dot" /> Hecho para aprender, observación a observación.</span><span>Motor Python · ejecución local · versión inicial</span></footer>
  </div>;
}
