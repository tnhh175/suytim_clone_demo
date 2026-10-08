# Ma trận truy vết yêu cầu (RTM)

**Mốc:** 08/10/2026 · **Phạm vi:** SRS v1.0: FR-01..34, FR-P01..04, NFR-01..13. Đây là đối chiếu trạng thái trong clone_demo, không phải biên bản nghiệm thu.

## Quy ước

- **Có schema** là có bảng/ràng buộc SQL; Gateway hiện kết nối PostgreSQL qua role runtime giới hạn.
- **Có route/contract** là có handler hoặc OpenAPI; không xác nhận lưu bền vững hay nghiệp vụ hoàn chỉnh.
- **Chưa triển khai** là cần API, UI hoặc xử lý bổ sung.
- Kết quả kiểm thử ghi trong mốc cuối của tài liệu này; không suy rộng PGlite thành PostgreSQL 16 thực tế.
- Giao diện đã có trong [web/](../web/); các trang chưa có API chỉ hiển thị trạng thái/chức năng được hỗ trợ.

## 1. Hiện trạng

| Lớp | Bằng chứng | Trạng thái |
|---|---|---|
| Yêu cầu | [SRS v1.0](SRS_v1.0.md) có 34 FR, 4 FR-P, 13 NFR; BDD/User Stories/Use Case/DFD còn thiếu. | Không suy ra hoàn thành từ yêu cầu. |
| Dữ liệu | [schema.sql](../database/schema.sql), seed và quyền portal. | PostgreSQL 16 Compose; Gateway dùng runtime DB role và patient RLS. |
| Mapping | [source_mapping.md](../database/source_mapping.md) ánh xạ FR sang schema. | RTM mở rộng tới API/UI/test. |
| API | [openapi.yaml](../api/openapi.yaml), sinh từ ứng dụng. | DB-backed auth/clinical/rules/portal; bốn module lâm sàng luôn stub. |
| Gateway | [main.py](../src/gateway/main.py), clinical/auth/rules/portal routers. | FastAPI, PostgreSQL, năm role; kiểm quyền theo vai trò và scope. |
| Module | Bốn adapter trả mock_not_evaluated, không có gợi ý y khoa. | Bắt buộc giữ stub và recommendations rỗng trong demo. |
| Kiểm thử | Gateway unit/API tests và database PGlite tests trong thư mục tests. | Xem lệnh/kết quả kiểm tra cuối trong [README kỹ thuật](../README_TUAN3.md); chưa thay thế kiểm chứng PostgreSQL 16 bằng Compose. |
| QA baseline | `001_result_integrity.sql`, auth/clinical/rules routers và scope tests. | Baseline findings đã được xử lý trong code/migration; kết quả regression và giới hạn môi trường ghi ở lần kiểm tra cuối. |

## 2. Truy vết chức năng

Bảng dưới phản ánh hiện trạng tích hợp trong demo; “chưa hỗ trợ” là phần SRS còn cần triển khai, không phải route giả lập.

