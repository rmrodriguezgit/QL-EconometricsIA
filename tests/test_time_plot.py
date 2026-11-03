import sys
from pathlib import Path
import unittest
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
from quantlabs.time_plot import time_plot
from quantlabs.core import EngineError,execute
class TimePlotTests(unittest.TestCase):
 def test_sort_negative_values_missing_years_and_values(self):
  data=time_plot(pd.DataFrame({'year':[2004,2000,2001,2003,None],'rate':[-.4,2,None,5,8]}),{'time':'year','value':'rate'})
  self.assertEqual(data['n'],3);self.assertEqual(data['missing'],1);self.assertEqual(data['missing_time'],1);self.assertEqual(data['gaps'],1)
  self.assertEqual([(p['x'],p['y']) for p in data['points']],[(2000,2),(2001,None),(2002,None),(2003,5),(2004,-.4)])
 def test_iso_dates_and_invalid_dates(self):
  data=time_plot(pd.DataFrame({'date':['2020-02-29','2019-12-01'],'rate':[3,2]}),{'time':'date','value':'rate','time_mode':'date'})
  self.assertEqual(data['points'][0]['label'],'2019-12-01')
  for date in ['2020-02-30','12/01/2020']:
   with self.assertRaises(EngineError):time_plot(pd.DataFrame({'date':[date,'2020-01-01'],'rate':[2,3]}),{'time':'date','value':'rate','time_mode':'date'})
 def test_repeated_periods_invalid_columns_infinities_and_short_series(self):
  for frame,params in [(pd.DataFrame({'t':[2000,2000],'v':[2,3]}),{}),(pd.DataFrame({'t':[2000,2001],'v':[2,float('inf')]}),{}),(pd.DataFrame({'t':[2000,2001],'v':[2,None]}),{}),(pd.DataFrame({'t':[2000.5,2001],'v':[2,3]}),{})]:
   with self.assertRaises(EngineError):time_plot(frame,{'time':'t','value':'v',**params})
 def test_connected_csv_project_produces_visible_result(self):
  p={'schema_version':'1.0.0','app_version':'0.7.4','title':'Serie','nodes':[{'id':'data','type':'csv','node_version':'1.0.0','parameters':{'content':'year,rate\n2001,3\n2000,2\n','delimiter':','},'position':{'x':0,'y':0}},{'id':'chart','type':'time_plot','node_version':'1.0.0','parameters':{'time':'year','value':'rate'},'position':{'x':300,'y':0}}],'edges':[{'id':'link','source':'data','source_port':'data','target':'chart','target_port':'data'}]}
  run=execute(p);self.assertEqual(run['status'],'succeeded',run['nodes']);self.assertEqual(run['nodes']['chart']['result']['points'][0]['x'],2000)
