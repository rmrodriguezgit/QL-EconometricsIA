import { useCallback, useMemo, useRef, useState } from 'react';
import { ReactFlow, Background, Controls, Handle, Position, addEdge, applyNodeChanges, applyEdgeChanges, type Node, type NodeProps, type Connection } from '@xyflow/react';
import { ArrowDownToLine, ArrowUpFromLine, Play, Plus, Search, FlaskConical, Database, ChartScatter, ChartNoAxesCombined, Sigma, BookOpen, ChevronRight, CircleCheck, RotateCcw, Undo2, Trash2, Network, CircleAlert, Braces, LoaderCircle } from 'lucide-react';
import ModelEquation from './ModelEquation';
import { catalog, download, parseProject, rpc, starter, version, type Kind, type Project, type Run, type NodeResult } from './model';

const icons = { simulate: FlaskConical, csv: Database, worldbank: Database, describe: Sigma, scatter: ChartScatter, ols: ChartNoAxesCombined };
const format = (v: unknown, digits = 3) => typeof v === 'number' ? new Intl.NumberFormat('es-MX', { maximumFractionDigits: digits }).format(v) : '—';
type CanvasNode = Node<{ kind: Kind; state?: NodeResult; index: number }, 'econometric'>;

function EconometricNode({ data, selected }: NodeProps<CanvasNode>) {
  const item = catalog[data.kind]; const Icon = icons[data.kind]; const state = data.state;
  const isSource = ['simulate', 'csv', 'worldbank'].includes(data.kind);
  const result = state?.result;
  return <div className={`flow-node ${selected ? 'selected' : ''} ${item.color}`}>
    {!isSource && <Handle type="target" position={Position.Left} id="data" aria-label="Entrada: datos" />}
    <div className="node-top"><span className={`node-icon ${item.color}`}><Icon size={17} /></span><span className="node-type">{isSource ? 'DATOS' : data.kind === 'ols' ? 'ESTIMACIÓN' : 'EXPLORACIÓN'}</span><span className="node-number">0{data.index + 1}</span></div>
    <strong>{item.label}</strong><p>{item.detail}</p>
    <div className={`node-bottom ${state?.status ?? ''}`}>
      {state?.status === 'succeeded' ? <><CircleCheck size={12} />{data.kind === 'ols' ? `R² ${format(result?.r_squared)}` : `${format(result?.n ?? result?.n_total)} observaciones`}</> : state?.status === 'failed' ? <><CircleAlert size={12} />Revisar parámetros</> : state?.status === 'skipped' ? 'Origen sin resultados' : <><span className="tiny-dot" /> Listo para conectar</>}
    </div>
    {isSource && <Handle type="source" position={Position.Right} id="data" aria-label="Salida: datos" />}
  </div>;
}
const nodeTypes = { econometric: EconometricNode };

function Scatter({ result, model }: { result: Record<string, unknown>; model?: Record<string, unknown> }) {
  const points = result.points as [number, number][];
  const xs = points.map(p => p[0]), ys = points.map(p => p[1]);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  const pad = (maxY - minY || 1) * .12;
  const x = (v: number) => 54 + (v - minX) / (maxX - minX || 1) * 405;
  const y = (v: number) => 174 - (v - (minY - pad)) / (maxY - minY + 2 * pad) * 150;
  const coefficients = model?.coefficients as { estimate: number }[] | undefined;
  const line = coefficients && model?.x === result.x && model?.y === result.y;
  return <svg className="scatter" viewBox="0 0 490 218" role="img" aria-label={`Dispersión de ${result.x} y ${result.y}, ${points.length} observaciones. Los datos también pueden exportarse en resultados JSON.`}>
    {[0, 1, 2, 3].map(i => { const v = minY + (maxY - minY) * i / 3; return <g key={i}><line x1="54" x2="459" y1={y(v)} y2={y(v)} stroke="#e8eeea" /><text x="44" y={y(v) + 4} textAnchor="end">{format(v, 0)}</text></g>; })}
    {points.map((p, i) => <circle key={i} cx={x(p[0])} cy={y(p[1])} r="2.8" fill="#259476" opacity=".65" />)}
    {line && <line x1={x(minX)} x2={x(maxX)} y1={y(coefficients[0].estimate + coefficients[1].estimate * minX)} y2={y(coefficients[0].estimate + coefficients[1].estimate * maxX)} stroke="#263e55" strokeWidth="1.8" />}
    {[0, 1, 2, 3, 4].map(i => { const v = minX + (maxX - minX) * i / 4; return <text key={i} x={x(v)} y="194" textAnchor="middle">{format(v, 0)}</text>; })}
    <text x="258" y="213" textAnchor="middle" className="axis-label">{String(result.x)}</text>
    <text transform="translate(13,100) rotate(-90)" textAnchor="middle" className="axis-label">{String(result.y)}</text>
  </svg>;
}

