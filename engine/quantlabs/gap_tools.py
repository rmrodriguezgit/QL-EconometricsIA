"""Herramientas incorporadas a partir de las fichas del segundo cerebro (0.10.0).

Cubren pendientes documentados en ``examples/tool-gaps.json``: tamaño de muestra (C07),
contrastes múltiples (C08), intervalos de predicción (C09), Chow y variables
dicotómicas (C12), descomposición estacional (C14), SARIMA y VAR (C15), Johansen
(C16), WLS/FGLS (C21), regularización (C22) y selección de k (C25).
En 0.11.0 se añaden panel con efectos fijos/aleatorios (C02), EGARCH/GJR (C17),
selección stepwise (C11), efectos marginales (C12) y bootstrap (C09).
En 0.13.0, pairplot (matriz de dispersión) para explorar varias variables a la vez (C03/C10).
Cada cálculo consume los artefactos conectados; ninguna acepta expresiones.
"""
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

from .core import EngineError, number
from .tools import Fitted, columns, regression_report, report, sample, series, table, time_order, ensure_contiguous

GAP_TOOLS = {'sample_size', 'multiple_testing', 'prediction_interval', 'chow', 'dummies', 'seasonal_decompose',
             'sarima', 'var', 'johansen', 'wls', 'regularized', 'cluster_selection',
             'panel', 'egarch', 'stepwise', 'marginal_effects', 'bootstrap', 'pairplot'}


def choice(params, key, options):
    value = params.get(key, options[0])
    if value not in options:
        raise EngineError('INVALID_PARAMETERS', f'{key} debe ser una de: {", ".join(options)}.')
    return value


def confidence(params, key='confidence'):
    return number(params, key, 0.95, 0.5, 0.999)


def single(frame, params, key, default):
    return columns(frame, str(params.get(key, default)))[0]


# ------------------------------------------------------------ inferencia y muestreo

def sample_size(params):
    target = choice(params, 'target', ['media', 'proporcion'])
    level = confidence(params)
    margin = number(params, 'margin', 0.05, 1e-9, 1e9)
    population = number(params, 'population_size', 0, 0, 1e12, True)
    z = stats.norm.ppf(1 - (1 - level) / 2)
    if target == 'media':
        sigma = number(params, 'sd', 1, 1e-12, 1e12)
        n0 = (z * sigma / margin) ** 2
        formula = 'n₀ = (z·σ / E)²'
    else:
        p = number(params, 'proportion', 0.5, 0.0001, 0.9999)
        if margin >= 1:
            raise EngineError('INVALID_PARAMETERS', 'Para proporciones el margen debe ser menor que 1.')
        n0 = z ** 2 * p * (1 - p) / margin ** 2
        formula = 'n₀ = z²·p(1−p) / E²'
    n = n0 / (1 + (n0 - 1) / population) if population else n0
    result = report('Tamaño mínimo para estimar con el margen de error pedido. La corrección por población finita (CPF) '
                    'solo aplica a muestreo aleatorio simple sin reemplazo.',
                    n_requerida=int(np.ceil(n)), n_sin_correccion=int(np.ceil(n0)), z=z, margen=margin, confianza=level)
    result['tables'] = [table('Fórmula', ['Paso', 'Expresión'], [['Inicial', formula],
                                                                  ['CPF', 'n = n₀ / (1 + (n₀ − 1)/N)' if population else 'No aplica (N infinita)']])]
    result['limitations'] = ['Supone muestreo aleatorio simple; diseños estratificados o por conglomerados requieren efecto de diseño.']
    return result, {'result': result}


def multiple_testing(frame, params):
    from statsmodels.stats.multitest import multipletests
    names = columns(frame, params.get('columns', ''))
    mu = number(params, 'mu', 0, -1e12, 1e12)
    alpha = number(params, 'alpha', 0.05, 1e-6, 0.5)
    method = choice(params, 'method', ['fdr_bh', 'holm', 'bonferroni'])
    rows, pvalues = [], []
    for name in names:
        values = frame[name].dropna()
        if len(values) < 3:
            raise EngineError('INSUFFICIENT_SAMPLE', f'{name} necesita al menos tres observaciones.')
        test = stats.ttest_1samp(values, mu)
        rows.append([name, len(values), values.mean(), test.statistic, test.pvalue])
        pvalues.append(test.pvalue)
    reject, adjusted, _, _ = multipletests(pvalues, alpha=alpha, method=method)
    for row, value, decision in zip(rows, adjusted, reject):
        row.extend([value, 'Rechaza H₀' if decision else 'No rechaza'])
    naive = int(sum(p < alpha for p in pvalues))
    result = report(f'Contraste t de H₀: media = {mu} para {len(names)} variables con corrección {method}. '
                    'Controla la tasa de falsos descubrimientos (BH) o la tasa de error por familia (Holm, Bonferroni).',
                    contrastes=len(names), rechazos_sin_corregir=naive, rechazos_corregidos=int(reject.sum()), alpha=alpha)
    result['tables'] = [table('Contrastes', ['Variable', 'n', 'Media', 't', 'p-valor', 'p ajustado', 'Decisión'], rows)]
    return result, {'result': result}


