-- Synthetic fixtures only. Run after schema.sql; safe to replay (existing rows are preserved).
-- Password hashes: PBKDF2-SHA256, 600,000 iterations, per-account demo salts.
-- These DB accounts do not change the existing in-memory Gateway login.
BEGIN;
SET LOCAL TIME ZONE 'Asia/Ho_Chi_Minh';

INSERT INTO department(code, name) VALUES
 ('cardiology', 'Khoa Tim mạch giả lập'), ('geriatrics', 'Khoa Lão khoa giả lập') ON CONFLICT DO NOTHING;
INSERT INTO role(code) VALUES ('doctor'), ('nurse'), ('pharmacist'), ('admin'), ('patient') ON CONFLICT DO NOTHING;
INSERT INTO permission(code, description) VALUES ('rule.approve', 'Phê duyệt chuyên môn nội dung quy tắc') ON CONFLICT DO NOTHING;
INSERT INTO app_user(id, username, password_hash, department_code) VALUES
 ('00000000-0000-4000-8000-000000000001', 'doctor_demo', 'pbkdf2_sha256$600000$c3V5dGltLWRlbW8tZG9jdG9y$n51i+8XHfNP98jCWGcjOH13tHQ/ogUe/P9ez8roAdZE=', 'cardiology'),
 ('00000000-0000-4000-8000-000000000002', 'nurse_demo', 'pbkdf2_sha256$600000$c3V5dGltLWRlbW8tbnVyc2U=$/tufb8aU1yehthTksR9FAwyf9pfPLKSKfXxFUiH/df4=', 'cardiology'),
 ('00000000-0000-4000-8000-000000000003', 'pharmacist_demo', 'pbkdf2_sha256$600000$c3V5dGltLWRlbW8tcGhhcm1hY2lzdA==$MLPvoECm3gR4nYZVbh9jIg4VsQA99IpuYXAZE9drUrA=', 'cardiology'),
 ('00000000-0000-4000-8000-000000000004', 'admin_demo', 'pbkdf2_sha256$600000$c3V5dGltLWRlbW8tYWRtaW4=$2dRekQ5bS+V7Y21lxH9Vy/eKMQZZPf3fR3d/ENMRszg=', NULL),
 ('00000000-0000-4000-8000-000000000005', 'patient_demo', 'pbkdf2_sha256$600000$c3V5dGltLWRlbW8tcGF0aWVudA==$Fxr8Qe48xCKdtapu8OcEdLz5vyjvwIxi8qBiOt8fr4Q=', NULL) ON CONFLICT DO NOTHING;
INSERT INTO user_role(user_id, role_code) VALUES
 ('00000000-0000-4000-8000-000000000001', 'doctor'), ('00000000-0000-4000-8000-000000000002', 'nurse'),
 ('00000000-0000-4000-8000-000000000003', 'pharmacist'), ('00000000-0000-4000-8000-000000000004', 'admin'),
 ('00000000-0000-4000-8000-000000000005', 'patient') ON CONFLICT DO NOTHING;
-- Explicit approval permission; never implied by the admin role.
INSERT INTO user_permission(user_id, permission_code) VALUES ('00000000-0000-4000-8000-000000000001', 'rule.approve') ON CONFLICT DO NOTHING;

