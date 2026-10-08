# Từ điển dữ liệu — schema cập nhật theo SRS và cổng bệnh nhân

PostgreSQL 16+. Có 39 bảng. Metadata và bảng cột được xuất từ schema đã khởi tạo, cùng kiểm thử SQL.

UUID là định danh nội bộ; thời gian sự kiện dùng timestamptz. Null biểu thị chưa có dữ liệu. Giới hạn số trong CHECK là kiểm tra biểu diễn, không phải ngưỡng chẩn đoán.

Hướng dẫn tài khoản, phân quyền, đơn thuốc và giờ uống nằm trong [README database](README.md). Các bảng bệnh nhân có RLS cho vai trò DB `hf_patient_portal`; staff backend phải kiểm tra quyền theo phiên và hồ sơ. Gateway hiện tại vẫn dùng RAM.

## allergy_status

Trạng thái dị ứng/phản ứng: chưa rõ, xác nhận không có hoặc đã biết (FR-14).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| case_id | uuid | Không |  | Hồ sơ bệnh nhân liên quan. |
| status | character varying(10) | Không |  | Trạng thái; các giá trị hợp lệ được ghi trong CHECK bên dưới. |
| recorded_by | uuid | Không |  | Người ghi nhận dữ liệu. |
| recorded_at | timestamp with time zone | Không | now() | Thời điểm ghi nhận dữ liệu. |

Ràng buộc bảng:

- `allergy_status_case_id_fkey`: `FOREIGN KEY (case_id) REFERENCES patient_case(id)`
- `allergy_status_pkey`: `PRIMARY KEY (case_id)`
- `allergy_status_recorded_by_fkey`: `FOREIGN KEY (recorded_by) REFERENCES app_user(id)`
- `allergy_status_status_check`: `CHECK (((status)::text = ANY ((ARRAY['unknown'::character varying, 'none'::character varying, 'known'::character varying])::text[])))`

Index:

- `CREATE UNIQUE INDEX allergy_status_pkey ON public.allergy_status USING btree (case_id)`

Trigger:

- `allergy_audit`: `CREATE TRIGGER allergy_audit AFTER INSERT OR DELETE OR UPDATE ON public.allergy_status FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `allergy_revision`: `CREATE TRIGGER allergy_revision AFTER INSERT OR DELETE OR UPDATE ON public.allergy_status FOR EACH ROW EXECUTE FUNCTION bump_case_revision()`
- `allergy_staff_validate`: `CREATE TRIGGER allergy_staff_validate BEFORE INSERT OR UPDATE ON public.allergy_status FOR EACH ROW EXECUTE FUNCTION validate_staff_record()`
- `allergy_status_validate`: `CREATE TRIGGER allergy_status_validate BEFORE INSERT OR UPDATE ON public.allergy_status FOR EACH ROW EXECUTE FUNCTION validate_allergies()`

## app_user

Tài khoản; chỉ lưu password hash. Nhân viên có thể thuộc khoa (FR-01,02).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| username | character varying(80) | Không |  | Tên đăng nhập giả lập. |
| password_hash | text | Không |  | Hash mật khẩu; seed dùng PBKDF2-SHA256, không chứa mật khẩu rõ. |
| active | boolean | Không | true | Trạng thái được phép sử dụng. |
| department_code | character varying(30) | Có |  | Mã khoa. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `app_user_department_code_fkey`: `FOREIGN KEY (department_code) REFERENCES department(code)`
- `app_user_pkey`: `PRIMARY KEY (id)`
- `app_user_username_key`: `UNIQUE (username)`

Index:

- `CREATE UNIQUE INDEX app_user_pkey ON public.app_user USING btree (id)`
- `CREATE UNIQUE INDEX app_user_username_key ON public.app_user USING btree (username)`

Trigger:

- `user_audit`: `CREATE TRIGGER user_audit AFTER INSERT OR DELETE OR UPDATE ON public.app_user FOR EACH ROW EXECUTE FUNCTION audit_record_change()`

## appointment

Lịch hẹn 30 phút do bệnh nhân yêu cầu; xác nhận, hoàn thành hoặc hủy (FR-P02).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| case_id | uuid | Không |  | Hồ sơ bệnh nhân liên quan. |
| doctor_id | uuid | Không |  | Bác sĩ phụ trách/xác nhận. |
| slot_at | timestamp with time zone | Không |  | Thời điểm bắt đầu slot khám 30 phút. |
| reason | character varying(500) | Không |  | Lý do yêu cầu/quyết định. |
| status | character varying(12) | Không | 'requested'::character varying | Trạng thái; các giá trị hợp lệ được ghi trong CHECK bên dưới. |
| requested_by | uuid | Không |  | Tài khoản yêu cầu thao tác. |
| encounter_id | uuid | Có |  | Lần khám/đợt điều trị liên quan. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `appointment_case_id_fkey`: `FOREIGN KEY (case_id) REFERENCES patient_case(id)`
- `appointment_doctor_id_fkey`: `FOREIGN KEY (doctor_id) REFERENCES app_user(id)`
- `appointment_encounter_id_case_id_fkey`: `FOREIGN KEY (encounter_id, case_id) REFERENCES encounter(id, case_id)`
- `appointment_pkey`: `PRIMARY KEY (id)`
- `appointment_reason_check`: `CHECK ((length(TRIM(BOTH FROM reason)) > 0))`
- `appointment_requested_by_fkey`: `FOREIGN KEY (requested_by) REFERENCES app_user(id)`
- `appointment_slot_at_check`: `CHECK (((EXTRACT(epoch FROM slot_at) % (1800)::numeric) = (0)::numeric))`
- `appointment_status_check`: `CHECK (((status)::text = ANY ((ARRAY['requested'::character varying, 'confirmed'::character varying, 'completed'::character varying, 'cancelled'::character varying])::text[])))`

Index:

- `CREATE UNIQUE INDEX appointment_pkey ON public.appointment USING btree (id)`
- `CREATE INDEX ix_appointment_case ON public.appointment USING btree (case_id, slot_at DESC)`
- `CREATE UNIQUE INDEX ux_appointment_doctor_slot ON public.appointment USING btree (doctor_id, slot_at) WHERE ((status)::text = ANY ((ARRAY['requested'::character varying, 'confirmed'::character varying])::text[]))`
- `CREATE UNIQUE INDEX ux_appointment_patient_slot ON public.appointment USING btree (case_id, slot_at) WHERE ((status)::text = ANY ((ARRAY['requested'::character varying, 'confirmed'::character varying])::text[]))`

Trigger:

- `appointment_audit`: `CREATE TRIGGER appointment_audit AFTER INSERT OR UPDATE ON public.appointment FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `appointment_validate`: `CREATE TRIGGER appointment_validate BEFORE INSERT OR UPDATE ON public.appointment FOR EACH ROW EXECUTE FUNCTION validate_appointment()`

RLS:

- `patient_appointment_cancel`: UPDATE; USING `((case_id = portal_case_id()) AND ((status)::text = ANY ((ARRAY['requested'::character varying, 'confirmed'::character varying])::text[])))`; WITH CHECK `((case_id = portal_case_id()) AND ((status)::text = 'cancelled'::text))`.
- `patient_appointment_create`: INSERT; USING ``; WITH CHECK `((case_id = portal_case_id()) AND (requested_by = current_app_user()) AND ((status)::text = 'requested'::text) AND (encounter_id IS NULL))`.
- `patient_appointment_read`: SELECT; USING `(case_id = portal_case_id())`; WITH CHECK ``.

## audit_event

Nhật ký bất biến: người hoặc tiến trình hệ thống, đối tượng, hành động và thời gian (FR-34).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| actor_id | uuid | Có |  | Tài khoản thao tác; null cho tiến trình hệ thống không gắn tài khoản. |
| actor_kind | character varying(10) | Không | 'user'::character varying | user hoặc system. |
| action | character varying(80) | Không |  | Hành động/quyết định. |
| entity_type | character varying(40) | Không |  | Loại đối tượng nhật ký. |
| entity_id | uuid | Không |  | UUID đối tượng nhật ký. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `audit_event_actor_id_fkey`: `FOREIGN KEY (actor_id) REFERENCES app_user(id)`
- `audit_event_actor_kind_check`: `CHECK (((actor_kind)::text = ANY ((ARRAY['user'::character varying, 'system'::character varying])::text[])))`
- `audit_event_check`: `CHECK (((((actor_kind)::text = 'user'::text) AND (actor_id IS NOT NULL)) OR (((actor_kind)::text = 'system'::text) AND (actor_id IS NULL))))`
- `audit_event_pkey`: `PRIMARY KEY (id)`

Index:

- `CREATE UNIQUE INDEX audit_event_pkey ON public.audit_event USING btree (id)`
- `CREATE INDEX ix_audit_entity_time ON public.audit_event USING btree (entity_type, entity_id, created_at DESC)`

Trigger:

- `audit_immutable`: `CREATE TRIGGER audit_immutable BEFORE DELETE OR UPDATE ON public.audit_event FOR EACH ROW EXECUTE FUNCTION prevent_mutation()`

## auth_session

Phiên xác thực có hạn dùng và trạng thái thu hồi; chỉ lưu hash token (FR-01).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| user_id | uuid | Không |  | Tài khoản liên quan. |
| token_hash | character varying(64) | Không |  | SHA-256 của token phiên, không lưu token rõ. |
| expires_at | timestamp with time zone | Không |  | Thời điểm hết hạn phiên. |
| revoked_at | timestamp with time zone | Có |  | Thời điểm thu hồi phiên. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `auth_session_check`: `CHECK ((expires_at > created_at))`
- `auth_session_pkey`: `PRIMARY KEY (id)`
- `auth_session_token_hash_check`: `CHECK (((token_hash)::text ~ '^[a-f0-9]{64}$'::text))`
- `auth_session_token_hash_key`: `UNIQUE (token_hash)`
- `auth_session_user_id_fkey`: `FOREIGN KEY (user_id) REFERENCES app_user(id)`

