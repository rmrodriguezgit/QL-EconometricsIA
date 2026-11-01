"""Typed, bounded DAG execution. No user-supplied expressions are executed."""
from collections import deque
from datetime import datetime, timezone
from importlib.metadata import version as package_version
import csv
import hashlib
import io
import json
import math
import platform
import re
from pathlib import Path
import subprocess
import uuid

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[2]
VERSION = (ROOT / 'VERSION').read_text().strip() if (ROOT / 'VERSION').exists() else '0.2.0'
SCHEMA = '1.0.0'

class EngineError(ValueError):
    def __init__(self, code, message, node_id=None):
        super().__init__(message)
        self.code = code
        self.node_id = node_id

# port name -> scientific type; each input currently has arity exactly one.
NODES = {
    'simulate': {'label': 'Datos simulados', 'inputs': {}, 'outputs': {'data': 'Dataset'}, 'references': ['B18', 'B29']},
    'csv': {'label': 'Archivo CSV', 'inputs': {}, 'outputs': {'data': 'Dataset'}, 'references': ['B16']},
    'worldbank': {'label': 'Banco Mundial', 'inputs': {}, 'outputs': {'data': 'Dataset'}, 'references': ['B01']},
    'describe': {'label': 'Estadística descriptiva', 'inputs': {'data': 'Dataset'}, 'outputs': {'summary': 'Summary'}, 'references': ['B18']},
    'scatter': {'label': 'Dispersión', 'inputs': {'data': 'Dataset'}, 'outputs': {'plot': 'Plot'}, 'references': ['B17']},
    'ols': {'label': 'Regresión OLS', 'inputs': {'data': 'Dataset'}, 'outputs': {'model': 'FittedModel'}, 'references': ['B03', 'B23', 'B29']},
}


