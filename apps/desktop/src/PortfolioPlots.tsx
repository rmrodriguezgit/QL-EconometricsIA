// Gráficos del portafolio de Markowitz: frontera eficiente, planos de Sharpe y Sortino, mínima varianza y pesos.
import { numberFormat } from './numberFormat';
import type { ReactNode } from 'react';

type Point = { vol: number; ret: number; down: number; sharpe: number | null; sortino: number | null; weights: number[] };
type Marker = Point & { name: string };
export type PortfolioPlotData = {
  columns: string[]; risk_free: number;
  assets: { name: string; ret: number; vol: number; down: number }[];
  portfolios: Marker[]; frontier: Point[]; lower: Point[];
  /** [volatilidad, rendimiento, desviación a la baja, Sharpe, Sortino] */
  cloud: [number, number, number, number | null, number | null][];
};

const ASSET_COLORS = ['#6cc9ac', '#79b4ef', '#ffd166', '#f4a3a9', '#b295ee', '#8adde4', '#f6a96b', '#c6d3e4', '#9be37a', '#e39bd6'];
const PORTFOLIO_COLORS: Record<string, string> = { 'Pesos iguales': '#c6d3e4', 'Mínima varianza': '#79b4ef', 'Máximo Sharpe': '#ffd166', 'Máximo Sortino': '#f4a3a9' };
const color = (name: string) => PORTFOLIO_COLORS[name] ?? '#c6d3e4';
const num = (value: number | null | undefined, digits = 2) => value === null || value === undefined || !Number.isFinite(value) ? '—' : numberFormat({ maximumFractionDigits: digits }).format(value);

const W = 470, H = 300, L = 56, R = 14, T = 14, B = 44;
function nice(lo: number, hi: number) {
  const pad = (hi - lo || Math.abs(hi) || 1) * .08;
  return [lo - pad, hi + pad] as const;
}
function ticks(lo: number, hi: number, count = 5) { return Array.from({ length: count }, (_, i) => lo + (hi - lo) * i / (count - 1)); }

/** Escala continua azul → verde → amarillo para Sharpe o Sortino. */
function heat(value: number | null, lo: number, hi: number) {
  if (value === null || !Number.isFinite(value)) return '#4a5a70';
  const t = Math.max(0, Math.min(1, (value - lo) / (hi - lo || 1)));
  const stops = [[59, 91, 143], [108, 201, 172], [255, 209, 102]];
  const [a, b, u] = t < .5 ? [stops[0], stops[1], t * 2] : [stops[1], stops[2], (t - .5) * 2];
  return `rgb(${a.map((c, i) => Math.round(c + (b[i] - c) * u)).join(',')})`;
}

function Plane({ xLabel, yLabel, xs, ys, children, label }: { xLabel: string; yLabel: string; xs: number[]; ys: number[]; children: (x: (v: number) => number, y: (v: number) => number) => ReactNode; label: string }) {
  const [x0, x1] = nice(Math.min(0, ...xs), Math.max(...xs));
  const [y0, y1] = nice(Math.min(...ys), Math.max(...ys));
  const x = (v: number) => L + (v - Math.max(0, x0)) / (x1 - Math.max(0, x0)) * (W - L - R);
  const y = (v: number) => H - B - (v - y0) / (y1 - y0) * (H - T - B);
  return <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={label}>
    <rect x={L} y={T} width={W - L - R} height={H - T - B} className="multi-frame" />
    {ticks(y0, y1).map(v => <g key={`y${v}`}><line x1={L} x2={W - R} y1={y(v)} y2={y(v)} className="multi-grid" /><text x={L - 6} y={y(v) + 3} textAnchor="end" className="pair-tick">{num(v, 1)}</text></g>)}
    {ticks(Math.max(0, x0), x1).map(v => <text key={`x${v}`} x={x(v)} y={H - B + 14} textAnchor="middle" className="pair-tick">{num(v, 1)}</text>)}
    {y0 < 0 && y1 > 0 && <line x1={L} x2={W - R} y1={y(0)} y2={y(0)} stroke="#3d5168" />}
    <svg x={L} y={T} width={W - L - R} height={H - T - B} overflow="hidden"><g transform={`translate(${-L},${-T})`}>{children(x, y)}</g></svg>
    <text x={(L + W - R) / 2} y={H - 8} textAnchor="middle" className="pair-axis">{xLabel}</text>
    <text transform={`translate(14,${(T + H - B) / 2}) rotate(-90)`} textAnchor="middle" className="pair-axis">{yLabel}</text>
  </svg>;
}

