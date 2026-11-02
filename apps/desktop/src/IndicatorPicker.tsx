import { useEffect, useRef, useState, useId } from 'react';
import { Check, ChevronDown, ChevronLeft, ChevronRight, LoaderCircle, Search, X } from 'lucide-react';
import { rpc } from './model';

type Indicator = { id: string; name: string; source: string; source_name: string; unit: string };
type CatalogPage = { items: Indicator[]; total: number; catalog_total: number; page: number; pages: number; retrieved_at: string; stale: boolean };

export default function IndicatorPicker({ value, source, name, unit, disabled, onChange }: { value: string; source: number; name?:string; unit?:string; disabled: boolean; onChange: (indicator: string, source: number, metadata:Indicator) => void }) {
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
  const dialog=useRef<HTMLDialogElement>(null);
  const titleId=useId();
  const listId = useId();
  const labelId=useId();
  useEffect(() => {
    if (!open) return;
    dialog.current?.showModal();
    search.current?.focus();
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
  const choose = (item: Indicator) => { setChoice(item); onChange(item.id, Number(item.source),item); setOpen(false); trigger.current?.focus(); };
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
    <label className="indicator-label" id={labelId}>Código de indicador</label>
    <button ref={trigger} type="button" role="combobox" aria-labelledby={labelId} aria-haspopup="dialog" aria-expanded={open} aria-controls={open ? listId : undefined} disabled={disabled} className="indicator-trigger" onClick={() => setOpen(!open)}><span><strong>{current?.name || name || 'Seleccionar indicador'}</strong><small>Buscar por nombre o código</small></span><ChevronDown size={14} /></button>
    <div className="indicator-selected"><span>Código seleccionado</span><button className="indicator-code-button" aria-label="Ver y cambiar indicador" title="Abrir ventana de indicadores" disabled={disabled} onClick={()=>setOpen(true)}><code aria-label="Código completo del indicador">{value}</code><span>Ver nombre completo y cambiar indicador ↗</span></button><small>Fuente {source}{(current?.unit||unit) ? ` · ${current?.unit||unit}` : ''}</small></div>
    {open && <dialog ref={dialog} className="indicator-menu indicator-dialog" aria-labelledby={titleId} onCancel={()=>setOpen(false)}><header className="indicator-dialog-header"><div><span>BANCO MUNDIAL</span><h3 id={titleId}>Seleccionar indicador</h3></div><button aria-label="Cerrar ventana de indicadores" onClick={()=>setOpen(false)}><X size={18}/></button></header><div className="indicator-current"><span>Selección actual</span><strong>{current?.name||name||'Indicador seleccionado'}</strong><code>{value}</code><small>Fuente {source}{(current?.unit||unit)?` · ${current?.unit||unit}`:''}</small></div><div className="indicator-search"><Search size={14} /><input ref={search} aria-label="Buscar indicador por nombre o código" placeholder="Nombre o código del indicador…" value={query} onChange={event => { setQuery(event.target.value); setPage(1); }} /></div>
      {loading ? <div className="indicator-status" role="status"><LoaderCircle className="spin" size={15} />Cargando catálogo…</div> : error ? <div className="indicator-status error" role="alert">{error}<button type="button" onClick={() => setRetry(n => n + 1)}>Reintentar</button></div> : data && <>
        <div className="indicator-count" role="status">{data.total.toLocaleString('es-MX')} coincidencias · catálogo de {data.catalog_total.toLocaleString('es-MX')} entradas</div>
        {data.stale && <div className="indicator-stale">Sin conexión: se muestra la última copia completa guardada.</div>}
        <div className="indicator-options" role="listbox" id={listId} aria-label="Indicadores del Banco Mundial">{data.items.map(item => <button type="button" key={`${item.source}-${item.id}`} role="option" aria-selected={item.id === value && Number(item.source) === source} onClick={() => choose(item)}><span className="indicator-option-text"><strong>{item.name}</strong><code>{item.id}</code><small>{item.source_name} · {item.source}{item.unit ? ` · ${item.unit}` : ''}</small></span>{item.id === value && Number(item.source) === source && <Check size={14} />}</button>)}{!data.items.length && <p className="indicator-status">No hay indicadores con ese nombre o código.</p>}</div>
        {data.pages > 1 && <div className="indicator-pagination"><button type="button" aria-label="Página anterior de indicadores" disabled={page <= 1} onClick={() => setPage(page - 1)}><ChevronLeft size={14} /></button><span>Página {page} de {data.pages}</span><button type="button" aria-label="Página siguiente de indicadores" disabled={page >= data.pages} onClick={() => setPage(page + 1)}><ChevronRight size={14} /></button></div>}
        <p className="indicator-availability">La disponibilidad de observaciones depende del país, período y frecuencia.</p>
      </>}
    </dialog>}
  </div>;
}
