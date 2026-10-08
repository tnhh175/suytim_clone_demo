# Hợp đồng REST API Gateway

`openapi.yaml` dùng OpenAPI 3.0.3, được xuất từ cùng mô hình và routing dùng khi chạy. `/docs` hiển thị Swagger UI, `/openapi.json` trả cùng hợp đồng. Chạy `python scripts/export_openapi.py` sau khi đổi route/model.

- Prefix: `/api/v1`; JSON; UUID cho ID, kể cả `owner_id`, `doctor_id` và các ID trong audit; ngày giờ ISO 8601 có timezone.
- Thành công: 200 đọc/test, 201 tạo. Lỗi: 401 token, 403 quyền, 404 đối tượng, 409 revision/trạng thái, 422 validation, 503 cấu hình demo thiếu.
- Envelope lỗi: `{"detail":"mô tả lỗi"}`. Lỗi validation không lặp lại giá trị đầu vào.
- Mỗi lần đánh giá trả `mode=stub`, `rule_version=STUB-0.1`, `status=mock_not_evaluated`, không trả chẩn đoán hoặc liều thuốc.
- Token demo là opaque bearer có hạn 1 giờ, không phải OAuth2/JWT production. Chỉ chạy localhost. Khi triển khai cần thay Identity adapter, HTTPS, giới hạn tốc độ và quyền theo ca.
- POST `/cases` tự sinh `synthetic_code` nếu không truyền; có thể truyền mã `SYN-...` khi cần thử luồng trùng mã. PUT `/cases/{id}` yêu cầu mã hiện có và `expected_revision`.
- Các trường chuỗi chỉ để synthetic. Từ chối trường ngoài schema không đảm bảo phát hiện PII nằm trong text hợp lệ; người nhập vẫn phải dùng dữ liệu giả lập.

## Nhóm endpoint và truy vết

| Endpoint | UC / FR được định hướng phục vụ | Quyền |
|---|---|---|
| POST /auth/token | UC-01 / FR-01 | Ba tài khoản demo |
| GET, POST /cases; GET, PUT /cases/{id} | UC-02 / FR-02–04 | Bác sĩ |
| POST /cases/{id}/encounters; GET /encounters/{id} | UC-02 / FR-02 | Bác sĩ |
| GET, POST /encounters/{id}/observations | UC-02 / FR-03–05,07 | Bác sĩ |
| GET, POST /encounters/{id}/medications | UC-02,06 / FR-06 | GET: bác sĩ/dược sĩ; POST: bác sĩ |
| POST /evaluations; GET /evaluations/{id} | UC-03–06 / FR-07–22,24 | Bác sĩ; dược sĩ chỉ MedSafety |
| POST /evaluations/{id}/decisions | UC-07 / FR-23–24 | Bác sĩ |
| GET /cases/{id}/history; GET /cases/{id}/export | UC-08,10 / FR-25–26 | Bác sĩ |
| GET, POST /rule-versions; POST /rule-versions/{id}/test, /activate | UC-09 / FR-27 | Quản trị; activate chặn khi chưa duyệt |
| GET /audit-events | UC-08 / FR-24 | Quản trị |
| GET /health | NFR-05 (kiểm sống tiến trình) | Công khai |

SRS có quản lý tài khoản ở US-11 nhưng chưa có UC riêng; skeleton chưa thêm CRUD tài khoản. Endpoint đánh giá là routing chung với `modules` để chọn trong bốn module; phản hồi giữ kết quả riêng theo module. Các endpoint hiện chạy handler và adapter cục bộ, chưa proxy tới dịch vụ mạng.

**Mã FR trong bảng là phạm vi thiết kế của route, không phải các yêu cầu đã hoàn tất.** Đặc biệt FR-08–22 chưa có logic lâm sàng: `/evaluations` luôn trả `mock_not_evaluated`, danh sách gợi ý/cảnh báo rỗng. FR-03–05 chỉ có tập biến demo. FR-27 chỉ tạo/test cấu trúc, luôn từ chối kích hoạt khi thiếu phê duyệt. Xem [bảng kiểm tra](../docs/consistency_review.md) trước khi phân công xây module.

## Ví dụ

1. POST `/auth/token`: `{"username":"doctor","password":"giá trị DEMO_PASSWORD bạn đặt"}`.
2. POST `/cases`: `{"age":75,"sex":"female"}`; phản hồi có `synthetic_code` do hệ thống sinh. Để chạy demo theo mã định sẵn, thêm `"synthetic_code":"SYN-DEMO-01"`.
3. POST `/cases/{case_id}/encounters`: `{"occurred_at":"2026-09-27T09:00:00+07:00"}`.
4. GET `/cases/{case_id}` lấy revision mới nhất, dùng cho POST `/evaluations`:

```json
{"encounter_id":"UUID-lượt-khám","expected_revision":2,"modules":["diagnosis","lab_test","treatment","medsafety"]}
```

5. POST `/evaluations/{evaluation_id}/decisions`: `{"action":"rejected","reason":"Kiểm thử luồng phản hồi demo"}`.

Mỗi thay đổi ca/CLS/thuốc/lượt khám tăng revision. Quyết định trên đánh giá cũ trả 409. Để sửa giá trị đo trong stub, gửi bản ghi mới có thời điểm đo phù hợp; không có DELETE/PATCH observation trong skeleton. Kết quả đánh giá cũ vẫn giữ snapshot cũ.
