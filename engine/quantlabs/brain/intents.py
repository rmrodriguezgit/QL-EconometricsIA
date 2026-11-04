"""Planificador determinista: reglas en español → plan de herramientas registradas.

Funciona sin modelo de lenguaje y sirve de respaldo cuando Ollama no está
disponible o devuelve un plan inválido. Cada intención apunta a un tipo de nodo;
si ese tipo todavía no existe en el catálogo, se convierte en ficha de herramienta
faltante en lugar de inventar un nodo.
"""
from functools import lru_cache
import json
import re

from ..core import NODE_CATALOG, ROOT
from .knowledge import fold

# (patrón sobre texto sin acentos, tipo de nodo, etapa, ficha si falta)
# Etapas: 1 transformación, 2 exploración, 3 modelo, 4 diagnóstico de modelo.
INTENTS = [
    (r'\blogaritm|\blog\b|elasticidad', 'log', 1, None),
    (r'deflact|precios constantes|termino[s]? real', 'deflate', 1, None),
    (r'per capita|por habitante', 'per_capita', 1, None),
    (r'crecimiento|tasa de variacion', 'growth', 1, None),
    (r'rezago|retardo|\blag\b', 'lag', 1, None),
    (r'primera diferencia|diferenciar|diferencia[s]? de la serie', 'difference', 1, None),
    (r'polinom|cuadratic|no lineal', 'polynomial', 1, None),
    (r'estandariz|normaliz[ae] (las|los) (variables|datos)|z-?score', 'standardize', 1, None),
    (r'imput|valores faltantes|datos faltantes', 'impute_mean', 1, None),
    (r'dummy|dummies|variable[s]? categoric|interaccion', 'dummies', 1,
     {'name': 'Variables dicotómicas e interacciones', 'module': 'C12', 'inputs': {'data': 'Dataset'}, 'outputs': {'data': 'Dataset'}}),
    (r'estacional|descompos', 'seasonal_decompose', 1,
     {'name': 'Descomposición estacional', 'module': 'C14', 'inputs': {'data': 'Dataset'}, 'outputs': {'data': 'Dataset', 'result': 'Result'}}),
    (r'descriptiv|resumen estadistic|estadistica[s]? basica|media y desviacion', 'describe', 2, None),
    (r'dispersion|scatter|nube de puntos', 'scatter', 2, None),
    (r'matriz de covarianza', 'covariance_matrix', 2, None),
    (r'(?<!auto)correlacion(?! serial)', 'correlation', 2, None),
    (r'histograma|distribucion de frecuencias', 'histogram', 2, None),
    (r'caja y bigotes|boxplot|diagrama de caja|atipic', 'boxplot', 2, None),
    (r'serie[s]? de tiempo|serie temporal|evolucion|grafic[ao] temporal', 'time_plot', 2, None),
    (r'intervalo de confianza', 'mean_ci', 2, None),
    (r'normalidad|shapiro|jarque', 'normality', 2, None),
    (r'autocorrelacion|\bacf\b|correlograma', 'acf', 2, None),
    (r'raiz unitaria|estacionari|dickey|\badf\b', 'unit_root', 2, None),
    (r'monte ?carlo', 'monte_carlo', 2, None),
    (r'tamano de (la )?muestra|tamano muestral|poblacion finita', 'sample_size', 2,
     {'name': 'Tamaño de muestra', 'module': 'C07', 'inputs': {}, 'outputs': {'result': 'Result'}}),
    (r'contrastes multiples|comparaciones multiples|falsos descubrimientos|bonferroni|\bfdr\b', 'multiple_testing', 2,
     {'name': 'Contrastes múltiples y FDR', 'module': 'C08', 'inputs': {'data': 'Dataset'}, 'outputs': {'result': 'Result'}}),
    (r'antes y despues|pareada|muestras relacionadas', 'paired_test', 2, None),
    (r'regresion multiple|varias variables explicativas|varios regresores|multivariad[ao] de consumo', 'multiple_ols', 3, None),
    (r'mco|minimos cuadrados ordinarios|regresion|\bols\b|recta', 'ols', 3, None),
    (r'minimos cuadrados ponderados|\bwls\b|\bgls\b|ponderad', 'wls', 3,
     {'name': 'WLS / GLS', 'module': 'C21', 'inputs': {'data': 'Dataset'}, 'outputs': {'model': 'FittedModel', 'result': 'Result'}}),
    (r'\bridge\b|lasso|elastic ?net|regulariz', 'regularized', 3,
     {'name': 'Regresión regularizada', 'module': 'C22', 'inputs': {'data': 'Dataset'}, 'outputs': {'result': 'Result'}}),
    (r'logit|probit|clasific|probabilidad de (que|ser)', 'logit', 3, None),
    (r'sarima|estacional[a-z]* arima', 'sarima', 3,
     {'name': 'SARIMA con intervalos de pronóstico', 'module': 'C15', 'inputs': {'data': 'Dataset'}, 'outputs': {'result': 'Result'}}),
    (r'arima|\barma\b|autorregresiv|pronostic', 'arima', 3, None),
    (r'\bvar\b|vector autorregresiv|causalidad de granger', 'var', 3,
     {'name': 'Vector autorregresivo (VAR)', 'module': 'C15', 'inputs': {'data': 'Dataset'}, 'outputs': {'result': 'Result'}}),
    (r'johansen|vecm', 'johansen', 3,
     {'name': 'Contraste de Johansen', 'module': 'C16', 'inputs': {'data': 'Dataset'}, 'outputs': {'result': 'Result'}}),
    (r'garch|volatilidad', 'garch', 3, None),
    (r'cointegra', 'cointegration', 3, None),
    (r'correccion de error|\becm\b', 'ecm', 3, None),
    (r'cuantil|mediana condicional', 'quantile', 3, None),
    (r'robust[ao]s? a atipic|regresion robusta|huber', 'robust', 3, None),
    (r'instrument|2sls|mc2e|endogen', 'iv2sls', 3, None),
    (r'markov|regimen|regimenes', 'hmm', 3, None),
    (r'mezcla gaussiana|\bgmm\b', 'gmm', 3, None),
    (r'k-?means|cluster|conglomerad|agrupa', 'kmeans', 3, None),
    (r'numero de (grupos|clusters)|codo|elegir k', 'cluster_selection', 3,
     {'name': 'Selección del número de grupos', 'module': 'C25', 'inputs': {'data': 'Dataset'}, 'outputs': {'result': 'Result'}}),
    (r'red(es)? neuronal|\bmlp\b|perceptron', 'mlp', 3, None),
    (r'componentes principales|\bpca\b|\bacp\b', 'pca', 3, None),
    (r'analisis factorial|factores latentes', 'factor_analysis', 3, None),
    (r'ecuaciones estructurales|\bsem\b', 'sem', 3, None),
    (r'heterocedast|diagnostic', 'diagnostics', 4, None),
    (r'errores (estandar )?robustos|\bhac\b|newey', 'covariance', 4, None),
    (r'normalidad de (los )?residuos', 'residual_normality', 4, None),
    (r'intervalo[s]? de prediccion', 'prediction_interval', 3,
     {'name': 'Intervalos de predicción', 'module': 'C09', 'inputs': {'data': 'Dataset'}, 'outputs': {'data': 'Dataset', 'result': 'Result'}}),
    (r'\bchow\b|cambio estructural|quiebre', 'chow', 3,
     {'name': 'Contraste de Chow', 'module': 'C12', 'inputs': {'data': 'Dataset'}, 'outputs': {'result': 'Result'}}),
    # Temas sin herramienta prevista todavía: quedan como fichas pendientes.
    (r'datos de panel|efectos fijos|efectos aleatorios|hausman', 'panel', 3,
     {'name': 'Modelos de datos de panel (efectos fijos/aleatorios)', 'module': 'C02', 'inputs': {'data': 'Dataset'}, 'outputs': {'model': 'FittedModel', 'result': 'Result'}}),
    (r'egarch|volatilidad multivariada|dcc', 'egarch', 3,
     {'name': 'EGARCH y volatilidad multivariada', 'module': 'C17', 'inputs': {'data': 'Dataset'}, 'outputs': {'model': 'FittedModel', 'result': 'Result'}}),
    (r'stepwise|paso a paso hacia', 'stepwise', 3,
     {'name': 'Selección stepwise de regresores', 'module': 'C11', 'inputs': {'data': 'Dataset'}, 'outputs': {'result': 'Result'}}),
    (r'efectos marginales', 'marginal_effects', 4,
     {'name': 'Efectos marginales', 'module': 'C12', 'inputs': {'model': 'FittedModel'}, 'outputs': {'result': 'Result'}}),
    (r'bootstrap|remuestreo', 'bootstrap', 2,
     {'name': 'Bootstrap de estadísticos', 'module': 'C09', 'inputs': {'data': 'Dataset'}, 'outputs': {'result': 'Result'}}),
]

