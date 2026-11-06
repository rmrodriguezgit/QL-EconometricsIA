"""Base de conocimiento local y recuperación BM25 sin dependencias externas.

Corpus: fichas del catálogo de nodos, los 28 recorridos guiados, la bibliografía
y los blueprints aceptados en la memoria del cerebro. Todo se lee del repositorio
o del espacio local; no se envía a ningún servicio.
"""
from functools import lru_cache
import json
import math
import re
import unicodedata

from ..core import NODE_CATALOG, ROOT

# Herramientas que el cerebro no debe proponer: compatibilidad anterior o entradas manuales.
# Recetas antiguas y herramientas reemplazadas: siguen en el catálogo para proyectos guardados, pero el cerebro no las ofrece.
EXCLUDED_TOOLS = {'experiment'} | {kind for kind, item in NODE_CATALOG.items() if item.get('superseded_by') or item.get('legacy')}
STOPWORDS = set('a al con de del el en es la las lo los o para por que se su sus un una y como entre sobre the of and to in'.split())


def fold(text):
    """Minúsculas sin acentos para comparar texto en español."""
    text = unicodedata.normalize('NFKD', str(text).lower())
    return ''.join(char for char in text if not unicodedata.combining(char))


def tokens(text):
    words = re.findall(r'[a-z0-9_]+', fold(text))
    out = []
    for word in words:
        if word in STOPWORDS or len(word) < 2:
            continue
        out.append(word)
        if len(word) > 5:
            out.append(word[:5])  # prefijo: regresion/regresiones, estimar/estimacion
    return out


def tool_text(kind, definition):
    return ' '.join([kind, kind.replace('_', ' '), definition.get('label', ''), definition.get('detail', ''),
                     definition.get('explanation', ''), definition.get('category', ''),
                     ' '.join(definition.get('aliases', []))])


@lru_cache(maxsize=1)
def bibliography():
    path = ROOT / 'docs/bibliografia.json'
    rows = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    return {row['id']: row.get('title', '') for row in rows}


@lru_cache(maxsize=1)
def examples():
    catalog = json.loads((ROOT / 'examples/catalog.json').read_text(encoding='utf-8'))['examples']
    items = []
    for item in catalog:
        path = ROOT / 'examples/projects' / f"{item['id']}.json"
        if not path.exists():
            continue
        project = json.loads(path.read_text(encoding='utf-8'))
        items.append({'id': item['id'], 'title': item['title'], 'topics': item.get('topics', ''),
                      'objective': item.get('objective', ''), 'tools': [node['type'] for node in project['nodes']],
                      'project': project})
    return items


class Index:
    """BM25 Okapi sobre documentos cortos."""

    def __init__(self, documents, k1=1.4, b=0.7):
        self.documents = documents
        self.k1, self.b = k1, b
        self.terms = [tokens(doc['text']) for doc in documents]
        self.avg = sum(map(len, self.terms)) / max(1, len(self.terms))
        frequency = {}
        for words in self.terms:
            for word in set(words):
                frequency[word] = frequency.get(word, 0) + 1
        n = len(documents)
        self.idf = {word: math.log(1 + (n - f + .5) / (f + .5)) for word, f in frequency.items()}

    def search(self, query, limit=10, kind=None):
        query_terms = tokens(query)
        scored = []
        for doc, words in zip(self.documents, self.terms):
            if kind and doc['kind'] != kind:
                continue
            score = 0.0
            for term in set(query_terms):
                count = words.count(term)
                if count:
                    norm = count * (self.k1 + 1) / (count + self.k1 * (1 - self.b + self.b * len(words) / self.avg))
                    score += self.idf.get(term, 0) * norm
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda pair: -pair[0])
        return [{**doc, 'score': round(score, 4)} for score, doc in scored[:limit]]


def build_index(memory_items=()):
    documents = []
    for kind, definition in NODE_CATALOG.items():
        if kind in EXCLUDED_TOOLS:
            continue
        refs = ' '.join(bibliography().get(ref, '') for ref in definition.get('references', []))
        documents.append({'kind': 'tool', 'id': kind, 'text': tool_text(kind, definition) + ' ' + refs})
    for item in examples():
        documents.append({'kind': 'example', 'id': item['id'], 'title': item['title'], 'tools': item['tools'],
                          'text': ' '.join([item['title'], item['topics'], item['objective'], ' '.join(item['tools'])])})
    for item in memory_items:
        documents.append({'kind': 'memory', 'id': item['id'], 'title': item.get('title', ''), 'tools': item.get('node_types', []),
                          'text': ' '.join([item.get('prompt', ''), item.get('title', ''), ' '.join(item.get('node_types', []))])})
    return Index(documents)


def tool_card(kind):
    """Ficha compacta para el contexto del modelo de lenguaje."""
    definition = NODE_CATALOG[kind]
    card = {'type': kind, 'label': definition['label'], 'inputs': definition['inputs'], 'outputs': definition['outputs'],
            'parameters': definition.get('defaults', {}), 'explanation': definition.get('explanation', '')[:220]}
    if definition.get('choices'):
        card['choices'] = definition['choices']
    return card
