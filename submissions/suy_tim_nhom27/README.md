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

## Đăng ký bệnh nhân

Bấm **Chưa có tài khoản? Đăng ký bệnh nhân**, nhập tên đăng nhập, mật khẩu từ 12 ký tự, tuổi và giới tính synthetic. Đăng ký tạo một tài khoản chỉ có vai trò bệnh nhân và một hồ sơ synthetic mới trong cùng giao dịch PostgreSQL. Không nhập thông tin người thật. Đăng nhập sau khi đăng ký; cổng bệnh nhân mới bắt đầu với danh sách rỗng.

Tài khoản bác sĩ, điều dưỡng, dược sĩ và quản trị dùng các tài khoản demo có sẵn; đăng ký công khai không cấp các vai trò này. Web xác định vai trò bằng `GET /api/v1/auth/me`, kể cả khi khôi phục phiên.

`HF_REGISTRATION_DOCTOR_USERNAME` chọn bác sĩ phụ trách hồ sơ mới, mặc định `doctor_demo`. Tài khoản này phải đang hoạt động và chỉ có vai trò bác sĩ; cấu hình không hợp lệ trả `503` và không tạo bản ghi. Không chọn bác sĩ hoặc liên kết hồ sơ có sẵn từ form đăng ký. Runtime dùng quyền owner chỉ trong giao dịch tạo mới, theo membership đã cấu hình trong `database/runtime_roles.sql`.

Mật khẩu được băm PBKDF2 SHA-256 600.000 vòng với salt ngẫu nhiên cho từng tài khoản. Đăng ký giới hạn 8 lần/phút cho mỗi địa chỉ kết nối trực tiếp và 64 lần/phút cho toàn bộ một tiến trình; `429` kèm `Retry-After: 60`. Đây là giới hạn trong bộ nhớ cho demo một worker, không phải hệ thống chống lạm dụng phân tán. Phiên đăng nhập và hồ sơ lưu trong PostgreSQL; mật khẩu không được lưu ở trình duyệt.

## Tài liệu và mã nguồn

- [Hướng dẫn chạy, cấu hình và kiểm tra](README_TUAN3.md)
- [Hợp đồng và ví dụ API](api/README.md), [OpenAPI](api/openapi.yaml)
- [Schema, seed và phân quyền](database/README.md)
- [SRS](docs/SRS_v1.0.md), [RTM](docs/RTM.md), [kế hoạch UI](docs/ui-ux-plan.md)
- [Gateway](src/gateway/), [giao diện web](web/)

Demo phục vụ trình diễn luồng và phân quyền. Không triển khai ra Internet hoặc dùng cho chăm sóc bệnh nhân thật.
