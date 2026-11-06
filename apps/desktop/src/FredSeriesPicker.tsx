import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { Check, ChevronDown, Search, X } from 'lucide-react';
import { fredGroups, fredItems, looksLikeFredId, searchFred, type FredItem } from './fredSearch';

const LIMIT = 120;
const selectStyle = { padding: '7px 8px', background: '#0d141e', border: '1px solid #303d4e', borderRadius: 5, color: '#c6d3e4', font: '11px inherit' };

/** Selector de series FRED con buscador y filtro por tema; también acepta un ID que no esté en el catálogo. */
export default function FredSeriesPicker({ value, disabled, onChange }: { value: string; disabled: boolean; onChange: (code: string, item?: FredItem) => void }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [group, setGroup] = useState('');
  const dialog = useRef<HTMLDialogElement>(null);
  const search = useRef<HTMLInputElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const container = useRef<HTMLDivElement>(null);
  const titleId = useId(), listId = useId();
  const current = fredItems.find(item => item.id === value.toUpperCase());
  const results = useMemo(() => searchFred(query, group), [query, group]);
  const manual = query.trim().toUpperCase();
  // Solo si se escribe como un ID (mayúsculas o con dígitos); «peso» o «desempleo» son búsquedas de texto.
  const offerManual = /^[A-Z0-9_]+$|\d/.test(query.trim()) && looksLikeFredId(manual) && !fredItems.some(item => item.id === manual);
  useEffect(() => { if (open) { dialog.current?.showModal(); search.current?.focus(); } }, [open]);
  const close = () => { setOpen(false); trigger.current?.focus(); };
  const choose = (code: string, item?: FredItem) => { onChange(code, item); close(); };
  return <div className="indicator-picker" ref={container} onKeyDown={event => {
    if (event.key === 'Escape' && open) { event.stopPropagation(); close(); }
    if (open && ['ArrowDown', 'ArrowUp'].includes(event.key)) {
      event.preventDefault();
      const options = [...(container.current?.querySelectorAll<HTMLButtonElement>('[role="option"]') ?? [])];
      const index = options.findIndex(option => option === document.activeElement);
      options[event.key === 'ArrowDown' ? Math.min(index + 1, options.length - 1) : Math.max(index - 1, 0)]?.focus();
    }
  }}>
    <button ref={trigger} type="button" className="indicator-trigger" aria-haspopup="dialog" aria-expanded={open} disabled={disabled}
      aria-label={`Buscar serie de FRED (actual: ${value || 'ninguna'})`} onClick={() => setOpen(true)}>
      <span><strong>{current?.title ?? (value ? `${value} · fuera del catálogo` : 'Seleccionar serie')}</strong><small>Buscar por ID, nombre o tema</small></span><ChevronDown size={14} />
    </button>
    {open && <dialog ref={dialog} className="indicator-menu indicator-dialog" aria-labelledby={titleId} onCancel={event => { event.preventDefault(); close(); }}>
      <header className="indicator-dialog-header"><div><span>FRED · RESERVA FEDERAL DE ST. LOUIS</span><h3 id={titleId}>Seleccionar serie</h3></div><button aria-label="Cerrar catálogo de FRED" onClick={close}><X size={18} /></button></header>
      <div className="indicator-current"><span>Selección actual</span><strong>{current?.title ?? 'Serie fuera del catálogo curado'}</strong><code>{value || '—'}</code>{current && <small>{current.units} · {current.frequency} · {current.seasonal}</small>}</div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <div className="indicator-search" style={{ flex: 1 }}><Search size={14} /><input ref={search} autoFocus aria-label="Buscar serie por ID, nombre o tema" placeholder="p. ej. desempleo, DGS10, peso, vivienda…" value={query} onChange={event => setQuery(event.target.value)} /></div>
        <select aria-label="Filtrar por tema" style={selectStyle} value={group} onChange={event => setGroup(event.target.value)}>
          <option value="">Todos los temas ({fredItems.length})</option>
          {Object.entries(fredGroups).map(([key, label]) => <option key={key} value={key}>{label} ({fredItems.filter(item => item.group === key).length})</option>)}
        </select>
      </div>
      <div className="indicator-count" role="status">{results.length} coincidencias · catálogo de {fredItems.length} series verificadas{results.length > LIMIT ? ` · se muestran ${LIMIT}; afina la búsqueda` : ''}</div>
      <div className="indicator-options" role="listbox" id={listId} aria-label="Series de FRED">
        {offerManual && <button type="button" role="option" aria-selected={false} onClick={() => choose(manual)}><span className="indicator-option-text"><strong>Usar «{manual}» tal cual</strong><code>{manual}</code><small>Fuera del catálogo: FRED dirá al ejecutar si existe. Revisa sus unidades en fred.stlouisfed.org/series/{manual}</small></span></button>}
        {results.slice(0, LIMIT).map(item => <button type="button" key={item.id} role="option" aria-selected={item.id === value} onClick={() => choose(item.id, item)}>
          <span className="indicator-option-text"><strong>{item.title}</strong><code>{item.id}</code><small>{fredGroups[item.group]} · {item.units} · {item.frequency} · {item.seasonal}</small></span>{item.id === value && <Check size={14} />}
        </button>)}
        {!results.length && !offerManual && <p className="indicator-status">No hay series con esa búsqueda en este tema.</p>}
      </div>
      <p className="indicator-availability">Catálogo curado. Cualquier otro ID de FRED puede escribirse en la búsqueda o en el campo del identificador.</p>
    </dialog>}
  </div>;
}
