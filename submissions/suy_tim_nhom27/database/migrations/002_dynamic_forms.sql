-- Additive migration. Run as the existing hf_demo_owner; never reset the DB.
BEGIN;
CREATE TABLE IF NOT EXISTS form_schema_migration (version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS form_catalog (id integer PRIMARY KEY CHECK(id=1), revision integer NOT NULL DEFAULT 1);
INSERT INTO form_catalog(id) VALUES(1) ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS form_field (
 code varchar(80) PRIMARY KEY, definition jsonb NOT NULL, version integer NOT NULL DEFAULT 1,
 updated_by uuid REFERENCES app_user(id), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS form_field_history (
 code varchar(80) REFERENCES form_field(code), version integer NOT NULL,
 definition jsonb NOT NULL, actor_id uuid REFERENCES app_user(id), created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(code, version)
);
-- Draft profiles do not invent age/sex or require a clinician's completed legacy case.
-- Optional legacy link preserves a route into the existing clinical modules later.
CREATE TABLE IF NOT EXISTS form_patient (
 id uuid PRIMARY KEY, code text NOT NULL UNIQUE, external_id text UNIQUE,
 display_name text, owner_id uuid NOT NULL REFERENCES app_user(id),
 legacy_case_id uuid UNIQUE REFERENCES patient_case(id), created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS form_access (
 patient_id uuid REFERENCES form_patient(id), user_id uuid REFERENCES app_user(id),
 PRIMARY KEY(patient_id,user_id)
);
CREATE TABLE IF NOT EXISTS form_visit (
 id uuid PRIMARY KEY, patient_id uuid NOT NULL REFERENCES form_patient(id), external_id text,
 occurred_at timestamptz, created_by uuid NOT NULL REFERENCES app_user(id),
 revision integer NOT NULL DEFAULT 0, values_json jsonb NOT NULL DEFAULT '{}',
 sources_json jsonb NOT NULL DEFAULT '{}', updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(patient_id,external_id)
);
CREATE TABLE IF NOT EXISTS form_history (
 visit_id uuid REFERENCES form_visit(id), revision integer NOT NULL,
 mutation_id uuid NOT NULL, request_hash text NOT NULL, actor_id uuid NOT NULL REFERENCES app_user(id),
 values_json jsonb NOT NULL, sources_json jsonb NOT NULL, definitions_json jsonb NOT NULL,
 catalog_revision integer NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(visit_id,revision), UNIQUE(visit_id,mutation_id)
);
CREATE INDEX IF NOT EXISTS ix_form_patient_owner ON form_patient(owner_id);
CREATE INDEX IF NOT EXISTS ix_form_visit_patient ON form_visit(patient_id);
CREATE INDEX IF NOT EXISTS ix_form_field_actor ON form_field(updated_by);
CREATE INDEX IF NOT EXISTS ix_form_field_history_actor ON form_field_history(actor_id);
CREATE INDEX IF NOT EXISTS ix_form_access_user ON form_access(user_id);
CREATE INDEX IF NOT EXISTS ix_form_visit_creator ON form_visit(created_by);
CREATE INDEX IF NOT EXISTS ix_form_history_actor ON form_history(actor_id);
INSERT INTO form_schema_migration(version) VALUES('002_dynamic_forms') ON CONFLICT DO NOTHING;
COMMIT;

-- DOWN (operator-reviewed, disposable schema or after data export):
-- DROP TABLE form_history, form_visit, form_access, form_patient, form_field_history, form_field, form_catalog;
-- DELETE FROM form_schema_migration WHERE version = '002_dynamic_forms';
