// Geometría del plano de regresión 3D (sin React, para poder probarla con Node).
export type Plane3DData = { features: string[]; y: string; n: number; shown: number; coefficients: Record<string, number>; means: Record<string, number>; rows: number[][] };
export type PartialData = { y: string; n: number; items: { feature: string; slope: number; coefficient: number; std_error: number; p_value: number; partial_r: number; points: [number, number][] }[] };

/** Prepara puntos y plano para dos regresores; los demás se fijan en su media y la respuesta se ajusta por ellos. */
export function planeGeometry(data: Plane3DData, a: string, b: string) {
  const ia = data.features.indexOf(a), ib = data.features.indexOf(b), iy = data.features.length;
  const others = data.features.filter(name => name !== a && name !== b);
  const beta = data.coefficients;
  const intercept = (beta.const ?? 0) + others.reduce((sum, name) => sum + beta[name] * data.means[name], 0);
  const plane = (xa: number, xb: number) => intercept + beta[a] * xa + beta[b] * xb;
  const points = data.rows.map(row => {
    // y* = y − Σ βj (xj − x̄j) para j ∉ {a, b}: la distancia vertical al plano es exactamente el residuo.
    const adjusted = row[iy] - others.reduce((sum, name) => sum + beta[name] * (row[data.features.indexOf(name)] - data.means[name]), 0);
    return { xa: row[ia], xb: row[ib], y: adjusted, residual: row[iy] - row[iy + 1] };
  });
  return { points, plane, intercept, others };
}

