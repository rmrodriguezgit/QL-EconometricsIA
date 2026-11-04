import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))

from quantlabs.core import EngineError  # noqa: E402
from quantlabs.tools import run_tool, synthetic  # noqa: E402


def metric(result, label):
    return next(item['value'] for item in result['metrics'] if item['label'] == label)


class PanelTests(unittest.TestCase):
    def setUp(self):
        self.data = synthetic({'scenario': 'panel', 'n': 600, 'seed': 3})

    def test_fixed_effects_equal_lsdv_and_recover_slope(self):
        result, _ = run_tool('panel', {'data': self.data}, {'entity': 'entidad', 'features': 'x', 'y': 'y', 'covariance': 'nonrobust'})
        row = result['tables'][0]['rows'][0]
        lsdv = sm.OLS(self.data['y'], pd.concat([self.data[['x']], pd.get_dummies(self.data['entidad'], dtype=float)], axis=1)).fit()
        self.assertAlmostEqual(row[2], lsdv.params['x'], places=10)
        self.assertAlmostEqual(row[3], lsdv.bse['x'], places=8)
        self.assertAlmostEqual(row[2], 1.5, delta=0.1)
        self.assertGreater(row[1], 1.7)  # MCO agrupado sesgado por el efecto correlacionado

    def test_hausman_rejects_correlated_effects_and_not_random_ones(self):
        result, _ = run_tool('panel', {'data': self.data}, {'entity': 'entidad', 'features': 'x', 'y': 'y'})
        self.assertLess(metric(result, 'p_Hausman'), 0.01)
        rejections, slopes = 0, []
        for seed in range(40):  # bajo H₀ (efectos aleatorios) la tasa de rechazo debe rondar el 5 %
            rng = np.random.default_rng(seed)
            entity = np.repeat(np.arange(60), 10)
            x = rng.normal(size=600)
            y = 1 + 1.5 * x + rng.normal(0, 2, 60)[entity] + rng.normal(size=600)
            random, _ = run_tool('panel', {'data': pd.DataFrame({'id': entity, 'x': x, 'y': y})}, {'entity': 'id', 'features': 'x', 'y': 'y'})
            p = metric(random, 'p_Hausman')
            rejections += p is not None and p < 0.05
            slopes.append(random['tables'][0]['rows'][0][4])
        self.assertLessEqual(rejections / 40, 0.15)
        self.assertAlmostEqual(np.mean(slopes), 1.5, delta=0.03)
        self.assertGreater(metric(random, 'rho'), 0.5)

    def test_time_invariant_regressor_is_rejected(self):
        data = self.data.assign(fijo=self.data['entidad'] * 1.0)
        with self.assertRaises(EngineError):
            run_tool('panel', {'data': data}, {'entity': 'entidad', 'features': 'x,fijo', 'y': 'y'})


class VolatilityTests(unittest.TestCase):
    def test_egarch_and_gjr_fit_and_feed_diagnostics(self):
        data = synthetic({'scenario': 'garch', 'n': 800, 'seed': 2})
        result, outputs = run_tool('egarch', {'data': data}, {'column': 'retorno', 'vol': 'EGARCH', 'p': 1, 'o': 1, 'q': 1, 'dist': 'normal'})
        self.assertIn('gamma[1]', [row[0] for row in result['tables'][0]['rows']])
        diagnostic, _ = run_tool('diagnostics', {'model': outputs['model']}, {})
        self.assertIn('p_ARCH_LM', [m['label'] for m in diagnostic['metrics']])
        gjr, _ = run_tool('egarch', {'data': data}, {'column': 'retorno', 'vol': 'GJR-GARCH', 'dist': 't'})
        self.assertIn('nu', [row[0] for row in gjr['tables'][0]['rows']])


class SelectionTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(8)
        self.data = pd.DataFrame(rng.normal(size=(400, 5)), columns=['a', 'b', 'r1', 'r2', 'r3'])
        self.data['y'] = 1 + 2 * self.data['a'] - 1.5 * self.data['b'] + rng.normal(size=400)

    def test_forward_and_backward_keep_true_regressors(self):
        for direction in ['forward', 'backward']:
            result, outputs = run_tool('stepwise', {'data': self.data}, {'features': 'a,b,r1,r2,r3', 'y': 'y', 'direction': direction, 'criterion': 'bic'})
            self.assertEqual(set(outputs['model'].features), {'a', 'b'}, direction)
        evaluation, _ = run_tool('diagnostics', {'model': outputs['model']}, {})
        self.assertIn('p_BP', [m['label'] for m in evaluation['metrics']])

    def test_forward_first_step_minimises_aic(self):
        result, _ = run_tool('stepwise', {'data': self.data}, {'features': 'a,b,r1', 'y': 'y', 'direction': 'forward', 'criterion': 'aic'})
        path = result['tables'][-1]['rows']
        best = min(['a', 'b', 'r1'], key=lambda c: sm.OLS(self.data['y'], sm.add_constant(self.data[[c]])).fit().aic)
        self.assertEqual(path[1][1], best)


class MarginalAndBootstrapTests(unittest.TestCase):
    def test_logit_average_marginal_effect_matches_statsmodels(self):
        data = synthetic({'scenario': 'logistic', 'n': 500, 'seed': 5})
        _, outputs = run_tool('logit', {'data': data}, {'features': 'x', 'y': 'clase', 'method': 'logit'})
        result, _ = run_tool('marginal_effects', {'model': outputs['model']}, {'at': 'overall'})
        fit = outputs['model'].fit
        p = fit.predict()
        expected = np.mean(p * (1 - p)) * fit.params['x']
        self.assertAlmostEqual(result['tables'][0]['rows'][0][1], expected, places=8)
        linear, ols_outputs = run_tool('multiple_ols', {'data': synthetic({'scenario': 'multiple', 'n': 200, 'seed': 1})}, {'features': 'x,z', 'y': 'y'})
        effects, _ = run_tool('marginal_effects', {'model': ols_outputs['model']}, {'at': 'mean'})
        self.assertAlmostEqual(effects['tables'][0]['rows'][0][1], ols_outputs['model'].fit.params['x'])

    def test_bootstrap_interval_contains_estimate_and_matches_normal_theory(self):
        rng = np.random.default_rng(11)
        data = pd.DataFrame({'valor': rng.normal(10, 2, 400)})
        result, _ = run_tool('bootstrap', {'data': data}, {'column': 'valor', 'statistic': 'mean', 'method': 'BCa', 'replications': 3000, 'confidence': 0.95, 'seed': 1})
        low, high = metric(result, 'ic_inferior'), metric(result, 'ic_superior')
        self.assertLess(low, metric(result, 'estimacion'))
        self.assertGreater(high, metric(result, 'estimacion'))
        theory = stats.sem(data['valor'])
        self.assertAlmostEqual(metric(result, 'error_estandar'), theory, delta=theory * 0.1)
        again, _ = run_tool('bootstrap', {'data': data}, {'column': 'valor', 'statistic': 'mean', 'method': 'BCa', 'replications': 3000, 'confidence': 0.95, 'seed': 1})
        self.assertEqual(metric(again, 'ic_inferior'), low)


if __name__ == '__main__':
    unittest.main()
