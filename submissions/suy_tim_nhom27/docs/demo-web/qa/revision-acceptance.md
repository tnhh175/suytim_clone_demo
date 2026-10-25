# Kiểm thử chấp nhận độc lập — bản sửa v1.0

Ngày: 26/10/2026 (Asia/Saigon). Người thực hiện: agent User Roleplay / Bug Tester. Đây là báo cáo API với PostgreSQL thật trong sandbox giả lập. Phần persona bên dưới là mô phỏng định tính, không phải dữ liệu nghiên cứu người dùng; chưa chạy walkthrough trình duyệt trong nhiệm vụ con này.

## Nguồn, phạm vi và ranh giới

Đã đọc đầy đủ `C:\Users\tnhh\Downloads\Yeu-cau-sua-demo`, bản đã duyệt v1.0 ngày 25/10/2026, và `docs/demo-web/revision-ui-spec.md`. Đối chiếu C01–C13, A01–A03, A07–A08, A12–A14 hiện tại; A04–A06 chỉ kiểm thành phần đã có hợp đồng. Không thêm quy tắc chuyên môn, suy diễn kết quả AI hoặc lấy A09–A11 làm tiêu chí phải triển khai đợt này.

Repo thực tế: `D:\1.TNHH\project\suytim_clone_demo`, nhánh `codex/demo-web`; thay đổi đang chưa commit. Skill đã áp dụng: context-shears, agency-evidence-collector, agency-persona-walkthrough-specialist. Không sửa mã production, test của dev, dữ liệu public hoặc schema live; chỉ thêm `tests/test_revision_acceptance.py` và báo cáo này.

Tất cả yêu cầu ghi trong test dùng `d3_form_qa_20261023`, bắt buộc kiểm tra chính xác `options=-csearch_path=d3_form_qa_20261023,public`. Tài khoản lấy từ tệp riêng bị Git bỏ qua, không ghi mật khẩu/token vào báo cáo. Tạo dữ liệu bằng API thông thường. Một fixture chuyển chủ sở hữu của đúng hồ sơ giả lập vừa tạo để thử bác sĩ ngoài phạm vi. Định nghĩa trường chỉ thêm mã `qa_accept_*`, `qa_added_*`; không đổi trường nguồn.

## Kết quả thực chạy

Lệnh trong `submissions/suy_tim_nhom27`:

```powershell
& 'C:\Users\tnhh\.codex\skills\context-shears\bin\context-shears.cmd' run --kind test -- '.\.venv\Scripts\python.exe' -m pytest tests/test_revision_acceptance.py -q --tb=short
```

Biến `FORM_TEST_DSN` được tạo bằng `make_conninfo` từ config cục bộ, thay search path thành QA; `FORM_TEST_CREDENTIALS` trỏ file QA riêng. Không công bố giá trị DSN.

Kết quả mới nhất: **13 passed, 1 warning, 4.66s**, exit 0. Artifact: `.context-shears/artifacts/command-20261025T173638.103230Z-addcf2902505.log` và metadata cùng tên `.json`. Warning là Starlette TestClient thông báo httpx deprecated; không có assertion thất bại. Đây không phải số liệu bộ test cũ trước sửa.

Sau lần chạy trên, thêm ca thứ 14 `test_k04_legacy_saved_catalog_matches_latest_history_readonly` để root chạy sau khi replay migration 004 đã chỉnh: kiểm không còn snapshot lấy lần lưu đầu, snapshot lượt cũ bằng định nghĩa lần lưu cuối và không ẩn key giá trị đã có. Ca này chỉ đọc và **chưa chạy trong báo cáo 13 passed**; cần cập nhật kết quả sau khi root chạy trên DB đã ổn định. Không chạy đồng thời các bộ test ghi chung QA vì các assertion đếm toàn cục của bộ test cũ sẽ bị nhiễu.

Lần đầu có lỗi setup test do truy vấn giả định cột `role.id`; đã sửa setup lấy `user_id` qua `/api/v1/auth/me`, rồi kiểm lại. Lỗi đó thuộc harness QA, không phải lỗi sản phẩm. Không phát hiện sai lệch sản phẩm tái hiện được trong 13 ca API đã chạy; không suy rộng thành toàn bộ K01–K15 đạt.

## Ma trận nghiệm thu

