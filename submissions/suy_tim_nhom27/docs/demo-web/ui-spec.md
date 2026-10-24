# UI spec — demo web M1/M2

Ngày: 23/10/2026. Chủ sở hữu U1 / UX/UI. Đây là thiết kế đề xuất bám nguồn, không phải kết quả triển khai backend hay xác nhận lâm sàng.

## Phạm vi và cách mở

Mở `../../design/demo-web/index.html` bằng Chrome/Edge. Có thể chỉnh trực tiếp index.html, styles.css và mockup.js. Hash bắt đầu `#login-doctor` hoặc `#login-admin`. Đăng nhập mẫu chỉ mở màn hình thiết kế; không xác thực. Mockup không gọi API, không lưu localStorage/CSDL. Tất cả tên, mã và số trong mockup là giả lập.

Nguồn ưu tiên: prompt-v3.txt mục C/D/F/G/I; gói v0.2 PHAM_VI_HIEN_HANH, PROMPT_DEV §§6–13, BIEU_DIEN_TRUONG. Yêu cầu mới nhất của người dùng bỏ chức năng nhập JSON; phạm vi UI hiện hành chỉ M1/M2 Excel. Không sửa SRS/report/RTM cũ. Không thêm dark mode/animation theo ví dụ skill.

## Thành phần và bố cục

- Header trắng: tên sản phẩm, cổng đã xác thực, đăng xuất. Sidebar 224px: hồ sơ, Excel; chỉ Admin có quản lý trường.
- Main tối đa 1420px; desktop padding 32px, mobile 14px. Form có mục lục 190px và nội dung linh hoạt; dưới 1000px mục lục thành hàng; dưới 700px sidebar thành navigation ngang, form một cột.
- Font Segoe UI/system; body 15px/1.55, H1 28px, H2 19px. Spacing 4/8/12/16/20/24/32px. Control min-height 44px.
- Tokens: nền #f4f7f9; surface #fff; text #172b37; muted #536775; primary #145b68; border #d6e0e5; lỗi #9f2727; cảnh báo #805313; thành công #23613c.
- PatientVisitContext: tên/mã hồ sơ và mã/thời điểm lượt luôn trước form; không dùng tên làm định danh.
- FieldControl: label gắn control, đơn vị ở nhãn, helper/error ngay dưới; details chứa mã/nguồn/phiên bản. Boolean luôn Chưa có dữ liệu/Có/Không; số/ngày/select bắt đầu trống.
- RepeatableList: thuốc/kết quả theo các mục có cấu trúc, thêm/bỏ mục; NULL chưa biết không tự đổi thành [] không có mục. Cấu trúc chính thức lấy từ import-contract/schema, không lấy mockup làm schema y khoa.
- PendingField: disabled + lý do thiếu đặc tả; không đặt lựa chọn/thang điểm giả.
- SaveBar: trạng thái chưa thay đổi/dirty/saving/success/error/conflict, nút lưu bị khóa trong request. Chỉ success khi máy chủ xác nhận. Lưu không hoàn tất lượt/chẩn đoán/đơn thuốc.
- ImportStepper: Nguồn → Cấu trúc/kiểm tra → Ánh xạ → Đối chiếu → Kết quả. Conflict table: vị trí nguồn, trường, giá trị đích, nguồn nhập, quyết định. Giữ hiện có mặc định.

## Trạng thái và tương tác bắt buộc trong live web

| Trạng thái | Hiển thị / hành động |
|---|---|
| Loading | Thông báo đang tải, aria-live polite; khóa thao tác phụ thuộc dữ liệu |
| Empty | Không có hồ sơ/lượt/mục; hành động tạo phù hợp quyền; không bịa dữ liệu |
| Dirty | Có thay đổi chưa lưu; xác nhận trước rời form; không xóa dữ liệu đang nhập |
| Saving | Đang lưu; tránh gửi lặp; chưa báo thành công |
| Saved | Phiên bản/thời điểm đã xác nhận; lịch sử cùng phiên bản |
| Error | Tóm tắt có liên kết tới control lỗi; giữ giá trị; đọc lại trạng thái nếu response không rõ |
| Conflict | Báo phiên bản mới, giữ bản nháp; đối chiếu trước–sau, không tự ghi đè |
| Pending import | Sai/mơ hồ định danh, đơn vị hoặc ngày; không ghi, nêu vị trí nguồn |
| Duplicate import | Không thay đổi/bỏ qua; không tạo hồ sơ/lượt/mục trùng |
| Retired field | Ngừng nhập mới; vẫn đọc giá trị và lịch sử cũ |

Các nút trong details “Điều khiển trạng thái bản thiết kế” dùng để xem loading/empty/error/conflict/success, không đưa vào live web. Trạng thái import và dữ liệu bảng là mẫu định trước, không phải parser thật. Bản thiết kế không chứng minh quyền, giao dịch, persistence hoặc rollback.

## Backend/component contract bàn giao

Kế thừa HTML/JS + FastAPI. `/api/forms/auth/admin|doctor` phải cố định cổng trên server; `/fields` GET POST PATCH; `/patients` GET POST; `/patients/{id}/visits` GET POST; `/visits/{id}` GET PATCH; `/visits/{id}/history` GET. Đây là hợp đồng phối hợp, cần đối chiếu implementation cuối.

FieldDefinition: code, label, group, type, unit, choices[{code,label}], help, order, active, version. Patient: code/external_id/display_name; Visit: external_id/occurred_at/revision. Mã immutable; đổi nhãn giữ giá trị; đổi kiểu/đơn vị đã có dữ liệu chặn khi chưa có chuyển đổi. Trường mới không tự trở thành AI input đã duyệt.

PATCH chỉ gửi thay đổi. Thiếu key giữ đích, null chỉ khi xóa chủ ý được phép; false/0 hợp lệ giữ nguyên. Import null/thiếu không xóa đích. Bác sĩ chỉ chọn field đã tồn tại, không tạo field qua mapping. Import limits, batch boundaries, schema_version và đường dẫn API lấy contract Agent 1/Dev; không hard-code từ mockup.

## Bàn phím, responsive và giới hạn kiểm tra

Dùng semantic header/nav/main/section/table/form, label, native select/date; skip-link; focus-visible 3px; tất cả control dùng Tab/Enter/Space theo native behavior. Cảnh báo có văn bản, không chỉ màu. Bảng rộng cuộn trong vùng riêng. Mục tiêu WCAG AA, chưa tuyên bố audit toàn diện hoặc screen-reader pass.

Đã render Edge headless qua Playwright desktop 1440×1100 và mobile 390×844, lưu `design/demo-web/renders`. Kiểm tra tương tác tạo mục thuốc, dirty, save mô phỏng, admin options/preview, Excel sheet, Excel conflict. Không pageerror; mobile không overflow toàn trang trong form. Xem validation.json cho bằng chứng chính xác. Ảnh đã quan sát trực tiếp: Excel conflicts desktop và form mobile. Chưa kiểm tra mọi chiều rộng/zoom hoặc mọi công nghệ hỗ trợ.

Kiểm tra bàn phím cụ thể: reload cổng Bác sĩ → Tab focus link “Đến nội dung chính” → Enter focus main (skipTarget=main); không pageerror. Kiểm tra menu Bác sĩ: số link Quản lý trường = 0. Đây là kiểm tra bàn phím hẹp, không phải full keyboard audit.
