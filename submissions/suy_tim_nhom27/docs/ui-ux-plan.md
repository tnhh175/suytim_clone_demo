# Hợp đồng UI/UX — demo quản lý bệnh viện

## 1. Phạm vi và nguồn sự thật

Tài liệu này là hợp đồng thiết kế cho demo web quản lý bệnh nhân suy tim cao tuổi trong submissions/suy_tim_nhom27. Phạm vi là giao diện và hành vi demo; đây không phải giao diện đủ điều kiện sử dụng lâm sàng.

Mọi nội dung, số liệu, mốc thời gian và chỉ số trên giao diện phải lấy từ API hoặc dữ liệu synthetic trong database/seed. Không chèn tên, hồ sơ, kết quả, KPI, ngưỡng hay diễn biến tự tạo để làm màn hình trông đầy đủ. Chỉ dẫn người dùng, tiêu đề và nhãn trạng thái được viết cho giao diện, không được giả làm dữ liệu hồ sơ.

Banner luôn hiện ở đầu ứng dụng, kể cả khi cuộn:

**Demo — Synthetic Data — Not for Clinical Use**

Gateway dùng PostgreSQL cho session và các luồng clinical/portal được triển khai. Tài khoản từ seed xác thực qua `/api/v1/auth/token`; browser chỉ gọi API và không đọc DB trực tiếp. Các trang vẫn phải phản ánh đúng phần SRS chưa có endpoint.

Mỗi lần đánh giá và từng module luôn hiển thị **mock_not_evaluated**. Không hiển thị chẩn đoán, mức độ nguy cơ, đề xuất xét nghiệm, thuốc/liều, cảnh báo tương tác, điểm tin cậy hoặc biểu đồ kết quả lâm sàng. Không suy diễn “bình thường”, “không có” hay “đã an toàn” từ trường rỗng hoặc dữ liệu thiếu. Trạng thái unknown, not_measured và present phải được giữ riêng biệt.

Số đếm trên dashboard chỉ được tính từ dữ liệu synthetic API đã tải và phải mang nhãn phạm vi, ví dụ “trong dữ liệu demo đang tải”. Không tạo tỷ lệ, xu hướng, hiệu quả điều trị hay KPI lâm sàng.

## 2. Hướng thiết kế

**Anchor duy nhất: Swiss.** Hồ sơ và diễn biến cần được quét nhanh, so sánh theo thời gian và truy ngược nguồn; nền trắng, kiểu chữ sans và lưới đường kẻ mảnh giữ cấu trúc rõ mà không tạo cảm giác một màn hình “cảnh báo” lâm sàng. Dùng Yves Klein Blue làm màu nhấn duy nhất cho điều hướng hiện tại, liên kết và hành động chính.

**Differentiator:** timeline lâm sàng bám vào từng encounter. Mỗi encounter là một khối có mốc thời gian và trạng thái riêng; các sự kiện bên trong ghi rõ thời điểm, nguồn, người ghi và loại dữ liệu. Khi đổi encounter, đường timeline và dữ liệu đi cùng nhau để tránh trộn các lần khám.

### Design tokens

| Token | Giá trị | Dùng cho |
| --- | --- | --- |
| Canvas | #FFFFFF | Nền chính |
| Surface phụ | #F7F7F8 | Thanh điều hướng, vùng lọc và nền nhóm bảng |
| Text chính | #17191D | Tiêu đề, nhãn và nội dung |
| Text phụ | #5E6673 | Nguồn, thời điểm, mô tả thứ cấp |
| Hairline | #D7DBE2 | Lưới và đường phân cách |
| Viền điều khiển | #707782 | Viền input/button có tương phản rõ |
| Accent | #002FA7 | Liên kết, trạng thái điều hướng, nút chính, focus |
| Semantic error | #B42318 | Lỗi nhập/API; chỉ dùng với nhãn văn bản |
| Semantic warning | #8A5A00 | Cảnh báo thao tác hoặc dữ liệu thiếu; không dùng để biểu diễn kết quả y khoa |
| Semantic success | #1A7F37 | Xác nhận thao tác lưu; không biểu diễn trạng thái sức khỏe |
| Font | Helvetica Neue, Helvetica, Arial, sans-serif | Một họ sans cho toàn bộ giao diện |
| Cỡ chữ | 12 / 14 / 16 / 20 / 28 / 36 px | Metadata / nội dung / tiêu đề / tiêu đề trang |
| Nhịp khoảng cách | Bội số 4 px; vùng trang 24–32 px | Grid và khoảng thở |
| Viền góc | 2 px cho trường, 4 px cho nút/khối | Hình học vuông, không tạo thẻ nổi |
| Đổ bóng | Không dùng | Phân lớp bằng nền và hairline |

