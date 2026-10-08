# Ánh xạ tài liệu y khoa → dữ liệu kỹ thuật MVP

Nguồn: DATA_DICTIONARY_SUY_TIM_AI_CDSS và SUY TIM.docx (bốn module), cùng SRS FR-02–07. Đây là tập con để dựng khung tuần 3, không tuyên bố bao phủ toàn bộ 206 biến chuyên môn. Nguồn nhập dữ liệu trong file thầy cung cấp được ghi là PHÂN LOẠI ĐỀ XUẤT, vẫn cần xác nhận.

| Biến trong tài liệu | Đích kỹ thuật | Quyết định |
|---|---|---|
| tuoi / gioi_tinh | patient_case.age / sex | Mã synthetic, không lưu tên/CCCD |
| sieu_am_tim_ef | observation(code=ef) | EF tách khỏi báo cáo siêu âm; đơn vị % |
| bnp_ntprobnp | observation(code=bnp) hoặc nt_probnp | Tách hai xét nghiệm, không gộp giá trị |
| creatinin_egfr | observation(code=creatinine) hoặc egfr | Tách hai chỉ số, đơn vị riêng |
| dien_giai | observation(code=potassium); sodium mở rộng danh mục | Một dòng cho mỗi chỉ số |
| huyết áp, mạch | systolic_bp / heart_rate | Miền hợp lệ kỹ thuật, không dùng làm ngưỡng cảnh báo tự chế |
| khó thở | dyspnea | bool khi đã đánh giá; unknown/not_measured khi chưa có |
| frailty / bệnh đồng mắc | frailty / comorbidity | Dạng text synthetic trong stub; thang đo/mã hóa chính thức chờ xác nhận |
| danh_sach_thuoc | ingredient + medication | Mỗi thuốc một dòng; chưa xử lý tất cả phác đồ PRN/truyền liên tục |
| đầu ra 4 model | module_result + recommendation | Căn cứ, phiên bản và trạng thái; stub không đưa kết luận y khoa |
| bác sĩ xác nhận | clinical_decision | Do con người ghi, không phải dự đoán của AI |

Không sao chép danh mục EF/ngưỡng khác nhau từ các nguồn thành rule chạy tự động. Các cận lâm sàng dạng tệp, thang frailty, nguồn FHIR và toàn bộ danh mục đồng mắc là phần hoàn thiện sau chốt nghiệp vụ. Bảng observation_type cho phép mở rộng có kiểm soát; API enum phải cập nhật cùng catalog và OpenAPI.

API nhận `unit` rồi kiểm tra với catalog. DB lưu đơn vị chuẩn ở observation_type, không lặp lại trong observation. Nếu cần giữ đơn vị gốc/chuyển đổi, phải thêm trường nguồn và quy tắc chuyển đổi được xác nhận.