| Mã | Schema, thực thể và ràng buộc | API hiện có / dự kiến | UI đích | Test/acceptance hiện tại |
|---|---|---|---|---|
| FR-01 | app_user: username UNIQUE, password_hash, active; auth_session: token_hash UNIQUE, expiry, revoke. | POST token, logout và GET me dùng PBKDF2/hash session trong PostgreSQL. | Đăng nhập năm role demo. | Có test auth/session; chưa phải xác thực production. |
| FR-02 | app_user.active; user_role; user/role audit. | Chưa CRUD; dự kiến /admin/users GET/POST/PATCH, khóa/mở. | Admin: tài khoản/vai trò. | Chưa có API/UI test CRUD. |
| FR-03 | user_role; case_access clinical/nursing/medsafety; patient_account và RLS. | Route kiểm role và scope; admin không mặc định xem hồ sơ; pharmacist chỉ medsafety scope. | Menu theo role, API vẫn là lớp bảo vệ quyền. | Unit tests role/scope; cần chạy ma trận tích hợp với DB thật. |
| FR-04 | department, observation_type, ingredient, drug_product; FK/active/unit/value_kind/domain; chặn đổi định nghĩa catalog đã dùng. | Chưa API; dự kiến GET/POST/PATCH catalogs. | Admin: khoa, chỉ số/đơn vị, thuốc/hoạt chất. | DB test chống đổi định nghĩa đã dùng; chưa test CRUD API/UI. |
| FR-05 | rule_version code+version UNIQUE, content_hash; rule_required_field; rule_approval hash; user_permission.rule.approve; workflow/status trigger. | GET/POST /rule-versions, POST test/activate. Activate hiện bị chặn nếu thiếu approval; chưa có approve API. | Admin soạn/test; approver có permission duyệt riêng. | test_rule_guard và DB approval/hash test. Seed không có rule lâm sàng active. |
| FR-06 | patient_case mã SYN duy nhất, owner doctor, revision. | GET/POST cases và GET/PUT case được lưu PostgreSQL; PUT cần expected_revision. | Bác sĩ tạo, xem, sửa hồ sơ synthetic. | Có API tests; coverage DB integration được ghi ở kết quả kiểm tra cuối. |
| FR-07 | encounter FK case/department/doctor, kind/status/time CHECK. | GET danh sách/chi tiết và POST encounter được hỗ trợ; tạo cần revision. | Bác sĩ tạo encounter, điều dưỡng đọc trong scope. | Có API tests; chưa có update/close encounter. |
| FR-08 | patient_history theo case, kind, recorded_by/time, FK. | Chưa API; dự kiến GET/POST tiền sử/comorbidity. | Doctor: tiền sử. | Chưa API/acceptance test. |
| FR-09 | observation, clinical_note.kind=nursing, case_access.nursing. | GET/POST observations và notes theo scope; điều dưỡng chỉ ghi allowlist nursing và `kind=nursing`. | Điều dưỡng xem ca, ghi observation/chăm sóc synthetic. | Có unit/API tests; chưa nghiệm thu trên PostgreSQL 16 Compose. |
| FR-10 | clinical_note.kind examination/diagnosis, encounter FK, staff scope. | Chưa API; dự kiến clinical-notes. | Doctor: khám/chẩn đoán do người ghi. | Chưa test API; module không tạo diagnosis. |
| FR-11 | Catalog observation frailty/cognition/ADL/IADL/nutrition/fall risk; clinical_note geriatric. Thang đo chưa chuẩn hóa. | Chưa API riêng; dùng observation/note sau khi chốt catalog. | Doctor: đánh giá lão khoa. | Chưa test; mã hóa/thang đo còn mở. |
| FR-12 | observation + test_report lab/echo/ecg, source, performed_at, external_ref, encounter FK. | Observation route một phần; test_report API chưa có. Dự kiến /encounters/{id}/reports. | Doctor: cận lâm sàng và nguồn/thời điểm. | Gateway test subset observation; chưa test report route. |
| FR-13 | medication và prescription/schedule có constraint riêng. | Encounter có GET/POST medication synthetic; patient chỉ đọc prescription đã seed/xác nhận. Chưa có API tạo/xác nhận prescription/schedule. | Bác sĩ ghi bản ghi medication; portal đọc đơn. | Có API tests cho medication và DB tests schedule; không tạo đơn từ stub. |
| FR-14 | allergy_status unknown/none/known; reaction chỉ khi known; ingredient FK. | Chưa API; dự kiến allergy status/reaction. | Doctor: dị ứng/phản ứng thuốc. | Có SQL guard; chưa test route/acceptance riêng. |
| FR-15 | Encounter/observation/medication có index thời gian; patient_measurement tách khỏi observation. | /cases/{id}/history hiện chỉ evaluation/decision; dự kiến clinical timeline/compare. | Doctor: diễn biến theo thời gian, có nhãn nguồn. | Test lịch sử evaluation có; chưa test so sánh lâm sàng/UI. |
| FR-16 | import_batch có source/file, external_ref UNIQUE, counts/status; import_error theo dòng/trường. | Chưa upload/parser API; dự kiến POST imports và GET errors. | Staff được cấp quyền: nhập file và lỗi dòng/trường. | Seed có fixture batch/error; chưa parser/API/UI test. |
| FR-17 | import_batch, test_report, observation có source/external_ref và FK encounter. | Chưa adapter/ingest API; payload nguồn và mapping định danh chưa chốt. | Staff nạp/xem dữ liệu; admin cấu hình nguồn nếu cần. | Chưa test nguồn ngoài. |
| FR-18 | observation_type kiểm kiểu/unit/domain; observation CHECK status/value và trigger; FK; rule_required_field/result_missing_field. | Pydantic chỉ validate tập demo; dự kiến API+DB validation và 422 theo trường. | Form lâm sàng báo trường sai/thiếu. | test_validation_and_stale_decision, test_extra_fields_unknown_and_expiry; DB test một số miền. Chưa bao phủ tất cả field. |
| FR-19 | evaluation snapshot/revision; result children và recommendation. | POST/GET evaluations lưu DB nhưng chỉ tạo `mock_not_evaluated`, không gọi rule lâm sàng. | Doctor/dược sĩ thấy rõ chưa đánh giá. | Có stub/immutability tests; không có gold cases lâm sàng. |
| FR-20 | rule_version có module/content/hash; approval gắn content hash. | Rule CRUD/schema-test/approve/activate được bảo vệ; evaluation không thực thi rules. | Admin soạn/test; duyệt dùng quyền riêng; không hiện phenotype. | Có API/DB status/hash tests; không có rule engine đã duyệt. |
| FR-21 | module_result lab_test; recommendation có severity/source_ref. | Evaluation có Lab/Test adapter stub, list rỗng. | Doctor: Lab/Test không hiển thị chỉ định giả. | Test workflow chỉ kiểm stub, không test gợi ý thật. |
| FR-22 | test_report.performed_at, observation.observed_at. | Chưa dedup; evaluation stub. | Doctor: chỉ hiển thị trùng lặp khi có rule được duyệt. | Chưa có test dedup/gold case. |
| FR-23 | module_result treatment, recommendation; decision/plan riêng do người ghi. | Evaluation stub; không tự tạo plan/đơn. | Doctor: Treatment ghi rõ chưa đánh giá; plan là thao tác riêng. | Test workflow yêu cầu recommendation rỗng; chưa test điều trị. |
| FR-24 | Medication dose là dữ liệu; rule_version lưu rule được duyệt; recommendation nguồn. Schema không xác định liều. | Không có gợi ý thuốc/liều thật. | Doctor: không có đề xuất thuốc/liều module. | Chưa rule/gold case; không nghiệm thu liều. |
| FR-25 | Lịch sử observation/medication, rule version, evaluation snapshot. | Chưa logic tăng/chỉnh liều; stub. | Doctor: xem lịch sử, không gợi ý tăng liều. | Chưa test lâm sàng. |
| FR-26 | medication/ingredient/product, allergy_status, drug_reaction; module_result medsafety. | Pharmacist gọi riêng MedSafety stub; chưa checker tương tác. | Pharmacist: rà thuốc ở trạng thái stub; doctor xem dữ liệu. | test_auth_and_roles kiểm quyền gọi MedSafety; không kiểm tương tác. |
| FR-27 | recommendation severity/source_ref và observation; chưa có ngưỡng chuẩn seed. | Chưa cảnh báo; evaluation stub. | Doctor/pharmacist: không hiện nguy cơ giả như cảnh báo thật. | Chưa ngưỡng được duyệt hoặc test. |
| FR-28 | Medication dose/unit/product; recommendation source_ref. Schema không đánh giá liều. | Chưa kiểm liều; evaluation stub. | Doctor/pharmacist: không hiện đánh giá liều. | Chưa rule/test liều. |
| FR-29 | evaluation snapshot; module_result/recommendation/missing fields; result-child integrity migration. | Evaluation/decision lưu PostgreSQL, mọi module giữ `mock_not_evaluated`; migration khóa cây kết quả sau decision. | Hiện rõ trạng thái chưa đánh giá lâm sàng. | Có migration regression tests; chưa có kết quả lâm sàng được thẩm định. |
| FR-30 | pharmacist_review evaluation/pharmacist/comment; trigger yêu cầu pharmacist có medsafety scope. | Chưa API; dự kiến POST pharmacist-reviews theo scope. | Pharmacist ghi review; doctor đọc. | Chưa route/test; chỉ có SQL constraint. |
| FR-31 | clinical_decision append-only, reason, adjustment_details và stale guard. | POST decision dùng DB; action adjusted bắt buộc chi tiết điều chỉnh. | Chỉ là quyết định demo, không phải y lệnh. | Có API/DB tests về duplicate, revision và validation. |
| FR-32 | treatment_plan encounter/doctor/decision; prescription/appointment state/FK. | Chưa API plan/đơn đầy đủ. Dự kiến plans/prescriptions confirm/cancel. | Doctor: plan, discharge, follow-up, prescription. | Seed có fixture; DB tests đơn/reminder; chưa route/UI. |
| FR-33 | evaluation snapshot/input_revision; DB triggers tăng revision và chặn stale decision. | POST/GET evaluation/history dùng DB; quyết định trên snapshot cũ bị từ chối. | Lịch sử demo theo phiên bản dữ liệu. | Có regression tests; cần verify trên PostgreSQL 16 thật. |
| FR-34 | audit_event actor/action/entity/time; append-only. | GET audit chỉ admin; DB audit events được ghi bởi trigger/service. | Admin xem nhật ký kỹ thuật. | Có API tests; coverage tích hợp DB cần xác nhận trong lần kiểm tra cuối. |
| FR-P01 | patient_account một user/one case; portal_case_id/RLS. | Patient đăng nhập bằng session DB; cổng chỉ nhận case gắn với tài khoản. | Portal bệnh nhân riêng. | Có DB isolation và API role tests; không phải danh tính thật. |
| FR-P02 | Appointment slot/unique/state/RLS constraints. | Patient đọc, yêu cầu và hủy lịch chưa hoàn thành; staff confirm/complete chưa được hỗ trợ. | Lịch hẹn synthetic. | Có DB tests; API/UI patient routes được thêm, cần xác nhận tích hợp cuối. |
| FR-P03 | patient_measurement riêng, validation và RLS; không nhập vào observation. | Patient đọc/ghi chỉ số tự khai gắn với case của mình. | Trang chỉ số tại nhà, giữ nhãn bệnh nhân tự nhập. | Có DB/API validation tests; không sinh khuyến cáo. |
| FR-P04 | Prescription/schedule/reminder constraints, timezone và RLS. | Patient đọc prescription/reminders và phản hồi pending thành taken/skipped; không có worker/notification thật. | Trang đơn và nhắc thuốc synthetic. | DB/API tests; worker, gửi notification và CRUD đơn chưa hỗ trợ. |

