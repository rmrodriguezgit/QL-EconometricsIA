"""Herramientas cuantitativas integradas desde Quantlabs-Blueprints, adaptadas al motor de tablas.

- ``data_quality``   Calidad de datos: duplicados, infinitos, faltantes (informar, eliminar o arrastrar) y atípicos.
- ``resample``       Cambiar la frecuencia de una tabla con fechas (semanal, mensual, trimestral, anual).
- ``select_columns`` Elegir, ordenar y renombrar columnas.
- ``quant_features`` Indicadores de un precio: rendimientos, volatilidad y Sharpe móviles, caída, medias, RSI, MACD y Bollinger.
- ``risk_metrics``   Desempeño y riesgo de series de rendimientos: Sharpe, Sortino, caída máxima, VaR/CVaR, beta y alfa.
- ``portfolio``      Portafolio de Markowitz: pesos iguales, mínima varianza, máximo Sharpe y máximo Sortino, con frontera eficiente, riesgo y prueba fuera de muestra.
- ``ml_compare``     Modelos clásicos de aprendizaje automático (media, Ridge, ElasticNet, bosque aleatorio, boosting, SVR, KNN) con selección por validación temporal.

Todas trabajan sobre filas ordenadas, sin mirar el futuro, y documentan en el resultado qué hicieron.
"""
import numpy as np
import pandas as pd

from .core import EngineError, number

QUANT_TOOLS = {'data_quality', 'resample', 'select_columns', 'quant_features', 'risk_metrics', 'portfolio', 'ml_compare'}


def fail(message, code='INVALID_PARAMETERS'):
    raise EngineError(code, message)


def choice(params, key, options, default):
    value = params.get(key, default)
    if value not in options:
        fail(f'{key}: elige {", ".join(options)}.')
    return value


def names(frame, value, label, numeric=True, allow_empty=False):
    items = [item.strip() for item in str(value or '').split(',') if item.strip()]
    if not items:
        if allow_empty:
            return [c for c in frame.columns if c != 'periodo' and pd.api.types.is_numeric_dtype(frame[c])]
        fail(f'Indica {label} separadas por coma.')
    missing = [item for item in items if item not in frame.columns]
    if missing:
        fail(f'No existen {", ".join(missing)}. Columnas disponibles: {", ".join(map(str, frame.columns))}.')
    if numeric:
        bad = [item for item in items if not pd.api.types.is_numeric_dtype(frame[item])]
        if bad:
            fail(f'{", ".join(bad)} no son numéricas.')
    if len(set(items)) != len(items):
        fail(f'Hay {label} repetidas.')
    return items


def report(text, **metrics):
    return {'kind': 'analysis', 'interpretation': text, 'metrics': [{'label': k, 'value': v} for k, v in metrics.items()],
            'tables': [], 'series': [], 'limitations': [], 'warnings': []}


def table(title, columns, rows):
    return {'title': title, 'columns': columns, 'rows': [[(float(v) if np.isfinite(v) else None) if isinstance(v, (float, np.floating)) else v for v in row] for row in rows]}


def dates(frame):
    if 'periodo' not in frame.columns:
        fail('La tabla necesita una columna periodo con fechas AAAA-MM-DD o años.')
    raw = frame['periodo']
    if pd.api.types.is_numeric_dtype(raw):
        values = pd.to_datetime(raw.astype('Int64').astype(str) + '-01-01', format='%Y-%m-%d', errors='coerce')
    else:
        values = pd.to_datetime(raw.astype(str), format='%Y-%m-%d', errors='coerce')
    if values.isna().any():
        fail('periodo debe contener fechas AAAA-MM-DD o años enteros.')
    return values


# ---------------------------------------------------------------- preparación

