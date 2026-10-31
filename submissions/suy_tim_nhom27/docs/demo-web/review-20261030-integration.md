# Bàn giao đợt sửa theo 22222.md — 30/10/2026

## Phạm vi và nguồn

Yêu cầu trực tiếp: làm theo review `22222.md`, tiếp tục chia agent. Bản review được dùng để triển khai UI01–UI12 và nền ghi nhận dữ liệu đủ rõ; các gợi ý chuyên môn P2/P3 vẫn theo lộ trình. Nội dung nguồn, nhận xét review và quyết định triển khai không được coi là thuật toán lâm sàng. Không thay SRS/report/FR/NFR/US/UC/RTM cũ.

SHA-256 bản review: `f61b64418137e01e591c4e0b702dc0c244a5c612990148894a3b173d20a761e8`.

Repo `D:/1.TNHH/project/suytim_clone_demo`, nhánh `codex/demo-web`, nền commit `9a46fa6`. Chia bốn vai trò dữ liệu, UX/UI, lập trình và kiểm thử, với skill chuyên môn tương ứng và vòng bàn giao–sửa–kiểm chứng. Commit và push đợt thay đổi này theo yêu cầu trực tiếp của người dùng khi bàn giao.

## Kết quả giao diện

- UI01–UI02: thống nhất **Hồ sơ bệnh nhân**; biểu tượng tim/ECG dùng chung; tài khoản và vai trò rõ. Backend hiện chưa có tên hiển thị riêng của nhân viên, nên dùng tên vai trò, tên đăng nhập nằm trong chi tiết tài khoản; không tạo tên bác sĩ giả.
- Đăng nhập: bố cục desktop 55%/45%, nhận diện ngắn trên mobile, giới thiệu đúng chức năng, hiện/ẩn mật khẩu, Enter để đăng nhập. Giữ một trang và vai trò từ máy chủ.
- UI03–UI06: tìm mã/tên, chỉ hiện tuổi/giới đã biết; lần khám gần nhất lấy ngày khám thực tế. Tách ba phần tóm tắt với nguồn độc lập, giữ danh sách lượt theo thời gian và loại khám đã ghi.
- UI07–UI09: nhập một cột dọc; nhóm bên trái desktop, select gọn trên mobile; ngữ cảnh BN/lượt/tuổi tại ngày khám gọn, phần chi tiết mở rộng. Khi mở chi tiết, ngữ cảnh không cố định che các ô nhập.
- UI08: giữ select ba trạng thái Có/Không/Chưa có dữ liệu. Không mặc định Không.
- UI10–UI12: trạng thái tải/nháp/lưu khác nhau; số mục chưa hỗ trợ lấy theo mẫu đã ghim và thu gọn. Lỗi ngay trường, đơn vị có khoảng trắng cho nhãn trợ năng; lỗi ngày giờ nhập dở không biến thành NULL.

## Kết quả dữ liệu và phần còn theo lộ trình

