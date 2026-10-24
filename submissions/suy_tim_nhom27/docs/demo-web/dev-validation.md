# Bằng chứng kiểm thử Dev M1/M2

Ngày 24/10/2026, repo `D:\1.TNHH\project\suytim_clone_demo`, branch `codex/demo-web`, base HEAD `bc90dbdde2dc7313f2d147029a701f2fcf1f8f2d`. Các thay đổi chưa commit/push. Đây là kết quả Dev; kết quả UI độc lập của điều phối/Tester được ghi riêng, không thay thế bằng ảnh hoặc suy ra từ test API.

## Môi trường

Windows, Python 3.13, `.venv` của submission, FastAPI/PostgreSQL; API dùng chính pool và `SET LOCAL ROLE hf_demo_owner`. Test ghi chạy trong schema `d3_form_qa_20261023`; live dùng `d3_form_live_20261024`, cùng database `hf_demo` và tài khoản runtime. Không reset/public data; dữ liệu thử và account đều giả lập. Credential/log/runtime state ở ignored `local-data`, không in password/token vào báo cáo.

## Kết quả thực chạy

- Full suite với `PYTHONPATH=src`, `FORM_TEST_DSN` có search_path QA, `FORM_TEST_CREDENTIALS`: **84 passed, 4 skipped**, một cảnh báo Starlette/httpx deprecation. Log: `.context-shears/artifacts/command-20261024T051955.864123Z-23456526c830.log` (trong submission).
- Sau bổ sung ca hai lượt không mã ngoài: `pytest tests/test_forms_imports.py -q`: **14 passed**, log `.context-shears/artifacts/command-20261024T052131.252129Z-fa40dba925d5.log`. Full suite cuối sẽ cập nhật bên dưới nếu có thay đổi.
- Full suite cuối sau sửa đối chiếu UUID lượt không mã ngoài: **85 passed, 4 skipped, 1 warning trong 9.88 giây**. Log `.context-shears/artifacts/command-20261024T052355.907383Z-3bf45e905449.log`. Các sửa tiếp theo chỉ là thông điệp replay và launcher nền; `node --check` và health được kiểm lại.
- `node --check web/forms.js`, Python compileall và export OpenAPI đã chạy thành công. OpenAPI được sinh từ runtime, giữ các API cũ và thêm biểu mẫu/Excel; không có JSON import endpoint/template.
- Restart tiến trình thật: dừng listener PID 33452, khởi động lại nền Windows; listener mới PID 28620. Đọc API trước/sau `SYN-FORM-001`/`VISIT-001-1` giữ **revision 4, history 4**, SHA-256 của id/revision/values/sources khớp chính xác; `/health` HTTP 200, persistence postgres. Đây là kiểm tra qua hai tiến trình khác nhau, không chỉ tạo lại app trong TestClient. Digest nằm riêng `local-data/form-restart-check.json`.
- Sau interruption môi trường thu hồi tiến trình con, Dev phục hồi bằng `pythonw.exe` qua Windows WMI, không có cửa sổ console và không thuộc job của lệnh kiểm thử. Listener PID 20904; `/health` HTTP 200 sau khi launcher hoàn tất. Config riêng `local-data/forms-live-runtime.json`, log cùng tên `.log`. PID là bằng chứng tại lúc kiểm, không là hằng số để dừng ở lần sau.

Lần full suite đầu thiếu `PYTHONPATH=src` làm legacy test không import được `gateway`; đã sửa lệnh. Lần tiếp theo có hai lỗi hồi quy: notice giả lập trong trang mới và OpenAPI snapshot chưa cập nhật. Trang loading notice và export contract đã sửa, full suite sau đó qua. Không sửa test cũ để bỏ qua lỗi.

## Ca Dev và tiêu chí được kiểm

| Nhóm | Bằng chứng tự động thực chạy | Tiêu chí |
|---|---|---|
| Xác thực/quyền | Hai endpoint cổng cố định; sai cổng 401; role client lạ 422; chưa login 401; Bác sĩ tạo/sửa định nghĩa 403; Admin không tự xem hồ sơ riêng của bác sĩ | M1-01/02/15 |
| Hồ sơ/lượt | Tạo hai hồ sơ, mỗi hồ sơ hai lượt; save một lượt không đổi lượt kia; scope owner và explicit access | M1-03 |
| Kiểu/NULL | Giữ 0/false/null; trường thiếu PATCH giữ nguyên; xóa chủ ý; sai số/boolean/choice/unknown field bị 422, revision không tăng | M1-04/06/07/11 |
| Trường động | Tạo qua API Admin, mã trùng 409, ca cũ field mới NULL, save/read, đổi nhãn giữ value/history, đổi type/unit 422, retire giữ lịch sử và chặn nhập mới | M1-08/09/10 |
| Lưu/history | Mutation UUID replay cùng nội dung, đổi payload cùng UUID 409; concurrent hai request chỉ một 200/một 409; catalog stale 409; snapshot actor/source/definition và recreate app persistence | M1-05/11/12/13 |
| Excel preview | Inspect/preview/cancel không đổi count của patient/visit/history/batch; dimensionless sheet, header/cột đầu trống, empty sheet không crash; vị trí sheet/ô đúng | M2-01/02/05 |
| Identity | Nhiều ca đúng mã; giữ định danh chuỗi số 0 đầu; numeric IDs giữ lỗi; không khớp pending; hai dòng cùng identity bị lỗi; một dòng explicit UUID không đổ cả file vào ca | M2-03/04 |
| Không mã lượt | Hai lượt cùng hồ sơ đều external_id NULL: explicit UUID ghi đúng lượt được chọn, lượt còn lại nguyên; chọn lượt thứ hai không bị dedup nhầm | M2-01/04 |
| Merge/provenance | Source NULL không xóa; conflict giữ đích mặc định; override cụ thể; nhập Excel rồi bổ sung manual giữ nguồn riêng; field/actor/ô nguồn/history đúng | M2-06/07/08/12 |
| Retry/transaction | Rename file replay, không thêm history/batch; hai concurrent commit một ghi/một replay; stale visit 409; token tamper 409; revoke scope sau commit làm replay 404 | M2-09/10 |
| Rollback | Tiêm lỗi ở persist bản ghi thứ hai, transaction rollback cả lượt thứ nhất/history/batch; bỏ lỗi rồi retry ghi đúng hai lượt | M2-10 |
| Field động Excel | Admin tạo text field, ánh xạ cột, preview/commit/read value; source không tự tạo field | M2-11 |

Các test mới ở `tests/test_forms_api.py` và `tests/test_forms_imports.py`. Bốn legacy test bị skip vì gate riêng; không tính là đã kiểm DB lâm sàng cũ. Cảnh báo httpx không làm test thất bại.

## Giới hạn bằng chứng

M1-08 tạo trường qua UI, M2-01 thao tác wizard thật, bố cục/keyboard/mobile và các trạng thái hiển thị phải đối chiếu báo cáo UI của điều phối/Tester. Dev API/DB không tự chứng minh chất lượng tương tác. M1-14: code/UI giữ vùng chưa đặc tả và không gọi module AI, cần UI review độc lập; không có kết quả AI để kiểm độ chính xác.

HIS thật, cấu trúc Excel lặp thuốc/kết quả chưa xác minh: parser chặn có giải thích, form nhập tay vẫn giữ cấu trúc. Không benchmark tải, kiểm toàn diện accessibility hoặc chứng nhận bảo mật/khả dụng lâm sàng. Preview ký bằng secret mỗi process, hết hạn sau 1.800 giây; restart yêu cầu preview lại. Không đưa dữ liệu thật hoặc secret lên Git.