Dùng số tabular cho ngày giờ, mã hồ sơ và số đo. Không thêm texture, gradient, serif, trang trí trung tâm hoặc màu nhấn thứ hai. Icon chỉ dùng inline SVG hoặc thư viện SVG có sẵn trong dự án; không dùng emoji hay ký tự Unicode thay icon. Nút vẫn có nhãn chữ dễ hiểu.

## 3. Bố cục và mẫu tương tác

- Thanh banner demo nằm trên cùng, luôn nhìn thấy. Bên dưới là header có tiêu đề trang và phạm vi hồ sơ/encounter đang mở.
- Desktop từ 1.366 px: thanh điều hướng trái có nhãn, vùng nội dung theo grid 12 cột, lưới hairline và tiêu đề căn trái. Khu vực hồ sơ luôn cho biết mã synthetic và encounter hiện tại.
- Ở viewport 768 px trở xuống: điều hướng thu gọn thành panel có thể mở; nội dung ưu tiên một cột và không che thao tác chính. Trong khoảng 769–1.365 px, giữ điều hướng có nhãn nếu đủ chỗ và giảm số cột. Màn hình hẹp chuyển bảng thành danh sách có nhãn trường hoặc vùng cuộn ngang có thông báo; không cắt mất nội dung.
- Timeline đặt ngày/giờ ở cột trái, sự kiện ở cột phải. Nhóm encounter có ranh giới rõ, hiển thị loại encounter, thời gian và trạng thái do API cung cấp. Mỗi sự kiện có loại dữ liệu, nguồn, người ghi và thời điểm khi nguồn trả các trường này. Không tự gắn mốc thời gian hiện tại cho dữ liệu thiếu thời gian.
- Bản ghi observation giữ đơn vị và trạng thái từ nguồn. Dữ liệu tự nhập ở nhà phải tách khỏi dữ liệu nhân viên đã ghi; không biểu diễn là đã được nhân viên xác nhận.
- Không dùng chart/đèn đỏ xanh để rút ra kết luận. Nếu endpoint chưa có dữ liệu thì để trạng thái rỗng có giải thích, không dựng điểm mẫu.
- Các form đặt nhãn ngoài trường, đơn vị kèm tên trường, lỗi ngay cạnh trường và giữ nội dung đã nhập khi lỗi mạng hoặc xung đột revision. Không có thao tác xóa nếu API không cung cấp.

## 4. Điều hướng và ranh giới theo role

Role trong schema/SRS là doctor, nurse, pharmacist, admin, patient. Điều hướng dưới đây mô tả đích UX cho cả năm role; menu ẩn không thay thế kiểm soát quyền ở server.

| Role | Điều hướng và chức năng | Ranh giới |
| --- | --- | --- |
| Doctor | Tổng quan; Hồ sơ; Encounter và timeline; Dữ liệu lâm sàng; Đánh giá demo; Lịch sử | Chỉ xem/sửa ca trong phạm vi API cho phép. Quyết định chuyên môn vẫn thuộc bác sĩ; không tự biến output stub thành y lệnh. |
| Nurse | Ca được phân công; Encounter; Theo dõi chỉ số; Ghi nhận chăm sóc | Chỉ scope nursing được cấp. Không xem kết quả đánh giá ngoài phạm vi điều dưỡng hoặc sửa đơn thuốc. |
| Pharmacist | Ca được phân công; Thuốc; Đánh giá MedSafety demo; Nhận xét dược sĩ | Chỉ dữ liệu cần rà soát và scope medsafety; không ghi quyết định của bác sĩ. |
| Admin | Tài khoản và role; Danh mục; Quy tắc; Nhật ký | Quyền quản trị kỹ thuật không cấp quyền đọc hồ sơ lâm sàng hoặc quyết định y khoa. Quyền duyệt chuyên môn rule.approve là quyền riêng. |
| Patient | Lịch khám; Chỉ số tại nhà; Đơn đã xác nhận; Nhắc thuốc | Chỉ một hồ sơ gắn với tài khoản. Có thể yêu cầu/hủy lịch chưa hoàn thành, nhập chỉ số của mình và phản hồi nhắc uống. Không sửa đơn, liều, đường dùng hoặc giờ uống. |

Demo có đăng nhập và điều hướng cho đủ năm role doctor, nurse, pharmacist, admin, patient. Ẩn menu không thay thế kiểm tra quyền server; cổng patient giới hạn theo case từ session/RLS, staff giới hạn theo role và scope.

## 5. Màn hình và candidate API

Các đường dẫn dưới đây là API hiện được giao diện gọi; những mục được ghi “chưa có” vẫn là candidate từ SRS/schema. Không gọi database trực tiếp từ browser.

### Doctor

