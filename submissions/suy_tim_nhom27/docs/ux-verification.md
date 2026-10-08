# Kiểm tra tương tác web và đăng ký

Phạm vi: giao diện HTML/CSS/JavaScript hiện tại; đăng ký mới chỉ patient, hồ sơ mới synthetic. Các quyền staff/patient, optimistic revision, RLS, allowlist điều dưỡng và output `mock_not_evaluated` giữ nguyên hợp đồng API. Mọi dữ liệu và giá trị hiển thị đến từ API; mock trong browser test chỉ dùng để mô phỏng lỗi/mạng.

## Luồng giao diện

- Bác sĩ có sidebar Tổng quan/Bệnh nhân; chọn hồ sơ để làm việc trong tabs ngữ cảnh. Danh sách lọc mã hồ sơ; Xem hồ sơ để xem/cập nhật, Các lần khám mở danh sách của bệnh nhân. Form tạo thu gọn khi đã có hồ sơ.
- Lần khám và Ghi nhận là hai tabs riêng của bác sĩ; tạo lần khám và mở ID trong phần mở rộng Thông tin kỹ thuật. Sửa observation mở form và đưa focus tới trường loại dữ liệu. Snapshot phân biệt thêm/sửa và ID observation; bản nháp thêm được giữ riêng theo lần khám, hủy sửa trả về đúng bản nháp, chuyển lần khám không mang theo observation đang sửa. Đổi bệnh nhân/đăng xuất xóa bản nháp; rời form chưa lưu cần xác nhận.
- Form giữ dữ liệu khi lỗi; nút đang xử lý chặn gửi lặp. `409` cho phép đọc phiên bản mới trước khi gửi lại. POST đã lưu nhưng GET tiếp theo thất bại chỉ cho tải dữ liệu đã lưu, không gửi lại mutation.
- Snapshot form có ngữ cảnh hồ sơ/lần khám tương ứng: hồ sơ mới không nhận bản nháp sửa hồ sơ cũ. MedSafety điền ID từ lần khám vừa tải thành công, giữ revision nhập ở cùng lần khám, xóa revision khi chuyển lần khám; không tự đoán revision. Tải bị từ chối giữ ngữ cảnh trước đó.
- Chỉ khi các API đọc lần khám mới đều thành công, ứng dụng xóa kết quả evaluation và ID chờ tải của lần khám cũ. Mở bằng ID, chọn hàng và chuyển hồ sơ đều áp dụng quy tắc này; kết quả hoặc retry cũ không hiển thị dưới lần khám mới.
- Mỗi request kiểm tra phiên/màn hình trước khi cập nhật state hoặc DOM. Phản hồi của màn hình cũ hoặc trước đăng xuất không thay đổi màn hình hiện tại.
- Cổng patient dùng cột tiếng Việt, thời điểm, đơn vị và trạng thái, bỏ cột JSON kỹ thuật. Chỉ lịch requested/confirmed có Hủy và xác nhận; chỉ reminder pending có Đã uống/Bỏ qua; đơn thuốc chỉ đọc. Số đo tự nhập có nhãn nguồn, lỗi tại trường và giữ đúng giá trị 0 được API cho phép.
- Trên 768/390/360/320 px form một cột, bảng patient thành hàng dạng thẻ. Sidebar ẩn không nhận Tab; Escape đóng và trả focus; chọn màn hình đưa focus tới tiêu đề. Xem mapping review và phần cần backend tại [review-implementation.md](review-implementation.md).

## Chạy kiểm tra

Chạy Python tại thư mục submission với `PYTHONPATH=src`:

```powershell
$env:PYTHONPATH = 'src'
python -m pytest -q
```

Các kiểm tra PostgreSQL đăng ký tự bỏ qua nếu không đặt biến sau. Chỉ dùng cơ sở dữ liệu QA synthetic riêng; kiểm tra cố ý giữ user/link có tên `qa_...` vì liên kết patient_account là bất biến.

```powershell
$env:HF_REGISTRATION_TEST_DATABASE_URL = 'postgresql://hf_demo_runtime@127.0.0.1:5432/hf_demo_ux_qa'
python -m pytest -q tests/test_registration.py
```

Browser test dùng Chrome/Playwright context riêng, không điều khiển phiên trình duyệt người dùng. Khởi chạy API của submission với database QA trên `127.0.0.1:8001`, cài `playwright-core` ở nơi QA riêng, rồi:

```powershell
$env:HF_QA_PLAYWRIGHT_MODULE = '<absolute-path-to-playwright-core>'
$env:HF_QA_BASE_URL = 'http://127.0.0.1:8001'
$env:HF_QA_ARTIFACT_DIR = '<absolute-managed-artifact-directory>'
node tests/ux-browser.mjs
# Chỉ chạy nhóm observation khi kiểm tra sửa/hủy/bản nháp:
$env:HF_QA_TEST_FILTER = 'observation'
node tests/ux-browser.mjs
Remove-Item Env:HF_QA_TEST_FILTER
```

Browser test đọc API thật cho năm vai trò, tạo hồ sơ/observation/signup synthetic chỉ trên DB QA, dùng request interception cho lỗi mạng/403/409/422 và GET sau mutation. Không chạy trên DB sử dụng thật. Screenshot/command artifacts thuộc `.context-shears`, không đưa vào Git.

Nhóm `context` kiểm tra giá trị code/tuổi/giới tính của hồ sơ mới, ID/revision MedSafety với hai lần khám thật trong scope, tải bị từ chối, và evaluation thật trước/sau chuyển lần khám. GET evaluation thất bại được mô phỏng; kiểm tra xác nhận không retry ID cũ dưới ngữ cảnh mới. Nhóm signup kiểm tra tổng quan của tài khoản patient mới không mang nhãn `patient_demo`.

Kiểm tra real DB chứng minh patient mới tách khỏi user khác/seed, staff403, concurrent duplicate201+409, cấu hình doctor sai không tạo user/case, failure mô phỏng ở bước INSERT link rollback các bước thật trước đó. Unit checks kiểm validation, salt, work factor, rate limit và DB chưa cấu hình.
