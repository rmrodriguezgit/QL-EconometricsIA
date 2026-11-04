import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))

from quantlabs.core import EngineError, parse_indicator_map, world_bank_multi, execute  # noqa: E402
from quantlabs.gap_tools import pairplot  # noqa: E402
from quantlabs.brain.intents import detect_source, rules_plan  # noqa: E402


class FakeClient:
    """Imita wbdata.Client.get_series(keep_levels=True): Serie con índice (country, date)."""

    def __init__(self, missing=()):
        self.calls, self.missing = [], set(missing)

    def get_series(self, code, country, date, source, parse_dates, name, keep_levels, skip_cache):
        self.calls.append((code, tuple(country), date, source, name))
        if code in self.missing:
            raise RuntimeError('404')
        names = {'USA': 'United States', 'MEX': 'Mexico'}
        years = [str(y) for y in range(int(date[0]), int(date[1]) + 1)]
        index = pd.MultiIndex.from_product([[names[c] for c in country], years], names=['country', 'date'])
        values = np.arange(len(index), dtype=float) + len(self.calls)
        if len(self.calls) == 1:
            values[0] = np.nan  # un año sin dato solo en la primera serie
        return pd.Series(values, index=index, name=name)


class WorldBankMultiTests(unittest.TestCase):
    def test_parse_matches_wbdata_mapping(self):
        mapping = parse_indicator_map('GC.REV.SOCL.CN: social_contri\nFR.INR.LEND: lending_rate; NY.GDP.MKTP.KD.ZG = gdp_growth, NE.CON.TOTL.CD')
        self.assertEqual(mapping, {'GC.REV.SOCL.CN': 'social_contri', 'FR.INR.LEND': 'lending_rate',
                                   'NY.GDP.MKTP.KD.ZG': 'gdp_growth', 'NE.CON.TOTL.CD': 'ne_con_totl_cd'})
        self.assertEqual(parse_indicator_map({'FR.INR.LEND': 'lending_rate'}), {'FR.INR.LEND': 'lending_rate'})
        for bad in ['FR.INR.LEND: 1rate', 'A: x\nB: x', 'A: periodo', '', 'código raro!: x']:
            with self.assertRaises(EngineError):
                parse_indicator_map(bad)

    def test_single_country_returns_one_column_per_alias(self):
        client = FakeClient()
        frame, source = world_bank_multi({'countries': 'usa', 'start': 2000, 'end': 2004}, client=client)
        self.assertEqual(list(frame.columns), ['periodo', 'social_contri', 'lending_rate', 'gdp_growth', 'fin_cons'])
        self.assertEqual(frame['periodo'].tolist(), [2000, 2001, 2002, 2003, 2004])
        self.assertEqual(sorted(call[0] for call in client.calls), sorted(['GC.REV.SOCL.CN', 'FR.INR.LEND', 'NY.GDP.MKTP.KD.ZG', 'NE.CON.TOTL.CD']))
        self.assertTrue(all(call[1] == ('USA',) and call[3] == 2 for call in client.calls))
        self.assertEqual(source['countries'], ['USA'])
        self.assertEqual(sum(source['observations_per_indicator'].values()), 4 * 5 - 1)

    def test_several_countries_add_pais_column(self):
        frame, _ = world_bank_multi({'countries': 'USA, MEX', 'indicators': 'FR.INR.LEND: lending_rate', 'start': 2010, 'end': 2011},
                                    client=FakeClient())
        self.assertEqual(list(frame.columns), ['pais', 'periodo', 'lending_rate'])
        self.assertEqual(set(frame['pais']), {'Mexico', 'United States'})

    def test_failed_indicator_names_code_and_alias(self):
        with self.assertRaises(EngineError) as error:
            world_bank_multi({'countries': 'USA', 'indicators': 'FR.INR.LEND: tasa\nXX.BAD: malo', 'start': 2000, 'end': 2001},
                             client=FakeClient(missing={'XX.BAD'}))
        self.assertIn('XX.BAD (malo)', str(error.exception))

    def test_countries_are_validated(self):
        with self.assertRaises(EngineError):
            world_bank_multi({'countries': 'US', 'start': 2000, 'end': 2001}, client=FakeClient())


class PairplotTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(1)
        x = rng.normal(size=200)
        self.frame = pd.DataFrame({'periodo': range(200), 'x': x, 'y': 2 * x + rng.normal(size=200), 'z': rng.normal(size=200),
                                   'pais': np.where(x > 0, 'A', 'B')})
        self.frame.loc[:20, 'z'] = np.nan

    def test_pairwise_correlations_match_pandas(self):
        result, outputs = pairplot(self.frame, {'group': 'pais'})
        data = result['pairplot']
        self.assertEqual(data['columns'], ['x', 'y', 'z'])  # periodo excluido por defecto
        self.assertEqual(data['groups'], ['A', 'B'])
        np.testing.assert_allclose(np.array(data['correlation'], dtype=float), self.frame[['x', 'y', 'z']].corr().to_numpy(), atol=1e-12)
        self.assertEqual([row[2] for row in result['tables'][1]['rows']], [200, 179, 179])
        for diag in data['diagonal']:
            self.assertEqual(sum(map(sum, diag['counts'])), diag['n'])
        self.assertIn('plot', outputs)
        within = result['tables'][2]['rows']
        a = self.frame[self.frame['pais'] == 'A']
        self.assertAlmostEqual(next(row[4] for row in within if row[:3] == ['A', 'x', 'y']), a['x'].corr(a['y']), places=12)

    def test_sampling_and_validation(self):
        result, _ = pairplot(self.frame, {'columns': 'x,y', 'max_points': 50})
        self.assertEqual(len(result['pairplot']['points']), 50)
        self.assertTrue(result['warnings'])
        for params in ({'columns': 'x'}, {'columns': 'x,y', 'group': 'x'}, {'group': 'periodo'}):
            with self.assertRaises(EngineError):
                pairplot(self.frame, params)

    def test_runs_inside_a_project(self):
        project = {'schema_version': '1.0.0', 'app_version': '0.13.0', 'title': 'Pairplot', 'nodes': [
                   {'id': 'd', 'type': 'synthetic', 'node_version': '1.0.0', 'position': {'x': 0, 'y': 0}, 'parameters': {'scenario': 'multiple'}},
                   {'id': 'p', 'type': 'pairplot', 'node_version': '1.0.0', 'position': {'x': 1, 'y': 0}, 'parameters': {}}],
                   'edges': [{'id': 'e', 'source': 'd', 'source_port': 'data', 'target': 'p', 'target_port': 'data'}]}
        run = execute(project)
        self.assertEqual(run['nodes']['p']['status'], 'succeeded')
        self.assertGreaterEqual(len(run['nodes']['p']['result']['pairplot']['columns']), 2)


class BrainTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'QL_BRAIN_DIR': self.folder.name, 'QL_BRAIN_OLLAMA_URL': 'http://127.0.0.1:9'})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.folder.cleanup()

    def test_several_indicators_choose_multi_source(self):
        kind, params, _ = detect_source('Crecimiento del PIB, tasa de préstamo y contribuciones sociales de Estados Unidos')
        self.assertEqual(kind, 'worldbank_multi')
        self.assertEqual(params['countries'], 'USA')
        self.assertIn('FR.INR.LEND: lending_rate', params['indicators'])
        self.assertEqual(detect_source('inflación de México del Banco Mundial')[0], 'worldbank')

    def test_indicator_names_do_not_trigger_tools(self):
        plan = rules_plan('Pairplot del crecimiento del PIB y tasa de préstamo de Estados Unidos y México por país')
        tools = [step['tool'] for step in plan['steps']]
        self.assertEqual(tools, ['worldbank_multi', 'describe', 'pairplot', 'report'])
        self.assertEqual(plan['steps'][2]['parameters']['group'], 'pais')


if __name__ == '__main__':
    unittest.main()
