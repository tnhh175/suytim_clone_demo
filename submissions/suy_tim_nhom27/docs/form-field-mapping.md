# Đối chiếu TL06 → biểu mẫu v0.2

Nguồn: TL06_DataDictionary.xlsx, sheet Trường dữ liệu; đã kiểm SHA-256 và tên biến với workbook gốc.
Không gộp các biến gần tên ở các module. Nhóm/widget/mã lựa chọn là thiết kế kỹ thuật, chưa là quy tắc lâm sàng được duyệt.
Số 0/false là dữ liệu; trường chưa đủ đặc tả luôn NULL. Không tính BMI/eGFR hoặc sinh đầu ra AI.

| Dòng | Biến nguồn | Nhãn | Kiểu triển khai | Đơn vị | Ghi chú |
|---|---|---|---|---|---|
| 2 | tuoi | Tuổi | integer | tuổi |  |
| 3 | gioi_tinh | Giới tính | select |  |  |
| 4 | chieu_cao | Chiều cao | number | cm |  |
| 5 | can_nang | Cân nặng | number | kg |  |
| 6 | bmi | BMI | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 7 | kho_tho_khi_gang_suc | Khó thở khi gắng sức | boolean |  |  |
| 8 | kho_tho_khi_nam | Khó thở khi nằm | boolean |  |  |
| 9 | kho_tho_kich_phat_ve_dem | Khó thở kịch phát về đêm | boolean |  |  |
| 10 | met_moi | Mệt mỏi | boolean |  |  |
| 11 | giam_kha_nang_gang_suc | Giảm khả năng gắng sức | boolean |  |  |
| 12 | phu_hai_chi_duoi | Phù hai chi dưới | boolean |  |  |
| 13 | tang_can_nhanh | Tăng cân nhanh | boolean |  |  |
| 14 | dau_nguc | Đau ngực | boolean |  |  |
| 15 | hoi_hop | Hồi hộp | boolean |  |  |
| 16 | ngat | Ngất | boolean |  |  |
| 17 | lu_lan_sang | Lú lẫn hoặc sảng | boolean |  |  |
| 18 | te_nga | Té ngã | boolean |  |  |
| 19 | chan_an | Chán ăn | boolean |  |  |
| 20 | mat_ngu | Mất ngủ | boolean |  |  |
| 21 | giam_van_dong | Giảm vận động | boolean |  |  |
| 22 | giam_kha_nang_tu_cham_soc | Giảm khả năng tự chăm sóc | boolean |  |  |
| 23 | suy_giam_chuc_nang_khong_giai_thich | Suy giảm chức năng không giải thích được | boolean |  |  |
| 24 | ha_t_the_nam_ngoi | Huyết áp khi nằm/ngồi | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 25 | ha_t_the_dung | Huyết áp khi đứng | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 26 | mach | Mạch | number | lần/phút |  |
| 27 | nhip_tho | Nhịp thở | number | lần/phút |  |
| 28 | spo2 | SpO₂ | number | % |  |
| 29 | tinh_mach_co_noi | Tĩnh mạch cổ nổi | boolean |  |  |
| 30 | phan_hoi_gan_tinh_mach_co | Phản hồi gan–tĩnh mạch cổ dương tính | boolean |  |  |
| 31 | tieng_tim_t3 | Tiếng tim T3 | boolean |  |  |
| 32 | ran_am_phoi | Ran ẩm ở phổi | boolean |  |  |
| 33 | phu_ngoai_bien | Phù ngoại biên | boolean |  |  |
| 34 | gan_to | Gan to | boolean |  |  |
| 35 | co_truong | Cổ trướng | boolean |  |  |
| 36 | giam_tuoi_mau_ngoai_vi | Dấu hiệu giảm tưới máu ngoại vi | boolean |  |  |
| 37 | frailty | Frailty | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 38 | chuc_nang_nhan_thuc | Chức năng nhận thức | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 39 | tien_su_sang | Tiền sử sảng | boolean |  |  |
| 40 | nguy_co_te_nga | Nguy cơ té ngã | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 41 | tinh_trang_dinh_duong | Tình trạng dinh dưỡng | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 42 | sarcopenia | Sarcopenia | select |  |  |
| 43 | tu_su_dung_thuoc | Khả năng tự sử dụng thuốc | select |  |  |
| 44 | benh_mach_vanh_nhoi_mau_co_tim | Bệnh mạch vành/nhồi máu cơ tim | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 45 | dai_thao_duong | Đái tháo đường | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 46 | beo_phi | Béo phì | boolean |  |  |
| 47 | benh_than_man | Bệnh thận mạn | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 48 | tien_su_hoa_tri_thuoc_doc_tim | Tiền sử hóa trị hoặc sử dụng thuốc độc với tim | boolean |  |  |
| 49 | tien_su_benh_co_tim_cau_truc | Tiền sử bệnh cơ tim hoặc bệnh tim cấu trúc | boolean |  |  |
| 50 | tang_huyet_ap_nguyen_nhan | Tăng huyết áp | boolean |  |  |
| 51 | benh_van_tim | Bệnh van tim | boolean |  |  |
| 52 | rung_nhi_roi_loan_nhip | Rung nhĩ hoặc rối loạn nhịp khác | boolean |  |  |
| 53 | benh_co_tim | Bệnh cơ tim | boolean |  |  |
| 54 | amyloidosis_tim | Amyloidosis tim | boolean |  |  |
| 55 | viem_co_tim | Viêm cơ tim | boolean |  |  |
| 56 | thuoc_doc_chat | Thuốc hoặc độc chất | boolean |  |  |
| 57 | takotsubo | Takotsubo | boolean |  |  |
| 58 | benh_noi_tiet_chuyen_hoa | Bệnh nội tiết–chuyển hóa | boolean |  |  |
| 59 | suy_tim_cung_luong_cao | Suy tim cung lượng cao | boolean |  |  |
| 60 | copd | COPD | boolean |  |  |
| 61 | thieu_mau | Thiếu máu | boolean |  |  |
| 62 | benh_gan | Bệnh gan | boolean |  |  |
| 63 | roi_loan_tuyen_giap | Rối loạn tuyến giáp | boolean |  |  |
| 64 | sa_sut_tri_tue | Sa sút trí tuệ | boolean |  |  |
| 65 | tram_cam | Trầm cảm | boolean |  |  |
| 66 | benh_mach_mau_nao | Bệnh mạch máu não | boolean |  |  |
| 67 | ung_thu | Ung thư | boolean |  |  |
| 68 | danh_sach_thuoc | Danh sách thuốc hiện tại | medications |  |  |
| 69 | da_thuoc | Tình trạng đa thuốc | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 70 | ecg_12_chuyen_dao | ECG 12 chuyển đạo | textarea |  | Chỉ lưu báo cáo bằng chữ; chưa nhận tệp đính kèm. |
| 71 | bnp_ntprobnp | BNP/NT-proBNP | results |  |  |
| 72 | troponin | Troponin | results |  |  |
| 73 | sieu_am_tim_ef | Siêu âm tim và EF | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 74 | xquang_tim_phoi | X-quang tim phổi | textarea |  | Chỉ lưu báo cáo bằng chữ; chưa nhận tệp đính kèm. |
| 75 | creatinin_egfr | Creatinin/eGFR | results |  |  |
| 76 | dien_giai | Điện giải đồ | results |  |  |
| 77 | thay_doi_trieu_chung | Thay đổi triệu chứng | select |  |  |
| 78 | thay_doi_can_nang | Thay đổi cân nặng | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 79 | thay_doi_nyha | Thay đổi NYHA | select |  |  |
| 80 | thay_doi_bnp_ntprobnp | Thay đổi BNP/NT-proBNP và EF | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 81 | so_lan_cap_cuu_nhap_vien | Số lần cấp cứu/nhập viện | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 82 | nhu_cau_tang_lieu_loi_tieu | Nhu cầu tăng liều lợi tiểu | boolean |  |  |
| 83 | nguoi_cham_soc | Người chăm sóc | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 84 | kha_nang_chi_tra | Khả năng chi trả | select |  |  |
| 85 | kha_nang_tai_kham | Khả năng tái khám | select |  |  |
| 86 | kha_nang_mua_su_dung_thuoc | Khả năng mua và sử dụng thuốc | select |  |  |
| 87 | khoang_cach_co_so_y_te | Khoảng cách đến cơ sở y tế | unavailable |  | Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính. |
| 88 | ho_tro_gia_dinh | Mức độ hỗ trợ của gia đình | select |  |  |
| 89 | xac_suat_suy_tim | Ước tính khả năng mắc suy tim | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 90 | kieu_hinh_ef | Phân loại kiểu hình | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 91 | benh_canh_suy_tim | Phân loại bệnh cảnh | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 92 | xep_hang_nguyen_nhan | Xếp hạng nguyên nhân suy tim có khả năng nhất | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 93 | canh_bao_gia_suy_tim | Cảnh báo khả năng mắc bệnh giả suy tim | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 94 | frailty_dung_nap_dieu_tri | Phân loại frailty và khả năng dung nạp điều trị | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 95 | du_bao_nhap_vien_tai_nhap_vien | Dự báo nguy cơ nhập viện/tái nhập viện | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 96 | du_bao_tu_vong | Dự báo nguy cơ tử vong | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 97 | du_bao_te_nga | Dự báo nguy cơ té ngã | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 98 | du_bao_sang | Dự báo nguy cơ sảng | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 99 | du_bao_suy_giam_chuc_nang | Dự báo nguy cơ suy giảm chức năng | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 100 | du_bao_mat_tu_cham_soc | Dự báo nguy cơ mất khả năng tự chăm sóc | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 101 | canh_bao_cap_cuu | Cảnh báo cấp cứu | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 102 | giai_doan_suy_tim_ai | Giai đoạn suy tim từ AI Diagnosis | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 103 | kieu_hinh_nghi_ngo_ai | Kiểu hình nghi ngờ | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 104 | benh_canh_ai | Bệnh cảnh | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 105 | nguyen_nhan_nghi_ngo_ai | Nguyên nhân nghi ngờ | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 106 | benh_gia_suy_tim_can_loai_tru | Bệnh giả suy tim cần loại trừ | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 107 | trieu_chung_dau_hieu | Triệu chứng và dấu hiệu lâm sàng | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 108 | frailty_hop_tac_xet_nghiem | Frailty, nhận thức và khả năng hợp tác thực hiện xét nghiệm | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 109 | xet_nghiem_da_co | Kết quả xét nghiệm đã có và thời điểm thực hiện | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 110 | chuc_nang_than_gan_dien_giai | Chức năng thận, gan và tình trạng điện giải | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 111 | benh_dong_mac_lab | Bệnh đồng mắc | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 112 | thuoc_dang_su_dung_lab | Thuốc đang sử dụng | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 113 | di_ung_thuoc_can_quang | Dị ứng thuốc cản quang | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 114 | thiet_bi_cay_ghep | Thiết bị cấy ghép và chống chỉ định MRI | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 115 | kha_nang_gang_suc_tham_do | Khả năng chịu đựng nghiệm pháp gắng sức hoặc thăm dò xâm lấn | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 116 | muc_tieu_kha_nang_xet_nghiem | Mục tiêu điều trị, khả năng chi trả và khả năng thực hiện xét nghiệm | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 117 | goi_y_bnp_ntprobnp | BNP hoặc NT-proBNP | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 118 | goi_y_ecg | ECG 12 chuyển đạo | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 119 | goi_y_sieu_am_tim | Siêu âm tim | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 120 | goi_y_xquang_tim_phoi | X-quang tim phổi | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 121 | goi_y_cong_thuc_mau | Công thức máu | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 122 | goi_y_ure_creatinin_egfr | Urê, creatinin, eGFR | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 123 | goi_y_kali_natri | Kali, natri | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 124 | goi_y_chuc_nang_gan | Chức năng gan | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 125 | goi_y_duong_huyet_hba1c | Đường huyết/HbA1c | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 126 | goi_y_tsh | TSH | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 127 | goi_y_ferritin_tsat | Ferritin và TSAT | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 128 | goi_y_uacr | UACR | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 129 | goi_y_danh_gia_mach_vanh | Đánh giá bệnh mạch vành | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 130 | goi_y_doppler_van_tim | Siêu âm Doppler bệnh van tim | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 131 | goi_y_holter_ecg | Holter ECG | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 132 | goi_y_mri_tim | MRI tim | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 133 | goi_y_xet_nghiem_amyloidosis | Xét nghiệm amyloidosis | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 134 | goi_y_danh_gia_benh_co_tim | Đánh giá bệnh cơ tim | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 135 | goi_y_suy_tim_cung_luong_cao | Xét nghiệm nguyên nhân suy tim cung lượng cao | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 136 | goi_y_danh_gia_benh_than | Đánh giá bệnh thận | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 137 | goi_y_danh_gia_benh_phoi | Đánh giá bệnh phổi | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 138 | goi_y_danh_gia_thieu_mau | Đánh giá thiếu máu | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 139 | goi_y_dinh_duong | Đánh giá suy dinh dưỡng | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 140 | goi_y_tuyen_giap | Đánh giá tuyến giáp | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 141 | goi_y_gang_suc_tham_do_huyet_dong | Nghiệm pháp gắng sức hoặc thăm dò huyết động khi cần | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 142 | phan_loai_ket_qua_xet_nghiem | Phân loại kết quả | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 143 | muc_uu_tien_xet_nghiem | Xếp mức ưu tiên | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 144 | danh_gia_loi_ich_nguy_co_xet_nghiem | Đánh giá lợi ích–nguy cơ của xét nghiệm | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 145 | canh_bao_khong_chi_dinh_xam_lan_theo_tuoi | Cảnh báo chỉ định xét nghiệm xâm lấn | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 146 | stage_suy_tim | Giai đoạn suy tim A–D | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 147 | ef_treatment | Kiểu hình EF | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 148 | nguyen_nhan_treatment | Nguyên nhân suy tim | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 149 | nyha | NYHA | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 150 | worsening_decompensated | Tình trạng worsening hoặc decompensated | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 151 | sung_huyet_tuoi_mau | Dấu hiệu sung huyết và tưới máu | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 152 | ha_treatment | Huyết áp | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 153 | mach_treatment | Mạch | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 154 | spo2_treatment | SpO₂ | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 155 | ef_hien_tai | EF hiện tại và EF trước đây | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 156 | bnp_treatment | BNP/NT-proBNP | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 157 | creatinin_egfr_treatment | Creatinin/eGFR | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 158 | kali_natri_gan | Kali, natri và chức năng gan | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 159 | thuoc_lieu_tuan_thu | Thuốc đang sử dụng, liều và mức độ tuân thủ | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 160 | khong_dung_nap_thuoc | Tiền sử không dung nạp thuốc | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 161 | benh_dong_mac_treatment | Bệnh đồng mắc | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 162 | frailty_treatment | Frailty | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 163 | nhan_thuc_treatment | Chức năng nhận thức | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 164 | adl_iadl_treatment | ADL/IADL | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 165 | nguy_co_te_nga_hha | Nguy cơ té ngã và hạ huyết áp tư thế | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 166 | dinh_duong_sarcopenia | Tình trạng dinh dưỡng và sarcopenia | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 167 | tu_quan_ly_thuoc | Khả năng tự quản lý thuốc hoặc hỗ trợ người chăm sóc | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 168 | muc_tieu_dieu_tri | Mục tiêu điều trị | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 169 | dieu_tri_stage_a | Điều trị Stage A | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 170 | dieu_tri_stage_b | Điều trị Stage B | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 171 | dieu_tri_stage_c | Điều trị Stage C | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 172 | ca_the_hoa_nguoi_cao_tuoi | Cá thể hóa theo người cao tuổi | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 173 | xu_tri_worsening_hf | Xử trí Worsening HF | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 174 | xu_tri_decompensated_hf | Xử trí Decompensated HF | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 175 | dieu_tri_stage_d | Điều trị Stage D | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 176 | ke_hoach_theo_doi | Kế hoạch theo dõi | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 177 | don_thuoc_moi | Đơn thuốc mới và toàn bộ thuốc đang sử dụng | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 178 | thuoc_otc_tpcn_yhct | Thuốc không kê đơn, thực phẩm chức năng và thuốc y học cổ truyền | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 179 | so_luong_thuoc_dong_thoi | Số lượng thuốc sử dụng đồng thời | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 180 | di_ung_phan_ung_co_hai | Dị ứng và phản ứng có hại | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 181 | creatinin_egfr_medsafety | Creatinin/eGFR | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 182 | kali_natri_dien_giai_medsafety | Kali, natri và các điện giải khác | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 183 | chuc_nang_gan_medsafety | Chức năng gan | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 184 | ha_nam_ngoi_dung | Huyết áp khi nằm/ngồi và khi đứng | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 185 | nhip_tim_ecg | Nhịp tim và ECG | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 186 | frailty_medsafety | Frailty | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 187 | nhan_thuc_tien_su_sang | Nhận thức và tiền sử sảng | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 188 | tien_su_te_nga_ngat | Tiền sử té ngã hoặc ngất | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 189 | kha_nang_nuot_tu_dung_thuoc | Khả năng nuốt và tự sử dụng thuốc | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 190 | dinh_duong_can_nang_sarcopenia | Tình trạng dinh dưỡng, cân nặng và sarcopenia | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 191 | ho_tro_nguoi_cham_soc_medsafety | Khả năng hỗ trợ của người chăm sóc | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 192 | chi_tra_tai_kham_medsafety | Khả năng chi trả và tái khám | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 193 | phat_hien_da_thuoc | Phát hiện đa thuốc và trùng lặp điều trị | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 194 | tuong_tac_thuoc_thuoc | Tương tác thuốc–thuốc | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 195 | tuong_tac_thuoc_benh | Tương tác thuốc–bệnh | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 196 | chong_chi_dinh | Chống chỉ định | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 197 | sai_lieu | Sai liều | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 198 | thuoc_khong_con_chi_dinh | Thuốc không còn chỉ định rõ ràng | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 199 | khuyen_nghi_chinh_lieu | Khuyến nghị chỉnh liều | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 200 | canh_bao_nguy_co | Cảnh báo nguy cơ | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 201 | thuoc_lam_nang_suy_tim | Cảnh báo thuốc làm nặng suy tim | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 202 | thuoc_suy_tim_dac_hieu | Cảnh báo đặc hiệu với thuốc suy tim | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 203 | don_gian_hoa_phac_do | Đề xuất đơn giản hóa phác đồ | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 204 | giam_ngung_thuoc | Đề xuất xem xét giảm/ngừng thuốc | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 205 | ke_hoach_xet_nghiem_theo_doi | Kế hoạch xét nghiệm và thời điểm theo dõi | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 206 | phan_tang_canh_bao | Phân tầng cảnh báo | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
| 207 | xac_nhan_bac_si | Xác nhận quyết định của bác sĩ | unavailable |  | Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI. |
