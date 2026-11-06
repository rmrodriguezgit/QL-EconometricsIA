import { useEffect, useMemo, useState, type ComponentType } from 'react';
import { Brain, ChartLine, ChartScatter, ChevronLeft, ChevronRight, ClipboardCheck, Clock, Database, Layers, Plus, Search, Sigma, TrendingUp, Wand2, Wifi, X } from 'lucide-react';
import { areaCount, areaGroups, areaOf, areas, isListed, ONLINE, searchTools } from './libraryAreas';
import type { Kind, ToolDefinition } from './model';

const AREA_ICONS: Record<string, ComponentType<{ size?: number }>> = {
  database: Database, wand: Wand2, chart: ChartScatter, sigma: Sigma, line: ChartLine, clock: Clock, layers: Layers, brain: Brain, trending: TrendingUp, check: ClipboardCheck,
};
const STORAGE = 'quantlabs.library.area';

type Props = { catalog: Record<Kind, ToolDefinition>; icons: Record<Kind, ComponentType<{ size?: number }>>; busy: boolean; examples: number; onAdd: (kind: Kind) => void };

function readArea() {
  try { const value = localStorage.getItem(STORAGE); return value && (value === '' || areas.some(area => area.id === value)) ? value : ''; } catch { return ''; }
}

/** Biblioteca por áreas: primero el submenú de áreas; al elegir una, sus herramientas agrupadas. La búsqueda cubre todas. */
export default function LibraryPanel({ catalog, icons, busy, examples, onAdd }: Props) {
  const [area, setArea] = useState<string>(readArea);
  const [query, setQuery] = useState('');
  useEffect(() => { try { localStorage.setItem(STORAGE, area); } catch { /* sin almacenamiento: solo no se recuerda */ } }, [area]);
  const total = useMemo(() => Object.values(catalog).filter(isListed).length, [catalog]);
  const results = useMemo(() => searchTools(query, catalog), [query, catalog]);
  const current = areas.find(item => item.id === area);
  const tool = (kind: string, withArea = false) => {
    const value = catalog[kind as Kind];
    const Icon = icons[kind as Kind];
    const where = withArea ? areaOf(kind)?.label : undefined;
    return <button disabled={busy} className="library-node" key={kind} onClick={() => onAdd(kind as Kind)} title={value.explanation || value.detail}>
      <span className={`node-icon ${value.color}`}><Icon size={17} /></span>
      <span><strong>{value.label}</strong><small>{where ? `${where} · ` : ''}{value.detail}</small>{ONLINE.has(kind) && <em className="library-tag"><Wifi size={10} /> Requiere conexión</em>}</span>
      <Plus size={14} />
    </button>;
  };
  return <aside className="library">
    <div className="section-heading"><h2>Biblioteca</h2><span title="Herramientas disponibles">{total}</span></div>
    <div className="search"><Search size={15} /><input aria-label="Buscar herramientas en todas las áreas" placeholder="Buscar en todas las áreas…" value={query} onChange={event => setQuery(event.target.value)} />
      {query && <button className="search-clear" aria-label="Borrar búsqueda" onClick={() => setQuery('')}><X size={13} /></button>}</div>
    {query ? <div className="library-nodes" aria-label="Resultados de búsqueda">
      <p className="subtle">{results.length ? `${results.length} herramienta${results.length === 1 ? '' : 's'}` : 'Sin coincidencias. Prueba con otra palabra (p. ej. «regresión», «volatilidad», «capas»).'}</p>
      {results.map(kind => tool(kind, true))}
    </div> : !current ? <div className="library-areas" role="menu" aria-label="Áreas de herramientas">
      <p className="subtle">Elige un área para ver sus herramientas.</p>
      {areas.map(item => { const Icon = AREA_ICONS[item.icon] ?? Layers; const count = areaCount(item.id, catalog); return count ? <button role="menuitem" key={item.id} className="library-area" title={item.description} onClick={() => setArea(item.id)}>
        <span className="library-area-icon"><Icon size={16} /></span><span><strong>{item.label}</strong><small>{item.description}</small></span><span className="library-area-count">{count}<ChevronRight size={13} /></span>
      </button> : null; })}
    </div> : <div className="library-nodes">
      <div className="library-area-bar">
        <button className="library-back" onClick={() => setArea('')} aria-label="Volver a las áreas"><ChevronLeft size={14} />Áreas</button>
        <select aria-label="Cambiar de área" value={area} onChange={event => setArea(event.target.value)}>
          {areas.map(item => <option key={item.id} value={item.id}>{item.label} ({areaCount(item.id, catalog)})</option>)}
        </select>
      </div>
      <p className="subtle">{current.description}.</p>
      {areaGroups(area, catalog).map(group => <section className="node-group" key={group.label}><h3>{group.label}</h3>{group.tools.map(kind => tool(kind))}</section>)}
    </div>}
    <p className="library-footer" title="Añade una fuente de datos, conecta su salida a una herramienta y ejecuta. Los puertos sugieren qué conectar después.">{total} herramientas · {areas.length} áreas · {examples} recorridos guiados</p>
  </aside>;
}
