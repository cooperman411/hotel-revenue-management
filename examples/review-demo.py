"""Generate deterministic synthetic inputs; no external services."""
import json,sys
from datetime import date,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from review_engine import analyze,write
p=Path(__file__).parent/'review-demo';p.mkdir(exist_ok=True)
day=date(2026,11,20); inv=[]; reservations=[]
for i in [3,4,5,6,52,53,54,55]:
 h=day-timedelta(days=7*i)
 inv.append(dict(stay_date=str(h),room_type='standard',sellable_rooms=100,history_reliable=True))
 for n,lead in [(10,30),(80,3)]:
  reservations.append(dict(reservation_key=f'{i}-{lead}',stay_date=str(h),room_type='standard',rooms=n,adr=180,status='checked_out',booked_at=f'{h-timedelta(days=lead)}T12:00:00+00:00'))
inv.append(dict(stay_date=str(day),room_type='standard',sellable_rooms=100,physical_rooms=102,out_of_order_rooms=2))
reservations.append(dict(reservation_key='current',stay_date=str(day),room_type='standard',rooms=30,adr=190,status='booked',booked_at='2026-11-01T12:00:00+00:00'))
data=dict(as_of='2026-11-06T23:00:00+00:00',start=str(day),days=2,property=dict(property_id='synthetic-inn',property_name='Synthetic Inn',currency='USD',room_types=[dict(room_type='standard')],rate_policy=dict(min_rate=100,max_rate=500,default_rate=200,adjustment_cap_pct=.15)),inventory=inv,reservations=reservations,rates=[dict(stay_date=str(day),room_type='standard',rate_plan='BAR',rate=200,currency='USD',observed_at='2026-11-06T22:00:00+00:00')])
(p/'input.json').write_text(json.dumps(data,indent=2));write(analyze(data),p)
