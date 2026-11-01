import { useEffect, useRef, useState } from 'react';
import { Check, ChevronDown, ChevronLeft, ChevronRight, LoaderCircle, Search } from 'lucide-react';
import { rpc } from './model';

type Indicator = { id: string; name: string; source: string; source_name: string; unit: string };
type CatalogPage = { items: Indicator[]; total: number; catalog_total: number; page: number; pages: number; retrieved_at: string; stale: boolean };

export default function IndicatorPicker({ value, source, disabled, onChange }: { value: string; source: number; disabled: boolean; onChange: (indicator: string, source: number) => void }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [data, setData] = useState<CatalogPage | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const [choice, setChoice] = useState<Indicator | null>(null);
  const container = useRef<HTMLDivElement>(null);
  const search = useRef<HTMLInputElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const listId = 'worldbank-indicator-options';
  useEffect(() => {
    if (!open) return;
    search.current?.focus();
    const close = (event: PointerEvent) => { if (!container.current?.contains(event.target as globalThis.Node)) setOpen(false); };
    document.addEventListener('pointerdown', close);
    return () => document.removeEventListener('pointerdown', close);
  }, [open]);
  useEffect(() => {
    if (!open) return;
    let active = true;
    setLoading(true); setError(''); setData(null);
    const timer = window.setTimeout(() => {
      rpc<CatalogPage>('worldbank.indicators', { query, page }).then(result => {
        if (active) { setData(result); const current = result.items.find(item => item.id === value && Number(item.source) === source); if (current) setChoice(current); }
      }).catch(reason => { if (active) setError(reason instanceof Error ? reason.message : 'No se pudo cargar el catálogo.'); })
        .finally(() => { if (active) setLoading(false); });
    }, 250);
    return () => { active = false; clearTimeout(timer); };
  }, [open, query, page, retry, value, source]);
  const choose = (item: Indicator) => { setChoice(item); onChange(item.id, Number(item.source)); setOpen(false); trigger.current?.focus(); };
  const current = choice?.id === value && Number(choice.source) === source ? choice : null;
  return <div className="indicator-picker" ref={container} onKeyDown={event => {
    if (event.key === 'Escape') { event.stopPropagation(); setOpen(false); trigger.current?.focus(); }
    if (open && ['ArrowDown', 'ArrowUp'].includes(event.key)) {
      event.preventDefault();
      const options = [...(container.current?.querySelectorAll<HTMLButtonElement>('[role="option"]') ?? [])];
      const index = options.findIndex(option => option === document.activeElement);
      const next = event.key === 'ArrowDown' ? Math.min(index + 1, options.length - 1) : Math.max(index - 1, 0);
      options[next]?.focus();
    }
  }}>
    <label className="indicator-label" id="indicator-label">Código de indicador</label>
    <button ref={trigger} type="button" role="combobox" aria-labelledby="indicator-label" aria-haspopup="listbox" aria-expanded={open} aria-controls={open ? listId : undefined} disabled={disabled} className="indicator-trigger" onClick={() => setOpen(!open)}><span><strong>{value}</strong><small>{current?.name ?? 'Buscar en el catálogo del Banco Mundial'}</small></span><ChevronDown size={14} /></button>
    <span className="indicator-source">Fuente {source}{current?.unit ? ` · ${current.unit}` : ''}</span>
    {open && <div className="indicator-menu"><div className="indicator-search"><Search size={14} /><input ref={search} aria-label="Buscar indicador por nombre o código" placeholder="Nombre o código del indicador…" value={query} onChange={event => { setQuery(event.target.value); setPage(1); }} /></div>
      {loading ? <div className="indicator-status" role="status"><LoaderCircle className="spin" size={15} />Cargando catálogo…</div> : error ? <div className="indicator-status error" role="alert">{error}<button type="button" onClick={() => setRetry(n => n + 1)}>Reintentar</button></div> : data && <>
        <div className="indicator-count" role="status">{data.total.toLocaleString('es-MX')} coincidencias · catálogo de {data.catalog_total.toLocaleString('es-MX')} entradas</div>
        {data.stale && <div className="indicator-stale">Sin conexión: se muestra la última copia completa guardada.</div>}
        <div className="indicator-options" role="listbox" id={listId} aria-label="Indicadores del Banco Mundial">{data.items.map(item => <button type="button" key={`${item.source}-${item.id}`} role="option" aria-selected={item.id === value && Number(item.source) === source} onClick={() => choose(item)}><span><strong>{item.name}</strong><code>{item.id}</code><small>{item.source_name} · {item.source}{item.unit ? ` · ${item.unit}` : ''}</small></span>{item.id === value && Number(item.source) === source && <Check size={14} />}</button>)}{!data.items.length && <p className="indicator-status">No hay indicadores con ese nombre o código.</p>}</div>
        {data.pages > 1 && <div className="indicator-pagination"><button type="button" aria-label="Página anterior de indicadores" disabled={page <= 1} onClick={() => setPage(page - 1)}><ChevronLeft size={14} /></button><span>Página {page} de {data.pages}</span><button type="button" aria-label="Página siguiente de indicadores" disabled={page >= data.pages} onClick={() => setPage(page + 1)}><ChevronRight size={14} /></button></div>}
        <p className="indicator-availability">La disponibilidad de observaciones depende del país, período y frecuencia.</p>
      </>}
    </div>}
  </div>;
}
