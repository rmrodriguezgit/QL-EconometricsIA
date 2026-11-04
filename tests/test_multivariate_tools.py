import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))

from quantlabs.core import EngineError, execute  # noqa: E402
from quantlabs.projects import example_get  # noqa: E402
from quantlabs.tools import run_tool  # noqa: E402


def data(n=60, seed=0):
    rng = np.random.default_rng(seed)
    a = rng.normal(size=n)
    frame = pd.DataFrame({'periodo': range(1960, 1960 + n), 'a': a, 'b': a * 0.98 + rng.normal(scale=.05, size=n),
                          'c': rng.normal(size=n)})
    frame['y'] = 1 + 2 * frame.a - frame.c + rng.normal(scale=.5, size=n)
    return frame


def metric(result, label):
    return next(m['value'] for m in result['metrics'] if m['label'] == label)


class DescriptiveTests(unittest.TestCase):
    def test_describe_transpose_matches_pandas(self):
        frame = data()
        frame.loc[2, 'c'] = np.nan
        result, _ = run_tool('describe_table', {'data': frame}, {'columns': 'a,c', 'orientation': 'transpuesta'})
        expected = frame[['a', 'c']].describe().T
        for row in result['tables'][0]['rows']:
            np.testing.assert_allclose(row[1:], expected.loc[row[0]].to_numpy(), rtol=1e-12)
        pandas, _ = run_tool('describe_table', {'data': frame}, {'columns': 'a,c', 'orientation': 'pandas'})
        self.assertEqual(pandas['tables'][0]['columns'], ['Estadístico', 'a', 'c'])

    def test_series_and_boxplots(self):
        frame = data()
        result, _ = run_tool('series_plot', {'data': frame}, {'mode': 'indice'})
        first = result['series_plot']['lines'][0]
        self.assertAlmostEqual(first['points'][0][1], 100.0)
        boxes, _ = run_tool('boxplots', {'data': frame}, {'columns': 'a,c', 'scale': 'zscore'})
        z = (frame.a - frame.a.mean()) / frame.a.std()
        self.assertAlmostEqual(boxes['boxplots']['boxes'][0]['median'], float(np.quantile(z, .5)), places=12)


class HypothesisTests(unittest.TestCase):
    def test_methods_match_scipy(self):
        frame = data()
        a, y = frame.a.to_numpy(), frame.y.to_numpy()
        cases = {'welch': stats.ttest_ind(a, y, equal_var=False), 'student': stats.ttest_ind(a, y),
                 'paired': stats.ttest_rel(a, y), 'mannwhitney': stats.mannwhitneyu(a, y)}
        for method, expected in cases.items():
            with self.subTest(method=method):
                result, _ = run_tool('two_sample_test', {'data': frame}, {'first': 'a', 'second': 'y', 'method': method})
                self.assertAlmostEqual(metric(result, 'p_valor'), expected.pvalue, places=12)
                self.assertIn('H₀', result['hypotheses']['h0'])
        with self.assertRaises(EngineError):
            run_tool('two_sample_test', {'data': frame}, {'first': 'a', 'second': 'a'})


class CollinearityTests(unittest.TestCase):
    def test_eigen_matrix_and_severity(self):
        frame = data()
        result, _ = run_tool('eigen_correlation', {'data': frame}, {'columns': 'a,b,c'})
        values = np.sort(np.linalg.eig(frame[['a', 'b', 'c']].corr().to_numpy())[0])[::-1]
        np.testing.assert_allclose([row[1] for row in result['tables'][1]['rows']], values, atol=1e-12)
        self.assertGreater(metric(result, 'indice_condicion_max'), 30)
        self.assertIn('severa', result['interpretation'])
        calm, _ = run_tool('eigen_correlation', {'data': frame}, {'columns': 'a,c'})
        self.assertIn('Sin colinealidad', calm['interpretation'])


class LearningTests(unittest.TestCase):
    def test_sklearn_coefficients_match_statsmodels(self):
        frame = data()
        result, outputs = run_tool('sklearn_linear', {'data': frame}, {'features': 'a,c', 'y': 'y', 'scale': 'standard'})
        reference = sm.OLS(frame.y, sm.add_constant(frame[['a', 'c']])).fit().params.to_numpy()
        np.testing.assert_allclose([row[2] for row in result['tables'][0]['rows']], reference, rtol=1e-9)
        self.assertEqual(outputs['model'].kind, 'sklearn_linear')

    def test_cross_validation_and_search(self):
        frame = data(120)
        _, ols = run_tool('multiple_ols', {'data': frame}, {'features': 'a,c', 'y': 'y'})
        cv, _ = run_tool('cross_validation', {'model': ols['model'], 'data': frame}, {'cv': 'timeseries', 'folds': 4})
        self.assertGreater(metric(cv, 'R2_medio'), .8)
        self.assertEqual(len(cv['tables'][0]['rows']), 4)
        search, out = run_tool('hyperparameter_search', {'data': frame}, {'features': 'a,b,c', 'y': 'y', 'estimator': 'ridge', 'cv': 'kfold'})
        self.assertGreater(metric(search, 'alpha_optimo'), 0)
        residuals, _ = run_tool('residual_analysis', {'model': out['model']}, {})
        self.assertAlmostEqual(metric(residuals, 'media_residuos'), 0, places=6)
        self.assertTrue(residuals['residual_plot']['points'])
        _, logit = run_tool('logit', {'data': pd.DataFrame({'x': frame.a, 'y': (frame.y > 1).astype(int)})}, {'x': 'x', 'y': 'y'})
        with self.assertRaises(EngineError):
            run_tool('residual_analysis', {'model': logit['model']}, {})


class ExampleTests(unittest.TestCase):
    def test_r01_runs_offline_with_equivalent_table(self):
        project = example_get('R01')['project']
        frame = data(49)
        source = next(node for node in project['nodes'] if node['id'] == 'datos')
        # Sustituye la descarga por un CSV con los mismos alias para ejecutar el recorrido sin red.
        rng = np.random.default_rng(3)
        table = pd.DataFrame({'periodo': range(1972, 2021), 'social_contri': np.linspace(1e11, 1.3e12, 49) * (1 + rng.normal(scale=.02, size=49)),
                              'lending_rate': np.abs(8 + 3 * rng.normal(size=49)), 'gdp_growth': 2.5 + 2 * rng.normal(size=49)})
        table['fin_cons'] = 10 * table.social_contri + 1e10 * table.lending_rate + rng.normal(scale=1e11, size=49)
        source.update({'type': 'csv', 'parameters': {'content': table.to_csv(index=False), 'delimiter': ','}})
        result = execute(project)
        failed = {k: v.get('error') for k, v in result['nodes'].items() if v['status'] != 'succeeded'}
        self.assertEqual(failed, {})
        self.assertEqual(len(frame), 49)


if __name__ == '__main__':
    unittest.main()
