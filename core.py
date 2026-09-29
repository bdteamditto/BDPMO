"""Persistent project workspace. All access decisions are enforced here."""
import json
import math
from lifecycle import MODULES, CHECKS, PHASE_LABELS, delivery_summary, lifecycle_checks, closure_blockers, control_summary
import sqlite3
import uuid
from datetime import date, datetime, timezone

PHASES = ['Contract', 'Procurement', 'Planning', 'Delivery', 'Acceptance', 'Billing', 'Closure']
STATUSES = ['TODO', 'IN_PROGRESS', 'WAITING', 'BLOCKED', 'REVIEW', 'DONE']
MILESTONE_STATUSES = [
    '',
    'NOT_DUE', 'IN_PROGRESS', 'READY', 'DELIVERED',
    'WAITING_REPLY', 'WAITING_ACCEPTANCE', 'ACCEPTED', 'LATE', 'BLOCKED'
]
PROJECT_INFO_FIELDS = {
    'contractName', 'contractNo', 'signedDate', 'projectStartDate',
    'deliveryDueDate', 'projectCode', 'contractValue'
}
MILESTONE_FIELDS = [
    'workNo', 'paymentNo', 'paymentPercent', 'contractMilestone', 'deliverables',
    'scope', 'contractClause', 'contractDue', 'days', 'torDue', 'planDue',
    'month', 'deliveredDate', 'letterRef', 'customerReplyRef',
    'customerAcceptedDate', 'status'
]

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
        row = self.db.execute('SELECT data FROM projects WHERE id=?', (project,)).fetchone()
        if not row:
            raise Problem('ไม่พบโครงการ', 404)
        p = json.loads(row['data'])
        p.setdefault('allowEditorInvites', False)
        p.setdefault('tasks', [])
        p.setdefault('handover', '')
        p.setdefault('milestone', '')
        p.setdefault('due', '')
        p.setdefault('completed', False)
        p.setdefault('projectInfo', default_project_info(p.get('name', '')))
        p.setdefault('milestones', [])
        p.setdefault('controls', {})
        p.setdefault('checks', {})
        return p

    def save(self, p):
        self.db.execute('INSERT OR REPLACE INTO projects VALUES (?,?)', (p['id'], json.dumps(p, ensure_ascii=False)))

    def event(self, p, actor, action, detail):
        self.db.execute(
            'INSERT INTO events(project,actor,action,detail,at) VALUES (?,?,?,?,?)',
            (p, actor, action, json.dumps(detail, ensure_ascii=False), datetime.now(timezone.utc).isoformat())
        )

    def notify(self, p, user, text):
        self.db.execute('INSERT INTO notifications(project,user,text) VALUES (?,?,?)', (p, user, text))

    def state(self, user):
        projects = []
        for row in self.db.execute('SELECT project,role FROM members WHERE user=?', (user,)):
            p = self.project(row['project'], user)
            p['role'] = row['role']
            p['members'] = [dict(r) for r in self.db.execute(
                'SELECT user,role,addedBy,grantedBy FROM members WHERE project=?', (p['id'],)
            )]
            p['events'] = [dict(r) for r in self.db.execute(
                'SELECT * FROM events WHERE project=? ORDER BY id DESC LIMIT 300', (p['id'],)
            )]
            p['deliverySummary'] = delivery_summary(p)
            p['lifecycleChecks'] = lifecycle_checks(p)
            p['closureBlockers'] = closure_blockers(p)
            p['controlSummary'] = control_summary(p)
            p['health'] = health(p)
            p['paymentSummary'] = payment_summary(p)
            projects.append(p)
        notices = [dict(r) for r in self.db.execute(
            'SELECT n.* FROM notifications n JOIN members m ON m.project=n.project AND m.user=n.user '
            'WHERE n.user=? ORDER BY n.id DESC LIMIT 100', (user,)
        )]
        return {
            'user': user,
            'projects': projects,
            'notifications': notices,
            'phases': PHASES,
            'phaseLabels': PHASE_LABELS,
            'controlModules': MODULES,
            'statuses': STATUSES,
            'milestoneStatuses': MILESTONE_STATUSES
        }

    def act(self, user, action, d):
        with self.db:
            if action == 'create_project':
                p = {
                    'id': uuid.uuid4().hex,
                    'name': required(d, 'name'),
                    'phase': 'Contract',
                    'allowEditorInvites': False,
                    'tasks': [],
                    'handover': '',
                    'milestone': '',
                    'due': '',
                    'completed': False,
                    'projectInfo': default_project_info(required(d, 'name')),
                    'milestones': []
                }
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

            if p['completed'] and action not in ['project','member']:
                raise Problem('เปิดโครงการอีกครั้งก่อนแก้ไขข้อมูล')

            if action == 'control':
                module = required(d, 'module')
                if module not in MODULES: raise Problem('หมวดไม่ถูกต้อง')
                records = p['controls'].setdefault(module, [])
                rid = d.get('id') or uuid.uuid4().hex
                old = next((r for r in records if r['id']==rid), None)
                if d.get('id') and not old: raise Problem('ไม่พบรายการ',404)
                record = {'id':rid,'comments':old.get('comments',[]) if old else []}
                for key,label,kind,*options in MODULES[module]['fields']:
                    value=d.get(key,'')
                    if kind=='money': value=money_value(value)
                    elif kind=='date': value=valid_date(value)
                    elif kind=='month':
                        if value:
                            if not isinstance(value,str) or len(value)!=7: raise Problem('รอบรายงานไม่ถูกต้อง')
                            valid_date(value+'-01')
                    elif kind=='select':
                        if value not in options[0]: raise Problem('ข้อมูลไม่ถูกต้อง: '+label)
                    elif kind=='status':
                        if value not in STATUSES: raise Problem('สถานะไม่ถูกต้อง')
                    elif kind=='member':
                        if value: self.role(pid,value)
                    elif not isinstance(value,str) or len(value)>10000: raise Problem('ข้อมูลไม่ถูกต้อง: '+label)
                    record[key]=value.strip() if isinstance(value,str) else value
                record['title']=required(d,'title',500)
                if record['status'] in ['WAITING','BLOCKED'] and not record['notes']:raise Problem('ระบุสิ่งที่รอ / ติดขัดในรายละเอียด')
                if record['status']=='DONE' and not record['evidence']:raise Problem('ระบุหลักฐานก่อนยืนยันเสร็จ')
                related={r['id'] for rows in p['controls'].values() for r in rows}|{m['id'] for m in p['milestones']}|{t['id'] for t in p['tasks']}
                if record.get('relatedId') and record['relatedId'] not in related:raise Problem('รายการอ้างอิงต้องอยู่ในโครงการเดียวกัน')
                if record.get('milestoneId') and record['milestoneId'] not in {m['id'] for m in p['milestones']}:raise Problem('ไม่พบงวดงานที่อ้างอิง')
                if module=='finance' and record['status']=='DONE' and record['kind'] in ['CUSTOMER_PAYMENT','VENDOR_PAYMENT']:
                    if record['amount'] is None or not record['completedDate']:raise Problem('ระบุจำนวนเงินและวันที่รับ/จ่ายจริง')
                record['updated']=datetime.now(timezone.utc).isoformat()
                p['controls'][module]=[record if r['id']==rid else r for r in records] if old else records+[record]
                validate_back_to_back(p)
                self.save(p)
                self.event(pid,user,action,{'module':module,'id':rid,'title':record['title'],'before':old,'after':record})
                if record['owner'] and (not old or old['owner']!=record['owner']):self.notify(pid,record['owner'],'ได้รับมอบหมาย: '+record['title'])
                return

            if action == 'checklist':
                key=required(d,'id')
                if key not in {k for items in CHECKS.values() for k,_,_ in items}:raise Problem('Checklist ไม่ถูกต้อง')
                status=d.get('status')
                if status not in STATUSES:raise Problem('สถานะไม่ถูกต้อง')
                owner=d.get('owner','')
                if owner:self.role(pid,owner)
                evidence=str(d.get('evidence',''))[:10000].strip()
                notes=str(d.get('notes',''))[:10000].strip()
                if status=='DONE' and not evidence:raise Problem('ระบุหลักฐาน หรือเหตุผลที่ไม่เกี่ยวข้อง ก่อนยืนยันเสร็จ')
                if status in ['WAITING','BLOCKED'] and not notes:raise Problem('ระบุสิ่งที่รอ / ติดขัด')
                before=p['checks'].get(key)
                item={'status':status,'owner':owner,'due':valid_date(d.get('due','')),'evidence':evidence,'notes':notes,'updated':datetime.now(timezone.utc).isoformat()}
                p['checks'][key]=item
                self.save(p)
                self.event(pid,user,action,{'id':key,'before':before,'after':item})
                if owner and (not before or before.get('owner')!=owner):self.notify(pid,owner,'ได้รับมอบหมาย: '+next(title for items in CHECKS.values() for k,title,_ in items if k==key))
                return

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
                    self.db.execute(
                        'INSERT OR REPLACE INTO members VALUES (?,?,?,?,?)',
                        (pid,target,newrole,old['addedBy'] if old else user,user)
                    )
                self.event(pid,user,action,{'user':target,'before':old['role'] if old else None,'after':newrole})
                return

            if action == 'project':
                if role != 'OWNER':
                    raise Problem('เฉพาะ OWNER เปลี่ยนการตั้งค่าโครงการได้',403)
                if d.get('phase') not in PHASES:
                    raise Problem('Phase ไม่ถูกต้อง')
                p.update(
                    name=required(d,'name'),
                    phase=d['phase'],
                    milestone=str(d.get('milestone',''))[:500],
                    due=valid_date(d.get('due','')),
                    allowEditorInvites=d.get('allowEditorInvites') is True
                )
                completed = d.get('completed') is True
                if completed and closure_blockers(p):
                    raise Problem('ยังปิดโครงการไม่ได้: '+'; '.join(closure_blockers(p)))
                p['completed'] = completed

            elif action == 'project_info':
                if role != 'OWNER':
                    raise Problem('เฉพาะ OWNER แก้ข้อมูลสัญญาหลักได้', 403)
                before = dict(p['projectInfo'])
                info = dict(before)
                for key in PROJECT_INFO_FIELDS:
                    if key == 'contractValue':
                        info[key] = money_value(d.get(key, info.get(key, 0)))
                    else:
                        info[key] = str(d.get(key, info.get(key, '')))[:2000].strip()
                p['projectInfo'] = info
                if info.get('contractName'):
                    p['name'] = info['contractName']
                self.save(p)
                changes = {
                    key: {'before': before.get(key), 'after': info.get(key)}
                    for key in PROJECT_INFO_FIELDS if before.get(key) != info.get(key)
                }
                if changes:
                    self.event(pid, user, action, {'changes': changes})
                return

            elif action == 'milestone_details':
                row=next((m for m in p['milestones'] if m['id']==d.get('id')),None)
                if not row:raise Problem('ไม่พบงวดงาน',404)
                before=dict(row)
                owner=d.get('owner','')
                if owner:self.role(pid,owner)
                status=normalize_milestone_value('status',d.get('status',row.get('status')))
                row.update(owner=owner,status=status, next=str(d.get('next',''))[:2000],waiting=str(d.get('waiting',''))[:2000],handover=str(d.get('handover',''))[:10000],evidence=str(d.get('evidence',''))[:10000])
                if status=='BLOCKED' and not row['waiting'].strip():raise Problem('ระบุสิ่งที่ติดขัด')
                if status=='ACCEPTED' and not (row['evidence'].strip() or row.get('customerAcceptedDate')):raise Problem('ระบุหลักฐานหรือวันตรวจรับก่อนยืนยันตรวจรับแล้ว')
                self.save(p)
                self.event(pid,user,action,{'id':row['id'],'workNo':row['workNo'],'before':before,'after':row})
                if owner and before.get('owner')!=owner:self.notify(pid,owner,'ได้รับมอบหมายงวดงาน '+row['workNo'])
                return

            elif action == 'milestone_add':
                milestone = blank_milestone()
                milestone['id'] = uuid.uuid4().hex
                milestone['workNo'] = next_work_no(p['milestones'])
                p['milestones'].append(milestone)
                self.save(p)
                self.event(pid, user, action, {'id': milestone['id'], 'workNo': milestone['workNo']})
                return

            elif action == 'milestone_cells':
                cells=d.get('cells')
                if not isinstance(cells,list) or not 0<len(cells)<=500:raise Problem('วางได้ไม่เกิน 500 ช่องต่อครั้ง')
                changes=[]
                for cell in cells:
                    if not isinstance(cell,dict):raise Problem('ข้อมูลช่องไม่ถูกต้อง')
                    field=cell.get('field')
                    if field not in MILESTONE_FIELDS:raise Problem('คอลัมน์ไม่ถูกต้อง')
                    row=next((m for m in p['milestones'] if m['id']==cell.get('id')),None)
                    if not row:raise Problem('ไม่พบงวดงาน',404)
                    before=row.get(field,'')
                    after=normalize_milestone_value(field,cell.get('value'))
                    row[field]=after
                    if before!=after:changes.append({'id':row['id'],'workNo':row['workNo'],'field':field,'before':before,'after':after,'reason':'วางข้อมูลหลายช่อง'})
                validate_payment_percent(p)
                for row in p['milestones']:
                    if row['status']=='ACCEPTED' and not (row.get('evidence') or row.get('customerAcceptedDate')):raise Problem('ระบุหลักฐานหรือวันตรวจรับก่อนยืนยันตรวจรับแล้ว')
                self.save(p)
                for change in changes:self.event(pid,user,'milestone_cell',change)
                return

            elif action == 'milestone_cell':
                mid = required(d, 'id')
                field = required(d, 'field')
                if field not in MILESTONE_FIELDS:
                    raise Problem('คอลัมน์ไม่ถูกต้อง')
                row = next((m for m in p['milestones'] if m['id'] == mid), None)
                if not row:
                    raise Problem('ไม่พบงวดงาน', 404)
                before = row.get(field, '')
                after = normalize_milestone_value(field, d.get('value'))
                if before == after:
                    return
                row[field] = after
                if field=='status' and after=='ACCEPTED' and not (row.get('evidence') or row.get('customerAcceptedDate')):raise Problem('ระบุหลักฐานหรือวันตรวจรับก่อนยืนยันตรวจรับแล้ว')
                validate_payment_percent(p)
                self.save(p)
                self.event(pid, user, action, {
                    'id': mid,
                    'workNo': row.get('workNo'),
                    'field': field,
                    'before': before,
                    'after': after,
                    'reason': str(d.get('reason',''))[:500]
                })
                return

            elif action == 'milestone_delete':
                mid = required(d, 'id')
                row = next((m for m in p['milestones'] if m['id'] == mid), None)
                if not row:
                    raise Problem('ไม่พบงวดงาน', 404)
                if any(r.get('relatedId')==mid or r.get('milestoneId')==mid for rows in p['controls'].values() for r in rows):raise Problem('ย้ายเอกสารหรือการเงินที่อ้างอิงงวดนี้ก่อนลบ')
                p['milestones'] = [m for m in p['milestones'] if m['id'] != mid]
                self.save(p)
                self.event(pid, user, action, {'id': mid, 'workNo': row.get('workNo')})
                return

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
                backup=d.get('backupOwner','')
                if backup:self.role(pid,backup)
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
                task = {
                    'id':tid,
                    'title':required(d,'title'),
                    'owner':owner,
                    'backupOwner':backup,
                    'doneNote':str(d.get('doneNote',''))[:4000],
                    'remainingNote':str(d.get('remainingNote',''))[:4000],
                    'due':valid_date(d.get('due','')),
                    'status':status,
                    'priority':d.get('priority','NORMAL'),
                    'waiting':waiting,
                    'next':str(d.get('next',''))[:2000],
                    'evidence':str(d.get('evidence',''))[:2000],
                    'dependencies':deps,
                    'comments':old['comments'] if old else [],
                    'updated':datetime.now(timezone.utc).isoformat()
                }
                p['tasks'] = [task if t['id']==tid else t for t in p['tasks']] if old else p['tasks']+[task]
                if not old or old['owner'] != owner:
                    self.notify(pid,owner,'ได้รับมอบหมาย: '+task['title'])

            elif action == 'comment':
                target_type=d.get('targetType','task')
                if target_type=='task':items=p['tasks']
                elif target_type=='milestone':items=p['milestones']
                elif target_type in MODULES:items=p['controls'].get(target_type,[])
                else:raise Problem('ประเภทความคิดเห็นไม่ถูกต้อง')
                task = next((t for t in items if t['id']==d.get('id')),None)
                if not task: raise Problem('ไม่พบรายการ',404)
                comment = {'author':user,'text':required(d,'text',4000),'at':datetime.now(timezone.utc).isoformat()}
                task.setdefault('comments',[]).append(comment)
                members = {r['user'] for r in self.db.execute('SELECT user FROM members WHERE project=?',(pid,))}
                mentioned = {word[1:] for word in comment['text'].split() if word.startswith('@')}
                for target in mentioned & members:
                    self.notify(pid,target,user+' กล่าวถึงคุณ: '+task.get('title','งวด '+task.get('workNo','')))

            else:
                raise Problem('ไม่รู้จักคำสั่ง')

            self.save(p)
            self.event(pid,user,action,d)

