# Hợp đồng giao diện — yêu cầu sửa đã duyệt v1.0

Ngày: 26/10/2026. Phạm vi: đăng nhập, hồ sơ dùng chung, lượt khám, biểu mẫu và nhập Excel. Đây là đặc tả bàn giao, **không phải kết quả kiểm thử**.

## Nguồn và thứ tự ưu tiên

Nguồn quyết định: `C:\Users\tnhh\Downloads\Yeu-cau-sua-demo`, “Yêu cầu sửa demo — đã duyệt”, v1.0 ngày 25/10/2026, đã đọc đầy đủ. Các mã C/A/K bên dưới tham chiếu chính tài liệu này. TL04/TL05/TL06 chỉ được dẫn theo mô tả của tài liệu duyệt; bản đặc tả này không xác nhận đã đối chiếu lại nội dung sáu nguồn hay file HIS.

Đã đối chiếu nhánh `codex/demo-web`, CSS hiện hữu `web/forms.css` và `docs/demo-web/qa/ui-design-contract.md`. Yêu cầu một cột C09 **thay thế** hướng dẫn hai cột desktop trong hợp đồng UI cũ. Giữ các thay đổi hợp lệ khác đang có; không cần đổi tên nhóm hoặc thiết kế lại thương hiệu. Không thay đổi production CSS/JS trong bàn giao này.

## Nền tảng và component

Giữ Segoe UI/Arial, màu chữ #172b37, nền #f4f7f9, mặt thẻ trắng, màu chính #145b68 và đường viền #d6e0e5 đang dùng. Các thông số dưới đây là lựa chọn thiết kế, không phải yêu cầu y khoa: body 15–16px, nhãn 15px/600, H1 25px, H2 19px, metadata 13px; khoảng trường 18px, khối 24px; control cao tối thiểu 44px. Không thêm hình trang trí, KPI hoặc chức năng theme vào đợt sửa này.

- `PatientIdentity`: BN + tên nổi bật; ngày tạo nhỏ hơn; hành chính có thể chia ô trên desktop. Nhãn rỗng hiển thị “Chưa có dữ liệu”, không dấu “Không” thay NULL.
- `ClinicalSummary`: chẩn đoán, thuốc và dị ứng/phản ứng đã ghi nhận; luôn có nguồn lượt và ngày. Dữ liệu lấy từ lượt khác nhau phải có nguồn riêng, không áp chung một ngày gây hiểu nhầm.
- `EncounterContext`: mã BN, tên, mã lượt, thời điểm khám, tuổi tại lượt khi đủ căn cứ; khoa/phòng, bác sĩ, tiếp nhận/kết thúc nếu có. Cùng component ở màn xem và màn nhập.
- `ClinicalField`: nhãn → control/giá trị → đơn vị/hướng dẫn → lỗi. Một cột tại mọi breakpoint. Scope riêng cho vùng nhập, tránh sửa mọi `.grid` khiến bảng đối chiếu nhập file mất cấu trúc.
- `RepeatRecord`: tiêu đề “Thuốc 1”/“Kết quả 1” và các trường thành một khối dọc; các khối xếp dọc; nút Thêm/Xóa chỉ khi có quyền. Không giữ bảng nhập ngang với nhiều input tối thiểu 110px.
- `GroupSaveState`: chữ “Chưa lưu”, “Đang lưu”, “Đã lưu” hoặc “Lưu không thành công”, không truyền trạng thái chỉ bằng màu. Chỉ cập nhật “Đã lưu” sau máy chủ xác nhận.
- `VersionPreview`: phiên bản hiện tại, thay đổi đề nghị, bản xem trước và nút “Lưu phiên bản mới”; tách khỏi biểu mẫu nhập giá trị bệnh nhân.

