// Formato de ejes común a las visualizaciones: números completos o notación científica con factor ×10ⁿ.
import { createContext, useContext } from 'react';
import { fullNumber, SCIENTIFIC_FROM } from './numberFormat.ts';

export type AxisMode = 'auto' | 'cientifica' | 'normal';
export const AXIS_KEYS = ['y_axis', 'x_axis'] as const;
/** Parámetros que solo cambian la presentación: no invalidan resultados ya calculados. */
export const DISPLAY_KEYS = new Set<string>(AXIS_KEYS);

const SUPERSCRIPT: Record<string, string> = { '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹' };
export const superscript = (value: number) => String(value).split('').map(char => SUPERSCRIPT[char] ?? char).join('');
const plain = (value: number) => new Intl.NumberFormat('es-MX', { maximumSignificantDigits: 4 }).format(value);

export type AxisScale = {
  /** Texto de cada marca del eje (mantisa si hay factor). */
  tick: (value: number) => string;
  /** «×10⁹» o cadena vacía. */
  factor: string;
  exponent: number;
  /** Nombre del eje con el factor: «fin_cons (×10¹²)». */
  label: (name: string) => string;
};

/**
 * Escala de un eje a partir de sus valores visibles.
 * - normal: números completos (formato propio del gráfico).
 * - cientifica: siempre ×10ⁿ con n = orden de magnitud del mayor valor absoluto (si n ≠ 0).
 * - auto: ×10ⁿ solo cuando |valor| ≥ 10⁴ o < 10⁻², donde los números completos estorban.
 */
export function axisScale(values: number[], mode: AxisMode = 'auto', fallback: (value: number) => string = plain): AxisScale {
  const finite = values.filter(Number.isFinite);
  const largest = finite.length ? Math.max(...finite.map(Math.abs)) : 0;
  const exponent = largest > 0 ? Math.floor(Math.log10(largest)) : 0;
  const scientific = exponent !== 0 && (mode === 'cientifica' || (mode === 'auto' && (exponent >= 4 || exponent <= -3)));
  // «normal» pide números completos aunque el formato propio del gráfico abrevie las cifras de miles de millones.
  if (!scientific) return { tick: mode === 'normal' ? value => Math.abs(value) >= SCIENTIFIC_FROM ? fullNumber(value) : fallback(value) : fallback, factor: '', exponent: 0, label: name => name };
  const scale = 10 ** exponent;
  const factor = `×10${superscript(exponent)}`;
  // Decimales según el rango visible, para que marcas cercanas no se vean iguales.
  const span = finite.length ? (Math.max(...finite) - Math.min(...finite)) / scale : 1;
  const digits = span > 0 ? Math.min(4, Math.max(1, 1 - Math.floor(Math.log10(span / 4)))) : 2;
  const format = new Intl.NumberFormat('es-MX', { maximumFractionDigits: digits });
  return { tick: value => format.format(value / scale), factor, exponent, label: name => `${name} (${factor})` };
}

/** Formato de valor suelto (tooltips): número completo o mantisa ×10ⁿ. */
export function scientificValue(value: number, mode: AxisMode = 'auto', fallback: (value: number) => string = plain) {
  const scale = axisScale([value], mode, fallback);
  return scale.factor ? `${scale.tick(value)}${scale.factor}` : fallback(value);
}

export const AxisContext = createContext<{ x: AxisMode; y: AxisMode }>({ x: 'auto', y: 'auto' });
export const useAxis = () => useContext(AxisContext);
export function axisModes(parameters: Record<string, unknown> | undefined): { x: AxisMode; y: AxisMode } {
  const pick = (value: unknown): AxisMode => value === 'cientifica' || value === 'normal' ? value : 'auto';
  return { x: pick(parameters?.x_axis), y: pick(parameters?.y_axis) };
}
