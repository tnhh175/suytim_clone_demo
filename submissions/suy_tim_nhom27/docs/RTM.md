# Ma trận truy vết yêu cầu (RTM)

**Mốc:** 08/10/2026 · **Phạm vi:** SRS v1.0: FR-01..34, FR-P01..04, NFR-01..13. Đây là đối chiếu trạng thái trong clone_demo, không phải biên bản nghiệm thu.

## Quy ước

- **Có schema** là có bảng/ràng buộc SQL, không đồng nghĩa Gateway đang dùng PostgreSQL.
- **Có route/contract** là có handler hoặc OpenAPI; không xác nhận lưu bền vững hay nghiệp vụ hoàn chỉnh.
- **Chưa triển khai** là cần API, UI hoặc xử lý bổ sung.
- Test source và kết quả lịch sử không được coi là lần chạy hiện tại. Phase tài liệu này không chạy test.
- Tên trang UI là đích đề xuất; hiện không có mã frontend trong thư mục submission.

## 1. Hiện trạng

| Lớp | Bằng chứng | Trạng thái |
|---|---|---|
| Yêu cầu | [SRS v1.0](SRS_v1.0.md) có 34 FR, 4 FR-P, 13 NFR; BDD/User Stories/Use Case/DFD còn thiếu. | Không suy ra hoàn thành từ yêu cầu. |
| Dữ liệu | [schema.sql](../database/schema.sql) có 39 bảng; [seed.sql](../database/seed.sql), [portal_permissions.sql](../database/portal_permissions.sql). | DB/RLS đã có, Gateway chưa kết nối. |
| Mapping | [source_mapping.md](../database/source_mapping.md) ánh xạ FR sang schema. | RTM mở rộng tới API/UI/test. |
| API | [openapi.yaml](../api/openapi.yaml): 17 path, 22 thao tác. | Contract sinh từ Gateway; một số thao tác là stub. |
| Gateway | [main.py](../src/gateway/main.py), [services.py](../src/gateway/services.py), [store.py](../src/gateway/store.py). | FastAPI một tiến trình, MemoryStore, ba role doctor/pharmacist/admin; pharmacist có thể đọc mọi ca synthetic trong demo. |
| Module | Bốn adapter trả mock_not_evaluated, không có gợi ý y khoa. | Bắt buộc giữ stub và recommendations rỗng trong demo. |
| Kiểm thử | [test_gateway.py](../tests/test_gateway.py): 8 test function RAM; [database.test.mjs](../database/tests/database.test.mjs): 19 test PGlite. | [verification.md](verification.md) ghi 8/8 Gateway test đạt ngày 28/09; database README ghi kiểm tra qua PGlite 18.3. Đây là kết quả lịch sử, không phải lần chạy phase này. |
| QA baseline | QA trên commit c2076c3 báo finding về result mutability, rule linkage, adjustment và quyền Gateway. | Các finding được nêu cụ thể ở mục 4; không ghi PASS chức năng ứng dụng. |

## 2. Truy vết chức năng

API “hiện có” chỉ là contract/handler hiện tại; đường dẫn “dự kiến” chưa được triển khai. UI là trang đích.