| Mục review | Thực hiện / giới hạn |
|---|---|
| DL01 | BP nằm/ngồi và đứng: tâm thu/tâm trương, tư thế đã biết, mmHg, thời điểm và nguồn. Cho lưu bản ghi đang thu thập, không tự bù thành phần còn thiếu. |
| DL02 | LVEF %, báo cáo chữ, thời điểm và nguồn siêu âm. Không suy kiểu hình hoặc chẩn đoán; chưa nhận tệp ảnh. |
| DL03–DL04 | Mã BNP riêng NT-proBNP; creatinin/eGFR/Na/K định danh riêng trong danh sách kết quả, giữ tên/đơn vị/thời điểm gốc. Không quy đổi hoặc tính eGFR. Na và một số xét nghiệm chưa có allowlist đơn vị đã xác nhận. |
| DL05 | Có nhóm kết quả bổ sung. CBC/LIVER vẫn là nhóm ghi nhận, cần tên chỉ số trên phiếu; chưa phải danh mục thuật ngữ hoàn chỉnh. |
| DL06 | Thuốc thêm hàm lượng, liều số + đơn vị, bắt đầu/kết thúc, trạng thái và loại sản phẩm, nguồn. Giữ mô tả liều gốc; trạng thái chưa biết để NULL. Nhãn mới là “Danh sách thuốc ghi nhận” để thuốc dự kiến/đã ngừng không bị gán là đang dùng. Chưa đủ hợp đồng MedSafety. |
| DL07 | Bảo toàn tình trạng dị ứng hiện có; ADR theo hoạt chất/biểu hiện/mức độ cần đặc tả P2. |
| DL08 | Tách bệnh mạch vành đã biết Có/Không/NULL và mô tả/can thiệp độc lập. |
| DL09, DL11, DL13, DL15–DL16 | Giữ theo P2: thang lão khoa, diễn biến, hợp đồng dùng lại dữ liệu giữa module, hòa giải kiểu hình/mức độ. Không tự chọn thang/ngưỡng. |
| DL10 | Nhãn và hướng dẫn mẫu mới là NYHA tại lần khám này. Mã lựa chọn I–IV không đổi; không tự tính biến thiên. |
| DL12 | Nguồn và thời điểm theo báo cáo được ghi riêng, không lấy giờ nhập làm giờ xét nghiệm. Chữ ký/xác nhận, tệp và QRS/QTc theo P2. |
| DL14 | Chưa tính BMI vì quy tắc làm tròn chưa thống nhất; chưa phân loại đa thuốc. |
| DL17, DL19 | Giữ BN, alias, hành chính, quyền, NULL/false/0/[]; không thêm CCCD hay dữ liệu thật. |
| DL18 | Kiểm kiểu hữu hạn, giới hạn vật lý và đơn vị có nguồn; không dùng khoảng bình thường để cấm số đo bệnh lý. Chuẩn hóa đơn vị toàn bộ còn cần hợp đồng bổ sung. |
| DL20 | Chưa xây tài khoản/cổng người chăm sóc. |

Catalog có 222 định nghĩa: 206 dòng nguồn giữ dấu vết + 15 scalar thành phần + 1 nhóm xét nghiệm; 88 định nghĩa có widget hỗ trợ, không phải 88 trường luôn bắt buộc nhập hoặc phần trăm hoàn thành y khoa. Các trường nguồn gộp giữ `supported_by`, không tự diễn giải lại dữ liệu lịch sử.

Nhập Excel dùng chung validation cho scalar mới và vẫn có preview/đối chiếu/xung đột. **Danh sách thuốc/kết quả chưa nhập được từ Excel** khi chưa có cấu trúc nguồn xác nhận; nhập qua form. Không có nhập file hoặc dán JSON. Không khẳng định tương thích HIS thật.

## Cập nhật danh mục an toàn

`database/catalog-upgrades/005_review_20261030.json` lưu chính xác định nghĩa trước/sau. `scripts/upgrade_form_catalog.py` mặc định chỉ lập kế hoạch; apply cần backup mới trong `local-data`, khóa catalog trong giao dịch và từ chối ghi đè định nghĩa đã được Admin sửa. Chỉ chấp nhận schema giả lập `d3_form_`; không fallback sang public.

Thay đổi chỉ áp dụng cho các lượt tạo sau khi cập nhật. Các lượt cũ, kể cả draft, giữ nguyên definitions, giá trị, provenance và lịch sử. Lượt cũ chưa có ô BP/EF mới phải tiếp tục dùng mẫu đã ghim; đợt này không có thao tác nâng mẫu hồi tố.

