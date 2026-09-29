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
    def test_static_allowlist(self):
        self.assertEqual(self.request('/server.py')[0],404)
        status,h,b=self.request('/')
        self.assertEqual(status,200);self.assertIn('Content-Security-Policy',h)

if __name__=='__main__':unittest.main()
