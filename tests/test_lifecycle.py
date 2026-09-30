import unittest
from datetime import date
from core import Workspace, Problem
from lifecycle import MODULES, CHECKS, delivery_summary, parse_day, control_summary

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.w=Workspace(':memory:'); self.addCleanup(self.w.close)
        self.w.db.executemany('INSERT INTO users VALUES (?,?)',[(u,'hash') for u in ['owner','editor','viewer','outsider']]);self.w.db.commit()
        self.w.act('owner','create_project',{'name':'Lifecycle'})
        self.pid=self.project()['id']
        for user,role in [('editor','EDITOR'),('viewer','VIEWER')]:self.act('member',user=user,role=role)
    def project(self):return self.w.state('owner')['projects'][0]
    def act(self,action,actor='owner',**data):self.w.act(actor,action,{'project':self.pid,**data})
    def record(self,module,**values):
        data={f[0]:f[3][0] if f[2]=='select' else 'TODO' if f[2]=='status' else '' for f in MODULES[module]['fields']}
        data.update(title='Test '+module,owner='editor',**values)
        self.act('control',module=module,**data)
        return self.project()['controls'][module][-1]
    def test_every_module_persists_and_audits(self):
        for module in MODULES:
            row=self.record(module)
            self.assertEqual(row['title'],'Test '+module)
            self.assertEqual(self.project()['events'][0]['action'],'control')
        self.assertEqual(len(self.w.state('editor')['notifications']),len(MODULES))
    def test_all_new_writes_enforce_membership(self):
        for actor in ['viewer','outsider']:
            for action,values in [('control',{'module':'risk','title':'x'}),('checklist',{'id':'contract_review','status':'DONE','evidence':'x'}),('milestone_details',{'id':'x'})]:
                with self.subTest(actor=actor,action=action),self.assertRaises(Problem):self.act(action,actor=actor,**values)
    def test_done_checklist_requires_evidence_and_keeps_audit(self):
        with self.assertRaises(Problem):self.act('checklist',id='contract_review',status='DONE')
        self.act('checklist',id='contract_review',status='DONE',evidence='review memo',actor='editor')
        self.assertEqual(self.project()['checks']['contract_review']['evidence'],'review memo')
        self.assertEqual(self.project()['events'][0]['actor'],'editor')
    def test_progress_is_delivery_not_finance_or_acceptance(self):
        for status in ['DELIVERED','DELIVERED','DELIVERED','IN_PROGRESS','NOT_DUE']:
            self.act('milestone_add');mid=self.project()['milestones'][-1]['id']
            self.act('milestone_cell',id=mid,field='status',value=status)
        p=self.project();s=p['deliverySummary']
        self.assertEqual((s['done'],s['total'],s['percent'],s['accepted']),(3,5,60,0))
        self.assertEqual(s['current']['workNo'],'4')
        self.assertFalse(p['controlSummary']['financeRecorded'])
        self.assertEqual(p['paymentSummary']['totalPercent'],0)
    def test_thai_dates_and_overdue(self):
        self.assertEqual(parse_day('9/10/2569'),date(2026,10,9))
        self.assertEqual(parse_day('2 กรกฎาคม 2569'),date(2026,7,2))
        self.assertIsNone(parse_day('31/2/2569'))
        p={'milestones':[{'id':'a','status':'IN_PROGRESS','planDue':'9/10/2569'},{'id':'b','status':'DELIVERED','planDue':'1/7/2569'}]}
        self.assertEqual(delivery_summary(p,date(2026,10,10))['overdue'],['a'])
    def test_rules_detect_vendor_and_missing_records(self):
        p={'projectInfo':{'signedDate':'2 กรกฎาคม 2569','deliveryDueDate':'29/12/2569'},'controls':{'procurement':[{'id':'a','kind':'VENDOR_CONTRACT','title':'Vendor','status':'TODO','poDate':'2026-08-01','startDate':'2026-07-01','endDate':'2026-12-29'}]}}
        alerts=control_summary(p,date(2026,9,29))['alerts']
        self.assertEqual(len(alerts),4)
    def test_back_to_back_allocation_and_receipt_cannot_be_reversed(self):
        with self.assertRaises(Problem):self.record('finance',kind='VENDOR_PAYMENT',status='DONE',evidence='proof',amount=20,completedDate='2026-09-29',condition='BACK_TO_BACK')
        receipt=self.record('finance',kind='CUSTOMER_PAYMENT',status='DONE',evidence='receipt',amount=100,completedDate='2026-09-28')
        self.record('finance',kind='VENDOR_PAYMENT',status='DONE',evidence='proof',amount=60,completedDate='2026-09-29',condition='BACK_TO_BACK',customerPaymentId=receipt['id'])
        with self.assertRaises(Problem):self.record('finance',kind='VENDOR_PAYMENT',status='DONE',evidence='proof',amount=50,completedDate='2026-09-29',condition='BACK_TO_BACK',customerPaymentId=receipt['id'])
        with self.assertRaises(Problem):self.act('control',module='finance',**{**receipt,'status':'TODO'})
        self.assertEqual(self.project()['controlSummary']['net'],40)
    def test_closure_gate_and_reopen(self):
        with self.assertRaises(Problem):self.act('project',name='Lifecycle',phase='Closure',completed=True)
        for phase in ['Acceptance','Billing','Closure']:
            for key,title,required in CHECKS[phase]:
                if required:self.act('checklist',id=key,status='DONE',evidence='Verified / N/A with reason')
        self.act('project',name='Lifecycle',phase='Closure',completed=True)
        self.assertTrue(self.project()['completed'])
        with self.assertRaises(Problem):self.record('risk')
        self.act('project',name='Lifecycle',phase='Closure',completed=False)
        self.record('risk')
        with self.assertRaises(Problem):self.act('project',name='Lifecycle',phase='Closure',completed=True)
    def test_bulk_paste_is_atomic(self):
        self.act('milestone_add');a=self.project()['milestones'][0]['id']
        self.act('milestone_add');b=self.project()['milestones'][1]['id']
        before=self.project()
        with self.assertRaises(Problem):self.act('milestone_cells',cells=[{'id':a,'field':'paymentPercent','value':'60'},{'id':b,'field':'paymentPercent','value':'50'}])
        self.assertEqual(self.project(),before)
        self.act('milestone_cells',cells=[{'id':a,'field':'paymentPercent','value':'60'},{'id':b,'field':'paymentPercent','value':'40'}])
        self.assertEqual(self.project()['paymentSummary']['totalPercent'],100)
    def test_linked_documents_and_comments(self):
        self.act('milestone_add');mid=self.project()['milestones'][0]['id']
        self.record('documents',relatedId=mid)
        with self.assertRaises(Problem):self.act('milestone_delete',id=mid)
        with self.assertRaises(Problem):self.record('documents',relatedId='other-project-id')
        self.act('comment',targetType='milestone',id=mid,text='@viewer please review @outsider')
        self.assertEqual(len(self.w.state('viewer')['notifications']),1)
        self.assertEqual(self.w.state('outsider')['notifications'],[])
    def test_control_comments_survive_record_edit(self):
        row=self.record('risk')
        self.act('comment',targetType='risk',id=row['id'],text='Keep this discussion')
        self.act('control',module='risk',**{**row,'title':'Revised'})
        self.assertEqual(self.project()['controls']['risk'][0]['comments'][0]['text'],'Keep this discussion')
    def test_acceptance_requires_supporting_evidence(self):
        self.act('milestone_add');mid=self.project()['milestones'][0]['id']
        with self.assertRaises(Problem):self.act('milestone_cell',id=mid,field='status',value='ACCEPTED')
        self.act('milestone_details',id=mid,status='ACCEPTED',evidence='Customer acceptance letter')
        self.assertEqual(self.project()['deliverySummary']['accepted'],1)

if __name__=='__main__':unittest.main()