# Escenario sintético que mejor sirve a cada herramienta principal.
SCENARIO_FOR = {
    'ols': 'regression', 'multiple_ols': 'multiple', 'logit': 'logistic', 'arima': 'ar1', 'acf': 'ar1',
    'unit_root': 'ar1', 'difference': 'ar1', 'lag': 'ar1', 'garch': 'garch', 'cointegration': 'cointegrated', 'ecm': 'cointegrated',
    'johansen': 'cointegrated', 'var': 'cointegrated', 'kmeans': 'clusters', 'cluster_selection': 'clusters',
    'pca': 'factors', 'factor_analysis': 'factors', 'sem': 'sem', 'iv2sls': 'endogenous', 'polynomial': 'polynomial',
    'robust': 'outliers', 'quantile': 'hetero', 'diagnostics': 'hetero', 'covariance': 'hetero', 'wls': 'hetero',
    'paired_test': 'pairs', 'hmm': 'regimes', 'gmm': 'regimes', 'deflate': 'prices', 'per_capita': 'prices',
    'log': 'cobb', 'compound': 'inflation', 'monte_carlo': 'inflation', 'signal': 'returns', 'mlp': 'nonlinear',
    'mean_ci': 'normal', 'histogram': 'normal', 'normality': 'normal', 'growth': 'positive', 'time_plot': 'positive',
    'regularized': 'multiple', 'chow': 'regression', 'prediction_interval': 'regression', 'multiple_testing': 'factors',
    'seasonal_decompose': 'seasonal', 'sarima': 'seasonal', 'dummies': 'multiple', 'boxplot': 'outliers',
}

