# Demo quản lý bệnh viện — Nhóm 27

Ứng dụng web chạy cục bộ với PostgreSQL 16+ và FastAPI. Có năm tài khoản demo theo vai trò bác sĩ, điều dưỡng, dược sĩ, quản trị và bệnh nhân. Chỉ dùng dữ liệu synthetic; bốn module chẩn đoán, xét nghiệm, điều trị và MedSafety luôn trả `mock_not_evaluated`, không đưa ra kết luận lâm sàng hay đơn thuốc.

## Chạy web trực tiếp

Cần Python 3.12 và PostgreSQL 16+ đang chạy trên máy. Khởi tạo database theo [hướng dẫn schema](database/README.md), sau đó mở PowerShell tại thư mục `submissions/suy_tim_nhom27/`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DATABASE_URL = "postgresql://hf_demo_runtime:<mat-khau>@127.0.0.1:5432/hf_demo"
.\.venv\Scripts\python.exe -m uvicorn src.gateway.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Mở [http://127.0.0.1:8000](http://127.0.0.1:8000) để dùng giao diện hoặc [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) để xem API. Thay `<mat-khau>` bằng mật khẩu của role `hf_demo_runtime`.

| Vai trò | Tài khoản | Mật khẩu |
|---|---|---|
| Bác sĩ | `doctor_demo` | `DemoOnly!2026` |
| Điều dưỡng | `nurse_demo` | `DemoOnly!2026` |
| Dược sĩ | `pharmacist_demo` | `DemoOnly!2026` |
| Quản trị | `admin_demo` | `DemoOnly!2026` |
| Bệnh nhân | `patient_demo` | `DemoOnly!2026` |

Web và API chạy trực tiếp trên máy; PostgreSQL lưu dữ liệu demo. Không cần Docker Desktop.

## Tài liệu và mã nguồn

- [Hướng dẫn chạy, cấu hình và kiểm tra](README_TUAN3.md)
- [Hợp đồng và ví dụ API](api/README.md), [OpenAPI](api/openapi.yaml)
- [Schema, seed và phân quyền](database/README.md)
- [SRS](docs/SRS_v1.0.md), [RTM](docs/RTM.md), [kế hoạch UI](docs/ui-ux-plan.md)
- [Gateway](src/gateway/), [giao diện web](web/)

Demo phục vụ trình diễn luồng và phân quyền. Không triển khai ra Internet hoặc dùng cho chăm sóc bệnh nhân thật.
