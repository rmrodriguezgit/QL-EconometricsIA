// Lista «CÓDIGO: alias» del nodo Banco Mundial · varios indicadores (misma sintaxis que interpreta el motor).
export type IndicatorRow = { code: string; alias: string };

export function parseIndicatorList(value: unknown): IndicatorRow[] {
  return String(value ?? '').split(/[\n;,]+/).map(item => item.trim()).filter(Boolean).map(item => {
    const separator = item.includes(':') ? ':' : '=';
    const [code, ...rest] = item.split(separator);
    return { code: code.trim(), alias: rest.join(separator).trim() };
  });
}

export function serializeIndicatorList(rows: IndicatorRow[]): string {
  return rows.filter(row => row.code.trim()).map(row => `${row.code.trim()}: ${row.alias.trim()}`).join('\n');
}

export function suggestAlias(code: string): string {
  return code.toLowerCase().replace(/[^a-z0-9_]/g, '_').replace(/^(\d)/, '_$1');
}

export const validAlias = (alias: string) => /^[A-Za-z_][A-Za-z0-9_]{0,40}$/.test(alias) && !['periodo', 'pais', 'iso3'].includes(alias);

/** Columnas numéricas que producirá la fuente: periodo y un alias por indicador. */
export function indicatorColumns(value: unknown): string[] {
  return ['periodo', ...parseIndicatorList(value).map(row => row.alias || suggestAlias(row.code))];
}
