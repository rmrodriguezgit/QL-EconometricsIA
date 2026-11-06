// Organización de la biblioteca por áreas (submenú) y búsqueda. Sin JSX para poder probarlo con node --test.
import areasFile from '../../../packages/contracts/toolAreas.json' with { type: 'json' };

export type ToolInfo = { label: string; detail: string; explanation?: string; superseded_by?: string | null; legacy?: boolean };
export type AreaGroup = { label: string; tools: string[] };
export type Area = { id: string; label: string; icon: string; description: string; groups: AreaGroup[] };

export const areas = (areasFile as { areas: Area[] }).areas;
export const ONLINE = new Set(['worldbank', 'worldbank_multi', 'fred', 'yfinance']);

const fold = (text: string) => text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

/** Herramientas que se muestran (las reemplazadas o heredadas siguen funcionando, pero no se ofrecen). */
export const isListed = (tool: ToolInfo | undefined) => !!tool && !tool.superseded_by && !tool.legacy;

/** Área de cada herramienta según toolAreas.json. */
export function areaOf(kind: string): Area | undefined {
  return areas.find(area => area.groups.some(group => group.tools.includes(kind)));
}

/** Grupos del área con solo las herramientas que existen en el catálogo y se ofrecen. */
export function areaGroups(areaId: string, catalog: Record<string, ToolInfo>): AreaGroup[] {
  const area = areas.find(item => item.id === areaId);
  return (area?.groups ?? []).map(group => ({ ...group, tools: group.tools.filter(kind => isListed(catalog[kind])) })).filter(group => group.tools.length);
}

export function areaCount(areaId: string, catalog: Record<string, ToolInfo>) {
  return areaGroups(areaId, catalog).reduce((total, group) => total + group.tools.length, 0);
}

/** Búsqueda sin acentos en nombre, descripción, explicación, área y grupo; las coincidencias en el nombre van primero. */
export function searchTools(query: string, catalog: Record<string, ToolInfo>): string[] {
  const words = fold(query.trim()).split(/\s+/).filter(Boolean);
  if (!words.length) return [];
  const scored: { kind: string; rank: number; order: number }[] = [];
  let order = 0;
  for (const area of areas) for (const group of area.groups) for (const kind of group.tools) {
    const tool = catalog[kind];
    order += 1;
    if (!isListed(tool)) continue;
    const label = fold(tool.label);
    const haystack = fold([kind, tool.label, tool.detail, tool.explanation ?? '', area.label, group.label].join(' '));
    if (!words.every(word => haystack.includes(word))) continue;
    scored.push({ kind, rank: words.every(word => label.includes(word)) ? 0 : 1, order });
  }
  return scored.sort((a, b) => a.rank - b.rank || a.order - b.order).map(entry => entry.kind);
}
