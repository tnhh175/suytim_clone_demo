# HF Care — Đề xuất thiết kế giao diện BÁC SĨ (Doctor Portal)

> **Nhóm 27 · Bản đặc tả UI/UX đề xuất · 09/10/2026 · Trạng thái: Chờ nhóm trưởng duyệt chi tiết**  
> **Đọc cùng:** `01_Dang_nhap_Review.md` (đăng nhập đã thảo luận trước).  
> **Phạm vi:** tài khoản **bác sĩ**; các vai trò điều dưỡng/dược sĩ/quản trị chưa được đặc tả trong tài liệu này.  
> **Nguồn đối chiếu:** ảnh của nhóm trưởng, `docs/SRS_v1.0.md`, `docs/ui-ux-plan.md`, `web/app.js`, `src/gateway/clinical.py`, `src/gateway/patient_portal.py` và `README.md` trên GitHub Nhóm 27.

## 0. Kết luận thiết kế và ranh giới triển khai

**Hướng đã được nhóm trưởng đồng ý:** **Patient-centric** — *chọn một bệnh nhân, sau đó làm việc trên toàn bộ hồ sơ, các lần khám, dữ liệu ghi nhận và lịch sử của bệnh nhân ấy*.

**Điều hướng đề xuất:** 

```text
HF Care / Bác sĩ
├── Tổng quan
└── Bệnh nhân
    ├── Danh sách & tìm kiếm
    └── Chi tiết một bệnh nhân  ← giữ ngữ cảnh hồ sơ đang chọn
        ├── Tổng quan hồ sơ
        ├── Các lần khám
        │   └── Chi tiết lần khám / ghi dữ liệu / thuốc / ghi chú
        ├── Hỗ trợ đánh giá (gắn với lần khám)
        └── Lịch sử đánh giá (theo bệnh nhân & lần khám)
```

**Không chốt:** tên thương hiệu chính thức (`HF Care` là tên tạm), thông tin nhân thân phải thu thập, các chức năng bệnh viện chưa có API. Các phần có ghi **[CẦN BACKEND]** không được coi là đã triển khai.

**An toàn:** toàn bộ bản hiện tại chỉ dùng dữ liệu mô phỏng. Không đưa kết luận lâm sàng, cảnh báo nguy cơ, chỉ định xét nghiệm hoặc gợi ý thuốc giả vào màn hình để lấp chỗ trống. Trạng thái module `mock_not_evaluated` phải được diễn đạt bằng lời dễ hiểu là **“Chưa có đánh giá lâm sàng”**; cảnh báo giới hạn thử nghiệm phải luôn tìm thấy trong UI, không nhất thiết đặt banner quá lớn.

### Hình tổng thể đề xuất (để hình dung bố cục, KHÔNG phải màn hình đã làm)

![Gợi ý các bố cục giao diện bác sĩ](assets/doctor_concept.png)

*Hình chỉ minh họa thẩm mỹ và cấu trúc. Tên bác sĩ, số ca, lịch khám, chỉ số nguy cơ, cảnh báo hoặc kết quả trong hình nếu có là ví dụ thiết kế, **không được copy thành dữ liệu thật/đánh giá lâm sàng**.*

## 1. Design System dùng chung (đồng bộ màn đăng nhập & bệnh nhân)

| Thành phần | Quy tắc đề xuất |
|---|---|
| Tên sản phẩm | `HF Care` (tạm), dùng nhất quán trên trang đăng nhập/header/sidebar |
| Primary | `#1746B5` — hành động chính, focus, link |
| Background | `#F5F8FC` — nền ứng dụng |
| Surface | `#FFFFFF` — vùng dữ liệu và form |
| Text | `#182538`, chữ phụ `#5E6673` |
| Accent | `#0F8B8D` — dùng tiết chế, không mang ý nghĩa “sức khỏe an toàn” |
| Border | `#D7DBE2` hoặc màu trung tính tương đương |
| Font | Inter / Be Vietnam Pro có hỗ trợ tiếng Việt |
| Cỡ chữ | Nội dung 16px; heading 24–30px; metadata 13–14px nhưng đủ tương phản |
| Khoảng cách | Bội số 8px; panel 16–24px; input/button cao ≥44px |
| Hành động | Nút chính màu xanh; nút phụ viền; tác vụ hủy/xóa cần xác nhận |
| Trạng thái | Loading / empty / error / saved / permission denied; không dùng màu đơn độc để truyền đạt trạng thái |
| Responsive | Desktop sidebar rộng, 1366×768 và 1920×1080; mobile/768px giảm cột, menu thu gọn |

