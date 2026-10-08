# QA baseline và migration toàn vẹn kết quả — 08/10/2026

Phạm vi kiểm tra: SRS hiện tại (34 FR, 13 NFR, FR-P01..P04), schema/seed/phân quyền cổng bệnh nhân, README/docs, OpenAPI, Gateway và các test hiện có. Baseline là commit `c2076c365a3ce337bdeee72c830d25c8a67fb4c5` trên clone demo; mọi dữ liệu kiểm tra là synthetic. Rà soát được thực hiện trong worktree QA, không ghi dữ liệu vào database triển khai.

## Findings baseline

Đường dẫn và số dòng trong bảng tham chiếu baseline, trước migration.

| Mức | Loại | Bằng chứng | Hành vi và hệ quả |
|---|---|---|---|
| P1 | Bug đã tái hiện, migration xử lý | `database/schema.sql:254–279,466–469,889–894` | UPDATE `module_result` của evaluation seed đã có quyết định thành `completed`, thay message và gắn rule draft thành công. Bảng kết quả con không bất biến; gợi ý gốc trong lịch sử có thể bị viết lại. |
| P2 | Bug đã tái hiện, migration xử lý | `database/schema.sql:257–262` | Kết quả `treatment` chấp nhận rule `diagnosis` đang `draft`; FK chỉ kiểm tra tồn tại, không kiểm tra module/phê duyệt. |
| P3 | Tài liệu cũ, còn tồn tại | `docs/consistency_review.md:3,11,21`; `api/README.md:18–26` | Tài liệu tuần 3 còn nói ba vai trò, seed chưa có app_user và 11 mã chỉ số; schema hiện có năm vai trò, năm app_user, 24 mã. Mapping số FR trong bảng API thuộc SRS cũ. |

Các phần đã được ghi nhận là chưa hoàn tất, không coi là regression:

- Gateway dùng RAM (`src/gateway/store.py:11–15`, `README_TUAN3.md:34`); chưa đáp ứng NFR-05 về tồn tại dữ liệu sau restart và chưa có frontend.
- Auth chỉ có doctor/pharmacist/admin và mật khẩu chung trong biến môi trường (`src/gateway/models.py:10–12`, `src/gateway/main.py:49–58`). Chưa có nurse/patient, logout, session DB hay khóa tài khoản.
- Stub cấp pharmacist phạm vi mọi ca synthetic (`src/gateway/main.py:35–39`), chưa dùng assignment của schema. Backend nhân viên phải kiểm tra phiên, vai trò và phạm vi ca; trigger xác thực ID người ghi không thay cho xác thực phiên.
- Quyết định `adjusted` của API chỉ cần reason (`src/gateway/models.py:135–143`): TestClient đã trả 201 khi không có nội dung điều chỉnh. SRS FR-31 và SQL `clinical_decision` yêu cầu `adjustment_details`.
- FR-P01..P04 mới hiện thực ở SQL; chưa có API/UI hay worker gửi thông báo (`database/README.md:5,82`, `docs/SRS_v1.0.md:222–225`).
- Nursing có thể ghi mọi mã observation/test_report theo trigger `database/schema.sql:568–569`; probe nurse ghi EF thành công. SRS chưa cung cấp whitelist cụ thể; ứng dụng cần giới hạn trường theo phạm vi nghiệp vụ được chốt.

Không coi mật khẩu seed demo công khai là secret bị lộ: tài liệu ghi rõ chỉ dùng local, seed lưu PBKDF2-SHA256 với 600.000 vòng. TestClient xác nhận admin đọc trực tiếp `/api/v1/cases/{id}` trả 403. Test hiện có xác nhận kết quả Gateway luôn `mode=stub`, `mock_not_evaluated`, khuyến cáo rỗng; không được trình bày đây là PASS y khoa.

## Các command thực sự chạy

Dependencies Python được cài trong `%TEMP%\suytim-qa-python`, PGlite được dùng từ `%TEMP%\suytim-sql-validation`; không cài dependency vào repo. Command kiểm thử dưới đây dùng thư mục nhóm làm root import; lần chạy QA sử dụng đường dẫn tuyệt đối, `PYTHONPATH` trỏ tới thư mục nhóm, `PYTHONDONTWRITEBYTECODE=1` và `-p no:cacheprovider` để không tạo cache trong worktree.

