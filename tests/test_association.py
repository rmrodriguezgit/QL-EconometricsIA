import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
from quantlabs.tools import run_tool
from quantlabs.core import EngineError,execute
class AssociationTests(unittest.TestCase):
 def test_common_rows_and_matrices_match_numpy(self):
  frame=pd.DataFrame({'x':[1,2,3,4,np.nan],'y':[2,np.nan,7,9,10]})
  result,_=run_tool('correlation',{'data':frame},{'columns':'x,y'})
  values=frame[['x','y']].dropna().to_numpy()
  self.assertEqual((result['n'],result['missing']),(3,2))
  np.testing.assert_allclose([row[1:] for row in result['tables'][0]['rows']],np.corrcoef(values.T))
  np.testing.assert_allclose([row[1:] for row in result['tables'][1]['rows']],np.cov(values.T,ddof=1))
 def test_two_rows_and_constant_columns(self):
  frame=pd.DataFrame({'x':[1.,2.],'y':[5.,5.]});result,_=run_tool('correlation',{'data':frame},{'columns':'x,y'})
  self.assertIsNone(result['tables'][0]['rows'][0][2]);self.assertTrue(result['warnings'])
  self.assertEqual(result['tables'][1]['rows'],[['x',.5,0.],['y',0.,0.]])
 def test_invalid_columns_insufficient_rows_and_infinity(self):
  for frame,columns in [(pd.DataFrame({'x':[1,2]}),'x'),(pd.DataFrame({'x':[1,np.nan],'y':[2,3]}),'x,y'),(pd.DataFrame({'x':[1,np.inf],'y':[2,3]}),'x,y'),(pd.DataFrame({'x':[1,2],'y':[2,3]}),'x,x')]:
   with self.assertRaises(EngineError):run_tool('covariance_matrix',{'data':frame},{'columns':columns})
 def test_covariance_node_runs_in_connected_project(self):
  p={'schema_version':'1.0.0','app_version':'0.8.4','title':'Covarianza','nodes':[{'id':'data','type':'csv','node_version':'1.0.0','parameters':{'content':'x,y\n1,2\n2,4\n3,6\n','delimiter':','},'position':{'x':0,'y':0}},{'id':'cov','type':'covariance_matrix','node_version':'1.0.0','parameters':{'columns':'x,y'},'position':{'x':300,'y':0}}],'edges':[{'id':'link','source':'data','source_port':'data','target':'cov','target_port':'data'}]}
  run=execute(p);self.assertEqual(run['status'],'succeeded',run['nodes']);self.assertEqual(run['nodes']['cov']['result']['tables'][0]['rows'],[['x',1.,2.],['y',2.,4.]])