def prediction_interval(frame, params):
    x, y = single(frame, params, 'x', 'ingreso'), single(frame, params, 'y', 'consumo')
    if x == y:
        raise EngineError('INVALID_PARAMETERS', 'Elige variables distintas.')
    level = confidence(params)
    data = sample(frame, [x, y], 5)
    fit = sm.OLS(data[y], sm.add_constant(data[[x]], has_constant='add')).fit()
    grid = pd.DataFrame({x: np.quantile(data[x], [0, .25, .5, .75, 1])})
    frame_pred = fit.get_prediction(sm.add_constant(grid, has_constant='add')).summary_frame(alpha=1 - level)
    rows = [[grid[x].iloc[i], frame_pred['mean'].iloc[i], frame_pred['mean_ci_lower'].iloc[i], frame_pred['mean_ci_upper'].iloc[i],
             frame_pred['obs_ci_lower'].iloc[i], frame_pred['obs_ci_upper'].iloc[i]] for i in range(len(grid))]
    full = fit.get_prediction(sm.add_constant(data[[x]], has_constant='add')).summary_frame(alpha=1 - level)
    output = frame.copy()
    for column, source in [('prediccion', 'mean'), ('pi_inferior', 'obs_ci_lower'), ('pi_superior', 'obs_ci_upper')]:
        output[column] = np.nan
        output.loc[data.index, column] = full[source].to_numpy()
    coverage = float(((data[y] >= full['obs_ci_lower']) & (data[y] <= full['obs_ci_upper'])).mean())
    result = report(f'El intervalo de confianza acota la media condicional; el de predicción, una observación nueva (incluye σ²). '
                    f'Nivel {level:.0%}.', n=len(data), cobertura_en_muestra=coverage, sigma=np.sqrt(fit.scale))
    result['tables'] = [table('Intervalos por valor de x', [x, 'ŷ', 'IC inferior', 'IC superior', 'IP inferior', 'IP superior'], rows)]
    return result, {'result': result, 'data': output}


def chow(frame, params):
    features = columns(frame, params.get('features', 'x'))
    y = single(frame, params, 'y', 'y')
    if y in features:
        raise EngineError('INVALID_PARAMETERS', 'La respuesta no puede ser regresor.')
    fraction = number(params, 'break_fraction', 0.5, 0.1, 0.9)
    data = sample(frame, [*features, y], 2 * (len(features) + 1) + 4)
    if 'periodo' in frame:
        data = data.loc[frame.loc[data.index, 'periodo'].sort_values().index]
    cut = int(round(len(data) * fraction))
    k = len(features) + 1
    if cut < k + 2 or len(data) - cut < k + 2:
        raise EngineError('INSUFFICIENT_SAMPLE', 'Cada submuestra necesita más observaciones que parámetros.')

    def ssr(part):
        return sm.OLS(part[y], sm.add_constant(part[features], has_constant='add')).fit().ssr
    pooled, first, second = ssr(data), ssr(data.iloc[:cut]), ssr(data.iloc[cut:])
    dof = len(data) - 2 * k
    statistic = ((pooled - first - second) / k) / ((first + second) / dof)
    pvalue = stats.f.sf(statistic, k, dof)
    result = report(f'Contraste de Chow con quiebre conocido en la observación {cut} ({fraction:.0%} de la muestra'
                    f'{", ordenada por periodo" if "periodo" in frame else ""}). H₀: mismos coeficientes en ambos tramos.',
                    F=statistic, p_valor=pvalue, gl_num=k, gl_den=dof, n=len(data))
    result['limitations'] = ['Supone varianzas iguales entre tramos y un quiebre fijado de antemano; buscar el quiebre en los datos invalida el p-valor.']
    return result, {'result': result}


def dummies(frame, params):
    column = single(frame, params, 'column', 'x')
    x = single(frame, params, 'x', 'x')
    threshold = number(params, 'threshold', 0, -1e12, 1e12)
    name = str(params.get('output', 'grupo'))[:40] or 'grupo'
    output = frame.copy()
    dummy = f'd_{name}'
    output[dummy] = np.where(frame[column].isna(), np.nan, (frame[column] > threshold).astype(float))
    output[f'{x}_x_{dummy}'] = output[x] * output[dummy]
    share = float(np.nanmean(output[dummy]))
    result = report(f'{dummy} = 1 si {column} > {threshold}. La interacción {x}·{dummy} permite que la pendiente de {x} cambie entre grupos.',
                    proporcion_grupo_1=share, n=int(output[dummy].notna().sum()))
    if share in (0.0, 1.0):
        result['warnings'] = ['El umbral deja un solo grupo: la dicotómica es constante y causará colinealidad.']
    return result, {'result': result, 'data': output}


# ------------------------------------------------------------------ series de tiempo

