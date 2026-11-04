"""Compila un plan (del modelo o de las reglas) en un proyecto Quantlabs válido.

Respeta la mecánica de construcción existente: solo nodos del catálogo, parámetros
declarados en ``defaults``, puertos tipados con una conexión por entrada, DAG sin
ciclos y guía paso a paso con un paso por nodo. Después puede ejecutar el flujo
para reparar nombres de columnas con las vistas previas reales de cada puerto.
"""
from collections import defaultdict
import re

from ..core import NODE_CATALOG, SCHEMA, VERSION, EngineError, execute, validate_project
from .knowledge import EXCLUDED_TOOLS, fold

SOURCES = {kind for kind, definition in NODE_CATALOG.items()
           if not definition['inputs'] and definition['outputs'].get('data') == 'Dataset'}
SINGLE_COLUMNS = {'x', 'y', 'column', 'value', 'nominal', 'index', 'population', 'returns', 'signal', 'before', 'after', 'error', 'time', 'group'}
MULTI_COLUMNS = {'columns', 'features', 'instruments'}
TARGET_NAMES = ['y', 'consumo', 'clase', 'produccion', 'valor', 'ventas', 'retorno', 'despues', 'lwage', 'wage', 'precio']
MAX_STEPS = 12
LINEAR = {'ols', 'multiple_ols', 'ecm', 'covariance'}
# Qué nodos productores de FittedModel acepta cada consumidor (según tools.py y normality_tools.py).
MODEL_ACCEPTS = {
    'diagnostics': LINEAR | {'garch'}, 'covariance': LINEAR, 'residual_normality': {'ols', 'multiple_ols', 'robust', 'covariance'},
    'silhouette': {'kmeans'}, 'evaluate': {'ols', 'multiple_ols', 'robust', 'iv2sls', 'logit', 'ecm', 'covariance', 'wls', 'mlp', 'arima', 'hmm', 'gmm'},
    'compare_models': {'ols', 'multiple_ols', 'robust', 'iv2sls', 'logit', 'ecm', 'covariance', 'wls', 'mlp', 'arima'},
}


def slug(value, used):
    base = re.sub(r'[^a-z0-9_-]+', '_', fold(value or 'paso')).strip('_')[:40] or 'paso'
    name, i = base, 2
    while name in used:
        name, i = f'{base}_{i}', i + 1
    used.add(name)
    return name


def clean_parameters(kind, raw):
    """Parámetros por defecto del catálogo + valores válidos propuestos."""
    definition = NODE_CATALOG[kind]
    params = dict(definition.get('defaults', {}))
    choices = definition.get('choices', {})
    notes = []
    for key, value in (raw or {}).items():
        if key not in params:
            notes.append(f'{kind}: se ignoró el parámetro desconocido «{key}».')
            continue
        default = params[key]
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            continue
        if isinstance(default, (int, float)) and not isinstance(default, bool):
            try:
                number = float(value)
            except (TypeError, ValueError):
                notes.append(f'{kind}: «{key}» debe ser numérico; se conserva {default}.')
                continue
            value = int(number) if isinstance(default, int) and number.is_integer() else number
        else:
            value = str(value)[:2000]
        if key in choices and value not in choices[key]:
            notes.append(f'{kind}: «{value}» no es una opción de «{key}»; se conserva {default}.')
            continue
        params[key] = value
    return params, notes


