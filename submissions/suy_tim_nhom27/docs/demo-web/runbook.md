# Chạy demo biểu mẫu và nhập Excel

Để đưa bản demo lên Internet, xem [cách deploy lên Railway](deploy-railway.md).

> Cập nhật 30/10 theo `22222.md`: xem `review-20261030-integration.md`, `review-20261030-data.md` và `review-20261030-ui.md`. Mẫu mới có cấu trúc BP/EF/kết quả/thuốc; lượt cũ giữ mẫu riêng. Catalog hiện có 222 định nghĩa (206 nguồn +16 bổ sung), không coi số trường là độ hoàn thiện chuyên môn.

> Bản cập nhật 26/10 theo yêu cầu v1.0: dùng hướng dẫn tại `revision-data-contract.md`, `revision-ui-spec.md` và `qa/revision-integration.md`. Admin quản lý hồ sơ dùng chung, chỉ đọc dữ liệu khám; bác sĩ nhập khám. Các lượt giữ mẫu riêng. Các bước minh họa M1/M2 bên dưới là lịch sử trước thay đổi này nếu có mâu thuẫn.

Phạm vi hiện hành: M1 nhập tay/trường động và M2 Excel. Kế thừa HTML/CSS/JavaScript, FastAPI, xác thực phiên và PostgreSQL của repo. Không có chức năng dán/tải file JSON, kết nối HIS trực tiếp hoặc AI hoạt động. Không sửa SRS/report/RTM cũ.

## Mở bản đang chạy

- Đăng nhập chung cho Admin và Bác sĩ: http://127.0.0.1:8001/login (hoặc trang chủ http://127.0.0.1:8001/).
- Nhập tài khoản và mật khẩu; máy chủ trả về vai trò đã xác thực để ứng dụng tự mở cổng tương ứng. Không cần chọn vai trò trước khi đăng nhập. Đăng xuất trở về `/login`.
- Các liên kết cũ `/admin/login` và `/bac-si/login` chuyển hướng về `/login`.
- Tài khoản thử nằm riêng trong `D:\1.TNHH\project\suytim_clone_demo\local-data\form-demo-live-credentials.json`. Không đưa nội dung file này vào Git, ảnh hoặc log công khai.
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

`seed_form_demo.py` chỉ chấp nhận schema tên bắt đầu `d3_form_`; tạo auth sandbox, chạy migration 002/003, nạp catalog rồi migration 004 để chuyển mã BN và ghim mẫu cũ. Không reset schema hoặc sửa public data. Dừng ứng dụng và lưu bản sao trước khi chuyển schema đang có dữ liệu; xem `revision-data-contract.md`. Seed tìm hồ sơ cũ qua mã nguồn/alias để giữ liên kết. Không chạy seed trên dữ liệu thật. File credential riêng là nguồn mật khẩu khi cần seed lại; không đưa lên Git.

Chạy nền Windows có thể dùng `Start-Process ... -WindowStyle Hidden` và chuyển stdout/stderr vào `local-data/`. Khi dừng, kiểm tra PID đang nghe cổng 8001 vì `.venv` launcher có thể khác PID Python thật. Không dừng tiến trình không xác minh. Sau khởi động lại, kiểm `/health` và đăng nhập/đọc hồ sơ; xem trước import cũ hết hiệu lực và cần tạo lại.

Nếu môi trường Codex thu hồi tiến trình con khi lượt bị ngắt, bản live hiện dùng `pythonw.exe` được tạo qua Windows WMI. `scripts/run_form_demo.py --config-file <file riêng trong local-data>` đọc object có `database_url`, `schema`, `port`; stdout/stderr ghi vào log cạnh config. Không lưu DSN hoặc mật khẩu trong command line được chia sẻ, không tạo automation hoặc service khởi động cùng Windows. Lệnh chạy trực tiếp phía trên vẫn là cách đơn giản để người dùng chủ động khởi động lại.

Các API lâm sàng cũ vẫn được giữ trong mã nguồn. Sandbox này phục vụ biểu mẫu/Excel; không thiết lập toàn bộ nghiệp vụ lâm sàng cũ trong schema thử và không phải môi trường triển khai viện.

## Kịch bản bảo vệ 7 phút

Đây là kịch bản thao tác và tiêu chí cần kiểm, chưa phải biên bản đã chạy đạt. Dùng môi trường giả lập dành riêng cho buổi trình bày; chuẩn bị hai phiên trình duyệt tách biệt cho Bác sĩ và Admin. Ghi lại URL, mã bản dựng, schema, thời điểm và mã lượt dùng trong buổi chạy; giữ tài khoản/mật khẩu ở file riêng. Seed chỉ tạo dữ liệu ban đầu, chạy lại không đưa những giá trị đã sửa về trạng thái gốc.