Index:

- `CREATE UNIQUE INDEX auth_session_pkey ON public.auth_session USING btree (id)`
- `CREATE UNIQUE INDEX auth_session_token_hash_key ON public.auth_session USING btree (token_hash)`
- `CREATE INDEX ix_auth_session_user ON public.auth_session USING btree (user_id, expires_at)`

## case_access

Phạm vi hồ sơ cấp riêng cho bác sĩ, điều dưỡng hoặc dược sĩ (FR-03).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| case_id | uuid | Không |  | Hồ sơ bệnh nhân liên quan. |
| user_id | uuid | Không |  | Tài khoản liên quan. |
| access_scope | character varying(20) | Không |  | Phạm vi clinical, nursing hoặc medsafety. |

Ràng buộc bảng:

- `case_access_access_scope_check`: `CHECK (((access_scope)::text = ANY ((ARRAY['clinical'::character varying, 'nursing'::character varying, 'medsafety'::character varying])::text[])))`
- `case_access_case_id_fkey`: `FOREIGN KEY (case_id) REFERENCES patient_case(id)`
- `case_access_pkey`: `PRIMARY KEY (case_id, user_id, access_scope)`
- `case_access_user_id_fkey`: `FOREIGN KEY (user_id) REFERENCES app_user(id)`

Index:

- `CREATE UNIQUE INDEX case_access_pkey ON public.case_access USING btree (case_id, user_id, access_scope)`

Trigger:

- `access_audit`: `CREATE TRIGGER access_audit AFTER INSERT OR DELETE OR UPDATE ON public.case_access FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `case_access_validate`: `CREATE TRIGGER case_access_validate BEFORE INSERT OR UPDATE ON public.case_access FOR EACH ROW EXECUTE FUNCTION validate_case_staff()`

## clinical_decision

Quyết định bất biến của bác sĩ; điều chỉnh phải có nội dung và lý do (FR-31,33).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| evaluation_id | uuid | Không |  | Lần đánh giá liên quan. |
| doctor_id | uuid | Không |  | Bác sĩ phụ trách/xác nhận. |
| action | character varying(10) | Không |  | Hành động/quyết định. |
| reason | text | Có |  | Lý do yêu cầu/quyết định. |
| adjustment_details | jsonb | Có |  | Nội dung bác sĩ điều chỉnh dưới dạng JSONB, bắt buộc khi adjusted. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `clinical_decision_action_check`: `CHECK (((action)::text = ANY ((ARRAY['accepted'::character varying, 'adjusted'::character varying, 'rejected'::character varying])::text[])))`
- `clinical_decision_check`: `CHECK ((((action)::text = 'accepted'::text) OR (length(TRIM(BOTH FROM COALESCE(reason, ''::text))) > 0)))`
- `clinical_decision_check1`: `CHECK (((((action)::text = 'adjusted'::text) AND (adjustment_details IS NOT NULL) AND (jsonb_typeof(adjustment_details) = 'object'::text) AND (adjustment_details <> '{}'::jsonb)) OR (((action)::text <> 'adjusted'::text) AND (adjustment_details IS NULL))))`
- `clinical_decision_doctor_id_fkey`: `FOREIGN KEY (doctor_id) REFERENCES app_user(id)`
- `clinical_decision_evaluation_id_fkey`: `FOREIGN KEY (evaluation_id) REFERENCES evaluation(id)`
- `clinical_decision_evaluation_id_key`: `UNIQUE (evaluation_id)`
- `clinical_decision_pkey`: `PRIMARY KEY (id)`

Index:

- `CREATE UNIQUE INDEX clinical_decision_evaluation_id_key ON public.clinical_decision USING btree (evaluation_id)`
- `CREATE UNIQUE INDEX clinical_decision_pkey ON public.clinical_decision USING btree (id)`

Trigger:

- `decision_audit`: `CREATE TRIGGER decision_audit AFTER INSERT ON public.clinical_decision FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `decision_immutable`: `CREATE TRIGGER decision_immutable BEFORE DELETE OR UPDATE ON public.clinical_decision FOR EACH ROW EXECUTE FUNCTION prevent_mutation()`
- `decision_validate`: `CREATE TRIGGER decision_validate BEFORE INSERT ON public.clinical_decision FOR EACH ROW EXECUTE FUNCTION validate_evaluation_decision()`

## clinical_note

Ghi nhận chăm sóc, khám, chẩn đoán hoặc đánh giá lão khoa theo lần khám (FR-09,10,11).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| encounter_id | uuid | Không |  | Lần khám/đợt điều trị liên quan. |
| kind | character varying(20) | Không |  | Loại bản ghi; xem CHECK của bảng. |
| content | text | Không |  | Nội dung ghi nhận hoặc JSONB; xem kiểu và ràng buộc của bảng. |
| recorded_by | uuid | Không |  | Người ghi nhận dữ liệu. |
| recorded_at | timestamp with time zone | Không | now() | Thời điểm ghi nhận dữ liệu. |

Ràng buộc bảng:

- `clinical_note_content_check`: `CHECK ((length(TRIM(BOTH FROM content)) > 0))`
- `clinical_note_encounter_id_fkey`: `FOREIGN KEY (encounter_id) REFERENCES encounter(id)`
- `clinical_note_kind_check`: `CHECK (((kind)::text = ANY ((ARRAY['nursing'::character varying, 'examination'::character varying, 'diagnosis'::character varying, 'geriatric'::character varying])::text[])))`
- `clinical_note_pkey`: `PRIMARY KEY (id)`
- `clinical_note_recorded_by_fkey`: `FOREIGN KEY (recorded_by) REFERENCES app_user(id)`

Index:

- `CREATE UNIQUE INDEX clinical_note_pkey ON public.clinical_note USING btree (id)`
- `CREATE INDEX ix_note_encounter ON public.clinical_note USING btree (encounter_id, recorded_at DESC)`

Trigger:

- `note_audit`: `CREATE TRIGGER note_audit AFTER INSERT OR DELETE OR UPDATE ON public.clinical_note FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `note_revision`: `CREATE TRIGGER note_revision AFTER INSERT OR DELETE OR UPDATE ON public.clinical_note FOR EACH ROW EXECUTE FUNCTION bump_case_revision()`
- `note_staff_validate`: `CREATE TRIGGER note_staff_validate BEFORE INSERT OR UPDATE ON public.clinical_note FOR EACH ROW EXECUTE FUNCTION validate_staff_record()`

## department

Danh mục khoa giả lập (FR-04,07).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| code | character varying(30) | Không |  | Mã danh mục/quy tắc. |
| name | text | Không |  | Tên danh mục. |
| active | boolean | Không | true | Trạng thái được phép sử dụng. |

Ràng buộc bảng:

- `department_name_check`: `CHECK ((length(TRIM(BOTH FROM name)) > 0))`
- `department_pkey`: `PRIMARY KEY (code)`

Index:

- `CREATE UNIQUE INDEX department_pkey ON public.department USING btree (code)`

## drug_product

Danh mục sản phẩm thuốc: hoạt chất, hàm lượng và dạng bào chế (FR-04,13).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| code | character varying(60) | Không |  | Mã danh mục/quy tắc. |
| ingredient_code | character varying(60) | Không |  | Hoạt chất liên quan. |
| display_name | text | Không |  | Tên hiển thị danh mục. |
| strength | numeric | Không |  | Hàm lượng sản phẩm. |
| strength_unit | character varying(10) | Không |  | Đơn vị hàm lượng. |
| dosage_form | character varying(30) | Không |  | Dạng bào chế. |
| active | boolean | Không | true | Trạng thái được phép sử dụng. |

Ràng buộc bảng:

- `drug_product_code_ingredient_code_key`: `UNIQUE (code, ingredient_code)`
- `drug_product_ingredient_code_fkey`: `FOREIGN KEY (ingredient_code) REFERENCES ingredient(code)`
- `drug_product_pkey`: `PRIMARY KEY (code)`
- `drug_product_strength_check`: `CHECK (((strength > (0)::numeric) AND ((strength)::text <> ALL (ARRAY['NaN'::text, 'Infinity'::text, '-Infinity'::text]))))`
- `drug_product_strength_unit_check`: `CHECK (((strength_unit)::text = ANY ((ARRAY['mg'::character varying, 'mcg'::character varying, 'g'::character varying, 'mg/mL'::character varying])::text[])))`

Index:

- `CREATE UNIQUE INDEX drug_product_code_ingredient_code_key ON public.drug_product USING btree (code, ingredient_code)`
- `CREATE UNIQUE INDEX drug_product_pkey ON public.drug_product USING btree (code)`

## drug_reaction

Chi tiết dị ứng hoặc phản ứng có hại với hoạt chất, chỉ khi trạng thái là known (FR-14).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| case_id | uuid | Không |  | Hồ sơ bệnh nhân liên quan. |
| ingredient_code | character varying(60) | Không |  | Hoạt chất liên quan. |
| kind | character varying(10) | Không |  | Loại bản ghi; xem CHECK của bảng. |
| description | text | Không |  | Mô tả nội dung. |
| recorded_by | uuid | Không |  | Người ghi nhận dữ liệu. |
| recorded_at | timestamp with time zone | Không | now() | Thời điểm ghi nhận dữ liệu. |

Ràng buộc bảng:

- `drug_reaction_case_id_fkey`: `FOREIGN KEY (case_id) REFERENCES allergy_status(case_id)`
- `drug_reaction_description_check`: `CHECK ((length(TRIM(BOTH FROM description)) > 0))`
- `drug_reaction_ingredient_code_fkey`: `FOREIGN KEY (ingredient_code) REFERENCES ingredient(code)`
- `drug_reaction_kind_check`: `CHECK (((kind)::text = ANY ((ARRAY['allergy'::character varying, 'adverse'::character varying])::text[])))`
- `drug_reaction_pkey`: `PRIMARY KEY (id)`
- `drug_reaction_recorded_by_fkey`: `FOREIGN KEY (recorded_by) REFERENCES app_user(id)`

Index:

- `CREATE UNIQUE INDEX drug_reaction_pkey ON public.drug_reaction USING btree (id)`

Trigger:

- `reaction_audit`: `CREATE TRIGGER reaction_audit AFTER INSERT OR DELETE OR UPDATE ON public.drug_reaction FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `reaction_revision`: `CREATE TRIGGER reaction_revision AFTER INSERT OR DELETE OR UPDATE ON public.drug_reaction FOR EACH ROW EXECUTE FUNCTION bump_case_revision()`
- `reaction_staff_validate`: `CREATE TRIGGER reaction_staff_validate BEFORE INSERT OR UPDATE ON public.drug_reaction FOR EACH ROW EXECUTE FUNCTION validate_staff_record()`
- `reaction_status_validate`: `CREATE TRIGGER reaction_status_validate BEFORE INSERT OR UPDATE ON public.drug_reaction FOR EACH ROW EXECUTE FUNCTION validate_allergies()`

