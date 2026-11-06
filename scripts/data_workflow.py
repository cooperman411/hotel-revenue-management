#!/usr/bin/env python3
"""Reusable CSV normalization and approved-only manual exports. Offline only."""
import argparse,csv,hashlib,json,math,re
from datetime import date,timedelta
from pathlib import Path
from review_engine import stamp,normalize,approvals

FIELDS={
 'reservations':['reservation_key','property_id','stay_date','room_type','rate_plan','rooms','adr','currency','status','booked_at'],
 'inventory':['property_id','stay_date','room_type','sellable_rooms'],
 'rates':['property_id','stay_date','room_type','rate_plan','rate','currency','observed_at'],
 'competitors':['hotel_id','stay_date','room_type','rate_plan','rate','currency','observed_at','occupancy','los','tax_basis','cancellation','meal_plan','channel','source','reliability','availability']}
INTEGERS={'rooms','sellable_rooms','physical_rooms','out_of_order_rooms','unpicked_group_rooms','occupancy','los'}
NUMBERS={'adr','rate'}

def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def safe(value):
 s=str(value)
 if s.lstrip().startswith(('=','+','-','@')): return "'"+s
 return value

def csv_write(path,rows,fields):
 with Path(path).open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:safe(r.get(k,'')) for k in fields} for r in rows)

