"""Complete World Bank indicator catalog, cached locally and searched in pages."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import tempfile
import unicodedata

import requests

from .core import EngineError, ROOT

URL = 'https://api.worldbank.org/v2/es/indicator'
PAGE_SIZE = 10000
TTL_SECONDS = 86400


def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))


def fetch_page(page):
    response = requests.get(URL, params={'format': 'json', 'per_page': PAGE_SIZE, 'page': page}, timeout=(5, 18))
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or len(payload) != 2 or not isinstance(payload[0], dict) or not isinstance(payload[1], list):
        raise ValueError('Invalid catalog page')
    metadata, rows = payload
    if int(metadata.get('page', 0)) != page:
        raise ValueError('Wrong catalog page')
    return metadata, rows


def cache_file():
    override = os.environ.get('QUANTLABS_CATALOG_CACHE')
    if override:
        return Path(override)
    # Development shares the cache directory already selected by the transport.
    wb_cache = os.environ.get('WBDATA_CACHE_PATH')
    if wb_cache:
        return Path(wb_cache).parent / 'indicators-es-v1.json'
    return ROOT / '.cache/wbdata/indicators-es-v1.json'


def read_cache(path):
    try:
        if path.stat().st_size > 25_000_000:
            return None
        data = json.loads(path.read_text())
        if data.get('catalog_version') != 1 or not isinstance(data.get('items'), list) or not data['items']:
            return None
        for row in data['items']:
            if not isinstance(row, dict) or any(not isinstance(row.get(k), str) for k in ['id', 'name', 'source', 'source_name', 'unit']):
                return None
        datetime.fromisoformat(data['retrieved_at'])
        return data
    except (OSError, ValueError, KeyError, TypeError):
        return None


def get_catalog(refresh=False):
    path = cache_file()
    cached = read_cache(path)
    now = datetime.now(timezone.utc)
    if cached and not refresh and (now - datetime.fromisoformat(cached['retrieved_at'])).total_seconds() < TTL_SECONDS:
        return cached, False
    try:
        first, rows = fetch_page(1)
        pages = int(first['pages'])
        if not 1 <= pages <= 20:
            raise ValueError('Catalog too large')
        with ThreadPoolExecutor(max_workers=3) as pool:
            for metadata, batch in pool.map(fetch_page, range(2, pages + 1)):
                if int(metadata['total']) != int(first['total']) or int(metadata['pages']) != pages:
                    raise ValueError('Catalog changed during download')
                rows.extend(batch)
        if len(rows) != int(first['total']):
            raise ValueError('Incomplete catalog')
        unique = {}
        for row in rows:
            code, source = str(row['id']), str(row['source']['id'])
            if not source.isdigit():
                raise ValueError('Invalid source')
            unique[(source, code)] = {'id': code, 'name': row.get('name') or code,
                                      'source': source, 'source_name': row['source'].get('value') or f'Fuente {source}',
                                      'unit': row.get('unit') or ''}
        items = sorted(unique.values(), key=lambda row: (row['source'] != '2', normalize(row['name']), row['id'], row['source']))
        data = {'catalog_version': 1, 'retrieved_at': now.isoformat(), 'items': items}
        # Never replace a valid cache with a partial response.
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(data, stream, ensure_ascii=False, separators=(',', ':'))
            os.replace(temporary, path)
        except OSError:
            if 'temporary' in locals():
                temporary.unlink(missing_ok=True)
        return data, False
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        if cached:
            return cached, True
        raise EngineError('CATALOG_UNAVAILABLE', 'No se pudo cargar el catálogo del Banco Mundial. Reintenta cuando tengas conexión.') from exc


def search_indicators(parameters):
    query = parameters.get('query', '')
    page = parameters.get('page', 1)
    refresh = parameters.get('refresh', False)
    if not isinstance(query, str) or len(query) > 200 or isinstance(page, bool) or not isinstance(page, int) or not 1 <= page <= 2000 or not isinstance(refresh, bool):
        raise EngineError('INVALID_PARAMETERS', 'La búsqueda de indicadores no es válida.')
    catalog, stale = get_catalog(refresh=refresh)
    tokens = normalize(query).split()
    matches = [row for row in catalog['items'] if all(token in normalize(f"{row['id']} {row['name']} {row['source_name']}") for token in tokens)]
    per_page = 100
    return {'items': matches[(page - 1) * per_page:page * per_page], 'page': page,
            'pages': math.ceil(len(matches) / per_page), 'total': len(matches),
            'catalog_total': len(catalog['items']), 'retrieved_at': catalog['retrieved_at'],
            'stale': stale, 'language': 'es', 'source_url': URL}