def default_project_info(name=''):
    return {
        'contractName': name,
        'contractNo': '',
        'signedDate': '',
        'projectStartDate': '',
        'deliveryDueDate': '',
        'projectCode': '',
        'contractValue': 0
    }

def blank_milestone():
    return {
        'id': '',
        'workNo': '',
        'paymentNo': '',
        'paymentPercent': 0,
        'contractMilestone': '',
        'deliverables': '',
        'scope': '',
        'contractClause': '',
        'contractDue': '',
        'days': '',
        'torDue': '',
        'planDue': '',
        'month': '',
        'deliveredDate': '',
        'letterRef': '',
        'customerReplyRef': '',
        'customerAcceptedDate': '',
        'status': 'NOT_DUE'
    }

def next_work_no(rows):
    nums = []
    for row in rows:
        try: nums.append(int(str(row.get('workNo','')).strip()))
        except ValueError: pass
    return str(max(nums, default=0) + 1)

def normalize_milestone_value(field, value):
    if field == 'paymentPercent':
        try:
            number = float(value or 0)
        except (TypeError, ValueError):
            raise Problem('สัดส่วนเงินต้องเป็นตัวเลข')
        if not math.isfinite(number) or number < 0 or number > 100:
            raise Problem('สัดส่วนเงินต้องอยู่ระหว่าง 0–100%')
        return round(number, 4)
    if field == 'status':
        value = str(value or '')
        if value not in MILESTONE_STATUSES:
            raise Problem('สถานะงวดงานไม่ถูกต้อง')
        return value
    text = str(value or '')
    limit = 10000 if field in ['deliverables','scope','contractMilestone'] else 2000
    if len(text) > limit:
        raise Problem('ข้อมูลในช่องยาวเกินไป')
    return text.strip()