Ở màn hẹp, header tự tăng chiều cao, tên/vai trò còn đọc được; điều hướng nhóm xuống dòng; bảng Excel cuộn bên trong vùng bảng. Không tràn ngang toàn trang. Thanh lưu không che trường cuối; khung ngữ cảnh còn tiếp cận được khi cuộn. Focus rõ, nhãn liên kết với control, lỗi liên kết qua `aria-describedby`, trạng thái lưu dùng live region; dialog đặt/trả focus hợp lý. Mục tiêu WCAG AA cần kiểm tra thực tế, chưa được xác nhận bởi tài liệu này.

## Màn hình và hành vi

### 1. Đăng nhập (C01, C13)

Tên duy nhất: “Hệ thống quản lý bệnh nhân suy tim”. Một form tài khoản/mật khẩu và nút Đăng nhập; không trang chọn cổng, không chọn vai trò, không phụ đề Demo/Biểu mẫu. Máy chủ xác định vai trò; sau xác thực hiện tên và vai trò gọn trong header. Lỗi xác thực ở form, giữ thông tin đã nhập phù hợp và tránh gửi lặp trong lúc chờ.

### 2. Danh sách và tạo hồ sơ (C02, C03, C05, C10)

Bác sĩ có “Tạo hồ sơ”; Admin quản lý cùng hồ sơ nhưng không có nút tạo. Tạo hồ sơ gồm tên giả lập, ngày sinh, giới tính, BHYT; BN do hệ thống cấp. Cho lưu khi chỉ đủ mã duy nhất và tên hiển thị; không ép ICD, ngày sinh hoặc BHYT. BHYT là chuỗi giữ số 0 đầu. Sau lưu mở đúng hồ sơ; “Tạo lượt khám” là bước riêng. Admin có thể sửa hành chính khi cần và có lịch sử; không có nút lưu lâm sàng. Quyền ẩn trên UI phải được máy chủ thực thi.

### 3. Tổng quan hồ sơ (C06–C08)

```text
BN-xxxxx · Người bệnh giả lập xxxxx
Ngày tạo hồ sơ: …                         [Chỉnh biểu mẫu — Admin]
Thông tin hành chính: ngày sinh · tuổi (ngữ cảnh) · giới tính · BHYT
Mã bệnh chính/kèm theo: …                 Theo lượt … — ngày …

Thông tin bệnh đã ghi nhận                Theo lượt … — ngày …
Thuốc đã ghi nhận tại lượt …              Ngày …
Dị ứng/phản ứng: Chưa có dữ liệu / giá trị đã ghi nhận

Danh sách lượt khám                       [Tạo lượt — Bác sĩ]
LK-…                                     [Mở lượt]
dd/MM/yyyy HH:mm
```

Thứ tự trên là bắt buộc. Mã bệnh nằm vùng đầu theo C06 nhưng nguồn vẫn theo lượt, không là thuộc tính hành chính bất biến. Tổng quan lấy lượt gần nhất có thông tin phù hợp và ghi nguồn. Không gọi mọi thuốc cũ là “đang dùng hôm nay”. Danh sách giảm dần theo `occurred_at`; lượt thiếu ngày ghi “Chưa có thời điểm khám” và đặt sau lượt có ngày, không thay bằng `updated_at`. Hồ sơ chưa có lượt hiển thị trạng thái trống rõ, không dựng bệnh/thuốc giả.

### 4. Lượt khám và biểu mẫu (C08, C09, A01–A03, A07, A08)

```text
BN-… · tên · LK-… · ngày giờ khám · Mẫu v…
Bác sĩ khám / Khoa phòng / Tiếp nhận / Kết thúc (khi có)
[Nhóm hiện tại] [trạng thái lưu theo nhóm]

Nhãn trường
[Ô nhập toàn chiều rộng vùng form]
Đơn vị hoặc hướng dẫn

[Khối thuốc/kết quả 1]
[Khối thuốc/kết quả 2]
                          [Lưu thay đổi]
```

Giữ đúng tám nhóm: Thông tin nền; Triệu chứng và dấu hiệu; Lão khoa và hỗ trợ; Tiền sử và bệnh đồng mắc; Thuốc đang sử dụng; Cận lâm sàng và theo dõi; Chờ đặc tả module; Trường bổ sung. Lý do khám, khám mới/tái khám, bệnh sử/diễn biến ngắn nằm trong nhóm phù hợp, không đổi hệ nhóm.

