# Kiểm thử giao diện ứng dụng thật

Ngày 24/10/2026, điều phối thực hiện qua Codex in-app browser tại `http://127.0.0.1:8001/`. Backend PostgreSQL schema giả lập `d3_form_live_20261024`. Đây là ứng dụng `web/forms.*`, không phải mockup `design/demo-web`.

## Kết quả đã quan sát

| Ca | Thao tác và bằng chứng | Kết quả |
|---|---|---|
| Cổng đăng nhập | Dùng tài khoản Doctor tại `/admin/login`: báo thông tin không hợp lệ; đúng `/bac-si/login` vào danh sách hai hồ sơ giả lập. Không có nút quản lý trường cho Doctor. | Đạt đường UI đã kiểm; kiểm cả chiều ngược và quyền API ở Dev suite. |
| Hồ sơ/lượt | Tìm `SYN-FORM-001`, thấy `VISIT-001-1` revision2 và `VISIT-001-2` revision0; mở lượt1. | Đúng ngữ cảnh hồ sơ/lượt. |
| Giá trị rỗng/0/false | Cân nặng hiển thị0, chiều cao trống, khó thở khi nằm Không; BMI hiển thị chưa đặc tả, không tự tính. | Giá trị hiển thị phân biệt đúng. |
| Lưu và lịch sử | Sửa ghi chú thành `QA giao diện 24/10: lưu và mở lại dữ liệu giả lập.`; máy chủ xác nhận, revision3. Lịch sử có actor forms_doctor, thời gian, nguồn manual; 0/Không/trống giữ nguyên. Reload và đăng nhập lại vẫn thấy ghi chú. | Đạt. |
| Trường động | Tab Admin tạo textarea `qa_ui_20261024`, nhãn `Ghi chú kiểm tra giao diện`. Doctor mở lại cùng lượt thấy trường trống; nhập `Giá trị trường động được nhập qua UI.` và lưu revision4. | Đạt, không sửa code/build/DDL giữa hai thao tác. |
| Excel nguồn/ánh xạ | Tải mẫu giả lập từ nút ứng dụng, upload `.xlsx`, chọn `GIA_LAP`, header1; A/B là mã hồ sơ/lượt; C→Cân nặng có xác nhận kg; D→Khó thở khi nằm với bảng mã true/false. | Đọc file/sheet và ánh xạ được. |
| Preview và hủy | Preview hai dòng hợp lệ: ca1 có C2=61 so với đích0 mặc định giữ; D2=false không đổi; ca2 C3 trống bỏ qua, D3=true bổ sung. Hủy rồi upload/preview lại vẫn thấy cùng giá trị đích. | UI đạt; API count test xác minh không ghi nghiệp vụ. |
| Commit Excel | Giữ xung đột mặc định, xác nhận cả hai dòng: ghi1 trường trong1 lượt, bỏ qua3 trường. Ca1 vẫn revision4; ca2 revision1. | Đạt, ảnh `qa/live-excel-result.png`. |
| Lịch sử nhập | Mở lịch sử tài khoản, thấy lần nhập đúng tên file/thời gian/số trường; mở chi tiết có kết quả và mục ánh xạ. | Đạt. |
| Nhập lại | Upload lại cùng file và ánh xạ, xác nhận: hiển thị `Đã nhận diện lần nhập lặp`, trả cùng revision4/1. | Đạt UI nhận diện replay; không thêm bản DB được kiểm trong suite. Ảnh `qa/live-excel-replay.png` chụp trước chỉnh câu giải thích kết quả cũ. |
| Mobile | Màn hình mapping tại viewport390×844: document/body scrollWidth375 ≤ innerWidth390; quan sát screenshot không tràn ngang toàn trang. Đã reset viewport sau kiểm. | Đạt tại màn hình này, không chứng nhận toàn bộ accessibility. |
| Phạm vi | Navigation chỉ Hồ sơ, Excel và quản lý trường theo role. Chú thích AI chưa triển khai; phần danh sách Excel chưa có adapter được nêu rõ. | Không có chức năng nhập JSON. |

## Bằng chứng bổ trợ và giới hạn

`dev-validation.md` ghi API/DB, rollback, retry/concurrency, quyền và restart tiến trình thật. `qa/independent-qa-report.md` ghi review và test hàm độc lập của Tester. Không suy ra rollback/quyền DB từ screenshot. Bốn test legacy opt-in bị skip được nêu riêng trong báo cáo Dev.

Chưa kiểm trên trình đọc màn hình thật, nhiều engine trình duyệt hoặc mạng di động; không công bố WCAG/Lighthouse hay benchmark tải. Workbook mẫu là dữ liệu giả lập; chưa xác nhận tương thích HIS thật. 136 trường TL06 chưa đủ đặc tả không được biến thành dữ liệu giả. Excel danh sách thuốc/kết quả cần hợp đồng nguồn riêng; biểu mẫu nhập tay hỗ trợ cấu trúc.

## Retest lượt chưa có mã ngoài

Root đã tạo hồ sơ `QA-UI-20261024` và một lượt qua UI, để trống mã ngoài/thời điểm. Trong Excel chọn chế độ một dòng, dòng2, đúng hồ sơ/lượt đích, tích xác nhận, C→Cân nặng và xác nhận đơn vị. Preview hiển thị đúng1 dòng đủ điều kiện, nhãn `Lượt được đối chiếu, chưa có mã ngoài`; commit ghi1 trường/1 lượt revision1. Không nhập dòng3 vào ca này. Q-IMPORT-02 được xác minh sửa trên UI, bổ sung cho test PostgreSQL và test hàm độc lập.

Khi retest, browser từng giữ JavaScript cũ khiến dropdown bỏ lượt trống mã. Đã thêm phiên bản query cho JS/CSS trong forms.html; tải lại sau sửa thấy `Lượt chưa có mã ngoài #1 · phiên bản 0` và hoàn tất nhập. Bản cuối cũng reset xác nhận khi đổi đích/dòng; phần reset này được review mã, chưa kiểm UI riêng. Luồng đăng xuất/hai chiều sai cổng được API suite kiểm; root chưa hoàn tất cả hai chiều UI do browser session bị khởi tạo lại giữa các lần tiếp tục.
