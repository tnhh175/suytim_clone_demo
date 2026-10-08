# Từ điển dữ liệu kỹ thuật — tuần 3
PostgreSQL 16+. Bản thiết kế MVP của nhóm, không thay thế Data Dictionary chuyên môn của thầy. Cột không có NOT NULL/PK được phép null. PK/UNIQUE tự tạo index; các index bổ sung ghi dưới bảng. UUID dùng cho định danh; thời gian dùng timestamptz.

## app_user
Tài khoản; không chứa thông tin bệnh nhân

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PRIMARY KEY DEFAULT gen_random_uuid() | Mã nội bộ |
| username | varchar(80) | NOT NULL UNIQUE | Tên đăng nhập |
| password_hash | text | NOT NULL | Băm mật khẩu, không lưu mật khẩu thô |
| active | boolean | NOT NULL DEFAULT true | Cho phép đăng nhập |
| created_at | timestamptz | NOT NULL DEFAULT now() | Thời điểm tạo |


## role
Ba vai trò đã chốt

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| code | varchar(20) | PRIMARY KEY CHECK (code IN ('doctor','pharmacist','admin')) | Mã vai trò |


## user_role
Một tài khoản có thể có nhiều vai trò

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| user_id | uuid | NOT NULL REFERENCES app_user(id) | Tài khoản |
| role_code | varchar(20) | NOT NULL REFERENCES role(code) | Vai trò |

Ràng buộc bảng: `PRIMARY KEY(user_id,role_code)`

## patient_case
Hồ sơ synthetic, không lưu tên/CCCD/địa chỉ

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PRIMARY KEY DEFAULT gen_random_uuid() | Mã nội bộ |
| synthetic_code | varchar(30) | NOT NULL UNIQUE CHECK (synthetic_code ~ '^SYN-[A-Z0-9-]{1,24}$') | Mã giả lập |
| age | smallint | NOT NULL CHECK (age BETWEEN 0 AND 120) | Tuổi tại tạo hồ sơ |
| sex | varchar(10) | NOT NULL CHECK (sex IN ('male','female','unknown')) | Giới tính |
| owner_id | uuid | NOT NULL REFERENCES app_user(id) | Bác sĩ phụ trách |
| revision | integer | NOT NULL DEFAULT 1 CHECK(revision>0) | Tăng khi dữ liệu nguồn thay đổi |
| created_at | timestamptz | NOT NULL DEFAULT now() | Thời điểm tạo |

Index: `CREATE INDEX ix_case_owner ON patient_case(owner_id);`

## case_access
Quyền đối với từng hồ sơ; một người có thể có nhiều phạm vi trên một ca

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| case_id | uuid | NOT NULL REFERENCES patient_case(id) | Ca bệnh |
| user_id | uuid | NOT NULL REFERENCES app_user(id) | Người được cấp quyền |
| access_scope | varchar(20) | NOT NULL CHECK(access_scope IN ('clinical','medsafety')) | Phạm vi dữ liệu |

Ràng buộc bảng: `PRIMARY KEY(case_id,user_id,access_scope)`

## encounter
Lượt khám thuộc ca

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PRIMARY KEY DEFAULT gen_random_uuid() | Mã nội bộ |
| case_id | uuid | NOT NULL REFERENCES patient_case(id) | Ca bệnh |
| occurred_at | timestamptz | NOT NULL | Thời gian khám |
| created_at | timestamptz | NOT NULL DEFAULT now() | Thời điểm tạo |

Index: `CREATE INDEX ix_encounter_case_time ON encounter(case_id,occurred_at DESC);`

## observation_type
Danh mục chỉ số và kiểu giá trị

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| code | varchar(60) | PRIMARY KEY | Mã biến kỹ thuật |
| label | text | NOT NULL | Tên hiển thị |
| value_kind | varchar(10) | NOT NULL CHECK(value_kind IN ('number','boolean','text')) | Kiểu giá trị |
| unit | varchar(40) | NULL | Đơn vị chuẩn; null nếu không có |
| min_value | numeric | NULL | Miền hợp lệ kỹ thuật, không phải ngưỡng cảnh báo |
| max_value | numeric | NULL | Giới hạn trên nếu có |

Ràng buộc bảng: `CHECK(min_value IS NULL OR max_value IS NULL OR min_value<=max_value)`

## observation
Mỗi dòng một giá trị, giữ lịch sử qua các lần đo

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PRIMARY KEY DEFAULT gen_random_uuid() | Mã nội bộ |
| encounter_id | uuid | NOT NULL REFERENCES encounter(id) | Lượt khám |
| code | varchar(60) | NOT NULL REFERENCES observation_type(code) | Loại chỉ số |
| value_number | numeric | NULL | Giá trị số |
| value_boolean | boolean | NULL | Giá trị có/không |
| value_text | text | NULL | Giá trị phân loại hoặc kết quả mô phỏng |
| status | varchar(20) | NOT NULL CHECK(status IN ('present','not_measured','unknown')) | Thiếu không đổi thành 0 |
| observed_at | timestamptz | NOT NULL | Thời gian đo/đánh giá |
| source | varchar(30) | NOT NULL CHECK(source IN ('manual_synthetic','mock_his','mock_lis','mock_pacs')) | Nguồn synthetic |
| recorded_by | uuid | NOT NULL REFERENCES app_user(id) | Người nhập |
| created_at | timestamptz | NOT NULL DEFAULT now() | Thời điểm tạo |

