# Ánh xạ tài liệu y khoa → dữ liệu kỹ thuật MVP

Nguồn: SRS hiện tại FR-01..34 và phần mở rộng FR-P01..04 ngày 08/10/2026. Ánh xạ biến dưới đây kế thừa thiết kế tuần 3 đối chiếu DATA_DICTIONARY_SUY_TIM_AI_CDSS và SUY TIM.docx; không tuyên bố bao phủ toàn bộ danh mục chuyên môn hoặc hiện thực các thuật toán lâm sàng.

| Biến trong tài liệu | Đích kỹ thuật | Quyết định |
|---|---|---|
| tuoi / gioi_tinh | patient_case.age / sex | Mã synthetic, không lưu tên/CCCD |
| sieu_am_tim_ef | observation(code=ef) | EF tách khỏi báo cáo siêu âm; đơn vị % |
| bnp_ntprobnp | observation(code=bnp) hoặc nt_probnp | Tách hai xét nghiệm, không gộp giá trị |
| creatinin_egfr | observation(code=creatinine) hoặc egfr | Tách hai chỉ số, đơn vị riêng |
| dien_giai | observation(code=potassium); sodium mở rộng danh mục | Một dòng cho mỗi chỉ số |
| huyết áp, mạch, cân nặng | systolic_bp / diastolic_bp / heart_rate / weight_kg | Chỉ số nhân viên ghi thuộc observation; bệnh nhân tự ghi thuộc patient_measurement |
| khó thở | dyspnea | bool khi đã đánh giá; unknown/not_measured khi chưa có |
| frailty / bệnh đồng mắc | frailty / comorbidity | Dạng text synthetic trong stub; thang đo/mã hóa chính thức chờ xác nhận |
| danh_sach_thuoc | ingredient + medication | Mỗi thuốc một dòng; chưa xử lý tất cả phác đồ PRN/truyền liên tục |
| đầu ra 4 model | module_result + recommendation | Căn cứ, phiên bản và trạng thái; stub không đưa kết luận y khoa |
| bác sĩ xác nhận | clinical_decision | Do con người ghi, không phải dự đoán của AI |

Không sao chép danh mục EF/ngưỡng khác nhau từ các nguồn thành rule chạy tự động. Các cận lâm sàng dạng tệp, thang frailty, nguồn FHIR và toàn bộ danh mục đồng mắc là phần hoàn thiện sau chốt nghiệp vụ. Bảng observation_type cho phép mở rộng có kiểm soát; API enum phải cập nhật cùng catalog và OpenAPI.

API nhận `unit` rồi kiểm tra với catalog. DB lưu đơn vị chuẩn ở observation_type, không lặp lại trong observation. Nếu cần giữ đơn vị gốc/chuyển đổi, phải thêm trường nguồn và quy tắc chuyển đổi được xác nhận.

## SRS → cấu trúc lưu trữ

