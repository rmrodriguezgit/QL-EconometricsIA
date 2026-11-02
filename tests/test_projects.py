"""Workspace lifecycle, conflicts, draft validation and catalog coverage."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'engine'))
from quantlabs.core import EngineError, validate_project, execute
from quantlabs.projects import dispatch_files, example_catalog, example_get, folder, mutation_lock
from quantlabs.audit import system_audit
from quantlabs.__main__ import dispatch

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, {'QUANTLABS_WORKSPACE': self.temp.name})
        self.environment.start()
        self.project = json.loads((ROOT / 'examples/ingreso-consumo.json').read_text())
    def tearDown(self):
        self.environment.stop(); self.temp.cleanup()
    def call(self, method, **params):
        return dispatch_files(method, params)
    def test_save_read_update_trash_restore(self):
        saved=self.call('projects.save',project=self.project)
        self.assertEqual(self.call('projects.read',id=saved['id'])['project'],self.project)
        changed={**self.project,'title':'Título editado'}
        updated=self.call('projects.save',project=changed,id=saved['id'],expected_revision=saved['revision'])
        self.assertNotEqual(saved['revision'],updated['revision'])
        self.call('projects.delete',id=updated['id'],expected_revision=updated['revision'])
        self.assertEqual(self.call('projects.list')['items'],[])
        self.assertEqual(len(self.call('projects.list',trash=True)['items']),1)
        restored=self.call('projects.restore',id=updated['id'],expected_revision=updated['revision'])
        self.assertEqual(restored['project'],changed)
        self.assertEqual(len(self.call('projects.list')['items']),1)
    def test_stale_revision_never_overwrites(self):
        saved=self.call('projects.save',project=self.project)
        updated=self.call('projects.save',project={**self.project,'title':'Primera edición'},id=saved['id'],expected_revision=saved['revision'])
        with self.assertRaises(EngineError) as caught:
            self.call('projects.save',project={**self.project,'title':'Edición obsoleta'},id=saved['id'],expected_revision=saved['revision'])
        self.assertEqual(caught.exception.code,'FILE_CONFLICT')
        self.assertEqual(self.call('projects.read',id=saved['id'])['revision'],updated['revision'])
    def test_path_traversal_rejected(self):
        for value in ['../../README','../files/a','not-a-uuid','/tmp/file',None]:
            with self.subTest(value=value), self.assertRaises(EngineError):
                self.call('projects.read',id=value)
    def test_corrupt_file_is_reported_and_preserved(self):
        saved=self.call('projects.save',project=self.project)
        path=folder()/f"{saved['id']}.json"
        path.write_text('{invalid JSON')
        result=self.call('projects.list')
        self.assertEqual(result['items'],[])
        self.assertEqual(result['unreadable'],[path.name])
        self.assertEqual(path.read_text(),'{invalid JSON')
    def test_valid_json_with_missing_metadata_is_reported_not_crashed(self):
        saved=self.call('projects.save',project=self.project)
        path=folder()/f"{saved['id']}.json"
        data=json.loads(path.read_text());del data['created_at'];path.write_text(json.dumps(data))
        self.assertEqual(self.call('projects.list')['unreadable'],[path.name])

    def test_failed_atomic_replace_preserves_old_project(self):
        saved=self.call('projects.save',project=self.project)
        with patch('quantlabs.projects.os.replace',side_effect=OSError('read only')):
            with self.assertRaises(EngineError):
                self.call('projects.save',project={**self.project,'title':'Unwritten'},id=saved['id'],expected_revision=saved['revision'])
        self.assertEqual(self.call('projects.read',id=saved['id'])['project'],self.project)
    def test_drafts_can_be_saved_but_not_executed(self):
        for draft in [{**self.project,'nodes':[],'edges':[]},{**self.project,'edges':[]}]:
            saved=self.call('projects.save',project=draft)
            self.assertEqual(saved['project'],draft)
            with self.assertRaises(EngineError): validate_project(draft)
    def test_duplicate_edge_ids_rejected(self):
        self.project['edges'][1]['id']=self.project['edges'][0]['id']
        with self.assertRaises(EngineError): validate_project(self.project)
    def test_runtime_audit_does_not_hide_pending_work(self):
        report=system_audit()
        status={check['id']:check['status'] for check in report['checks']}
        self.assertEqual(status['catalog'],'ok');self.assertEqual(status['references'],'ok')
        self.assertEqual(status['storage'],'ok');self.assertEqual(status['desktop'],'pending')
        self.assertEqual(status['curriculum'],'pending')
    def test_mutation_lock_blocks_another_process(self):
        import subprocess
        code = """import json,sys
from quantlabs.projects import dispatch_files
from quantlabs.core import EngineError
try:
    dispatch_files('projects.save', {'project':json.load(sys.stdin)})
except EngineError as error:
    print(error.code)
"""
        with mutation_lock():
            process=subprocess.run([sys.executable,'-c',code],input=json.dumps(self.project),text=True,capture_output=True,timeout=30,cwd=ROOT,env={**os.environ,'PYTHONPATH':str(ROOT/'engine')})
        self.assertEqual(process.returncode,0,process.stderr)
        self.assertEqual(process.stdout.strip(),'FILE_BUSY')
        self.assertEqual(self.call('projects.list')['items'],[])

    def test_rpc_returns_storage_errors(self):
        response=dispatch({'jsonrpc':'2.0','id':9,'method':'projects.read','params':{'id':'../other'}})
        self.assertEqual(response['error']['data']['code'],'INVALID_FILE_ID')

class ExampleCatalogTests(unittest.TestCase):
    def test_every_module_and_chapter_has_an_example(self):
        examples=example_catalog()
        self.assertEqual({item['id'] for item in examples},{f'C{i:02}' for i in range(1,29)})
        self.assertEqual({ref for item in examples for ref in item['references']},{f'B{i:02}' for i in range(1,37)})
        self.assertTrue(all(item['scope'] and item['question'] for item in examples))
    def test_all_28_examples_execute_with_finite_json_and_interpretation(self):
        for example in example_catalog():
            with self.subTest(topic=example['id']):
                result=execute(example_get(example['id'])['project'])
                node=result['nodes']['reporte']
                self.assertEqual(node['status'],'succeeded',node.get('error'))
                self.assertEqual(node['result']['tool_type'],'report')
                self.assertTrue(node['result'].get('interpretation') or node['result'].get('note') or node['result'].get('teaching_note'))
                json.dumps(result,allow_nan=False)
    def test_known_properties_of_teaching_generators(self):
        from quantlabs.experiments import run_experiment
        def metrics(topic): return {metric['label']:metric['value'] for metric in run_experiment({'topic':topic,'seed':42,'n':300})['metrics']}
        self.assertAlmostEqual(metrics('C05')['probabilidad_condicional_Bayes'],.0095/(.0095+.0495))
        self.assertGreater(metrics('C20')['varianza_PCA_dos_componentes'],.85)
        self.assertGreater(metrics('C24')['acierto_estados_permutacion'],.9)
        self.assertGreater(metrics('C25')['silueta'],.5)
        neural=metrics('C26')
        self.assertLess(neural['RMSE_red_neuronal'],neural['RMSE_lineal'])

    def test_unknown_topic_and_example_are_rejected(self):
        with self.assertRaises(EngineError): example_get('../C01')
        project=example_get('C01')['project'];project['nodes'][0]['parameters']['scenario']='C99'
        self.assertEqual(execute(project)['nodes']['datos']['status'],'failed')

if __name__ == '__main__': unittest.main()