**Tài khoản hiển thị:** vai trò “Bác sĩ”; chỉ hiển thị **họ tên** nếu có trường dữ liệu đáng tin cậy từ API, nếu không dùng tên đăng nhập — không tự dựng tên bác sĩ. **Không hiển thị** `Gateway`, `stub`, `synthetic API`, `revision` hoặc UUID dài trong màn hình nghiệp vụ thường. Giữ một chú thích an toàn ngắn: *“Hệ thống thử nghiệm với dữ liệu giả lập, không dùng cho quyết định y khoa.”*

## 2. D-01 / UI-07 — Layout dùng chung và điều hướng

**HIỆN TẠI:** Trang chung hiển thị banner demo lớn, logo `HF`, thanh bên nhãn “Quản lý hồ sơ”, dưới cùng `doctor_demo`; năm mục menu `Tổng quan / Hồ sơ / Lần khám / Đánh giá demo / Lịch sử đánh giá`. Bác sĩ chưa được đặt vào ngữ cảnh một bệnh nhân cụ thể khi di chuyển trang.

**ĐỀ XUẤT:**

- **Header:** logo + tên sản phẩm; người đăng nhập + “Bác sĩ”; nút đăng xuất; trạng thái dịch vụ không xuất hiện thường trực (nếu có, đặt ở khu vực quản trị/kỹ thuật).
- **Sidebar cấp ứng dụng:** chỉ cần `Tổng quan` và `Bệnh nhân`; khi chọn hồ sơ, đưa nội dung chuyên môn vào **tabs trong hồ sơ**, không đẩy người dùng ra năm khu vực độc lập.
- **Thanh ngữ cảnh cố định trong hồ sơ:** `Mã hồ sơ • Tuổi • Giới tính • Lần khám đang xem`, nút “Đổi bệnh nhân”. Không có lần khám thì hiển thị “Chưa chọn lần khám”.
- **Breadcrumb:** `Bệnh nhân > SYN-… > Lần khám > …` để tránh lạc đường.
- **Không nhân bản điều hướng:** cùng hành động “Mở lần khám” ở đúng ngữ cảnh; tất cả màn chi tiết có đường về hồ sơ.

**LÝ DO:** giúp bác sĩ hiểu đang xem ai và hành động nào ảnh hưởng đến hồ sơ nào.

**ƯU TIÊN:** P1. **TIÊU CHÍ NGHIỆM THU:** chọn bệnh nhân một lần, chuyển tabs không mất ngữ cảnh; đổi bệnh nhân thì làm sạch ngữ cảnh lần khám/form chưa lưu; không rò thông tin bệnh nhân trước vào hồ sơ mới.

## 3. D-02 / UI-08 — Tổng quan của bác sĩ

**HIỆN TẠI:** chỉ có “2 hồ sơ trong API hiện tại”, khung “Thông tin kỹ thuật Gateway”, “Giới hạn demo”.

![Tổng quan bác sĩ hiện tại](assets/doctor_01_overview.png)

**ĐỀ XUẤT:** màn “Tổng quan bệnh nhân” có 3 phần: 