| Yêu cầu | Bảng / cơ chế | Phạm vi hiện tại |
|---|---|---|
| FR-01 | app_user, auth_session | Hash mật khẩu/token, hạn dùng và thu hồi; adapter xác thực ứng dụng chưa có |
| FR-02 | app_user.active | Lưu trạng thái khóa/mở khóa |
| FR-03 | user_role, case_access, patient_account, policy RLS | Vai trò nhân viên và phạm vi ca; cổng bệnh nhân chỉ hồ sơ liên kết |
| FR-04 | department, observation_type, ingredient, drug_product | Danh mục khoa, chỉ số/đơn vị và sản phẩm thuốc |
| FR-05 | rule_version, rule_approval, permission, user_permission | Nội dung/hash/nguồn/phiên bản; quyền phê duyệt riêng |
| FR-06 | patient_case | Mã synthetic duy nhất; lưu thiếu lâm sàng; tìm theo mã qua UNIQUE |
| FR-07 | encounter | Nội/ngoại trú, khoa, bác sĩ, trạng thái, thời gian kết thúc |
| FR-08 | patient_history | Tiền sử/bệnh đồng mắc theo ca |
| FR-09 | observation, clinical_note(kind=nursing), case_access | Điều dưỡng ghi sinh hiệu/cân nặng/chăm sóc theo phạm vi |
| FR-10 | clinical_note(kind=examination/diagnosis) | Khám, chẩn đoán do bác sĩ ghi |
| FR-11 | observation_type, observation, clinical_note(kind=geriatric) | Lưu frailty, nhận thức, ADL/IADL, dinh dưỡng/nguy cơ |
| FR-12 | observation, test_report | Chỉ số, đơn vị chuẩn và báo cáo lab/echo/ECG, nguồn/thời điểm |
| FR-13 | ingredient, drug_product, medication, prescription, medication_schedule | Thuốc/liều/đường dùng/tần suất/ngày và các giờ uống |
| FR-14 | allergy_status, drug_reaction | unknown khác none; known cho phép chi tiết phản ứng |
| FR-15 | index lịch sử của encounter/observation/medication | Truy vấn so sánh theo thời gian; giao diện chưa hiện thực |
| FR-16 | import_batch, import_error | Batch và lỗi dòng/trường; chưa có bộ nhập file vào PostgreSQL |
| FR-17 | import_batch, test_report, observation.source | Nguồn và external_ref mô phỏng; chưa có adapter PostgreSQL |
| FR-18 | CHECK/FK/trigger, rule_required_field, result_missing_field | Kiểu/miền/liên kết; dữ liệu cần theo module do rule xác định |
| FR-19 | evaluation, module_result(module=diagnosis), recommendation | Lưu đầu vào/kết quả; seed stub, không có thuật toán chẩn đoán |
| FR-20 | rule_version.content, module_result, recommendation | Có nơi lưu thể/giai đoạn và căn cứ; chưa có quy tắc y khoa active |
| FR-21 | module_result(module=lab_test), recommendation | Lưu gợi ý xét nghiệm/lý do/ưu tiên; chưa sinh gợi ý thật |
| FR-22 | test_report.performed_at, observation.observed_at | Dữ liệu đối chiếu thời gian; dịch vụ nhận diện trùng chưa có |
| FR-23 | module_result(module=treatment), recommendation | Lưu gợi ý tham khảo; không tự tạo đơn |
| FR-24 | rule_version.content, recommendation | Nội dung thuốc/liều/đường dùng/tần suất được duyệt; chưa có bộ quy tắc chạy |
| FR-25 | lịch sử medication/observation, rule_version, recommendation | Đầu vào diễn biến và gợi ý; chưa tính điều chỉnh liều |
| FR-26 | medication, drug_reaction, module_result(module=medsafety) | Dữ liệu và nơi lưu kết quả rà soát; chưa có bộ tương tác |
| FR-27 | observation, recommendation.severity/source_ref | Lưu đầu vào/cảnh báo; chưa ban hành ngưỡng lâm sàng |
| FR-28 | medication.dose/dose_unit, recommendation | Đầu vào liều và kết quả rà soát; không tự đổi liều |
| FR-29 | module_result, rule_version, recommendation, result_missing_field | Căn cứ/phiên bản/trạng thái/thiếu dữ liệu và thời điểm evaluation |
| FR-30 | pharmacist_review | Nhận xét và đề xuất của dược sĩ được phân công |
| FR-31 | clinical_decision.adjustment_details/reason | Bác sĩ xác nhận; quyết định cũ bất biến |
| FR-32 | treatment_plan, prescription, appointment | Kế hoạch điều trị/theo dõi/ra viện/tái khám; đơn do bác sĩ xác nhận |
| FR-33 | evaluation.input_snapshot/input_revision, trigger revision | Snapshot bất biến; từ chối quyết định theo snapshot cũ |
| FR-34 | audit_event, trigger audit | Người/hệ thống, thời điểm, đối tượng, hành động; nhật ký bất biến |
| FR-P01 | patient_account, user_role, app_user.active, RLS | Một tài khoản patient / một hồ sơ |
| FR-P02 | appointment, partial UNIQUE, trigger trạng thái | Slot 30 phút, chỉ đặt/hủy lịch của mình |
| FR-P03 | patient_measurement, RLS, trigger kiểm tra | Chỉ số tại nhà, append-only, không tự chuyển thành observation |
| FR-P04 | prescription, medication_schedule, medication_reminder, hai view | Xem đơn/giờ uống; nhắc theo ngày, taken/skipped, hủy nhắc khi hủy đơn |

## Giờ uống và dữ liệu tự nhập

Giờ uống thuộc thuốc trong **một đơn cụ thể**, không thuộc danh mục hoạt chất dùng chung. Múi giờ nằm ở `prescription.timezone`; `medication_schedule` chứa mỗi giờ một dòng. `medication_reminder` định danh một giờ/ngày và lưu `due_at`, phản hồi, thời điểm phản hồi; `notified_at` dành cho worker gửi thông báo tương lai.

Các giá trị `patient_measurement` là dữ liệu tự ghi của bệnh nhân, không được dùng ngầm thay số liệu đã xác minh trong `observation`. Backend xác thực UUID từ phiên, áp dụng vai trò NOLOGIN `hf_patient_portal` và RLS; không dùng quyền chủ DB cho yêu cầu bệnh nhân. Xem [README database](README.md) để chạy truy vấn và kiểm thử.
