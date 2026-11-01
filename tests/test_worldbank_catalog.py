"""Catalog completeness, offline fallback and source-aware queries without network."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))
import pandas as pd
import requests
from quantlabs import worldbank_catalog as catalog
from quantlabs.core import EngineError, world_bank
from quantlabs.__main__ import dispatch


def entry(code, name, source='2'):
    return {'id': code, 'name': name, 'unit': '', 'source': {'id': source, 'value': f'Fuente {source}'}}

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'catalog.json'
        self.environment = patch.dict(os.environ, {'QUANTLABS_CATALOG_CACHE': str(self.path)})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temp.cleanup()

    def test_all_pages_and_same_code_in_distinct_sources_preserved(self):
        responses = [({'page': 1, 'pages': 2, 'total': 3}, [entry('A', 'Índice'), entry('A', 'Índice', '37')]),
                     ({'page': 2, 'pages': 2, 'total': 3}, [entry('B', 'Consumo')])]
        with patch.object(catalog, 'fetch_page', side_effect=responses) as fetch:
            data, stale = catalog.get_catalog()
            self.assertEqual(fetch.call_count, 2)
        self.assertEqual(len(data['items']), 3)
        self.assertFalse(stale)
        with patch.object(catalog, 'fetch_page') as fetch:
            cached, _ = catalog.get_catalog()
            fetch.assert_not_called()
        self.assertEqual(data, cached)
        result = catalog.search_indicators({'query': 'indice'})
        self.assertEqual(result['total'], 2)

    def test_filter_and_pagination_do_not_hide_remaining_matches(self):
        rows = [entry(f'C{i:03}', f'Consumo {i}') for i in range(205)]
        with patch.object(catalog, 'fetch_page', return_value=({'page': 1, 'pages': 1, 'total': 205}, rows)):
            first = catalog.search_indicators({})
        second = catalog.search_indicators({'page': 2})
        third = catalog.search_indicators({'page': 3})
        self.assertEqual((first['total'], first['pages']), (205, 3))
        self.assertEqual([len(result['items']) for result in [first, second, third]], [100, 100, 5])
        ids = [item['id'] for result in [first, second, third] for item in result['items']]
        self.assertEqual(len(set(ids)), 205)

    def test_partial_download_never_replaces_valid_cache_and_returns_stale(self):
        with patch.object(catalog, 'fetch_page', return_value=({'page': 1, 'pages': 1, 'total': 1}, [entry('A', 'Ingreso')])):
            original, _ = catalog.get_catalog()
        saved = self.path.read_bytes()
        with patch.object(catalog, 'fetch_page', return_value=({'page': 1, 'pages': 1, 'total': 2}, [entry('B', 'Incompleto')])):
            data, stale = catalog.get_catalog(refresh=True)
        self.assertTrue(stale)
        self.assertEqual(original, data)
        self.assertEqual(saved, self.path.read_bytes())

    def test_network_failure_without_cache_has_actionable_error(self):
        with patch.object(catalog, 'fetch_page', side_effect=requests.Timeout()):
            with self.assertRaises(EngineError) as caught:
                catalog.get_catalog()
        self.assertEqual(caught.exception.code, 'CATALOG_UNAVAILABLE')
        self.assertFalse(self.path.exists())

    def test_invalid_search_rejected_before_network(self):
        with patch.object(catalog, 'get_catalog') as get:
            for parameters in [{'page': 0}, {'page': True}, {'query': []}, {'refresh': 'yes'}]:
                with self.assertRaises(EngineError):
                    catalog.search_indicators(parameters)
            get.assert_not_called()

    def test_rpc_catalog_method(self):
        with patch.object(catalog, 'search_indicators', return_value={'items': [], 'total': 0}) as search:
            result = dispatch({'jsonrpc': '2.0', 'id': 10, 'method': 'worldbank.indicators', 'params': {'query': 'PIB'}})
        search.assert_called_once_with({'query': 'PIB'})
        self.assertEqual(result['result']['total'], 0)

    def test_selected_source_and_mixed_case_code_reach_the_data_query(self):
        client = Mock()
        client.get_dataframe.return_value = pd.DataFrame({'valor': [3., 4.]}, index=pd.Index(['2021', '2020'], name='date'))
        module = Mock()
        module.Client.return_value = client
        with patch.dict(sys.modules, {'wbdata': module}):
            frame, source = world_bank({'indicator': '1.0.HCount.1.90usd', 'source': 37, 'start': 2020, 'end': 2021})
        self.assertEqual(client.get_dataframe.call_args.kwargs['source'], 37)
        self.assertEqual(client.get_dataframe.call_args.args[0], {'1.0.HCount.1.90usd': 'valor'})
        self.assertEqual(frame['periodo'].tolist(), [2020, 2021])
        self.assertEqual(source['source_id'], 37)

if __name__ == '__main__':
    unittest.main()
