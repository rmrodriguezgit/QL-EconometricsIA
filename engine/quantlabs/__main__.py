"""JSON-RPC 2.0, one request/response per line on standard input/output.

El escritorio mantiene varios procesos abiertos (grupo de trabajadores) y les envía una solicitud
tras otra; cada respuesta ocupa exactamente una línea. Lo que impriman las librerías se desvía a
stderr para no corromper el canal.
"""
import json
import os
import sys
from .core import EngineError, NODES, SCHEMA, VERSION, canonical, execute, validate_project


def dispatch(request):
    if not isinstance(request, dict) or request.get('jsonrpc') != '2.0' or 'id' not in request or isinstance(request.get('id'), bool) or not isinstance(request.get('id'), (str, int, type(None))) or not isinstance(request.get('method'), str):
        return {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32600, 'message': 'Solicitud JSON-RPC inválida.'}}
    request_id = request['id']
    method, params = request.get('method'), request.get('params', {})
    try:
        if not isinstance(params, dict):
            raise EngineError('INVALID_PARAMETERS', 'params debe ser un objeto.')
        if method == 'engine.health':
            result = {'version': VERSION, 'schema_version': SCHEMA, 'protocol_version': '1.0.0'}
        elif method == 'engine.warmup':
            result = warmup()
        elif method == 'system.audit':
            from .audit import system_audit
            result = system_audit()
        elif method == 'nodes.list':
            result = NODES
        elif method == 'project.validate':
            draft = params.get('draft', False)
            if not isinstance(draft, bool):
                raise EngineError('INVALID_PARAMETERS', 'draft debe ser booleano.')
            validate_project(params.get('project'), require_connected=not draft)
            result = {'valid': True}
        elif method == 'worldbank.indicators':
            from .worldbank_catalog import search_indicators
            result = search_indicators(params)
        elif method in ['projects.list', 'projects.read', 'projects.save', 'projects.delete', 'projects.restore', 'examples.list', 'examples.read']:
            from .projects import dispatch_files
            result = dispatch_files(method, params)
        elif method.startswith('brain.'):
            from .brain.service import dispatch as brain_dispatch
            result = brain_dispatch(method, params)
        elif method == 'run.start':
            result = execute(params.get('project'), params.get('target_node'))
        else:
            return {'jsonrpc': '2.0', 'id': request_id, 'error': {'code': -32601, 'message': 'Método desconocido.'}}
        return {'jsonrpc': '2.0', 'id': request_id, 'result': result}
    except EngineError as exc:
        return {'jsonrpc': '2.0', 'id': request_id, 'error': {'code': -32602, 'message': str(exc), 'data': {'code': exc.code, 'node_id': exc.node_id}}}
    except Exception:
        return {'jsonrpc': '2.0', 'id': request_id, 'error': {'code': -32603, 'message': 'Error interno del motor.'}}


def warmup():
    """Carga por adelantado las librerías pesadas para que la primera ejecución no pague la importación."""
    import time
    started = time.perf_counter()
    import scipy.stats  # noqa: F401
    import statsmodels.api  # noqa: F401
    import sklearn.linear_model, sklearn.model_selection, sklearn.preprocessing  # noqa: F401,E401
    from . import tools, gap_tools, multivariate_tools, normality_tools  # noqa: F401
    from .parallel import install, workers
    install()
    return {'ready': True, 'pid': os.getpid(), 'threads': workers(), 'seconds': round(time.perf_counter() - started, 3)}


def main():
    # Respuestas por un duplicado del stdout original; el resto de salidas estándar va a stderr.
    channel = os.fdopen(os.dup(sys.stdout.fileno()), 'w', encoding='utf-8')
    sys.stdout.flush()
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    sys.stdout = sys.stderr
    # Bounded reads prevent untrusted projects exhausting memory before validation.
    while True:
        line = sys.stdin.buffer.readline(4_000_001)
        if not line:
            break
        if len(line) > 4_000_000:
            # Drain only this oversized request; keep the following request intact.
            while not line.endswith(b'\n'):
                line = sys.stdin.buffer.readline(4_000_001)
                if not line:
                    break
            response = {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32600, 'message': 'Solicitud demasiado grande.'}}
        else:
            try:
                def reject_constant(value):
                    raise ValueError('Non-finite JSON')
                request = json.loads(line, parse_constant=reject_constant)
                response = dispatch(request)
            except (ValueError, UnicodeDecodeError):
                response = {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'JSON inválido.'}}
        channel.write(canonical(response) + '\n')
        channel.flush()


if __name__ == '__main__':
    main()
