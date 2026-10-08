# Hợp đồng REST API Gateway

API JSON dùng prefix `/api/v1`, UUID cho ID và ngày giờ ISO 8601 có timezone. Hợp đồng runtime tại `/openapi.json` được xuất vào [openapi.yaml](openapi.yaml). Mọi lỗi có dạng `{"detail":"..."}`; lỗi validation không echo giá trị nhập. Token demo là bearer opaque có hạn một giờ; API chỉ dành cho môi trường local.

Các module `diagnosis`, `lab_test`, `treatment`, `medsafety` luôn trả `mode=stub`, `status=mock_not_evaluated` và không có khuyến nghị/cảnh báo lâm sàng. Bản ghi thuốc qua encounter là dữ liệu synthetic, không tạo đơn hoặc lịch uống.

## Endpoint đang được hỗ trợ

| Nhóm | Endpoint | Quyền/phạm vi |
|---|---|---|
| Identity | `POST /auth/register`, `POST /auth/token`, `POST /auth/logout`, `GET /auth/me` | Đăng ký mới chỉ patient; đăng nhập tài khoản demo hoặc patient đã đăng ký; session lưu trong PostgreSQL. |
| Hồ sơ | `GET /cases`, `POST /cases`, `GET /cases/{id}` | Bác sĩ; điều dưỡng chỉ hồ sơ thuộc nursing scope. Tạo hồ sơ chỉ bác sĩ. |
| Hồ sơ | `PUT /cases/{id}?expected_revision=...` | Bác sĩ; cập nhật có kiểm tra revision. |
| Encounter | `GET /cases/{id}/encounters`, `POST /cases/{id}/encounters`, `GET /encounters/{id}` | Đọc theo role/scope; tạo encounter chỉ bác sĩ và cần revision. |
| Clinical data | `GET/POST /encounters/{id}/observations`; `PUT /cases/{case_id}/encounters/{encounter_id}/observations/{observation_id}` | Bác sĩ; điều dưỡng được ghi allowlist nursing trong nursing scope. Thao tác ghi cần revision. |
| Notes | `GET/POST /encounters/{id}/notes` | Bác sĩ ghi `examination`; điều dưỡng ghi `nursing`; revision được gửi qua query. |
| Medication | `GET/POST /encounters/{id}/medications` | Bác sĩ clinical scope; dược sĩ chỉ đọc trong medsafety scope. POST chỉ bác sĩ, cần `expected_revision`; ghi bản ghi synthetic. |
| Evaluation | `POST /evaluations`, `GET /evaluations/{id}`, `POST /evaluations/{id}/decisions` | Bác sĩ; dược sĩ chỉ gọi/đọc MedSafety. Kết quả luôn stub; quyết định chỉ là bản ghi demo. |
| History | `GET /cases/{id}/history`, `GET /cases/{id}/export` | Bác sĩ trong clinical scope; chỉ lịch sử evaluation/decision hiện có, không phải timeline đầy đủ. |
| Rules | `GET/POST /rule-versions`; `POST /rule-versions/{id}/test`, `/approve`, `/activate` | Quản trị soạn/test; quyền duyệt tách riêng. Không bật nếu thiếu phê duyệt đúng phiên bản/hash. Test chỉ kiểm cấu trúc. |
| Audit | `GET /audit-events` | Quản trị. |
| Patient portal | `GET /patient/doctors`, `/appointments`, `/measurements`, `/prescriptions`, `/reminders`; `POST /patient/appointments`, `/measurements`, `/appointments/{id}/cancel`; `PATCH /patient/reminders/{id}` | Chỉ patient, giới hạn vào case gắn với tài khoản bằng role `hf_patient_portal` và RLS. Không sửa prescription/schedule. |
| System | `GET /health` | Công khai; kiểm tra kết nối PostgreSQL và báo `503` nếu DB chưa sẵn sàng. |

Tất cả endpoint trên có đầy đủ prefix `/api/v1`. Xem schema cụ thể và mã lỗi trong `/docs` hoặc `openapi.yaml`.

## Đăng nhập nhanh

```json
{"username":"doctor_demo","password":"DemoOnly!2026"}
```

Gửi token nhận được trong header `Authorization: Bearer <access_token>`. Tài khoản chỉ dùng dữ liệu synthetic của seed.

## Đăng ký bệnh nhân

`POST /api/v1/auth/register` công khai nhận:

```json
{"username":"patient_synthetic","password":"SyntheticOnly!2026","age":70,"sex":"unknown"}
```

Thành công `201`: `{"username":"patient_synthetic","role":"patient"}`. Không trả token, hash, ID hồ sơ hoặc mật khẩu; đăng nhập qua `/auth/token`, sau đó `/auth/me` để đọc vai trò được server cấp.

- Tên đăng nhập được cắt khoảng trắng đầu/cuối, phân biệt hoa thường, 3–80 ký tự `[A-Za-z0-9_.-]`, bắt đầu bằng chữ hoặc số.
- Mật khẩu 12–128 ký tự, không chỉ gồm khoảng trắng; tuổi số nguyên 0–120; giới tính `male`, `female` hoặc `unknown` (mặc định).
- Trường ngoài schema như `role`, `case_id`, `owner_id` bị từ chối `422`. Mọi validation dùng thông báo không echo giá trị nhập.
- Giao dịch tạo user, role patient, hồ sơ synthetic mới và liên kết 1:1; lỗi ở bất kỳ bước nào rollback toàn bộ. Không gắn với hồ sơ hoặc tài khoản khác.
- `409` nếu tên đăng nhập đã có, kể cả yêu cầu đồng thời; `503` nếu DB/bác sĩ phụ trách không hợp lệ; `429` với `Retry-After: 60` nếu quá giới hạn. Cấu hình bác sĩ và giới hạn demo được mô tả trong README.

## Lưu ý dữ liệu và revision

- Hồ sơ/encounter/observations/notes/medications kiểm tra scope phía server; thao tác ghi có revision để tránh ghi đè thay đổi mới.
- Bệnh nhân không gửi `case_id`; server lấy hồ sơ từ phiên đã xác thực. DB RLS là lớp giới hạn dữ liệu thứ hai.
- Chỉ số tự khai tại nhà được lưu ở `patient_measurement`, không biến thành observation đã nhân viên xác minh.
- Một evaluation không có nghĩa là lâm sàng đã được đánh giá; `mock_not_evaluated` không đồng nghĩa “không có nguy cơ”.
- Ngoài tạo tài khoản patient qua `/auth/register`, không có API CRUD người dùng, catalog, prescription/schedule hay tích hợp dịch vụ ngoài trong phạm vi demo.