## encounter

Lần khám ngoại trú/đợt nội trú, khoa, bác sĩ, trạng thái và thời điểm kết thúc (FR-07).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| case_id | uuid | Không |  | Hồ sơ bệnh nhân liên quan. |
| occurred_at | timestamp with time zone | Không |  | Thời điểm bắt đầu lần khám/đợt điều trị. |
| kind | character varying(12) | Không | 'outpatient'::character varying | Loại bản ghi; xem CHECK của bảng. |
| department_code | character varying(30) | Không |  | Mã khoa. |
| doctor_id | uuid | Không |  | Bác sĩ phụ trách/xác nhận. |
| status | character varying(12) | Không | 'open'::character varying | Trạng thái; các giá trị hợp lệ được ghi trong CHECK bên dưới. |
| ended_at | timestamp with time zone | Có |  | Thời điểm kết thúc. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `encounter_case_id_fkey`: `FOREIGN KEY (case_id) REFERENCES patient_case(id)`
- `encounter_check`: `CHECK (((ended_at IS NULL) OR (ended_at >= occurred_at)))`
- `encounter_check1`: `CHECK (((((status)::text = 'open'::text) AND (ended_at IS NULL)) OR (((status)::text <> 'open'::text) AND (ended_at IS NOT NULL))))`
- `encounter_department_code_fkey`: `FOREIGN KEY (department_code) REFERENCES department(code)`
- `encounter_doctor_id_fkey`: `FOREIGN KEY (doctor_id) REFERENCES app_user(id)`
- `encounter_id_case_id_key`: `UNIQUE (id, case_id)`
- `encounter_kind_check`: `CHECK (((kind)::text = ANY ((ARRAY['outpatient'::character varying, 'inpatient'::character varying])::text[])))`
- `encounter_pkey`: `PRIMARY KEY (id)`
- `encounter_status_check`: `CHECK (((status)::text = ANY ((ARRAY['open'::character varying, 'completed'::character varying, 'cancelled'::character varying])::text[])))`

Index:

- `CREATE UNIQUE INDEX encounter_id_case_id_key ON public.encounter USING btree (id, case_id)`
- `CREATE UNIQUE INDEX encounter_pkey ON public.encounter USING btree (id)`
- `CREATE INDEX ix_encounter_case_time ON public.encounter USING btree (case_id, occurred_at DESC)`

Trigger:

- `encounter_audit`: `CREATE TRIGGER encounter_audit AFTER INSERT OR DELETE OR UPDATE ON public.encounter FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `encounter_revision`: `CREATE TRIGGER encounter_revision AFTER INSERT OR DELETE OR UPDATE ON public.encounter FOR EACH ROW EXECUTE FUNCTION bump_case_revision()`
- `encounter_staff_validate`: `CREATE TRIGGER encounter_staff_validate BEFORE INSERT OR UPDATE ON public.encounter FOR EACH ROW EXECUTE FUNCTION validate_case_staff()`

## evaluation

Snapshot bất biến của một lần đánh giá cùng revision nguồn và người yêu cầu (FR-18,33).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| encounter_id | uuid | Không |  | Lần khám/đợt điều trị liên quan. |
| input_revision | integer | Không |  | Revision của hồ sơ nguồn khi đánh giá. |
| input_snapshot | jsonb | Không |  | Bản sao JSONB bất biến dữ liệu được dùng. |
| requested_by | uuid | Không |  | Tài khoản yêu cầu thao tác. |
| mode | character varying(10) | Không |  | Chế độ stub hoặc validated; seed chỉ dùng stub. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `evaluation_encounter_id_fkey`: `FOREIGN KEY (encounter_id) REFERENCES encounter(id)`
- `evaluation_id_encounter_id_key`: `UNIQUE (id, encounter_id)`
- `evaluation_input_revision_check`: `CHECK ((input_revision > 0))`
- `evaluation_input_snapshot_check`: `CHECK ((jsonb_typeof(input_snapshot) = 'object'::text))`
- `evaluation_mode_check`: `CHECK (((mode)::text = ANY ((ARRAY['stub'::character varying, 'validated'::character varying])::text[])))`
- `evaluation_pkey`: `PRIMARY KEY (id)`
- `evaluation_requested_by_fkey`: `FOREIGN KEY (requested_by) REFERENCES app_user(id)`

Index:

- `CREATE UNIQUE INDEX evaluation_id_encounter_id_key ON public.evaluation USING btree (id, encounter_id)`
- `CREATE UNIQUE INDEX evaluation_pkey ON public.evaluation USING btree (id)`
- `CREATE INDEX ix_evaluation_history ON public.evaluation USING btree (encounter_id, created_at DESC)`

Trigger:

- `evaluation_audit`: `CREATE TRIGGER evaluation_audit AFTER INSERT ON public.evaluation FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `evaluation_immutable`: `CREATE TRIGGER evaluation_immutable BEFORE DELETE OR UPDATE ON public.evaluation FOR EACH ROW EXECUTE FUNCTION prevent_mutation()`
- `evaluation_validate`: `CREATE TRIGGER evaluation_validate BEFORE INSERT ON public.evaluation FOR EACH ROW EXECUTE FUNCTION validate_evaluation_decision()`

## import_batch

Lần nhập file/API mô phỏng, mã nguồn, trạng thái và số dòng thành công/lỗi (FR-16,17).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| encounter_id | uuid | Không |  | Lần khám/đợt điều trị liên quan. |
| source | character varying(30) | Không |  | Nguồn nhập giả lập hoặc nguồn mô phỏng. |
| external_ref | text | Không |  | Mã bản tin/báo cáo/batch nguồn giả lập. |
| status | character varying(12) | Không |  | Trạng thái; các giá trị hợp lệ được ghi trong CHECK bên dưới. |
| accepted_rows | integer | Không | 0 | Số dòng nhập thành công. |
| rejected_rows | integer | Không | 0 | Số dòng nhập lỗi. |
| imported_by | uuid | Không |  | Người nhập batch. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `import_batch_accepted_rows_check`: `CHECK ((accepted_rows >= 0))`
- `import_batch_encounter_id_fkey`: `FOREIGN KEY (encounter_id) REFERENCES encounter(id)`
- `import_batch_imported_by_fkey`: `FOREIGN KEY (imported_by) REFERENCES app_user(id)`
- `import_batch_pkey`: `PRIMARY KEY (id)`
- `import_batch_rejected_rows_check`: `CHECK ((rejected_rows >= 0))`
- `import_batch_source_check`: `CHECK (((source)::text = ANY ((ARRAY['file'::character varying, 'mock_his'::character varying, 'mock_lis'::character varying, 'mock_pacs'::character varying, 'mock_emr'::character varying])::text[])))`
- `import_batch_source_external_ref_key`: `UNIQUE (source, external_ref)`
- `import_batch_status_check`: `CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'completed'::character varying, 'partial'::character varying, 'failed'::character varying])::text[])))`

Index:

- `CREATE UNIQUE INDEX import_batch_pkey ON public.import_batch USING btree (id)`
- `CREATE UNIQUE INDEX import_batch_source_external_ref_key ON public.import_batch USING btree (source, external_ref)`

Trigger:

