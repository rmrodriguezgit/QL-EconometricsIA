"""Cliente mínimo de Ollama (HTTP local) con salida JSON estructurada.

Solo se conecta a la URL configurada (por defecto 127.0.0.1:11434). El modelo
recibe fichas del catálogo y ejemplos recuperados; nunca recibe datos del usuario
ni rutas locales. La respuesta se trata como datos no confiables: se valida y
compila con el catálogo antes de construir el grafo.
"""
import json
import os
import time
import urllib.error
import urllib.request

from .knowledge import tool_card

DEFAULT_URL = 'http://127.0.0.1:11434'
PREFERRED_MODELS = ['qwen3.5:4b', 'qwen3.5-4b-ctx16k:latest', 'qwen2.5:7b-instruct', 'qwen2.5:3b-instruct-q4_K_M', 'qwen2.5:3b']

PLAN_SCHEMA = {
    'type': 'object',
    'properties': {
        'title': {'type': 'string'},
        'objective': {'type': 'string'},
        'steps': {'type': 'array', 'items': {'type': 'object', 'properties': {
            'id': {'type': 'string'}, 'tool': {'type': 'string'},
            'parameters': {'type': 'object'},
            'inputs': {'type': 'object'},
            'why': {'type': 'string'}}, 'required': ['id', 'tool', 'why']}},
        'missing': {'type': 'array', 'items': {'type': 'object', 'properties': {
            'name': {'type': 'string'}, 'purpose': {'type': 'string'},
            'inputs': {'type': 'object'}, 'outputs': {'type': 'object'}}, 'required': ['name', 'purpose']}},
        'question': {'type': 'string'},
    },
    'required': ['title', 'objective', 'steps', 'missing'],
}

SYSTEM = """Eres el segundo cerebro de Quantlabs Econometrics, un laboratorio educativo de econometría con programación visual por nodos.
Tu tarea: convertir el enunciado del usuario en un BLUEPRINT (plan de nodos) usando EXCLUSIVAMENTE las herramientas listadas.
Reglas:
1. Cada paso usa un "tool" que exista en la lista. No inventes tipos ni parámetros.
2. El primer paso es una fuente de datos (synthetic, simulate, worldbank, worldbank_multi, wooldridge, fred o csv; worldbank_multi para dos o más indicadores con alias; fred para series de EE. UU. de la Reserva Federal de St. Louis: tasas del Tesoro, fondos federales, desempleo, IPC, PIB, recesiones). Si el enunciado no da datos, usa synthetic con el escenario adecuado.
3. Las conexiones respetan tipos: una entrada Dataset recibe una salida Dataset, FittedModel recibe FittedModel, Result recibe Result.
   Usa "inputs" {puerto_entrada: id_paso_origen} solo si hay ambigüedad; si no, se conecta al último paso compatible.
4. Orden pedagógico: datos → transformaciones → exploración → modelo → diagnóstico → report.
5. "parameters" solo con claves de la ficha de esa herramienta; usa nombres de columnas que produzca la fuente elegida.
6. Si el enunciado pide un análisis que ninguna herramienta cubre, NO lo simules: descríbelo en "missing" con name, purpose, inputs y outputs tipados.
7. "why" explica en una frase, en español, para qué sirve el paso en este análisis.
8. Máximo 10 pasos. Responde SOLO un objeto JSON, sin texto adicional, con esta forma:
{"title": "...", "objective": "...", "steps": [{"id": "datos", "tool": "synthetic", "parameters": {"scenario": "regression"}, "inputs": {}, "why": "..."}],
 "missing": [{"name": "...", "purpose": "...", "inputs": {"data": "Dataset"}, "outputs": {"result": "Result"}}], "question": "..."}"""


def config():
    return {'url': os.environ.get('QL_BRAIN_OLLAMA_URL', DEFAULT_URL).rstrip('/'),
            'model': os.environ.get('QL_BRAIN_MODEL', ''),
            'timeout': float(os.environ.get('QL_BRAIN_TIMEOUT', '150'))}


