# Nhóm 27 — Bàn giao tuần 3

Phạm vi: Case 2, hệ thống hỗ trợ quyết định suy tim. Đây là **thiết kế + API Gateway stub**, chưa phải phần mềm chẩn đoán được kiểm chứng. [SRS hiện tại](docs/SRS_v1.0.md) kế thừa bản GitHub cập nhật ngày 02/10/2026 và bổ sung cổng bệnh nhân ở tầng database ngày 08/10/2026 trên nhánh `update-off`. Hướng dẫn API bên dưới vẫn dành cho stub tuần 3.

## 1. Đọc theo thứ tự

| Yêu cầu | Tệp bàn giao |
|---|---|
| 3.1 — C4 C1/C2 | [Kiến trúc](docs/architecture/architecture.md) |
| 3.2 — ERD | [ERD](database/erd.md) |
| 3.2 — Data Dictionary | [Từ điển dữ liệu](database/data_dictionary.md), [ánh xạ nguồn](database/source_mapping.md) |
| 3.2 — DDL | [schema.sql](database/schema.sql), [seed.sql](database/seed.sql) |
| 3.3 — Class + 3 Sequence | [UML](docs/uml/uml.md) |
| 3.4 — OpenAPI | [openapi.yaml](api/openapi.yaml), [hướng dẫn API](api/README.md) |
| 3.4 — Gateway skeleton | [main.py](src/gateway/main.py), models.py, services.py, store.py |
| Nguồn sơ đồ | [So_do_tuan3.drawio](docs/architecture/So_do_tuan3.drawio): 11 trang; từng nguồn và PNG ở docs/architecture |
| Kiểm chứng | [Kết quả kiểm thử](docs/verification.md) |
| Báo cáo ngắn | [Bao_cao_tuan3.md](docs/Bao_cao_tuan3.md) |
| Rà soát SRS ↔ tuần 3 | [consistency_review.md](docs/consistency_review.md) |

## 2. Chạy trên Windows bằng PowerShell

Cài Python 3.12 và mở terminal tại thư mục có README này (`submissions/suy_tim_nhom27/`).

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DEMO_PASSWORD = "tu-dat-mat-khau-demo-o-day"
.\.venv\Scripts\python.exe -m uvicorn src.gateway.main:app --host 127.0.0.1 --port 8000
```

Mở `http://127.0.0.1:8000/docs`. Tại POST `/api/v1/auth/token`, chọn username `doctor`, `pharmacist` hoặc `admin`, password đúng giá trị vừa đặt. Copy `access_token`, bấm **Authorize**, dán token (không thêm chữ Bearer). Sau đó thử các API theo api/README.md.

Gateway dùng RAM: tắt/chạy lại sẽ mất dữ liệu. Chỉ chạy một worker. Bản này không cần cài DB để thử API; không công khai lên Internet.

Trong mục 3.3, Class 05–06 và C4 C2 là **thiết kế dự kiến**; Class 11 và Sequence 07–09 thể hiện đúng khung mã đang chạy. `docs/uml/uml.md` giải thích từng hình và cách đối chiếu với mã.

## 3. Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts/export_openapi.py
.\.venv\Scripts\python.exe -m pytest -q
```

Linux/macOS: dùng `python3 -m venv .venv`, `.venv/bin/python` thay đường dẫn Windows; đặt biến môi trường bằng `export DEMO_PASSWORD='...'`.

## 4. Khởi tạo CSDL đích

PostgreSQL 16+, database rỗng. Không chạy schema lặp trên DB đã có bảng.

```sh
psql -v ON_ERROR_STOP=1 -d hf_demo -f database/schema.sql
psql -v ON_ERROR_STOP=1 -d hf_demo -f database/seed.sql
psql -v ON_ERROR_STOP=1 -d hf_demo -f database/portal_permissions.sql
```

Hoặc nếu đã cài Docker Desktop và đặt DEMO_PASSWORD:

```sh
docker compose --profile database up -d db
```

PostgreSQL container chạy schema/seed/phân quyền lần đầu khi volume rỗng. Lần sau không tự chạy lại. Schema mới có 39 bảng và phần bệnh nhân tối giản; đọc [hướng dẫn database](database/README.md) để chạy kiểm thử SQL, dùng phân quyền và xuất metadata. Gateway vẫn lưu RAM, chưa kết nối database. `docker compose up --build gateway` chạy Gateway riêng. Compose chưa được thực thi trong môi trường cập nhật này.

## 5. Kiểm tra trong repository của nhóm

Các tệp tuần 3 đã nằm trong **`submissions/suy_tim_nhom27/`** trên nhánh `submit/suy_tim-nhom27`. SRS nhóm chỉnh ở `docs/SRS_v1.0.md`; sơ đồ, ảnh và nguồn draw.io ở `docs/architecture/`. `src/__init__.py` phục vụ import package Python. Từ gốc repository chạy:

```sh
python scripts/validate_submission.py submissions/suy_tim_nhom27
```

Đây là kiểm tra cách ly thư mục, manifest và dấu hiệu secret của repo thầy. Workflow hiện có chạy khi mở PR vào `main`; các lệnh ở mục 3 kiểm tra cú pháp hợp đồng và Gateway riêng. Không chép `.venv`, cache hoặc mật khẩu vào GitHub.

## 6. Điều cần chốt tiếp

- Cách duyệt rule/gold labels và mức cho phép rule-based/ML/LLM.
- Treatment chỉ strategy hay thuốc/liều; đầu ra xác suất có bắt buộc không.
- Danh mục biến/đơn vị/thang đo được chốt, đặc biệt các biến gộp BNP–NT-proBNP, creatinine–eGFR.
- Tích hợp thật hay mô phỏng; FHIR và yêu cầu triển khai bốn dịch vụ riêng.
- Quyền dược sĩ theo ca, quản lý tài khoản và các chỗ còn thiếu khi so SRS đã nêu trong [consistency_review.md](docs/consistency_review.md).

Bộ điều chỉnh đầu ra thầy bổ sung sẽ được đối chiếu sau. Các chỗ chưa chốt được đánh dấu; không tự coi là yêu cầu chính thức đã phê duyệt.
