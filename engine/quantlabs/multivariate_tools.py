"""Herramientas para el análisis multivariado de indicadores (0.14.0).

Cubren el recorrido a–p de indicadores de EE. UU.: varias series en un gráfico,
boxplots de varias variables, describe()/transpose, pruebas de dos variables,
detección de correlación severa con valores propios, regresión lineal con
scikit-learn, validación cruzada, búsqueda de hiperparámetros y análisis de
residuos para cualquier modelo con respuesta. Ninguna acepta expresiones.
"""
import numpy as np
import pandas as pd
from scipy import stats

from .core import EngineError, number
from .tools import Fitted, columns, predict, report, sample, series, table

MULTIVARIATE_TOOLS = {'series_plot', 'boxplots', 'describe_table', 'two_sample_test', 'eigen_correlation',
                      'sklearn_linear', 'cross_validation', 'hyperparameter_search', 'residual_analysis'}
SKLEARN_KINDS = {'sklearn_linear', 'sklearn_search'}
STATSMODELS_LINEAR = {'ols', 'multiple_ols', 'covariance', 'wls', 'robust', 'stepwise'}


def by_time(frame):
    """Ordena por periodo (si existe) para que la validación temporal respete el tiempo."""
    return frame.sort_values('periodo', kind='stable') if 'periodo' in frame.columns else frame


def choice(params, key, options):
    value = params.get(key, options[0])
    if value not in options:
        raise EngineError('INVALID_PARAMETERS', f'{key} debe ser una de: {", ".join(map(str, options))}.')
    return value


def default_columns(frame, params, key='columns', limit=8):
    requested = str(params.get(key, '') or '').strip()
    if requested:
        return columns(frame, requested)
    numeric = [c for c in frame.columns if pd.api.types.is_numeric_dtype(frame[c]) and c not in ('periodo', 'entidad')]
    if not numeric:
        raise EngineError('INVALID_PARAMETERS', 'La tabla no tiene variables numéricas.')
    return numeric[:limit]


# ----------------------------------------------------------------- b. varias series

def series_plot(frame, params):
    names = default_columns(frame, params)
    time = str(params.get('time', 'periodo') or 'periodo')
    mode = choice(params, 'mode', ['paneles', 'indice', 'original'])
    if time not in frame.columns:
        raise EngineError('INVALID_PARAMETERS', f'No existe la columna de tiempo «{time}».')
    data = frame[[time, *names]].dropna(subset=[time]).sort_values(time)
    if 'pais' in frame.columns and frame['pais'].nunique() > 1:
        raise EngineError('INVALID_PARAMETERS', 'La tabla tiene varios países; filtra uno antes de graficar las series en el tiempo.')
    lines = []
    for name in names:
        values = pd.to_numeric(data[name], errors='coerce')
        if mode == 'indice':
            base = values.dropna()
            if base.empty or base.iloc[0] == 0:
                raise EngineError('INVALID_PARAMETERS', f'{name} no tiene un primer valor distinto de cero para el índice base 100.')
            values = values / base.iloc[0] * 100
        lines.append({'name': name, 'points': [[float(t), None if pd.isna(v) else float(v)] for t, v in zip(data[time], values)],
                      'n': int(values.notna().sum())})
    note = {'paneles': 'Un panel por variable con su propia escala: permite ver la forma de cada serie aunque las unidades difieran.',
            'indice': 'Cada serie como índice (primer año observado = 100): compara crecimientos relativos, no niveles.',
            'original': 'Todas las series en el mismo eje: solo es legible si comparten unidades y magnitud.'}[mode]
    result = report(note + ' Los huecos son años sin dato; no se interpolan.', variables=len(names), periodos=len(data))
    result['series_plot'] = {'time': time, 'mode': mode, 'lines': lines}
    result['tables'] = [table('Observaciones por serie', ['Variable', 'n', 'Primer año', 'Último año'],
                              [[line['name'], line['n'], *(lambda pts: [pts[0][0], pts[-1][0]] if pts else [None, None])(
                                  [p for p in line['points'] if p[1] is not None])] for line in lines])]
    return result, {'result': result, 'plot': result}


