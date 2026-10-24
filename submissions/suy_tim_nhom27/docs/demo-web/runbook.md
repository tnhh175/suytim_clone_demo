# Chạy demo biểu mẫu và nhập Excel

Phạm vi hiện hành: M1 nhập tay/trường động và M2 Excel. Kế thừa HTML/CSS/JavaScript, FastAPI, xác thực phiên và PostgreSQL của repo. Không có chức năng dán/tải file JSON, kết nối HIS trực tiếp hoặc AI hoạt động. Không sửa SRS/report/RTM cũ.

## Mở bản đang chạy

- Trang chọn cổng: http://127.0.0.1:8001/
- Admin: http://127.0.0.1:8001/admin/login
- Bác sĩ: http://127.0.0.1:8001/bac-si/login
- Tài khoản thử được tạo ngẫu nhiên, nằm riêng trong `D:\1.TNHH\project\suytim_clone_demo\local-data\form-demo-live-credentials.json`. Không đưa nội dung file này vào Git, ảnh hoặc log công khai.
- Bản chạy dùng schema riêng `d3_form_live_20261024` trong PostgreSQL `hf_demo`; các ca giả lập không trộn với bảng nghiệp vụ có sẵn trong `public`.

Kiểm tra `/health` phải trả HTTP 200, `persistence=postgres`. `/` HTTP 200 chỉ xác nhận trang tải được; đăng nhập và đọc hồ sơ còn cần database.

## Thiết lập và chạy lại

Thực hiện từ `submissions/suy_tim_nhom27` trong đúng repo. Cần Python, PostgreSQL và runtime role của ứng dụng đã được thiết lập. DSN lấy từ cấu hình riêng; tài khoản runtime phải được phép `SET ROLE hf_demo_owner`. Không ghi mật khẩu thật vào tài liệu/lệnh được chia sẻ.

```powershell
Set-Location 'D:\1.TNHH\project\suytim_clone_demo\submissions\suy_tim_nhom27'
$env:DATABASE_URL = '<DSN PostgreSQL riêng của môi trường>'
& '.\.venv\Scripts\python.exe' -m pip install -r requirements-dev.txt
& '.\.venv\Scripts\python.exe' scripts/seed_form_demo.py --schema d3_form_live_20261024 --credentials-file 'D:\1.TNHH\project\suytim_clone_demo\local-data\form-demo-live-credentials.json'
& '.\.venv\Scripts\python.exe' scripts/run_form_demo.py --schema d3_form_live_20261024 --port 8001
```

`seed_form_demo.py` chỉ chấp nhận schema tên bắt đầu `d3_form_`; tạo thêm auth sandbox, chạy migration 002/003 additive và nạp catalog. Không reset schema hoặc sửa public data. Script tạo hai tài khoản, hai hồ sơ, mỗi hồ sơ hai lượt; seed thêm trường ghi chú và hai phiên bản dữ liệu giả lập lần đầu. Chạy lại giữ các lượt/giá trị đã có; password của hai tài khoản thử được đồng bộ với file riêng hiện hành. Không chạy seed trên một schema dùng dữ liệu thật.

Chạy nền Windows có thể dùng `Start-Process ... -WindowStyle Hidden` và chuyển stdout/stderr vào `local-data/`. Khi dừng, kiểm tra PID đang nghe cổng 8001 vì `.venv` launcher có thể khác PID Python thật. Không dừng tiến trình không xác minh. Sau khởi động lại, kiểm `/health` và đăng nhập/đọc hồ sơ; xem trước import cũ hết hiệu lực và cần tạo lại.

Nếu môi trường Codex thu hồi tiến trình con khi lượt bị ngắt, bản live hiện dùng `pythonw.exe` được tạo qua Windows WMI. `scripts/run_form_demo.py --config-file <file riêng trong local-data>` đọc object có `database_url`, `schema`, `port`; stdout/stderr ghi vào log cạnh config. Không lưu DSN hoặc mật khẩu trong command line được chia sẻ, không tạo automation hoặc service khởi động cùng Windows. Lệnh chạy trực tiếp phía trên vẫn là cách đơn giản để người dùng chủ động khởi động lại.

Các API lâm sàng cũ vẫn được giữ trong mã nguồn. Sandbox này phục vụ biểu mẫu/Excel; không thiết lập toàn bộ nghiệp vụ lâm sàng cũ trong schema thử và không phải môi trường triển khai viện.

## Demo M1

1. Đăng nhập cổng đúng vai trò. Tài khoản Bác sĩ tại cổng Admin hoặc ngược lại bị backend từ chối.
2. Chọn `SYN-FORM-001`, lượt `VISIT-001-1`: seed có cân nặng 0, khó thở khi nằm Không, chiều cao trống và ghi chú trường bổ sung. Các số là dữ liệu giả lập kiểm phần mềm, không phải đánh giá y khoa.
3. Nhập một số trường và Lưu. Trường không sửa không được gửi trong PATCH; ô được xóa chủ ý gửi null. Mở lại/reload vẫn đọc PostgreSQL. Trong lúc chờ lưu, ô nhập và điều hướng được khóa để tránh mất thay đổi mới.
4. Xem Lịch sử: nhãn/định nghĩa lúc lưu, phiên bản, người/thời điểm và nguồn được giữ. Hai tab cùng phiên bản: tab lưu sau nhận xung đột và giữ bản nháp để đối chiếu.
5. Admin → Quản lý trường → Thêm trường: mã ổn định, nhãn, nhóm, kiểu, đơn vị đã xác định nếu có, lựa chọn mã/nhãn, hướng dẫn, thứ tự; Xem trước rồi Lưu. Bác sĩ mở lại biểu mẫu sẽ thấy trường mà không build/DDL. Trường mới chưa nhập ở ca cũ là NULL.
6. Đổi nhãn/nhóm/hướng dẫn/thứ tự/trạng thái tạo phiên bản. Kiểu, đơn vị, mã và lựa chọn của trường đã có bị khóa khi chưa có chuyển đổi được đặc tả; tạo mã mới khi cần ý nghĩa khác. Ngừng dùng không xóa giá trị/lịch sử.

