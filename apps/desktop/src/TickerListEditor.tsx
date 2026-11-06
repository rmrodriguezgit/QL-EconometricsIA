import { Plus, Trash2 } from 'lucide-react';
import yahoo from '../../../packages/contracts/yfinanceCatalog.json' with { type: 'json' };
import { tickerAlias } from './sourceColumns';

type Row = { code: string; alias: string };
type Props = { tickers: string; index: string; disabled: boolean; onPatch: (parameters: Record<string, string | number>) => void };

// Estilos en línea, como en el editor de FRED, para no depender de cambios en studio.css.
const idStyle = { padding: '7px 8px', background: '#0d141e', border: '1px solid #303d4e', borderRadius: 5, color: '#c6d3e4', font: '11px ui-monospace,monospace' };
const metaStyle = { color: '#8296af', fontSize: 10, lineHeight: 1.35 };
const assets = new Map(yahoo.assets.map(item => [item.ticker, item]));
const groups = [...new Set(yahoo.assets.map(item => item.group))];
const validAlias = (alias: string) => /^[A-Za-z_][A-Za-z0-9_]{0,40}$/.test(alias) && alias !== 'periodo';

const parse = (value: string): Row[] => value.split(/[\n;,]+/).map(item => item.trim()).filter(Boolean).map(item => {
  const [code, ...alias] = item.split(':');
  return { code: code.trim().toUpperCase(), alias: alias.join(':').trim() };
});
const serialize = (rows: Row[]) => rows.filter(row => row.code).map(row => row.alias ? `${row.code}: ${row.alias}` : row.code).join('\n');

/** Activos de Yahoo Finance («TICKER: alias»); el índice de comparación se elige en su propio campo. */
export default function TickerListEditor({ tickers, index, disabled, onPatch }: Props) {
  const rows = parse(tickers);
  const save = (next: Row[]) => onPatch({ tickers: serialize(next) });
  const change = (i: number, row: Partial<Row>) => save(rows.map((item, k) => k === i ? { ...item, ...row } : item));
  const aliases = rows.map(row => row.alias || tickerAlias(row.code));
  const indexAlias = index && index !== 'ninguno' ? tickerAlias(index) : '';
  const duplicated = (alias: string) => aliases.filter(item => item === alias).length > 1 || alias === indexAlias;
  return <section className="indicator-list" aria-label="Activos de Yahoo Finance">
    <h4>ACTIVOS Y ALIAS DE COLUMNA</h4>
    <p className="subtle">Tickers de Yahoo Finance: acciones de EE. UU. (<code>AAPL</code>), de la BMV con <code>.MX</code> (<code>WALMEX.MX</code>), ETF, cripto (<code>BTC-USD</code>) o divisas (<code>MXN=X</code>). Máximo 10.</p>
    <datalist id="yahoo-assets">{groups.map(group => yahoo.assets.filter(item => item.group === group).map(item => <option key={item.ticker} value={item.ticker}>{`${item.name} · ${group}`}</option>))}</datalist>
    {rows.map((row, i) => {
      const alias = aliases[i], meta = assets.get(row.code), invalid = !validAlias(alias) || duplicated(alias);
      return <div className="indicator-row" key={i}>
        <input aria-label={`Ticker ${i + 1}`} list="yahoo-assets" disabled={disabled} value={row.code} placeholder="AAPL" style={idStyle}
          onChange={event => {
            const code = event.target.value.toUpperCase().replace(/[^A-Z0-9^=._-]/g, '');
            const suggested = !row.alias || row.alias === tickerAlias(row.code);
            change(i, { code, alias: suggested ? '' : row.alias });
          }} />
        <small style={metaStyle}>{meta ? `${meta.name} · ${meta.group}` : row.code ? 'Ticker fuera de la lista sugerida: Yahoo Finance dirá al ejecutar si existe.' : ''}</small>
        <div className="indicator-alias">
          <input aria-label={`Alias de ${row.code}`} disabled={disabled} value={row.alias} placeholder={tickerAlias(row.code)} aria-invalid={invalid}
            onChange={event => change(i, { alias: event.target.value.replace(/\s+/g, '_') })} />
          <button className="icon-button" type="button" title="Quitar activo" aria-label={`Quitar ${row.code}`} disabled={disabled || rows.length < 2} onClick={() => save(rows.filter((_, k) => k !== i))}><Trash2 size={14} /></button>
        </div>
        {invalid && <small className="indicator-error">{duplicated(alias) ? 'Alias repetido o igual al del índice.' : 'Usa letras, números y «_», sin empezar por número ni llamarlo periodo.'}</small>}
      </div>;
    })}
    <button className="text-button indicator-add" type="button" disabled={disabled || rows.length >= 10}
      onClick={() => { const next = yahoo.assets.find(item => !rows.some(row => row.code === item.ticker)); save([...rows, { code: next?.ticker ?? 'SPY', alias: '' }]); }}><Plus size={13} /> Añadir activo</button>
    <p className="subtle">El índice de comparación se elige abajo, en «Índice de comparación»; su columna se llama <code>{indexAlias || '—'}</code>.</p>
  </section>;
}