# Matices del enunciado que se trasladan a parámetros del catálogo.
PARAM_HINTS = {
    'sample_size': [(r'proporcion|porcentaje', {'target': 'proporcion'})],
    'multiple_testing': [(r'bonferroni', {'method': 'bonferroni'}), (r'\bholm\b', {'method': 'holm'})],
    'regularized': [(r'\bridge\b', {'method': 'ridge'}), (r'elastic', {'method': 'elasticnet'})],
    'logit': [(r'probit', {'method': 'probit'})],
    'covariance': [(r'\bhac\b|newey|autocorrelacion', {'method': 'HAC'})],
    'wls': [(r'1/x|inversa', {'method': 'inversa_x2'})],
    'split': [(r'aleatori', {'method': 'aleatorio'})],
    'seasonal_decompose': [(r'multiplicativ', {'model': 'multiplicative'})],
    'ols': [(r'clasic|no robust', {'covariance': 'nonrobust'})],
}


def hints(kind, folded):
    params = {}
    for pattern, values in PARAM_HINTS.get(kind, []):
        if re.search(pattern, folded):
            params.update(values)
    return params


INDICATORS = [
    (r'pib per capita|producto interno bruto per capita|ingreso per capita', 'NY.GDP.PCAP.KD'),
    (r'crecimiento del pib|crecimiento economico', 'NY.GDP.MKTP.KD.ZG'),
    (r'\bpib\b|producto interno bruto', 'NY.GDP.MKTP.KD'),
    (r'inflacion', 'FP.CPI.TOTL.ZG'),
    (r'desempleo', 'SL.UEM.TOTL.ZS'),
    (r'poblacion', 'SP.POP.TOTL'),
    (r'exportacion', 'NE.EXP.GNFS.ZS'),
    (r'importacion', 'NE.IMP.GNFS.ZS'),
    (r'tasa de interes|interes real', 'FR.INR.RINR'),
    (r'tasa de prestamo|interes de (los )?prestamos', 'FR.INR.LEND'),
    (r'consumo final', 'NE.CON.TOTL.KD'),
    (r'esperanza de vida', 'SP.DYN.LE00.IN'),
    (r'emisiones|co2', 'EN.GHG.CO2.PC.CE.AR5'),
]


@lru_cache(maxsize=1)
def countries():
    path = ROOT / 'packages/contracts/worldbankCountries.json'
    items = json.loads(path.read_text(encoding='utf-8'))['items'] if path.exists() else []
    names = {fold(item['name']).strip(): item['id'] for item in items if len(item.get('id', '')) == 3}
    names.update({'estados unidos': 'USA', 'eeuu': 'USA', 'ee uu': 'USA', 'usa': 'USA', 'mexico': 'MEX', 'reino unido': 'GBR',
                  'corea del sur': 'KOR', 'rusia': 'RUS'})
    return names


@lru_cache(maxsize=1)
def wooldridge_names():
    path = ROOT / 'packages/contracts/wooldridgeCatalog.json'
    if not path.exists():
        return set()
    # Nombres cortos (p. ej. 'card', 'crime1') solo cuentan si van precedidos de "wooldridge" o "conjunto".
    return {item['id'].lower() for item in json.loads(path.read_text(encoding='utf-8'))['items']}


