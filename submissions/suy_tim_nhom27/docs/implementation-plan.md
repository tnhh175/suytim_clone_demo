# Kế hoạch hiện thực và tích hợp

**Mục tiêu:** đưa clone_demo tới demo web có phân quyền, nối PostgreSQL và luồng synthetic kiểm tra được; bốn module lâm sàng vẫn stub/mock_not_evaluated.
**Phạm vi:** submissions/suy_tim_nhom27 trên nhánh demo riêng. Sơ đồ microservice là đích thiết kế, không phải service đang chạy.

## 1. Mốc và kiến trúc đích

### Hiện trạng

- Schema PostgreSQL có 39 bảng; seed năm role và dữ liệu synthetic. portal_permissions.sql tạo hf_patient_portal NOLOGIN, không owner, không BYPASSRLS, grant giới hạn.
- Gateway FastAPI gom route trong main.py, model trong models.py, adapter trong services.py và MemoryStore trong store.py. Dữ liệu RAM.
- OpenAPI 3.0.3 sinh từ FastAPI; 17 path/22 thao tác, nhưng API chưa kết nối PostgreSQL. Auth hiện có doctor/pharmacist/admin; nurse/patient chỉ có trong SQL.
- Không thấy mã frontend. SRS chưa hoàn thiện BDD/User Story/Use Case. FR-P01..04 mới có SQL/schema/seed/RLS.
- QA baseline c2076c3 phát hiện result child rows mutable, rule linkage không buộc cùng module/status, Gateway adjusted decision có thể thiếu adjustment_details và pharmacist đọc mọi ca synthetic.

Dùng modular monolith FastAPI với router/service/repository tách theo miền. Chưa cần tách bốn dịch vụ mạng. Giữ interface module nhưng bốn adapter luôn trả mock_not_evaluated, không có clinical_recommendations.

~~~mermaid
flowchart LR
  UI[Web pages by role] --> API[FastAPI routers]
  API --> AUTH[Identity and case-scope checks]
  AUTH --> SVC[Domain services]
  SVC --> REPO[Transactions and repositories]
  REPO --> DB[(PostgreSQL)]
  SVC --> STUB[Four module ports: mock_not_evaluated]
  DB --> AUDIT[Append-only audit and snapshots]
~~~

- Mọi request xác thực ở server; kiểm role và phạm vi trước repository, mặc định từ chối và không trả hồ sơ khi sai quyền.
- Ghi nghiệp vụ và audit trong cùng transaction. Chỉ báo thành công sau commit.
- Portal đặt app.user_id theo identity phiên bằng SET LOCAL và dùng SET LOCAL ROLE hf_patient_portal trong transaction. Không chạy patient request bằng owner/superuser/BYPASSRLS; không giữ DB identity qua pooled connection.
- patient_measurement tách khỏi observation đã xác minh.
- rule.approve tách khỏi admin; approval chỉ khi nội dung tested và hash khớp.
- Rule status theo schema draft/tested/approved/active/retired. Không tự thêm pending_review từ tài liệu cũ.
- Diagnosis, Lab/Test, Treatment, MedSafety giữ message “chưa đánh giá lâm sàng”, status mock_not_evaluated và recommendations/cảnh báo rỗng. Không tạo lời khuyên/thuốc/liều/chẩn đoán/phân tầng/nguy cơ có vẻ thật.

## 2. Ma trận vai trò

Ẩn control trên UI không thay thế authorization ở API. Tất cả trang UI là dự kiến, chưa tồn tại.