| Mã | Schema, thực thể và ràng buộc | API hiện có / dự kiến | UI đích | Test/acceptance hiện tại |
|---|---|---|---|---|
| FR-01 | app_user: username UNIQUE, password_hash, active; auth_session: token_hash UNIQUE, expiry, revoke. | POST /api/v1/auth/token dùng DEMO_PASSWORD chung và token RAM. Dự kiến logout/me/session DB. | Đăng nhập staff và portal. | test_auth_and_roles, test_extra_fields_unknown_and_expiry kiểm token RAM; DB test hash. Chưa test logout/session/log. |
| FR-02 | app_user.active; user_role; user/role audit. | Chưa CRUD; dự kiến /admin/users GET/POST/PATCH, khóa/mở. | Admin: tài khoản/vai trò. | Chưa có API/UI test CRUD. |
| FR-03 | user_role; case_access clinical/nursing/medsafety; can_access_case; patient_account và RLS. | Gateway kiểm role một phần; doctor chỉ owner, pharmacist hiện xem toàn bộ case synthetic. Dự kiến scope trên mọi route, API phân công. | Doctor ca được giao; nurse nursing-scope; pharmacist medsafety-scope; admin quản quyền, không xem case mặc định. | test_auth_and_roles chỉ kiểm role; DB test nurse scope và patient isolation. Thiếu route × role × scope. |
| FR-04 | department, observation_type, ingredient, drug_product; FK/active/unit/value_kind/domain; chặn đổi định nghĩa catalog đã dùng. | Chưa API; dự kiến GET/POST/PATCH catalogs. | Admin: khoa, chỉ số/đơn vị, thuốc/hoạt chất. | DB test chống đổi định nghĩa đã dùng; chưa test CRUD API/UI. |
| FR-05 | rule_version code+version UNIQUE, content_hash; rule_required_field; rule_approval hash; user_permission.rule.approve; workflow/status trigger. | GET/POST /rule-versions, POST test/activate. Activate hiện bị chặn nếu thiếu approval; chưa có approve API. | Admin soạn/test; approver có permission duyệt riêng. | test_rule_guard và DB approval/hash test. Seed không có rule lâm sàng active. |
| FR-06 | patient_case mã SYN duy nhất theo regex, age/sex CHECK, owner doctor FK, revision. | GET/POST /cases; GET/PUT /cases/{id}, RAM. Dự kiến nối DB/tìm kiếm. | Doctor: tìm/tạo/sửa hồ sơ synthetic. | test_case_code_generated_and_preserved; cấm patient_name trong test extra field. Chưa DB/UI test. |
| FR-07 | encounter FK case/department/doctor, kind/status/time CHECK, UNIQUE(id,case_id). | POST /cases/{id}/encounters; GET /encounters/{id}; chưa update/close. | Doctor: quản lý encounter/đợt điều trị. | test_full_workflow tạo encounter RAM; DB FK/state có. Chưa test update/close API. |
| FR-08 | patient_history theo case, kind, recorded_by/time, FK. | Chưa API; dự kiến GET/POST tiền sử/comorbidity. | Doctor: tiền sử. | Chưa API/acceptance test. |
| FR-09 | observation kiểu/nguồn/thời điểm/trạng thái; clinical_note.kind=nursing; case_access.nursing. | Observation GET/POST hiện doctor-only, RAM; dự kiến nurse scope và nursing notes. | Nurse: sinh hiệu, cân nặng, triệu chứng, diễn biến. | DB test nurse ghi vital signs ca được giao; không có nurse Gateway route/test. |
| FR-10 | clinical_note.kind examination/diagnosis, encounter FK, staff scope. | Chưa API; dự kiến clinical-notes. | Doctor: khám/chẩn đoán do người ghi. | Chưa test API; module không tạo diagnosis. |
| FR-11 | Catalog observation frailty/cognition/ADL/IADL/nutrition/fall risk; clinical_note geriatric. Thang đo chưa chuẩn hóa. | Chưa API riêng; dùng observation/note sau khi chốt catalog. | Doctor: đánh giá lão khoa. | Chưa test; mã hóa/thang đo còn mở. |
| FR-12 | observation + test_report lab/echo/ecg, source, performed_at, external_ref, encounter FK. | Observation route một phần; test_report API chưa có. Dự kiến /encounters/{id}/reports. | Doctor: cận lâm sàng và nguồn/thời điểm. | Gateway test subset observation; chưa test report route. |
| FR-13 | ingredient/product/medication; dose/unit/route/frequency/date CHECK; prescription/schedule; confirm yêu cầu số giờ = frequency; confirmed item bất biến. | Medications GET/POST hiện đơn giản/RAM; chưa prescription/schedule/confirm. | Doctor: thuốc/đơn; patient chỉ đọc đơn xác nhận. | DB test giờ uống/bất biến; Gateway test chỉ model medication. |
| FR-14 | allergy_status unknown/none/known; reaction chỉ khi known; ingredient FK. | Chưa API; dự kiến allergy status/reaction. | Doctor: dị ứng/phản ứng thuốc. | Có SQL guard; chưa test route/acceptance riêng. |
| FR-15 | Encounter/observation/medication có index thời gian; patient_measurement tách khỏi observation. | /cases/{id}/history hiện chỉ evaluation/decision; dự kiến clinical timeline/compare. | Doctor: diễn biến theo thời gian, có nhãn nguồn. | Test lịch sử evaluation có; chưa test so sánh lâm sàng/UI. |
| FR-16 | import_batch có source/file, external_ref UNIQUE, counts/status; import_error theo dòng/trường. | Chưa upload/parser API; dự kiến POST imports và GET errors. | Staff được cấp quyền: nhập file và lỗi dòng/trường. | Seed có fixture batch/error; chưa parser/API/UI test. |
| FR-17 | import_batch, test_report, observation có source/external_ref và FK encounter. | Chưa adapter/ingest API; payload nguồn và mapping định danh chưa chốt. | Staff nạp/xem dữ liệu; admin cấu hình nguồn nếu cần. | Chưa test nguồn ngoài. |
| FR-18 | observation_type kiểm kiểu/unit/domain; observation CHECK status/value và trigger; FK; rule_required_field/result_missing_field. | Pydantic chỉ validate tập demo; dự kiến API+DB validation và 422 theo trường. | Form lâm sàng báo trường sai/thiếu. | test_validation_and_stale_decision, test_extra_fields_unknown_and_expiry; DB test một số miền. Chưa bao phủ tất cả field. |
| FR-19 | evaluation snapshot/revision; module_result diagnosis; result_missing_field/recommendation; mock_not_evaluated không cần rule. | POST/GET evaluations trả stub, không thuật toán. module_result.rule_version_id chỉ FK, chưa bắt buộc rule active/approved hoặc module khớp. | Doctor: trạng thái “chưa đánh giá lâm sàng”. | test_full_workflow xác nhận mock và list rỗng; EF-alone test không sinh phenotype. |
| FR-20 | rule_version có module/content/hash; module_result/recommendation lưu liên kết; không có stage/phenotype chuẩn riêng. | Evaluation hiện stub; chưa rule. Cần validate status và module của rule association. | Doctor: Diagnosis chỉ nhãn chưa đánh giá. | Không có test thuật toán; EF-alone chỉ chặn kết luận sai. |
| FR-21 | module_result lab_test; recommendation có severity/source_ref. | Evaluation có Lab/Test adapter stub, list rỗng. | Doctor: Lab/Test không hiển thị chỉ định giả. | Test workflow chỉ kiểm stub, không test gợi ý thật. |
| FR-22 | test_report.performed_at, observation.observed_at. | Chưa dedup; evaluation stub. | Doctor: chỉ hiển thị trùng lặp khi có rule được duyệt. | Chưa có test dedup/gold case. |
| FR-23 | module_result treatment, recommendation; decision/plan riêng do người ghi. | Evaluation stub; không tự tạo plan/đơn. | Doctor: Treatment ghi rõ chưa đánh giá; plan là thao tác riêng. | Test workflow yêu cầu recommendation rỗng; chưa test điều trị. |
| FR-24 | Medication dose là dữ liệu; rule_version lưu rule được duyệt; recommendation nguồn. Schema không xác định liều. | Không có gợi ý thuốc/liều thật. | Doctor: không có đề xuất thuốc/liều module. | Chưa rule/gold case; không nghiệm thu liều. |
| FR-25 | Lịch sử observation/medication, rule version, evaluation snapshot. | Chưa logic tăng/chỉnh liều; stub. | Doctor: xem lịch sử, không gợi ý tăng liều. | Chưa test lâm sàng. |
| FR-26 | medication/ingredient/product, allergy_status, drug_reaction; module_result medsafety. | Pharmacist gọi riêng MedSafety stub; chưa checker tương tác. | Pharmacist: rà thuốc ở trạng thái stub; doctor xem dữ liệu. | test_auth_and_roles kiểm quyền gọi MedSafety; không kiểm tương tác. |
| FR-27 | recommendation severity/source_ref và observation; chưa có ngưỡng chuẩn seed. | Chưa cảnh báo; evaluation stub. | Doctor/pharmacist: không hiện nguy cơ giả như cảnh báo thật. | Chưa ngưỡng được duyệt hoặc test. |
| FR-28 | Medication dose/unit/product; recommendation source_ref. Schema không đánh giá liều. | Chưa kiểm liều; evaluation stub. | Doctor/pharmacist: không hiện đánh giá liều. | Chưa rule/test liều. |
| FR-29 | evaluation snapshot/time; module_result status/message/rule; recommendation source/severity; missing fields. QA baseline: module_result/recommendation/result_missing_field có thể bị sửa sau decision. | GET evaluation/history hiện RAM, mode=stub/STUB-0.1. Cần khóa child result sau decision. | Doctor/pharmacist: nhãn stub; không confidence giả. | Test workflow chỉ kiểm status/list rỗng; chưa test immutability hoặc traceability lâm sàng. |
| FR-30 | pharmacist_review evaluation/pharmacist/comment; trigger yêu cầu pharmacist có medsafety scope. | Chưa API; dự kiến POST pharmacist-reviews theo scope. | Pharmacist ghi review; doctor đọc. | Chưa route/test; chỉ có SQL constraint. |
| FR-31 | clinical_decision UNIQUE evaluation, action CHECK, reason và adjustment_details CHECK; append-only; chặn stale snapshot. | POST decisions hiện RAM. DecisionInput chỉ nhận action/reason, không có adjustment_details; SQL CHECK không bảo vệ runtime chưa nối DB. | Doctor: accept/adjust/reject; adjusted phải có chi tiết. | Tests hiện kiểm reason/duplicate/stale; chưa test adjusted thiếu adjustment_details ở Gateway. |
| FR-32 | treatment_plan encounter/doctor/decision; prescription/appointment state/FK. | Chưa API plan/đơn đầy đủ. Dự kiến plans/prescriptions confirm/cancel. | Doctor: plan, discharge, follow-up, prescription. | Seed có fixture; DB tests đơn/reminder; chưa route/UI. |
| FR-33 | evaluation snapshot/input_revision immutable; trigger tăng revision và chặn quyết định stale. Child result chưa bất biến sau decision theo QA. | POST/GET eval/history có contract; snapshot RAM. | Doctor: lịch sử eval theo phiên bản và input. | Test workflow/stale và DB revision; chưa test child mutation hoặc Gateway persistence. |
| FR-34 | audit_event actor/action/entity/time; triggers; UPDATE/DELETE bị chặn. | GET audit admin-only nhưng RAM; DB audit trigger riêng. | Admin: audit theo quyền. | Test workflow kiểm RAM event; DB append-only test; chưa xác nhận mọi route trên PG16. |
| FR-P01 | patient_account một user/one case; FK patient role; trigger tách patient/staff; active; portal_case_id/RLS. | Chưa login/API patient; hiện ba user demo staff. | Patient: portal chỉ một hồ sơ; khóa thì từ chối. | DB test locked/missing identity/isolation; chưa API/UI. |
| FR-P02 | Appointment slot %1800=0; partial UNIQUE doctor+slot, case+slot khi requested/confirmed; trigger tương lai/state; RLS theo case. | Chưa API; dự kiến patient GET/POST/cancel, staff confirm/complete. | Patient đặt/xem/hủy; staff xác nhận/hoàn thành. | DB duplicate/cancel/permission tests; chưa API/UI. |
| FR-P03 | patient_measurement riêng; ít nhất một giá trị; BP theo cặp; miền/future checks; account FK; append-only/RLS. Không nhập vào observation. | Chưa API; dự kiến patient GET/POST measurement; staff đọc có nhãn nguồn. | Patient nhập/xem; staff xem “bệnh nhân tự ghi”. | DB tests validation/isolation; chưa API/UI; không khuyến cáo từ fixture. |
| FR-P04 | Prescription confirmed/cancelled; schedule giờ duy nhất; số giờ = frequency; timezone; reminder pending→taken/skipped/cancelled; hủy đơn hủy nhắc pending; RLS. | Chưa API đọc đơn/reminder hoặc worker; dự kiến patient read/respond, worker sinh nhắc. Không notification thật. | Patient đơn/giờ uống/taken/skipped; doctor lập/xác nhận/hủy đơn. | DB tests timezone/response/cancel/immutability; chưa API/UI/worker. |