def compile_plan(plan, prompt=''):
    """Devuelve (proyecto, informe). El informe incluye pasos descartados y huecos."""
    report = {'notes': [], 'dropped': [], 'gaps': []}
    used, nodes, explanations, by_step = set(), [], {}, {}
    produced = []  # (node_id, port, tipo) en orden de creación
    node_types = {}
    steps = [step for step in plan.get('steps', []) if isinstance(step, dict)][:MAX_STEPS]
    for gap in plan.get('missing', []) or []:
        if isinstance(gap, dict) and gap.get('name'):
            report['gaps'].append(gap)
    if not any(step.get('tool') in SOURCES for step in steps):
        steps.insert(0, {'id': 'datos', 'tool': 'synthetic', 'parameters': {'scenario': 'regression'},
                         'why': 'Fuente añadida automáticamente: el plan no tenía datos de entrada.'})
        report['notes'].append('Se añadió una fuente sintética porque el plan no tenía datos.')
    for step in steps:
        kind = step.get('tool')
        if not isinstance(kind, str) or kind not in NODE_CATALOG or kind in EXCLUDED_TOOLS:
            report['gaps'].append({'name': str(kind)[:80], 'purpose': str(step.get('why', ''))[:400],
                                   'inputs': step.get('inputs_types', {}), 'outputs': {}})
            report['dropped'].append({'tool': kind, 'reason': 'No existe en el catálogo; se registró como herramienta faltante.'})
            continue
        definition = NODE_CATALOG[kind]
        params, notes = clean_parameters(kind, step.get('parameters'))
        report['notes'].extend(notes)
        node_id = slug(str(step.get('id') or kind), used)
        wiring, taken, missing = {}, set(), []
        explicit = step.get('inputs') if isinstance(step.get('inputs'), dict) else {}
        for port, expected in definition['inputs'].items():
            choice = None
            origin = by_step.get(str(explicit.get(port, '')))
            if origin:
                candidates = [p for p in produced if p[0] == origin and p[2] == expected]
                choice = next((p for p in candidates if p[1] == port), candidates[0] if candidates else None)
            if choice is None:
                accepted = MODEL_ACCEPTS.get(kind) if expected == 'FittedModel' else None
                for candidate in reversed(produced):
                    if candidate[2] == expected and (candidate[0], candidate[1]) not in taken and \
                            (accepted is None or node_types[candidate[0]] in accepted):
                        choice = candidate
                        break
            if choice is not None and expected == 'FittedModel':
                latest = next((p for p in reversed(produced) if p[2] == expected), None)
                if latest and latest[0] != choice[0]:
                    report['notes'].append(f'{kind} se conectó a «{choice[0]}» ({node_types[choice[0]]}) porque no admite '
                                           f'el modelo más reciente «{latest[0]}» ({node_types[latest[0]]}).')
            if choice is None:
                missing.append(f'{port} ({expected})')
            else:
                taken.add((choice[0], choice[1]))
                wiring[port] = choice
        if missing:
            used.discard(node_id)
            report['dropped'].append({'tool': kind, 'reason': 'Sin salida compatible para ' + ', '.join(missing) + '.'})
            continue
        by_step[str(step.get('id') or kind)] = node_id
        node_types[node_id] = kind
        nodes.append({'id': node_id, 'type': kind, 'node_version': '1.0.0', 'parameters': params,
                      'position': {'x': 0, 'y': 0}, '_wiring': wiring})
        explanations[node_id] = str(step.get('why') or definition.get('explanation', ''))[:600]
        produced.extend((node_id, port, kind_type) for port, kind_type in definition['outputs'].items())
    edges = []
    for node in nodes:
        for port, (source, source_port, _) in node.pop('_wiring').items():
            edges.append({'id': f'{source}-{source_port}-{node["id"]}-{port}', 'source': source, 'target': node['id'],
                          'source_port': source_port, 'target_port': port})
    layout(nodes, edges)
    title = str(plan.get('title') or prompt[:80] or 'Blueprint generado').strip()[:120]
    objective = str(plan.get('objective') or prompt)[:1200]
    references = sorted({ref for node in nodes for ref in NODE_CATALOG[node['type']].get('references', [])})
    question = str(plan.get('question') or f'¿Qué responde este flujo sobre «{prompt.strip()[:160]}» y qué supuestos lo limitan?')
    lesson = {'module': 'IA', 'title': title, 'objective': objective, 'references': references,
              'missing_tools': [str(gap.get('name'))[:300] for gap in report['gaps']][:100],
              'steps': [{'node_id': node['id'], 'title': NODE_CATALOG[node['type']]['label'],
                         'instruction': explanations[node['id']] or NODE_CATALOG[node['type']].get('explanation', ''),
                         'expected': expected_text(node['type']), 'question': question if node is nodes[-1] else
                         '¿La salida de este paso tiene sentido antes de continuar?'} for node in nodes]}
    project = {'schema_version': SCHEMA, 'app_version': VERSION, 'title': title, 'nodes': nodes, 'edges': edges, 'lesson': lesson}
    validate_project(project)  # mismo validador DAG del motor; lanza EngineError si algo no cuadra
    return project, report


def expected_text(kind):
    outputs = NODE_CATALOG[kind]['outputs']
    return 'Produce ' + ', '.join(f'{port} ({kind_type})' for port, kind_type in outputs.items()) + '.' if outputs else 'Sin salidas.'


