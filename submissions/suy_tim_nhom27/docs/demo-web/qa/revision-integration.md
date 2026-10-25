# Tích hợp bản sửa v1.0 — 26/10/2026

Nhánh `codex/demo-web`, nền `36cac2c`; đợt sửa này chưa commit/push. Nguồn và các phần theo giai đoạn ghi ở `../revision-scope.md`. Phân công: Data/Schema Astra medium, UX/UI Astra medium, Full-stack Sol xhigh, Tester Astra high. Root kiểm tra tích hợp và browser. Không dùng số test trước sửa làm bằng chứng đợt này.

## Kiểm thử thực chạy

- Toàn bộ Python suite sau chốt backend và bổ sung đối chiếu BN: **113 passed, 4 skipped, 1 warning**, 33.91 giây. Log ngoài Git: `.context-shears/artifacts/command-20261025T185709.469067Z-0bbf90254b5e.log`. Bốn test cũ có gate môi trường riêng; warning Starlette/httpx có sẵn.
- **33 ca hồi quy frontend** chạy chính `forms.js` trong VM/DOM/API giả: giữ nháp khi request lỗi; retry mutation; vai trò; snapshot; ngày giờ; badInput; trạng thái busy; file stale/race; mapping/preset; đích BN; data_role. Lệnh: `node tests/forms_frontend_regression.cjs`. Đây không phải thay thế browser.
- `node --check web/forms.js`, kiểm tra whitespace và export OpenAPI đã thực hiện. Catalog nguồn 206 dòng/72 hỗ trợ; không tính trường Admin thêm vào số nguồn này.
- Lần full suite đầu có lỗi số lượng do hai bộ ghi QA chạy đồng thời; đã dừng ghi song song và chạy tuần tự. Hai lỗi khác là test loading text cũ mâu thuẫn C13 và OpenAPI chưa export; đã cập nhật kiểm tra tên sản phẩm/loading status và export hợp đồng runtime, không bỏ kiểm tra phân quyền hay persistence.

## Chuyển dữ liệu live

Schema đích duy nhất `d3_form_live_20261024`; không sửa `public`. Dừng đúng process của ứng dụng, áp migration 004 hai lần rồi khởi động lại. So với bản sao riêng trước chuyển:

| Đối tượng | Trước | Sau migration | Đối chiếu |
|---|---:|---:|---|
| Hồ sơ | 4 | 4 | ID và thuộc tính cũ giữ nguyên trừ mã hiển thị; alias trỏ đúng người |
| Lượt | 5 | 5 | ID/liên kết, ngày, revision, giá trị/nguồn cũ giữ nguyên |
| Lịch sử giá trị | 7 | 7 | Toàn bộ nội dung cũ giữ nguyên |
| Lần nhập file | 2 | 2 | Nội dung cũ giữ nguyên |

Tất cả khóa giá trị đã lưu còn có định nghĩa trong snapshot. Kết quả riêng: `local-data/revision-20261026/live-migration-result.json`. Với lượt trước migration, không thể khôi phục chính xác mẫu lúc tạo khi chưa từng lưu; dùng snapshot lần lưu cuối cho lượt có lịch sử, baseline tại chuyển cho lượt trống và ghi rõ `snapshot_origin`. Mọi lượt mới ghim ngay lúc tạo. Đây là giới hạn phục hồi dữ liệu cũ, không phải tự nâng lượt mới theo mẫu toàn cục.

## Browser thật trên bản đang chạy

