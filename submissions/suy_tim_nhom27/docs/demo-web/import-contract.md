# Hợp đồng dữ liệu M1/M2 — Excel — version 1.0

Đây là thiết kế kỹ thuật demo thống nhất S1/Dev, không là định dạng HIS đã xác minh. Theo yêu cầu mới, không có tính năng dán/tải file JSON. Catalog động và validator dùng chung cho nhập tay/Excel; không tạo trường từ file.

## Nhận diện và quyền

Mã hồ sơ và mã lượt là chuỗi, phải khớp chính xác hồ sơ/lượt có sẵn trong phạm vi owner hoặc form_access. Không so tên gần giống, không tạo hồ sơ/lượt ngầm, không mất số 0 đầu. Admin không mặc nhiên được mọi dữ liệu bệnh nhân. Actor/quyền lấy từ phiên đăng nhập server; client không được tự khai actor/provenance.

Excel chọn sheet/header/mapping trường hiện có; nếu có mã hồ sơ/lượt rõ thì đối chiếu từng hàng. Nếu thiếu mã lượt (workbook được cấp đang như vậy), chọn một hàng rõ ràng và xác nhận hồ sơ+lượt đích; tuyệt đối không gán cả workbook vào ca đang mở. Mã số Excel đã mất số 0 đầu không thể phục hồi bằng đoán.

## Kiểu và NULL

PATCH trường không gửi giữ nguyên; null là xóa có chủ ý theo thao tác cho phép. Import null/thiếu luôn bỏ qua, không xóa đích. false/0 giữ nguyên. Chuỗi trống được chuẩn hóa thành NULL theo validator chung; không coi chuỗi "NULL" là thiếu. [] chỉ hợp lệ ở kiểu danh sách và có nghĩa danh sách ghi nhận rỗng.

Thuốc: array object `{name, ingredient?, dose?, route?, frequency?, observed_at?}`. Kết quả: array object `{name, value?, unit?, observed_at?}`. Tên bắt buộc không trống; thuộc tính chưa biết null/thiếu; value số hữu hạn; observed_at ISO datetime có timezone hoặc null. Không suy đơn vị/thời điểm, liều không được parse thành quy tắc kê đơn. Đây là cấu trúc kỹ thuật theo các thành phần nguồn TL06, CHƯA CÓ NGUỒN XÁC NHẬN là schema chuyên môn viện duyệt.

Array là một giá trị nguyên tử: so sánh toàn cấu trúc theo thứ tự; không append/gộp mục bằng tên thuốc/xét nghiệm vì thiếu định danh sự kiện. Giá trị nguồn khác đích là conflict; mặc định giữ đích, thay cả array chỉ khi người dùng chọn rõ. Không tự bỏ các kết quả trùng tên vì có thể khác thời điểm.

## Validation và giới hạn

Giới hạn Excel kỹ thuật: `.xlsx` tối đa 4 MiB, nội dung ZIP giải nén tối đa 32 MiB/1.000 thành phần, sheet tối đa 1.000 hàng dữ liệu và 500 cột; header hàng 1–100; tối đa 100 bản ghi một preview, 500 mapping, preview hết hạn sau 1.800 giây. Giá trị text tối đa 5.000 ký tự, mảng nội bộ tối đa 200 mục, mã hồ sơ 60/mã lượt 100 ký tự. Không phải ngưỡng y khoa.

Kiểm định dạng file, sheet/header, công thức không được thực thi, cột/định danh/mapping trùng và giới hạn trước commit. Runtime resolve từng target trong catalog hiện hành, kiểm active/type/choices và từ chối trường chưa đặc tả. Lỗi có sheet/hàng/cột/field và lý do. Không tự đoán ngày, bảng mã, đơn vị hoặc chuyển năm sinh thành tuổi. Chuyển đổi số/cờ/ngày phải chọn rõ và có căn cứ; không đánh đồng cờ số với boolean khi chưa có bảng mã.


## Preview, merge và commit

Preview chỉ đọc nghiệp vụ, trả kế hoạch có dấu xác thực server cùng catalog revision, revision từng lượt, canonical payload hash, mapping version và nguồn vị trí. Nguồn Excel theo sheet/hàng/cột gốc. Preview/hủy không ghi hồ sơ/lượt/history/import_batch. Metadata nguồn do server tạo từ file/parser và session.

Chỉ điền đích NULL; source NULL bỏ qua; bằng nhau báo unchanged; khác nhau báo conflict và giữ đích mặc định. Chấp nhận override phải là lựa chọn cụ thể theo field/record. Trùng nhiều record cùng lượt phải gộp có kiểm soát hoặc báo mơ hồ, không last-row-wins. Không gán record thiếu identity vào ca hiện hành.

