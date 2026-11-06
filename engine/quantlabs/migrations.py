"""Herramientas reemplazadas → recomendadas (packages/contracts/toolMigrations.json).

El catálogo conserva las herramientas antiguas para que los proyectos guardados sigan ejecutándose,
pero la biblioteca y el Cerebro IA ofrecen solo la recomendada. Este módulo traduce sus parámetros.
"""
import json
import re

from .core import NODE_CATALOG, ROOT

MIGRATIONS = json.loads((ROOT / 'packages/contracts/toolMigrations.json').read_text(encoding='utf-8'))['migrations']
SUPERSEDED = {kind for kind, item in NODE_CATALOG.items() if item.get('superseded_by') or item.get('legacy')}


def migrate_parameters(kind, parameters):
    """(tipo nuevo, parámetros nuevos) o None si no hay migración simple (p. ej. la red, que es una cadena)."""
    rule = MIGRATIONS.get(kind)
    if not rule or rule.get('chain'):
        return None
    parameters = parameters or {}
    merged = {**NODE_CATALOG[kind]['defaults'], **parameters}
    out = {}
    for key, source in rule['params'].items():
        if isinstance(source, str):
            if source in parameters:
                out[key] = parameters[source]
        elif 'value' in source:
            out[key] = source['value']
        elif 'template' in source:
            out[key] = re.sub(r'\{(\w+)\}', lambda m: str(merged.get(m.group(1), '')), source['template'])
    return rule['to'], out
