# Demo quản lý bệnh viện — hướng dẫn kỹ thuật

Đây là demo cục bộ cho SRS của nhóm 27. Dữ liệu chỉ synthetic. PostgreSQL lưu phiên đăng nhập, hồ sơ và các bản ghi; giao diện tĩnh được FastAPI phục vụ trên cùng origin. Bốn module clinical luôn là `mock_not_evaluated` và không trả khuyến nghị, chẩn đoán hoặc y lệnh.

## Chạy web trực tiếp

Cần Python 3.12 và PostgreSQL 16+ đang chạy trên máy. Khởi tạo database theo [hướng dẫn schema](database/README.md). Từ thư mục `submissions/suy_tim_nhom27/`, chạy:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DATABASE_URL = "postgresql://hf_demo_runtime:<mat-khau>@127.0.0.1:5432/hf_demo"
.\.venv\Scripts\python.exe -m uvicorn src.gateway.main:app --host 127.0.0.1 --port 8000 --workers 1
```

- Giao diện: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`
- Health: `http://127.0.0.1:8000/health`

Dùng các tài khoản `doctor_demo`, `nurse_demo`, `pharmacist_demo`, `admin_demo`, `patient_demo`; mật khẩu demo chung là `DemoOnly!2026`. Chỉ dùng trên máy cá nhân. Không đưa tài khoản hoặc cổng demo ra Internet.

Dùng mật khẩu URL-encoded nếu có ký tự đặc biệt. Pool được đóng/mở theo vòng đời ứng dụng; `/health` trả 503 nếu DB chưa sẵn sàng. Không dùng tài khoản owner/superuser của DB cho Gateway. Không cần Docker Desktop.

## Kiểm tra hợp đồng và mã nguồn

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts/export_openapi.py
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m pytest -q
node --check web/app.js
```

Mọi endpoint và quyền hiện có được liệt kê trong [api/README.md](api/README.md). Kiểm thử SQL baseline dùng PGlite có trong `database/tests`; PGlite không thay thế PostgreSQL 16 thực tế. Kiểm thử service hoặc browser chỉ được xác nhận khi chạy thành công trên môi trường tương ứng.

## Ranh giới demo

- Bản ghi thuốc thủ công không tạo prescription, lịch dùng thuốc hoặc reminder.
- Đơn và reminder trong portal là dữ liệu synthetic được seed; bệnh nhân chỉ xem đơn và phản hồi reminder theo quyền DB.
- Admin quản trị rule/audit, không mặc định đọc hồ sơ lâm sàng. Kích hoạt rule bị chặn nếu chưa có phê duyệt hợp lệ.
- Không có tích hợp HIS/LIS/PACS, xác thực production, triển khai đa worker, hay thuật toán đã được thẩm định lâm sàng.
- Các mục chưa được hỗ trợ cần để trạng thái chưa triển khai; giao diện không sinh số đo, kết quả hoặc cảnh báo giả.

Xem [README chính](README.md), [SRS](docs/SRS_v1.0.md), [RTM](docs/RTM.md), [schema và dữ liệu](database/README.md).
