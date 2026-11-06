"""Yahoo Finance con yfinance: uno o más activos y, opcionalmente, un índice para compararlos.

- Tickers como lista permitida por expresión regular (nunca URL ni rutas); «TICKER: alias» por línea.
- Precios de cierre ajustados por dividendos y divisiones (``auto_adjust=True``).
- Las filas se alinean a las fechas en que cotizan todos (bolsas con feriados distintos): se informa cuántas se descartan.
- Salida: precios, rendimientos simples o logarítmicos (%) o índice base 100, más una tabla de comparación
  frente al índice (rendimiento, volatilidad, caída máxima, beta, correlación y R²) calculada con rendimientos simples.
- Caché de zonas horarias de yfinance en un directorio temporal por proceso (evita bloqueos de su SQLite).
"""
from datetime import date, timedelta
import atexit
import json
import re
import tempfile
import threading
import time

import numpy as np
import pandas as pd

from .core import EngineError, ROOT
from .fred_source import parse_date

CATALOG = json.loads((ROOT / 'packages/contracts/yfinanceCatalog.json').read_text(encoding='utf-8'))
INDICES = {item['ticker']: item for item in CATALOG['indices']}
ASSETS = {item['ticker']: item for item in CATALOG['assets']}
TICKER = re.compile(r'[A-Z0-9^][A-Z0-9^=._-]{0,19}')
ALIAS = re.compile(r'[A-Za-z_][A-Za-z0-9_]{0,40}')
INTERVALS = {'diario': ('1d', 252), 'semanal': ('1wk', 52), 'mensual': ('1mo', 12)}
VALUES = ['precios', 'rendimientos', 'log', 'base100']
DEFAULT_TICKERS = 'AAPL\nMSFT'
CACHE_SECONDS = 3600
_cache, _lock, _setup = {}, threading.Lock(), []
# yfinance comparte una caché SQLite y estado global: dos descargas a la vez (nodos en hilos paralelos) dan «database is locked».
_download_lock = threading.Lock()


def fail(message, code='INVALID_PARAMETERS'):
    raise EngineError(code, message)


def suggest_alias(ticker):
    known = ASSETS.get(ticker) or INDICES.get(ticker)
    if known:
        return known['alias']
    alias = re.sub(r'[^a-z0-9]+', '_', ticker.lower()).strip('_') or 'activo'
    return 't_' + alias if alias[0].isdigit() else alias


def parse_tickers(value):
    """«TICKER: alias» por línea, coma o punto y coma → dict ordenado ticker → alias."""
    if not isinstance(value, str):
        fail('Indica los activos como tickers de Yahoo Finance, uno por línea (p. ej. AAPL o WALMEX.MX).')
    mapping = {}
    for item in re.split(r'[\n;,]+', value):
        if not item.strip():
            continue
        code, _, alias = item.partition(':')
        code, alias = code.strip().upper(), alias.strip()
        if not TICKER.fullmatch(code):
            fail(f'Ticker no válido: «{code}». Usa el símbolo de Yahoo Finance, p. ej. AAPL, WALMEX.MX o BTC-USD.')
        alias = alias or suggest_alias(code)
        if not ALIAS.fullmatch(alias) or alias == 'periodo':
            fail(f'Alias no válido: «{alias}». Usa letras, números y «_», sin empezar por número ni llamarlo periodo.')
        if code in mapping:
            fail(f'El ticker {code} está repetido.')
        mapping[code] = alias
    if not mapping:
        fail('Añade al menos un activo.')
    if len(mapping) > 10:
        fail('Como máximo 10 activos por consulta.')
    return mapping


def isolate_cache():
    """yfinance guarda zonas horarias en SQLite: un directorio temporal por proceso evita «database is locked»."""
    with _lock:
        if not _setup:
            import yfinance as yf
            folder = tempfile.TemporaryDirectory(prefix='quantlabs-yfinance-')
            atexit.register(folder.cleanup)
            yf.set_tz_cache_location(folder.name)
            _setup.append(folder)


def download(tickers, start, end, interval):
    """Cierres ajustados (columnas = tickers). end es inclusivo; yfinance lo trata como exclusivo."""
    key = (tuple(tickers), start.isoformat(), end.isoformat(), interval)
    with _lock:
        hit = _cache.get(key)
        if hit and time.monotonic() - hit[0] < CACHE_SECONDS:
            return hit[1].copy()
    isolate_cache()
    import yfinance as yf
    try:
        with _download_lock:
            raw = yf.download(list(tickers), start=start.isoformat(), end=(end + timedelta(days=1)).isoformat(), interval=interval,
                              auto_adjust=True, progress=False, threads=False, actions=False)
    except Exception as exc:
        raise EngineError('DATA_UNAVAILABLE', 'Yahoo Finance no respondió. Revisa la conexión e inténtalo de nuevo.') from exc
    if raw is None or raw.empty or 'Close' not in raw.columns.get_level_values(0):
        fail('Yahoo Finance no devolvió precios para esos tickers y fechas.', 'DATA_UNAVAILABLE')
    close = raw['Close']
    if isinstance(close, pd.Series):
        close = close.to_frame(tickers[0])
    close = close.reindex(columns=list(tickers))
    close.index = pd.to_datetime(close.index).tz_localize(None) if getattr(close.index, 'tz', None) else pd.to_datetime(close.index)
    with _lock:
        _cache[key] = (time.monotonic(), close)
    return close.copy()


def max_drawdown(prices):
    path = prices / prices.cummax() - 1
    return float(path.min() * 100)


