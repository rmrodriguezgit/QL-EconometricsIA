"""Offline integration checks against the installed, pinned textbook package."""
import copy
import json
from pathlib import Path
import sys
import unittest
import numpy as np
import statsmodels.api as sm
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
from quantlabs.core import execute,EngineError,VERSION
from quantlabs.wooldridge_source import load_wooldridge,DATASETS

def source_project(name):
 return {'schema_version':'1.0.0','app_version':VERSION,'title':'Wooldridge fixture','nodes':[{'id':'data','type':'wooldridge','node_version':'1.0.0','parameters':{'dataset':name},'position':{'x':0,'y':0}}],'edges':[]}

class WooldridgeTests(unittest.TestCase):
 def test_every_dataset_loads_and_exposes_current_variables_including_large_tables(self):
  self.assertEqual(len(DATASETS),115)
  for name,metadata in DATASETS.items():
   with self.subTest(dataset=name):
    result=execute(source_project(name))['nodes']['data']
    self.assertEqual(result['status'],'succeeded',result.get('error'))
    data=result['result'];self.assertEqual(data['n'],metadata['rows'])
    self.assertEqual(data['columns'],[col['name'] for col in metadata['columns']])
    self.assertEqual(data['numeric_columns'],[col['name'] for col in metadata['columns'] if col['numeric']])
    self.assertEqual(data['source']['dataset'],name)
    self.assertEqual(data['source']['package_version'],'0.5.0')
    self.assertEqual(data['records_complete'],metadata['rows']<=10000)
    if not data['records_complete']:self.assertEqual(len(data['records']),1000)
 def test_invalid_names_and_paths_are_rejected(self):
  for value in ['../wage1','unknown',None,12,'wage1.csv','']:
   with self.assertRaises(EngineError):load_wooldridge(value)
 def test_loader_returns_an_independent_copy(self):
  first=load_wooldridge('wage1');expected=first.loc[0,'wage'];first.loc[0,'wage']=-999
  self.assertEqual(load_wooldridge('wage1').loc[0,'wage'],expected)
 def test_switching_dataset_changes_schema_and_invalid_variables_are_not_reused(self):
  p=source_project('wage1');p['nodes'].append({'id':'model','type':'ols','node_version':'1.0.0','parameters':{'x':'educ','y':'wage','covariance':'HC3'},'position':{'x':320,'y':0}});p['edges']=[{'id':'link','source':'data','source_port':'data','target':'model','target_port':'data'}]
  result=execute(p);self.assertEqual(result['status'],'succeeded')
  frame=load_wooldridge('wage1')[['educ','wage']].dropna();expected=sm.OLS(frame.wage,sm.add_constant(frame.educ)).fit(cov_type='HC3')
  np.testing.assert_allclose([row['estimate'] for row in result['nodes']['model']['result']['coefficients']],expected.params,rtol=1e-10)
  p['nodes'][0]['parameters']['dataset']='card';card=execute(p);self.assertEqual(card['nodes']['data']['result']['n'],3010)
  self.assertIn('nearc4',card['nodes']['data']['result']['numeric_columns'])
  p['nodes'][0]['parameters']['dataset']='hprice1';changed=execute(p)
  self.assertEqual(changed['nodes']['model']['status'],'failed')
  self.assertNotIn('wage',changed['nodes']['data']['result']['numeric_columns'])

 def test_multiple_ols_example_matches_statsmodels_and_has_valid_regressors(self):
  p=json.loads((ROOT/'examples/wooldridge-wage1-multiple-ols.json').read_text())
  result=execute(p)
  self.assertEqual(result['status'],'succeeded',result['nodes'])
  frame=load_wooldridge('wage1')[['wage','educ','exper','tenure']].dropna()
  expected=sm.OLS(frame.wage,sm.add_constant(frame[['educ','exper','tenure']])).fit(cov_type='HC3')
  rows=result['nodes']['modelo']['result']['tables'][0]['rows']
  self.assertEqual([row[0] for row in rows],['const','educ','exper','tenure'])
  np.testing.assert_allclose([row[1] for row in rows],expected.params,rtol=1e-10)
  self.assertEqual(result['nodes']['modelo']['result']['n'],526)
