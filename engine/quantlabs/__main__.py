"""JSON-RPC 2.0, one request/response per line on standard input/output."""
import json
import sys
from .core import EngineError, NODES, SCHEMA, VERSION, canonical, execute, validate_project


def dispatch(request):
    if not isinstance(request, dict) or request.get('jsonrpc') != '2.0' or 'id' not in request:
        return {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32600, 'message': 'Solicitud JSON-RPC inválida.'}}
    request_id = request['id']
    method, params = request.get('method'), request.get('params', {})
    try:
        if not isinstance(params, dict):
            raise EngineError('INVALID_PARAMETERS', 'params debe ser un objeto.')
        if method == 'engine.health':
            result = {'version': VERSION, 'schema_version': SCHEMA, 'protocol_version': '1.0.0'}
        elif method == 'nodes.list':
            result = NODES
        elif method == 'project.validate':
            validate_project(params.get('project'))
            result = {'valid': True}
        elif method == 'worldbank.indicators':
            from .worldbank_catalog import search_indicators
            result = search_indicators(params)
        elif method == 'run.start':
            result = execute(params.get('project'))
        else:
            return {'jsonrpc': '2.0', 'id': request_id, 'error': {'code': -32601, 'message': 'Método desconocido.'}}
        return {'jsonrpc': '2.0', 'id': request_id, 'result': result}
    except EngineError as exc:
        return {'jsonrpc': '2.0', 'id': request_id, 'error': {'code': -32602, 'message': str(exc), 'data': {'code': exc.code, 'node_id': exc.node_id}}}
    except Exception:
        return {'jsonrpc': '2.0', 'id': request_id, 'error': {'code': -32603, 'message': 'Error interno del motor.'}}


def main():
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
        print(canonical(response), flush=True)


if __name__ == '__main__':
    main()