# ----------------------------------------------------------------- c. boxplots

def boxplots(frame, params):
    names = default_columns(frame, params)
    scale = choice(params, 'scale', ['zscore', 'original'])
    boxes = []
    for name in names:
        values = pd.to_numeric(frame[name], errors='coerce').dropna().to_numpy(dtype=float)
        if len(values) < 2:
            raise EngineError('INSUFFICIENT_SAMPLE', f'{name} tiene menos de dos observaciones.')
        raw_mean, raw_sd = float(values.mean()), float(values.std(ddof=1))
        if scale == 'zscore':
            values = (values - raw_mean) / raw_sd if raw_sd > 0 else values - raw_mean
        q1, median, q3 = np.quantile(values, [.25, .5, .75])
        iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        inside = values[(values >= low) & (values <= high)]
        outliers = np.sort(values[(values < low) | (values > high)])
        boxes.append({'column': name, 'n': len(values), 'q1': float(q1), 'median': float(median), 'q3': float(q3),
                      'whisker_low': float(inside.min()), 'whisker_high': float(inside.max()), 'mean': float(values.mean()),
                      'outliers': outliers.tolist()[:200], 'outlier_count': int(len(outliers)), 'raw_mean': raw_mean, 'raw_sd': raw_sd})
    result = report(('Valores estandarizados (z = (x − media) / DE) para comparar la forma de variables con unidades distintas. '
                     if scale == 'zscore' else 'Valores en su escala original. ') +
                    'Caja = Q1–Q3 (cuartiles lineales), línea = mediana, bigotes = datos observados dentro de 1.5·RIC; '
                    'los puntos fuera son atípicos según Tukey, no errores.', variables=len(names))
    result['boxplots'] = {'scale': scale, 'boxes': boxes}
    result['tables'] = [table('Resumen de cajas' + (' (z)' if scale == 'zscore' else ''),
                              ['Variable', 'n', 'Q1', 'Mediana', 'Q3', 'Atípicos', 'Media original', 'DE original'],
                              [[b['column'], b['n'], b['q1'], b['median'], b['q3'], b['outlier_count'], b['raw_mean'], b['raw_sd']] for b in boxes])]
    return result, {'result': result, 'plot': result}


# ----------------------------------------------------------------- g. describe + transpose

def describe_table(frame, params):
    names = default_columns(frame, params, limit=30)
    orientation = choice(params, 'orientation', ['transpuesta', 'pandas'])
    stats_order = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
    described = frame[names].apply(pd.to_numeric, errors='coerce').describe().loc[stats_order]
    if orientation == 'transpuesta':
        body = described.transpose()
        rows = [[name, *body.loc[name].tolist()] for name in body.index]
        result_table = table('describe().transpose()', ['Variable', *stats_order], rows)
    else:
        rows = [[stat, *described.loc[stat].tolist()] for stat in stats_order]
        result_table = table('describe()', ['Estadístico', *names], rows)
    result = report('Equivale a pandas DataFrame.describe()' + ('.transpose(): una fila por variable. ' if orientation == 'transpuesta' else ': una columna por variable. ') +
                    'count excluye faltantes; std es muestral (n−1); los cuartiles usan interpolación lineal.', variables=len(names))
    result['tables'] = [result_table]
    missing = {name: int(frame[name].isna().sum()) for name in names if frame[name].isna().any()}
    if missing:
        result['warnings'].append('Faltantes por variable: ' + ', '.join(f'{k} {v}' for k, v in missing.items()) + '. Cada estadístico usa los datos disponibles de su variable.')
    return result, {'result': result, 'summary': result}


# ----------------------------------------------------------------- h. dos variables