## 3. Truy vết NFR

| Mã | Schema/ràng buộc | API/điểm triển khai | UI đích | Kiểm thử/acceptance |
|---|---|---|---|---|
| NFR-01 | role, user_role, case_access, can_access_case, portal RLS/grants. | Mọi route phải kiểm actor+scope; hiện RBAC RAM một phần. | Mỗi role chỉ thấy ca/trang được cấp. | Gateway role tests và DB nurse/patient isolation có; thiếu toàn bộ ma trận endpoint/fail-closed. |
| NFR-02 | password_hash; auth_session token_hash/expiry/revoked; PBKDF2 seed. | Hiện DEMO_PASSWORD chung, token RAM; cần hash/revoke, không log secret. | Login không phản chiếu bí mật. | DB hash và Gateway expiry test có; chưa test logs/revoke. |
| NFR-03 | Không được đảm bảo bởi schema. | OpenAPI local HTTP; cần HTTPS/TLS khi qua mạng. | Không có trang riêng. | Chưa cấu hình/kiểm chứng deployment. |
| NFR-04 | FK/composite FK/CHECK/trigger. | API trả 422/409, không nhận tham chiếu sai. | Chỉ trường lỗi và cách sửa, không lộ stack/input nhạy cảm. | Gateway validation, SQL parse và DB tests hiện có; chưa bao phủ mọi API với DB thật. |
| NFR-05 | PostgreSQL bền vững nhưng Gateway hiện MemoryStore. | Repository/transaction, chỉ báo thành công sau commit. | Trạng thái saved sau DB commit. | Chưa Gateway-DB/restart test; seed replay khác kiểm tra persistence. |
| NFR-06 | Không có constraint schema đo hiệu năng. | Search/query và index cần đo. | Tìm hồ sơ đạt SRS. | Chưa benchmark; cần p95 ≤2 giây, 10 user, 1.000 hồ sơ, ghi cấu hình. |
| NFR-07 | Không có time constraint trong DB. | Evaluation cần timeout/trạng thái lỗi; stub không phải workload thực. | Báo timeout, không chờ vô hạn. | Chưa đo; ngưỡng ≤10 giây trên bộ thử đã chốt. |
| NFR-08 | Không trực tiếp schema; response cần case/encounter IDs và revision. | Case/evaluation giữ context đang thao tác. | Banner mã case+encounter; lỗi rõ trường/cách sửa. | Chưa frontend/browser test. |
| NFR-09 | Snapshot, rule_version/hash, module_result, source_ref, missing fields; nhưng result có thể mutable và rule linkage chưa buộc status/module đúng. | Hiện chỉ STUB-0.1/mock_not_evaluated; kết quả thật cần trace đầy đủ. | Không confidence giả; hiển thị source/version hợp lệ. | Chưa có rule/gold case; test stub chỉ check list rỗng. Cần test rule linkage/immutable. |
| NFR-10 | mock_not_evaluated/insufficient_data; decision riêng; prescription bác sĩ xác nhận; stale chặn. | Stub phải gợi ý rỗng, không tự tạo plan/đơn. | Nhãn demo/chưa đánh giá, không thao tác điều trị tự động. | Test workflow/EF-alone bảo vệ stub; chưa test lâm sàng. |
| NFR-11 | Schema có thể dump/restore, chưa có quy trình. | Cần backup/restore và đối chiếu dữ liệu/liên kết. | Không có UI nghiệp vụ. | Chưa restore test; mục tiêu ≤30 phút. |
| NFR-12 | Rule version/hash/status và required-field guard; evaluation append-only. Child result mutable; rule link chưa ràng buộc status/module. | Sửa bằng version mới; giữ kết quả cũ và child result bất biến. | Admin/approver quản phiên bản, result đọc version đã dùng. | Rule/approval/stale tests có; QA ghi finding mutable/linkage; chưa rule engine được duyệt. |
| NFR-13 | Không schema. | UI gọi API đúng version. | Chrome/Edge, 1366px và 768px, nút không bị che. | Chưa có frontend/browser test. |

