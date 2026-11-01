export type Kind = 'simulate' | 'csv' | 'worldbank' | 'describe' | 'scatter' | 'ols';
export type Parameters = Record<string, string | number>;
export type ProjectNode = { id: string; type: Kind; node_version: '1.0.0'; parameters: Parameters; position: { x: number; y: number } };
export type Project = { schema_version: '1.0.0'; app_version: string; title: string; nodes: ProjectNode[]; edges: { id: string; source: string; target: string; source_port: string; target_port: string }[] };
export type NodeResult = { status: 'succeeded' | 'failed' | 'skipped'; result?: Record<string, unknown>; error?: { code: string; message: string }; message?: string };
export type Run = { run_id: string; status: string; nodes: Record<string, NodeResult>; manifest: { graph_sha256: string; [key: string]: unknown } };
export const version = '0.2.0';
export const catalog: Record<Kind, { label: string; detail: string; category: string; color: string; references: string; explanation: string; defaults: Parameters }> = {
  simulate: { label: 'Datos simulados', detail: 'Una muestra que puedes reproducir', category: 'Fuentes de datos', color: 'green', references: 'B18 · B29', explanation: 'Consumo = intercepto + pendiente × ingreso + ruido normal. Cambia la semilla para obtener otra muestra o consérvala para repetir el experimento.', defaults: { n: 120, seed: 42, intercept: 12, slope: 0.72, noise: 9 } },
  csv: { label: 'Archivo CSV', detail: 'Tus datos, desde un archivo local', category: 'Fuentes de datos', color: 'green', references: 'B16', explanation: 'Importa hasta 10.000 filas y 50 columnas. Los datos faltantes permanecen explícitos; declara sus unidades antes de interpretar.', defaults: { content: '', delimiter: ',' } },
  worldbank: { label: 'Banco Mundial', detail: 'Indicadores económicos por país', category: 'Fuentes de datos', color: 'green', references: 'B01', explanation: 'Consulta un indicador anual por país. Requiere conexión. La ejecución registra consulta, fecha y huella de los datos; revisa las unidades del indicador.', defaults: { country: 'MEX', indicator: 'NY.GDP.PCAP.KD', start: 2000, end: 2023 } },
  describe: { label: 'Descriptivos', detail: 'Entiende la muestra antes de modelar', category: 'Exploración', color: 'blue', references: 'B18', explanation: 'Media, mediana, desviación estándar muestral y extremos. Cada columna informa su número de valores observados y faltantes.', defaults: {} },
  scatter: { label: 'Dispersión', detail: 'Explora la relación entre variables', category: 'Exploración', color: 'blue', references: 'B17', explanation: 'Cada punto es una observación completa de dos variables. Una asociación visual no demuestra causalidad.', defaults: { x: 'ingreso', y: 'consumo' } },
  ols: { label: 'Regresión OLS', detail: 'Estima una relación lineal simple', category: 'Modelos', color: 'purple', references: 'B03 · B23 · B29', explanation: 'y = β₀ + β₁x + ε. OLS estima los coeficientes que minimizan los residuos al cuadrado. HC3 ajusta los errores estándar ante heterocedasticidad; no identifica causalidad.', defaults: { x: 'ingreso', y: 'consumo', covariance: 'HC3' } },
};
export function starter(): Project {
  return { schema_version: '1.0.0', app_version: version, title: 'Ingreso y consumo', nodes: [
    { id: 'data', type: 'simulate', node_version: '1.0.0', parameters: { ...catalog.simulate.defaults }, position: { x: 30, y: 150 } },
    { id: 'summary', type: 'describe', node_version: '1.0.0', parameters: {}, position: { x: 350, y: 15 } },
    { id: 'model', type: 'ols', node_version: '1.0.0', parameters: { ...catalog.ols.defaults }, position: { x: 350, y: 160 } },
    { id: 'chart', type: 'scatter', node_version: '1.0.0', parameters: { ...catalog.scatter.defaults }, position: { x: 350, y: 305 } },
  ], edges: ['summary', 'model', 'chart'].map(target => ({ id: `data-${target}`, source: 'data', target, source_port: 'data', target_port: 'data' })) };
}
export function parseProject(text: string): Project {
  if (new TextEncoder().encode(text).length > 3_000_000) throw new Error('El proyecto supera 3 MB.');
  const value = JSON.parse(text);
  if (!value || value.schema_version !== '1.0.0' || typeof value.title !== 'string' || value.title.length > 120 || !Array.isArray(value.nodes) || !Array.isArray(value.edges) || value.nodes.length > 100 || value.edges.length > 400) throw new Error('Formato o versión de proyecto no compatible.');
  for (const node of value.nodes) {
    if (!node || typeof node.id !== 'string' || !Object.hasOwn(catalog, node.type) || node.node_version !== '1.0.0' || !node.parameters || Array.isArray(node.parameters) || typeof node.parameters !== 'object' || !Object.values(node.parameters).every(v => typeof v === 'string' || (typeof v === 'number' && Number.isFinite(v))) || !Number.isFinite(node.position?.x) || !Number.isFinite(node.position?.y)) throw new Error('El proyecto contiene un nodo inválido.');
  }
  for (const edge of value.edges) {
    if (!edge || !['id', 'source', 'target', 'source_port', 'target_port'].every(key => typeof edge[key] === 'string')) throw new Error('El proyecto contiene una conexión inválida.');
  }
  return value as Project;
}
export async function rpc<T>(method: string, params = {}): Promise<T> {
  const request = { jsonrpc: '2.0', id: crypto.randomUUID(), method, params };
  let response;
  if ('__TAURI_INTERNALS__' in window) {
    const { invoke } = await import('@tauri-apps/api/core');
    response = await invoke('engine_request', { request });
  } else {
    const http = await fetch('/api/rpc', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request) });
    if (!http.ok) throw new Error(await http.text());
    response = await http.json();
  }
  if (response.error) throw new Error(response.error.message);
  return response.result as T;
}
export function download(name: string, value: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }));
  const a = document.createElement('a'); a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