def two_sample_test(frame, params):
    first = columns(frame, str(params.get('first', '')))[0]
    second = columns(frame, str(params.get('second', '')))[0]
    if first == second:
        raise EngineError('INVALID_PARAMETERS', 'Elige dos variables distintas.')
    method = choice(params, 'method', ['welch', 'student', 'paired', 'mannwhitney'])
    alternative = choice(params, 'alternative', ['two-sided', 'less', 'greater'])
    alpha = number(params, 'alpha', 0.05, 0.001, 0.2)
    if method == 'paired':
        data = sample(frame, [first, second], 3)
        a, b = data[first].to_numpy(float), data[second].to_numpy(float)
        test = stats.ttest_rel(a, b, alternative=alternative)
        label = 't pareada (mismo año)'
    else:
        a = frame[first].dropna().to_numpy(float)
        b = frame[second].dropna().to_numpy(float)
        if len(a) < 3 or len(b) < 3:
            raise EngineError('INSUFFICIENT_SAMPLE', 'Cada variable necesita al menos tres observaciones.')
        if method == 'mannwhitney':
            test = stats.mannwhitneyu(a, b, alternative=alternative)
            label = 'Mann-Whitney U (rangos, sin suponer normalidad)'
        else:
            test = stats.ttest_ind(a, b, equal_var=method == 'student', alternative=alternative)
            label = 't de Welch (varianzas distintas)' if method == 'welch' else 't de Student (varianzas iguales)'
    p = float(test.pvalue)
    reject = p < alpha
    sign = {'two-sided': '≠', 'less': '<', 'greater': '>'}[alternative]
    center = 'mediana' if method == 'mannwhitney' else 'media'
    h0 = f'H₀: no hay diferencia significativa entre {first} y {second} ({center}s iguales).'
    ha = f'Hₐ: {center} de {first} {sign} {center} de {second}.'
    decision = (f'Se rechaza H₀ al {alpha:.0%}: hay evidencia de diferencia entre {first} y {second}.' if reject else
                f'No se rechaza H₀ al {alpha:.0%}: no hay evidencia suficiente de diferencia (no demuestra igualdad).')
    result = report(f'{label}. {decision}', estadistico=float(test.statistic), p_valor=p, alpha=alpha,
                    n_primera=len(a), n_segunda=len(b), media_primera=float(np.mean(a)), media_segunda=float(np.mean(b)))
    result['hypotheses'] = {'h0': h0, 'ha': ha, 'decision': decision, 'reject': bool(reject)}
    result['tables'] = [table('Resumen de la prueba', ['Variable', 'n', 'Media', 'Mediana', 'DE'],
                              [[first, len(a), float(np.mean(a)), float(np.median(a)), float(np.std(a, ddof=1))],
                               [second, len(b), float(np.mean(b)), float(np.median(b)), float(np.std(b, ddof=1))]])]
    ratio = max(abs(np.mean(a)), abs(np.mean(b))) / max(1e-300, min(abs(np.mean(a)), abs(np.mean(b))))
    if ratio > 1e3:
        result['warnings'].append('Las variables difieren en varios órdenes de magnitud (posiblemente en unidades distintas): '
                                  'la diferencia es casi segura y dice poco; compara variables en las mismas unidades o tasas.')
    if method != 'paired':
        result['limitations'].append('Supone observaciones independientes; con series anuales hay autocorrelación y el p-valor puede ser optimista.')
    return result, {'result': result}


# ----------------------------------------------------------------- i. correlación severa