def detect_source(text):
    """Devuelve (tipo, parámetros, razón) para la fuente de datos."""
    folded = fold(text)
    if 'csv' in folded or 'mi archivo' in folded or 'mis datos' in folded:
        return 'csv', {}, 'El enunciado menciona datos propios: carga el CSV en el nodo antes de ejecutar.'
    for name in sorted(wooldridge_names(), key=len, reverse=True):
        # Exige un nombre con dígito (wage1, hprice1) o la mención explícita de Wooldridge para evitar falsos positivos.
        explicit = 'wooldridge' in folded or any(char.isdigit() for char in name)
        if name and explicit and re.search(r'\b' + re.escape(name) + r'\b', folded):
            return 'wooldridge', {'dataset': name}, f'Se usa el conjunto {name} de Wooldridge.'
    if 'wooldridge' in folded:
        return 'wooldridge', {'dataset': 'wage1'}, 'Wooldridge sin conjunto explícito: se usa wage1.'
    country = None
    for name, code in sorted(countries().items(), key=lambda pair: -len(pair[0])):
        if len(name) > 3 and re.search(r'\b' + re.escape(name) + r'\b', folded):
            country = code
            break
    indicator = next((code for pattern, code in INDICATORS if re.search(pattern, folded)), None)
    if 'banco mundial' in folded or 'world bank' in folded or (country and indicator):
        params = {'country': country or 'MEX', 'indicator': indicator or 'NY.GDP.PCAP.KD'}
        years = [int(y) for y in re.findall(r'\b(19[6-9]\d|20[0-4]\d)\b', folded)]
        if len(years) >= 2:
            params.update({'start': min(years), 'end': max(years)})
        return 'worldbank', params, f"Serie anual del Banco Mundial ({params['indicator']}, {params['country']})."
    return None, {}, ''


def detect_tools(text):
    """Herramientas registradas y fichas faltantes deducidas del enunciado."""
    folded = fold(text)
    found, gaps, seen = [], [], set()
    for pattern, kind, stage, spec in INTENTS:
        if kind in seen or not re.search(pattern, folded):
            continue
        # 'regresion múltiple' implica no añadir también OLS simple
        if kind == 'ols' and 'multiple_ols' in seen:
            continue
        if kind == 'arima' and 'sarima' in seen and 'sarima' in NODE_CATALOG:
            continue
        seen.add(kind)
        if kind in NODE_CATALOG:
            found.append((stage, kind))
        elif spec:
            gaps.append({'id': kind, **spec, 'evidence': re.search(pattern, folded).group(0)})
    if 'residual_normality' in seen and not re.search(r'normalidad de (las )?variables|normalidad de los datos', folded):
        found = [pair for pair in found if pair[1] != 'normality']
    found.sort(key=lambda pair: pair[0])
    return [kind for _, kind in found], gaps


STAGE = {kind: stage for _, kind, stage, _ in INTENTS}


def scenario_for(kinds):
    """Escenario sintético guiado por la herramienta principal (modelo antes que exploración)."""
    priority = {3: 0, 4: 1, 1: 2, 2: 3}
    for kind in sorted(kinds, key=lambda k: priority.get(STAGE.get(k, 2), 4)):
        if kind in SCENARIO_FOR:
            return SCENARIO_FOR[kind]
    return 'regression'


def rules_plan(prompt, retrieved_tools=()):
    """Plan determinista con la misma estructura que devuelve el modelo de lenguaje."""
    source, source_params, source_reason = detect_source(prompt)
    kinds, gaps = detect_tools(prompt)
    if not kinds:
        # Sin palabras clave: usar las herramientas mejor recuperadas por BM25.
        kinds = [kind for kind in retrieved_tools if NODE_CATALOG.get(kind, {}).get('inputs') == {'data': 'Dataset'}][:2]
    if not kinds:
        kinds = ['describe', 'scatter', 'ols']
    if source is None:
        scenario = scenario_for(kinds + [g['id'] for g in gaps])
        if scenario not in NODE_CATALOG['synthetic'].get('choices', {}).get('scenario', []):
            scenario = 'regression'
        source, source_params, source_reason = 'synthetic', {'scenario': scenario, 'n': 300, 'seed': 42}, \
            f'Sin fuente explícita: datos sintéticos reproducibles (escenario {scenario}, semilla 42).'
    steps = [{'id': 'datos', 'tool': source, 'parameters': source_params, 'why': source_reason}]
    if 'describe' not in kinds and source != 'csv':
        kinds.insert(0, 'describe')
    for kind in kinds:
        steps.append({'id': kind, 'tool': kind, 'parameters': hints(kind, fold(prompt)), 'why': NODE_CATALOG[kind].get('explanation', '')})
    if any(NODE_CATALOG[k]['outputs'].get('result') == 'Result' for k in kinds):
        steps.append({'id': 'reporte', 'tool': 'report', 'parameters': {'note': f'Interpreta el resultado para responder: {prompt[:300]}'},
                      'why': 'Cierra el flujo con una pregunta de interpretación.'})
    title = prompt.strip().split('\n')[0][:80] or 'Blueprint generado'
    return {'title': title, 'objective': f'Responder: {prompt.strip()[:400]}', 'steps': steps, 'missing': gaps}