Ngày giờ dùng date/datetime-local hoặc bộ chọn tương đương, hiển thị dễ đọc, không bắt gõ ISO/múi giờ. Phân biệt ngày khám, ngày đo/lấy mẫu và ngày nhập. Không điền giờ mở trang cho lượt cũ hoặc thiếu ngày. Bảo toàn giá trị cũ qua chu trình đọc/sửa; máy chủ xử lý quy ước múi giờ nhất quán.

Mở lượt cũ dùng header, tuổi theo ngày khám, chẩn đoán, thuốc, giá trị và định nghĩa mẫu của chính lượt đó. Hành chính có thể dùng nguồn chung nhưng phải giữ dấu vết giá trị lịch sử phù hợp. Tạo lượt mới không tự xác nhận lại sinh hiệu/thuốc cũ.

Lỗi định dạng/giá trị bất khả thi đặt ngay dưới ô và có tóm tắt tới trường lỗi; không gộp NULL, Không và số 0. Không đặt ngưỡng chuyên môn mới trong thiết kế. Điều kiện A01 phải được kiểm tra cả UI/API. Trong nhóm Chờ đặc tả module, phân biệt “Đầu vào”, “Giá trị tính”, “Đầu ra AI”, “Chưa triển khai”; không dựng ô nhập cho toàn bộ dòng nguồn hay kết quả AI giả.

Rời nhóm/lượt có sửa chưa lưu phải bảo toàn draft hoặc đưa cảnh báo rõ với lựa chọn tiếp tục chỉnh sửa/hủy thay đổi/lưu theo khả năng thực tế. Lỗi lưu không mất input và không cho đi tiếp như đã lưu. Lịch sử sửa là vùng riêng, dùng nhãn lựa chọn và đơn vị từ đúng phiên bản thay JSON/mã thô; không lẫn với danh sách lượt khám.

### 5. Quản lý trường và phiên bản (C03, C04, C12, A13)

Admin mở “Chỉnh biểu mẫu” từ hồ sơ hoặc điều hướng quản lý. Màn hình có chọn nhóm trong tám nhóm hiện hữu, kiểu dữ liệu bằng tên dễ hiểu, đơn vị và các lựa chọn theo kiểu. Kiểu không có đơn vị thì không ép nhập đơn vị. Trường lựa chọn có nhãn hiển thị; mã kỹ thuật là thông tin phụ khi thực sự cần.

Luồng: chọn/thêm trường → chỉnh → xem trước form theo một cột → “Lưu phiên bản mới” → xác nhận phiên bản đã lưu. Nêu rõ “Lượt mới dùng phiên bản mới; lượt đã tạo giữ phiên bản hiện tại”. Trường bổ sung không tự tham gia AI. Lượt cũ kể cả nháp chưa lưu lần đầu giữ nhãn/nhóm/kiểu/đơn vị/lựa chọn cũ. Không có thao tác nâng mẫu ngầm; nếu chưa làm nâng mẫu thì không hiển thị nút hoạt động giả. Trường có dữ liệu được ẩn/ngừng dùng theo phiên bản, không hứa xóa vật lý.

### 6. Nhập file (C11, A12)

Nhãn hành động “Nhập file”; hướng dẫn cạnh ô chọn ghi “Excel”. Các bước: chọn file → đọc sheet/cột/số dòng và cấu hình ánh xạ theo nguồn → xem trước → xác nhận phần hợp lệ → báo cáo dòng → mở đúng lượt để bổ sung. Preview cần cột dòng/sheet, mã BN và mã lượt đích, trường, giá trị trước/sau, nguồn/ngày, trạng thái/lỗi. Lỗi phải chỉ dòng/cột và nguyên nhân: thiếu mã, không tồn tại, mã lượt thuộc người khác, sai định dạng.