def eigen_correlation(frame, params):
    names = default_columns(frame, params)
    if len(names) < 2:
        raise EngineError('INVALID_PARAMETERS', 'Se necesitan al menos dos variables.')
    data = sample(frame, names, len(names) + 2)
    corr = data.corr().to_numpy()
    if not np.isfinite(corr).all():
        raise EngineError('INVALID_PARAMETERS', 'Hay variables constantes: la correlación no está definida.')
    values, vectors = np.linalg.eigh(corr)  # simétrica: valores reales; mismo resultado que np.linalg.eig ordenado
    order = np.argsort(values)[::-1]
    values, vectors = values[order], vectors[:, order]
    condition = np.sqrt(values.max() / np.clip(values, 1e-15, None))
    threshold = number(params, 'condition_threshold', 30, 5, 1000)
    determinant = float(np.linalg.det(corr))
    try:
        vif = np.diag(np.linalg.inv(corr))
    except np.linalg.LinAlgError:
        vif = np.full(len(names), np.inf)
    severe = bool(condition.max() > threshold or values.min() < 0.01)
    moderate = bool(condition.max() > 10)
    verdict = ('Correlación severa (multicolinealidad): ' if severe else 'Colinealidad moderada: ' if moderate else 'Sin colinealidad preocupante: ') + \
        f'índice de condición máximo {condition.max():.1f} (umbral {threshold:g}), menor valor propio {values.min():.4f}, det(R) = {determinant:.4g}.'
    result = report(verdict + ' Valores propios cercanos a 0 indican combinaciones casi lineales de variables; su vector propio muestra cuáles.',
                    indice_condicion_max=float(condition.max()), valor_propio_min=float(values.min()), det_R=determinant, n=len(data))
    result['tables'] = [
        table('Matriz propia (como el listado: valores propios + vectores)', ['Variable', 'Eigen values', *[f'v{i + 1}' for i in range(len(names))]],
              [[name, float(values[i]), *vectors[i].tolist()] for i, name in enumerate(names)]),
        table('Valores propios', ['Componente', 'Valor propio', '% varianza', 'Índice de condición'],
              [[f'v{i + 1}', float(v), float(v / len(names) * 100), float(condition[i])] for i, v in enumerate(values)]),
        table('Vectores propios (columnas = componentes)', ['Variable', *[f'v{i + 1}' for i in range(len(names))]],
              [[name, *vectors[i].tolist()] for i, name in enumerate(names)]),
        table('Factor de inflación de la varianza (VIF)', ['Variable', 'VIF'], [[name, float(v)] for name, v in zip(names, vif)]),
    ]
    result['limitations'] = ['Fila i de la matriz propia: valor propio i y componente de la variable i en cada vector (misma disposición que '
                             'pd.concat([eigenvalues, eigenvectors]) del listado). Para leer un vector, usa la tabla de vectores por columnas.',
                             'Umbrales habituales: índice de condición > 30 severo, > 10 moderado; VIF > 10 alto. Son guías, no pruebas.']
    result['series'] = [series('Valores propios', values)]
    return result, {'result': result}


# ----------------------------------------------------------------- m. scikit-learn

def _features_target(frame, params):
    target = columns(frame, str(params.get('y', '')))[0]
    features = columns(frame, str(params.get('features', '')))
    if target in features:
        raise EngineError('INVALID_PARAMETERS', 'La respuesta no puede ser también regresor.')
    data = sample(frame, [*features, target], len(features) + 3)
    return data, features, target


def _pipeline(estimator, scale):
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    return make_pipeline(StandardScaler(), estimator) if scale == 'standard' else make_pipeline(estimator)


def _coefficients(pipeline, features):
    estimator = pipeline[-1]
    coefs = np.ravel(estimator.coef_)
    scaler = pipeline[0] if len(pipeline) > 1 else None
    intercept = float(estimator.intercept_)
    if scaler is not None:  # devolver también los coeficientes en unidades originales
        original = coefs / scaler.scale_
        intercept_original = intercept - float(np.sum(original * scaler.mean_))
        return [[name, float(c), float(o)] for name, c, o in zip(features, coefs, original)], intercept, intercept_original
    return [[name, float(c), float(c)] for name, c in zip(features, coefs)], intercept, intercept


def _fit_metrics(pipeline, data, features, target):
    predicted = pipeline.predict(data[features])
    actual = data[target].to_numpy(float)
    rss = float(np.sum((actual - predicted) ** 2))
    tss = float(np.sum((actual - actual.mean()) ** 2))
    return 1 - rss / tss if tss else float('nan'), float(np.sqrt(rss / len(actual))), float(np.mean(np.abs(actual - predicted)))


