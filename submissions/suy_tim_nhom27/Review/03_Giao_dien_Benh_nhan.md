# HF Care — Đề xuất thiết kế giao diện BỆNH NHÂN (Patient Portal)

> **Nhóm 27 · Bản đặc tả UI/UX đề xuất · 09/10/2026 · Trạng thái: Chờ nhóm trưởng duyệt chi tiết**  
> **Đọc cùng:** `01_Dang_nhap_Review.md` và `02_Giao_dien_Bac_si.md`.  
> **Phạm vi:** **bệnh nhân suy tim cao tuổi**, website responsive (không tự nhận có ứng dụng di động).  
> **Căn cứ:** SRS `FR-P01–FR-P04`, `docs/ui-ux-plan.md`, `web/app.js` và `src/gateway/patient_portal.py` trên GitHub Nhóm 27.

## 0. Định hướng và chức năng đang có

**Mục tiêu:** bệnh nhân truy cập thông tin của chính mình và thực hiện ít thao tác nhưng rõ kết quả. Giữ cùng **HF Care Design System** như cổng bác sĩ, nhưng tăng cỡ chữ, khoảng bấm, ưu tiên bố cục **mobile-first**, giọng văn gần gũi, không dùng thuật ngữ API.

**Cấu trúc điều hướng đề xuất:**

```text
HF Care / Bệnh nhân
├── Trang chủ
├── Lịch khám
├── Theo dõi sức khỏe
├── Thuốc của tôi
│   ├── Đơn thuốc
│   └── Lịch dùng thuốc
└── Tài khoản (chỉ hiện dữ liệu/cài đặt mà API thực sự hỗ trợ)
```

**Luồng hiện có trong backend:**

- `GET/POST /api/v1/patient/appointments`: xem và gửi **yêu cầu** lịch khám; `POST /appointments/{id}/cancel` hủy lịch có trạng thái cho phép; chưa tự xác nhận lịch.
- `GET/POST /api/v1/patient/measurements`: xem và nhập chỉ số/triệu chứng tại nhà do bệnh nhân tự ghi.
- `GET /api/v1/patient/prescriptions`: **chỉ đọc** đơn đã xác nhận; bệnh nhân không sửa liều, giờ uống hoặc thuốc.
- `GET /api/v1/patient/reminders`, `PATCH /reminders/{id}`: xem các nhắc và phản hồi **Đã uống/Bỏ qua**.
- `GET /api/v1/patient/doctors`: danh sách bác sĩ đủ điều kiện chọn cho yêu cầu lịch.

**Chưa có:** thông báo push/SMS/email tự động; API bệnh nhân chỉnh sửa mọi thông tin cá nhân; hiển thị đầy đủ lịch sử thăm khám từ phía bệnh nhân; luồng nhân viên xác nhận lịch hoàn chỉnh; bệnh nhân tự kê/sửa đơn thuốc. Tránh nút/link giả dẫn vào những chức năng chưa có.

### Phác thảo tham khảo cho khu vực bệnh nhân

![Gợi ý bố cục màn bệnh nhân](assets/patient_concept.png)

*Ảnh ý tưởng bố cục sinh từ brief UI. Các tên, chỉ số và biểu đồ nếu có chỉ là ví dụ; **không được dùng như dữ liệu sức khỏe hoặc cảnh báo lâm sàng**.*

## 1. P-01 — Nguyên tắc UI dễ sử dụng cho bệnh nhân cao tuổi

| Thành phần | Đề xuất |
|---|---|
| Bộ màu & tên sản phẩm | Dùng chung `#1746B5`, `#F5F8FC`, `#182538`, `#0F8B8D`; tên HF Care (tạm) |
| Chữ | Nội dung quan trọng 17–18px (hoặc người dùng phóng to); heading 24–28px; tương phản cao |
| Nút chính | Cao ≥48px, khoảng chạm dễ thao tác; tránh chỉ dùng icon không nhãn |
| Ngôn ngữ | “Lịch khám”, “Số đo của tôi”, “Đơn thuốc”, “Đã uống”; không dùng “API”, “synthetic”, “revision”, “scope” |
| Responsive | Desktop bố cục gọn; trên điện thoại ưu tiên một cột, nút đầy đủ chiều rộng, không phải cuộn ngang |
| Biểu mẫu | Nhãn ở trên ô nhập; đơn vị hiển thị rõ; lỗi ngay tại trường; có xác nhận đã lưu |
| Trạng thái | Chưa có dữ liệu ≠ chỉ số bình thường; không dùng màu đỏ/xanh để tự suy luận nguy cơ |
| An toàn | Một chú thích ngắn nhưng nhìn thấy được: “Hệ thống thử nghiệm với dữ liệu giả lập, không dùng cho quyết định y khoa” |

