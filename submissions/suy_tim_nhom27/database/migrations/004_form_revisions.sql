-- Additive migration for approved revision v1.0 (25/10/2026).
-- Run with hf_demo_owner and an explicitly selected d3_form_ sandbox search_path.
-- Stop the application while migrating: the patient-code allocation needs a short lock.
BEGIN;
DO $$ BEGIN
 IF current_schema() !~ '^d3_form_' THEN RAISE EXCEPTION 'Dedicated forms schema required'; END IF;
END $$;
LOCK TABLE form_patient IN SHARE ROW EXCLUSIVE MODE;
CREATE SEQUENCE IF NOT EXISTS form_patient_code_seq MINVALUE 1 MAXVALUE 99999 NO CYCLE;
CREATE TABLE IF NOT EXISTS form_patient_alias (
 alias text PRIMARY KEY, patient_id uuid NOT NULL REFERENCES form_patient(id),
 origin text NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_form_patient_alias_patient ON form_patient_alias(patient_id);
ALTER TABLE form_patient ADD COLUMN IF NOT EXISTS date_of_birth date;
ALTER TABLE form_patient ADD COLUMN IF NOT EXISTS sex text CHECK(sex IN ('male','female','other'));
ALTER TABLE form_patient ADD COLUMN IF NOT EXISTS insurance_number text;
ALTER TABLE form_patient ADD COLUMN IF NOT EXISTS demographic_revision integer NOT NULL DEFAULT 0;
ALTER TABLE form_patient ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
CREATE TABLE IF NOT EXISTS form_patient_history (
 patient_id uuid NOT NULL REFERENCES form_patient(id), revision integer NOT NULL,
 mutation_id uuid NOT NULL, request_hash text NOT NULL, actor_id uuid NOT NULL REFERENCES app_user(id),
 before_json jsonb NOT NULL, after_json jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(patient_id,revision), UNIQUE(patient_id,mutation_id)
);
CREATE INDEX IF NOT EXISTS ix_form_patient_history_actor ON form_patient_history(actor_id);
-- Preserve EVERY old code as an unambiguous identity alias before changing display codes.
INSERT INTO form_patient_alias(alias,patient_id,origin)
 SELECT code,id,'pre_004_display_code' FROM form_patient WHERE code !~ '^BN-[0-9]{5}$'
 ON CONFLICT DO NOTHING;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM form_patient p JOIN form_patient_alias a ON a.alias=p.code
           WHERE p.code !~ '^BN-[0-9]{5}$' AND a.patient_id<>p.id) THEN
   RAISE EXCEPTION 'Legacy patient code alias collision; reconcile explicitly before migration';
 END IF;
END $$;
DO $$ DECLARE p record; highest bigint; allocated bigint; BEGIN
 SELECT greatest(coalesce(max(substring(code FROM 4)::bigint),0),
   (SELECT CASE WHEN is_called THEN last_value ELSE 0 END FROM form_patient_code_seq))
 INTO highest FROM form_patient WHERE code ~ '^BN-[0-9]{5}$';
 IF highest > 0 THEN PERFORM setval('form_patient_code_seq',highest,true); END IF;
 FOR p IN SELECT id,code FROM form_patient WHERE code !~ '^BN-[0-9]{5}$' ORDER BY created_at,id LOOP
   LOOP
     allocated := nextval('form_patient_code_seq');
     EXIT WHEN NOT EXISTS(SELECT 1 FROM form_patient_alias WHERE alias='BN-'||lpad(allocated::text,5,'0'));
   END LOOP;
   UPDATE form_patient SET code='BN-'||lpad(allocated::text,5,'0') WHERE id=p.id;
 END LOOP;