Commit kiểm lại quyền và token, khóa catalog/lượt theo thứ tự nhất quán, kiểm revision, tính lại validation/merge. Nếu catalog hoặc lượt thay đổi phải preview lại; không silently rebase. Một transaction cho tập record được chọn: mọi thay đổi + form_history + form_import_batch cùng commit; lỗi rollback toàn bộ tập đó. Không báo saved cho rejected/pending/unchanged.

Dedup duy nhất `(actor_id, content_hash)` ở form_import_batch. Hash nội dung canonical mapped values + identity; không phụ thuộc filename. Retry cùng nội dung trả kết quả batch trước, không nhân đôi ca/lượt/array/history. Hash phải gắn nội dung và quyết định đã xác nhận; mutation replay không được đổi payload. Conflict đã chọn giữ đích cần hiện skipped, không gọi đã ghi.

## PostgreSQL và phiên bản

Kế thừa PostgreSQL/pool/auth hiện có. Các bảng form_patient/form_visit hỗ trợ hồ sơ/lượt trống vì legacy patient_case yêu cầu tuổi và ràng buộc bác sĩ; legacy_case_id nullable giữ đường nối tương lai. JSONB giữ giá trị động, sources; relational FK giữ hồ sơ/lượt/actor. Không thêm cột SQL khi Admin thêm trường.

form_field + form_field_history lưu định nghĩa phiên bản; form_catalog.revision phát hiện đổi danh mục; form_visit.revision phát hiện sửa đè; form_history snapshot giữ values/sources/definitions/catalog revision/actor/time/mutation. Đổi nhãn không đổi mã; kiểu/đơn vị/ý nghĩa bị chặn khi không có chuyển đổi được định nghĩa. Ngừng dùng giữ định nghĩa/lịch sử, không xóa. AI chưa đọc tự động trường mới.

Migration 002/003 additive, không reset; chạy trong schema của ứng dụng với role owner. DOWN chỉ là chỉ dẫn có comment cho operator sau xuất dữ liệu hoặc schema test; không chạy trên dữ liệu thật trong nhiệm vụ này. FK có index (PK/UNIQUE hoặc index riêng). Query chính dùng patient_id/visit PK, không cần GIN JSONB khi chưa có query nghiệp vụ tìm nội dung JSON.

```sql
-- Query tham số hóa; kiểm quyền trước khi lấy dữ liệu.
SELECT id, revision, values_json FROM form_visit WHERE patient_id = %s;
SELECT revision, values_json, sources_json, definitions_json, created_at
FROM form_history WHERE visit_id = %s ORDER BY revision DESC;
```

## Bằng chứng S1 thực chạy (2026-10-23)

`python scripts/build_form_catalog.py <bundle.zip>`: SHA-256 và toàn bộ 8 cột của 206 dòng khớp gốc, max STT211; 70 supported.

`python scripts/form_schema_check.py --database-url <test DSN>`: offline PASS sau đổi Excel-only: 2 hàng Excel hợp lệ giữ 0/false/ô trống; 1 hàng sai kiểu bị validator từ chối; 1 hàng thiếu định danh được xác nhận trong fixture (API preview do Dev kiểm thử). PostgreSQL PASS: schema riêng s1_form_qa_20261023 tạo trong transaction rồi rollback; migration 002/003 mỗi cái chạy hai lần; 1 hồ sơ, 1 lượt, 1 history, 1 import batch; 2 vi phạm duplicate/FK bị từ chối; NULL,false,0,[],array object round-trip khớp. EXPLAIN ANALYZE Bitmap Heap Scan, 0.440ms trên bộ cực nhỏ (không là benchmark tải). Không đổi public data.

Đây là kiểm tra DDL/constraint/Excel fixture/validator/query, KHÔNG thay thế kiểm thử API import commit, concurrent requests, persistence restart hoặc UI. Dev sở hữu và báo bằng chứng runtime riêng. Chưa xác minh tương thích workbook HIS thực.

## Thay đổi phạm vi

Đã gỡ JSON Schema và fixture nhập JSON do nhiệm vụ tạo. `catalog.json`, JSONB và dữ liệu JSON nội bộ của API vẫn là chi tiết triển khai, không phải tính năng nhập JSON. Fixture Excel có nhãn giả lập và mapping tại `tests/fixtures/forms/README.md`.

Migration 003 hiện giữ CHECK nguồn cũ để không giả định trạng thái deployment; runtime chỉ được nhận Excel. Thu hẹp CHECK trên DB đã tồn tại cần migration riêng có kiểm tra lịch sử, không xóa hoặc đổi lịch sử nguồn cũ.
