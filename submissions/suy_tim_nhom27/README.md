# CS-2: Hỗ trợ quyết định suy tim ở người cao tuổi — nhom27

**Trạng thái:** Gateway vẫn là stub trong RAM; bốn module lâm sàng **chưa được hiện thực/kiểm chứng**. Schema/seed trên nhánh `update-off` được cập nhật theo SRS, có năm vai trò: bác sĩ, điều dưỡng, dược sĩ, quản trị và bệnh nhân. Phần bệnh nhân ở tầng database hỗ trợ đặt lịch, nhập chỉ số tại nhà, xem đơn đã xác nhận, giờ uống và nhắc thuốc. Chỉ dùng dữ liệu synthetic.

## Checklist bàn giao

| Mục | Tệp chính | Trạng thái |
|---|---|---|
| SRS và RTM (FR → US → UC → module → bảng dữ liệu) | [SRS_v1.0.md](docs/SRS_v1.0.md) | Bản review; các câu hỏi cho giảng viên ở mục 12 |
| C4 C1/C2; DFD; UML Class/Sequence; ảnh và nguồn draw.io | [Kiến trúc](docs/architecture/architecture.md), [UML](docs/uml/uml.md), [tệp nguồn/ảnh](docs/architecture/) | C4, Class 05–06 là thiết kế đích; Sequence 07–09 mô tả stub |
| ERD, từ điển dữ liệu, DDL, seed và metadata | [Hướng dẫn database](database/README.md), [ERD](database/erd.md), [Data Dictionary](database/data_dictionary.md), [schema.sql](database/schema.sql), [seed.sql](database/seed.sql), [metadata](database/schema_metadata.json) | 39 bảng; có kiểm thử thực thi SQL/RLS; Gateway chưa kết nối PostgreSQL |
| OpenAPI 3.0.3 và Gateway | [openapi.yaml](api/openapi.yaml), [hướng dẫn API](api/README.md), [mã nguồn](src/gateway/) | Stub chạy trong RAM; không chẩn đoán/kê đơn |

[Báo cáo tuần 3](docs/Bao_cao_tuan3.md) · [Điểm chưa khớp/việc chờ xác nhận](docs/consistency_review.md) · [Hướng dẫn chạy và kiểm thử](README_TUAN3.md)

## Chạy thử Gateway trên máy

Mở terminal **ngay tại thư mục `submissions/suy_tim_nhom27/`**, làm theo [README_TUAN3.md](README_TUAN3.md). Swagger UI ở `http://127.0.0.1:8000/docs` khi server chạy. API trả `mode=stub` và `mock_not_evaluated`, không đưa ra kết luận y khoa.

## Kiểm tra bài nộp

Từ gốc repository: `python scripts/validate_submission.py submissions/suy_tim_nhom27`. Workflow sẵn có của repo chạy khi mở PR vào `main`; script này kiểm tra cách ly thư mục, manifest, kích thước và dấu hiệu secret. Kiểm tra cú pháp OpenAPI, DDL và test Gateway dùng lệnh riêng trong [README_TUAN3.md](README_TUAN3.md).
