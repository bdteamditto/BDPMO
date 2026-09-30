const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function app() {
  const nodes = { '#message': {}, '#paymentSummary': {}, '#torAudit': {} };
  const context = vm.createContext({
    Intl, setTimeout() {},
    document: {
      querySelector: s => nodes[s],
      createElement: () => ({ innerHTML: '', querySelector() { return { innerHTML: this.innerHTML }; } })
    }
  });
  const source = fs.readFileSync('hosted/public/app.js', 'utf8').replace(/refresh\(\);\s*$/, '');
  vm.runInContext(source, context);
  vm.runInContext(`
    state={user:'demo',csrf:'test',milestoneStatuses:['NOT_DUE'],projects:[{
      id:'p',role:'OWNER',projectInfo:{contractValue:1000},
      paymentSummary:{totalPercent:0,remainingPercent:100,groups:{}},
      milestones:[{id:'m',workNo:'1',paymentPercent:0,status:'NOT_DUE'}],events:[]
    }]}; selected='p'; view='tor';
  `, context);
  return {context, nodes, run: code => vm.runInContext(code, context)};
}

test('Read mode has no editable cells or row mutation controls; viewer stays read-only', () => {
  const {run} = app();
  let html = run('torView(pnow())');
  assert.doesNotMatch(html, /class='cell-input'|id="addMilestone"|data-delete-milestone/);
  html = run('torEdit=true; torView(pnow())');
  assert.match(html, /class='cell-input'/);
  assert.match(html, /data-delete-milestone/);
  html = run("pnow().role='VIEWER'; torView(pnow())");
  assert.doesNotMatch(html, /class='cell-input'|id="addMilestone"|data-delete-milestone/);
});

test('A successful cell save updates payment and audit panels without replacing the sheet', async () => {
  const {context, nodes, run} = app();
  assert.match(run('torView(pnow())'),/id='paymentSummary'/);
  assert.match(run('torView(pnow())'),/id='torAudit'/);
  context.el = {dataset:{mid:'m',field:'paymentPercent'},value:'25',isConnected:true};
  run(`api=async(path,data)=>{
    if(path==='action'){
      pnow().milestones[0].paymentPercent=25;
      pnow().paymentSummary={totalPercent:25,remainingPercent:75,groups:{'1':{percent:25,amount:250}}};
      pnow().events=[{actor:'demo',at:'2026-09-29T00:00:00Z',action:'milestone_cell',detail:JSON.stringify({field:'paymentPercent',before:0,after:25})}];
      return {ok:true};
    } return state;
  }`);
  await run('saveTorCell(el)');
  assert.match(nodes['#paymentSummary'].innerHTML, /รวม 25%/);
  assert.match(nodes['#torAudit'].innerHTML, /paymentPercent: 0 → 25/);
  assert.equal(nodes['#message'].textContent, 'บันทึกแล้ว');
});

test('A rejected cell save retains the draft and reports the failure', async () => {
  const {context, nodes, run} = app();
  context.el = {dataset:{mid:'m',field:'paymentPercent'},value:'NaN',isConnected:true};
  run("api=async()=>{throw Error('invalid percentage')}");
  await run('saveTorCell(el)');
  assert.equal(context.el.value, 'NaN');
  assert.equal(run("cellDrafts.get(draftKey('p','m','paymentPercent'))"),'NaN');
  assert.match(nodes['#message'].textContent, /invalid percentage/);
});

test('A failed request does not overwrite newer unsaved typing', async () => {
  const {context, run} = app();
  context.el = {dataset:{mid:'m',field:'paymentPercent'},value:'bad',isConnected:true};
  run("api=async()=>{el.value='30';throw Error('invalid percentage')}");
  await run('saveTorCell(el)');
  assert.equal(context.el.value, '30');
});

function lifecycleApp() {
  const instance=app();
  const {execFileSync}=require('node:child_process');
  const fixture=JSON.parse(execFileSync('python3',['-c',`
import json
from core import Workspace
w=Workspace(':memory:')
w.db.execute("INSERT INTO users VALUES ('demo','hash')")
w.act('demo','create_project',{'name':'Lifecycle review'})
p=w.state('demo')['projects'][0]['id']
for status in ['DELIVERED','DELIVERED','DELIVERED','IN_PROGRESS','NOT_DUE']:
 w.act('demo','milestone_add',{'project':p})
 m=w.state('demo')['projects'][0]['milestones'][-1]['id']
 w.act('demo','milestone_cell',{'project':p,'id':m,'field':'status','value':status})
w.act('demo','project',{'project':p,'name':'Lifecycle review','phase':'Delivery'})
print(json.dumps(w.state('demo')))
`],{encoding:'utf8'}));
  instance.context.fixture=fixture;
  instance.run('state=fixture;selected=state.projects[0].id;state.projects[0].deliverySummary.next=state.projects[0].milestones[4]');
  return instance;
}