- Đăng nhập Bác sĩ qua `/login`, không có trang chọn cổng hoặc dòng phụ Demo/Biểu mẫu cạnh tên sản phẩm.
- Tạo hồ sơ bằng UI với tên để trống cho hệ thống cấp `BN-00005` / `Người bệnh giả lập 00005`; DOB giả lập 15/03/1970, Nữ, mã nguồn `SYN-REVISION-20261026`, BHYT ban đầu NULL. Mở lại giữ đúng dữ liệu.
- Tạo hai lượt riêng bằng bộ chọn ngày giờ: `LK-TRINH-DIEN-01` 20/10/2026 09:00 và `LK-TRINH-DIEN-02` 26/10/2026 00:30, chọn khám mới/tái khám, lý do/bệnh sử giả lập. Cân nặng 62/61 và khó thở khi gắng sức Có/Không minh họa hai lần ghi nhận; không sao chép sinh hiệu hoặc tạo quyết định điều trị. Không gán ICD/thuốc chưa biết để làm đầy màn hình.
- Tổng quan đúng thứ tự hành chính → bệnh/thuốc có nguồn lượt/ngày → danh sách lượt giảm dần; lượt không ngày nằm sau và không giả ngày khám. Khối bệnh lấy lượt nguồn có thông tin, độc lập khối thuốc/dị ứng.
- Tuổi 150 và cân nặng -1 bị lỗi UI, không đi tiếp như đã lưu. Sau sửa giá trị hợp lệ, đổi nhóm giữ nháp và lưu được; lịch sử đọc được nhãn, kg/tuổi, Có/Không và người/thời điểm. Kiểm tra beforeunload đầy đủ ở các trình duyệt chưa thực hiện; có ca hồi quy handler và quan sát giữ nháp khi thử rời.
- Mở Admin ở tab khác thấy cùng `BN-00005`, cùng hai lượt và giá trị. Sửa BHYT giả lập `000DEMO005`; vào lượt cũ vẫn dùng hành chính snapshot, không sửa giá trị khám; không có nút Lưu thay đổi, tạo lượt hoặc Nhập file.
- Admin thêm `ghi_chu_theo_doi` qua editor chọn nhóm/kiểu, xem trước, lưu mẫu v5. Lượt v4 không có trường này. Tạo lượt nháp `LK-MAU-MOI-NHAP` dùng v5; Admin đổi nhãn toàn cục thành “Ghi chú theo dõi sau khám”, tải lại lượt nháp vẫn thấy nhãn cũ. Không có thao tác nâng mẫu ngầm.
- Danh sách thuốc hiện các mục thành khối dọc với nhãn cho từng thành phần; đã thử thêm rồi trả lại NULL, không ghi thuốc giả để qua bước lưu.
- File Excel giả lập hiện có qua nguồn cũ `SYN-FORM-001/002` đối chiếu đúng đích `BN-00001/00002`; preview hiện mã BN/tên/lượt đích riêng với mã trong file, nguồn trống không xóa và xung đột mặc định giữ đích. Lưu preset theo nguồn, reload và khởi động lại backend, chọn lại preset vẫn dùng được. Browser kiểm preview/preset; commit/rollback/replay kiểm bằng API trong suite.
- Bố cục một cột và repeat dọc; kiểm hẹp 390×844 và 320×740, chiều rộng tài liệu lần lượt 375 và 305 px, không tràn ngang toàn trang. Admin editor có vùng bảng cuộn riêng. Không tuyên bố audit WCAG toàn diện.

Ca trình diễn được thêm **sau** kiểm chứng migration: một hồ sơ và ba lượt (hai lượt có diễn biến và một nháp thử phiên bản), tách khỏi bộ ca lỗi cũ. Không làm thay đổi bằng chứng 4/5/7/2 của bước chuyển mã.

## Ảnh và giới hạn

- `revision-overview.png`: tổng quan ca giả lập.
- `revision-form-mobile.png`: biểu mẫu ở 390 px.
- `revision-file-preview.png`: đối chiếu mã nguồn và BN.

Workbook bệnh viện thực, thuốc/kết quả lặp trong Excel, chuẩn hóa A04/A06 trước AI và A09–A11 vẫn theo giai đoạn đã duyệt. Chưa xác nhận tương thích HIS, công thức lâm sàng, AI hoặc triển khai viện. Xem `../revision-data-contract.md` và `revision-acceptance.md` cho tiêu chí/dữ liệu và giới hạn độc lập.
