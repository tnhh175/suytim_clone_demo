# Hợp đồng dữ liệu đợt sửa 25/10/2026

Căn cứ: `Yeu-cau-sua-demo` v1.0 đã duyệt; TL06 trong `docs/sources/TL06_DataDictionary.xlsx` và bản catalog có SHA256, sheet, hàng nguồn. Đây là hợp đồng triển khai hiện tại, không phải kết luận chuyên môn hoặc xác nhận tương thích HIS thật.

## Quyền và danh tính

- Admin đọc mọi hồ sơ/lượt/giá trị trong schema sandbox đang cấu hình; sửa hành chính có lịch sử; thêm/sửa định nghĩa trường. Admin không tạo hồ sơ/lượt, sửa giá trị khám hoặc xem trước/xác nhận nhập file.
- Bác sĩ giữ giới hạn chủ sở hữu hoặc `form_access`. Dùng chung hồ sơ không mở quyền đọc hồ sơ của bác sĩ khác.
- `POST /api/forms/patients`: `{id, display_name?, date_of_birth?, sex?, insurance_number?, external_id?}`. Không nhận `code`; cấp tuần tự `BN-00001` đến `BN-99999`, không quay vòng. Hết phạm vi trả 409, cần đặc tả mở rộng.
- Tên mặc định `Người bệnh giả lập xxxxx`; tên nhập cũng phải thuộc dạng giả lập. Ngày sinh ISO, giới tính `male|female|other|null`, BHYT chuỗi giữ số 0 đầu. Không suy ra ngày sinh từ tuổi.
- Mã UUID và liên kết không đổi khi chuyển mã. `form_patient_alias` giữ mã hiển thị cũ và mã nguồn cũ khi sửa hành chính. Mã nguồn mới không được trùng mã/alias của người khác.
- Import đối chiếu mã BN hoặc external_id hoặc alias, phải chỉ ra đúng một người trước khi lọc quyền, rồi đối chiếu mã lượt thuộc người đó. Xung đột danh tính bị chặn; không đối chiếu tên.

## Hành chính và thông tin lượt

`PATCH /api/forms/patients/{id}` nhận `expected_revision` (giá trị `demographic_revision`), `mutation_id` và các trường hành chính cần sửa. `GET /patients/{id}/history` trả lịch sử giảm dần gồm `before_json`, `after_json`, người sửa, thời điểm. Tên không được xóa. Mỗi lần sửa tăng revision; retry cùng mutation và nội dung không ghi thêm.

`POST /patients/{id}/visits` nhận `id`, `external_id?`, `occurred_at?`, `metadata?`. Metadata gồm:

| Khóa | Kiểu/nghĩa |
|---|---|
| primary_diagnosis_code | Chuỗi hoặc NULL, không tự gán ICD |
| secondary_diagnosis_codes | NULL khi chưa biết; danh sách mã riêng không trùng; [] khi chủ động ghi không có |
| reason, hpi | Lý do khám, bệnh sử/diễn biến ngắn |
| visit_type | `new`, `followup` hoặc NULL |
| examining_doctor, department | Bác sĩ khám và khoa/phòng; không đồng nhất với người nhập |
| admitted_at, ended_at | Thời điểm có múi giờ; kết thúc không trước tiếp nhận |
| allergy_status | `unknown`, `none`, `known` hoặc NULL |
| allergy_details | Chi tiết khi ghi nhận dị ứng; không đi kèm trạng thái không có/chưa biết |

`PATCH /visits/{id}` giữ envelope `expected_revision`, `catalog_revision`, `mutation_id`, `values` và bổ sung `metadata` (patch từng khóa), `occurred_at` (nếu gửi). Cùng một lần lưu và lịch sử ghi giá trị, nguồn, metadata và thời điểm khám. NULL của thao tác sửa tay là xóa có chủ đích; NULL của import là bỏ qua.

`GET /visits/{id}` có `fields` theo snapshot, `catalog_revision`, `metadata` (cùng nội dung `metadata_json`), `demographics_snapshot`, `age_at_visit`, `snapshot_origin`. Tuổi đủ năm tính từ ngày sinh snapshot tại ngày khám theo lịch Việt Nam (`Asia/Ho_Chi_Minh`); thiếu một trong hai trả NULL. Tạo/sửa thời điểm khám trước ngày sinh đã biết bị từ chối. Lượt mới không sao chép giá trị khám/thuốc từ lượt trước. Hành chính được chụp riêng nên sửa giới tính/ngày sinh hiện tại không thay lịch sử lượt cũ.

`GET /patients/{id}/overview` trả `{patient, latest_visit, visits, summary_visits}`. Lượt sắp `occurred_at DESC NULLS LAST`, rồi thời điểm tạo; không dùng thời điểm sửa làm thời điểm khám. `latest_visit` chỉ chọn lượt có ngày khám. `summary_visits.disease`, `.medications`, `.allergy` chọn riêng lượt có ngày và có thông tin tương ứng; một lượt trống mới không che thông tin cũ đã biết. Mỗi khối phải ghi riêng nguồn ngày và phân biệt danh sách thuốc đã ghi nhận với xác nhận đang dùng hôm nay.

## Snapshot biểu mẫu và migration 004

