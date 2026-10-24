# Danh mục nguồn demo web

Kiểm tra trực tiếp ngày 23/10/2026. Dữ liệu riêng tư và bản tải nguồn giữ ngoài Git trong `local-data/`; không coi tên file là chứng minh nguồn HIS.

Yêu cầu trực tiếp sau prompt v3 đã bỏ nhập JSON và gỡ ràng buộc riêng cho các agent để dùng quy tắc skill. Phạm vi hiện hành: M1 nhập tay và M2 Excel. Những nội dung v3/nguồn nói M3 chỉ còn là lịch sử yêu cầu, không phải chức năng cần triển khai.

| ID | Nguồn | Trạng thái đọc | Vai trò |
|---|---|---|---|
| U3 | Prompt v3 người dùng dán | Đã đọc toàn bộ | Yêu cầu sản phẩm ban đầu; các điều chỉnh trực tiếp sau đó bỏ M3 và thay ràng buộc agent bằng skill |
| Z0 | Bo-prompt-dev-demo-bieu-mau-v0.2.zip | Đã đọc README → PHAM_VI → PROMPT_DEV → BIEU_DIEN | Phạm vi M1/M2 và tiêu chí chi tiết |
| TL01 | Hướng dẫn Bộ Y tế trong ZIP | Tra cứu khi cần; không triển khai logic y khoa | Tài liệu nguồn, không suy ra ngưỡng/công thức ngoài yêu cầu |
| TL02 | Quy trình Hữu Nghị trong ZIP | Agent Schema đối chiếu phần liên quan | Không giới hạn toàn hệ thống ở người cao tuổi |
| TL03 | SUY_TIM trong ZIP, kèm bản Drive | Đã so sánh Word text; xem conflict-log | Đầu vào/đầu ra module; module chưa triển khai |
| TL04 | Schema năm bệnh trong ZIP | Agent Schema đối chiếu phần liên quan | Tham khảo cấu trúc, không ép đổi nền repo |
| TL05 | Bảng biến năm bệnh trong ZIP | Agent Schema đối chiếu phần liên quan | Tham khảo, không tự gộp biến |
| TL06 | DataDictionary.xlsx trong ZIP | Đã kiểm SHA-256 và đối chiếu tên biến workbook gốc | 206 dòng định nghĩa, không là dữ liệu bệnh nhân |
| REF | data-reference/TL06_fields_source.json | Đọc và đối chiếu TL06 | Bản trích tra cứu, không phải payload bệnh nhân |
| EX | examples/*.json trong ZIP | Ví dụ kỹ thuật | Không là schema HIS đã xác nhận |
| GD | [Google Docs định hướng](https://docs.google.com/document/d/1BRNTjQUJJ8KK-5-J2xCGmRduIgGWC2-G30pbBiJE1aM/edit?tab=t.ob68kbl3zufi) | Browser truy cập và export Markdown, đọc đủ 8 mục | Hướng dài hạn; ưu tiên sau v3 và PHAM_VI/PROMPT_DEV |
| GF | [Thư mục SUYTIM 27](https://drive.google.com/drive/folders/15qbmJ90UbdevQXgwtNeSD_r1R0-xUczK) | Browser đọc danh mục 7 tệp; tải TL03/TL06 để so sánh | Bổ sung xác minh nguồn; không thay baseline âm thầm |
| DATA | 20261019_Du_lieu_AI_CDSS_da_ma_hoa_20.xlsx | Đã khảo sát workbook local; metadata trong data-profile | Mẫu dữ liệu đã cấp; nguồn xuất HIS: CHƯA CÓ NGUỒN XÁC NHẬN |

## Dữ kiện từ nguồn

- Workbook đính kèm có sheet `Sheet3`, 20 hàng gồm tiêu đề, 42 cột; 19 hàng dữ liệu. Có `MaNghienCuu`; chưa thấy cột mã lượt rõ ràng.
- TL06 ZIP SHA-256: `b7c5fe2d8f276cc7d94d3161a219edd7f4c29383bd8af1acde84042460122e19`.
- TL06 Drive SHA-256: `a7429f3f5243e1f03858eeaf9f0cca95d4ca296f67cb4a4f946bb11e2b070ccc`. So sánh toàn bộ giá trị ô bằng openpyxl với `data_only=False`: ba sheet `Trường dữ liệu`, `Danh mục`, `Ghi chú`, không có hàng khác nhau.
- Drive liệt kê cùng tên workbook dữ liệu đã cấp; chưa so sánh byte workbook Drive với bản local, không tuyên bố chúng đồng nhất.
- Google Docs vẫn mô tả nguồn từ web năm bệnh, bốn module AI và app bệnh nhân ở hướng tổng thể. Đây không phải quyết định thay thế phạm vi demo v3.

## Diễn giải áp dụng

Nhập tay và Excel dùng chung dữ liệu hồ sơ/lượt và validation. Với Excel thiếu mã lượt, chọn một dòng và đối chiếu lượt đích rõ ràng. Không khớp theo tên gần giống hoặc ngày vào viện. Số lượng 206 dòng TL06 không đồng nghĩa 206 widget có thể nhập.

## Đề xuất kỹ thuật

Contract, widget, mapping và fixture của nhóm là thiết kế kiểm chứng cho demo; không được gọi là định dạng HIS hoặc schema lâm sàng đã duyệt. Nguồn thực chưa rõ đơn vị/bảng mã/thời điểm được đánh dấu cần xác nhận trong mapping.