- `import_audit`: `CREATE TRIGGER import_audit AFTER INSERT OR UPDATE ON public.import_batch FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `import_staff_validate`: `CREATE TRIGGER import_staff_validate BEFORE INSERT OR UPDATE ON public.import_batch FOR EACH ROW EXECUTE FUNCTION validate_staff_record()`

## import_error

Lỗi nhập theo dòng, trường và thông báo (FR-16,18).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| batch_id | uuid | Không |  | Batch nhập dữ liệu liên quan. |
| row_number | integer | Không |  | Số dòng gây lỗi. |
| field_code | character varying(60) | Không |  | Mã chỉ số/trường dữ liệu. |
| message | text | Không |  | Thông báo diễn giải/lỗi. |

Ràng buộc bảng:

- `import_error_batch_id_fkey`: `FOREIGN KEY (batch_id) REFERENCES import_batch(id)`
- `import_error_pkey`: `PRIMARY KEY (id)`
- `import_error_row_number_check`: `CHECK ((row_number > 0))`

Index:

- `CREATE UNIQUE INDEX import_error_pkey ON public.import_error USING btree (id)`
- `CREATE INDEX ix_import_error_batch ON public.import_error USING btree (batch_id)`

## ingredient

Danh mục hoạt chất; seed chỉ có hoạt chất giả lập (FR-04).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| code | character varying(60) | Không |  | Mã danh mục/quy tắc. |
| display_name | text | Không |  | Tên hiển thị danh mục. |

Ràng buộc bảng:

- `ingredient_pkey`: `PRIMARY KEY (code)`

Index:

- `CREATE UNIQUE INDEX ingredient_pkey ON public.ingredient USING btree (code)`

## medication

Thuốc hiện dùng/đề xuất, liều, đường dùng, tần suất, khoảng ngày và liên kết đơn (FR-13).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| encounter_id | uuid | Không |  | Lần khám/đợt điều trị liên quan. |
| ingredient_code | character varying(60) | Không |  | Hoạt chất liên quan. |
| drug_product_code | character varying(60) | Có |  | Sản phẩm thuốc; phải thuộc đúng hoạt chất. |
| prescription_id | uuid | Có |  | Đơn thuốc liên quan. |
| dose | numeric | Không |  | Liều của một lần dùng. |
| dose_unit | character varying(10) | Không |  | Đơn vị liều. |
| route | character varying(10) | Không |  | Đường dùng. |
| frequency_per_day | smallint | Không |  | Số lần dùng mỗi ngày. |
| kind | character varying(10) | Không |  | Loại bản ghi; xem CHECK của bảng. |
| starts_on | date | Không | CURRENT_DATE | Ngày bắt đầu dùng. |
| ends_on | date | Có |  | Ngày kết thúc nếu có. |
| instructions | text | Không | ''::text | Hướng dẫn dạng văn bản. |
| recorded_by | uuid | Không |  | Người ghi nhận dữ liệu. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `medication_check`: `CHECK (((ends_on IS NULL) OR (ends_on >= starts_on)))`
- `medication_check1`: `CHECK (((prescription_id IS NULL) OR ((kind)::text = 'current'::text)))`
- `medication_dose_check`: `CHECK (((dose > (0)::numeric) AND ((dose)::text <> ALL (ARRAY['NaN'::text, 'Infinity'::text, '-Infinity'::text]))))`
- `medication_dose_unit_check`: `CHECK (((dose_unit)::text = ANY ((ARRAY['mg'::character varying, 'mcg'::character varying, 'g'::character varying, 'mL'::character varying])::text[])))`
- `medication_drug_product_code_ingredient_code_fkey`: `FOREIGN KEY (drug_product_code, ingredient_code) REFERENCES drug_product(code, ingredient_code)`
- `medication_encounter_id_fkey`: `FOREIGN KEY (encounter_id) REFERENCES encounter(id)`
- `medication_frequency_per_day_check`: `CHECK (((frequency_per_day >= 1) AND (frequency_per_day <= 24)))`
- `medication_ingredient_code_fkey`: `FOREIGN KEY (ingredient_code) REFERENCES ingredient(code)`
- `medication_kind_check`: `CHECK (((kind)::text = ANY ((ARRAY['current'::character varying, 'proposed'::character varying])::text[])))`
- `medication_pkey`: `PRIMARY KEY (id)`
- `medication_prescription_id_encounter_id_fkey`: `FOREIGN KEY (prescription_id, encounter_id) REFERENCES prescription(id, encounter_id)`
- `medication_recorded_by_fkey`: `FOREIGN KEY (recorded_by) REFERENCES app_user(id)`
- `medication_route_check`: `CHECK (((route)::text = ANY ((ARRAY['oral'::character varying, 'iv'::character varying, 'other'::character varying])::text[])))`

Index:

- `CREATE INDEX ix_medication_encounter ON public.medication USING btree (encounter_id)`
- `CREATE INDEX ix_medication_prescription ON public.medication USING btree (prescription_id)`
- `CREATE UNIQUE INDEX medication_pkey ON public.medication USING btree (id)`

Trigger:

- `medication_audit`: `CREATE TRIGGER medication_audit AFTER INSERT OR DELETE OR UPDATE ON public.medication FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `medication_revision`: `CREATE TRIGGER medication_revision AFTER INSERT OR DELETE OR UPDATE ON public.medication FOR EACH ROW EXECUTE FUNCTION bump_case_revision()`
- `medication_staff_validate`: `CREATE TRIGGER medication_staff_validate BEFORE INSERT OR UPDATE ON public.medication FOR EACH ROW EXECUTE FUNCTION validate_staff_record()`
- `prescribed_medication_guard`: `CREATE TRIGGER prescribed_medication_guard BEFORE INSERT OR DELETE OR UPDATE ON public.medication FOR EACH ROW EXECUTE FUNCTION guard_prescribed_medication()`

RLS:

- `patient_medication_read`: SELECT; USING `portal_owns_medication(id)`; WITH CHECK ``.

## medication_reminder

Một nhắc uống cho một giờ trong một ngày; pending/taken/skipped/cancelled (FR-P04).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| schedule_id | uuid | Không |  | Giờ uống liên quan. |
| scheduled_on | date | Không |  | Ngày uống địa phương. |
| due_at | timestamp with time zone | Không |  | Thời điểm nhắc thực tế có múi giờ. |
| status | character varying(12) | Không | 'pending'::character varying | Trạng thái; các giá trị hợp lệ được ghi trong CHECK bên dưới. |
| responded_at | timestamp with time zone | Có |  | Thời điểm đánh dấu đã uống/bỏ qua, do trigger ghi. |
| notified_at | timestamp with time zone | Có |  | Thời điểm worker đã gửi thông báo nếu có. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `medication_reminder_check`: `CHECK (((((status)::text = ANY ((ARRAY['pending'::character varying, 'cancelled'::character varying])::text[])) AND (responded_at IS NULL)) OR (((status)::text = ANY ((ARRAY['taken'::character varying, 'skipped'::character varying])::text[])) AND (responded_at IS NOT NULL))))`
- `medication_reminder_pkey`: `PRIMARY KEY (id)`
- `medication_reminder_schedule_id_fkey`: `FOREIGN KEY (schedule_id) REFERENCES medication_schedule(id)`
- `medication_reminder_schedule_id_scheduled_on_key`: `UNIQUE (schedule_id, scheduled_on)`
- `medication_reminder_status_check`: `CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'taken'::character varying, 'skipped'::character varying, 'cancelled'::character varying])::text[])))`

Index:

- `CREATE INDEX ix_reminder_due ON public.medication_reminder USING btree (due_at) WHERE ((status)::text = 'pending'::text)`
- `CREATE UNIQUE INDEX medication_reminder_pkey ON public.medication_reminder USING btree (id)`
- `CREATE UNIQUE INDEX medication_reminder_schedule_id_scheduled_on_key ON public.medication_reminder USING btree (schedule_id, scheduled_on)`

Trigger:

- `reminder_audit`: `CREATE TRIGGER reminder_audit AFTER INSERT OR UPDATE ON public.medication_reminder FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `reminder_validate`: `CREATE TRIGGER reminder_validate BEFORE INSERT OR UPDATE ON public.medication_reminder FOR EACH ROW EXECUTE FUNCTION validate_reminder()`

RLS:

- `patient_reminder_read`: SELECT; USING `portal_owns_schedule(schedule_id)`; WITH CHECK ``.
- `patient_reminder_respond`: UPDATE; USING `(portal_owns_schedule(schedule_id) AND ((status)::text = 'pending'::text))`; WITH CHECK `(portal_owns_schedule(schedule_id) AND ((status)::text = ANY ((ARRAY['taken'::character varying, 'skipped'::character varying])::text[])))`.

## medication_schedule

Giờ uống hằng ngày của từng thuốc trong đơn, theo múi giờ của đơn (FR-13,FR-P04).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| medication_id | uuid | Không |  | Thuốc trong đơn liên quan. |
| dose_time | time without time zone | Không |  | Giờ uống địa phương hằng ngày; một dòng cho mỗi lần uống. |
| instructions | text | Không | ''::text | Hướng dẫn dạng văn bản. |

Ràng buộc bảng:

- `medication_schedule_dose_time_check`: `CHECK (((dose_time >= '00:00:00'::time without time zone) AND (dose_time < '24:00:00'::time without time zone)))`
- `medication_schedule_medication_id_dose_time_key`: `UNIQUE (medication_id, dose_time)`
- `medication_schedule_medication_id_fkey`: `FOREIGN KEY (medication_id) REFERENCES medication(id)`
- `medication_schedule_pkey`: `PRIMARY KEY (id)`

Index:

- `CREATE UNIQUE INDEX medication_schedule_medication_id_dose_time_key ON public.medication_schedule USING btree (medication_id, dose_time)`
- `CREATE UNIQUE INDEX medication_schedule_pkey ON public.medication_schedule USING btree (id)`

Trigger:

- `dose_time_audit`: `CREATE TRIGGER dose_time_audit AFTER INSERT OR DELETE OR UPDATE ON public.medication_schedule FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `medication_schedule_guard`: `CREATE TRIGGER medication_schedule_guard BEFORE INSERT OR DELETE OR UPDATE ON public.medication_schedule FOR EACH ROW EXECUTE FUNCTION guard_prescribed_medication()`

RLS:

