# Điều phối demo web — phạm vi hiện hành

> Đợt sửa 26/10 theo `revision-scope.md` và `revision-ui-spec.md` có ưu tiên cao hơn checkpoint bên dưới. Bản nền đã commit/push `36cac2c`; các sửa đăng nhập chung và đợt v1.0 đang để review. Kết quả checkpoint không thay thế nghiệm thu đợt mới.

Ngày cập nhật: 24/10/2026. Repo `tnhh175/suytim_clone_demo`, checkout `D:/1.TNHH/project/suytim_clone_demo`, nhánh `codex/demo-web`, nền `bc90dbd`. Tên “demo web” được chuyển thành tên Git hợp lệ.

## Chỉ dẫn và phạm vi

Prompt v3 là yêu cầu sản phẩm ban đầu; ZIP, workbook và Google Docs/Drive là tài liệu tham chiếu. Các yêu cầu trực tiếp sau đó của người dùng có ưu tiên cao hơn:

- Chỉ triển khai M1 nhập tay/trường động và M2 nhập Excel; bỏ tính năng nhập JSON.
- Agent tuân theo skill tương ứng; bỏ ràng buộc riêng của prompt v3. Tester được kiểm thử ghi trên dữ liệu giả lập, phối hợp để tránh tác động dữ liệu người dùng.
- Giữ cấu hình model đã chọn. Phân công file nhằm tránh ghi đè lẫn nhau.
- Chưa commit/push; để bản sửa cho người dùng review. Không sửa SRS, báo cáo, FR/NFR/US/Use Case hoặc RTM cũ. `.agents/` có từ trước được giữ nguyên.
- Dữ liệu bệnh nhân nguồn, thông tin đăng nhập và log giữ ngoài Git trong `local-data/` hoặc `.context-shears/`. Không triển khai AI, không tạo kết quả AI giả.

Điều phối áp dụng `agency-agents-orchestrator` và `context-shears`. Bốn vai trò được bố trí theo số slot thực tế, không tạo thêm vai trò thay thế.

| Agent | Model / reasoning | Skills | Bàn giao |
|---|---|---|---|
| Schema | gpt-6-astra / medium | data-engineer, database-optimizer | Catalog, migrations, profile, mapping, contract Excel, fixture và kiểm tra PostgreSQL |
| Mockup | gpt-6-astra / medium | ui-designer, ux-architect | Mockup editable, UI spec, flows, ảnh render Excel-only |
| Dev | gpt-6.1-sol / xhigh | frontend-developer, backend-architect | Runtime FastAPI/PostgreSQL, UI, test API, seed/run và runbook |
| Tester | gpt-6-astra / high | evidence-collector, persona-walkthrough-specialist | Review độc lập, ca kiểm, bug/retest và giới hạn bằng chứng |

## Trình tự và bằng chứng

Schema và mockup bàn giao hợp đồng trước phần triển khai phụ thuộc. Dev kiểm API/DB; Tester kiểm độc lập và gửi lỗi có bước tái hiện. Dev sửa rồi tái kiểm. Điều phối kiểm giao diện trực tiếp khi browser chỉ khả dụng tại root. Ảnh mockup không thay thế bằng chứng ứng dụng thật; test tái tạo app không thay thế restart process.

RTM mới `requirements-rtm.md` giữ 27 tiêu chí M1/M2. Chỉ đánh dấu đạt theo bằng chứng phù hợp, nêu rõ phần chưa kiểm. Không có tiêu chí M3 trong nghiệm thu hiện hành.

## Trạng thái tại checkpoint 24/10

- Schema: đối chiếu đủ 206 dòng TL06/8 cột; 70 trường hỗ trợ, 136 cần đặc tả. Kiểm migration lặp, constraint và NULL/false/0/array trên PostgreSQL riêng đạt. Contract và fixture đã chuyển Excel-only.
- Mockup: bỏ toàn bộ luồng JSON, có 7 ảnh render. Kiểm skip-link, không tràn ngang mobile, không lỗi trang; đây là prototype.
- Dev: hoàn thiện M1 và wizard Excel; toàn bộ suite 85 passed, 4 skipped. Restart process giữ nguyên dữ liệu/history, đã có runbook và dev-validation.
- Tester: review độc lập và 25 kiểm tra parser/hàm đạt; hai lỗi save/UUID đã sửa và retest. Root thực hiện UI thật, ghi tại live-ui-validation.md.
- Server demo được chạy trong schema giả lập riêng, không reset dữ liệu `public`. Trạng thái URL và kiểm restart được ghi ở báo cáo validation/runbook khi hoàn tất.
