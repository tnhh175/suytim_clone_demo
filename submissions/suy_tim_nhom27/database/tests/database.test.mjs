import { test, before, beforeEach, afterEach, after } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { pbkdf2Sync } from 'node:crypto';
import { exportMetadata } from './metadata.mjs';

// Install @electric-sql/pglite@0.5.8 locally, or point PGLITE_MODULE at its dist/index.js.
const { PGlite } = await import(process.env.PGLITE_MODULE
  ? pathToFileURL(process.env.PGLITE_MODULE).href : '@electric-sql/pglite');
const db = new PGlite();
const root = new URL('../', import.meta.url);
const sql = name => readFile(new URL(name, root), 'utf8');
const doctor = '00000000-0000-4000-8000-000000000001';
const nurse = '00000000-0000-4000-8000-000000000002';
const admin = '00000000-0000-4000-8000-000000000004';
const patient = '00000000-0000-4000-8000-000000000005';
const case1 = '10000000-0000-4000-8000-000000000001';
const case2 = '10000000-0000-4000-8000-000000000002';
const encounter1 = '20000000-0000-4000-8000-000000000001';
const encounter2 = '20000000-0000-4000-8000-000000000002';
const rx = '40000000-0000-4000-8000-000000000001';
const medication = '41000000-0000-4000-8000-000000000001';
const schedule = '42000000-0000-4000-8000-000000000001';
const rule = '50000000-0000-4000-8000-000000000001';
const evaluation = '51000000-0000-4000-8000-000000000001';
let replayStable;

async function rows(query, params = []) { return (await db.query(query, params)).rows; }
async function scalar(query, params = []) { return Object.values((await rows(query, params))[0])[0]; }
async function failure(query, pattern, params = []) {
  await db.exec('SAVEPOINT expected_failure');
  await assert.rejects(db.query(query, params), pattern);
  await db.exec('ROLLBACK TO SAVEPOINT expected_failure; RELEASE SAVEPOINT expected_failure');
}
async function asPatient(user = patient) {
  await db.query("SELECT set_config('app.user_id', $1, true)", [user]);
  await db.exec('SET LOCAL ROLE hf_patient_portal');
}
async function draft(caseId = case1, encounterId = encounter1) {
  const id = await scalar(`INSERT INTO prescription(case_id, encounter_id, doctor_id, starts_on, ends_on)
    VALUES ($1,$2,$3,CURRENT_DATE,CURRENT_DATE+13) RETURNING id`, [caseId, encounterId, doctor]);
  const med = await scalar(`INSERT INTO medication(encounter_id, ingredient_code, prescription_id, dose,
    dose_unit, route, frequency_per_day, kind, starts_on, ends_on, recorded_by)
    VALUES ($1,'synthetic_drug_a',$2,1,'mg','oral',1,'current',CURRENT_DATE,CURRENT_DATE+13,$3) RETURNING id`,
    [encounterId, id, doctor]);
  return { id, med };
}

before(async () => {
  await db.exec("SET TIME ZONE 'Asia/Ho_Chi_Minh'");
  await db.exec(await sql('schema.sql'));
  await db.exec(await sql('seed.sql'));
  await db.exec(await sql('portal_permissions.sql'));
  const counts = await rows(`SELECT
    (SELECT count(*) FROM app_user) AS users, (SELECT count(*) FROM observation) AS observations,
    (SELECT count(*) FROM appointment) AS appointments, (SELECT count(*) FROM medication_reminder) AS reminders,
    (SELECT count(*) FROM audit_event) AS audit, (SELECT sum(revision) FROM patient_case) AS revisions`);
  await db.exec(await sql('seed.sql'));
  replayStable = JSON.stringify(counts) === JSON.stringify(await rows(`SELECT
    (SELECT count(*) FROM app_user) AS users, (SELECT count(*) FROM observation) AS observations,
    (SELECT count(*) FROM appointment) AS appointments, (SELECT count(*) FROM medication_reminder) AS reminders,
    (SELECT count(*) FROM audit_event) AS audit, (SELECT sum(revision) FROM patient_case) AS revisions`));
  console.log(await scalar('SELECT version()'));
  if (process.env.DB_EXPORT_METADATA === '1') {
    await exportMetadata(db);
  }
});
beforeEach(async () => { await db.exec('BEGIN'); });
afterEach(async () => { await db.exec('ROLLBACK'); });
after(async () => { await db.close(); });

