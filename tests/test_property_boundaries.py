"""Property identity and local-calendar regressions, using synthetic fixtures only."""
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from review_engine import analyze
from data_workflow import assemble_analysis,import_csv,approved_export

class PropertyBoundaries(unittest.TestCase):
 def setUp(self):
  self.data=json.loads((ROOT/'examples/review-demo/input.json').read_text())
  self.path=ROOT/'examples/integration-demo'
  self.profile=json.loads((self.path/'mapping-profile.json').read_text())
  self.now='2026-11-07T02:00:00+00:00'
 def test_forecast_accepts_current_property_day_after_utc_midnight(self):
  self.data['property']['timezone']='America/Los_Angeles'
  self.data.update(as_of=self.now,start='2026-11-06',days=1)
  self.data['inventory'].append(dict(property_id='synthetic-inn',stay_date='2026-11-06',room_type='standard',sellable_rooms=100))
  report=analyze(self.data)
  self.assertEqual(report['recommendations'][0]['stay_date'],'2026-11-06')
 def test_same_instant_uses_same_analogs_and_forecast(self):
  self.data['property']['timezone']='America/Los_Angeles'
  self.data['as_of']=self.now
  utc=analyze(self.data)['recommendations'][0]
  self.data['as_of']='2026-11-06T18:00:00-08:00'
  local=analyze(self.data)['recommendations'][0]
  for k in ('analog_dates','booked_rooms','demand_p50','recommended_rate'):
   self.assertEqual(utc[k],local[k],k)
 def test_wrong_property_in_direct_rows_is_rejected(self):
  for kind in ('inventory','reservations','rates'):
   data=copy.deepcopy(self.data);data[kind][0]['property_id']='another-hotel'
   with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,'Wrong property'):analyze(data)
 def test_import_from_other_property_cannot_be_assembled(self):
  imports={k:import_csv(self.path/(k+'.csv'),self.profile,k,self.now) for k in ('reservations','inventory','rates')}
  prop=dict(self.data['property'],property_id='another-hotel')
  with self.assertRaisesRegex(ValueError,'Import property'):assemble_analysis(prop,imports,self.now,'2026-11-20',1)
 def test_import_currency_cannot_be_relabelled(self):
  imports={k:import_csv(self.path/(k+'.csv'),self.profile,k,self.now) for k in ('reservations','inventory')}
  prop=dict(self.data['property'],currency='EUR')
  with self.assertRaisesRegex(ValueError,'Import currency'):assemble_analysis(prop,imports,self.now,'2026-11-20',1)
 def test_export_uses_property_day(self):
  report=analyze(self.data);report['property']['timezone']='America/Los_Angeles'
  report['recommendations'][0]['stay_date']='2026-11-06'
  decisions=json.loads((ROOT/'examples/review-demo/decisions.json').read_text())
  config=json.loads((self.path/'export-config.json').read_text());config['timezone']='America/Los_Angeles'
  self.assertEqual(approved_export(report,decisions,config,self.now)['rows'][0]['stay_date'],'2026-11-06')
 def test_mismatched_export_timezone_is_rejected(self):
  report=analyze(self.data);config=json.loads((self.path/'export-config.json').read_text());config['timezone']='America/Los_Angeles'
  with self.assertRaisesRegex(ValueError,'timezone'):approved_export(report,[],config,self.now)
if __name__=='__main__':unittest.main()
