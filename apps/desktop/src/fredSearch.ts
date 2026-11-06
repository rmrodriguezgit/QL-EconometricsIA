// Búsqueda local en el catálogo curado de FRED (sin red): ID, alias, título en español o inglés y tema.
import fred from '../../../packages/contracts/fredCatalog.json' with { type: 'json' };

export type FredItem = { id: string; alias: string; title: string; title_en?: string; units: string; frequency: string; seasonal: string; group: string };
type RawCatalog = { items?: unknown; groups?: unknown };

/** Catálogo tolerante: sin `items` queda vacío; sin `groups` (o con temas que faltan) los temas salen de los items. */
export function normalizeCatalog(raw: RawCatalog | null | undefined): { items: FredItem[]; groups: Record<string, string> } {
  const items = (Array.isArray(raw?.items) ? raw.items : []).filter((item): item is FredItem =>
    !!item && typeof item === 'object' && typeof (item as FredItem).id === 'string').map(item => ({
      ...item, alias: item.alias ?? '', title: item.title ?? item.id, units: item.units ?? '', frequency: item.frequency ?? '',
      seasonal: item.seasonal ?? '', group: item.group ?? 'otros' }));
  const declared = raw?.groups && typeof raw.groups === 'object' && !Array.isArray(raw.groups) ? raw.groups as Record<string, string> : {};
  const groups: Record<string, string> = {};
  for (const [key, label] of Object.entries(declared)) if (typeof label === 'string') groups[key] = label;
  for (const item of items) if (!(item.group in groups)) groups[item.group] = item.group === 'otros' ? 'Otros' : item.group;
  return { items, groups };
}

const catalog = normalizeCatalog(fred as RawCatalog);
export const fredItems = catalog.items;
export const fredGroups = catalog.groups;

const fold = (text: string) => text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

/** Coincidencias ordenadas: ID exacto, ID que empieza igual, y luego el resto en el orden del catálogo. */
export function searchFred(query: string, group = '', items: FredItem[] = fredItems, groups: Record<string, string> = fredGroups): FredItem[] {
  const words = fold(query.trim()).split(/\s+/).filter(Boolean);
  const pool = group ? items.filter(item => item.group === group) : items;
  if (!words.length) return pool;
  const scored = pool.map((item, index) => {
    const haystack = fold([item.id, item.alias, item.title, item.title_en ?? '', item.units, item.frequency, groups[item.group] ?? ''].join(' '));
    if (!words.every(word => haystack.includes(word))) return null;
    const id = item.id.toLowerCase(), first = words[0];
    return { item, rank: id === first ? 0 : id.startsWith(first) ? 1 : fold(item.title).includes(first) ? 2 : 3, index };
  }).filter((entry): entry is { item: FredItem; rank: number; index: number } => entry !== null);
  return scored.sort((a, b) => a.rank - b.rank || a.index - b.index).map(entry => entry.item);
}

/** ¿El texto parece un identificador de FRED escrito a mano? (misma regla que el motor). */
export const looksLikeFredId = (text: string) => /^[A-Z0-9][A-Z0-9_]{0,39}$/.test(text.trim().toUpperCase());
