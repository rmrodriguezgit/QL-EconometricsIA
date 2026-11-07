// Gráficos de las herramientas multivariadas: varias series, boxplots, residuos e hipótesis.
const palette = ['#6cc9ac', '#79b4ef', '#ffd166', '#f4a3a9', '#b295ee', '#8adde4', '#f6a96b', '#c6d3e4'];
import { numberFormat } from './numberFormat';
import { axisScale, scientificValue, useAxis } from './axisFormat';
const plain = (value: number) => numberFormat({ maximumSignificantDigits: 3 }).format(value);
const format = (value: number) => scientificValue(value, 'auto', plain);
const extent = (values: number[]) => { const min = Math.min(...values), max = Math.max(...values); return min === max ? [min - 1, max + 1] : [min, max]; };

export type SeriesPlotData = { time: string; mode: 'paneles' | 'indice' | 'original'; lines: { name: string; points: [number, number | null][]; n: number }[] };

function path(points: [number, number | null][], x: (v: number) => number, y: (v: number) => number) {
  let d = '', open = false;
  for (const [t, v] of points) {
    if (v === null) { open = false; continue; }
    d += `${open ? 'L' : 'M'}${x(t).toFixed(1)},${y(v).toFixed(1)}`; open = true;
  }
  return d;
}

