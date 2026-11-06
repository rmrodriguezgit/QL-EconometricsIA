import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))

from quantlabs.__main__ import dispatch  # noqa: E402
from quantlabs.brain import interpret as module  # noqa: E402
from quantlabs.brain.interpret import digest, interpret, rules, unverified_numbers  # noqa: E402
from quantlabs.core import execute  # noqa: E402
from quantlabs.projects import dispatch_files  # noqa: E402


def run_example(example_id):
    project = dispatch_files('examples.read', {'id': example_id})['project']
    run = execute(project)
    return project, run


def node_result(project, run, kind):
    node = next(n for n in project['nodes'] if n['type'] == kind)
    return node, run['nodes'][node['id']]['result']


class InterpretCase(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        # Memoria aislada y Ollama en un puerto cerrado: las pruebas no dependen de un modelo instalado.
        self.env = patch.dict(os.environ, {'QL_BRAIN_DIR': self.folder.name, 'QL_BRAIN_OLLAMA_URL': 'http://127.0.0.1:9'})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.folder.cleanup()


class RulesTests(InterpretCase):
    @classmethod
    def setUpClass(cls):
        cls.c01 = run_example('C01')
        cls.c10 = run_example('C10')

    def test_ols_reads_slope_r2_and_causality(self):
        node, result = node_result(*self.c01, 'ols')
        reading, _ = rules('ols', result, node['parameters'])
        slope = next(c for c in result['coefficients'] if c['term'] != 'const')
        self.assertIn(f"{result['r_squared'] * 100:.1f}".rstrip('0').rstrip('.'), reading['summary'])
        self.assertTrue(any(str(slope['term']) in f and ('aumenta' if slope['estimate'] > 0 else 'disminuye') in f for f in reading['findings']))
        self.assertTrue(any('causal' in c for c in reading['cautions']))
        self.assertTrue(reading['next_steps'])

    def test_diagnostics_compare_p_values_with_alpha(self):
        node, result = node_result(*self.c10, 'diagnostics')
        reading, _ = rules('diagnostics', result, node['parameters'])
        metrics = {m['label']: m['value'] for m in result['metrics']}
        bp = next(f for f in reading['findings'] if f.startswith('Breusch-Pagan'))
        self.assertIn('se rechaza' if metrics['p_BP'] < 0.05 else 'no se rechaza', bp)
        self.assertTrue(any('Durbin-Watson' in f for f in reading['findings']))
        # Los avisos de deprecación de librerías no son advertencias del resultado.
        self.assertFalse(any('currently returns' in c for c in reading['cautions']))

    def test_alpha_from_node_parameters(self):
        node, result = node_result(*self.c10, 'multiple_ols')
        strict, _ = rules('multiple_ols', result, {**node['parameters'], 'alpha': 0.0000001})
        self.assertTrue(any('α = 1e-07' in f for f in strict['findings']))

    def test_every_offline_example_has_a_reading(self):
        items = dispatch_files('examples.list', {})['items']
        online = {'worldbank', 'worldbank_multi', 'fred', 'yfinance'}
        checked = set()
        for item in items:
            project = dispatch_files('examples.read', {'id': item['id']})['project']
            if any(n['type'] in online for n in project['nodes']):
                continue
            run = execute(project)
            for node in project['nodes']:
                result = (run['nodes'].get(node['id']) or {}).get('result')
                if not result or node['type'] in checked:
                    continue
                checked.add(node['type'])
                reading, _ = rules(node['type'], result, node['parameters'])
                self.assertTrue(reading['summary'].strip(), node['type'])
                self.assertTrue(reading['findings'] or reading['cautions'], node['type'])
        self.assertGreater(len(checked), 40)


class DigestTests(InterpretCase):
    def test_dataset_digest_has_aggregates_not_rows(self):
        project, run = run_example('C01')
        node, result = node_result(project, run, 'synthetic')
        d = digest('synthetic', result, node['parameters'])
        text = json.dumps(d, default=str)
        self.assertNotIn('records', text)
        first = result['records'][0]
        # Ningún valor de fila individual se copia tal cual al resumen.
        self.assertFalse(all(str(v) in text for v in first.values() if isinstance(v, float)))
        self.assertEqual(d['tables'][0]['columns'][0], 'Columna')

    def test_tables_are_truncated(self):
        result = {'kind': 'analysis', 'metrics': [], 'tables': [{'title': 'T', 'columns': list('abcdefghij'), 'rows': [[i] * 10 for i in range(40)]}]}
        table = digest('acf', result)['tables'][0]
        self.assertEqual((len(table['rows']), len(table['columns']), len(table['rows'][0]), table['total_rows']), (12, 8, 8, 40))


class EngineTests(InterpretCase):
    def setUp(self):
        super().setUp()
        project, run = run_example('C01')
        self.node, self.result = node_result(project, run, 'ols')

    def test_auto_falls_back_to_rules_without_ollama(self):
        out = interpret({'node_type': 'ols', 'result': self.result, 'parameters': self.node['parameters']})
        self.assertEqual(out['engine'], 'rules')
        self.assertIn('Ollama', out['fallback_reason'])
        self.assertTrue(out['summary'])

    def test_ollama_engine_reports_unavailable(self):
        response = dispatch({'jsonrpc': '2.0', 'id': 1, 'method': 'brain.interpret',
                             'params': {'node_type': 'ols', 'result': self.result, 'engine': 'ollama'}})
        self.assertEqual(response['error']['data']['code'], 'BRAIN_UNAVAILABLE')

    def test_model_reading_is_used_and_numbers_are_checked(self):
        slope = next(c['estimate'] for c in self.result['coefficients'] if c['term'] != 'const')
        reply = {'summary': f'La pendiente es {slope:.4f} y el R² es {self.result["r_squared"] * 100:.1f} %.',
                 'findings': ['El efecto es 123.45 veces mayor.'], 'cautions': ['Asociación, no causalidad.'], 'next_steps': ['Diagnósticos.']}
        with patch.object(module.llm, 'available_models', return_value=['qwen3.5:4b']), \
                patch.object(module.llm, '_request', return_value={'message': {'content': json.dumps(reply)}}) as request:
            out = interpret({'node_type': 'ols', 'result': self.result, 'parameters': self.node['parameters']})
        self.assertEqual((out['engine'], out['model']), ('ollama', 'qwen3.5:4b'))
        self.assertEqual(out['unverified'], ['123.45'])
        self.assertTrue(out['base']['summary'])
        sent = request.call_args[0][1]['messages'][1]['content']
        self.assertNotIn('records', sent)
        self.assertNotIn('fitted', sent)

    def test_invalid_model_reply_falls_back(self):
        with patch.object(module.llm, 'available_models', return_value=['qwen3.5:4b']), \
                patch.object(module.llm, '_request', return_value={'message': {'content': 'sin json'}}):
            out = interpret({'node_type': 'ols', 'result': self.result})
        self.assertEqual(out['engine'], 'rules')
        self.assertIn('JSON', out['fallback_reason'])

    def test_rejects_bad_requests(self):
        for params in ({'node_type': 'nope', 'result': self.result}, {'node_type': 'ols', 'result': {}},
                       {'node_type': 'ols', 'result': self.result, 'engine': 'gpt'}):
            response = dispatch({'jsonrpc': '2.0', 'id': 1, 'method': 'brain.interpret', 'params': params})
            self.assertEqual(response['error']['data']['code'], 'INVALID_PARAMETERS')

    def test_unverified_numbers_rules(self):
        self.assertEqual(unverified_numbers(['R² de 36.9 % y pendiente 0.84, año 2020, 3 pasos'], [0.3691, 0.8356]), [])
        self.assertEqual(unverified_numbers(['pendiente 0.91'], [0.8356]), ['0.91'])


if __name__ == '__main__':
    unittest.main()
