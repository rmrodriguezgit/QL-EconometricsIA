const format = (v: unknown, digits = 3) => typeof v === 'number' ? new Intl.NumberFormat('es-MX', { maximumFractionDigits: digits }).format(v) : '—';
export default function Scatter({ result, model }: { result: Record<string, unknown>; model?: Record<string, unknown> }) {
  const points = result.points as [number, number][];
  const xs = points.map(p => p[0]), ys = points.map(p => p[1]);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  const pad = (maxY - minY || 1) * .12;
  const x = (v: number) => 54 + (v - minX) / (maxX - minX || 1) * 405;
  const y = (v: number) => 174 - (v - (minY - pad)) / (maxY - minY + 2 * pad) * 150;
  const coefficients = model?.coefficients as { estimate: number }[] | undefined;
  const line = coefficients && model?.x === result.x && model?.y === result.y && model?.input_source_id === result.input_source_id;
  return <svg className="scatter" viewBox="0 0 490 218" role="img" aria-label={`Dispersión de ${result.x} y ${result.y}, ${points.length} observaciones. Los datos también pueden exportarse en resultados JSON.`}>
    {[0, 1, 2, 3].map(i => { const v = minY + (maxY - minY) * i / 3; return <g key={i}><line x1="54" x2="459" y1={y(v)} y2={y(v)} stroke="#2d3b4e" /><text x="44" y={y(v) + 4} textAnchor="end">{format(v, 0)}</text></g>; })}
    {points.map((p, i) => <circle key={i} cx={x(p[0])} cy={y(p[1])} r="2.8" fill="#259476" opacity=".65" />)}
    {line && <line x1={x(minX)} x2={x(maxX)} y1={y(coefficients[0].estimate + coefficients[1].estimate * minX)} y2={y(coefficients[0].estimate + coefficients[1].estimate * maxX)} className="regression-line" stroke="#ffd166" strokeWidth="3" strokeLinecap="round" />}
    {[0, 1, 2, 3, 4].map(i => { const v = minX + (maxX - minX) * i / 4; return <text key={i} x={x(v)} y="194" textAnchor="middle">{format(v, 0)}</text>; })}
    <text x="258" y="213" textAnchor="middle" className="axis-label">{String(result.x)}</text>
    <text transform="translate(13,100) rotate(-90)" textAnchor="middle" className="axis-label">{String(result.y)}</text>
    {line && <g aria-label="Recta de regresión OLS"><line x1="315" x2="338" y1="12" y2="12" stroke="#ffd166" strokeWidth="3"/><text x="345" y="15" className="regression-legend">Recta OLS</text></g>}
  </svg>;
}

