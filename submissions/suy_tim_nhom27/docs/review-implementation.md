# Đối chiếu triển khai review giao diện ngày 09/10/2026

Phạm vi: đăng nhập, cổng bác sĩ và cổng bệnh nhân trong `web/`, cùng thay đổi tối thiểu ở xác thực vai trò đăng nhập. Các tài liệu trong `Review/` là yêu cầu đối chiếu, không bị sửa thành biên bản nghiệm thu. Tên HF Care được dùng tạm theo review; thiết kế Swiss hiện có giữ nền `#FFFFFF`/`#F7F7F8`, xanh `#002FA7`, Helvetica/sans và đường kẻ 1 px.

## Đăng nhập

| Mục review | Triển khai | Chứng cứ kiểm tra |
|---|---|---|
| UI-01 | HF Care, tiêu đề và mô tả quản lý bệnh nhân suy tim thống nhất với header | Browser nhóm `review login` |
| UI-02 | Hai cột gọn trên desktop; form đứng trước phần giới thiệu trên mobile | 1366×768, 1920×1080, 360×800; screenshot `login-clean-*` |
| UI-03 | Username/password trống, năm vai trò, không chọn nhanh tài khoản; Hiện/Ẩn có `aria-controls`/`aria-pressed`; chặn gửi lặp | Browser kiểm tra trường trống, focus, sai vai trò, đăng nhập đúng; Python auth |
| UI-04 | Thông báo an toàn ngắn bằng tiếng Việt; bỏ endpoint và nhãn demo khỏi màn đăng nhập; thông tin kỹ thuật ở phần mở rộng | Kiểm tra source và ảnh login |
| UI-05 | Style chung, focus rõ, target tối thiểu 44 px; bệnh nhân 48 px và chữ 17–18 px | Browser responsive và kiểm tra CSS |
| UI-06 | Lỗi thân thiện theo mã HTTP; lỗi đăng nhập tại trường và focus; đăng xuất “Bạn đã đăng xuất.” theo trạng thái thành công | Browser lỗi mạng/403/409/422, logout và login |
| UI-14 | Chỉ tự đăng ký bệnh nhân; tạo hồ sơ giả lập mới; không tự liên kết hồ sơ đã tồn tại | Python đăng ký trên PostgreSQL QA; browser signup/login/restore session |
| AUTH-01 | Giữ yêu cầu mật khẩu đăng ký hiện có; không hạ xuống mật khẩu yếu | Không thay đổi chính sách mật khẩu |

`selected_role` là trường tùy chọn của `/auth/token`: enum năm vai trò; server so với `actor.role` sau xác thực mật khẩu và trước INSERT phiên. Sai vai trò trả cùng thông báo `401` như sai tài khoản/mật khẩu; enum không hợp lệ trả `422`. Caller hai trường username/password giữ tương thích. Trường `role` không thuộc schema vẫn bị từ chối. `api/openapi.yaml` được xuất lại từ app; mô tả tại `api/README.md`.

## Bác sĩ

