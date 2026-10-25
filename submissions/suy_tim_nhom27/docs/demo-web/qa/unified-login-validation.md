# Kiểm tra đăng nhập chung — 24/10/2026

Điều chỉnh trực tiếp của người dùng thay yêu cầu hai màn hình đăng nhập riêng: một trang `/login`, tài khoản tự vào giao diện theo vai trò máy chủ. Giữ API xác thực hiện có, không thay dữ liệu hồ sơ hoặc cấp thêm quyền.

- Trình duyệt thật: Admin đăng nhập từ trang chung, URL `/forms`, hiển thị Admin và menu Quản lý trường dữ liệu.
- Tải lại phiên Admin vẫn vào giao diện; đăng xuất về `/login`.
- Sai mật khẩu Bác sĩ hiển thị lỗi tại `/login`; thử lại đúng mật khẩu vào `/forms`, hiển thị Bác sĩ và không có menu Quản lý trường dữ liệu.
- Bác sĩ đăng xuất về `/login`; mở bookmark `/admin/login` chuyển về trang chung. Cả hai bookmark cũ được kiểm tự động.
- Ảnh trang chung: `unified-login.png`; không chứa tài khoản hoặc mật khẩu đang điền.
- Kiểm thử tích hợp toàn bộ: **90 passed, 4 skipped, 1 warning**, 12.08 giây. Bốn test cũ có gate môi trường riêng; cảnh báo Starlette/httpx có sẵn. Chỉ test ghi vào schema QA `d3_form_qa_20261023`.
- `node --check web/forms.js` và `git diff --check` đạt.

Log đầy đủ giữ ngoài Git: `.context-shears/artifacts/command-20261024T160453.291675Z-58b5f72081b3.log`. Các kiểm tra giao diện ở trên không ghi thay đổi hồ sơ người bệnh. Bằng chứng hai cổng trong báo cáo cũ là lịch sử trước điều chỉnh này.