const line = (points: { x: number; y: number }[]) => points.map((p, i) => `${i ? 'L' : 'M'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join('');

function MarkerShape({ m, cx, cy, big }: { m: Marker; cx: number; cy: number; big?: boolean }) {
  const r = big ? 7 : 5.5;
  const tip = `${m.name}\nRendimiento ${num(m.ret)} % · Volatilidad ${num(m.vol)} % · Desv. a la baja ${num(m.down)} %\nSharpe ${num(m.sharpe, 3)} · Sortino ${num(m.sortino, 3)}`;
  return <g><path d={`M${cx},${cy - r}L${cx + r},${cy}L${cx},${cy + r}L${cx - r},${cy}Z`} fill={color(m.name)} stroke="#0d1622" strokeWidth="1.4"><title>{tip}</title></path></g>;
}

function Legend({ items }: { items: { label: string; color: string; shape?: 'line' | 'dash' | 'dot' | 'square' | 'diamond' }[] }) {
  return <div className="pair-legend portfolio-legend">{items.map(item => <span key={item.label}>
    {item.shape === 'line' || item.shape === 'dash' ? <i className="legend-line" style={{ borderTopColor: item.color, borderTopStyle: item.shape === 'dash' ? 'dashed' : 'solid' }} />
      : <i style={{ background: item.color, borderRadius: item.shape === 'square' ? 2 : item.shape === 'diamond' ? 1 : '50%', transform: item.shape === 'diamond' ? 'rotate(45deg)' : undefined }} />}{item.label}</span>)}</div>;
}

function Figure({ title, note, children }: { title: string; note: string; children: ReactNode }) {
  return <figure className="portfolio-figure"><figcaption><strong>{title}</strong><span>{note}</span></figcaption>{children}</figure>;
}

function ColorBar({ lo, hi, name }: { lo: number; hi: number; name: string }) {
  return <div className="portfolio-colorbar"><span>{name} {num(lo, 2)}</span><i style={{ background: `linear-gradient(90deg, ${heat(lo, lo, hi)}, ${heat((lo + hi) / 2, lo, hi)}, ${heat(hi, lo, hi)})` }} /><span>{num(hi, 2)}</span></div>;
}

export default function PortfolioPlots({ data }: { data: PortfolioPlotData }) {
  const find = (name: string) => data.portfolios.find(p => p.name === name);
  const gmv = find('Mínima varianza'), tangent = find('Máximo Sharpe'), sortino = find('Máximo Sortino');
  const all = [...data.frontier, ...data.lower];
  const cloudX = data.cloud.map(c => c[0]), cloudY = data.cloud.map(c => c[1]);
  const volXs = [...cloudX, ...all.map(p => p.vol), ...data.assets.map(a => a.vol), ...data.portfolios.map(p => p.vol)];
  const retYs = [...cloudY, ...all.map(p => p.ret), ...data.assets.map(a => a.ret), ...data.portfolios.map(p => p.ret), data.risk_free];
  const downXs = [...data.cloud.map(c => c[2]), ...data.frontier.map(p => p.down), ...data.assets.map(a => a.down), ...data.portfolios.map(p => p.down)];
  const range = (values: (number | null)[]) => { const v = values.filter((x): x is number => x !== null && Number.isFinite(x)); return [Math.min(...v), Math.max(...v)] as const; };
  const [s0, s1] = range([...data.cloud.map(c => c[3]), ...data.portfolios.map(p => p.sharpe)]);
  const [o0, o1] = range([...data.cloud.map(c => c[4]), ...data.portfolios.map(p => p.sortino)]);
  const lowerPath = gmv ? [...data.lower, data.frontier[0]].filter(Boolean) : data.lower;
  // Línea del mercado de capitales: de (0, rf) a través del portafolio de máximo Sharpe, hasta la volatilidad máxima del gráfico.
  const capitalLine = (x: (v: number) => number, y: (v: number) => number, through: Marker | undefined, risk: (m: Marker) => number, maxX: number) =>
    through && risk(through) > 0 ? <path d={line([{ x: x(0), y: y(data.risk_free) }, { x: x(maxX), y: y(data.risk_free + (through.ret - data.risk_free) / risk(through) * maxX) }])} stroke={color(through.name)} strokeWidth="1.4" strokeDasharray="6 4" fill="none" opacity=".85" /> : null;
  const assetSquares = (x: (v: number) => number, y: (v: number) => number, key: 'vol' | 'down') => data.assets.map((a, i) => <g key={a.name}>
    <rect x={x(a[key]) - 4} y={y(a.ret) - 4} width="8" height="8" fill={ASSET_COLORS[i % ASSET_COLORS.length]} stroke="#0d1622"><title>{`${a.name}\nRendimiento ${num(a.ret)} % · ${key === 'vol' ? 'Volatilidad' : 'Desv. a la baja'} ${num(a[key])} %`}</title></rect>
    <text x={x(a[key]) + 7} y={y(a.ret) + 3} className="portfolio-label">{a.name}</text></g>);
  const maxVol = Math.max(...volXs) * 1.08, maxDown = Math.max(...downXs) * 1.08;

  return <section className="multi-plot portfolio-plots">
    <div className="result-title"><h3>Gráficos del portafolio</h3><span>Estimación con el bloque inicial · valores anualizados en %</span></div>
    <div className="portfolio-grid">
      <Figure title="Frontera eficiente" note="Rendimiento esperado frente a volatilidad. La rama punteada (debajo de la mínima varianza) es ineficiente: hay otro portafolio con igual riesgo y más rendimiento.">
        <Plane xLabel="Volatilidad anual (%)" yLabel="Rendimiento esperado anual (%)" xs={volXs} ys={retYs} label={`Frontera eficiente de ${data.columns.join(', ')} con ${data.portfolios.length} portafolios marcados.`}>
          {(x, y) => <>
            {data.cloud.map((c, i) => <circle key={i} cx={x(c[0])} cy={y(c[1])} r="1.8" fill="#6f879e" opacity=".35" />)}
            {capitalLine(x, y, tangent, m => m.vol, maxVol)}
            <path d={line(lowerPath.map(p => ({ x: x(p.vol), y: y(p.ret) })))} stroke="#79b4ef" strokeWidth="1.8" strokeDasharray="4 4" fill="none" />
            <path d={line(data.frontier.map(p => ({ x: x(p.vol), y: y(p.ret) })))} stroke="#6cc9ac" strokeWidth="2.6" fill="none" />
            {assetSquares(x, y, 'vol')}
            {data.portfolios.map(m => <MarkerShape key={m.name} m={m} cx={x(m.vol)} cy={y(m.ret)} />)}
          </>}
        </Plane>
        <Legend items={[{ label: 'Frontera eficiente', color: '#6cc9ac', shape: 'line' }, { label: 'Rama ineficiente', color: '#79b4ef', shape: 'dash' }, { label: 'Línea del mercado de capitales', color: color('Máximo Sharpe'), shape: 'dash' },
          { label: 'Portafolios aleatorios', color: '#6f879e' }, ...data.portfolios.map(p => ({ label: p.name, color: color(p.name), shape: 'diamond' as const })), { label: 'Activos', color: ASSET_COLORS[0], shape: 'square' }]} />
      </Figure>

      <Figure title="Ratio de Sharpe" note={`Cada punto es un portafolio factible coloreado por su Sharpe (exceso de rendimiento por unidad de volatilidad, rf = ${num(data.risk_free)} %). El máximo Sharpe es la tangencia entre la frontera y la recta que parte de rf.`}>
        <Plane xLabel="Volatilidad anual (%)" yLabel="Rendimiento esperado anual (%)" xs={volXs} ys={retYs} label={`Portafolios coloreados por Sharpe. Máximo Sharpe ${num(tangent?.sharpe, 3)}.`}>
          {(x, y) => <>
            {data.cloud.map((c, i) => <circle key={i} cx={x(c[0])} cy={y(c[1])} r="2.4" fill={heat(c[3], s0, s1)} opacity=".8" />)}
            <path d={line(data.frontier.map(p => ({ x: x(p.vol), y: y(p.ret) })))} stroke="#d5e4f5" strokeWidth="1.6" fill="none" opacity=".8" />
            {capitalLine(x, y, tangent, m => m.vol, maxVol)}
            <circle cx={x(0)} cy={y(data.risk_free)} r="3.5" fill="#d5e4f5"><title>{`Tasa libre de riesgo ${num(data.risk_free)} %`}</title></circle>
            {tangent && <><MarkerShape m={tangent} cx={x(tangent.vol)} cy={y(tangent.ret)} big /><text x={x(tangent.vol) + 9} y={y(tangent.ret) - 7} className="portfolio-label strong">Sharpe {num(tangent.sharpe, 3)}</text></>}
          </>}
        </Plane>
        <ColorBar lo={s0} hi={s1} name="Sharpe" />
      </Figure>

      <Figure title="Ratio de Sortino" note="Igual que Sharpe pero el riesgo es solo la desviación a la baja (rendimientos por debajo de rf). Premia portafolios cuyas caídas son pequeñas aunque su volatilidad total no lo sea.">
        <Plane xLabel="Desviación a la baja anual (%)" yLabel="Rendimiento esperado anual (%)" xs={downXs} ys={retYs} label={`Portafolios coloreados por Sortino. Máximo Sortino ${num(sortino?.sortino, 3)}.`}>
          {(x, y) => <>
            {data.cloud.map((c, i) => <circle key={i} cx={x(c[2])} cy={y(c[1])} r="2.4" fill={heat(c[4], o0, o1)} opacity=".8" />)}
            {capitalLine(x, y, sortino, m => m.down, maxDown)}
            <circle cx={x(0)} cy={y(data.risk_free)} r="3.5" fill="#d5e4f5"><title>{`Tasa libre de riesgo ${num(data.risk_free)} %`}</title></circle>
            {assetSquares(x, y, 'down')}
            {data.portfolios.filter(p => p.name !== 'Máximo Sortino').map(m => <circle key={m.name} cx={x(m.down)} cy={y(m.ret)} r="4" fill="none" stroke={color(m.name)} strokeWidth="1.6"><title>{`${m.name} · Sortino ${num(m.sortino, 3)}`}</title></circle>)}
            {sortino && <><MarkerShape m={sortino} cx={x(sortino.down)} cy={y(sortino.ret)} big /><text x={x(sortino.down) + 9} y={y(sortino.ret) - 7} className="portfolio-label strong">Sortino {num(sortino.sortino, 3)}</text></>}
          </>}
        </Plane>
        <ColorBar lo={o0} hi={o1} name="Sortino" />
      </Figure>

      <Figure title="Mínima varianza" note={gmv ? `El portafolio de mínima varianza global es el punto más a la izquierda de la frontera: volatilidad ${num(gmv.vol)} %, rendimiento ${num(gmv.ret)} %. Ningún otro portafolio factible tiene menos riesgo.` : 'Frontera completa de mínima varianza.'}>
        <Plane xLabel="Volatilidad anual (%)" yLabel="Rendimiento esperado anual (%)" xs={[...all.map(p => p.vol), ...data.assets.map(a => a.vol)]} ys={[...all.map(p => p.ret), ...data.assets.map(a => a.ret)]} label="Frontera de mínima varianza con el portafolio de mínima varianza global.">
          {(x, y) => <>
            <path d={line(lowerPath.map(p => ({ x: x(p.vol), y: y(p.ret) })))} stroke="#79b4ef" strokeWidth="1.8" strokeDasharray="4 4" fill="none" />
            <path d={line(data.frontier.map(p => ({ x: x(p.vol), y: y(p.ret) })))} stroke="#6cc9ac" strokeWidth="2.6" fill="none" />
            {assetSquares(x, y, 'vol')}
            {gmv && <><line x1={x(gmv.vol)} x2={x(gmv.vol)} y1={T} y2={H - B} stroke="#79b4ef" strokeDasharray="2 4" opacity=".7" />
              <MarkerShape m={gmv} cx={x(gmv.vol)} cy={y(gmv.ret)} big /><text x={x(gmv.vol) + 9} y={y(gmv.ret) + 16} className="portfolio-label strong">σ mín. {num(gmv.vol)} %</text></>}
          </>}
        </Plane>
        {gmv && <div className="portfolio-bars" aria-label="Pesos del portafolio de mínima varianza">{data.columns.map((c, i) => <div key={c}><span>{c}</span><i><b style={{ width: `${Math.max(0, gmv.weights[i])}%`, background: ASSET_COLORS[i % ASSET_COLORS.length] }} /></i><em>{num(gmv.weights[i], 1)} %</em></div>)}</div>}
      </Figure>

      <Figure title="Pesos de cada portafolio" note="Composición en % del capital. Las barras suman 100 %; solo posiciones largas.">
        <div className="portfolio-stack">{data.portfolios.map(p => <div key={p.name}><span style={{ color: color(p.name) }}>{p.name}</span><i>{p.weights.map((w, i) => w > .05 ? <b key={i} style={{ width: `${w}%`, background: ASSET_COLORS[i % ASSET_COLORS.length] }} title={`${data.columns[i]}: ${num(w, 2)} %`}>{w >= 9 ? `${num(w, 0)} %` : ''}</b> : null)}</i></div>)}</div>
        <Legend items={data.columns.map((c, i) => ({ label: c, color: ASSET_COLORS[i % ASSET_COLORS.length], shape: 'square' as const }))} />
        <div className="table-wrap"><table><thead><tr><th>Portafolio</th>{data.columns.map(c => <th key={c}>{c}</th>)}<th>Rend. (%)</th><th>Vol. (%)</th><th>Sharpe</th><th>Sortino</th></tr></thead>
          <tbody>{data.portfolios.map(p => <tr key={p.name}><td>{p.name}</td>{p.weights.map((w, i) => <td key={i}>{num(w, 2)}</td>)}<td>{num(p.ret)}</td><td>{num(p.vol)}</td><td>{num(p.sharpe, 3)}</td><td>{num(p.sortino, 3)}</td></tr>)}</tbody></table></div>
      </Figure>

      <Figure title="Composición a lo largo de la frontera" note="Cómo cambian los pesos al moverse de la mínima varianza (izquierda) al máximo rendimiento (derecha).">
        <FrontierWeights data={data} />
      </Figure>
    </div>
  </section>;
}

function FrontierWeights({ data }: { data: PortfolioPlotData }) {
  const f = data.frontier;
  if (f.length < 2) return <p className="subtle">La frontera tiene un solo punto.</p>;
  const x = (i: number) => L + i / (f.length - 1) * (W - L - R);
  const y = (v: number) => H - B - v / 100 * (H - T - B);
  const layers = data.columns.map((_, k) => {
    const lowerEdge = f.map(p => p.weights.slice(0, k).reduce((a, b) => a + b, 0));
    const upperEdge = f.map((p, i) => lowerEdge[i] + p.weights[k]);
    return `M${upperEdge.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join('L')}L${lowerEdge.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).reverse().join('L')}Z`;
  });
  return <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Pesos de los activos a lo largo de la frontera eficiente.">
    <rect x={L} y={T} width={W - L - R} height={H - T - B} className="multi-frame" />
    {layers.map((d, k) => <path key={k} d={d} fill={ASSET_COLORS[k % ASSET_COLORS.length]} opacity=".85"><title>{data.columns[k]}</title></path>)}
    {[0, 25, 50, 75, 100].map(v => <text key={v} x={L - 6} y={y(v) + 3} textAnchor="end" className="pair-tick">{v}</text>)}
    {[0, Math.floor((f.length - 1) / 2), f.length - 1].map(i => <text key={i} x={x(i)} y={H - B + 14} textAnchor="middle" className="pair-tick">{num(f[i].vol, 1)}</text>)}
    <text x={(L + W - R) / 2} y={H - 8} textAnchor="middle" className="pair-axis">Volatilidad del punto de la frontera (%)</text>
    <text transform={`translate(14,${(T + H - B) / 2}) rotate(-90)`} textAnchor="middle" className="pair-axis">Peso (%)</text>
  </svg>;
}