def seasonal_decompose(frame, params):
    from statsmodels.tsa.seasonal import seasonal_decompose as decompose
    column = single(frame, params, 'column', 'ventas')
    period = number(params, 'period', 12, 2, 365, True)
    model = choice(params, 'model', ['additive', 'multiplicative'])
    data = sample(time_order(frame), [column], 2 * period + 1)
    ensure_contiguous(data)
    if model == 'multiplicative' and (data[column] <= 0).any():
        raise EngineError('INVALID_PARAMETERS', 'El modelo multiplicativo requiere valores positivos.')
    parts = decompose(data[column], model=model, period=period)
    output = frame.copy()
    for name, values in [('tendencia', parts.trend), ('estacional', parts.seasonal), ('irregular', parts.resid)]:
        output[f'{column}_{name}'] = np.nan
        output.loc[data.index, f'{column}_{name}'] = values.to_numpy()
    resid, detrended = parts.resid.dropna(), (data[column] - parts.trend).dropna()
    strength = max(0.0, 1 - resid.var() / detrended.var()) if model == 'additive' and detrended.var() > 0 else None
    result = report(f'Descomposición {model} por medias móviles con período {period}.', n=len(data),
                    fuerza_estacional=strength, amplitud_estacional=float(parts.seasonal.max() - parts.seasonal.min()))
    result['series'] = [series('Tendencia', parts.trend.dropna()), series('Componente estacional', parts.seasonal.iloc[:period * 3])]
    result['limitations'] = ['Los extremos de la tendencia se pierden (media móvil centrada). Para pronosticar usa SARIMA.']
    return result, {'result': result, 'data': output}


def sarima(frame, params):
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    column = single(frame, params, 'column', 'ventas')
    order = tuple(number(params, key, default, 0, 3, True) for key, default in [('p', 1), ('d', 0), ('q', 0)])
    seasonal = tuple(number(params, key, default, 0, 2, True) for key, default in [('P', 1), ('D', 0), ('Q', 0)])
    period = number(params, 's', 12, 0, 365, True)
    horizon = number(params, 'horizon', 12, 1, 120, True)
    level = confidence(params)
    data = sample(time_order(frame), [column], max(20, 2 * period + 5))
    ensure_contiguous(data)
    fit = SARIMAX(data[column].to_numpy(), order=order, seasonal_order=(*seasonal, period) if period else (0, 0, 0, 0)).fit(disp=False)
    forecast = fit.get_forecast(horizon)
    interval = np.asarray(forecast.conf_int(alpha=1 - level))
    mean = np.asarray(forecast.predicted_mean)
    result = report(f'SARIMA{order}×{seasonal}{period}. El intervalo de pronóstico se ensancha con el horizonte; '
                    'no incluye incertidumbre de especificación.', n=len(data), AIC=fit.aic, BIC=fit.bic, horizonte=horizon)
    result['tables'] = [table('Coeficientes', ['Parámetro', 'Estimación', 'p-valor'], [[name, value, p] for name, value, p in zip(fit.param_names, fit.params, fit.pvalues)]),
                        table(f'Pronóstico ({level:.0%})', ['h', 'Media', 'Inferior', 'Superior'], [[i + 1, mean[i], interval[i, 0], interval[i, 1]] for i in range(horizon)])]
    result['series'] = [series('Observado', data[column]), series('Pronóstico', mean)]
    return result, {'result': result}


