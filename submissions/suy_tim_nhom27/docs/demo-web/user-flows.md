# User flows — thiết kế đề xuất

Luồng hiện hành dùng một màn hình đăng nhập theo điều chỉnh mới nhất của người dùng. HTML mockup ban đầu vẫn là mô phỏng, chỉ dùng dữ liệu giả lập. Nguồn nền: prompt v3 C/D/F/G, PROMPT_DEV §§6–11 và BIEU_DIEN_TRUONG.

## M1 — Bác sĩ

1. Mở `/login` → gửi tài khoản/mật khẩu qua API xác thực chung → đọc vai trò do máy chủ xác nhận → tự mở cổng Bác sĩ khi tài khoản có vai trò Bác sĩ. Sai thông tin đăng nhập: giữ màn hình đăng nhập và báo lỗi; không tự suy vai trò từ tên tài khoản.
2. Danh sách hồ sơ trong phạm vi tài khoản → tìm theo mã/tên → chọn hồ sơ hoặc tạo hồ sơ.
3. Danh sách lượt → mở lượt đã có hoặc tạo lượt mới. Luôn kiểm tra mã hồ sơ/lượt trong context banner.
4. Nhập nhóm dữ liệu đủ rõ. Chưa có để trống; boolean chưa có/không/có phân biệt. Thuốc/kết quả thêm theo mục có cấu trúc.
5. Dirty → lưu. Thiếu thông tin chuyên môn không chặn lưu nếu định danh tối thiểu hợp lệ.
6. Success khi server xác nhận → mở lại và xem lịch sử. Error giữ nháp. Conflict giữ nháp, lấy bản mới để đối chiếu; không âm thầm ghi đè.

## M1 — Admin quản lý định nghĩa

Mở `/login` → gửi tài khoản/mật khẩu → máy chủ xác thực vai trò Admin → tự mở cổng Admin → Quản lý trường → tìm mã/nhãn/nhóm → thêm/sửa → cấu hình nhãn/mã/nhóm/kiểu/đơn vị/hướng dẫn/thứ tự và mã–nhãn lựa chọn → preview giá trị NULL → lưu/áp dụng → biểu mẫu Bác sĩ tải định nghĩa mới. Mã trùng báo lỗi. Đổi ý nghĩa khi đã có dữ liệu bị chặn nếu chưa có chuyển đổi rõ. Ngừng dùng có xác nhận, giữ lịch sử. Bác sĩ không thấy action quản lý và API phải từ chối trực tiếp. Các URL đăng nhập cũ chuyển hướng về `/login`.

## M2 — Excel

Chọn .xlsx → kiểm tra file → chọn sheet/header rõ → xem cột/dòng mẫu → mapping trường có sẵn và định danh chuỗi → preview từng ca → lỗi/trùng/xung đột → xác nhận phần đủ điều kiện → kết quả đã nhận/bỏ qua/chờ/lỗi → mở biểu mẫu đúng ca để bổ sung tay.

Không có workbook viện thật: dùng fixture ghi rõ giả lập; chưa tuyên bố tương thích HIS. Một ca/nhiều ca phải được nêu rõ theo khả năng contract; không tự lấy ca đang mở cho mọi dòng. Dòng chưa khớp định danh không được ghi. Không tự đoán ngày/đơn vị/bảng mã. NULL nguồn không xóa đích, khác giá trị giữ đích mặc định; muốn thay phải chọn rõ. Nhập lại/đổi tên file không được tạo trùng.

## Điều kiện rời màn hình

Dirty: hỏi trước rời form. Import trước confirm: hủy an toàn; không ghi nghiệp vụ. Request commit mất phản hồi: kiểm tra lần nhập/trạng thái trước retry, không báo success giả. Logout thu hồi phiên và trở về `/login`.

## Phạm vi bằng chứng kiểm thử

Kiểm thử chức năng cần bao gồm thao tác ghi, xác thực và phân quyền, transaction, dedup, concurrency, restart/persistence trong môi trường thử nghiệm. Kiểm thử UI cần đi qua đăng nhập, điều hướng, tìm kiếm, lịch sử, nhập tay, Excel preview và xác nhận. Mockup validation chỉ chứng minh thiết kế chạy/render, không thay nghiệm thu backend. Áp dụng quyền và phân công hiện hành của người dùng; không giữ giới hạn riêng cho agent từ prompt cũ.