**ƯU TIÊN:** P1. **TIÊU CHÍ:** thao tác bằng bàn phím và touch, chữ dễ đọc ở 360px/768px/1366px, không có thành phần nhỏ khó bấm.

## 2. P-02 — Trang chủ bệnh nhân (Dashboard cá nhân)

**HIỆN TẠI TRONG CODE:** màn tổng quan hiện là khối “Cổng bệnh nhân”, mô tả API và nút nhanh đến lịch hẹn/số đo/đơn thuốc/nhắc nhở. Chưa thấy ảnh chụp màn bệnh nhân từ nhóm trưởng; đây là đánh giá từ `web/app.js`, **chưa kiểm thử giao diện thực tế**.

**ĐỀ XUẤT:** trang chủ tập trung vào 4 câu hỏi: lịch khám của tôi ở đâu, ghi số đo ở đâu, xem thuốc thế nào, có nhắc nào cần phản hồi không.

```text
HF Care                                       [Tài khoản] [Đăng xuất]
Xin chào! Cùng theo dõi lịch khám và sức khỏe của bạn.
┌────────────────────────┐ ┌─────────────────────────┐
│ Lịch khám               │ │ Theo dõi sức khỏe        │
│ [Xem / Đặt lịch]        │ │ [Nhập số đo]             │
└────────────────────────┘ └─────────────────────────┘
┌────────────────────────┐ ┌─────────────────────────┐
│ Đơn thuốc               │ │ Lịch dùng thuốc          │
│ [Xem đơn đã xác nhận]   │ │ [Xem / Phản hồi lời nhắc]│
└────────────────────────┘ └─────────────────────────┘
[Đầu việc của tôi — chỉ hiển thị dữ liệu lịch/nhắc thật từ API]
```

**Chi tiết:**

- 4 card có biểu tượng + tiêu đề + mô tả 1 dòng + CTA. Trên điện thoại xếp 1 cột.
- Có thể hiển thị “Lịch hẹn sắp tới” khi từ `appointments` có bản ghi tương lai `requested/confirmed`. Phải phân biệt rõ **chờ xác nhận** với **đã xác nhận**.
- Có thể hiển thị “Lời nhắc chưa phản hồi” khi từ `reminders` có bản ghi pending. **Không ghi “đã gửi thông báo”** khi chỉ là bản ghi DB.
- Chỉ hiện “Chỉ số gần đây” khi có measurement từ API, kèm nhãn **“Bạn tự ghi”** và thời điểm. Không biến phép đo này thành nhận định khỏe/xấu.
- Tài khoản mới chưa có bản ghi: hiển thị hướng dẫn bắt đầu bằng “Đặt lịch” và “Nhập số đo” thay vì card số 0 trống hoặc bảng kỹ thuật.

**LÝ DO:** bệnh nhân hiểu ngay các việc có thể làm. **ƯU TIÊN:** P1.

**TIÊU CHÍ:** không có số/chỉ số giả; CTA đến đúng chức năng; trạng thái rỗng cho người dùng mới rõ ràng.

## 3. P-03 — Lịch khám / đặt và hủy lịch

**API HIỆN CÓ:** `GET/POST /patient/appointments`, `GET /patient/doctors`, `POST /patient/appointments/{id}/cancel`.

**ĐỀ XUẤT — MÀN LỊCH KHÁM:**

```text
LỊCH KHÁM CỦA TÔI                               [+ Yêu cầu lịch khám]
┌────────────────────────────────────────────────────────────┐
│ Ngày, giờ         Bác sĩ      Lý do       Trạng thái       │
│ [từ API]          [API]       [API]       Chờ xác nhận     │
│                               [Xem chi tiết] [Hủy lịch]  │
└────────────────────────────────────────────────────────────┘
```

**ĐỀ XUẤT — FORM TẠO:** Bước 1 chọn bác sĩ từ danh sách backend có thật; bước 2 chọn ngày/giờ; bước 3 nhập lý do ngắn; xác nhận `Gửi yêu cầu lịch khám`. Không ghi “Đặt lịch thành công/Đã xác nhận” ngay khi API chỉ tạo `requested`.

