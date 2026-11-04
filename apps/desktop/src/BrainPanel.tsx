import { useEffect, useRef, useState } from 'react';
import { Brain, CircleAlert, CircleCheck, FolderOpen, LoaderCircle, Play, ThumbsDown, ThumbsUp, Wrench, X } from 'lucide-react';
import { catalog, parseProject, rpc, type Kind, type Project } from './model';

type Gap = { id: string; name: string; status: string; purpose: string; module?: string; count: number; inputs: Record<string, string>; outputs: Record<string, string> };
type BrainStatus = { brain_version: string; tools: number; default_engine: string; memory: number; pending_gaps: number; ollama: { reachable: boolean; ready: boolean; model: string | null; models: string[] } };
type Verification = { executed: boolean; status?: string; reason?: string; nodes: Record<string, { status: string; error?: string }>; repairs?: { node_id: string }[] };
export type BrainResult = { blueprint_id: string; engine: 'ollama' | 'rules'; model: string | null; llm: { seconds?: number }; fallback_reason: string | null; project: Project; notes: string[]; dropped: { tool: string; reason: string }[]; gaps: Gap[]; verification: Verification; trace: { retrieved_tools: string[]; examples: { id: string; title: string; score: number }[] } };
type HistoryItem = { id: string; prompt: string; title: string; engine: string; created_at: string; feedback: string | null; node_types: string[] };

const EXAMPLES = [
  'Estima cómo el ingreso explica el consumo con MCO robusto, revisa heterocedasticidad y normalidad de residuos',
  'Analiza la inflación de México 2000-2023 del Banco Mundial: gráfico temporal, raíz unitaria y ARIMA',
  'Con wage1 de Wooldridge estima una regresión múltiple del salario y compara con una regresión cuantílica',
  'Agrupa observaciones con k-means, elige el número de grupos y evalúa la silueta',
  'Contrasta un cambio estructural con Chow y calcula intervalos de predicción',
];
const label = (kind: string) => (catalog as Record<string, { label: string }>)[kind]?.label ?? kind;

