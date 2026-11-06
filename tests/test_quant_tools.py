"""Herramientas integradas desde Quantlabs-Blueprints, organización de la biblioteca y migración de reemplazadas."""
from collections import Counter
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
from quantlabs.core import EngineError, NODE_CATALOG, execute
from quantlabs.migrations import MIGRATIONS, SUPERSEDED, migrate_parameters
from quantlabs.quant_tools import data_quality, ml_compare, portfolio, quant_features, resample, risk_metrics, select_columns


def daily(n=400, seed=0):
    rng = np.random.default_rng(seed)
    days = pd.bdate_range('2023-01-02', periods=n)
    price = 100 * np.exp(np.cumsum(rng.normal(.0005, .01, n)))
    return pd.DataFrame({'periodo': days.strftime('%Y-%m-%d'), 'precio': price, 'otro': rng.normal(size=n)})


class PreparationTests(unittest.TestCase):
    def test_resample_matches_pandas(self):
        frame = daily()
        stamp = pd.to_datetime(frame['periodo'])
        for aggregation, method in [('ultimo', 'last'), ('media', 'mean'), ('primero', 'first')]:
            _, out = resample(frame, {'frequency': 'mensual', 'aggregation': aggregation, 'incomplete': 'conservar', 'columns': 'precio'})
            expected = getattr(frame.set_index(stamp)['precio'].resample('MS'), method)()
            np.testing.assert_allclose(out['data']['precio'].to_numpy(), expected.to_numpy())
            self.assertEqual(out['data']['periodo'].iloc[0], '2023-01-01')
        _, annual = resample(frame, {'frequency': 'anual', 'aggregation': 'suma', 'incomplete': 'conservar'})
        self.assertEqual(annual['data']['periodo'].tolist(), [2023, 2024])

    def test_resample_excludes_incomplete_last_period(self):
        frame = daily(300)  # termina a mitad de mes
        _, kept = resample(frame, {'frequency': 'mensual', 'incomplete': 'conservar'})
        _, cut = resample(frame, {'frequency': 'mensual', 'incomplete': 'excluir'})
        self.assertEqual(len(kept['data']) - len(cut['data']), 1)
        with self.assertRaises(EngineError):
            resample(frame.drop(columns='periodo'), {})

    def test_data_quality_policies(self):
        frame = pd.DataFrame({'periodo': ['2024-01-03', '2024-01-02', '2024-01-02', '2024-01-04', '2024-01-05'],
                              'x': [1., 2., 3., np.inf, np.nan], 'y': [1., 1., 1., 1., 1.]})
        result, out = data_quality(frame, {'duplicates': 'ultimo', 'missing': 'arrastrar', 'ffill_limit': 1})
        data = out['data']
        self.assertEqual(data['periodo'].tolist(), ['2024-01-02', '2024-01-03', '2024-01-04'])  # ordenada, sin duplicado; el último faltante excede el arrastre
        self.assertEqual(data['x'].tolist(), [3., 1., 1.])
        rows = {row[0]: row for row in result['tables'][0]['rows']}
        self.assertEqual(rows['x'][2], 1)  # un infinito
        self.assertEqual(rows['y'][5], 'sí')  # constante
        informed, kept = data_quality(frame, {})
        self.assertEqual(len(kept['data']), 5)
        self.assertTrue(informed['warnings'])

    def test_select_columns(self):
        frame = daily(10)
        _, out = select_columns(frame, {'columns': 'precio: cierre, periodo'})
        self.assertEqual(out['data'].columns.tolist(), ['cierre', 'periodo'])
        for bad in ['', 'nada', 'precio, precio', 'precio: 1x']:
            with self.subTest(bad=bad), self.assertRaises(EngineError):
                select_columns(frame, {'columns': bad})


