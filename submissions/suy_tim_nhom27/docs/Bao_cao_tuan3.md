# Báo cáo tuần 3 — Nhóm 27

**Đề tài:** Hệ thống hỗ trợ quyết định suy tim ở người cao tuổi.

**Mục tiêu tuần:** Chuyển yêu cầu tuần 2 thành kiến trúc, mô hình dữ liệu và hợp đồng API để nhóm bắt đầu lập trình song song.

## Kết quả

| Công việc | Kết quả bàn giao |
|---|---|
| 3.1 | C4 C1 xác định ba vai trò và các nguồn HIS/EMR, LIS, PACS/RIS mô phỏng. C2 đề xuất Web App, Gateway, Core, bốn dịch vụ lâm sàng và PostgreSQL, ghi rõ giao thức. |
| 3.2 | ERD 18 bảng; từ điển từng trường, PK/FK, CHECK, index; DDL PostgreSQL và catalog seed synthetic. |
| 3.3 | Class Diagram nghiệp vụ và dịch vụ dự kiến; Class Diagram đối chiếu mã stub đang chạy; ba Sequence của luồng đánh giá, quyết định và quản trị rule trên Gateway hiện tại. Có nguồn draw.io. |
| 3.4 | OpenAPI 3.0.3 và Gateway FastAPI chạy stub. Frontend có thể gọi thử tạo ca, nhập dữ liệu, xem kết quả mẫu và ghi phản hồi. |

## Quyết định chính

Nhóm giữ ba vai trò đã thống nhất. Bác sĩ là người quyết định; dược sĩ dùng MedSafety; quản trị không tự duyệt quy tắc lâm sàng. API lưu phiên bản dữ liệu và chặn xác nhận đánh giá cũ. Các kết quả tuần 3 ghi rõ `stub`, chưa cung cấp chẩn đoán hoặc liều thuốc thực.

CSDL tách ca, lượt khám, chỉ số, thuốc, kết quả và quyết định để tránh dữ liệu lặp. Snapshot JSON chỉ dùng tái hiện căn cứ tại thời điểm đánh giá. C2 là kiến trúc **dự kiến** có các dịch vụ riêng. Mã bàn giao tuần 3 thực hiện khung API với các route, kiểm quyền và adapter stub trong một tiến trình FastAPI, lưu RAM. Việc gộp chỉ phục vụ thử hợp đồng API và giao diện ở Sprint 1; chưa coi như đã xây xong Core, bốn service hay lớp lưu trữ.

## Kiểm chứng và giới hạn

Đã chạy kiểm thử API cho luồng chuẩn, phân quyền, dữ liệu sai/thiếu, revision cũ, quyết định trùng và chặn rule chưa duyệt. Đã kiểm tra OpenAPI 3.0.3, đồng bộ hợp đồng với routing, phân tích cú pháp DDL PostgreSQL. Chi tiết và lệnh chạy nằm trong verification.md.

Ngày 28/09/2026, nhóm chạy `database/schema.sql` và `database/seed.sql` trên một PostgreSQL 16.15 cục bộ với database rỗng, bật `ON_ERROR_STOP=1`. Hai lệnh hoàn tất không lỗi; truy vấn lại có 18 bảng, 5 trigger, 3 vai trò, 11 loại chỉ số và 1 hoạt chất giả lập. `/docs` trả HTTP 200 và `/openapi.json` trả OpenAPI 3.0.3. Đây là phép thử trên database riêng trong thư mục tạm của máy kiểm tra, chưa phải triển khai hoặc kết nối Gateway với PostgreSQL.

### Đối chiếu checklist cuối tuần 3

