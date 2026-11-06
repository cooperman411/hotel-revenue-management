import json,sys,csv,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
from data_workflow import approved_export,csv_write,EXPORT_FIELDS,import_csv
from publishing import MockDestination,preview,key,publish_mock
p=Path(__file__).parent
load=lambda f:json.loads((ROOT/f).read_text())
config={'property_id':'synthetic-inn','currency':'USD','authorized_reviewers':['Synthetic Reviewer'],'destination_mappings':{'property_id':{'synthetic-inn':'MOCK-H1'},'room_type':{'standard':'STD'},'rate_plan':{'BAR':'FLEX'}}}
(p/'export-config.json').write_text(json.dumps(config,indent=2))
export=approved_export(load('examples/review-demo/analysis.json'),load('examples/review-demo/decisions.json'),config,'2026-11-07T02:00:00+00:00')
csv_write(p/'approved-rates.csv',export['rows'],EXPORT_FIELDS);(p/'approval-audit.json').write_text(json.dumps(export,indent=2))
destination=MockDestination('MOCK-H1',{key(r):200 for r in export['rows']});batch=preview(export,destination)
(p/'publication-preview.json').write_text(json.dumps(batch,indent=2))
auth={'decision':'authorize_publication','batch_hash':batch['batch_hash'],'reviewer':'Synthetic Publisher','authorized_at':'2026-11-07T02:01:00+00:00'}
with tempfile.TemporaryDirectory() as tmp:result=publish_mock(export,batch,auth,destination,str(Path(tmp)/'ledger.sqlite'),'2026-11-07T02:02:00+00:00')
(p/'mock-publication-audit.json').write_text(json.dumps(result,indent=2))
profile={'property_id':'synthetic-inn','currency':'USD','mappings':{'property_id':{'H1':'synthetic-inn'},'room_type':{'DBL':'standard'},'rate_plan':{'RACK':'BAR'}},'tables':{}}
from data_workflow import FIELDS
for kind,fields in FIELDS.items():profile['tables'][kind]={'columns':{k:k for k in fields}}
profile['tables']['competitors']['comparison_conditions']={'occupancy':2,'los':1,'tax_basis':'included','cancellation':'flexible','meal_plan':'room_only'}
(p/'mapping-profile.json').write_text(json.dumps(profile,indent=2))
fixtures={'reservations':{'reservation_key':'anon-1','property_id':'H1','stay_date':'2026-11-20','room_type':'DBL','rate_plan':'RACK','rooms':2,'adr':200,'currency':'USD','status':'booked','booked_at':'2026-11-01T10:00:00+00:00'},'inventory':{'property_id':'H1','stay_date':'2026-11-20','room_type':'DBL','sellable_rooms':100},'rates':{'property_id':'H1','stay_date':'2026-11-20','room_type':'DBL','rate_plan':'RACK','rate':200,'currency':'USD','observed_at':'2026-11-07T01:00:00+00:00'},'competitors':{'hotel_id':'comp-1','stay_date':'2026-11-20','room_type':'DBL','rate_plan':'RACK','rate':240,'currency':'USD','observed_at':'2026-11-07T01:00:00+00:00','occupancy':2,'los':1,'tax_basis':'included','cancellation':'flexible','meal_plan':'room_only','channel':'direct','source':'customer-authorized-export','reliability':'authorized_export','availability':'available'}}
for kind,row in fixtures.items():
 csv_write(p/(kind+'.csv'),[row],list(row));(p/(kind+'-normalized.json')).write_text(json.dumps(import_csv(p/(kind+'.csv'),profile,kind,'2026-11-07T02:00:00+00:00'),indent=2))
