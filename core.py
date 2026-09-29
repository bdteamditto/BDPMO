"""Persistent project workspace. All access decisions are enforced here."""
import json
import sqlite3
import uuid
from datetime import date, datetime, timezone

PHASES = ['Contract', 'Procurement', 'Planning', 'Delivery', 'Acceptance', 'Billing', 'Closure']
STATUSES = ['TODO', 'IN_PROGRESS', 'WAITING', 'BLOCKED', 'REVIEW', 'DONE']

class Problem(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status

class Workspace:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, password TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS members(project TEXT, user TEXT, role TEXT, addedBy TEXT, grantedBy TEXT, PRIMARY KEY(project,user));
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, project TEXT, actor TEXT, action TEXT, detail TEXT, at TEXT);
        CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY, project TEXT, user TEXT, text TEXT, seen INTEGER DEFAULT 0);
        ''')

    def close(self):
        self.db.close()

    def role(self, project, user):
        row = self.db.execute('SELECT role FROM members WHERE project=? AND user=?', (project, user)).fetchone()
        if not row:
            raise Problem('คุณไม่มีสิทธิ์เข้าถึงโครงการนี้', 403)
        return row['role']

    def project(self, project, user, write=False):
        role = self.role(project, user)
        if write and role == 'VIEWER':
            raise Problem('VIEWER ดูข้อมูลได้อย่างเดียว', 403)
        return json.loads(self.db.execute('SELECT data FROM projects WHERE id=?', (project,)).fetchone()['data'])

    def save(self, p):
        self.db.execute('INSERT OR REPLACE INTO projects VALUES (?,?)', (p['id'], json.dumps(p, ensure_ascii=False)))

    def event(self, p, actor, action, detail):
        self.db.execute('INSERT INTO events(project,actor,action,detail,at) VALUES (?,?,?,?,?)', (p, actor, action, json.dumps(detail, ensure_ascii=False), datetime.now(timezone.utc).isoformat()))

    def notify(self, p, user, text):
        self.db.execute('INSERT INTO notifications(project,user,text) VALUES (?,?,?)', (p, user, text))

    def state(self, user):
        projects = []
        for row in self.db.execute('SELECT project,role FROM members WHERE user=?', (user,)):
            p = self.project(row['project'], user)
            p['role'] = row['role']
            p['members'] = [dict(r) for r in self.db.execute('SELECT user,role,addedBy,grantedBy FROM members WHERE project=?', (p['id'],))]
            p['events'] = [dict(r) for r in self.db.execute('SELECT * FROM events WHERE project=? ORDER BY id DESC LIMIT 100', (p['id'],))]
            p['health'] = health(p)
            projects.append(p)
        notices = [dict(r) for r in self.db.execute('SELECT n.* FROM notifications n JOIN members m ON m.project=n.project AND m.user=n.user WHERE n.user=? ORDER BY n.id DESC LIMIT 100', (user,))]
        return {'user': user, 'projects': projects, 'notifications': notices, 'phases': PHASES, 'statuses': STATUSES}

    def act(self, user, action, d):
        with self.db:
            if action == 'create_project':
                p = {'id': uuid.uuid4().hex, 'name': required(d, 'name'), 'phase': 'Contract', 'allowEditorInvites': False, 'tasks': [], 'handover': '', 'milestone': '', 'due': '', 'completed': False}
                self.save(p)
                self.db.execute('INSERT INTO members VALUES (?,?,?,?,?)', (p['id'], user, 'OWNER', user, user))
                self.event(p['id'], user, action, {'name': p['name']})
                return
            if action == 'read_notice':
                self.db.execute('UPDATE notifications SET seen=1 WHERE id=? AND user=?', (d.get('id'), user))
                return
            pid = required(d, 'project')
            p = self.project(pid, user, write=True)
            role = self.role(pid, user)
            if action == 'member':
                target = required(d, 'user')
                newrole = d.get('role')
                if newrole not in ['OWNER', 'EDITOR', 'VIEWER', 'REMOVE']:
                    raise Problem('สิทธิ์ไม่ถูกต้อง')
                old = self.db.execute('SELECT * FROM members WHERE project=? AND user=?', (pid,target)).fetchone()
                if role != 'OWNER' and (not p['allowEditorInvites'] or old or newrole not in ['EDITOR','VIEWER']):
                    raise Problem('ไม่มีสิทธิ์จัดการสมาชิกนี้', 403)
                if not self.db.execute('SELECT 1 FROM users WHERE id=?', (target,)).fetchone():
                    raise Problem('ไม่พบบัญชีนี้ ให้ผู้ดูแลสร้างบัญชีก่อน')
                if old and old['role'] == 'OWNER' and newrole != 'OWNER':
                    count = self.db.execute("SELECT count(*) FROM members WHERE project=? AND role='OWNER'", (pid,)).fetchone()[0]
                    if count == 1:
                        raise Problem('ต้องเหลือ OWNER อย่างน้อยหนึ่งคน')
                if newrole == 'REMOVE':
                    self.db.execute('DELETE FROM members WHERE project=? AND user=?', (pid,target))
                else:
                    self.db.execute('INSERT OR REPLACE INTO members VALUES (?,?,?,?,?)', (pid,target,newrole,old['addedBy'] if old else user,user))
                self.event(pid,user,action,{'user':target,'before':old['role'] if old else None,'after':newrole})
                return
            if action == 'project':
                if role != 'OWNER':
                    raise Problem('เฉพาะ OWNER เปลี่ยนการตั้งค่าโครงการได้',403)
                if d.get('phase') not in PHASES:
                    raise Problem('Phase ไม่ถูกต้อง')
                p.update(name=required(d,'name'),phase=d['phase'],milestone=str(d.get('milestone',''))[:500],due=valid_date(d.get('due','')),allowEditorInvites=d.get('allowEditorInvites') is True)
                completed = d.get('completed') is True
                if completed and (p['phase'] != 'Closure' or any(t['status'] != 'DONE' for t in p['tasks'])):
                    raise Problem('ปิดโครงการได้เมื่ออยู่ Closure และงานทั้งหมดเสร็จแล้ว')
                p['completed'] = completed
            elif action == 'handover':
                p['handover'] = required(d,'text',10000)
            elif action == 'task':
                if p['completed']:
                    raise Problem('เปิดโครงการอีกครั้งก่อนแก้งาน')
                tid = d.get('id') or uuid.uuid4().hex
                old = next((t for t in p['tasks'] if t['id']==tid), None)
                if d.get('id') and not old:
                    raise Problem('ไม่พบงาน',404)
                status = d.get('status','TODO')
                if status not in STATUSES or d.get('priority','NORMAL') not in ['HIGH','NORMAL','LOW']:
                    raise Problem('สถานะหรือความสำคัญไม่ถูกต้อง')
                owner = required(d,'owner')
                self.role(pid,owner)
                waiting = str(d.get('waiting',''))[:1000]
                if status in ['WAITING','BLOCKED'] and not waiting.strip():
                    raise Problem('กรุณาระบุว่ารอใครหรือมีอะไรติดขัด')
                deps = d.get('dependencies',[])
                if not isinstance(deps,list) or any(not isinstance(x,str) for x in deps):
                    raise Problem('Dependency ไม่ถูกต้อง')
                ids = {t['id'] for t in p['tasks']}
                if any(x not in ids or x==tid for x in deps):
                    raise Problem('Dependency ต้องเป็นงานอื่นในโครงการเดียวกัน')
                graph = {t['id']:t['dependencies'] for t in p['tasks']}
                graph[tid] = deps
                def visit(n, path):
                    if n in path:
                        raise Problem('Dependency วนกลับมาที่งานเดิม')
                    for child in graph.get(n,[]): visit(child,path|{n})
                visit(tid,set())
                if status == 'DONE' and any(t['id'] in deps and t['status']!='DONE' for t in p['tasks']):
                    raise Problem('งานที่ต้องทำก่อนยังไม่เสร็จ')
                if old and old['status']=='DONE' and status!='DONE' and any(t['status']=='DONE' and tid in t['dependencies'] for t in p['tasks']):
                    raise Problem('เปิดงานที่อ้างอิงงานนี้อีกครั้งก่อน')
                task = {'id':tid,'title':required(d,'title'),'owner':owner,'due':valid_date(d.get('due','')),'status':status,'priority':d.get('priority','NORMAL'),'waiting':waiting,'next':str(d.get('next',''))[:2000],'evidence':str(d.get('evidence',''))[:2000],'dependencies':deps,'comments':old['comments'] if old else [],'updated':datetime.now(timezone.utc).isoformat()}
                p['tasks'] = [task if t['id']==tid else t for t in p['tasks']] if old else p['tasks']+[task]
                if not old or old['owner'] != owner:
                    self.notify(pid,owner,'ได้รับมอบหมาย: '+task['title'])
            elif action == 'comment':
                task = next((t for t in p['tasks'] if t['id']==d.get('id')),None)
                if not task: raise Problem('ไม่พบงาน',404)
                comment = {'author':user,'text':required(d,'text',4000),'at':datetime.now(timezone.utc).isoformat()}
                task['comments'].append(comment)
                members = {r['user'] for r in self.db.execute('SELECT user FROM members WHERE project=?',(pid,))}
                mentioned = {word[1:] for word in comment['text'].split() if word.startswith('@')}
                for target in mentioned & members:
                    self.notify(pid,target,user+' กล่าวถึงคุณ: '+task['title'])
            else:
                raise Problem('ไม่รู้จักคำสั่ง')
            self.save(p)
            self.event(pid,user,action,d)

def required(d, key, limit=200):
    value = d.get(key)
    if not isinstance(value,str) or not value.strip() or len(value)>limit:
        raise Problem('ข้อมูลไม่ถูกต้อง: '+key)
    return value.strip()

def valid_date(value):
    if value == '': return ''
    try: return date.fromisoformat(value).isoformat()
    except (TypeError,ValueError): raise Problem('วันที่ไม่ถูกต้อง')

def health(p):
    active = [t for t in p['tasks'] if t['status']!='DONE']
    today = date.today().isoformat()
    if p['completed']: return {'status':'COMPLETED','reason':'ปิดโครงการแล้ว'}
    blocked = [t for t in active if t['status']=='BLOCKED']
    if blocked: return {'status':'BLOCKED','reason':blocked[0]['waiting']}
    if (p['due'] and p['due']<today) or any(t['due'] and t['due']<today for t in active):
        return {'status':'OVERDUE','reason':'มีงานหรือ milestone เกินกำหนด'}
    if any(t['priority']=='HIGH' or t['status']=='WAITING' or (t['due'] and 0 <= (date.fromisoformat(t['due'])-date.today()).days <= 3) for t in active):
        return {'status':'AT RISK','reason':'มีงานสำคัญ ใกล้กำหนด หรือรอการตอบกลับ'}
    return {'status':'ON TRACK','reason':'ไม่มีงานเกินกำหนดหรือ blocker ที่บันทึกไว้'}
