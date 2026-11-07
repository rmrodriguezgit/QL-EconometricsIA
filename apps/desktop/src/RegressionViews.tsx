// Vistas del OLS múltiple: plano de regresión 3D giratorio y gráficos de variable añadida (Frisch–Waugh–Lovell).
import { numberFormat } from './numberFormat';
import { useEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent, type KeyboardEvent } from 'react';
import { axisScale, useAxis } from './axisFormat';
import { planeGeometry, type Plane3DData, type PartialData } from './regressionGeometry';
export type { Plane3DData, PartialData } from './regressionGeometry';

const plain = (value: number) => numberFormat({ maximumSignificantDigits: 3 }).format(value);
const pFormat = (p: number) => p < 1e-4 ? '< 0.0001' : p.toFixed(4);
const VIEWS = { inicial: { yaw: -0.65, pitch: 0.42 }, x1: { yaw: 0, pitch: 0 }, x2: { yaw: -Math.PI / 2, pitch: 0 }, arriba: { yaw: 0, pitch: 1.5 } };

const range = (values: number[]) => { const lo = Math.min(...values), hi = Math.max(...values); return lo === hi ? [lo - 1, hi + 1] : [lo, hi]; };

export function RegressionPlane3D({ data }: { data: Plane3DData }) {
  const axis = useAxis();
  const [a, setA] = useState(data.features[0]);
  const [b, setB] = useState(data.features[1] ?? data.features[0]);
  const [view, setView] = useState(VIEWS.inicial);
  const [zoom, setZoom] = useState(1);
  const [spin, setSpin] = useState(false);
  const [residuals, setResiduals] = useState(true);
  const drag = useRef<{ x: number; y: number } | null>(null);
  useEffect(() => {
    if (!spin) return;
    let frame = requestAnimationFrame(function step() { setView(current => ({ ...current, yaw: current.yaw + 0.008 })); frame = requestAnimationFrame(step); });
    return () => cancelAnimationFrame(frame);
  }, [spin]);
  const geometry = useMemo(() => planeGeometry(data, a, b), [data, a, b]);
  const [ax0, ax1] = range(geometry.points.map(p => p.xa)), [bx0, bx1] = range(geometry.points.map(p => p.xb));
  const corners = [geometry.plane(ax0, bx0), geometry.plane(ax0, bx1), geometry.plane(ax1, bx0), geometry.plane(ax1, bx1)];
  const [y0, y1] = range([...geometry.points.map(p => p.y), ...corners]);
  const norm = (value: number, lo: number, hi: number) => (value - lo) / (hi - lo) * 2 - 1;
  const width = 640, height = 500, scale = 118 * zoom;
  const cos = Math.cos(view.yaw), sin = Math.sin(view.yaw), cp = Math.cos(view.pitch), sp = Math.sin(view.pitch);
  // Rotación alrededor del eje vertical (yaw) y luego inclinación (pitch); proyección ortográfica.
  const project = (X: number, Y: number, Z: number) => {
    const x1 = X * cos - Y * sin, y1 = X * sin + Y * cos;
    const depth = y1 * cp - Z * sp, up = y1 * sp + Z * cp;
    return { x: width / 2 + x1 * scale, y: height / 2 + 10 - up * scale, depth };
  };
  const world = (xa: number, xb: number, y: number) => project(norm(xa, ax0, ax1), norm(xb, bx0, bx1), norm(y, y0, y1));
  const sa = axisScale([ax0, ax1], axis.x, plain), sb = axisScale([bx0, bx1], axis.x, plain), sy = axisScale([y0, y1], axis.y, plain);
  const grid = Array.from({ length: 9 }, (_, i) => i / 8);
  const planeLines = [
    ...grid.map(t => [world(ax0 + (ax1 - ax0) * t, bx0, geometry.plane(ax0 + (ax1 - ax0) * t, bx0)), world(ax0 + (ax1 - ax0) * t, bx1, geometry.plane(ax0 + (ax1 - ax0) * t, bx1))]),
    ...grid.map(t => [world(ax0, bx0 + (bx1 - bx0) * t, geometry.plane(ax0, bx0 + (bx1 - bx0) * t)), world(ax1, bx0 + (bx1 - bx0) * t, geometry.plane(ax1, bx0 + (bx1 - bx0) * t))]),
  ];
  const polygon = [[ax0, bx0], [ax1, bx0], [ax1, bx1], [ax0, bx1]].map(([xa, xb]) => world(xa, xb, geometry.plane(xa, xb)));
  const cube = [-1, 1].flatMap(i => [-1, 1].flatMap(j => [[[-1, i, j], [1, i, j]], [[i, -1, j], [i, 1, j]], [[i, j, -1], [i, j, 1]]])) as [number[], number[]][];
  const drawn = geometry.points.map((p, i) => ({ i, p, at: world(p.xa, p.xb, p.y), foot: world(p.xa, p.xb, geometry.plane(p.xa, p.xb)) })).sort((u, v) => v.at.depth - u.at.depth);
  const depths = drawn.map(d => d.at.depth), dmin = Math.min(...depths), dmax = Math.max(...depths);
  const above = geometry.points.filter(p => p.residual > 0).length;
  const onDown = (event: ReactPointerEvent<SVGSVGElement>) => { drag.current = { x: event.clientX, y: event.clientY }; event.currentTarget.setPointerCapture(event.pointerId); setSpin(false); };
  const onMove = (event: ReactPointerEvent<SVGSVGElement>) => {
    if (!drag.current) return;
    const dx = event.clientX - drag.current.x, dy = event.clientY - drag.current.y;
    drag.current = { x: event.clientX, y: event.clientY };
    setView(current => ({ yaw: current.yaw - dx * 0.01, pitch: Math.max(-1.55, Math.min(1.55, current.pitch + dy * 0.01)) }));
  };
  const onKey = (event: KeyboardEvent<SVGSVGElement>) => {
    const step = { ArrowLeft: [0.1, 0], ArrowRight: [-0.1, 0], ArrowUp: [0, -0.1], ArrowDown: [0, 0.1] }[event.key];
    if (!step) return;
    event.preventDefault();
    setView(current => ({ yaw: current.yaw + step[0], pitch: Math.max(-1.55, Math.min(1.55, current.pitch + step[1])) }));
  };
  const label = (X: number, Y: number, Z: number, text: string, anchor: 'start' | 'middle' | 'end' = 'middle', cls = 'pair-tick') => { const at = project(X, Y, Z); return <text x={at.x} y={at.y} textAnchor={anchor} className={cls}>{text}</text>; };
  const signed = (value: number) => `${value < 0 ? '−' : '+'} ${plain(Math.abs(value))}`;
  return <section className="plane3d">
    <div className="result-title"><h3>Plano de regresión en 3D</h3><span>{data.shown < data.n ? `${data.shown} de ${data.n} puntos` : `${data.n} puntos`} · arrastra para girar</span></div>
    <div className="plane3d-controls">
      {data.features.length > 2 && <>
        <label>Eje 1<select value={a} onChange={event => { const next = event.target.value; if (next === b) setB(a); setA(next); }}>{data.features.map(name => <option key={name}>{name}</option>)}</select></label>
        <label>Eje 2<select value={b} onChange={event => { const next = event.target.value; if (next === a) setA(b); setB(next); }}>{data.features.map(name => <option key={name}>{name}</option>)}</select></label>
      </>}
      <div className="plane3d-buttons" role="group" aria-label="Vista del plano">
        <button type="button" onClick={() => { setView(VIEWS.inicial); setZoom(1); }}>Vista inicial</button>
        <button type="button" onClick={() => setView(VIEWS.x1)}>De frente a {a}</button>
        <button type="button" onClick={() => setView(VIEWS.x2)}>De frente a {b}</button>
        <button type="button" onClick={() => setView(VIEWS.arriba)}>Desde arriba</button>
        <button type="button" aria-pressed={spin} onClick={() => setSpin(value => !value)}>{spin ? 'Detener giro' : 'Girar'}</button>
        <button type="button" aria-pressed={residuals} onClick={() => setResiduals(value => !value)}>Residuos</button>
        <button type="button" aria-label="Acercar" onClick={() => setZoom(value => Math.min(3, value * 1.2))}>+</button>
        <button type="button" aria-label="Alejar" onClick={() => setZoom(value => Math.max(0.5, value / 1.2))}>−</button>
      </div>
    </div>
    <svg className="plane3d-canvas" viewBox={`0 0 ${width} ${height}`} tabIndex={0} role="img"
      aria-label={`Plano ŷ = ${plain(geometry.intercept)} ${signed(data.coefficients[a])}·${a} ${signed(data.coefficients[b])}·${b}. ${above} puntos sobre el plano y ${geometry.points.length - above} debajo. Usa las flechas para girar.`}
      onPointerDown={onDown} onPointerMove={onMove} onPointerUp={() => { drag.current = null; }} onPointerCancel={() => { drag.current = null; }} onKeyDown={onKey}>
      {cube.map(([p, q], i) => { const u = project(p[0], p[1], p[2]), v = project(q[0], q[1], q[2]); return <line key={i} x1={u.x} y1={u.y} x2={v.x} y2={v.y} className="plane3d-box" />; })}
      <polygon points={polygon.map(p => `${p.x},${p.y}`).join(' ')} className="plane3d-surface" />
      {planeLines.map(([u, v], i) => <line key={i} x1={u.x} y1={u.y} x2={v.x} y2={v.y} className="plane3d-grid" />)}
      {drawn.map(({ i, p, at, foot }) => {
        const fade = dmax === dmin ? 1 : 0.45 + 0.55 * (dmax - at.depth) / (dmax - dmin);
        const tone = p.residual > 0 ? '#6cc9ac' : '#f4a3a9';
        return <g key={i} opacity={fade}>
          {residuals && <line x1={at.x} y1={at.y} x2={foot.x} y2={foot.y} stroke={tone} strokeWidth="1" opacity=".55" />}
          <circle cx={at.x} cy={at.y} r={2.4 * Math.sqrt(zoom)} fill={tone}><title>{`${a} = ${plain(p.xa)}, ${b} = ${plain(p.xb)}, ${data.y}${geometry.others.length ? '*' : ''} = ${plain(p.y)}, residuo = ${plain(p.residual)}`}</title></circle>
        </g>;
      })}
      {/* Cada eje en su propia arista para que las marcas no coincidan en una esquina. */}
      {label(-1, -1.22, -1, sa.tick(ax0))}{label(1, -1.22, -1, sa.tick(ax1))}{label(0, -1.42, -1, sa.label(a), 'middle', 'pair-axis')}
      {label(1.22, -1, -1, sb.tick(bx0))}{label(1.22, 1, -1, sb.tick(bx1))}{label(1.42, 0, -1, sb.label(b), 'middle', 'pair-axis')}
      {label(-1.16, -1, -0.92, sy.tick(y0), 'end')}{label(-1.16, -1, 1, sy.tick(y1), 'end')}{label(-1, -1, 1.18, sy.label(geometry.others.length ? `${data.y}*` : data.y), 'middle', 'pair-axis')}
      {[[-1, -1, -1, 1, -1, -1], [1, -1, -1, 1, 1, -1], [-1, -1, -1, -1, -1, 1]].map(([p1, p2, p3, q1, q2, q3], i) => { const u = project(p1, p2, p3), v = project(q1, q2, q3); return <line key={`axis-${i}`} x1={u.x} y1={u.y} x2={v.x} y2={v.y} className="plane3d-axis" />; })}
    </svg>
    <div className="pair-legend"><span><i style={{ background: '#6cc9ac' }} />Sobre el plano (residuo &gt; 0) · {above}</span><span><i style={{ background: '#f4a3a9' }} />Debajo (residuo &lt; 0) · {geometry.points.length - above}</span></div>
    <p className="result-footnote">ŷ = {plain(geometry.intercept)} {signed(data.coefficients[a])}·{a} {signed(data.coefficients[b])}·{b}
      {geometry.others.length ? `. Corte del modelo con ${geometry.others.join(', ')} en su media: ${data.y}* = ${data.y} − Σ βⱼ(xⱼ − x̄ⱼ) descuenta su efecto, así que la distancia vertical de cada punto al plano es su residuo exacto.` : '. La línea vertical de cada punto al plano es su residuo.'} La perspectiva 3D puede engañar: confirma con los gráficos de variable añadida.</p>
  </section>;
}

