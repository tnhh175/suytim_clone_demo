# Hợp đồng điều chỉnh giao diện biểu mẫu

> Hợp đồng này là bản trước yêu cầu v1.0 ngày 25/10. Yêu cầu một cột ở mọi kích thước, quyền Admin chỉ đọc dữ liệu khám và bố cục mới được xác định tại `../revision-ui-spec.md`. Các mô tả hai cột bên dưới giữ để đối chiếu lịch sử.

Người dùng là Bác sĩ nhập/xem hồ sơ theo lượt và Admin quản lý định nghĩa trường. Đối tượng phải đọc trước là mã hồ sơ, lượt, phiên bản; hành động chính là lưu thay đổi hoặc xác nhận phần Excel đã đối chiếu. Giữ mật độ biểu mẫu hai cột trên desktop, một cột trên màn hình hẹp, màu teal hiện có và dữ liệu giả lập. Không thêm dashboard, KPI, ảnh trang trí, gradient hoặc animation.

Giả định: giữ nguyên nghiệp vụ, nhãn tiếng Việt, đăng nhập chung và quyền do máy chủ quyết định. Điều chỉnh CSS không thay đổi dữ liệu hay thêm khả năng HIS/AI.

## Bằng chứng và lựa chọn

- `qa/unified-login.png`: màn hình đăng nhập một cột đang phù hợp; giữ biểu mẫu trực tiếp, giới hạn chiều rộng và khoảng cách co theo chiều cao màn hình.
- `qa/live-excel-result.png`: bảng đối chiếu/kết quả phải giữ cột để đọc theo hàng; cho cuộn trong vùng riêng, không ép toàn trang tràn ngang.
- `design/demo-web/renders/03-doctor-form-mobile.png`: các nhóm dữ liệu và ngữ cảnh hồ sơ phải được nhìn thấy trên điện thoại; giữ nút nhóm có thể xuống dòng, không chỉ ẩn sau một dải cuộn ngang. Đây là ảnh mockup cũ, không là bằng chứng live sau sửa.
- Mẫu tương tác của chính ứng dụng: danh sách hồ sơ → lượt → biểu mẫu; vùng lưu cố định theo màn hình. Giữ mã/lượt nổi bật, chỉ hành động chính dùng nền teal.

## Điều chỉnh có thể kiểm tra

1. Grid nội dung dùng `minmax(0, 1fr)`, các phần tử co được; bảng và chuỗi dài không kéo giãn toàn trang.
2. Header tự tăng chiều cao; không ẩn tên/vai trò đã đăng nhập ở màn hình hẹp. Điều hướng và nhóm trường xuống dòng để mọi mục vẫn có thể tiếp cận.
3. Nút và ô nhập cao ít nhất 44 px; nhãn checkbox cũng có vùng bấm 44 px. Focus bàn phím có viền rõ; control trong bảng có cùng hình thức với biểu mẫu.
4. Văn bản phụ giữ màu tối đủ đọc trên nền sáng, mục đang chọn có màu nền và cạnh nhấn. Disabled phân biệt với trạng thái chờ request; loading có phản hồi khi có `aria-busy`.
5. Dialog có giới hạn chiều cao và tự cuộn; thanh lưu xuống dòng, nút chính dễ tìm ở điện thoại; nội dung dài không bị che/cắt.

## Cổng nghiệm thu

**HOLD cho tới khi có bằng chứng live sau sửa.** Root kiểm đăng nhập, danh sách, biểu mẫu, bảng Excel và dialog tại desktop và 390 px (thêm 320 px khi có thể); xác nhận không tràn ngang toàn trang, focus thấy được, nhóm trường dễ tiếp cận và nút lưu/đăng nhập còn thao tác được. Kiểm tra source/CSS không thay thế screenshot hoặc kiểm thử bàn phím. Không tuyên bố audit WCAG đầy đủ.
