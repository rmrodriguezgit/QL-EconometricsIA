import { Plus, Trash2 } from 'lucide-react';
import fred from '../../../packages/contracts/fredCatalog.json' with { type: 'json' };
import { parseIndicatorList, serializeIndicatorList, type IndicatorRow } from './indicatorList';
import { fredAlias } from './sourceColumns';

type Props = { series: string; disabled: boolean; onPatch: (parameters: Record<string, string | number>) => void };
type FredItem = { id: string; alias: string; title: string; units: string; frequency: string; group: string };

// Estilos en línea: studio.css lo edita otra parte de la interfaz a la vez.
const idStyle = { padding: '7px 8px', background: '#0d141e', border: '1px solid #303d4e', borderRadius: 5, color: '#c6d3e4', font: '11px ui-monospace,monospace' };
const metaStyle = { color: '#8296af', fontSize: 10, lineHeight: 1.35 };
const items = fred.items as FredItem[];
const known = new Map(items.map(item => [item.id, item]));
const validAlias = (alias: string) => /^[A-Za-z_][A-Za-z0-9_]{0,40}$/.test(alias) && !['periodo', 'fecha'].includes(alias);

/** Editor de pares «ID de FRED → alias»; la lista sugiere series curadas, pero acepta cualquier ID. */
export default function FredSeriesEditor({ series, disabled, onPatch }: Props) {
  const rows = parseIndicatorList(series);
  const save = (next: IndicatorRow[]) => onPatch({ series: serializeIndicatorList(next) });
  const change = (index: number, row: Partial<IndicatorRow>) => save(rows.map((item, i) => i === index ? { ...item, ...row } : item));
  const aliases = rows.map(row => row.alias || fredAlias(row.code));
  const duplicated = (alias: string) => aliases.filter(item => item === alias).length > 1;
  return <section className="indicator-list" aria-label="Series de FRED">
    <h4>SERIES DE FRED Y ALIAS DE COLUMNA</h4>
    <p className="subtle">Escribe o elige el identificador (p. ej. <code>DGS3MO</code>, <code>UNRATE</code>). Se descarga de <code>fredgraph.csv?id=…</code>, sin clave de API.</p>
    <datalist id="fred-series">{items.map(item => <option key={item.id} value={item.id}>{`${item.title} · ${item.units} · ${item.frequency}`}</option>)}</datalist>
    {rows.map((row, index) => {
      const alias = aliases[index], meta = known.get(row.code.toUpperCase());
      const invalid = !validAlias(alias) || duplicated(alias);
      return <div className="indicator-row" key={index}>
        <input aria-label={`Identificador FRED ${index + 1}`} list="fred-series" disabled={disabled} value={row.code} placeholder="DGS10"
          style={idStyle} onChange={event => {
            const code = event.target.value.toUpperCase().replace(/[^A-Z0-9_]/g, '');
            const wasSuggested = !row.alias || row.alias === fredAlias(row.code);
            change(index, { code, alias: wasSuggested ? fredAlias(code) : row.alias });
          }} />
        {meta ? <small style={metaStyle}>{meta.title} · {meta.units} · {meta.frequency}</small> : row.code && <small style={metaStyle}>Serie fuera de la lista curada: revisa sus unidades en fred.stlouisfed.org/series/{row.code}</small>}
        <div className="indicator-alias">
          <input aria-label={`Alias de ${row.code}`} disabled={disabled} value={row.alias} placeholder={fredAlias(row.code)} aria-invalid={invalid}
            onChange={event => change(index, { alias: event.target.value.replace(/\s+/g, '_') })} />
          <button className="icon-button" type="button" title="Quitar serie" aria-label={`Quitar ${row.code}`} disabled={disabled || rows.length < 2} onClick={() => save(rows.filter((_, i) => i !== index))}><Trash2 size={14} /></button>
        </div>
        {invalid && <small className="indicator-error">{duplicated(alias) ? 'Alias repetido.' : 'Usa letras, números y «_», sin empezar por número ni llamarlo periodo.'}</small>}
      </div>;
    })}
    <button className="text-button indicator-add" type="button" disabled={disabled || rows.length >= 12}
      onClick={() => { const next = items.find(item => !rows.some(row => row.code === item.id)) ?? items[0]; save([...rows, { code: next.id, alias: next.alias }]); }}><Plus size={13} /> Añadir serie</button>
  </section>;
}
