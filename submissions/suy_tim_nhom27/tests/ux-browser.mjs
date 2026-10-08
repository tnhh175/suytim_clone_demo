// Opt-in browser regression: node tests/ux-browser.mjs. Requires playwright-core
// (HF_QA_PLAYWRIGHT_MODULE may name its absolute path) and an isolated QA server.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.HF_QA_PLAYWRIGHT_MODULE || 'playwright-core');
const base = process.env.HF_QA_BASE_URL || 'http://127.0.0.1:8001';
assert(new URL(base).hostname === '127.0.0.1', 'Use an isolated local QA server');
const artifacts = process.env.HF_QA_ARTIFACT_DIR || path.resolve('.context-shears/browser');
await mkdir(artifacts, {recursive:true});
const browser = await chromium.launch({headless:true, executablePath:process.env.HF_QA_CHROME || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'});
let passed=0; let failed=0;
const errors=[];
const sleep = ms => new Promise(resolve=>setTimeout(resolve,ms));
async function check(name, task) { if(process.env.HF_QA_TEST_FILTER && !name.includes(process.env.HF_QA_TEST_FILTER)) return; try {await task(); passed++; console.log('PASS '+name);} catch(e) { failed++; console.error('FAIL '+name+' '+e.message); } }
async function session(account='doctor_demo', width=1440) {
 const context=await browser.newContext({viewport:{width,height:width<800?844:900}});
 const page=await context.newPage(); page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base); await page.locator('#loginRole').fill(account); await page.locator('#loginPassword').fill('DemoOnly!2026'); await page.locator('#loginButton').click();
 await page.locator('#appView').waitFor({state:'visible'}); await idle(page); return {context,page};
}
async function idle(page) { await page.waitForFunction(()=>document.querySelector('#viewContent').getAttribute('aria-busy')==='false'); }
async function navigate(page, view) { if(await page.locator('#navToggle').isVisible()) { if(await page.locator('#navToggle').getAttribute('aria-expanded')==='false') await page.locator('#navToggle').click(); } await page.locator('[data-view="'+view+'"]').click(); await idle(page); }
async function noOverflow(page) { assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'document overflows'); }
async function openEncounter(page) {await navigate(page,'cases'); await page.locator('[data-select-case="10000000-0000-4000-8000-000000000001"][data-case-target="encounter"]').click(); await idle(page); await page.locator('[data-select-encounter="20000000-0000-4000-8000-000000000001"]').click(); await idle(page); await page.locator('#observationForm').waitFor({state:'attached'});}
async function api(page, method, route, body) {
 const result=await page.evaluate(async({method,route,body})=>{const response=await fetch(route,{method,headers:{Authorization:'Bearer '+sessionStorage.getItem('hf-demo.access-token'),'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});return {status:response.status,data:await response.json()};},{method,route,body});
 assert(result.status>=200&&result.status<300,'QA API '+method+' '+route+' returned '+result.status);return result.data;
}
async function observationValues(page) {return page.locator('#observationForm').evaluate(form=>Object.fromEntries(new FormData(form)));}
async function assertHydratedObservation(page, observation) {
 const expectedDate=await page.evaluate(value=>{const date=new Date(value);return new Date(date.getTime()-date.getTimezoneOffset()*60000).toISOString().slice(0,16);},observation.observed_at);
 const values=await observationValues(page);
 assert.equal(values.code,observation.code);assert.equal(values.status,observation.status);assert.equal(values.observed_at,expectedDate);assert.equal(values.source,observation.source);
 if(observation.status==='present') {assert.equal(values.value,String(observation.value));if(observation.unit)assert.equal(values.unit,observation.unit);}
 else {assert.equal(values.value,undefined);assert.equal(values.unit,undefined);}
}
async function fillObservation(page, values) {
 await page.locator('#observationSection').evaluate(e=>e.open=true);await page.locator('#obsCode').selectOption(values.code);await page.locator('#obsStatus').selectOption(values.status);
 if(values.status==='present'){await page.locator('#obsValue').fill(values.value);if(values.unit)await page.locator('#obsUnit').selectOption(values.unit);}
 await page.locator('#obsObservedAt').fill(values.observed_at);await page.locator('#obsSource').selectOption(values.source);
}
async function createValues(page, code) {await page.locator('#createCaseSection').evaluate(e=>e.open=true);await page.locator('#newAge').fill('71');await page.locator('#newSex').selectOption('unknown');await page.locator('#newSyntheticCode').fill(code);}

try {
 await check('five roles read real API and correct patient final-state controls',async()=>{
  const views={doctor_demo:['cases','encounter','evaluation','history'],nurse_demo:['cases','encounter'],pharmacist_demo:['medsafety'],admin_demo:['rules','audit'],patient_demo:['appointments','measurements','prescriptions','reminders']};
  for(const [account, list] of Object.entries(views)) {
   const {context,page}=await session(account);
   for(const view of list) {await navigate(page,view);assert(!(await page.locator('#globalMessage.error').count()),account+' '+view+' error');await noOverflow(page);}
   if(account==='patient_demo') {const pending=await page.evaluate(async()=>{const t=sessionStorage.getItem('hf-demo.access-token');return (await (await fetch('/api/v1/patient/reminders',{headers:{Authorization:'Bearer '+t}})).json()).filter(r=>r.status==='pending').length;});assert.equal(await page.locator('[data-reminder-id]').count(),pending*2); await page.screenshot({path:path.join(artifacts,'patient-desktop.png'),fullPage:true});}
   if(account==='pharmacist_demo'){await page.locator('#pharmacyEncounterId').fill('20000000-0000-4000-8000-000000000001');await page.locator('#pharmacyLoadForm button').click();await idle(page);assert.equal(await page.locator('#evalRevision').inputValue(),'');assert((await page.locator('#viewContent').innerText()).includes('không tự đoán'));}
   await context.close();
  }
 });
 await check('one action case to encounter, local case filter, nurse allowlist',async()=>{
  for(const account of ['doctor_demo','nurse_demo']) {
   const {context,page}=await session(account);await navigate(page,'cases');
   assert.equal(await page.locator('#createCaseSection[open]').count(),0);
   await page.locator('#caseFilter').fill('NO-MATCH');assert.equal(await page.locator('[data-case-search]:visible').count(),0);await page.locator('#caseFilter').fill('');
   await page.locator('[data-select-case="10000000-0000-4000-8000-000000000001"][data-case-target="encounter"]').click();await idle(page);assert((await page.locator('#viewTitle').innerText()).includes('Lần khám'));
   await page.locator('[data-select-encounter="20000000-0000-4000-8000-000000000001"]').click();await idle(page);
   if(account==='nurse_demo'){const codes=await page.locator('#obsCode option').evaluateAll(list=>list.map(o=>o.value).filter(Boolean));assert.deepEqual(codes.sort(),['systolic_bp','diastolic_bp','heart_rate','weight_kg','spo2','temperature_c','dyspnea','edema','fatigue'].sort());assert.equal(await page.locator('#medicationForm').count(),0);}
   else{const button=page.locator('[data-edit-observation]').first();const id=await button.getAttribute('data-edit-observation');const records=await api(page,'GET','/api/v1/encounters/20000000-0000-4000-8000-000000000001/observations');await button.click();await idle(page);await assertHydratedObservation(page,records.find(record=>record.id===id));assert.equal(await page.locator('#observationSection').getAttribute('open'),'');assert.equal(await page.evaluate(()=>document.activeElement.id),'obsCode');await page.screenshot({path:path.join(artifacts,'doctor-encounter-desktop.png'),fullPage:true});}
   await context.close();
  }
 });
 await check('responsive 768/390/320 all roles and keyboard drawer',async()=>{
  for(const width of [768,390,320])for(const account of ['doctor_demo','nurse_demo','pharmacist_demo','admin_demo','patient_demo']) {
   const {context,page}=await session(account,width);
   assert(await page.locator('#sidebar').evaluate(e=>e.inert));await page.locator('#navToggle').click();await page.keyboard.press('Escape');assert.equal(await page.evaluate(()=>document.activeElement.id),'navToggle');assert(await page.locator('#sidebar').evaluate(e=>e.inert));
   const views=await page.locator('[data-view]').evaluateAll(list=>list.map(e=>e.dataset.view));for(const view of views){await navigate(page,view);await noOverflow(page);}
   if(width===390&&account==='patient_demo'){await navigate(page,'measurements');await page.screenshot({path:path.join(artifacts,'patient-measurements-mobile.png'),fullPage:true});}
   if(width===390&&account==='doctor_demo'){await openEncounter(page);await page.locator('#observationSection').evaluate(e=>e.open=true);await noOverflow(page);await page.screenshot({path:path.join(artifacts,'doctor-encounter-mobile.png'),fullPage:true});}
   await context.close();
  }
 });
 await check('delayed view response cannot overwrite new navigation',async()=>{
  const {context,page}=await session();let release;const gate=new Promise(r=>release=r);
  await page.route('**/api/v1/cases',async route=>{await gate;await route.continue();});
  await page.locator('[data-view="cases"]').click();await page.locator('[data-view="evaluation"]').click();await idle(page);release();await sleep(300);
  assert.equal(await page.locator('#evaluationForm').count(),1);assert.equal(await page.locator('#createCaseForm').count(),0);await context.close();
 });
 await check('logout ignores late responses including old 401',async()=>{
  const {context,page}=await session();let release;const gate=new Promise(r=>release=r);
  await page.route('**/api/v1/cases',async route=>{await gate;await route.fulfill({status:401,json:{detail:'old expired request'}});});
  await page.locator('[data-view="cases"]').click();await page.locator('#logoutButton').click();await page.locator('#loginView').waitFor({state:'visible'});release();await sleep(200);
  await page.locator('#loginRole').fill('patient_demo');await page.locator('#loginPassword').fill('DemoOnly!2026');await page.locator('#loginButton').click();await page.locator('#appView').waitFor({state:'visible'});await idle(page);assert.equal(await page.locator('#roleLabel').innerText(),'Bệnh nhân');await context.close();
 });
 await check('403/409/422/network preserve inputs, pending blocks duplicate submissions',async()=>{
  const {context,page}=await session();await navigate(page,'cases');await createValues(page,'SYN-QA-FAIL');
  for(const status of [403,409,422,0]) {
   let count=0;
   const routeHandler=async route=>{if(route.request().method()!=='POST')return route.continue();count++;await sleep(200);if(!status)return route.abort();return route.fulfill({status,json:{detail:'QA simulated failure '+status}});};
   await page.route('**/api/v1/cases',routeHandler);
   await page.locator('#createCaseForm button[type=submit]').click();await page.locator('#newAge').press('Enter');assert(await page.locator('#createCaseForm button[type=submit]').isDisabled());
   await page.waitForFunction(()=>document.querySelector('#createCaseError').textContent.length>0);
   assert.equal(await page.locator('#newSyntheticCode').inputValue(),'SYN-QA-FAIL');assert.equal(count,1);assert(await page.locator('#createCaseForm button[type=submit]').isEnabled());await page.unroute('**/api/v1/cases',routeHandler);
  }
  await context.close();
 });
 await check('successful real POST + failed refresh only retries GET',async()=>{
  const {context,page}=await session();await navigate(page,'cases');const code='SYN-QA-'+Date.now();await createValues(page,code);
  let posted=false;let count=0;let failedOnce=false;
  const handler=async route=>{if(route.request().method()==='POST'){count++;const response=await route.fetch();posted=true;return route.fulfill({response});}if(posted&&!failedOnce){failedOnce=true;return route.abort();}return route.continue();};
  await page.route('**/api/v1/cases',handler);await page.locator('#createCaseForm button[type=submit]').click();await page.waitForFunction(()=>document.querySelector('#globalMessage').textContent.includes('Đã lưu thành công, nhưng'));
  assert(await page.locator('#createCaseForm button[type=submit]').isDisabled());assert.equal(await page.locator('#newSyntheticCode').inputValue(),code);
  await page.locator('#retryView').click();await idle(page);assert.equal(count,1);assert((await page.locator('#viewContent').innerText()).includes(code));await context.close();
 });
 await check('real observation save with failed GET preserves note draft and retries reads',async()=>{
  const {context,page}=await session();await openEncounter(page);await page.locator('#noteContent').fill('QA unrelated draft');await page.locator('#observationSection').evaluate(e=>e.open=true);
  await page.locator('#obsCode').selectOption('heart_rate');await page.locator('#obsStatus').selectOption('present');await page.locator('#obsValue').fill('75');await page.locator('#obsUnit').selectOption('bpm');await page.locator('#obsObservedAt').fill('2026-10-08T15:00');await page.locator('#obsSource').selectOption('manual_synthetic');
  let posted=false,count=0,failedOnce=false;const handler=async route=>{if(route.request().method()==='POST'){count++;const response=await route.fetch();posted=true;return route.fulfill({response});}if(posted&&!failedOnce){failedOnce=true;return route.abort();}return route.continue();};
  await page.route('**/api/v1/encounters/*/observations*',handler);await page.locator('#observationForm button[type=submit]').click();await page.waitForFunction(()=>document.querySelector('#observationError').textContent.includes('Đã lưu thành công'));
  assert.equal(await page.locator('#noteContent').inputValue(),'QA unrelated draft');assert(await page.locator('#observationForm button[type=submit]').isDisabled());await page.getByRole('button',{name:'Tải lại dữ liệu đã lưu',exact:true}).click();await idle(page);assert.equal(count,1);assert.equal(await page.locator('#noteContent').inputValue(),'QA unrelated draft');await context.close();
 });
 await check('observation create/edit contexts hydrate, cancel, safely update and isolate encounters',async()=>{
  const {context,page}=await session();
  const profile=await api(page,'POST','/api/v1/cases',{synthetic_code:'SYN-QA-EDIT-'+Date.now(),age:71,sex:'unknown'});
  const one=await api(page,'POST','/api/v1/cases/'+profile.id+'/encounters?expected_revision='+profile.revision,{occurred_at:'2026-10-08T08:00:00Z'});
  let fresh=await api(page,'GET','/api/v1/cases/'+profile.id);
  const two=await api(page,'POST','/api/v1/cases/'+profile.id+'/encounters?expected_revision='+fresh.revision,{occurred_at:'2026-10-08T09:00:00Z'});
  fresh=await api(page,'GET','/api/v1/cases/'+profile.id);
  const present=await api(page,'POST','/api/v1/encounters/'+one.id+'/observations?expected_revision='+fresh.revision,{code:'heart_rate',value:75,unit:'bpm',status:'present',observed_at:'2026-10-08T08:10:00Z',source:'manual_synthetic'});
  fresh=await api(page,'GET','/api/v1/cases/'+profile.id);
  const unknown=await api(page,'POST','/api/v1/encounters/'+one.id+'/observations?expected_revision='+fresh.revision,{code:'potassium',value:null,unit:null,status:'unknown',observed_at:'2026-10-08T08:11:00Z',source:'mock_lis'});
  await navigate(page,'cases');await page.locator('[data-select-case="'+profile.id+'"][data-case-target="encounter"]').click();await idle(page);await page.locator('[data-select-encounter="'+one.id+'"]').click();await idle(page);
  const draftA={code:'potassium',status:'present',value:'4.4',unit:'mmol/L',observed_at:'2026-10-08T15:02',source:'mock_lis'};await fillObservation(page,draftA);
  const encounterFailure=async route=>route.abort();await page.route('**/api/v1/encounters/'+one.id,encounterFailure);
  await page.locator('[data-edit-observation="'+present.id+'"]').click();await idle(page);assert.equal(await page.locator('#retryView').count(),1);assert.deepEqual(await observationValues(page),draftA);assert((await page.locator('#observationForm').getAttribute('data-form-context')).endsWith(':create'));
  let attemptedMethod;const blockedWrite=async route=>{if(route.request().method()==='GET')return route.continue();attemptedMethod=route.request().method();return route.fulfill({status:422,json:{detail:'QA simulated validation failure'}});};await page.route('**/observations**',blockedWrite);await page.locator('#observationForm button[type=submit]').click();await idle(page);assert.equal(attemptedMethod,'POST');await page.unroute('**/observations**',blockedWrite);await page.unroute('**/api/v1/encounters/'+one.id,encounterFailure);
  await page.locator('#retryView').click();await idle(page);await assertHydratedObservation(page,present);await page.locator('#obsValue').fill('76');await page.locator('#cancelObservationEdit').click();await idle(page);assert.deepEqual(await observationValues(page),draftA);
  let writes=0;page.on('request',request=>{if(request.method()==='PUT'&&request.url().includes('/observations/'))writes++;});
  await page.locator('[data-edit-observation="'+present.id+'"]').click();await idle(page);await assertHydratedObservation(page,present);await page.locator('#obsValue').fill('76');await page.locator('#observationForm button[type=submit]').click();await idle(page);assert.equal(writes,1);assert.deepEqual(await observationValues(page),draftA);
  const authoritative=await api(page,'GET','/api/v1/encounters/'+one.id+'/observations');assert.equal(authoritative.find(record=>record.id===present.id).value,76);assert.equal(authoritative.find(record=>record.id===present.id).code,'heart_rate');assert.equal(authoritative.length,2);
  await page.locator('[data-edit-observation="'+unknown.id+'"]').click();await idle(page);await assertHydratedObservation(page,unknown);await page.locator('#cancelObservationEdit').click();await idle(page);assert.deepEqual(await observationValues(page),draftA);
  await page.locator('[data-select-encounter="'+two.id+'"]').click();await idle(page);assert.equal((await observationValues(page)).code,'');assert.equal(await page.locator('#cancelObservationEdit').count(),0);
  const draftB={code:'heart_rate',status:'present',value:'88',unit:'bpm',observed_at:'2026-10-08T16:02',source:'manual_synthetic'};await fillObservation(page,draftB);
  await page.locator('[data-select-encounter="'+one.id+'"]').click();await idle(page);assert.deepEqual(await observationValues(page),draftA);await page.locator('[data-edit-observation="'+present.id+'"]').click();await idle(page);await assertHydratedObservation(page,authoritative.find(record=>record.id===present.id));
  await page.screenshot({path:path.join(artifacts,'observation-edit-hydrated-desktop.png'),fullPage:true});
  await page.locator('[data-select-encounter="'+two.id+'"]').click();await idle(page);assert.equal(await page.locator('#cancelObservationEdit').count(),0);assert.deepEqual(await observationValues(page),draftB);
  await page.locator('#logoutButton').click();await page.locator('#loginView').waitFor({state:'visible'});await page.locator('#loginPassword').fill('DemoOnly!2026');await page.locator('#loginButton').click();await page.locator('#appView').waitFor({state:'visible'});await idle(page);await navigate(page,'cases');await page.locator('[data-select-case="'+profile.id+'"][data-case-target="encounter"]').click();await idle(page);await page.locator('[data-select-encounter="'+one.id+'"]').click();await idle(page);assert.equal((await observationValues(page)).code,'');await page.locator('[data-select-encounter="'+two.id+'"]').click();await idle(page);assert.equal((await observationValues(page)).code,'');await context.close();
 });
 await check('real stub evaluation failed GET retries read and keeps modules',async()=>{
  const {context,page}=await session();await openEncounter(page);await navigate(page,'evaluation');
  assert((await page.locator('#evalEncounterId').inputValue()).length>0);await page.locator('input[name=modules][value=diagnosis]').check();await page.locator('input[name=modules][value=medsafety]').check();
  let posted=false,count=0,failedOnce=false;
  const handler=async route=>{if(route.request().method()==='POST'){count++;const response=await route.fetch();posted=true;return route.fulfill({response});}if(posted&&!failedOnce){failedOnce=true;return route.abort();}return route.continue();};
  await page.route('**/api/v1/evaluations**',handler);await page.locator('#evaluationForm button').click();await page.waitForFunction(()=>document.querySelector('#evaluationError').textContent.includes('Đã lưu thành công'));
  assert(await page.locator('input[name=modules][value=diagnosis]').isChecked());await page.getByRole('button',{name:'Tải lại dữ liệu đã lưu',exact:true}).click();await idle(page);assert.equal(count,1);assert(await page.locator('input[name=modules][value=diagnosis]').isChecked());assert(await page.locator('input[name=modules][value=medsafety]').isChecked());assert((await page.locator('.module-result').count())>0);await context.close();
 });
 await check('MedSafety context hydrates actual IDs, isolates revision and preserves denied loads',async()=>{
  const a='20000000-0000-4000-8000-000000000001', caseId='10000000-0000-4000-8000-000000000001';
  const doctor=await session();const profile=await api(doctor.page,'GET','/api/v1/cases/'+caseId);
  const second=await api(doctor.page,'POST','/api/v1/cases/'+caseId+'/encounters?expected_revision='+profile.revision,{occurred_at:'2026-10-08T09:00:00Z'});
  const current=await api(doctor.page,'GET','/api/v1/cases/'+caseId);await doctor.context.close();
  const {context,page}=await session('pharmacist_demo');await navigate(page,'medsafety');
  const load=async id=>{await page.locator('#pharmacyEncounterId').fill(id);await page.locator('#pharmacyLoadForm button').click();await idle(page);};
  await load(a);assert.equal(await page.locator('#evalEncounterId').inputValue(),a);assert.equal(await page.locator('#evalRevision').inputValue(),'');
  await page.locator('#evalRevision').fill(String(current.revision));await load(a);assert.equal(await page.locator('#evalRevision').inputValue(),String(current.revision));
  await load('20000000-0000-4000-8000-000000000002');await page.waitForFunction(()=>document.querySelector('#pharmacyLoadError').textContent.length>0);
  assert.equal(await page.locator('#evalEncounterId').inputValue(),a);assert.equal(await page.locator('#evalRevision').inputValue(),String(current.revision));
  await load(second.id);assert.equal(await page.locator('#evalEncounterId').inputValue(),second.id);assert.equal(await page.locator('#evalRevision').inputValue(),'');
  assert.equal(await page.locator('.data-table tbody tr').count(),0);await page.screenshot({path:path.join(artifacts,'medsafety-context-desktop.png'),fullPage:true});await context.close();
 });
 await check('evaluation context clears result and pending GET after successful manual or case switch',async()=>{
  const a='20000000-0000-4000-8000-000000000001',b='20000000-0000-4000-8000-000000000002';
  const {context,page}=await session();await openEncounter(page);
  await page.locator('#loadEncounterSection').evaluate(e=>e.open=true);await page.locator('#knownEncounterId').fill(a);await page.locator('#loadEncounterForm button').click();await idle(page);await navigate(page,'evaluation');
  await page.locator('input[name=modules][value=diagnosis]').check();await page.locator('#evaluationForm button').click();await idle(page);
  assert((await page.locator('.module-result').count())>0);
  const manual=async id=>{await navigate(page,'encounter');await page.locator('#loadEncounterSection').evaluate(e=>e.open=true);await page.locator('#knownEncounterId').fill(id);await page.locator('#loadEncounterForm button').click();await idle(page);};
  await manual('29999999-0000-4000-8000-000000000099');await page.waitForFunction(()=>document.querySelector('#encounterLoadError').textContent.length>0);
  await navigate(page,'evaluation');assert((await page.locator('.module-result').count())>0);assert.equal(await page.locator('#evalEncounterId').inputValue(),a);
  await manual(b);await navigate(page,'evaluation');assert.equal(await page.locator('.module-result').count(),0);
  const profileB=await api(page,'GET','/api/v1/cases/10000000-0000-4000-8000-000000000002');assert.equal(await page.locator('#evalEncounterId').inputValue(),b);assert.equal(await page.locator('#evalRevision').inputValue(),String(profileB.revision));
  await manual(a);await navigate(page,'evaluation');await page.locator('input[name=modules][value=medsafety]').check();let reads=0,posts=0;
  const handler=async route=>{if(route.request().method()==='POST'){posts++;return route.continue();}reads++;return route.abort();};
  await page.route('**/api/v1/evaluations**',handler);await page.locator('#evaluationForm button').click();await page.waitForFunction(()=>document.querySelector('#evaluationError').textContent.includes('Đã lưu thành công'));assert.equal(posts,1);assert.equal(reads,1);
  await manual(b);await navigate(page,'evaluation');assert.equal(reads,1);assert.equal(await page.locator('#evalEncounterId').inputValue(),b);assert.equal(await page.locator('#evalRevision').inputValue(),String(profileB.revision));assert.equal(await page.getByRole('button',{name:'Tải lại dữ liệu đã lưu',exact:true}).count(),0);assert.equal(await page.locator('.module-result').count(),0);
  await page.unroute('**/api/v1/evaluations**',handler);await page.locator('input[name=modules][value=diagnosis]').check();await page.locator('#evaluationForm button').click();await idle(page);assert((await page.locator('.module-result').count())>0);
  await navigate(page,'cases');await page.locator('[data-select-case="10000000-0000-4000-8000-000000000001"][data-case-target="encounter"]').click();await idle(page);await navigate(page,'evaluation');assert.equal(await page.locator('#evalEncounterId').inputValue(),'');assert.equal(await page.locator('.module-result').count(),0);await context.close();
 });
 await check('case context hydrates new profile instead of restoring previous edit draft',async()=>{
  const {context,page}=await session();await navigate(page,'cases');await page.locator('[data-select-case="10000000-0000-4000-8000-000000000001"][data-case-target="cases"]').click();await idle(page);
  await page.locator('#editAge').fill('26');await page.locator('#editSex').selectOption('male');await page.locator('#editSyntheticCode').fill('SYN-QA-OLD-DRAFT');const code='SYN-QA-'+Date.now();await createValues(page,code);await page.locator('#createCaseForm button[type=submit]').click();await idle(page);
  assert.equal(await page.locator('#editSyntheticCode').inputValue(),code);assert.equal(await page.locator('#editAge').inputValue(),'71');assert.equal(await page.locator('#editSex').inputValue(),'unknown');assert.equal(await page.locator('#newSyntheticCode').inputValue(),'');await context.close();
 });
 await check('real admin metadata schema test and activation409 retain feedback',async()=>{
  const {context,page}=await session('admin_demo');await navigate(page,'rules');const code='QA_'+Date.now();await page.locator('#ruleCode').fill(code);await page.locator('#ruleModule').selectOption('diagnosis');await page.locator('#ruleSource').fill('QA synthetic metadata source');await page.locator('#ruleForm button').click();await idle(page);
  const card=page.locator('.rule-card').filter({hasText:code});await card.locator('[data-test-rule]').click();await idle(page);assert((await page.locator('#viewContent').innerText()).includes('schema_passed'));await page.locator('.rule-card').filter({hasText:code}).locator('[data-activate-rule]').click();await page.waitForFunction(()=>document.querySelector('#globalMessage').textContent.length>0);assert(await page.locator('.rule-card').filter({hasText:code}).locator('[data-activate-rule]').isEnabled());await context.close();
 });
 await check('simulated final patient states remove invalid actions',async()=>{
  const {context,page}=await session('patient_demo');
  const appointmentHandler=async route=>{const response=await route.fetch();const records=await response.json();await route.fulfill({response,json:records.map((record,index)=>({...record,status:index%2?'cancelled':'completed'}))});};
  const reminderHandler=async route=>{const response=await route.fetch();const records=await response.json();await route.fulfill({response,json:records.map((record,index)=>({...record,status:index%2?'skipped':'taken'}))});};
  await page.route('**/api/v1/patient/appointments',appointmentHandler);await navigate(page,'appointments');assert.equal(await page.locator('[data-cancel-appointment]').count(),0);await page.route('**/api/v1/patient/reminders',reminderHandler);await navigate(page,'reminders');assert.equal(await page.locator('[data-reminder-id]').count(),0);await context.close();
 });
 await check('simulated logout failure restores usable workspace and permits retry',async()=>{
  const {context,page}=await session();await navigate(page,'cases');await createValues(page,'SYN-QA-LOGOUT-DRAFT');
  const handler=async route=>route.abort();await page.route('**/api/v1/auth/logout',handler);await page.locator('#logoutButton').click();await page.waitForFunction(()=>document.querySelector('#globalMessage').textContent.includes('Không thể xác nhận thu hồi'));
  assert.equal(await page.locator('#newSyntheticCode').inputValue(),'SYN-QA-LOGOUT-DRAFT');assert(await page.locator('#createCaseForm button[type=submit]').isEnabled());assert(!(await page.locator('#appView').evaluate(e=>e.inert)));await page.unroute('**/api/v1/auth/logout',handler);await page.locator('#logoutButton').click();await page.locator('#loginView').waitFor({state:'visible'});await context.close();
 });
 await check('real signup mobile then authoritative login and restored session',async()=>{
  const context=await browser.newContext({viewport:{width:390,height:844}});const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));await page.goto(base);await page.locator('#showRegister').click();await noOverflow(page);
  const name='qa_browser_'+Date.now();await page.locator('#registerUsername').fill(name);await page.locator('#registerPassword').fill('SyntheticOnly!2026');await page.locator('#registerConfirm').fill('MismatchOnly!2026');await page.locator('#registerAge').fill('70');await page.locator('#registerButton').click();assert((await page.locator('#registrationMessage').innerText()).includes('chưa khớp'));
  await page.locator('#registerConfirm').fill('SyntheticOnly!2026');assert.equal(await page.locator('#registrationMessage').innerText(),'');assert.equal(await page.locator('#registerConfirm').getAttribute('aria-invalid'),null);assert.equal(await page.locator('#authTitle').innerText(),'Đăng ký bệnh nhân');await page.screenshot({path:path.join(artifacts,'registration-mobile-viewport.png')});await page.screenshot({path:path.join(artifacts,'registration-mobile.png'),fullPage:true});await page.locator('#registerButton').click();await page.waitForFunction(()=>document.querySelector('#loginMessage').textContent.includes('Đã đăng ký'));
  assert.equal(await page.locator('#loginRole').inputValue(),name);assert.equal(await page.locator('#registerPassword').inputValue(),'');assert.equal(await page.locator('#registerConfirm').inputValue(),'');await page.locator('#loginPassword').fill('SyntheticOnly!2026');await page.locator('#loginButton').click();await page.locator('#appView').waitFor({state:'visible'});await idle(page);assert.equal(await page.locator('#roleLabel').innerText(),'Bệnh nhân');assert((await page.locator('#viewContent').innerText()).includes('tài khoản đang đăng nhập'));assert(!(await page.locator('#viewContent').innerText()).includes('patient_demo'));await navigate(page,'measurements');assert((await page.locator('#viewContent').innerText()).includes('Chưa có bản ghi'));await page.reload();await page.locator('#appView').waitFor({state:'visible'});await idle(page);assert.equal(await page.locator('#roleLabel').innerText(),'Bệnh nhân');await context.close();
 });
 assert.deepEqual(errors,[],'browser runtime errors');
} finally {await browser.close();}
console.log(`Browser checks: ${passed} passed, ${failed} failed; screenshots ${artifacts}`);
process.exitCode=failed?1:0;