- `patient_schedule_read`: SELECT; USING `portal_owns_medication(medication_id)`; WITH CHECK ``.

## module_result

Kết quả một module: phiên bản quy tắc, trạng thái và diễn giải (FR-19..29).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| evaluation_id | uuid | Không |  | Lần đánh giá liên quan. |
| module | character varying(20) | Không |  | Module diagnosis, lab_test, treatment hoặc medsafety. |
| rule_version_id | uuid | Có |  | Phiên bản quy tắc liên quan. |
| status | character varying(30) | Không |  | Trạng thái; các giá trị hợp lệ được ghi trong CHECK bên dưới. |
| message | text | Không |  | Thông báo diễn giải/lỗi. |

Ràng buộc bảng:

- `module_result_check`: `CHECK ((((status)::text = 'mock_not_evaluated'::text) OR (rule_version_id IS NOT NULL)))`
- `module_result_evaluation_id_fkey`: `FOREIGN KEY (evaluation_id) REFERENCES evaluation(id)`
- `module_result_evaluation_id_module_key`: `UNIQUE (evaluation_id, module)`
- `module_result_module_check`: `CHECK (((module)::text = ANY ((ARRAY['diagnosis'::character varying, 'lab_test'::character varying, 'treatment'::character varying, 'medsafety'::character varying])::text[])))`
- `module_result_pkey`: `PRIMARY KEY (id)`
- `module_result_rule_version_id_fkey`: `FOREIGN KEY (rule_version_id) REFERENCES rule_version(id)`
- `module_result_status_check`: `CHECK (((status)::text = ANY ((ARRAY['mock_not_evaluated'::character varying, 'completed'::character varying, 'insufficient_data'::character varying, 'failed'::character varying])::text[])))`

Index:

- `CREATE UNIQUE INDEX module_result_evaluation_id_module_key ON public.module_result USING btree (evaluation_id, module)`
- `CREATE UNIQUE INDEX module_result_pkey ON public.module_result USING btree (id)`

## observation

Chỉ số theo lần khám, có loại giá trị, trạng thái thiếu, nguồn và người ghi (FR-09,11,12).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| encounter_id | uuid | Không |  | Lần khám/đợt điều trị liên quan. |
| code | character varying(60) | Không |  | Mã danh mục/quy tắc. |
| value_number | numeric | Có |  | Giá trị số; không nhận NaN/Infinity. |
| value_boolean | boolean | Có |  | Giá trị có/không. |
| value_text | text | Có |  | Giá trị văn bản. |
| status | character varying(20) | Không |  | Trạng thái; các giá trị hợp lệ được ghi trong CHECK bên dưới. |
| observed_at | timestamp with time zone | Không |  | Thời điểm đo/đánh giá. |
| source | character varying(30) | Không |  | Nguồn nhập giả lập hoặc nguồn mô phỏng. |
| recorded_by | uuid | Không |  | Người ghi nhận dữ liệu. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `observation_check`: `CHECK (((((status)::text = 'present'::text) AND (num_nonnulls(value_number, value_boolean, value_text) = 1)) OR (((status)::text <> 'present'::text) AND (num_nonnulls(value_number, value_boolean, value_text) = 0))))`
- `observation_code_fkey`: `FOREIGN KEY (code) REFERENCES observation_type(code)`
- `observation_encounter_id_fkey`: `FOREIGN KEY (encounter_id) REFERENCES encounter(id)`
- `observation_pkey`: `PRIMARY KEY (id)`
- `observation_recorded_by_fkey`: `FOREIGN KEY (recorded_by) REFERENCES app_user(id)`
- `observation_source_check`: `CHECK (((source)::text = ANY ((ARRAY['manual_synthetic'::character varying, 'mock_his'::character varying, 'mock_lis'::character varying, 'mock_pacs'::character varying, 'mock_emr'::character varying])::text[])))`
- `observation_status_check`: `CHECK (((status)::text = ANY ((ARRAY['present'::character varying, 'not_measured'::character varying, 'unknown'::character varying])::text[])))`

Index:

- `CREATE INDEX ix_observation_latest ON public.observation USING btree (encounter_id, code, observed_at DESC)`
- `CREATE UNIQUE INDEX observation_pkey ON public.observation USING btree (id)`

Trigger:

- `observation_audit`: `CREATE TRIGGER observation_audit AFTER INSERT OR DELETE OR UPDATE ON public.observation FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `observation_revision`: `CREATE TRIGGER observation_revision AFTER INSERT OR DELETE OR UPDATE ON public.observation FOR EACH ROW EXECUTE FUNCTION bump_case_revision()`
- `observation_staff_validate`: `CREATE TRIGGER observation_staff_validate BEFORE INSERT OR UPDATE ON public.observation FOR EACH ROW EXECUTE FUNCTION validate_staff_record()`
- `observation_validate`: `CREATE TRIGGER observation_validate BEFORE INSERT OR UPDATE ON public.observation FOR EACH ROW EXECUTE FUNCTION validate_observation()`

## observation_type

Danh mục chỉ số, kiểu và đơn vị; giới hạn biểu diễn, không phải ngưỡng cảnh báo (FR-04,18).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| code | character varying(60) | Không |  | Mã danh mục/quy tắc. |
| label | text | Không |  | Nhãn hiển thị. |
| value_kind | character varying(10) | Không |  | Kiểu number, boolean hoặc text. |
| unit | character varying(40) | Có |  | Đơn vị chuẩn của chỉ số. |
| min_value | numeric | Có |  | Giới hạn biểu diễn dưới; không phải ngưỡng y khoa. |
| max_value | numeric | Có |  | Giới hạn biểu diễn trên nếu áp dụng. |

Ràng buộc bảng:

- `observation_type_check`: `CHECK (((min_value IS NULL) OR (max_value IS NULL) OR (min_value <= max_value)))`
- `observation_type_max_value_check`: `CHECK (((max_value)::text <> ALL (ARRAY['NaN'::text, 'Infinity'::text, '-Infinity'::text])))`
- `observation_type_min_value_check`: `CHECK (((min_value)::text <> ALL (ARRAY['NaN'::text, 'Infinity'::text, '-Infinity'::text])))`
- `observation_type_pkey`: `PRIMARY KEY (code)`
- `observation_type_value_kind_check`: `CHECK (((value_kind)::text = ANY ((ARRAY['number'::character varying, 'boolean'::character varying, 'text'::character varying])::text[])))`

Index:

- `CREATE UNIQUE INDEX observation_type_pkey ON public.observation_type USING btree (code)`

Trigger:

- `observation_catalog_guard`: `CREATE TRIGGER observation_catalog_guard BEFORE UPDATE ON public.observation_type FOR EACH ROW EXECUTE FUNCTION protect_observation_catalog()`

## patient_account

Liên kết duy nhất tài khoản patient với một hồ sơ synthetic (FR-P01).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| user_id | uuid | Không |  | Tài khoản liên quan. |
| case_id | uuid | Không |  | Hồ sơ bệnh nhân liên quan. |
| role_code | character varying(20) | Không | 'patient'::character varying | Mã vai trò. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `patient_account_case_id_fkey`: `FOREIGN KEY (case_id) REFERENCES patient_case(id)`
- `patient_account_case_id_key`: `UNIQUE (case_id)`
- `patient_account_pkey`: `PRIMARY KEY (user_id)`
- `patient_account_role_code_check`: `CHECK (((role_code)::text = 'patient'::text))`
- `patient_account_user_id_fkey`: `FOREIGN KEY (user_id) REFERENCES app_user(id)`
- `patient_account_user_id_role_code_fkey`: `FOREIGN KEY (user_id, role_code) REFERENCES user_role(user_id, role_code)`

Index:

- `CREATE UNIQUE INDEX patient_account_case_id_key ON public.patient_account USING btree (case_id)`
- `CREATE UNIQUE INDEX patient_account_pkey ON public.patient_account USING btree (user_id)`

Trigger:

- `patient_account_immutable`: `CREATE TRIGGER patient_account_immutable BEFORE DELETE OR UPDATE ON public.patient_account FOR EACH ROW EXECUTE FUNCTION prevent_mutation()`

## patient_case

Hồ sơ synthetic, bác sĩ phụ trách và revision; không lưu định danh thật (FR-06).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| synthetic_code | character varying(30) | Không |  | Mã hồ sơ giả lập duy nhất bắt đầu bằng SYN-. |
| age | smallint | Không |  | Tuổi ghi nhận trong hồ sơ. |
| sex | character varying(10) | Không |  | Giới tính hoặc chưa rõ. |
| owner_id | uuid | Không |  | Bác sĩ phụ trách hồ sơ. |
| revision | integer | Không | 1 | Tăng khi dữ liệu lâm sàng liên quan thay đổi. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `patient_case_age_check`: `CHECK (((age >= 0) AND (age <= 120)))`
- `patient_case_owner_id_fkey`: `FOREIGN KEY (owner_id) REFERENCES app_user(id)`
- `patient_case_pkey`: `PRIMARY KEY (id)`
- `patient_case_revision_check`: `CHECK ((revision > 0))`
- `patient_case_sex_check`: `CHECK (((sex)::text = ANY ((ARRAY['male'::character varying, 'female'::character varying, 'unknown'::character varying])::text[])))`
- `patient_case_synthetic_code_check`: `CHECK (((synthetic_code)::text ~ '^SYN-[A-Z0-9-]{1,24}$'::text))`
- `patient_case_synthetic_code_key`: `UNIQUE (synthetic_code)`

Index:

- `CREATE INDEX ix_case_owner ON public.patient_case USING btree (owner_id)`
- `CREATE UNIQUE INDEX patient_case_pkey ON public.patient_case USING btree (id)`
- `CREATE UNIQUE INDEX patient_case_synthetic_code_key ON public.patient_case USING btree (synthetic_code)`

Trigger:

- `case_audit`: `CREATE TRIGGER case_audit AFTER INSERT OR UPDATE ON public.patient_case FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `case_staff_validate`: `CREATE TRIGGER case_staff_validate BEFORE INSERT OR UPDATE ON public.patient_case FOR EACH ROW EXECUTE FUNCTION validate_case_staff()`
- `profile_revision`: `CREATE TRIGGER profile_revision BEFORE UPDATE ON public.patient_case FOR EACH ROW EXECUTE FUNCTION guard_profile_revision()`

