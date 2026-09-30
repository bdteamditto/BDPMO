"""Project lifecycle metadata and derived summaries; no external actions."""
from datetime import date, timedelta
import calendar

PHASE_LABELS = {'Contract':'เริ่มงาน / สัญญา','Procurement':'สัญญา Vendor / จัดซื้อ','Planning':'วางแผนโครงการ','Delivery':'ดำเนินงาน / ส่งมอบ','Acceptance':'ตรวจรับ','Billing':'วางบิล / รับ–จ่ายเงิน','Closure':'ปิดโครงการ'}
CHECKS = {
 'Contract':[('contract_review','ตรวจ TOR และสัญญาลูกค้า',True),('project_open','เปิดเลขโครงการและแต่งตั้งผู้รับผิดชอบ',True),('guarantee','ตรวจ Bank Guarantee และอากรแสตมป์',True)],
 'Procurement':[('cost_approval','อนุมัติ Cost Sheet / งบประมาณ',True),('purchase','ตรวจ PR / PO และสัญญา Vendor หรือบันทึกว่าไม่เกี่ยวข้อง',True)],
 'Planning':[('kickoff','ประชุมเริ่มงานและยืนยัน Project Plan',True),('risk_assessment','ประเมินความเสี่ยงและผูก TOR กับแผน',True)],
 'Delivery':[('vendor_progress','รวบรวมความก้าวหน้า Vendor สิ้นเดือน',False),('accounting_report','ส่งรายงานความก้าวหน้าให้บัญชีภายในวันที่ 5',False)],
 'Acceptance':[('acceptance_evidence','รวบรวมหลักฐานตรวจรับครบทุกงวด',True)],
 'Billing':[('invoice','ตรวจเอกสาร Invoice / RC',True),('payment_reconcile','กระทบยอดรับจากลูกค้าและจ่าย Vendor',True)],
 'Closure':[('final_acceptance','ยืนยัน Final Acceptance',True),('asset_handover','ส่งมอบทรัพย์สิน เอกสาร และผู้ดูแลต่อ',True),('financial_close','ยืนยันปิดยอดการเงินและภาระคงค้าง',True),('lessons','สรุปผลโครงการและบทเรียน',True),('guarantee_release','ติดตามคืนหลักประกัน / เงื่อนไขรับประกัน',False)]
}
# [key, label, input type, optional enum choices]
COMMON = [['title','ชื่อรายการ','text'],['owner','ผู้รับผิดชอบ','member'],['due','กำหนดเสร็จ','date'],['status','สถานะ','status'],['evidence','หลักฐาน / เลขเอกสาร / ลิงก์','textarea'],['notes','รายละเอียด / ขั้นตอนถัดไป','textarea']]
MODULES = {
 'opening':{'label':'เริ่มงาน / สัญญา','phase':'Contract','fields':[
 ['kind','ประเภท','select',['CONTRACT_REVIEW','PROJECT_OPENING','BANK_GUARANTEE','STAMP_DUTY','KICKOFF']],['reference','เลขที่อ้างอิง','text'],['completedDate','วันที่ดำเนินการแล้ว','date'],['expiryDate','วันหมดอายุ / คืนหลักประกัน','date'],['amount','จำนวนเงิน','money']]},
 'cost':{'label':'ต้นทุน / งบประมาณ','phase':'Procurement','fields':[
 ['kind','ประเภท','select',['COST_SHEET','APPROVED_BUDGET','ADVANCE_CASH','FORECAST']],['amount','จำนวนเงิน','money'],['approvalRef','เลขอนุมัติ / ผู้อนุมัติ','text']]},
 'procurement':{'label':'จัดซื้อ / Vendor','phase':'Procurement','fields':[
 ['kind','ประเภท','select',['PR','PO','VENDOR_CONTRACT','VENDOR_PROGRESS','ACCOUNTING_REPORT']],['vendor','Vendor','text'],['reference','เลข PR / PO / สัญญา','text'],['lsfNo','เลขของาน LSF','text'],['poDate','วันที่ PO','date'],['startDate','เริ่มสัญญา Vendor','date'],['endDate','สิ้นสุดสัญญา Vendor','date'],['period','รอบรายงาน','month'],['completedDate','วันที่ได้รับ / ส่งรายงานแล้ว','date'],['amount','จำนวนเงิน','money']]},
 'finance':{'label':'การเงิน / รับ–จ่าย','phase':'Billing','fields':[
 ['kind','ประเภท','select',['INVOICE','RC','CUSTOMER_PAYMENT','VENDOR_PAYMENT']],['reference','เลข Invoice / RC / ใบสำคัญ','text'],['amount','จำนวนเงิน','money'],['completedDate','วันที่รับ / จ่ายแล้ว','date'],['condition','เงื่อนไข','select',['STANDARD','BACK_TO_BACK']],['customerPaymentId','รายการรับเงินลูกค้าที่รองรับ (Back-to-back)','customerPayment'],['milestoneId','งวดงานที่เกี่ยวข้อง','milestone']]},
 'risk':{'label':'ความเสี่ยง','phase':'Planning','fields':[
 ['severity','ระดับความเสี่ยง','select',['LOW','MEDIUM','HIGH','CRITICAL']],['impact','ผลกระทบ','textarea'],['mitigation','แผนลดความเสี่ยง','textarea'],['waiting','ติดอะไร / รอใคร','textarea']]},
 'documents':{'label':'เอกสาร / การตัดสินใจ','phase':'Planning','fields':[
 ['kind','ประเภท','select',['DOCUMENT','DECISION']],['reference','เลขเอกสาร / เวอร์ชัน','text'],['relatedId','ผูกกับงาน / งวด / รายการควบคุม','related'],['reason','เหตุผล / ผลกระทบการตัดสินใจ','textarea']]},
 'closure':{'label':'ปิดโครงการ','phase':'Closure','fields':[
 ['kind','ประเภท','select',['FINAL_ACCEPTANCE','ASSET','HANDOVER','LESSONS','WARRANTY','GUARANTEE_RELEASE']],['recipient','ผู้รับมอบ / ผู้ดูแลต่อ','text'],['completedDate','วันที่ดำเนินการแล้ว','date'],['warrantyEnd','สิ้นสุดการรับประกัน','date']]}
}
for module in MODULES.values():
 module['fields'] = COMMON + module['fields']