def data_quality(frame, params):
    duplicates = choice(params, 'duplicates', ['informar', 'ultimo'], 'informar')
    missing = choice(params, 'missing', ['informar', 'eliminar', 'arrastrar'], 'informar')
    limit = number(params, 'ffill_limit', 3, 1, 30, True)
    z_limit = number(params, 'outlier_z', 4, 1, 20)
    data = frame.copy()
    numeric = [c for c in data.columns if c != 'periodo' and pd.api.types.is_numeric_dtype(data[c])]
    infinite = {c: int(np.isinf(data[c].to_numpy(dtype=float)).sum()) for c in numeric}
    data[numeric] = data[numeric].replace([np.inf, -np.inf], np.nan)
    before = len(data)
    duplicated = 0
    if 'periodo' in data.columns:
        duplicated = int(data['periodo'].duplicated(keep='last').sum())
        if duplicated and duplicates == 'ultimo':
            data = data.loc[~data['periodo'].duplicated(keep='last')]
        try:
            order = dates(data).argsort(kind='stable').to_numpy()
            unsorted = not np.array_equal(order, np.arange(len(data)))
            data = data.iloc[order]
        except EngineError:
            unsorted = False
    else:
        unsorted = False
    missing_before = {c: int(data[c].isna().sum()) for c in numeric}
    if missing == 'arrastrar':
        data[numeric] = data[numeric].ffill(limit=limit)
    if missing in ('arrastrar', 'eliminar'):
        data = data.dropna(subset=numeric)
    if len(data) < 3:
        fail('La limpieza deja menos de tres filas.', 'INSUFFICIENT_SAMPLE')
    rows = []
    for c in numeric:
        values = data[c].to_numpy(dtype=float)
        finite = values[np.isfinite(values)]
        sd = finite.std(ddof=1) if len(finite) > 1 else 0
        outliers = int(np.sum(np.abs(finite - finite.mean()) > z_limit * sd)) if sd > 0 else 0
        rows.append([c, missing_before[c], infinite[c], int(np.isnan(values).sum()), outliers, 'sí' if len(np.unique(finite)) <= 1 else 'no'])
    result = report(f'Revisión de calidad: duplicados de periodo → {duplicates}; faltantes → {missing}'
                    + (f' (arrastre de hasta {limit} filas)' if missing == 'arrastrar' else '') + '. Los atípicos se cuentan, no se eliminan.',
                    filas_entrada=before, filas_salida=len(data), periodos_duplicados=duplicated, desordenada='sí' if unsorted else 'no')
    result['tables'] = [table('Calidad por columna', ['Columna', 'Faltantes', 'Infinitos (→ faltante)', 'Faltantes tras limpiar', f'Atípicos |z| > {z_limit:g}', 'Constante'], rows)]
    if duplicated and duplicates == 'informar':
        result['warnings'].append(f'Hay {duplicated} periodos repetidos; elige «ultimo» para conservar la última fila de cada uno o filtra antes (p. ej. un país).')
    if missing == 'informar' and any(missing_before.values()):
        result['warnings'].append('Hay faltantes; la tabla de salida los conserva. Elige eliminar o arrastrar para limpiarlos.')
    result['limitations'] = ['Arrastrar el último valor supone que la serie no cambió; úsalo solo en huecos cortos (feriados).']
    return result, {'result': result, 'data': data.reset_index(drop=True)}


RULES = {'semanal': 'W-FRI', 'mensual': 'MS', 'trimestral': 'QS', 'anual': 'YS'}


def resample(frame, params):
    frequency = choice(params, 'frequency', list(RULES), 'mensual')
    aggregation = choice(params, 'aggregation', ['ultimo', 'media', 'suma', 'primero'], 'ultimo')
    incomplete = choice(params, 'incomplete', ['excluir', 'conservar'], 'excluir')
    columns = names(frame, params.get('columns', ''), 'las columnas', allow_empty=True)
    if not columns:
        fail('No hay columnas numéricas para remuestrear.')
    stamp = dates(frame)
    data = frame[columns].copy()
    data.index = stamp.values
    data = data.sort_index()
    grouped = data.resample(RULES[frequency])
    out = {'ultimo': grouped.last, 'media': grouped.mean, 'primero': grouped.first, 'suma': lambda: grouped.sum(min_count=1)}[aggregation]()
    counts = grouped.size()
    dropped = 0
    if incomplete == 'excluir' and len(out) > 1:
        # Incompleto si la última fecha observada queda antes del cierre del período (margen: fin de semana + un feriado).
        if frequency == 'semanal':
            period_end, margin = out.index[-1], 1  # W-FRI etiqueta con el viernes de cierre
        else:
            period_end, margin = out.index[-1] + pd.tseries.frequencies.to_offset(RULES[frequency]) - pd.Timedelta(days=1), 3
        if data.index.max() < period_end - pd.Timedelta(days=margin):
            out, counts, dropped = out.iloc[:-1], counts.iloc[:-1], 1
    out = out.dropna(how='all')
    if len(out) < 2:
        fail('El remuestreo deja menos de dos períodos.', 'INSUFFICIENT_SAMPLE')
    result_frame = out.reset_index(drop=True)
    result_frame.insert(0, 'periodo', out.index.year.astype(int) if frequency == 'anual' else out.index.strftime('%Y-%m-%d'))
    result = report(f'Frecuencia {frequency} con {"el último valor" if aggregation == "ultimo" else "el primer valor" if aggregation == "primero" else "la " + aggregation} de cada período. '
                    'Las fechas son el inicio del período (viernes de cierre en semanal).', periodos=len(result_frame), filas_originales=len(frame),
                    periodo_incompleto_excluido='sí' if dropped else 'no', observaciones_por_periodo_min=int(counts.loc[out.index].min()))
    return result, {'result': result, 'data': result_frame}


