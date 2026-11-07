import { numberFormat } from './numberFormat';
import { useMemo, useState } from 'react';
import { axisScale, useAxis } from './axisFormat';
import { niceTicks, residualHistogram } from './olsFitGeometry';

export type FitPlotData = { x: string; y: string; points: [number, number, number, number, number][]; band: [number, number, number, number][]; sigma: number; sampled: boolean; n: number; shown: number; outliers: number; note: string };
type Coefficient = { term: string; estimate: number };

const format = (v: number, digits = 3) => Number.isFinite(v) ? numberFormat({ maximumFractionDigits: digits }).format(v) : '—';
const W = 660, LEFT = 66, RIGHT = 92, TOP = 14, FIT_H = 250, GAP = 34, RES_H = 130, BOTTOM = 40;
const PLOT_W = W - LEFT - RIGHT, RES_TOP = TOP + FIT_H + GAP, H = RES_TOP + RES_H + BOTTOM;

/** Recta OLS con banda IC 95 %, residuos como segmentos verticales y panel de residuos con su histograma. */
export default function OlsFitPlot({ data, coefficients, rSquared }: { data: FitPlotData; coefficients?: Coefficient[]; rSquared?: number }) {
  const [segments, setSegments] = useState(true);
  const [band, setBand] = useState(true);
  const [against, setAgainst] = useState<'x' | 'fitted'>('x');
  const [hover, setHover] = useState<number | null>(null);
  const axis = useAxis();
  const points = data.points;
  const b0 = coefficients?.find(c => c.term === 'const')?.estimate, b1 = coefficients?.find(c => c.term !== 'const')?.estimate;

  const geometry = useMemo(() => {
    const xs = points.map(p => p[0]), ys = [...points.map(p => p[1]), ...data.band.flatMap(b => [b[2], b[3]])];
    const [x0, x1] = [Math.min(...xs), Math.max(...xs)], [y0, y1] = [Math.min(...ys), Math.max(...ys)];
    const xPad = (x1 - x0 || 1) * .03, yPad = (y1 - y0 || 1) * .06;
    const xTicks = niceTicks(x0 - xPad, x1 + xPad, 6), yTicks = niceTicks(y0 - yPad, y1 + yPad, 5);
    const xd: [number, number] = [x0 - xPad, x1 + xPad];
    const yd: [number, number] = [y0 - yPad, y1 + yPad];
    const limit = Math.max(2.6 * data.sigma, ...points.map(p => Math.abs(p[3]))) * 1.08 || 1;
    const fittedValues = points.map(p => p[2]), f0 = Math.min(...fittedValues), f1 = Math.max(...fittedValues), fPad = (f1 - f0 || 1) * .03;
    return { xd, yd, xTicks: xTicks.filter(t => t >= xd[0] && t <= xd[1]), yTicks: yTicks.filter(t => t >= yd[0] && t <= yd[1]), limit, fd: [f0 - fPad, f1 + fPad] as [number, number],
      histogram: residualHistogram(points.map(p => p[3]), limit, 16) };
  }, [points, data.band, data.sigma]);

  const sx = (v: number) => LEFT + (v - geometry.xd[0]) / (geometry.xd[1] - geometry.xd[0]) * PLOT_W;
  const sy = (v: number) => TOP + (1 - (v - geometry.yd[0]) / (geometry.yd[1] - geometry.yd[0])) * FIT_H;
  const rx = (p: number[]) => against === 'x' ? sx(p[0]) : LEFT + (p[2] - geometry.fd[0]) / (geometry.fd[1] - geometry.fd[0]) * PLOT_W;
  const ry = (e: number) => RES_TOP + (1 - (e + geometry.limit) / (2 * geometry.limit)) * RES_H;
  const fx = axisScale(geometry.xTicks, axis.x, v => format(v, 2)), fy = axisScale(geometry.yTicks, axis.y, v => format(v, 2));
  const fr = axisScale([-geometry.limit, geometry.limit], axis.y, v => format(v, 2));
  const fTicks = niceTicks(geometry.fd[0], geometry.fd[1], 6).filter(t => t >= geometry.fd[0] && t <= geometry.fd[1]);
  const ff = axisScale(fTicks, axis.x, v => format(v, 2));
  const resTicks = niceTicks(-geometry.limit, geometry.limit, 4).filter(t => Math.abs(t) <= geometry.limit);
  const sign = (e: number) => e >= 0 ? 'above' : 'below';
  const histMax = Math.max(1, ...geometry.histogram.counts);
  const binH = RES_H / geometry.histogram.counts.length;
  const normal = (e: number) => Math.exp(-.5 * (e / data.sigma) ** 2) / (data.sigma * Math.sqrt(2 * Math.PI));
  const scaleNormal = points.length * geometry.histogram.width;
  const current = hover === null ? null : points[hover];
  const upper = data.band.map(b => `${sx(b[0])},${sy(b[3])}`), lower = data.band.map(b => `${sx(b[0])},${sy(b[2])}`).reverse();
  const yName = fy.label(data.y), xName = against === 'x' ? fx.label(data.x) : ff.label(`ŷ (${data.y} ajustado)`);

  return <figure className="ols-fit">
    <figcaption className="ols-fit-header">
      <div className="ols-fit-equation">{b0 !== undefined && b1 !== undefined ? <>ŷ = {format(b0)} {b1 < 0 ? '−' : '+'} {format(Math.abs(b1))}·{data.x}</> : `${data.y} sobre ${data.x}`}</div>
      <div className="ols-fit-chips">{rSquared !== undefined && <span>R² {format(rSquared)}</span>}<span>σ̂ {format(data.sigma)}</span><span>n {format(data.n, 0)}</span><span className={data.outliers ? 'warn' : ''}>{data.outliers} con |r| &gt; 2</span></div>
      <div className="ols-fit-controls" role="group" aria-label="Opciones del gráfico">
        <button className={segments ? 'active' : ''} aria-pressed={segments} onClick={() => setSegments(v => !v)}>Residuos</button>
        <button className={band ? 'active' : ''} aria-pressed={band} onClick={() => setBand(v => !v)}>Banda IC 95 %</button>
        <button className={against === 'fitted' ? 'active' : ''} aria-pressed={against === 'fitted'} onClick={() => setAgainst(v => v === 'x' ? 'fitted' : 'x')}>Residuos vs ŷ</button>
      </div>
    </figcaption>
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Regresión OLS de ${data.y} sobre ${data.x} con ${points.length} puntos, recta ajustada, residuos y panel de residuos`} onMouseLeave={() => setHover(null)}>
      {geometry.yTicks.map(t => <g key={`y${t}`}><line className="grid" x1={LEFT} x2={LEFT + PLOT_W} y1={sy(t)} y2={sy(t)} /><text x={LEFT - 8} y={sy(t) + 4} textAnchor="end">{fy.tick(t)}</text></g>)}
      {geometry.xTicks.map(t => <line key={`x${t}`} className="grid" x1={sx(t)} x2={sx(t)} y1={TOP} y2={TOP + FIT_H} />)}
      <rect className="frame" x={LEFT} y={TOP} width={PLOT_W} height={FIT_H} />
      {band && <polygon className="ci-band" points={[...upper, ...lower].join(' ')} />}
      {segments && points.map((p, i) => <line key={`s${i}`} className={`residual ${sign(p[3])}`} x1={sx(p[0])} x2={sx(p[0])} y1={sy(p[1])} y2={sy(p[2])} />)}
      <polyline className="fit-line" points={data.band.map(b => `${sx(b[0])},${sy(b[1])}`).join(' ')} />
      {points.map((p, i) => <circle key={`p${i}`} className={`point ${Math.abs(p[4]) > 2 ? 'outlier' : ''} ${hover === i ? 'hover' : ''}`} cx={sx(p[0])} cy={sy(p[1])} r={hover === i ? 5 : 3.2} onMouseEnter={() => setHover(i)} />)}
      <text className="axis-label" transform={`translate(16,${TOP + FIT_H / 2}) rotate(-90)`} textAnchor="middle">{yName}</text>

      <g className="legend" transform={`translate(${LEFT + PLOT_W + 12},${TOP + 6})`}>
        <line x1="0" x2="18" y1="6" y2="6" className="fit-line" /><text x="23" y="9">Recta OLS</text>
        <rect x="0" y="18" width="18" height="10" className="ci-band" /><text x="23" y="27">IC 95 %</text>
        <line x1="9" x2="9" y1="36" y2="50" className="residual above" /><text x="23" y="46">e &gt; 0</text>
        <line x1="9" x2="9" y1="56" y2="70" className="residual below" /><text x="23" y="66">e &lt; 0</text>
        <circle cx="9" cy="82" r="3.6" className="point outlier" /><text x="23" y="86">|r| &gt; 2</text>
      </g>

      {/* Panel de residuos */}
      <rect className="frame" x={LEFT} y={RES_TOP} width={PLOT_W} height={RES_H} />
      {resTicks.map(t => <g key={`r${t}`}><line className="grid" x1={LEFT} x2={LEFT + PLOT_W} y1={ry(t)} y2={ry(t)} /><text x={LEFT - 8} y={ry(t) + 4} textAnchor="end">{fr.tick(t)}</text></g>)}
      {[-2, 2].map(k => Math.abs(k * data.sigma) <= geometry.limit && <g key={k}><line className="sigma-line" x1={LEFT} x2={LEFT + PLOT_W} y1={ry(k * data.sigma)} y2={ry(k * data.sigma)} /><text className="sigma-label" x={LEFT + PLOT_W - 4} y={ry(k * data.sigma) + (k > 0 ? -4 : 11)} textAnchor="end">{k > 0 ? '+2σ̂' : '−2σ̂'}</text></g>)}
      <line className="zero-line" x1={LEFT} x2={LEFT + PLOT_W} y1={ry(0)} y2={ry(0)} />
      {points.map((p, i) => <g key={`e${i}`}>{segments && <line className={`residual ${sign(p[3])}`} x1={rx(p)} x2={rx(p)} y1={ry(0)} y2={ry(p[3])} />}<circle className={`point small ${sign(p[3])} ${Math.abs(p[4]) > 2 ? 'outlier' : ''} ${hover === i ? 'hover' : ''}`} cx={rx(p)} cy={ry(p[3])} r={hover === i ? 4.5 : 2.6} onMouseEnter={() => setHover(i)} /></g>)}
      <text className="axis-label" transform={`translate(16,${RES_TOP + RES_H / 2}) rotate(-90)`} textAnchor="middle">{fr.label('Residuo e')}</text>
      {(against === 'x' ? geometry.xTicks : fTicks).map(t => { const x = against === 'x' ? sx(t) : LEFT + (t - geometry.fd[0]) / (geometry.fd[1] - geometry.fd[0]) * PLOT_W; return <text key={`t${t}`} x={x} y={RES_TOP + RES_H + 16} textAnchor="middle">{(against === 'x' ? fx : ff).tick(t)}</text>; })}
      {geometry.xTicks.map(t => <line key={`m${t}`} className="tick" x1={sx(t)} x2={sx(t)} y1={TOP + FIT_H} y2={TOP + FIT_H + 4} />)}
      {geometry.xTicks.map(t => <text key={`f${t}`} x={sx(t)} y={TOP + FIT_H + 15} textAnchor="middle" className="minor">{fx.tick(t)}</text>)}
      <text className="axis-label" x={LEFT + PLOT_W / 2} y={H - 8} textAnchor="middle">{xName}</text>

      {/* Histograma marginal de residuos con la normal N(0, σ̂²) */}
      <g className="residual-hist">
        {geometry.histogram.counts.map((count, k) => <rect key={k} x={LEFT + PLOT_W + 6} y={RES_TOP + k * binH + .5} width={count / histMax * (RIGHT - 22)} height={Math.max(0, binH - 1)} />)}
        <polyline className="normal-curve" points={Array.from({ length: 41 }, (_, k) => { const e = geometry.limit - k / 40 * 2 * geometry.limit; return `${LEFT + PLOT_W + 6 + normal(e) * scaleNormal / histMax * (RIGHT - 22)},${ry(e)}`; }).join(' ')} />
        <text x={W - 4} y={RES_TOP - 5} textAnchor="end">Distribución</text>
      </g>

      {current && <g className="tooltip" transform={`translate(${Math.min(sx(current[0]) + 10, LEFT + PLOT_W - 150)},${Math.max(TOP + 4, Math.min(sy(current[1]) - 70, TOP + FIT_H - 80))})`}>
        <rect width="150" height="76" rx="5" />
        <text x="9" y="16">{data.x} = {format(current[0])}</text>
        <text x="9" y="31">{data.y} = {format(current[1])}</text>
        <text x="9" y="46">ŷ = {format(current[2])}</text>
        <text x="9" y="61" className={sign(current[3])}>e = {format(current[3])} · r = {format(current[4], 2)}</text>
      </g>}
    </svg>
    <p className="ols-fit-note">{data.note}{data.sampled ? ` Se dibujan ${format(data.shown, 0)} de ${format(data.n, 0)} puntos (muestra fija), siempre con los residuos más extremos.` : ''} En el panel inferior los residuos deberían repartirse sin patrón alrededor de 0; un abanico sugiere heterocedasticidad y una curva, una relación no lineal.</p>
  </figure>;
}
