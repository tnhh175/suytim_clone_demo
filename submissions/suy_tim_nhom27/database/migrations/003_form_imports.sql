-- Additive; same owner and schema search_path as migration 002. No source file blobs.
BEGIN;
CREATE TABLE IF NOT EXISTS form_import_batch (
 id uuid PRIMARY KEY,
 actor_id uuid NOT NULL REFERENCES app_user(id),
 source_kind text NOT NULL CHECK(source_kind IN ('excel','json')),
 content_hash text NOT NULL,
 mapping jsonb NOT NULL CHECK(jsonb_typeof(mapping)='object'),
 mapping_version text NOT NULL DEFAULT '1.0',
 result jsonb NOT NULL CHECK(jsonb_typeof(result)='object'),
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(actor_id, content_hash)
);
INSERT INTO form_schema_migration(version) VALUES('003_form_imports') ON CONFLICT DO NOTHING;
COMMIT;
-- DOWN (operator-reviewed; preserve audit first):
-- DROP TABLE form_import_batch;
-- DELETE FROM form_schema_migration WHERE version='003_form_imports';
