/** Marcas «redondas» (1, 2, 2.5, 5 × 10ⁿ) que cubren [low, high]. */
export function niceTicks(low: number, high: number, count = 5): number[] {
  if (!Number.isFinite(low) || !Number.isFinite(high)) return [];
  if (low === high) return [low];
  if (low > high) [low, high] = [high, low];
  const raw = (high - low) / Math.max(1, count);
  const power = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map(m => m * power).find(s => s >= raw) ?? 10 * power;
  const start = Math.floor(low / step + 1e-9) * step, end = Math.ceil(high / step - 1e-9) * step, ticks: number[] = [];
  for (let v = start; v <= end + step * 1e-9; v += step) ticks.push(Number((Math.abs(v) < step * 1e-9 ? 0 : v).toPrecision(12)));
  return ticks;
}

/** Histograma de residuos en `bins` intervalos de [−limit, limit], ordenado de arriba (+limit) abajo (−limit). */
export function residualHistogram(residuals: number[], limit: number, bins = 16) {
  const width = 2 * limit / bins, counts = new Array<number>(bins).fill(0);
  for (const e of residuals) {
    if (!Number.isFinite(e)) continue;
    const k = Math.min(bins - 1, Math.max(0, Math.floor((limit - e) / width)));
    counts[k] += 1;
  }
  return { counts, width };
}