DONE_DELIVERY = {'DELIVERED','WAITING_REPLY','WAITING_ACCEPTANCE','ACCEPTED'}

def parse_day(value):
    """Parse existing ISO and Thai contract dates for comparisons, retaining original text."""
    text = str(value or '').strip()
    months = ['มกราคม','กุมภาพันธ์','มีนาคม','เมษายน','พฤษภาคม','มิถุนายน','กรกฎาคม','สิงหาคม','กันยายน','ตุลาคม','พฤศจิกายน','ธันวาคม']
    try:
        if '/' in text:
            day, month, year = map(int, text.split('/'))
        elif any(m in text for m in months):
            parts=text.split(); day=int(parts[0]); month=months.index(parts[1])+1; year=int(parts[2])
        else:
            return date.fromisoformat(text)
        return date(year-543 if year>2400 else year,month,day)
    except (ValueError, TypeError, IndexError):
        return None

def delivery_summary(p, today=None):
    today = today or date.today()
    rows=p.get('milestones',[])
    done=[r for r in rows if r.get('status') in DONE_DELIVERY]
    pending=[r for r in rows if r not in done]
    current=next((r for r in pending if r.get('status')=='IN_PROGRESS'),pending[0] if pending else None)
    overdue=[r for r in pending if (parse_day(r.get('planDue') or r.get('torDue')) or date.max)<today]
    return {'total':len(rows),'done':len(done),'accepted':sum(r.get('status')=='ACCEPTED' for r in rows),
            'percent':round(len(done)*100/len(rows),1) if rows else 0,
            'current':current,'overdue':[r['id'] for r in overdue],
            'blocked':[r['id'] for r in pending if r.get('status')=='BLOCKED']}

def lifecycle_checks(p):
    stored=p.get('checks',{})
    return {phase:[{'id':key,'title':title,'required':required,**stored.get(key,{})} for key,title,required in items] for phase,items in CHECKS.items()}

