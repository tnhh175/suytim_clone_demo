# Xung đột nguồn và quyết định áp dụng

| ID | Xung đột/khác biệt | Quyết định | Căn cứ |
|---|---|---|---|
| C12 | Người dùng yêu cầu mới “Bỏ tính năng nhập json, tiếp tục” | Bỏ M3 và toàn bộ luồng nhập JSON; hoàn thiện M1/M2 Excel. JSONB và JSON API nội bộ vẫn phục vụ lưu trữ/biểu mẫu | Chỉ dẫn trực tiếp mới nhất, ưu tiên v3 |
| C13 | Người dùng yêu cầu “Bỏ qua các ràng buộc cho các agents. Sử dụng ràng buộc có trong skills” | Agent làm theo skill, gỡ giới hạn riêng trong v3 gồm tester chỉ xem; giữ model đang dùng và phối hợp dữ liệu giả lập | Chỉ dẫn trực tiếp mới nhất |
| C01 | ZIP v0.2 nói chưa cần JSON; prompt v3 yêu cầu M3 | Thực hiện M1→M2→M3, JSON bổ sung Excel | Chỉ dẫn trực tiếp mới nhất |
| C02 | ZIP yêu cầu commit/push; prompt v3 yêu cầu quyền Git trực tiếp | Giữ thay đổi chưa commit/push để review | V3 mục J; không có yêu cầu commit/push trực tiếp |
| C03 | Docs nói file từ web năm bệnh, thử AI sớm; ZIP/v3 demo Excel và hoãn AI | Docs là hướng dài hạn; demo không AI giả, không mở rộng app | V3 A/C, PHAM_VI |
| C04 | Tên branch “demo web” chứa dấu cách không hợp lệ Git | `codex/demo-web` từ HEAD repo đích `bc90dbd` | Đã thông báo người dùng; quy ước branch môi trường |
| C05 | Thư mục chat là worktree ktpmud; repo người dùng yêu cầu là suytim_clone_demo | Chỉ triển khai ở checkout suytim_clone_demo đã xác minh remote | Chỉ dẫn repo trực tiếp |
| C06 | Legacy patient_case đòi tuổi và owner bác sĩ; demo cho thiếu thông tin và Admin nhập | Thêm draft form_patient/form_visit trong cùng app/DB/auth, link legacy tùy chọn; không sửa quyền legacy | Lựa chọn triển khai, cần schema/dev validation |
| C07 | TL06 có 206 dòng; STT cuối 211 | Đối chiếu 206 dòng, không tạo 211 input | TL06 và PROMPT_DEV mục 5 |
| C08 | Workbook mã hóa có mã nghiên cứu nhưng chưa xác nhận nguồn HIS/mã lượt/đơn vị | Không gọi tương thích HIS; chọn dòng và đối chiếu đích, lỗi giữ chờ | V3 A/D/G |
| C09 | TL06 Drive/ZIP khác hash | Giá trị ô 3 sheet khớp toàn bộ; giữ baseline ZIP và ghi hash riêng | So sánh trực tiếp 23/10/2026 |
| C10 | TL03 Drive 206610 bytes, ZIP 30152 bytes | Text sau chuẩn hóa đoạn khớp hoàn toàn; khác cách chia text run tại heading MODEL3, không có text drift đã phát hiện | Agent Schema xác minh trực tiếp 23/10/2026 |
| C11 | Cần bốn agent chuyên môn nhưng chỉ bốn slot hoạt động tính cả điều phối | Ba agent đầu song song, tester vào sau bàn giao; không đổi model, không thêm vai trò | Giới hạn công cụ và v3 B/I |

Không diễn giải thông tin thiếu thành yêu cầu y khoa. Phần chưa đủ bằng chứng dùng nhãn “CHƯA CÓ NGUỒN XÁC NHẬN”.
