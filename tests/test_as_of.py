import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class AsOfTest(unittest.TestCase):
    def test_future_booking_is_not_on_the_books(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p/'property.json').write_text(json.dumps({'timezone':'America/Los_Angeles','rate_policy':{'min_rate':50,'max_rate':500,'default_rate':200}}))
            (p/'history.json').write_text('{}')
            (p/'inventory.csv').write_text('stay_date,room_type,sellable_rooms\n2026-12-01,standard,10\n')
            (p/'reservations.csv').write_text('reservation_key,stay_date,room_type,room_nights,adr,status,booked_at\nr1,2026-12-01,standard,3,200,booked,2026-11-20T12:00:00+00:00\n')
            subprocess.run([sys.executable, str(ROOT/'scripts/calculate_rates.py'), '--property',str(p/'property.json'),'--history',str(p/'history.json'),'--inventory',str(p/'inventory.csv'),'--reservations',str(p/'reservations.csv'),'--as-of','2026-11-06','--days','26','--output',str(p/'out.csv')],check=True,capture_output=True)
            with (p/'out.csv').open() as f:
                self.assertEqual(float(next(csv.DictReader(f))['otb_occupancy']), 0)

if __name__ == '__main__':
    unittest.main()
