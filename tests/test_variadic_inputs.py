"""Entradas variables («+» en la tarjeta): unir N series y comparar N modelos."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))

from quantlabs.core import EngineError, NODE_CATALOG, execute, node_inputs  # noqa: E402


def node(id, kind, parameters, x=0):
    return {'id': id, 'type': kind, 'node_version': '1.0.0', 'position': {'x': x, 'y': 0}, 'parameters': parameters}


def csv(id, text):
    return node(id, 'csv', {'content': text, 'delimiter': ','})


def edge(source, target, port, source_port='data'):
    return {'id': f'{source}-{target}-{port}', 'source': source, 'source_port': source_port, 'target': target, 'target_port': port}


def project(nodes, edges):
    return {'schema_version': '1.0.0', 'app_version': '0.15.0', 'title': 'Entradas variables', 'nodes': nodes, 'edges': edges}


class VariadicCatalogTests(unittest.TestCase):
    def test_only_join_and_compare_declare_extra_inputs(self):
        self.assertEqual(sorted(k for k, d in NODE_CATALOG.items() if 'variadic' in d), ['compare_models', 'join_series'])
        ports = node_inputs(node('j', 'join_series', {'extra_inputs': 2}))
        self.assertEqual(list(ports), ['left', 'right', 'serie_3', 'serie_4'])
        self.assertEqual(list(node_inputs(node('c', 'compare_models', {'extra_inputs': 1}))), ['first', 'second', 'data', 'modelo_3'])

    def test_bounds_and_non_variadic_nodes(self):
        for bad in (-1, 7, 1.5, True, '2'):
            with self.assertRaises(EngineError):
                node_inputs(node('j', 'join_series', {'extra_inputs': bad}))
        with self.assertRaises(EngineError):
            node_inputs(node('d', 'describe', {'extra_inputs': 1}))


class JoinSeriesTests(unittest.TestCase):
    def setUp(self):
        self.sources = [csv('a', 'periodo,valor\n2000,1\n2001,2\n'), csv('b', 'año,v\n2001,5\n2002,6\n'),
                        csv('c', 'periodo,valor\n2000,9\n2003,7\n'), csv('d', 'periodo,valor\n2002,4\n')]

    def build(self, extra, ports, **params):
        join = node('j', 'join_series', {'extra_inputs': extra, 'left_name': 'a', 'right_key': 'año', 'right_value': 'v', 'right_name': 'b',
                                         'serie_3_name': 'c', 'serie_4_name': 'd', **params}, 1)
        return project([*self.sources, join], [edge(s, 'j', p) for s, p in ports])

    def test_four_series_outer_join_matches_pandas(self):
        run = execute(self.build(2, [('a', 'left'), ('b', 'right'), ('c', 'serie_3'), ('d', 'serie_4')]))
        result = run['nodes']['j']
        self.assertEqual(result['status'], 'succeeded', result.get('error'))
        frames = [pd.DataFrame({'periodo': [2000, 2001], 'a': [1, 2]}), pd.DataFrame({'periodo': [2001, 2002], 'b': [5, 6]}),
                  pd.DataFrame({'periodo': [2000, 2003], 'c': [9, 7]}), pd.DataFrame({'periodo': [2002], 'd': [4]})]
        expected = frames[0]
        for frame in frames[1:]:
            expected = expected.merge(frame, on='periodo', how='outer', sort=True)
        self.assertEqual(result['result']['columns'], ['periodo', 'a', 'b', 'c', 'd'])
        self.assertEqual(result['result']['alignment']['rows'], len(expected))
        self.assertEqual([item['port'] for item in result['result']['alignment']['inputs']], ['left', 'right', 'serie_3', 'serie_4'])

    def test_declared_port_must_be_connected_and_undeclared_rejected(self):
        with self.assertRaises(EngineError):
            execute(self.build(2, [('a', 'left'), ('b', 'right'), ('c', 'serie_3')]))
        with self.assertRaises(EngineError):
            execute(self.build(0, [('a', 'left'), ('b', 'right'), ('c', 'serie_3')]))

    def test_duplicated_names_fail(self):
        run = execute(self.build(1, [('a', 'left'), ('b', 'right'), ('c', 'serie_3')], serie_3_name='a'))
        self.assertEqual(run['nodes']['j']['status'], 'failed')
        self.assertIn('distintos', run['nodes']['j']['error']['message'])

    def test_two_inputs_still_work(self):
        run = execute(self.build(0, [('a', 'left'), ('b', 'right')]))
        self.assertEqual(run['nodes']['j']['result']['columns'], ['periodo', 'a', 'b'])


class CompareModelsTests(unittest.TestCase):
    def test_three_models_rmse_on_common_data(self):
        rng = np.random.default_rng(3)
        x1, x2 = rng.normal(size=80), rng.normal(size=80)
        y = 1 + 2 * x1 - x2 + rng.normal(size=80)
        text = 'x1,x2,y\n' + '\n'.join(f'{a},{b},{c}' for a, b, c in zip(x1, x2, y))
        nodes = [csv('d', text),
                 node('m1', 'ols', {'x': 'x1', 'y': 'y', 'covariance': 'nonrobust'}, 1),
                 node('m2', 'multiple_ols', {'features': 'x1,x2', 'y': 'y', 'covariance': 'nonrobust'}, 1),
                 node('m3', 'ols', {'x': 'x2', 'y': 'y', 'covariance': 'nonrobust'}, 1),
                 node('c', 'compare_models', {'extra_inputs': 1}, 2)]
        edges = [edge('d', m, 'data') for m in ('m1', 'm2', 'm3')] + [edge('m1', 'c', 'first', 'model'), edge('m2', 'c', 'second', 'model'),
                                                                     edge('m3', 'c', 'modelo_3', 'model'), edge('d', 'c', 'data')]
        run = execute(project(nodes, edges))
        result = run['nodes']['c']
        self.assertEqual(result['status'], 'succeeded', result.get('error'))
        rows = result['result']['tables'][0]['rows']
        self.assertEqual(len(rows), 3)
        X = np.column_stack([np.ones(80), x1, x2])
        rmse = np.sqrt(np.mean((y - X @ np.linalg.lstsq(X, y, rcond=None)[0]) ** 2))
        self.assertAlmostEqual(rows[1][3], rmse, places=8)
        self.assertLess(rows[1][3], min(rows[0][3], rows[2][3]))


if __name__ == '__main__':
    unittest.main()
