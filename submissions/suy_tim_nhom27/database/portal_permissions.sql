-- Run as the schema owner with CREATEROLE (the demo Docker postgres user qualifies).
-- This role cannot log in; the trusted backend switches to it within a transaction.
BEGIN;
DO $$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hf_patient_portal') THEN
   CREATE ROLE hf_patient_portal NOLOGIN NOSUPERUSER NOBYPASSRLS;
 END IF;
 IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hf_patient_portal' AND (rolsuper OR rolbypassrls OR rolcanlogin)) OR
    EXISTS (SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid = m.member WHERE r.rolname = 'hf_patient_portal') OR
    EXISTS (SELECT 1 FROM pg_class c JOIN pg_roles r ON r.oid = c.relowner WHERE r.rolname = 'hf_patient_portal') THEN
   RAISE EXCEPTION 'hf_patient_portal must be NOLOGIN, non-owner, without bypass or inherited role memberships';
 END IF;
END $$;
GRANT USAGE ON SCHEMA public TO hf_patient_portal;
GRANT SELECT ON appointment, patient_measurement, prescription, medication, medication_schedule,
 medication_reminder, ingredient, drug_product, patient_prescription_view, patient_reminder_view TO hf_patient_portal;
GRANT INSERT (case_id, doctor_id, slot_at, reason, requested_by) ON appointment TO hf_patient_portal;
GRANT UPDATE (status) ON appointment TO hf_patient_portal;
GRANT INSERT (case_id, recorded_by, observed_at, systolic_bp, diastolic_bp, heart_rate, weight_kg,
 spo2, temperature_c, symptoms) ON patient_measurement TO hf_patient_portal;
GRANT UPDATE (status) ON medication_reminder TO hf_patient_portal;
GRANT EXECUTE ON FUNCTION current_app_user(), portal_case_id(), portal_owns_medication(uuid),
 portal_owns_schedule(uuid), portal_doctors() TO hf_patient_portal;
-- No grants on app_user/password hashes, audit, clinical tables or rule management.
COMMIT;