def var_model(frame, params):
    from statsmodels.tsa.api import VAR
    names = columns(frame, params.get('columns', 'x,y'))
    if len(names) < 2:
        raise EngineError('INVALID_PARAMETERS', 'VAR necesita al menos dos series.')
    lags = number(params, 'lags', 0, 0, 12, True)
    horizon = number(params, 'horizon', 8, 1, 60, True)
    data = sample(time_order(frame), names, 30)
    ensure_contiguous(data)
    model = VAR(data.reset_index(drop=True))
    fit = model.fit(maxlags=min(8, len(data) // 5), ic='aic') if lags == 0 else model.fit(lags)
    if fit.k_ar == 0:
        fit = model.fit(1)
    granger = []
    for caused in names:
        for causing in names:
            if caused != causing:
                test = fit.test_causality(caused, [causing], kind='f')
                granger.append([causing, caused, test.test_statistic, test.pvalue])
    forecast = fit.forecast(data.to_numpy()[-fit.k_ar:], horizon)
    stable = bool(fit.is_stable())
    result = report(f'VAR({fit.k_ar}) {"elegido por AIC" if lags == 0 else "con rezagos fijados"}. '
                    'Causalidad de Granger significa capacidad predictiva incremental, no causalidad estructural.',
                    rezagos=fit.k_ar, n=int(fit.nobs), AIC=fit.aic, estable=int(stable))
    result['tables'] = [table('Causalidad de Granger', ['Causa', 'Efecto', 'F', 'p-valor'], granger),
                        table('Pronóstico', ['h', *names], [[i + 1, *row] for i, row in enumerate(forecast)])]
    result['series'] = [series(f'Pronóstico {name}', forecast[:, i]) for i, name in enumerate(names)]
    if not stable:
        result['warnings'] = ['El VAR estimado no es estable: revisa estacionariedad o diferencia las series.']
    result['limitations'] = ['Requiere series estacionarias; con series I(1) cointegradas usa Johansen/VECM.']
    return result, {'result': result}


def johansen(frame, params):
    from statsmodels.tsa.vector_ar.vecm import coint_johansen
    names = columns(frame, params.get('columns', 'x,y'))
    if not 2 <= len(names) <= 6:
        raise EngineError('INVALID_PARAMETERS', 'Johansen admite de dos a seis series.')
    det_order = number(params, 'det_order', 0, -1, 1, True)
    k_ar_diff = number(params, 'k_ar_diff', 1, 0, 8, True)
    data = sample(time_order(frame), names, 30)
    ensure_contiguous(data)
    test = coint_johansen(data.to_numpy(), det_order, k_ar_diff)
    rows, rank = [], 0
    for r in range(len(names)):
        trace, critical = test.lr1[r], test.cvt[r, 1]
        rows.append([f'r ≤ {r}', trace, critical, test.lr2[r], test.cvm[r, 1], 'Rechaza' if trace > critical else 'No rechaza'])
    for r in range(len(names)):
        if test.lr1[r] > test.cvt[r, 1]:
            rank = r + 1
        else:
            break
    result = report('Contraste de Johansen (traza y máximo autovalor) al 5 %. El rango indica cuántas relaciones de largo plazo existen.',
                    rango_cointegracion=rank, n=len(data), series=len(names))
    result['tables'] = [table('Estadísticos', ['H₀', 'Traza', 'Crítico traza 5%', 'Máx. autovalor', 'Crítico máx. 5%', 'Decisión (traza)'], rows),
                        table('Vectores de cointegración (columnas)', ['Serie', *[f'β{i + 1}' for i in range(len(names))]], [[name, *test.evec[i]] for i, name in enumerate(names)])]
    result['limitations'] = ['Las series deben ser I(1). Los valores críticos son asintóticos; en muestras pequeñas sobre-rechazan.']
    return result, {'result': result}


# ---------------------------------------------------------------------- modelos

def wls(frame, params):
    features = columns(frame, params.get('features', 'x'))
    y = single(frame, params, 'y', 'y')
    method = choice(params, 'method', ['fgls', 'inversa_x2'])
    data = sample(frame, [*features, y], len(features) + 5)
    design = sm.add_constant(data[features], has_constant='add')
    ols = sm.OLS(data[y], design).fit()
    if method == 'inversa_x2':
        scale = data[features[0]].abs()
        if (scale == 0).any():
            raise EngineError('INVALID_PARAMETERS', f'{features[0]} contiene ceros: no se puede usar 1/x².')
        weights = 1 / scale ** 2
        text = f'WLS con pesos 1/{features[0]}²: supone Var(ε|x) ∝ {features[0]}².'
    else:
        auxiliary = sm.OLS(np.log(ols.resid ** 2 + 1e-12), design).fit()
        weights = 1 / np.exp(auxiliary.fittedvalues)
        text = 'FGLS: la varianza se estima con log(ε̂²) sobre los regresores y se usan sus inversos como pesos.'
    fit = sm.WLS(data[y], design, weights=weights).fit()
    model = Fitted('wls', fit, data, features, y, 'WLS ' + method)
    result = regression_report(model, text + ' Compara errores estándar con OLS: los coeficientes siguen siendo asociaciones.')
    result['metrics'] += [{'label': 'R2_ponderado', 'value': fit.rsquared}, {'label': 'AIC', 'value': fit.aic}]
    result['tables'].append(table('OLS de referencia', ['Término', 'Coeficiente', 'Error estándar'],
                                  [[name, ols.params[name], ols.bse[name]] for name in ols.params.index]))
    return result, {'result': result, 'model': model}


def regularized(frame, params):
    from sklearn.linear_model import ElasticNetCV, LassoCV, RidgeCV
    from sklearn.model_selection import KFold, cross_val_score
    from sklearn.preprocessing import StandardScaler
    features = columns(frame, params.get('features', 'x,z'))
    y = single(frame, params, 'y', 'y')
    method = choice(params, 'method', ['lasso', 'ridge', 'elasticnet'])
    folds = number(params, 'folds', 5, 3, 10, True)
    seed = number(params, 'seed', 42, 0, 2**32 - 1, True)
    data = sample(frame, [*features, y], folds * 4)
    X = StandardScaler().fit_transform(data[features])
    target = data[y].to_numpy()
    cv = KFold(folds, shuffle=True, random_state=seed)
    estimator = {'lasso': LassoCV(cv=cv, random_state=seed), 'ridge': RidgeCV(alphas=np.logspace(-3, 3, 50)),
                 'elasticnet': ElasticNetCV(cv=cv, l1_ratio=[.2, .5, .8], random_state=seed)}[method].fit(X, target)
    score = cross_val_score(estimator.__class__(**estimator.get_params()), X, target, cv=cv, scoring='r2')
    ols = sm.OLS(target, sm.add_constant(X)).fit()
    rows = [[name, coef, ols.params[i + 1], 'Excluida' if abs(coef) < 1e-10 else 'Incluida'] for i, (name, coef) in enumerate(zip(features, estimator.coef_))]
    result = report(f'{method} con regresores estandarizados y penalización elegida por validación cruzada de {folds} pliegues. '
                    'Los coeficientes contraídos sacrifican sesgo por varianza; no admiten inferencia clásica.',
                    alpha=float(estimator.alpha_), R2_validacion_cruzada=float(score.mean()), R2_desviacion=float(score.std()),
                    seleccionadas=int(sum(abs(c) > 1e-10 for c in estimator.coef_)), n=len(data))
    result['tables'] = [table('Coeficientes estandarizados', ['Variable', method, 'OLS', 'Estado'], rows)]
    result['limitations'] = ['La validación cruzada de este nodo no es anidada: el R² reportado es optimista respecto a un bloque de prueba.']
    return result, {'result': result}


def cluster_selection(frame, params):
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler
    names = columns(frame, params.get('columns', 'x1,x2'))
    max_k = number(params, 'max_k', 8, 2, 15, True)
    seed = number(params, 'seed', 42, 0, 2**32 - 1, True)
    data = sample(frame, names, max_k * 3)
    X = StandardScaler().fit_transform(data)
    rows = []
    for k in range(2, max_k + 1):
        fit = KMeans(k, n_init=10, random_state=seed).fit(X)
        rows.append([k, fit.inertia_, silhouette_score(X, fit.labels_)])
    best = max(rows, key=lambda row: row[2])
    result = report('Inercia (codo) y silueta media para k = 2…máx. con variables estandarizadas. La mejor silueta es una guía, no una prueba de que existan grupos.',
                    k_sugerido=best[0], silueta_maxima=best[2], n=len(data))
    result['tables'] = [table('Selección de k', ['k', 'Inercia', 'Silueta'], rows)]
    result['series'] = [series('Inercia', [row[1] for row in rows]), series('Silueta', [row[2] for row in rows])]
    return result, {'result': result}


# ------------------------------------------------------------------ 0.11.0

def panel(frame, params):
    entity = str(params.get('entity', 'entidad'))
    if entity not in frame:
        raise EngineError('INVALID_PARAMETERS', f'No existe la columna de unidades «{entity}».')
    features = columns(frame, params.get('features', 'x'))
    y = single(frame, params, 'y', 'y')
    if y in features or entity in features + [y]:
        raise EngineError('INVALID_PARAMETERS', 'La respuesta, los regresores y la unidad deben ser columnas distintas.')
    covariance = choice(params, 'covariance', ['cluster', 'nonrobust'])
    data = frame[[entity, *features, y]].dropna().copy()
    sizes = data.groupby(entity)[y].transform('size')
    data = data[sizes >= 2]
    groups = data[entity].nunique()
    k = len(features)
    if groups < 3 or len(data) < groups + k + 3:
        raise EngineError('INSUFFICIENT_SAMPLE', 'Se necesitan al menos tres unidades con dos o más observaciones cada una.')
    codes = pd.factorize(data[entity])[0]
    names = [*features, y]
    means = data.groupby(entity)[names].transform('mean')
    within = data[names] - means
    if (within[features].std() < 1e-12).any():
        raise EngineError('RANK_DEFICIENT', 'Algún regresor no varía dentro de las unidades: efectos fijos no lo identifican.')
    dof = len(data) - groups - k
    fe = sm.OLS(within[y], within[features]).fit()
    sigma_e2 = fe.ssr / dof
    fe_cov = sigma_e2 * np.linalg.inv(within[features].T.to_numpy() @ within[features].to_numpy())
    fe_se = np.sqrt(np.diag(fe_cov))
    if covariance == 'cluster':
        clustered = sm.OLS(within[y], within[features]).fit(cov_type='cluster', cov_kwds={'groups': codes})
        fe_se_report = np.asarray(clustered.bse) * np.sqrt((len(data) - k) / dof)  # corrige gl por los efectos absorbidos
    else:
        fe_se_report = fe_se
    # Efectos aleatorios (Swamy–Arora): cuasi-diferencia con θᵢ = 1 − √(σ²ₑ / (Tᵢσ²ᵤ + σ²ₑ)).
    group_means = data.groupby(entity)[names].mean()
    t_i = data.groupby(entity)[y].size()
    between = sm.OLS(group_means[y], sm.add_constant(group_means[features], has_constant='add')).fit()
    t_bar = groups / (1 / t_i).sum()
    sigma_u2 = max(0.0, between.ssr / max(1, groups - k - 1) - sigma_e2 / t_bar)
    theta = 1 - np.sqrt(sigma_e2 / (t_i.loc[data[entity]].to_numpy() * sigma_u2 + sigma_e2))
    quasi = data[names] - theta[:, None] * means.to_numpy()
    design = sm.add_constant(quasi[features], has_constant='add')
    design['const'] = 1 - theta
    re = sm.OLS(quasi[y], design).fit(**({'cov_type': 'cluster', 'cov_kwds': {'groups': codes}} if covariance == 'cluster' else {}))
    re_classic = sm.OLS(quasi[y], design).fit()
    diff = fe.params.to_numpy() - re_classic.params[features].to_numpy()
    variance = fe_cov - re_classic.cov_params().loc[features, features].to_numpy()
    definite = bool(np.all(np.linalg.eigvalsh((variance + variance.T) / 2) > 0))
    hausman = float(diff @ np.linalg.pinv(variance) @ diff) if definite else None
    p_hausman = float(stats.chi2.sf(hausman, k)) if definite else None
    pooled = sm.OLS(data[y], sm.add_constant(data[features], has_constant='add')).fit()
    rows = [[name, pooled.params[name], fe.params[name], fe_se_report[i], re.params[name], re.bse[name]] for i, name in enumerate(features)]
    result = report(f'Panel con {groups} unidades y {len(data)} observaciones. Efectos fijos usan solo la variación dentro de cada unidad; '
                    'efectos aleatorios suponen que el efecto individual no se correlaciona con los regresores. '
                    + (f'Hausman {"rechaza" if p_hausman < 0.05 else "no rechaza"} esa hipótesis al 5 %.' if definite else
                     'Hausman no está definido: Var(FE) − Var(RE) no es definida positiva en esta muestra.'),
                    unidades=groups, n=len(data), Hausman=hausman, p_Hausman=p_hausman, sigma_u=np.sqrt(sigma_u2),
                    sigma_e=np.sqrt(sigma_e2), rho=sigma_u2 / (sigma_u2 + sigma_e2) if sigma_u2 + sigma_e2 else None)
    result['tables'] = [table('Coeficientes', ['Variable', 'Agrupado (MCO)', 'Efectos fijos', 'EE fijos', 'Efectos aleatorios', 'EE aleatorios'], rows)]
    result['limitations'] = ['Hausman usa covarianzas clásicas aunque se reporten EE por conglomerado; con heterocedasticidad usa un contraste robusto (pendiente).',
                             'Las unidades con una sola observación se excluyen. Sin efectos temporales en esta versión.']
    return result, {'result': result}


def egarch(frame, params):
    from arch import arch_model
    name = single(frame, params, 'column', 'retorno')
    vol = choice(params, 'vol', ['EGARCH', 'GJR-GARCH'])
    dist = choice(params, 'dist', ['normal', 't'])
    p, o, q = (number(params, key, 1, 0 if key == 'o' else 1, 3, True) for key in ['p', 'o', 'q'])
    data = sample(time_order(frame), [name], 50)
    ensure_contiguous(data)
    fit = arch_model(data[name].to_numpy(), mean='Constant', vol='EGARCH' if vol == 'EGARCH' else 'GARCH', p=p, o=o, q=q,
                     dist=dist, rescale=False).fit(disp='off')
    if fit.convergence_flag:
        raise EngineError('NON_CONVERGENCE', f'{vol} no convergió; prueba otra escala de retornos u órdenes menores.')
    gamma = [value for key, value in fit.params.items() if key.startswith('gamma')]
    result = report(f'{vol}({p},{o},{q}) con distribución {dist}. El término γ capta asimetría: '
                    + ('en EGARCH, γ < 0 indica que los choques negativos elevan más la volatilidad.' if vol == 'EGARCH'
                       else 'en GJR, γ > 0 indica efecto apalancamiento.'),
                    AIC=fit.aic, BIC=fit.bic, n=len(data), gamma=gamma[0] if gamma else None)
    result['tables'] = [table('Parámetros', ['Parámetro', 'Estimación', 'p-valor'], [[key, fit.params[key], fit.pvalues[key]] for key in fit.params.index])]
    result['series'] = [series('Volatilidad condicional', fit.conditional_volatility)]
    result['limitations'] = ['Univariado: la volatilidad multivariada (DCC/BEKK) sigue pendiente.']
    return result, {'result': result, 'model': Fitted('garch', fit, data, [], name, vol)}


def stepwise(frame, params):
    features = columns(frame, params.get('features', 'x,z'))
    y = single(frame, params, 'y', 'y')
    features = [f for f in features if f != y]
    direction = choice(params, 'direction', ['forward', 'backward'])
    criterion = choice(params, 'criterion', ['aic', 'bic'])
    data = sample(frame, [*features, y], len(features) + 5)

    def score(names):
        design = sm.add_constant(data[names], has_constant='add') if names else np.ones((len(data), 1))
        fit = sm.OLS(data[y], design).fit()
        return getattr(fit, criterion), fit
    selected = [] if direction == 'forward' else list(features)
    current, _ = score(selected)
    path = [['inicio', '—', ', '.join(selected) or '(solo constante)', current]]
    while True:
        candidates = [f for f in features if f not in selected] if direction == 'forward' else list(selected)
        if not candidates:
            break
        trials = [(score(selected + [c] if direction == 'forward' else [s for s in selected if s != c])[0], c) for c in candidates]
        best, variable = min(trials)
        if best >= current - 1e-9:
            break
        selected = selected + [variable] if direction == 'forward' else [s for s in selected if s != variable]
        current = best
        path.append(['añade' if direction == 'forward' else 'elimina', variable, ', '.join(selected) or '(solo constante)', best])
    if not selected:
        raise EngineError('INSUFFICIENT_SAMPLE', 'Ningún regresor mejora el criterio frente a la constante.')
    _, fit = score(selected)
    model = Fitted('multiple_ols', fit, data[[*selected, y]], selected, y, 'OLS stepwise')
    result = regression_report(model, f'Selección {direction} por {criterion.upper()}. Los p-valores tras seleccionar son optimistas: '
                                      'la misma muestra eligió las variables. Valida con datos nuevos.')
    result['metrics'] += [{'label': criterion.upper(), 'value': current}, {'label': 'seleccionadas', 'value': len(selected)}, {'label': 'candidatas', 'value': len(features)}]
    result['tables'].append(table('Recorrido', ['Paso', 'Variable', 'Modelo', criterion.upper()], path))
    return result, {'result': result, 'model': model}


def marginal_effects(model, params):
    at = choice(params, 'at', ['overall', 'mean'])
    fit = model.fit
    if model.kind == 'logit':
        margins = fit.get_margeff(at=at)
        frame = margins.summary_frame()
        rows = [[name, frame.iloc[i, 0], frame.iloc[i, 1], frame.iloc[i, 3]] for i, name in enumerate(model.features)]
        text = ('Efecto medio de un cambio unitario en cada regresor sobre la probabilidad (promedio de efectos individuales).' if at == 'overall'
                else 'Efecto sobre la probabilidad evaluado en la media de los regresores.')
    elif model.kind in ('ols', 'multiple_ols', 'covariance', 'robust', 'wls'):
        rows = [[name, fit.params[name], fit.bse[name], fit.pvalues[name]] for name in model.features]
        text = 'En un modelo lineal sin términos no lineales el efecto marginal es el propio coeficiente y no depende de x.'
        powered = [name for name in model.features if '^' in name or '_x_' in name or name.startswith('poly')]
        if powered:
            text += f' Atención: {", ".join(powered)} parecen potencias o interacciones; el efecto total combina varios coeficientes.'
    else:
        raise EngineError('TYPE_MISMATCH', 'Conecta un modelo logit/probit o una regresión lineal.')
    result = report(text, n=len(model.frame), modelo=model.label or model.kind)
    result['tables'] = [table('Efectos marginales', ['Variable', 'dy/dx', 'Error estándar', 'p-valor'], rows)]
    return result, {'result': result}


def bootstrap(frame, params):
    column = single(frame, params, 'column', 'valor')
    statistic = choice(params, 'statistic', ['mean', 'median', 'std', 'iqr'])
    method = choice(params, 'method', ['percentile', 'basic', 'BCa'])
    replications = number(params, 'replications', 2000, 100, 20000, True)
    level = confidence(params)
    seed = number(params, 'seed', 42, 0, 2**32 - 1, True)
    values = frame[column].dropna().to_numpy(dtype=float)
    if len(values) < 10:
        raise EngineError('INSUFFICIENT_SAMPLE', 'El bootstrap necesita al menos 10 observaciones.')
    function = {'mean': np.mean, 'median': np.median, 'std': lambda v, axis=-1: np.std(v, ddof=1, axis=axis),
                'iqr': lambda v, axis=-1: stats.iqr(v, axis=axis)}[statistic]
    res = stats.bootstrap((values,), function, n_resamples=replications, confidence_level=level, method=method,
                          random_state=np.random.default_rng(seed), vectorized=True)
    estimate = float(function(values))
    distribution = np.sort(res.bootstrap_distribution)
    counts, edges = np.histogram(distribution, bins=20)
    result = report(f'Bootstrap no paramétrico ({method}) de la {statistic} de {column} con {replications} remuestras. '
                    'Supone observaciones independientes; con dependencia temporal usa bootstrap por bloques (pendiente).',
                    estimacion=estimate, ic_inferior=float(res.confidence_interval.low), ic_superior=float(res.confidence_interval.high),
                    error_estandar=float(res.standard_error), n=len(values), confianza=level)
    result['tables'] = [table('Distribución bootstrap', ['Desde', 'Hasta', 'Frecuencia'], [[edges[i], edges[i + 1], int(c)] for i, c in enumerate(counts)])]
    result['series'] = [series('Frecuencia por intervalo', counts)]
    return result, {'result': result}



# ------------------------------------------------------------------ 0.13.0

def pairplot(frame, params):
    """Matriz de dispersión (pairplot): pares por debajo de la diagonal, histogramas en ella y r de Pearson por par."""
    requested = str(params.get('columns', '') or '').strip()
    numeric = [c for c in frame.columns if pd.api.types.is_numeric_dtype(frame[c]) and c != 'periodo']
    names = columns(frame, requested) if requested else numeric[:6]
    if len(names) < 2:
        raise EngineError('INVALID_PARAMETERS', 'El pairplot necesita al menos dos variables numéricas.')
    if len(names) > 8:
        raise EngineError('INVALID_PARAMETERS', 'Elige como máximo 8 variables para que la matriz sea legible.')
    group = str(params.get('group', '') or '').strip()
    if group and group not in frame.columns:
        raise EngineError('INVALID_PARAMETERS', f'No existe la columna de grupo «{group}».')
    if group in names:
        raise EngineError('INVALID_PARAMETERS', 'La columna de grupo no puede ser también una variable de la matriz.')
    bins = number(params, 'bins', 15, 3, 60, True)
    limit = number(params, 'max_points', 600, 50, 3000, True)
    seed = number(params, 'seed', 42, 0, 2**32 - 1, True)
    data = frame[names + ([group] if group else [])].copy()
    values = data[names].apply(pd.to_numeric, errors='coerce').replace([np.inf, -np.inf], np.nan)
    usable = values.notna().sum(axis=1) >= 2  # cada par usa sus filas completas
    data, values = data[usable], values[usable]
    if len(data) < 3:
        raise EngineError('INSUFFICIENT_SAMPLE', 'No hay suficientes filas con datos para comparar variables.')
    if group:
        labels = data[group].astype(str).where(data[group].notna(), 'sin dato')
        groups = list(dict.fromkeys(labels.sort_values()))
        if len(groups) > 8:
            raise EngineError('INVALID_PARAMETERS', f'«{group}» tiene {len(groups)} categorías; usa una con 8 o menos.')
    else:
        labels, groups = pd.Series('todos', index=data.index), ['todos']
    shown = values.sample(n=limit, random_state=seed) if len(values) > limit else values
    points = [[None if pd.isna(v) else float(v) for v in row] + [groups.index(labels[idx])] for idx, row in zip(shown.index, shown.to_numpy())]
    diagonal, correlation_rows, pairs = [], [], []
    for name in names:
        column = values[name].dropna()
        edges = np.histogram_bin_edges(column, bins=bins) if len(column) else np.array([0.0, 1.0])
        counts = [np.histogram(values.loc[labels == g, name].dropna(), bins=edges)[0].astype(int).tolist() for g in groups]
        diagonal.append({'column': name, 'edges': edges.tolist(), 'counts': counts, 'n': int(len(column))})
    matrix = []
    for i, a in enumerate(names):
        row = []
        for j, b in enumerate(names):
            both = values[[a] if i == j else [a, b]].dropna()
            defined = len(both) >= 3 and both[a].nunique() > 1 and both[b].nunique() > 1
            r = 1.0 if i == j and defined else (float(both[a].corr(both[b])) if defined else None)
            row.append(r)
            if i < j:
                pairs.append((a, b, r, len(both)))
        matrix.append(row)
        correlation_rows.append([a, *row])
    strongest = max((p for p in pairs if p[2] is not None), key=lambda p: abs(p[2]), default=None)
    note = (f'Matriz de {len(names)} variables con {len(values)} filas' + (f', coloreada por «{group}»' if group else '') + '. '
            'Cada panel usa las filas completas de su par; los histogramas usan todos los datos de la variable. '
            'Asociación no implica causalidad.')
    result = report(note, n=len(values), variables=len(names), puntos_mostrados=len(points),
                    **({'r_maximo': strongest[2]} if strongest else {}))
    if strongest:
        result['teaching_note'] = f'Par más asociado: {strongest[0]} y {strongest[1]} (r = {strongest[2]:.3f}, n = {strongest[3]}).'
    if len(points) < len(values):
        result['warnings'].append(f'Se dibujan {len(points)} de {len(values)} filas (muestra aleatoria con semilla {seed}); '
                                  'histogramas y correlaciones usan todas.')
    if group and len(groups) > 1:
        result['warnings'].append('Las correlaciones y los histogramas combinan todos los grupos. Si las unidades difieren entre grupos '
                                  '(p. ej. indicadores en moneda local, códigos .CN), compara la tabla de correlación por grupo.')
        by_group = []
        for g in groups:
            subset = values[labels == g]
            for a, b, _, _ in pairs:
                both = subset[[a, b]].dropna()
                ok = len(both) >= 3 and both[a].nunique() > 1 and both[b].nunique() > 1
                by_group.append([g, a, b, len(both), float(both[a].corr(both[b])) if ok else None])
    result['pairplot'] = {'columns': names, 'group': group or None, 'groups': groups, 'points': points,
                          'diagonal': diagonal, 'correlation': matrix}
    result['tables'] = [table('Correlación de Pearson por pares', ['Variable', *names], correlation_rows),
                        table('Filas completas por par', ['Variable A', 'Variable B', 'n', 'r'], [[a, b, n, r] for a, b, r, n in pairs])]
    if group and len(groups) > 1:
        result['tables'].append(table(f'Correlación dentro de cada grupo ({group})', ['Grupo', 'Variable A', 'Variable B', 'n', 'r'], by_group))
    return result, {'result': result, 'plot': result}

def run_gap_tool(kind, inputs, params):
    if kind == 'sample_size':
        return sample_size(params)
    if kind == 'marginal_effects':
        return marginal_effects(inputs['model'], params)
    frame = inputs['data']
    handler = {'multiple_testing': multiple_testing, 'prediction_interval': prediction_interval, 'chow': chow, 'dummies': dummies,
               'seasonal_decompose': seasonal_decompose, 'sarima': sarima, 'var': var_model, 'johansen': johansen, 'wls': wls,
               'regularized': regularized, 'cluster_selection': cluster_selection, 'panel': panel, 'egarch': egarch,
               'stepwise': stepwise, 'bootstrap': bootstrap, 'pairplot': pairplot}[kind]
    return handler(frame, params)