Ràng buộc bảng: `CHECK ((status = 'present' AND num_nonnulls(value_number,value_boolean,value_text)=1) OR (status<>'present' AND num_nonnulls(value_number,value_boolean,value_text)=0))`
Index: `CREATE INDEX ix_observation_latest ON observation(encounter_id,code,observed_at DESC);`

## ingredient
Danh mục hoạt chất dùng chung

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| code | varchar(60) | PRIMARY KEY | Mã hoạt chất |
| display_name | text | NOT NULL | Tên hiển thị |


## medication
Thuốc hiện tại hoặc đơn dự kiến; không phải y lệnh tự động

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PRIMARY KEY DEFAULT gen_random_uuid() | Mã nội bộ |
| encounter_id | uuid | NOT NULL REFERENCES encounter(id) | Lượt khám |
| ingredient_code | varchar(60) | NOT NULL REFERENCES ingredient(code) | Hoạt chất |
| dose | numeric | NOT NULL CHECK(dose>0) | Liều đã nhập, không phải liều AI kê |
| dose_unit | varchar(10) | NOT NULL CHECK(dose_unit IN ('mg','mcg','g','mL')) | Đơn vị liều |
| route | varchar(10) | NOT NULL CHECK(route IN ('oral','iv','other')) | Đường dùng |
| frequency_per_day | smallint | NOT NULL CHECK(frequency_per_day BETWEEN 1 AND 24) | Số lần/ngày trong MVP |
| kind | varchar(10) | NOT NULL CHECK(kind IN ('current','proposed')) | Loại danh sách |
| created_at | timestamptz | NOT NULL DEFAULT now() | Thời điểm tạo |

Index: `CREATE INDEX ix_medication_encounter ON medication(encounter_id);`

## rule_version
Phiên bản bộ quy tắc theo module

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PRIMARY KEY DEFAULT gen_random_uuid() | Mã nội bộ |
| code | varchar(60) | NOT NULL | Mã bộ quy tắc |
| version | integer | NOT NULL CHECK(version>0) | Số phiên bản |
| module | varchar(20) | NOT NULL CHECK(module IN ('diagnosis','lab_test','treatment','medsafety')) | Module |
| source_ref | text | NOT NULL | Nguồn chuyên môn, trang/mục và phiên bản |
| content_hash | varchar(64) | NOT NULL CHECK(content_hash ~ '^[a-f0-9]{64}$') | SHA256 nội dung đã duyệt |
| status | varchar(12) | NOT NULL CHECK(status IN ('draft','tested','approved','active','retired')) | Vòng đời |
| created_by | uuid | NOT NULL REFERENCES app_user(id) | Người tạo |
| created_at | timestamptz | NOT NULL DEFAULT now() | Thời điểm tạo |

Ràng buộc bảng: `UNIQUE(code,version)`
Index: `CREATE UNIQUE INDEX ux_rule_active ON rule_version(code) WHERE status='active';`

## rule_approval
Bằng chứng duyệt ngoài hệ thống hoặc theo quyền được xác nhận

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| rule_version_id | uuid | PRIMARY KEY REFERENCES rule_version(id) | Phiên bản duyệt |
| approval_ref | text | NOT NULL CHECK(length(trim(approval_ref))>0) | Tham chiếu biên bản duyệt được xác minh |
| approved_content_hash | varchar(64) | NOT NULL CHECK(approved_content_hash ~ '^[a-f0-9]{64}$') | Hash nội dung đã duyệt |
| approved_at | timestamptz | NOT NULL | Thời điểm duyệt chuyên môn |
| recorded_by | uuid | NOT NULL REFERENCES app_user(id) | Người ghi nhận, không đồng nghĩa người duyệt |


## evaluation
Một lần đánh giá với ảnh chụp đầu vào bất biến

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PRIMARY KEY DEFAULT gen_random_uuid() | Mã nội bộ |
| encounter_id | uuid | NOT NULL REFERENCES encounter(id) | Lượt khám |
| input_revision | integer | NOT NULL CHECK(input_revision>0) | Phiên bản ca lúc đánh giá |
| input_snapshot | jsonb | NOT NULL CHECK(jsonb_typeof(input_snapshot)='object') | Snapshot kiểm toán; ngoại lệ có chủ đích với dữ liệu chuẩn hóa |
| requested_by | uuid | NOT NULL REFERENCES app_user(id) | Người yêu cầu |
| mode | varchar(10) | NOT NULL CHECK(mode IN ('stub','validated')) | Phân biệt demo và đã thẩm định |
| created_at | timestamptz | NOT NULL DEFAULT now() | Thời điểm tạo |

Index: `CREATE INDEX ix_evaluation_history ON evaluation(encounter_id,created_at DESC);`