- Hiển thị nhãn trạng thái tiếng Việt: `requested` → “Chờ xác nhận”, `confirmed` → “Đã xác nhận”, `completed` → “Đã hoàn tất”, `cancelled` → “Đã hủy”.
- Nút `Hủy lịch` chỉ hiện với lịch `requested` hoặc `confirmed` nếu API cho phép; hỏi xác nhận trước khi hủy, không xóa hẳn lịch sử.
- Hiển thị giờ đúng múi giờ và định dạng Việt Nam; khi không có bác sĩ đủ điều kiện thì vô hiệu hóa CTA và hướng dẫn nguyên nhân.
- Không hiển thị “Lịch trống” với ngụ ý không có lịch cho bác sĩ; đây chỉ là lịch của tài khoản bệnh nhân.
- `[CẦN BACKEND]` lựa chọn khung giờ còn trống trực quan và luồng bác sĩ/nhân viên xác nhận lịch để tích hợp toàn quy trình.

**LÝ DO:** tách yêu cầu khỏi xác nhận. **ƯU TIÊN:** P1.

**TIÊU CHÍ:** tạo yêu cầu → thấy `Chờ xác nhận`; hủy lịch trong trạng thái cho phép; lịch đã hoàn tất không có nút hủy.

## 4. P-04 — Theo dõi sức khỏe / ghi chỉ số tại nhà

**API HIỆN CÓ:** `GET/POST /patient/measurements` với `observed_at`, cặp huyết áp tâm thu/tâm trương, nhịp tim, cân nặng, SpO₂, nhiệt độ, triệu chứng.

**ĐỀ XUẤT:** hai tabs `Ghi số đo` và `Lịch sử đã ghi`.

```text
THEO DÕI SỨC KHỎE
[Ghi số đo]     [Lịch sử đã ghi]

Thời điểm đo: [ngày/giờ]
Huyết áp:   [tâm thu] / [tâm trương] mmHg
Nhịp tim:   [____] lần/phút       Cân nặng: [____] kg
SpO₂:       [____] %             Nhiệt độ: [____] °C
Triệu chứng / ghi chú: [________________________]
                                       [Lưu số đo]

Dữ liệu bạn tự ghi — chưa được nhân viên y tế xác nhận.
```

**Quy tắc giao diện:**

- Không bắt người dùng nhập tất cả; ít nhất một chỉ số hoặc ghi chú. Nếu nhập huyết áp, yêu cầu **đủ cả tâm thu và tâm trương**; tránh tâm thu thấp hơn tâm trương.
- Gắn đơn vị trực tiếp trên nhãn, không bắt người dùng suy luận.
- Cho nhập ngày/giờ đo. Không âm thầm dùng thời gian tạo bản ghi thay cho thời gian đã đo nếu người dùng cần sửa.
- Lịch sử: dòng theo thời gian, số đo đã ghi, nguồn **“Bệnh nhân tự nhập”**, không ghi “Bác sĩ đã xem”.
- Nếu có nhiều số đo qua thời gian, **có thể** thêm biểu đồ tuyến tính huyết áp/cân nặng theo đúng nguồn và đơn vị, nhưng không gắn “tốt/xấu”, vùng nguy cơ hoặc màu cảnh báo do tự suy diễn.
- `[CẦN BACKEND]` để chia sẻ số đo như “đã được bác sĩ xác nhận” thì phải có quy trình kiểm tra và API nhân viên y tế riêng. Hiện số đo bệnh nhân không tự thành ghi nhận lâm sàng.

**LÝ DO:** đơn giản hóa việc theo dõi tại nhà nhưng tránh nhầm dữ liệu tự nhập với dữ liệu y tế xác nhận. **ƯU TIÊN:** P1.

**TIÊU CHÍ:** lưu được ít nhất một số đo hợp lệ; huyết áp thiếu một số được thông báo ngay; lịch sử hiển thị đúng; không suy luận lâm sàng từ dữ liệu.

## 5. P-05 — Thuốc của tôi: Đơn thuốc & lịch dùng thuốc

**API HIỆN CÓ:** `GET /patient/prescriptions` (chỉ đọc); `GET /patient/reminders`, `PATCH /patient/reminders/{id}` (chỉ trạng thái `taken`/`skipped` khi đang `pending`).

