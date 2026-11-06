"""Fuente Yahoo Finance sin red: tickers, alineación, transformaciones, comparación con el índice y ejemplos Y01–Y02."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
from quantlabs import yfinance_source
from quantlabs.core import EngineError, NODE_CATALOG, execute
from quantlabs.projects import example_catalog, example_get
from quantlabs.yfinance_source import parse_tickers, yfinance_data


def synthetic(tickers, start, end, interval):
    """Precios inventados con un factor común: beta conocida aproximada y un feriado distinto por bolsa."""
    freq = {'1d': 'B', '1wk': 'W-MON', '1mo': 'MS'}[interval]
    dates = pd.date_range(start, end, freq=freq)
    rng = np.random.default_rng(7)
    market = rng.normal(.008, .04, len(dates))
    prices = {}
    for k, ticker in enumerate(tickers):
        beta = 1.0 if ticker.startswith('^') else 0.5 + 0.5 * k
        returns = beta * market + rng.normal(0, .02, len(dates))
        prices[ticker] = 100 * np.cumprod(1 + returns)
    frame = pd.DataFrame(prices, index=dates)
    if interval == '1d' and len(frame) > 5:
        frame.iloc[3, 0] = np.nan  # feriado en la bolsa del primer activo
    return frame


class TickerTests(unittest.TestCase):
    def test_parse_tickers(self):
        self.assertEqual(parse_tickers('aapl\nWALMEX.MX: wm\nMXN=X, BTC-USD'),
                         {'AAPL': 'aapl', 'WALMEX.MX': 'wm', 'MXN=X': 'usd_mxn', 'BTC-USD': 'bitcoin'})
        self.assertEqual(parse_tickers('ZZZ.MX'), {'ZZZ.MX': 'zzz_mx'})
        self.assertEqual(parse_tickers('000001.SS'), {'000001.SS': 'shanghai'})
        for bad in ['', 'AAPL\nAAPL', 'AAPL: periodo', 'AAPL: 1x', 'https://x', '../etc', 'A' * 25, ','.join(f'T{i}' for i in range(11)), 5]:
            with self.subTest(bad=bad), self.assertRaises(EngineError):
                parse_tickers(bad)

    def test_invalid_choices(self):
        for params in [{'index': '^XYZ'}, {'interval': 'horario'}, {'values': 'volumen'}, {'start_date': '2024-01-01', 'end_date': '2023-01-01'},
                       {'tickers': '^GSPC', 'index': '^GSPC'}, {'tickers': 'AAPL: sp500', 'index': '^GSPC'}]:
            with self.subTest(params=params), self.assertRaises(EngineError):
                yfinance_data({'start_date': '2020-01-01', 'end_date': '2022-12-31', **params}, fetch=synthetic)

    def test_missing_ticker_is_reported(self):
        def partial(tickers, start, end, interval):
            frame = synthetic(tickers, start, end, interval)
            frame[tickers[0]] = np.nan
            return frame
        with self.assertRaises(EngineError) as caught:
            yfinance_data({'tickers': 'NOEXISTE', 'start_date': '2020-01-01', 'end_date': '2021-01-01'}, fetch=partial)
        self.assertEqual(caught.exception.code, 'DATA_UNAVAILABLE')
        self.assertIn('NOEXISTE', str(caught.exception))


class ValuesTests(unittest.TestCase):
    params = {'tickers': 'AAPL\nMSFT', 'index': '^GSPC', 'start_date': '2015-01-01', 'end_date': '2020-12-31', 'interval': 'mensual'}

    def prices(self):
        frame, _ = yfinance_data({**self.params, 'values': 'precios'}, fetch=synthetic)
        return frame

    def test_returns_log_and_base100_from_prices(self):
        prices = self.prices().set_index('periodo')
        self.assertEqual(list(prices.columns), ['aapl', 'msft', 'sp500'])
        simple = yfinance_data({**self.params, 'values': 'rendimientos'}, fetch=synthetic)[0].set_index('periodo')
        logs = yfinance_data({**self.params, 'values': 'log'}, fetch=synthetic)[0].set_index('periodo')
        base = yfinance_data({**self.params, 'values': 'base100'}, fetch=synthetic)[0].set_index('periodo')
        np.testing.assert_allclose(simple.to_numpy(), (prices.pct_change().iloc[1:] * 100).to_numpy())
        np.testing.assert_allclose(logs.to_numpy(), (np.log(prices).diff().iloc[1:] * 100).to_numpy())
        np.testing.assert_allclose(base.iloc[0].to_numpy(), [100, 100, 100])
        self.assertEqual(len(simple), len(prices) - 1)

    def test_comparison_matches_numpy(self):
        prices = self.prices().set_index('periodo')
        _, source = yfinance_data({**self.params, 'values': 'rendimientos'}, fetch=synthetic)
        table = source['comparison']
        returns = prices.pct_change().dropna()
        beta = np.cov(returns['aapl'], returns['sp500'], ddof=1)[0, 1] / returns['sp500'].var(ddof=1)
        row = dict(zip(table['columns'], table['rows'][0]))
        self.assertAlmostEqual(row['Beta vs sp500'], beta)
        self.assertAlmostEqual(row['Correlación'], returns['aapl'].corr(returns['sp500']))
        self.assertAlmostEqual(row['Rendimiento total (%)'], (prices['aapl'].iloc[-1] / prices['aapl'].iloc[0] - 1) * 100)
        self.assertAlmostEqual(row['Volatilidad anualizada (%)'], returns['aapl'].std(ddof=1) * np.sqrt(12) * 100)
        self.assertLessEqual(row['Caída máxima (%)'], 0)
        self.assertEqual(table['rows'][-1][0], 'sp500')
        json.dumps(source, allow_nan=False)

    def test_daily_alignment_drops_non_common_dates(self):
        frame, source = yfinance_data({**self.params, 'interval': 'diario', 'values': 'precios', 'end_date': '2015-03-31'}, fetch=synthetic)
        self.assertEqual(source['dropped_rows'], 1)
        self.assertFalse(frame.isna().any().any())

    def test_without_index(self):
        frame, source = yfinance_data({**self.params, 'index': 'ninguno'}, fetch=synthetic)
        self.assertEqual(list(frame.columns), ['periodo', 'aapl', 'msft'])
        self.assertEqual(source['comparison']['columns'][-1], 'Caída máxima (%)')


class IntegrationTests(unittest.TestCase):
    def test_node_registered(self):
        self.assertIn('yfinance', NODE_CATALOG)
        schema = json.loads((ROOT / 'packages/contracts/project.schema.json').read_text())
        self.assertIn('yfinance', schema['$defs']['node']['properties']['type']['enum'])
        catalog = json.loads((ROOT / 'packages/contracts/yfinanceCatalog.json').read_text())
        self.assertEqual(set(NODE_CATALOG['yfinance']['choices']['index']), {item['ticker'] for item in catalog['indices']} | {'ninguno'})
        aliases = [item['alias'] for item in catalog['indices'] + catalog['assets']]
        self.assertEqual(len(aliases), len(set(aliases)))

    def test_examples_run_offline(self):
        ids = [item['id'] for item in example_catalog() if item['id'].startswith('Y')]
        self.assertEqual(ids, ['Y01', 'Y02'])
        yfinance_source._cache.clear()
        with patch('quantlabs.yfinance_source.download', side_effect=synthetic):
            for example in ids:
                with self.subTest(example=example):
                    project = example_get(example)['project']
                    self.assertEqual({s['node_id'] for s in project['lesson']['steps']}, {n['id'] for n in project['nodes']})
                    result = execute(project)
                    self.assertEqual({k: v.get('error') for k, v in result['nodes'].items() if v['status'] != 'succeeded'}, {})
                    json.dumps(result, allow_nan=False)

    def test_brain_detects_yahoo(self):
        from quantlabs.brain.intents import detect_source, rules_plan
        kind, params, _ = detect_source('Con yfinance calcula la beta de Apple y Microsoft frente al Nasdaq desde 2020')
        self.assertEqual((kind, params['tickers'], params['index'], params['start_date']), ('yfinance', 'AAPL\nMSFT', '^IXIC', '2020-01-01'))
        self.assertEqual(detect_source('Beta de WALMEX.MX y Bimbo frente al IPC mensual')[1]['tickers'], 'WALMEX.MX\nBIMBOA.MX')
        steps = {s['tool']: s['parameters'] for s in rules_plan('Beta de WALMEX.MX frente al IPC de la bolsa mexicana')['steps']}
        self.assertEqual(steps['ols'], {'x': 'ipc_mexico', 'y': 'walmex'})
        self.assertEqual(detect_source('Analiza la inflación de México con el IPC del Banco Mundial')[0], 'worldbank')


if __name__ == '__main__':
    unittest.main()