def validate_payment_percent(p):
    total = sum(float(m.get('paymentPercent') or 0) for m in p['milestones'])
    if total > 100.0001:
        raise Problem('สัดส่วนงวดเงินรวมกันเกิน 100%')

def payment_summary(p):
    total = round(sum(float(m.get('paymentPercent') or 0) for m in p.get('milestones', [])), 4)
    raw_value = p.get('projectInfo', {}).get('contractValue')
    contract_value = None if raw_value is None else float(raw_value)
    groups = {}
    for m in p.get('milestones', []):
        payment_no = str(m.get('paymentNo') or '').strip()
        percent = float(m.get('paymentPercent') or 0)
        if payment_no and percent:
            groups.setdefault(payment_no, {'percent': 0, 'workNos': []})
            groups[payment_no]['percent'] += percent
            groups[payment_no]['workNos'].append(m.get('workNo'))
    for item in groups.values():
        item['percent'] = round(item['percent'], 4)
        item['amount'] = None if contract_value is None else round(contract_value * item['percent'] / 100, 2)
    return {
        'totalPercent': total,
        'remainingPercent': round(100 - total, 4),
        'complete': abs(total - 100) < 0.0001,
        'contractValue': contract_value,
        'groups': groups
    }

def money_value(value):
    if value is None or value == '':
        return None
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        raise Problem('มูลค่าสัญญาต้องเป็นตัวเลข')
    if not math.isfinite(number) or number < 0 or number > 1_000_000_000_000:
        raise Problem('มูลค่าสัญญาไม่ถูกต้อง')
    return round(number, 2)

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
    delivery=delivery_summary(p)
    blocked=[t for t in active if t['status']=='BLOCKED']
    if blocked:return {'status':'BLOCKED','reason':blocked[0]['waiting']}
    if delivery['blocked']:return {'status':'BLOCKED','reason':'มีงวดส่งมอบติดปัญหา'}
    controls=[r for rows in p.get('controls',{}).values() for r in rows]
    if any(r.get('status')=='BLOCKED' for r in controls):return {'status':'BLOCKED','reason':'มีรายการควบคุมโครงการติดขัด'}
    if delivery['overdue']:return {'status':'OVERDUE','reason':'มีงวดส่งมอบเกินกำหนดตามแผน'}
    if (p['due'] and p['due']<today) or any(t['due'] and t['due']<today for t in active):
        return {'status':'OVERDUE','reason':'มีงานหรือ milestone เกินกำหนด'}
    if any(t['priority']=='HIGH' or t['status']=='WAITING' or (t['due'] and 0 <= (date.fromisoformat(t['due'])-date.today()).days <= 3) for t in active):
        return {'status':'AT RISK','reason':'มีงานสำคัญ ใกล้กำหนด หรือรอการตอบกลับ'}
    alerts=control_summary(p)['alerts']
    if alerts:return {'status':'AT RISK','reason':alerts[0]['title']}
    return {'status':'ON TRACK','reason':'ไม่มีงานเกินกำหนดหรือ blocker ที่บันทึกไว้'}


def validate_back_to_back(p):
    rows=p.get('controls',{}).get('finance',[])
    receipts={r['id']:r for r in rows if r.get('kind')=='CUSTOMER_PAYMENT' and r.get('status')=='DONE'}
    allocated={}
    for r in rows:
        if r.get('kind')=='VENDOR_PAYMENT' and r.get('condition')=='BACK_TO_BACK' and r.get('status')=='DONE':
            receipt=receipts.get(r.get('customerPaymentId'))
            if not receipt:raise Problem('Back-to-back ต้องมีรายการรับเงินลูกค้าที่ยืนยันแล้ว')
            if not receipt.get('completedDate') or receipt['completedDate']>r['completedDate']:raise Problem('วันที่จ่าย Vendor ต้องไม่ก่อนวันที่รับเงินลูกค้า')
            allocated[receipt['id']]=allocated.get(receipt['id'],0)+(r.get('amount') or 0)
            if allocated[receipt['id']]>(receipt.get('amount') or 0):raise Problem('ยอดจ่าย Back-to-back รวมเกินเงินลูกค้าที่อ้างอิง')