def sklearn_linear(frame, params):
    from sklearn.linear_model import LinearRegression
    data, features, target = _features_target(frame, params)
    scale = choice(params, 'scale', ['none', 'standard'])
    pipeline = _pipeline(LinearRegression(), scale).fit(data[features], data[target])
    rows, intercept, intercept_original = _coefficients(pipeline, features)
    r2, rmse, mae = _fit_metrics(pipeline, data, features, target)
    result = report('LinearRegression de scikit-learn: mismos coeficientes que MCO de statsmodels, sin errores estándar ni p-valores '
                    '(scikit-learn no hace inferencia). Úsalo para predicción, validación cruzada y comparación con modelos regularizados.',
                    R2_ajuste=r2, RMSE_ajuste=rmse, MAE_ajuste=mae, n_ajuste=len(data))
    result['tables'] = [table('Coeficientes', ['Término', 'Coeficiente' + (' (estandarizado)' if scale == 'standard' else ''), 'Coeficiente (unidades originales)'],
                              [['intercepto', intercept, intercept_original], *rows])]
    model = Fitted('sklearn_linear', pipeline, data, features, target, 'LinearRegression' + (' + StandardScaler' if scale == 'standard' else ''))
    return result, {'result': result, 'model': model}


# ----------------------------------------------------------------- n. validación cruzada

def _splitter(params, n):
    from sklearn.model_selection import KFold, TimeSeriesSplit
    folds = number(params, 'folds', 5, 2, 20, True)
    if folds > n - 1:
        raise EngineError('INSUFFICIENT_SAMPLE', f'Con {n} filas usa como máximo {n - 1} pliegues.')
    method = choice(params, 'cv', ['kfold', 'timeseries'])
    if method == 'timeseries':
        return TimeSeriesSplit(n_splits=folds), method, folds
    seed = number(params, 'seed', 42, 0, 2**32 - 1, True)
    return KFold(n_splits=folds, shuffle=True, random_state=seed), method, folds


def _estimator_for(model):
    from sklearn.base import clone
    from sklearn.linear_model import LinearRegression
    if model.kind in SKLEARN_KINDS:
        return clone(model.fit)
    if model.kind in STATSMODELS_LINEAR and model.target:
        return LinearRegression()  # misma especificación MCO
    raise EngineError('TYPE_MISMATCH', 'La validación cruzada acepta regresiones lineales (statsmodels o scikit-learn) con variable respuesta.')


def cross_validation(model, frame, params):
    from sklearn.model_selection import cross_validate
    frame = by_time(frame)
    data = sample(frame, [*model.features, model.target], len(model.features) + 4)
    splitter, method, folds = _splitter(params, len(data))
    estimator = _estimator_for(model)
    scores = cross_validate(estimator, data[model.features], data[model.target], cv=splitter,
                            scoring=('r2', 'neg_root_mean_squared_error', 'neg_mean_absolute_error'))
    r2, rmse, mae = scores['test_r2'], -scores['test_neg_root_mean_squared_error'], -scores['test_neg_mean_absolute_error']
    result = report(f'Validación cruzada {"KFold con barajado" if method == "kfold" else "temporal (TimeSeriesSplit: entrena con el pasado, evalúa el futuro)"} '
                    f'en {folds} pliegues: el modelo se reajusta en cada pliegue con la misma especificación y se evalúa en datos no usados para ajustar.',
                    R2_medio=float(np.mean(r2)), R2_DE=float(np.std(r2, ddof=1)), RMSE_medio=float(np.mean(rmse)), MAE_medio=float(np.mean(mae)),
                    pliegues=folds, n=len(data))
    result['tables'] = [table('Puntuación por pliegue', ['Pliegue', 'R²', 'RMSE', 'MAE'],
                              [[i + 1, float(a), float(b), float(c)] for i, (a, b, c) in enumerate(zip(r2, rmse, mae))])]
    result['series'] = [series('R² por pliegue', r2)]
    if method == 'kfold' and 'periodo' in frame.columns:
        result['warnings'].append('Datos anuales con KFold barajado: el modelo puede ver años futuros al entrenar. Para pronóstico usa cv = timeseries.')
    return result, {'result': result}


# ----------------------------------------------------------------- o. hiperparámetros

