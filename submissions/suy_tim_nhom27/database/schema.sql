-- PostgreSQL 16+. Run once on an empty database. No DROP statements.

BEGIN;

CREATE TABLE app_user (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  username varchar(80) NOT NULL UNIQUE,
  password_hash text NOT NULL,
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE role (
  code varchar(20) PRIMARY KEY CHECK (code IN ('doctor','pharmacist','admin'))
);

CREATE TABLE user_role (
  user_id uuid NOT NULL REFERENCES app_user(id),
  role_code varchar(20) NOT NULL REFERENCES role(code) ,
  PRIMARY KEY(user_id,role_code)
);

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

CREATE TABLE case_access (
  case_id uuid NOT NULL REFERENCES patient_case(id),
  user_id uuid NOT NULL REFERENCES app_user(id),
  access_scope varchar(20) NOT NULL CHECK(access_scope IN ('clinical','medsafety')) ,
  PRIMARY KEY(case_id,user_id,access_scope)
);

CREATE TABLE encounter (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id uuid NOT NULL REFERENCES patient_case(id),
  occurred_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ix_encounter_case_time ON encounter(case_id,occurred_at DESC);

CREATE TABLE observation_type (
  code varchar(60) PRIMARY KEY,
  label text NOT NULL,
  value_kind varchar(10) NOT NULL CHECK(value_kind IN ('number','boolean','text')),
  unit varchar(40) ,
  min_value numeric ,
  max_value numeric  ,
  CHECK(min_value IS NULL OR max_value IS NULL OR min_value<=max_value)
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
  source varchar(30) NOT NULL CHECK(source IN ('manual_synthetic','mock_his','mock_lis','mock_pacs')),
  recorded_by uuid NOT NULL REFERENCES app_user(id),
  created_at timestamptz NOT NULL DEFAULT now() ,
  CHECK ((status = 'present' AND num_nonnulls(value_number,value_boolean,value_text)=1) OR (status<>'present' AND num_nonnulls(value_number,value_boolean,value_text)=0))
);

CREATE INDEX ix_observation_latest ON observation(encounter_id,code,observed_at DESC);

CREATE TABLE ingredient (
  code varchar(60) PRIMARY KEY,
  display_name text NOT NULL
);

CREATE TABLE medication (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  encounter_id uuid NOT NULL REFERENCES encounter(id),
  ingredient_code varchar(60) NOT NULL REFERENCES ingredient(code),
  dose numeric NOT NULL CHECK(dose>0),
  dose_unit varchar(10) NOT NULL CHECK(dose_unit IN ('mg','mcg','g','mL')),
  route varchar(10) NOT NULL CHECK(route IN ('oral','iv','other')),
  frequency_per_day smallint NOT NULL CHECK(frequency_per_day BETWEEN 1 AND 24),
  kind varchar(10) NOT NULL CHECK(kind IN ('current','proposed')),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ix_medication_encounter ON medication(encounter_id);

CREATE TABLE rule_version (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code varchar(60) NOT NULL,
  version integer NOT NULL CHECK(version>0),
  module varchar(20) NOT NULL CHECK(module IN ('diagnosis','lab_test','treatment','medsafety')),
  source_ref text NOT NULL,
  content_hash varchar(64) NOT NULL CHECK(content_hash ~ '^[a-f0-9]{64}$'),
  status varchar(12) NOT NULL CHECK(status IN ('draft','tested','approved','active','retired')),
  created_by uuid NOT NULL REFERENCES app_user(id),
  created_at timestamptz NOT NULL DEFAULT now() ,
  UNIQUE(code,version)
);

CREATE UNIQUE INDEX ux_rule_active ON rule_version(code) WHERE status='active';

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
  created_at timestamptz NOT NULL DEFAULT now()
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
  created_at timestamptz NOT NULL DEFAULT now() ,
  CHECK(action='accepted' OR length(trim(coalesce(reason,'')))>0)
);

CREATE TABLE audit_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id uuid NOT NULL REFERENCES app_user(id),
  action varchar(80) NOT NULL,
  entity_type varchar(40) NOT NULL,
  entity_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
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
CREATE FUNCTION guard_rule_activation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='UPDATE' AND OLD.status IN ('approved','active','retired') AND
 (NEW.content_hash<>OLD.content_hash OR NEW.source_ref<>OLD.source_ref OR NEW.module<>OLD.module OR NEW.code<>OLD.code OR NEW.version<>OLD.version) THEN
 RAISE EXCEPTION 'Create a new version for changed rule content'; END IF;
 IF NEW.status IN ('approved','active') AND NOT EXISTS
 (SELECT 1 FROM rule_approval WHERE rule_version_id=NEW.id AND approved_content_hash=NEW.content_hash)
 THEN RAISE EXCEPTION 'Verified approval required'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER rule_activation_guard BEFORE INSERT OR UPDATE ON rule_version FOR EACH ROW EXECUTE FUNCTION guard_rule_activation();
COMMIT;