#!/usr/bin/env python3
"""Offline empirical pickup forecasts and human review outputs. No publishing APIs."""
import argparse, csv, hashlib, html, json, math, statistics, zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

def stamp(s):
    t=datetime.fromisoformat(s.replace('Z','+00:00'))
    if t.tzinfo is None: raise ValueError('Timestamps require UTC offsets')
    return t

def quantile(v,p):
    v=sorted(v); x=(len(v)-1)*p; i=int(x)
    return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(x-i)

def normalize(rows):
    facts={}
    for source in rows:
        r=dict(source)
        stamp(r['booked_at'])
        for key in ('cancelled_at','no_show_at'):
            if r.get(key) and stamp(r[key])<stamp(r['booked_at']): raise ValueError('Status precedes booking')
        if r['status'] in ('cancelled','no_show') and not r.get('cancelled_at' if r['status']=='cancelled' else 'no_show_at'):
            raise ValueError('Cancelled/no-show records require effective timestamps')
        if 'arrival' in r:
            start=date.fromisoformat(r['arrival']); end=date.fromisoformat(r['departure'])
            if end<=start: raise ValueError('Departure must follow arrival')
            days=[(start+timedelta(days=i)).isoformat() for i in range((end-start).days)]
        else: days=[r['stay_date']]
        for day in days:
            date.fromisoformat(day)
            f={**r,'stay_date':day,'rooms':r.get('rooms',r.get('room_nights',1))}
            if not isinstance(f['rooms'],int) or f['rooms']<=0: raise ValueError('Rooms must be positive integers per night')
            if f.get('adr',0)<0: raise ValueError('Negative ADR')
            key=(f['reservation_key'],day)
            if key in facts and facts[key]!=f: raise ValueError('Contradictory duplicate reservation '+str(key))
            facts[key]=f
    return list(facts.values())

def active(r,at):
    return stamp(r['booked_at'])<=at and not any(r.get(k) and stamp(r[k])<=at for k in ('cancelled_at','no_show_at'))