-- Representation domains, not diagnostic or alert thresholds.
INSERT INTO observation_type(code, label, value_kind, unit, min_value, max_value) VALUES
 ('ef', 'Phân suất tống máu', 'number', '%', 0, 100),
 ('potassium', 'Kali', 'number', 'mmol/L', 0, NULL), ('sodium', 'Natri', 'number', 'mmol/L', 0, NULL),
 ('egfr', 'eGFR', 'number', 'mL/min/1.73m2', 0, NULL), ('creatinine', 'Creatinin', 'number', 'umol/L', 0, NULL),
 ('bnp', 'BNP', 'number', 'pg/mL', 0, NULL), ('nt_probnp', 'NT-proBNP', 'number', 'pg/mL', 0, NULL),
 ('systolic_bp', 'Huyết áp tâm thu', 'number', 'mmHg', 0, NULL), ('diastolic_bp', 'Huyết áp tâm trương', 'number', 'mmHg', 0, NULL),
 ('heart_rate', 'Nhịp tim', 'number', 'bpm', 0, NULL), ('weight_kg', 'Cân nặng', 'number', 'kg', 0, NULL),
 ('height_cm', 'Chiều cao', 'number', 'cm', 0, NULL), ('spo2', 'Độ bão hòa oxy', 'number', '%', 0, 100),
 ('temperature_c', 'Nhiệt độ', 'number', 'degC', -273.15, NULL),
 ('dyspnea', 'Khó thở', 'boolean', NULL, NULL, NULL), ('edema', 'Phù', 'boolean', NULL, NULL, NULL),
 ('fatigue', 'Mệt mỏi', 'boolean', NULL, NULL, NULL), ('frailty', 'Đánh giá frailty', 'text', NULL, NULL, NULL),
 ('cognition', 'Đánh giá nhận thức', 'text', NULL, NULL, NULL), ('adl', 'Sinh hoạt hằng ngày ADL', 'text', NULL, NULL, NULL),
 ('iadl', 'Sinh hoạt có sử dụng công cụ IADL', 'text', NULL, NULL, NULL), ('nutrition', 'Đánh giá dinh dưỡng', 'text', NULL, NULL, NULL),
 ('fall_risk', 'Đánh giá nguy cơ ngã', 'text', NULL, NULL, NULL), ('comorbidity', 'Bệnh đồng mắc', 'text', NULL, NULL, NULL)
ON CONFLICT DO NOTHING;
-- Fictional drugs have no clinical meaning and are not treatment guidance.
INSERT INTO ingredient(code, display_name) VALUES ('synthetic_drug_a', 'Hoạt chất giả lập A'), ('synthetic_drug_b', 'Hoạt chất giả lập B') ON CONFLICT DO NOTHING;
INSERT INTO drug_product(code, ingredient_code, display_name, strength, strength_unit, dosage_form) VALUES
 ('demo_tablet_a', 'synthetic_drug_a', 'Viên thuốc demo A', 1, 'mg', 'tablet'),
 ('demo_tablet_b', 'synthetic_drug_b', 'Viên thuốc demo B', 1, 'mg', 'tablet') ON CONFLICT DO NOTHING;
INSERT INTO patient_case(id, synthetic_code, age, sex, owner_id) VALUES
 ('10000000-0000-4000-8000-000000000001', 'SYN-DEMO-001', 75, 'female', '00000000-0000-4000-8000-000000000001'),
 ('10000000-0000-4000-8000-000000000002', 'SYN-DEMO-002', 80, 'male', '00000000-0000-4000-8000-000000000001') ON CONFLICT DO NOTHING;
INSERT INTO patient_account(user_id, case_id) VALUES ('00000000-0000-4000-8000-000000000005', '10000000-0000-4000-8000-000000000001') ON CONFLICT DO NOTHING;
INSERT INTO case_access(case_id, user_id, access_scope) VALUES
 ('10000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000002', 'nursing'),
 ('10000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000003', 'medsafety') ON CONFLICT DO NOTHING;
INSERT INTO encounter(id, case_id, occurred_at, kind, department_code, doctor_id) VALUES
 ('20000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001', now() - INTERVAL '2 days', 'outpatient', 'cardiology', '00000000-0000-4000-8000-000000000001'),
 ('20000000-0000-4000-8000-000000000002', '10000000-0000-4000-8000-000000000002', now() - INTERVAL '1 day', 'inpatient', 'geriatrics', '00000000-0000-4000-8000-000000000001') ON CONFLICT DO NOTHING;
INSERT INTO patient_history(id, case_id, kind, description, recorded_by) VALUES
 ('30000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001', 'medical', 'Tiền sử giả lập phục vụ luồng demo.', '00000000-0000-4000-8000-000000000001') ON CONFLICT DO NOTHING;