export default function BrainPanel({ onOpen, onRun, onClose }: { onOpen: (project: Project) => void; onRun: (project: Project) => void; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [prompt, setPrompt] = useState('');
  const [engine, setEngine] = useState<'auto' | 'ollama' | 'rules'>('auto');
  const [network, setNetwork] = useState(false);
  const [status, setStatus] = useState<BrainStatus | null>(null);
  const [result, setResult] = useState<BrainResult | null>(null);
  const [view, setView] = useState<'plan' | 'gaps' | 'history'>('plan');
  const [gaps, setGaps] = useState<Gap[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [elapsed, setElapsed] = useState(0);
  const [rated, setRated] = useState<'up' | 'down' | null>(null);
  useEffect(() => { const d = dialog.current; d?.showModal(); return () => d?.close(); }, []);
  useEffect(() => { rpc<BrainStatus>('brain.status').then(setStatus).catch(reason => setError(String(reason instanceof Error ? reason.message : reason))); }, []);
  useEffect(() => {
    if (view === 'gaps') void rpc<{ items: Gap[] }>('brain.gaps').then(value => setGaps(value.items)).catch(() => setGaps([]));
    if (view === 'history') void rpc<{ items: HistoryItem[] }>('brain.history', { limit: 30 }).then(value => setHistory(value.items)).catch(() => setHistory([]));
  }, [view, result]);
  useEffect(() => { if (!pending) return; const started = Date.now(); const timer = setInterval(() => setElapsed(Math.round((Date.now() - started) / 1000)), 500); return () => clearInterval(timer); }, [pending]);
  const close = () => { if (!pending) onClose(); };
  async function build() {
    setPending(true); setError(''); setElapsed(0);
    try {
      const value = await rpc<BrainResult>('brain.plan', { prompt, engine, allow_network: network });
      parseProject(JSON.stringify(value.project)); // mismas comprobaciones que un JSON importado
      setResult(value); setRated(null); setView('plan');
    } catch (reason) { setError(reason instanceof Error ? reason.message : String(reason)); }
    finally { setPending(false); }
  }
  async function feedback(value: 'up' | 'down') {
    if (!result) return;
    try { await rpc('brain.feedback', { id: result.blueprint_id, value }); setError(''); setRated(value); } catch (reason) { setError(String(reason)); }
  }
  async function setGapStatus(id: string, next: string) {
    try { await rpc('brain.gaps.update', { id, status: next }); const value = await rpc<{ items: Gap[] }>('brain.gaps'); setGaps(value.items); } catch (reason) { setError(String(reason)); }
  }
  const ollama = status?.ollama;
  const verification = result?.verification;
  return <dialog ref={dialog} className="manager-dialog brain-dialog" aria-labelledby="brain-title" onCancel={event => { event.preventDefault(); close(); }}>
    <header className="manager-header"><span className="manager-emblem brain-emblem"><Brain size={22} /></span><div><span className="eyebrow">SEGUNDO CEREBRO · IA LOCAL</span><h2 id="brain-title">Del enunciado al blueprint</h2></div>
      <span className={`brain-engine ${!status ? '' : ollama?.ready ? 'ok' : 'off'}`}>{!status ? 'Consultando motor…' : ollama?.ready ? `Qwen local · ${ollama.model}` : ollama?.reachable ? 'Ollama sin modelo · reglas' : 'Ollama apagado · reglas'}</span>
      <button className="icon-button" aria-label="Cerrar segundo cerebro" onClick={close} disabled={pending}><X size={20} /></button></header>
    <div className="manager-layout"><aside className="manager-sidebar">
      <nav>{([['plan', 'Blueprint'], ['gaps', 'Herramientas faltantes'], ['history', 'Memoria']] as const).map(([id, text]) => <button key={id} className={view === id ? 'active' : ''} onClick={() => setView(id)}>{text}{id === 'gaps' && status ? <span>{status.pending_gaps}</span> : id === 'history' && status ? <span>{status.memory}</span> : null}</button>)}</nav>
      <label className="brain-label" htmlFor="brain-prompt">¿Qué quieres analizar?</label>
      <textarea id="brain-prompt" className="brain-prompt" maxLength={4000} disabled={pending} value={prompt} placeholder="Describe datos, preguntas y técnicas: p. ej. «regresión del consumo con errores robustos y diagnóstico»." onChange={event => setPrompt(event.target.value)} onKeyDown={event => { if ((event.metaKey || event.ctrlKey) && event.key === 'Enter' && prompt.trim().length >= 3) void build(); }} />
      <div className="brain-options">
        <select aria-label="Motor del cerebro" value={engine} disabled={pending} onChange={event => setEngine(event.target.value as typeof engine)}><option value="auto">Automático (Qwen → reglas)</option><option value="ollama">Solo Qwen local</option><option value="rules">Solo reglas deterministas</option></select>
        <label className="brain-check"><input type="checkbox" checked={network} disabled={pending} onChange={event => setNetwork(event.target.checked)} />Verificar con Banco Mundial (red)</label>
      </div>
      <button className="manager-primary brain-build" disabled={pending || prompt.trim().length < 3} onClick={() => void build()}>{pending ? <><LoaderCircle className="spin" size={14} />Construyendo… {elapsed}s</> : <><Brain size={14} />Construir blueprint</>}</button>
      <div className="manager-list brain-examples">{EXAMPLES.map(text => <button key={text} className="example-entry" disabled={pending} onClick={() => setPrompt(text)}><span>EJEMPLO</span><strong>{text}</strong></button>)}</div>
      <div className="manager-local-note">El cerebro solo usa herramientas registradas y valida el grafo con el motor. Lo que falta queda como ficha pendiente; nunca se ejecuta código generado.</div>
    </aside><section className="manager-main brain-main">
      {view === 'plan' && (!result ? <div className="brain-empty"><Brain size={34} /><h3>Escribe un enunciado y construye su blueprint</h3><p>El cerebro recupera herramientas y recorridos similares, planifica con Qwen (o reglas si no está disponible), conecta los puertos por tipo, ejecuta el flujo para reparar columnas y te entrega una guía paso a paso.</p></div> : <div className="brain-result">
        <div className="brain-summary"><div><span className="eyebrow">{result.engine === 'ollama' ? `QWEN · ${result.model} · ${result.llm.seconds ?? '?'} s` : 'REGLAS DETERMINISTAS'}</span><h3>{result.project.title}</h3><p>{result.project.lesson?.objective}</p></div>
          <div className="brain-actions"><button className="manager-secondary" onClick={() => onOpen(result.project)}><FolderOpen size={14} />Abrir en canvas</button><button className="manager-primary" onClick={() => onRun(result.project)}><Play size={14} />Abrir y ejecutar</button></div></div>
        {result.notes.filter(note => note.includes('se conectó a')).map(note => <p key={note} className="brain-warning"><CircleAlert size={13} /> {note}</p>)}
        {result.fallback_reason && <p className="brain-warning"><CircleAlert size={13} /> Respaldo con reglas: {result.fallback_reason}</p>}
        <p className={`brain-verify ${verification?.executed ? verification.status : 'skip'}`}>{verification?.executed ? <><CircleCheck size={13} /> Verificado ejecutando el flujo: {Object.values(verification.nodes).filter(n => n.status === 'succeeded').length}/{Object.keys(verification.nodes).length} nodos correctos{verification.repairs?.length ? ` · ${verification.repairs.length} columnas reparadas` : ''}.</> : <><CircleAlert size={13} /> {verification?.reason}</>}</p>
        <ol className="brain-steps">{result.project.nodes.map((node, index) => { const state = verification?.nodes[node.id]; const step = result.project.lesson?.steps.find(item => item.node_id === node.id); return <li key={node.id} className={state?.status ?? ''}><span className="brain-step-index">{index + 1}</span><div><strong>{label(node.type as Kind)} <code>{node.type}</code></strong><p>{step?.instruction}</p>{state?.error && <small className="brain-error">{state.error}</small>}<small>{Object.entries(node.parameters).filter(([key]) => key !== 'content').map(([key, value]) => `${key}=${value}`).join(' · ') || 'Sin parámetros'}</small></div></li>; })}</ol>
        {!!result.gaps.length && <div className="brain-gaps"><h4><Wrench size={13} /> Herramientas que faltan para responder del todo</h4>{result.gaps.map(gap => <p key={gap.id}><strong>{gap.name}</strong> · {gap.status === 'implemented' ? 'ya disponible' : 'ficha pendiente'}{gap.purpose ? ` — ${gap.purpose}` : ''}</p>)}</div>}
        {!!result.dropped.length && <details className="brain-details"><summary>Pasos descartados ({result.dropped.length})</summary>{result.dropped.map((item, i) => <p key={i}><code>{String(item.tool)}</code> {item.reason}</p>)}</details>}
        <details className="brain-details"><summary>Trazabilidad: recuperación y notas</summary><p>Herramientas recuperadas: {result.trace.retrieved_tools.join(', ')}</p><p>Recorridos similares: {result.trace.examples.map(item => `${item.id} ${item.title}`).join(' · ') || '—'}</p>{result.notes.map((note, i) => <p key={i}>{note}</p>)}</details>
        <div className="brain-feedback"><span>¿El blueprint es útil? Las valoraciones positivas alimentan la memoria.</span><button className={`icon-button ${rated === 'up' ? 'active' : ''}`} aria-label="Útil" aria-pressed={rated === 'up'} onClick={() => void feedback('up')}><ThumbsUp size={15} /></button><button className={`icon-button ${rated === 'down' ? 'active' : ''}`} aria-label="No útil" aria-pressed={rated === 'down'} onClick={() => void feedback('down')}><ThumbsDown size={15} /></button></div>
      </div>)}
      {view === 'gaps' && <div className="brain-result"><h3>Herramientas faltantes</h3><p className="brain-muted">Fichas creadas cuando un enunciado pide un análisis que el catálogo aún no cubre. Se implementan como nodos reales con pruebas, siguiendo docs/CEREBRO.md.</p>{gaps.map(gap => <article key={gap.id} className={`audit-check ${gap.status === 'implemented' ? '' : 'pending'}`}><span>{gap.status === 'implemented' ? '✓' : '○'}</span><div><h4>{gap.name} <code>{gap.id}</code></h4><p>{gap.purpose}</p><p>{Object.entries(gap.inputs).map(([k, v]) => `${k}:${v}`).join(', ') || '—'} → {Object.entries(gap.outputs).map(([k, v]) => `${k}:${v}`).join(', ') || '—'} · {gap.count} solicitudes{gap.module ? ` · ${gap.module}` : ''}</p><small>{gap.status}</small>{gap.status !== 'implemented' && <div className="brain-gap-actions">{['pending', 'planned', 'rejected'].map(next => <button key={next} className="manager-secondary" disabled={gap.status === next} onClick={() => void setGapStatus(gap.id, next)}>{{ pending: 'Pendiente', planned: 'Planificada', rejected: 'Descartar' }[next]}</button>)}</div>}</div></article>)}{!gaps.length && <p className="brain-muted">No hay fichas todavía.</p>}</div>}
      {view === 'history' && <div className="brain-result"><h3>Memoria del cerebro</h3>{history.map(item => <article key={item.id} className="brain-history"><span>{new Date(item.created_at).toLocaleString('es-MX')} · {item.engine}{item.feedback ? ` · ${item.feedback === 'up' ? '👍' : '👎'}` : ''}</span><strong>{item.title}</strong><small>{item.node_types.join(' → ')}</small><button className="manager-secondary" disabled={pending} onClick={() => { setPrompt(item.prompt); setView('plan'); }}>Reutilizar enunciado</button></article>)}{!history.length && <p className="brain-muted">Aún no hay blueprints en memoria.</p>}</div>}
      <div className={`manager-status ${error ? 'error' : ''}`} role={error ? 'alert' : 'status'}>{pending ? 'El modelo local puede tardar hasta un par de minutos la primera vez.' : error || (status ? `Cerebro ${status.brain_version} · ${status.tools} herramientas disponibles.` : 'Consultando el estado del cerebro…')}</div>
    </section></div>
  </dialog>;
}
