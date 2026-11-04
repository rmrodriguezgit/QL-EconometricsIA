import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))

from quantlabs.core import NODE_CATALOG, EngineError, execute  # noqa: E402
from quantlabs.gap_tools import GAP_TOOLS  # noqa: E402
from quantlabs.tools import run_tool, synthetic  # noqa: E402


def metric(result, label):
    return next(item['value'] for item in result['metrics'] if item['label'] == label)


def frame(scenario, n=300, seed=7):
    return synthetic({'scenario': scenario, 'n': n, 'seed': seed})


class RegistryTests(unittest.TestCase):
    def test_every_gap_tool_is_registered_with_references(self):
        for kind in GAP_TOOLS:
            self.assertIn(kind, NODE_CATALOG)
            self.assertTrue(NODE_CATALOG[kind]['references'])
            for key, options in NODE_CATALOG[kind].get('choices', {}).items():
                self.assertIn(NODE_CATALOG[kind]['defaults'][key], options)

    def test_seasonal_scenario(self):
        data = frame('seasonal', 60)
        self.assertEqual(list(data.columns), ['periodo', 'ventas'])


class InferenceTests(unittest.TestCase):
    def test_sample_size_matches_closed_form(self):
        result, _ = run_tool('sample_size', {}, {'target': 'proporcion', 'confidence': 0.95, 'margin': 0.05, 'proportion': 0.5, 'population_size': 0})
        self.assertEqual(metric(result, 'n_requerida'), 385)
        result, _ = run_tool('sample_size', {}, {'target': 'proporcion', 'confidence': 0.95, 'margin': 0.05, 'proportion': 0.5, 'population_size': 1000})
        self.assertEqual(metric(result, 'n_requerida'), 278)
        result, _ = run_tool('sample_size', {}, {'target': 'media', 'confidence': 0.95, 'margin': 1, 'sd': 10, 'population_size': 0})
        self.assertEqual(metric(result, 'n_requerida'), 385)

    def test_multiple_testing_adjusts_pvalues(self):
        rng = np.random.default_rng(1)
        data = pd.DataFrame({'a': rng.normal(0, 1, 40), 'b': rng.normal(0.8, 1, 40), 'c': rng.normal(0, 1, 40)})
        result, _ = run_tool('multiple_testing', {'data': data}, {'columns': 'a,b,c', 'mu': 0, 'method': 'bonferroni', 'alpha': 0.05})
        rows = result['tables'][0]['rows']
        raw = stats.ttest_1samp(data['b'], 0).pvalue
        self.assertAlmostEqual(rows[1][4], raw)
        self.assertAlmostEqual(rows[1][5], min(1, 3 * raw))
        self.assertGreaterEqual(metric(result, 'rechazos_sin_corregir'), metric(result, 'rechazos_corregidos'))

    def test_prediction_interval_is_wider_than_confidence_interval(self):
        data = frame('regression')
        result, outputs = run_tool('prediction_interval', {'data': data}, {'x': 'ingreso', 'y': 'consumo', 'confidence': 0.95})
        for row in result['tables'][0]['rows']:
            self.assertLess(row[4], row[2])
            self.assertGreater(row[5], row[3])
        reference = sm.OLS(data['consumo'], sm.add_constant(data[['ingreso']])).fit().get_prediction(sm.add_constant(data[['ingreso']])).summary_frame()
        np.testing.assert_allclose(outputs['data']['pi_superior'], reference['obs_ci_upper'])
        self.assertGreater(metric(result, 'cobertura_en_muestra'), 0.9)

    def test_chow_detects_break_and_not_otherwise(self):
        rng = np.random.default_rng(3)
        x = rng.normal(size=200)
        y = np.where(np.arange(200) < 100, 1 + x, 3 - x) + rng.normal(0, .5, 200)
        result, _ = run_tool('chow', {'data': pd.DataFrame({'x': x, 'y': y})}, {'features': 'x', 'y': 'y', 'break_fraction': 0.5})
        self.assertLess(metric(result, 'p_valor'), 1e-6)
        result, _ = run_tool('chow', {'data': frame('regression', 200)}, {'features': 'ingreso', 'y': 'consumo', 'break_fraction': 0.5})
        self.assertGreater(metric(result, 'p_valor'), 0.01)

    def test_dummies_build_indicator_and_interaction(self):
        data = pd.DataFrame({'x': [-1.0, 0.5, 2.0, np.nan]})
        _, outputs = run_tool('dummies', {'data': data}, {'column': 'x', 'threshold': 0, 'x': 'x', 'output': 'alto'})
        self.assertEqual(outputs['data']['d_alto'].tolist()[:3], [0.0, 1.0, 1.0])
        self.assertTrue(np.isnan(outputs['data']['d_alto'].iloc[3]))
        self.assertEqual(outputs['data']['x_x_d_alto'].tolist()[:3], [-0.0, 0.5, 2.0])


