// Búsqueda local en el catálogo curado de FRED (sin red): ID, alias, título en español o inglés y tema.
import fred from '../../../packages/contracts/fredCatalog.json' with { type: 'json' };

export type FredItem = { id: string; alias: string; title: string; title_en?: string; units: string; frequency: string; seasonal: string; group: string };
export const fredItems = fred.items as FredItem[];
export const fredGroups = fred.groups as Record<string, string>;

const fold = (text: string) => text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

/** Coincidencias ordenadas: ID exacto, ID que empieza igual, y luego el resto en el orden del catálogo. */
export function searchFred(query: string, group = '', items: FredItem[] = fredItems): FredItem[] {
  const words = fold(query.trim()).split(/\s+/).filter(Boolean);
  const pool = group ? items.filter(item => item.group === group) : items;
  if (!words.length) return pool;
  const scored = pool.map((item, index) => {
    const haystack = fold([item.id, item.alias, item.title, item.title_en ?? '', item.units, item.frequency, fredGroups[item.group] ?? ''].join(' '));
    if (!words.every(word => haystack.includes(word))) return null;
    const id = item.id.toLowerCase(), first = words[0];
    return { item, rank: id === first ? 0 : id.startsWith(first) ? 1 : fold(item.title).includes(first) ? 2 : 3, index };
  }).filter((entry): entry is { item: FredItem; rank: number; index: number } => entry !== null);
  return scored.sort((a, b) => a.rank - b.rank || a.index - b.index).map(entry => entry.item);
}

/** ¿El texto parece un identificador de FRED escrito a mano? (misma regla que el motor). */
export const looksLikeFredId = (text: string) => /^[A-Z0-9][A-Z0-9_]{0,39}$/.test(text.trim().toUpperCase());
