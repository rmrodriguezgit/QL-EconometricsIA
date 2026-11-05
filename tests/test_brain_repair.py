"""Cerebro IA repara el flujo actual (brain.repair) sin crear un blueprint nuevo."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))

from quantlabs.brain.repair import Repairer, repair, safe_name  # noqa: E402
from quantlabs.brain.service import dispatch  # noqa: E402
from quantlabs.core import EngineError, execute  # noqa: E402


def node(id, kind, parameters, x=0):
    return {'id': id, 'type': kind, 'node_version': '1.0.0', 'position': {'x': x, 'y': 0}, 'parameters': parameters}


def csv(id, text):
    return node(id, 'csv', {'content': text, 'delimiter': ','})


def edge(source, target, port, source_port='data'):
    return {'id': f'{source}-{target}-{port}', 'source': source, 'source_port': source_port, 'target': target, 'target_port': port}


def project(nodes, edges):
    return {'schema_version': '1.0.0', 'app_version': '0.16.0', 'title': 'Reparar', 'nodes': nodes, 'edges': edges}


RATE = 'año,tasa\n2000,1.5\n2001,2.5\n2002,3\n'
CONS = 'periodo,consumo\n2001,5\n2002,6\n2003,7\n'


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'QL_BRAIN_DIR': self.folder.name, 'QL_BRAIN_OLLAMA_URL': 'http://127.0.0.1:9'})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.folder.cleanup()

    def join(self, **params):
        base = {'left_key': 'año', 'left_value': 'tasa', 'left_name': 'tasa', 'right_key': 'periodo', 'right_value': 'consumo', 'right_name': 'consumo'}
        return project([csv('a', RATE), csv('b', CONS), node('j', 'join_series', {**base, **params}, 1)],
                       [edge('a', 'j', 'left'), edge('b', 'j', 'right')])

    def test_safe_name(self):
        self.assertEqual(safe_name('tasa de interés'), 'tasa_de_interes')
        self.assertEqual(safe_name('2020 PIB'), 'v_2020_PIB')
        self.assertEqual(safe_name('periodo'), 'periodo_valor')
        self.assertEqual(safe_name('¿?', 'serie'), 'serie')

    def test_invalid_output_names_are_fixed(self):
        broken = self.join(left_name='tasa de interés', right_name='periodo')
        self.assertEqual(execute(broken)['nodes']['j']['status'], 'failed')
        result = dispatch('brain.repair', {'project': broken})
        self.assertEqual(result['status'], 'succeeded', result['unresolved'])
        params = result['project']['nodes'][2]['parameters']
        self.assertEqual((params['left_name'], params['right_name']), ('tasa_de_interes', 'consumo'))
        self.assertEqual(broken['nodes'][2]['parameters']['left_name'], 'tasa de interés')  # el original no se toca
        self.assertEqual([n['id'] for n in result['project']['nodes']], ['a', 'b', 'j'])  # mismos nodos: no es un blueprint nuevo

    def test_repeated_names_and_missing_columns(self):
        result = repair({'project': self.join(left_key='periodo', left_value='valor', left_name='x', right_name='x')})
        self.assertEqual(result['status'], 'succeeded', result['unresolved'])
        params = result['project']['nodes'][2]['parameters']
        self.assertEqual((params['left_key'], params['left_value']), ('año', 'tasa'))
        self.assertNotEqual(params['left_name'], params['right_name'])
        self.assertTrue(all(change['reason'] for change in result['changes']))

    def test_empty_input_connects_distinct_producer_only(self):
        broken = self.join()
        broken['edges'] = [edge('a', 'j', 'left')]
        result = repair({'project': broken})
        self.assertEqual(result['status'], 'succeeded', result['unresolved'])
        self.assertIn(('b', 'right'), {(e['source'], e['target_port']) for e in result['project']['edges']})
        alone = project([csv('a', RATE), node('j', 'join_series', {}, 1)], [edge('a', 'j', 'left')])
        result = repair({'project': alone})
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(any('right' in item['message'] for item in result['unresolved']))
        self.assertNotIn(('a', 'right'), {(e['source'], e['target_port']) for e in result['project']['edges']})

    def test_no_time_column_is_left_to_the_user(self):
        broken = self.join()
        broken['nodes'][1]['parameters']['content'] = 'x,consumo\n1,5\n2,6\n'
        broken['nodes'][2]['parameters']['right_key'] = 'periodo'
        result = repair({'project': broken})
        self.assertTrue(any('año o fecha' in item['message'] for item in result['unresolved']))

    def test_numeric_range_and_wrong_edges(self):
        flow = project([csv('a', 'x,y\n' + '\n'.join(f'{i},{2 * i}' for i in range(60))), node('s', 'split', {'fraction': 2.0, 'method': 'temporal', 'seed': 42}, 1),
                        node('d', 'describe', {}, 2)],
                       [edge('a', 's', 'data'), edge('s', 'd', 'data', 'train'), edge('a', 'd', 'nope')])
        result = repair({'project': flow})
        self.assertEqual(result['status'], 'succeeded', result['unresolved'])
        self.assertEqual(result['project']['nodes'][1]['parameters']['fraction'], 0.9)
        self.assertEqual(len(result['project']['edges']), 2)

    def test_variadic_extra_inputs_trimmed_and_world_bank_aliases(self):
        broken = self.join(extra_inputs=2)
        result = repair({'project': broken})
        self.assertEqual(result['project']['nodes'][2]['parameters']['extra_inputs'], 0)
        repairer = Repairer(project([node('w', 'worldbank_multi', {'countries': 'USA', 'indicators': 'FR.INR.LEND: tasa préstamo\nNY.GDP.MKTP.KD.ZG: periodo', 'start': 2000, 'end': 2001})], []))
        self.assertTrue(repairer.fix_names(repairer.nodes['w']))
        self.assertEqual(repairer.nodes['w']['parameters']['indicators'], 'FR.INR.LEND: tasa_prestamo\nNY.GDP.MKTP.KD.ZG: periodo_valor')

    def test_rejects_unknown_nodes(self):
        with self.assertRaises(EngineError):
            repair({'project': project([node('z', 'codigo_libre', {})], [])})


if __name__ == '__main__':
    unittest.main()