export function SeriesPlot({ data }: { data: SeriesPlotData }) {
  const times = data.lines.flatMap(line => line.points.map(p => p[0]));
  const [t0, t1] = extent(times);
  const panels = data.mode === 'paneles' ? data.lines.map(line => [line]) : [data.lines];
  const width = 640, left = 62, right = 16, panelH = data.mode === 'paneles' ? 120 : 260, gap = 18;
  const height = panels.length * (panelH + gap) + 30;
  const x = (t: number) => left + (t - t0) / (t1 - t0) * (width - left - right);
  const axis = useAxis();
  return <section className="multi-plot">
    <div className="result-title"><h3>{data.mode === 'indice' ? 'Series como índice (primer año = 100)' : data.mode === 'paneles' ? 'Series por panel' : 'Series en el mismo eje'}</h3><span>{data.lines.length} variables · eje x: {data.time}</span></div>
    {data.mode !== 'paneles' && <div className="pair-legend">{data.lines.map((line, i) => <span key={line.name}><i style={{ background: palette[i % 8] }} />{line.name}</span>)}</div>}
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Series de ${data.lines.map(l => l.name).join(', ')} frente a ${data.time}.`}>
      {panels.map((lines, p) => {
        const top = p * (panelH + gap) + 8;
        const [v0, v1] = extent(lines.flatMap(line => line.points.map(pt => pt[1]).filter((v): v is number => v !== null)));
        const y = (v: number) => top + panelH - (v - v0) / (v1 - v0) * panelH;
        const sy = axisScale([v0, v1], axis.y, plain);
        return <g key={p}>
          <rect x={left} y={top} width={width - left - right} height={panelH} className="multi-frame" />
          {[v0, (v0 + v1) / 2, v1].map(v => <g key={v}><line x1={left} x2={width - right} y1={y(v)} y2={y(v)} className="multi-grid" /><text x={left - 6} y={y(v) + 3} textAnchor="end" className="pair-tick">{sy.tick(v)}</text></g>)}
          {sy.factor && data.mode !== 'paneles' && <text x={left + 8} y={top + 15} className="axis-factor">{sy.factor}</text>}
          {lines.map(line => { const i = data.lines.indexOf(line); return <path key={line.name} d={path(line.points, x, y)} fill="none" stroke={palette[i % 8]} strokeWidth="2"><title>{line.name}</title></path>; })}
          {data.mode === 'paneles' && <text x={left + 8} y={top + 15} className="pair-name">{lines[0].name}{sy.factor && <tspan className="axis-factor"> ({sy.factor})</tspan>}</text>}
        </g>;
      })}
      {[t0, (t0 + t1) / 2, t1].map(t => <text key={t} x={x(t)} y={height - 8} textAnchor="middle" className="pair-tick">{Math.round(t)}</text>)}
    </svg>
  </section>;
}

export type BoxplotsData = { scale: 'zscore' | 'original'; boxes: { column: string; n: number; q1: number; median: number; q3: number; whisker_low: number; whisker_high: number; mean: number; outliers: number[]; outlier_count: number }[] };

export function MultiBoxPlot({ data }: { data: BoxplotsData }) {
  const width = 640, height = 300, left = 56, bottom = 40, top = 14;
  const all = data.boxes.flatMap(b => [b.whisker_low, b.whisker_high, ...b.outliers]);
  const [v0, v1] = extent(all);
  const y = (v: number) => top + (1 - (v - v0) / (v1 - v0)) * (height - top - bottom);
  const slot = (width - left - 10) / data.boxes.length, box = Math.min(60, slot * .5);
  const sy = axisScale([v0, v1], useAxis().y, plain);
  return <section className="multi-plot">
    <div className="result-title"><h3>Boxplots · {data.boxes.length} variables</h3><span>{data.scale === 'zscore' ? 'Valores estandarizados (z)' : 'Escala original'}</span></div>
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Boxplots de varias variables; valores exactos en la tabla.">
      {[v0, (v0 + v1) / 2, v1, ...(v0 < 0 && v1 > 0 ? [0] : [])].map(v => <g key={v}><line x1={left} x2={width - 10} y1={y(v)} y2={y(v)} className="multi-grid" /><text x={left - 6} y={y(v) + 3} textAnchor="end" className="pair-tick">{sy.tick(v)}</text></g>)}
      {sy.factor && <text x={left + 4} y={top + 10} className="axis-factor">{sy.factor}</text>}
      {data.boxes.map((b, i) => {
        const cx = left + slot * (i + .5), color = palette[i % 8];
        return <g key={b.column}>
          <line x1={cx} x2={cx} y1={y(b.whisker_low)} y2={y(b.q1)} stroke={color} /><line x1={cx} x2={cx} y1={y(b.q3)} y2={y(b.whisker_high)} stroke={color} />
          <line x1={cx - box / 4} x2={cx + box / 4} y1={y(b.whisker_low)} y2={y(b.whisker_low)} stroke={color} /><line x1={cx - box / 4} x2={cx + box / 4} y1={y(b.whisker_high)} y2={y(b.whisker_high)} stroke={color} />
          <rect x={cx - box / 2} y={y(b.q3)} width={box} height={Math.max(1, y(b.q1) - y(b.q3))} fill={color} fillOpacity=".18" stroke={color}><title>{`${b.column}: Q1 ${format(b.q1)} · mediana ${format(b.median)} · Q3 ${format(b.q3)} · n ${b.n}`}</title></rect>
          <line x1={cx - box / 2} x2={cx + box / 2} y1={y(b.median)} y2={y(b.median)} stroke="#ffd166" strokeWidth="2.5" />
          <circle cx={cx} cy={y(b.mean)} r="3" fill="none" stroke="#e0e9f5"><title>Media</title></circle>
          {b.outliers.map((v, k) => <circle key={k} cx={cx + ((k % 5) - 2) * 3} cy={y(v)} r="2.6" fill={color}><title>{format(v)}</title></circle>)}
          <text x={cx} y={height - 18} textAnchor="middle" className="pair-axis">{b.column}</text>
          <text x={cx} y={height - 5} textAnchor="middle" className="pair-tick">{b.outlier_count} atípicos</text>
        </g>;
      })}
    </svg>
  </section>;
}

export function ResidualPlot({ data }: { data: { points: [number, number][]; sd: number } }) {
  const width = 640, height = 260, left = 62, bottom = 34, top = 12;
  const [x0, x1] = extent(data.points.map(p => p[0]));
  const limit = Math.max(3 * data.sd, ...data.points.map(p => Math.abs(p[1])));
  const x = (v: number) => left + (v - x0) / (x1 - x0) * (width - left - 12);
  const y = (v: number) => top + (1 - (v + limit) / (2 * limit)) * (height - top - bottom);
  const axis = useAxis(), sy = axisScale([-limit, limit], axis.y, plain), sx = axisScale([x0, x1], axis.x, plain);
  return <section className="multi-plot">
    <div className="result-title"><h3>Residuos frente a predichos</h3><span>Banda = ±2 DE · se busca una nube sin patrón alrededor de 0</span></div>
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Residuos frente a valores predichos.">
      <rect x={left} y={y(2 * data.sd)} width={width - left - 12} height={y(-2 * data.sd) - y(2 * data.sd)} fill="#79b4ef" opacity=".07" />
      <line x1={left} x2={width - 12} y1={y(0)} y2={y(0)} stroke="#ffd166" strokeWidth="1.5" />
      {[-limit, 0, limit].map(v => <text key={v} x={left - 6} y={y(v) + 3} textAnchor="end" className="pair-tick">{sy.tick(v)}</text>)}
      {sy.factor && <text x={left + 4} y={top + 10} className="axis-factor">Residuo {sy.factor}</text>}
      {data.points.map(([p, r], i) => <circle key={i} cx={x(p)} cy={y(r)} r="2.6" fill={Math.abs(r) > 3 * data.sd ? '#f4a3a9' : '#6cc9ac'} opacity=".8" />)}
      {[x0, (x0 + x1) / 2, x1].map(v => <text key={v} x={x(v)} y={height - 14} textAnchor="middle" className="pair-tick">{sx.tick(v)}</text>)}
      <text x={(width + left) / 2} y={height - 1} textAnchor="middle" className="pair-axis">{sx.label('Valor predicho')}</text>
    </svg>
  </section>;
}

export function HypothesisCard({ data }: { data: { h0: string; ha: string; decision: string; reject: boolean } }) {
  return <section className={`hypothesis-card ${data.reject ? 'reject' : 'keep'}`}>
    <p><strong>H₀</strong> {data.h0.replace(/^H₀:\s*/, '')}</p>
    <p><strong>Hₐ</strong> {data.ha.replace(/^Hₐ:\s*/, '')}</p>
    <p className="hypothesis-decision">{data.decision}</p>
  </section>;
}