| Command | Exit | Trạng thái |
|---|---:|---|
| `%TEMP%\suytim-qa-python\Scripts\python.exe -m pip install -r requirements-dev.txt` | 0 | Cài thành công trên Python 3.12 |
| `%TEMP%\suytim-qa-python\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_gateway.py` | 0 | Baseline: 8 passed, 1 cảnh báo Starlette/httpx deprecation |
| `node --test database/tests/database.test.mjs` | 0 | Baseline: 19 passed, PostgreSQL 18.3 / PGlite 0.5.8 |
| `node --test database/tests/database.test.mjs database/tests/result_integrity.test.mjs` | 0 | Sau migration: 28 passed, 0 failed, 0 skipped; 19 test bootstrap cũ và 9 regression trên database có migration |

PGlite dùng biến môi trường `PGLITE_MODULE` trỏ tới `dist/index.js` theo `database/README.md`. Các probe bổ sung chạy trong PGlite RAM và rollback mỗi tình huống; hai probe P1/P2 trước migration được chấp nhận, regression sau migration chứng minh bị từ chối.

## Migration bổ sung

`database/migrations/001_result_integrity.sql` là migration chạy một lần bằng schema owner, sau bootstrap `schema.sql`, `seed.sql`, `portal_permissions.sql`:

```sh
psql -v ON_ERROR_STOP=1 -d hf_demo -f database/migrations/001_result_integrity.sql
```

Migration không được tự thêm vào Compose/bootstrap. Người ghép nhánh cần chạy migration trước khi ghi kết quả ứng dụng. `schema.sql`, seed và metadata bootstrap được giữ nguyên; test regression nạp migration riêng sau bootstrap.

Migration chặn UPDATE/DELETE của `module_result`, `recommendation`, `result_missing_field`. INSERT mới của mode stub chỉ nhận `mock_not_evaluated` và không gắn clinical rule. Mode validated yêu cầu kết quả không mock, rule đang active, đúng module, có approval khớp content hash. Recommendation chỉ được thêm cho kết quả completed thuộc evaluation validated. Share lock trên rule bảo vệ việc ghi kết quả trước retirement đồng thời.

Validation áp dụng khi INSERT kết quả mới, không hồi tố hoặc xóa lịch sử. Rule retired vẫn được truy từ kết quả cũ, nhưng không thể tạo kết quả mới dùng rule retired. Các approval/regression fixture là synthetic, không chứng minh độ đúng lâm sàng. Cây evaluation và children phải được ghi trong một transaction ứng dụng. Khi đã có `clinical_decision`, trigger AFTER INSERT từ chối hàng mới bổ sung trên cả ba bảng bằng exception rollback; trước quyết định vẫn được INSERT. Validation mode/status/rule dùng BEFORE INSERT. AFTER INSERT không chạy khi ON CONFLICT DO NOTHING bỏ qua hàng trùng, nên replay seed không bị chặn. Guard children và trigger quyết định khóa cùng hàng evaluation để tuần tự hóa việc ghi children với quyết định. Migration không thêm audit cho INSERT children và không tự đánh dấu evaluation hoàn tất trước khi có quyết định.

## Giới hạn kiểm chứng

- Không có `psql` hoặc Docker trong PATH của môi trường QA: chưa chạy PostgreSQL 16 thật hay Compose. PASS PGlite không thay cho kiểm chứng triển khai đó.
- Chưa kiểm tra browser/layout, tải, backup/restore, mạng dịch vụ hay tính đúng y khoa.
- Kiểm thử migration không mô phỏng hai connection đồng thời; khóa row được xem xét qua SQL, chưa chứng minh bằng test retirement hoặc quyết định cạnh tranh.
- Migration bảo vệ INSERT mới và mutation tương lai, không rà soát/sửa các kết quả legacy không hợp lệ đã tồn tại trước khi áp dụng. Baseline seed đang có kết quả stub và được giữ nguyên.
- Các gap ứng dụng và tài liệu P3 trong báo cáo chưa được sửa bởi nhánh QA.

- Regression xác nhận bootstrap → seed → migration → seed replay thành công, giữ nguyên số kết quả, recommendation, missing fields, audit và revision. Probe ban đầu phát hiện BEFORE INSERT chặn seed replay; guard finalization đã chuyển sang AFTER INSERT và lỗi đó đã được xử lý.
