"""Reparación del flujo actual: ejecuta, localiza nodos fallidos y corrige parámetros y conexiones.

No crea un blueprint nuevo ni genera código: modifica una copia del proyecto con reglas
deterministas (nombres de salida, columnas reales de cada puerto, rangos numéricos,
opciones del catálogo y conexiones con el tipo correcto) y vuelve a ejecutar para
comprobar cada cambio. Lo que no sabe arreglar lo devuelve como pendiente.
"""
import copy
import re
import unicodedata

from ..core import NODE_CATALOG, EngineError, execute, node_inputs
from .compiler import MULTI_COLUMNS, SINGLE_COLUMNS, assign_columns

ROUNDS = 5
NAME = re.compile(r'[A-Za-z][A-Za-z0-9_]{0,49}')
RESERVED = {'periodo', 'pais', 'iso3'}
TIME_NAMES = ('periodo', 'year', 'anio', 'ano', 'fecha', 'date', 'time', 'tiempo')
FIXABLE = {'INVALID_PARAMETERS', 'INSUFFICIENT_SAMPLE', 'ESTIMATION_ERROR', 'TYPE_MISMATCH'}


def safe_name(value, fallback='variable'):
    """Convierte un texto en nombre de columna válido: sin acentos ni espacios, empieza por letra."""
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r'[^A-Za-z0-9_]+', '_', text).strip('_')[:50]
    if not text:
        text = fallback
    if not text[0].isalpha():
        text = ('v_' + text)[:50]
    if text.lower() in RESERVED:
        text = text + '_valor'
    return text


def unique(name, used):
    candidate, i = name, 2
    while candidate in used:
        candidate, i = f'{name[:46]}_{i}', i + 1
    used.add(candidate)
    return candidate