1. **Đầu trang:** “Tổng quan bệnh nhân” + mô tả ngắn “Truy cập các hồ sơ trong phạm vi phụ trách”.
2. **Thông tin có căn cứ:** thẻ `Hồ sơ có quyền truy cập` đếm từ `GET /api/v1/cases`; danh sách tối đa 5 hồ sơ có thể mở nhanh. Có thể bổ sung `Lần khám gần đây` **chỉ khi** đã tổng hợp được từ các encounter có quyền truy cập.
3. **Thao tác nhanh:** `Xem danh sách bệnh nhân`, `Tạo hồ sơ` (bác sĩ được phép); `Tạo lần khám` chỉ khả dụng khi đã chọn hồ sơ.

**Không thêm** “bệnh nhân nguy cơ cao”, “cần chú ý”, “lịch khám hôm nay”, “tỷ lệ điều trị hiệu quả” nếu không có nguồn/logic API hợp lệ. Mẫu dashboard nên hấp dẫn nhờ thứ bậc thông tin, không nhờ chỉ số giả.

**WIREFRAME CHỨC NĂNG:**

```text
TỔNG QUAN BỆNH NHÂN                        [Xem danh sách bệnh nhân]
┌────────────────────┐ ┌────────────────────────────────────────┐
│ Hồ sơ được truy cập│ │ Thao tác nhanh                          │
│ 2 (từ API)         │ │ [Tìm bệnh nhân]  [Tạo hồ sơ]            │
└────────────────────┘ └────────────────────────────────────────┘
┌───────────────────────────────────────────────────────────────┐
│ Hồ sơ bệnh nhân                                               │
│ [SYN-DEMO-001]  75 tuổi  Nữ                        [Chi tiết] │
│ [SYN-DEMO-002]  80 tuổi  Nam                       [Chi tiết] │
└───────────────────────────────────────────────────────────────┘
```

**LÝ DO:** thay thông tin kỹ thuật bằng hướng thao tác hữu ích cho bác sĩ. **ƯU TIÊN:** P1.

**TIÊU CHÍ:** chỉ hiển thị số lượng và thông tin lấy từ API, nút đi đúng trang, hiển thị loading/error/empty có giải thích, không tự giả định đã có lịch khám hay cảnh báo.

## 4. D-03 / UI-09 — Danh sách bệnh nhân và chi tiết hồ sơ

**HIỆN TẠI:** danh sách hai hồ sơ; tìm theo mã/UUID; mã UUID dài, tuổi và giới tính nằm rải trên hàng; nút `Mở lần khám`, `Chi tiết`; một mục `Tạo hồ sơ synthetic` đóng/mở.

![Danh sách hồ sơ bác sĩ hiện tại](assets/doctor_02_cases.png)

**ĐỀ XUẤT — danh sách:**

| Cột | Hành vi |
|---|---|
| Mã hồ sơ | Nhấn để xem chi tiết; hiển thị mã ngắn (không phải UUID dài) |
| Thông tin sẵn có | Tuổi, giới tính; **không dựng họ tên** vì API hiện chưa có trường này |
| Lần khám gần nhất | Chỉ hiển thị khi dữ liệu encounter tải được; rỗng dùng `Chưa có` |
| Thao tác | `Xem hồ sơ` là hành động chính; `Tạo lần khám` chỉ khi ngữ cảnh hợp lệ |
| Tìm kiếm | Ưu tiên tìm theo mã hồ sơ; lọc tuổi/giới tính tùy chọn nếu có nhu cầu |

**ĐỀ XUẤT — chi tiết một hồ sơ:**

```text
[Bệnh nhân] > SYN-DEMO-001
SYN-DEMO-001       75 tuổi · Nữ       [Tạo lần khám]
────────────────────────────────────────────────────────
[Tổng quan hồ sơ] [Các lần khám] [Ghi nhận] [Hỗ trợ đánh giá] [Lịch sử]
────────────────────────────────────────────────────────
Hồ sơ cơ bản                  Các lần khám gần đây
Mã · tuổi · giới tính        Danh sách theo thời điểm từ API
```

