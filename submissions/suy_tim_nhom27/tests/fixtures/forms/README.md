# Fixture Excel giả lập

Mọi định danh và giá trị là giả lập, không phải xuất HIS hoặc dữ liệu bệnh nhân.

- `synthetic-valid.xlsx`: sheet GIA_LAP, header hàng 1, hai hồ sơ/lượt khác nhau; 0, false và ô trống không được đánh đồng.
- `synthetic-invalid.xlsx`: sheet GIA_LAP, hàng 2 sai kiểu tuổi; hàng 3 thiếu cả hai định danh. Preview phải báo riêng lỗi/chờ, không báo đã lưu.
- Mapping: cột 1 mã hồ sơ, cột 2 mã lượt, cột 3 → tuoi (native), cột 4 → kho_tho_khi_nam (native), cột 5 → can_nang (native, xác nhận kg). Cột note là nhãn giả lập, bỏ qua.
- Chuẩn bị hồ sơ/lượt có đúng mã trên DB thử trước commit. Không import vào dữ liệu thật. Preview không tạo hồ sơ/lượt ngầm.
- NULL/[] và danh sách có cấu trúc được kiểm tra bằng validator nội bộ; workbook scalar này không chứng minh adapter nhóm thuốc/xét nghiệm đã hoàn tất.

Đã bỏ fixture nhập JSON theo yêu cầu mới. Catalog JSON, JSONB và serialization API nội bộ vẫn phục vụ ứng dụng.
