# Yêu cầu → màn hình → dữ liệu

Nguồn gói: `local-data/source-bundle/Bo-prompt-dev-demo-bieu-mau-v0.2`. Nền nguồn: `local-data/prompt-v3.txt`; yêu cầu trực tiếp mới nhất bỏ chức năng nhập JSON, chỉ giữ M1/M2 Excel. Đây là UI traceability mới, không sửa RTM/SRS cũ. Trạng thái mọi dòng: **đã thiết kế**, không đồng nghĩa live implementation/test đã đạt.

| Yêu cầu | Nguồn | Màn hình / hash | Dữ liệu và quy tắc |
|---|---|---|---|
| Hai cổng, đúng quyền | M1-01/02/15; v3 D | login-admin, login-doctor; fields chỉ Admin | session server; không role dropdown |
| Hồ sơ/lượt riêng | M1-03 | patients, patient-new, visits, visit-new, form | mã chuỗi, patient_id/visit_id; context luôn rõ |
| Widget, NULL, thiếu chuyên môn | M1-04/06/07; BIEU_DIEN_TRUONG | form | scalar typed; false/0 giữ nguyên; lỗi không thành NULL |
| Lưu/mở lại/restart | M1-05/12 | form, visits | revision/server acknowledgement; UI không chứng minh persistence |
| Trường động | M1-08/09/10 | fields, field-new, field-edit | code immutable, version, choices, active; NULL cho chưa nhập |
| Xung đột/PATCH | M1-11 | form state controls | missing giữ đích, explicit null xóa có chủ ý; conflict giữ nháp |
| Lịch sử | M1-13 | history | actor/time/revision/source/before/after |
| Chưa đặc tả/AI | M1-14; v3 C/F | form pending | disabled + lý do; không fake AI |
| Excel sheet/header/mapping | M2-01/11 | excel bước 1–3 | file/sheet/header/source columns → field code |
| Null/cột thiếu/sai kiểu | M2-02/05/08 | excel bước 3–4 | vị trí nguồn, raw/normalized, status/reason; NULL không xóa |
| Nhiều ca/mã mơ hồ | M2-03/04 | excel bước 4 | mã hồ sơ/lượt chuỗi; pending không ghi |
| Bổ sung tay | M2-06 | excel bước 5 → form | cùng ca, nguồn từng phần |
| Xung đột | M2-07 | excel bước 4 | giữ đích mặc định, chọn thay rõ |
| Dedup/retry | M2-09/10 | excel bước 5 + error | fingerprint, result counters; không chỉ tên file |
| History/hồi quy | M2-12 | history, form | mapping version, sheet/row/column, actor/time |
| Responsive, keyboard, states | v3 F; PROMPT_DEV §13 | mọi màn hình | labels/focus/skip-link; mobile layout; state controls |

## Truy nguồn các ví dụ trường

| Trường hiển thị | Nguồn cụ thể | Diễn giải / giới hạn |
|---|---|---|
| Chiều cao cm | docs/extracted/TL06.txt R4 (sheet row 4) | số, để trống ban đầu |
| Cân nặng kg | TL06.txt R5 | số, không tự tính ngưỡng |
| Khó thở khi nằm | TL06.txt R8 | Có/Không/null |
| Frailty | TL06.txt R37 | thang cơ sở chưa rõ, disabled; không chọn giả |
| Ghi chú bổ sung demo | BIEU_DIEN_TRUONG mục Admin thêm định nghĩa | ví dụ kỹ thuật giả lập, không biến y khoa nguồn |
| Thuốc/kết quả lặp | BIEU_DIEN_TRUONG bảng widget; v3 F/G | cấu trúc UI đề xuất; contract Agent 1 quyết định keys hợp lệ |

Màu, kích thước, bố cục và tên component là đề xuất thiết kế của U1. Không coi những đề xuất đó là yêu cầu y khoa từ TL06. Tài liệu thiếu: workbook HIS thật và bảng mã/quy tắc còn chưa đặc tả. CHƯA CÓ NGUỒN XÁC NHẬN cho tương thích HIS thật hoặc thang Frailty cụ thể.
