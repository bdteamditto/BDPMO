import http.client
import json
import os
import tempfile
import threading
import unittest
from http.server import HTTPServer
import server

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        server.DB=os.path.join(cls.tmp.name,'test.sqlite3')
        server.add_user('tester','long-test-password')
        cls.http=HTTPServer(('127.0.0.1',0),server.Handler)
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown();cls.http.server_close();cls.tmp.cleanup()
    def request(self,path,data=None,headers=None):
        c=http.client.HTTPConnection('127.0.0.1',self.http.server_port)
        c.request('POST' if data is not None else 'GET',path,json.dumps(data) if data is not None else None,{'Content-Type':'application/json',**(headers or {})})
        r=c.getresponse();status=r.status; hs=dict(r.getheaders());body=r.read();c.close()
        return status,hs,body
    def test_auth_csrf_and_logout(self):
        self.assertEqual(self.request('/api/state')[0],401)
        self.assertEqual(self.request('/api/login',{'user':'tester','password':'wrong'})[0],401)
        status,h,_=self.request('/api/login',{'user':'tester','password':'long-test-password'})
        self.assertEqual(status,200);self.assertIn('HttpOnly',h['Set-Cookie'])
        cookie={'Cookie':h['Set-Cookie'].split(';')[0]}
        _,_,b=self.request('/api/state',headers=cookie)
        token=json.loads(b)['csrf']
        self.assertEqual(self.request('/api/action',{'action':'create_project','name':'API'},cookie)[0],403)
        cookie['X-CSRF-Token']=token
        self.assertEqual(self.request('/api/action',{'action':'create_project','name':'API'},cookie)[0],200)
        self.assertEqual(self.request('/api/action',{'action':'create_project','name':'bad'},{**cookie,'Origin':'https://evil.invalid'})[0],403)
        self.assertEqual(self.request('/api/logout',{},cookie)[0],200)
        self.assertEqual(self.request('/api/state',headers=cookie)[0],401)
    def test_tor_http_payment_audit_and_reload(self):
        status,h,_=self.request('/api/login',{'user':'tester','password':'long-test-password'})
        self.assertEqual(status,200)
        headers={'Cookie':h['Set-Cookie'].split(';')[0]}
        state=json.loads(self.request('/api/state',headers=headers)[2])
        headers['X-CSRF-Token']=state['csrf']
        def action(action_name, **data):
            status,_,body=self.request('/api/action',{'action':action_name,**data},headers)
            self.assertEqual(status,200,body)
        def project():
            state=json.loads(self.request('/api/state',headers=headers)[2])
            return next(p for p in state['projects'] if p['name']=='HTTP TOR')
        action('create_project',name='HTTP TOR')
        pid=project()['id']
        action('project_info',project=pid,contractValue='1000000')
        action('milestone_add',project=pid)
        mid=project()['milestones'][0]['id']
        action('milestone_cell',project=pid,id=mid,field='paymentNo',value='1')
        action('milestone_cell',project=pid,id=mid,field='paymentPercent',value='25')
        action('milestone_cell',project=pid,id=mid,field='deliverables',value='Demo acceptance report')
        saved=project()
        self.assertEqual(saved['paymentSummary']['groups']['1']['amount'],250000)
        self.assertEqual(saved['milestones'][0]['deliverables'],'Demo acceptance report')
        event=saved['events'][0]
        self.assertEqual(event['actor'],'tester')
        self.assertEqual(json.loads(event['detail'])['after'],'Demo acceptance report')
        status,_,_=self.request('/api/action',{'action':'milestone_cell','project':pid,'id':mid,'field':'paymentPercent','value':'NaN'},headers)
        self.assertEqual(status,400)
        self.assertEqual(project()['paymentSummary'],saved['paymentSummary'])
        self.assertEqual(project()['events'],saved['events'])

    def test_lifecycle_records_and_checklists_survive_http_reload(self):
        from lifecycle import MODULES
        status,h,_=self.request('/api/login',{'user':'tester','password':'long-test-password'})
        self.assertEqual(status,200)
        headers={'Cookie':h['Set-Cookie'].split(';')[0]}
        getstate=lambda:json.loads(self.request('/api/state',headers=headers)[2])
        headers['X-CSRF-Token']=getstate()['csrf']
        self.assertEqual(self.request('/api/action',{'action':'create_project','name':'HTTP Lifecycle'},headers)[0],200)
        p=next(p for p in getstate()['projects'] if p['name']=='HTTP Lifecycle')
        for module,meta in MODULES.items():
            values={f[0]:f[3][0] if f[2]=='select' else 'TODO' if f[2]=='status' else '' for f in meta['fields']}
            values.update(title='Record '+module,owner='tester')
            status,_,body=self.request('/api/action',{'action':'control','project':p['id'],'module':module,**values},headers)
            self.assertEqual(status,200,body)
        status,_,body=self.request('/api/action',{'action':'checklist','project':p['id'],'id':'project_open','status':'DONE','owner':'tester','evidence':'Opening approval'},headers)
        self.assertEqual(status,200,body)
        saved=next(x for x in getstate()['projects'] if x['id']==p['id'])
        self.assertEqual(set(saved['controls']),set(MODULES))
        self.assertEqual(saved['checks']['project_open']['evidence'],'Opening approval')
        self.assertEqual(saved['events'][0]['action'],'checklist')
        self.assertTrue(saved['closureBlockers'])

    def test_static_allowlist(self):
        self.assertEqual(self.request('/server.py')[0],404)
        status,h,b=self.request('/')
        self.assertEqual(status,200);self.assertIn('Content-Security-Policy',h)

if __name__=='__main__':unittest.main()