class IndicatorAndRiskTests(unittest.TestCase):
    def test_indicators_match_definitions_and_do_not_look_ahead(self):
        frame = daily()
        _, out = quant_features(frame, {'price': 'precio', 'window': 10})
        data = out['data']
        np.testing.assert_allclose(data['precio_sma'].iloc[20], frame['precio'].iloc[11:21].mean())
        macd = frame['precio'].ewm(span=12, adjust=False).mean() - frame['precio'].ewm(span=26, adjust=False).mean()
        np.testing.assert_allclose(data['precio_macd'], macd)
        self.assertTrue(((data['precio_rsi'].dropna() >= 0) & (data['precio_rsi'].dropna() <= 100)).all())
        rising = pd.DataFrame({'precio': np.arange(1., 60.)})
        self.assertEqual(quant_features(rising, {'price': 'precio'})[1]['data']['precio_rsi'].iloc[-1], 100)
        changed = frame.copy()
        changed.loc[300:, 'precio'] *= 3
        _, again = quant_features(changed, {'price': 'precio', 'window': 10})
        pd.testing.assert_frame_equal(data.iloc[:300].drop(columns='precio'), again['data'].iloc[:300].drop(columns='precio'))
        with self.assertRaises(EngineError):
            quant_features(frame.assign(precio=-frame['precio']), {'price': 'precio', 'values': 'precios'})

    def test_indicators_from_returns_like_yahoo_finance(self):
        # Yahoo Finance con «rendimientos» entrega columnas por ticker en %, con negativos; antes el nodo fallaba.
        rng = np.random.default_rng(5)
        returns = rng.normal(.8, 4, 120)
        frame = pd.DataFrame({'periodo': pd.date_range('2014-01-01', periods=120, freq='MS').strftime('%Y-%m-%d'), 'spy': returns, 'qqq': returns * 1.2})
        result, out = quant_features(frame, {'price': 'precio', 'window': 12, 'periods_per_year': 12})
        data = out['data']
        np.testing.assert_allclose(data['spy_indice'], 100 * np.cumprod(1 + returns / 100))
        np.testing.assert_allclose(data['spy_rend'], returns)
        np.testing.assert_allclose(data['spy_sma'].iloc[11], data['spy_indice'].iloc[:12].mean())
        np.testing.assert_allclose(data['spy_vol_movil'].iloc[-1], np.std(returns[-12:] / 100, ddof=1) * np.sqrt(12) * 100)
        self.assertTrue(any('se usó spy' in w for w in result['warnings']))
        self.assertTrue(any('rendimientos en %' in w for w in result['warnings']))
        self.assertFalse(any('mal escalados' in w for w in result['warnings']))
        monthly_as_daily = quant_features(frame, {'price': 'spy', 'periods_per_year': 252})[0]
        self.assertTrue(any('≈ 12 períodos por año' in w for w in monthly_as_daily['warnings']))
        chosen = quant_features(frame.assign(qqq=frame['qqq'] / 100), {'price': 'qqq', 'values': 'decimal'})[1]['data']
        np.testing.assert_allclose(chosen['qqq_indice'], 100 * np.cumprod(1 + returns * 1.2 / 100))
        with self.assertRaises(EngineError):
            quant_features(frame, {'price': 'spy', 'values': 'precios'})

    def test_risk_metrics_against_manual_formulas(self):
        rng = np.random.default_rng(3)
        market = rng.normal(.0004, .01, 750)
        asset = .0002 + 1.4 * market + rng.normal(0, .005, 750)
        frame = pd.DataFrame({'a': asset * 100, 'm': market * 100})
        result, _ = risk_metrics(frame, {'columns': 'a,m', 'values': 'porcentaje', 'benchmark': 'm', 'periods_per_year': 252, 'risk_free': 0, 'confidence': .95})
        head = result['tables'][0]['columns']
        row = dict(zip(head, result['tables'][0]['rows'][0]))
        self.assertAlmostEqual(row['Volatilidad anual (%)'], asset.std(ddof=1) * np.sqrt(252) * 100, places=6)
        self.assertAlmostEqual(row['Sharpe'], asset.mean() / asset.std(ddof=1) * np.sqrt(252), places=6)
        self.assertAlmostEqual(row['VaR 95% (%)'], -np.quantile(asset, .05) * 100, places=6)
        self.assertAlmostEqual(row['Beta vs m'], np.cov(asset, market, ddof=1)[0, 1] / market.var(ddof=1), places=6)
        equity = np.cumprod(1 + asset)
        self.assertAlmostEqual(row['Caída máxima (%)'], (equity / np.maximum.accumulate(equity) - 1).min() * 100, places=6)

    def test_price_input_and_errors(self):
        frame = daily()
        result, _ = risk_metrics(frame, {'columns': 'precio', 'values': 'precios', 'periods_per_year': 252})
        total = result['tables'][0]['rows'][0][2]
        self.assertAlmostEqual(total, (frame['precio'].iloc[-1] / frame['precio'].iloc[0] - 1) * 100, places=6)
        with self.assertRaises(EngineError):
            risk_metrics(frame, {'columns': 'precio', 'benchmark': 'nada'})


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(1)
        n = 400
        self.frame = pd.DataFrame({'a': rng.normal(.8, 4, n), 'b': rng.normal(.4, 1.5, n), 'c': rng.normal(.6, 3, n)})

    def test_weights_valid_and_min_variance_is_lowest(self):
        result, out = portfolio(self.frame, {'columns': 'a,b,c', 'values': 'porcentaje', 'periods_per_year': 12, 'max_weight': .7, 'fraction': .7, 'risk_free': .02})
        tables = {t['title']: t for t in result['tables']}
        weights = {row[0]: row for row in tables['Pesos de cada portafolio (%)']['rows']}
        self.assertEqual(list(weights), ['Pesos iguales', 'Mínima varianza', 'Máximo Sharpe', 'Máximo Sortino'])
        for label, row in weights.items():
            w = np.array(row[1:4]) / 100
            with self.subTest(label=label):
                self.assertAlmostEqual(w.sum(), 1, places=6)
                self.assertTrue((w >= -1e-9).all() and (w <= .7 + 1e-6).all())
                self.assertAlmostEqual(row[4], 1 / np.sum(w ** 2), places=6)
        expected = {row[0]: row for row in tables['Rendimiento, volatilidad y riesgo esperados (estimación)']['rows']}
        vol, sharpe, sortino = ({label: row[k] for label, row in expected.items()} for k in (2, 5, 6))
        self.assertLessEqual(vol['Mínima varianza'], min(vol.values()) + 1e-6)
        self.assertGreaterEqual(sharpe['Máximo Sharpe'], max(sharpe.values()) - 1e-6)
        self.assertGreaterEqual(sortino['Máximo Sortino'], max(sortino.values()) - 1e-6)
        # La frontera no tiene puntos con menos volatilidad que la mínima varianza ni más Sharpe que el máximo.
        frontier = tables['Frontera eficiente (estimación)']['rows']
        self.assertGreaterEqual(min(r[0] for r in frontier), vol['Mínima varianza'] - 1e-4)
        self.assertLessEqual(max(r[2] for r in frontier), sharpe['Máximo Sharpe'] + 1e-6)
        self.assertTrue(all(b[1] >= a[1] - 1e-9 for a, b in zip(frontier, frontier[1:])))
        for row in tables['Contribución de cada activo al riesgo (% de la varianza)']['rows']:
            self.assertAlmostEqual(sum(row[1:]), 100, places=6)
        self.assertEqual(out['data'].columns.tolist(), ['pesos_iguales', 'minima_varianza', 'maximo_sharpe', 'maximo_sortino'])
        self.assertEqual(len(out['data']), 400 - 280)
        plot = result['portfolio_plot']
        self.assertEqual((plot['columns'], len(plot['portfolios']), len(plot['cloud'])), (['a', 'b', 'c'], 4, 600))
        self.assertTrue(len(plot['frontier']) > 10 and plot['lower'])

    def test_equal_weights_metrics_match_manual_calculation(self):
        result, _ = portfolio(self.frame, {'columns': 'a,b,c', 'covariance': 'muestral', 'periods_per_year': 12, 'risk_free': .02, 'fraction': .7})
        train = self.frame.iloc[:280] / 100
        path = train.mean(axis=1).to_numpy()
        ret = path.mean() * 12
        vol = np.sqrt(np.full(3, 1 / 3) @ train.cov(ddof=1).to_numpy() @ np.full(3, 1 / 3) * 12)
        rf_period = 1.02 ** (1 / 12) - 1
        down = np.sqrt(np.mean(np.minimum(path - rf_period, 0) ** 2) * 12)
        row = next(r for r in result['tables'][1]['rows'] if r[0] == 'Pesos iguales')
        self.assertAlmostEqual(row[1], ret * 100, places=8)
        self.assertAlmostEqual(row[2], vol * 100, places=8)
        self.assertAlmostEqual(row[4], down * 100, places=8)
        self.assertAlmostEqual(row[5], (ret - .02) / vol, places=8)
        self.assertAlmostEqual(row[6], (ret - .02) / down, places=8)
        self.assertAlmostEqual(row[7], -np.quantile(path, .05) * 100, places=8)

    def test_two_asset_minimum_variance_matches_formula(self):
        result, _ = portfolio(self.frame, {'columns': 'a,b', 'values': 'porcentaje', 'covariance': 'muestral', 'fraction': .9})
        train = self.frame[['a', 'b']].iloc[:360] / 100
        s = train.cov(ddof=1).to_numpy()
        expected = (s[1, 1] - s[0, 1]) / (s[0, 0] + s[1, 1] - 2 * s[0, 1])
        row = next(r for r in result['tables'][0]['rows'] if r[0] == 'Mínima varianza')
        self.assertAlmostEqual(row[1] / 100, expected, places=3)

    def test_errors(self):
        with self.assertRaises(EngineError):
            portfolio(self.frame, {'columns': 'a'})
        with self.assertRaises(EngineError):
            portfolio(self.frame.head(10), {'columns': 'a,b'})