- `Tổng quan hồ sơ`: hiển thị các trường hiện có (`synthetic_code`, `age`, `sex`); cập nhật hồ sơ với revision do backend quản lý.
- `Các lần khám`: chỉ hiển thị lần khám của hồ sơ đã chọn, sắp xếp thời gian gần nhất.
- `Ghi nhận`: phải chọn lần khám, mới cho nhập ghi nhận/sinh hiệu/ghi chú.
- `Hỗ trợ đánh giá` và `Lịch sử`: cùng ngữ cảnh hồ sơ/lần khám.
- **Chưa cần** Họ tên/ngày sinh/số điện thoại/CMND. Nếu nhóm muốn có, phải bổ sung cấu trúc dữ liệu, luồng danh tính và đồng ý thay đổi SRS; không dựng giao diện điền thông tin thật.

**LÝ DO:** giảm nhầm lẫn giữa hồ sơ và lần khám, tránh lộ dữ liệu kỹ thuật không cần thiết. **ƯU TIÊN:** P1.

**TIÊU CHÍ:** chọn `Chi tiết` mở đúng hồ sơ; từ đây vào được các tab mà không cần nhập lại mã; tìm kiếm/cập nhật đúng phạm vi quyền; ID kỹ thuật chỉ ở chi tiết dành cho dev khi cần.

## 5. D-04 / UI-10 — Lần khám và dữ liệu ghi nhận

**HIỆN TẠI:** khi chưa chọn hồ sơ, màn hình hiển thị “Chọn hồ sơ trong scope trước” và đồng thời “API trả về danh sách encounter rỗng”, tạo cảm giác hồ sơ không có lần khám. Có khu vực “Mở bằng ID”.

![Màn hình lần khám hiện tại](assets/doctor_03_encounters.png)

**ĐỀ XUẤT:** thay màn tách rời thành tab **Các lần khám** bên trong hồ sơ; phân biệt ba trạng thái:

| Trạng thái | Nội dung chính | Hành động |
|---|---|---|
| Chưa chọn hồ sơ | “Chọn một bệnh nhân để xem các lần khám” | `Chọn bệnh nhân` |
| Đã chọn, chưa có lần khám | “Chưa có lần khám nào được ghi nhận” | `Tạo lần khám đầu tiên` |
| Đã có lần khám | Danh sách theo ngày, thời điểm, dữ liệu sẵn có | `Xem chi tiết` / `Tạo lần khám` |

**Mẫu màn chi tiết lần khám**:

```text
Hồ sơ SYN-DEMO-001 > Các lần khám > [ngày từ API]
[Thông tin lần khám] [Sinh hiệu & triệu chứng] [Ghi chú khám] [Thuốc] [Diễn biến]
────────────────────────────────────────────────────────────────────────────────
Thông tin lần khám: thời điểm, mã hồ sơ, bác sĩ thực hiện nếu API có
Dữ liệu ghi nhận: nhịp tim, huyết áp, cân nặng, SpO₂... (chỉ trường đã lưu)
[Tạo ghi nhận]   [Lưu ghi chú]   [Xem thuốc]   [Hỗ trợ đánh giá]
```

- `Tạo lần khám` dùng ngày/giờ theo `POST /api/v1/cases/{case_id}/encounters`, hiển thị xác nhận đã lưu; lỗi revision thì thông báo xung đột và tải dữ liệu mới; không âm thầm ghi đè.
- Biểu mẫu ghi nhận cần nhãn tiếng Việt, đơn vị kèm trường, validate theo danh mục `observation_type` và quyền; phân biệt **chưa đo** với **giá trị đo bằng 0**.
- Ghi chú khám thuộc lần khám hiện tại; thuốc là **bản ghi thuốc trong lần khám**, **không tự coi là đơn thuốc có giờ uống đã xác nhận**.
- Ẩn thao tác `Mở bằng ID` và `revision` khỏi giao diện thường; vẫn dùng các giá trị nội bộ để gọi API.

**LÝ DO:** làm rõ quan hệ bệnh nhân → lần khám → dữ liệu. **ƯU TIÊN:** P1.