END $$;
ALTER TABLE form_visit ADD COLUMN IF NOT EXISTS catalog_revision integer;
ALTER TABLE form_visit ADD COLUMN IF NOT EXISTS definitions_json jsonb;
ALTER TABLE form_visit ADD COLUMN IF NOT EXISTS demographics_snapshot jsonb;
ALTER TABLE form_visit ADD COLUMN IF NOT EXISTS snapshot_origin text;
ALTER TABLE form_visit ADD COLUMN IF NOT EXISTS metadata_json jsonb NOT NULL DEFAULT '{}';
ALTER TABLE form_visit ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now();
-- Last saved catalog is the evidence for the CURRENT legacy values, including
-- fields added after the first save. Creation-time catalogs cannot be recovered
-- reliably for pre-migration visits; old history snapshots stay untouched.
-- Empty drafts freeze migration-time catalog; all NEW visits pin at creation.
UPDATE form_visit v SET catalog_revision=coalesce((SELECT h.catalog_revision FROM form_history h WHERE h.visit_id=v.id ORDER BY h.revision DESC LIMIT 1),c.revision),
 definitions_json=coalesce((SELECT h.definitions_json FROM form_history h WHERE h.visit_id=v.id ORDER BY h.revision DESC LIMIT 1),
   (SELECT jsonb_object_agg(code,definition||jsonb_build_object('version',version)) FROM form_field),'{}'),
 demographics_snapshot=jsonb_build_object('display_name',p.display_name,'date_of_birth',p.date_of_birth,'sex',p.sex,'insurance_number',p.insurance_number),
 snapshot_origin=CASE WHEN EXISTS(SELECT 1 FROM form_history h WHERE h.visit_id=v.id) THEN 'migration_004_last_saved_catalog' ELSE 'migration_004_current_catalog' END
 FROM form_catalog c,form_patient p WHERE c.id=1 AND p.id=v.patient_id
 AND (v.definitions_json IS NULL OR v.snapshot_origin='migration_004_first_saved_catalog');
ALTER TABLE form_visit ALTER COLUMN catalog_revision SET NOT NULL;
ALTER TABLE form_visit ALTER COLUMN definitions_json SET NOT NULL;
ALTER TABLE form_visit ALTER COLUMN demographics_snapshot SET NOT NULL;
ALTER TABLE form_visit ALTER COLUMN snapshot_origin SET NOT NULL;
ALTER TABLE form_history ADD COLUMN IF NOT EXISTS metadata_json jsonb;
ALTER TABLE form_history ADD COLUMN IF NOT EXISTS occurred_at timestamptz;
CREATE INDEX IF NOT EXISTS ix_form_visit_patient_occurred ON form_visit(patient_id,occurred_at DESC NULLS LAST,created_at DESC);
CREATE TABLE IF NOT EXISTS form_import_preset (
 id uuid PRIMARY KEY, actor_id uuid NOT NULL REFERENCES app_user(id), name text NOT NULL,
 source_name text NOT NULL, mapping jsonb NOT NULL, revision integer NOT NULL DEFAULT 1,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(actor_id,source_name,name)
);
-- A05 source TL06 rows 45/47: record the known boolean condition separately
-- from unresolved HbA1c/eGFR. Apply AFTER legacy snapshots; never upgrade them.
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM form_schema_migration WHERE version='004_form_revisions') THEN
   UPDATE form_field SET version=version+1,updated_at=now(),definition=definition||jsonb_build_object(
     'type','boolean','implementation_status','supported_condition_only',
     'help','Ghi nhận tình trạng đã biết: Có/Không/Chưa có dữ liệu. Không tính hoặc suy ra từ HbA1c/eGFR; thành phần xét nghiệm còn chờ đặc tả.')
     WHERE code IN ('dai_thao_duong','benh_than_man') AND definition->>'type'='unavailable';
   INSERT INTO form_field_history(code,version,definition)
     SELECT code,version,definition FROM form_field WHERE code IN ('dai_thao_duong','benh_than_man') ON CONFLICT DO NOTHING;
   UPDATE form_catalog SET revision=revision+1 WHERE id=1;
 END IF;
END $$;
INSERT INTO form_schema_migration(version) VALUES('004_form_revisions') ON CONFLICT DO NOTHING;
COMMIT;
-- DOWN: rollback application deployment only after restoring a verified pre-migration
-- backup into a NEW sandbox and reconciling post-migration writes. Do not drop the
-- new snapshots/history/aliases or undo identifiers in place: that loses provenance.
-- No automatic destructive DOWN is supplied because history must be retained.