def hyperparameter_search(frame, params):
    from sklearn.linear_model import ElasticNet, Lasso, Ridge
    from sklearn.model_selection import GridSearchCV
    frame = by_time(frame)
    data, features, target = _features_target(frame, params)
    kind = choice(params, 'estimator', ['ridge', 'lasso', 'elasticnet'])
    low = number(params, 'alpha_min', 1e-4, 1e-8, 1e6)
    high = number(params, 'alpha_max', 100, low, 1e8)
    count = number(params, 'n_alphas', 20, 3, 200, True)
    alphas = np.logspace(np.log10(low), np.log10(high), count)
    estimator = {'ridge': Ridge(), 'lasso': Lasso(max_iter=50000), 'elasticnet': ElasticNet(max_iter=50000)}[kind]
    grid = {'model__alpha': alphas}
    if kind == 'elasticnet':
        grid['model__l1_ratio'] = [0.1, 0.5, 0.9]
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    pipeline = Pipeline([('scale', StandardScaler()), ('model', estimator)])
    splitter, method, folds = _splitter(params, len(data))
    search = GridSearchCV(pipeline, grid, cv=splitter, scoring='neg_root_mean_squared_error', refit=True).fit(data[features], data[target])
    best = search.best_estimator_
    rows, intercept, intercept_original = _coefficients(best, features)
    r2, rmse, mae = _fit_metrics(best, data, features, target)
    best_alpha = float(search.best_params_['model__alpha'])
    result = report(f'GridSearchCV de {kind} con escalado estándar: {len(alphas)} valores de α en escala logarítmica'
                    + (' × 3 valores de l1_ratio' if kind == 'elasticnet' else '') + f', {folds} pliegues ({method}); '
                    'se elige el α con menor RMSE de validación y se reajusta con todos los datos.',
                    alpha_optimo=best_alpha, RMSE_validacion=float(-search.best_score_), R2_ajuste=r2, RMSE_ajuste=rmse, n=len(data),
                    **({'l1_ratio': float(search.best_params_['model__l1_ratio'])} if kind == 'elasticnet' else {}))
    curve = pd.DataFrame(search.cv_results_)
    if kind == 'elasticnet':  # curva para el l1_ratio elegido
        curve = curve[curve['param_model__l1_ratio'].astype(float) == search.best_params_['model__l1_ratio']]
    result['tables'] = [table('Coeficientes del mejor modelo', ['Término', 'Coeficiente (estandarizado)', 'Coeficiente (unidades originales)'],
                              [['intercepto', intercept, intercept_original], *rows]),
                        table('Curva de validación', ['α', 'RMSE medio', 'DE'],
                              [[float(a), float(-m), float(s)] for a, m, s in zip(curve['param_model__alpha'], curve['mean_test_score'], curve['std_test_score'])])]
    result['series'] = [series('RMSE de validación por α', -curve['mean_test_score'].to_numpy())]
    if best_alpha in (alphas[0], alphas[-1]):
        result['warnings'].append('El α óptimo está en el borde de la rejilla: amplía alpha_min o alpha_max.')
    model = Fitted('sklearn_search', best, data, features, target, f'{kind} (α = {best_alpha:.4g})')
    return result, {'result': result, 'model': model}


# ----------------------------------------------------------------- l / p. residuos

