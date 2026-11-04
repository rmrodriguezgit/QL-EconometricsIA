import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))

from quantlabs.__main__ import dispatch  # noqa: E402
from quantlabs.core import validate_project  # noqa: E402
from quantlabs.brain import llm, store  # noqa: E402
from quantlabs.brain.compiler import assign_columns, clean_parameters, compile_plan  # noqa: E402
from quantlabs.brain.intents import detect_source, detect_tools, rules_plan  # noqa: E402
from quantlabs.brain.knowledge import build_index  # noqa: E402
from quantlabs.brain.service import normalize_gaps, plan  # noqa: E402


class BrainCase(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        # Aísla memoria y fichas; Ollama apunta a un puerto cerrado para pruebas deterministas.
        self.env = patch.dict(os.environ, {'QL_BRAIN_DIR': self.folder.name, 'QL_BRAIN_OLLAMA_URL': 'http://127.0.0.1:9'})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.folder.cleanup()


class KnowledgeTests(BrainCase):
    def test_bm25_recovers_relevant_tools(self):
        hits = [hit['id'] for hit in build_index().search('regresión cuantílica de la mediana', kind='tool')]
        self.assertIn('quantile', hits[:3])
        hits = [hit['id'] for hit in build_index().search('volatilidad de retornos', kind='tool')]
        self.assertIn('garch', hits[:3])

    def test_examples_are_part_of_the_corpus(self):
        hits = build_index().search('cointegración y corrección de error', kind='example')
        self.assertTrue(hits and hits[0]['id'].startswith('C'))


class IntentTests(BrainCase):
    def test_sources(self):
        self.assertEqual(detect_source('inflación de México 2000-2020 del Banco Mundial')[:2],
                         ('worldbank', {'country': 'MEX', 'indicator': 'FP.CPI.TOTL.ZG', 'start': 2000, 'end': 2020}))
        self.assertEqual(detect_source('salarios con wage1')[0], 'wooldridge')
        self.assertEqual(detect_source('regresión con Wooldridge (puente)')[0], 'wooldridge')
        self.assertIsNone(detect_source('una regresión simple')[0])

    def test_tools_and_false_positives(self):
        kinds, _ = detect_tools('Pronostica con ARIMA y revisa autocorrelación')
        self.assertIn('arima', kinds)
        self.assertIn('acf', kinds)
        self.assertNotIn('correlation', kinds)
        kinds, gaps = detect_tools('Regresión con datos de Wooldridge')
        self.assertNotIn('regularized', kinds + [g['id'] for g in gaps])

    def test_unregistered_topics_become_gap_specs(self):
        _, gaps = detect_tools('Estima efectos fijos con datos de panel')
        self.assertEqual(gaps[0]['id'], 'panel')
        self.assertEqual(gaps[0]['outputs']['model'], 'FittedModel')


class CompilerTests(BrainCase):
    def test_rules_plan_compiles_to_a_valid_guided_project(self):
        project, report = compile_plan(rules_plan('regresión múltiple con diagnóstico de heterocedasticidad'))
        validate_project(project)
        self.assertEqual({s['node_id'] for s in project['lesson']['steps']}, {n['id'] for n in project['nodes']})
        types = [node['type'] for node in project['nodes']]
        self.assertEqual(types[0], 'synthetic')
        self.assertIn('multiple_ols', types)
        self.assertIn('diagnostics', types)
        self.assertEqual(project['lesson']['module'], 'IA')

    def test_unknown_tools_and_parameters_never_reach_the_graph(self):
        raw = {'title': 't', 'objective': 'o', 'missing': [], 'steps': [
            {'id': 'd', 'tool': 'synthetic', 'parameters': {'scenario': 'inexistente', 'n': '200', 'rm -rf': 1}, 'why': ''},
            {'id': 'magia', 'tool': 'python_exec', 'parameters': {'code': 'print(1)'}, 'why': 'ejecutar código'},
            {'id': 'm', 'tool': 'ols', 'parameters': {}, 'why': ''}]}
        project, report = compile_plan(raw)
        self.assertEqual([n['type'] for n in project['nodes']], ['synthetic', 'ols'])
        self.assertEqual(project['nodes'][0]['parameters']['scenario'], 'regression')
        self.assertEqual(project['nodes'][0]['parameters']['n'], 200)
        self.assertNotIn('rm -rf', project['nodes'][0]['parameters'])
        self.assertEqual(report['gaps'][0]['name'], 'python_exec')

    def test_source_is_added_and_unwirable_steps_are_dropped(self):
        project, report = compile_plan({'steps': [{'id': 'diag', 'tool': 'diagnostics', 'why': ''}, {'id': 'ols', 'tool': 'ols', 'why': ''}]})
        self.assertEqual([n['type'] for n in project['nodes']], ['synthetic', 'ols'])
        self.assertTrue(any(item['tool'] == 'diagnostics' for item in report['dropped']))

    def test_explicit_inputs_wire_two_models(self):
        raw = {'steps': [{'id': 'd', 'tool': 'synthetic', 'parameters': {'scenario': 'multiple'}, 'why': ''},
                         {'id': 'a', 'tool': 'ols', 'parameters': {'x': 'x', 'y': 'y'}, 'why': ''},
                         {'id': 'b', 'tool': 'multiple_ols', 'parameters': {}, 'why': ''},
                         {'id': 'c', 'tool': 'compare_models', 'inputs': {'first': 'a', 'second': 'b', 'data': 'd'}, 'why': ''}]}
        project, _ = compile_plan(raw)
        edges = {(e['source'], e['target_port']) for e in project['edges'] if e['target'] == 'c'}
        self.assertEqual(edges, {('a', 'first'), ('b', 'second'), ('d', 'data')})

    def test_model_consumers_skip_incompatible_models(self):
        raw = {'steps': [{'id': 'd', 'tool': 'synthetic', 'parameters': {'scenario': 'hetero'}, 'why': ''},
                         {'id': 'mco', 'tool': 'ols', 'why': ''}, {'id': 'pond', 'tool': 'wls', 'why': ''},
                         {'id': 'diag', 'tool': 'diagnostics', 'why': ''}]}
        project, report = compile_plan(raw)
        self.assertEqual(next(e['source'] for e in project['edges'] if e['target'] == 'diag'), 'mco')
        self.assertTrue(any('«pond»' in note for note in report['notes']))

    def test_rules_translate_prompt_nuances_to_parameters(self):
        project, _ = compile_plan(rules_plan('tamaño de muestra para una proporción con Bonferroni en contrastes múltiples'))
        params = {n['type']: n['parameters'] for n in project['nodes']}
        self.assertEqual(params['sample_size']['target'], 'proporcion')
        self.assertEqual(params['multiple_testing']['method'], 'bonferroni')

    def test_clean_parameters_respects_choices(self):
        params, notes = clean_parameters('split', {'method': 'aleatorio', 'fraction': 0.6})
        self.assertEqual((params['method'], params['fraction']), ('aleatorio', 0.6))
        params, notes = clean_parameters('split', {'method': 'kfold'})
        self.assertEqual(params['method'], 'temporal')
        self.assertTrue(notes)

    def test_column_repair_uses_real_preview(self):
        node = {'type': 'ols', 'parameters': {'x': 'ingreso', 'y': 'consumo', 'covariance': 'HC3'}}
        self.assertTrue(assign_columns(node, {'columns': ['educ', 'wage'], 'numeric_columns': ['educ', 'wage']}, 'salario y educación'))
        self.assertEqual((node['parameters']['x'], node['parameters']['y']), ('educ', 'wage'))


class ServiceTests(BrainCase):
    def test_auto_falls_back_to_rules_and_verifies_by_execution(self):
        result = plan({'prompt': 'Regresión múltiple con normalidad de residuos y un modelo de datos de panel'})
        self.assertEqual(result['engine'], 'rules')
        self.assertIn('Ollama', result['fallback_reason'])
        self.assertTrue(result['verification']['executed'])
        self.assertEqual(result['verification']['status'], 'succeeded')
        self.assertEqual([g['id'] for g in result['gaps']], ['panel'])
        self.assertEqual(store.list_gaps('pending')[0]['id'], 'panel')
        self.assertEqual(len(store.history()), 1)

    def test_explicit_ollama_engine_reports_unavailability(self):
        response = dispatch({'jsonrpc': '2.0', 'id': 1, 'method': 'brain.plan', 'params': {'prompt': 'regresión', 'engine': 'ollama'}})
        self.assertEqual(response['error']['data']['code'], 'BRAIN_UNAVAILABLE')

    def test_llm_plan_is_compiled_and_gaps_are_normalized(self):
        fake = {'title': 'Consumo', 'objective': 'o', 'steps': [
            {'id': 'datos', 'tool': 'synthetic', 'parameters': {'scenario': 'regression'}, 'why': 'datos'},
            {'id': 'mco', 'tool': 'ols', 'parameters': {'x': 'ingreso', 'y': 'consumo'}, 'why': 'estimar'},
            {'id': 'diag', 'tool': 'diagnostics', 'why': 'residuos'}],
            'missing': [{'name': 'Contraste de efectos fijos en panel', 'purpose': 'datos de panel'}, {'name': 'missing', 'purpose': ''}]}
        with patch.object(llm, 'plan', return_value=(fake, {'model': 'qwen-test', 'seconds': 1})):
            result = plan({'prompt': 'consumo e ingreso con panel'})
        self.assertEqual(result['engine'], 'ollama')
        self.assertEqual([n['type'] for n in result['project']['nodes']], ['synthetic', 'ols', 'diagnostics'])
        self.assertEqual([g['id'] for g in result['gaps']], ['panel'])

    def test_feedback_feeds_memory_and_rpc_endpoints(self):
        result = plan({'prompt': 'histograma y normalidad de una variable', 'engine': 'rules'})
        rated = dispatch({'jsonrpc': '2.0', 'id': 2, 'method': 'brain.feedback', 'params': {'id': result['blueprint_id'], 'value': 'up'}})
        self.assertEqual(rated['result']['feedback'], 'up')
        self.assertEqual(len(store.accepted()), 1)
        status = dispatch({'jsonrpc': '2.0', 'id': 3, 'method': 'brain.status', 'params': {}})['result']
        self.assertFalse(status['ollama']['reachable'])
        self.assertEqual(status['default_engine'], 'rules')
        bad = dispatch({'jsonrpc': '2.0', 'id': 4, 'method': 'brain.plan', 'params': {'prompt': 'x'}})
        self.assertEqual(bad['error']['data']['code'], 'INVALID_PARAMETERS')

    def test_normalize_gaps_deduplicates(self):
        gaps = normalize_gaps([{'name': 'Modelo VAR', 'purpose': 'vector autorregresivo'}, {'id': 'panel', 'name': 'x'}, {'id': 'panel', 'name': 'y'}])
        self.assertEqual(len([g for g in gaps if g['id'] == 'panel']), 1)

    def test_remote_ollama_requires_opt_in(self):
        with patch.dict(os.environ, {'QL_BRAIN_OLLAMA_URL': 'http://example.com:11434'}):
            self.assertIsNone(llm.available_models())


if __name__ == '__main__':
    unittest.main()
