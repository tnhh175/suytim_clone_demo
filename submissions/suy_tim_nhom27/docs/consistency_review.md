# Rà soát điểm nối giữa SRS và thiết kế tuần 3

Mốc đối chiếu: `docs/SRS_v1.0.md` trên nhánh `submit/suy_tim-nhom27`, Git blob `7d3a0557f962e33a1c4b12fd865e638effb80977` (28/09/2026). Đây là bảng trạng thái **bàn giao tuần 3**, không phải biên bản nghiệm thu hệ thống lâm sàng. Ba vai trò duy nhất đang chốt: bác sĩ, dược sĩ, quản trị viên. Bệnh nhân là đối tượng ca bệnh, chưa là người dùng đăng nhập.

## 1. Phần đã thống nhất để chia việc

| Điểm nối | Đã khóa trong bộ tuần 3 | Hệ quả khi chia việc |
|---|---|---|
| FR-08 ↔ US-03 | SRS mới phân biệt nhóm EF và kết luận kiểu hình suy tim; cần bằng chứng/rule được duyệt trước kết luận. | Module Diagnosis không được đồng nhất EF đơn lẻ với chẩn đoán. |
| FR-02 ↔ POST `/cases` ↔ `patient_case` | API tự sinh `SYN-...` nếu không gửi mã; `synthetic_code` vẫn NOT NULL/UNIQUE ở DB. | Frontend có thể để trống mã; repository lưu mã do API sinh. |
| ID người dùng ↔ FK | `owner_id`, `doctor_id`, `actor_id`, `entity_id` của API là UUID; DDL dùng UUID. | Tài khoản demo được ánh xạ UUID cố định theo vai trò. `seed.sql` chưa tạo hàng `app_user`; khi nối DB phải tạo user demo tương ứng hoặc dùng Identity thật trước khi lưu FK. |
| Quyền nhiều phạm vi | Khóa `case_access(case_id,user_id,access_scope)` cho phép một người có cả clinical và medsafety. | Khi xây phân quyền phải kiểm tra từng phạm vi; stub hiện dược sĩ xem mọi ca giả lập. |
| Kiểu kết quả | OpenAPI 3.0.3 có `mode=stub`, `mock_not_evaluated`; bốn adapter chung một process. | Frontend phải hiển thị nhãn bản demo; không hiển thị lời khuyên lâm sàng rỗng như kết luận âm tính. |
| Sơ đồ ↔ mã | C1/C2 + class 05–06 là đích dự kiến; class 11 + sequence 07–09 là mã stub đang chạy; DDL và ERD chung metadata. | Không báo đã triển khai microservices/PostgreSQL chỉ vì có C2/ERD. |

## 2. Chưa nghiệm thu so với yêu cầu SRS

| SRS | Trong bộ tuần 3 | Việc cần làm để tránh lệch về sau |
|---|---|---|
| FR-01, NFR-07 | Bearer token demo, một tài khoản mỗi vai trò, khóa bằng mật khẩu trong biến môi trường. | Thay Identity thật, hash mật khẩu, quyền theo ca, nhiều vai trò và kiểm thử truy cập; đừng coi demo là RBAC hoàn chỉnh. |
| FR-03–05 | API nhận 11 mã chỉ số/triệu chứng demo; catalog `seed.sql` cùng mã. Kiểm kiểu/đơn vị/miền kỹ thuật ở một phần dữ liệu. | Chốt Data Dictionary chuyên môn, mã hóa triệu chứng, sinh hiệu, cận lâm sàng/hình ảnh, nguồn và độ mới. Đồng bộ model, seed, DDL, Swagger theo một bảng mapping. |
| FR-07–12 | Trả trường thiếu và snapshot. Chưa phân nhóm EF, stage, cấp cứu hoặc bệnh phân biệt. | Thiết kế rule và kết quả khi thiếu bằng chứng; chưa chạy rule khi đang `pending_review`. |
| FR-13–18 | Endpoint/DTO đã dự trù; kết quả Lab/Test, Treatment chỉ là mock. | Phải chốt đầu ra và căn cứ trước khi hiện thực gợi ý CLS/strategy/thuốc. |
| FR-19–22 | Chưa phát hiện NSAID, tăng kali, digoxin; chưa có nguồn chứng cứ cho cảnh báo. | Chốt mã hoạt chất, tương tác, tài liệu/ngưỡng và quy tắc duyệt; tạo gold cases kiểm đúng/sai và trường hợp thiếu dữ liệu. |
| FR-23–26, NFR-09 | Có quyết định, revision, lịch sử, xuất dữ liệu demo, audit trong RAM. | Nối transaction DB, bảo vệ audit/snapshot, kiểm căn cứ rule và xuất tóm tắt đúng quyền; chưa thể tuyên bố 100% traceability. |
| FR-27; SRS §2.3 | Tạo nháp, test schema, chặn kích hoạt; DDL có `draft/tested/approved/active/retired`. Chưa có rule ngưỡng, trạng thái `pending_review`, phê duyệt chuyên môn được xác thực. | Quyết định `pending_review` áp vào **ngưỡng** hay **phiên bản rule**; sau khi chốt, thêm cột/trạng thái và quy tắc chuyển trạng thái trong DB/API cùng một lượt. Chưa tự phê duyệt qua quyền quản trị kỹ thuật. |
| NFR-01–06,08,10–12 | Chưa kiểm tải, độ sẵn sàng, mã hóa dữ liệu lưu, quét PII trong text, browser/usability hay coverage Rule Engine. | Lên bộ kiểm chứng riêng trước nghiệm thu; parser SQL không thay cho chạy PostgreSQL thật. |

## 3. Những chỗ SRS còn cần làm rõ với nhóm/thầy

- `US-11` nói quản lý tài khoản nhưng UC chi tiết của SRS chưa có UC quản lý tài khoản riêng. Chọn bổ sung UC và RTM nếu yêu cầu xây CRUD tài khoản, hoặc giới hạn story cho MVP.
- Bảng DFD Level 1 trong SRS đã bổ sung D1 cho P3 và D3 cho P4; ảnh và tệp draw.io tuần 2 còn thiếu các mũi tên đó, cần sửa đồng thời hai bản hình.
- Ranh giới dữ liệu thật/giả lập, quyền dược sĩ theo ca, danh mục biến và rule, cách duyệt, mức đầu ra bốn module, bộ ca nhãn chuẩn và kiểu tích hợp còn ở mục 12 SRS; chưa biến các giả định của nhóm thành yêu cầu đã duyệt.
- Nếu SRS được sửa tiếp, lưu mã commit/blob mới rồi cập nhật cùng lúc: bảng này → C4/UML → ERD/Data Dictionary/DDL → OpenAPI/DTO/Gateway → tests. `pending_review` không có trong enum DB hiện tại là điểm phụ thuộc phải xử lý trước khi lưu rule/ngưỡng thật.

## 4. Kiểm tra trước ghép nhánh

1. Cùng một mã chỉ số phải khớp `ObservationInput.code`, `observation_type`, `seed.sql` và rule tương ứng; `unknown`/`not_measured` không chuyển thành 0.
2. Bảng UUID và quan hệ FK phải khớp request/response OpenAPI; tránh truyền tên vai trò vào cột UUID.
3. Kết quả thật phải chỉ ra đầu vào đã dùng, rule version, nguồn và người xác nhận; nếu chưa đủ căn cứ thì trả trạng thái chưa đánh giá được.
4. Không khởi chạy lệnh sinh DDL lên DB đã chứa dữ liệu; cần migration sau khi chọn schema cuối.
