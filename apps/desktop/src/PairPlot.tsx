// Matriz de dispersión (pairplot): dispersión bajo la diagonal, histogramas en ella y r de Pearson encima.
export type PairPlotData = {
  columns: string[]; group: string | null; groups: string[];
  points: (number | null)[][]; // valores por columna + índice de grupo al final
  diagonal: { column: string; edges: number[]; counts: number[][]; n: number }[];
  correlation: (number | null)[][];
};
const palette = ['#6cc9ac', '#79b4ef', '#ffd166', '#f4a3a9', '#b295ee', '#8adde4', '#f6a96b', '#c6d3e4'];
import { numberFormat } from './numberFormat';
import { axisScale, scientificValue, useAxis } from './axisFormat';
const plain = (value: number) => numberFormat({ maximumSignificantDigits: 3 }).format(value);
const format = (value: number) => scientificValue(value, 'auto', plain);

export default function PairPlot({ data }: { data: PairPlotData }) {
  const k = data.columns.length;
  const cell = k <= 3 ? 170 : k <= 5 ? 135 : 105, pad = 8, left = 70, top = 10, bottom = 40;
  const size = left + k * cell, height = top + k * cell + bottom;
  const ranges = data.columns.map((_, c) => {
    const values = data.points.map(row => row[c]).filter((v): v is number => v !== null);
    const edges = data.diagonal[c].edges;
    const min = Math.min(edges[0], ...values), max = Math.max(edges.at(-1)!, ...values);
    return [min, max === min ? min + 1 : max] as const;
  });
  const sx = (c: number, v: number) => left + c * cell + pad + (v - ranges[c][0]) / (ranges[c][1] - ranges[c][0]) * (cell - 2 * pad);
  const sy = (r: number, v: number) => top + r * cell + cell - pad - (v - ranges[r][0]) / (ranges[r][1] - ranges[r][0]) * (cell - 2 * pad);
  const color = (g: number) => palette[g % palette.length];
  const axis = useAxis();
  const xScales = ranges.map(range => axisScale([...range], axis.x, plain)), yScales = ranges.map(range => axisScale([...range], axis.y, plain));
  return <section className="pair-plot">
    <div className="result-title"><h3>Pairplot · {k} variables</h3><span>{data.points.length} puntos{data.group ? ` · color por ${data.group}` : ''}</span></div>
    {data.groups.length > 1 && <div className="pair-legend">{data.groups.map((g, i) => <span key={g}><i style={{ background: color(i) }} />{g}</span>)}</div>}
    <div className="pair-scroll"><svg viewBox={`0 0 ${size} ${height}`} style={{ minWidth: Math.min(size, 640) }} role="img" aria-label={`Matriz de dispersión de ${data.columns.join(', ')}. Correlaciones exactas en la tabla.`}>
      {data.columns.map((rowName, r) => data.columns.map((colName, c) => {
        const x0 = left + c * cell, y0 = top + r * cell;
        const frame = <rect x={x0 + 2} y={y0 + 2} width={cell - 4} height={cell - 4} rx="4" className="pair-cell" />;
        if (r === c) {
          const diag = data.diagonal[c], edges = diag.edges;
          const totals = edges.slice(0, -1).map((_, b) => diag.counts.reduce((sum, counts) => sum + counts[b], 0));
          const peak = Math.max(1, ...totals);
          return <g key={`${r}-${c}`}>{frame}{edges.slice(0, -1).map((lower, b) => {
            let base = y0 + cell - pad;
            return diag.counts.map((counts, g) => {
              const h = counts[b] / peak * (cell - 2 * pad - 14);
              base -= h;
              return h > 0 ? <rect key={`${b}-${g}`} x={sx(c, lower) + .5} y={base} width={Math.max(1, sx(c, edges[b + 1]) - sx(c, lower) - 1)} height={h} fill={color(g)} opacity=".75"><title>{`${rowName}: ${format(lower)} – ${format(edges[b + 1])} · ${counts[b]}${data.groups.length > 1 ? ` (${data.groups[g]})` : ''}`}</title></rect> : null;
            });
          })}<text x={x0 + cell / 2} y={y0 + 16} textAnchor="middle" className="pair-name">{rowName}</text></g>;
        }
        if (r < c) {
          const value = data.correlation[r][c];
          const strength = value === null ? 0 : Math.abs(value);
          return <g key={`${r}-${c}`}>{frame}<rect x={x0 + 2} y={y0 + 2} width={cell - 4} height={cell - 4} rx="4" fill={value === null ? 'transparent' : value >= 0 ? '#6cc9ac' : '#f4a3a9'} opacity={strength * .28} />
            <text x={x0 + cell / 2} y={y0 + cell / 2} textAnchor="middle" dominantBaseline="middle" className="pair-r" style={{ fontSize: 12 + strength * 10 }}>{value === null ? 'No definido' : `r = ${value.toFixed(2)}`}</text>
            <text x={x0 + cell / 2} y={y0 + cell / 2 + 20} textAnchor="middle" className="pair-sub">{rowName} · {colName}</text></g>;
        }
        return <g key={`${r}-${c}`}>{frame}{data.points.map((row, i) => row[c] === null || row[r] === null ? null :
          <circle key={i} cx={sx(c, row[c]!)} cy={sy(r, row[r]!)} r={k > 5 ? 1.6 : 2.2} fill={color(Number(row[k]))} opacity=".7" />)}</g>;
      }))}
      {data.columns.map((name, c) => <g key={`ax-${name}`}>
        <text x={left + c * cell + cell / 2} y={top + k * cell + 26} textAnchor="middle" className="pair-axis">{xScales[c].label(name)}</text>
        <text x={left + c * cell + pad} y={top + k * cell + 12} className="pair-tick">{xScales[c].tick(ranges[c][0])}</text>
        <text x={left + (c + 1) * cell - pad} y={top + k * cell + 12} textAnchor="end" className="pair-tick">{xScales[c].tick(ranges[c][1])}</text>
        <text transform={`translate(${left - 56},${top + c * cell + cell / 2}) rotate(-90)`} textAnchor="middle" className="pair-axis">{yScales[c].label(name)}</text>
        <text x={left - 4} y={sy(c, ranges[c][0])} textAnchor="end" className="pair-tick">{yScales[c].tick(ranges[c][0])}</text>
        <text x={left - 4} y={sy(c, ranges[c][1]) + 8} textAnchor="end" className="pair-tick">{yScales[c].tick(ranges[c][1])}</text>
      </g>)}
    </svg></div>
    <p className="result-footnote">Bajo la diagonal: dispersión de cada par (filas completas del par). Diagonal: histograma{data.groups.length > 1 ? ' apilado por grupo' : ''}. Sobre la diagonal: correlación de Pearson; color verde positivo, rojo negativo, más intenso cuanto más fuerte.</p>
  </section>;
}
