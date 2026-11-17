# Đưa demo lên Railway

Nhánh `demo-web-3` có cấu hình để chạy biểu mẫu và nhập Excel với FastAPI cùng PostgreSQL 16 trở lên. Railway cấp URL HTTPS cho web. PostgreSQL chỉ cần dùng mạng riêng của project. Bản deploy dùng hồ sơ giả lập được tạo từ mã nguồn.

## Tạo project và dữ liệu mẫu

1. Tạo project Railway và thêm một PostgreSQL mới. Đặt tên service là `Postgres` nếu muốn dùng các tham chiếu biến dưới đây.
2. Thêm service tạm tên `forms-bootstrap` từ repo `tnhh175/suytim_clone_demo`, nhánh `demo-web-3`. Đặt **Root Directory** là `/submissions/suy_tim_nhom27`. Dockerfile trong thư mục này cài thư viện và chép web, API, migration vào image.
3. Trên service tạm, đặt **Start Command** là `python scripts/bootstrap_hosted_forms.py` và **Restart Policy** là **Never**. Để trống mục **Healthcheck Path** và **Config File** trên service tạm. Đặt các biến trước khi deploy.

   | Biến | Giá trị |
   |---|---|
   | `BOOTSTRAP_DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
   | `HF_RUNTIME_PASSWORD` | Mật khẩu riêng cho role PostgreSQL `hf_demo_runtime` |
   | `HF_ADMIN_PASSWORD` | Mật khẩu đăng nhập web của `forms_admin` |
   | `HF_DOCTOR_PASSWORD` | Mật khẩu đăng nhập web của `forms_doctor` |

   Tạo ba mật khẩu riêng, mỗi mật khẩu dài 20–128 ký tự. Chuỗi hex ngẫu nhiên dài 32 ký tự tránh phải mã hóa ký tự khi ghép vào URL. Lưu mật khẩu vào nơi quản lý bí mật của nhóm.
4. Chạy service tạm một lần. Kết quả thành công có `d3_form_hosted`, 2 hồ sơ và 4 lượt khám. Script yêu cầu PostgreSQL mới dành riêng cho demo và từ chối khi đã có role hoặc dữ liệu ứng dụng. Khi hoàn tất, gỡ service tạm hoặc xóa các biến bootstrap khỏi service đó.

## Chạy web

1. Tạo web service từ cùng repo, nhánh và Root Directory. Đặt đường dẫn **Railway Config File** là `/submissions/suy_tim_nhom27/railway.toml`. Dùng Start Command mặc định từ Dockerfile.
2. Thêm biến `DATABASE_URL` cho web. Thay `<runtime-password>` bằng mật khẩu `HF_RUNTIME_PASSWORD` đã đặt lúc bootstrap.

   ```text
   postgresql://hf_demo_runtime:<runtime-password>@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}
   ```

   Web dùng role runtime có quyền đọc và ghi trên các bảng cần thiết trong `d3_form_hosted`. Giữ thông tin kết nối bootstrap và mật khẩu tài khoản web ngoài cấu hình web service.
3. Deploy rồi chọn **Settings → Networking → Generate Domain**. Mở `/health` trên domain mới và kiểm tra HTTP 200. Mở `/login`, đăng nhập bằng hai vai trò. Tài khoản Bác sĩ có thể thử lưu vào lượt giả lập và kiểm tra lại sau khi tải trang.

## Chuyển sang quyền runtime giới hạn

Nếu đã bootstrap từ bản cấp quyền `SET ROLE hf_demo_owner` cho web, dừng web service rồi chạy `python scripts/bootstrap_hosted_forms.py --restrict-runtime` bằng service tạm. Lần này chỉ cần cấu hình `BOOTSTRAP_DATABASE_URL`. Lệnh cấp quyền trực tiếp trên schema demo và thu hồi quyền chuyển sang role owner. Lệnh có thể chạy lại, giữ nguyên tài khoản và dữ liệu. Sau khi triển khai phiên bản mới, kiểm lại `/health`, đăng nhập và lưu lượt khám, rồi gỡ service tạm hoặc xóa biến bootstrap khỏi service đó.

Railway tính chi phí theo gói và mức sử dụng cho web cùng PostgreSQL. Xem [giá](https://docs.railway.com/pricing/plans), [cách nối PostgreSQL](https://docs.railway.com/databases/postgresql) và [cấu hình thư mục repo](https://docs.railway.com/deployments/monorepo).