def select_columns(frame, params):
    spec = str(params.get('columns', '') or '')
    items = [item.strip() for item in spec.replace('\n', ',').split(',') if item.strip()]
    if not items:
        fail('Escribe las columnas a conservar, p. ej. «periodo, precio: cierre».')
    picked, renamed = [], {}
    for item in items:
        old, _, new = item.partition(':')
        old, new = old.strip(), new.strip()
        if old not in frame.columns:
            fail(f'No existe la columna «{old}». Disponibles: {", ".join(map(str, frame.columns))}.')
        if old in picked:
            fail(f'«{old}» está repetida.')
        picked.append(old)
        if new:
            if not new.replace('_', 'a').isalnum() or new[0].isdigit():
                fail(f'Nombre nuevo no válido: «{new}». Usa letras, números y «_».')
            renamed[old] = new
    data = frame[picked].rename(columns=renamed)
    if data.columns.duplicated().any():
        fail('Dos columnas terminarían con el mismo nombre.')
    result = report('Columnas elegidas en este orden' + (f'; renombradas: {", ".join(f"{a} → {b}" for a, b in renamed.items())}.' if renamed else '.'),
                    columnas=len(picked), descartadas=len(frame.columns) - len(picked))
    return result, {'result': result, 'data': data}


# ---------------------------------------------------------------- indicadores y riesgo

def rsi(price, window):
    change = price.diff()
    gain, loss = change.clip(lower=0), -change.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).where(avg_loss > 0, 100.)


def quant_features(frame, params):
    column = str(params.get('price', 'precio'))
    if column not in frame.columns or not pd.api.types.is_numeric_dtype(frame[column]):
        fail(f'Elige una columna de precios numérica. Disponibles: {", ".join(map(str, frame.columns))}.')
    window = number(params, 'window', 20, 2, 252, True)
    annual = number(params, 'periods_per_year', 252, 1, 366, True)
    rf = number(params, 'risk_free', .02, -.99, 1)
    data = frame.copy()
    if 'periodo' in data.columns:
        # Periodo numérico (años o índice) se ordena tal cual; si no, como fechas ISO.
        key = data['periodo'] if pd.api.types.is_numeric_dtype(data['periodo']) else dates(data)
        data = data.iloc[key.argsort(kind='stable').to_numpy()].reset_index(drop=True)
    price = data[column].astype(float)
    if (price.dropna() <= 0).any():
        fail('Los indicadores requieren precios positivos.')
    p = column
    r = price.pct_change(fill_method=None)
    data[f'{p}_rend'] = r * 100
    data[f'{p}_rend_log'] = np.log(price / price.shift(1)) * 100
    data[f'{p}_vol_movil'] = r.rolling(window).std(ddof=1) * np.sqrt(annual) * 100
    excess = r - ((1 + rf) ** (1 / annual) - 1)
    data[f'{p}_sharpe_movil'] = excess.rolling(window).mean() / r.rolling(window).std(ddof=1).replace(0, np.nan) * np.sqrt(annual)
    data[f'{p}_caida'] = (price / price.cummax() - 1) * 100
    data[f'{p}_sma'] = price.rolling(window).mean()
    data[f'{p}_ema'] = price.ewm(span=window, adjust=False).mean()
    data[f'{p}_rsi'] = rsi(price, 14)
    macd = price.ewm(span=12, adjust=False).mean() - price.ewm(span=26, adjust=False).mean()
    data[f'{p}_macd'] = macd
    data[f'{p}_macd_senal'] = macd.ewm(span=9, adjust=False).mean()
    mid, sd = price.rolling(window).mean(), price.rolling(window).std(ddof=0)
    data[f'{p}_boll_sup'], data[f'{p}_boll_inf'] = mid + 2 * sd, mid - 2 * sd
    added = [c for c in data.columns if c.startswith(f'{p}_') and c not in frame.columns]
    last = data.iloc[-1]
    result = report(f'Indicadores de {p} con ventana {window} y {annual} períodos por año. Cada valor usa solo datos hasta su fila (sin mirar el futuro); '
                    'las primeras filas quedan vacías hasta completar la ventana.', columnas_nuevas=len(added), filas=len(data),
                    rsi_final=float(last[f'{p}_rsi']) if pd.notna(last[f'{p}_rsi']) else None, caida_maxima_pct=float(data[f'{p}_caida'].min()))
    result['tables'] = [table('Columnas añadidas', ['Columna', 'Qué mide'], [
        [f'{p}_rend', 'Rendimiento simple por período (%)'], [f'{p}_rend_log', 'Rendimiento logarítmico (%)'],
        [f'{p}_vol_movil', f'Volatilidad anualizada de {window} períodos (%)'], [f'{p}_sharpe_movil', f'Sharpe anualizado móvil (tasa libre {rf:.1%})'],
        [f'{p}_caida', 'Caída desde el máximo previo (%)'], [f'{p}_sma', f'Media móvil simple de {window}'], [f'{p}_ema', f'Media móvil exponencial de {window}'],
        [f'{p}_rsi', 'RSI de 14 (Wilder)'], [f'{p}_macd', 'MACD 12-26'], [f'{p}_macd_senal', 'Señal del MACD (9)'],
        [f'{p}_boll_sup', 'Banda de Bollinger superior (±2 DE)'], [f'{p}_boll_inf', 'Banda de Bollinger inferior']])]
    result['series'] = [{'label': p, 'points': [[i, float(v)] for i, v in enumerate(price) if pd.notna(v)][-1500:]},
                        {'label': f'{p} media móvil', 'points': [[i, float(v)] for i, v in enumerate(data[f'{p}_sma']) if pd.notna(v)][-1500:]}]
    return result, {'result': result, 'data': data}


