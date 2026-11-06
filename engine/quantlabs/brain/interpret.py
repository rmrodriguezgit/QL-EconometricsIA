"""Interpretación bajo demanda del resultado de un nodo.

Dos lecturas:
- reglas: determinista, siempre disponible. Lee métricas, p-valores, coeficientes y advertencias
  del resultado ya calculado y las explica con el criterio habitual (α del nodo o 0.05).
- ollama: el modelo local redacta la interpretación a partir de un resumen agregado del resultado
  (métricas y tablas recortadas, nunca las filas de datos) y de la lectura por reglas. Las cifras
  que menciona se cotejan con las del resultado; las que no aparecen se señalan como no verificadas.

Si Ollama no está disponible, «auto» entrega la lectura por reglas e indica el motivo.
"""
import json
import math
import re
import time
import urllib.error

from ..core import NODE_CATALOG, EngineError
from . import llm

ENGINES = ['auto', 'ollama', 'rules']
MAX_ROWS = 12
MAX_COLS = 8

INTERPRET_SCHEMA = {
    'type': 'object',
    'properties': {
        'summary': {'type': 'string'},
        'findings': {'type': 'array', 'items': {'type': 'string'}},
        'cautions': {'type': 'array', 'items': {'type': 'string'}},
        'next_steps': {'type': 'array', 'items': {'type': 'string'}},
    },
    'required': ['summary', 'findings', 'cautions', 'next_steps'],
}

SYSTEM = """Eres el tutor de Quantlabs Econometrics, un laboratorio educativo de econometría.
Recibes el RESUMEN de un resultado ya calculado por una herramienta y una LECTURA BASE hecha por reglas.
Escribe, en español claro para un estudiante, la interpretación de ese resultado.
Reglas:
1. Usa solo cifras que aparezcan en el resumen; no inventes valores, unidades ni pruebas que no se calcularon.
2. Explica qué significa cada cifra importante en el contexto de la herramienta (p. ej. qué implica un p-valor frente a α, el signo de un coeficiente, la magnitud de un R²).
3. Asociación no implica causalidad salvo que el diseño lo justifique; dilo cuando aplique.
4. "cautions" recoge supuestos, límites y advertencias del cálculo. "next_steps" sugiere 1 a 3 análisis siguientes: parte de los de la LECTURA BASE y propón solo remedios que correspondan al problema detectado (p. ej. colinealidad → quitar o combinar regresores, regularizar; heterocedasticidad → errores robustos; raíz unitaria → diferenciar). Variables instrumentales solo si se sospecha endogeneidad.
5. Si la LECTURA BASE y tu lectura discrepan en una decisión (rechazar o no H₀), sigue la LECTURA BASE.
6. Sé breve: "summary" en 2 o 3 frases; cada elemento de las listas en una frase.
Responde SOLO un objeto JSON: {"summary": "...", "findings": ["..."], "cautions": ["..."], "next_steps": ["..."]}"""

# Pruebas conocidas: etiqueta de métrica (sin acentos, minúsculas) → (prueba, hipótesis nula, lectura al rechazar, lectura al no rechazar).
TESTS = {
    'p_bp': ('Breusch-Pagan', 'varianza constante de los errores', 'hay evidencia de heterocedasticidad; conviene usar errores robustos (HC3)', 'no hay evidencia de heterocedasticidad'),
    'p_white': ('White', 'varianza constante de los errores', 'hay evidencia de heterocedasticidad (forma general)', 'no hay evidencia de heterocedasticidad general'),
    'p_bg': ('Breusch-Godfrey', 'errores sin autocorrelación', 'los errores están autocorrelacionados; los errores estándar clásicos no son fiables', 'no hay evidencia de autocorrelación en los errores'),
    'p_engle_granger': ('Engle-Granger', 'las series no están cointegradas', 'las series comparten una relación de largo plazo (cointegración)', 'no hay evidencia de cointegración'),
    'p_valor': ('prueba del nodo', 'el efecto o la diferencia es cero', 'el resultado es estadísticamente significativo', 'no hay evidencia suficiente para descartar un efecto nulo'),
    'p_jarque_bera': ('Jarque-Bera', 'normalidad', 'los datos se alejan de la normalidad', 'no hay evidencia contra la normalidad'),
    'p_shapiro': ('Shapiro-Wilk', 'normalidad', 'los datos se alejan de la normalidad', 'no hay evidencia contra la normalidad'),
}