def comparison(prices, names, index_name, per_year):
    """Tabla por activo: rendimientos y riesgo; frente al índice, beta, correlación y R² con rendimientos simples."""
    returns = prices.pct_change(fill_method=None).dropna()
    years = len(returns) / per_year
    rows = []
    for name in names + ([index_name] if index_name else []):
        r = returns[name]
        total = prices[name].iloc[-1] / prices[name].iloc[0] - 1
        row = [name, total * 100, ((1 + total) ** (1 / years) - 1) * 100 if years > 0 and total > -1 else None,
               r.std(ddof=1) * np.sqrt(per_year) * 100, max_drawdown(prices[name])]
        if index_name:
            if name == index_name:
                row += [1.0, 1.0, 1.0]
            else:
                market = returns[index_name]
                beta = float(np.cov(r, market, ddof=1)[0, 1] / market.var(ddof=1)) if market.var(ddof=1) > 0 else None
                corr = float(r.corr(market))
                row += [beta, corr, corr ** 2]
        rows.append(row)
    columns = ['Serie', 'Rendimiento total (%)', 'Rendimiento anualizado (%)', 'Volatilidad anualizada (%)', 'Caída máxima (%)']
    if index_name:
        columns += [f'Beta vs {index_name}', 'Correlación', 'R²']
    return {'title': 'Comparación de activos' + (f' frente a {index_name}' if index_name else ''), 'columns': columns,
            'rows': [[(float(v) if np.isfinite(v) else None) if isinstance(v, (float, np.floating)) else v for v in row] for row in rows]}


def yfinance_data(parameters, fetch=None):
    mapping = parse_tickers(parameters.get('tickers', DEFAULT_TICKERS))
    index = parameters.get('index', '^GSPC')
    if index != 'ninguno' and index not in INDICES:
        fail('Elige un índice de la lista o «ninguno».')
    index = None if index == 'ninguno' else index
    if index and index in mapping:
        fail(f'{index} ya es el índice de comparación; quítalo de los activos.')
    start = parse_date(parameters.get('start_date', '2020-01-01'), date(2020, 1, 1), 'La fecha inicial')
    end = parse_date(parameters.get('end_date', ''), date.today(), 'La fecha final')
    if end <= start:
        fail('La fecha final debe ser posterior a la inicial.')
    interval = parameters.get('interval', 'diario')
    values = parameters.get('values', 'rendimientos')
    if interval not in INTERVALS:
        fail('Intervalo: diario, semanal o mensual.')
    if values not in VALUES:
        fail('Valores: precios, rendimientos, log o base100.')
    code, per_year = INTERVALS[interval]
    tickers = list(mapping) + ([index] if index else [])
    prices = (fetch or download)(tickers, start, end, code)
    missing = [t for t in tickers if t not in prices or prices[t].notna().sum() == 0]
    if missing:
        fail(f'Yahoo Finance no tiene precios de {", ".join(missing)} en ese rango. Revisa el ticker (p. ej. las acciones de la BMV terminan en .MX).', 'DATA_UNAVAILABLE')
    names = {**mapping, **({index: INDICES[index]['alias']} if index else {})}
    if len(set(names.values())) != len(names):
        fail('Cada activo y el índice necesitan un alias distinto.')
    prices = prices[tickers].rename(columns=names).sort_index()
    total_rows = len(prices)
    prices = prices.dropna(how='any')
    if len(prices) < 3:
        fail('Hay menos de tres fechas en que coticen todos los activos y el índice.', 'INSUFFICIENT_SAMPLE')
    asset_names = list(mapping.values())
    index_name = names.get(index) if index else None
    table = comparison(prices, asset_names, index_name, per_year)
    if values == 'precios':
        data = prices
    elif values == 'rendimientos':
        data = prices.pct_change(fill_method=None) * 100
    elif values == 'log':
        data = np.log(prices).diff() * 100
    else:
        data = prices / prices.iloc[0] * 100
    data = data.iloc[1:] if values in ('rendimientos', 'log') else data
    frame = data.reset_index(drop=False)
    frame.insert(0, 'periodo', pd.to_datetime(frame.pop(frame.columns[0])).dt.strftime('%Y-%m-%d'))
    frame = frame.reset_index(drop=True)
    frame.columns.name = None
    labels = {'precios': 'precio de cierre ajustado', 'rendimientos': 'rendimiento simple por período (%)',
              'log': 'rendimiento logarítmico por período (%)', 'base100': 'índice base 100 en la primera fecha común'}
    note = (f'Cierres ajustados por dividendos y divisiones; {labels[values]}. Se conservan solo las fechas en que cotizan todas las series '
            f'({total_rows - len(prices)} de {total_rows} descartadas). Volatilidad anualizada con {per_year} períodos por año.')
    if interval == 'diario':
        note += ' Los días hábiles no forman un calendario regular: para rezagos o pruebas de raíz unitaria usa intervalo semanal o mensual.'
    source = {'provider': 'Yahoo Finance (yfinance)', 'tickers': mapping, 'index': index, 'index_name': INDICES[index]['name'] if index else None,
              'start': start.isoformat(), 'end': end.isoformat(), 'interval': interval, 'values': values, 'rows': len(frame),
              'dropped_rows': total_rows - len(prices), 'comparison': table, 'units': {name: labels[values] for name in names.values()},
              'note': note + ' Datos de Yahoo Finance para uso educativo; no son asesoría financiera.'}
    return frame, source