**TIÊU CHÍ:** không xuất hiện “API trả rỗng” khi chưa chọn hồ sơ; tạo/mở một lần khám và thêm ghi nhận từ đúng ngữ cảnh; chuyển hồ sơ không để nhầm dữ liệu cũ.

## 6. D-05 / UI-11 — Hỗ trợ đánh giá theo lần khám

**HIỆN TẠI:** form trực tiếp nhận `Lần khám ID`, `revision`, bốn module `Diagnosis/Lab/Test/Treatment/MedSafety` và trả `mock_not_evaluated`. Chức năng lâm sàng thực sự chưa được hiện thực.

![Màn hình đánh giá hiện tại](assets/doctor_04_evaluation.png)

**ĐỀ XUẤT:** tab **Hỗ trợ đánh giá** ở hồ sơ/lần khám đang chọn:

1. Đầu màn hình: `Hồ sơ SYN-…` và `Lần khám [thời điểm]`. Nếu chưa chọn lần khám: yêu cầu chọn, không mở form API.
2. Nhóm module với nhãn tiếng Việt: `Đánh giá tình trạng`, `Xét nghiệm và thăm dò`, `Hỗ trợ điều trị`, `An toàn thuốc`.
3. Với module hiện có: cho phép gửi yêu cầu để thử luồng API nếu cần kiểm thử; khu vực phản hồi **chỉ** báo “Chưa có đánh giá lâm sàng – tính năng đang phát triển”.
4. Không hiển thị chẩn đoán, thuốc/liều đề xuất, cảnh báo tương tác hoặc các nút “Chấp nhận điều trị”, “Kê đơn” nếu chưa có logic và phê duyệt lâm sàng.
5. Trong bản mở rộng [CẦN BACKEND], chỉ sau khi module có kết quả hợp lệ mới được thiết kế khối: kết quả → dữ liệu đầu vào/căn cứ → mức độ thiếu dữ liệu → bác sĩ xác nhận/từ chối.

**LÝ DO:** bác sĩ tập trung vào lần khám, không tự nhập ID và revision; UI không đưa ra tín hiệu sai về tính an toàn y khoa. **ƯU TIÊN:** P1.

**TIÊU CHÍ:** form nhận ngữ cảnh tự động; phân biệt rõ chưa đánh giá/đánh giá chưa hỗ trợ/có kết quả hợp lệ; không có nút quyết định từ kết quả stub.

## 7. D-06 / UI-12 — Lịch sử đánh giá & tiến trình chăm sóc

**HIỆN TẠI:** trang lịch sử bắt bác sĩ quay lại Hồ sơ khi chưa chọn bệnh nhân. Dữ liệu API hiện trả **lịch sử đánh giá (evaluation/decision)**, không phải toàn bộ tiến trình bệnh viện.

![Màn hình lịch sử đánh giá hiện tại](assets/doctor_05_history.png)

**ĐỀ XUẤT:** đặt tab `Lịch sử đánh giá` trong chi tiết hồ sơ. Với mỗi bản ghi có thể hiển thị thời điểm, lần khám liên quan, nhóm module đã gọi và trạng thái đánh giá; có nút xem chi tiết. **Không đổi tên thành “Lịch sử khám chữa bệnh đầy đủ”** khi backend chưa có đủ nguồn.

- `Chưa chọn hồ sơ`: nhắc chọn bệnh nhân ở màn danh sách.
- `Đã chọn, không có lịch sử`: nói “Chưa có bản ghi đánh giá cho hồ sơ này”, **không suy diễn tình trạng sức khỏe**.
- `Có dữ liệu`: hiển thị theo thứ tự mới nhất → cũ nhất; mở bản ghi đúng quyền; hỗ trợ xuất JSON nếu API hiện có.
- `[CẦN BACKEND]` timeline điều trị/chỉ số/thuốc theo thời gian chỉ được thêm sau khi có endpoint trả sự kiện đầy đủ, provenance và thời điểm.

**LÝ DO:** đưa lịch sử về đúng hồ sơ bệnh nhân và phản ánh đúng phạm vi dữ liệu. **ƯU TIÊN:** P2.

