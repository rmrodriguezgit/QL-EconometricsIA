import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))

from quantlabs.cluster_views import kmeans_views  # noqa: E402
from quantlabs.core import execute  # noqa: E402
from quantlabs.projects import dispatch_files  # noqa: E402


def blobs(features=2, n=90, seed=0, scale=1.0):
    rng = np.random.default_rng(seed)
    centers = np.array([[0] * features, [6] * features, [0, 6] + [3] * (features - 2)], dtype=float)
    X = np.vstack([c + rng.normal(0, .6, (n // 3, features)) for c in centers])
    X[:, 0] *= scale
    return pd.DataFrame(X, columns=[f'x{i + 1}' for i in range(features)])


def fit(frame, k=3):
    from sklearn.cluster import KMeans
    return KMeans(n_clusters=k, n_init=10, random_state=42).fit(frame.to_numpy())


class ClusterViewTests(unittest.TestCase):
    def test_c25_plot_matches_model_and_silhouette_node(self):
        project = dispatch_files('examples.read', {'id': 'C25'})['project']
        run = execute(project)
        result = run['nodes']['modelo']['result']
        plot = result['cluster_plot']
        self.assertEqual((plot['k'], plot['n'], plot['axes']), (3, 300, ['x1', 'x2']))
        self.assertEqual(sum(g['n'] for g in plot['groups']), 300)
        silhouette = next(m['value'] for m in run['nodes']['silueta']['result']['metrics'] if m['label'] == 'silueta')
        self.assertAlmostEqual(plot['silhouette_mean'], silhouette, places=10)
        k3 = next(c for c in plot['curve'] if c['k'] == 3)
        inertia = next(m['value'] for m in result['metrics'] if m['label'] == 'inercia')
        self.assertAlmostEqual(k3['inertia'], inertia)
        self.assertEqual([c['k'] for c in plot['curve']], list(range(2, 9)))

    def test_group_statistics_and_profile(self):
        frame = blobs()
        model = fit(frame)
        plot, metrics, warnings = kmeans_views(frame, list(frame.columns), model, 42)
        X = frame.to_numpy()
        for g in plot['groups']:
            inside = X[model.labels_ == g['group']]
            self.assertAlmostEqual(g['sse'], ((inside - model.cluster_centers_[g['group']]) ** 2).sum())
            self.assertEqual(len(g['values']), g['n'])
            self.assertEqual(g['values'], sorted(g['values'], reverse=True))
        self.assertAlmostEqual(sum(g['sse'] for g in plot['groups']), model.inertia_, places=6)
        z = (model.cluster_centers_ - X.mean(axis=0)) / X.std(axis=0, ddof=1)
        np.testing.assert_allclose(plot['profile'], z)
        self.assertGreater(metrics['silueta_media'], .7)
        self.assertEqual(warnings, [])

    def test_more_than_two_variables_use_principal_components(self):
        frame = blobs(features=4)
        plot, _, _ = kmeans_views(frame, list(frame.columns), fit(frame), 42)
        self.assertTrue(plot['axes'][0].startswith('Componente 1'))
        self.assertGreater(sum(plot['explained']), 50)
        self.assertEqual(len(plot['centers'][0]), 4)
        self.assertEqual(len(plot['points'][0]), 3)

    def test_warns_about_scale_and_better_k(self):
        frame = blobs(scale=100)
        _, _, warnings = kmeans_views(frame, list(frame.columns), fit(frame), 42)
        self.assertTrue(any('escalas muy distintas' in w for w in warnings))
        frame = blobs()
        _, _, warnings = kmeans_views(frame, list(frame.columns), fit(frame, 5), 42)
        self.assertTrue(any('k = 3' in w for w in warnings))

    def test_large_tables_are_sampled(self):
        frame = blobs(n=3600)
        plot, _, _ = kmeans_views(frame, list(frame.columns), fit(frame), 42)
        self.assertTrue(plot['sampled_points'] and plot['sampled_silhouette'])
        self.assertEqual(len(plot['points']), 2500)
        self.assertEqual(sum(len(g['values']) for g in plot['groups']), 2000)


if __name__ == '__main__':
    unittest.main()
