# ERD — mô hình cập nhật theo SRS và cổng bệnh nhân

Schema hiện tại có **39 bảng**. Các sơ đồ Mermaid dưới đây chia theo nghiệp vụ; một thực thể xuất hiện lại vẫn là cùng bảng. Danh sách đầy đủ cột, FK, CHECK, index, trigger và RLS nằm trong [metadata](schema_metadata.json) và [từ điển dữ liệu](data_dictionary.md). Các ảnh ERD PNG tuần 3 mô tả phiên bản 18 bảng cũ, không phản ánh phần mở rộng này.

## Tài khoản, hồ sơ, lần khám và bệnh nhân

```mermaid
erDiagram
  department o|--o{ app_user : belongs_to
  app_user ||--o{ user_role : has
  role ||--o{ user_role : assigns
  app_user ||--o{ user_permission : granted
  permission ||--o{ user_permission : grants
  app_user ||--o{ auth_session : opens
  app_user ||--o{ patient_case : doctor_owner
  patient_case ||--o| patient_account : patient_login
  app_user ||--o| patient_account : linked
  patient_case ||--o{ case_access : grants
  app_user ||--o{ case_access : receives
  patient_case ||--o{ encounter : has
  department ||--o{ encounter : treats
  app_user ||--o{ encounter : doctor
  patient_case ||--o{ appointment : books
  app_user ||--o{ appointment : doctor_or_requester
  encounter o|--o{ appointment : completed_visit
  patient_case ||--o{ patient_measurement : home_readings
  patient_account ||--o{ patient_measurement : records
```

`patient_account` có UNIQUE trên hồ sơ và PK trên tài khoản; FK đến vai trò `patient`. Tài khoản bệnh nhân không được gán vai trò nhân viên. Lịch hẹn có UNIQUE có điều kiện cho `(doctor_id, slot_at)` và `(case_id, slot_at)` khi còn chờ/xác nhận. Chỉ số tự nhập thuộc hồ sơ, tách khỏi số liệu theo lần khám.

## Dữ liệu lâm sàng và nguồn nhập

```mermaid
erDiagram
  patient_case ||--o{ patient_history : history
  patient_case ||--o| allergy_status : allergy_state
  allergy_status ||--o{ drug_reaction : known_reactions
  ingredient ||--o{ drug_reaction : causes
  encounter ||--o{ clinical_note : notes
  encounter ||--o{ observation : measurements
  observation_type ||--o{ observation : catalog
  encounter ||--o{ test_report : reports
  encounter ||--o{ import_batch : imports
  import_batch ||--o{ import_error : errors
```

Ghi chú phân loại chăm sóc, khám, chẩn đoán và lão khoa. Dị ứng phân biệt `unknown`, `none`, `known`. Từng giá trị observation có loại/status/nguồn/thời điểm và liên kết người ghi; đơn vị chuẩn thuộc catalog. Mọi bảng này tham chiếu nhân viên ghi dữ liệu, không thể nhận UUID người dùng không tồn tại.

## Đơn thuốc, giờ uống và nhắc uống

```mermaid
erDiagram
  patient_case ||--o{ prescription : prescribed_for
  encounter ||--o{ prescription : issued_at
  app_user ||--o{ prescription : doctor_confirms
  ingredient ||--o{ drug_product : products
  ingredient ||--o{ medication : ingredient
  drug_product o|--o{ medication : optional_product
  encounter ||--o{ medication : list
  prescription o|--o{ medication : prescribed_items
  medication ||--o{ medication_schedule : daily_clock_times
  medication_schedule ||--o{ medication_reminder : per_date
```

FK ghép giữ đúng hoạt chất/sản phẩm và đơn/lần khám/hồ sơ. Giờ uống nằm ở thuốc trong đơn; số giờ phải bằng tần suất trước xác nhận. Múi giờ và khoảng ngày ở đơn/thuốc quyết định `due_at`. UNIQUE `(schedule_id, scheduled_on)` chống nhắc trùng. Đơn xác nhận giữ bất biến; hủy đơn hủy nhắc đang chờ.

## Quy tắc, đánh giá và quyết định

```mermaid
erDiagram
  rule_version ||--o| rule_approval : approval
  rule_version ||--o{ rule_required_field : needs
  observation_type ||--o{ rule_required_field : required_input
  encounter ||--o{ evaluation : evaluates
  evaluation ||--o{ module_result : results
  rule_version o|--o{ module_result : explains
  module_result ||--o{ recommendation : suggests
  module_result ||--o{ result_missing_field : missing
  observation_type ||--o{ result_missing_field : field
  evaluation ||--o{ pharmacist_review : reviewed
  evaluation ||--o| clinical_decision : doctor_decides
  encounter ||--o{ treatment_plan : plans
  clinical_decision o|--o{ treatment_plan : accepted_basis
  app_user o|--o{ audit_event : user_actor
```

Phê duyệt yêu cầu quyền riêng và hash của nội dung đã tested. Snapshot đánh giá, quyết định và audit bất biến. Kế hoạch liên kết quyết định được chấp nhận/điều chỉnh của đúng lần khám khi dùng kết quả hỗ trợ; bác sĩ cũng có thể nhập kế hoạch độc lập. Seed chỉ tạo kết quả stub và rule draft, không tự sinh đơn từ gợi ý.

RLS của cổng bệnh nhân và luồng SQL mẫu được mô tả trong [README database](README.md). Gateway ứng dụng hiện tại chưa nối PostgreSQL.
