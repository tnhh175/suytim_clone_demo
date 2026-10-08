-- PostgreSQL 16+. Fresh database bootstrap, not an in-place migration.
-- SRS FR-01..34 plus the minimal patient portal extension FR-P01..04.

BEGIN;

CREATE TABLE department (
  code varchar(30) PRIMARY KEY,
  name text NOT NULL CHECK (length(trim(name)) > 0),
  active boolean NOT NULL DEFAULT true
);

CREATE TABLE app_user (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  username varchar(80) NOT NULL UNIQUE,
  password_hash text NOT NULL,
  active boolean NOT NULL DEFAULT true,
  department_code varchar(30) REFERENCES department(code),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE role (
  code varchar(20) PRIMARY KEY CHECK (code IN ('doctor','nurse','pharmacist','admin','patient'))
);

CREATE TABLE user_role (
  user_id uuid NOT NULL REFERENCES app_user(id),
  role_code varchar(20) NOT NULL REFERENCES role(code) ,
  PRIMARY KEY(user_id,role_code)
);

CREATE TABLE permission (
  code varchar(60) PRIMARY KEY,
  description text NOT NULL
);

CREATE TABLE user_permission (
  user_id uuid NOT NULL REFERENCES app_user(id),
  permission_code varchar(60) NOT NULL REFERENCES permission(code),
  PRIMARY KEY (user_id, permission_code)
);

CREATE TABLE auth_session (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES app_user(id),
  token_hash varchar(64) NOT NULL UNIQUE CHECK (token_hash ~ '^[a-f0-9]{64}$'),
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (expires_at > created_at)
);
CREATE INDEX ix_auth_session_user ON auth_session(user_id, expires_at);

CREATE TABLE patient_case (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  synthetic_code varchar(30) NOT NULL UNIQUE CHECK (synthetic_code ~ '^SYN-[A-Z0-9-]{1,24}$'),
  age smallint NOT NULL CHECK (age BETWEEN 0 AND 120),
  sex varchar(10) NOT NULL CHECK (sex IN ('male','female','unknown')),
  owner_id uuid NOT NULL REFERENCES app_user(id),
  revision integer NOT NULL DEFAULT 1 CHECK(revision>0),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ix_case_owner ON patient_case(owner_id);

-- One patient account owns one synthetic profile; staff access uses case_access.
CREATE TABLE patient_account (
  user_id uuid PRIMARY KEY REFERENCES app_user(id),
  case_id uuid NOT NULL UNIQUE REFERENCES patient_case(id),
  role_code varchar(20) NOT NULL DEFAULT 'patient' CHECK (role_code = 'patient'),
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (user_id, role_code) REFERENCES user_role(user_id, role_code)
);

CREATE TABLE case_access (
  case_id uuid NOT NULL REFERENCES patient_case(id),
  user_id uuid NOT NULL REFERENCES app_user(id),
  access_scope varchar(20) NOT NULL CHECK(access_scope IN ('clinical','nursing','medsafety')) ,
  PRIMARY KEY(case_id,user_id,access_scope)
);

CREATE TABLE encounter (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL REFERENCES patient_case(id),
  occurred_at timestamptz NOT NULL,
  kind varchar(12) NOT NULL DEFAULT 'outpatient' CHECK (kind IN ('outpatient','inpatient')),
  department_code varchar(30) NOT NULL REFERENCES department(code),
  doctor_id uuid NOT NULL REFERENCES app_user(id),
  status varchar(12) NOT NULL DEFAULT 'open' CHECK (status IN ('open','completed','cancelled')),
  ended_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (id, case_id),
  CHECK (ended_at IS NULL OR ended_at >= occurred_at),
  CHECK ((status = 'open' AND ended_at IS NULL) OR (status <> 'open' AND ended_at IS NOT NULL))
);

CREATE INDEX ix_encounter_case_time ON encounter(case_id,occurred_at DESC);

CREATE TABLE observation_type (
  code varchar(60) PRIMARY KEY,
  label text NOT NULL,
  value_kind varchar(10) NOT NULL CHECK(value_kind IN ('number','boolean','text')),
  unit varchar(40) ,
  min_value numeric ,
  max_value numeric  ,
  CHECK(min_value IS NULL OR max_value IS NULL OR min_value<=max_value),
  CHECK(min_value::text NOT IN ('NaN','Infinity','-Infinity')),
  CHECK(max_value::text NOT IN ('NaN','Infinity','-Infinity'))
);

CREATE TABLE observation (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  encounter_id uuid NOT NULL REFERENCES encounter(id),
  code varchar(60) NOT NULL REFERENCES observation_type(code),
  value_number numeric ,
  value_boolean boolean ,
  value_text text ,
  status varchar(20) NOT NULL CHECK(status IN ('present','not_measured','unknown')),
  observed_at timestamptz NOT NULL,
  source varchar(30) NOT NULL CHECK(source IN ('manual_synthetic','mock_his','mock_lis','mock_pacs','mock_emr')),
  recorded_by uuid NOT NULL REFERENCES app_user(id),
  created_at timestamptz NOT NULL DEFAULT now() ,
  CHECK ((status = 'present' AND num_nonnulls(value_number,value_boolean,value_text)=1) OR (status<>'present' AND num_nonnulls(value_number,value_boolean,value_text)=0))
);

CREATE INDEX ix_observation_latest ON observation(encounter_id,code,observed_at DESC);

CREATE TABLE ingredient (
  code varchar(60) PRIMARY KEY,
  display_name text NOT NULL
);

CREATE TABLE drug_product (
  code varchar(60) PRIMARY KEY,
  ingredient_code varchar(60) NOT NULL REFERENCES ingredient(code),
  display_name text NOT NULL,
  strength numeric NOT NULL CHECK (strength > 0 AND strength::text NOT IN ('NaN','Infinity','-Infinity')),
  strength_unit varchar(10) NOT NULL CHECK (strength_unit IN ('mg','mcg','g','mg/mL')),
  dosage_form varchar(30) NOT NULL,
  active boolean NOT NULL DEFAULT true,
  UNIQUE (code, ingredient_code)
);

CREATE TABLE prescription (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL REFERENCES patient_case(id),
  encounter_id uuid NOT NULL,
  doctor_id uuid NOT NULL REFERENCES app_user(id),
  status varchar(12) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','confirmed','cancelled')),
  starts_on date NOT NULL,
  ends_on date,
  timezone varchar(60) NOT NULL DEFAULT 'Asia/Ho_Chi_Minh',
  instructions text NOT NULL DEFAULT '',
  confirmed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (encounter_id, case_id) REFERENCES encounter(id, case_id),
  UNIQUE (id, encounter_id),
  CHECK (ends_on IS NULL OR ends_on >= starts_on),
  CHECK ((status = 'draft' AND confirmed_at IS NULL) OR (status <> 'draft' AND confirmed_at IS NOT NULL))
);
CREATE INDEX ix_prescription_case ON prescription(case_id, created_at DESC);

CREATE TABLE medication (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  encounter_id uuid NOT NULL REFERENCES encounter(id),
  ingredient_code varchar(60) NOT NULL REFERENCES ingredient(code),
  drug_product_code varchar(60),
  prescription_id uuid,
  dose numeric NOT NULL CHECK(dose>0 AND dose::text NOT IN ('NaN','Infinity','-Infinity')),
  dose_unit varchar(10) NOT NULL CHECK(dose_unit IN ('mg','mcg','g','mL')),
  route varchar(10) NOT NULL CHECK(route IN ('oral','iv','other')),
  frequency_per_day smallint NOT NULL CHECK(frequency_per_day BETWEEN 1 AND 24),
  kind varchar(10) NOT NULL CHECK(kind IN ('current','proposed')),
  starts_on date NOT NULL DEFAULT CURRENT_DATE,
  ends_on date,
  instructions text NOT NULL DEFAULT '',
  recorded_by uuid NOT NULL REFERENCES app_user(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (drug_product_code, ingredient_code) REFERENCES drug_product(code, ingredient_code),
  FOREIGN KEY (prescription_id, encounter_id) REFERENCES prescription(id, encounter_id),
  CHECK (ends_on IS NULL OR ends_on >= starts_on),
  CHECK (prescription_id IS NULL OR kind = 'current')
);

CREATE INDEX ix_medication_encounter ON medication(encounter_id);
CREATE INDEX ix_medication_prescription ON medication(prescription_id);

-- Daily local clock times, one row per dose. The prescription supplies timezone.
CREATE TABLE medication_schedule (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  medication_id uuid NOT NULL REFERENCES medication(id),
  dose_time time NOT NULL CHECK (dose_time >= TIME '00:00' AND dose_time < TIME '24:00'),
  instructions text NOT NULL DEFAULT '',
  UNIQUE (medication_id, dose_time)
);

CREATE TABLE medication_reminder (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  schedule_id uuid NOT NULL REFERENCES medication_schedule(id),
  scheduled_on date NOT NULL,
  due_at timestamptz NOT NULL,
  status varchar(12) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','taken','skipped','cancelled')),
  responded_at timestamptz,
  notified_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (schedule_id, scheduled_on),
  CHECK ((status IN ('pending','cancelled') AND responded_at IS NULL) OR
         (status IN ('taken','skipped') AND responded_at IS NOT NULL))
);
CREATE INDEX ix_reminder_due ON medication_reminder(due_at) WHERE status = 'pending';

CREATE TABLE rule_version (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code varchar(60) NOT NULL,
  version integer NOT NULL CHECK(version>0),
  module varchar(20) NOT NULL CHECK(module IN ('diagnosis','lab_test','treatment','medsafety')),
  source_ref text NOT NULL,
  content_hash varchar(64) NOT NULL CHECK(content_hash ~ '^[a-f0-9]{64}$'),
  content jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(content) = 'object'),
  status varchar(12) NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','tested','approved','active','retired')),
  created_by uuid NOT NULL REFERENCES app_user(id),
  created_at timestamptz NOT NULL DEFAULT now() ,
  UNIQUE(code,version)
);

CREATE UNIQUE INDEX ux_rule_active ON rule_version(code) WHERE status='active';

CREATE TABLE rule_required_field (
  rule_version_id uuid NOT NULL REFERENCES rule_version(id),
  field_code varchar(60) NOT NULL REFERENCES observation_type(code),
  PRIMARY KEY (rule_version_id, field_code)
);

CREATE TABLE rule_approval (
  rule_version_id uuid PRIMARY KEY REFERENCES rule_version(id),
  approval_ref text NOT NULL CHECK(length(trim(approval_ref))>0),
  approved_content_hash varchar(64) NOT NULL CHECK(approved_content_hash ~ '^[a-f0-9]{64}$'),
  approved_at timestamptz NOT NULL,
  recorded_by uuid NOT NULL REFERENCES app_user(id)
);

CREATE TABLE evaluation (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  encounter_id uuid NOT NULL REFERENCES encounter(id),
  input_revision integer NOT NULL CHECK(input_revision>0),
  input_snapshot jsonb NOT NULL CHECK(jsonb_typeof(input_snapshot)='object'),
  requested_by uuid NOT NULL REFERENCES app_user(id),
  mode varchar(10) NOT NULL CHECK(mode IN ('stub','validated')),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (id, encounter_id)
);

CREATE INDEX ix_evaluation_history ON evaluation(encounter_id,created_at DESC);

CREATE TABLE module_result (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  evaluation_id uuid NOT NULL REFERENCES evaluation(id),
  module varchar(20) NOT NULL CHECK(module IN ('diagnosis','lab_test','treatment','medsafety')),
  rule_version_id uuid REFERENCES rule_version(id),
  status varchar(30) NOT NULL CHECK(status IN ('mock_not_evaluated','completed','insufficient_data','failed')),
  message text NOT NULL ,
  UNIQUE(evaluation_id,module),
  CHECK(status='mock_not_evaluated' OR rule_version_id IS NOT NULL)
);

CREATE TABLE recommendation (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  module_result_id uuid NOT NULL REFERENCES module_result(id),
  code varchar(80) NOT NULL,
  severity varchar(12) NOT NULL CHECK(severity IN ('info','warning','critical')),
  description text NOT NULL,
  source_ref text NOT NULL
);

CREATE INDEX ix_recommendation_result ON recommendation(module_result_id);

CREATE TABLE result_missing_field (
  module_result_id uuid NOT NULL REFERENCES module_result(id),
  field_code varchar(60) NOT NULL REFERENCES observation_type(code) ,
  PRIMARY KEY(module_result_id,field_code)
);

CREATE TABLE clinical_decision (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  evaluation_id uuid NOT NULL UNIQUE REFERENCES evaluation(id),
  doctor_id uuid NOT NULL REFERENCES app_user(id),
  action varchar(10) NOT NULL CHECK(action IN ('accepted','adjusted','rejected')),
  reason text ,
  adjustment_details jsonb,
  created_at timestamptz NOT NULL DEFAULT now() ,
  CHECK(action='accepted' OR length(trim(coalesce(reason,'')))>0),
  CHECK ((action = 'adjusted' AND adjustment_details IS NOT NULL AND
          jsonb_typeof(adjustment_details) = 'object' AND adjustment_details <> '{}') OR
         (action <> 'adjusted' AND adjustment_details IS NULL))
);

CREATE TABLE patient_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL REFERENCES patient_case(id),
  kind varchar(20) NOT NULL CHECK (kind IN ('medical','comorbidity','family','social')),
  description text NOT NULL CHECK (length(trim(description)) > 0),
  recorded_by uuid NOT NULL REFERENCES app_user(id),
  recorded_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_history_case ON patient_history(case_id, recorded_at DESC);

CREATE TABLE clinical_note (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  encounter_id uuid NOT NULL REFERENCES encounter(id),
  kind varchar(20) NOT NULL CHECK (kind IN ('nursing','examination','diagnosis','geriatric')),
  content text NOT NULL CHECK (length(trim(content)) > 0),
  recorded_by uuid NOT NULL REFERENCES app_user(id),
  recorded_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_note_encounter ON clinical_note(encounter_id, recorded_at DESC);

-- Distinguish unknown, confirmed-none and known reactions at the profile level.
CREATE TABLE allergy_status (
  case_id uuid PRIMARY KEY REFERENCES patient_case(id),
  status varchar(10) NOT NULL CHECK (status IN ('unknown','none','known')),
  recorded_by uuid NOT NULL REFERENCES app_user(id),
  recorded_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE drug_reaction (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL REFERENCES allergy_status(case_id),
  ingredient_code varchar(60) NOT NULL REFERENCES ingredient(code),
  kind varchar(10) NOT NULL CHECK (kind IN ('allergy','adverse')),
  description text NOT NULL CHECK (length(trim(description)) > 0),
  recorded_by uuid NOT NULL REFERENCES app_user(id),
  recorded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE test_report (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  encounter_id uuid NOT NULL REFERENCES encounter(id),
  kind varchar(10) NOT NULL CHECK (kind IN ('lab','echo','ecg','other')),
  performed_at timestamptz NOT NULL,
  source varchar(30) NOT NULL CHECK (source IN ('manual_synthetic','mock_his','mock_lis','mock_pacs','mock_emr')),
  external_ref text,
  content jsonb NOT NULL CHECK (jsonb_typeof(content) = 'object'),
  recorded_by uuid NOT NULL REFERENCES app_user(id),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_test_report_encounter ON test_report(encounter_id, performed_at DESC);

CREATE TABLE import_batch (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  encounter_id uuid NOT NULL REFERENCES encounter(id),
  source varchar(30) NOT NULL CHECK (source IN ('file','mock_his','mock_lis','mock_pacs','mock_emr')),
  external_ref text NOT NULL,
  status varchar(12) NOT NULL CHECK (status IN ('pending','completed','partial','failed')),
  accepted_rows integer NOT NULL DEFAULT 0 CHECK (accepted_rows >= 0),
  rejected_rows integer NOT NULL DEFAULT 0 CHECK (rejected_rows >= 0),
  imported_by uuid NOT NULL REFERENCES app_user(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (source, external_ref)
);
CREATE TABLE import_error (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  batch_id uuid NOT NULL REFERENCES import_batch(id),
  row_number integer NOT NULL CHECK (row_number > 0),
  field_code varchar(60) NOT NULL,
  message text NOT NULL
);
CREATE INDEX ix_import_error_batch ON import_error(batch_id);

CREATE TABLE pharmacist_review (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  evaluation_id uuid NOT NULL REFERENCES evaluation(id),
  pharmacist_id uuid NOT NULL REFERENCES app_user(id),
  comment text NOT NULL CHECK (length(trim(comment)) > 0),
  proposal text,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_review_evaluation ON pharmacist_review(evaluation_id);

CREATE TABLE treatment_plan (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  encounter_id uuid NOT NULL REFERENCES encounter(id),
  doctor_id uuid NOT NULL REFERENCES app_user(id),
  decision_id uuid REFERENCES clinical_decision(id),
  kind varchar(12) NOT NULL CHECK (kind IN ('treatment','monitoring','discharge','follow_up')),
  content text NOT NULL CHECK (length(trim(content)) > 0),
  follow_up_at timestamptz,
  status varchar(12) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','confirmed','cancelled')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_plan_encounter ON treatment_plan(encounter_id, created_at DESC);

-- Fixed 30-minute slots make concurrent booking conflicts enforceable by UNIQUE.
CREATE TABLE appointment (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL REFERENCES patient_case(id),
  doctor_id uuid NOT NULL REFERENCES app_user(id),
  slot_at timestamptz NOT NULL CHECK (extract(epoch FROM slot_at) % 1800 = 0),
  reason varchar(500) NOT NULL CHECK (length(trim(reason)) > 0),
  status varchar(12) NOT NULL DEFAULT 'requested' CHECK (status IN ('requested','confirmed','completed','cancelled')),
  requested_by uuid NOT NULL REFERENCES app_user(id),
  encounter_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (encounter_id, case_id) REFERENCES encounter(id, case_id)
);
CREATE UNIQUE INDEX ux_appointment_doctor_slot ON appointment(doctor_id, slot_at)
  WHERE status IN ('requested','confirmed');
CREATE UNIQUE INDEX ux_appointment_patient_slot ON appointment(case_id, slot_at)
  WHERE status IN ('requested','confirmed');
CREATE INDEX ix_appointment_case ON appointment(case_id, slot_at DESC);

-- Home entries stay separate from clinician-verified encounter observations.
CREATE TABLE patient_measurement (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL REFERENCES patient_case(id),
  recorded_by uuid NOT NULL REFERENCES patient_account(user_id),
  observed_at timestamptz NOT NULL,
  systolic_bp numeric,
  diastolic_bp numeric,
  heart_rate numeric,
  weight_kg numeric,
  spo2 numeric,
  temperature_c numeric,
  symptoms varchar(500),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (num_nonnulls(systolic_bp, diastolic_bp, heart_rate, weight_kg, spo2, temperature_c, symptoms) > 0),
  CHECK ((systolic_bp IS NULL AND diastolic_bp IS NULL) OR
         (systolic_bp IS NOT NULL AND diastolic_bp IS NOT NULL AND systolic_bp >= diastolic_bp)),
  CHECK (systolic_bp > 0 AND systolic_bp::text NOT IN ('NaN','Infinity','-Infinity')),
  CHECK (diastolic_bp > 0 AND diastolic_bp::text NOT IN ('NaN','Infinity','-Infinity')),
  CHECK (heart_rate > 0 AND heart_rate::text NOT IN ('NaN','Infinity','-Infinity')),
  CHECK (weight_kg > 0 AND weight_kg::text NOT IN ('NaN','Infinity','-Infinity')),
  CHECK (spo2 BETWEEN 0 AND 100 AND spo2::text NOT IN ('NaN','Infinity','-Infinity')),
  CHECK (temperature_c > -273.15 AND temperature_c::text NOT IN ('NaN','Infinity','-Infinity')),
  CHECK (symptoms IS NULL OR length(trim(symptoms)) > 0)
);
CREATE INDEX ix_patient_measurement_time ON patient_measurement(case_id, observed_at DESC);

CREATE TABLE audit_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id uuid REFERENCES app_user(id),
  actor_kind varchar(10) NOT NULL DEFAULT 'user' CHECK (actor_kind IN ('user','system')),
  action varchar(80) NOT NULL,
  entity_type varchar(40) NOT NULL,
  entity_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK ((actor_kind = 'user' AND actor_id IS NOT NULL) OR (actor_kind = 'system' AND actor_id IS NULL))
);

CREATE INDEX ix_audit_entity_time ON audit_event(entity_type,entity_id,created_at DESC);

CREATE FUNCTION validate_observation() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE t observation_type;
BEGIN
 SELECT * INTO STRICT t FROM observation_type WHERE code=NEW.code;
 IF NEW.status='present' THEN
  IF (t.value_kind='number' AND NEW.value_number IS NULL) OR
     (t.value_kind='boolean' AND NEW.value_boolean IS NULL) OR
     (t.value_kind='text' AND NEW.value_text IS NULL) THEN RAISE EXCEPTION 'Observation type mismatch'; END IF;
  IF NEW.value_number::text IN ('NaN','Infinity','-Infinity') THEN RAISE EXCEPTION 'Non-finite observation'; END IF;
  IF NEW.value_number<t.min_value OR NEW.value_number>t.max_value THEN RAISE EXCEPTION 'Invalid observation domain'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER observation_validate BEFORE INSERT OR UPDATE ON observation FOR EACH ROW EXECUTE FUNCTION validate_observation();
CREATE FUNCTION prevent_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Append-only record'; END $$;
CREATE TRIGGER audit_immutable BEFORE UPDATE OR DELETE ON audit_event FOR EACH ROW EXECUTE FUNCTION prevent_mutation();
CREATE TRIGGER evaluation_immutable BEFORE UPDATE OR DELETE ON evaluation FOR EACH ROW EXECUTE FUNCTION prevent_mutation();
CREATE TRIGGER decision_immutable BEFORE UPDATE OR DELETE ON clinical_decision FOR EACH ROW EXECUTE FUNCTION prevent_mutation();
CREATE TRIGGER patient_account_immutable BEFORE UPDATE OR DELETE ON patient_account FOR EACH ROW EXECUTE FUNCTION prevent_mutation();
CREATE FUNCTION guard_profile_revision() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF (NEW.age, NEW.sex, NEW.synthetic_code, NEW.owner_id) IS DISTINCT FROM
    (OLD.age, OLD.sex, OLD.synthetic_code, OLD.owner_id) THEN NEW.revision := OLD.revision + 1; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER profile_revision BEFORE UPDATE ON patient_case FOR EACH ROW EXECUTE FUNCTION guard_profile_revision();

CREATE FUNCTION protect_observation_catalog() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF (NEW.value_kind, NEW.unit, NEW.min_value, NEW.max_value) IS DISTINCT FROM
    (OLD.value_kind, OLD.unit, OLD.min_value, OLD.max_value) AND
    EXISTS (SELECT 1 FROM observation WHERE code = OLD.code) THEN
   RAISE EXCEPTION 'Create a new observation code to change a catalog definition with recorded values'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER observation_catalog_guard BEFORE UPDATE ON observation_type FOR EACH ROW EXECUTE FUNCTION protect_observation_catalog();
CREATE FUNCTION guard_rule_activation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='INSERT' AND NEW.status <> 'draft' THEN RAISE EXCEPTION 'New rules start draft'; END IF;
 IF TG_OP='UPDATE' AND NEW.status <> OLD.status AND NOT
 ((OLD.status='draft' AND NEW.status='tested') OR
  (OLD.status='tested' AND NEW.status IN ('draft','approved')) OR
  (OLD.status='approved' AND NEW.status IN ('active','retired')) OR
  (OLD.status='active' AND NEW.status='retired')) THEN RAISE EXCEPTION 'Invalid rule status transition'; END IF;
 IF TG_OP='UPDATE' AND OLD.status IN ('tested','approved','active','retired') AND
 (NEW.content_hash<>OLD.content_hash OR NEW.content<>OLD.content OR NEW.source_ref<>OLD.source_ref OR NEW.module<>OLD.module OR NEW.code<>OLD.code OR NEW.version<>OLD.version) THEN
 RAISE EXCEPTION 'Create a new version for changed rule content'; END IF;
 IF NEW.content_hash <> encode(sha256(convert_to(NEW.content::text, 'UTF8')), 'hex') THEN
 RAISE EXCEPTION 'Rule content hash mismatch'; END IF;
 IF NEW.status IN ('approved','active') AND NOT EXISTS
 (SELECT 1 FROM rule_approval WHERE rule_version_id=NEW.id AND approved_content_hash=NEW.content_hash)
 THEN RAISE EXCEPTION 'Verified approval required'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER rule_activation_guard BEFORE INSERT OR UPDATE ON rule_version FOR EACH ROW EXECUTE FUNCTION guard_rule_activation();

CREATE FUNCTION has_role(p_user uuid, p_role text) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS $$
 SELECT EXISTS (SELECT 1 FROM app_user u JOIN user_role r ON r.user_id = u.id
                WHERE u.id = p_user AND u.active AND r.role_code = p_role);
$$;

CREATE FUNCTION can_access_case(p_user uuid, p_case uuid, p_scope text) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS $$
 SELECT (has_role(p_user, 'doctor') AND EXISTS
         (SELECT 1 FROM patient_case WHERE id = p_case AND owner_id = p_user))
 OR (EXISTS (SELECT 1 FROM case_access WHERE case_id = p_case AND user_id = p_user
             AND access_scope = p_scope) AND
     ((p_scope = 'clinical' AND has_role(p_user, 'doctor')) OR
      (p_scope = 'nursing' AND has_role(p_user, 'nurse')) OR
      (p_scope = 'medsafety' AND (has_role(p_user, 'doctor') OR has_role(p_user, 'pharmacist')))));
$$;

CREATE FUNCTION validate_roles() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF (NEW.role_code = 'patient' AND EXISTS
     (SELECT 1 FROM user_role WHERE user_id = NEW.user_id AND role_code <> 'patient')) OR
    (NEW.role_code <> 'patient' AND EXISTS
     (SELECT 1 FROM user_role WHERE user_id = NEW.user_id AND role_code = 'patient')) THEN
   RAISE EXCEPTION 'A patient account must be separate from staff accounts';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER user_role_validate BEFORE INSERT OR UPDATE ON user_role
 FOR EACH ROW EXECUTE FUNCTION validate_roles();

CREATE FUNCTION validate_case_staff() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_TABLE_NAME = 'patient_case' THEN
   IF NOT has_role(NEW.owner_id, 'doctor') THEN RAISE EXCEPTION 'Case owner must be an active doctor'; END IF;
 ELSIF TG_TABLE_NAME = 'encounter' THEN
   IF NOT can_access_case(NEW.doctor_id, NEW.case_id, 'clinical') THEN
     RAISE EXCEPTION 'Encounter doctor has no clinical access to this case'; END IF;
 ELSIF TG_TABLE_NAME = 'case_access' THEN
   IF NOT ((NEW.access_scope = 'clinical' AND has_role(NEW.user_id, 'doctor')) OR
           (NEW.access_scope = 'nursing' AND has_role(NEW.user_id, 'nurse')) OR
           (NEW.access_scope = 'medsafety' AND (has_role(NEW.user_id, 'doctor') OR has_role(NEW.user_id, 'pharmacist')))) THEN
     RAISE EXCEPTION 'Role does not match case access scope'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER case_staff_validate BEFORE INSERT OR UPDATE ON patient_case
 FOR EACH ROW EXECUTE FUNCTION validate_case_staff();
CREATE TRIGGER encounter_staff_validate BEFORE INSERT OR UPDATE ON encounter
 FOR EACH ROW EXECUTE FUNCTION validate_case_staff();
CREATE TRIGGER case_access_validate BEFORE INSERT OR UPDATE ON case_access
 FOR EACH ROW EXECUTE FUNCTION validate_case_staff();

CREATE FUNCTION validate_staff_record() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_case uuid; v_actor uuid;
BEGIN
 v_actor := COALESCE((to_jsonb(NEW)->>'recorded_by')::uuid, (to_jsonb(NEW)->>'imported_by')::uuid);
 IF TG_TABLE_NAME IN ('patient_history','allergy_status','drug_reaction') THEN
   v_case := NEW.case_id;
 ELSE
   SELECT case_id INTO v_case FROM encounter WHERE id = NEW.encounter_id;
 END IF;
 IF can_access_case(v_actor, v_case, 'clinical') THEN RETURN NEW; END IF;
 IF TG_TABLE_NAME IN ('observation','test_report','import_batch') AND can_access_case(v_actor, v_case, 'nursing') THEN RETURN NEW; END IF;
 IF TG_TABLE_NAME = 'clinical_note' THEN
   IF NEW.kind = 'nursing' AND can_access_case(v_actor, v_case, 'nursing') THEN RETURN NEW; END IF;
 END IF;
 RAISE EXCEPTION 'Staff member has no write access for this clinical record';
 RETURN NEW;
END $$;
CREATE TRIGGER observation_staff_validate BEFORE INSERT OR UPDATE ON observation FOR EACH ROW EXECUTE FUNCTION validate_staff_record();
CREATE TRIGGER medication_staff_validate BEFORE INSERT OR UPDATE ON medication FOR EACH ROW EXECUTE FUNCTION validate_staff_record();
CREATE TRIGGER history_staff_validate BEFORE INSERT OR UPDATE ON patient_history FOR EACH ROW EXECUTE FUNCTION validate_staff_record();
CREATE TRIGGER note_staff_validate BEFORE INSERT OR UPDATE ON clinical_note FOR EACH ROW EXECUTE FUNCTION validate_staff_record();
CREATE TRIGGER allergy_staff_validate BEFORE INSERT OR UPDATE ON allergy_status FOR EACH ROW EXECUTE FUNCTION validate_staff_record();
CREATE TRIGGER reaction_staff_validate BEFORE INSERT OR UPDATE ON drug_reaction FOR EACH ROW EXECUTE FUNCTION validate_staff_record();
CREATE TRIGGER report_staff_validate BEFORE INSERT OR UPDATE ON test_report FOR EACH ROW EXECUTE FUNCTION validate_staff_record();
CREATE TRIGGER import_staff_validate BEFORE INSERT OR UPDATE ON import_batch FOR EACH ROW EXECUTE FUNCTION validate_staff_record();

CREATE FUNCTION validate_allergies() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_TABLE_NAME = 'drug_reaction' THEN
   IF NOT EXISTS (SELECT 1 FROM allergy_status WHERE case_id = NEW.case_id AND status = 'known') THEN
     RAISE EXCEPTION 'Reaction requires known allergy/reaction status'; END IF;
 ELSE
   IF NEW.status <> 'known' AND EXISTS (SELECT 1 FROM drug_reaction WHERE case_id = NEW.case_id) THEN
     RAISE EXCEPTION 'Existing reactions cannot be marked none or unknown'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER reaction_status_validate BEFORE INSERT OR UPDATE ON drug_reaction FOR EACH ROW EXECUTE FUNCTION validate_allergies();
CREATE TRIGGER allergy_status_validate BEFORE INSERT OR UPDATE ON allergy_status FOR EACH ROW EXECUTE FUNCTION validate_allergies();

CREATE FUNCTION validate_approval() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM user_permission p JOIN app_user u ON u.id = p.user_id
                WHERE p.user_id = NEW.recorded_by AND u.active AND p.permission_code = 'rule.approve') THEN
   RAISE EXCEPTION 'Explicit clinical rule approval permission required'; END IF;
 IF NOT EXISTS (SELECT 1 FROM rule_version WHERE id = NEW.rule_version_id AND status = 'tested'
                AND content_hash = NEW.approved_content_hash) THEN
   RAISE EXCEPTION 'Approval must match the tested rule content'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER rule_approval_validate BEFORE INSERT ON rule_approval FOR EACH ROW EXECUTE FUNCTION validate_approval();
CREATE TRIGGER rule_approval_immutable BEFORE UPDATE OR DELETE ON rule_approval FOR EACH ROW EXECUTE FUNCTION prevent_mutation();

CREATE FUNCTION guard_required_fields() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_id uuid;
BEGIN
 v_id := CASE WHEN TG_OP = 'DELETE' THEN OLD.rule_version_id ELSE NEW.rule_version_id END;
 IF EXISTS (SELECT 1 FROM rule_version WHERE id = v_id AND status IN ('tested','approved','active','retired')) OR
    (TG_OP = 'UPDATE' AND EXISTS (SELECT 1 FROM rule_version WHERE id = OLD.rule_version_id AND status IN ('tested','approved','active','retired'))) THEN
   RAISE EXCEPTION 'Create a new rule version to change required fields'; END IF;
 IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER required_field_guard BEFORE INSERT OR UPDATE OR DELETE ON rule_required_field FOR EACH ROW EXECUTE FUNCTION guard_required_fields();

CREATE FUNCTION bump_case_revision() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_new uuid; v_old uuid;
BEGIN
 IF TG_OP <> 'DELETE' THEN
   IF TG_TABLE_NAME IN ('patient_history','allergy_status','drug_reaction') THEN v_new := NEW.case_id;
   ELSIF TG_TABLE_NAME = 'encounter' THEN v_new := NEW.case_id;
   ELSE SELECT case_id INTO v_new FROM encounter WHERE id = NEW.encounter_id; END IF;
 END IF;
 IF TG_OP <> 'INSERT' THEN
   IF TG_TABLE_NAME IN ('patient_history','allergy_status','drug_reaction','encounter') THEN v_old := OLD.case_id;
   ELSE SELECT case_id INTO v_old FROM encounter WHERE id = OLD.encounter_id; END IF;
 END IF;
 UPDATE patient_case SET revision = revision + 1 WHERE id = v_new OR id = v_old;
 IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER encounter_revision AFTER INSERT OR UPDATE OR DELETE ON encounter FOR EACH ROW EXECUTE FUNCTION bump_case_revision();
CREATE TRIGGER observation_revision AFTER INSERT OR UPDATE OR DELETE ON observation FOR EACH ROW EXECUTE FUNCTION bump_case_revision();
CREATE TRIGGER medication_revision AFTER INSERT OR UPDATE OR DELETE ON medication FOR EACH ROW EXECUTE FUNCTION bump_case_revision();
CREATE TRIGGER note_revision AFTER INSERT OR UPDATE OR DELETE ON clinical_note FOR EACH ROW EXECUTE FUNCTION bump_case_revision();
CREATE TRIGGER history_revision AFTER INSERT OR UPDATE OR DELETE ON patient_history FOR EACH ROW EXECUTE FUNCTION bump_case_revision();
CREATE TRIGGER allergy_revision AFTER INSERT OR UPDATE OR DELETE ON allergy_status FOR EACH ROW EXECUTE FUNCTION bump_case_revision();
CREATE TRIGGER reaction_revision AFTER INSERT OR UPDATE OR DELETE ON drug_reaction FOR EACH ROW EXECUTE FUNCTION bump_case_revision();
CREATE TRIGGER report_revision AFTER INSERT OR UPDATE OR DELETE ON test_report FOR EACH ROW EXECUTE FUNCTION bump_case_revision();

CREATE FUNCTION validate_evaluation_decision() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_case uuid; v_revision integer; v_encounter uuid;
BEGIN
 IF TG_TABLE_NAME = 'evaluation' THEN
   v_encounter := NEW.encounter_id;
 ELSE SELECT encounter_id INTO v_encounter FROM evaluation WHERE id = NEW.evaluation_id; END IF;
 SELECT c.id, c.revision INTO v_case, v_revision FROM patient_case c
 JOIN encounter e ON e.case_id = c.id WHERE e.id = v_encounter FOR UPDATE OF c;
 IF TG_TABLE_NAME = 'evaluation' THEN
   IF NEW.input_revision <> v_revision THEN RAISE EXCEPTION 'Stale evaluation input revision'; END IF;
   IF NOT can_access_case(NEW.requested_by, v_case, 'clinical') AND NOT can_access_case(NEW.requested_by, v_case, 'medsafety') THEN
     RAISE EXCEPTION 'No evaluation access'; END IF;
 ELSE
   IF NOT can_access_case(NEW.doctor_id, v_case, 'clinical') THEN RAISE EXCEPTION 'Doctor clinical access required'; END IF;
   IF (SELECT input_revision FROM evaluation WHERE id = NEW.evaluation_id) <> v_revision THEN
     RAISE EXCEPTION 'Stale evaluation: evaluate again before deciding'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER evaluation_validate BEFORE INSERT ON evaluation FOR EACH ROW EXECUTE FUNCTION validate_evaluation_decision();
CREATE TRIGGER decision_validate BEFORE INSERT ON clinical_decision FOR EACH ROW EXECUTE FUNCTION validate_evaluation_decision();

CREATE FUNCTION validate_review_plan() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_case uuid; v_encounter uuid;
BEGIN
 IF TG_TABLE_NAME = 'pharmacist_review' THEN
   SELECT e.case_id INTO v_case FROM evaluation v JOIN encounter e ON e.id = v.encounter_id WHERE v.id = NEW.evaluation_id;
   IF NOT has_role(NEW.pharmacist_id, 'pharmacist') OR NOT can_access_case(NEW.pharmacist_id, v_case, 'medsafety') THEN
     RAISE EXCEPTION 'Assigned pharmacist required'; END IF;
 ELSE
   SELECT case_id INTO v_case FROM encounter WHERE id = NEW.encounter_id;
   IF NOT can_access_case(NEW.doctor_id, v_case, 'clinical') THEN RAISE EXCEPTION 'Assigned doctor required'; END IF;
   IF NEW.decision_id IS NOT NULL THEN
     SELECT v.encounter_id INTO v_encounter FROM clinical_decision d JOIN evaluation v ON v.id = d.evaluation_id
       WHERE d.id = NEW.decision_id AND d.action <> 'rejected';
     IF v_encounter IS DISTINCT FROM NEW.encounter_id THEN RAISE EXCEPTION 'Plan decision must belong to this encounter and not be rejected'; END IF;
   END IF;
   NEW.updated_at := now();
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER pharmacist_review_validate BEFORE INSERT OR UPDATE ON pharmacist_review FOR EACH ROW EXECUTE FUNCTION validate_review_plan();
CREATE TRIGGER treatment_plan_validate BEFORE INSERT OR UPDATE ON treatment_plan FOR EACH ROW EXECUTE FUNCTION validate_review_plan();

CREATE FUNCTION guard_prescription() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT can_access_case(NEW.doctor_id, NEW.case_id, 'clinical') THEN RAISE EXCEPTION 'Prescription requires an assigned doctor'; END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_timezone_names WHERE name = NEW.timezone) THEN RAISE EXCEPTION 'Unknown prescription timezone'; END IF;
 IF TG_OP = 'INSERT' AND NEW.status <> 'draft' THEN RAISE EXCEPTION 'Create a draft prescription first'; END IF;
 IF TG_OP = 'UPDATE' THEN
   IF OLD.status <> 'draft' THEN
     IF NEW.status <> 'cancelled' OR OLD.status <> 'confirmed' OR
        (to_jsonb(NEW) - 'status') IS DISTINCT FROM (to_jsonb(OLD) - 'status') THEN
       RAISE EXCEPTION 'Confirmed prescription is immutable; cancel and issue a new prescription'; END IF;
   ELSIF NEW.status = 'cancelled' THEN RAISE EXCEPTION 'Delete or finish a draft instead of cancelling it';
   END IF;
   IF OLD.status = 'draft' AND NEW.status = 'confirmed' THEN
     IF NOT EXISTS (SELECT 1 FROM medication WHERE prescription_id = NEW.id) OR EXISTS
        (SELECT 1 FROM medication m WHERE m.prescription_id = NEW.id AND
         (m.starts_on < NEW.starts_on OR (NEW.ends_on IS NOT NULL AND (m.ends_on IS NULL OR m.ends_on > NEW.ends_on)) OR
          (SELECT count(*) FROM medication_schedule s WHERE s.medication_id = m.id) <> m.frequency_per_day)) THEN
       RAISE EXCEPTION 'Each prescribed medication needs dates within the prescription and one clock time per daily dose'; END IF;
     NEW.confirmed_at := now();
   END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER prescription_guard BEFORE INSERT OR UPDATE ON prescription FOR EACH ROW EXECUTE FUNCTION guard_prescription();

CREATE FUNCTION guard_prescribed_medication() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_rx uuid; v_old_rx uuid;
BEGIN
 IF TG_TABLE_NAME = 'medication' THEN
   IF TG_OP <> 'DELETE' THEN v_rx := NEW.prescription_id; END IF;
   IF TG_OP <> 'INSERT' THEN v_old_rx := OLD.prescription_id; END IF;
 ELSE
   IF TG_OP <> 'DELETE' THEN SELECT prescription_id INTO v_rx FROM medication WHERE id = NEW.medication_id; END IF;
   IF TG_OP <> 'INSERT' THEN SELECT prescription_id INTO v_old_rx FROM medication WHERE id = OLD.medication_id; END IF;
   IF TG_OP <> 'DELETE' AND v_rx IS NULL THEN RAISE EXCEPTION 'Clock times require a prescription medication'; END IF;
 END IF;
 -- Lock the parent so confirming a draft cannot race an item/schedule edit.
 PERFORM id FROM prescription WHERE id IN (v_rx, v_old_rx) ORDER BY id FOR UPDATE;
 IF EXISTS (SELECT 1 FROM prescription WHERE id IN (v_rx, v_old_rx) AND status <> 'draft') THEN
   RAISE EXCEPTION 'Confirmed prescription items and clock times are immutable'; END IF;
 IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER prescribed_medication_guard BEFORE INSERT OR UPDATE OR DELETE ON medication FOR EACH ROW EXECUTE FUNCTION guard_prescribed_medication();
CREATE TRIGGER medication_schedule_guard BEFORE INSERT OR UPDATE OR DELETE ON medication_schedule FOR EACH ROW EXECUTE FUNCTION guard_prescribed_medication();

-- Only the trusted service sets this identity after checking its auth session.
CREATE FUNCTION current_app_user() RETURNS uuid LANGUAGE sql STABLE AS $$
 SELECT NULLIF(current_setting('app.user_id', true), '')::uuid;
$$;
CREATE FUNCTION portal_case_id() RETURNS uuid
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS $$
 SELECT case_id FROM patient_account WHERE user_id = current_app_user() AND has_role(user_id, 'patient');
$$;
CREATE FUNCTION portal_owns_medication(p_medication uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS $$
 SELECT EXISTS (SELECT 1 FROM medication m JOIN prescription p ON p.id = m.prescription_id
                WHERE m.id = p_medication AND p.case_id = portal_case_id() AND p.status IN ('confirmed','cancelled'));
$$;
CREATE FUNCTION portal_owns_schedule(p_schedule uuid) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS $$
 SELECT EXISTS (SELECT 1 FROM medication_schedule WHERE id = p_schedule AND portal_owns_medication(medication_id));
$$;
CREATE FUNCTION portal_doctors() RETURNS TABLE (doctor_id uuid, label text, department_code varchar, department_name text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public AS $$
 SELECT u.id, u.username::text, d.code, d.name FROM app_user u JOIN department d ON d.code = u.department_code
 WHERE u.active AND d.active AND has_role(u.id, 'doctor') AND portal_case_id() IS NOT NULL;
$$;

CREATE FUNCTION validate_patient_measurement() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM patient_account WHERE user_id = NEW.recorded_by AND case_id = NEW.case_id)
 OR NOT has_role(NEW.recorded_by, 'patient') THEN RAISE EXCEPTION 'Patient can only record measurements for their own profile'; END IF;
 IF NEW.observed_at > now() + INTERVAL '5 minutes' THEN RAISE EXCEPTION 'Measurement time is in the future'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER patient_measurement_validate BEFORE INSERT ON patient_measurement FOR EACH ROW EXECUTE FUNCTION validate_patient_measurement();
ALTER FUNCTION validate_patient_measurement() SECURITY DEFINER;
ALTER FUNCTION validate_patient_measurement() SET search_path = pg_catalog, public;
CREATE TRIGGER patient_measurement_immutable BEFORE UPDATE OR DELETE ON patient_measurement FOR EACH ROW EXECUTE FUNCTION prevent_mutation();

CREATE FUNCTION validate_appointment() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT has_role(NEW.doctor_id, 'doctor') THEN RAISE EXCEPTION 'Appointment requires an active doctor'; END IF;
 IF NOT EXISTS (SELECT 1 FROM patient_account WHERE user_id = NEW.requested_by AND case_id = NEW.case_id)
    OR NOT has_role(NEW.requested_by, 'patient') THEN RAISE EXCEPTION 'Appointment requester must own the patient profile'; END IF;
 IF TG_OP = 'INSERT' THEN
   IF NEW.status <> 'requested' OR NEW.slot_at <= now() THEN RAISE EXCEPTION 'Request a future appointment slot'; END IF;
 ELSIF TG_OP = 'UPDATE' THEN
   IF (to_jsonb(NEW) - ARRAY['status','encounter_id']) IS DISTINCT FROM (to_jsonb(OLD) - ARRAY['status','encounter_id']) THEN
     RAISE EXCEPTION 'Appointment details are immutable; cancel and book another slot'; END IF;
   IF NOT ((OLD.status = 'requested' AND NEW.status IN ('confirmed','cancelled')) OR
           (OLD.status = 'confirmed' AND NEW.status IN ('completed','cancelled'))) THEN RAISE EXCEPTION 'Invalid appointment status transition'; END IF;
   IF NEW.encounter_id IS NOT NULL AND NEW.status <> 'completed' THEN RAISE EXCEPTION 'Link encounter when appointment is completed'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER appointment_validate BEFORE INSERT OR UPDATE ON appointment FOR EACH ROW EXECUTE FUNCTION validate_appointment();
ALTER FUNCTION validate_appointment() SECURITY DEFINER;
ALTER FUNCTION validate_appointment() SET search_path = pg_catalog, public;

CREATE FUNCTION validate_reminder() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_rx prescription; v_med medication; v_time time;
BEGIN
 IF TG_OP = 'INSERT' THEN
   SELECT m.* INTO v_med FROM medication m JOIN medication_schedule s ON s.medication_id = m.id WHERE s.id = NEW.schedule_id;
   SELECT * INTO v_rx FROM prescription WHERE id = v_med.prescription_id;
   SELECT dose_time INTO v_time FROM medication_schedule WHERE id = NEW.schedule_id;
   IF v_rx.id IS NULL OR v_rx.status <> 'confirmed' OR NEW.scheduled_on < v_rx.starts_on OR
      NEW.scheduled_on < v_med.starts_on OR NEW.scheduled_on > v_rx.ends_on OR NEW.scheduled_on > v_med.ends_on THEN
     RAISE EXCEPTION 'Reminder must fall within a confirmed prescription'; END IF;
   NEW.due_at := (NEW.scheduled_on + v_time) AT TIME ZONE v_rx.timezone;
   IF NEW.status <> 'pending' THEN RAISE EXCEPTION 'New reminders start pending'; END IF;
 ELSE
   IF (to_jsonb(NEW) - ARRAY['status','responded_at','notified_at']) IS DISTINCT FROM
      (to_jsonb(OLD) - ARRAY['status','responded_at','notified_at']) THEN RAISE EXCEPTION 'Reminder identity and due time are immutable'; END IF;
   IF NEW.status <> OLD.status THEN
     IF OLD.status <> 'pending' OR NEW.status NOT IN ('taken','skipped','cancelled') THEN RAISE EXCEPTION 'Reminder already resolved'; END IF;
     NEW.responded_at := CASE WHEN NEW.status IN ('taken','skipped') THEN now() ELSE NULL END;
   ELSIF NEW.responded_at IS DISTINCT FROM OLD.responded_at THEN RAISE EXCEPTION 'Cannot rewrite reminder response time'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER reminder_validate BEFORE INSERT OR UPDATE ON medication_reminder FOR EACH ROW EXECUTE FUNCTION validate_reminder();

CREATE FUNCTION generate_medication_reminders(p_from date, p_to date) RETURNS integer LANGUAGE plpgsql AS $$
DECLARE v_count integer;
BEGIN
 IF p_from IS NULL OR p_to IS NULL OR p_to < p_from OR p_to - p_from > 30 THEN RAISE EXCEPTION 'Generate between 1 and 31 days per batch'; END IF;
 INSERT INTO medication_reminder (schedule_id, scheduled_on, due_at)
 SELECT s.id, day::date, (day::date + s.dose_time) AT TIME ZONE p.timezone
 FROM medication_schedule s JOIN medication m ON m.id = s.medication_id JOIN prescription p ON p.id = m.prescription_id
 JOIN patient_account a ON a.case_id = p.case_id JOIN app_user u ON u.id = a.user_id
 CROSS JOIN generate_series(p_from::timestamp, p_to::timestamp, INTERVAL '1 day') day
 WHERE p.status = 'confirmed' AND u.active AND day::date >= p.starts_on AND day::date >= m.starts_on
   AND (p.ends_on IS NULL OR day::date <= p.ends_on) AND (m.ends_on IS NULL OR day::date <= m.ends_on)
 ON CONFLICT (schedule_id, scheduled_on) DO NOTHING;
 GET DIAGNOSTICS v_count = ROW_COUNT;
 RETURN v_count;
END $$;
REVOKE ALL ON FUNCTION generate_medication_reminders(date, date) FROM PUBLIC;

CREATE FUNCTION cancel_prescription_reminders() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.status = 'cancelled' AND OLD.status = 'confirmed' THEN
   UPDATE medication_reminder r SET status = 'cancelled' FROM medication_schedule s JOIN medication m ON m.id = s.medication_id
   WHERE r.schedule_id = s.id AND m.prescription_id = NEW.id AND r.status = 'pending';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER prescription_cancel_reminders AFTER UPDATE ON prescription FOR EACH ROW EXECUTE FUNCTION cancel_prescription_reminders();

CREATE FUNCTION audit_record_change() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_actor uuid; v_row jsonb; v_entity uuid;
BEGIN
 v_row := CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE to_jsonb(NEW) END;
 v_entity := COALESCE((v_row->>'id')::uuid, (v_row->>'case_id')::uuid,
                      (v_row->>'user_id')::uuid, (v_row->>'rule_version_id')::uuid);
 v_actor := current_app_user();
 IF v_actor IS NULL THEN
   v_actor := COALESCE((v_row->>'recorded_by')::uuid, (v_row->>'requested_by')::uuid,
                       (v_row->>'doctor_id')::uuid, (v_row->>'created_by')::uuid,
                       (v_row->>'pharmacist_id')::uuid, (v_row->>'imported_by')::uuid,
                       (v_row->>'owner_id')::uuid);
   IF TG_TABLE_NAME = 'medication_schedule' THEN
     SELECT recorded_by INTO v_actor FROM medication WHERE id = (v_row->>'medication_id')::uuid;
   END IF;
 END IF;
 INSERT INTO audit_event(actor_id, actor_kind, action, entity_type, entity_id)
 VALUES (v_actor, CASE WHEN v_actor IS NULL THEN 'system' ELSE 'user' END,
         TG_TABLE_NAME || '.' || lower(TG_OP), TG_TABLE_NAME, v_entity);
 IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END $$;
-- Definer permits a constrained patient DB role to append audit rows, never edit them.
ALTER FUNCTION audit_record_change() SECURITY DEFINER;
ALTER FUNCTION audit_record_change() SET search_path = pg_catalog, public;
CREATE TRIGGER appointment_audit AFTER INSERT OR UPDATE ON appointment FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER measurement_audit AFTER INSERT ON patient_measurement FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER prescription_audit AFTER INSERT OR UPDATE ON prescription FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER reminder_audit AFTER INSERT OR UPDATE ON medication_reminder FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER user_audit AFTER INSERT OR UPDATE OR DELETE ON app_user FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER role_audit AFTER INSERT OR UPDATE OR DELETE ON user_role FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER permission_audit AFTER INSERT OR UPDATE OR DELETE ON user_permission FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER access_audit AFTER INSERT OR UPDATE OR DELETE ON case_access FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER case_audit AFTER INSERT OR UPDATE ON patient_case FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER encounter_audit AFTER INSERT OR UPDATE OR DELETE ON encounter FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER observation_audit AFTER INSERT OR UPDATE OR DELETE ON observation FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER medication_audit AFTER INSERT OR UPDATE OR DELETE ON medication FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER dose_time_audit AFTER INSERT OR UPDATE OR DELETE ON medication_schedule FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER history_audit AFTER INSERT OR UPDATE OR DELETE ON patient_history FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER note_audit AFTER INSERT OR UPDATE OR DELETE ON clinical_note FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER allergy_audit AFTER INSERT OR UPDATE OR DELETE ON allergy_status FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER reaction_audit AFTER INSERT OR UPDATE OR DELETE ON drug_reaction FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER report_audit AFTER INSERT OR UPDATE OR DELETE ON test_report FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER import_audit AFTER INSERT OR UPDATE ON import_batch FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER evaluation_audit AFTER INSERT ON evaluation FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER decision_audit AFTER INSERT ON clinical_decision FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER review_audit AFTER INSERT OR UPDATE ON pharmacist_review FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER plan_audit AFTER INSERT OR UPDATE ON treatment_plan FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER rule_audit AFTER INSERT OR UPDATE ON rule_version FOR EACH ROW EXECUTE FUNCTION audit_record_change();
CREATE TRIGGER approval_audit AFTER INSERT ON rule_approval FOR EACH ROW EXECUTE FUNCTION audit_record_change();

ALTER TABLE appointment ENABLE ROW LEVEL SECURITY;
CREATE POLICY patient_appointment_read ON appointment FOR SELECT USING (case_id = portal_case_id());
CREATE POLICY patient_appointment_create ON appointment FOR INSERT
 WITH CHECK (case_id = portal_case_id() AND requested_by = current_app_user() AND status = 'requested' AND encounter_id IS NULL);
CREATE POLICY patient_appointment_cancel ON appointment FOR UPDATE
 USING (case_id = portal_case_id() AND status IN ('requested','confirmed'))
 WITH CHECK (case_id = portal_case_id() AND status = 'cancelled');
ALTER TABLE patient_measurement ENABLE ROW LEVEL SECURITY;
CREATE POLICY patient_measurement_read ON patient_measurement FOR SELECT USING (case_id = portal_case_id());
CREATE POLICY patient_measurement_create ON patient_measurement FOR INSERT
 WITH CHECK (case_id = portal_case_id() AND recorded_by = current_app_user());
ALTER TABLE prescription ENABLE ROW LEVEL SECURITY;
CREATE POLICY patient_prescription_read ON prescription FOR SELECT
 USING (case_id = portal_case_id() AND status IN ('confirmed','cancelled'));
ALTER TABLE medication ENABLE ROW LEVEL SECURITY;
CREATE POLICY patient_medication_read ON medication FOR SELECT USING (portal_owns_medication(id));
ALTER TABLE medication_schedule ENABLE ROW LEVEL SECURITY;
CREATE POLICY patient_schedule_read ON medication_schedule FOR SELECT USING (portal_owns_medication(medication_id));
ALTER TABLE medication_reminder ENABLE ROW LEVEL SECURITY;
CREATE POLICY patient_reminder_read ON medication_reminder FOR SELECT USING (portal_owns_schedule(schedule_id));
CREATE POLICY patient_reminder_respond ON medication_reminder FOR UPDATE
 USING (portal_owns_schedule(schedule_id) AND status = 'pending')
 WITH CHECK (portal_owns_schedule(schedule_id) AND status IN ('taken','skipped'));

CREATE VIEW patient_prescription_view WITH (security_invoker = true) AS
 SELECT p.id AS prescription_id, p.case_id, p.status, p.starts_on, p.ends_on, p.timezone,
        p.instructions AS prescription_instructions, m.id AS medication_id, i.display_name AS ingredient,
        d.display_name AS drug_product, m.dose, m.dose_unit, m.route, m.frequency_per_day,
        m.starts_on AS medication_starts_on, m.ends_on AS medication_ends_on, m.instructions,
        ARRAY(SELECT dose_time FROM medication_schedule WHERE medication_id = m.id ORDER BY dose_time) AS dose_times
 FROM prescription p JOIN medication m ON m.prescription_id = p.id JOIN ingredient i ON i.code = m.ingredient_code
 LEFT JOIN drug_product d ON d.code = m.drug_product_code;

CREATE VIEW patient_reminder_view WITH (security_invoker = true) AS
 SELECT r.id, p.case_id, p.id AS prescription_id, m.id AS medication_id, i.display_name AS ingredient,
        m.dose, m.dose_unit, m.instructions, s.dose_time, s.instructions AS dose_instructions, p.timezone,
        r.scheduled_on, r.due_at, r.status, r.responded_at
 FROM medication_reminder r JOIN medication_schedule s ON s.id = r.schedule_id
 JOIN medication m ON m.id = s.medication_id JOIN prescription p ON p.id = m.prescription_id
 JOIN ingredient i ON i.code = m.ingredient_code;
COMMIT;
