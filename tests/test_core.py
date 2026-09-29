import unittest
from core import Workspace, Problem, health

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.w=Workspace(':memory:')
        self.addCleanup(self.w.close)
        self.w.db.executemany('INSERT INTO users VALUES (?,?)',[(u,'test') for u in ['owner','editor','viewer','new']])
        self.w.db.commit()
        self.w.act('owner','create_project',{'name':'Delivery'})
        self.p=self.w.state('owner')['projects'][0]['id']
        for user,role in [('editor','EDITOR'),('viewer','VIEWER')]: self.act('member',{'user':user,'role':role})
    def act(self,action,data,user='owner'):
        return self.w.act(user,action,{'project':self.p,**data})
    def task(self,**kw):
        self.act('task',{'title':'Deliver','owner':'editor',**kw})
        return self.w.state('owner')['projects'][0]['tasks'][-1]
    def test_viewer_cannot_write(self):
        for action,data in [('task',{'title':'x','owner':'viewer'}),('handover',{'text':'x'}),('member',{'user':'new','role':'EDITOR'}),('comment',{'id':'x','text':'x'})]:
            with self.assertRaises(Problem): self.act(action,data,'viewer')
    def test_editor_invites_and_owner_protection(self):
        with self.assertRaises(Problem): self.act('member',{'user':'new','role':'EDITOR'},'editor')
        self.act('project',{'name':'Delivery','phase':'Contract','allowEditorInvites':True})
        self.act('member',{'user':'new','role':'VIEWER'},'editor')
        for user,role in [('owner','REMOVE'),('owner','EDITOR'),('new','OWNER')]:
            with self.assertRaises(Problem): self.act('member',{'user':user,'role':role},'editor')
        members=self.w.state('owner')['projects'][0]['members']
        self.assertEqual(next(m for m in members if m['user']=='new')['addedBy'],'editor')
    def test_last_owner(self):
        with self.assertRaises(Problem): self.act('member',{'user':'owner','role':'REMOVE'})
    def test_dependencies_and_cycle(self):
        a=self.task(); b=self.task(dependencies=[a['id']])
        with self.assertRaises(Problem): self.task(id=a['id'],dependencies=[b['id']])
        with self.assertRaises(Problem): self.task(id=b['id'],dependencies=[a['id']],status='DONE')
        self.task(id=a['id'],status='DONE');self.task(id=b['id'],dependencies=[a['id']],status='DONE')
        with self.assertRaises(Problem): self.task(id=a['id'],status='TODO')
    def test_waiting_requires_context(self):
        with self.assertRaises(Problem): self.task(status='WAITING')
        self.task(status='BLOCKED',waiting='Customer approval')
        self.assertEqual(self.w.state('owner')['projects'][0]['health']['status'],'BLOCKED')
    def test_isolation_and_revocation(self):
        self.assertEqual(self.w.state('new')['projects'],[])
        with self.assertRaises(Problem): self.w.project(self.p,'new')
        self.task(owner='editor');self.act('member',{'user':'editor','role':'REMOVE'})
        self.assertEqual(self.w.state('editor')['notifications'],[])
        with self.assertRaises(Problem): self.act('handover',{'text':'x'},'editor')
    def test_comments_notify_only_members(self):
        t=self.task();self.act('comment',{'id':t['id'],'text':'@viewer @new please review'})
        self.assertEqual(len(self.w.state('viewer')['notifications']),1)
        self.assertEqual(len(self.w.state('new')['notifications']),0)
    def test_closure_gate(self):
        self.task()
        with self.assertRaises(Problem): self.act('project',{'name':'Delivery','phase':'Closure','completed':True})
        self.assertFalse(self.w.state('owner')['projects'][0]['completed'])
    def test_audit_and_atomic_failure(self):
        before=len(self.w.state('owner')['projects'][0]['events'])
        with self.assertRaises(Problem): self.task(owner='new')
        self.assertEqual(len(self.w.state('owner')['projects'][0]['events']),before)
        self.act('handover',{'text':'Next: request sign-off'},'editor')
        self.assertEqual(self.w.state('owner')['projects'][0]['events'][0]['actor'],'editor')
    def test_invalid_status(self):
        with self.assertRaises(Problem): self.task(status='HACK')

    def test_tor_milestone_payment_summary_and_audit(self):
        self.act('project_info',{'contractName':'Contract A','contractValue':'10000000'})
        self.act('milestone_add',{})
        m=self.w.state('owner')['projects'][0]['milestones'][0]
        self.act('milestone_cell',{'id':m['id'],'field':'paymentNo','value':'1'})
        self.act('milestone_cell',{'id':m['id'],'field':'paymentPercent','value':'20'})
        p=self.w.state('owner')['projects'][0]
        self.assertEqual(p['paymentSummary']['totalPercent'],20)
        self.assertEqual(p['paymentSummary']['groups']['1']['amount'],2000000)
        event=next(e for e in p['events'] if e['action']=='milestone_cell' and 'paymentPercent' in e['detail'])
        self.assertIn('before',event['detail']);self.assertIn('after',event['detail'])

    def test_tor_payment_total_cannot_exceed_100(self):
        self.act('milestone_add',{});self.act('milestone_add',{})
        rows=self.w.state('owner')['projects'][0]['milestones']
        self.act('milestone_cell',{'id':rows[0]['id'],'field':'paymentPercent','value':'60'})
        with self.assertRaises(Problem):
            self.act('milestone_cell',{'id':rows[1]['id'],'field':'paymentPercent','value':'50'})
        p=self.w.state('owner')['projects'][0]
        self.assertEqual(p['paymentSummary']['totalPercent'],60)

    def test_viewer_cannot_edit_tor_sheet(self):
        self.act('milestone_add',{})
        mid=self.w.state('owner')['projects'][0]['milestones'][0]['id']
        with self.assertRaises(Problem):
            self.act('milestone_cell',{'id':mid,'field':'deliverables','value':'x'},'viewer')

    def test_editor_can_edit_tor_but_not_project_contract_info(self):
        self.act('milestone_add',{})
        mid=self.w.state('owner')['projects'][0]['milestones'][0]['id']
        self.act('milestone_cell',{'id':mid,'field':'deliverables','value':'SIT Report'},'editor')
        self.assertEqual(self.w.state('owner')['projects'][0]['milestones'][0]['deliverables'],'SIT Report')
        with self.assertRaises(Problem):
            self.act('project_info',{'contractName':'Changed'},'editor')

    def test_nonfinite_financial_values_are_atomic(self):
        self.act('milestone_add', {})
        before = self.w.state('owner')['projects'][0]
        mid = before['milestones'][0]['id']
        for value in ['NaN', 'Infinity', '-Infinity', float('nan')]:
            with self.subTest(value=value):
                with self.assertRaises(Problem):
                    self.act('project_info', {'contractValue': value})
                with self.assertRaises(Problem):
                    self.act('milestone_cell', {'id': mid, 'field': 'paymentPercent', 'value': value})
        self.assertEqual(self.w.state('owner')['projects'][0], before)

if __name__=='__main__': unittest.main()