class MachineLearningTests(unittest.TestCase):
    def test_selects_nonlinear_model_and_predicts(self):
        rng = np.random.default_rng(42)
        x = rng.uniform(-3, 3, 500)
        frame = pd.DataFrame({'x': x, 'y': np.sin(x) + rng.normal(0, .1, 500)})
        result, out = ml_compare(frame, {'features': 'x', 'y': 'y'})
        chosen = {m['label']: m['value'] for m in result['metrics']}['elegido']
        self.assertNotIn(chosen, ['Media (referencia)', 'Ridge', 'ElasticNet'])
        model = out['model']
        prediction = model.fit.predict(pd.DataFrame({'x': [0., np.pi / 2]}))
        np.testing.assert_allclose(prediction, [0, 1], atol=.2)
        again, _ = ml_compare(frame, {'features': 'x', 'y': 'y'})
        self.assertEqual(result['tables'], again['tables'])
        single, _ = ml_compare(frame, {'features': 'x', 'y': 'y', 'algorithm': 'ridge'})
        self.assertEqual(len(single['tables'][0]['rows']), 1)


class LibraryOrganizationTests(unittest.TestCase):
    def setUp(self):
        self.areas = json.loads((ROOT / 'packages/contracts/toolAreas.json').read_text(encoding='utf-8'))['areas']

    def test_every_visible_tool_in_exactly_one_group(self):
        listed = [tool for area in self.areas for group in area['groups'] for tool in group['tools']]
        self.assertEqual([tool for tool, n in Counter(listed).items() if n > 1], [])
        visible = {kind for kind, item in NODE_CATALOG.items() if not item.get('superseded_by') and not item.get('legacy')}
        self.assertEqual(set(listed), visible)
        self.assertFalse(set(listed) & SUPERSEDED)
        self.assertEqual(len({area['id'] for area in self.areas}), len(self.areas))

    def test_superseded_tools_have_valid_migrations(self):
        for kind, item in NODE_CATALOG.items():
            if item.get('superseded_by'):
                with self.subTest(kind=kind):
                    self.assertIn(kind, MIGRATIONS)
                    self.assertEqual(MIGRATIONS[kind]['to'], item['superseded_by'])
                    self.assertIn(item['superseded_by'], NODE_CATALOG)
                    self.assertTrue(item.get('superseded_reason'))
                    if not MIGRATIONS[kind].get('chain'):
                        new_kind, params = migrate_parameters(kind, NODE_CATALOG[kind]['defaults'])
                        self.assertTrue(set(params) <= set(NODE_CATALOG[new_kind]['defaults']), params)

    def test_migrated_paired_test_gives_same_result(self):
        rng = np.random.default_rng(0)
        before = rng.normal(10, 2, 60)
        def run(kind, params):
            project = {'schema_version': '1.0.0', 'app_version': '0.24.0', 'title': 't', 'edges': [{'id': 'e', 'source': 'd', 'source_port': 'data', 'target': 't', 'target_port': 'data'}],
                       'nodes': [{'id': 'd', 'type': 'synthetic', 'node_version': '1.0.0', 'parameters': {'scenario': 'pairs', 'n': 80, 'seed': 3}, 'position': {'x': 0, 'y': 0}},
                                 {'id': 't', 'type': kind, 'node_version': '1.0.0', 'parameters': params, 'position': {'x': 0, 'y': 0}}]}
            node = execute(project)['nodes']['t']
            self.assertEqual(node['status'], 'succeeded', node.get('error'))
            return json.dumps(node['result'], sort_keys=True)
        old = run('paired_test', {'before': 'antes', 'after': 'despues'})
        new_kind, params = migrate_parameters('paired_test', {'before': 'antes', 'after': 'despues'})
        new = run(new_kind, params)
        import re
        p_old = re.findall(r'p[_ -]?valor[^0-9]*([0-9.e-]+)', old, re.I)
        self.assertTrue(p_old)
        self.assertIn(p_old[0][:8], new)

    def test_brain_never_plans_superseded_tools(self):
        with tempfile.TemporaryDirectory() as folder:
            os.environ['QL_BRAIN_DIR'] = folder
            from quantlabs.brain.compiler import compile_plan
            from quantlabs.brain.intents import rules_plan
            for prompt in ['PIB de México del Banco Mundial 2000 2020 con serie temporal', 'Prueba pareada antes y después', 'Red neuronal para predecir y',
                           'Matriz de covarianza', 'Regresión lasso regularizada', 'Portafolio de Markowitz y Sharpe', 'Random forest frente a boosting']:
                with self.subTest(prompt=prompt):
                    project, _ = compile_plan(rules_plan(prompt), prompt)
                    self.assertFalse({node['type'] for node in project['nodes']} & SUPERSEDED)


if __name__ == '__main__':
    unittest.main()