def analyze(data):
    at=stamp(data['as_of']); prop=data['property']; policy=prop['rate_policy']; facts=normalize(data['reservations'])
    start=date.fromisoformat(data['start']); days=data['days']
    if days<1 or start<at.date(): raise ValueError('Invalid forecast horizon')
    lo,hi=policy['min_rate'],policy['max_rate']; baseline=policy['default_rate']; cap=policy.get('adjustment_cap_pct',.15)
    if not 0<lo<=baseline<=hi or not 0<=cap<=.5: raise ValueError('Invalid rate policy')
    inv={}
    for r in data['inventory']:
        key=(r['stay_date'],r['room_type'])
        if key in inv: raise ValueError('Duplicate inventory '+str(key))
        if r['sellable_rooms']<0 or int(r['sellable_rooms'])!=r['sellable_rooms']: raise ValueError('Invalid inventory')
        if 'physical_rooms' in r and r['physical_rooms']-r.get('out_of_order_rooms',0)!=r['sellable_rooms']: raise ValueError('Inventory does not reconcile')
        inv[key]=r
    rates={}
    for r in data.get('rates',[]):
        if stamp(r['observed_at'])<=at and (at-stamp(r['observed_at'])).total_seconds()<=86400:
            key=(r['stay_date'],r['room_type'],r['rate_plan'])
            if r['rate']<=0 or r['currency']!=prop['currency']: raise ValueError('Invalid current rate')
            if key in rates: raise ValueError('Duplicate current rate')
            rates[key]=r['rate']
    out=[]; gaps=[]
    types=[r['room_type'] for r in prop['room_types']]; plans=data.get('rate_plans',['BAR'])
    for offset in range(days):
        day=start+timedelta(days=offset); keyday=day.isoformat(); lead=(day-at.date()).days
        for typ in types:
            inventory=inv.get((keyday,typ))
            if inventory is None: gaps.append(keyday+'/'+typ+': missing inventory'); continue
            capacity=inventory['sellable_rooms']; warnings=[]
            booked=sum(r['rooms'] for r in facts if r['stay_date']==keyday and r['room_type']==typ and active(r,at))
            block=inventory.get('unpicked_group_rooms',0)
            if block<0 or booked+block>capacity: raise ValueError('Booked rooms plus unpicked group blocks exceed inventory')
            if not capacity: gaps.append(keyday+'/'+typ+': closed inventory'); continue
            samples=[]; analogs=[]
            # Completed dates only. Match weekday, season and room type. Preserve cancellations at their effective time.
            for (hist,room),iv in inv.items():
                hd=date.fromisoformat(hist)
                if room!=typ or hd>=at.date() or hd.weekday()!=day.weekday() or min((hd.month-day.month)%12,(day.month-hd.month)%12)>1: continue
                if not iv.get('history_reliable',False) or iv.get('unpicked_group_rooms',0): continue
                if (at.date()-hd).days>730 or iv['sellable_rooms']<=0: continue
                past=[r for r in facts if r['stay_date']==hist and r['room_type']==typ]
                decision=at-timedelta(days=(day-hd).days)
                final=sum(r['rooms'] for r in past if active(r,at))
                then=sum(r['rooms'] for r in past if active(r,decision))
                # Capacity-censored dates cannot reveal unconstrained demand.
                if final>=iv['sellable_rooms']: continue
                scale=capacity/iv['sellable_rooms']
                samples.append(max(0,booked+(final-then)*scale)+block)
                analogs.append(hist)
            relevant=[r for r in facts if r['stay_date']==keyday and r['room_type']==typ]
            def otb(t): return sum(r['rooms'] for r in relevant if active(r,t))
            pickup=booked-otb(at-timedelta(days=7)); previous=otb(at-timedelta(days=7))-otb(at-timedelta(days=14))
            accel=(pickup-previous)/7
            supported=len(samples)>=5
            p10=p50=p90=prob=displaced=expected=None
            if supported:
                p10,p50,p90=[round(quantile(samples,p),2) for p in (.1,.5,.9)]
                prob=sum(x>=capacity for x in samples)/len(samples); displaced=statistics.mean(max(x-capacity,0) for x in samples)
                expected=statistics.mean(min(x,capacity) for x in samples)/capacity
            else: warnings.append('Insufficient reliable comparable dates')
            warnings.append('Provisional empirical forecast; calibration not established')
            if block: warnings.append('Unpicked group block assumed fully materialized; displacement contribution unavailable')
            for plan in plans:
                current=rates.get((keyday,typ,plan)); move=0
                if supported:
                    # Explicit configurable decision policy, not an optimal price claim.
                    if prob>=policy.get('compression_probability',.5): move=cap
                    elif expected<policy.get('weak_expected_occupancy',.4): move=-cap/2
                reference=current if current is not None else baseline
                recommended=round(max(lo,min(hi,reference*(1+move))),2)
                w=list(warnings)
                if current is None: w.append('Current selling rate missing or stale; configured reference used')
                ident=hashlib.sha256((prop['property_id']+keyday+typ+plan+data['as_of']).encode()).hexdigest()[:20]
                rationale=(f'{booked}/{capacity} rooms booked; net seven-day pickup {pickup:+}; acceleration {accel:+.2f} rooms/day. ')
                rationale+=f'{len(samples)} comparable dates; empirical sellout frequency {prob:.0%}.' if supported else 'No supportable final occupancy forecast; hold reference rate.'
                out.append(dict(recommendation_id=ident,property_id=prop['property_id'],analysis_timestamp=data['as_of'],stay_date=keyday,day_of_week=day.strftime('%A'),room_type=typ,rate_plan=plan,currency=prop['currency'],current_rate=current,recommended_rate=recommended,adjustment_pct=(recommended/current-1) if current else None,min_rate=lo,max_rate=hi,booked_rooms=booked,sellable_rooms=capacity,occupancy=booked/capacity,expected_occupancy=expected,demand_p10=p10,demand_p50=p50,demand_p90=p90,sellout_probability=prob,expected_displaced_rooms=displaced,pickup_7=pickup,acceleration=accel,competitor_comparison=None,confidence='provisional' if supported else 'insufficient',priority='high' if supported and prob>=.5 else ('review' if not supported or current is None else 'normal'),rationale=rationale,warnings='; '.join(w),baseline=reference,adjustment_logic=f'Configured movement {move:+.1%}; floor {lo}; ceiling {hi}',analog_dates=','.join(analogs),human_decision='pending',approved_rate=None,reviewer='',review_timestamp='',review_notes=''))
    out.sort(key=lambda r:({'high':0,'review':1,'normal':2}[r['priority']],r['stay_date'],r['room_type'],r['rate_plan']))
    return {'property':prop,'as_of':data['as_of'],'start':data['start'],'days':days,'requested_cells':days*len(types),'evaluated_cells':len({(r['stay_date'],r['room_type']) for r in out}),'gaps':gaps,'recommendations':out}