Quyền hồ sơ demo: owner hoặc `form_access` được cấp rõ ràng. Admin có thêm quyền định nghĩa trường, không mặc nhiên được mọi hồ sơ. Seed chỉ cấp hai tài khoản thử quyền với hai hồ sơ giả lập.

## Demo M2

1. Nhập Excel → Tải mẫu Excel giả lập. Mẫu có sheet `GIA_LAP`; đây không phải mẫu HIS đã xác nhận. Có thể dùng workbook fixture của `tests/fixtures/forms` nhưng định danh fixture khác seed; dùng chế độ đối chiếu một dòng khi cần.
2. Chọn file `.xlsx` → Đọc cấu trúc → chọn sheet và hàng tiêu đề rõ ràng → Xem cột và mẫu dòng.
3. Mẫu tải từ ứng dụng: chọn chế độ nhiều ca, cột A là mã hồ sơ, B là mã lượt. Ánh xạ C → Cân nặng và xác nhận đơn vị nguồn kg trùng đích; D → Khó thở khi nằm, chọn bảng mã true/false. Cột E là ghi chú mô tả mẫu, có thể bỏ qua rõ ràng.
4. File thiếu mã lượt: chọn chế độ một dòng, số hàng nguồn, hồ sơ/lượt đích và tích xác nhận đã đối chiếu. Lượt đích được nhận diện bằng UUID đã kiểm quyền, kể cả chưa có mã ngoài; không gán những dòng khác vào ca này.
5. Xem trước chưa ghi hồ sơ/lượt/history/import batch. Mỗi trường có vị trí sheet/ô, giá trị gốc, giá trị đích, giá trị nhập và quyết định. Nguồn trống bỏ qua; giống đích không thay đổi; khác đích mặc định giữ hiện có. Ghi đè phải chọn rõ từng trường xung đột.
6. Chọn các dòng hợp lệ → Xác nhận. Một giao dịch ghi toàn bộ tập được chọn hoặc rollback toàn bộ khi có lỗi. Kết quả báo số trường/lượt đã ghi, phần bỏ qua và dòng không chọn/lỗi. Mở biểu mẫu để bổ sung tay phần thiếu.
7. Nhập lại/đổi tên file không nhân bản hồ sơ/lượt/history khi nội dung và quyết định tương đương. Lịch sử nhập của tài khoản giữ mapping phiên bản 1.0, kết quả, vị trí nguồn ở lịch sử giá trị. Nếu mất phản hồi, thử lại cùng preview/quyết định; nếu backend đã khởi động lại, xem trước mới để nhận diện kết quả đã ghi.

## Giới hạn và phần chưa xác minh

`.xlsx` tối đa 4 MiB; ZIP giải nén 32 MiB/1.000 mục; sheet tối đa 500 cột, 1.000 dòng dữ liệu và 100 dòng tiêu đề; preview tối đa 100 bản ghi/500 mapping, kế hoạch 8 MiB, hết hạn 1.800 giây. Văn bản 5.000 ký tự. Không chạy công thức/macro, không tự chuyển đơn vị, bù số 0 đầu, đoán bảng mã/ngày hay ghép bằng tên gần giống. Mã dạng số bị giữ lỗi để đối chiếu thay vì đổi thành chuỗi rồi đoán.

Excel danh sách thuốc/kết quả/multiselect chưa có hợp đồng nguồn phù hợp nên bị chặn rõ ràng; bổ sung trên biểu mẫu có cấu trúc. Không nhập chuỗi JSON trong ô để lách giới hạn. Biểu mẫu lưu NULL khác danh sách rỗng; không suy liều hoặc thời điểm từ tên thuốc.

Catalog nguồn có 70/206 dòng được hỗ trợ; 136 dòng chưa đủ đặc tả/không là đầu vào nhập tay được hiển thị cùng giới hạn, không dựng đầu ra AI. Chi tiết ở `field-catalog-and-mapping.md`. Workbook được cấp riêng chưa xác nhận là xuất HIS và thiếu mã lượt; chưa tuyên bố tương thích viện. Chưa đánh giá tải, bảo mật triển khai hoặc kiểm định lâm sàng.

## Kiểm thử lại

```powershell
$env:PYTHONPATH = 'src'
$env:FORM_TEST_DSN = '<DSN có options=-csearch_path=d3_form_qa_20261023,public>'
$env:FORM_TEST_CREDENTIALS = 'D:\1.TNHH\project\suytim_clone_demo\local-data\form-demo-credentials.json'
& '.\.venv\Scripts\python.exe' -m pytest tests -q
& node --check web/forms.js
& '.\.venv\Scripts\python.exe' scripts/export_openapi.py
```

Hai bộ test mới từ chối DSN không chỉ tới schema `d3_form_`. Tạo schema QA/credentials riêng bằng seed trước; không dùng schema live cho các test sinh nhiều hồ sơ. Các ca DB lâm sàng cũ có gate môi trường riêng và được báo skip khi chưa cấu hình.