| Mục review | Triển khai | Chứng cứ kiểm tra |
|---|---|---|
| D-01/UI-07 | Sidebar Tổng quan/Bệnh nhân; hồ sơ có tabs Tổng quan hồ sơ/Các lần khám/Ghi nhận/Hỗ trợ đánh giá/Lịch sử; breadcrumb, mã/tuổi/giới/lần khám, Đổi bệnh nhân | Browser nhóm doctor tabs và desktop |
| D-02/UI-08 | Tổng quan đếm hồ sơ từ API, tối đa năm hồ sơ mở nhanh, danh sách và tạo hồ sơ | API thật; không tạo số liệu hoặc cảnh báo lâm sàng |
| D-03/UI-09 | Tìm mã hồ sơ, xem/cập nhật hồ sơ đúng ngữ cảnh; tạo hồ sơ thu gọn; giữ CRUD hiện có | Browser tìm kiếm, create/update context; UUID không nằm ở danh sách thường |
| D-04/UI-10 | Chưa chọn bệnh nhân khác hồ sơ chưa có lần khám; lần khám mới nhất trước; ghi nhận nằm ở tab riêng; dữ liệu/đơn vị từ API | Browser observation thêm/sửa/hydrate/cancel, nurse allowlist |
| D-05/UI-11 | ID/revision bác sĩ là trường hidden từ ngữ cảnh; module tiếng Việt; trạng thái “Chưa có đánh giá lâm sàng”; không quyết định/kê đơn từ kết quả thử nghiệm | Browser evaluation và lỗi GET sau POST; pharmacist vẫn cần revision được cấp |
| D-06/UI-12 | Lịch sử trong hồ sơ, lấy thời điểm lần khám từ API, mới nhất trước, xuất JSON | Browser history và source đối chiếu |
| D-07/UI-13 | Xác nhận trước khi rời form chưa lưu; Hủy giữ dữ liệu; đổi bệnh nhân xóa lần khám/kết quả/draft cũ; request kiểm tra epoch/token | Browser dirty cancel/proceed, delayed response, logout401, object/context snapshots |

Luồng mở lần khám bằng ID được giữ trong phần **Thông tin kỹ thuật** đóng mặc định để bảo toàn khả năng kiểm tra ngữ cảnh/quyền hiện có. Giao diện nghiệp vụ dùng danh sách lần khám. Bản nháp ghi nhận mới được lưu riêng theo ID lần khám; không gán bản nháp hay observation đang sửa vào lần khám khác. Đổi bệnh nhân và đăng xuất xóa bản nháp. Khôi phục sau lỗi và retry đều xử lý tab Ghi nhận như luồng lần khám trước đây.

## Bệnh nhân

| Mục review | Triển khai | Chứng cứ kiểm tra |
|---|---|---|
| P-01 | Chữ/target lớn, một cột mobile, bảng thành thẻ, nhãn/đơn vị/focus rõ | 768/390/360/320 px, năm vai trò; desktop 1366/1920 |
| P-02 | Bốn CTA Lịch khám/Theo dõi sức khỏe/Đơn thuốc/Lịch dùng thuốc; lịch sắp tới, nhắc pending và thời điểm số đo từ API | Browser bốn CTA và API thật; signup mới hiển thị hướng dẫn bắt đầu |
| P-03 | “Gửi yêu cầu lịch khám”; chỉ báo Chờ xác nhận khi API `requested`; hủy có xác nhận; chỉ requested/confirmed có nút; không có bác sĩ thì disable và giải thích | Browser tạo/hủy lịch thật trên QA; trường hợp không có bác sĩ/final states mô phỏng |
| P-04 | Đơn vị, nguồn Bệnh nhân tự nhập; cặp huyết áp, số dương, SpO₂ 0–100, tâm thu ≥ tâm trương; thời điểm theo ràng buộc SQL; lỗi tại trường/focus; ô trống khác số 0 | Browser BP/range/focus, lưu SpO₂=0 thật, lịch sử; Python portal |
| P-05 | Đơn chỉ đọc; Đã uống/Bỏ qua chỉ pending; không tự sửa thuốc/liều/giờ; phản hồi tải trạng thái từ API | Browser pending/final states; Python portal |
| P-06 | Tài khoản chỉ hiển thị username/vai trò từ `/auth/me`, không dựng thông tin nhân thân; đăng ký/quyền/liên kết giữ nguyên | Python đăng ký/isolation; browser tài khoản/signup |
| P-07 | Loading/empty/error/saved nhất quán, an toàn luôn tìm thấy; API patient/RLS giữ phạm vi chính tài khoản | Browser lỗi/race/saved retry; Python portal/auth |

