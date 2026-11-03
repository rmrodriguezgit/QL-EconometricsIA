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
 def test_conditional_mean_matches_numpy_where_and_preserves_original(self):
  values=np.array([1.,14.5,15.,20.,np.nan]);frame=pd.DataFrame({'rate':values,'other':[1,2,3,4,5]})
  from operator import gt,ge,lt,le,eq,ne
  for op,comparison in [('>',gt),('>=',ge),('<',lt),('<=',le),('==',eq),('!=',ne)]:
   result,data=box_plot(frame,{'column':'rate','operator':op,'threshold':14.5},with_data=True)
   mask=comparison(values,14.5)&~np.isnan(values)
   expected=np.where(mask,np.nanmean(values),values)
   np.testing.assert_allclose(data.rate,expected,equal_nan=True);pd.testing.assert_series_equal(data.other,frame.other)
   self.assertEqual(result['replacement']['matched'],int(mask.sum()));self.assertEqual(result['replacement']['mean'],np.nanmean(values));self.assertEqual(result['missing'],1)
   np.testing.assert_allclose([result['q1'],result['median'],result['q3']],np.quantile(expected[~np.isnan(expected)],[.25,.5,.75]))
  np.testing.assert_allclose(frame.rate,values,equal_nan=True)
 def test_conditional_boundaries_disabled_and_invalid_parameters(self):
  frame=pd.DataFrame({'rate':[14.,14.5,15.]})
  self.assertEqual(box_plot(frame,{'column':'rate','operator':'>','threshold':14.5})['replacement']['matched'],1)
  self.assertEqual(box_plot(frame,{'column':'rate','operator':'>=','threshold':14.5})['replacement']['matched'],2)
  result,data=box_plot(frame,{'column':'rate'},with_data=True);self.assertNotIn('replacement',result);pd.testing.assert_frame_equal(data,frame)
  for params in [{'operator':'eval(x)'},{'operator':'>=','threshold':float('nan')},{'operator':'>=','threshold':float('inf')}]:
   with self.assertRaises(EngineError):box_plot(frame,{'column':'rate',**params})
 def test_output_data_can_feed_a_following_node(self):
  import json
  p=json.loads((ROOT/'examples/normalidad-interes-consumo-usa.json').read_text())
  # A small complete graph proves that the visible box and the forwarded data agree.
  p.pop('lesson',None);p['nodes']=[{'id':'data','type':'csv','node_version':'1.0.0','parameters':{'content':'rate\n1\n14.5\n15\n20\n','delimiter':','},'position':{'x':0,'y':0}},{'id':'box','type':'boxplot','node_version':'1.0.0','parameters':{'column':'rate','operator':'>=','threshold':14.5},'position':{'x':300,'y':0}},{'id':'summary','type':'describe','node_version':'1.0.0','parameters':{},'position':{'x':600,'y':0}}];p['edges']=[{'id':'first','source':'data','source_port':'data','target':'box','target_port':'data'},{'id':'second','source':'box','source_port':'data','target':'summary','target_port':'data'}]
  run=execute(p);self.assertEqual(run['status'],'succeeded',run['nodes']);self.assertEqual(run['nodes']['box']['result']['replacement']['matched'],3)
  expected=np.mean([1,np.mean([1,14.5,15,20]),np.mean([1,14.5,15,20]),np.mean([1,14.5,15,20])]);self.assertAlmostEqual(run['nodes']['summary']['result']['rows'][0]['mean'],expected)