def to_returns(frame, columns, kind):
    data = frame[columns].astype(float)
    if kind == 'precios':
        data = data.pct_change(fill_method=None)
    elif kind == 'porcentaje':
        data = data / 100
    elif kind == 'log':
        data = np.expm1(data / 100)
    return data


def performance(r, annual, rf, confidence, benchmark=None):
    r = r.dropna()
    if len(r) < 3:
        return None
    rf_period = (1 + rf) ** (1 / annual) - 1
    equity = (1 + r).cumprod()
    total = float(equity.iloc[-1] - 1)
    years = len(r) / annual
    cagr = (1 + total) ** (1 / years) - 1 if total > -1 and years > 0 else np.nan
    vol = float(r.std(ddof=1) * np.sqrt(annual))
    excess = r - rf_period
    downside = np.sqrt(np.mean(np.minimum(excess, 0) ** 2)) * np.sqrt(annual)
    drawdown = float((equity / equity.cummax() - 1).min())
    var = float(-np.quantile(r, 1 - confidence))
    tail = r[r <= -var]
    out = {'total': total, 'cagr': cagr, 'vol': vol, 'sharpe': float(excess.mean() / r.std(ddof=1) * np.sqrt(annual)) if r.std(ddof=1) > 0 else np.nan,
           'sortino': float(excess.mean() * annual / downside) if downside > 0 else np.nan, 'drawdown': drawdown,
           'calmar': cagr / abs(drawdown) if drawdown < 0 else np.nan, 'var': var, 'cvar': float(-tail.mean()) if len(tail) else np.nan,
           'skew': float(r.skew()), 'kurt': float(r.kurt()), 'n': len(r), 'equity': equity}
    if benchmark is not None:
        b = benchmark.reindex(r.index).dropna()
        common = r.reindex(b.index)
        if len(b) > 2 and b.var(ddof=1) > 0:
            beta = float(np.cov(common, b, ddof=1)[0, 1] / b.var(ddof=1))
            alpha = float(((common - rf_period) - beta * (b - rf_period)).mean() * annual)
            te = float((common - b).std(ddof=1) * np.sqrt(annual))
            out.update({'beta': beta, 'alpha': alpha, 'te': te, 'ir': float((common - b).mean() * annual / te) if te > 0 else np.nan,
                        'corr': float(common.corr(b))})
    return out


def risk_metrics(frame, params):
    columns = names(frame, params.get('columns', ''), 'las columnas de rendimientos o precios')
    kind = choice(params, 'values', ['porcentaje', 'decimal', 'log', 'precios'], 'porcentaje')
    bench = str(params.get('benchmark', '') or '').strip()
    annual = number(params, 'periods_per_year', 252, 1, 366, True)
    rf = number(params, 'risk_free', 0, -.99, 1)
    confidence = number(params, 'confidence', .95, .5, .999)
    if bench and bench not in frame.columns:
        fail(f'No existe la columna de referencia «{bench}».')
    returns = to_returns(frame, columns + ([bench] if bench and bench not in columns else []), kind)
    benchmark = returns[bench] if bench else None
    rows, series = [], []
    for c in columns:
        m = performance(returns[c], annual, rf, confidence, benchmark if c != bench else None)
        if m is None:
            fail(f'{c} tiene menos de tres rendimientos.', 'INSUFFICIENT_SAMPLE')
        row = [c, m['n'], m['total'] * 100, m['cagr'] * 100, m['vol'] * 100, m['sharpe'], m['sortino'], m['drawdown'] * 100, m['calmar'],
               m['var'] * 100, m['cvar'] * 100, m['skew'], m['kurt']]
        if bench:
            row += [m.get('beta'), (m.get('alpha') or np.nan) * 100 if m.get('alpha') is not None else None, m.get('corr'), m.get('ir')]
        rows.append(row)
        series.append({'label': f'Capital de {c}', 'points': [[i, float(v)] for i, v in enumerate(m['equity'])][-1500:]})
    level = f'{confidence:.0%}'
    head = ['Serie', 'n', 'Rendimiento total (%)', 'Rendimiento anual compuesto (%)', 'Volatilidad anual (%)', 'Sharpe', 'Sortino', 'Caída máxima (%)', 'Calmar',
            f'VaR {level} (%)', f'CVaR {level} (%)', 'Asimetría', 'Curtosis exceso']
    if bench:
        head += [f'Beta vs {bench}', 'Alfa anual (%)', 'Correlación', 'Ratio de información']
    result = report(f'Métricas con {annual} períodos por año y tasa libre de riesgo {rf:.2%} anual. VaR y CVaR históricos de un período '
                    f'(pérdida que no se supera con {level} de confianza y pérdida media más allá). Uso educativo, no asesoría financiera.',
                    series=len(columns), periodos=int(returns[columns].notna().sum().max()))
    result['tables'] = [table('Desempeño y riesgo', head, rows)]
    result['series'] = series
    result['limitations'] = ['Rendimientos pasados no garantizan rendimientos futuros.', 'El VaR histórico depende de la ventana: no captura riesgos que no ocurrieron en la muestra.']
    return result, {'result': result}