## patient_history

Tiền sử, bệnh đồng mắc, gia đình và xã hội theo hồ sơ (FR-08).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| case_id | uuid | Không |  | Hồ sơ bệnh nhân liên quan. |
| kind | character varying(20) | Không |  | Loại bản ghi; xem CHECK của bảng. |
| description | text | Không |  | Mô tả nội dung. |
| recorded_by | uuid | Không |  | Người ghi nhận dữ liệu. |
| recorded_at | timestamp with time zone | Không | now() | Thời điểm ghi nhận dữ liệu. |

Ràng buộc bảng:

- `patient_history_case_id_fkey`: `FOREIGN KEY (case_id) REFERENCES patient_case(id)`
- `patient_history_description_check`: `CHECK ((length(TRIM(BOTH FROM description)) > 0))`
- `patient_history_kind_check`: `CHECK (((kind)::text = ANY ((ARRAY['medical'::character varying, 'comorbidity'::character varying, 'family'::character varying, 'social'::character varying])::text[])))`
- `patient_history_pkey`: `PRIMARY KEY (id)`
- `patient_history_recorded_by_fkey`: `FOREIGN KEY (recorded_by) REFERENCES app_user(id)`

Index:

- `CREATE INDEX ix_history_case ON public.patient_history USING btree (case_id, recorded_at DESC)`
- `CREATE UNIQUE INDEX patient_history_pkey ON public.patient_history USING btree (id)`

Trigger:

- `history_audit`: `CREATE TRIGGER history_audit AFTER INSERT OR DELETE OR UPDATE ON public.patient_history FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `history_revision`: `CREATE TRIGGER history_revision AFTER INSERT OR DELETE OR UPDATE ON public.patient_history FOR EACH ROW EXECUTE FUNCTION bump_case_revision()`
- `history_staff_validate`: `CREATE TRIGGER history_staff_validate BEFORE INSERT OR UPDATE ON public.patient_history FOR EACH ROW EXECUTE FUNCTION validate_staff_record()`

## patient_measurement

Chỉ số tự nhập tại nhà; không tự trở thành dữ liệu đã được nhân viên xác minh (FR-P03).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| case_id | uuid | Không |  | Hồ sơ bệnh nhân liên quan. |
| recorded_by | uuid | Không |  | Người ghi nhận dữ liệu. |
| observed_at | timestamp with time zone | Không |  | Thời điểm đo/đánh giá. |
| systolic_bp | numeric | Có |  | Huyết áp tâm thu, mmHg; phải nhập cùng tâm trương. |
| diastolic_bp | numeric | Có |  | Huyết áp tâm trương, mmHg. |
| heart_rate | numeric | Có |  | Nhịp tim, bpm. |
| weight_kg | numeric | Có |  | Cân nặng, kg. |
| spo2 | numeric | Có |  | Độ bão hòa oxy, %. Giới hạn biểu diễn 0–100. |
| temperature_c | numeric | Có |  | Nhiệt độ, độ C. |
| symptoms | character varying(500) | Có |  | Triệu chứng/ghi chú tự nhập, tối đa 500 ký tự. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `patient_measurement_case_id_fkey`: `FOREIGN KEY (case_id) REFERENCES patient_case(id)`
- `patient_measurement_check`: `CHECK ((num_nonnulls(systolic_bp, diastolic_bp, heart_rate, weight_kg, spo2, temperature_c, symptoms) > 0))`
- `patient_measurement_check1`: `CHECK ((((systolic_bp IS NULL) AND (diastolic_bp IS NULL)) OR ((systolic_bp IS NOT NULL) AND (diastolic_bp IS NOT NULL) AND (systolic_bp >= diastolic_bp))))`
- `patient_measurement_diastolic_bp_check`: `CHECK (((diastolic_bp > (0)::numeric) AND ((diastolic_bp)::text <> ALL (ARRAY['NaN'::text, 'Infinity'::text, '-Infinity'::text]))))`
- `patient_measurement_heart_rate_check`: `CHECK (((heart_rate > (0)::numeric) AND ((heart_rate)::text <> ALL (ARRAY['NaN'::text, 'Infinity'::text, '-Infinity'::text]))))`
- `patient_measurement_pkey`: `PRIMARY KEY (id)`
- `patient_measurement_recorded_by_fkey`: `FOREIGN KEY (recorded_by) REFERENCES patient_account(user_id)`
- `patient_measurement_spo2_check`: `CHECK ((((spo2 >= (0)::numeric) AND (spo2 <= (100)::numeric)) AND ((spo2)::text <> ALL (ARRAY['NaN'::text, 'Infinity'::text, '-Infinity'::text]))))`
- `patient_measurement_symptoms_check`: `CHECK (((symptoms IS NULL) OR (length(TRIM(BOTH FROM symptoms)) > 0)))`
- `patient_measurement_systolic_bp_check`: `CHECK (((systolic_bp > (0)::numeric) AND ((systolic_bp)::text <> ALL (ARRAY['NaN'::text, 'Infinity'::text, '-Infinity'::text]))))`
- `patient_measurement_temperature_c_check`: `CHECK (((temperature_c > '-273.15'::numeric) AND ((temperature_c)::text <> ALL (ARRAY['NaN'::text, 'Infinity'::text, '-Infinity'::text]))))`
- `patient_measurement_weight_kg_check`: `CHECK (((weight_kg > (0)::numeric) AND ((weight_kg)::text <> ALL (ARRAY['NaN'::text, 'Infinity'::text, '-Infinity'::text]))))`

Index:

- `CREATE INDEX ix_patient_measurement_time ON public.patient_measurement USING btree (case_id, observed_at DESC)`
- `CREATE UNIQUE INDEX patient_measurement_pkey ON public.patient_measurement USING btree (id)`

Trigger:

- `measurement_audit`: `CREATE TRIGGER measurement_audit AFTER INSERT ON public.patient_measurement FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `patient_measurement_immutable`: `CREATE TRIGGER patient_measurement_immutable BEFORE DELETE OR UPDATE ON public.patient_measurement FOR EACH ROW EXECUTE FUNCTION prevent_mutation()`
- `patient_measurement_validate`: `CREATE TRIGGER patient_measurement_validate BEFORE INSERT ON public.patient_measurement FOR EACH ROW EXECUTE FUNCTION validate_patient_measurement()`

RLS:

- `patient_measurement_create`: INSERT; USING ``; WITH CHECK `((case_id = portal_case_id()) AND (recorded_by = current_app_user()))`.
- `patient_measurement_read`: SELECT; USING `(case_id = portal_case_id())`; WITH CHECK ``.

## permission

Danh mục quyền đặc biệt, gồm quyền phê duyệt chuyên môn rule.approve (FR-05).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| code | character varying(60) | Không |  | Mã danh mục/quy tắc. |
| description | text | Không |  | Mô tả nội dung. |

Ràng buộc bảng:

- `permission_pkey`: `PRIMARY KEY (code)`

Index:

- `CREATE UNIQUE INDEX permission_pkey ON public.permission USING btree (code)`

## pharmacist_review

Nhận xét và đề xuất của dược sĩ được phân công về một lần đánh giá (FR-30).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| evaluation_id | uuid | Không |  | Lần đánh giá liên quan. |
| pharmacist_id | uuid | Không |  | Dược sĩ nhận xét. |
| comment | text | Không |  | Nhận xét dược sĩ. |
| proposal | text | Có |  | Đề xuất để bác sĩ xem xét. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `pharmacist_review_comment_check`: `CHECK ((length(TRIM(BOTH FROM comment)) > 0))`
- `pharmacist_review_evaluation_id_fkey`: `FOREIGN KEY (evaluation_id) REFERENCES evaluation(id)`
- `pharmacist_review_pharmacist_id_fkey`: `FOREIGN KEY (pharmacist_id) REFERENCES app_user(id)`
- `pharmacist_review_pkey`: `PRIMARY KEY (id)`

Index:

- `CREATE INDEX ix_review_evaluation ON public.pharmacist_review USING btree (evaluation_id)`
- `CREATE UNIQUE INDEX pharmacist_review_pkey ON public.pharmacist_review USING btree (id)`

Trigger:

- `pharmacist_review_validate`: `CREATE TRIGGER pharmacist_review_validate BEFORE INSERT OR UPDATE ON public.pharmacist_review FOR EACH ROW EXECUTE FUNCTION validate_review_plan()`
- `review_audit`: `CREATE TRIGGER review_audit AFTER INSERT OR UPDATE ON public.pharmacist_review FOR EACH ROW EXECUTE FUNCTION audit_record_change()`

## prescription