## 4. Findings và điểm mở

1. QA baseline c2076c3 ghi nhận module_result, recommendation, result_missing_field có thể bị sửa sau clinical_decision. Cần guard/test bất biến trước khi coi FR-29/33 hoặc NFR-09/12 hoàn thành.
2. module_result.rule_version_id hiện chỉ FK, không buộc rule cùng module hoặc status được phép; phải từ chối draft/sai module.
3. DecisionInput chỉ có action/reason, không có adjustment_details. SQL CHECK yêu cầu adjustment cho action adjusted nhưng Gateway RAM bỏ qua; cần API validation cùng DB guard.
4. Gateway staff auth hiện ba role RAM; pharmacist được đọc mọi case synthetic. Chưa đáp ứng case_access least privilege.
5. FR-P01..04 hiện chỉ có SQL/schema/seed/RLS tests; chưa route/UI/auth tích hợp.
6. API README, consistency_review.md, architecture.md còn trạng thái từ snapshot SRS cũ ba role; SRS 08/10 và schema/seed hiện hành là nguồn ưu tiên.
7. SRS chưa có US/UC/BDD; không tự gán mã thay nhóm.
8. Rule status schema draft → tested → approved → active → retired; không có pending_review. Không tự thêm nếu chưa sửa SRS/migration.
9. Seed chỉ có rule draft và thuốc giả lập; không có rule/ngưỡng/liều/gold cases được chuyên môn duyệt. Không nghiệm thu FR-19..28 như tính năng y khoa.
10. Định dạng file/source, UI framework, session/logout, notifications, backup/restore và deployment HTTPS còn mở.