## 3. Truy vết NFR

| Mã | Schema/ràng buộc | API/điểm triển khai | UI đích | Kiểm thử/acceptance |
|---|---|---|---|---|
| NFR-01 | role, user_role, case_access, portal RLS/grants. | Các router kiểm actor+scope; patient dùng role DB giới hạn. | Điều hướng và dữ liệu theo năm role. | Có unit/API tests; cần ma trận PG16 end-to-end. |
| NFR-02 | password_hash; auth_session token_hash/expiry/revoked; PBKDF2 seed. | Session DB lưu hash, revoke và hết hạn; không log token/password. | Login không hiển thị bí mật. | Có auth tests; tài khoản chung chỉ dùng demo local. |
| NFR-03 | Không được đảm bảo bởi schema. | OpenAPI local HTTP; cần HTTPS/TLS khi qua mạng. | Không có trang riêng. | Chưa cấu hình/kiểm chứng deployment. |
| NFR-04 | FK/composite FK/CHECK/trigger. | API trả 422/409, không nhận tham chiếu sai. | Chỉ trường lỗi và cách sửa, không lộ stack/input nhạy cảm. | Gateway validation, SQL parse và DB tests hiện có; chưa bao phủ mọi API với DB thật. |
| NFR-05 | PostgreSQL persistent storage. | Gateway thao tác DB theo transaction và pool; Compose khai báo PostgreSQL 16. | Chỉ xác nhận ghi khi request thành công. | Unit/DB tests; chưa xác nhận container runtime nếu Docker không khả dụng. |
| NFR-06 | Không có constraint schema đo hiệu năng. | Search/query và index cần đo. | Tìm hồ sơ đạt SRS. | Chưa benchmark; cần p95 ≤2 giây, 10 user, 1.000 hồ sơ, ghi cấu hình. |
| NFR-07 | Không có time constraint trong DB. | Evaluation cần timeout/trạng thái lỗi; stub không phải workload thực. | Báo timeout, không chờ vô hạn. | Chưa đo; ngưỡng ≤10 giây trên bộ thử đã chốt. |
| NFR-08 | Không trực tiếp schema; response cần case/encounter IDs và revision. | Case/evaluation giữ context đang thao tác. | Banner mã case+encounter; lỗi rõ trường/cách sửa. | Chưa frontend/browser test. |
| NFR-09 | Snapshot, rule_version/hash, module_result, source_ref, missing fields; migration khóa result tree sau decision. | Kết quả demo chỉ STUB-0.1/mock_not_evaluated; không hiển thị confidence lâm sàng. | Trạng thái rõ, không confidence giả. | Có integrity tests; chưa có rule/gold case lâm sàng. |
| NFR-10 | mock_not_evaluated/insufficient_data; decision riêng; prescription bác sĩ xác nhận; stale chặn. | Stub phải gợi ý rỗng, không tự tạo plan/đơn. | Nhãn demo/chưa đánh giá, không thao tác điều trị tự động. | Test workflow/EF-alone bảo vệ stub; chưa test lâm sàng. |
| NFR-11 | Schema có thể dump/restore, chưa có quy trình. | Cần backup/restore và đối chiếu dữ liệu/liên kết. | Không có UI nghiệp vụ. | Chưa restore test; mục tiêu ≤30 phút. |
| NFR-12 | Rule version/hash/status và required-field guard; result child tree bất biến sau decision. | Sửa rule bằng version mới; approval kiểm hash, evaluation không thực thi rule. | Admin/approver theo permission riêng. | Rule/approval/immutability tests có; engine lâm sàng chưa triển khai. |
| NFR-13 | Không schema. | UI gọi API đúng version. | Chrome/Edge, 1366px và 768px, nút không bị che. | Chưa có frontend/browser test. |

## 4. Phần SRS còn mở

1. FR-02/04: CRUD người dùng, role và danh mục chưa được cung cấp.
2. FR-08, FR-10..12, FR-14..18, FR-22..28, FR-30, FR-32: tiền sử, báo cáo/import, allergy, pharmacist review, engine lâm sàng và các workflow liên quan chưa hoàn chỉnh. Bốn module giữ stub.
3. FR-P02/04: nhân viên chưa có workflow xác nhận/hủy prescription/appointment; reminder worker/notification chưa có.
4. NFR hiệu năng, browser compatibility, backup/restore và deployment HTTPS chưa được benchmark/nghiệm thu.
5. Những kết quả test chưa chạy trong môi trường PostgreSQL 16/Docker phải được ghi rõ là unit/PGlite, không coi là xác nhận production.