Đơn thuốc do bác sĩ xác nhận; ngày dùng và múi giờ; bản xác nhận được giữ bất biến (FR-13,32,FR-P04).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| case_id | uuid | Không |  | Hồ sơ bệnh nhân liên quan. |
| encounter_id | uuid | Không |  | Lần khám/đợt điều trị liên quan. |
| doctor_id | uuid | Không |  | Bác sĩ phụ trách/xác nhận. |
| status | character varying(12) | Không | 'draft'::character varying | Trạng thái; các giá trị hợp lệ được ghi trong CHECK bên dưới. |
| starts_on | date | Không |  | Ngày bắt đầu dùng. |
| ends_on | date | Có |  | Ngày kết thúc nếu có. |
| timezone | character varying(60) | Không | 'Asia/Ho_Chi_Minh'::character varying | Múi giờ IANA của các giờ uống; mặc định Asia/Ho_Chi_Minh. |
| instructions | text | Không | ''::text | Hướng dẫn dạng văn bản. |
| confirmed_at | timestamp with time zone | Có |  | Thời điểm bác sĩ xác nhận đơn. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `prescription_case_id_fkey`: `FOREIGN KEY (case_id) REFERENCES patient_case(id)`
- `prescription_check`: `CHECK (((ends_on IS NULL) OR (ends_on >= starts_on)))`
- `prescription_check1`: `CHECK (((((status)::text = 'draft'::text) AND (confirmed_at IS NULL)) OR (((status)::text <> 'draft'::text) AND (confirmed_at IS NOT NULL))))`
- `prescription_doctor_id_fkey`: `FOREIGN KEY (doctor_id) REFERENCES app_user(id)`
- `prescription_encounter_id_case_id_fkey`: `FOREIGN KEY (encounter_id, case_id) REFERENCES encounter(id, case_id)`
- `prescription_id_encounter_id_key`: `UNIQUE (id, encounter_id)`
- `prescription_pkey`: `PRIMARY KEY (id)`
- `prescription_status_check`: `CHECK (((status)::text = ANY ((ARRAY['draft'::character varying, 'confirmed'::character varying, 'cancelled'::character varying])::text[])))`

Index:

- `CREATE INDEX ix_prescription_case ON public.prescription USING btree (case_id, created_at DESC)`
- `CREATE UNIQUE INDEX prescription_id_encounter_id_key ON public.prescription USING btree (id, encounter_id)`
- `CREATE UNIQUE INDEX prescription_pkey ON public.prescription USING btree (id)`

Trigger:

- `prescription_audit`: `CREATE TRIGGER prescription_audit AFTER INSERT OR UPDATE ON public.prescription FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `prescription_cancel_reminders`: `CREATE TRIGGER prescription_cancel_reminders AFTER UPDATE ON public.prescription FOR EACH ROW EXECUTE FUNCTION cancel_prescription_reminders()`
- `prescription_guard`: `CREATE TRIGGER prescription_guard BEFORE INSERT OR UPDATE ON public.prescription FOR EACH ROW EXECUTE FUNCTION guard_prescription()`

RLS:

- `patient_prescription_read`: SELECT; USING `((case_id = portal_case_id()) AND ((status)::text = ANY ((ARRAY['confirmed'::character varying, 'cancelled'::character varying])::text[])))`; WITH CHECK ``.

## recommendation

Gợi ý/cảnh báo có mức độ và nguồn tham chiếu; không tự tạo y lệnh (FR-21..29).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| module_result_id | uuid | Không |  | Kết quả module liên quan. |
| code | character varying(80) | Không |  | Mã danh mục/quy tắc. |
| severity | character varying(12) | Không |  | Mức info, warning hoặc critical. |
| description | text | Không |  | Mô tả nội dung. |
| source_ref | text | Không |  | Nguồn tham chiếu của nội dung. |

Ràng buộc bảng:

- `recommendation_module_result_id_fkey`: `FOREIGN KEY (module_result_id) REFERENCES module_result(id)`
- `recommendation_pkey`: `PRIMARY KEY (id)`
- `recommendation_severity_check`: `CHECK (((severity)::text = ANY ((ARRAY['info'::character varying, 'warning'::character varying, 'critical'::character varying])::text[])))`

Index:

- `CREATE INDEX ix_recommendation_result ON public.recommendation USING btree (module_result_id)`
- `CREATE UNIQUE INDEX recommendation_pkey ON public.recommendation USING btree (id)`

## result_missing_field

Các chỉ số còn thiếu cho một kết quả module (FR-18,29).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| module_result_id | uuid | Không |  | Kết quả module liên quan. |
| field_code | character varying(60) | Không |  | Mã chỉ số/trường dữ liệu. |

Ràng buộc bảng:

- `result_missing_field_field_code_fkey`: `FOREIGN KEY (field_code) REFERENCES observation_type(code)`
- `result_missing_field_module_result_id_fkey`: `FOREIGN KEY (module_result_id) REFERENCES module_result(id)`
- `result_missing_field_pkey`: `PRIMARY KEY (module_result_id, field_code)`

Index:

- `CREATE UNIQUE INDEX result_missing_field_pkey ON public.result_missing_field USING btree (module_result_id, field_code)`

## role

Năm vai trò: doctor, nurse, pharmacist, admin, patient (FR-03,FR-P01).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| code | character varying(20) | Không |  | Mã danh mục/quy tắc. |

Ràng buộc bảng:

- `role_code_check`: `CHECK (((code)::text = ANY ((ARRAY['doctor'::character varying, 'nurse'::character varying, 'pharmacist'::character varying, 'admin'::character varying, 'patient'::character varying])::text[])))`
- `role_pkey`: `PRIMARY KEY (code)`

Index:

- `CREATE UNIQUE INDEX role_pkey ON public.role USING btree (code)`

## rule_approval

Bằng chứng duyệt nội dung đã kiểm thử, hash, người duyệt có quyền và thời điểm (FR-05).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| rule_version_id | uuid | Không |  | Phiên bản quy tắc liên quan. |
| approval_ref | text | Không |  | Tham chiếu bằng chứng phê duyệt. |
| approved_content_hash | character varying(64) | Không |  | Hash của nội dung được duyệt. |
| approved_at | timestamp with time zone | Không |  | Thời điểm duyệt. |
| recorded_by | uuid | Không |  | Người ghi nhận dữ liệu. |

Ràng buộc bảng:

- `rule_approval_approval_ref_check`: `CHECK ((length(TRIM(BOTH FROM approval_ref)) > 0))`
- `rule_approval_approved_content_hash_check`: `CHECK (((approved_content_hash)::text ~ '^[a-f0-9]{64}$'::text))`
- `rule_approval_pkey`: `PRIMARY KEY (rule_version_id)`
- `rule_approval_recorded_by_fkey`: `FOREIGN KEY (recorded_by) REFERENCES app_user(id)`
- `rule_approval_rule_version_id_fkey`: `FOREIGN KEY (rule_version_id) REFERENCES rule_version(id)`

Index:

- `CREATE UNIQUE INDEX rule_approval_pkey ON public.rule_approval USING btree (rule_version_id)`

Trigger:

- `approval_audit`: `CREATE TRIGGER approval_audit AFTER INSERT ON public.rule_approval FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `rule_approval_immutable`: `CREATE TRIGGER rule_approval_immutable BEFORE DELETE OR UPDATE ON public.rule_approval FOR EACH ROW EXECUTE FUNCTION prevent_mutation()`
- `rule_approval_validate`: `CREATE TRIGGER rule_approval_validate BEFORE INSERT ON public.rule_approval FOR EACH ROW EXECUTE FUNCTION validate_approval()`

## rule_required_field

Chỉ số bắt buộc của phiên bản quy tắc; giữ nguyên từ trạng thái tested (FR-18).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| rule_version_id | uuid | Không |  | Phiên bản quy tắc liên quan. |
| field_code | character varying(60) | Không |  | Mã chỉ số/trường dữ liệu. |

Ràng buộc bảng:

- `rule_required_field_field_code_fkey`: `FOREIGN KEY (field_code) REFERENCES observation_type(code)`
- `rule_required_field_pkey`: `PRIMARY KEY (rule_version_id, field_code)`
- `rule_required_field_rule_version_id_fkey`: `FOREIGN KEY (rule_version_id) REFERENCES rule_version(id)`

Index:

- `CREATE UNIQUE INDEX rule_required_field_pkey ON public.rule_required_field USING btree (rule_version_id, field_code)`

Trigger:

- `required_field_guard`: `CREATE TRIGGER required_field_guard BEFORE INSERT OR DELETE OR UPDATE ON public.rule_required_field FOR EACH ROW EXECUTE FUNCTION guard_required_fields()`

## rule_version

Nội dung JSON, hash SHA-256, module, nguồn và vòng đời phiên bản quy tắc (FR-05).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| code | character varying(60) | Không |  | Mã danh mục/quy tắc. |
| version | integer | Không |  | Số phiên bản quy tắc. |
| module | character varying(20) | Không |  | Module diagnosis, lab_test, treatment hoặc medsafety. |
| source_ref | text | Không |  | Nguồn tham chiếu của nội dung. |
| content_hash | character varying(64) | Không |  | SHA-256 của chuỗi JSONB content chuẩn hóa bởi PostgreSQL. |
| content | jsonb | Không | '{}'::jsonb | Nội dung ghi nhận hoặc JSONB; xem kiểu và ràng buộc của bảng. |
| status | character varying(12) | Không | 'draft'::character varying | Trạng thái; các giá trị hợp lệ được ghi trong CHECK bên dưới. |
| created_by | uuid | Không |  | Người tạo phiên bản. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `rule_version_code_version_key`: `UNIQUE (code, version)`
- `rule_version_content_check`: `CHECK ((jsonb_typeof(content) = 'object'::text))`
- `rule_version_content_hash_check`: `CHECK (((content_hash)::text ~ '^[a-f0-9]{64}$'::text))`
- `rule_version_created_by_fkey`: `FOREIGN KEY (created_by) REFERENCES app_user(id)`
- `rule_version_module_check`: `CHECK (((module)::text = ANY ((ARRAY['diagnosis'::character varying, 'lab_test'::character varying, 'treatment'::character varying, 'medsafety'::character varying])::text[])))`
- `rule_version_pkey`: `PRIMARY KEY (id)`
- `rule_version_status_check`: `CHECK (((status)::text = ANY ((ARRAY['draft'::character varying, 'tested'::character varying, 'approved'::character varying, 'active'::character varying, 'retired'::character varying])::text[])))`
- `rule_version_version_check`: `CHECK ((version > 0))`

