import { useState } from 'react';
import { AlertTriangle, ListChecks, Loader2, RefreshCw, Sparkles, X } from 'lucide-react';
import { rpc, type Kind } from './model';

export type Interpretation = {
  engine: 'ollama' | 'rules'; model: string | null; fallback_reason: string | null; label: string; seconds: number | null;
  summary: string; findings: string[]; cautions: string[]; next_steps: string[]; unverified: string[];
  base: { summary: string; findings: string[]; cautions: string[]; next_steps: string[] } | null;
};

// Solo viaja lo que lee la interpretación: escalares, métricas, tablas y avisos. Filas y puntos se acotan.
const KEEP = new Set(['metrics', 'tables', 'coefficients', 'rows', 'limitations', 'warnings', 'columns', 'numeric_columns', 'scenario_info']);
const MAX_ROWS = 5000;
export function compactResult(result: Record<string, unknown>) {
  const out: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(result)) {
    if (value === null || ['string', 'number', 'boolean'].includes(typeof value) || KEEP.has(key)) out[key] = value;
    else if ((key === 'records' || key === 'points') && Array.isArray(value)) out[key] = value.slice(0, MAX_ROWS);
  }
  return out;
}

// Las interpretaciones se recuerdan por objeto de resultado: una nueva ejecución produce resultados nuevos y las invalida.
const cache = new WeakMap<object, Interpretation>();

function Lists({ value }: { value: Pick<Interpretation, 'summary' | 'findings' | 'cautions' | 'next_steps'> }) {
  return <>
    <p className="interpret-summary">{value.summary}</p>
    {value.findings.length > 0 && <section><h4>Qué dicen los resultados</h4><ul>{value.findings.map(text => <li key={text}>{text}</li>)}</ul></section>}
    {value.cautions.length > 0 && <section className="interpret-cautions"><h4>Cautelas y supuestos</h4><ul>{value.cautions.map(text => <li key={text}>{text}</li>)}</ul></section>}
    {value.next_steps.length > 0 && <section><h4>Siguiente paso sugerido</h4><ul>{value.next_steps.map(text => <li key={text}>{text}</li>)}</ul></section>}
  </>;
}

/** Botón «Explicar este resultado»: pide al agente (IA local con Ollama, o reglas si no está) la lectura del resultado del nodo. */
export default function InterpretPanel({ nodeType, parameters, result }: { nodeType: Kind; parameters: Record<string, unknown>; result: Record<string, unknown> }) {
  const [value, setValue] = useState<Interpretation | undefined>(() => cache.get(result));
  const [owner, setOwner] = useState<object>(result);
  const [open, setOpen] = useState(() => cache.has(result));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [showBase, setShowBase] = useState(false);
  if (owner !== result) { setOwner(result); setValue(cache.get(result)); setOpen(cache.has(result)); setError(''); setShowBase(false); }

  const ask = async (engine: 'auto' | 'rules' = 'auto') => {
    setBusy(true); setError(''); setOpen(true);
    try {
      const reading = await rpc<Interpretation>('brain.interpret', { node_type: nodeType, parameters, result: compactResult(result), engine });
      cache.set(result, reading); setValue(reading); setShowBase(false);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally { setBusy(false); }
  };

  if (!open) return <div className="interpret-bar"><button className="interpret-button" disabled={busy} onClick={() => value ? setOpen(true) : void ask()}><Sparkles size={13} />Explicar este resultado</button></div>;
  return <section className="interpret-panel" aria-live="polite" aria-busy={busy}>
    <header>
      <strong><Sparkles size={13} />Explicación del resultado</strong>
      {value && !busy && <span className={`interpret-engine ${showBase ? 'rules' : value.engine}`}>{value.engine === 'ollama' && !showBase ? `IA local · ${value.model} · ${value.seconds} s` : 'Lectura por reglas'}</span>}
      <span className="interpret-actions">
        <button disabled={busy} onClick={() => void ask()} title="Volver a explicar"><RefreshCw size={12} />Otra vez</button>
        {value?.engine === 'ollama' && value.base && <button onClick={() => setShowBase(!showBase)} title="Comparar con la lectura determinista"><ListChecks size={12} />{showBase ? 'Ver IA' : 'Ver reglas'}</button>}
        <button aria-label="Cerrar explicación" onClick={() => setOpen(false)}><X size={12} /></button>
      </span>
    </header>
    {busy ? <p className="interpret-loading"><Loader2 size={14} className="spin" />Analizando el resultado… con la IA local puede tardar unos segundos.</p>
      : error ? <p className="axis-warning">{error} <button className="text-button" onClick={() => void ask('rules')}>Usar lectura por reglas</button></p>
      : value ? <>
        {value.fallback_reason && <p className="interpret-note">IA local no disponible ({value.fallback_reason}). Se muestra la lectura por reglas.</p>}
        {value.unverified.length > 0 && !showBase && <p className="interpret-warning"><AlertTriangle size={12} />Cifras que no aparecen en el resultado: {value.unverified.join(', ')}. Compruébalas antes de usarlas.</p>}
        <Lists value={showBase && value.base ? value.base : value} />
        <p className="result-footnote">{value.engine === 'ollama' && !showBase ? 'Redactado por un modelo local a partir de las métricas del resultado (no de las filas de datos). Puede equivocarse: contrástalo con «Ver reglas».' : 'Lectura determinista de métricas, p-valores y coeficientes con α del nodo (0.05 si no tiene).'}</p>
      </> : null}
  </section>;
}
