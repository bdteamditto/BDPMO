"""Local/pilot HTTP server. Put behind HTTPS for remote team access."""
import argparse
import getpass
import hashlib
import hmac
import json
import os
import secrets
import time
from http.cookies import SimpleCookie
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from core import Workspace, Problem

DB = os.environ.get('PMO_DB','pmo.sqlite3')
SESSIONS = {}
ATTEMPTS = {}
STATIC = Path(__file__).parent / 'static'

def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    return salt + ':' + hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),600000).hex()

def add_user(name, password):
    if not name or len(name)>100 or any(c.isspace() for c in name): raise ValueError('Username must be 1–100 characters without spaces')
    if len(password)<12: raise ValueError('Password must have at least 12 characters')
    w=Workspace(DB)
    with w.db: w.db.execute('INSERT INTO users VALUES (?,?)',(name,hash_password(password)))
    w.close()

class Handler(BaseHTTPRequestHandler):
    def send(self, status, data, cookie=None):
        body=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        if cookie: self.send_header('Set-Cookie',cookie)
        self.end_headers(); self.wfile.write(body)

    def session(self):
        c=SimpleCookie(); c.load(self.headers.get('Cookie',''))
        token=c['pmo'].value if 'pmo' in c else ''
        session=SESSIONS.get(token)
        if not session or session['expires']<time.time():
            SESSIONS.pop(token,None)
            raise Problem('กรุณาเข้าสู่ระบบ',401)
        return token,session

    def do_GET(self):
        if self.path=='/api/state':
            w=Workspace(DB)
            try:
                _,s=self.session()
                self.send(200,{**w.state(s['user']),'csrf':s['csrf']})
            except Problem as e: self.send(e.status,{'error':str(e)})
            finally: w.close()
            return
        files={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
        if self.path not in files: self.send(404,{'error':'Not found'}); return
        path=STATIC/files[self.path]
        self.send_response(200)
        self.send_header('Content-Type',{'html':'text/html; charset=utf-8','js':'text/javascript; charset=utf-8','css':'text/css; charset=utf-8'}[path.suffix[1:]])
        self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers(); self.wfile.write(path.read_bytes())

    def do_POST(self):
        w=Workspace(DB)
        try:
            origin=self.headers.get('Origin')
            if origin and origin not in ['http://'+self.headers.get('Host',''),'https://'+self.headers.get('Host','')]: raise Problem('Invalid origin',403)
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=65536: raise Problem('Request too large or empty',413)
            d=json.loads(self.rfile.read(size))
            if not isinstance(d,dict): raise Problem('Invalid request')
            if self.path=='/api/login':
                key=self.client_address[0]
                recent=[t for t in ATTEMPTS.get(key,[]) if t>time.time()-300]
                ATTEMPTS[key]=recent
                if len(recent)>=10: raise Problem('ลองใหม่ใน 5 นาที',429)
                recent.append(time.time())
                name=d.get('user',''); password=d.get('password','')
                if not isinstance(name,str) or not isinstance(password,str): raise Problem('Invalid login')
                row=w.db.execute('SELECT password FROM users WHERE id=?',(name,)).fetchone()
                saved=row['password'] if row else hash_password('dummy password')
                if not hmac.compare_digest(saved,hash_password(password,saved.split(':')[0])) or not row: raise Problem('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง',401)
                ATTEMPTS.pop(key,None)
                token=secrets.token_urlsafe(32)
                SESSIONS[token]={'user':name,'csrf':secrets.token_urlsafe(32),'expires':time.time()+28800}
                secure='; Secure' if os.environ.get('PMO_SECURE_COOKIE')=='1' else ''
                self.send(200,{'ok':True},'pmo='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800'+secure); return
            token,s=self.session()
            if not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),s['csrf']): raise Problem('Invalid session request',403)
            if self.path=='/api/logout':
                SESSIONS.pop(token,None); self.send(200,{'ok':True},'pmo=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'); return
            if self.path!='/api/action': raise Problem('Not found',404)
            w.act(s['user'],d.get('action'),d)
            self.send(200,{'ok':True})
        except Problem as e: self.send(e.status,{'error':str(e)})
        except (ValueError,TypeError,KeyError): self.send(400,{'error':'ข้อมูลไม่ถูกต้อง'})
        finally: w.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--add-user'); parser.add_argument('--port',type=int,default=8000); parser.add_argument('--host',default='127.0.0.1')
    args=parser.parse_args()
    if args.add_user: add_user(args.add_user,getpass.getpass('Password (12+ characters): '))
    else:
        Workspace(DB).close()
        print(f'PMO workspace: http://{args.host}:{args.port}',flush=True)
        HTTPServer((args.host,args.port),Handler).serve_forever()