**ĐỀ XUẤT:** gộp 2 mục sidebar thành `Thuốc của tôi`, bên trong có **hai tabs**:

### 5.1 Đơn thuốc

- Group thuốc theo từng đơn/đợt dùng nếu API trả `prescription_id`; hiển thị tên thuốc/sản phẩm, liều, đường dùng, số lần/ngày, giờ dùng, ngày bắt đầu–kết thúc, hướng dẫn nếu được xác nhận.
- Chỉ hiển thị đơn **được xác nhận** theo quyền bệnh nhân; nội dung có thể rỗng khi chưa có đơn.
- Không đưa nút sửa thuốc, tự thay liều, tạo đơn, đổi giờ uống.
- Không biến **bản ghi thuốc trong encounter của bác sĩ** thành **đơn thuốc đã xác nhận**: hai loại dữ liệu có ràng buộc khác nhau.

### 5.2 Lịch dùng thuốc / lời nhắc

```text
THUỐC CỦA TÔI
[Đơn thuốc]           [Lịch dùng thuốc]

Ngày [từ API] — Lịch dùng thuốc
┌──────────────────────────────────────────────────┐
│ [Giờ theo timezone]  [Tên thuốc, liều từ API]    │
│ Hướng dẫn: ...                                    │
│ Trạng thái: Chưa phản hồi                        │
│                        [Đã uống]   [Bỏ qua]      │
└──────────────────────────────────────────────────┘
```

- Xếp nhóm theo ngày/giờ; hiển thị **thời điểm đến hạn** từ API, múi giờ tương ứng, thuốc, liều, hướng dẫn.
- Chỉ bản ghi `pending` có nút `Đã uống` và `Bỏ qua`; sau khi phản hồi phải hiển thị “Đã uống” hoặc “Đã bỏ qua” và thời điểm phản hồi.
- Xác nhận trước thao tác “Bỏ qua” nếu nhóm thấy cần; tránh bấm nhầm, nhưng không ngăn người dùng phản hồi một trạng thái đã xảy ra.
- **Không viết “Đã nhắc bạn”**, “Thông báo sắp gửi”, “Sẽ nhắc qua điện thoại” vì hiện tại chưa có worker/email/SMS/push.
- Không suy luận “tuân thủ điều trị tốt” hay “đủ liều” từ một vài trạng thái lời nhắc.

**LÝ DO:** một nơi theo dõi thuốc dễ dùng, vẫn giữ rõ sự khác biệt giữa đơn và nhắc lịch. **ƯU TIÊN:** P1.

**TIÊU CHÍ:** bệnh nhân không sửa được nội dung đơn; chỉ phản hồi lời nhắc pending; trạng thái cập nhật đúng và không hiện tác vụ sau khi đã phản hồi.

## 6. P-06 — Hồ sơ/tài khoản & đăng ký

**HIỆN TRẠNG CODE:** đăng ký người dùng mới chỉ tạo tài khoản `patient` và một hồ sơ giả lập mới; hiện chưa có một màn `Tài khoản` đầy đủ với các thao tác cập nhật thông tin liên hệ.

**ĐỀ XUẤT NGẮN HẠN:**

- Ở header hiển thị tên đăng nhập đang có và nhãn “Bệnh nhân”; nút đăng xuất rõ ràng.
- Nếu có màn `Thông tin của tôi`, chỉ đọc các thông tin tài khoản/hồ sơ **được API hiện tại trả**, không tự dựng tên, địa chỉ hoặc lịch sử bệnh nhân đầy đủ.
- Đăng ký mới chỉ dành cho bệnh nhân; không cấp role nhân viên từ form công khai (đã thống nhất trong tài liệu đăng nhập).
- Nêu trạng thái sau đăng ký: “Tài khoản đã tạo. Vui lòng đăng nhập.”; hồ sơ mới có thể chưa có lịch, số đo hoặc đơn thuốc.
- **Điểm cần chốt**: cơ chế liên kết người bệnh đăng ký với hồ sơ đã tồn tại, tránh tạo trùng, xử lý người quản lý/bác sĩ phụ trách. Code hiện đang tạo **hồ sơ synthetic mới** gắn bác sĩ mặc định, không phải nhận diện người bệnh thật.

