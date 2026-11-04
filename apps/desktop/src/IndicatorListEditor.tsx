import { Plus, Trash2 } from 'lucide-react';
import IndicatorPicker from './IndicatorPicker';
import { parseIndicatorList, serializeIndicatorList, suggestAlias, validAlias, type IndicatorRow } from './indicatorList';

type Props = { countries: string; indicators: string; source: number; disabled: boolean; onPatch: (parameters: Record<string, string | number>) => void };

/** Editor de países y pares «indicador → alias» para wbdata.get_dataframe({código: alias}, country=[…]). */
export default function IndicatorListEditor({ countries, indicators, source, disabled, onPatch }: Props) {
  const rows = parseIndicatorList(indicators);
  const save = (next: IndicatorRow[]) => onPatch({ indicators: serializeIndicatorList(next) });
  const change = (index: number, row: Partial<IndicatorRow>) => save(rows.map((item, i) => i === index ? { ...item, ...row } : item));
  const aliases = rows.map(row => row.alias || suggestAlias(row.code));
  const duplicated = (alias: string) => aliases.filter(item => item === alias).length > 1;
  return <section className="indicator-list" aria-label="Indicadores del Banco Mundial">
    <label className="field"><span>Países (ISO 3, separados por coma)</span>
      <input disabled={disabled} value={countries} placeholder="USA, MEX" onChange={event => onPatch({ countries: event.target.value.toUpperCase() })} /></label>
    <h4>INDICADORES Y ALIAS DE COLUMNA</h4>
    <p className="subtle">Cada indicador se descarga como una columna con su alias, igual que <code>wbdata.get_dataframe({'{código: alias}'})</code>.</p>
    {rows.map((row, index) => {
      const alias = aliases[index];
      const invalid = !validAlias(alias) || duplicated(alias);
      return <div className="indicator-row" key={`${index}-${row.code}`}>
        <IndicatorPicker value={row.code} source={source} disabled={disabled}
          onChange={(code, nextSource) => { const next = rows.map((item, i) => i === index ? { code, alias: item.alias || suggestAlias(code) } : item); onPatch({ indicators: serializeIndicatorList(next), source: nextSource }); }} />
        <div className="indicator-alias">
          <input aria-label={`Alias de ${row.code}`} disabled={disabled} value={row.alias} placeholder={suggestAlias(row.code)} aria-invalid={invalid}
            onChange={event => change(index, { alias: event.target.value.replace(/\s+/g, '_') })} />
          <button className="icon-button" type="button" title="Quitar indicador" aria-label={`Quitar ${row.code}`} disabled={disabled || rows.length < 2} onClick={() => save(rows.filter((_, i) => i !== index))}><Trash2 size={14} /></button>
        </div>
        {invalid && <small className="indicator-error">{duplicated(alias) ? 'Alias repetido.' : 'Usa letras, números y «_», sin empezar por número.'}</small>}
      </div>;
    })}
    <button className="text-button indicator-add" type="button" disabled={disabled || rows.length >= 12}
      onClick={() => save([...rows, { code: 'NY.GDP.PCAP.KD', alias: suggestAlias('NY.GDP.PCAP.KD') }])}><Plus size={13} /> Añadir indicador</button>
    {source !== 2 && <p className="subtle">Fuente {source}: todos los indicadores se consultan en esa misma fuente.</p>}
  </section>;
}