| Vai trò | Phạm vi đích | Trang UI đích | Contract hiện có |
|---|---|---|---|
| Bác sĩ | Ca sở hữu hoặc case_access clinical; encounter, clinical data, thuốc/đơn, evaluation stub, decision/plan, xác nhận/hủy đơn. Không tự duyệt rule nếu thiếu permission. | Login; tìm hồ sơ; hồ sơ/lịch sử; encounter; khám/CLS/thuốc/dị ứng/lão khoa; kết quả stub; decision; plan/đơn. | Case/encounter/observation/medication/evaluation/decision/history/export một phần; RAM. |
| Điều dưỡng | case_access nursing; sinh hiệu, cân nặng, triệu chứng, nursing note; không diagnosis/decision/đơn. | Danh sách ca được giao; chăm sóc; sinh hiệu/diễn biến; nhập dữ liệu. | Không Gateway account/endpoint; role/scope có trong schema. |
| Dược sĩ | case_access medsafety; đọc thuốc/dữ liệu cần thiết, gọi riêng MedSafety stub, ghi pharmacist_review; không decision/plan/đơn. | Hàng đợi rà thuốc; chi tiết nguồn; nhận xét gửi bác sĩ. | MedSafety riêng trong route evaluation; hiện quyền đọc mọi case synthetic; chưa có review route. |
| Quản trị kỹ thuật | Tài khoản/role/scope/catalog/rule/audit; không clinical scope mặc định. | User/quyền; khoa/catalog; rule draft/test; audit. | Có rules GET/POST/test/activate và audit GET; chưa CRUD user/catalog. |
| Bệnh nhân | Một user gắn một case; lịch, số tự nhập, đơn confirmed và reminder của mình. Không đọc encounter/decision/note hoặc sửa thuốc/liều/giờ. | Cổng patient; lịch hẹn; số đo tại nhà; đơn/giờ uống. | Chưa login/API/UI; DB có patient_account/RLS/grants. |
| Người có rule.approve | Permission riêng cho người đủ chuyên môn; duyệt content/hash tested, không phải role thứ năm. | Trang duyệt rule riêng. | SQL/permission có; seed cấp riêng cho user demo; approve API chưa có. |

## 3. Hợp đồng API và phụ thuộc

Prefix /api/v1, JSON, UUID, ISO 8601 có timezone. Lỗi chung: 401/403/404/409/422. Đổi route/model phải sinh lại OpenAPI từ source, không sửa YAML riêng.

| Route có hiện tại | Giới hạn hiện tại |
|---|---|
| GET /health | Chỉ process health, chưa DB readiness. |
| POST /auth/token | DEMO_PASSWORD chung, token opaque trong RAM, không revoke/session bền vững. |
| GET/POST /cases; GET/PUT /cases/{id} | Doctor-only, MemoryStore. |
| POST /cases/{id}/encounters; GET /encounters/{id} | RAM, chưa update/close. |
| GET/POST /encounters/{id}/observations; GET/POST /encounters/{id}/medications | Tập demo, doctor-only; medication chưa prescription/schedule. |
| POST/GET /evaluations; POST /evaluations/{id}/decisions | Snapshot/decision RAM; bốn result mock. Pharmacist chỉ gọi MedSafety. |
| GET /cases/{id}/history; GET /cases/{id}/export | History evaluation/decision, không phải timeline clinical đầy đủ. |
| GET/POST /rule-versions; POST /rule-versions/{id}/test,/activate | Admin soạn/test; activation bị chặn nếu thiếu approval. |
| GET /audit-events | Audit RAM, admin-only. |

Các route dưới là dự kiến, chưa implement:

| Lát cắt | Hợp đồng dự kiến | Dữ liệu/quyền phụ thuộc |
|---|---|---|
| Identity | POST /auth/logout; GET /auth/me; GET/POST/PATCH /admin/users; gán role/scope; POST /rule-versions/{id}/approve | app_user, user_role, user_permission, auth_session; hash/revoke; audit; rule.approve riêng admin. |
| Hồ sơ/clinical | Encounter PATCH/complete; history/comorbidity; clinical-notes; reports; allergy/reactions; prescriptions/medications/schedules; treatment-plans | patient_case, encounter, observation, clinical_note, test_report, medication, allergy_status, drug_reaction, treatment_plan; UUID/FK/revision. |
| Catalog | GET/POST/PATCH khoa, observation type, ingredient, drug product | department, observation_type, ingredient, drug_product; review unit/value_kind change. |
| Import/integration | POST /encounters/{id}/imports; GET /imports/{id}/errors; ingest endpoint cho mock source | import_batch/import_error/test_report/observation; chốt template/unit/external_ref/idempotency trước. |
| Evaluation/rules | Giữ evaluation/decision; thêm pharmacist review và approve | evaluation/module_result/recommendation/result_missing_field; rule_version/rule_approval; validate rule association; stub outputs remain empty. |
| Patient portal | GET /patient/me; GET/POST appointments; cancel; staff confirm/complete; GET/POST measurements; GET prescriptions/reminders; respond taken/skipped | patient_account, portal RLS/role, appointment, patient_measurement, prescription/schedule/reminder. |
| Audit/operations | Giữ audit GET, phân trang/lọc; health DB riêng; backup/restore | audit_event append-only, transaction, operations. |

