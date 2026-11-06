"""Red multicapa capa por capa y agente de refuerzo: gradientes, validación de la cadena, entrenamiento y política."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
from quantlabs.core import EngineError, NODE_CATALOG
from quantlabs.deep_tools import DeepNetwork, nn_input, nn_layer, nn_output, nn_train, rl_agent


def build(features, layers, target='y', task='regresion'):
    _, spec = nn_input({'features': ','.join(features), 'standardize': 'si'})
    for layer in layers:
        _, spec = nn_layer({'network': spec}, layer)
    _, spec = nn_output({'network': spec}, {'y': target, 'task': task})
    return spec


class GradientTests(unittest.TestCase):
    def check(self, task, layers):
        rng = np.random.default_rng(0)
        spec = build(['a', 'b'], layers, task=task)
        net = DeepNetwork(spec)
        net.init(rng)
        x = rng.normal(size=(7, 2))
        y = rng.integers(0, 2, 7).astype(float) if task == 'clasificacion' else rng.normal(size=7)
        output, cache = net.forward(x)
        grads = net.gradients(output, y, cache, l2=.01)
        for i, (W, b) in enumerate(net.weights):
            for k, param in enumerate((W, b)):
                numeric = np.zeros_like(param)
                for idx in np.ndindex(param.shape):
                    old = param[idx]
                    param[idx] = old + 1e-6
                    up = net.loss(net.forward(x)[0], y, .01)
                    param[idx] = old - 1e-6
                    down = net.loss(net.forward(x)[0], y, .01)
                    param[idx] = old
                    numeric[idx] = (up - down) / 2e-6
                np.testing.assert_allclose(grads[i][k], numeric, rtol=1e-4, atol=1e-7, err_msg=f'capa {i} parámetro {k}')

    def test_backprop_matches_numeric_gradient(self):
        for activation in ['tanh', 'sigmoide', 'swish', 'elu', 'lineal']:
            with self.subTest(activation=activation):
                self.check('regresion', [{'layer_type': 'densa', 'units': 4, 'activation': activation}, {'layer_type': 'densa', 'units': 3, 'activation': 'tanh'}])
        self.check('clasificacion', [{'layer_type': 'densa', 'units': 5, 'activation': 'tanh'}])

    def test_dropout_mask_is_used_in_backprop(self):
        rng = np.random.default_rng(1)
        spec = build(['a'], [{'layer_type': 'densa', 'units': 6, 'activation': 'tanh'}, {'layer_type': 'dropout', 'rate': .5}])
        net = DeepNetwork(spec)
        net.init(rng)
        x, y = rng.normal(size=(5, 1)), rng.normal(size=5)
        output, cache = net.forward(x, np.random.default_rng(3))
        mask = next(entry[1] for entry in cache if entry[0] == 'dropout')
        grads = net.gradients(output, y, cache, 0)
        # Neuronas apagadas en todas las filas no reciben gradiente en la capa de salida.
        dead = np.all(mask == 0, axis=0)
        np.testing.assert_allclose(grads[-1][0][dead], 0)


class ChainTests(unittest.TestCase):
    def test_architecture_and_parameters(self):
        spec = build(['x1', 'x2', 'x3'], [{'layer_type': 'densa', 'units': 8, 'activation': 'relu'}, {'layer_type': 'dropout', 'rate': .2},
                                          {'layer_type': 'densa', 'units': 4, 'activation': 'tanh'}])
        result, _ = nn_output({'network': {**spec, 'output': None}}, {'y': 'y', 'task': 'regresion'})
        rows = result['tables'][0]['rows']
        self.assertEqual([row[5] for row in rows], [0, 3 * 8 + 8, 0, 8 * 4 + 4, 4 + 1])
        self.assertEqual({m['label']: m['value'] for m in result['metrics']}['parametros'], 73)

    def test_invalid_chains(self):
        _, start = nn_input({'features': 'x'})
        with self.assertRaises(EngineError):
            nn_layer({'network': start}, {'layer_type': 'dropout', 'rate': .2})  # dropout antes de una densa
        with self.assertRaises(EngineError):
            nn_output({'network': start}, {'y': 'y'})  # sin capas intermedias
        spec = build(['x'], [{'layer_type': 'densa', 'units': 2, 'activation': 'relu'}])
        with self.assertRaises(EngineError):
            nn_layer({'network': spec}, {'layer_type': 'densa'})  # capa tras la salida
        with self.assertRaises(EngineError):
            nn_train({'network': start, 'data': pd.DataFrame({'x': range(30), 'y': range(30)})}, {})  # red incompleta
        with self.assertRaises(EngineError):
            nn_output({'network': nn_layer({'network': start}, {'units': 3})[1]}, {'y': 'x'})  # respuesta = entrada
        with self.assertRaises(EngineError):
            nn_layer({'network': start}, {'layer_type': 'densa', 'units': 0})
        layers = start
        for _ in range(12):
            layers = nn_layer({'network': layers}, {'units': 2})[1]
        with self.assertRaises(EngineError):
            nn_layer({'network': layers}, {'units': 2})

    def test_does_not_mutate_upstream_spec(self):
        _, start = nn_input({'features': 'x'})
        nn_layer({'network': start}, {'units': 3})
        self.assertEqual(start['layers'], [])


class TrainingTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(42)
        x = rng.uniform(-3, 3, 500)
        self.frame = pd.DataFrame({'x': x, 'y': np.sin(x) + rng.normal(0, .1, 500)})

    def test_learns_nonlinear_function_reproducibly(self):
        spec = build(['x'], [{'units': 32, 'activation': 'relu'}, {'units': 16, 'activation': 'tanh'}])
        result, outputs = nn_train({'network': spec, 'data': self.frame}, {'epochs': 300, 'seed': 7})
        metrics = {m['label']: m['value'] for m in result['metrics']}
        self.assertGreater(metrics['R2_validacion'], .9)
        again, _ = nn_train({'network': spec, 'data': self.frame}, {'epochs': 300, 'seed': 7})
        self.assertEqual(result['metrics'], again['metrics'])
        model = outputs['model']
        self.assertEqual(model.kind, 'deep_mlp')
        predicted = model.fit.predict(pd.DataFrame({'x': [0., np.pi / 2]}))
        np.testing.assert_allclose(predicted, [0, 1], atol=.15)

    def test_optimizers_and_classification(self):
        rng = np.random.default_rng(0)
        x = rng.normal(size=(400, 2))
        frame = pd.DataFrame({'a': x[:, 0], 'b': x[:, 1], 'c': ((x[:, 0] * x[:, 1]) > 0).astype(float)})
        spec = build(['a', 'b'], [{'units': 16, 'activation': 'tanh'}, {'units': 8, 'activation': 'relu'}], target='c', task='clasificacion')
        for optimizer in ['adam', 'rmsprop', 'sgd']:
            with self.subTest(optimizer=optimizer):
                result, _ = nn_train({'network': spec, 'data': frame}, {'epochs': 400, 'optimizer': optimizer, 'learning_rate': .01 if optimizer != 'sgd' else .05, 'patience': 100})
                self.assertGreater({m['label']: m['value'] for m in result['metrics']}['exactitud_validacion'], .85)
        with self.assertRaises(EngineError):
            nn_train({'network': spec, 'data': frame.assign(c=frame['c'] * 2)}, {})

    def test_missing_columns(self):
        spec = build(['z'], [{'units': 2}])
        with self.assertRaises(EngineError):
            nn_train({'network': spec, 'data': self.frame}, {})


class ReinforcementTests(unittest.TestCase):
    def test_reward_uses_next_return_not_current(self):
        # Rendimientos que alternan: tras un alza viene una baja. Sin mirar el futuro la política óptima es
        # «corto» en el tramo alto y «largo» en el bajo; usar el rendimiento actual daría lo contrario.
        returns = np.tile([.01, -.01], 300)
        result, outputs = rl_agent({'data': pd.DataFrame({'r': returns})}, {'returns': 'r', 'state': 'r', 'bins': 2, 'cost_bps': 0, 'episodes': 100})
        policy = {row[0]: row[-1] for row in result['tables'][1]['rows']}
        self.assertEqual(policy['r: tramo 1/2'], 'largo')
        self.assertEqual(policy['r: tramo 2/2'], 'corto')
        metrics = {m['label']: m['value'] for m in result['metrics']}
        self.assertGreater(metrics['retorno_agente_prueba_%'], 100)
        self.assertEqual(set(outputs['data']['posicion'].unique()) - {-1., 0., 1.}, set())

    def test_costs_and_validation(self):
        frame = pd.DataFrame({'r': np.random.default_rng(0).normal(0, .01, 400)})
        result, _ = rl_agent({'data': frame}, {'returns': 'r', 'state': 'r', 'cost_bps': 500, 'episodes': 50})
        self.assertLessEqual({m['label']: m['value'] for m in result['metrics']}['cambios_de_posicion_prueba'], 2)
        with self.assertRaises(EngineError):
            rl_agent({'data': frame}, {'returns': 'nada'})
        with self.assertRaises(EngineError):
            rl_agent({'data': frame.head(20)}, {'returns': 'r', 'state': 'r'})


class CatalogAndBrainTests(unittest.TestCase):
    def test_nodes_registered_with_network_ports(self):
        self.assertEqual(NODE_CATALOG['nn_layer']['inputs'], {'network': 'Network'})
        self.assertEqual(NODE_CATALOG['nn_train']['inputs'], {'network': 'Network', 'data': 'Dataset'})
        self.assertEqual(NODE_CATALOG['nn_train']['outputs']['model'], 'FittedModel')

    def test_brain_builds_layer_chain(self):
        with tempfile.TemporaryDirectory() as folder:
            os.environ['QL_BRAIN_DIR'] = folder
            from quantlabs.brain.intents import rules_plan
            plan = rules_plan('Entrena una red neuronal profunda con capas de 64, 32 y 16 neuronas tanh')
            tools = [step['tool'] for step in plan['steps']]
            self.assertEqual(tools[tools.index('nn_input'):tools.index('nn_train') + 1], ['nn_input', 'nn_layer', 'nn_layer', 'nn_layer', 'nn_output', 'nn_train'])
            self.assertEqual([s['parameters']['units'] for s in plan['steps'] if s['tool'] == 'nn_layer'], [64, 32, 16])
            self.assertNotIn('mlp', tools)
            self.assertIn('rl_agent', [s['tool'] for s in rules_plan('Agente de aprendizaje por refuerzo con Q-learning')['steps']])


if __name__ == '__main__':
    unittest.main()