def _request(path, payload=None, timeout=5.0):
    settings = config()
    if not settings['url'].startswith(('http://127.0.0.1', 'http://localhost', 'http://[::1]')) and not os.environ.get('QL_BRAIN_ALLOW_REMOTE'):
        raise RuntimeError('Ollama debe ser local; define QL_BRAIN_ALLOW_REMOTE=1 para permitir otro host.')
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(settings['url'] + path, data=data, headers={'Content-Type': 'application/json'},
                                     method='POST' if data else 'GET')
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - URL local validada arriba
        return json.loads(response.read().decode('utf-8'))


def available_models():
    try:
        return [item['name'] for item in _request('/api/tags', timeout=2.0).get('models', [])]
    except (OSError, urllib.error.URLError, ValueError, RuntimeError):
        return None


def choose_model(models):
    wanted = config()['model']
    if wanted:
        return wanted if models is None or wanted in models else None
    for name in PREFERRED_MODELS:
        if models and name in models:
            return name
    return next((name for name in models or [] if 'embed' not in name), None)


def status():
    models = available_models()
    model = choose_model(models) if models is not None else None
    return {'provider': 'ollama', 'url': config()['url'], 'reachable': models is not None,
            'models': models or [], 'model': model, 'ready': bool(model)}


def build_messages(prompt, tools, examples):
    cards = [tool_card(kind) for kind in tools]
    shots = [{'titulo': item.get('title', ''), 'herramientas_en_orden': item.get('tools', [])} for item in examples]
    user = ('HERRAMIENTAS DISPONIBLES:\n' + json.dumps(cards, ensure_ascii=False) +
            '\n\nRECORRIDOS SIMILARES (referencia de orden):\n' + json.dumps(shots, ensure_ascii=False) +
            '\n\nESCENARIOS SINTÉTICOS Y SUS COLUMNAS: regression(ingreso,consumo) multiple(x,z,y) hetero(x,y) outliers(x,y) '
            'logistic(x,clase) prices(periodo,nominal,indice,poblacion) positive(periodo,valor) normal(valor) pairs(antes,despues) '
            'cobb(capital,trabajo,produccion) ar1(periodo,y,walk) cointegrated(periodo,x,y) garch(periodo,retorno) '
            'factors(x1..x6) endogenous(z,x,y) polynomial(x,y) returns(periodo,retorno) regimes(periodo,valor) clusters(x1,x2) '
            'nonlinear(x,y) inflation(r1..r5) sem(x1,x2,x3,y) seasonal(periodo,ventas). worldbank produce (periodo,valor); worldbank_multi produce (periodo[,pais], un alias por indicador); fred produce (periodo, un alias por serie «ID: alias»; periodo es año si frequency=anual o fecha AAAA-MM-DD).'
            '\n\nENUNCIADO DEL USUARIO:\n' + prompt.strip()[:4000])
    return [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': user}]


def plan(prompt, tools, examples, model=None):
    """Devuelve (plan, metadatos). Lanza RuntimeError si Ollama no está disponible o responde mal."""
    models = available_models()
    if models is None:
        raise RuntimeError('Ollama no responde en ' + config()['url'])
    model = model or choose_model(models)
    if not model:
        raise RuntimeError('No hay modelo de lenguaje instalado en Ollama.')
    started = time.monotonic()
    payload = {'model': model, 'messages': build_messages(prompt, tools, examples), 'stream': False,
               'format': PLAN_SCHEMA, 'think': False, 'options': {'temperature': 0.15, 'num_ctx': 12288, 'num_predict': 1800}}
    response = None
    # Degradación progresiva: esquema JSON → modo json → texto libre (runners MLX no admiten salida estructurada).
    for fallback in ('schema', 'json', 'plain'):
        if fallback == 'json':
            payload['format'] = 'json'
        elif fallback == 'plain':
            payload.pop('format', None)
        try:
            response = _request('/api/chat', payload, timeout=config()['timeout'])
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
    if not isinstance(value, dict) or not isinstance(value.get('steps'), list):
        raise RuntimeError('El modelo devolvió un plan sin pasos.')
    return value, {'model': model, 'format': fallback, 'seconds': round(time.monotonic() - started, 2),
                   'eval_count': response.get('eval_count'), 'prompt_eval_count': response.get('prompt_eval_count')}