Ràng buộc số đo dựa vào `MeasurementCreate` và `validate_patient_measurement`, không thêm ngưỡng nguy cơ/chẩn đoán. Lịch yêu cầu dùng khung 30 phút theo CHECK SQL; không coi việc chọn giờ là bằng chứng bác sĩ còn lịch trống. Đơn thuốc và lịch dùng thuốc giữ hai mục để phản ánh hai nguồn và hai quyền thao tác hiện có; biểu mẫu nhập/lịch sử số đo cùng màn hình.

## Phần chưa triển khai vì cần nguồn/API bổ sung

- Tên sản phẩm chính thức, họ tên/ngày sinh/liên hệ, quy trình danh tính/xác minh/liên kết hồ sơ thật; không dựng trường hoặc tên người dùng.
- Lịch bác sĩ còn trống, nhân viên xác nhận/hoàn tất lịch và tích hợp lần khám; không báo lịch đã xác nhận từ `requested`.
- Bác sĩ duyệt số đo bệnh nhân thành dữ liệu lâm sàng; số đo tự nhập vẫn là `patient_measurement`.
- Module đánh giá lâm sàng thật, kết quả/chẩn đoán/xét nghiệm/điều trị/an toàn thuốc và quyết định từ kết quả; không giả dữ liệu.
- Tạo/xác nhận đơn thuốc đầy đủ từ ghi nhận thuốc trong lần khám; hai khái niệm vẫn tách biệt.
- Timeline chăm sóc đầy đủ, biểu đồ/nhận định nguy cơ, thông báo push/SMS/email, đổi mật khẩu/chỉnh nhân thân khi chưa có API.

## Kiểm tra và nguồn chứng cứ

Sau review độc lập, ba điểm P2 đã được sửa: mở lần khám bằng ID cũng xác nhận form chưa lưu trước khi tải; ghi chú/thuốc dùng nhãn tiếng Việt và UUID ghi chú nằm trong phần kỹ thuật đóng mặc định; trang chủ bệnh nhân hiển thị bốn thao tác trước khi đọc dữ liệu, mỗi nguồn có loading/error/empty và nút tải lại riêng. Lỗi một nguồn không che thao tác hoặc dữ liệu của nguồn khác, tải lại chỉ đọc nguồn bị lỗi. Kiểm thử bổ sung xác nhận Hủy/Đồng ý với form ghi chú, UUID/option labels giữ nguyên dữ liệu, lỗi nguồn, retry riêng và phản hồi 401 cũ sau chuyển màn.

- Python: `PYTHONPATH=src`, `HF_REGISTRATION_TEST_DATABASE_URL=postgresql://hf_demo_runtime@127.0.0.1:5432/hf_demo_ux_qa`; **64 passed, 0 skipped**. Có một cảnh báo deprecation từ Starlette/httpx; không làm thay đổi kết quả.
- Browser: Chrome/Playwright context QA riêng tại `127.0.0.1:8001`, dùng database `hf_demo_ux_qa`; **24 passed, 0 failed**, không có lỗi runtime trình duyệt. Giữ 17 nhóm hồi quy cũ và thêm 7 nhóm review, gồm hai nhóm sửa sau review độc lập. Kích thước: desktop 1366×768/1920×1080, mobile/tablet 768/390/360/320 px.
- API thật được dùng cho năm vai trò, CRUD hồ sơ/lần khám/ghi nhận, evaluation trạng thái thử nghiệm, đăng ký, số đo và yêu cầu/hủy lịch. Xác nhận đổi lần khám bằng ID và UUID/nhãn dùng dữ liệu API thật. Interception chỉ mô phỏng lỗi mạng/403/409/422, GET lỗi sau mutation, delayed responses, không có bác sĩ, trạng thái final và lỗi riêng nguồn lời nhắc trên trang chủ; retry đọc nguồn thật và kiểm tra 401 cũ không ghi đè màn hình mới.
- Screenshot và log đầy đủ nằm trong `.context-shears/review-browser` và `.context-shears/artifacts` của workspace; không đưa artifact runtime vào Git. Không chạy mutation test trên preview `:8000`/database `hf_demo`.