def layout(nodes, edges):
    parents = defaultdict(list)
    for edge in edges:
        parents[edge['target']].append(edge['source'])
    depth = {}
    for node in nodes:  # los nodos ya están en orden topológico
        depth[node['id']] = 1 + max((depth[p] for p in parents[node['id']]), default=-1)
    rows = defaultdict(int)
    for node in nodes:
        level = depth[node['id']]
        node['position'] = {'x': 40 + level * 330, 'y': 60 + rows[level] * 190}
        rows[level] += 1


# ---------------------------------------------------------------- verificación

def _pick(candidates, prompt, preferred=()):
    folded = fold(prompt)
    for name in candidates:
        if re.search(r'\b' + re.escape(fold(name)) + r'\b', folded):
            return name
    return next((name for name in preferred if name in candidates), candidates[-1] if candidates else None)


def assign_columns(node, schema, prompt):
    """Reasigna parámetros de columna con columnas numéricas reales del puerto de entrada."""
    numeric = list(schema.get('numeric_columns') or [])
    if not numeric:
        return False
    usable = [c for c in numeric if c != 'periodo'] or numeric
    params, changed = node['parameters'], False
    kind = node['type']
    target = _pick(usable, prompt, ['clase'] if kind == 'logit' else TARGET_NAMES)
    others = [c for c in usable if c != target]
    for key in list(params):
        if key not in SINGLE_COLUMNS | MULTI_COLUMNS:
            continue
        current = [c.strip() for c in str(params[key]).split(',') if c.strip()]
        if current and all(c in schema.get('columns', []) for c in current):
            continue
        if key == 'time':
            value = 'periodo' if 'periodo' in schema.get('columns', []) else (schema.get('columns') or [''])[0]
        elif key in ('y', 'column', 'value', 'returns', 'after', 'nominal'):
            value = target
        elif key in ('x', 'before', 'signal', 'index', 'population', 'error', 'group'):
            value = others[0] if others else target
        elif key == 'instruments':
            value = 'z' if 'z' in usable and 'z' != target else (others[-1] if others else target)
        elif key == 'features':
            instruments = str(params.get('instruments', ''))
            value = ','.join([c for c in others if c not in instruments.split(',')][:5]) or target
        else:  # columns
            value = ','.join(usable[:6])
        if value and value != params[key]:
            params[key], changed = value, True
    return changed


def verify(project, prompt='', allow_network=False, rounds=4):
    """Ejecuta el flujo y repara columnas. Devuelve un resumen por nodo."""
    if not allow_network and any(node['type'] == 'worldbank' for node in project['nodes']):
        return {'executed': False, 'reason': 'El flujo consulta el Banco Mundial; actívalo para verificar con red.', 'nodes': {}}
    if any(node['type'] == 'csv' and not node['parameters'].get('content') for node in project['nodes']):
        return {'executed': False, 'reason': 'Carga tu CSV en el nodo de datos y ejecuta el flujo.', 'nodes': {}}
    incoming = defaultdict(dict)
    for edge in project['edges']:
        incoming[edge['target']][edge['target_port']] = (edge['source'], edge['source_port'])
    repairs, run = [], None
    for _ in range(rounds):
        try:
            run = execute(project)
        except EngineError as error:
            return {'executed': False, 'reason': str(error), 'nodes': {}, 'repairs': repairs}
        changed = False
        for node in project['nodes']:
            state = run['nodes'].get(node['id'], {})
            if state.get('status') != 'failed' or state['error']['code'] not in ('INVALID_PARAMETERS', 'INSUFFICIENT_SAMPLE', 'ESTIMATION_ERROR'):
                continue
            link = incoming[node['id']].get('data') or next(iter(incoming[node['id']].values()), None)
            if not link:
                continue
            parent = run['nodes'].get(link[0], {}).get('result', {})
            schema = (parent.get('output_previews') or {}).get(link[1])
            before = dict(node['parameters'])
            if schema and assign_columns(node, schema, prompt):
                changed = True
                repairs.append({'node_id': node['id'], 'before': before, 'after': dict(node['parameters'])})
        if not changed:
            break
    summary = {key: {'status': value['status'], **({'error': value['error']['message']} if value.get('error') else {})}
               for key, value in (run or {}).get('nodes', {}).items()}
    return {'executed': True, 'status': (run or {}).get('status'), 'nodes': summary, 'repairs': repairs}
