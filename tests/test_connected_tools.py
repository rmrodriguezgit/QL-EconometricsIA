"""Check real data flow, reusable tools and prefix execution, not closed recipes."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
from quantlabs.core import execute,validate_project,EngineError,NODE_CATALOG
from quantlabs.projects import example_get,example_catalog


def project(nodes,edges,lesson=None):
    return {'schema_version':'1.0.0','app_version':'0.4.0','title':'Fixture de herramientas','nodes':nodes,'edges':edges,**({'lesson':lesson} if lesson else {})}

def node(id,kind,parameters):return {'id':id,'type':kind,'node_version':'1.0.0','parameters':parameters,'position':{'x':0,'y':0}}

def edge(source,port,target,target_port):return {'id':f'{source}-{port}-{target}-{target_port}','source':source,'source_port':port,'target':target,'target_port':target_port}

class ConnectedToolsTests(unittest.TestCase):
    def test_output_schema_preserves_numeric_columns_even_with_missing_values(self):
        from quantlabs.tools import frame_result
        import pandas as pd
        frame=pd.DataFrame({'periodo':[2000,2001],'valor':[float('nan'),2.0],'pais':['MEX','MEX']})
        result=frame_result(frame,'')
        self.assertEqual(result['numeric_columns'],['periodo','valor'])
        self.assertEqual(result['preview'][0]['valor'],None)
        project=json.loads((ROOT/'examples/ingreso-consumo.json').read_text())
        run=execute(project)
        self.assertIn('numeric_columns',run['nodes']['data']['result']['output_previews']['data'])

    def test_every_catalog_example_is_a_real_connected_graph_with_all_steps(self):
        for example in example_catalog():
            with self.subTest(module=example['id']):
                p=example_get(example['id'])['project'];validate_project(p)
                self.assertGreaterEqual(len(p['nodes']),3)
                self.assertGreaterEqual(len(p['edges']),len(p['nodes'])-1)
                self.assertNotIn('experiment',[n['type'] for n in p['nodes']])
                self.assertEqual({s['node_id'] for s in p['lesson']['steps']},{n['id'] for n in p['nodes']})
                self.assertTrue(all(s['instruction'] and s['expected'] for s in p['lesson']['steps']))

    def test_examples_never_call_the_legacy_closed_recipe(self):
        with patch('quantlabs.experiments.run_experiment',side_effect=AssertionError('closed recipe called')):
            for example in example_catalog():
                result=execute(example_get(example['id'])['project'])
                self.assertEqual(result['status'],'succeeded',(example['id'],[(k,v.get('error')) for k,v in result['nodes'].items() if v['status']=='failed']))

    def test_swapping_the_source_changes_the_model_to_known_coefficients(self):
        p=example_get('C09')['project']
        p['nodes'][0]['type']='csv'
        p['nodes'][0]['parameters']={'content':'ingreso,consumo\n'+'\n'.join(f'{i},{3+2*i+[.1,-.1,-.1,.1][(i-1)%4]}' for i in range(1,17))}
        result=execute(p)['nodes']['modelo']['result']
        self.assertAlmostEqual(result['coefficients'][0]['estimate'],3)
        self.assertAlmostEqual(result['coefficients'][1]['estimate'],2)
        self.assertEqual(result['n'],16)

    def test_scaler_learns_only_from_training_and_test_is_not_refitted(self):
        content='x,y\n'+'\n'.join(f'{i if i<12 else 1000+i},{i*2}' for i in range(16))
        p=project([node('source','csv',{'content':content}),node('split','split',{'fraction':.75}),node('scale','standardize',{'columns':'x'}),node('apply','apply_scaler',{})],
                  [edge('source','data','split','data'),edge('split','train','scale','data'),edge('split','test','apply','data'),edge('scale','transformer','apply','transformer')])
        result=execute(p)
        transformer=result['nodes']['scale']['result']['transformer']
        self.assertEqual(transformer['n_fit'],12)
        self.assertAlmostEqual(transformer['mean'][0],np.arange(12).mean())
        first_test=result['nodes']['apply']['result']['records'][0]['x']
        self.assertAlmostEqual(first_test,(1012-np.arange(12).mean())/np.arange(12).std(ddof=0))
        self.assertGreater(first_test,100)

    def test_deflation_and_per_capita_use_the_connected_table(self):
        p=example_get('C02')['project'];r=execute(p)
        raw=r['nodes']['datos']['result']['records'][0]
        actual=r['nodes']['habitante']['result']['records'][0]
        self.assertAlmostEqual(actual['real'],raw['nominal']/raw['indice']*100)
        self.assertAlmostEqual(actual['real_per_capita'],actual['real']/raw['poblacion'])

    def test_prefix_runs_only_ancestors_and_handles_incomplete_unrelated_branch(self):
        p=example_get('C26')['project']
        p['edges']=[e for e in p['edges'] if e['target']!='red']
        r=execute(p,target_node='aplicar')
        self.assertEqual(set(r['nodes']),{'datos','particion','escalar','aplicar'})
        self.assertEqual(r['status'],'succeeded')
        with self.assertRaises(EngineError):execute(p)

    def test_missing_input_of_active_step_is_rejected(self):
        p=example_get('C26')['project'];p['edges']=[e for e in p['edges'] if not (e['target']=='aplicar' and e['target_port']=='transformer')]
        with self.assertRaises(EngineError):execute(p,target_node='aplicar')

    def test_every_guide_step_can_execute_independently_of_later_steps(self):
        for id in ['C09','C11','C15','C26']:
            p=example_get(id)['project']
            for step in p['lesson']['steps']:
                r=execute(p,target_node=step['node_id'])
                self.assertEqual(r['nodes'][step['node_id']]['status'],'succeeded',(id,step,r))
                self.assertEqual(r['manifest']['target_node'],step['node_id'])

    def test_invalid_port_types_and_real_cycle_are_rejected(self):
        p=example_get('C26')['project'];p['edges'][-1]['source_port']='model';p['edges'][-1]['source']='red'
        with self.assertRaises(EngineError):validate_project(p)
        p=project([node('a','lag',{'column':'x'}),node('b','difference',{'column':'x'})],[edge('a','data','b','data'),edge('b','data','a','data')])
        with self.assertRaisesRegex(EngineError,'ciclo'):validate_project(p)

    def test_log_domain_error_does_not_invent_a_result(self):
        p=project([node('data','csv',{'content':'x\n1\n-2\n3\n4\n'}),node('log','log',{'columns':'x'})],[edge('data','data','log','data')])
        r=execute(p)
        self.assertEqual(r['nodes']['log']['status'],'failed')
        self.assertEqual(r['nodes']['log']['error']['code'],'INVALID_PARAMETERS')

    def test_lesson_metadata_cannot_point_to_missing_or_duplicate_nodes(self):
        p=example_get('C09')['project'];p['lesson']['steps'][0]['node_id']='missing'
        with self.assertRaises(EngineError):validate_project(p)
        p=example_get('C09')['project'];p['lesson']['steps'][1]['node_id']=p['lesson']['steps'][0]['node_id']
        with self.assertRaises(EngineError):validate_project(p)

    def test_momentum_signal_cannot_use_current_or_future_returns(self):
        nodes=[node('data','csv',{'content':'retorno\n'+'\n'.join(str(v) for v in [1,-1,2,-2,3,-3,4,-4,5,-5,6,-6])}),node('signal','signal',{'lookback':3})]
        p=project(nodes,[edge('data','data','signal','data')]);first=execute(p)['nodes']['signal']['result']['records']
        p['nodes'][0]['parameters']['content']='retorno\n'+'\n'.join(str(v) for v in [1,-1,2,-2,3,999,999,999,999,999,999,999])
        second=execute(p)['nodes']['signal']['result']['records']
        self.assertEqual([v['senal'] for v in first[:6]],[v['senal'] for v in second[:6]])

    def test_covariance_change_preserves_coefficients(self):
        r=execute(example_get('C11')['project'])
        original=[row['estimate'] for row in r['nodes']['modelo']['result']['coefficients']]
        changed=[row[1] for row in r['nodes']['inferencia']['result']['tables'][0]['rows']]
        np.testing.assert_allclose(original,changed,rtol=1e-12)

    def test_time_gaps_are_not_silently_treated_as_adjacent_periods(self):
        p=project([node('data','csv',{'content':'periodo,x\n2000,1\n2001,2\n2003,3\n2004,4\n'}),node('lag','lag',{'column':'x'})],[edge('data','data','lag','data')])
        r=execute(p)
        self.assertEqual(r['nodes']['lag']['status'],'failed')
        self.assertEqual(r['nodes']['lag']['error']['code'],'IRREGULAR_PERIOD')

    def test_shared_registry_matches_public_schema(self):
        schema=json.loads((ROOT/'packages/contracts/project.schema.json').read_text())
        self.assertEqual(set(schema['$defs']['node']['properties']['type']['enum']),set(NODE_CATALOG))

if __name__=='__main__':unittest.main()