Bản local live đã cập nhật từ catalog v6 lên v8 (v7 dữ liệu nền, v8 nhãn thuốc trung tính). Kiểm toàn bộ row/hash trước/sau: 5 hồ sơ, 9 lượt, 11 dòng lịch sử khám, 4 alias, 1 lịch sử hành chính, 4 quyền truy cập, 2 batch import, 1 preset giữ nguyên. Backup/catalog và kết quả đối chiếu nằm riêng trong `local-data/review-20261030/`. Dry run bản manifest cuối không còn thay đổi; trường Admin bổ sung được giữ nguyên.

## Kiểm chứng

| Bộ kiểm | Kết quả |
|---|---|
| Full Python suite, PostgreSQL QA riêng, chạy tuần tự | **142 passed, 4 skipped, 1 warning**, 19.64s |
| Frontend regressions thực thi JS trong VM | **45 passed** |
| Pure data/catalog/version checks sau chỉnh nhãn cuối | **24 passed** |
| `node --check web/forms.js`, offline form schema check, OpenAPI contract, `git diff --check` | Đạt |

Log full suite: `.context-shears/artifacts/command-20261030T131544.305500Z-dc8572f83ea1.log`. Lần chuẩn bị đầu thiếu `PYTHONPATH=src`, dừng ở collection; đã sửa môi trường rồi chạy đủ suite. Bốn skip thuộc các ca legacy cần môi trường tùy chọn, không tính là pass; warning là Starlette/httpx deprecation có sẵn.

Kiểm trình duyệt thật bởi điều phối:

1. Admin/Bác sĩ dùng cùng login; hiện/ẩn mật khẩu đổi đúng kiểu input; Enter đăng nhập. Admin không có control nhập khám hoạt động hoặc nút lưu, backend tests cũng trả 403 khi cố ghi.
2. Desktop 1280×800: grid đăng nhập đo được 704px/576px; không tràn ngang. Mobile 390px/320px: document375px/305px, nhóm select và danh sách dọc; không tràn ngang ở các màn đã kiểm.
3. Lượt live cũ vẫn dùng v4, không xuất hiện trường mới; 119 mục chờ module thu gọn, mặc định đóng. Ngữ cảnh nhận đúng bệnh nhân, mã lượt và tuổi tại lần khám.
4. Schema QA riêng: hiển thị đúng hai mã BNP/NT-proBNP và nguồn/thời điểm; LVEF101 báo lỗi tại ô, sửa43 → lưu → GET lại thấy43 và “Đã lưu”. Thuốc dự kiến giữ trạng thái, không tự chuyển đang dùng. Không ghi các giá trị thử này vào live.
5. Đã sửa hai lỗi phát hiện trực tiếp: tiêu đề dính chữ khi ẩn `<br>` trên mobile; nhãn số dính đơn vị trong accessibility tree.

Ảnh bằng chứng: `qa/review-20261030-login.jpg`, `qa/review-20261030-mobile.jpg`, `qa/review-20261030-medications-mobile.jpg`. Ảnh thuốc dùng lượt QA đã ghim trước lần tinh chỉnh nhãn, nên còn nhãn “Danh sách thuốc hiện tại”; trạng thái Dự kiến vẫn giữ và mẫu mới sau v8 dùng nhãn trung tính.

Chưa chứng nhận WCAG, kiểm định chuyên môn, thuật toán AI, hiệu năng hoặc tương thích dữ liệu viện. Không dùng kiểm thử VM để thay cho bằng chứng bố cục; báo cáo độc lập ở `qa/review-20261030.md` tách rõ phần agent thực chạy.

Kiểm tra bàn giao 31/10: frontend vẫn 45 pass; `py_compile`, `node --check` đạt; live `/health`200, catalogv8 không còn conflict/change và toàn bộ tám bảng nghiệp vụ trên vẫn khớp hash trước nâng. Đã dừng đúng tiến trình QA tạm cổng8003, giữ demo live cổng8001. Phiên browser hết hiệu lực khi dọn tab nên không xác nhận được reset viewport/đóng tab QA; các kiểm chứng và ảnh ở trên đã được ghi trước đó.