Mỗi lượt mới, kể cả trống, chụp toàn bộ định nghĩa và revision ngay khi tạo, trong transaction khóa chia sẻ catalog. Đổi toàn cục tạo revision/field history mới, chỉ dùng cho lượt tạo sau. Đọc, sửa tay, preview và commit Excel dùng định nghĩa đã ghim của từng lượt. Thay đổi toàn cục sau preview không vô hiệu hóa lượt đang dùng snapshot cũ. Kiểm tra revision giá trị vẫn chống ghi đè đồng thời.

Không có thao tác tự nâng mẫu cũ. Đổi kiểu/đơn vị trong PATCH định nghĩa vẫn bị từ chối vì chưa có quy tắc chuyển đổi. Không xóa vật lý trường đã có dữ liệu.

Lượt trước migration chưa từng chụp đầy đủ phiên bản lúc tạo. Không thể khôi phục chính xác dữ liệu chưa được ghi:

- Có lịch sử: ghim **snapshot lần lưu cuối**, vì nó mô tả các giá trị hiện có, gồm trường được thêm và đã lưu sau lần lưu đầu. `snapshot_origin=migration_004_last_saved_catalog`.
- Chưa có lịch sử: ghim danh mục tại thời điểm migration, `snapshot_origin=migration_004_current_catalog`.
- Lịch sử cũ giữ nguyên definitions/values/sources/revision. Không tuyên bố baseline chuyển đổi là phiên bản lúc tạo ban đầu.

Migration chỉ chạy với current_schema khớp `d3_form_`, thêm cột/bảng/index/sequence, đổi mã tại chỗ và lưu alias. Dừng app khi triển khai để khóa đổi mã ngắn. Re-run không cấp lại mã/đổi snapshot đã chốt. Rollback phải giữ history/aliases và đối chiếu bản backup ở sandbox mới; không cung cấp DROP tự động gây mất lịch sử.

## Kiểm tra dữ liệu và A05

- Tuổi nguyên 0–120 theo TL06 hàng 2 (`0–120 tuổi`), từ chối 150.
- Cân nặng/chiều cao số hữu hạn và không âm; từ chối -1, không dựng cận trên “bình thường”. Số 0 vẫn giữ khác NULL và False.
- Chuỗi chỉ gồm khoảng trắng được chuẩn hóa NULL trong giá trị biểu mẫu; ngày chỉ nhận ISO thực; datetime phải có múi giờ.
- `constraints` được trả về cho frontend; máy chủ áp dụng cả manual và Excel. Các kiểm tra lỗi nguồn/không âm vẫn áp dụng khi sửa mẫu cũ, không đổi nhãn/kiểu/đơn vị/lựa chọn cũ.
- TL06 hàng 45/47 cho biết tình trạng đái tháo đường/bệnh thận mạn Có/Không, còn HbA1c/eGFR chưa rõ. Hai boolean được mở cho **catalog mới** sau khi ghim lượt cũ; không suy ra chẩn đoán/xét nghiệm và không mở thành phần thiếu đặc tả.

## Import và preset

File XLSX phải có cột định danh hồ sơ và lượt. `explicit_target` không thể thay cặp mã bị thiếu. Mã chuỗi giữ số 0; số hoặc công thức ở ô định danh bị chặn. Không tạo hồ sơ/lượt khi nhập. Giá trị mới được đối chiếu trước–sau, xung đột cần chọn ghi đè từng trường. Lặp cùng nội dung được replay bằng batch durable; quyền hiện tại vẫn kiểm tra.

`GET /api/forms/imports/presets` trả cấu hình của bác sĩ đăng nhập. `POST /presets` nhận `{id,name,source_name,mapping:{sheet,header_row,patient_column,visit_column,columns:[{column,target,unit_confirmed,conversion}]}}`. Cấu hình không chứa tệp/giá trị bệnh nhân, có revision và thời điểm. Lưu tên mới cho phiên bản mới; retry cùng ID/nội dung trả cùng cấu hình. Đơn vị phải được xác nhận, không tự chuyển đổi.

Nguồn `DATA` đang có chưa có mã lượt nên không đủ điều kiện nhập trực tiếp. Danh sách nhiều thuốc/kết quả Excel vẫn chặn cho đến khi cấu trúc nguồn đã được đối chiếu; biểu mẫu có cấu trúc vẫn dùng được. Mẫu tải về ghi rõ giả lập, không phải bằng chứng tương thích HIS bệnh viện.

## Kiểm chứng backend

Chỉ chạy với `d3_form_qa_20261023`; không test ghi vào live/public. Bộ `test_forms_api.py` và `test_forms_imports.py`: 30 passed, 11.07 giây (25/10/2026 UTC), log `.context-shears/artifacts/command-20261025T173334.612570Z-037237ba06e4.log`. Kiểm tra migration initial/replay giữ 178 hồ sơ, 200 lượt, 135 lịch sử, 60 batch và nội dung cũ ngoài mã hiển thị. Thêm 6 unit tests qua cho ngày sinh/ranh giới múi giờ, NULL/danh sách rỗng và giới hạn nguồn; `form_schema_check.py` offline qua với 206 trường, 72 trường có kiểu hỗ trợ sau A05. Kiểm thử chấp nhận độc lập và kiểm tra migration cuối sau điều chỉnh baseline do QA/root ghi ở báo cáo riêng.