Trước buổi demo, kiểm `/health` và đăng nhập cả hai vai trò. Mở hai hồ sơ mẫu để đối chiếu mã nguồn `SYN-FORM-001` và `SYN-FORM-002`, rồi ghi lại mã BN dùng để tìm trong danh sách. Seed tạo bốn lượt: `VISIT-001-1`, `VISIT-001-2`, `VISIT-002-1`, `VISIT-002-2`. Mã BN phụ thuộc sequence. Tải `synthetic-form-template.xlsx` từ ứng dụng để lấy đúng mã nguồn của seed. Hai workbook trong `tests/fixtures/forms` dùng bộ cột riêng.

| Thời gian | Thao tác | Kết quả cần nhìn thấy |
|---|---|---|
| 0:00–0:40 | Nêu phạm vi dữ liệu giả lập; Bác sĩ mở `SYN-FORM-001` / `VISIT-001-1`. | Đúng hồ sơ, đúng lượt; phân biệt mã BN với mã nguồn Excel. |
| 0:40–2:00 | Đặt Cân nặng = `60`, Khó thở khi nằm = `Không`, Chiều cao để trống. Ghi chú thêm mã buổi demo. Lưu từng nhóm đã sửa rồi tải lại trang và mở đúng lượt. | Đọc lại `60`, `Không` và ghi chú. Chiều cao trống vẫn trống. Lịch sử có lần lưu và người thực hiện. Các giá trị dùng để kiểm phần mềm. |
| 2:00–3:40 | Bác sĩ nhập mẫu vừa tải, sheet `GIA_LAP`, header hàng 1, chế độ nhiều ca. A → mã hồ sơ, B → mã lượt, C → Cân nặng (`kg`, xác nhận đơn vị), D → Khó thở khi nằm (bảng mã `true/false`), bỏ qua E. Xem trước và chỉ chọn dòng 2. | Ô C2 là `61`, khác đích `60`; mặc định giữ `60`. D2 là `false`, trùng giá trị Không. Xem trước chưa lưu hồ sơ. Chọn rõ ghi đè C2 rồi xác nhận; mở lại lượt thấy `61`, lịch sử chỉ rõ nguồn Excel. Dòng 3 không chọn phải được báo trong kết quả. |
| 3:40–5:30 | Admin sửa nhãn trường `ghi_chu_demo_qa` thành nhãn có mã buổi demo; xem trước rồi lưu phiên bản mới. Bác sĩ mở lại `VISIT-001-1`, sau đó tạo lượt mới với mã nguồn chưa dùng trong buổi chạy. | Lượt cũ giữ nhãn cũ và giá trị đã lưu. Lượt mới dùng nhãn mới, chưa có giá trị ghi chú. Mã trường, kiểu và đơn vị không đổi theo sửa nhãn. |
| 5:30–6:30 | Đối chiếu bằng chứng kiểm quyền API trên schema QA riêng, cùng bản dựng. | Bác sĩ sửa định nghĩa trường bị 403; Admin ghi dữ liệu khám bị 403; chưa đăng nhập đọc hồ sơ bị 401. Ẩn nút trên giao diện chưa đủ chứng minh quyền máy chủ. |
| 6:30–7:00 | Nêu kết quả đạt/chưa đạt và giới hạn nguồn Excel. | Không suy ra tương thích HIS từ mẫu giả lập; không mô tả AI hoặc kết nối HIS như chức năng đang hoạt động. |

Nếu chạy lại, đặt cân nặng về `60` và lưu ở đầu kịch bản để luôn có xung đột với C2 = `61`. Ghi lại nhãn hiện tại trước khi Admin sửa, dùng nhãn và mã lượt mới cho từng buổi. Không xóa lịch sử hoặc reset schema để che lần chạy trước. Khi lỗi, giữ thông báo và mã lượt, dừng bước phụ thuộc; ảnh hay test cũ chỉ dùng minh họa và phải ghi rõ thời điểm.

### Checklist nghiệm thu trước buổi bảo vệ

- [ ] Bác sĩ lưu và tải lại đúng lượt: dữ liệu giữ nguyên; phân biệt `false`, `0`, `null`; lịch sử có người và nguồn.
- [ ] Preview Excel hiện rõ đích `60` / nguồn `61`, mặc định giữ đích; chỉ ghi đè khi chọn rõ và xác nhận. Tải lại thấy `61` cùng nguồn ô C2.
- [ ] Admin lưu phiên bản nhãn mới; lượt cũ giữ snapshot; lượt tạo sau thay đổi dùng nhãn mới, không tự sao chép giá trị khám cũ.
- [ ] Bằng chứng API có request hợp lệ và status 403 cho Doctor sửa field, 403 cho Admin ghi khám, 401 khi thiếu phiên. Kiểm ở QA, không chạy test ghi dữ liệu trên DB đang trình bày.
- [ ] Ghi URL/bản dựng/thời điểm, mã hồ sơ/lượt và kết quả thực tế. Mục chưa chạy hoặc bị skip vẫn để chưa đạt xác minh.

### Quyền truy cập khi trình bày

