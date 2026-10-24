# Mockup editable M1 / M2

Mở index.html bằng Chrome/Edge. Cổng mặc định Bác sĩ; liên kết bên dưới login dẫn đến cổng Admin riêng. Không cần server. Mọi dữ liệu là giả lập; không gọi API hoặc lưu CSDL. Đây là thiết kế để Dev tham khảo, không phải demo persistence.

Chỉnh index.html (shell), styles.css (tokens/layout/components), mockup.js (screens/interactions). Handoff: ../../docs/demo-web/ui-spec.md, user-flows.md, ui-requirements-map.md.

Renders: 01 doctor login; 02 desktop form; 03 mobile form; 04 Excel conflicts; 05 Excel sheet; 06 Admin login; 07 Admin field. validation.json ghi kiểm tra thật đã chạy. render-check.cjs dùng Playwright bundled trên máy hiện tại và Edge; đường dẫn dependency là đường dẫn môi trường, cần sửa khi chạy máy khác.

Các state controls nằm trong details cuối trang để duyệt loading/empty/error/conflict/success. Form có dirty, thêm mục thuốc/kết quả, save mô phỏng. Không dùng số counter hoặc phản hồi mockup làm bằng chứng kiểm thử backend.
