import { useEffect, useRef, useState } from 'react';
import { Brain, CircleAlert, CircleCheck, LoaderCircle, Play, Wrench, X } from 'lucide-react';
import { rpc, type Project } from './model';

type Change = { node_id: string; label: string; field: string; before: unknown; after: unknown; reason: string };
export type RepairResult = { project: Project; changes: Change[]; unresolved: { node_id: string | null; label: string; message: string }[]; status: string; nodes: Record<string, string>; executed: boolean };

const show = (value: unknown) => value === null || value === undefined || value === '' ? '—' : String(value);

/** Cerebro IA repara el flujo del canvas: propone cambios comprobados y el usuario decide si aplicarlos. */
export default function RepairPanel({ project, onApply, onClose }: { project: Project; onApply: (project: Project, run: boolean) => void; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [result, setResult] = useState<RepairResult | null>(null);
  const [error, setError] = useState('');
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    dialog.current?.showModal();
    const started = Date.now(), timer = window.setInterval(() => setElapsed(Math.round((Date.now() - started) / 1000)), 1000);
    rpc<RepairResult>('brain.repair', { project, allow_network: true })
      .then(setResult).catch(reason => setError(reason instanceof Error ? reason.message : String(reason))).finally(() => window.clearInterval(timer));
    return () => window.clearInterval(timer);
  }, []);
  const pending = !result && !error;
  const fixed = result?.status === 'succeeded';
  return <dialog ref={dialog} className="manager-dialog repair-dialog" aria-labelledby="repair-title" onCancel={event => { event.preventDefault(); onClose(); }}>
    <header className="manager-header"><span className="manager-emblem brain-emblem"><Wrench size={20} /></span><div><span className="eyebrow">CEREBRO IA · REPARAR FLUJO</span><h2 id="repair-title">{pending ? 'Revisando el flujo del canvas…' : fixed ? 'Flujo reparado' : result ? 'Reparación parcial' : 'No se pudo reparar'}</h2></div>
      <button className="icon-button" aria-label="Cerrar reparación" onClick={onClose}><X size={20} /></button></header>
    <div className="repair-body">
      {pending && <p className="repair-pending"><LoaderCircle className="spin" size={16} /> Ejecutando el flujo, localizando errores y probando correcciones… {elapsed}s</p>}
      {error && <p className="brain-warning"><CircleAlert size={13} /> {error}</p>}
      {result && <>
        <p className="repair-intro">Se trabajó sobre una copia de tu flujo: mismos nodos, sin crear un blueprint nuevo. {result.changes.length ? `${result.changes.length} cambio${result.changes.length === 1 ? '' : 's'} propuesto${result.changes.length === 1 ? '' : 's'}` : 'No hizo falta cambiar parámetros'}{result.executed ? `; tras aplicarlos, ${Object.values(result.nodes).filter(s => s === 'succeeded').length} de ${Object.keys(result.nodes).length} nodos se ejecutan bien.` : '.'}</p>
        {!!result.changes.length && <table className="repair-table"><thead><tr><th>Nodo</th><th>Campo</th><th>Antes</th><th>Después</th><th>Motivo</th></tr></thead>
          <tbody>{result.changes.map((change, i) => <tr key={i}><td>{change.label}</td><td><code>{change.field}</code></td><td>{show(change.before)}</td><td><strong>{show(change.after)}</strong></td><td>{change.reason}</td></tr>)}</tbody></table>}
        {!!result.unresolved.length && <div className="repair-unresolved"><h4><CircleAlert size={13} /> Necesita tu decisión</h4>{result.unresolved.map((item, i) => <p key={i}><strong>{item.label}</strong>: {item.message}</p>)}</div>}
        {fixed && <p className="repair-ok"><CircleCheck size={13} /> Todos los nodos se ejecutan sin error con estos cambios. Revisa que las columnas elegidas sean las que quieres analizar.</p>}
      </>}
    </div>
    <footer className="repair-actions">
      <button className="manager-secondary" onClick={onClose}>Cancelar</button>
      <button className="manager-secondary" disabled={!result?.changes.length} onClick={() => result && onApply(result.project, false)}><Brain size={14} />Aplicar cambios</button>
      <button className="manager-primary" disabled={!result?.changes.length} onClick={() => result && onApply(result.project, true)}><Play size={14} />Aplicar y ejecutar</button>
    </footer>
  </dialog>;
}