class Repairer:
    def __init__(self, project):
        self.project = copy.deepcopy(project)
        self.changes, self.unresolved = [], []
        self.nodes = {node['id']: node for node in self.project.get('nodes', []) if isinstance(node, dict) and 'id' in node}

    def label(self, node_id):
        node = self.nodes.get(node_id)
        return NODE_CATALOG.get(node['type'], {}).get('label', node['type']) if node else node_id

    def note(self, node_id, field, before, after, reason):
        self.changes.append({'node_id': node_id, 'label': self.label(node_id), 'field': field,
                             'before': before, 'after': after, 'reason': reason})

    def set(self, node, key, value, reason):
        before = node['parameters'].get(key)
        if before != value:
            node['parameters'][key] = value
            self.note(node['id'], key, before, value, reason)
            return True
        return False

    # ------------------------------------------------------------ estructura

    def ports(self, node):
        try:
            return node_inputs(node)
        except EngineError:
            variadic = NODE_CATALOG[node['type']].get('variadic')
            raw = node['parameters'].get('extra_inputs', 0)
            fixed = max(0, min(variadic['max_extra'], int(raw))) if variadic and isinstance(raw, (int, float)) and not isinstance(raw, bool) else 0
            if variadic:
                self.set(node, 'extra_inputs', fixed, 'Número de entradas adicionales fuera del límite del nodo.')
            else:
                node['parameters'].pop('extra_inputs', None)
                self.note(node['id'], 'extra_inputs', raw, None, 'Este nodo no admite entradas adicionales.')
            return node_inputs(node)

    def structure(self):
        """Quita conexiones imposibles, ajusta entradas «+» y conecta entradas vacías con un productor compatible."""
        edges, kept, taken = self.project.get('edges', []), [], set()
        order = list(self.nodes)
        for edge in edges:
            source, target = self.nodes.get(edge.get('source')), self.nodes.get(edge.get('target'))
            if not source or not target:
                self.note(edge.get('target', '?'), 'conexión', edge.get('id'), None, 'La conexión apuntaba a un nodo inexistente.')
                continue
            output = NODE_CATALOG[source['type']]['outputs'].get(edge.get('source_port'))
            expected = self.ports(target).get(edge.get('target_port'))
            if output is None or output != expected:
                self.note(target['id'], f"entrada {edge.get('target_port')}", f"{self.label(source['id'])}.{edge.get('source_port')}", None,
                          'Conexión retirada: los puertos no existen o sus tipos no coinciden.')
                continue
            if (target['id'], edge['target_port']) in taken:
                self.note(target['id'], f"entrada {edge['target_port']}", f"{self.label(source['id'])}.{edge['source_port']}", None,
                          'Conexión duplicada retirada: cada entrada admite una sola conexión.')
                continue
            taken.add((target['id'], edge['target_port']))
            kept.append(edge)
        self.project['edges'] = kept
        for node in self.nodes.values():
            variadic = NODE_CATALOG[node['type']].get('variadic')
            while variadic and node['parameters'].get('extra_inputs', 0):
                last = f"{variadic['prefix']}{variadic['start'] + node['parameters']['extra_inputs'] - 1}"
                if (node['id'], last) in taken:
                    break
                count = node['parameters']['extra_inputs']
                for key in [k for k in node['parameters'] if k.startswith(last + '_')]:
                    node['parameters'].pop(key)
                self.set(node, 'extra_inputs', count - 1, f'La entrada añadida {last} estaba vacía; se retiró.')
        for node in self.nodes.values():
            for port, kind in self.ports(node).items():
                if (node['id'], port) in taken:
                    continue
                producer = self.producer(node['id'], kind, order)
                if producer is None:
                    self.unresolved.append({'node_id': node['id'], 'label': self.label(node['id']),
                                            'message': f'La entrada «{port}» ({kind}) está vacía y no hay otro nodo {kind} distinto que conectar. Añade la fuente o el modelo que corresponda y conéctalo.'})
                    continue
                source_id, source_port = producer
                self.project['edges'].append({'id': f'reparar-{source_id}-{node["id"]}-{port}'[:120], 'source': source_id, 'source_port': source_port,
                                              'target': node['id'], 'target_port': port})
                taken.add((node['id'], port))
                self.note(node['id'], f'entrada {port}', None, f'{self.label(source_id)}.{source_port}',
                          f'Entrada vacía conectada al productor {kind} más cercano.')

    def descendants(self, node_id):
        children = {}
        for edge in self.project['edges']:
            children.setdefault(edge['source'], []).append(edge['target'])
        seen, stack = set(), [node_id]
        while stack:
            for child in children.get(stack.pop(), []):
                if child not in seen:
                    seen.add(child)
                    stack.append(child)
        return seen

    def producer(self, node_id, kind, order):
        """Productor más cercano antes del nodo (en el orden del proyecto) sin crear ciclos."""
        blocked = self.descendants(node_id) | {node_id}
        before = order[:order.index(node_id)][::-1] + order[order.index(node_id) + 1:]
        used = {edge['source'] for edge in self.project['edges'] if edge['target'] == node_id}
        found = []
        for candidate in before:
            if candidate in blocked:
                continue
            port = next((p for p, t in NODE_CATALOG[self.nodes[candidate]['type']]['outputs'].items() if t == kind), None)
            if port:
                found.append((candidate, port))
        # Solo productores que aún no alimentan este nodo: conectar la misma tabla o el mismo
        # modelo a dos entradas (unir una serie consigo misma, comparar un modelo consigo mismo) no tiene sentido.
        return next((item for item in found if item[0] not in used), None)

    # ------------------------------------------------------------ parámetros

    def schemas(self, node, run):
        out = {}
        for edge in self.project['edges']:
            if edge['target'] == node['id']:
                result = run['nodes'].get(edge['source'], {}).get('result', {})
                schema = (result.get('output_previews') or {}).get(edge['source_port'])
                if schema:
                    out[edge['target_port']] = schema
        return out

    def fix_numbers(self, node, message):
        definition = NODE_CATALOG[node['type']]
        changed = False
        match = re.match(r'(\w+) debe estar entre (\S+) y (\S+?)\.?$', message)
        if match and match.group(1) in node['parameters']:
            key, low, high = match.group(1), float(match.group(2)), float(match.group(3))
            value = node['parameters'][key]
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                fixed = min(max(value, low), high)
                fixed = int(round(fixed)) if isinstance(definition['defaults'].get(key), int) else fixed
                changed |= self.set(node, key, fixed, f'Valor fuera del rango permitido [{match.group(2)}, {match.group(3)}].')
        match = re.match(r'(\w+) debe ser un número finito', message)
        if match and match.group(1) in definition.get('defaults', {}):
            changed |= self.set(node, match.group(1), definition['defaults'][match.group(1)], 'Se restableció el valor por defecto: debía ser un número.')
        for key, options in definition.get('choices', {}).items():
            if key in node['parameters'] and node['parameters'][key] not in options:
                changed |= self.set(node, key, definition['defaults'].get(key, options[0]), f'«{node["parameters"][key]}» no es una opción válida.')
        return changed

    def fix_names(self, node):
        params, changed = node['parameters'], False
        if node['type'] == 'join_series':
            return False  # se tratan junto con sus columnas
        if 'output' in params and isinstance(params['output'], str):
            name = safe_name(params['output'], NODE_CATALOG[node['type']]['defaults'].get('output', 'variable'))
            changed |= self.set(node, 'output', name, 'Nombre de salida con espacios, acentos o símbolos.')
        if node['type'] == 'worldbank_multi' and isinstance(params.get('indicators'), str):
            used, lines = set(), []
            for item in re.split(r'[\n;,]+', params['indicators']):
                if not item.strip():
                    continue
                code, _, alias = item.partition(':') if ':' in item else item.partition('=')
                code = code.strip()
                alias = unique(safe_name(alias.strip() or code.lower(), 'indicador').lower(), used)
                lines.append(f'{code}: {alias}')
            changed |= self.set(node, 'indicators', '\n'.join(lines), 'Alias de indicadores convertidos en nombres de columna válidos y distintos.')
        return changed

    def fix_join(self, node, schemas):
        params, changed, used = node['parameters'], False, set()
        for side in self.ports(node):
            schema = schemas.get(side)
            if schema:
                columns, numeric = schema.get('columns', []), schema.get('numeric_columns', [])
                key = params.get(f'{side}_key')
                if key not in columns:
                    found = next((c for c in columns if unicodedata.normalize('NFKD', c.lower()).encode('ascii', 'ignore').decode() in TIME_NAMES), None)
                    if found is None:
                        self.unresolved.append({'node_id': node['id'], 'label': self.label(node['id']),
                                                'message': f'La tabla conectada a {side} no tiene una columna de año o fecha reconocible ({", ".join(columns[:8])}). Elige la clave a mano.'})
                    else:
                        key = found
                        changed |= self.set(node, f'{side}_key', key, f'Clave de tiempo de {side} elegida entre las columnas reales.')
                value = params.get(f'{side}_value')
                if value not in numeric or value == key:
                    options = [c for c in numeric if c != key and c.lower() not in RESERVED]
                    if options:
                        value = options[0]
                        changed |= self.set(node, f'{side}_value', value, f'Variable de valores de {side} elegida entre las columnas numéricas reales.')
            raw = params.get(f'{side}_name')
            fallback = safe_name(params.get(f'{side}_value') if params.get(f'{side}_value') not in (None, 'valor') else side, side)
            reserved = not raw or str(raw).strip().lower() in RESERVED
            name = unique(fallback if reserved else safe_name(raw, fallback), used)
            changed |= self.set(node, f'{side}_name', name, 'Nombre de salida inválido o repetido: se usan letras, números y «_», distinto de periodo.')
        return changed

    def fix_node(self, node, state, run):
        message = state['error']['message']
        schemas = self.schemas(node, run)
        changed = self.fix_numbers(node, message) | self.fix_names(node)
        if node['type'] == 'join_series':
            changed |= self.fix_join(node, schemas)
        elif any(key in SINGLE_COLUMNS | MULTI_COLUMNS for key in node['parameters']):
            schema = schemas.get('data') or next(iter(schemas.values()), None)
            before = dict(node['parameters'])
            if schema and assign_columns(node, schema, ''):
                for key, value in node['parameters'].items():
                    if before.get(key) != value:
                        self.note(node['id'], key, before.get(key), value, 'Columna inexistente o no numérica: se eligió una columna real de la entrada.')
                changed = True
        return changed

    def run(self):
        self.structure()
        run, attempts = None, {}
        for _ in range(ROUNDS):
            try:
                run = execute(self.project)
            except EngineError as error:
                self.unresolved.append({'node_id': getattr(error, 'node_id', None), 'label': self.label(getattr(error, 'node_id', None)), 'message': str(error)})
                break
            changed = False
            for node_id, state in run['nodes'].items():
                if state.get('status') != 'failed' or state['error']['code'] not in FIXABLE:
                    continue
                attempts[node_id] = attempts.get(node_id, 0) + 1
                if attempts[node_id] <= 3:
                    changed |= self.fix_node(self.nodes[node_id], state, run)
            if not changed:
                break
        statuses = {key: value['status'] for key, value in (run or {}).get('nodes', {}).items()}
        for key, value in (run or {}).get('nodes', {}).items():
            if value['status'] == 'failed':
                self.unresolved.append({'node_id': key, 'label': self.label(key), 'message': value['error']['message']})
        seen, unresolved = set(), []
        for item in self.unresolved:
            marker = (item['node_id'], item['message'])
            if marker not in seen:
                seen.add(marker)
                unresolved.append(item)
        return {'project': self.project, 'changes': self.changes, 'unresolved': unresolved,
                'status': (run or {}).get('status', 'failed'), 'nodes': statuses, 'executed': run is not None}


def repair(params):
    project = params.get('project')
    if not isinstance(project, dict) or not isinstance(project.get('nodes'), list) or not isinstance(project.get('edges'), list):
        raise EngineError('INVALID_PARAMETERS', 'Envía el proyecto del canvas para repararlo.')
    unknown = [node.get('type') for node in project['nodes'] if not isinstance(node, dict) or node.get('type') not in NODE_CATALOG]
    if unknown:
        raise EngineError('INVALID_PARAMETERS', f'Tipos de nodo desconocidos: {unknown[:5]}.')
    for node in project['nodes']:
        if not isinstance(node.get('parameters'), dict):
            node['parameters'] = {}
    if not params.get('allow_network', True) and any(node['type'] in ('worldbank', 'worldbank_multi') for node in project['nodes']):
        raise EngineError('INVALID_PARAMETERS', 'El flujo consulta el Banco Mundial; permite la red para repararlo.')
    return Repairer(project).run()
