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
  const source = fs.readFileSync('static/app.js', 'utf8').replace(/refresh\(\);\s*$/, '');
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
  instance.run('state=fixture;selected=state.projects[0].id');
  return instance;
}

test('Overview renders backend delivery progress, current milestone, and unknown finance honestly',()=>{
 const {run}=lifecycleApp();
 const html=run('homeView(pnow())');
 assert.match(html,/3 \/ 5 งวด · 60%/);
 assert.match(html,/งวดที่ 4/);
 assert.match(html,/ยังไม่มีข้อมูลรับ–จ่ายเงินจริง/);
 assert.match(html,/0 \/ 5 งวด/);
 assert.doesNotMatch(html,/undefined|NaN/);
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
});

test('Date edits retain ISO format after save and detail audit is not reported as deletion',async()=>{
 const {context,run}=app();
 context.el={dataset:{mid:'m',field:'planDue'},type:'date',value:'2026-10-09',isConnected:true};
 run("api=async(path)=>{pnow().milestones[0].planDue='9/10/2569';return state}");
 await run('saveTorCell(el)');
 assert.equal(context.el.value,'2026-10-09');
 assert.match(run("torEvent({action:'milestone_details',detail:'{}'})"),/แก้สถานะ/);
});
