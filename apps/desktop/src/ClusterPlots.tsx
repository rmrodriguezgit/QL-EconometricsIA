// Gráficos del modelo k-means: mapa de grupos con envolventes y centroides, silueta, elección de k y perfil de centroides.
import type { ReactNode } from 'react';

type Group = { group: number; n: number; share: number; sse: number; silhouette: number | null; negative: number; values: number[] };
export type ClusterPlotData = {
  features: string[]; axes: [string, string]; explained: [number, number] | null; k: number; n: number;
  points: [number, number, number][]; centroids: [number, number][]; centers: number[][]; profile: number[][];
  groups: Group[]; curve: { k: number; inertia: number; silhouette: number | null }[]; silhouette_mean: number;
  sampled_points: boolean; sampled_silhouette: boolean;
};

const COLORS = ['#6cc9ac', '#79b4ef', '#ffd166', '#f4a3a9', '#b295ee', '#8adde4', '#f6a96b', '#c6d3e4', '#9be37a', '#e39bd6'];
const color = (g: number) => COLORS[g % COLORS.length];
const num = (v: number | null | undefined, digits = 2) => v === null || v === undefined || !Number.isFinite(v) ? '—' : new Intl.NumberFormat('es-MX', { maximumFractionDigits: digits }).format(v);
const W = 470, H = 320, L = 58, R = 16, T = 18, B = 46;

function ticks(lo: number, hi: number, count = 5) { return Array.from({ length: count }, (_, i) => lo + (hi - lo) * i / (count - 1)); }
function padded(values: number[], share = .07) {
  const lo = Math.min(...values), hi = Math.max(...values), pad = (hi - lo || Math.abs(hi) || 1) * share;
  return [lo - pad, hi + pad] as const;
}

/** Envolvente convexa (cadena monótona de Andrew). */
function hull(points: [number, number][]) {
  const p = [...points].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  if (p.length < 3) return p;
  const cross = (o: number[], a: number[], b: number[]) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lower: [number, number][] = [], upper: [number, number][] = [];
  for (const q of p) { while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], q) <= 0) lower.pop(); lower.push(q); }
  for (const q of [...p].reverse()) { while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], q) <= 0) upper.pop(); upper.push(q); }
  return [...lower.slice(0, -1), ...upper.slice(0, -1)];
}

function Frame({ xLabel, yLabel, x0, x1, y0, y1, children, label, yTicks, xTicks, right }: {
  xLabel: string; yLabel: string; x0: number; x1: number; y0: number; y1: number; label: string; right?: ReactNode;
  children: (x: (v: number) => number, y: (v: number) => number) => ReactNode; yTicks?: number[]; xTicks?: number[];
}) {
  const x = (v: number) => L + (v - x0) / (x1 - x0 || 1) * (W - L - R);
  const y = (v: number) => H - B - (v - y0) / (y1 - y0 || 1) * (H - T - B);
  return <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={label}>
    <rect x={L} y={T} width={W - L - R} height={H - T - B} className="multi-frame" />
    {(yTicks ?? ticks(y0, y1)).map(v => <g key={`y${v}`}><line x1={L} x2={W - R} y1={y(v)} y2={y(v)} className="multi-grid" /><text x={L - 6} y={y(v) + 3} textAnchor="end" className="pair-tick">{num(v, 2)}</text></g>)}
    {(xTicks ?? ticks(x0, x1)).map(v => <g key={`x${v}`}><line x1={x(v)} x2={x(v)} y1={T} y2={H - B} className="multi-grid" /><text x={x(v)} y={H - B + 14} textAnchor="middle" className="pair-tick">{num(v, 2)}</text></g>)}
    {children(x, y)}
    {right}
    <text x={(L + W - R) / 2} y={H - 8} textAnchor="middle" className="pair-axis">{xLabel}</text>
    <text transform={`translate(14,${(T + H - B) / 2}) rotate(-90)`} textAnchor="middle" className="pair-axis">{yLabel}</text>
  </svg>;
}