# ---------------------------------------------------------------- portafolio

def project_weights(w, cap):
    """Proyección a pesos no negativos que suman 1 con tope por activo."""
    w = np.clip(w, 0, None)
    for _ in range(100):
        w = w / w.sum() if w.sum() > 0 else np.full(len(w), 1 / len(w))
        over = w > cap + 1e-12
        if not over.any():
            break
        excess = (w[over] - cap).sum()
        w[over] = cap
        free = ~over & (w < cap)
        w[free] += excess * (w[free] / w[free].sum() if w[free].sum() > 0 else 1 / free.sum())
    return w


def downside_deviation(returns, w, rf_period, annual):
    """Desviación a la baja anualizada respecto de la tasa libre de riesgo por período (denominador del Sortino)."""
    excess = returns @ w - rf_period
    return float(np.sqrt(np.mean(np.minimum(excess, 0) ** 2) * annual))


def optimize(mean, cov, rf, cap, objective, returns=None, rf_period=0, annual=252, starts=()):
    """Pesos solo largos que suman 1 con tope por activo. Varios puntos de partida: se conserva el mejor objetivo."""
    from scipy.optimize import minimize
    n = len(mean)
    if objective == 'minima_varianza':
        fun = lambda w: w @ cov @ w
    elif objective == 'maximo_sharpe':
        fun = lambda w: -(w @ mean - rf) / np.sqrt(max(w @ cov @ w, 1e-18))
    else:  # maximo_sortino
        fun = lambda w: -(w @ mean - rf) / max(downside_deviation(returns, w, rf_period, annual), 1e-9)
    best, best_value = None, np.inf
    for start in [np.full(n, 1 / n), *starts]:
        start = project_weights(np.asarray(start, dtype=float), cap)
        res = minimize(fun, start, method='SLSQP', bounds=[(0, cap)] * n, constraints=[{'type': 'eq', 'fun': lambda w: w.sum() - 1}],
                       options={'maxiter': 500, 'ftol': 1e-12})
        candidate = project_weights(res.x if np.all(np.isfinite(res.x)) else start, cap)
        value = fun(candidate)
        if value < best_value:
            best, best_value = candidate, value
    return best