**TIÊU CHÍ:** bệnh nhân đã chọn thì vào lịch sử không phải chọn lại; trạng thái trống đúng ngữ cảnh; lịch sử chỉ có thông tin hệ thống thực sự lưu.

## 8. D-07 / UI-13 — Quy tắc giữ ngữ cảnh & chống nhầm hồ sơ

**ĐỀ XUẤT LUỒNG CHUẨN:**

```text
Bác sĩ mở danh sách → chọn SYN-001 → mở lần khám A
   → ghi sinh hiệu → xem hỗ trợ đánh giá → xem lịch sử → về hồ sơ SYN-001
Bác sĩ chuyển SYN-002
   → hiện rõ hồ sơ mới; xóa lựa chọn lần khám A; xác nhận khi còn form chưa lưu
```

**Yêu cầu kỹ thuật UX:**

- Tiêu đề ngữ cảnh luôn nói rõ mã hồ sơ và lần khám; thao tác có nguy cơ ghi dữ liệu phải thể hiện đối tượng.
- Khi chuyển bệnh nhân hoặc lần khám, form đang điền chưa lưu cần cảnh báo trước khi rời trang.
- Nếu API trả `401/403/404/409/422/503`, dùng thông báo tiếng Việt: hết phiên/không đủ quyền/không tìm thấy/xung đột dữ liệu/dữ liệu không hợp lệ/dịch vụ chưa sẵn sàng.
- Nếu có nhiều tab trình duyệt, trạng thái phiên và revision phải tuân thủ kiểm tra server, không dựa vào kiểm tra hiển thị.

**ƯU TIÊN:** P1. **TIÊU CHÍ:** không thể lưu ghi nhận của lần khám A sang bệnh nhân B do chuyển màn; đổi hồ sơ không giữ dữ liệu của hồ sơ trước.

## 9. Mapping: giao diện ↔ API / mức độ triển khai

| Giao diện / chức năng | API hoặc nguồn code | Phạm vi hiện tại | Cần làm thêm |
|---|---|---|---|
| Tổng quan / hồ sơ | `GET /api/v1/cases` | **Đã có** | Thiết kế lại UI/empty/loading |
| Tạo / sửa hồ sơ | `POST /api/v1/cases`, `PUT /cases/{id}?expected_revision=` | **Đã có** | Form rõ ràng, validate, cảnh báo xung đột |
| Danh sách / tạo lần khám | `GET/POST /cases/{id}/encounters` | **Đã có** | Đặt vào ngữ cảnh hồ sơ |
| Ghi nhận chỉ số và ghi chú | `GET/POST/PUT /encounters/{id}/observations`, `GET/POST /notes` | **Đã có** (tùy quyền) | Tab và form dễ dùng |
| Thuốc theo lần khám | `GET/POST /encounters/{id}/medications` | **Đã có** (bản ghi thuốc) | **Không** đồng nhất với đơn đã xác nhận |
| Hỗ trợ đánh giá | `POST /api/v1/evaluations` | **Chỉ stub**, không kết luận lâm sàng | `[CẦN BACKEND]` để có kết quả đúng SRS |
| Lịch sử đánh giá | `GET /cases/{id}/history` | **Có** (evaluation/decision) | Hiển thị theo hồ sơ, không gọi timeline đầy đủ |
| Lịch khám bác sĩ / xác nhận lịch | Mới thấy luồng yêu cầu lịch ở API bệnh nhân | **Chưa đủ luồng staff** | `[CẦN BACKEND]` nếu đưa lên dashboard bác sĩ |
| Gợi ý/phác đồ/đơn xác nhận | SRS FR-19..32 | **Chưa hoàn thiện** | `[CẦN BACKEND]` và xác minh an toàn |

*Lưu ý: “Đã có” là đã tìm thấy route/mã xử lý trong repo; chưa thay thế kiểm thử thực tế từng chức năng trên máy người dùng.*