| Yêu cầu | Trạng thái và bằng chứng |
|---|---|
| SRS v1.0 có FR, NFR, Use Case | Có tại `docs/SRS_v1.0.md`; còn các câu hỏi chờ xác nhận ở mục 12. |
| C4 C1/C2, DFD, Class UML có ảnh và nguồn | Có trong `docs/architecture/`: 18 tệp `.drawio`, 17 ảnh PNG; hình DFD Level 1 tuần 2 còn thiếu hai luồng đã bổ sung trong bảng SRS. |
| ERD, Data Dictionary và DDL tạo bảng | Có trong `database/`; DDL/seed đã chạy thành công trên PostgreSQL 16.15 cục bộ như trên. Chuẩn hóa 3NF là mục tiêu thiết kế, chưa có thẩm định độc lập. |
| OpenAPI và Gateway stub | `api/openapi.yaml` hợp lệ theo OpenAPI 3.0.3 và khớp contract runtime; `/docs` và `/openapi.json` trả 200. Gateway vẫn lưu RAM, kết quả lâm sàng chỉ là stub. |
| RTM liên kết 100% yêu cầu nghiệp vụ được chọn tới Use Case/schema | Báo cáo Word nối BR-01–05 với FR, User Story và Use Case nhưng chưa có cột Schema. `docs/SRS_v1.0.md` nối FR-01–27 với Use Case/bảng CSDL, song chưa nối trực tiếp BR. Cần hợp nhất hai bảng trước khi xác nhận đạt 100%. |
| CI kiểm cú pháp code và tính hợp lệ schema/tài liệu | Workflow `.github/workflows/validate-submission.yml` chạy khi có PR vào `main`, nhưng script hiện chỉ kiểm tra phạm vi thư mục, manifest, kích thước và dấu hiệu secret. Chưa có job CI chạy `pytest`, kiểm OpenAPI hoặc DDL; chưa xác nhận một lần chạy CI trên PR tuần 3. |

### Đối chiếu slide báo cáo tuần 3

Hình C1, C2, ERD lõi và Sequence đánh giá ở slide 3–6 trùng tệp PNG tương ứng trong `docs/architecture/`. Con số trên slide 7 khớp `api/openapi.yaml`: 17 đường dẫn, 22 thao tác; `/health`, `/docs`, `/openapi.json` đều trả HTTP 200 qua TestClient. Cụm “8 ca đạt” trên slide là **8 hàm kiểm thử API đạt**, không phải 8 ca lâm sàng. Slide 5 và 8 ghi “chờ chạy DDL” theo trạng thái cũ; kết quả chạy thật đã được ghi ở trên. Việc GET `/docs` trả HTML không thay cho kiểm tra giao diện Swagger bằng trình duyệt.

Rà soát với SRS mới: API đã tự sinh mã ca và thống nhất UUID với khóa ngoại DB; `case_access` cho phép nhiều phạm vi trên cùng ca. Từ điển dữ liệu đã sửa định dạng bảng Markdown, sơ đồ ERD được xuất lại từ metadata. Đây là kiểm tra **tính nhất quán của thiết kế và stub**, chưa nghiệm thu FR lâm sàng.

Chưa chạy Docker Compose; chưa kết nối HIS hoặc triển khai các dịch vụ độc lập. Chưa đánh giá độ đúng lâm sàng, hiệu năng tải, độ sẵn sàng hoặc bảo mật triển khai. Đây là các bước tiếp theo, không ghi nhận là đã hoàn thành.

## Việc tiếp theo

Thêm truy vết BR-01–05 vào RTM; cập nhật hai luồng thiếu trên hình DFD Level 1; bổ sung CI chạy kiểm thử Python/OpenAPI/DDL. Đối chiếu các câu hỏi đang mở ở mục 12 SRS với thầy, đặc biệt danh mục dữ liệu và quyền duyệt chuyên môn; nối PostgreSQL vào Gateway; thay stub bằng module theo quy tắc/thuật toán đã được xác nhận; đối chiếu bộ điều chỉnh đầu ra mới. Bảng [đối chiếu SRS ↔ tuần 3](consistency_review.md) ghi rõ phần đã có và phần chưa có. Phân công cá nhân do nhóm điền theo người thực hiện thực tế.
