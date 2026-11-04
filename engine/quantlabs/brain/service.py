"""Orquestación del segundo cerebro: recuperar → planear → compilar → verificar → recordar."""
import re

from ..core import NODE_CATALOG, EngineError
from . import BRAIN_VERSION, llm, store
from .compiler import compile_plan, verify
from .intents import INTENTS, detect_tools, rules_plan
from .knowledge import EXCLUDED_TOOLS, build_index, fold

ENGINES = ['auto', 'ollama', 'rules']
ALWAYS = ['synthetic', 'simulate', 'worldbank', 'worldbank_multi', 'wooldridge', 'csv', 'describe', 'report']


def retrieve(prompt, limit=18):
    index = build_index(store.accepted())
    tools = [hit['id'] for hit in index.search(prompt, limit=limit, kind='tool')]
    rule_tools, _ = detect_tools(prompt)
    candidates = list(dict.fromkeys(ALWAYS + rule_tools + tools))
    candidates = [kind for kind in candidates if kind in NODE_CATALOG and kind not in EXCLUDED_TOOLS]
    examples = index.search(prompt, limit=3, kind='memory') + index.search(prompt, limit=3, kind='example')
    return candidates, tools, examples[:4]


IGNORED_GAPS = {'', 'missing', 'none', 'null', 'ninguno', 'ninguna', 'n_a', 'na'}


def normalize_gaps(gaps):
    """Unifica fichas del modelo y de las reglas; si un hueco coincide con una intención conocida, usa su id."""
    out = {}
    for gap in gaps:
        if not isinstance(gap, dict):
            continue
        name = str(gap.get('name') or gap.get('id') or '')
        if store.gap_id(name) in IGNORED_GAPS:
            continue
        identifier = gap.get('id')
        if not identifier:
            text = fold(name + ' ' + str(gap.get('purpose', '')))
            match = next((intent for intent in INTENTS if intent[3] and re.search(intent[0], text)), None)
            if match:
                identifier, gap = match[1], {**match[3], **{k: v for k, v in gap.items() if v}}
                gap['name'] = match[3]['name']
        identifier = store.gap_id(identifier or name)
        if identifier in NODE_CATALOG:
            continue  # ya existe: el compilador debió usarla o descartarla por puertos
        out.setdefault(identifier, {**gap, 'id': identifier})
    return list(out.values())


def status():
    ollama = llm.status()
    return {'brain_version': BRAIN_VERSION, 'tools': len([k for k in NODE_CATALOG if k not in EXCLUDED_TOOLS]),
            'engines': ENGINES, 'ollama': ollama, 'default_engine': 'ollama' if ollama['ready'] else 'rules',
            'memory': len(store.history(10_000)), 'pending_gaps': len(store.list_gaps('pending'))}


def plan(params):
    prompt = params.get('prompt')
    engine = params.get('engine', 'auto')
    if not isinstance(prompt, str) or not 3 <= len(prompt.strip()) <= 4000:
        raise EngineError('INVALID_PARAMETERS', 'Escribe un enunciado de 3 a 4.000 caracteres.')
    if engine not in ENGINES:
        raise EngineError('INVALID_PARAMETERS', 'Motor no válido: auto, ollama o rules.')
    allow_network = params.get('allow_network', False) is True
    should_verify = params.get('verify', True) is not False
    candidates, retrieved, examples = retrieve(prompt)
    trace = {'retrieved_tools': retrieved[:10], 'examples': [{'id': e['id'], 'title': e.get('title', ''), 'score': e['score']} for e in examples]}
    raw, meta, used, fallback_reason = None, {}, 'rules', None
    if engine in ('auto', 'ollama'):
        try:
            raw, meta = llm.plan(prompt, candidates, examples)
            used = 'ollama'
        except RuntimeError as error:
            if engine == 'ollama':
                raise EngineError('BRAIN_UNAVAILABLE', str(error)) from error
            fallback_reason = str(error)
    project = report = None
    if raw is not None:
        try:
            project, report = compile_plan(raw, prompt)
            if len(project['nodes']) < 2:
                raise EngineError('INVALID_GRAPH', 'El plan del modelo quedó con menos de dos nodos útiles.')
        except EngineError as error:
            if engine == 'ollama':
                raise
            fallback_reason, used, project = f'Plan del modelo descartado: {error}', 'rules', None
    if project is None:
        raw = rules_plan(prompt, retrieved)
        project, report = compile_plan(raw, prompt)
    # Las reglas detectan huecos conocidos aunque el modelo no los mencione.
    _, rule_gaps = detect_tools(prompt)
    report['gaps'] = normalize_gaps(report['gaps'] + rule_gaps)
    project['lesson']['missing_tools'] = list(dict.fromkeys(str(g.get('name')) for g in report['gaps']))[:100]
    verification = verify(project, prompt, allow_network) if should_verify else {'executed': False, 'reason': 'Verificación desactivada.', 'nodes': {}}
    entry = store.remember({'prompt': prompt.strip()[:4000], 'engine': used, 'model': meta.get('model'), 'title': project['title'],
                            'node_types': [node['type'] for node in project['nodes']],
                            'gaps': [str(g.get('name')) for g in report['gaps']], 'verified': verification.get('status')})
    gaps = store.record_gaps(report['gaps'], prompt, entry['id']) if report['gaps'] else []
    return {'blueprint_id': entry['id'], 'engine': used, 'model': meta.get('model'), 'llm': meta, 'fallback_reason': fallback_reason,
            'project': project, 'plan': raw, 'notes': report['notes'], 'dropped': report['dropped'], 'gaps': gaps,
            'verification': verification, 'trace': trace}


def dispatch(method, params):
    if method == 'brain.status':
        return status()
    if method == 'brain.plan':
        return plan(params)
    if method == 'brain.history':
        return {'items': store.history(int(params.get('limit', 30)) if isinstance(params.get('limit', 30), int) else 30)}
    if method == 'brain.feedback':
        return store.rate(params.get('id'), params.get('value'))
    if method == 'brain.gaps':
        status_filter = params.get('status')
        return {'items': store.list_gaps(status_filter if status_filter in store.STATUSES else None)}
    if method == 'brain.gaps.update':
        return store.update_gap(params.get('id'), params.get('status'))
    raise EngineError('INVALID_PARAMETERS', 'Método del cerebro desconocido.')