export default function App() {
  const [project, setProject] = useState<Project>(starter);
  const [history, setHistory] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState('model');
  const [run, setRun] = useState<Run | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [query, setQuery] = useState('');
  const [tab, setTab] = useState('Resultados');
  const [equationOpen, setEquationOpen] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const selected = project.nodes.find(n => n.id === selectedId);
  const item = selected && catalog[selected.type];
  const equationNode = selected?.type === 'ols' ? selected : project.nodes.find(node => node.type === 'ols');
  const update = useCallback((next: Project, remember = true) => {
    if (busy) return;
    if (remember) setHistory(h => [...h.slice(-29), project]);
    setProject(next); setRun(null); setError(''); setNotice('');
  }, [project, busy]);
  const nodes: CanvasNode[] = useMemo(() => project.nodes.map((node, index) => ({ id: node.id, type: 'econometric', position: node.position, selected: selectedId === node.id, data: { kind: node.type, state: run?.nodes[node.id], index } })), [project, selectedId, run]);
  const edges = useMemo(() => project.edges.map(edge => ({ ...edge, sourceHandle: edge.source_port, targetHandle: edge.target_port, type: 'smoothstep', animated: busy, style: { stroke: '#73a795', strokeWidth: 1.6 } })), [project.edges, busy]);
  const addNode = (kind: Kind) => {
    const id = crypto.randomUUID();
    update({ ...project, nodes: [...project.nodes, { id, type: kind, node_version: '1.0.0', parameters: { ...catalog[kind].defaults }, position: { x: 90 + project.nodes.length * 35, y: 80 + project.nodes.length * 40 } }] }); setSelectedId(id);
  };
  const connect = (connection: Connection) => {
    if (connection.sourceHandle !== 'data' || connection.targetHandle !== 'data' || connection.source === connection.target) return;
    if (project.edges.some(e => e.target === connection.target)) { setError('Esta entrada ya tiene una conexión. Elimínala antes de conectar otra fuente.'); return; }
    const next = addEdge(connection, edges);
    update({ ...project, edges: next.map(e => ({ id: e.id, source: e.source, target: e.target, source_port: e.sourceHandle ?? 'data', target_port: e.targetHandle ?? 'data' })) });
  };
  const setParameter = (key: string, value: string | number) => {
    if (!selected) return;
    update({ ...project, nodes: project.nodes.map(n => n.id === selected.id ? { ...n, parameters: { ...n.parameters, [key]: value } } : n) });
  };
  const execute = async () => {
    setBusy(true); setError(''); setNotice(''); setRun(null);
    try {
      const value = await rpc<Run>('run.start', { project }); setRun(value);
      if (value.status === 'failed') setError('Hay nodos que necesitan revisión. Selecciónalos para consultar el error.');
      else setNotice('Flujo ejecutado. Resultados calculados con Python.');
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo ejecutar el flujo.'); }
    finally { setBusy(false); }
  };
  const openProject = async (file?: File) => {
    if (!file) return;
    try {
      if (file.size > 3_000_000) throw new Error('El proyecto supera 3 MB.');
      const value = parseProject(await file.text());
      await rpc('project.validate', { project: value });
      update(value); setSelectedId(value.nodes[0]?.id ?? ''); setNotice('Proyecto abierto. Ejecuta para recalcular los resultados.');
    } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo abrir el proyecto.'); }
  };
  const resultOf = (kind: Kind) => {
    const node = project.nodes.find(n => n.type === kind && run?.nodes[n.id]?.status === 'succeeded');
    return node && run?.nodes[node.id]?.result;
  };
  const model = resultOf('ols'), scatter = resultOf('scatter'), summary = resultOf('describe');
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
        {['Fuentes de datos', 'Exploración', 'Modelos'].map(group => <section className="node-group" key={group}><h3>{group}</h3>{visible.filter(([, value]) => value.category === group).map(([kind, value]) => { const Icon = icons[kind as Kind]; return <button disabled={busy} className="library-node" key={kind} onClick={() => addNode(kind as Kind)} title={`Añadir ${value.label}`}><span className={`node-icon ${value.color}`}><Icon size={17} /></span><span><strong>{value.label}</strong><small>{kind === 'simulate' ? 'Empieza sin descargar datos' : kind === 'worldbank' ? 'Requiere conexión' : kind === 'ols' ? 'Mínimos cuadrados ordinarios' : kind === 'csv' ? 'Hasta 2 MB · CSV' : 'Explora tus observaciones'}</small></span><Plus size={14} /></button>; })}</section>)}
        <div className="library-note"><span className="note-symbol">↗</span><strong>Aprende conectando</strong><p>Conecta la salida de una fuente con la entrada de un modelo o una visualización.</p><span>6 nodos disponibles · 28 módulos en el plan</span></div>
      </aside>
      <section className="center-pane">
        <div className="canvas-toolbar"><div className="project-title"><span className="project-dot" /><input aria-label="Nombre del proyecto" maxLength={120} disabled={busy} value={project.title} onChange={e => update({ ...project, title: e.target.value })} /><span className="draft-tag">LOCAL</span></div><div className="toolbar-buttons">
          {equationNode && <button className="equation-button" title="Ecuación del modelo" aria-label="Ecuación del modelo" onClick={() => setEquationOpen(true)}><Sigma size={16} /><span>Ecuación</span></button>}
          <button className="icon-button" title="Deshacer" aria-label="Deshacer" disabled={!history.length || busy} onClick={() => { const previous = history[history.length - 1]; setHistory(history.slice(0, -1)); setProject(previous); setRun(null); }}><Undo2 size={16} /></button>
          <button className="icon-button" title="Abrir proyecto" aria-label="Abrir proyecto" disabled={busy} onClick={() => fileRef.current?.click()}><ArrowUpFromLine size={16} /></button>
          <button className="icon-button" title="Guardar proyecto" aria-label="Guardar proyecto" onClick={() => { download('quantlabs-proyecto.json', project); setNotice('Proyecto descargado. Incluye el contenido de los CSV importados.'); }}><ArrowDownToLine size={16} /></button>
          <button className="run-button" disabled={busy} onClick={execute}>{busy ? <LoaderCircle className="spin" size={15} /> : <Play size={14} fill="currentColor" />}{busy ? 'Calculando…' : 'Ejecutar flujo'}</button>
        </div></div>
        <input ref={fileRef} type="file" accept=".json" hidden onChange={e => { void openProject(e.target.files?.[0]); e.target.value = ''; }} />
        <div className="canvas-area"><div className="canvas-breadcrumb"><Network size={13} /> Espacio de trabajo <ChevronRight size={12} /> <strong>{project.title || 'Sin título'}</strong></div><ReactFlow<CanvasNode> nodes={nodes} edges={edges} nodeTypes={nodeTypes} onConnect={connect} nodesDraggable={!busy} nodesConnectable={!busy} elementsSelectable={!busy}
          onNodeClick={(_, node) => setSelectedId(node.id)} onPaneClick={() => setSelectedId('')}
          onNodeDragStart={() => setHistory(h => [...h.slice(-29), project])}
          onNodesChange={changes => { if (busy) return; const changed = applyNodeChanges(changes, nodes); if (changes.some(c => c.type === 'position')) setProject(p => ({ ...p, nodes: p.nodes.map(n => ({ ...n, position: changed.find(c => c.id === n.id)?.position ?? n.position })) })); const removed = changes.filter(c => c.type === 'remove').map(c => c.id); if (removed.length) update({ ...project, nodes: project.nodes.filter(n => !removed.includes(n.id)), edges: project.edges.filter(e => !removed.includes(e.source) && !removed.includes(e.target)) }); }}
          onEdgesChange={changes => { if (busy) return; if (changes.some(c => c.type === 'remove')) { const changed = applyEdgeChanges(changes, edges); update({ ...project, edges: project.edges.filter(e => changed.some(c => c.id === e.id)) }); } }}
          fitView fitViewOptions={{ padding: .25, maxZoom: 1 }} minZoom={.3} maxZoom={1.6} deleteKeyCode={['Backspace', 'Delete']}><Background gap={22} size={1} color="#cdd8d0" /><Controls showInteractive={false} /></ReactFlow>
          <div className="canvas-footer"><span>{project.nodes.length} nodos <span>·</span> {project.edges.length} conexiones</span><button disabled={busy} onClick={() => { update(starter()); setSelectedId('model'); }}><RotateCcw size={12} /> Restaurar ejemplo</button></div>
        </div>
        <section className="results"><div className="results-header"><div className="result-tabs">{['Resultados', 'Descriptivos', 'Trazabilidad'].map(name => <button key={name} className={tab === name ? 'active' : ''} onClick={() => setTab(name)}>{name}</button>)}</div>{run && <button className="text-button" onClick={() => download('quantlabs-resultados.json', run)}><ArrowDownToLine size={13} /> Exportar</button>}</div>
          <div role={error ? 'alert' : 'status'} className={`status-message ${error ? 'error' : ''}`}>{error ? <><CircleAlert size={14} />{error}</> : notice ? <><CircleCheck size={14} />{notice}</> : <><span className="tiny-dot" />Ejecuta el flujo para calcular resultados con tu muestra.</>}</div>
          {!run ? <div className="empty-results"><span className="empty-icon"><ChartNoAxesCombined size={25} /></span><strong>Tu primera pregunta empieza aquí</strong><p>El ejemplo ya está conectado. Ejecuta el flujo para explorar<br />cómo se relacionan el ingreso y el consumo.</p><button className="text-button" onClick={execute} disabled={busy}>{busy ? 'Calculando…' : 'Ejecutar mi primer experimento'} <ChevronRight size={14} /></button></div> : tab === 'Trazabilidad' ? <div className="manifest"><p>Versión, dependencias, semilla, consulta y huellas de datos de esta ejecución.</p><pre>{JSON.stringify(run.manifest, null, 2)}</pre></div> : tab === 'Descriptivos' ? summary ? <div className="table-wrap"><table><thead><tr><th>Variable</th><th>n</th><th>Faltantes</th><th>Media</th><th>Mediana</th><th>Desv. estándar</th><th>Mínimo</th><th>Máximo</th></tr></thead><tbody>{(summary.rows as Record<string, unknown>[]).map(row => <tr key={String(row.variable)}><td>{String(row.variable)}</td>{['n', 'missing', 'mean', 'median', 'std', 'min', 'max'].map(k => <td key={k}>{format(row[k])}</td>)}</tr>)}</tbody></table><p className="result-footnote">{String(summary.note)}</p></div> : <div className="empty-small">Añade y conecta un nodo de descriptivos para ver su tabla.</div> : <div className="result-grid"><div className="model-result">{model && coefficients ? <><div className="result-title"><h3>Regresión lineal simple</h3><span>OLS · {String(model.covariance)}</span></div><div className="metrics"><div><span>R²</span><strong>{format(model.r_squared)}</strong></div><div><span>Observaciones</span><strong>{format(model.n, 0)}</strong></div><div><span>Filas excluidas</span><strong>{format(model.dropped, 0)}</strong></div></div><table><thead><tr><th>Coeficiente</th><th>Estimación</th><th>Error est.</th><th>p-valor</th></tr></thead><tbody>{coefficients.map(c => <tr key={c.term}><td>{c.term === 'const' ? 'Intercepto' : c.term}</td><td>{format(c.estimate)}</td><td>{format(c.std_error)}</td><td>{c.p_value < .001 ? '< 0.001' : format(c.p_value)}</td></tr>)}</tbody></table><p className="result-footnote">Asociación no implica causalidad. IC 95 % y residuos disponibles al exportar.</p></> : <div className="empty-small">Añade OLS para estimar una relación.<br />Selecciona cualquier nodo para inspeccionar su resultado.</div>}</div><div className="chart-result"><div className="result-title"><h3>La relación en los datos</h3>{scatter && <span>{format(scatter.n, 0)} puntos · {format(scatter.dropped, 0)} excluidos</span>}</div>{scatter ? <Scatter result={scatter} model={model || undefined} /> : <div className="empty-small">Conecta un nodo de dispersión para ver el gráfico.</div>}</div></div>}
        </section>
      </section>
      <aside className="inspector"><div className="section-heading"><h2>Inspector</h2><span><Braces size={15} /></span></div>{selected && item ? <><div className="inspector-title"><span className={`node-icon ${item.color}`}>{(() => { const Icon = icons[selected.type]; return <Icon size={20} />; })()}</span><div><h3>{item.label}</h3><p>Configuración del nodo</p></div></div><div className="inspector-divider" /><h4>PARÁMETROS</h4>
          {Object.entries(selected.parameters).filter(([key]) => key !== 'content').map(([key, value]) => <label className="field" key={`${selected.id}-${key}`}><span>{{ n: 'Observaciones', seed: 'Semilla aleatoria', intercept: 'Intercepto (β₀)', slope: 'Pendiente (β₁)', noise: 'Desviación del ruido', x: 'Variable explicativa (x)', y: 'Variable respuesta (y)', covariance: 'Errores estándar', delimiter: 'Separador CSV', country: 'País (ISO 3)', indicator: 'Código de indicador', start: 'Año inicial', end: 'Año final' }[key] ?? key}</span>{key === 'covariance' ? <select disabled={busy} value={value} onChange={e => setParameter(key, e.target.value)}><option value="HC3">Robustos · HC3</option><option value="nonrobust">Clásicos</option></select> : key === 'delimiter' ? <select disabled={busy} value={value} onChange={e => setParameter(key, e.target.value)}><option value=",">Coma (,)</option><option value=";">Punto y coma (;)</option><option value={'\t'}>Tabulación</option></select> : <input disabled={busy} type={typeof value === 'number' ? 'number' : 'text'} step="any" value={Number.isNaN(value) ? '' : value} onChange={e => setParameter(key, typeof value === 'number' ? e.target.valueAsNumber : e.target.value)} />}</label>)}
          {selected.type === 'csv' && <label className="csv-upload"><ArrowUpFromLine size={18} />Seleccionar CSV<input disabled={busy} type="file" accept=".csv,.tsv,text/csv" onChange={async e => { const file = e.target.files?.[0]; if (!file) return; if (file.size > 2_000_000) { setError('El CSV supera 2 MB.'); return; } setParameter('content', await file.text()); }} /><small>{selected.parameters.content ? 'Archivo cargado en el proyecto' : 'Datos guardados dentro del proyecto local'}</small></label>}
          {!Object.keys(selected.parameters).length && <p className="subtle">Este nodo usa las columnas numéricas de la fuente conectada.</p>}
          <div className="learning-card"><div><BookOpen size={15} /><strong>Detrás del nodo</strong></div>{selected.type === 'ols' && <div className="formula">y = β₀ + β₁x + ε</div>}<p>{item.explanation}</p><span>Referencias {item.references}</span></div>
          {selectedResult?.error && <div role="alert" className="node-error"><strong>{selectedResult.error.code}</strong><p>{selectedResult.error.message}</p></div>}
          {selectedResult?.result && <details className="node-details"><summary>Ver resultado del nodo</summary><pre>{JSON.stringify(selectedResult.result, null, 2)}</pre></details>}
          <button className="delete-node" disabled={busy} onClick={() => { update({ ...project, nodes: project.nodes.filter(n => n.id !== selected.id), edges: project.edges.filter(e => e.source !== selected.id && e.target !== selected.id) }); setSelectedId(''); }}><Trash2 size={13} />Eliminar nodo</button>
        </> : <div className="inspector-empty"><Network size={28} /><p>Selecciona un nodo para explorar sus parámetros y fundamentos.</p></div>}</aside>
    </main>{equationOpen && <ModelEquation node={equationNode} result={equationNode ? run?.nodes[equationNode.id] : undefined} onClose={() => setEquationOpen(false)} />}<footer className="app-footer"><span><span className="tiny-dot" /> Hecho para aprender, observación a observación.</span><span>Motor Python · ejecución local · versión inicial</span></footer>
  </div>;
}
