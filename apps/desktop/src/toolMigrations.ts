// Conversión de una herramienta reemplazada en la recomendada (mismo contrato que usa el Cerebro IA en el motor).
import file from '../../../packages/contracts/toolMigrations.json' with { type: 'json' };

type Rule = string | { value?: string | number; template?: string };
type Migration = { to: string; chain?: boolean; params: Record<string, Rule> };
type Node = { id: string; type: string; parameters: Record<string, string | number> };
type Edge = { id: string; source: string; target: string; source_port: string; target_port: string };
type Tool = { defaults: Record<string, string | number>; inputs: Record<string, string>; outputs: Record<string, string> };

export const migrations = (file as { migrations: Record<string, Migration> }).migrations;

/** Parámetros de la herramienta nueva a partir de los de la antigua (los no mapeados toman los valores por defecto). */
export function migrateParameters(kind: string, parameters: Record<string, string | number>): Record<string, string | number> | null {
  const rule = migrations[kind];
  if (!rule || rule.chain) return null;
  const out: Record<string, string | number> = {};
  for (const [key, source] of Object.entries(rule.params)) {
    if (typeof source === 'string') { if (parameters[source] !== undefined) out[key] = parameters[source]; }
    else if (source.value !== undefined) out[key] = source.value;
    else if (source.template) out[key] = source.template.replace(/\{(\w+)\}/g, (_, name) => String(parameters[name] ?? ''));
  }
  return out;
}

/** Cambia el nodo de tipo conservando su id y las conexiones cuyos puertos siguen existiendo. */
export function migrateNode<P extends { nodes: Node[]; edges: Edge[] }>(project: P, nodeId: string, catalog: Record<string, Tool>): { project: P; dropped: number } | null {
  const node = project.nodes.find(item => item.id === nodeId);
  const rule = node && migrations[node.type];
  const parameters = node && migrateParameters(node.type, node.parameters);
  if (!node || !rule || !parameters || !catalog[rule.to]) return null;
  const target = catalog[rule.to];
  const keep = (edge: Edge) => (edge.source !== nodeId || edge.source_port in target.outputs) && (edge.target !== nodeId || edge.target_port in target.inputs);
  const edges = project.edges.filter(keep);
  return {
    project: { ...project, nodes: project.nodes.map(item => item.id === nodeId ? { ...item, type: rule.to, parameters: { ...target.defaults, ...parameters } } : item), edges },
    dropped: project.edges.length - edges.length,
  };
}
