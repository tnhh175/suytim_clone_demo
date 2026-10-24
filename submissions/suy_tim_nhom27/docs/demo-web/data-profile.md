# Source profile — S1

## Dữ kiện đã kiểm tra

- Workbook người dùng cấp: `20261019_Du_lieu_AI_CDSS_da_ma_hoa_20.xlsx`; một sheet `Sheet3`, 20 hàng × 42 cột, header hàng 1, 19 hàng dữ liệu. Không sao chép bản ghi vào Git/log.
- `MaNghienCuu`: 19 ô chuỗi không trống, 15 giá trị phân biệt. Có mã lặp; không thể coi mỗi hàng là bệnh nhân mới. Không có cột mã lượt rõ ràng.
- 215 ô chuỗi, 277 ô số, 106 ô datetime không trống (không tính header). Ngày Excel không có múi giờ. Không suy ra timezone hoặc định dạng HIS.
- TL06 là data dictionary, 206 dòng; không dùng làm payload bệnh nhân. Các ví dụ ZIP chỉ là giả lập.

## Giới hạn nguồn

CHƯA CÓ NGUỒN XÁC NHẬN workbook là xuất HIS, bảng mã giới tính/cờ số, đơn vị số đo, định danh lượt, quy ước NULL và nghĩa mã nghiên cứu. Creatinin_DonVi thiếu toàn bộ 19 hàng; không tự đoán đơn vị. Dữ liệu số 0 không mặc nhiên là thiếu. Năm sinh không tự đổi thành tuổi khi thiếu quy tắc ngày tham chiếu.

Google Docs là hướng tổng thể; yêu cầu mới ưu tiên M1/M2 Excel, bỏ nhập JSON và hoãn AI. Drive TL06 khác bytes nhưng đối chiếu cả 3 sheet không khác giá trị ô (bằng chứng root local-data/TL06-drive-diff.json). TL03 ZIP/Drive khác bytes nhưng nội dung đoạn văn sau nối text runs và chuẩn hóa khoảng trắng bằng nhau. Không tự thay baseline gói ZIP.

## Mapping đề xuất, chưa tự động áp dụng

- MaNghienCuu → đối chiếu mã hồ sơ sau xác nhận phạm vi định danh; một hàng được chọn rõ và xác nhận mã hồ sơ/lượt đích khi thiếu mã lượt. Không gán tất cả hàng vào ca đang mở.
- Mach→mach; NhipTho→nhip_tho; CanNang→can_nang; ChieuCao→chieu_cao chỉ sau xác nhận đơn vị. Các cột này không đủ để tự suy diễn dữ liệu thiếu.
- GioiTinh→gioi_tinh cần bảng mã được xác nhận; NamSinh không map trực tiếp tuoi. BMI là dẫn xuất, chưa nhập tự do.
- NTproBNP/Troponin/Creatinin và Na/K/Cl cần nhóm kết quả + tên + đơn vị + thời điểm; giữ cấu trúc lặp. Adapter chuyển nhóm cột thành array chưa được xác minh với workbook viện. Không dùng mapping scalar làm mất cấu trúc.
- ICD, khoa, tiền sử/dị ứng/cờ hành vi chưa có mapping đã duyệt; giữ chưa ánh xạ.

## Thống kê theo cột (không có dữ liệu bệnh nhân)

| Cột | Header | Ô trống / 19 | Kiểu có mặt |
|---|---|---|---|
| 1 | MaNghienCuu | 0 | str |
| 2 | GioiTinh | 0 | str |
| 3 | NamSinh | 0 | int |
| 4 | NgayVaoVien | 0 | datetime |
| 5 | NgayRaVien | 0 | datetime |
| 6 | KhoaRa | 0 | str |
| 7 | MaICD_VaoKhoa | 0 | str |
| 8 | TenICD_VaoKhoa | 0 | str |
| 9 | DanhSachMaICD_Phu | 0 | str |
| 10 | TienSuBanThan | 19 | — |
| 11 | DiUng | 0 | int |
| 12 | MaTuy | 0 | int |
| 13 | NgayMaTuy | 19 | — |
| 14 | RuouBia | 0 | int |
| 15 | ThuocLa | 0 | int |
| 16 | ThuocLao | 0 | int |
| 17 | TienSuKhac | 0 | int |
| 18 | Mach | 19 | — |
| 19 | NhipTho | 19 | — |
| 20 | NhietDo | 19 | — |
| 21 | CanNang | 19 | — |
| 22 | HuyetApCao | 19 | — |
| 23 | HuyetApThap | 19 | — |
| 24 | ChieuCao | 0 | int |
| 25 | BMI | 0 | int |
| 26 | NTproBNP_KetQua | 3 | float,int |
| 27 | NTproBNP_DonVi | 3 | str |
| 28 | NTproBNP_Ngay | 3 | datetime |
| 29 | Troponin_TenDichVu | 5 | str |
| 30 | Troponin_KetQua | 5 | float |
| 31 | Troponin_DonVi | 5 | str |
| 32 | Troponin_Ngay | 5 | datetime |
| 33 | Creatinin_KetQua | 0 | float,int |
| 34 | Creatinin_DonVi | 19 | — |
| 35 | Creatinin_Ngay | 0 | datetime |
| 36 | Natri_KetQua | 0 | int |
| 37 | Natri_DonVi | 0 | str |
| 38 | Kali_KetQua | 0 | float |
| 39 | Kali_DonVi | 0 | str |
| 40 | Clo_KetQua | 0 | int |
| 41 | Clo_DonVi | 0 | str |
| 42 | DienGiai_Ngay | 0 | datetime |