URL Internet không đồng nghĩa mọi người được phép ghi. Khi trình bày có kiểm soát, người trình bày giữ thông tin đăng nhập, dùng hai phiên riêng và chỉ dùng dữ liệu giả lập. Nếu phát tài khoản Doctor/Admin cho người xem, họ có thể ghi dữ liệu hoặc sửa mẫu theo quyền tài khoản; bản demo hiện có chưa được coi là chế độ công khai chỉ đọc. Cần môi trường tách biệt trước khi cho người ngoài thử ghi; tài liệu này không tự cấp phép triển khai hay phát tài khoản.

## Demo M1

1. Mở `/login`, nhập tài khoản và mật khẩu. Tài khoản Admin vào cổng Admin; tài khoản Bác sĩ vào cổng Bác sĩ theo vai trò do máy chủ xác nhận. Quyền API vẫn được kiểm tra tại máy chủ.
2. Tìm hồ sơ theo mã nguồn `SYN-FORM-001` (mã nội bộ hiển thị dạng `BN-xxxxx`), chọn lượt `VISIT-001-1`: seed có cân nặng 0, khó thở khi nằm Không, chiều cao trống và ghi chú trường bổ sung. Các số là dữ liệu giả lập kiểm phần mềm, không phải đánh giá y khoa.
3. Nhập một số trường và Lưu. Trường không sửa không được gửi trong PATCH; ô được xóa chủ ý gửi null. Mở lại/reload vẫn đọc PostgreSQL. Trong lúc chờ lưu, ô nhập và điều hướng được khóa để tránh mất thay đổi mới.
4. Xem Lịch sử: nhãn/định nghĩa lúc lưu, phiên bản, người/thời điểm và nguồn được giữ. Hai tab cùng phiên bản: tab lưu sau nhận xung đột và giữ bản nháp để đối chiếu.
5. Admin → Quản lý trường → Thêm trường: mã ổn định, nhãn, nhóm, kiểu, đơn vị đã xác định nếu có, lựa chọn mã/nhãn, hướng dẫn, thứ tự; Xem trước rồi Lưu. Bác sĩ tạo lượt mới sau khi Admin lưu sẽ thấy trường mà không build/DDL; giá trị ban đầu là NULL. Lượt đã tạo giữ mẫu được ghim, nên mở lại lượt cũ không làm xuất hiện trường mới.
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

Catalog nguồn hiện có 72/206 dòng hỗ trợ: đã tách ghi nhận Có/Không của đái tháo đường và bệnh thận mạn khỏi thành phần xét nghiệm chưa rõ; 134 dòng còn thiếu đặc tả/không là đầu vào nhập tay. Lượt cũ tiếp tục dùng snapshot đã ghim. Không dựng đầu ra AI. Workbook riêng thiếu mã lượt; chưa xác nhận tương thích HIS. Danh sách thuốc/kết quả Excel, BMI/NYHA và luồng AI tiếp tục theo giai đoạn trong `revision-scope.md`.

## Kiểm thử lại

### Nâng catalog cho schema giả lập đã có

Từ thư mục app, xem kế hoạch trước; chỉ apply sau khi không có conflict và đã chọn file backup mới:

```powershell
& '.\.venv\Scripts\python.exe' scripts/upgrade_form_catalog.py --config-file 'D:\1.TNHH\project\suytim_clone_demo\local-data\forms-live-runtime.json'
& '.\.venv\Scripts\python.exe' scripts/upgrade_form_catalog.py --config-file 'D:\1.TNHH\project\suytim_clone_demo\local-data\forms-live-runtime.json' --apply --backup-file 'D:\1.TNHH\project\suytim_clone_demo\local-data\catalog-backup-NEW.json'
```

Không dùng lại tên backup đã có. Nếu báo conflict, đối chiếu định nghĩa Admin đã sửa; script không tự ghi đè. Không dùng schema public hoặc dữ liệu thật. Các lượt đã ghim không đổi; tạo lượt mới để dùng mẫu mới. Seed trên schema đã có không tự nâng định nghĩa trùng mã. `build_form_catalog.py` tái dựng baseline v0.2 lịch sử và ghi file đầu ra, không dùng để thay catalog hiện hành.

### Chạy kiểm thử

```powershell
$env:PYTHONPATH = 'src'
$env:FORM_TEST_DSN = '<DSN có options=-csearch_path=d3_form_qa_20261023,public>'
$env:FORM_TEST_CREDENTIALS = 'D:\1.TNHH\project\suytim_clone_demo\local-data\form-demo-credentials.json'
& '.\.venv\Scripts\python.exe' -m pytest tests -q
& node --check web/forms.js
& '.\.venv\Scripts\python.exe' scripts/export_openapi.py
```

Hai bộ test mới từ chối DSN không chỉ tới schema `d3_form_`. Tạo schema QA/credentials riêng bằng seed trước; không dùng schema live cho các test sinh nhiều hồ sơ. Các ca DB lâm sàng cũ có gate môi trường riêng và được báo skip khi chưa cấu hình.
