import copy,json,sys,tempfile,unittest,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from data_workflow import import_csv,approved_export,format_export
from publishing import MockDestination,preview,publish_mock,key
class IntegrationTests(unittest.TestCase):
 def setUp(self):
  self.p=ROOT/'examples/integration-demo';self.load=lambda f:json.loads((self.p/f).read_text());self.config=self.load('export-config.json');self.profile=self.load('mapping-profile.json');self.report=json.loads((ROOT/'examples/review-demo/analysis.json').read_text());self.decisions=json.loads((ROOT/'examples/review-demo/decisions.json').read_text());self.now='2026-11-07T02:00:00+00:00'
 def export(self):return approved_export(self.report,self.decisions,self.config,self.now)
 def test_all_imports(self):
  for kind in ('reservations','inventory','rates','competitors'):
   self.assertEqual(len(import_csv(self.p/(kind+'.csv'),self.profile,kind,self.now)['rows']),1)
 def test_incompatible_competitor(self):
  self.profile['tables']['competitors']['comparison_conditions']['occupancy']=1
  with self.assertRaises(ValueError):import_csv(self.p/'competitors.csv',self.profile,'competitors',self.now)
 def test_unmapped(self):
  self.profile['mappings']['room_type']={}
  with self.assertRaises(ValueError):import_csv(self.p/'rates.csv',self.profile,'rates',self.now)
 def test_stale_competitor(self):
  with self.assertRaises(ValueError):import_csv(self.p/'competitors.csv',self.profile,'competitors','2026-11-10T02:00:00+00:00')
 def test_modified_rate_exported(self):self.assertEqual(self.export()['rows'][0]['approved_rate'],215)
 def test_reject_defer_pending_excluded(self):
  for d in ('reject','defer'):
   self.decisions[0]['decision']=d;self.assertFalse(self.export()['rows'])
  self.decisions=[];self.assertFalse(self.export()['rows'])
 def test_stale_approval(self):
  self.now='2026-11-10T02:00:00+00:00'
  with self.assertRaises(ValueError):self.export()
 def test_missing_destination(self):
  self.config['destination_mappings']['rate_plan']={}
  with self.assertRaises(ValueError):self.export()
 def test_format_mapping(self):
  profile={'status':'verified','documentation_reference':'fictional-test-spec','verified_by':'Test','columns':{'Hotel':'property_id','Price':'approved_rate'},'required_fields':['Hotel','Price']}
  self.assertEqual(format_export(self.export(),profile)[0]['Price'],215)
  profile['status']='draft'
  with self.assertRaises(ValueError):format_export(self.export(),profile)
 def test_publication_controls_and_audit(self):
  ex=self.export();dest=MockDestination('MOCK-H1',{key(r):200 for r in ex['rows']});batch=preview(ex,dest)
  self.assertEqual(dest.calls,[])
  with tempfile.TemporaryDirectory() as t:
   ledger=str(Path(t)/'ledger.sqlite')
   with self.assertRaises(ValueError):publish_mock(ex,batch,{},dest,ledger,self.now)
   auth={'decision':'authorize_publication','batch_hash':batch['batch_hash'],'reviewer':'Test','authorized_at':self.now}
   result=publish_mock(ex,batch,auth,dest,ledger,self.now);self.assertEqual(result['results'][0]['status'],'verified')
   dest.rates[key(ex['rows'][0])]=200
   with self.assertRaises(ValueError):publish_mock(ex,batch,auth,dest,ledger,self.now)
   db=sqlite3.connect(ledger);self.assertEqual(db.execute('select count(*) from attempts').fetchone()[0],1);db.close()
 def test_partial_failure_no_retry(self):
  ex=self.export();r=copy.deepcopy(ex['rows'][0]);r.update(stay_date='2026-11-21',approval_reference='second-fixture');ex['rows'].append(r);a=copy.deepcopy(ex['audit'][0]);a.update(stay_date='2026-11-21',approval_reference='second-fixture');ex['audit'].append(a)
  dest=MockDestination('MOCK-H1',{key(r):200 for r in ex['rows']},fail=[key(r)]);batch=preview(ex,dest);auth={'decision':'authorize_publication','batch_hash':batch['batch_hash'],'reviewer':'Test','authorized_at':self.now}
  with tempfile.TemporaryDirectory() as t:
   result=publish_mock(ex,batch,auth,dest,str(Path(t)/'l.sqlite'),self.now)
   self.assertTrue(result['partial_failure']);self.assertEqual([r['status'] for r in result['results']],['verified','failed']);self.assertEqual(len(dest.calls),2)
 def test_changed_state(self):
  ex=self.export();dest=MockDestination('MOCK-H1',{key(r):200 for r in ex['rows']});batch=preview(ex,dest);dest.rates[key(ex['rows'][0])]=201
  with self.assertRaises(ValueError):publish_mock(ex,batch,{'decision':'authorize_publication','batch_hash':batch['batch_hash'],'reviewer':'Test','authorized_at':self.now},dest,':memory:',self.now)
 def test_no_competitors_assembly(self):
  from data_workflow import assemble_analysis
  imports={k:import_csv(self.p/(k+'.csv'),self.profile,k,self.now) for k in ('reservations','inventory','rates')}
  report=assemble_analysis(self.report['property'],imports,self.now,'2026-11-20',1)
  self.assertEqual(len(report['recommendations']),1)
 def test_unauthorized_reviewer(self):
  self.config['authorized_reviewers']=[]
  with self.assertRaises(ValueError):self.export()
 def test_invalid_currency(self):
  self.profile['currency']='EUR'
  with self.assertRaises(ValueError):import_csv(self.p/'rates.csv',self.profile,'rates',self.now)
 def test_uncertain_write_audited(self):
  ex=self.export();dest=MockDestination('MOCK-H1',{key(r):200 for r in ex['rows']},uncertain=[key(ex['rows'][0])]);batch=preview(ex,dest)
  with tempfile.TemporaryDirectory() as t:
   result=publish_mock(ex,batch,{'decision':'authorize_publication','batch_hash':batch['batch_hash'],'reviewer':'Test','authorized_at':self.now},dest,str(Path(t)/'l.sqlite'),self.now)
   self.assertEqual(result['results'][0]['status'],'uncertain');self.assertEqual(len(dest.calls),1)
if __name__=='__main__':unittest.main()