test('schema loads, seed replays without duplicates or revision/audit changes', async () => {
  assert.ok(replayStable);
  assert.equal(await scalar('SELECT count(*) FROM app_user'), 5);
  assert.equal(await scalar('SELECT count(*) FROM role'), 5);
  assert.equal(await scalar('SELECT count(*) FROM patient_account'), 1);
  assert.equal(await scalar('SELECT count(*) FROM medication_reminder'), 21);
  assert.equal(await scalar('SELECT generate_medication_reminders(CURRENT_DATE,CURRENT_DATE+6)'), 0);
});
test('all seeded password hashes verify using the documented demo password', async () => {
  for (const { password_hash } of await rows('SELECT password_hash FROM app_user')) {
    const [scheme, iterations, salt, hash] = password_hash.split('$');
    assert.equal(scheme, 'pbkdf2_sha256');
    assert.equal(pbkdf2Sync('DemoOnly!2026', Buffer.from(salt, 'base64'), Number(iterations), 32, 'sha256').toString('base64'), hash);
  }
});
test('patient sees their confirmed prescription with exact daily dose times', async () => {
  await asPatient();
  const prescriptions = await rows('SELECT * FROM patient_prescription_view ORDER BY medication_id');
  assert.equal(prescriptions.length, 2);
  assert.deepEqual(prescriptions[0].dose_times, ['08:00:00', '20:00:00']);
  assert.deepEqual(prescriptions[1].dose_times, ['12:00:00']);
  assert.equal((await rows('SELECT * FROM portal_doctors()')).length, 1);
  await failure('SELECT password_hash FROM app_user', /permission denied/);
});
test('locked patient account and missing identity cannot see portal data', async () => {
  await db.query('UPDATE app_user SET active=false WHERE id=$1', [patient]);
  await asPatient();
  assert.equal(await scalar('SELECT count(*) FROM patient_prescription_view'), 0);
  assert.equal(await scalar('SELECT count(*) FROM patient_measurement'), 0);
  assert.equal(await scalar('SELECT count(*) FROM appointment'), 0);
  await failure(`INSERT INTO patient_measurement(case_id,recorded_by,observed_at,weight_kg) VALUES($1,$2,now(),60)`, /own profile|row-level security/, [case1, patient]);
});
test('patient isolation hides other profiles and their confirmed prescriptions/reminders', async () => {
  const other = '00000000-0000-4000-8000-000000000006';
  await db.query(`INSERT INTO app_user(id,username,password_hash) SELECT $1,'other_patient',password_hash FROM app_user WHERE id=$2`, [other, patient]);
  await db.query("INSERT INTO user_role VALUES($1,'patient')", [other]);
  await db.query('INSERT INTO patient_account(user_id,case_id) VALUES($1,$2)', [other, case2]);
  const p = await draft(case2, encounter2);
  await db.query("INSERT INTO medication_schedule(medication_id,dose_time) VALUES($1,'07:00')", [p.med]);
  await db.query("UPDATE prescription SET status='confirmed' WHERE id=$1", [p.id]);
  await db.exec('SELECT generate_medication_reminders(CURRENT_DATE,CURRENT_DATE+6)');
  await asPatient();
  assert.equal(await scalar('SELECT count(*) FROM patient_prescription_view WHERE case_id=$1', [case2]), 0);
  assert.equal(await scalar('SELECT count(*) FROM patient_reminder_view WHERE case_id=$1', [case2]), 0);
  assert.equal(await scalar('SELECT count(*) FROM patient_reminder_view'), 21);
  await db.query("SELECT set_config('app.user_id',$1,true)", [other]);
  assert.equal(await scalar('SELECT count(*) FROM patient_prescription_view'), 1);
  assert.equal(await scalar('SELECT count(*) FROM patient_reminder_view'), 7);
  await db.query("SELECT set_config('app.user_id','',true)");
  assert.equal(await scalar('SELECT count(*) FROM patient_prescription_view'), 0);
});
test('patient records minimal home measurements but cannot write another profile or clinical observations', async () => {
  await asPatient();
  await db.query(`INSERT INTO patient_measurement(case_id,recorded_by,observed_at,systolic_bp,diastolic_bp,heart_rate,weight_kg)
    VALUES($1,$2,now(),120,80,72,60)`, [case1, patient]);
  assert.equal(await scalar('SELECT count(*) FROM patient_measurement'), 3);
  await failure(`INSERT INTO patient_measurement(case_id,recorded_by,observed_at,weight_kg) VALUES($1,$2,now(),60)`, /own profile|row-level security/, [case2, patient]);
  await failure(`INSERT INTO observation(encounter_id,code,status,observed_at,source,recorded_by) VALUES($1,'ef','unknown',now(),'manual_synthetic',$2)`, /permission denied/, [encounter1, patient]);
});
test('home readings reject empty payloads, partial BP, nonfinite/negative values and future timestamps', async () => {
  await asPatient();
  const prefix = `INSERT INTO patient_measurement(case_id,recorded_by,observed_at,`;
  for (const [fields, values] of [['systolic_bp','120'], ['systolic_bp,diastolic_bp','70,90'], ['heart_rate','-1'], ['weight_kg',"'NaN'"], ['spo2','101']]) {
    await failure(`${prefix}${fields}) VALUES($1,$2,now(),${values})`, /check constraint/, [case1, patient]);
  }
  await failure('INSERT INTO patient_measurement(case_id,recorded_by,observed_at) VALUES($1,$2,now())', /check constraint/, [case1, patient]);
  await failure(`INSERT INTO patient_measurement(case_id,recorded_by,observed_at,weight_kg) VALUES($1,$2,now()+interval '1 day',60)`, /future/, [case1, patient]);
});
test('appointment slots enforce duplicate booking, cancellation and patient permissions', async () => {
  await asPatient();
  await failure(`INSERT INTO appointment(case_id,doctor_id,slot_at,reason,requested_by)
    SELECT $1,$2,slot_at,'Duplicate',$3 FROM appointment LIMIT 1`, /unique constraint/, [case1, doctor, patient]);
  await failure("UPDATE appointment SET status='confirmed'", /row-level security/);
  await failure("UPDATE appointment SET slot_at=slot_at+interval '30 minutes'", /permission denied/);
  await db.exec("UPDATE appointment SET status='cancelled'");
  await db.query(`INSERT INTO appointment(case_id,doctor_id,slot_at,reason,requested_by)
    SELECT $1,$2,slot_at,'Book released slot',$3 FROM appointment LIMIT 1`, [case1, doctor, patient]);
  assert.equal(await scalar("SELECT count(*) FROM appointment WHERE status='requested'"), 1);
  await failure(`INSERT INTO appointment(case_id,doctor_id,slot_at,reason,requested_by)
    VALUES($1,$2,now()-interval '1 day','Past',$3)`, /future|check constraint/, [case1, doctor, patient]);
});
test('draft prescriptions stay hidden and patient cannot edit doses or clock times', async () => {
  await draft();
  await asPatient();
  assert.equal(await scalar('SELECT count(*) FROM prescription'), 1);
  await failure('UPDATE medication SET dose=2', /permission denied/);
  await failure("UPDATE medication_schedule SET dose_time='09:00'", /permission denied/);
  await failure("UPDATE prescription SET status='cancelled'", /permission denied/);
});
test('doctor must add one daily time per dose before confirming a prescription', async () => {
  const p = await draft();
  await failure("UPDATE prescription SET status='confirmed' WHERE id=$1", /one clock time/, [p.id]);
  await db.query("INSERT INTO medication_schedule(medication_id,dose_time) VALUES($1,'09:00')", [p.med]);
  await failure("INSERT INTO medication_schedule(medication_id,dose_time) VALUES($1,'09:00')", /unique constraint/, [p.med]);
  await failure("INSERT INTO medication_schedule(medication_id,dose_time) VALUES($1,'24:00')", /check constraint/, [p.med]);
  await db.query("UPDATE prescription SET status='confirmed' WHERE id=$1", [p.id]);
  await failure('UPDATE medication SET dose=2 WHERE id=$1', /immutable/, [p.med]);
  await failure("UPDATE medication_schedule SET dose_time='10:00' WHERE medication_id=$1", /immutable/, [p.med]);
  await failure("UPDATE prescription SET instructions='changed' WHERE id=$1", /immutable/, [p.id]);
});
test('reminders use prescription timezone and patient response is timestamped and final', async () => {
  assert.equal(await scalar(`SELECT count(*) FROM medication_reminder r JOIN medication_schedule s ON s.id=r.schedule_id
    WHERE r.due_at <> (r.scheduled_on+s.dose_time) AT TIME ZONE 'Asia/Ho_Chi_Minh'`), 0);
  const reminder = await scalar('SELECT id FROM medication_reminder WHERE schedule_id=$1 ORDER BY due_at LIMIT 1', [schedule]);
  await asPatient();
  await db.query("UPDATE medication_reminder SET status='taken' WHERE id=$1", [reminder]);
  assert.equal(await scalar('SELECT count(*) FROM medication_reminder WHERE id=$1 AND responded_at IS NOT NULL', [reminder]), 1);
  // Resolved rows are excluded by the UPDATE policy, so another response affects zero rows.
  assert.equal((await db.query("UPDATE medication_reminder SET status='skipped' WHERE id=$1", [reminder])).affectedRows, 0);
  await failure('UPDATE medication_reminder SET due_at=now()', /permission denied/);
  await failure('SELECT generate_medication_reminders(CURRENT_DATE,CURRENT_DATE+1)', /permission denied/);
});
test('cancelling a prescription cancels pending reminders and preserves dose history', async () => {
  await db.query("UPDATE prescription SET status='cancelled' WHERE id=$1", [rx]);
  assert.equal(await scalar("SELECT count(*) FROM medication_reminder WHERE status='pending'"), 0);
  assert.equal(await scalar("SELECT count(*) FROM medication_reminder WHERE status='cancelled'"), 21);
  assert.equal(await scalar('SELECT generate_medication_reminders(CURRENT_DATE,CURRENT_DATE+6)'), 0);
  assert.equal(await scalar('SELECT count(*) FROM medication_schedule'), 3);
});
test('approval requires an explicit permission, matching tested content and immutable evidence', async () => {
  await failure("UPDATE rule_version SET status='active' WHERE id=$1", /Invalid rule status transition/, [rule]);
  await db.query("UPDATE rule_version SET status='tested' WHERE id=$1", [rule]);
  const query = `INSERT INTO rule_approval(rule_version_id,approval_ref,approved_content_hash,approved_at,recorded_by)
    SELECT id,'Synthetic test-only approval',content_hash,now(),$1 FROM rule_version WHERE id=$2`;
  await failure(query, /permission required/, [admin, rule]);
  await db.query(query, [doctor, rule]);
  await db.query("UPDATE rule_version SET status='approved' WHERE id=$1", [rule]);
  await db.query("UPDATE rule_version SET status='active' WHERE id=$1", [rule]);
  await failure("UPDATE rule_version SET content='{}' WHERE id=$1", /new version/, [rule]);
  await failure('DELETE FROM rule_approval WHERE rule_version_id=$1', /Append-only/, [rule]);
  await failure('DELETE FROM rule_required_field WHERE rule_version_id=$1', /new rule version/, [rule]);
});
test('clinical changes increment revisions and stale evaluations cannot produce decisions', async () => {
  const beforeRevision = Number(await scalar('SELECT revision FROM patient_case WHERE id=$1', [case1]));
  await db.query("UPDATE observation SET value_number=121 WHERE code='systolic_bp'");
  assert.equal(Number(await scalar('SELECT revision FROM patient_case WHERE id=$1', [case1])), beforeRevision + 1);
  const newEval = await scalar(`INSERT INTO evaluation(encounter_id,input_revision,input_snapshot,requested_by,mode)
    SELECT $1,revision,'{}',$2,'stub' FROM patient_case WHERE id=$3 RETURNING id`, [encounter1, doctor, case1]);
  await db.exec("UPDATE observation SET value_number=122 WHERE code='systolic_bp'");
  await failure(`INSERT INTO clinical_decision(evaluation_id,doctor_id,action) VALUES($1,$2,'accepted')`, /Stale evaluation/, [newEval, doctor]);
});
test('profile edits increment revision and recorded catalog definitions cannot be retyped', async () => {
  const rev = Number(await scalar('SELECT revision FROM patient_case WHERE id=$1', [case1]));
  await db.query('UPDATE patient_case SET age=age+1 WHERE id=$1', [case1]);
  assert.equal(Number(await scalar('SELECT revision FROM patient_case WHERE id=$1', [case1])), rev+1);
  await failure("UPDATE observation_type SET unit='other' WHERE code='systolic_bp'", /new observation code/);
  await failure('UPDATE patient_account SET case_id=$1 WHERE user_id=$2', /Append-only/, [case2, patient]);
});
test('exported metadata matches actual table columns, keys, RLS policies and triggers', async () => {
  const metadata = JSON.parse(await sql('schema_metadata.json'));
  const tables = await rows("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename");
  assert.deepEqual(metadata.map(x => x.name), tables.map(x => x.tablename));
  for (const table of metadata) {
    assert.ok(table.description);
    const columns = await rows(`SELECT attname AS name,format_type(atttypid,atttypmod) AS type,NOT attnotnull AS nullable
      FROM pg_attribute WHERE attrelid=$1::regclass AND attnum>0 AND NOT attisdropped ORDER BY attnum`, [table.name]);
    assert.deepEqual(table.columns.map(({ name, type, nullable }) => ({ name, type, nullable })), columns);
    assert.ok(table.columns.every(c => c.description && c.constraint));
    assert.deepEqual(table.constraints.map(({ name, definition }) => ({ name, definition })), await rows(`SELECT conname AS name,
      pg_get_constraintdef(oid) AS definition FROM pg_constraint WHERE conrelid=$1::regclass AND contype <> 'n' ORDER BY conname`, [table.name]));
    assert.deepEqual(table.triggers, await rows(`SELECT tgname AS name,pg_get_triggerdef(oid) AS definition FROM pg_trigger
      WHERE tgrelid=$1::regclass AND NOT tgisinternal ORDER BY tgname`, [table.name]));
    assert.deepEqual(table.indexes, await rows(`SELECT indexname AS name,indexdef AS definition FROM pg_indexes
      WHERE schemaname='public' AND tablename=$1 ORDER BY indexname`, [table.name]));
    assert.deepEqual(table.row_level_security, await rows(`SELECT policyname AS name,cmd AS command,qual AS using_expression,
      with_check AS check_expression FROM pg_policies WHERE schemaname='public' AND tablename=$1 ORDER BY policyname`, [table.name]));
  }
});
test('nurse writes assigned vital signs but cannot write doctor diagnosis or another case', async () => {
  await db.query(`INSERT INTO observation(encounter_id,code,value_number,status,observed_at,source,recorded_by)
    VALUES($1,'heart_rate',75,'present',now(),'manual_synthetic',$2)`, [encounter1, nurse]);
  await failure(`INSERT INTO clinical_note(encounter_id,kind,content,recorded_by) VALUES($1,'diagnosis','Demo',$2)`, /no write access/, [encounter1, nurse]);
  await failure(`INSERT INTO observation(encounter_id,code,value_number,status,observed_at,source,recorded_by)
    VALUES($1,'heart_rate',75,'present',now(),'manual_synthetic',$2)`, /no write access/, [encounter2, nurse]);
});
test('cross-encounter prescriptions and mixed patient/staff accounts are rejected', async () => {
  await failure(`INSERT INTO medication(encounter_id,ingredient_code,prescription_id,dose,dose_unit,route,frequency_per_day,kind,recorded_by)
    VALUES($1,'synthetic_drug_a',$2,1,'mg','oral',1,'current',$3)`, /immutable|foreign key/, [encounter2, rx, doctor]);
  await failure("INSERT INTO user_role VALUES($1,'doctor')", /separate from staff/, [patient]);
  await failure("INSERT INTO case_access VALUES($1,$2,'clinical')", /Role does not match/, [case1, patient]);
});
test('audit, evaluation snapshots and decisions are append-only', async () => {
  assert.equal(await scalar("SELECT count(*) FROM audit_event WHERE entity_type='medication_reminder' AND actor_kind='system'"), 21);
  const count = Number(await scalar("SELECT count(*) FROM audit_event WHERE entity_type='observation'"));
  await db.exec("UPDATE observation SET value_number=123 WHERE code='systolic_bp'");
  assert.equal(Number(await scalar("SELECT count(*) FROM audit_event WHERE entity_type='observation'")), count+1);
  await failure('DELETE FROM audit_event', /Append-only/);
  await failure("UPDATE evaluation SET input_snapshot='{}' WHERE id=$1", /Append-only/, [evaluation]);
  await failure("UPDATE clinical_decision SET reason='Changed'", /Append-only/);
});