test('My Projects and Overview stay separate, concise, and derive Current/Next from TOR',()=>{
 const {run}=lifecycleApp();
 const home=run('homeDashboard()');
 assert.match(home,/Current[\s\S]*งวดงานที่ 4/);
 assert.match(home,/Next[\s\S]*งวดงานที่ 5/);
 assert.match(home,/ตามแผน|มีความเสี่ยง|ล่าช้า/);
 const overview=run('homeView(pnow())');
 assert.match(overview,/3 \/ 5 งวด · 60%/);
 assert.match(overview,/งวดงานที่ 4/);
 assert.match(overview,/งวดงานที่ 5/);
 assert.match(overview,/ความเคลื่อนไหวล่าสุด/);
 assert.doesNotMatch(overview,/ยังไม่มีข้อมูลรับ–จ่ายเงินจริง|เส้นทางส่งมอบและตรวจรับ|undefined|NaN/);
});

test('Team page renders structured handover fields and does not hide membership metadata',()=>{
 const {run}=lifecycleApp();
 const html=run('teamView(pnow())');
 assert.match(html,/เพิ่มสมาชิก/);
 assert.match(html,/เพิ่มโดย/);
 assert.match(html,/ให้สิทธิ์โดย/);
 assert.match(html,/สถานะปัจจุบัน/);
 assert.match(html,/ขั้นตอนถัดไป/);
 assert.match(html,/ลิงก์ \/ เอกสารสำคัญ/);
});

test('Admin page exposes user lifecycle controls and cross-project membership',()=>{
 const {run}=lifecycleApp();
 run("state.isAdmin=true;state.users=[{user:'admin',createdBy:'admin',createdAt:'2026-09-30',disabled:false}];state.adminProjects=[{id:'p',name:'Lifecycle review',members:[]}];state.adminEvents=[]");
 const html=run('adminView()');
 assert.match(html,/สร้างบัญชี/);
 assert.match(html,/จัดการ \/ Reset/);
 assert.match(html,/สร้างโดย admin/);
 assert.match(html,/data-admin-member/);
 assert.match(html,/System Admin Audit Log/);
});

test('Every lifecycle module and checklist form renders using real backend metadata',()=>{
 const {run}=lifecycleApp();
 run('modal=(title,html,submit)=>({title,html,editable:!!submit})');
 for(const module of run('Object.keys(state.controlModules)')){
  const html=run(`controlView(pnow(),${JSON.stringify(module)})`);
  assert.doesNotMatch(html,/undefined|NaN/);
  const form=run(`controlForm(${JSON.stringify(module)});`);
  // Forms use the shared modal; capture the output without a DOM library.
  run('modal=(title,html,submit)=>{captured={title,html,editable:!!submit}}');
  run(`controlForm(${JSON.stringify(module)})`);
  assert.match(run('captured.html'),/name="title"/);
  assert.doesNotMatch(run('captured.html'),/undefined|NaN/);
 }
 run("checklistForm('final_acceptance')");
 assert.match(run('captured.html'),/name="evidence"/);
 assert.match(run('lifecycleView(pnow())'),/ปิดโครงการ/);
 assert.match(run('planningView(pnow())'),/Timeline งวดส่งมอบ/);
 assert.match(run('acceptanceView(pnow())'),/CUSTOMER ACCEPTANCE/);
});

test('Date edits retain ISO format after save and detail audit is not reported as deletion',async()=>{
 const {context,run}=app();
 context.el={dataset:{mid:'m',field:'planDue'},type:'date',value:'2026-10-09',isConnected:true};
 run("api=async(path)=>{pnow().milestones[0].planDue='9/10/2569';return state}");
 await run('saveTorCell(el)');
 assert.equal(context.el.value,'2026-10-09');
 assert.match(run("torEvent({action:'milestone_details',detail:'{}'})"),/แก้สถานะ/);
});


test('Validation failures stay visible inside the open dialog and allow retry',async()=>{
 const {context,nodes,run}=app();
 Object.assign(nodes,{'#dialog':{open:false,showModal(){this.open=true},close(){this.open=false}},'#modalForm':{},'#cancel':{},'#save':{},'#modalError':{}});
 context.FormData=class { *[Symbol.iterator](){} };
 run("modal('Evidence','',async()=>{throw Error('Evidence required')})");
 await nodes['#modalForm'].onsubmit({preventDefault(){},target:{}});
 assert.equal(nodes['#dialog'].open,true);
 assert.equal(nodes['#modalError'].textContent,'Evidence required');
 assert.equal(nodes['#save'].disabled,false);
});