Không đoán đích từ tên hoặc hồ sơ đang mở; không tự tạo ca. NULL là bỏ qua cập nhật, không xóa giá trị tay. Có phản hồi file lặp và thống kê thành công/lỗi. Cho lưu/tái sử dụng mapping theo nguồn; các thông báo chỉ khẳng định cấu trúc đã thật sự kiểm tra. Chưa đọc file bệnh viện thì không hiển thị “Tương thích HIS”. Excel preview là bảng dữ liệu, ngoại lệ hợp lý với yêu cầu nhập form một cột.

## Phạm vi giai đoạn

Làm hiện tại C01–C13, A01–A03, A07, A08, A12–A14 theo thứ tự tài liệu duyệt. A04–A06 chỉ đưa component có cấu trúc nguồn đã rõ; vị trí hiển thị không chứng minh đã có quy tắc hay dữ liệu. A09–A11 và AI/MedSafety không thuộc bàn giao triển khai đợt này. Bộ ca trình diễn A14 phải tách ca hợp lý với ca kiểm thử lỗi, ghi nhận là dữ liệu giả lập.

## Checklist nghiệm thu có khóa nguồn

Mọi dòng dưới đây là **chưa kiểm chứng trong bàn giao thiết kế**. Tester ghi bằng chứng live/API riêng; không đánh dấu pass từ việc đọc CSS.

| Mã | Điểm quan sát | Bằng chứng tối thiểu cần lấy |
|---|---|---|
| K01 | Một login, đúng role, bác sĩ không vào cấu hình | Hai phiên đăng nhập + request đường dẫn/API trực tiếp |
| K02 | Tạo BN duy nhất, tên giả lập, hành chính NULL được, không ép ICD | Tạo → mở lại + payload lưu |
| K03 | Admin thấy đúng hồ sơ/lượt bác sĩ tạo | Đối chiếu cùng ID giữa hai role |
| K04 | Chuyển mã không nhân bản hoặc mất liên kết | Đếm/đối chiếu dữ liệu trước–sau, mã nguồn và lịch sử |
| K05 | Hành chính → bệnh/thuốc có nguồn ngày → lượt đúng thứ tự | Hồ sơ nhiều lượt và một lượt thiếu occurred_at |
| K06 | Lượt cũ không lẫn dữ liệu mới | Hai lượt có chẩn đoán/thuốc/mẫu khác nhau |
| K07 | Lượt mới giữ hành chính nhưng không tự xác nhận lâm sàng cũ | Tạo lượt, kiểm tuổi theo ngày và trường lâm sàng |
| K08 | Tám nhóm nguyên tên; một cột; repeat dọc; context dễ thấy | Desktop + 390px/320px, bàn phím, chuỗi dài |
| K09 | v2 cho lượt mới, v1 cho lượt cũ/nháp; role đúng | Sửa mẫu giữa hai thời điểm tạo lượt; mở bằng hai role |
| K10 | Đổi nhãn/nhóm/ẩn vẫn giữ nghĩa lịch sử | Trước–sau + đọc lịch sử với nhãn/đơn vị cũ |
| K11 | Excel có đích và trước–sau; đọc lại đúng ca | File nguồn đã xác định + import preview/commit/readback |
| K12 | Sai cặp/thiếu mã/NULL/0 đầu/file lặp đúng | Bộ file biên + kiểm không ghi chéo hoặc sinh trùng |
| K13 | Tuổi 150/cân nặng -1 bị chặn; NULL/Không/0 hợp lệ riêng | UI và yêu cầu trực tiếp, không chỉ browser validation |
| K14 | Chưa lưu được báo/cảnh báo, lưu và tải lại giữ đúng | Đổi nhóm, đổi lượt, rời trang, lỗi lưu và reload |
| K15 | Tên sản phẩm sạch; trạng thái chưa có ở đúng chức năng | Login, shell, nhóm Chờ đặc tả module |

Không có browser test hoặc screenshot mới được thực hiện trong nhiệm vụ thiết kế này. Cần Tester xác nhận riêng trạng thái lưu/rời trang, quyền máy chủ, phiên bản và dữ liệu nhập; đây là các điểm không thể chứng minh bằng mockup.