def finite_json(value):
    if isinstance(value, dict):
        return {str(k): finite_json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [finite_json(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if math.isfinite(value) else None
    return value


def canonical(value):
    return json.dumps(finite_json(value), sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def fail(message, code='INVALID_GRAPH', node_id=None):
    raise EngineError(code, message, node_id)


def validate_project(project):
    if not isinstance(project, dict) or project.get('schema_version') != SCHEMA:
        fail('El esquema del proyecto debe ser 1.0.0; no se puede abrir una versión desconocida.')
    if not isinstance(project.get('title'), str) or len(project['title']) > 120 or not isinstance(project.get('app_version'), str):
        fail('El proyecto necesita título y versión de aplicación válidos.')
    nodes, edges = project.get('nodes'), project.get('edges')
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= 100:
        fail('El proyecto necesita entre 1 y 100 nodos.')
    if not isinstance(edges, list) or len(edges) > 400:
        fail('Se permiten hasta 400 conexiones.')
    ids = {}
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get('id'), str) or not node['id'] or len(node['id']) > 128:
            fail('Cada nodo necesita un identificador válido.')
        if node['id'] in ids:
            fail('Hay identificadores de nodo duplicados.')
        if not isinstance(node.get('type'), str) or node['type'] not in NODES:
            fail('Tipo de nodo desconocido.', node_id=node['id'])
        if node.get('node_version') != '1.0.0':
            fail('Versión de nodo incompatible.', node_id=node['id'])
        if not isinstance(node.get('parameters'), dict):
            fail('Los parámetros deben ser un objeto.', node_id=node['id'])
        position = node.get('position')
        if not isinstance(position, dict) or any(isinstance(position.get(k), bool) or not isinstance(position.get(k), (int, float)) or not math.isfinite(position[k]) for k in ['x', 'y']):
            fail('La posición del nodo no es válida.', node_id=node['id'])
        if any(not isinstance(value, (str, int, float)) or isinstance(value, bool) or (isinstance(value, (int, float)) and not math.isfinite(value)) for value in node['parameters'].values()):
            fail('Los parámetros deben ser textos o números finitos.', node_id=node['id'])
        ids[node['id']] = node
    children = {key: [] for key in ids}
    indegree = {key: 0 for key in ids}
    incoming = {key: {} for key in ids}
    for edge in edges:
        if not isinstance(edge, dict):
            fail('Conexión inválida.')
        if any(not isinstance(edge.get(k), str) for k in ['id', 'source', 'target', 'source_port', 'target_port']):
            fail('Una conexión necesita identificadores y puertos válidos.')
        source, target = edge.get('source'), edge.get('target')
        if not isinstance(source, str) or not isinstance(target, str) or source not in ids or target not in ids:
            fail('Una conexión apunta a un nodo inexistente.')
        source_port, target_port = edge.get('source_port'), edge.get('target_port')
        output = NODES[ids[source]['type']]['outputs'].get(source_port)
        expected = NODES[ids[target]['type']]['inputs'].get(target_port)
        if output is None or expected is None or output != expected:
            fail('Los puertos no existen o sus tipos no son compatibles.', 'TYPE_MISMATCH', target)
        if target_port in incoming[target]:
            fail('Cada puerto de entrada admite una sola conexión.', node_id=target)
        incoming[target][target_port] = source
        children[source].append(target)
        indegree[target] += 1
    queue = deque(key for key in ids if indegree[key] == 0)
    ordered = []
    while queue:
        key = queue.popleft()
        ordered.append(key)
        for child in children[key]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(ordered) != len(nodes):
        fail('El flujo contiene un ciclo.')
    for key, node in ids.items():
        missing = set(NODES[node['type']]['inputs']) - set(incoming[key])
        if missing:
            fail('Conecta la entrada de datos antes de ejecutar.', node_id=key)
    return ids, ordered, incoming


def number(parameters, key, default, low, high, integer=False):
    value = parameters.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        fail(f'{key} debe ser un número finito.', 'INVALID_PARAMETERS')
    if value < low or value > high or (integer and int(value) != value):
        fail(f'{key} debe estar entre {low} y {high}.', 'INVALID_PARAMETERS')
    return int(value) if integer else float(value)


def simulate(parameters):
    n = number(parameters, 'n', 120, 5, 10000, True)
    seed = number(parameters, 'seed', 42, 0, 2**32 - 1, True)
    intercept = number(parameters, 'intercept', 12, -1e6, 1e6)
    slope = number(parameters, 'slope', 0.72, -1e6, 1e6)
    noise = number(parameters, 'noise', 9, 0, 1e6)
    rng = np.random.default_rng(seed)
    income = rng.uniform(20, 150, n)
    consumption = intercept + slope * income + rng.normal(0, noise, n)
    frame = pd.DataFrame({'ingreso': income, 'consumo': consumption})
    return frame, {'provider': 'synthetic', 'seed': seed, 'parameters': parameters,
                   'units': {'ingreso': 'unidades monetarias simuladas', 'consumo': 'unidades monetarias simuladas'}}


def csv_data(parameters):
    content = parameters.get('content', '')
    delimiter = parameters.get('delimiter', ',')
    if not isinstance(content, str) or not content or len(content.encode()) > 2_000_000:
        fail('Selecciona un CSV de hasta 2 MB.', 'INVALID_PARAMETERS')
    if delimiter not in [',', ';', '\t']:
        fail('Delimitador CSV no válido.', 'INVALID_PARAMETERS')
    header = next(csv.reader(io.StringIO(content), delimiter=delimiter), [])
    if not header or len(header) > 50 or len(set(header)) != len(header) or any(not col.strip() for col in header):
        fail('El CSV necesita de 1 a 50 columnas con nombres únicos y no vacíos.', 'INVALID_PARAMETERS')
    try:
        frame = pd.read_csv(io.StringIO(content), sep=delimiter, nrows=10001)
    except (ValueError, pd.errors.ParserError) as exc:
        raise EngineError('INVALID_PARAMETERS', 'No se pudo interpretar el CSV.') from exc
    if frame.empty or len(frame) > 10000:
        fail('El CSV debe contener entre 1 y 10.000 filas.', 'INVALID_PARAMETERS')
    return frame, {'provider': 'csv', 'sha256': hashlib.sha256(content.encode()).hexdigest(),
                   'delimiter': delimiter, 'units': 'declaradas por el usuario; no inferidas'}


def world_bank(parameters):
    import wbdata
    from requests import Session

    class BoundedSession(Session):
        def request(self, method, url, **kwargs):
            kwargs.setdefault('timeout', (5, 12))
            response = super().request(method, url, **kwargs)
            response.raise_for_status()
            return response

    client = wbdata.Client()
    # wbdata 1.1.0 accepts a session but does not forward it to Fetcher.
    client.fetcher.session = BoundedSession()
    country = parameters.get('country', 'MEX')
    indicator = parameters.get('indicator', 'NY.GDP.PCAP.KD')
    source_id = number(parameters, 'source', 2, 1, 100000, True)
    start = number(parameters, 'start', 2000, 1960, datetime.now().year, True)
    end = number(parameters, 'end', 2023, start, datetime.now().year, True)
    if not isinstance(country, str) or len(country) != 3 or not country.isalpha():
        fail('Usa un código de país de tres letras, por ejemplo MEX.', 'INVALID_PARAMETERS')
    if not isinstance(indicator, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,200}', indicator):
        fail('Código de indicador no válido.', 'INVALID_PARAMETERS')
    try:
        frame = client.get_dataframe({indicator: 'valor'}, country=country.upper(),
                                   date=(str(start), str(end)), source=source_id, parse_dates=False).reset_index()
    except Exception as exc:
        raise EngineError('DATA_UNAVAILABLE', 'Banco Mundial no respondió. Revisa la conexión y los códigos o usa datos simulados.') from exc
    if frame.empty or 'date' not in frame.columns:
        fail('La consulta no devolvió períodos disponibles.', 'DATA_UNAVAILABLE')
    frame = frame.rename(columns={'date': 'periodo'})
    frame['periodo'] = pd.to_numeric(frame['periodo'], errors='raise')
    frame = frame.sort_values('periodo').reset_index(drop=True)
    return frame, {'provider': 'World Bank', 'country': country.upper(), 'indicator': indicator,
                   'source_id': source_id, 'start': start, 'end': end, 'units': 'consultar metadatos del indicador; no inferidas'}


def numeric(frame, columns):
    if not columns or any(not isinstance(col, str) or col not in frame.columns for col in columns):
        fail('Selecciona columnas existentes en los datos.', 'INVALID_PARAMETERS')
    values = frame[columns]
    if any(not pd.api.types.is_numeric_dtype(values[col]) for col in columns):
        fail('Las columnas seleccionadas deben ser numéricas.', 'INVALID_PARAMETERS')
    if np.isinf(values.to_numpy(dtype=float)).any():
        fail('Hay valores infinitos en la muestra.', 'INVALID_PARAMETERS')
    return values


def describe(frame, parameters):
    columns = frame.select_dtypes(include='number').columns.tolist()
    if not columns:
        fail('No hay columnas numéricas para resumir.', 'INVALID_PARAMETERS')
    values = numeric(frame, columns)
    rows = []
    for col in columns:
        s = values[col]
        rows.append({'variable': col, 'n': int(s.count()), 'missing': int(s.isna().sum()),
                     'mean': s.mean(), 'median': s.median(), 'std': s.std(ddof=1),
                     'min': s.min(), 'max': s.max()})
    return {'kind': 'summary', 'rows': finite_json(rows), 'n_total': len(frame),
            'note': 'Desviación estándar muestral (ddof=1); faltantes excluidos por columna.'}


def scatter(frame, parameters):
    x, y = parameters.get('x', 'ingreso'), parameters.get('y', 'consumo')
    if x == y:
        fail('Selecciona dos variables distintas.', 'INVALID_PARAMETERS')
    values = numeric(frame, [x, y]).dropna()
    if values.empty:
        fail('No hay pares completos para graficar.', 'INSUFFICIENT_SAMPLE')
    return {'kind': 'scatter', 'x': x, 'y': y, 'points': values.values.tolist(),
            'n': len(values), 'dropped': len(frame) - len(values)}


def ols(frame, parameters):
    x, y = parameters.get('x', 'ingreso'), parameters.get('y', 'consumo')
    cov = parameters.get('covariance', 'HC3')
    if x == y or cov not in ['nonrobust', 'HC3']:
        fail('Elige variables distintas y covarianza clásica o HC3.', 'INVALID_PARAMETERS')
    values = numeric(frame, [x, y]).dropna()
    if len(values) < 4:
        fail('OLS necesita al menos cuatro pares completos.', 'INSUFFICIENT_SAMPLE')
    design = sm.add_constant(values[[x]], has_constant='add')
    if np.linalg.matrix_rank(design) < design.shape[1]:
        fail('El regresor no varía: la matriz de diseño no tiene rango completo.', 'RANK_DEFICIENT')
    fitted = sm.OLS(values[y], design).fit(cov_type=cov)
    interval = fitted.conf_int()
    coefficients = [{'term': term, 'estimate': fitted.params[term], 'std_error': fitted.bse[term],
                     'statistic': fitted.tvalues[term], 'p_value': fitted.pvalues[term],
                     'ci_low': interval.loc[term, 0], 'ci_high': interval.loc[term, 1]}
                    for term in fitted.params.index]
    return finite_json({'kind': 'ols', 'x': x, 'y': y, 'n': int(fitted.nobs),
            'dropped': len(frame) - len(values), 'r_squared': fitted.rsquared,
            'r_squared_adj': fitted.rsquared_adj, 'aic': fitted.aic, 'bic': fitted.bic,
            'covariance': cov, 'coefficients': coefficients,
            'residuals': fitted.resid.tolist(), 'fitted': fitted.fittedvalues.tolist(),
            'note': 'Asociación estimada; no identifica un efecto causal. HC3 modifica la inferencia, no los coeficientes OLS.'})


def execute(project):
    ids, ordered, incoming = validate_project(project)
    results, raw, sources = {}, {}, {}
    started = datetime.now(timezone.utc).isoformat()
    for key in ordered:
        node = ids[key]
        parents = list(incoming[key].values())
        if any(results[parent]['status'] != 'succeeded' for parent in parents):
            results[key] = {'status': 'skipped', 'message': 'El nodo de origen no produjo datos.'}
            continue
        try:
            kind, params = node['type'], node['parameters']
            if kind in ['simulate', 'csv', 'worldbank']:
                frame, source = {'simulate': simulate, 'csv': csv_data, 'worldbank': world_bank}[kind](params)
                if len(frame.columns) > 50 or len(frame) > 10000:
                    fail('Se excedió el límite de filas o columnas.', 'INVALID_PARAMETERS')
                raw[key] = frame
                records = json.loads(frame.to_json(orient='records', double_precision=15))
                source.update({'retrieved_at': datetime.now(timezone.utc).isoformat(),
                               'data_sha256': digest(records), 'n': len(frame)})
                sources[key] = source
                result = {'kind': 'dataset', 'columns': frame.columns.tolist(), 'n': len(frame),
                          'preview': records[:8], 'records': records, 'source': source}
            else:
                frame = raw[incoming[key]['data']]
                result = {'describe': describe, 'scatter': scatter, 'ols': ols}[kind](frame, params)
            results[key] = {'status': 'succeeded', 'result': finite_json(result)}
        except EngineError as exc:
            results[key] = {'status': 'failed', 'error': {'code': exc.code, 'message': str(exc)}}
        except Exception:
            results[key] = {'status': 'failed', 'error': {'code': 'INTERNAL_ERROR', 'message': 'No se pudo calcular el nodo; revisa los datos y parámetros.'}}
    try:
        commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, timeout=2).stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        commit = None
    return {'run_id': str(uuid.uuid4()), 'status': 'failed' if any(r['status'] == 'failed' for r in results.values()) else 'succeeded',
            'nodes': results, 'manifest': {'app_version': VERSION, 'schema_version': SCHEMA,
            'protocol_version': '1.0.0', 'started_at': started,
            'finished_at': datetime.now(timezone.utc).isoformat(), 'graph_sha256': digest({'schema_version': project['schema_version'], 'nodes': [{k: node[k] for k in ['id', 'type', 'node_version', 'parameters']} for node in project['nodes']], 'edges': project['edges']}),
            'python': platform.python_version(), 'platform': platform.platform(),
            'dependencies': {name: package_version(name) for name in ['numpy', 'pandas', 'statsmodels', 'wbdata']},
            'git_commit': commit, 'sources': sources}}