| Mã | Bằng chứng hiện có | Kết luận đúng phạm vi / phần còn thiếu |
|---|---|---|
| K01 | Hai tài khoản đăng nhập chung qua API; bác sĩ POST cấu hình nhận 403; tài khoản Admin không tạo hồ sơ | Đạt phần API đã thử. Một trang login, đường dẫn UI trực tiếp: cần bằng chứng browser riêng. |
| K02 | Tạo tối thiểu, BN đúng mẫu và khác nhau, tên giả lập, DOB/sex/BHYT NULL, đọc lại, không ép ICD; client tự gán code bị 422 | Đạt API; các ô và thao tác tạo trên UI chưa kiểm trong nhiệm vụ con này. |
| K03 | Admin đọc cùng patient/visit/values; PATCH lâm sàng và tạo lượt bị 403; bác sĩ ngoài phạm vi GET/PATCH nhận 404 | Đạt API đọc chung và giới hạn vai trò. |
| K04 | API thay mã nguồn vẫn ánh xạ mã cũ qua alias, không cho dùng alias cho hồ sơ thứ hai | Đạt alias API. Bảo toàn toàn bộ IDs/count/history qua migration cần đối chiếu trước–sau riêng của root; không lấy test alias làm bằng chứng migration. |
| K05 | Ba lượt: ngày mới, ngày cũ, thiếu ngày; sửa lượt cũ không đổi thứ tự; latest theo ngày khám | Đạt API thứ tự/ngày trống. Bố cục và nguồn từng khối tổng quan cần browser. |
| K06 | Lượt cũ giữ ICD, giá trị, giới tính snapshot, mẫu và thuốc; nguồn manual và ngày thuốc giữ nguyên | Đạt API dữ liệu của lượt; header trình bày đúng cần browser. |
| K07 | Hành chính mới từ sửa Admin; lượt cũ giữ snapshot; tuổi 23/25 theo ngày; ca sinh nhật 00:30 +07 có tuổi 24; lượt không ngày tuổi NULL; không sao chép cân nặng/thuốc | Đạt API. Ca tuổi ghi nhận 48 không tự sinh DOB. |
| K08 | Không có bằng chứng browser trong nhiệm vụ con này | Chưa kiểm: tám nhóm nguyên tên, một cột, repeat dọc, context, 390px/320px, bàn phím/chuỗi dài. |
| K09 | Tạo lượt đã lưu và nháp trước sửa; Admin thêm/đổi nhãn/đổi nhóm/ngừng trường; đọc cả hai role vẫn mẫu cũ; lượt mới revision mới | Đạt API, kể cả nháp chưa lưu lần đầu; thao tác UI cần browser. |
| K10 | Giá trị/lựa chọn/nhãn/nhóm cũ còn đúng; lịch sử dùng định nghĩa cũ; ngừng toàn cục vẫn sửa được lượt cũ; đổi kiểu bị 422 | Đạt API; lịch sử hiển thị nhãn/đơn vị dễ đọc cần browser. |
| K11 | XLSX giả lập chứa cặp mã nguồn/visit, preview eligible, commit, đọc lại đúng ca và `QA_SYNTHETIC!D2` | Đạt đường API file giả lập. Không xác nhận tương thích HIS/file bệnh viện. |
| K12 | Mã nguồn và mã lượt có 0 đầu, alias; NULL giữ dữ liệu tay; nhập lặp không tăng revision; thiếu/sai cặp/không tồn tại bị báo lỗi; chọn kèm lỗi không ghi; record thứ hai stale thì record thứ nhất không ghi | Đạt API các tình huống đã nêu. Chưa kiểm file bệnh viện có thuốc/kết quả lặp. |
| K13 | Tuổi 150/cân nặng -1 bị 422, cả payload không ghi; 0/false/NULL phân biệt | Đạt API; validation UI cần browser. |
| K14 | Các lần lưu đều đọc lại được; conflict import không ghi từng phần | Chỉ đạt persistence API trong ca thử. Chưa kiểm đổi nhóm/rời lượt, beforeunload, input sau lỗi và reload trình duyệt. |
| K15 | Không có bằng chứng browser trong nhiệm vụ con này | Chưa kiểm tên sản phẩm và trạng thái tính năng chưa có. |

## Persona và đường đi cần đối chiếu bằng browser

Các persona là giả định kiểm thử từ hai vai trò đã duyệt, không thêm yêu cầu sản phẩm hoặc thay người dùng phê duyệt. Không ghi phản ứng quan sát hay điểm UX khi chưa nhìn màn hình.

**Bác sĩ:** người dùng Việt Nam quen nhập bệnh án, vào trực tiếp bằng tài khoản thử; mục tiêu tạo người bệnh chỉ biết thông tin tối thiểu, nhập lượt, lưu và xem lại lượt cũ. Lo ngại mất dữ liệu đang nhập hoặc nhầm thuốc/tuổi của lượt khác. Lời mô phỏng: “Tôi cần thấy đây là người bệnh nào, khám hôm nào, và phần tôi vừa nhập đã lưu chưa.” Phân tích: kiểm Clarity, khả năng thao tác và nút lưu; five-second test phải xác định được ứng dụng, vai trò, hành động tiếp theo ở màn đầu. Những tiêu chí này chưa được chấm.

**Admin:** người quản lý Việt Nam, vào trực tiếp bằng tài khoản thử; mục tiêu tìm hồ sơ bác sĩ vừa tạo, sửa hành chính có dấu vết, sửa mẫu cho lượt mới. Lo ngại đổi cấu hình làm biến dạng lượt cũ. Lời mô phỏng: “Tôi muốn sửa tên trường cho lần sau mà vẫn đọc đúng những lần đã nhập.” Phân tích: kiểm thông báo phạm vi phiên bản, nút xem trước/lưu và chế độ chỉ đọc lâm sàng; five-second test phải phân biệt quản lý mẫu với nhập giá trị. Chưa có phản ứng hoặc ảnh browser được coi là bằng chứng.

Kịch bản browser bàn giao root: đăng nhập cả vai trò → bác sĩ tạo tối thiểu → mở hồ sơ → tạo hai lượt khác ngày/thuốc → sửa và kiểm dữ liệu cũ → Admin xem cùng ID/chỉnh mẫu → trở lại bác sĩ → đổi nhóm khi chưa lưu, hủy/giữ dữ liệu → thử lỗi lưu → reload → kiểm 390px và 320px. Phải ghi bằng chứng thực tế riêng trước khi đánh dấu K08/K14/K15 hoặc walkthrough đạt.

## Giới hạn bàn giao

Không có commit/push. Chưa xác minh file HIS thật, chưa chạy walkthrough trong nhiệm vụ con này, chưa xác nhận WCAG hoặc production-ready. Migration trước–sau và browser do root đang thực hiện; khi có kết quả cần dẫn đúng artifact mới, không biến thông báo của agent khác thành kết quả đã tự quan sát.