def import_csv(path,profile,kind,as_of):
 """Map configured columns, reject invalid rows, and preserve exact source CSV separately."""
 if kind not in FIELDS: raise ValueError('Unsupported table')
 at=stamp(as_of); spec=profile['tables'][kind]; result=[]; seen=set()
 with Path(path).open(newline='',encoding='utf-8-sig') as f:
  reader=csv.DictReader(f)
  if len(reader.fieldnames or [])!=len(set(reader.fieldnames or [])): raise ValueError('Duplicate CSV headers')
  for number,raw in enumerate(reader,2):
   try:
    if None in raw: raise ValueError('Malformed CSV row')
    row=dict(spec.get('constants',{}))
    for canonical,column in spec['columns'].items():
     if column not in raw: raise ValueError('Missing source column '+column)
     row[canonical]=raw[column].strip()
    if any(row.get(k) in (None,'') for k in FIELDS[kind]): raise ValueError('Missing required value')
    for key in list(row):
     if key in INTEGERS:
      row[key]=int(row[key])
      if row[key]<0: raise ValueError('Negative count')
     if key in NUMBERS:
      row[key]=float(row[key])
      if not math.isfinite(row[key]) or row[key]<0: raise ValueError('Invalid money')
     if key.endswith('_at') and row[key]:
      if stamp(row[key])>at: raise ValueError('Future observation or status timestamp')
    date.fromisoformat(row['stay_date'])
    for key in ('room_type','rate_plan','property_id'):
     if key not in row: continue
     mapping=profile.get('mappings',{}).get(key,{})
     if row[key] not in mapping: raise ValueError('Unmapped '+key+': '+row[key])
     row[key]=mapping[row[key]]
    if 'currency' in row and row['currency']!=profile['currency']: raise ValueError('Currency mismatch; no implicit FX')
    if kind!='competitors' and row['property_id']!=profile['property_id']: raise ValueError('Wrong property')
    if kind=='reservations':
     if row['status'] not in ('booked','checked_in','checked_out','cancelled','no_show'): raise ValueError('Invalid reservation status')
     normalize([row])
    if kind=='inventory':
     if 'physical_rooms' in row and row['physical_rooms']-row.get('out_of_order_rooms',0)!=row['sellable_rooms']: raise ValueError('Inventory mismatch')
     if 'history_reliable' in row:
      if str(row['history_reliable']).lower() not in ('true','false'): raise ValueError('Invalid reliability boolean')
      row['history_reliable']=str(row['history_reliable']).lower()=='true'
    if kind=='rates' and row['rate']<=0: raise ValueError('Rate must be positive')
    if kind=='competitors':
     conditions=spec['comparison_conditions']
     for key in ('occupancy','los','tax_basis','cancellation','meal_plan'):
      if row[key]!=conditions[key]: raise ValueError('Incompatible competitor '+key)
     if row['reliability']!='authorized_export': raise ValueError('Unverified source reliability')
     if row['availability'] not in ('available','unavailable','unknown'): raise ValueError('Invalid availability')
     if row['occupancy']<1 or row['los']<1: raise ValueError('Invalid occupancy/LOS')
     if row['availability']=='available' and row['rate']<=0: raise ValueError('Missing available rate')
     if (at-stamp(row['observed_at'])).total_seconds()>spec.get('max_age_hours',24)*3600: raise ValueError('Stale competitor observation')
    key=tuple(row.get(k) for k in ({'reservations':['reservation_key','stay_date'],'inventory':['property_id','stay_date','room_type'],'rates':['property_id','stay_date','room_type','rate_plan'],'competitors':['hotel_id','stay_date','room_type','rate_plan','channel','observed_at']}[kind]))
    if key in seen: raise ValueError('Duplicate record')
    seen.add(key);result.append(row)
   except (KeyError,ValueError,TypeError) as exc: raise ValueError(f'{kind} CSV row {number}: {exc}') from exc
 return {'rows':result,'provenance':{'source_file':Path(path).name,'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'profile_hash':digest(profile),'import_as_of':as_of,'table':kind}}

EXPORT_FIELDS=['property_id','stay_date','room_type','rate_plan','approved_rate','currency','recommendation_id','approval_reference']
def approved_export(report,decisions,config,now):
 at=stamp(now);records=approvals(report,decisions);rows=[];audit=[];seen=set()
 for r in records['approved_rates']:
  a=r['approval_record'];approved_at=stamp(a['review_timestamp'])
  if a['reviewer'] not in config.get('authorized_reviewers',[]): raise ValueError('Reviewer is not in configured approval authority')
  if not 0<=(at-approved_at).total_seconds()<=config.get('approval_max_age_hours',24)*3600: raise ValueError('Stale or future approval')
  if not 0<=(at-stamp(r['analysis_timestamp'])).total_seconds()<=config.get('analysis_max_age_hours',48)*3600: raise ValueError('Stale or future analysis')
  day=date.fromisoformat(r['stay_date'])
  if day<at.date(): raise ValueError('Past stay date')
  if r['property_id']!=config['property_id'] or r['currency']!=config['currency']: raise ValueError('Wrong property or currency')
  mapped={}
  for k in ('property_id','room_type','rate_plan'):
   v=config['destination_mappings'][k].get(r[k])
   if not isinstance(v,str) or not v.strip(): raise ValueError('Missing destination '+k)
   mapped[k]=v
  key=(mapped['property_id'],r['stay_date'],mapped['room_type'],mapped['rate_plan'])
  if key in seen: raise ValueError('Duplicate destination change')
  seen.add(key)
  reference=digest({'analysis':digest(report),'approval':a})
  rows.append(dict(mapped,stay_date=r['stay_date'],approved_rate=r['approved_new_rate'],currency=r['currency'],recommendation_id=r['recommendation_id'],approval_reference=reference))
  audit.append(dict(r,approval_reference=reference,destination=mapped,analysis_hash=digest(report)))
 return {'rows':rows,'audit':audit,'generated_at':now,'live_publish_enabled':False}

def format_export(export,profile):
 """No provider format is shipped as verified. Explicit local mappings require a checked specification."""
 if profile.get('status')!='verified' or not profile.get('documentation_reference') or not profile.get('verified_by'): raise ValueError('Unverified destination CSV format')
 fields=profile['columns'];allowed=set(EXPORT_FIELDS)
 if not fields or len(set(fields))!=len(fields) or any(v not in allowed for v in fields.values()): raise ValueError('Unsupported output fields')
 if not set(profile['required_fields']).issubset(fields): raise ValueError('Missing required destination columns')
 return [{column:r[source] for column,source in fields.items()} for r in export['rows']]

def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 i=sub.add_parser('import');i.add_argument('csv');i.add_argument('profile');i.add_argument('kind',choices=FIELDS);i.add_argument('as_of');i.add_argument('output')
 e=sub.add_parser('export');e.add_argument('analysis');e.add_argument('decisions');e.add_argument('config');e.add_argument('now');e.add_argument('directory')
 a=p.parse_args();load=lambda f:json.loads(Path(f).read_text())
 if a.command=='import':Path(a.output).write_text(json.dumps(import_csv(a.csv,load(a.profile),a.kind,a.as_of),indent=2))
 else:
  result=approved_export(load(a.analysis),load(a.decisions),load(a.config),a.now);d=Path(a.directory);d.mkdir(parents=True,exist_ok=True)
  csv_write(d/'approved-rates.csv',result['rows'],EXPORT_FIELDS);(d/'approval-audit.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()


def assemble_analysis(property_config, imports, as_of, start, days):
 """Join normalized imports to the Task 4 engine without treating absent competitors as zero."""
 from review_engine import analyze
 if any(k not in imports for k in ('reservations','inventory')): raise ValueError('Reservations and inventory are required')
 for kind,item in imports.items():
  if item['provenance']['table']!=kind or stamp(item['provenance']['import_as_of'])>stamp(as_of): raise ValueError('Wrong table or future import')
 data={'property':property_config,'as_of':as_of,'start':start,'days':days,**{k:imports[k]['rows'] for k in ('reservations','inventory','rates') if k in imports}}
 data['rate_plans']=sorted({r['rate_plan'] for r in data.get('rates',[])}) or ['BAR']
 return analyze(data)