**LÝ DO:** bảo đảm nhất quán danh tính giữa cổng bác sĩ và bệnh nhân. **ƯU TIÊN:** P1 cho quyền/liên kết, P2 cho UI tài khoản.

## 7. P-07 — Trạng thái, phản hồi và quyền truy cập

- `401`: phiên hết hạn → “Phiên đăng nhập đã hết, vui lòng đăng nhập lại”.
- `403`: không đủ quyền → “Bạn không có quyền xem nội dung này”. Không tiết lộ dữ liệu hồ sơ khác.
- `404`: không tồn tại/không còn → “Không tìm thấy thông tin yêu cầu”.
- `409`: lịch hoặc nhắc đã thay đổi → “Thông tin đã được cập nhật. Vui lòng tải lại”. Giữ nội dung người dùng đã nhập nếu có thể.
- `422`: lỗi form → báo ngay cạnh trường (ví dụ thiếu một trị số huyết áp).
- Loading: “Đang tải…” với skeleton/trạng thái trung tính; không đặt dữ liệu giả vào lúc chờ.
- Empty: mô tả bước tiếp theo: chưa có lịch → `Đặt lịch`, chưa có số đo → `Ghi số đo`, chưa có đơn → thông báo trung tính.
- Tuyệt đối không gọi dữ liệu tự nhập là do bác sĩ xác nhận nếu chưa có quy trình xác minh.

**TIÊU CHÍ:** trạng thái nhất quán trên mobile/desktop; người bệnh biết nên làm gì tiếp theo và không nhầm dữ liệu dùng thử là hướng dẫn điều trị.

## 8. Cách cổng bệnh nhân kết nối cổng bác sĩ

| Tác vụ / dữ liệu | Bệnh nhân | Bác sĩ | Hiện tại / cần làm |
|---|---|---|---|
| Hồ sơ bệnh nhân | Chỉ hồ sơ được liên kết với tài khoản | Xem hồ sơ trong phạm vi được phân quyền | **Cần xác minh quy trình liên kết tài khoản & ca** |
| Lịch khám | Gửi yêu cầu, xem, hủy khi hợp lệ | Trong hướng thiết kế mong muốn: xem/xác nhận/lập lần khám | **[CẦN BACKEND]** luồng xác nhận của nhân viên chưa hoàn chỉnh |
| Số đo tại nhà | Ghi và xem lịch sử tự nhập | Trong mục tiêu: có thể xem theo quy trình xác minh phù hợp | **[CẦN BACKEND]** nếu đưa số đo qua quy trình duyệt của bác sĩ |
| Thuốc | Xem đơn đã xác nhận; phản hồi lời nhắc | Ghi dữ liệu thuốc theo lần khám | **[CẦN BACKEND]** luồng tạo/xác nhận đơn đầy đủ không tương đương ghi bản ghi thuốc |
| Nhắc thuốc | Xem lịch ghi trong DB, đánh dấu đã uống/bỏ qua | Không cần chỉnh trên cổng bác sĩ nếu chưa có nghiệp vụ | **Chưa có** cơ chế gửi thông báo thực tế |

**Không hiển thị nút liên thông ảo:** chỉ hiển thị CTA khi endpoint và quy tắc nghiệp vụ đã có; các tính năng dự kiến nên xuất hiện trong backlog, không giả làm chức năng hoàn thành.

## 9. Mapping UI ↔ API/FR (để giao dev)

| Trang / thao tác | FR | API hiện có | Trạng thái |
|---|---|---|---|
| Quyền xem đúng hồ sơ | FR-P01 | phiên / RLS / `patient_account` | Nền tảng đã có, **cần test phân quyền** |
| Yêu cầu/hủy lịch khám | FR-P02 | `/patient/doctors`, `/patient/appointments`, `/cancel` | API có; staff confirm cần phát triển thêm |
| Ghi số đo + lịch sử | FR-P03 | `GET/POST /patient/measurements` | API có; dữ liệu tự nhập, chưa bác sĩ duyệt |
| Xem đơn đã xác nhận | FR-P04 | `GET /patient/prescriptions` | API đọc có; ghi đơn xác nhận cần workflow khác |
| Xem/phản hồi nhắc | FR-P04 | `GET /patient/reminders`, `PATCH /reminders/{id}` | Có trả trạng thái, **không** có push notification |
| Thông tin cá nhân, thay đổi mật khẩu | Chưa chốt | Chưa thấy API UI tương ứng | **Không hứa hẹn** trong bản này |