class TimeSeriesTests(unittest.TestCase):
    def test_seasonal_decompose_recovers_amplitude(self):
        result, outputs = run_tool('seasonal_decompose', {'data': frame('seasonal', 120)}, {'column': 'ventas', 'period': 12, 'model': 'additive'})
        self.assertAlmostEqual(metric(result, 'amplitud_estacional'), 24, delta=4)
        self.assertGreater(metric(result, 'fuerza_estacional'), 0.8)
        self.assertIn('ventas_tendencia', outputs['data'])

    def test_sarima_forecast_interval(self):
        result, _ = run_tool('sarima', {'data': frame('seasonal', 96)}, {'column': 'ventas', 'p': 1, 'd': 1, 'q': 0, 'P': 1, 'D': 0, 'Q': 0, 's': 12, 'horizon': 6, 'confidence': 0.9})
        rows = result['tables'][1]['rows']
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(row[2] < row[1] < row[3] for row in rows))
        self.assertGreater(rows[-1][3] - rows[-1][2], rows[0][3] - rows[0][2])

    def test_var_granger_direction(self):
        rng = np.random.default_rng(5)
        x = rng.normal(size=300)
        y = np.zeros(300)
        for t in range(1, 300):
            y[t] = 0.8 * x[t - 1] + rng.normal(0, .3)
        data = pd.DataFrame({'periodo': np.arange(300), 'x': x, 'y': y})
        result, _ = run_tool('var', {'data': data}, {'columns': 'x,y', 'lags': 1, 'horizon': 4})
        granger = {(row[0], row[1]): row[3] for row in result['tables'][0]['rows']}
        self.assertLess(granger[('x', 'y')], 1e-6)
        self.assertGreater(granger[('y', 'x')], 0.01)

    def test_johansen_finds_one_relation(self):
        result, _ = run_tool('johansen', {'data': frame('cointegrated', 400)}, {'columns': 'x,y', 'det_order': 0, 'k_ar_diff': 1})
        self.assertEqual(metric(result, 'rango_cointegracion'), 1)


class ModelTests(unittest.TestCase):
    def test_wls_matches_statsmodels_and_feeds_evaluate(self):
        data = frame('hetero', 400)
        result, outputs = run_tool('wls', {'data': data}, {'features': 'x', 'y': 'y', 'method': 'inversa_x2'})
        expected = sm.WLS(data['y'], sm.add_constant(data[['x']]), weights=1 / data['x'] ** 2).fit()
        np.testing.assert_allclose(outputs['model'].fit.params, expected.params)
        evaluation, _ = run_tool('evaluate', {'model': outputs['model'], 'data': data}, {})
        self.assertEqual(evaluation['kind'], 'analysis')
        fgls, _ = run_tool('wls', {'data': data}, {'features': 'x', 'y': 'y', 'method': 'fgls'})
        self.assertEqual(fgls['tables'][0]['rows'][1][0], 'x')

    def test_lasso_drops_irrelevant_feature(self):
        rng = np.random.default_rng(9)
        data = pd.DataFrame(rng.normal(size=(300, 4)), columns=['a', 'b', 'ruido1', 'ruido2'])
        data['y'] = 2 * data['a'] - data['b'] + rng.normal(0, .5, 300)
        result, _ = run_tool('regularized', {'data': data}, {'features': 'a,b,ruido1,ruido2', 'y': 'y', 'method': 'lasso', 'folds': 5, 'seed': 1})
        states = {row[0]: row[3] for row in result['tables'][0]['rows']}
        self.assertEqual(states['a'], 'Incluida')
        self.assertGreater(metric(result, 'R2_validacion_cruzada'), 0.9)
        ridge, _ = run_tool('regularized', {'data': data}, {'features': 'a,b', 'y': 'y', 'method': 'ridge'})
        self.assertGreater(metric(ridge, 'alpha'), 0)

    def test_cluster_selection_prefers_true_k(self):
        result, _ = run_tool('cluster_selection', {'data': frame('clusters', 300)}, {'columns': 'x1,x2', 'max_k': 6, 'seed': 1})
        self.assertEqual(len(result['tables'][0]['rows']), 5)
        self.assertIn(metric(result, 'k_sugerido'), [2, 3, 4])

    def test_invalid_choices_are_rejected(self):
        with self.assertRaises(EngineError):
            run_tool('regularized', {'data': frame('multiple')}, {'features': 'x,z', 'y': 'y', 'method': 'bayes'})


class GraphTests(unittest.TestCase):
    def test_new_tools_run_inside_a_connected_project(self):
        project = {'schema_version': '1.0.0', 'app_version': '0.10.0', 'title': 'Estacional', 'nodes': [
            {'id': 'd', 'type': 'synthetic', 'node_version': '1.0.0', 'parameters': {'scenario': 'seasonal', 'n': 96, 'seed': 1}, 'position': {'x': 0, 'y': 0}},
            {'id': 'dec', 'type': 'seasonal_decompose', 'node_version': '1.0.0', 'parameters': {}, 'position': {'x': 300, 'y': 0}},
            {'id': 'sar', 'type': 'sarima', 'node_version': '1.0.0', 'parameters': {'horizon': 3}, 'position': {'x': 600, 'y': 0}},
            {'id': 'n', 'type': 'sample_size', 'node_version': '1.0.0', 'parameters': {}, 'position': {'x': 0, 'y': 200}}],
            'edges': [{'id': 'e1', 'source': 'd', 'source_port': 'data', 'target': 'dec', 'target_port': 'data'},
                      {'id': 'e2', 'source': 'dec', 'source_port': 'data', 'target': 'sar', 'target_port': 'data'}]}
        run = execute(project)
        self.assertEqual(run['status'], 'succeeded', run['nodes'])
        self.assertIn('ventas_estacional', run['nodes']['dec']['result']['output_previews']['data']['columns'])


if __name__ == '__main__':
    unittest.main()
