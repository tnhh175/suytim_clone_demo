# Database theo SRS và cổng bệnh nhân tối giản

`schema.sql` xây dựng 39 bảng PostgreSQL 16+ từ mô hình hiện có, đối chiếu FR-01..34 và thêm FR-P01..04. `seed.sql` tạo dữ liệu synthetic cho năm vai trò, hai hồ sơ, một đơn thuốc đã xác nhận, ba giờ uống mỗi ngày, một lịch hẹn và các chỉ số tự nhập. `schema_metadata.json` cùng `data_dictionary.md` được xuất từ schema đã chạy.

Đây là phần lưu trữ và phân quyền CSDL. Gateway trong `src/gateway/` vẫn dùng RAM với ba tài khoản stub; chưa có API/giao diện bệnh nhân, bộ xác thực DB hay tiến trình gửi thông báo. Các chức năng dưới đây được kiểm tra bằng SQL.

## Khởi tạo

Chạy trên database **rỗng**, bằng chủ schema. Bước tạo vai trò DB cần quyền `CREATEROLE`.

Bootstrap gồm năm bước, theo đúng thứ tự. Các lệnh chạy bằng chủ CSDL `hf_demo`; bước cuối cần quyền `CREATEROLE` và một `HF_RUNTIME_PASSWORD` đặt trong môi trường tiến trình `psql`:

```sh
export HF_RUNTIME_PASSWORD='(chọn mật khẩu riêng cho môi trường demo cục bộ)'
psql -v ON_ERROR_STOP=1 -d hf_demo -f database/schema.sql
psql -v ON_ERROR_STOP=1 -d hf_demo -f database/seed.sql
psql -v ON_ERROR_STOP=1 -d hf_demo -f database/portal_permissions.sql
psql -v ON_ERROR_STOP=1 -d hf_demo -f database/migrations/001_result_integrity.sql
psql -v ON_ERROR_STOP=1 -d hf_demo -f database/runtime_roles.sql
```

Compose gắn cả năm script lần lượt thành `01-schema.sql` đến `05-runtime-roles.sql`; PostgreSQL chỉ chạy chúng khi volume `hf_data` còn rỗng. Trong Compose, `DB_RUNTIME_PASSWORD` (mặc định chỉ dành cho demo cục bộ) được chuyển thành `HF_RUNTIME_PASSWORD` để tạo role `hf_demo_runtime`. Gateway container kết nối bằng `DATABASE_URL=postgresql://hf_demo_runtime:<mật-khẩu>@db:5432/hf_demo`. Khi chạy Gateway ngoài Compose, đặt `DATABASE_URL` trỏ tới cùng role runtime và host/port CSDL có thể truy cập được, ví dụ `postgresql://hf_demo_runtime:<mật-khẩu>@127.0.0.1:5432/hf_demo`; không dùng tài khoản bootstrap của PostgreSQL cho Gateway. Volume đã có schema cũ cần migration riêng; bootstrap không tự nâng cấp hoặc xóa dữ liệu. `seed.sql` được kiểm tra chạy lại hai lần mà không thêm bản ghi trùng, thay revision hoặc lặp audit. Các fixture đã có được giữ nguyên.

## Tài khoản và dữ liệu mẫu

| Username trong CSDL | Vai trò | UUID cuối | Phạm vi |
|---|---|---|---|
| doctor_demo | doctor | 001 | Bác sĩ phụ trách hai ca; được cấp riêng `rule.approve` |
| nurse_demo | nurse | 002 | Sinh hiệu/chăm sóc của SYN-DEMO-001 |
| pharmacist_demo | pharmacist | 003 | MedSafety/nhận xét của SYN-DEMO-001 |
| admin_demo | admin | 004 | Quản lý kỹ thuật; không tự có quyền phê duyệt y khoa |
| patient_demo | patient | 005 | Chỉ hồ sơ SYN-DEMO-001 |

UUID tài khoản có dạng `00000000-0000-4000-8000-00000000000x`. Mật khẩu fixture là `DemoOnly!2026`; chỉ hash PBKDF2-SHA256 với 600.000 vòng và salt riêng được lưu trong seed. Định dạng: `pbkdf2_sha256$iterations$base64(salt)$base64(hash)`. Đây là tài khoản DB demo đã công khai mật khẩu trong hướng dẫn, cần thay khi xây dựng ứng dụng thực. Chúng chưa đăng nhập được vào Gateway RAM hiện tại.