def residual_analysis(model, frame, params):
    from statsmodels.stats.diagnostic import het_breuschpagan
    from statsmodels.stats.stattools import durbin_watson, jarque_bera
    import statsmodels.api as sm
    if not model.target or model.kind in {'hmm', 'gmm', 'kmeans', 'garch', 'arima', 'logit'}:
        raise EngineError('TYPE_MISMATCH', 'El análisis de residuos acepta regresiones con respuesta continua (statsmodels o scikit-learn).')
    source = frame if frame is not None else model.frame
    source = by_time(source)
    predicted, actual, data = predict(model, source)
    residuals = actual - predicted
    n = len(residuals)
    if n < 8:
        raise EngineError('INSUFFICIENT_SAMPLE', 'Se necesitan al menos 8 observaciones para analizar residuos.')
    alpha = number(params, 'alpha', 0.05, 0.001, 0.2)
    jb_stat, jb_p, skew, kurt = jarque_bera(residuals)
    shapiro_p = float(stats.shapiro(residuals).pvalue) if n <= 5000 else None
    exog = sm.add_constant(data[model.features].to_numpy(float), has_constant='add')
    bp_p = float(het_breuschpagan(residuals, exog)[1])
    dw = float(durbin_watson(residuals))
    ordered = np.sort(residuals)
    theoretical = stats.norm.ppf((np.arange(1, n + 1) - 0.375) / (n + 0.25))
    counts, bounds = np.histogram(residuals, bins=min(20, max(5, int(np.sqrt(n)))))
    sd = float(np.std(residuals, ddof=1))
    findings = [f'normalidad {"rechazada" if jb_p < alpha else "no rechazada"} (Jarque-Bera p = {jb_p:.3g})',
                f'heterocedasticidad {"detectada" if bp_p < alpha else "no detectada"} (Breusch-Pagan p = {bp_p:.3g})',
                f'Durbin-Watson = {dw:.2f} ({"posible autocorrelación positiva" if dw < 1.5 else "posible autocorrelación negativa" if dw > 2.5 else "sin indicio fuerte de autocorrelación"})']
    where = 'datos conectados' if frame is not None else 'muestra de ajuste'
    result = report(f'Residuos = observado − predicho del modelo {model.label or model.kind} en {where}: ' + '; '.join(findings) + '.',
                    media_residuos=float(residuals.mean()), DE_residuos=sd, p_Jarque_Bera=float(jb_p), p_Shapiro=shapiro_p,
                    p_Breusch_Pagan=bp_p, Durbin_Watson=dw, asimetria=float(skew), curtosis=float(kurt), n=n)
    result['normality'] = [{'column': 'residuos', 'histogram': {'column': 'residuos', 'n': n, 'missing': 0,
                            'bins': [{'lower': float(bounds[i]), 'upper': float(bounds[i + 1]), 'count': int(c)} for i, c in enumerate(counts)]},
                            'qq': {'points': [[float(a), float(b)] for a, b in zip(theoretical, ordered)][:400], 'mean': float(residuals.mean()),
                                   'std': sd, 'n': n, 'shown': min(n, 400)}}]
    result['residual_plot'] = {'points': [[float(p), float(r)] for p, r in zip(predicted, residuals)][:2000], 'sd': sd}
    big = np.abs(residuals) > 3 * sd
    result['tables'] = [table('Contrastes sobre los residuos', ['Contraste', 'Estadístico', 'p-valor', 'Lectura'],
                              [['Jarque-Bera (normalidad)', float(jb_stat), float(jb_p), 'H₀: normalidad'],
                               ['Shapiro-Wilk (normalidad)', None, shapiro_p, 'H₀: normalidad'],
                               ['Breusch-Pagan (heterocedasticidad)', None, bp_p, 'H₀: varianza constante'],
                               ['Durbin-Watson (autocorrelación)', dw, None, '≈ 2 sin autocorrelación de orden 1']])]
    if big.any():
        result['warnings'].append(f'{int(big.sum())} residuos superan 3 desviaciones estándar: revisa esas observaciones.')
    if model.kind in SKLEARN_KINDS:
        result['limitations'].append('scikit-learn no reporta errores estándar: los contrastes se calculan aquí sobre sus residuos.')
    return result, {'result': result}


def run_multivariate_tool(kind, inputs, params):
    if kind == 'cross_validation':
        return cross_validation(inputs['model'], inputs['data'], params)
    if kind == 'residual_analysis':
        return residual_analysis(inputs['model'], None, params)
    handler = {'series_plot': series_plot, 'boxplots': boxplots, 'describe_table': describe_table, 'two_sample_test': two_sample_test,
               'eigen_correlation': eigen_correlation, 'sklearn_linear': sklearn_linear, 'hyperparameter_search': hyperparameter_search}[kind]
    return handler(inputs['data'], params)
