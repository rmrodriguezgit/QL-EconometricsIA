"""Vistas del OLS múltiple: plano 3D y variable añadida (Frisch–Waugh–Lovell) frente a statsmodels."""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))

from quantlabs.tools import MAX_VIEW_POINTS, run_tool  # noqa: E402


class RegressionViewsTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(7)
        n = 250
        self.frame = pd.DataFrame({'x': rng.normal(size=n), 'z': rng.normal(size=n), 'w': rng.normal(size=n)})
        self.frame['z'] += 0.6 * self.frame['x']  # regresores correlacionados: la pendiente simple ≠ la parcial
        self.frame['y'] = 1 + 2 * self.frame.x - 0.5 * self.frame.z + 0.3 * self.frame.w + rng.normal(size=n)

    def test_partial_slopes_equal_multiple_coefficients(self):
        result, _ = run_tool('multiple_ols', {'data': self.frame}, {'features': 'x,z,w', 'y': 'y', 'covariance': 'nonrobust'})
        reference = sm.OLS(self.frame.y, sm.add_constant(self.frame[['x', 'z', 'w']])).fit()
        items = {item['feature']: item for item in result['partial_regression']['items']}
        for name in ['x', 'z', 'w']:
            self.assertAlmostEqual(items[name]['slope'], reference.params[name], places=10)
            self.assertAlmostEqual(items[name]['coefficient'], reference.params[name], places=10)
            ex, ey = np.array(items[name]['points']).T
            self.assertAlmostEqual(float(ex.mean()), 0, places=10)
            self.assertAlmostEqual(float(ey.mean()), 0, places=10)
        simple = np.polyfit(self.frame.z, self.frame.y, 1)[0]
        self.assertGreater(abs(simple - items['z']['slope']), 0.3)

    def test_plane_rows_reproduce_fitted_values(self):
        result, _ = run_tool('multiple_ols', {'data': self.frame}, {'features': 'x,z,w', 'y': 'y', 'covariance': 'HC3'})
        plane = result['plane3d']
        beta = plane['coefficients']
        for x, z, w, y, fitted in plane['rows']:
            self.assertAlmostEqual(fitted, beta['const'] + beta['x'] * x + beta['z'] * z + beta['w'] * w, places=9)
        self.assertEqual(plane['features'], ['x', 'z', 'w'])
        self.assertAlmostEqual(plane['means']['w'], float(self.frame.w.mean()), places=12)

    def test_large_samples_are_capped(self):
        rng = np.random.default_rng(1)
        big = pd.DataFrame({'x': rng.normal(size=4000), 'z': rng.normal(size=4000)})
        big['y'] = big.x + big.z + rng.normal(size=4000)
        result, _ = run_tool('multiple_ols', {'data': big}, {'features': 'x,z', 'y': 'y', 'covariance': 'nonrobust'})
        self.assertEqual(len(result['plane3d']['rows']), MAX_VIEW_POINTS)
        self.assertEqual(result['plane3d']['n'], 4000)
        self.assertEqual(len(result['partial_regression']['items'][0]['points']), MAX_VIEW_POINTS)


if __name__ == '__main__':
    unittest.main()
