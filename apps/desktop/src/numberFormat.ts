// Formato numérico común de tablas, métricas y etiquetas: las cifras de miles de millones o más (|x| ≥ 10⁹) se escriben
// en notación científica (2.534 × 10¹³) para no mostrar números de 13 dígitos (PIB, población o comercio del Banco Mundial).
const SUPERSCRIPT: Record<string, string> = { '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹' };
const superscript = (value: number) => String(value).split('').map(char => SUPERSCRIPT[char] ?? char).join('');

/** Umbral desde el que una cifra se escribe en notación científica: mil millones. */
export const SCIENTIFIC_FROM = 1e9;
const mantissa = new Intl.NumberFormat('es-MX', { maximumFractionDigits: 3 });
const full = new Intl.NumberFormat('es-MX', { maximumFractionDigits: 0 });

/** Mantisa con 4 cifras significativas y potencia de diez: «−1.25 × 10⁹». */
export function scientific(value: number) {
  let exponent = Math.floor(Math.log10(Math.abs(value)));
  let base = Number((value / 10 ** exponent).toFixed(3));
  if (Math.abs(base) >= 10) { base /= 10; exponent += 1; }
  return `${mantissa.format(base)} × 10${superscript(exponent)}`;
}

/** Número con el formato pedido, o en notación científica si |valor| ≥ 10⁹. */
export function formatNumber(value: number, options: Intl.NumberFormatOptions = { maximumFractionDigits: 3 }) {
  return Number.isFinite(value) && Math.abs(value) >= SCIENTIFIC_FROM ? scientific(value) : new Intl.NumberFormat('es-MX', options).format(value);
}

/** Número completo, sin notación científica (eje en modo «normal»). */
export const fullNumber = (value: number) => full.format(value);

/** Sustituto de `new Intl.NumberFormat('es-MX', options)` con el mismo `format` y el umbral científico. */
export const numberFormat = (options: Intl.NumberFormatOptions = {}) => ({ format: (value: number) => formatNumber(value, options) });