export function AddedVariablePlots({ data }: { data: PartialData }) {
  const axis = useAxis();
  const width = 300, height = 230, left = 46, bottom = 34, top = 10, right = 10;
  return <section className="added-variable">
    <div className="result-title"><h3>Gráficos de variable añadida</h3><span>Regresión parcial · un panel por regresor</span></div>
    <div className="added-variable-grid">{data.items.map(item => {
      const xs = item.points.map(p => p[0]), ys = item.points.map(p => p[1]);
      const [x0, x1] = range(xs), [y0, y1] = range(ys);
      const x = (v: number) => left + (v - x0) / (x1 - x0) * (width - left - right);
      const y = (v: number) => top + (1 - (v - y0) / (y1 - y0)) * (height - top - bottom);
      const sx = axisScale([x0, x1], axis.x, plain), sy = axisScale([y0, y1], axis.y, plain);
      const significant = item.p_value < 0.05;
      return <figure key={item.feature} className="added-variable-panel">
        <figcaption><strong>{item.feature}</strong><span className={significant ? 'ok' : ''}>β = {plain(item.coefficient)} · EE {plain(item.std_error)} · p {pFormat(item.p_value)} · r parcial {Number.isFinite(item.partial_r) ? item.partial_r.toFixed(2) : '—'}</span></figcaption>
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Variable añadida de ${item.feature}: pendiente ${plain(item.slope)}, igual al coeficiente del modelo múltiple.`}>
          <rect x={left} y={top} width={width - left - right} height={height - top - bottom} className="multi-frame" />
          {[y0, (y0 + y1) / 2, y1].map(v => <g key={v}><line x1={left} x2={width - right} y1={y(v)} y2={y(v)} className="multi-grid" /><text x={left - 4} y={y(v) + 3} textAnchor="end" className="pair-tick">{sy.tick(v)}</text></g>)}
          {[x0, x1].map(v => <text key={v} x={x(v)} y={height - bottom + 12} textAnchor={v === x0 ? 'start' : 'end'} className="pair-tick">{sx.tick(v)}</text>)}
          {item.points.map(([u, v], i) => <circle key={i} cx={x(u)} cy={y(v)} r="2.2" fill="#79b4ef" opacity=".7" />)}
          {Number.isFinite(item.slope) && <line x1={x(x0)} y1={y(item.slope * x0)} x2={x(x1)} y2={y(item.slope * x1)} stroke="#ffd166" strokeWidth="2" />}
          <text x={(width + left) / 2} y={height - 4} textAnchor="middle" className="pair-axis">{sx.label(`${item.feature} | demás`)}</text>
          <text transform={`translate(11,${(height - bottom + top) / 2}) rotate(-90)`} textAnchor="middle" className="pair-axis">{sy.label(`${data.y} | demás`)}</text>
        </svg>
      </figure>;
    })}</div>
    <p className="result-footnote">Cada panel muestra los residuos de {data.y} frente a los residuos del regresor, ambos tras descontar los demás regresores. Por el teorema de Frisch–Waugh–Lovell la pendiente amarilla es exactamente el coeficiente del modelo múltiple; los puntos alejados de la recta son los que más influyen en ese coeficiente.</p>
  </section>;
}
