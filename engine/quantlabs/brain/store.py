"""Memoria del cerebro y cola de herramientas faltantes, en disco local.

- ``history.jsonl``: cada blueprint generado (enunciado, motor, nodos, huecos y valoración).
- ``tool-requests.json``: fichas de herramientas faltantes deduplicadas por identificador.

Ubicación: ``QL_BRAIN_DIR`` o ``.quantlabs/brain`` en la raíz (excluida de Git).
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
import uuid

from ..core import NODE_CATALOG, ROOT, EngineError
from .knowledge import fold

STATUSES = ['pending', 'planned', 'implemented', 'rejected']


def home():
    path = Path(os.environ.get('QL_BRAIN_DIR', str(ROOT / '.quantlabs/brain')))
    path.mkdir(parents=True, exist_ok=True)
    return path


def now():
    return datetime.now(timezone.utc).isoformat()


def _atomic_write(path, value):
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False, prefix='.tmp-') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        temporary = Path(stream.name)
    temporary.replace(path)


# ------------------------------------------------------------------ memoria

def remember(entry):
    entry = {'id': str(uuid.uuid4()), 'created_at': now(), 'feedback': None, **entry}
    with (home() / 'history.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + '\n')
    return entry


def history(limit=50):
    path = home() / 'history.jsonl'
    if not path.exists():
        return []
    items = []
    for line in path.read_text(encoding='utf-8').splitlines():
        try:
            items.append(json.loads(line))
        except ValueError:
            continue
    feedback = _feedback()
    for item in items:
        item['feedback'] = feedback.get(item['id'], item.get('feedback'))
    return items[-limit:][::-1]


def _feedback():
    path = home() / 'feedback.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def rate(entry_id, value):
    if value not in ('up', 'down', None):
        raise EngineError('INVALID_PARAMETERS', 'La valoración debe ser up, down o null.')
    if not isinstance(entry_id, str) or not any(item['id'] == entry_id for item in history(10_000)):
        raise EngineError('INVALID_PARAMETERS', 'No existe ese blueprint en la memoria.')
    data = _feedback()
    data[entry_id] = value
    _atomic_write(home() / 'feedback.json', data)
    return {'id': entry_id, 'feedback': value}


def accepted():
    """Blueprints valorados positivamente: se suman al corpus de recuperación."""
    return [item for item in history(10_000) if item.get('feedback') == 'up']


# -------------------------------------------------- herramientas faltantes

def gap_id(name):
    return re.sub(r'[^a-z0-9]+', '_', fold(name)).strip('_')[:60] or 'herramienta'


def _load_gaps():
    path = home() / 'tool-requests.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def _types(value):
    allowed = {'Dataset', 'FittedModel', 'Result', 'Transformer', 'Summary', 'Plot'}
    if not isinstance(value, dict):
        return {}
    return {str(k)[:40]: v for k, v in value.items() if isinstance(v, str) and v in allowed}


def record_gaps(gaps, prompt, blueprint_id=None):
    """Añade o actualiza fichas. Una ficha cuyo tipo ya existe pasa a 'implemented'."""
    data, out = _load_gaps(), []
    for gap in gaps:
        identifier = gap.get('id') or gap_id(gap.get('name', ''))
        identifier = gap_id(identifier)
        item = data.get(identifier) or {
            'id': identifier, 'name': str(gap.get('name') or identifier)[:120], 'status': 'pending',
            'purpose': '', 'module': gap.get('module', ''), 'inputs': {}, 'outputs': {}, 'parameters': {},
            'acceptance': ['Puertos tipados registrados en nodeCatalog.json', 'Prueba numérica contra una referencia (statsmodels/scipy)',
                           'Mensajes de error con códigos del motor', 'Documentado en docs/HERRAMIENTAS.md'],
            'prompts': [], 'count': 0, 'created_at': now()}
        item['purpose'] = item['purpose'] or str(gap.get('purpose') or gap.get('evidence') or '')[:600]
        item['inputs'] = item['inputs'] or _types(gap.get('inputs'))
        item['outputs'] = item['outputs'] or _types(gap.get('outputs'))
        item['count'] += 1
        item['prompts'] = (item['prompts'] + [prompt.strip()[:300]])[-5:]
        item['last_blueprint'] = blueprint_id
        item['updated_at'] = now()
        if identifier in NODE_CATALOG:
            item['status'] = 'implemented'
        data[identifier] = item
        out.append(item)
    _atomic_write(home() / 'tool-requests.json', data)
    return out


def list_gaps(status=None):
    data = _load_gaps()
    for identifier, item in data.items():  # sincroniza con el catálogo real
        if identifier in NODE_CATALOG and item['status'] != 'implemented':
            item['status'] = 'implemented'
    items = sorted(data.values(), key=lambda item: (-item['count'], item['id']))
    return [item for item in items if status in (None, item['status'])]


def update_gap(identifier, status):
    if status not in STATUSES:
        raise EngineError('INVALID_PARAMETERS', 'Estado no válido: ' + ', '.join(STATUSES))
    data = _load_gaps()
    if identifier not in data:
        raise EngineError('INVALID_PARAMETERS', 'No existe esa ficha.')
    data[identifier].update({'status': status, 'updated_at': now()})
    _atomic_write(home() / 'tool-requests.json', data)
    return data[identifier]


def gaps_markdown():
    lines = ['# Herramientas solicitadas por el segundo cerebro', '', '| Ficha | Estado | Solicitudes | Entradas → Salidas | Propósito |', '|---|---|---|---|---|']
    for item in list_gaps():
        ports = (', '.join(f'{k}:{v}' for k, v in item['inputs'].items()) or '—') + ' → ' + (', '.join(f'{k}:{v}' for k, v in item['outputs'].items()) or '—')
        lines.append(f"| `{item['id']}` {item['name']} | {item['status']} | {item['count']} | {ports} | {item['purpose'][:120]} |")
    return '\n'.join(lines) + '\n'