def portfolio(frame, params):
    from scipy.optimize import linprog, minimize
    columns = names(frame, params.get('columns', ''), 'las columnas de los activos')
    if len(columns) < 2:
        fail('Un portafolio necesita al menos dos activos.')
    kind = choice(params, 'values', ['porcentaje', 'decimal', 'log', 'precios'], 'porcentaje')
    annual = number(params, 'periods_per_year', 252, 1, 366, True)
    rf = number(params, 'risk_free', 0, -.99, 1)
    cap = number(params, 'max_weight', 1, 1 / len(columns), 1)
    fraction = number(params, 'fraction', .7, .3, .95)
    covariance = choice(params, 'covariance', ['muestral', 'contraccion'], 'contraccion')
    returns = to_returns(frame, columns, kind).dropna()
    if len(returns) < 20:
        fail('Se necesitan al menos 20 períodos completos.', 'INSUFFICIENT_SAMPLE')
    n = len(columns)
    cut = int(len(returns) * fraction)
    train, test = returns.iloc[:cut], returns.iloc[cut:]
    R = train.to_numpy()
    rf_period = (1 + rf) ** (1 / annual) - 1
    mean = train.mean().to_numpy() * annual
    if covariance == 'contraccion':
        from sklearn.covariance import LedoitWolf
        cov = LedoitWolf().fit(R).covariance_ * annual
    else:
        cov = train.cov(ddof=1).to_numpy() * annual

    def stats(w):
        ret, vol = float(w @ mean), float(np.sqrt(max(w @ cov @ w, 0)))
        down = downside_deviation(R, w, rf_period, annual)
        return {'ret': ret, 'vol': vol, 'down': down, 'sharpe': (ret - rf) / vol if vol > 0 else np.nan,
                'sortino': (ret - rf) / down if down > 0 else np.nan}

    # Frontera de mínima varianza: rama eficiente (desde la mínima varianza hasta el máximo rendimiento alcanzable) y rama ineficiente.
    bounds = [(0, cap)] * n
    reach = [linprog(sign * mean, A_eq=np.ones((1, n)), b_eq=[1], bounds=bounds, method='highs') for sign in (1, -1)]
    low_ret, high_ret = (float(r.x @ mean) if r.success else float(f(mean)) for r, f in zip(reach, (np.min, np.max)))
    gmv = optimize(mean, cov, rf, cap, 'minima_varianza')
    gmv_ret = float(gmv @ mean)

    def frontier_at(targets):
        points, start = [], gmv
        for target in targets:
            res = minimize(lambda w: w @ cov @ w, start, method='SLSQP', bounds=bounds,
                           constraints=[{'type': 'eq', 'fun': lambda w: w.sum() - 1}, {'type': 'eq', 'fun': lambda w, t=target: w @ mean - t}],
                           options={'maxiter': 300, 'ftol': 1e-12})
            if res.success:
                w = project_weights(res.x, cap)
                points.append((w, stats(w)))
                start = w
        return points

    span = high_ret - gmv_ret
    efficient = [(gmv, stats(gmv))] + frontier_at(np.linspace(gmv_ret, high_ret - 1e-9 * max(abs(span), 1), 31)[1:]) if span > 1e-12 else [(gmv, stats(gmv))]
    lower = frontier_at(np.linspace(gmv_ret, low_ret + 1e-9, 13)[1:]) if gmv_ret - low_ret > 1e-12 else []
    # Nube de portafolios aleatorios (semilla fija): muestra la región factible coloreada por Sharpe o Sortino.
    rng = np.random.default_rng(7)
    cloud_w = np.array([project_weights(w, cap) for w in rng.dirichlet(np.ones(n), 600)])
    best_sharpe = max(efficient, key=lambda p: -np.inf if not np.isfinite(p[1]['sharpe']) else p[1]['sharpe'])[0]
    cloud_stats = [stats(w) for w in cloud_w]
    best_cloud_sortino = cloud_w[int(np.nanargmax([s['sortino'] if np.isfinite(s['sortino']) else -np.inf for s in cloud_stats]))]

    weights = {'Pesos iguales': np.full(n, 1 / n),
               'Mínima varianza': gmv,
               'Máximo Sharpe': optimize(mean, cov, rf, cap, 'maximo_sharpe', starts=[best_sharpe]),
               'Máximo Sortino': optimize(mean, cov, rf, cap, 'maximo_sortino', R, rf_period, annual, starts=[best_sharpe, best_cloud_sortino])}
    level = '95 %'
    weight_rows, expected_rows, risk_rows, perf_rows, series, outputs, markers = [], [], [], [], [], pd.DataFrame(index=test.index), []
    for label, w in weights.items():
        s = stats(w)
        hist = performance(pd.Series(R @ w, index=train.index), annual, rf, .95)
        weight_rows.append([label, *[x * 100 for x in w], 1 / float(np.sum(w ** 2)), float(w.max()) * 100])
        expected_rows.append([label, s['ret'] * 100, s['vol'] * 100, s['vol'] ** 2, s['down'] * 100, s['sharpe'], s['sortino'],
                              hist['var'] * 100, hist['cvar'] * 100, hist['drawdown'] * 100])
        total_var = float(w @ cov @ w)
        risk_rows.append([label, *[float(w[i] * (cov @ w)[i] / total_var * 100) if total_var > 0 else None for i in range(n)]])
        path = test.to_numpy() @ w
        m = performance(pd.Series(path, index=test.index), annual, rf, .95)
        perf_rows.append([label, m['total'] * 100, m['cagr'] * 100, m['vol'] * 100, m['sharpe'], m['sortino'], m['drawdown'] * 100, m['var'] * 100, m['cvar'] * 100])
        series.append({'label': f'Capital {label} (prueba)', 'points': [[i, float(v)] for i, v in enumerate(m['equity'])][-1500:]})
        outputs[label.lower().replace(' ', '_').replace('í', 'i').replace('á', 'a')] = path * 100
        markers.append({'name': label, 'ret': s['ret'] * 100, 'vol': s['vol'] * 100, 'down': s['down'] * 100, 'sharpe': s['sharpe'], 'sortino': s['sortino'],
                        'weights': [float(x) * 100 for x in w]})
    asset_rows, assets = [], []
    for i, c in enumerate(columns):
        s = stats(np.eye(n)[i])
        asset_rows.append([c, s['ret'] * 100, s['vol'] * 100, s['down'] * 100, s['sharpe'], s['sortino']])
        assets.append({'name': c, 'ret': s['ret'] * 100, 'vol': s['vol'] * 100, 'down': s['down'] * 100})
    frontier_rows = [[p['vol'] * 100, p['ret'] * 100, p['sharpe'], p['sortino'], *[x * 100 for x in w]] for w, p in efficient]
    clean = lambda v: float(v) if np.isfinite(v) else None
    point = lambda w, p: {'vol': p['vol'] * 100, 'ret': p['ret'] * 100, 'down': p['down'] * 100, 'sharpe': clean(p['sharpe']), 'sortino': clean(p['sortino']),
                          'weights': [float(x) * 100 for x in w]}

    tangency, sortino_best, gmv_stats = (stats(weights[k]) for k in ('Máximo Sharpe', 'Máximo Sortino', 'Mínima varianza'))
    result = report(f'Markowitz con {n} activos: medias y covarianza ({covariance}) estimadas con el {fraction:.0%} inicial ({len(train)} períodos) '
                    f'y cada portafolio evaluado sin reajustar en los {len(test)} siguientes. Solo posiciones largas, tope {cap:.0%} por activo, '
                    f'tasa libre de riesgo {rf:.2%} anual. Valores anualizados con {annual} períodos por año. Uso educativo, no asesoría financiera.',
                    activos=n, periodos_estimacion=len(train), periodos_prueba=len(test))
    result['metrics'] += [{'label': 'Volatilidad mínima (%)', 'value': gmv_stats['vol'] * 100},
                          {'label': 'Rendimiento con máximo Sharpe (%)', 'value': tangency['ret'] * 100},
                          {'label': 'Sharpe máximo', 'value': clean(tangency['sharpe'])},
                          {'label': 'Sortino máximo', 'value': clean(sortino_best['sortino'])}]
    result['tables'] = [
        table('Pesos de cada portafolio (%)', ['Portafolio', *columns, 'Activos efectivos', 'Peso máximo (%)'], weight_rows),
        table('Rendimiento, volatilidad y riesgo esperados (estimación)', ['Portafolio', 'Rendimiento anual (%)', 'Volatilidad anual (%)', 'Varianza anual',
              'Desviación a la baja (%)', 'Sharpe', 'Sortino', f'VaR {level} (%)', f'CVaR {level} (%)', 'Caída máxima (%)'], expected_rows),
        table('Desempeño fuera de muestra (prueba)', ['Portafolio', 'Rendimiento total (%)', 'Rendimiento anual compuesto (%)', 'Volatilidad anual (%)', 'Sharpe', 'Sortino',
              'Caída máxima (%)', f'VaR {level} (%)', f'CVaR {level} (%)'], perf_rows),
        table('Contribución de cada activo al riesgo (% de la varianza)', ['Portafolio', *columns], risk_rows),
        table('Activos individuales (estimación)', ['Activo', 'Rendimiento anual (%)', 'Volatilidad anual (%)', 'Desviación a la baja (%)', 'Sharpe', 'Sortino'], asset_rows),
        table('Frontera eficiente (estimación)', ['Volatilidad (%)', 'Rendimiento esperado (%)', 'Sharpe', 'Sortino', *[f'{c} (%)' for c in columns]], frontier_rows)]
    result['series'] = series
    result['portfolio_plot'] = {
        'columns': columns, 'risk_free': rf * 100, 'assets': assets, 'portfolios': [{**m, 'sharpe': clean(m['sharpe']), 'sortino': clean(m['sortino'])} for m in markers],
        'frontier': [point(w, p) for w, p in efficient], 'lower': [point(w, p) for w, p in lower][::-1],
        'cloud': [[s['vol'] * 100, s['ret'] * 100, s['down'] * 100, clean(s['sharpe']), clean(s['sortino'])] for s in cloud_stats]}
    result['limitations'] = ['Las medias estimadas son muy ruidosas: el máximo Sharpe y el máximo Sortino suelen decepcionar fuera de muestra.',
                             'Volatilidad y Sharpe esperados usan la covarianza elegida; Sortino, VaR, CVaR y caída máxima de estimación usan los rendimientos históricos del bloque inicial.',
                             'Sin costos de transacción ni rebalanceo; uso educativo, no asesoría financiera.']
    data = outputs.reset_index(drop=True)
    if 'periodo' in frame.columns:
        data.insert(0, 'periodo', frame.loc[test.index, 'periodo'].to_numpy())
    return result, {'result': result, 'data': data}


