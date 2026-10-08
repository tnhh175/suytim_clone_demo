import { test, before, beforeEach, afterEach, after } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

const { PGlite } = await import(process.env.PGLITE_MODULE
  ? pathToFileURL(process.env.PGLITE_MODULE).href : '@electric-sql/pglite');
const db = new PGlite();
const root = new URL('../', import.meta.url);
const doctor = '00000000-0000-4000-8000-000000000001';
const encounter = '20000000-0000-4000-8000-000000000001';
const caseId = '10000000-0000-4000-8000-000000000001';
const draftRule = '50000000-0000-4000-8000-000000000001';
const decidedResult = '52000000-0000-4000-8000-000000000001';
const treatmentResult = '52000000-0000-4000-8000-000000000003';

async function scalar(sql, params = []) { return Object.values((await db.query(sql, params)).rows[0])[0]; }
async function failure(sql, pattern, params = []) {
  await db.exec('SAVEPOINT expected_failure');
  await assert.rejects(db.query(sql, params), pattern);
  await db.exec('ROLLBACK TO SAVEPOINT expected_failure; RELEASE SAVEPOINT expected_failure');
}
async function evaluation(mode = 'validated') {
  return scalar(`INSERT INTO evaluation(encounter_id,input_revision,input_snapshot,requested_by,mode)
    SELECT $1,revision,'{}',$2,$3 FROM patient_case WHERE id=$4 RETURNING id`, [encounter, doctor, mode, caseId]);
}
async function activateRule(finalStatus = 'active') {
  await db.query("UPDATE rule_version SET status='tested' WHERE id=$1", [draftRule]);
  await db.query(`INSERT INTO rule_approval(rule_version_id,approval_ref,approved_content_hash,approved_at,recorded_by)
    SELECT id,'Synthetic test evidence only',content_hash,now(),$1 FROM rule_version WHERE id=$2`, [doctor, draftRule]);
  await db.query("UPDATE rule_version SET status='approved' WHERE id=$1", [draftRule]);
  if (finalStatus === 'active') await db.query("UPDATE rule_version SET status='active' WHERE id=$1", [draftRule]);
}
async function result(id, status = 'completed', module = 'diagnosis', rule = draftRule) {
  return scalar(`INSERT INTO module_result(evaluation_id,module,rule_version_id,status,message)
    VALUES($1,$2,$3,$4,'Synthetic regression fixture') RETURNING id`, [id, module, rule, status]);
}
const recommendation = `INSERT INTO recommendation(module_result_id,code,severity,description,source_ref)
  VALUES($1,'SYN_QA','info','Synthetic regression fixture','Synthetic evidence only') RETURNING id`;

before(async () => {
  for (const file of ['schema.sql', 'seed.sql', 'portal_permissions.sql', 'migrations/001_result_integrity.sql']) {
    await db.exec(await readFile(new URL(file, root), 'utf8'));
  }
});
beforeEach(async () => { await db.exec('BEGIN'); });
afterEach(async () => { await db.exec('ROLLBACK'); });
after(async () => { await db.close(); });

test('regression: decided result cannot be rewritten to completed with a draft rule', async () => {
  await failure(`UPDATE module_result SET message='Rewritten after decision',status='completed',rule_version_id=$1
    WHERE id=$2`, /Append-only/, [draftRule, decidedResult]);
  await failure('DELETE FROM module_result WHERE id=$1', /Append-only/, [decidedResult]);
  assert.equal(await scalar('SELECT status FROM module_result WHERE id=$1', [decidedResult]), 'mock_not_evaluated');
});

test('regression: treatment cannot be rewritten or inserted using a diagnosis draft rule', async () => {
  await failure("UPDATE module_result SET status='completed',rule_version_id=$1 WHERE id=$2", /Append-only/, [draftRule, treatmentResult]);
  const id = await evaluation();
  await failure(`INSERT INTO module_result(evaluation_id,module,rule_version_id,status,message)
    VALUES($1,'treatment',$2,'completed','Demo')`, /active approved rule/, [id, draftRule]);
  await activateRule();
  await failure(`INSERT INTO module_result(evaluation_id,module,rule_version_id,status,message)
    VALUES($1,'treatment',$2,'completed','Demo')`, /same module/, [id, draftRule]);
});