def fold(text):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', str(text)) if unicodedata.category(c) != 'Mn').lower()


def num(value, digits=4):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return str(value)
    if value == 0:
        return '0'
    if abs(value) >= 1e6 or abs(value) < 1e-4:
        return f'{value:.3g}'
    if abs(value) >= 1000:
        return f'{value:,.1f}'
    return f'{value:.{digits}g}'


def pct(value):
    return f'{value * 100:.1f}'.rstrip('0').rstrip('.') if finite(value) else str(value)


def pvalue(value):
    return '< 0.001' if isinstance(value, (int, float)) and value < 0.001 else num(value, 3)


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


# ---------------------------------------------------------------- resumen agregado (lo único que ve el modelo)

def _table(title, columns, rows):
    return {'title': str(title), 'columns': [str(c) for c in columns][:MAX_COLS],
            'rows': [list(row)[:MAX_COLS] for row in rows][:MAX_ROWS], 'total_rows': len(rows)}


def _column_stats(records, columns):
    out = []
    for column in columns[:MAX_COLS]:
        values = [row.get(column) for row in records if isinstance(row, dict)]
        numbers = [v for v in values if finite(v)]
        if not numbers:
            continue
        mean = sum(numbers) / len(numbers)
        ordered = sorted(numbers)
        out.append([column, len(numbers), len(values) - len(numbers), mean, ordered[len(ordered) // 2], ordered[0], ordered[-1]])
    return out


REMEDIES = {
    'p_bp': 'Usa errores estándar robustos (HC3) o modela la varianza.',
    'p_white': 'Usa errores estándar robustos (HC3) y revisa la forma funcional.',
    'p_bg': 'Usa errores HAC (Newey-West) o añade rezagos de la respuesta.',
    'p_engle_granger': 'Estima un modelo de corrección de error (ECM) para separar corto y largo plazo.',
}


# Avisos de deprecación de librerías (en inglés): no dicen nada del resultado.
LIBRARY_NOTICE = re.compile(r'\b(currently returns|will switch|deprecated|FutureWarning|in release|is deprecated)\b', re.I)


def digest(node_type, result, parameters=None):
    """Resumen agregado y acotado del resultado: métricas y tablas, sin filas de datos."""
    if not isinstance(result, dict):
        raise EngineError('INVALID_PARAMETERS', 'result debe ser un objeto.')
    definition = NODE_CATALOG.get(node_type, {})
    kind = result.get('kind')
    safe_params = {k: v for k, v in (parameters or {}).items()
                   if isinstance(v, (int, float, str)) and k not in ('content', 'source') and len(str(v)) <= 200}
    out = {'tool': node_type, 'label': definition.get('label', node_type), 'kind': kind,
           'purpose': definition.get('explanation', '')[:300], 'parameters': safe_params,
           'metrics': [], 'tables': [], 'text': [], 'limitations': [], 'warnings': []}
    for key in ('interpretation', 'note', 'teaching_note'):
        if isinstance(result.get(key), str) and result[key].strip():
            out['text'].append(result[key].strip()[:600])
    out['limitations'] = [str(t)[:300] for t in result.get('limitations', [])][:6] if isinstance(result.get('limitations'), list) else []
    out['warnings'] = [str(t)[:300] for t in result.get('warnings', []) if not LIBRARY_NOTICE.search(str(t))][:6] if isinstance(result.get('warnings'), list) else []
    if kind in ('analysis', 'experiment'):
        out['metrics'] = [[str(m.get('label')), m.get('value')] for m in result.get('metrics', []) if isinstance(m, dict)][:20]
        out['tables'] = [_table(t.get('title', ''), t.get('columns', []), t.get('rows', []))
                         for t in result.get('tables', []) if isinstance(t, dict)][:4]
    elif kind == 'ols':
        out['metrics'] = [[k, result.get(k)] for k in ('r_squared', 'r_squared_adj', 'n', 'dropped', 'aic', 'bic', 'covariance') if k in result]
        out['metrics'] += [['x', result.get('x')], ['y', result.get('y')]]
        out['tables'] = [_table('Coeficientes', ['Término', 'Coeficiente', 'Error estándar', 'p-valor', 'IC95 inferior', 'IC95 superior'],
                                [[c.get('term'), c.get('estimate'), c.get('std_error'), c.get('p_value'), c.get('ci_low'), c.get('ci_high')]
                                 for c in result.get('coefficients', [])])]
    elif kind == 'summary':
        out['tables'] = [_table('Descriptivos', ['Variable', 'n', 'Faltantes', 'Media', 'Mediana', 'Desviación', 'Mínimo', 'Máximo'],
                                [[r.get(k) for k in ('variable', 'n', 'missing', 'mean', 'median', 'std', 'min', 'max')] for r in result.get('rows', [])])]
        out['metrics'] = [['n_total', result.get('n_total')]]
    elif kind == 'scatter':
        points = [p for p in result.get('points', []) if isinstance(p, list) and len(p) == 2 and finite(p[0]) and finite(p[1])]
        out['metrics'] = [['x', result.get('x')], ['y', result.get('y')], ['n', result.get('n')], ['dropped', result.get('dropped')]]
        r = _pearson(points)
        if r is not None:
            out['metrics'].append(['correlacion_pearson', r])
    elif kind == 'dataset':
        columns = result.get('columns') or []
        out['metrics'] = [['filas', result.get('n')], ['columnas', len(columns)]]
        records = result.get('records') if isinstance(result.get('records'), list) else result.get('preview') or []
        stats = _column_stats(records, result.get('numeric_columns') or columns)
        if finite(result.get('n')) and 0 < len(records) < result['n']:
            out['warnings'].append(f'Resumen por columna calculado con las primeras {len(records)} de {result["n"]} filas.')
        if stats:
            out['tables'] = [_table('Resumen por columna', ['Columna', 'n', 'Faltantes', 'Media', 'Mediana', 'Mínimo', 'Máximo'], stats)]
        info = result.get('scenario_info')
        if isinstance(info, dict):
            out['text'].append(f"{info.get('title', '')}: {info.get('equation', '')}"[:300])
    else:
        # Gráficos u otras salidas: solo escalares de primer nivel.
        out['metrics'] = [[k, v] for k, v in result.items() if isinstance(v, (int, float, str)) and not isinstance(v, bool)
                          and k not in ('kind', 'tool_type', 'note', 'teaching_note', 'data_sha256', 'input_source_id') and len(str(v)) <= 80][:15]
    return out


def _pearson(points):
    if len(points) < 3:
        return None
    n = len(points)
    mx = sum(p[0] for p in points) / n
    my = sum(p[1] for p in points) / n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in points)
    sxx = sum((p[0] - mx) ** 2 for p in points)
    syy = sum((p[1] - my) ** 2 for p in points)
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else None


# ---------------------------------------------------------------- lectura por reglas

def strength(r):
    a = abs(r)
    return 'muy débil' if a < 0.2 else 'débil' if a < 0.4 else 'moderada' if a < 0.6 else 'fuerte' if a < 0.8 else 'muy fuerte'


def _coefficients_reading(rows, alpha, y_name=None):
    findings = []
    significant = 0
    for row in rows:
        term, estimate, p = row[0], row[1], row[3] if len(row) > 3 else None
        if str(term).lower() in ('const', 'intercepto', 'intercept') or not finite(estimate):
            continue
        sig = finite(p) and p < alpha
        significant += sig
        direction = 'aumenta' if estimate > 0 else 'disminuye'
        target = f' {y_name}' if y_name else ' la respuesta'
        text = f'{term}: por cada unidad adicional,{target} {direction} en promedio {num(abs(estimate))}'
        text += f' (p {pvalue(p)}, {"significativo" if sig else "no significativo"} con α = {num(alpha)}).' if finite(p) else '.'
        findings.append(text)
    return findings, significant


def rules(node_type, result, parameters=None):
    """Interpretación determinista. Devuelve summary, findings, cautions, next_steps."""
    d = digest(node_type, result, parameters)
    params = parameters or {}
    alpha = params.get('alpha') if finite(params.get('alpha')) and 0 < params.get('alpha') < 1 else 0.05
    kind = d['kind']
    summary, findings, cautions, steps = [], [], list(d['warnings']), []
    metrics = {fold(k): v for k, v in d['metrics']}

    if kind == 'ols':
        r2, n = result.get('r_squared'), result.get('n')
        y, x = result.get('y'), result.get('x')
        if finite(r2):
            summary.append(f'La recta explica el {pct(r2)} % de la variación de {y} con {num(n)} observaciones.')
        rows = d['tables'][0]['rows'] if d['tables'] else []
        coef, sig = _coefficients_reading(rows, alpha, y)
        findings += coef
        if finite(r2):
            findings.append(f'R² = {num(r2)}: ajuste {"bajo" if r2 < 0.3 else "moderado" if r2 < 0.7 else "alto"}; un R² bajo no invalida la pendiente, solo indica que otros factores explican buena parte de {y}.')
        if finite(result.get('dropped')) and result['dropped'] > 0:
            cautions.append(f'Se excluyeron {num(result["dropped"])} filas con faltantes; revisa si su ausencia es aleatoria.')
        cautions.append(f'La pendiente mide asociación entre {x} y {y}; interpretarla como efecto causal requiere exogeneidad.')
        cautions.append(f'Errores estándar {result.get("covariance")}: ' + ('robustos a heterocedasticidad.' if 'HC' in str(result.get('covariance')) else 'clásicos, suponen varianza constante.'))
        steps += ['Revisa los supuestos con el nodo Diagnósticos (heterocedasticidad, autocorrelación, VIF).',
                  'Compara con una regresión múltiple si sospechas variables omitidas.']
    elif kind == 'summary':
        for row in d['tables'][0]['rows'] if d['tables'] else []:
            name, n, missing, mean, median, std = row[:6]
            parts = [f'{name}: media {num(mean)}, mediana {num(median)}']
            if finite(std) and finite(mean) and mean != 0:
                parts.append(f'coeficiente de variación {pct(abs(std / mean))} %')
            if finite(mean) and finite(median) and finite(std) and std > 0:
                gap = (mean - median) / std
                if abs(gap) > 0.1:
                    parts.append('asimetría ' + ('positiva (cola a la derecha)' if gap > 0 else 'negativa (cola a la izquierda)'))
            findings.append(', '.join(parts) + '.')
            if finite(missing) and missing > 0:
                cautions.append(f'{name} tiene {num(missing)} valores faltantes.')
        summary.append(f'Descriptivos de {len(findings)} variable(s). Compara media y mediana para detectar asimetrías y la desviación para la dispersión.')
        steps += ['Grafica un histograma o un diagrama de caja para confirmar la forma de la distribución.']
    elif kind == 'scatter':
        r = metrics.get('correlacion_pearson')
        if finite(r):
            summary.append(f'Entre {result.get("x")} y {result.get("y")} hay una relación lineal {strength(r)} y {"positiva" if r > 0 else "negativa"} (r = {num(r, 3)}).')
            findings.append(f'r² = {num(r * r, 3)}: una recta explicaría cerca del {pct(r * r)} % de la variación.')
        findings.append(f'{num(result.get("n"))} pares completos; {num(result.get("dropped"))} excluidos.')
        cautions.append('La correlación solo capta relaciones lineales y es sensible a valores atípicos.')
        steps.append('Ajusta una regresión OLS para cuantificar la pendiente e inferir sobre ella.')
    elif kind == 'dataset':
        summary.append(f'Tabla con {num(result.get("n"))} filas y {len(result.get("columns") or [])} columnas: {", ".join(map(str, (result.get("columns") or [])[:8]))}.')
        for row in d['tables'][0]['rows'] if d['tables'] else []:
            findings.append(f'{row[0]}: media {num(row[3])}, rango {num(row[5])} a {num(row[6])}' + (f', {num(row[2])} faltantes' if row[2] else '') + '.')
            if row[2]:
                cautions.append(f'{row[0]} tiene {num(row[2])} faltantes; los modelos los excluyen por fila.')
        steps.append('Conecta Descriptivos o un gráfico para explorar las variables antes de modelar.')
    else:
        if node_type == 'portfolio':
            _portfolio_rules(result, params, summary, findings, cautions, steps)
        _analysis_rules(d, metrics, alpha, summary, findings, cautions, steps, params)

    if not summary and d['text']:
        summary.append(d['text'][0])
    for text in d['text']:
        if text not in summary and len(findings) < 12 and kind in ('analysis', 'experiment'):
            findings.insert(0, text)
            break
    cautions += [t for t in d['limitations'] if t not in cautions]
    return {'summary': ' '.join(summary) or f'Resultado de {d["label"]}.', 'findings': _unique(findings)[:12],
            'cautions': _unique(cautions)[:8], 'next_steps': _unique(steps)[:4]}, d


def _portfolio_rules(result, params, summary, findings, cautions, steps):
    """Markowitz: compara lo esperado con lo obtenido fuera de muestra, la concentración y el reparto del riesgo."""
    tables = {t.get('title'): t for t in result.get('tables') or []}
    weights = tables.get('Pesos de cada portafolio (%)')
    expected = tables.get('Rendimiento, volatilidad y riesgo esperados (estimación)')
    test = tables.get('Desempeño fuera de muestra (prueba)')
    risk = tables.get('Contribución de cada activo al riesgo (% de la varianza)')
    if not (weights and expected and test):
        return
    columns = weights['columns'][1:-2]
    exp = {r[0]: r for r in expected['rows']}
    out = {r[0]: r for r in test['rows']}
    tangent, gmv = exp.get('Máximo Sharpe'), exp.get('Mínima varianza')
    if tangent and gmv:
        summary.append(f'Con los datos de estimación, el portafolio de máximo Sharpe espera {num(tangent[1], 4)} % anual con {num(tangent[2], 4)} % de volatilidad '
                       f'(Sharpe {num(tangent[5], 3)}); el de mínima varianza baja la volatilidad a {num(gmv[2], 4)} % con {num(gmv[1], 4)} % de rendimiento esperado.')
    ranked = sorted((r for r in test['rows'] if finite(r[4])), key=lambda r: -r[4])
    if ranked:
        best = ranked[0]
        summary.append(f'Fuera de muestra el mejor Sharpe lo obtuvo {best[0]} ({num(best[4], 3)}), '
                       + ('el mismo que se esperaba ganador.' if best[0] == 'Máximo Sharpe' else 'no el de máximo Sharpe estimado: las medias estimadas no se repitieron.'))
    for name, row in out.items():
        e = exp.get(name)
        if e and finite(e[5]) and finite(row[4]):
            findings.append(f'{name}: Sharpe esperado {num(e[5], 3)} frente a {num(row[4], 3)} en la prueba; Sortino {num(e[6], 3)} frente a {num(row[5], 3)}; '
                            f'caída máxima en la prueba {num(row[6], 3)} %.')
    cap = params.get('max_weight', 1)
    for row in weights['rows']:
        name, w = row[0], row[1:1 + len(columns)]
        effective = row[-2]
        if name == 'Pesos iguales' or not finite(effective):
            continue
        zero = [c for c, v in zip(columns, w) if finite(v) and v < 0.5]
        text = f'{name}: equivale a {num(effective, 3)} activos efectivos'
        if zero:
            text += f'; deja fuera {", ".join(map(str, zero))}'
        findings.append(text + '.')
        if finite(cap) and cap < 1 and any(finite(v) and v >= cap * 100 - 0.01 for v in w):
            cautions.append(f'En {name} algún activo llega al tope de {pct(cap)} %: la restricción está activa y determina los pesos.')
    if risk:
        for row in risk['rows']:
            share = [(c, v) for c, v in zip(columns, row[1:]) if finite(v)]
            if share:
                c, v = max(share, key=lambda x: x[1])
                if v > 60:
                    findings.append(f'En {row[0]}, {c} aporta el {num(v, 3)} % de la varianza: el riesgo está concentrado en un activo.')
    if tangent and out.get('Máximo Sharpe') and finite(tangent[5]) and finite(out['Máximo Sharpe'][4]) and out['Máximo Sharpe'][4] < tangent[5] / 2:
        cautions.append('El Sharpe obtenido fuera de muestra es menos de la mitad del esperado: síntoma típico del error de estimación de las medias.')
    steps += ['Cambia la fracción de estimación o la covarianza (contracción frente a muestral) y observa si los pesos se mantienen estables.',
              'Pasa la salida de rendimientos a Medidas de riesgo para comparar VaR, CVaR y caídas de cada portafolio en la prueba.']


def _unique(items):
    return list(dict.fromkeys(i for i in items if i))


def _analysis_rules(d, metrics, alpha, summary, findings, cautions, steps, params):
    tool = d['tool']
    # p-valores conocidos en las métricas
    for label, value in d['metrics']:
        key = fold(label)
        if key in TESTS and finite(value):
            name, null, reject, keep = TESTS[key]
            decision = value < alpha
            findings.append(f'{name}: p {pvalue(value)} {"<" if decision else "≥"} α = {num(alpha)} → '
                            f'{"se rechaza" if decision else "no se rechaza"} H₀ ({null}); {reject if decision else keep}.')
            if decision and key in REMEDIES:
                steps.append(REMEDIES[key])
        elif key.startswith('p_') and finite(value) and 0 <= value <= 1:
            findings.append(f'{label}: p {pvalue(value)} ({"significativo" if value < alpha else "no significativo"} con α = {num(alpha)}).')
        elif key == 'durbin_watson' and finite(value):
            findings.append(f'Durbin-Watson = {num(value, 3)}: ' + ('cercano a 2, sin autocorrelación de primer orden aparente.' if 1.5 <= value <= 2.5
                            else 'lejos de 2, posible autocorrelación de los errores.'))
        elif key in ('r²', 'r2', 'r2_ajuste', 'r²_validacion', 'r2_validacion') and finite(value):
            findings.append(f'{label} = {num(value)}: el modelo explica el {pct(value)} % de la variación.')
        elif key in ('r² ajustado', 'r²_ajustado') and finite(value):
            findings.append(f'{label} = {num(value)}: penaliza regresores que no aportan.')
        elif key in ('cfi',) and finite(value):
            findings.append(f'CFI = {num(value, 3)}: ' + ('ajuste aceptable (≥ 0.95).' if value >= 0.95 else 'ajuste mejorable (< 0.95).'))
        elif key in ('rmsea',) and finite(value):
            findings.append(f'RMSEA = {num(value, 3)}: ' + ('ajuste bueno (≤ 0.06).' if value <= 0.06 else 'ajuste deficiente (> 0.08).' if value > 0.08 else 'ajuste aceptable.'))
        elif key in ('silueta', 'silueta_media') and finite(value):
            findings.append(f'Silueta = {num(value, 3)}: ' + ('grupos bien separados.' if value > 0.5 else 'separación moderada.' if value > 0.25 else 'grupos poco definidos.'))
    for table in d['tables']:
        columns = [fold(c) for c in table['columns']]
        if 'p-valor' in columns and ('termino' in columns or 'serie' in columns):
            p_index = columns.index('p-valor')
            if 'termino' in columns:
                rows = [[r[0], r[1], None, r[p_index]] for r in table['rows']]
                coef, sig = _coefficients_reading(rows, alpha, params.get('y') if isinstance(params.get('y'), str) and params.get('y') else None)
                findings += coef
                if coef:
                    summary.append(f'{sig} de {len(coef)} regresor(es) resultan significativos con α = {num(alpha)}.')
            else:
                for row in table['rows']:
                    p = row[p_index]
                    if finite(p):
                        findings.append(f'ADF en {row[0]}: p {pvalue(p)} → ' + ('se rechaza la raíz unitaria; la serie es estacionaria.' if p < alpha
                                        else 'no se rechaza la raíz unitaria; considera diferenciar la serie.'))
        if 'rmse' in columns and 'modelo' in columns:
            i = columns.index('rmse')
            ranked = sorted((r for r in table['rows'] if finite(r[i])), key=lambda r: r[i])
            if ranked:
                findings.append(f'Menor RMSE de evaluación: {ranked[0][0]} ({num(ranked[0][i])}).')
        if 'vif' in columns:
            high = [r[0] for r in table['rows'] if finite(r[columns.index('vif')]) and r[columns.index('vif')] > 10]
            findings.append('VIF > 10 en ' + ', '.join(map(str, high)) + ': colinealidad fuerte.' if high else 'Todos los VIF ≤ 10: sin colinealidad grave.')
            if high:
                steps.append('Quita o combina los regresores colineales, o usa una regresión regularizada (ridge o lasso).')
    agent, hold = metrics.get('retorno_agente_prueba_%'), metrics.get('retorno_comprar_mantener_%')
    if finite(agent) and finite(hold):
        better = agent > hold
        summary.append(f'Fuera de muestra el agente obtiene {num(agent)} % frente a {num(hold)} % de comprar y mantener: '
                       + ('la política aprendida supera a la referencia.' if better else 'la política aprendida no supera a la referencia.'))
        sa, sh = metrics.get('sharpe_agente'), metrics.get('sharpe_comprar_mantener')
        if finite(sa) and finite(sh):
            findings.append(f'Sharpe anualizado {num(sa)} frente a {num(sh)}: ' + ('mejor rendimiento por unidad de riesgo.' if sa > sh else 'no mejora el rendimiento por unidad de riesgo.'))
        if finite(metrics.get('cambios_de_posicion_prueba')):
            findings.append(f'{num(metrics["cambios_de_posicion_prueba"])} cambios de posición en la prueba; cada uno paga el costo de transacción.')
        if abs(agent) > 500:
            cautions.append('Un rendimiento tan extremo indica una serie muy predecible (p. ej. sintética con regímenes persistentes); no es esperable en mercados reales.')
        steps.append('Sube el costo por cambio de posición o cambia la semilla para ver si la ventaja persiste.')
    fit, val = metrics.get('r2_ajuste'), metrics.get('r2_validacion')
    if finite(fit) and finite(val):
        gap = fit - val
        findings.append(f'Diferencia de R² entre ajuste y validación: {num(gap, 3)} → ' + ('sin señales claras de sobreajuste.' if gap < 0.05 else 'posible sobreajuste; aumenta dropout o L2, o reduce capas.'))
        steps.append('Compara la red con un modelo lineal en la misma muestra de validación (Comparar modelos ML).')
    if finite(metrics.get('retorno_neto')) and finite(metrics.get('baseline')):
        net, base = metrics['retorno_neto'], metrics['baseline']
        findings.append(f'Retorno neto {num(net)} frente a la referencia {num(base)}: la señal ' + ('aporta' if net > base else 'no aporta') + ' después de costos.')
    if isinstance(metrics.get('elegido'), str):
        summary.append(f'El modelo elegido por menor error de validación es {metrics["elegido"]}.')
    if tool in ('correlation',):
        steps.append('Si una correlación es alta, ajusta una regresión para cuantificarla y revisa causalidad.')
    if tool in ('multiple_ols', 'robust', 'logit', 'iv2sls', 'ecm', 'covariance'):
        steps.append('Valida supuestos con Diagnósticos y compara modelos en una muestra de evaluación.')
    if tool in ('unit_root', 'acf'):
        steps.append('Elige el orden de diferenciación y ajusta un ARIMA.')
    if not findings:
        findings += [f'{label}: {num(value) if finite(value) else value}.' for label, value in d['metrics'][:8]]
    if not findings:
        for table in d['tables'][:2]:
            for row in table['rows'][:4]:
                findings.append(f'{table["title"]} · ' + ', '.join(f'{c}: {num(v) if finite(v) else v}' for c, v in zip(table['columns'], row)) + '.')


# ---------------------------------------------------------------- lectura con el modelo local

def numbers_in(value, out=None):
    out = [] if out is None else out
    if isinstance(value, dict):
        for item in value.values():
            numbers_in(item, out)
    elif isinstance(value, (list, tuple)):
        for item in value:
            numbers_in(item, out)
    elif finite(value):
        out.append(float(value))
    elif isinstance(value, str):
        out += [float(m.replace(',', '')) for m in re.findall(r'-?\d[\d,]*\.?\d*(?:e-?\d+)?', value) if _float(m.replace(',', '')) is not None]
    return out


def _float(text):
    try:
        return float(text)
    except ValueError:
        return None


NUMBER = re.compile(r'(?<![\w.])-?\d+(?:[.,]\d+)?(?:\s?%)?')


def unverified_numbers(texts, reference):
    """Cifras del texto que no coinciden (al redondeo o como porcentaje) con ninguna del resumen."""
    pool = set()
    for value in reference:
        for candidate in (value, value * 100, abs(value), abs(value) * 100):
            pool.add(candidate)
    missing = []
    for text in texts:
        for match in NUMBER.findall(text):
            raw = match.replace('%', '').strip()
            if raw.count(',') == 1 and '.' not in raw:
                raw = raw.replace(',', '.')
            value = _float(raw)
            if value is None or (float(value).is_integer() and abs(value) <= 10) or 1900 <= abs(value) <= 2100:
                continue  # conteos pequeños, órdenes y años no se cotejan
            decimals = len(raw.split('.')[1]) if '.' in raw else 0
            tolerance = max(0.5 * 10 ** -decimals, abs(value) * 0.005)
            if not any(abs(abs(value) - abs(ref)) <= tolerance for ref in pool):
                missing.append(match.strip())
    return list(dict.fromkeys(missing))


def _clean_list(value, limit):
    return [str(item).strip()[:400] for item in value if isinstance(item, str) and item.strip()][:limit] if isinstance(value, list) else []


def ollama_reading(d, base, model=None):
    models = llm.available_models()
    if models is None:
        raise RuntimeError('Ollama no responde en ' + llm.config()['url'])
    model = model or llm.choose_model(models)
    if not model:
        raise RuntimeError('No hay modelo de lenguaje instalado en Ollama.')
    user = ('RESUMEN DEL RESULTADO:\n' + json.dumps(d, ensure_ascii=False, default=str)[:9000] +
            '\n\nLECTURA BASE (reglas):\n' + json.dumps(base, ensure_ascii=False)[:3000])
    payload = {'model': model, 'messages': [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': user}],
               'stream': False, 'format': INTERPRET_SCHEMA, 'think': False,
               'options': {'temperature': 0.2, 'num_ctx': 8192, 'num_predict': 900}}
    started = time.monotonic()
    response = None
    for fallback in ('schema', 'json', 'plain'):
        if fallback == 'json':
            payload['format'] = 'json'
        elif fallback == 'plain':
            payload.pop('format', None)
        try:
            response = llm._request('/api/chat', payload, timeout=llm.config()['timeout'])
            break
        except urllib.error.HTTPError as error:
            if error.code not in (400, 500, 501) or fallback == 'plain':
                raise RuntimeError(f'Ollama devolvió HTTP {error.code}.') from error
        except (OSError, urllib.error.URLError) as error:
            raise RuntimeError('Ollama no respondió a tiempo.') from error
    content = response.get('message', {}).get('content', '')
    try:
        value = json.loads(content[content.find('{'):content.rfind('}') + 1])
    except ValueError as error:
        raise RuntimeError('El modelo no devolvió JSON válido.') from error
    if not isinstance(value, dict) or not isinstance(value.get('summary'), str) or not value['summary'].strip():
        raise RuntimeError('El modelo devolvió una interpretación vacía.')
    reading = {'summary': value['summary'].strip()[:900], 'findings': _clean_list(value.get('findings'), 10),
               'cautions': _clean_list(value.get('cautions'), 8), 'next_steps': _clean_list(value.get('next_steps'), 4)}
    return reading, {'model': model, 'seconds': round(time.monotonic() - started, 2), 'eval_count': response.get('eval_count')}


def interpret(params):
    node_type = params.get('node_type')
    result = params.get('result')
    parameters = params.get('parameters') if isinstance(params.get('parameters'), dict) else {}
    engine = params.get('engine', 'auto')
    if node_type not in NODE_CATALOG:
        raise EngineError('INVALID_PARAMETERS', 'Tipo de nodo desconocido.')
    if not isinstance(result, dict) or not result.get('kind'):
        raise EngineError('INVALID_PARAMETERS', 'No hay resultado calculado para interpretar.')
    if engine not in ENGINES:
        raise EngineError('INVALID_PARAMETERS', 'Motor de interpretación desconocido.')
    started = time.monotonic()
    base, d = rules(node_type, result, parameters)
    out = {'engine': 'rules', 'model': None, 'fallback_reason': None, **base, 'base': None, 'unverified': [],
           'label': d['label'], 'seconds': None}
    if engine in ('auto', 'ollama'):
        try:
            reading, meta = ollama_reading(d, base)
            texts = [reading['summary'], *reading['findings'], *reading['cautions'], *reading['next_steps']]
            out.update(reading)
            out.update({'engine': 'ollama', 'model': meta['model'], 'base': base,
                        'unverified': unverified_numbers(texts, numbers_in(d) + numbers_in(base))})
        except RuntimeError as error:
            if engine == 'ollama':
                raise EngineError('BRAIN_UNAVAILABLE', str(error)) from error
            out['fallback_reason'] = str(error)
    out['seconds'] = round(time.monotonic() - started, 2)
    return out
