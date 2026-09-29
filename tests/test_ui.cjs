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

test('A rejected cell save restores the persisted value and reports the failure', async () => {
  const {context, nodes, run} = app();
  context.el = {dataset:{mid:'m',field:'paymentPercent'},value:'NaN',isConnected:true};
  run("api=async()=>{throw Error('invalid percentage')}");
  await run('saveTorCell(el)');
  assert.equal(context.el.value, 0);
  assert.equal(nodes['#message'].textContent, 'invalid percentage');
});

test('A failed request does not overwrite newer unsaved typing', async () => {
  const {context, run} = app();
  context.el = {dataset:{mid:'m',field:'paymentPercent'},value:'bad',isConnected:true};
  run("api=async()=>{el.value='30';throw Error('invalid percentage')}");
  await run('saveTorCell(el)');
  assert.equal(context.el.value, '30');
});
