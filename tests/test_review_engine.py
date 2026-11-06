import copy,json,sys,unittest,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from review_engine import analyze,approvals,normalize
ROOT=Path(__file__).resolve().parents[1]
class ReviewTests(unittest.TestCase):
 def setUp(self): self.data=json.loads((ROOT/'examples/review-demo/input.json').read_text())
 def test_low_occupancy_forward_compression(self):
  r=analyze(self.data)['recommendations'][0];self.assertEqual(r['occupancy'],.3);self.assertGreater(r['recommended_rate'],200);self.assertEqual(r['sellout_probability'],1)
 def test_future_booking_leak(self):
  original=analyze(self.data)
  self.data['reservations'].append(dict(self.data['reservations'][-1],reservation_key='future',rooms=60,booked_at='2026-11-10T00:00:00+00:00'))
  self.assertEqual(analyze(self.data),original)
 def test_missing_current_rate(self):
  self.data['rates']=[];r=analyze(self.data)['recommendations'][0];self.assertIsNone(r['current_rate']);self.assertIsNone(r['adjustment_pct'])
 def test_bad_history(self):
  for iv in self.data['inventory']:iv['history_reliable']=False
  r=analyze(self.data)['recommendations'][0];self.assertIsNone(r['expected_occupancy']);self.assertEqual(r['recommended_rate'],200)
 def test_missing_inventory_coverage(self): self.assertEqual(analyze(self.data)['evaluated_cells'],1)
 def test_duplicate_conflict(self):
  self.data['reservations'].append(dict(self.data['reservations'][-1],rooms=1))
  with self.assertRaises(ValueError):analyze(self.data)
 def test_multinight(self):
  r=dict(self.data['reservations'][-1]);r.pop('stay_date');r.update(arrival='2026-11-20',departure='2026-11-23');self.assertEqual(len(normalize([r])),3)
 def test_cancellation_asof(self):
  self.data['reservations'][-1].update(status='cancelled',cancelled_at='2026-11-10T00:00:00+00:00');self.assertEqual(analyze(self.data)['recommendations'][0]['booked_rooms'],30)
  self.data['reservations'][-1]['cancelled_at']='2026-11-05T00:00:00+00:00';self.assertEqual(analyze(self.data)['recommendations'][0]['booked_rooms'],0)
 def test_inventory_reconciliation(self):
  self.data['inventory'][-1]['physical_rooms']=105
  with self.assertRaises(ValueError):analyze(self.data)
 def test_group_double_count(self):
  self.data['inventory'][-1]['unpicked_group_rooms']=80
  with self.assertRaises(ValueError):analyze(self.data)
 def test_approval_modification_rejection(self):
  report=analyze(self.data);r=report['recommendations'][0]
  d=dict(recommendation_id=r['recommendation_id'],decision='modify',approved_rate=215,reviewer='Synthetic Reviewer',review_timestamp='2026-11-07T01:00:00+00:00',notes='Synthetic review')
  a=approvals(report,[d]);self.assertEqual(a['approved_rates'][0]['approved_new_rate'],215);self.assertEqual(a['approval_records'][0]['original_recommended_rate'],230)
  d['decision']='reject';self.assertFalse(approvals(report,[d])['approved_rates'])
 def test_pending_not_approved(self):
  report=analyze(self.data);self.assertFalse(approvals(report,[])['approved_rates']);self.assertTrue(all(r['human_decision']=='pending' for r in report['recommendations']))
 def test_workbook_values(self):
  with zipfile.ZipFile(ROOT/'examples/review-demo/recommendations.xlsx') as z:
   for n in z.namelist():ET.fromstring(z.read(n))
   s=z.read('xl/worksheets/sheet2.xml').decode();self.assertIn('230.0',s);self.assertIn('pending',s)
if __name__=='__main__':unittest.main()
