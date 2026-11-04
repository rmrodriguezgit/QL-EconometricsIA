"""CLI del segundo cerebro.

Ejemplos::

    uv run python -m quantlabs.brain status
    uv run python -m quantlabs.brain plan "Regresión del consumo sobre el ingreso con diagnóstico" -o blueprint.json
    uv run python -m quantlabs.brain gaps --markdown
"""
import argparse
import json
import sys

from ..core import EngineError, canonical
from . import store
from .service import ENGINES, plan, status


def main(argv=None):
    parser = argparse.ArgumentParser(prog='quantlabs.brain', description='Segundo cerebro de Quantlabs Econometrics')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('status', help='Estado de Ollama, memoria y fichas pendientes')
    p = sub.add_parser('plan', help='Construir un blueprint desde un enunciado')
    p.add_argument('prompt')
    p.add_argument('--engine', choices=ENGINES, default='auto')
    p.add_argument('--network', action='store_true', help='Permitir verificación con Banco Mundial')
    p.add_argument('--no-verify', action='store_true')
    p.add_argument('-o', '--output', help='Guardar el proyecto JSON en esta ruta')
    g = sub.add_parser('gaps', help='Fichas de herramientas faltantes')
    g.add_argument('--markdown', action='store_true')
    sub.add_parser('history', help='Últimos blueprints')
    args = parser.parse_args(argv)
    try:
        if args.command == 'status':
            print(json.dumps(status(), ensure_ascii=False, indent=2))
        elif args.command == 'plan':
            result = plan({'prompt': args.prompt, 'engine': args.engine, 'allow_network': args.network, 'verify': not args.no_verify})
            project = result['project']
            print(f"Motor: {result['engine']}{' · ' + result['model'] if result['model'] else ''}")
            if result['fallback_reason']:
                print('Respaldo:', result['fallback_reason'])
            print('Título:', project['title'])
            for node in project['nodes']:
                state = result['verification']['nodes'].get(node['id'], {})
                print(f"  · {node['id']:<18} {node['type']:<18} {state.get('status', '—')} {state.get('error', '')}")
            if not result['verification'].get('executed'):
                print('  Sin ejecutar:', result['verification'].get('reason'))
            for gap in result['gaps']:
                print(f"  ✗ falta: {gap['name']} ({gap['status']})")
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as stream:
                    json.dump(project, stream, ensure_ascii=False, indent=2)
                print('Proyecto guardado en', args.output)
        elif args.command == 'gaps':
            print(store.gaps_markdown() if args.markdown else canonical(store.list_gaps()))
        elif args.command == 'history':
            for item in store.history(20):
                print(item['created_at'][:19], item['engine'], item['title'], item.get('feedback') or '')
    except EngineError as error:
        print('Error:', error, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