# ---------------------------------------------------------------- aprendizaje automático clásico

ALGORITHMS = ['media', 'ridge', 'elasticnet', 'bosque', 'boosting', 'svr', 'knn']
LABELS = {'media': 'Media (referencia)', 'ridge': 'Ridge', 'elasticnet': 'ElasticNet', 'bosque': 'Bosque aleatorio', 'boosting': 'Boosting por histogramas', 'svr': 'SVR', 'knn': 'KNN'}


class ScaledModel:
    """Escala X e y con el bloque de ajuste; predict acepta un DataFrame con las columnas originales."""

    def __init__(self, estimator, features, x_mean, x_scale, y_mean, y_scale):
        self.estimator, self.features = estimator, features
        self.x_mean, self.x_scale, self.y_mean, self.y_scale = x_mean, x_scale, y_mean, y_scale

    def predict(self, frame):
        x = (frame[self.features].to_numpy(dtype=float) - self.x_mean) / self.x_scale
        return self.estimator.predict(x) * self.y_scale + self.y_mean


def ml_compare(frame, params):
    features = names(frame, params.get('features', 'x'), 'los regresores')
    target = str(params.get('y', 'y'))
    if target not in frame.columns or target in features:
        fail('Elige una respuesta existente y distinta de los regresores.')
    algorithm = choice(params, 'algorithm', ['comparar', *ALGORITHMS], 'comparar')
    fraction = number(params, 'validation', .2, .1, .5)
    trees = number(params, 'estimators', 200, 10, 1000, True)
    depth = number(params, 'max_depth', 6, 1, 32, True)
    alpha = number(params, 'alpha', 1, 1e-6, 1e6)
    neighbors = number(params, 'neighbors', 5, 1, 100, True)
    seed = number(params, 'seed', 42, 0, 2**32 - 1, True)
    data = frame[features + [target]].apply(pd.to_numeric, errors='coerce').dropna()
    if len(data) < 30:
        fail('Se necesitan al menos 30 filas completas.', 'INSUFFICIENT_SAMPLE')
    cut = int(len(data) * (1 - fraction))
    x, y = data[features].to_numpy(dtype=float), data[target].to_numpy(dtype=float)
    x_mean, x_scale = x[:cut].mean(0), np.where(x[:cut].std(0) > 0, x[:cut].std(0), 1)
    y_mean, y_scale = float(y[:cut].mean()), float(y[:cut].std() or 1)
    xs, ys = (x - x_mean) / x_scale, (y - y_mean) / y_scale
    from sklearn.dummy import DummyRegressor
    from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import ElasticNet, Ridge
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.svm import SVR
    factories = {'media': lambda: DummyRegressor(strategy='mean'), 'ridge': lambda: Ridge(alpha=alpha),
                 'elasticnet': lambda: ElasticNet(alpha=alpha / 100, l1_ratio=.5, max_iter=10000, random_state=seed),
                 'bosque': lambda: RandomForestRegressor(n_estimators=trees, max_depth=depth, min_samples_leaf=3, random_state=seed, n_jobs=1),
                 'boosting': lambda: HistGradientBoostingRegressor(max_iter=trees, max_depth=depth, early_stopping=False, random_state=seed),
                 'svr': lambda: SVR(C=alpha, epsilon=.1), 'knn': lambda: KNeighborsRegressor(n_neighbors=min(neighbors, cut), weights='distance')}
    candidates = ALGORITHMS if algorithm == 'comparar' else [algorithm]
    if 'svr' in candidates and cut > 5000:
        candidates = [c for c in candidates if c != 'svr']
    rows, best = [], None
    for name in candidates:
        model = factories[name]().fit(xs[:cut], ys[:cut])
        pred_fit = model.predict(xs[:cut]) * y_scale + y_mean
        pred_val = model.predict(xs[cut:]) * y_scale + y_mean
        rmse_fit = float(np.sqrt(np.mean((y[:cut] - pred_fit) ** 2)))
        rmse_val = float(np.sqrt(np.mean((y[cut:] - pred_val) ** 2)))
        r2_val = float(1 - np.mean((y[cut:] - pred_val) ** 2) / np.var(y[cut:])) if np.var(y[cut:]) > 0 else None
        rows.append([LABELS[name], rmse_fit, rmse_val, r2_val])
        if best is None or rmse_val < best[1]:
            best = (name, rmse_val, model)
    name, _, model = best
    # Reajuste final con todas las filas para el modelo de salida (la selección ya se hizo con la validación).
    final = factories[name]().fit(xs, ys)
    from .tools import Fitted
    fitted = Fitted('ml_compare', ScaledModel(final, features, x_mean, x_scale, y_mean, y_scale), data, features, target, f'ML · {LABELS[name]}')
    result = report(f'Comparación con validación temporal: las primeras {cut} filas ajustan y las {len(data) - cut} últimas validan. '
                    f'Gana {LABELS[name]} por menor RMSE de validación; el modelo de salida se reajusta con todas las filas. Evalúalo con datos de prueba separados.',
                    elegido=LABELS[name], n_ajuste=cut, n_validacion=len(data) - cut)
    result['tables'] = [table('Modelos comparados', ['Modelo', 'RMSE ajuste', 'RMSE validación', 'R² validación'], rows)]
    result['limitations'] = ['Si el RMSE de ajuste es mucho menor que el de validación, el modelo sobreajusta (típico del bosque o KNN con pocos datos).',
                             'La validación es un solo bloque final; usa validación cruzada para una estimación más estable.']
    return result, {'result': result, 'model': fitted}


HANDLERS = {'data_quality': data_quality, 'resample': resample, 'select_columns': select_columns, 'quant_features': quant_features,
            'risk_metrics': risk_metrics, 'portfolio': portfolio, 'ml_compare': ml_compare}


def run_quant_tool(kind, inputs, params):
    return HANDLERS[kind](inputs['data'], params)