Đơn thuốc chỉ dùng hoạt chất giả lập A/B. A có giờ 08:00 và 20:00; B có giờ 12:00, theo `Asia/Ho_Chi_Minh`. Seed tạo 21 nhắc cho bảy ngày bắt đầu ngày chạy seed. Thuốc/liều mẫu không dùng điều trị.

## Phân quyền cổng bệnh nhân

`hf_patient_portal` là vai trò CSDL **NOLOGIN**, không sở hữu bảng, không có quyền bypass RLS. Backend dùng connection tin cậy, xác thực phiên, lấy UUID từ phiên và chuyển vai trò trong một transaction. Không lấy `app.user_id` từ UUID do client tự gửi. DB owner/superuser bỏ qua RLS; không dùng quyền đó để xử lý yêu cầu bệnh nhân.

```sql
BEGIN;
SET LOCAL ROLE hf_patient_portal;
SELECT set_config('app.user_id', '00000000-0000-4000-8000-000000000005', true);
SELECT * FROM portal_doctors();
SELECT * FROM patient_prescription_view;
SELECT * FROM patient_reminder_view ORDER BY due_at;
SELECT * FROM patient_measurement ORDER BY observed_at DESC;
COMMIT;
```

RLS chỉ trả dữ liệu thuộc hồ sơ được liên kết. Không có identity, hoặc tài khoản bị khóa, sẽ không có hồ sơ cổng. Vai trò bệnh nhân chỉ được thêm lịch/chỉ số và cập nhật cột `status` của lịch hẹn/nhắc uống; không đọc password hash, audit, quy tắc hay kết quả hỗ trợ chuyên môn. Backend nhân viên vẫn phải kiểm tra quyền theo phiên và phạm vi hồ sơ cho mọi thao tác; các trigger kiểm tra vai trò của người ghi, bác sĩ phụ trách và quyền phê duyệt không thay thế việc xác thực phiên.

## Đặt lịch và chỉ số tại nhà

Trong transaction bệnh nhân ở trên:

```sql
INSERT INTO appointment(case_id, doctor_id, slot_at, reason, requested_by)
VALUES ('10000000-0000-4000-8000-000000000001',
        '00000000-0000-4000-8000-000000000001',
        (CURRENT_DATE + 8 + TIME '09:30') AT TIME ZONE 'Asia/Ho_Chi_Minh',
        'Tái khám demo', current_app_user());

INSERT INTO patient_measurement(case_id, recorded_by, observed_at,
                               systolic_bp, diastolic_bp, heart_rate, weight_kg)
VALUES (portal_case_id(), current_app_user(), now(), 120, 80, 72, 60);
```

Lịch có slot cố định 30 phút; partial UNIQUE chặn trùng bác sĩ và bệnh nhân khi `requested/confirmed`, kể cả các yêu cầu đồng thời. Bệnh nhân hủy lịch bằng `UPDATE appointment SET status='cancelled' WHERE id=...`; quyền cột và RLS không cho tự xác nhận. Nhân viên mới được chuyển `requested → confirmed → completed`. Hủy slot cho phép đặt lại. Lần khám được liên kết khi lịch hoàn thành và phải cùng hồ sơ.

Chỉ số tại nhà có ít nhất một giá trị; huyết áp phải có đủ hai số; từ chối số âm, NaN/Infinity, SpO₂ ngoài miền biểu diễn 0–100 và thời điểm đo vượt quá 5 phút trong tương lai. Bản ghi là append-only: nhập sai thì ghi bản mới. Không gộp tự động với `observation` theo lần khám; nhân viên cần xác minh và nhập dữ liệu lâm sàng khi sử dụng trong đánh giá.

## Đơn thuốc, giờ uống và nhắc uống

1. Bác sĩ tạo `prescription` ở trạng thái `draft` cho đúng hồ sơ/lần khám.
2. Thêm `medication` với hoạt chất/sản phẩm, liều, đường dùng, tần suất, khoảng ngày và hướng dẫn.
3. Thêm mỗi giờ uống vào một dòng `medication_schedule`; không dùng chuỗi `08:00,20:00` trong cột thuốc.
4. Chuyển đơn sang `confirmed`. Trigger yêu cầu có thuốc, khoảng ngày hợp lệ và số giờ uống bằng `frequency_per_day` của từng thuốc.
5. Worker gọi hàm sau bằng connection dịch vụ được cấp quyền, mỗi batch tối đa 31 ngày:

```sql
SELECT generate_medication_reminders(CURRENT_DATE, CURRENT_DATE + 6);
```

Hàm chuyển ngày địa phương + giờ uống + múi giờ đơn thành `due_at` có múi giờ. UNIQUE `(schedule_id, scheduled_on)` chống tạo nhắc trùng khi retry. Chỉ sinh nhắc cho đơn xác nhận trong thời gian dùng và tài khoản bệnh nhân đang hoạt động. Worker gửi thông báo thực tế chưa có; `notified_at` được dành cho worker tương lai.

Trong transaction bệnh nhân, đọc `patient_reminder_view` rồi cập nhật nhắc của mình:

```sql
UPDATE medication_reminder SET status = 'taken'
WHERE id = (SELECT id FROM patient_reminder_view WHERE status = 'pending' ORDER BY due_at LIMIT 1);
-- Hoặc status = 'skipped'. Trigger tự ghi responded_at.
```

Nhắc đã phản hồi không sửa lại; đơn xác nhận và các thuốc/giờ uống trong đó được giữ bất biến. Muốn đổi liều/giờ, bác sĩ hủy đơn và lập bản mới để bảo toàn lịch sử. Hủy đơn hủy các nhắc `pending`, giữ các nhắc đã uống/bỏ qua. Lịch tối giản là uống hằng ngày; PRN, lịch theo tuần và thông báo thật nằm ngoài bản cập nhật SQL.

## Quy tắc, revision và audit

Quy tắc đi qua `draft → tested → approved → active → retired`; có thể trả `tested → draft` để sửa. Nội dung đã tested được giữ nguyên; các phiên bản đã duyệt cần bản mới khi thay đổi. Hash là `encode(sha256(convert_to(content::text,'UTF8')),'hex')` từ JSONB PostgreSQL. Quyền duyệt `rule.approve` được cấp riêng, bằng chứng phải khớp nội dung đã tested. Seed chỉ có rule draft, không có rule lâm sàng active.

Các thay đổi dữ liệu lâm sàng tăng `patient_case.revision`; quyết định bác sĩ bị từ chối khi snapshot cũ hơn dữ liệu hiện tại. Quyết định điều chỉnh phải có JSONB `adjustment_details` và lý do. Snapshot, quyết định, bằng chứng duyệt và audit là append-only. Trigger ghi audit cho các bảng nghiệp vụ quan trọng; backend phải đặt `app.user_id` theo phiên cho thao tác nhân viên. Tiến trình tạo nhắc không có phiên được ghi `actor_kind=system`, không gán nhầm cho bệnh nhân.

## Kiểm thử và xuất lại metadata

Node.js và `@electric-sql/pglite@0.5.8` chạy schema/seed/RLS/trigger trong PostgreSQL WASM. Trên PowerShell, từ thư mục nhóm:

```powershell
$sqlTestRoot = Join-Path $env:TEMP 'suytim-sql-validation'
npm install --prefix $sqlTestRoot --no-audit --no-fund @electric-sql/pglite@0.5.8
$env:PGLITE_MODULE = Join-Path $sqlTestRoot 'node_modules\@electric-sql\pglite\dist\index.js'
node --test database/tests/database.test.mjs

# Chỉ khi cần đồng bộ metadata và từ điển dữ liệu:
$env:DB_EXPORT_METADATA = '1'
node --test database/tests/database.test.mjs
Remove-Item Env:DB_EXPORT_METADATA
```

Kiểm thử thực thi: bootstrap + seed replay, hash mật khẩu, giới hạn dữ liệu nhập, RLS giữa hai bệnh nhân, giờ uống, chống trùng lịch, quyền cập nhật, tạo nhắc/retry/hủy, quyền duyệt rule, revision và nhật ký bất biến. Metadata gồm cột/kiểu chính xác/nullable/default/mô tả/constraint, khóa, index, trigger và policy RLS, xuất từ catalog PostgreSQL. Bộ chạy đã kiểm tra trên PGlite PostgreSQL 18.3; môi trường này chưa có server PostgreSQL 16/Docker để kiểm tra triển khai thật.