### Trình tự phụ thuộc

1. **Đóng contract:** chốt SRS/schema baseline, role/scope, errors, pagination, file import, appointment state. Không chốt clinical thresholds/dose.
2. **Identity/scope:** session hash/revoke, RBAC/case_access, DB identity. Chưa mở portal trước RLS cross-account test.
3. **Persistence:** PostgreSQL repository/transaction cho case, encounter, clinical data, medications, decision, audit; báo thành công sau commit.
4. **Patient portal:** router/repository riêng bằng hf_patient_portal; appointment/measurement/prescription/reminder. Worker local nếu cần; không SMS/email/push.
5. **UI:** sau khi OpenAPI ổn định; login/case context trước, rồi doctor/nurse/pharmacist/admin/patient.
6. **Nghiệm thu:** chạy gates mục 7. Bốn module giữ mock. Chỉ xem xét rule thật sau khi chốt chuyên gia, nguồn, approval và gold cases.

## 4. Ranh giới file khi chia việc

Gateway hiện dồn route ở main.py và model ở models.py. Tách router theo miền trước khi nhiều người làm; một integrator giữ app assembly/OpenAPI.

| Stream | File riêng đề xuất | Tránh xung đột |
|---|---|---|
| Identity | Tạo routers/auth.py, services/identity.py, repositories/identity.py, schemas/identity.py, tests/test_auth.py | Không sửa main.py, models.py, openapi.yaml. Bàn giao Actor/Session interface. |
| Authorization | Tạo authorization.py và tests/test_authorization.py; policy chỉ sau review | Không cấp scope mặc định cho admin; phối hợp auth owner. |
| Clinical CRUD | Tạo routers/cases.py, routers/clinical.py, repositories/cases.py, repositories/clinical.py, services/clinical.py, schemas/clinical.py, tests/test_clinical_api.py | Dùng schema hiện có; không sửa metadata/SQL trực tiếp; UUID/revision. |
| Rules/evaluation | Tạo routers/evaluations.py hoặc routers/rules.py, services/evaluation.py, services/rule_workflow.py, test riêng | Không sửa services.py registry, main.py, models.py; adapter vẫn stub/no recommendation. |
| Patient portal | Tạo routers/patient_portal.py, services/patient_portal.py, repositories/patient_portal.py, schemas/patient_portal.py, tests/test_patient_portal.py | Phụ thuộc auth owner và hf_patient_portal trong transaction; không dùng DB owner. |
| Frontend | Tạo web/index.html, web/assets/styles.css, web/src/api.js và các script/module JavaScript theo vai trò | Vanilla HTML/CSS/JS đã chốt; không thêm framework hay build chain. Chỉ dùng OpenAPI đã chốt; không chỉnh backend model; hiển thị stub đúng mức. |
| Integrator | Chỉ một owner sửa main.py, app factory/router registration, models.py, spec.py, scripts/export_openapi.py | Ghép từng interface/test rồi sinh api/openapi.yaml. |
| Schema/migration | Một owner; migration SQL mới và đồng bộ schema.sql, seed.sql, portal_permissions.sql, dictionary/metadata, database tests | Không cho auth/clinical/portal streams cùng sửa SQL/RLS. |

Không đổi tên bảng/enum trong lúc các stream chạy. Thiếu cột/quyền thì change riêng kèm lý do, migration, seed/metadata và DB tests.

## 5. Bảo mật, dữ liệu và safety

