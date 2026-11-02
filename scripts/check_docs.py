"""Validate documentation and bibliography coverage without reading private PDFs."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ['README.md', 'AGENTS.md', 'CHANGELOG.md', 'VERSION',
            'docs/ARQUITECTURA.md', 'docs/BIBLIOGRAFIA.md', 'docs/COBERTURA.md',
            'docs/ROADMAP.md', 'docs/VERSIONES.md', 'docs/VERSIONADO.md', 'docs/DESARROLLO.md', 'docs/EJEMPLOS.md', 'docs/AUDITORIA.md', 'docs/HERRAMIENTAS.md']


def check(root=ROOT):
    for name in REQUIRED:
        if not (root / name).is_file():
            raise ValueError(f'Missing required document: {name}')
    version = (root / 'VERSION').read_text().strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('VERSION must contain a SemVer number')
    for name in ['README.md', 'CHANGELOG.md', 'docs/VERSIONES.md']:
        if version not in (root / name).read_text():
            raise ValueError(f'Current version missing from {name}')
    inventory = json.loads((root / 'docs/bibliografia.json').read_text())
    ids = [row['id'] for row in inventory]
    if len(ids) < 36 or len(ids) != len(set(ids)):
        raise ValueError('Expected at least 36 unique bibliography IDs')
    coverage = (root / 'docs/COBERTURA.md').read_text()
    bibliography = (root / 'docs/BIBLIOGRAFIA.md').read_text()
    for row in inventory:
        if not re.fullmatch(r'[a-f0-9]{64}', row['sha256']):
            raise ValueError(f"Invalid SHA-256: {row['id']}")
        if row['bytes'] <= 0 or row['pages'] <= 0:
            raise ValueError(f"Invalid file metadata: {row['id']}")
        for text in [coverage, bibliography]:
            if row['id'] not in text:
                raise ValueError(f"Missing reference: {row['id']}")
    for name in REQUIRED:
        if not name.endswith('.md'):
            continue
        content = (root / name).read_text()
        if content.count('```') % 2:
            raise ValueError(f'Unbalanced fences: {name}')
        for target in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', content):
            if '://' in target or target.startswith('#'):
                continue
            if not ((root / name).parent / target.split('#')[0]).exists():
                raise ValueError(f'Broken link in {name}: {target}')
    examples = json.loads((root / 'examples/catalog.json').read_text())['examples']
    if {item['id'] for item in examples} != {f'C{i:02}' for i in range(1, 29)} or len(examples) != 28:
        raise ValueError('Expected one example per curricular module')
    if {ref for item in examples for ref in item['references']} != set(ids):
        raise ValueError('Examples must reference every chapter')
    registry=json.loads((root/'packages/contracts/nodeCatalog.json').read_text())
    for item in examples:
        if not (root / 'examples/projects' / f"{item['id']}.json").is_file():
            raise ValueError(f"Missing example file: {item['id']}")
        graph=json.loads((root/'examples/projects'/f"{item['id']}.json").read_text())
        if any(node['type'] not in registry or node['type']=='experiment' for node in graph['nodes']):
            raise ValueError('Examples must use actual registered tools')
        if {step['node_id'] for step in graph.get('lesson',{}).get('steps',[])}!={node['id'] for node in graph['nodes']}:
            raise ValueError('Every example node needs an explanatory step')
    print(f'OK: version {version}; {len(ids)} references covered; local links valid.')


if __name__ == '__main__':
    check()
