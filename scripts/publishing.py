"""Offline publishing protocol. Only the mock destination is implemented; live writes are disabled."""
import json,sqlite3
from data_workflow import digest

class MockDestination:
 name='offline-mock'
 def __init__(self,property_id,rates,fail=(),uncertain=()):self.property_id=property_id;self.rates=dict(rates);self.fail=set(fail);self.uncertain=set(uncertain);self.calls=[]
 def read(self,key):return self.rates.get(key)
 def write(self,key,rate):
  self.calls.append(key)
  if key in self.uncertain:raise TimeoutError('Mock uncertain result')
  if key in self.fail:raise ValueError('Mock rejected write')
  self.rates[key]=rate

def key(r):return '|'.join(r[k] for k in ('property_id','stay_date','room_type','rate_plan'))
def preview(export,destination):
 if type(destination) is not MockDestination:raise ValueError('Live adapters are disabled')
 rows=[]
 audits={r['approval_reference']:r for r in export['audit']}
 for r in export['rows']:
  if r['property_id']!=destination.property_id:raise ValueError('Destination property mismatch')
  existing=destination.read(key(r))
  original=audits[r['approval_reference']]['current_rate']
  if original is not None and existing!=original:raise ValueError('Underlying current rate changed; refresh analysis and approval')
  rows.append(dict(r,existing_rate=existing))
 batch={'destination':destination.name,'property':destination.property_id,'generated_at':export['generated_at'],'changes':rows,'change_count':len(rows),'warnings':['Offline mock only; no live connection','Unknown existing rates block mock publication']}
 return dict(batch,batch_hash=digest(batch))

def publish_mock(export,batch,authorization,destination,ledger_path,now):
 """Record intent durably before a mock write. Failed/uncertain attempts require manual reconciliation."""
 from review_engine import stamp
 if type(destination) is not MockDestination:raise ValueError('Live publication disabled')
 if authorization.get('decision')!='authorize_publication' or authorization.get('batch_hash')!=batch['batch_hash'] or not authorization.get('reviewer','').strip():raise ValueError('Exact second approval required')
 if not 0<=(stamp(now)-stamp(authorization['authorized_at'])).total_seconds()<=900:raise ValueError('Publication authorization expired')
 if stamp(authorization['authorized_at'])<stamp(batch['generated_at']):raise ValueError('Authorization predates preview')
 if not 0<=(stamp(now)-stamp(export['generated_at'])).total_seconds()<=900:raise ValueError('Export/preview expired')
 if preview(export,destination)!=batch:raise ValueError('Destination state or batch changed; create a fresh preview')
 for r in batch['changes']:
  if r['existing_rate'] is None:raise ValueError('Unknown current destination rate')
 db=sqlite3.connect(ledger_path);db.execute('CREATE TABLE IF NOT EXISTS attempts (change_key TEXT PRIMARY KEY, result TEXT NOT NULL)')
 results=[]
 try:
  for r in batch['changes']:
   k=key(r);identity=digest({x:r[x] for x in ('approval_reference','property_id','stay_date','room_type','rate_plan','approved_rate')})
   result={'key':k,'old_rate':r['existing_rate'],'new_rate':r['approved_rate'],'batch_hash':batch['batch_hash'],'authorization':authorization,'attempted_at':now,'status':'attempted'}
   try:
    db.execute('INSERT INTO attempts VALUES (?,?)',(identity,json.dumps(result)));db.commit()
   except sqlite3.IntegrityError:raise ValueError('Previously attempted change; reconcile manually before any new approval')
   try:
    destination.write(k,r['approved_rate'])
    result['status']='verified' if destination.read(k)==r['approved_rate'] else 'uncertain'
   except TimeoutError:result['status']='uncertain'
   except ValueError as exc:result.update(status='failed',error=str(exc))
   db.execute('UPDATE attempts SET result=? WHERE change_key=?',(json.dumps(result),identity));db.commit();results.append(result)
  return {'results':results,'partial_failure':any(r['status']!='verified' for r in results),'live':False}
 finally:db.close()