def closure_blockers(p):
    blockers=[]
    if p.get('phase')!='Closure':blockers.append('เปลี่ยน Phase เป็นปิดโครงการก่อน')
    if any(t['status']!='DONE' for t in p.get('tasks',[])):blockers.append('ยังมีงานย่อยไม่เสร็จ')
    if any(m.get('status')!='ACCEPTED' for m in p.get('milestones',[])):blockers.append('ยังมีงวดงานที่ไม่ยืนยันตรวจรับ')
    if any(r.get('status')!='DONE' for r in p.get('controls',{}).get('risk',[])):blockers.append('ยังมีความเสี่ยงที่ไม่ปิด')
    if any(r.get('status')!='DONE' for r in p.get('controls',{}).get('finance',[])):blockers.append('ยังมีรายการการเงินไม่เสร็จ')
    checks=lifecycle_checks(p)
    for phase in ['Acceptance','Billing','Closure']:
        for item in checks[phase]:
            if item['required'] and (item.get('status')!='DONE' or not item.get('evidence')):
                blockers.append(item['title'])
    return blockers

def control_summary(p, today=None):
    today=today or date.today()
    records=p.get('controls',{})
    alerts=[]
    def alert(module,title,record=None):alerts.append({'module':module,'title':title,'id':(record or {}).get('id','')})
    end=parse_day(p.get('projectInfo',{}).get('deliveryDueDate'))
    signed=parse_day(p.get('projectInfo',{}).get('signedDate'))
    for r in records.get('procurement',[]):
        start=parse_day(r.get('startDate')); po=parse_day(r.get('poDate')); vend_end=parse_day(r.get('endDate'))
        if start and po and start<po:alert('procurement','สัญญา Vendor เริ่มก่อนวันที่ PO',r)
        if end and vend_end and (end-vend_end).days<15:alert('procurement','สัญญา Vendor มีระยะเผื่อก่อนจบสัญญาลูกค้าน้อยกว่า 15 วัน',r)
        period=r.get('period')
        if period and r.get('kind') in ['VENDOR_PROGRESS','ACCOUNTING_REPORT']:
            y,m=map(int,period.split('-')); last=date(y,m,calendar.monthrange(y,m)[1])
            due=last if r['kind']=='VENDOR_PROGRESS' else (last+timedelta(days=5) if last<=date(9999,12,26) else date.max)
            completed=parse_day(r.get('completedDate'))
            if (completed and completed>due) or (not completed and due<today):alert('procurement','รายงานรอบ '+period+' เลยกำหนด '+due.isoformat(),r)
    if signed:
        stamps=[r for r in records.get('opening',[]) if r.get('kind')=='STAMP_DUTY']
        if (today-signed).days>15 and not any(r.get('status')=='DONE' for r in stamps):
            alert('opening','ยังไม่มีหลักฐานอากรแสตมป์ที่ยืนยันเสร็จ ภายในกรอบ 15 วันตามกระบวนการ')
        next_month=signed.month%12+1; year=min(9999,signed.year+(signed.month==12))
        risk_due=date(year,next_month,min(signed.day,calendar.monthrange(year,next_month)[1]))
        if risk_due<today and p.get('checks',{}).get('risk_assessment',{}).get('status')!='DONE':alert('risk','ยังไม่ยืนยันการประเมินความเสี่ยงภายใน 1 เดือนตามกระบวนการ')
    for module, rows in records.items():
        for r in rows:
            if r.get('status')=='DONE':continue
            if module=='risk' and r.get('severity') in ['HIGH','CRITICAL']:alert(module,'ความเสี่ยงสูง: '+r['title'],r)
            if r.get('status')=='BLOCKED':alert(module,'ติดขัด: '+r['title'],r)
            elif (parse_day(r.get('due')) or date.max)<today:alert(module,'เกินกำหนด: '+r['title'],r)
    finance=records.get('finance',[])
    def total(kind):
        return sum(r.get('amount') or 0 for r in finance if r.get('kind')==kind and r.get('status')=='DONE')
    return {'alerts':alerts,'openRisks':sum(r.get('status')!='DONE' for r in records.get('risk',[])),
            'received':total('CUSTOMER_PAYMENT'),'paid':total('VENDOR_PAYMENT'),
            'net':total('CUSTOMER_PAYMENT')-total('VENDOR_PAYMENT'),
            'financeRecorded':bool(finance)}
