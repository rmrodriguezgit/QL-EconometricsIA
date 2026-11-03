import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
from quantlabs.box_plot import box_plot
from quantlabs.core import EngineError,execute
class BoxPlotTests(unittest.TestCase):
 def test_known_quartiles_whiskers_outliers_and_missing(self):
  frame=pd.DataFrame({'rate':[1,2,3,4,5,6,7,100,np.nan]});data=box_plot(frame,{'column':'rate','color':'#008000'})
  self.assertEqual((data['q1'],data['median'],data['q3']),(2.75,4.5,6.25));self.assertEqual((data['whisker_low'],data['whisker_high']),(1,7));self.assertEqual(data['outliers'],[100]);self.assertEqual((data['n'],data['missing']),(8,1));self.assertEqual(data['color'],'#008000');self.assertTrue(pd.isna(frame.rate.iloc[-1]))
 def test_constant_singleton_negative_and_interpolated_quartiles(self):
  for values in [[3],[2,2,2],[-5,-4,-3,-1],[0,100,100,100]]:
   data=box_plot(pd.DataFrame({'v':values}),{'column':'v'});np.testing.assert_allclose([data['q1'],data['median'],data['q3']],np.quantile(values,[.25,.5,.75],method='linear'));self.assertLessEqual(data['whisker_low'],data['q1']);self.assertGreaterEqual(data['whisker_high'],data['q3'])
 def test_invalid_values_and_colors(self):
  for frame,params in [(pd.DataFrame({'v':[np.nan]}),{'column':'v'}),(pd.DataFrame({'v':[1,np.inf]}),{'column':'v'}),(pd.DataFrame({'v':['a','b']}),{'column':'v'}),(pd.DataFrame({'v':[1,2]}),{'column':'missing'}),(pd.DataFrame({'v':[1,2]}),{'column':'v','color':'red'})]:
   with self.assertRaises(EngineError):box_plot(frame,params)
 def test_connected_csv(self):
  p={'schema_version':'1.0.0','app_version':'0.8.1','title':'Boxplot','nodes':[{'id':'data','type':'csv','node_version':'1.0.0','parameters':{'content':'rate\n1\n2\n3\n4\n5\n100\n','delimiter':','},'position':{'x':0,'y':0}},{'id':'box','type':'boxplot','node_version':'1.0.0','parameters':{'column':'rate'},'position':{'x':300,'y':0}}],'edges':[{'id':'link','source':'data','source_port':'data','target':'box','target_port':'data'}]}
  result=execute(p);self.assertEqual(result['status'],'succeeded',result['nodes']);self.assertEqual(result['nodes']['box']['result']['outliers'],[100])
