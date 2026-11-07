import { numberFormat, scientific } from './numberFormat';
import { axisScale, useAxis } from './axisFormat';
import type { ReactNode } from 'react';
const format = (value: unknown): ReactNode => typeof value === 'number' ? (value !== 0 && Math.abs(value) < 1e-4 ? scientific(value) : numberFormat({ maximumSignificantDigits: 6 }).format(value)) : value === null ? 'No definido' : String(value);
type Report = { topic: string; seed?: number; n?: number; interpretation: string; scope: string; metrics: { label: string; value: unknown }[]; tables: { title: string; columns: string[]; rows: unknown[][] }[]; series: { label: string; points: [number, number][] }[]; limitations: string[]; warnings: string[] };
export default function ExperimentReport({ result }: { result: Record<string, unknown> }) {
  const report = result as unknown as Report;
  const points = report.series.flatMap(series => series.points);
  const low = Math.min(...points.map(p => p[1])), high = Math.max(...points.map(p => p[1]));
  const maximum = Math.max(1, ...points.map(p => p[0]));
  const sy = axisScale([low, high], useAxis().y, value => String(format(value)));
  return <div className="experiment-report"><div className="experiment-report-heading"><span>{report.topic} · RESULTADO</span><span>{report.seed !== undefined ? `Semilla ${report.seed} · ` : ""}{report.n !== undefined && report.n !== null ? `Muestra ${report.n}` : ""}</span></div><p className="experiment-interpretation">{report.interpretation}</p>
    <div className="experiment-metrics">{report.metrics.map(metric => <div key={metric.label}><span>{metric.label.replaceAll('_', ' ')}</span><strong>{format(metric.value)}</strong></div>)}</div>
    {report.tables.map(table => <section className="experiment-table" key={table.title}><h3>{table.title}</h3><div className="table-wrap"><table><thead><tr>{table.columns.map(column => <th key={column}>{column}</th>)}</tr></thead><tbody>{table.rows.map((row, index) => <tr key={index}>{row.map((value, i) => <td key={i}>{format(value)}</td>)}</tr>)}</tbody></table></div></section>)}
    {points.length > 0 && <section className="experiment-series"><h3>Observa el experimento</h3><svg viewBox="0 0 600 180" role="img" aria-label={`Series del experimento: ${report.series.map(series => series.label).join(', ')}. Valores numéricos disponibles al exportar resultados.`}><line x1="40" y1="145" x2="580" y2="145" stroke="#dfe7d9"/><text x="35" y="22" textAnchor="end">{sy.tick(high)}</text><text x="35" y="147" textAnchor="end">{sy.tick(low)}</text>{sy.factor && <text x="45" y="12" className="axis-factor">{sy.factor}</text>}{report.series.map((series, i) => <polyline key={series.label} fill="none" stroke={['#428263','#9c82ad','#bd985e'][i % 3]} strokeWidth="1.5" points={series.points.map(([x,y]) => `${45+x/maximum*530},${140-(y-low)/(high-low || 1)*115}`).join(' ')} />)}<text x="45" y="166">0</text><text x="575" y="166" textAnchor="end">Índice {maximum}</text></svg><div className="series-legend">{report.series.map((series,i) => <span key={series.label} style={{color:['#428263','#9c82ad','#bd985e'][i % 3]}}>● {series.label}</span>)}</div></section>}
    {report.limitations.length > 0 && <div className="experiment-limitations"><strong>Límites del ejemplo</strong>{report.limitations.map(text => <p key={text}>{text}</p>)}</div>}
    {report.warnings.length > 0 && <details className="experiment-limitations"><summary>Advertencias del cálculo</summary>{report.warnings.map(text => <p key={text}>{text}</p>)}</details>}
    <p className="result-footnote">{report.scope} Consulta objetivos, bibliografía y subtemas en el catálogo.</p>
  </div>;
}