function Figure({ title, note, children }: { title: string; note: string; children: ReactNode }) {
  return <figure className="portfolio-figure"><figcaption><strong>{title}</strong><span>{note}</span></figcaption>{children}</figure>;
}

function ClusterMap({ data }: { data: ClusterPlotData }) {
  const [x0, x1] = padded([...data.points.map(p => p[0]), ...data.centroids.map(c => c[0])]);
  const [y0, y1] = padded([...data.points.map(p => p[1]), ...data.centroids.map(c => c[1])]);
  const r = data.points.length > 1200 ? 1.8 : data.points.length > 400 ? 2.4 : 3.2;
  return <Frame xLabel={data.axes[0]} yLabel={data.axes[1]} x0={x0} x1={x1} y0={y0} y1={y1} label={`Mapa de ${data.k} grupos k-means con ${data.n} observaciones.`}>
    {(x, y) => <>
      {data.groups.map(g => { const h = hull(data.points.filter(p => p[2] === g.group).map(p => [p[0], p[1]] as [number, number])); return h.length > 2
        ? <path key={`h${g.group}`} d={`M${h.map(p => `${x(p[0]).toFixed(1)},${y(p[1]).toFixed(1)}`).join('L')}Z`} fill={color(g.group)} fillOpacity=".08" stroke={color(g.group)} strokeOpacity=".55" strokeWidth="1.2" strokeDasharray="4 3" /> : null; })}
      {data.points.map((p, i) => <circle key={i} cx={x(p[0])} cy={y(p[1])} r={r} fill={color(p[2])} fillOpacity=".75" stroke="#0d1622" strokeWidth=".4" />)}
      {data.centroids.map((c, g) => <g key={`c${g}`}>
        <circle cx={x(c[0])} cy={y(c[1])} r="9" fill="#0d1622" stroke={color(g)} strokeWidth="2.4"><title>{`Centroide del grupo ${g}: ${data.features.map((f, i) => `${f} = ${num(data.centers[g][i], 3)}`).join(', ')}`}</title></circle>
        <text x={x(c[0])} y={y(c[1]) + 3.5} textAnchor="middle" className="cluster-centroid-label" style={{ fill: color(g) }}>{g}</text>
      </g>)}
    </>}
  </Frame>;
}