## 10. Thứ tự giao task đề xuất

| Đợt | Task | Ưu tiên | Nhóm việc |
|---|---|---|---|
| 1 | Chuẩn hóa header/sidebar, ẩn thuật ngữ kỹ thuật, giữ cảnh báo an toàn | P1 | Frontend |
| 1 | Chuyển menu sang `Tổng quan / Bệnh nhân` + tabs của hồ sơ | P1 | Frontend |
| 1 | Giữ ngữ cảnh hồ sơ/lần khám và ngăn lưu nhầm | P1 | Frontend + test |
| 1 | Thiết kế lại danh sách/chi tiết hồ sơ | P1 | Frontend |
| 1 | Cải thiện lần khám và form ghi nhận | P1 | Frontend |
| 1 | Đánh giá hiển thị trạng thái chưa hỗ trợ lâm sàng | P1 | Frontend |
| 2 | Lịch sử đánh giá, responsive/accessibility | P2 | Frontend + test |
| 3 | Luồng staff lịch hẹn, timeline đầy đủ và 4 module | Cần quyết định phạm vi | Backend + phân tích nghiệp vụ |

## 11. Checklist nghiệm thu cho nhóm trưởng

- [ ] Logo/tên và Design System đồng bộ giao diện đăng nhập.
- [ ] Dashboard không còn “Gateway/Synthetic API” dưới dạng nội dung chính.
- [ ] Danh sách hồ sơ có thể tìm/chọn; thông tin đều lấy từ API.
- [ ] Tab của hồ sơ giữ đúng hồ sơ đang chọn.
- [ ] Chưa chọn bệnh nhân **không** hiển thị “encounter rỗng”.
- [ ] Tạo, mở lần khám và ghi dữ liệu không yêu cầu nhập ID kỹ thuật thủ công.
- [ ] Đổi bệnh nhân làm mới đúng dữ liệu lần khám, tránh lưu nhầm.
- [ ] Không có kết luận/gợi ý lâm sàng giả trên trang Hỗ trợ đánh giá.
- [ ] Lịch sử chỉ gắn với hồ sơ và API được cấp quyền.
- [ ] Có trạng thái loading/empty/error và kiểm tra bàn phím/1366×768/768px.
- [ ] Có chú thích dễ thấy hệ thống thử nghiệm, không dùng cho quyết định y khoa.

## 12. Quyết định cần nhóm trưởng/dev chốt

1. Tên sản phẩm (HF Care chỉ là tên tạm).
2. Có giữ `Tổng quan / Bệnh nhân` làm toàn bộ sidebar, và tabs trong hồ sơ như sơ đồ trên không? (Hướng patient-centric đã được đồng ý; chi tiết menu còn có thể chỉnh.)
3. Trong phạm vi đồ án, có cần thêm trường họ tên bệnh nhân (giả lập) hay tiếp tục chỉ dùng mã/tuổi/giới tính?
4. Luồng liên kết tài khoản bệnh nhân tự đăng ký với hồ sơ bác sĩ đang quản lý được thực hiện như thế nào?
5. Có ưu tiên hoàn thiện backend đánh giá hay giới hạn ở demo luồng nhập/xem dữ liệu trước kỳ nghiệm thu?

## 13. Nguồn mã để dev đối chiếu

- [Repository](https://github.com/tnhh175/suytim_clone_demo/)
- [SRS](https://github.com/tnhh175/suytim_clone_demo/blob/main/submissions/suy_tim_nhom27/docs/SRS_v1.0.md)
- [Kế hoạch UI hiện có](https://github.com/tnhh175/suytim_clone_demo/blob/main/submissions/suy_tim_nhom27/docs/ui-ux-plan.md)
- [Frontend](https://github.com/tnhh175/suytim_clone_demo/blob/main/submissions/suy_tim_nhom27/web/app.js)
- [Backend clinical](https://github.com/tnhh175/suytim_clone_demo/blob/main/submissions/suy_tim_nhom27/src/gateway/clinical.py)