## module_result
Đầu ra từng module của một lần đánh giá

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PRIMARY KEY DEFAULT gen_random_uuid() | Mã nội bộ |
| evaluation_id | uuid | NOT NULL REFERENCES evaluation(id) | Lần đánh giá |
| module | varchar(20) | NOT NULL CHECK(module IN ('diagnosis','lab_test','treatment','medsafety')) | Module |
| rule_version_id | uuid | REFERENCES rule_version(id) | Null chỉ cho stub chưa chạy rule |
| status | varchar(30) | NOT NULL CHECK(status IN ('mock_not_evaluated','completed','insufficient_data','failed')) | Trạng thái |
| message | text | NOT NULL | Diễn giải |

Ràng buộc bảng: `UNIQUE(evaluation_id,module)`; `CHECK(status='mock_not_evaluated' OR rule_version_id IS NOT NULL)`

## recommendation
Khuyến nghị thuộc kết quả module

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PRIMARY KEY DEFAULT gen_random_uuid() | Mã nội bộ |
| module_result_id | uuid | NOT NULL REFERENCES module_result(id) | Kết quả nguồn |
| code | varchar(80) | NOT NULL | Mã gợi ý/cảnh báo |
| severity | varchar(12) | NOT NULL CHECK(severity IN ('info','warning','critical')) | Mức cảnh báo |
| description | text | NOT NULL | Nội dung |
| source_ref | text | NOT NULL | Căn cứ truy vết |

Index: `CREATE INDEX ix_recommendation_result ON recommendation(module_result_id);`

## result_missing_field
Danh sách thiếu tách thành dòng, không lưu chuỗi ghép

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| module_result_id | uuid | NOT NULL REFERENCES module_result(id) | Kết quả |
| field_code | varchar(60) | NOT NULL REFERENCES observation_type(code) | Biến còn thiếu |

Ràng buộc bảng: `PRIMARY KEY(module_result_id,field_code)`

## clinical_decision
Quyết định của bác sĩ cho một lần đánh giá

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PRIMARY KEY DEFAULT gen_random_uuid() | Mã nội bộ |
| evaluation_id | uuid | NOT NULL UNIQUE REFERENCES evaluation(id) | Lần đánh giá |
| doctor_id | uuid | NOT NULL REFERENCES app_user(id) | Bác sĩ quyết định |
| action | varchar(10) | NOT NULL CHECK(action IN ('accepted','adjusted','rejected')) | Phản hồi |
| reason | text | NULL | Lý do điều chỉnh/từ chối |
| created_at | timestamptz | NOT NULL DEFAULT now() | Thời điểm tạo |

Ràng buộc bảng: `CHECK(action='accepted' OR length(trim(coalesce(reason,'')))>0)`

## audit_event
Nhật ký append-only, không chép giá trị dữ liệu lâm sàng

| Trường | Kiểu | Ràng buộc | Ý nghĩa |
|---|---|---|---|
| id | uuid | PRIMARY KEY DEFAULT gen_random_uuid() | Mã nội bộ |
| actor_id | uuid | NOT NULL REFERENCES app_user(id) | Tài khoản thao tác |
| action | varchar(80) | NOT NULL | Tên sự kiện |
| entity_type | varchar(40) | NOT NULL | Loại đối tượng |
| entity_id | uuid | NOT NULL | Mã đối tượng, tham chiếu đa hình do dịch vụ kiểm tra |
| created_at | timestamptz | NOT NULL DEFAULT now() | Thời điểm tạo |

Index: `CREATE INDEX ix_audit_entity_time ON audit_event(entity_type,entity_id,created_at DESC);`

## Kiểm tra ngoài CHECK
Trigger validate_observation kiểm tra kiểu và miền số theo danh mục. Trigger chặn sửa/xóa audit, snapshot đánh giá, quyết định. Trigger yêu cầu bằng chứng có hash khớp trước duyệt/kích hoạt rule. Quyền bác sĩ, quyền theo ca, tính mới của revision, tính xác thực bằng chứng duyệt và chuyển trạng thái hợp lệ cần được dịch vụ kiểm tra trong transaction; DDL không tự xác minh chuyên môn.

## 3NF và ngoại lệ
Các bảng quan hệ tách người dùng/vai trò, ca/lượt khám, danh mục chỉ số/kết quả, hoạt chất/thuốc, phiên bản/quyết định. Thuộc tính danh mục không lặp trong từng giao dịch; quan hệ nhiều-nhiều dùng bảng nối. Mỗi thuộc tính mô tả khóa của bảng, không dùng danh sách thuốc hoặc kết quả ghép trong một cột.
evaluation.input_snapshot là bản lưu bất biến để tái hiện quyết định, không dùng làm nguồn cập nhật nghiệp vụ. Đây là ngoại lệ phi chuẩn hóa có chủ đích; không tuyên bố toàn bộ JSON đạt 3NF. audit_event.entity_id là tham chiếu đa hình, dịch vụ chịu trách nhiệm kiểm tra đối tượng.
Bộ schema mô tả lưu trữ đích. Gateway tuần 3 dùng RAM, chưa kết nối schema này.
