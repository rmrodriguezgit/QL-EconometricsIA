"""Fuente FRED sin red: parseo, remuestreo, errores y ejemplos F01–F05 con datos sintéticos inyectados."""
from datetime import date
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
from quantlabs import fred_source
from quantlabs.core import EngineError, NODE_CATALOG, execute
from quantlabs.fred_source import fred_data, parse_csv, parse_date, parse_series
from quantlabs.projects import example_catalog, example_get
from quantlabs.tools import time_order


def synthetic(code, start, end):
    """Serie inventada con la frecuencia nativa de cada ID (diaria, mensual o trimestral)."""
    freq = {'GDPC1': 'QS', 'UNRATE': 'MS', 'CPIAUCSL': 'MS', 'PCEPI': 'MS', 'FEDFUNDS': 'MS', 'USREC': 'MS'}.get(code, 'B')
    dates = pd.date_range(start, end, freq=freq)
    rng = np.random.default_rng(abs(hash(code)) % 2**32)
    t = np.arange(len(dates))
    if code == 'USREC':
        values = ((t // 40) % 4 == 0).astype(float)
    elif code in ('CPIAUCSL', 'PCEPI', 'GDPC1'):
        values = 100 * np.exp(np.cumsum(rng.normal(.003, .004, len(t))))
    else:
        values = 5 + np.cumsum(rng.normal(0, .05, len(t)))
    return pd.DataFrame({'fecha': dates, 'valor': values})


class ParsingTests(unittest.TestCase):
    def test_series_map(self):
        self.assertEqual(parse_series('dgs3mo: corto\nDGS10'), {'DGS3MO': 'corto', 'DGS10': 'bono_10y'})
        self.assertEqual(parse_series('ZZZ1; UNRATE=paro'), {'ZZZ1': 'zzz1', 'UNRATE': 'paro'})
        for bad in ['', 'DGS10: periodo', 'DGS10: a\nDGS2: a', 'DGS10\nDGS10', '../x', 'https://evil', 5]:
            with self.subTest(bad=bad), self.assertRaises(EngineError):
                parse_series(bad)

    def test_dates(self):
        self.assertEqual(parse_date('1982', None, 'x'), date(1982, 1, 1))
        self.assertEqual(parse_date(1990, None, 'x'), date(1990, 1, 1))
        self.assertEqual(parse_date('', date(2000, 1, 1), 'x'), date(2000, 1, 1))
        for bad in ['2020-13-01', 'ayer', '3000-01-01']:
            with self.subTest(bad=bad), self.assertRaises(EngineError):
                parse_date(bad, None, 'x')

    def test_csv_formats(self):
        new = parse_csv('observation_date,DGS3MO\n2024-01-02,5.46\n2024-01-03,\n2024-01-04,5.48\n', 'DGS3MO')
        old = parse_csv('DATE,DGS3MO\n2024-01-02,5.46\n2024-01-03,.\n', 'DGS3MO')
        self.assertEqual(list(new.columns), ['fecha', 'valor'])
        self.assertTrue(np.isnan(new['valor'][1]) and np.isnan(old['valor'][1]))
        with self.assertRaises(EngineError):
            parse_csv('PK\x03\x04binario', 'X')

    def test_missing_series_is_reported(self):
        class Response:
            status_code, text = 404, 'Not found'
        class Session:
            def get(self, *args, **kwargs):
                return Response()
        with self.assertRaises(EngineError) as caught:
            fred_source.download('NOEXISTE123', date(2020, 1, 1), date(2020, 2, 1), session=Session())
        self.assertEqual(caught.exception.code, 'DATA_UNAVAILABLE')
        self.assertIn('NOEXISTE123', str(caught.exception))


class ResampleTests(unittest.TestCase):
    def test_monthly_mean_aligns_daily_and_monthly(self):
        frame, source = fred_data({'series': 'DGS10: largo\nUNRATE: paro', 'start_date': '2010-01-01', 'end_date': '2012-12-31',
                                   'frequency': 'mensual', 'aggregation': 'media'}, fetch=synthetic)
        self.assertEqual(len(frame), 36)
        self.assertEqual(frame['periodo'].iloc[0], '2010-01-01')
        raw = synthetic('DGS10', date(2010, 1, 1), date(2012, 12, 31))
        self.assertAlmostEqual(frame['largo'].iloc[0], raw[raw.fecha.dt.month.eq(1) & raw.fecha.dt.year.eq(2010)]['valor'].mean())
        self.assertEqual({item['native_frequency'] for item in source['series']}, {'diaria', 'mensual'})
        time_order(frame)  # fechas mensuales regulares

    def test_annual_period_is_integer_and_last_and_sum(self):
        frame, _ = fred_data({'series': 'UNRATE', 'start_date': 2000, 'end_date': '2004-12-31', 'frequency': 'anual', 'aggregation': 'ultimo'}, fetch=synthetic)
        self.assertEqual(frame['periodo'].tolist(), [2000, 2001, 2002, 2003, 2004])
        raw = synthetic('UNRATE', date(2000, 1, 1), date(2004, 12, 31))
        self.assertAlmostEqual(frame['desempleo'].iloc[0], raw['valor'].iloc[11])
        total, _ = fred_data({'series': 'UNRATE', 'start_date': 2000, 'end_date': '2000-12-31', 'frequency': 'anual', 'aggregation': 'suma'}, fetch=synthetic)
        self.assertAlmostEqual(total['desempleo'].iloc[0], raw['valor'].iloc[:12].sum())

    def test_original_daily_is_irregular_for_time_tools(self):
        frame, source = fred_data({'series': 'DGS10', 'start_date': '2020-01-01', 'end_date': '2020-03-31', 'frequency': 'original'}, fetch=synthetic)
        with self.assertRaises(EngineError) as caught:
            time_order(frame)
        self.assertEqual(caught.exception.code, 'IRREGULAR_PERIOD')

    def test_invalid_choices(self):
        for params in [{'frequency': 'horaria'}, {'aggregation': 'mediana'}, {'start_date': '2020-01-01', 'end_date': '2019-01-01'}]:
            with self.subTest(params=params), self.assertRaises(EngineError):
                fred_data(params, fetch=synthetic)


class TimeToolTests(unittest.TestCase):
    def test_growth_honours_periods(self):
        frame = pd.DataFrame({'periodo': [f'2020-{m:02d}-01' for m in range(1, 13)] + [f'2021-{m:02d}-01' for m in range(1, 13)],
                              'ipc': np.arange(100, 124, dtype=float)})
        from quantlabs.tools import run_tool
        result, outputs = run_tool('growth', {'data': frame}, {'column': 'ipc', 'output': 'yoy', 'periods': 12})
        data = outputs['data']
        self.assertTrue(data['yoy'].iloc[:12].isna().all())
        self.assertAlmostEqual(data['yoy'].iloc[12], (112 / 100 - 1) * 100)

    def test_quarterly_iso_dates_are_regular(self):
        frame = pd.DataFrame({'periodo': ['2020-01-01', '2020-04-01', '2020-07-01', '2020-10-01'], 'x': [1., 2, 3, 4]})
        time_order(frame)
        with self.assertRaises(EngineError):
            time_order(frame.drop(index=1))


class CatalogTests(unittest.TestCase):
    """Estructura del catálogo curado, sin red (la verificación con red queda registrada en el propio JSON)."""
    def setUp(self):
        self.catalog = json.loads((ROOT / 'packages/contracts/fredCatalog.json').read_text(encoding='utf-8'))
        self.items = self.catalog['items']

    def test_ids_aliases_and_groups(self):
        ids = [item['id'] for item in self.items]
        aliases = [item['alias'] for item in self.items]
        self.assertGreaterEqual(len(ids), 150)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(aliases), len(set(aliases)))
        for item in self.items:
            with self.subTest(id=item['id']):
                self.assertTrue(fred_source.SERIES_ID.fullmatch(item['id']))
                self.assertTrue(fred_source.ALIAS.fullmatch(item['alias']) and item['alias'] not in ('periodo', 'fecha'))
                self.assertIn(item['group'], self.catalog['groups'])
                self.assertIn(item['frequency'], ['diaria', 'semanal', 'mensual', 'trimestral', 'anual'])
                self.assertTrue(item['title'] and item['units'] and item['seasonal'])
        self.assertEqual(set(self.catalog['groups']), {item['group'] for item in self.items})

    def test_verification_record_matches_items(self):
        record = self.catalog['verification']
        self.assertEqual(record['kept'], len(self.items))
        self.assertFalse(set(record['dropped']) & {item['id'] for item in self.items})

    def test_catalog_alias_is_the_default_alias(self):
        self.assertEqual(parse_series('DEXMXUS\nTXUR'), {'DEXMXUS': 'tc_peso_dolar', 'TXUR': 'desempleo_texas'})

    def test_brain_recognises_titles_and_aliases(self):
        from quantlabs.brain.intents import detect_source
        kind, params, _ = detect_source('Con datos de FRED, la tasa de desempleo de Texas y el precio del petróleo Brent mensual desde 2010')
        self.assertEqual(kind, 'fred')
        self.assertEqual(params['series'].splitlines(), ['TXUR: desempleo_texas', 'DCOILBRENTEU: petroleo_brent'])
        kind, params, _ = detect_source('FRED: tc_peso_dolar y bono_10y_mexico')
        self.assertEqual([line.split(':')[0] for line in params['series'].splitlines()], ['DEXMXUS', 'IRLTLT01MXM156N'])
        self.assertEqual(detect_source('Tasa de desempleo de Texas del Banco Mundial')[0], 'worldbank')


class ExampleTests(unittest.TestCase):
    def test_fred_node_is_registered(self):
        self.assertIn('fred', NODE_CATALOG)
        schema = json.loads((ROOT / 'packages/contracts/project.schema.json').read_text())
        self.assertIn('fred', schema['$defs']['node']['properties']['type']['enum'])

    def test_examples_run_offline_with_injected_series(self):
        ids = [item['id'] for item in example_catalog() if item['id'].startswith('F')]
        self.assertEqual(ids, ['F01', 'F02', 'F03', 'F04', 'F05'])
        fred_source._cache.clear()
        with patch('quantlabs.fred_source.download', side_effect=synthetic):
            for example in ids:
                with self.subTest(example=example):
                    project = example_get(example)['project']
                    self.assertEqual({s['node_id'] for s in project['lesson']['steps']}, {n['id'] for n in project['nodes']})
                    result = execute(project)
                    failed = {k: v.get('error') for k, v in result['nodes'].items() if v['status'] != 'succeeded'}
                    self.assertEqual(failed, {})
                    self.assertEqual(result['nodes']['datos']['result']['source']['provider'], 'FRED · Federal Reserve Bank of St. Louis')
                    json.dumps(result, allow_nan=False)


if __name__ == '__main__':
    unittest.main()