def approvals(report,decisions):
    source={r['recommendation_id']:r for r in report['recommendations']}; seen=set(); records=[]; approved=[]
    for d in decisions:
        ident=d['recommendation_id']
        if ident in seen or ident not in source: raise ValueError('Duplicate or unknown recommendation')
        seen.add(ident); r=source[ident]; choice=d['decision']
        if choice not in ('approve','modify','reject','defer'): raise ValueError('Invalid human decision')
        if not d['reviewer'].strip() or stamp(d['review_timestamp'])<stamp(r['analysis_timestamp']): raise ValueError('Invalid reviewer or review timestamp')
        if choice!='approve' and not d.get('notes','').strip(): raise ValueError('Reasons required')
        rate=r['recommended_rate'] if choice=='approve' else d.get('approved_rate') if choice=='modify' else None
        if rate is not None and (not math.isfinite(rate) or not r['min_rate']<=rate<=r['max_rate']): raise ValueError('Approved rate outside guardrails')
        record={**d,'original_recommended_rate':r['recommended_rate'],'approved_rate':rate}
        records.append(record)
        if choice in ('approve','modify'):
            if rate is None: raise ValueError('Modified rate required')
            approved.append({k:r[k] for k in ('property_id','stay_date','room_type','rate_plan','current_rate','currency','analysis_timestamp','recommendation_id')}|{'approved_new_rate':rate,'approval_record':record})
    return {'approval_records':records,'approved_rates':approved}

def workbook(path,sheets):
    """Minimal portable OOXML workbook with typed values, filters and frozen headers."""
    ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    def col(n):
        s=''
        while n: n,a=divmod(n-1,26); s=chr(65+a)+s
        return s
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'+''.join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1,len(sheets)+1))+'</Types>')
        z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml',f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'+''.join(f'<sheet name="{name}" sheetId="{i}" r:id="rId{i}"/>' for i,(name,_) in enumerate(sheets,1))+'</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1,len(sheets)+1))+'</Relationships>')
        for i,(_,rows) in enumerate(sheets,1):
            body=''
            for rownum,row in enumerate(rows,1):
                cells=''
                for j,v in enumerate(row,1):
                    if v is None: continue
                    ref=f'{col(j)}{rownum}'
                    cells+=f'<c r="{ref}"><v>{v}</v></c>' if isinstance(v,(int,float)) else f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(v))}</t></is></c>'
                body+=f'<row r="{rownum}">{cells}</row>'
            z.writestr(f'xl/worksheets/sheet{i}.xml',f'<worksheet xmlns="{ns}"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" state="frozen"/></sheetView></sheetViews><sheetData>{body}</sheetData><autoFilter ref="A1:{col(len(rows[0]))}{len(rows)}"/></worksheet>')

def write(report,directory):
    p=Path(directory); p.mkdir(parents=True,exist_ok=True); rows=report['recommendations']
    (p/'analysis.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    if rows:
        fields=list(rows[0]); table=[fields]+[[r[k] for k in fields] for r in rows]
        with (p/'recommendations.csv').open('w',newline='') as f: csv.writer(f).writerows(table)
        workbook(p/'recommendations.xlsx',[('Summary',[['Metric','Value'],['Property',report['property']['property_id']],['Analysis',report['as_of']],['Evaluated cells',report['evaluated_cells']],['Requested cells',report['requested_cells']],['High priority',sum(r['priority']=='high' for r in rows)],['Status','All recommendations pending; no live publishing']]),('Recommendations',table)])
    lines=[f"# {report['property'].get('property_name',report['property']['property_id'])}: Revenue Review",f"Analysis: {report['as_of']}. Horizon: {report['start']} for {report['days']} days.",f"Evaluated {report['evaluated_cells']} of {report['requested_cells']} date/room-type cells. All recommendations require human review.",'## Dates Requiring Attention']
    for r in rows[:12]:
        lines.append(f"- {r['stay_date']} / {r['room_type']} / {r['rate_plan']}: current {r['current_rate'] if r['current_rate'] is not None else 'unverified'}, proposed {r['recommended_rate']} {r['currency']}. {r['rationale']} Confidence: {r['confidence']}. {r['warnings']}")
    lines+=['## Data Gaps']+report['gaps']+['Revenue impact, causal price elasticity, group contribution displacement and forecast accuracy are not established. Competitor data is optional and does not affect confidence. Historical accepted prices are not assumed optimal.']
    (p/'summary.md').write_text('\n\n'.join(lines))
    (p/'summary.html').write_text('<!doctype html><meta charset="utf-8"><title>Revenue Review</title><style>body{font:16px system-ui;max-width:1000px;margin:40px auto;line-height:1.6}pre{white-space:pre-wrap}</style><pre>'+html.escape('\n\n'.join(lines))+'</pre>')
    (p/'approvals.json').write_text(json.dumps({'approval_records':[],'approved_rates':[]},indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('output'); args=ap.parse_args()
    write(analyze(json.loads(Path(args.input).read_text())),args.output)