| Màn hình / thao tác | Candidate API và hành vi |
| --- | --- |
| Đăng nhập | POST /api/v1/auth/token. Mật khẩu PBKDF2 theo tài khoản, session lưu hash trong DB; token opaque có hạn một giờ. |
| Tổng quan và danh sách hồ sơ | GET /api/v1/cases. Tạo hồ sơ synthetic bằng POST /api/v1/cases; chi tiết GET /api/v1/cases/{case_id}; cập nhật PUT /api/v1/cases/{case_id} với expected_revision. Các route hồ sơ chỉ dành cho doctor. |
| Encounter | GET danh sách `/cases/{case_id}/encounters`, POST tạo encounter có revision, GET `/encounters/{encounter_id}`. Tất cả ID/scope do API kiểm tra. |
| Observation và thuốc | GET/POST observations, PUT observation theo revision; GET/POST medications. POST thuốc chỉ ghi bản ghi synthetic, không tạo prescription/schedule. |
| Timeline và lịch sử | GET /api/v1/cases/{case_id}/history hiện chỉ trả lịch sử evaluations và decision, không phải timeline đầy đủ của hồ sơ. Cần API liệt kê encounter và sự kiện lâm sàng trước khi tuyên bố timeline hoàn chỉnh. |
| Đánh giá demo | POST /api/v1/evaluations nhận encounter, revision và danh sách module; GET /api/v1/evaluations/{evaluation_id} đọc lại. Tất cả module luôn là mock_not_evaluated, mode stub, không có kết quả lâm sàng. |
| Thao tác decision demo | POST /api/v1/evaluations/{evaluation_id}/decisions có trong OpenAPI. Vì evaluation không có gợi ý thật, UI không được gọi thao tác này là “chấp nhận phác đồ” hay “ra y lệnh”; nếu dùng để trình diễn route, phải ghi rõ là thao tác stub. |
| Xuất lịch sử | GET /api/v1/cases/{case_id}/export; chỉ xuất nội dung endpoint trả và gắn nhãn synthetic/demo. |

### Nurse

| Màn hình / thao tác | Candidate API và dữ liệu nguồn |
| --- | --- |
| Ca được phân công | GET `/api/v1/cases`; API chỉ trả ca theo nursing scope của điều dưỡng. |
| Theo dõi encounter | GET danh sách/detail encounter trong nursing scope; GET observations và notes theo encounter. |
| Nhập sinh hiệu, cân nặng, triệu chứng và ghi chú chăm sóc | POST observation theo nursing allowlist và POST note với `kind=nursing`; yêu cầu revision, ghi actor từ session. |

### Pharmacist

| Màn hình / thao tác | Candidate API và dữ liệu nguồn |
| --- | --- |
| Thuốc theo encounter | GET /api/v1/encounters/{encounter_id}/medications; Gateway cho pharmacist đọc thuốc trong giới hạn hiện tại. Không hiển thị cả hồ sơ nếu endpoint không trả hoặc quyền không cho phép. |
| Đánh giá MedSafety demo | POST /api/v1/evaluations chỉ với module medsafety; GET /api/v1/evaluations/{evaluation_id} chỉ trả module được phép. Trạng thái vẫn là mock_not_evaluated, không dựng cảnh báo tương tác hay liều. |
| Nhận xét dược sĩ | Schema có bảng pharmacist_review; OpenAPI chưa có route tạo/đọc nhận xét. Chỉ bật tương tác lưu khi API tương ứng được bổ sung. |

### Admin

| Màn hình / thao tác | Candidate API và dữ liệu nguồn |
| --- | --- |
| Quy tắc | GET/POST /api/v1/rule-versions; test bằng POST /api/v1/rule-versions/{rule_id}/test; kích hoạt bằng POST /api/v1/rule-versions/{rule_id}/activate. Kết quả test schema_passed chỉ là kiểm tra schema, clinical_validation là not_performed. |
| Duyệt chuyên môn | Không đồng nhất admin với người duyệt. Schema dùng quyền riêng rule.approve; API Gateway hiện chặn activate bằng 409 khi không có phê duyệt đã xác minh. UI phải trình bày đúng trạng thái chặn, không báo thành công. |
| Nhật ký | GET /api/v1/audit-events. Chỉ cho phép admin. |
| Tài khoản, role và danh mục | SRS FR-02..04; schema có app_user, user_role, permission, department, các danh mục. OpenAPI chưa có CRUD tương ứng; màn hình này chưa được giả lập thao tác lưu. |
| Hồ sơ lâm sàng | Không có menu, route, tìm kiếm hoặc truy vấn ca cho admin. Không cấp quyền lâm sàng ngầm qua bảng điều khiển quản trị. |

### Patient

