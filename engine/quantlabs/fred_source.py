"""FRED (Federal Reserve Bank of St. Louis) sin clave de API.

Descarga cada serie de ``https://fred.stlouisfed.org/graph/fredgraph.csv?id=ID&cosd=INICIO&coed=FIN``,
la misma URL pública que usa el botón «Download CSV» de FRED. Los identificadores son una lista
permitida por expresión regular (nunca URL ni rutas) y el host es fijo.

- Una petición por serie, en paralelo: con varias frecuencias, FRED responde un ZIP en lugar de un CSV.
- Las fechas se conservan tal como las publica FRED (inicio del período). Convertir a mensual,
  trimestral o anual es explícito (media, último valor o suma) y queda en la procedencia.
- Caché en memoria por proceso (6 h) para no repetir descargas al re-ejecutar el flujo.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
import io
import json
import re
import threading
import time

import numpy as np
import pandas as pd

from .core import EngineError, ROOT

URL = 'https://fred.stlouisfed.org/graph/fredgraph.csv'
SERIES_URL = 'https://fred.stlouisfed.org/series/'
CATALOG = json.loads((ROOT / 'packages/contracts/fredCatalog.json').read_text(encoding='utf-8'))
KNOWN = {item['id']: item for item in CATALOG['items']}
DEFAULT_SERIES = 'DGS3MO: tbill_3m\nDGS10: bono_10y'
SERIES_ID = re.compile(r'[A-Z0-9][A-Z0-9_]{0,39}')
ALIAS = re.compile(r'[A-Za-z_][A-Za-z0-9_]{0,40}')
FREQUENCIES = {'original': None, 'semanal': 'W-FRI', 'mensual': 'MS', 'trimestral': 'QS', 'anual': 'YS'}
AGGREGATIONS = ['media', 'ultimo', 'suma']
MAX_ROWS = 60000
CACHE_SECONDS = 6 * 3600
_cache, _lock = {}, threading.Lock()


def fail(message, code='INVALID_PARAMETERS'):
    raise EngineError(code, message)


def parse_series(value):
    """«ID: alias» por línea, coma o punto y coma → dict ordenado ID → alias."""
    if isinstance(value, dict):
        pairs = [(str(k).strip(), str(v).strip()) for k, v in value.items()]
    elif isinstance(value, str):
        pairs = []
        for item in re.split(r'[\n;,]+', value):
            if item.strip():
                code, _, alias = item.partition(':') if ':' in item else item.partition('=')
                pairs.append((code.strip(), alias.strip()))
    else:
        fail('Indica las series como «ID: alias», una por línea (p. ej. DGS3MO: tbill_3m).')
    mapping = {}
    for code, alias in pairs:
        code = code.upper()
        if not SERIES_ID.fullmatch(code):
            fail(f'Identificador FRED no válido: «{code}». Usa el código de la serie, p. ej. UNRATE o DGS10.')
        alias = alias or KNOWN.get(code, {}).get('alias') or code.lower()
        if not ALIAS.fullmatch(alias) or alias in ('periodo', 'fecha'):
            fail(f'Alias no válido: «{alias}». Usa letras, números y «_», sin empezar por número ni llamarlo periodo.')
        if code in mapping:
            fail(f'La serie {code} está repetida.')
        mapping[code] = alias
    if not mapping:
        fail('Añade al menos una serie de FRED.')
    if len(mapping) > 12:
        fail('Como máximo 12 series por consulta.')
    if len(set(mapping.values())) != len(mapping):
        fail('Cada serie necesita un alias distinto.')
    return mapping


def parse_date(value, default, label):
    if value in (None, ''):
        return default
    if isinstance(value, (int, float)) and not isinstance(value, bool) and float(value).is_integer():
        value = f'{int(value):04d}-01-01'
    text = str(value).strip()
    if re.fullmatch(r'\d{4}', text):
        text += '-01-01'
    try:
        parsed = datetime.strptime(text, '%Y-%m-%d').date()
    except ValueError:
        fail(f'{label} debe ser una fecha AAAA-MM-DD (o un año).')
    if parsed.year < 1776 or parsed > date.today():
        fail(f'{label} debe estar entre 1776 y hoy.')
    return parsed


def download(code, start, end, session=None):
    """CSV de una serie como DataFrame (fecha, valor). Lanza DATA_UNAVAILABLE con un mensaje claro."""
    key = (code, start.isoformat(), end.isoformat())
    with _lock:
        hit = _cache.get(key)
        if hit and time.monotonic() - hit[0] < CACHE_SECONDS:
            return hit[1].copy()
    import requests
    for attempt in range(2):  # FRED a veces tarda en generar el CSV: un reintento antes de fallar
        try:
            response = (session or requests).get(URL, params={'id': code, 'cosd': key[1], 'coed': key[2]},
                                                 timeout=(5, 40))  # un User-Agent propio hace que FRED retenga la respuesta
            break
        except requests.RequestException as exc:
            if attempt:
                raise EngineError('DATA_UNAVAILABLE', f'FRED no respondió al pedir {code}. Revisa la conexión e inténtalo de nuevo.') from exc
    if response.status_code == 404:
        fail(f'FRED no tiene la serie {code}. Comprueba el identificador en fred.stlouisfed.org.', 'DATA_UNAVAILABLE')
    if response.status_code != 200:
        fail(f'FRED devolvió el estado {response.status_code} para {code}.', 'DATA_UNAVAILABLE')
    frame = parse_csv(response.text, code)
    with _lock:
        _cache[key] = (time.monotonic(), frame)
    return frame.copy()


def parse_csv(text, code):
    head = text[:200].lstrip('﻿')
    if not head or ',' not in head.splitlines()[0]:
        fail(f'FRED no devolvió un CSV para {code}.', 'DATA_UNAVAILABLE')
    try:
        frame = pd.read_csv(io.StringIO(text.lstrip('﻿')), na_values=['.', ''], keep_default_na=False)
    except (ValueError, pd.errors.ParserError) as exc:
        raise EngineError('DATA_UNAVAILABLE', f'No se pudo leer el CSV de FRED para {code}.') from exc
    if len(frame.columns) != 2:
        fail(f'El CSV de FRED para {code} no tiene el formato fecha, valor.', 'DATA_UNAVAILABLE')
    frame.columns = ['fecha', 'valor']
    frame['fecha'] = pd.to_datetime(frame['fecha'], format='%Y-%m-%d', errors='coerce')
    frame['valor'] = pd.to_numeric(frame['valor'], errors='coerce')
    return frame.dropna(subset=['fecha']).sort_values('fecha').reset_index(drop=True)


def infer_frequency(dates):
    """Frecuencia nativa aproximada a partir de la separación mediana entre fechas."""
    if len(dates) < 3:
        return 'desconocida'
    gap = float(np.median(np.diff(dates.to_numpy()).astype('timedelta64[D]').astype(float)))
    return 'diaria' if gap < 4 else 'semanal' if gap < 10 else 'mensual' if gap < 45 else 'trimestral' if gap < 120 else 'anual'


def fred_data(parameters, fetch=None):
    mapping = parse_series(parameters.get('series', DEFAULT_SERIES))
    start = parse_date(parameters.get('start_date', '2000-01-01'), date(2000, 1, 1), 'La fecha inicial')
    end = parse_date(parameters.get('end_date', ''), date.today(), 'La fecha final')
    if end < start:
        fail('La fecha final debe ser posterior a la inicial.')
    frequency = parameters.get('frequency', 'mensual')
    aggregation = parameters.get('aggregation', 'media')
    if frequency not in FREQUENCIES:
        fail('Frecuencia: original, semanal, mensual, trimestral o anual.')
    if aggregation not in AGGREGATIONS:
        fail('Agregación: media, ultimo o suma.')
    fetch = fetch or download
    with ThreadPoolExecutor(max_workers=min(6, len(mapping))) as pool:
        frames = list(pool.map(lambda code: fetch(code, start, end), mapping))
    native, parts = {}, []
    for (code, alias), frame in zip(mapping.items(), frames):
        if frame['valor'].notna().sum() == 0:
            fail(f'{code} no tiene datos entre {start} y {end}.', 'DATA_UNAVAILABLE')
        native[alias] = infer_frequency(frame['fecha'])
        series = frame.set_index('fecha')['valor'].rename(alias)
        rule = FREQUENCIES[frequency]
        if rule:
            grouped = series.resample(rule)
            series = grouped.mean() if aggregation == 'media' else grouped.last() if aggregation == 'ultimo' else grouped.sum(min_count=1)
        parts.append(series)
    data = pd.concat(parts, axis=1, join='outer').sort_index()
    data = data.dropna(how='all')
    if data.empty:
        fail('Ninguna serie tiene datos en el rango elegido.', 'DATA_UNAVAILABLE')
    if len(data) > MAX_ROWS:
        fail(f'La consulta produce {len(data)} filas; acorta el rango o usa una frecuencia menor.', 'DATASET_LIMIT')
    periodo = data.index.year.astype(int) if frequency == 'anual' else data.index.strftime('%Y-%m-%d')
    data.insert(0, 'periodo', periodo)
    data = data.reset_index(drop=True)
    mixed = len(set(native.values())) > 1 and frequency == 'original'
    series_meta = [{'id': code, 'alias': alias, 'native_frequency': native[alias],
                    'observations': int(data[alias].notna().sum()), 'url': SERIES_URL + code,
                    **{k: KNOWN[code][k] for k in ('title', 'units', 'seasonal') if code in KNOWN and k in KNOWN[code]}}
                   for code, alias in mapping.items()]
    notes = ['Fechas de FRED = inicio de cada período.']
    if frequency != 'original':
        notes.append(f'Convertidas a frecuencia {frequency} con {"la media" if aggregation == "media" else "el último valor" if aggregation == "ultimo" else "la suma"} de cada período; los períodos sin datos quedan vacíos.')
    if mixed:
        notes.append('Las series tienen frecuencias distintas: sin convertir, las filas de una serie quedan vacías en las fechas de otra. Elige mensual, trimestral o anual para alinearlas.')
    return data, {'provider': 'FRED · Federal Reserve Bank of St. Louis', 'series': series_meta,
                  'start': start.isoformat(), 'end': end.isoformat(), 'frequency': frequency, 'aggregation': aggregation,
                  'rows': len(data), 'source_url': URL,
                  'units': {item['alias']: item.get('units', 'consultar la ficha de la serie en FRED; no inferidas') for item in series_meta},
                  'note': ' '.join(notes) + ' Fuente: FRED, Federal Reserve Bank of St. Louis; respeta los términos de uso de cada serie.'}