## 10. Thứ tự giao task đề xuất

| Đợt | Task | Ưu tiên | Tính chất |
|---|---|---|---|
| 1 | Cùng Design System với login/bác sĩ; bỏ từ API, synthetic trên giao diện chính | P1 | Frontend |
| 1 | Trang chủ 4 nhóm chức năng + trạng thái trống phù hợp | P1 | Frontend |
| 1 | Trang Lịch khám: yêu cầu/đã xác nhận/hủy, hướng dẫn hợp lệ | P1 | Frontend |
| 1 | Trang Theo dõi sức khỏe: form đơn giản và lịch sử | P1 | Frontend |
| 1 | `Thuốc của tôi` gồm Đơn thuốc + Lịch dùng thuốc | P1 | Frontend |
| 1 | Mobile, cỡ chữ/target, lỗi form, thông báo trạng thái | P1 | Frontend + QA |
| 2 | Trang Tài khoản chỉ đọc, nếu có nguồn dữ liệu | P2 | Frontend + kiểm tra API |
| 3 | Xác nhận lịch cho staff, liên kết hồ sơ, xử lý đơn và hệ thống thông báo | Cần chốt phạm vi | Backend + nghiệp vụ |

## 11. Checklist nghiệm thu bệnh nhân

- [ ] Cổng bệnh nhân sử dụng cùng tên, màu sắc, font với đăng nhập và bác sĩ.
- [ ] Bố cục 1 cột hợp lý trên điện thoại; nút lớn, chữ dễ đọc.
- [ ] Trang chủ chỉ dùng dữ liệu thật từ API, không có số đo hoặc cảnh báo tự tạo.
- [ ] Yêu cầu lịch chỉ hiển thị “Chờ xác nhận” khi API trả `requested`.
- [ ] Hủy lịch chỉ ở trạng thái cho phép; có xác nhận thao tác.
- [ ] Nhập được số đo hợp lệ, ghi rõ nguồn “Bệnh nhân tự nhập”.
- [ ] Đơn thuốc chỉ xem; không có nút tự sửa đơn/liều/giờ uống.
- [ ] Lịch dùng thuốc phản hồi được “Đã uống/Bỏ qua” và cập nhật trạng thái đúng.
- [ ] Không hiển thị giả việc gửi thông báo (push/SMS/email).
- [ ] Bệnh nhân A không thể đọc dữ liệu bệnh nhân B, kể cả sửa URL/ID API.
- [ ] Empty/loading/error được thể hiện bằng câu tiếng Việt dễ hiểu.
- [ ] Thông báo giới hạn dữ liệu giả lập & không dùng cho quyết định y khoa vẫn nhìn thấy.

## 12. Vấn đề cần nhóm trưởng/dev thống nhất

1. Cách hiển thị bệnh nhân: chỉ mã/tuổi/giới tính hiện có hay thêm tên/ngày sinh giả lập từ schema mới?
2. Có thể hiển thị lịch khám sắp tới trên trang chủ trước khi làm luồng nhân viên xác nhận hay chỉ xem lịch “chờ xác nhận”?
3. Muốn gộp `Đơn thuốc` và `Nhắc nhở` vào một mục `Thuốc của tôi` như đề xuất hay để hai menu riêng?
4. Có ưu tiên biểu đồ số đo khi đủ dữ liệu hay để bảng lịch sử đơn giản ở phiên bản đầu?
5. Lộ trình thực hiện hệ thống thông báo nhắc thuốc thật (email/web push/app) sau đồ án?

## 13. Nguồn mã để dev đối chiếu

- [Repository](https://github.com/tnhh175/suytim_clone_demo/)
- [SRS](https://github.com/tnhh175/suytim_clone_demo/blob/main/submissions/suy_tim_nhom27/docs/SRS_v1.0.md)
- [Kế hoạch UI](https://github.com/tnhh175/suytim_clone_demo/blob/main/submissions/suy_tim_nhom27/docs/ui-ux-plan.md)
- [Frontend patient](https://github.com/tnhh175/suytim_clone_demo/blob/main/submissions/suy_tim_nhom27/web/app.js)
- [Backend patient](https://github.com/tnhh175/suytim_clone_demo/blob/main/submissions/suy_tim_nhom27/src/gateway/patient_portal.py)