| Màn hình / thao tác | Candidate API và dữ liệu nguồn |
| --- | --- |
| Lịch khám | GET/POST `/api/v1/patient/appointments`; POST `/appointments/{id}/cancel`. Patient chỉ yêu cầu lịch và hủy trạng thái chưa hoàn thành; staff confirm/complete chưa có trong demo. |
| Chỉ số tại nhà | GET/POST `/api/v1/patient/measurements`; server gắn case và recorded_by từ session. Nội dung lưu riêng, giữ nhãn bệnh nhân tự nhập, không tạo tư vấn. |
| Đơn đã xác nhận | GET `/api/v1/patient/prescriptions`; dữ liệu chỉ đọc từ view/RLS. Demo không tạo/sửa prescription hoặc schedule. |
| Nhắc thuốc | GET `/api/v1/patient/reminders`; PATCH `/reminders/{id}` chỉ cho phép phản hồi pending thành taken/skipped. Không có worker hoặc notification thật. |
| Phạm vi | `patient_account` gắn một tài khoản với một case; session server và `hf_patient_portal`/RLS giới hạn mọi thao tác vào hồ sơ đó. |

## 6. Trạng thái, lỗi và an toàn thao tác

- Loading: skeleton trung tính chỉ cho biết đang tải; không lấp bằng số đo minh họa.
- Empty: nêu rõ chưa có dữ liệu trong nguồn hiện tại; không diễn giải là “không có bệnh”, “không có thuốc” hay kết quả âm tính.
- Lưu thành công: xác nhận đúng bản ghi/loại thao tác và trạng thái trả về. Chỉ dùng semantic success cho kết quả thao tác, không cho sức khỏe.
- Đánh giá: nhãn rõ “Chưa được đánh giá lâm sàng — mock_not_evaluated”. Giữ mode=stub; danh sách gợi ý/cảnh báo rỗng vẫn phải nói là không có đánh giá, không phải không có nguy cơ.
- 401: yêu cầu đăng nhập lại. 403: báo không đủ quyền mà không tiết lộ dữ liệu. 404: bản ghi không còn hoặc không tồn tại. 409: nêu xung đột revision/trạng thái, giữ dữ liệu form và cho tải lại. 422: nêu trường cần sửa, không echo nội dung nhạy cảm. 503: báo cấu hình demo chưa sẵn sàng.
- Không tự retry thao tác ghi khiến có thể tạo bản ghi trùng; chỉ retry sau phản hồi lỗi có thể xác định hoặc xác nhận trạng thái với API.
- Mọi thao tác trong phạm vi dữ liệu cần ghi đúng actor và thời điểm API trả về. UI không tự tạo audit event hoặc giả lập lưu bền vững.

## 7. Accessibility và responsive

- Dùng ngữ nghĩa heading, landmark, bảng có header, nhãn trường liên kết với input và thông báo lỗi được đọc bởi screen reader.
- Toàn bộ luồng dùng được bằng bàn phím; thứ tự focus theo thứ tự thị giác; focus nhìn thấy rõ bằng viền 2 px accent. Không dùng màu đơn độc để phân biệt trạng thái.
- Mục tiêu tương phản WCAG 2.2 AA: ít nhất 4.5:1 cho chữ thường và 3:1 cho chữ lớn, viền điều khiển và focus. Giữ nút chính có nhãn hành động cụ thể.
- Tôn trọng prefers-reduced-motion; không dùng animation để báo lỗi hoặc trạng thái đánh giá.
- Đối chiếu hai chiều rộng tối thiểu SRS nêu là 1.366 px và 768 px; tại chiều rộng nhỏ hơn, không che nút lưu/điều hướng và không yêu cầu hover để khám phá thông tin.
- Icon SVG có aria-hidden nếu trang trí; icon-only control phải có accessible name. Không dùng ký tự Unicode/emoji làm biểu tượng hoặc trạng thái.

## 8. Nguồn đối chiếu

- [SRS_v1.0.md](SRS_v1.0.md): FR-01..34, FR-P01..04, role, NFR-01..13 và giới hạn dữ liệu synthetic.
- [schema.sql](../database/schema.sql), [portal_permissions.sql](../database/portal_permissions.sql), [seed.sql](../database/seed.sql): năm role, scope truy cập, portal, dữ liệu fixtures và trạng thái module.
- [data_dictionary.md](../database/data_dictionary.md): định nghĩa bảng/cột và quyền trong schema.
- [openapi.yaml](../api/openapi.yaml) và [api/README.md](../api/README.md): endpoint Gateway hiện có, role hiện được hỗ trợ và trạng thái stub.

Tài liệu này không sửa OpenAPI hay hành vi API. Những luồng ghi nhận là “chưa có API” cần được triển khai và kiểm tra phân quyền phía server trước khi được bật trong giao diện.
