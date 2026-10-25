# Phạm vi sửa theo yêu cầu đã duyệt v1.0

Ngày tiếp nhận: 26/10/2026. Nguồn trực tiếp: `Yeu-cau-sua-demo`, bản ghi ngày duyệt 25/10/2026, SHA-256 `841d9732b028714451b7226d2e08f00c35749c5d12d866cd029548eb1008c07c`.

Tài liệu là yêu cầu sản phẩm người dùng yêu cầu áp dụng; các câu mô tả chưa sửa mã/chưa commit trong tài liệu là trạng thái tại thời điểm soạn, không phải bằng chứng triển khai hoặc kiểm thử. Quyết định mới thay những điểm mâu thuẫn của prompt v3, đặc biệt đăng nhập chung, Admin xem hồ sơ dùng chung và giữ mẫu theo lượt.

## Đợt hiện tại

- C01–C13: đăng nhập chung; quyền Admin/Bác sĩ; mã BN; thông tin hành chính và lượt; tổng quan có nguồn; một cột nhập; nhập file Excel; quản lý phiên bản mẫu; bỏ dòng phụ dư quanh tên sản phẩm.
- A01–A03, A07–A08, A12–A14: kiểm tra dữ liệu, bệnh sử/lý do khám, chọn ngày giờ, phân biệt chức năng chưa làm, trạng thái lưu/lịch sử, cấu hình ánh xạ, editor mẫu và ca trình diễn giả lập.
- A05: triển khai thông tin đã đủ căn cứ; trạng thái bệnh đã biết không phụ thuộc việc HbA1c/eGFR còn thiếu đặc tả.
- A04/A06: chỉ nhận phần cấu trúc đủ nguồn phục vụ đợt này; không tuyên bố đã chuẩn hóa toàn bộ dữ liệu trước AI.
- A09–A11 và chuỗi AI, điểm số, công thức chưa đủ nghĩa dữ liệu: giai đoạn sau theo mục 7 của nguồn. Không tạo kết quả AI giả.

## Kiểm tra nguồn file

Đã đọc lại workbook người dùng cấp bằng openpyxl: `Sheet3`, 19 dòng dữ liệu, 42 cột, 15 giá trị `MaNghienCuu` phân biệt, không có header mã lượt rõ ràng. Không ghi giá trị bệnh nhân vào Git. Vì thiếu định danh lượt và hợp đồng nguồn chưa xác nhận, không thể lấy việc đọc được workbook này làm bằng chứng tương thích HIS.

Luồng nhập vẫn là Excel; tên Nhập file không bổ sung JSON/CSV/HL7. Các dòng thiếu cặp mã hồ sơ/lượt phải chờ đối chiếu; không dùng ngầm hồ sơ đang mở. Mã cũ/mã nguồn đã có liên kết được giữ khi đổi mã BN. NULL không xóa giá trị đích.

TL06 `Trường dữ liệu` hàng 2 có phạm vi tuổi `0–120 tuổi`; đây là căn cứ kiểm tra tuổi. Không dùng phạm vi bình thường để chặn giá trị bất thường có thể xảy ra. Các quy tắc khác chỉ được thêm trong giới hạn nguồn và yêu cầu đã duyệt.

## Bảo toàn và bằng chứng

Trước chuyển dữ liệu live đã lưu bản sao riêng ngoài Git. Baseline có 4 hồ sơ, 5 lượt, 7 phiên bản lịch sử và 2 lần nhập file. Mục tiêu migration là giữ nguyên ID/liên kết/số bản ghi; dữ liệu giả lập trình diễn bổ sung phải được ghi nhận riêng.

K01–K15 là tiêu chí, chưa phải kết quả. Kết quả thực chạy ghi riêng trong `qa/revision-acceptance.md` và báo cáo tích hợp. Các cập nhật hợp lệ sau commit `36cac2c` được giữ; chưa có yêu cầu commit/push đợt này.