test('stub permits only mock results without clinical rule attribution', async () => {
  const id = await evaluation('stub');
  await failure(`INSERT INTO module_result(evaluation_id,module,rule_version_id,status,message)
    VALUES($1,'diagnosis',$2,'completed','Demo')`, /Stub evaluation/, [id, draftRule]);
  await failure(`INSERT INTO module_result(evaluation_id,module,rule_version_id,status,message)
    VALUES($1,'diagnosis',$2,'mock_not_evaluated','Demo')`, /Stub evaluation/, [id, draftRule]);
  assert.ok(await result(id, 'mock_not_evaluated', 'diagnosis', null));
});

test('validated mode rejects mock, missing, draft and approved-but-inactive rules', async () => {
  const id = await evaluation();
  for (const [status, rule] of [['mock_not_evaluated', null], ['completed', null], ['completed', draftRule]]) {
    await failure(`INSERT INTO module_result(evaluation_id,module,rule_version_id,status,message)
      VALUES($1,'diagnosis',$2,$3,'Demo')`, /active approved rule/, [id, rule, status]);
  }
  await activateRule('approved');
  await failure(`INSERT INTO module_result(evaluation_id,module,rule_version_id,status,message)
    VALUES($1,'diagnosis',$2,'completed','Demo')`, /active approved rule/, [id, draftRule]);
  await db.query("UPDATE rule_version SET status='active' WHERE id=$1", [draftRule]);
  await db.query("UPDATE rule_version SET status='retired' WHERE id=$1", [draftRule]);
  await failure(`INSERT INTO module_result(evaluation_id,module,rule_version_id,status,message)
    VALUES($1,'diagnosis',$2,'completed','Demo')`, /active approved rule/, [id, draftRule]);
});

test('a transaction may insert evaluation, result and children before recording its decision', async () => {
  await activateRule();
  const id = await evaluation();
  const completed = await result(id);
  const rec = await scalar(recommendation, [completed]);
  await db.query("INSERT INTO result_missing_field(module_result_id,field_code) VALUES($1,'ef')", [completed]);
  assert.ok(await scalar(`INSERT INTO clinical_decision(evaluation_id,doctor_id,action)
    VALUES($1,$2,'accepted') RETURNING id`, [id, doctor]));
  await failure("UPDATE recommendation SET description='Rewritten' WHERE id=$1", /Append-only/, [rec]);
  await failure('DELETE FROM recommendation WHERE id=$1', /Append-only/, [rec]);
  await failure("UPDATE result_missing_field SET field_code='egfr' WHERE module_result_id=$1", /Append-only/, [completed]);
  await failure('DELETE FROM result_missing_field WHERE module_result_id=$1', /Append-only/, [completed]);
});

test('recommendations are rejected on mock, insufficient and failed results', async () => {
  await failure(recommendation, /completed validated/, [decidedResult]);
  await activateRule();
  for (const status of ['insufficient_data', 'failed']) {
    const id = await evaluation();
    const module = await result(id, status);
    await failure(recommendation, /completed validated/, [module]);
  }
});

test('a clinical decision prevents appending module results, recommendations and missing fields', async () => {
  await activateRule();
  const id = await evaluation();
  const completed = await result(id);
  await db.query("INSERT INTO clinical_decision(evaluation_id,doctor_id,action) VALUES($1,$2,'accepted')", [id, doctor]);
  await failure(`INSERT INTO module_result(evaluation_id,module,rule_version_id,status,message)
    VALUES($1,'diagnosis',$2,'completed','Extra result')`, /finalized/, [id, draftRule]);
  await failure(recommendation, /finalized/, [completed]);
  await failure("INSERT INTO result_missing_field(module_result_id,field_code) VALUES($1,'ef')", /finalized/, [completed]);
  await failure("INSERT INTO result_missing_field(module_result_id,field_code) VALUES($1,'egfr')", /finalized/, [decidedResult]);
});

test('retiring a rule preserves existing result and recommendation history', async () => {
  await activateRule();
  const id = await evaluation();
  const completed = await result(id);
  const rec = await scalar(recommendation, [completed]);
  await db.query("UPDATE rule_version SET status='retired' WHERE id=$1", [draftRule]);
  assert.equal(await scalar('SELECT rule_version_id FROM module_result WHERE id=$1', [completed]), draftRule);
  assert.equal(await scalar('SELECT description FROM recommendation WHERE id=$1', [rec]), 'Synthetic regression fixture');
});
