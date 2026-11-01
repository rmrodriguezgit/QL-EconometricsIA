"""Scientific fixtures and invalid graph tests, no network required."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
import numpy as np
import pandas as pd
from quantlabs.core import EngineError, describe, execute, ols, simulate, validate_project, csv_data
from quantlabs.__main__ import dispatch

class EngineTests(unittest.TestCase):
    def setUp(self):
        self.project = json.loads((ROOT / 'examples/ingreso-consumo.json').read_text())

    def test_complete_example_and_reproducible_fingerprints(self):
        first, second = execute(self.project), execute(self.project)
        self.assertEqual(first['status'], 'succeeded')
        self.assertEqual(first['nodes']['model']['result'], second['nodes']['model']['result'])
        self.assertEqual(first['manifest']['sources']['data']['data_sha256'], second['manifest']['sources']['data']['data_sha256'])
        self.assertNotEqual(first['run_id'], second['run_id'])
        self.assertIn('statsmodels', first['manifest']['dependencies'])

    def test_known_ols_coefficients_and_classical_standard_errors(self):
        # x=0..4, residuals=[1,-2,2,-2,1] orthogonal to intercept and x.
        x = np.arange(5, dtype=float)
        residuals = np.array([1, -2, 2, -2, 1], dtype=float)
        frame = pd.DataFrame({'x': x, 'y': 3 + 2 * x + residuals})
        result = ols(frame, {'x': 'x', 'y': 'y', 'covariance': 'nonrobust'})
        self.assertAlmostEqual(result['coefficients'][0]['estimate'], 3)
        self.assertAlmostEqual(result['coefficients'][1]['estimate'], 2)
        self.assertAlmostEqual(result['coefficients'][1]['std_error'], np.sqrt(14 / 3 / 10))
        self.assertEqual(result['n'], 5)

    def test_robust_covariance_preserves_coefficients(self):
        frame, _ = simulate({'n': 80, 'seed': 4})
        robust = ols(frame, {'covariance': 'HC3'})
        classic = ols(frame, {'covariance': 'nonrobust'})
        self.assertEqual([c['estimate'] for c in robust['coefficients']], [c['estimate'] for c in classic['coefficients']])
        self.assertNotEqual(robust['coefficients'][1]['std_error'], classic['coefficients'][1]['std_error'])

    def test_explicit_missing_data_and_sample_standard_deviation(self):
        frame = pd.DataFrame({'x': [1., 2., 3., None], 'y': [2., 3., 4., 5.]})
        row = describe(frame, {})['rows'][0]
        self.assertEqual((row['n'], row['missing'], row['mean'], row['std']), (3, 1, 2, 1))
        with self.assertRaises(EngineError) as caught:
            ols(frame, {'x': 'x', 'y': 'y'})
        self.assertEqual(caught.exception.code, 'INSUFFICIENT_SAMPLE')

    def test_rank_deficient_rejected(self):
        with self.assertRaises(EngineError) as caught:
            ols(pd.DataFrame({'x': [1] * 8, 'y': range(8)}), {'x': 'x', 'y': 'y'})
        self.assertEqual(caught.exception.code, 'RANK_DEFICIENT')

    def test_duplicate_ids_missing_parent_unknown_node_and_schema(self):
        cases = []
        p = copy.deepcopy(self.project); p['nodes'][1]['id'] = 'data'; cases.append(p)
        p = copy.deepcopy(self.project); p['edges'][0]['source'] = 'absent'; cases.append(p)
        p = copy.deepcopy(self.project); p['nodes'][0]['type'] = '__import__'; cases.append(p)
        p = copy.deepcopy(self.project); p['schema_version'] = '999'; cases.append(p)
        p = copy.deepcopy(self.project); p['edges'] = []; cases.append(p)
        p = copy.deepcopy(self.project); p['edges'][0]['source_port'] = 'summary'; cases.append(p)
        for project in cases:
            with self.subTest(project=project):
                with self.assertRaises(EngineError):
                    validate_project(project)

    def test_branch_failure_skips_only_dependent_nodes(self):
        self.project['nodes'][0]['parameters']['noise'] = -1
        self.project['nodes'].append({'id': 'independent', 'type': 'simulate', 'node_version': '1.0.0', 'parameters': {}, 'position': {'x': 0, 'y': 0}})
        result = execute(self.project)
        self.assertEqual(result['nodes']['data']['status'], 'failed')
        self.assertEqual(result['nodes']['model']['status'], 'skipped')
        self.assertEqual(result['nodes']['independent']['status'], 'succeeded')

    def test_csv_does_not_silently_drop_missing_values(self):
        frame, source = csv_data({'content': 'x;y\n1;2\n3;\n', 'delimiter': ';'})
        self.assertEqual(len(frame), 2)
        self.assertTrue(pd.isna(frame.iloc[1]['y']))
        self.assertEqual(source['provider'], 'csv')
        with self.assertRaises(EngineError):
            csv_data({'content': 'x,x\n1,2\n'})

    def test_rpc_errors_and_protocol(self):
        request = {'jsonrpc': '2.0', 'id': 'test', 'method': 'engine.health'}
        self.assertEqual(dispatch(request)['result']['protocol_version'], '1.0.0')
        self.assertEqual(dispatch({**request, 'method': 'bad'})['error']['code'], -32601)
        self.assertEqual(dispatch({**request, 'params': []})['error']['code'], -32602)
        self.assertEqual(dispatch([])['error']['code'], -32600)
        self.assertEqual(dispatch({**request, 'id': {}})['error']['code'], -32600)
        self.assertEqual(dispatch({**request, 'method': []})['error']['code'], -32600)

    def test_stdio_multiple_requests_and_malformed_json(self):
        requests = 'broken\n' + json.dumps({'jsonrpc': '2.0', 'id': 7, 'method': 'engine.health'}) + '\n'
        import os
        process = subprocess.run([sys.executable, '-m', 'quantlabs'], cwd=ROOT,
                                 env={**os.environ, 'PYTHONPATH': str(ROOT / 'engine')},
                                 input=requests, capture_output=True, text=True, check=True, timeout=30)
        first, second = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(first['error']['code'], -32700)
        self.assertEqual(second['id'], 7)
        self.assertIn('result', second)

if __name__ == '__main__':
    unittest.main()