Index:

- `CREATE UNIQUE INDEX rule_version_code_version_key ON public.rule_version USING btree (code, version)`
- `CREATE UNIQUE INDEX rule_version_pkey ON public.rule_version USING btree (id)`
- `CREATE UNIQUE INDEX ux_rule_active ON public.rule_version USING btree (code) WHERE ((status)::text = 'active'::text)`

Trigger:

- `rule_activation_guard`: `CREATE TRIGGER rule_activation_guard BEFORE INSERT OR UPDATE ON public.rule_version FOR EACH ROW EXECUTE FUNCTION guard_rule_activation()`
- `rule_audit`: `CREATE TRIGGER rule_audit AFTER INSERT OR UPDATE ON public.rule_version FOR EACH ROW EXECUTE FUNCTION audit_record_change()`

## test_report

Báo cáo xét nghiệm, siêu âm, ECG hoặc thăm dò, có thời điểm và nguồn (FR-12).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| encounter_id | uuid | Không |  | Lần khám/đợt điều trị liên quan. |
| kind | character varying(10) | Không |  | Loại bản ghi; xem CHECK của bảng. |
| performed_at | timestamp with time zone | Không |  | Thời điểm thực hiện xét nghiệm/thăm dò. |
| source | character varying(30) | Không |  | Nguồn nhập giả lập hoặc nguồn mô phỏng. |
| external_ref | text | Có |  | Mã bản tin/báo cáo/batch nguồn giả lập. |
| content | jsonb | Không |  | Nội dung ghi nhận hoặc JSONB; xem kiểu và ràng buộc của bảng. |
| recorded_by | uuid | Không |  | Người ghi nhận dữ liệu. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |

Ràng buộc bảng:

- `test_report_content_check`: `CHECK ((jsonb_typeof(content) = 'object'::text))`
- `test_report_encounter_id_fkey`: `FOREIGN KEY (encounter_id) REFERENCES encounter(id)`
- `test_report_kind_check`: `CHECK (((kind)::text = ANY ((ARRAY['lab'::character varying, 'echo'::character varying, 'ecg'::character varying, 'other'::character varying])::text[])))`
- `test_report_pkey`: `PRIMARY KEY (id)`
- `test_report_recorded_by_fkey`: `FOREIGN KEY (recorded_by) REFERENCES app_user(id)`
- `test_report_source_check`: `CHECK (((source)::text = ANY ((ARRAY['manual_synthetic'::character varying, 'mock_his'::character varying, 'mock_lis'::character varying, 'mock_pacs'::character varying, 'mock_emr'::character varying])::text[])))`

Index:

- `CREATE INDEX ix_test_report_encounter ON public.test_report USING btree (encounter_id, performed_at DESC)`
- `CREATE UNIQUE INDEX test_report_pkey ON public.test_report USING btree (id)`

Trigger:

- `report_audit`: `CREATE TRIGGER report_audit AFTER INSERT OR DELETE OR UPDATE ON public.test_report FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `report_revision`: `CREATE TRIGGER report_revision AFTER INSERT OR DELETE OR UPDATE ON public.test_report FOR EACH ROW EXECUTE FUNCTION bump_case_revision()`
- `report_staff_validate`: `CREATE TRIGGER report_staff_validate BEFORE INSERT OR UPDATE ON public.test_report FOR EACH ROW EXECUTE FUNCTION validate_staff_record()`

## treatment_plan

Kế hoạch điều trị, theo dõi, ra viện hoặc tái khám do bác sĩ nhập (FR-32).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| id | uuid | Không | gen_random_uuid() | Định danh nội bộ UUID. |
| encounter_id | uuid | Không |  | Lần khám/đợt điều trị liên quan. |
| doctor_id | uuid | Không |  | Bác sĩ phụ trách/xác nhận. |
| decision_id | uuid | Có |  | Quyết định gốc nếu kế hoạch dùng kết quả hỗ trợ. |
| kind | character varying(12) | Không |  | Loại bản ghi; xem CHECK của bảng. |
| content | text | Không |  | Nội dung ghi nhận hoặc JSONB; xem kiểu và ràng buộc của bảng. |
| follow_up_at | timestamp with time zone | Có |  | Thời điểm tái khám dự kiến. |
| status | character varying(12) | Không | 'draft'::character varying | Trạng thái; các giá trị hợp lệ được ghi trong CHECK bên dưới. |
| created_at | timestamp with time zone | Không | now() | Thời điểm tạo. |
| updated_at | timestamp with time zone | Không | now() | Thời điểm cập nhật gần nhất. |

Ràng buộc bảng:

- `treatment_plan_content_check`: `CHECK ((length(TRIM(BOTH FROM content)) > 0))`
- `treatment_plan_decision_id_fkey`: `FOREIGN KEY (decision_id) REFERENCES clinical_decision(id)`
- `treatment_plan_doctor_id_fkey`: `FOREIGN KEY (doctor_id) REFERENCES app_user(id)`
- `treatment_plan_encounter_id_fkey`: `FOREIGN KEY (encounter_id) REFERENCES encounter(id)`
- `treatment_plan_kind_check`: `CHECK (((kind)::text = ANY ((ARRAY['treatment'::character varying, 'monitoring'::character varying, 'discharge'::character varying, 'follow_up'::character varying])::text[])))`
- `treatment_plan_pkey`: `PRIMARY KEY (id)`
- `treatment_plan_status_check`: `CHECK (((status)::text = ANY ((ARRAY['draft'::character varying, 'confirmed'::character varying, 'cancelled'::character varying])::text[])))`

Index:

- `CREATE INDEX ix_plan_encounter ON public.treatment_plan USING btree (encounter_id, created_at DESC)`
- `CREATE UNIQUE INDEX treatment_plan_pkey ON public.treatment_plan USING btree (id)`

Trigger:

- `plan_audit`: `CREATE TRIGGER plan_audit AFTER INSERT OR UPDATE ON public.treatment_plan FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `treatment_plan_validate`: `CREATE TRIGGER treatment_plan_validate BEFORE INSERT OR UPDATE ON public.treatment_plan FOR EACH ROW EXECUTE FUNCTION validate_review_plan()`

## user_permission

Cấp quyền đặc biệt theo tài khoản; admin không tự có quyền phê duyệt chuyên môn (FR-05).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| user_id | uuid | Không |  | Tài khoản liên quan. |
| permission_code | character varying(60) | Không |  | Mã quyền đặc biệt. |

Ràng buộc bảng:

- `user_permission_permission_code_fkey`: `FOREIGN KEY (permission_code) REFERENCES permission(code)`
- `user_permission_pkey`: `PRIMARY KEY (user_id, permission_code)`
- `user_permission_user_id_fkey`: `FOREIGN KEY (user_id) REFERENCES app_user(id)`

Index:

- `CREATE UNIQUE INDEX user_permission_pkey ON public.user_permission USING btree (user_id, permission_code)`

Trigger:

- `permission_audit`: `CREATE TRIGGER permission_audit AFTER INSERT OR DELETE OR UPDATE ON public.user_permission FOR EACH ROW EXECUTE FUNCTION audit_record_change()`

## user_role

Các vai trò tài khoản; tài khoản bệnh nhân tách khỏi tài khoản nhân viên (FR-03,FR-P01).

| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |
|---|---|---|---|---|
| user_id | uuid | Không |  | Tài khoản liên quan. |
| role_code | character varying(20) | Không |  | Mã vai trò. |

Ràng buộc bảng:

- `user_role_pkey`: `PRIMARY KEY (user_id, role_code)`
- `user_role_role_code_fkey`: `FOREIGN KEY (role_code) REFERENCES role(code)`
- `user_role_user_id_fkey`: `FOREIGN KEY (user_id) REFERENCES app_user(id)`

Index:

- `CREATE UNIQUE INDEX user_role_pkey ON public.user_role USING btree (user_id, role_code)`

Trigger:

- `role_audit`: `CREATE TRIGGER role_audit AFTER INSERT OR DELETE OR UPDATE ON public.user_role FOR EACH ROW EXECUTE FUNCTION audit_record_change()`
- `user_role_validate`: `CREATE TRIGGER user_role_validate BEFORE INSERT OR UPDATE ON public.user_role FOR EACH ROW EXECUTE FUNCTION validate_roles()`

## Chuẩn hóa và snapshot

Vai trò, quyền, hồ sơ, lần khám, danh mục chỉ số, thuốc, giờ uống và nhắc theo ngày có bảng riêng. Ngày/giờ uống không được ghép thành chuỗi trong bản ghi thuốc. Múi giờ thuộc đơn; thời điểm nhắc được suy ra từ ngày, giờ uống và múi giờ.

`evaluation.input_snapshot` là bản sao bất biến để truy vết, không phải nguồn cập nhật. `audit_event.entity_id` là liên kết đa hình, trigger ghi đối tượng đang thay đổi; không dùng FK tới một bảng duy nhất. Không tuyên bố các payload JSONB tự đạt 3NF.