INSERT INTO allergy_status(case_id, status, recorded_by) VALUES
 ('10000000-0000-4000-8000-000000000001', 'unknown', '00000000-0000-4000-8000-000000000001'),
 ('10000000-0000-4000-8000-000000000002', 'none', '00000000-0000-4000-8000-000000000001') ON CONFLICT DO NOTHING;
INSERT INTO clinical_note(id, encounter_id, kind, content, recorded_by) VALUES
 ('31000000-0000-4000-8000-000000000001', '20000000-0000-4000-8000-000000000001', 'nursing', 'Ghi nhận chăm sóc giả lập; các chỉ số được nhập riêng.', '00000000-0000-4000-8000-000000000002'),
 ('31000000-0000-4000-8000-000000000002', '20000000-0000-4000-8000-000000000001', 'examination', 'Khám giả lập, chưa sử dụng để kết luận y khoa.', '00000000-0000-4000-8000-000000000001') ON CONFLICT DO NOTHING;
INSERT INTO observation(id, encounter_id, code, value_number, status, observed_at, source, recorded_by) VALUES
 ('32000000-0000-4000-8000-000000000001', '20000000-0000-4000-8000-000000000001', 'systolic_bp', 120, 'present', now() - INTERVAL '2 days', 'manual_synthetic', '00000000-0000-4000-8000-000000000002'),
 ('32000000-0000-4000-8000-000000000002', '20000000-0000-4000-8000-000000000001', 'diastolic_bp', 80, 'present', now() - INTERVAL '2 days', 'manual_synthetic', '00000000-0000-4000-8000-000000000002'),
 ('32000000-0000-4000-8000-000000000003', '20000000-0000-4000-8000-000000000001', 'heart_rate', 72, 'present', now() - INTERVAL '2 days', 'manual_synthetic', '00000000-0000-4000-8000-000000000002'),
 ('32000000-0000-4000-8000-000000000004', '20000000-0000-4000-8000-000000000001', 'weight_kg', 60, 'present', now() - INTERVAL '2 days', 'manual_synthetic', '00000000-0000-4000-8000-000000000002') ON CONFLICT DO NOTHING;
INSERT INTO test_report(id, encounter_id, kind, performed_at, source, external_ref, content, recorded_by) VALUES
 ('33000000-0000-4000-8000-000000000001', '20000000-0000-4000-8000-000000000001', 'echo', now() - INTERVAL '2 days', 'mock_pacs', 'SYN-ECHO-001', '{"note":"Báo cáo siêu âm giả lập, chưa có kết luận"}', '00000000-0000-4000-8000-000000000001') ON CONFLICT DO NOTHING;
INSERT INTO import_batch(id, encounter_id, source, external_ref, status, accepted_rows, rejected_rows, imported_by) VALUES
 ('34000000-0000-4000-8000-000000000001', '20000000-0000-4000-8000-000000000001', 'file', 'SYN-IMPORT-001', 'partial', 4, 1, '00000000-0000-4000-8000-000000000002') ON CONFLICT DO NOTHING;
INSERT INTO import_error(id, batch_id, row_number, field_code, message) VALUES
 ('35000000-0000-4000-8000-000000000001', '34000000-0000-4000-8000-000000000001', 5, 'weight_kg', 'Dòng giả lập thiếu đơn vị kg.') ON CONFLICT DO NOTHING;

INSERT INTO prescription(id, case_id, encounter_id, doctor_id, starts_on, ends_on, instructions)
SELECT '40000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001', '20000000-0000-4000-8000-000000000001',
 '00000000-0000-4000-8000-000000000001', CURRENT_DATE, CURRENT_DATE + 13, 'Đơn thuốc giả lập để kiểm thử xem đơn và giờ uống; không dùng điều trị.'
