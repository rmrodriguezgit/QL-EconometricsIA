"""Datos del gráfico de ajuste OLS: residuos, residuo estandarizado, banda IC 95 % y muestreo."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
from quantlabs.core import MAX_FIT_POINTS, ols


def frame(n, seed=3):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, 10, n)
    return pd.DataFrame({'x': x, 'y': 2 + 0.5 * x + rng.normal(0, 1, n)})


class OlsFitPlotTests(unittest.TestCase):
    def test_points_residuals_and_band_match_statsmodels(self):
        data = frame(80)
        result = ols(data, {'x': 'x', 'y': 'y', 'covariance': 'nonrobust'})
        plot = result['fit_plot']
        fit = sm.OLS(data['y'], sm.add_constant(data[['x']])).fit()
        points = np.array(plot['points'])
        self.assertEqual(points.shape, (80, 5))
        np.testing.assert_allclose(points[:, 1] - points[:, 2], points[:, 3], atol=1e-10)
        np.testing.assert_allclose(points[:, 3], fit.resid, atol=1e-10)
        internal = fit.get_influence().resid_studentized_internal
        np.testing.assert_allclose(points[:, 4], internal, atol=1e-8)
        self.assertEqual(plot['outliers'], int((np.abs(internal) > 2).sum()))
        self.assertAlmostEqual(plot['sigma'], float(np.sqrt(fit.scale)))
        band = np.array(plot['band'])
        np.testing.assert_allclose(band[:, 1], fit.params['const'] + fit.params['x'] * band[:, 0], atol=1e-10)
        self.assertTrue((band[:, 2] < band[:, 1]).all() and (band[:, 3] > band[:, 1]).all())
        self.assertFalse(plot['sampled'])

    def test_hc3_band_is_wider_than_classic_under_heteroskedasticity(self):
        rng = np.random.default_rng(7)
        x = rng.uniform(0, 10, 200)
        data = pd.DataFrame({'x': x, 'y': 1 + x + rng.normal(0, 0.2 + 0.6 * x)})
        classic = np.array(ols(data, {'x': 'x', 'y': 'y', 'covariance': 'nonrobust'})['fit_plot']['band'])
        robust = np.array(ols(data, {'x': 'x', 'y': 'y', 'covariance': 'HC3'})['fit_plot']['band'])
        self.assertGreater((robust[-1, 3] - robust[-1, 2]), (classic[-1, 3] - classic[-1, 2]))

    def test_large_samples_are_sampled_but_keep_extremes(self):
        data = frame(MAX_FIT_POINTS + 1500)
        data.loc[17, 'y'] += 40  # atípico evidente
        plot = ols(data, {'x': 'x', 'y': 'y', 'covariance': 'nonrobust'})['fit_plot']
        self.assertTrue(plot['sampled'])
        self.assertEqual(plot['n'], len(data))
        self.assertEqual(plot['shown'], len(plot['points']))
        self.assertLessEqual(len(plot['points']), MAX_FIT_POINTS + 20)
        self.assertTrue(any(abs(p[3]) > 30 for p in plot['points']))


if __name__ == '__main__':
    unittest.main()
