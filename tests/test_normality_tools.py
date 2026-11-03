import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from scipy import stats
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
from quantlabs.normality_tools import run_normality_tool
from quantlabs.core import EngineError,execute
class NormalityToolsTests(unittest.TestCase):
 def test_outer_alignment_keeps_all_years_and_missing_values(self):
  result,outputs=run_normality_tool('join_series',{'left':pd.DataFrame({'periodo':[2002,2000],'valor':[5,3]}),'right':pd.DataFrame({'periodo':[2001,2000],'valor':[8,6]})},{'left_name':'rate','right_name':'consumption'})
  self.assertEqual(outputs['data'].periodo.tolist(),[2000,2001,2002]);self.assertTrue(pd.isna(outputs['data'].rate.iloc[1]));self.assertEqual(result['alignment']['rows'],3)
 def test_join_rejects_duplicates_and_identical_aliases(self):
  frame=pd.DataFrame({'periodo':[2000,2000],'valor':[1,2]})
  with self.assertRaises(EngineError):run_normality_tool('join_series',{'left':frame,'right':frame},{})
  frame.periodo=[2000,2001]
  with self.assertRaises(EngineError):run_normality_tool('join_series',{'left':frame,'right':frame},{'left_name':'same','right_name':'same'})
 def test_mean_imputation_is_explicit_non_mutating_and_reports_affected_rows(self):
  frame=pd.DataFrame({'a':[1,np.nan,5],'b':[2,3,4]})
  result,out=run_normality_tool('impute_mean',{'data':frame},{'columns':'a'})
  np.testing.assert_allclose(out['data'].a,[1,3,5]);self.assertTrue(pd.isna(frame.a.iloc[1]));self.assertEqual(result['imputation'],[{'column':'a','mean':3.,'observed':2,'filled':1}]);pd.testing.assert_series_equal(out['data'].b,frame.b)
  with self.assertRaises(EngineError):run_normality_tool('impute_mean',{'data':pd.DataFrame({'a':[np.nan,np.nan]})},{'columns':'a'})
 def test_normality_matches_scipy_and_sample_formulas(self):
  values=np.array([1,2,2,4,7,8,10,13.]);result,_=run_normality_tool('normality',{'data':pd.DataFrame({'a':[*values,np.nan]})},{'columns':'a','alpha':.05})
  row=result['tables'][0]['rows'][0];self.assertEqual(row[:3],['a',8,1]);np.testing.assert_allclose(row[3:],[values.mean(),np.median(values),values.std(ddof=1),values.var(ddof=1)])
  for row,expected in zip(result['tables'][1]['rows'],[stats.shapiro(values),stats.jarque_bera(values)]):np.testing.assert_allclose(row[3:5],expected)
  np.testing.assert_allclose(result['normality'][0]['qq']['points'],np.column_stack(stats.probplot(values,fit=False)))
  self.assertEqual(sum(b['count'] for b in result['normality'][0]['histogram']['bins']),8)
 def test_constant_and_large_samples_do_not_produce_false_normality_conclusions(self):
  result,_=run_normality_tool('normality',{'data':pd.DataFrame({'a':[2.,2.,2.]})},{'columns':'a'})
  self.assertEqual(result['tables'][1]['rows'],[]);self.assertTrue(any('constante' in w for w in result['warnings']))
  result,_=run_normality_tool('normality',{'data':pd.DataFrame({'a':np.random.default_rng(4).normal(size=5001)})},{'columns':'a'})
  self.assertEqual(len(result['tables'][1]['rows']),1);self.assertEqual(result['normality'][0]['qq']['shown'],400)
 def test_offline_lesson_runs_every_branch_and_diagnoses_ols_residuals(self):
  import json
  project=json.loads((ROOT/'examples/normalidad-interes-consumo-usa.json').read_text())
  for node in project['nodes']:
   if node['id'] in ['interes','consumo']:
    node['type']='csv';node['parameters']={'content':'periodo,valor\n2000,1\n2001,2\n2002,\n2003,4\n2004,7\n2005,8\n2006,10\n2007,12\n','delimiter':','}
    if node['id']=='consumo':node['parameters']['content']='periodo,valor\n2000,4\n2001,3\n2002,8\n2003,5\n2004,12\n2005,15\n2006,14\n2007,19\n'
  run=execute(project);self.assertEqual(run['status'],'succeeded',run['nodes'])
  model=run['nodes']['ols']['result'];result=run['nodes']['residuos']['result'];self.assertEqual(result['normality'][0]['column'],'residuos');self.assertEqual(result['n'],model['n'])