- Chỉ dữ liệu synthetic: SYN-*, users demo, thuốc/hoạt chất giả. Không đưa PII thật vào seed/log/screenshot/test.
- Server token là nguồn user_id; bỏ qua user_id/role/case_id client gửi. Patient và staff là tài khoản tách biệt.
- Portal dùng SET LOCAL app.user_id và SET LOCAL ROLE hf_patient_portal trong transaction. Không dùng table owner/superuser/BYPASSRLS; grant tối thiểu, không đọc app_user/password hash/audit hoặc ghi clinical.
- Case access kiểm role lẫn scope, default deny. Pharmacist chỉ ca medsafety được giao; không giữ ngoại lệ “mọi case synthetic”. Admin kỹ thuật không tự xem hồ sơ.
- Write/decision/prescription/audit dùng transaction; snapshot/decision/audit/measurement/approval immutable. Đơn đã xác nhận đổi bằng hủy và lập đơn mới.
- patient_measurement không thành observation đã xác minh; mọi trang staff hiển thị nhãn “bệnh nhân tự ghi”.
- rule.approve riêng và hash phải khớp bản tested; admin soạn/test không tự duyệt.
- QA baseline c2076c3: module_result/recommendation/result_missing_field mutable sau decision. Thêm DB guard/service invariant và test chống update/delete sau chốt.
- QA baseline: module_result.rule_version_id chưa buộc cùng module hoặc rule status hợp lệ. Validate association trước khi lưu result; không dùng draft/sai module.
- DecisionInput hiện chỉ action/reason. Bổ sung adjustment_details bắt buộc cho adjusted ở API và giữ SQL CHECK; DB chưa nằm trên luồng runtime.
- Bốn module luôn trả mock_not_evaluated, message minh bạch, recommendations/cảnh báo rỗng. Không lời khuyên, liều, ngưỡng hay chẩn đoán minh họa có vẻ thật.

## 6. Unknowns cần chốt

1. **Đã chốt với nhóm:** frontend dùng vanilla HTML/CSS/JS, không framework hoặc build chain. Tổ chức trang/script theo vai trò trong web/ và ghép theo OpenAPI.
2. Login/logout: bearer hay cookie, expiry/revoke, CSRF/CORS và user nào đăng nhập patient portal.
3. Quy trình cấp case_access và staff xác nhận/hoàn thành appointment chưa đủ chi tiết.
4. FR-16: CSV/XLSX, cột, unit, encoding, duplicate/upsert, upload size. FR-17: payload/external_ref/mapping patient-encounter.
5. Ai sửa catalog và cách version hóa code đã dùng trong observation/rule.
6. Chưa có rule y khoa, reviewer/gold labels; không thể nghiệm thu FR-19..28/NFR-09 từ stub.
7. BDD/User Story/Use Case chưa có mã đã chốt; không tự tạo.
8. HTTPS, backup/restore, secret deployment, benchmark 10 user/1.000 case chưa có bằng chứng.
9. Seed patient_demo và credential demo chỉ dùng local.
10. consistency_review.md và architecture.md còn mô tả ba role theo snapshot SRS cũ; cần đồng bộ riêng theo SRS 08/10 và schema hiện tại.

## 7. Test gates trước nghiệm thu

Đây là kế hoạch, chưa chạy trong phase tài liệu. Kết quả lịch sử ở docs/verification.md và database/README.md không được xem là tái xác nhận.

| Gate | Bằng chứng cần có |
|---|---|
| G1 Contract/API | Sinh và validate OpenAPI; route 401/403/404/409/422; không lộ secret; không tin role/scope client. |
| G2 Identity/scope | Password/token/session hash, inactive/expiry/revoke, log redaction; role × action × case scope; patient/staff tách biệt. |
| G3 DB/integrity | Bootstrap/seed replay; FK/CHECK/trigger, composite case-encounter, revision/rollback, audit cùng transaction, restart persistence. Test result child immutable sau decision; rule link cùng module/status; adjusted phải có adjustment_details. |
| G4 Portal | RLS isolation, locked/missing identity, slot 30 phút/duplicate/state, BP theo cặp/ít nhất một field, home data không thành observation, đơn/timezone/reminder/cancel. |
| G5 Stub/safety | 4 module mock_not_evaluated, recommendations rỗng, EF-alone không phenotype, thiếu data không thành bình thường/âm tính, không tự tạo đơn/plan. |
| G6 Rule/trace | Approval permission/hash; version không sửa; result module/status/version hợp lệ; snapshot/result child immutable; adjusted cần reason + adjustment_details. |
| G7 UI | Luồng role, case/encounter context, lỗi tại field, patient source label, Chrome/Edge 1366px/768px. |
| G8 NFR ops | p95 xem/tìm ≤2 giây ở 10 user/1.000 case; evaluation ≤10 giây; HTTPS qua mạng; backup/restore ≤30 phút và dữ liệu/liên kết khớp. Ghi cấu hình/artefact. |

**Điều kiện gọi là demo tích hợp:** G1–G7 có bằng chứng mới; Gateway lưu PostgreSQL; quyền kiểm tra ở API và RLS; UI gọi API; bốn module hiển thị chưa đánh giá. Báo riêng trạng thái NFR tải/TLS/backup; không suy từ unit test hoặc SQL parser.