function SilhouettePlot({ data }: { data: ClusterPlotData }) {
  const all = data.groups.flatMap(g => g.values);
  const lo = Math.min(-0.1, Math.floor(Math.min(...all) * 10) / 10), hi = 1;
  const gap = 6, total = all.length + gap * (data.groups.length - 1);
  const h = H - T - B;
  const x = (v: number) => L + (v - lo) / (hi - lo) * (W - L - R);
  let offset = 0;
  return <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Silueta por observación; media ${num(data.silhouette_mean, 3)}.`}>
    <rect x={L} y={T} width={W - L - R} height={h} className="multi-frame" />
    {ticks(lo, hi, 6).map(v => <g key={v}><line x1={x(v)} x2={x(v)} y1={T} y2={H - B} className="multi-grid" /><text x={x(v)} y={H - B + 14} textAnchor="middle" className="pair-tick">{num(v, 1)}</text></g>)}
    <line x1={x(0)} x2={x(0)} y1={T} y2={H - B} stroke="#5a6f88" />
    {data.groups.map(g => {
      const start = offset; offset += g.values.length + gap;
      const band = h / total;
      const top = T + start * band;
      const d = g.values.map((v, i) => `M${x(0).toFixed(1)},${(top + (i + .5) * band).toFixed(2)}H${x(v).toFixed(1)}`).join('');
      return <g key={g.group}>
        <path d={d} stroke={color(g.group)} strokeWidth={Math.max(band, .6)} opacity=".9"><title>{`Grupo ${g.group}: ${g.n} observaciones, silueta media ${num(g.silhouette, 3)}, ${g.negative} negativas`}</title></path>
        <text x={L - 6} y={top + g.values.length * band / 2 + 4} textAnchor="end" className="cluster-group-tick" style={{ fill: color(g.group) }}>{g.group}</text>
      </g>;
    })}
    <line x1={x(data.silhouette_mean)} x2={x(data.silhouette_mean)} y1={T} y2={H - B} stroke="#ff7a90" strokeWidth="1.6" strokeDasharray="5 4" />
    <text x={Math.min(x(data.silhouette_mean), W - R - 40)} y={T - 3} textAnchor="middle" className="portfolio-label strong" style={{ fill: '#ff9aab' }}>media {num(data.silhouette_mean, 3)}</text>
    <text x={(L + W - R) / 2} y={H - 8} textAnchor="middle" className="pair-axis">Coeficiente de silueta</text>
    <text transform={`translate(14,${(T + H - B) / 2}) rotate(-90)`} textAnchor="middle" className="pair-axis">Grupo (observaciones ordenadas)</text>
  </svg>;
}

function ElbowPlot({ data }: { data: ClusterPlotData }) {
  const ks = data.curve.map(c => c.k);
  if (ks.length < 2) return <p className="subtle">Se necesitan más observaciones para comparar valores de k.</p>;
  const [i0, i1] = padded(data.curve.map(c => c.inertia), .08);
  const sils = data.curve.map(c => c.silhouette).filter((v): v is number => v !== null);
  const s0 = Math.min(0, ...sils), s1 = Math.max(1, ...sils);
  const ys = (v: number) => H - B - (v - s0) / (s1 - s0) * (H - T - B);
  return <Frame xLabel="Número de grupos (k)" yLabel="Inercia (suma de cuadrados intra)" x0={ks[0] - .3} x1={ks[ks.length - 1] + .3} y0={Math.max(0, i0)} y1={i1} xTicks={ks} label="Inercia y silueta media según el número de grupos."
    right={<>{ticks(s0, s1, 5).map(v => <text key={v} x={W - R + 3} y={ys(v) + 3} className="pair-tick cluster-right-tick">{num(v, 2)}</text>)}</>}>
    {(x, y) => <>
      <rect x={x(data.k) - 14} y={T} width="28" height={H - T - B} fill="#ffd16614" stroke="#ffd16666" strokeDasharray="3 3" />
      <path d={data.curve.map((c, i) => `${i ? 'L' : 'M'}${x(c.k).toFixed(1)},${y(c.inertia).toFixed(1)}`).join('')} stroke="#79b4ef" strokeWidth="2.4" fill="none" />
      {data.curve.map(c => <circle key={`i${c.k}`} cx={x(c.k)} cy={y(c.inertia)} r={c.k === data.k ? 5.5 : 3.5} fill="#79b4ef" stroke="#0d1622"><title>{`k = ${c.k}: inercia ${num(c.inertia, 3)}`}</title></circle>)}
      <path d={data.curve.filter(c => c.silhouette !== null).map((c, i) => `${i ? 'L' : 'M'}${x(c.k).toFixed(1)},${ys(c.silhouette as number).toFixed(1)}`).join('')} stroke="#ffd166" strokeWidth="2" strokeDasharray="6 4" fill="none" />
      {data.curve.filter(c => c.silhouette !== null).map(c => <circle key={`s${c.k}`} cx={x(c.k)} cy={ys(c.silhouette as number)} r={c.k === data.k ? 5.5 : 3.5} fill="#ffd166" stroke="#0d1622"><title>{`k = ${c.k}: silueta media ${num(c.silhouette, 3)}`}</title></circle>)}
      <text x={x(data.k)} y={T + 12} textAnchor="middle" className="portfolio-label strong cluster-halo">k elegido = {data.k}</text>
    </>}
  </Frame>;
}

/** Color divergente: azul (por debajo de la media) → neutro → ámbar (por encima). */
function diverging(z: number) {
  const t = Math.max(-1, Math.min(1, z / 2));
  const [a, b] = t < 0 ? [[22, 33, 48], [70, 140, 220]] : [[22, 33, 48], [240, 170, 70]];
  const u = Math.abs(t);
  return `rgb(${a.map((c, i) => Math.round(c + (b[i] - c) * u)).join(',')})`;
}

function Profile({ data }: { data: ClusterPlotData }) {
  return <div className="cluster-profile">
    <div className="table-wrap"><table className="cluster-heat"><thead><tr><th>Grupo</th><th>Tamaño</th>{data.features.map(f => <th key={f}>{f}</th>)}</tr></thead>
      <tbody>{data.groups.map(g => <tr key={g.group}>
        <td><span className="cluster-swatch" style={{ background: color(g.group) }} />{g.group}</td>
        <td><div className="cluster-size"><i style={{ width: `${g.share}%`, background: color(g.group) }} /><span>{g.n} · {num(g.share, 1)} %</span></div></td>
        {data.profile[g.group].map((z, i) => <td key={i} style={{ background: diverging(z) }} title={`${data.features[i]}: centroide ${num(data.centers[g.group][i], 3)} (${num(z, 2)} DE de la media)`}>{num(data.centers[g.group][i], 2)}<small>{z >= 0 ? '+' : ''}{num(z, 1)} DE</small></td>)}
      </tr>)}</tbody></table></div>
    <div className="portfolio-colorbar"><span>Por debajo de la media</span><i style={{ background: `linear-gradient(90deg, ${diverging(-2)}, ${diverging(0)}, ${diverging(2)})` }} /><span>Por encima</span></div>
  </div>;
}

export default function ClusterPlots({ data }: { data: ClusterPlotData }) {
  const best = data.curve.filter(c => c.silhouette !== null).reduce<typeof data.curve[number] | null>((a, c) => !a || (c.silhouette as number) > (a.silhouette as number) ? c : a, null);
  return <section className="multi-plot portfolio-plots">
    <div className="result-title"><h3>Gráficos de k-means</h3><span>{data.k} grupos · {data.n} observaciones · silueta media {num(data.silhouette_mean, 3)}</span></div>
    <div className="pair-legend portfolio-legend">{data.groups.map(g => <span key={g.group}><i style={{ background: color(g.group) }} />Grupo {g.group} · {g.n} obs. ({num(g.share, 1)} %)</span>)}</div>
    <div className="portfolio-grid">
      <Figure title="Mapa de grupos" note={data.explained ? `Proyección en los dos primeros componentes principales de las variables estandarizadas (${num(data.explained[0] + data.explained[1], 1)} % de la varianza). Los grupos se calcularon con todas las variables.` : 'Cada punto es una observación coloreada por su grupo; la línea punteada envuelve el grupo y el círculo numerado marca su centroide.'}>
        <ClusterMap data={data} />
        {data.sampled_points && <p className="subtle">Se dibuja una muestra aleatoria de {data.points.length} puntos.</p>}
      </Figure>
      <Figure title="Silueta por observación" note="Qué tan cerca está cada observación de su grupo frente al grupo vecino: cerca de 1 = bien asignada, cerca de 0 = en la frontera, negativa = probablemente en el grupo equivocado.">
        <SilhouettePlot data={data} />
        {data.sampled_silhouette && <p className="subtle">Silueta calculada en una muestra aleatoria de 2000 observaciones.</p>}
      </Figure>
      <Figure title="Elección de k" note={`Inercia (línea azul, eje izquierdo): baja siempre al añadir grupos; busca el «codo». Silueta media (ámbar, eje derecho): más alta es mejor${best ? `; aquí la máxima es k = ${best.k}` : ''}.`}>
        <ElbowPlot data={data} />
      </Figure>
      <Figure title="Perfil de los grupos" note="Centroide de cada grupo en la escala de entrada; el color indica cuántas desviaciones estándar se aleja de la media general de la variable.">
        <Profile data={data} />
      </Figure>
    </div>
  </section>;
}