WHERE NOT EXISTS (SELECT 1 FROM prescription WHERE id = '40000000-0000-4000-8000-000000000001');
INSERT INTO medication(id, encounter_id, ingredient_code, drug_product_code, prescription_id, dose, dose_unit, route, frequency_per_day, kind, starts_on, ends_on, instructions, recorded_by)
SELECT '41000000-0000-4000-8000-000000000001', '20000000-0000-4000-8000-000000000001', 'synthetic_drug_a', 'demo_tablet_a',
 '40000000-0000-4000-8000-000000000001', 1, 'mg', 'oral', 2, 'current', CURRENT_DATE, CURRENT_DATE + 13,
 'Ví dụ lịch hai lần mỗi ngày cho thuốc giả lập A.', '00000000-0000-4000-8000-000000000001'
WHERE NOT EXISTS (SELECT 1 FROM medication WHERE id = '41000000-0000-4000-8000-000000000001');
INSERT INTO medication(id, encounter_id, ingredient_code, drug_product_code, prescription_id, dose, dose_unit, route, frequency_per_day, kind, starts_on, ends_on, instructions, recorded_by)
SELECT '41000000-0000-4000-8000-000000000002', '20000000-0000-4000-8000-000000000001', 'synthetic_drug_b', 'demo_tablet_b',
 '40000000-0000-4000-8000-000000000001', 1, 'mg', 'oral', 1, 'current', CURRENT_DATE, CURRENT_DATE + 13,
 'Ví dụ lịch một lần mỗi ngày cho thuốc giả lập B.', '00000000-0000-4000-8000-000000000001'
WHERE NOT EXISTS (SELECT 1 FROM medication WHERE id = '41000000-0000-4000-8000-000000000002');
INSERT INTO medication_schedule(id, medication_id, dose_time, instructions)
SELECT v.id::uuid, v.medication_id::uuid, v.dose_time::time, v.instructions FROM (VALUES
 ('42000000-0000-4000-8000-000000000001', '41000000-0000-4000-8000-000000000001', '08:00', 'Giờ uống sáng demo'),
 ('42000000-0000-4000-8000-000000000002', '41000000-0000-4000-8000-000000000001', '20:00', 'Giờ uống tối demo'),
 ('42000000-0000-4000-8000-000000000003', '41000000-0000-4000-8000-000000000002', '12:00', 'Giờ uống trưa demo')
) v(id, medication_id, dose_time, instructions) WHERE NOT EXISTS (SELECT 1 FROM medication_schedule WHERE id = v.id::uuid);
UPDATE prescription SET status = 'confirmed' WHERE id = '40000000-0000-4000-8000-000000000001' AND status = 'draft';

-- Draft rules and mock results demonstrate persistence, not clinical correctness.
INSERT INTO rule_version(id, code, version, module, source_ref, content, content_hash, created_by)
SELECT '50000000-0000-4000-8000-000000000001', 'SYN_DEMO_DIAGNOSIS', 1, 'diagnosis', 'Synthetic fixture; no clinical rule',
 '{"mode":"stub","description":"Not clinically evaluated"}'::jsonb,
 encode(sha256(convert_to('{"mode":"stub","description":"Not clinically evaluated"}'::jsonb::text, 'UTF8')), 'hex'), '00000000-0000-4000-8000-000000000004'
WHERE NOT EXISTS (SELECT 1 FROM rule_version WHERE id = '50000000-0000-4000-8000-000000000001');
INSERT INTO rule_required_field(rule_version_id, field_code)
SELECT '50000000-0000-4000-8000-000000000001', 'ef'
WHERE NOT EXISTS (SELECT 1 FROM rule_required_field WHERE rule_version_id = '50000000-0000-4000-8000-000000000001' AND field_code = 'ef');
INSERT INTO evaluation(id, encounter_id, input_revision, input_snapshot, requested_by, mode)
SELECT '51000000-0000-4000-8000-000000000001', e.id, c.revision,
 jsonb_build_object('case', to_jsonb(c), 'encounter', to_jsonb(e),
   'observations', (SELECT coalesce(jsonb_agg(to_jsonb(o)), '[]') FROM observation o WHERE o.encounter_id = e.id),
   'medications', (SELECT coalesce(jsonb_agg(to_jsonb(m)), '[]') FROM medication m WHERE m.encounter_id = e.id)), '00000000-0000-4000-8000-000000000001', 'stub'
FROM encounter e JOIN patient_case c ON c.id = e.case_id WHERE e.id = '20000000-0000-4000-8000-000000000001'
AND NOT EXISTS (SELECT 1 FROM evaluation WHERE id = '51000000-0000-4000-8000-000000000001');
INSERT INTO module_result(id, evaluation_id, module, status, message) VALUES
 ('52000000-0000-4000-8000-000000000001', '51000000-0000-4000-8000-000000000001', 'diagnosis', 'mock_not_evaluated', 'Stub; không có kết luận chẩn đoán.'),
 ('52000000-0000-4000-8000-000000000002', '51000000-0000-4000-8000-000000000001', 'lab_test', 'mock_not_evaluated', 'Stub; chưa gợi ý cận lâm sàng.'),
 ('52000000-0000-4000-8000-000000000003', '51000000-0000-4000-8000-000000000001', 'treatment', 'mock_not_evaluated', 'Stub; không tự tạo đơn thuốc.'),
 ('52000000-0000-4000-8000-000000000004', '51000000-0000-4000-8000-000000000001', 'medsafety', 'mock_not_evaluated', 'Stub; chưa đánh giá an toàn thuốc.') ON CONFLICT DO NOTHING;
INSERT INTO result_missing_field(module_result_id, field_code) VALUES ('52000000-0000-4000-8000-000000000001', 'ef') ON CONFLICT DO NOTHING;
INSERT INTO pharmacist_review(id, evaluation_id, pharmacist_id, comment, proposal) VALUES
 ('53000000-0000-4000-8000-000000000001', '51000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000003',
 'Nhận xét giả lập; chưa xác nhận đánh giá thuốc.', 'Bác sĩ xem xét hồ sơ trước khi đưa ra quyết định.') ON CONFLICT DO NOTHING;
INSERT INTO clinical_decision(id, evaluation_id, doctor_id, action, reason)
SELECT '54000000-0000-4000-8000-000000000001', '51000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000001', 'rejected', 'Kết quả stub chưa được đánh giá chuyên môn.'
WHERE NOT EXISTS (SELECT 1 FROM clinical_decision WHERE id = '54000000-0000-4000-8000-000000000001');
INSERT INTO treatment_plan(id, encounter_id, doctor_id, kind, content, follow_up_at, status) VALUES
 ('55000000-0000-4000-8000-000000000001', '20000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000001',
 'follow_up', 'Kế hoạch giả lập do bác sĩ nhập: theo dõi chỉ số tại nhà và đặt lịch tái khám.',
 (CURRENT_DATE + 7 + TIME '09:00') AT TIME ZONE 'Asia/Ho_Chi_Minh', 'confirmed') ON CONFLICT DO NOTHING;

INSERT INTO patient_measurement(id, case_id, recorded_by, observed_at, systolic_bp, diastolic_bp, heart_rate, weight_kg, spo2, symptoms) VALUES
 ('60000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000005', now() - INTERVAL '1 day', 122, 80, 74, 60.2, 97, 'Ghi chú giả lập tại nhà.'),
 ('60000000-0000-4000-8000-000000000002', '10000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000005', now() - INTERVAL '1 hour', 120, 78, 72, 60, 98, NULL) ON CONFLICT DO NOTHING;
INSERT INTO appointment(id, case_id, doctor_id, slot_at, reason, requested_by)
SELECT '61000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001', '00000000-0000-4000-8000-000000000001',
 (CURRENT_DATE + 7 + TIME '09:00') AT TIME ZONE 'Asia/Ho_Chi_Minh', 'Tái khám demo.', '00000000-0000-4000-8000-000000000005'
WHERE NOT EXISTS (SELECT 1 FROM appointment WHERE id = '61000000-0000-4000-8000-000000000001');
SELECT generate_medication_reminders(CURRENT_DATE, CURRENT_DATE + 6);
COMMIT;
