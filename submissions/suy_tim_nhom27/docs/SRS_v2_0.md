# Đặc tả yêu cầu phần mềm hệ thống quản lý bệnh nhân suy tim

Nhóm 27

Phiên bản 2.0 ngày 21/10/2026

Trạng thái dự thảo chờ nhóm rà soát và chốt các điểm còn mở

## 1 Giới thiệu

### 1.1 Mục đích

Tài liệu đặc tả hành vi, dữ liệu, giao diện và điều kiện nghiệm thu của hệ thống quản lý bệnh nhân suy tim theo báo cáo hiện tại của nhóm. Nhóm phát triển, kiểm thử, giảng viên và người có chuyên môn sử dụng tài liệu để thống nhất phạm vi, triển khai và truy vết yêu cầu. Một yêu cầu có trong SRS không đồng nghĩa đã được hiện thực hoặc kiểm thử đạt.

SRS này thay cơ sở phạm vi của bộ 34 FR cộng 4 FR bệnh nhân trước đây bằng nội dung báo cáo Google Docs đọc ngày 21/10/2026. Phạm vi mới ưu tiên khám và theo dõi ngoại trú, tích hợp dữ liệu, quyết định của bác sĩ và cung cấp thông tin cho bệnh nhân. Không dùng mã FR/NFR cũ để suy ra ý nghĩa hoặc trạng thái của mã mới.

### 1.2 Phạm vi sản phẩm

Trong phạm vi dự kiến:

- Quản lý hồ sơ, lịch hẹn, lượt khám, dữ liệu lâm sàng và cận lâm sàng, thuốc và diễn biến theo thời gian.
- Tiếp nhận, đối chiếu, kiểm tra, chuẩn hóa dữ liệu HIS/EMR, LIS, PACS/RIS; ghi trả nội dung được bác sĩ xác nhận và cho phép gửi. Kiểm chứng trước bằng nguồn và đích mô phỏng.
- Cung cấp bốn module Diagnosis, Lab/Test, Treatment và MedSafety theo phạm vi đầu vào, quy tắc/mô hình và đầu ra đã được đặc tả, rà soát.
- Ghi nhận phản hồi của bác sĩ, kết luận, kế hoạch, xác nhận phiên bản và công bố nội dung được phép.
- Hỗ trợ bệnh nhân đặt/xem lịch, xem kết quả và kế hoạch đã công bố, nhận thông báo, nhắc lịch và nhắc thuốc.
- Quản lý tài khoản, quyền, danh mục, cấu hình, phiên bản quy tắc/mô hình và nhật ký.

Chưa cam kết trong phạm vi hiện tại:

- Quản lý nội trú toàn diện như giường bệnh, phân ca, thực hiện thuốc và chăm sóc hằng ngày.
- Nhật ký uống thuốc, theo dõi tuân thủ sát sao, tự nhập chỉ số tại nhà hoặc báo tác dụng không mong muốn. Các chức năng này không tự trở thành phạm vi mới chỉ vì demo cũ có một phần chức năng tương tự.
- Tự động kê đơn, thay đổi/ngừng thuốc hoặc tự xác nhận quyết định lâm sàng.
- Tích hợp bệnh viện thật, triển khai lâm sàng hoặc dùng mô hình dự báo khi chưa đủ điều kiện kỹ thuật, dữ liệu, kiểm định và thẩm quyền.
- Tài khoản người chăm sóc.

### 1.3 Nguồn và quản lý phiên bản

| Nguồn | Vai trò trong đặc tả |
|---|---|
| Báo cáo Google Docs hiện tại, mục II đến V, đọc ngày 21/10/2026 | Nguồn chính cho phạm vi, sáu phân hệ, FR, NFR, 45 User Stories, BDD và kiến trúc định hướng |
| Repository suytim_clone_demo, main, commit e7b4dbc220625d19390a071af9fee6b237b356de | Đối chiếu hiện trạng demo, hợp đồng API và kiểm thử; không ghi đè phạm vi mới |
| SRS cũ, RTM, README và tài liệu review trong repo | Bằng chứng lịch sử và khoảng trống triển khai; cần ánh xạ lại trước khi nghiệm thu theo SRS này |
| Tài liệu chuyên môn được báo cáo liệt kê | Nguồn cần được ghi phiên bản, điều kiện và rà soát khi xây quy tắc; tài liệu này không tự đưa thêm ngưỡng lâm sàng |

Đường dẫn nguồn chính: https://docs.google.com/document/d/1IoiV6fsCr3QuCS_i4Is7AEKOq-Cpb9wyMNK0gR7sBkI/edit?tab=t.0

Đường dẫn mã nguồn đối chiếu: https://github.com/tnhh175/suytim_clone_demo/tree/e7b4dbc220625d19390a071af9fee6b237b356de

### 1.4 Quy ước mã và độ ưu tiên

- Giữ mã FR01 đến FR26, FR35 đến FR46 theo bảng yêu cầu hiện tại.
- Bảng nhóm 4 của báo cáo đang lặp FR16 đến FR23 thay vì mô tả kết luận và kế hoạch. FR27 đến FR34 trong SRS này là đề xuất chuẩn hóa từ chức năng 4.1 đến 4.3, US-30 đến US-35 và BDD tương ứng. Tách thao tác lập và điều chỉnh dự thảo, chọn nội dung và công bố nội dung để có mã rõ ràng. Chưa coi các mã phục hồi này là bộ mã đã được nhóm phê duyệt.
- Có 46 FR trong bản dự thảo sau chuẩn hóa. Không cộng bộ FR35 đến FR38 cũ với FR35 đến FR39 của bản này.
- P1: ưu tiên luồng nghiệp vụ, tích hợp và hỗ trợ chuyên môn. P2: khôi phục truy cập và các yêu cầu chất lượng liên quan. P3: lịch hẹn và app bệnh nhân sau luồng chính. Đây là ưu tiên triển khai đề xuất trong báo cáo, không phải mức khẩn cấp y khoa.
- Ký hiệu TBD chỉ dữ liệu hoặc tiêu chí cần chốt. Không dùng giá trị giả định để nghiệm thu mục TBD.

### 1.5 Thuật ngữ

| Thuật ngữ | Ý nghĩa |
|---|---|
| Hồ sơ bệnh nhân | Thông tin liên kết theo một người bệnh, có thể bao gồm nhiều lượt khám và dữ liệu theo thời gian |
| Tài khoản | Định danh để xác thực truy cập; không đồng nhất với hồ sơ bệnh nhân |
| Lượt khám | Một lần tiếp nhận và xử lý nghiệp vụ, thuộc đúng hồ sơ; lịch hẹn không tự tạo lượt khám |
| Bản dự thảo | Nội dung đang chuẩn bị, chưa được xác nhận chính thức |
| Bản xác nhận | Phiên bản do bác sĩ có quyền xác nhận; vẫn cần điều kiện công bố hoặc cho phép gửi |
| Nội dung đã công bố | Phần được chọn và cho phép bệnh nhân tương ứng xem |
| Diagnosis và Lab/Test | Hỗ trợ nhận định/phân loại và gợi ý cận lâm sàng, không thay kết luận hoặc chỉ định của bác sĩ |
| Treatment và MedSafety | Gợi ý phương án và rà soát thuốc theo phạm vi được duyệt, không tự kê/đổi/ngừng thuốc |
| Snapshot | Dữ liệu hoặc tham chiếu phiên bản đầu vào dùng cho một lần đánh giá |
| Giao dịch tích hợp | Một lần nhận/gửi dữ liệu cùng mã tham chiếu, nguồn/đích, trạng thái và phản hồi |
| Synthetic | Dữ liệu giả lập không chứa thông tin định danh bệnh nhân thật |
| HIS/EMR, LIS, PACS/RIS | Hệ thống bệnh viện/bệnh án, xét nghiệm và hình ảnh/chẩn đoán hình ảnh ngoài sản phẩm |

## 2 Mô tả tổng quan

### 2.1 Bài toán và mục tiêu nghiệp vụ

Hệ thống liên kết dữ liệu đúng bệnh nhân và lượt khám, giúp người có quyền nhận biết dữ liệu thiếu, xem diễn biến, đối chiếu gợi ý và ghi quyết định. Bác sĩ chịu trách nhiệm lâm sàng cuối cùng. Khảo sát thực tế bệnh viện chưa hoàn tất. Thông tin trong báo cáo về hệ thống eHealth tại Bệnh viện Hữu Nghị là thông tin nhóm cung cấp, chưa được sử dụng làm kết quả khảo sát độc lập hoặc bằng chứng hệ thống này có kết nối.

| Mã | Mục tiêu | Nhóm FR liên quan |
|---|---|---|
| OB1 | Quản lý đúng hồ sơ và lượt khám | FR01, FR04 đến FR06 |
| OB2 | Theo dõi diễn biến theo thời gian | FR07, FR25, FR27 đến FR34 |
| OB3 | Tích hợp và trao đổi dữ liệu bệnh viện, kiểm chứng mô phỏng | FR08 đến FR15, FR41 |
| OB4 | Hỗ trợ đánh giá và bổ sung bằng chứng | FR16 đến FR19, FR24 đến FR26 |
| OB5 | Hỗ trợ điều trị và an toàn thuốc | FR20 đến FR23, FR27 đến FR31 |
| OB6 | Theo dõi, tái khám và bàn giao | FR07, FR29 đến FR34, FR38 đến FR39 |
| OB7 | Hỗ trợ bệnh nhân | FR02 đến FR03, FR35 đến FR40 |

FR42 đến FR46 là các chức năng quản trị và hỗ trợ truy cập phục vụ các mục tiêu trên. Bảng này là ánh xạ phân tích trong SRS, không phải số liệu bao phủ đã nghiệm thu.

### 2.2 Người dùng và các bên liên quan

| Nhóm | Trách nhiệm và phạm vi |
|---|---|
| Bác sĩ | Xem bệnh án, ghi/kiểm dữ liệu theo quyền; yêu cầu hỗ trợ; xác nhận kết luận, chỉ định, phương án và kế hoạch |
| Nhân viên y tế được phân quyền | Tiếp nhận, xác nhận hành chính, ghi dữ liệu, hỗ trợ chuyên môn theo phân công; mỗi công việc có quyền riêng |
| Bệnh nhân | Đăng ký/đăng nhập, đặt/xem lịch, xem nội dung đã công bố và nhận nhắc của bản thân |
| Quản trị kỹ thuật | Quản lý tài khoản, quyền, danh mục/cấu hình và nhật ký theo phân công; không tự có quyền phê duyệt y khoa |
| Người có thẩm quyền chuyên môn | Rà soát và chấp thuận nội dung/quy tắc/mô hình theo thẩm quyền; không mặc nhiên là vai trò tài khoản mới |
| Dịch vụ tích hợp và nguồn/đích ngoài | Cung cấp/nhận dữ liệu theo giao diện, danh tính và quyền kỹ thuật đã chốt |

Điều dưỡng, dược sĩ và nhân viên tiếp đón có thể là các chức danh trong nhóm nhân viên y tế. Không đồng nhất mọi nhân viên có cùng quyền. Quyền xem, nhập, sửa, xác nhận, công bố, gửi lại và xử lý giao dịch phải được phân biệt. Ma trận gán quyền theo chức danh cụ thể là TBD.

Đại diện bệnh viện và người có chuyên môn góp ý nghiệp vụ, dữ liệu và quy tắc; giảng viên hướng dẫn, giám sát và đánh giá; nhóm thực hiện phân tích, thiết kế, phát triển và kiểm thử. Vai trò bên liên quan không tự tạo quyền truy cập phần mềm. Customer cụ thể và người có quyền chấp nhận sản phẩm cần được xác nhận.

### 2.3 Quy trình nghiệp vụ

1. Bệnh nhân đặt lịch hoặc đến khám trực tiếp.
2. Nhân sự có nhiệm vụ tiếp nhận, xác nhận thông tin; người có trách nhiệm chuyên môn xem xét nhu cầu xử trí khẩn và chuyển hướng phù hợp khi cần.
3. Tìm/liên kết/tạo đúng hồ sơ và mở lượt khám; xác minh liên kết tài khoản theo quy trình riêng.
4. Bác sĩ hoặc nhân viên có quyền ghi bệnh sử, sinh hiệu, thuốc, kết quả và đánh giá lão khoa khi phù hợp.
5. Diagnosis hỗ trợ nhận định; bác sĩ xem dữ liệu và gợi ý Lab/Test để quyết định chỉ định.
6. Nhận kết quả mới vào đúng lượt khám và đánh giá lại khi cần.
7. Bác sĩ ghi kết luận hoặc chưa đủ bằng chứng.
8. Treatment gợi ý phương án; MedSafety rà soát dữ liệu và thuốc liên quan.
9. Bác sĩ điều chỉnh, xem xét lại và xác nhận kế hoạch.
10. Hoàn tất ngoại trú hoặc ghi tóm tắt hướng nhập viện/chuyển tuyến/ra viện trong phạm vi được cung cấp.
11. Công bố nội dung được phép; ghi trả theo quyền; thông báo, nhắc và tái khám theo kế hoạch hiện hành.

Chuỗi module có thể lặp khi dữ liệu hoặc phương án đổi, không buộc mọi ca chạy đủ bốn module. Gợi ý cận lâm sàng không phải kết quả thực đo; gợi ý điều trị không phải đơn chính thức.

### 2.4 Kiến trúc định hướng và ranh giới

Theo thiết kế báo cáo, web React và TypeScript phục vụ nhân viên, app React Native phục vụ bệnh nhân; backend Python/FastAPI chứa nghiệp vụ, bốn module Python và Integration Adapter. PostgreSQL lưu dữ liệu; worker Python/APScheduler xử lý nhắc và thông báo theo lịch. File storage bằng Docker volume và Docker Compose là lựa chọn thiết kế dự kiến.

Đặc tả không bắt buộc tách bốn module thành bốn máy chủ hay microservice. Hình C4 mức C2 mới đặt các module trong backend. Chi tiết triển khai file storage, worker, nền tảng app, kênh thông báo và đóng gói cần được hoàn thiện khi thiết kế triển khai.

Khi chưa tích hợp, bệnh án của sản phẩm là nơi nhập/cập nhật chính của demo. Khi tích hợp, HIS/EMR giữ nguồn chính của bệnh án viện; LIS và PACS/RIS giữ nguồn dữ liệu tương ứng. Không ghi đè toàn bộ bệnh án khi chỉ được phép gửi một phần nội dung.

### 2.5 Giả định và ràng buộc

- Ban đầu dùng dữ liệu giả lập; nếu được cấp dữ liệu bệnh viện phải có điều kiện sử dụng và quyền phù hợp. Không đưa dữ liệu định danh thật vào fixture demo.
- Kết nối nguồn viện chưa được mặc định có sẵn. Đặc tả định danh, chuẩn bản tin, xác thực và phạm vi ghi trả phải được các bên thống nhất.
- Quy tắc/mô hình có nguồn, phiên bản, đối tượng, điều kiện và xử lý thiếu dữ liệu; phải được rà soát trước áp dụng.
- Không tự học lại từ phản hồi bác sĩ. Dự báo nguy cơ chỉ bật khi có phương pháp và kiểm định phù hợp.
- Bác sĩ xác nhận quyết định lâm sàng; admin kỹ thuật không tự có quyền này.
- Số liệu hiệu quả, độ đúng và hiệu năng chỉ được công bố sau khi có bộ thử, môi trường và kết quả tương ứng.

## 3 Yêu cầu giao diện bên ngoài

### 3.1 Giao diện người dùng

- Web tiếng Việt cho nhân viên và quản trị; nhận diện người bệnh, lượt khám và trạng thái đang thao tác.
- Màn hình bệnh viện mở/nhúng theo ngữ cảnh HIS/EMR phải xác thực người dùng, thông tin truyền sang và quyền trước khi cho thao tác.
- App bệnh nhân dùng chung dịch vụ/dữ liệu lịch và kế hoạch với backend; chỉ hiện nội dung được phép của đúng tài khoản đã liên kết.
- Giao diện phân biệt loading, rỗng, lỗi, thiếu dữ liệu, dự thảo, đã xác nhận và đã công bố; không suy ra bình thường/an toàn từ kết quả rỗng hoặc lỗi.
- Luồng chính dùng được khi phóng to 200% trên web; cảnh báo không chỉ dựa vào màu. Trình duyệt/thiết bị và phiên bản thuộc bộ thử TBD.

### 3.2 Giao diện tích hợp

| Nguồn hoặc đích | Dữ liệu và quan hệ cần hỗ trợ |
|---|---|
| HIS/EMR | Nhận bệnh án/ngữ cảnh; gửi phần kết luận, kế hoạch hoặc đơn đã xác nhận và được cho phép; nhận phản hồi |
| LIS | Nhận kết quả xét nghiệm và nguồn, mã tham chiếu, thời điểm, đơn vị phù hợp |
| PACS/RIS | Nhận báo cáo, chỉ số hoặc tham chiếu hình ảnh theo phạm vi nguồn cung cấp |
| Nguồn và đích mô phỏng | Kiểm chứng cùng lõi nghiệp vụ trước khi thay bằng kết nối thực |

Chưa chốt giao thức/chuẩn bản tin, cấu trúc payload, mã nguồn, quy tắc đối soát hoặc nhà cung cấp. Không mặc định đã triển khai FHIR, HL7, DICOM hay kết nối eHealth. Mỗi lần trao đổi cần lưu nguồn/đích, tham chiếu, thời điểm, trạng thái và bằng chứng phản hồi.

### 3.3 API ứng dụng và thông báo

API web/app cần thực thi quyền ở máy chủ, validation, kiểm phiên bản/cập nhật đồng thời và trả lỗi đủ rõ để người dùng sửa. Chi tiết endpoint, schema, mã HTTP và cơ chế xác thực sẽ được cập nhật trong hợp đồng OpenAPI tương ứng SRS này. Không coi OpenAPI của demo cũ là hợp đồng hoàn chỉnh cho FR01 đến FR46 mới.

Kênh thông báo, múi giờ, chính sách tạo/gửi/thử lại/lưu giữ là TBD. Trạng thái đã tạo, đã gửi, đã tiếp nhận và đã đọc phải phản ánh bằng chứng thực tế của kênh; không suy đã uống thuốc từ trạng thái thông báo.

## 4 Yêu cầu chức năng

Hệ thống phải đáp ứng các yêu cầu dưới đây trong phạm vi được chốt cho từng đợt triển khai. Mỗi hàng gồm hành vi cần có và điều kiện để kiểm tra. Những nội dung còn phụ thuộc quyết định của nhóm hoặc bệnh viện được liệt kê tại mục 10.

### 4.1 Hồ sơ bệnh án và lượt khám

| Mã và ưu tiên | Yêu cầu | Tiêu chí nghiệm thu |
|---|---|---|
| FR01 P1 | Tra cứu/tạo hồ sơ bằng số định danh, mã hồ sơ hoặc thông tin người bệnh; tự cấp mã, lưu hành chính và thời điểm tạo | Kiểm tra trùng số định danh; cho tạo khi thiếu định danh hoặc dữ liệu chuyên môn và bổ sung sau; giữ lịch sử |
| FR02 P3 | Liên kết tài khoản với đúng bệnh án sau xác minh; chỉ cho xem nội dung đã công bố | Chưa xác minh hoặc thông tin không khớp thì không cấp quyền; CCCD đơn lẻ không đủ bằng chứng |
| FR03 P3 | Quản lý khung giờ, sức chứa, đơn vị khám; tạo/tra cứu/cập nhật lịch chung tại quầy và app | Không vượt sức chứa; thay đổi đồng bộ; đặt lịch không tự tạo lượt khám |
| FR04 P1 | Tiếp nhận, mở/liên kết lượt đúng hồ sơ; quản lý chờ xử lý, đang xử lý, hoàn tất | Hoàn tất khi đã lưu và xác nhận nội dung bắt buộc hoặc nêu lý do thiếu; xem hồ sơ không tự bắt đầu lượt |
| FR05 P1 | Ghi bệnh sử, triệu chứng, dấu hiệu, sinh hiệu, tiền sử, dị ứng, thuốc; đánh giá lão khoa khi phù hợp | Đúng hồ sơ/lượt/mốc cập nhật, có người/thời điểm; tách chưa đánh giá với bình thường; module dùng chung bệnh án |
| FR06 P1 | Ghi chỉ định do bác sĩ quyết định; nhập/nhận và cập nhật kết quả xét nghiệm/thăm dò đúng lượt | Phân biệt gợi ý, chỉ định, kết quả; có nguồn/thời điểm/đơn vị; dùng được để đánh giá lại |
| FR07 P1 | Tra cứu dữ liệu khám, thuốc, kết luận, kế hoạch theo thời gian; xem liên kết/tóm tắt bàn giao được cung cấp | Đúng lượt/đợt, thời điểm và phiên bản; không trình bày dữ liệu cũ như mới; không mở rộng sang quản lý nội trú toàn diện |

### 4.2 Tích hợp và tiền xử lý dữ liệu

| Mã và ưu tiên | Yêu cầu | Tiêu chí nghiệm thu |
|---|---|---|
| FR08 P1 | Nhận bệnh án HIS/EMR, xét nghiệm LIS, báo cáo/chỉ số/tham chiếu PACS/RIS; lưu nguồn và các mốc thời gian | Truy được dữ liệu gốc/tham chiếu; dữ liệu không đọc được có lỗi rõ; không buộc đủ ba nguồn mỗi ca |
| FR09 P1 | Đối chiếu mã nguồn, số định danh khi có và liên kết xác minh để gắn đúng hồ sơ/lượt/đợt | Không khớp hoặc mơ hồ phải giữ chờ; không tự chọn lượt hoặc tạo trùng do khác mã nguồn |
| FR10 P1 | Kiểm cấu trúc, kiểu, trường bắt buộc, giá trị, đơn vị và trạng thái dữ liệu | Chỉ rõ lỗi/thiếu; phân biệt hợp lệ, không hợp lệ, chưa có, không áp dụng; không điền thiếu thành 0/bình thường |
| FR11 P1 | Chuẩn hóa trường, mã thuốc/xét nghiệm, đơn vị và ngày giờ; lưu dấu vết và cập nhật khi đủ điều kiện | Truy được giá trị gốc/quy tắc; mã hoặc phép đổi chưa rõ giữ chờ; không tự sửa giá trị bất thường |
| FR12 P1 | Nhận biết dữ liệu đã xử lý và bản sửa; chống trùng, giữ phiên bản và quan hệ thay thế | Nhận lại không tạo bản mới; bản sửa giữ lịch sử; không mặc định bản đến sau đúng hơn |
| FR13 P1 | Ghi trả nội dung đã xác nhận và được cho phép tới HIS/EMR; lưu tham chiếu và phản hồi | Đúng phiên bản; không gửi dự thảo như chính thức; thành công có bằng chứng đích; thiếu phản hồi là chưa rõ |
| FR14 P1 | Tra cứu trao đổi theo tham chiếu, hồ sơ/lượt, nguồn/đích, thời gian, trạng thái; xem lỗi/lịch sử | Tìm được lần trao đổi và lý do lỗi; quyền tra cứu không tự gồm gửi lại hoặc sửa chuyên môn |
| FR15 P1 | Đối soát tại đích khi chưa rõ kết quả; xử lý/gửi lại sau khắc phục, giữ tham chiếu và lịch sử | Mất phản hồi sau khi đích lưu không gây trùng; sửa chuyên môn cần phiên bản/xác nhận phù hợp trước gửi |

### 4.3 Hỗ trợ chuyên môn

| Mã và ưu tiên | Yêu cầu | Tiêu chí nghiệm thu |
|---|---|---|
| FR16 P1 | Lấy dữ liệu bệnh án/lượt phù hợp; kiểm đối tượng và mức đủ dữ liệu cho Diagnosis | Thiếu hoặc ngoài đối tượng có thông báo cụ thể; chỉ tạo đầu ra được phép |
| FR17 P1 | Diagnosis cung cấp nhận định/phân loại theo đặc tả, căn cứ hoặc chưa đủ bằng chứng | Ca thử khớp kỳ vọng đã rà soát chuyên môn; dự báo nguy cơ chỉ bật khi có phương pháp và kiểm định |
| FR18 P1 | Lab/Test gợi ý xét nghiệm/thăm dò, lý do và ưu tiên từ bệnh án, Diagnosis liên quan và kết quả đã có | Gợi ý không tự thành chỉ định LIS/RIS hoặc kết quả xét nghiệm |
| FR19 P1 | Đánh giá lại khi có kết quả mới; xét thời điểm và điều kiện dùng kết quả cũ | Chạy lại tạo lần mới; không chặn xét nghiệm lặp chỉ vì từng làm khi thiếu quy tắc phù hợp |
| FR20 P1 | Treatment gợi ý phương án theo bệnh cảnh, phân loại, kết quả thực đo, bệnh đồng mắc, thuốc và quyết định liên quan | Không dùng đề xuất xét nghiệm như giá trị đo; gợi ý không tự thành đơn hoặc kế hoạch xác nhận |
| FR21 P1 | Hiển thị điều kiện cân nhắc, theo dõi và giới hạn áp dụng cùng phương án Treatment | Gắn đúng phương án; chưa có quyết định bác sĩ không tạo lịch/nhắc thuốc chính thức |
| FR22 P1 | MedSafety rà soát tương tác, chống chỉ định, trùng, liều/nguy cơ từ thuốc dự kiến/hiện dùng và dữ liệu liên quan | Ca thử đúng quy tắc duyệt; nêu thiếu dữ liệu quan trọng; không kết luận toàn bộ là an toàn |
| FR23 P1 | Hiển thị thuốc/yếu tố liên quan, mức cảnh báo, lý do, căn cứ và gợi ý xử lý nếu nguồn có | Truy được căn cứ/dữ liệu; ngưỡng được đặc tả; không tự đổi/ngừng thuốc hoặc liều |
| FR24 P1 | Sử dụng đầu ra liên quan theo chuỗi Diagnosis, Lab/Test, Treatment, MedSafety | Truy đầu vào/phiên bản; phân biệt thực đo, gợi ý và quyết định; không buộc đủ bốn module |
| FR25 P1 | Lưu từng lần chạy và đánh dấu cần xem lại khi dữ liệu liên quan đổi | Giữ đầu vào/tham chiếu, kết quả, thời điểm, phiên bản và căn cứ; giữ lịch sử; xác định bản bác sĩ đã xem |
| FR26 P1 | Báo module lỗi, hết thời gian hoặc ngoài phạm vi; giữ dữ liệu/dự thảo | Nêu rõ module chưa đánh giá được; không mất dữ liệu hoặc coi lỗi là bình thường/an toàn |

### 4.4 Kết luận và kế hoạch điều trị

Mã FR27 đến FR34 dưới đây khôi phục từ phần chức năng và User Stories của báo cáo, thay bảng lặp. Ý nghĩa nghiệp vụ có nguồn; việc chia thành tám mã là đề xuất chuẩn hóa cần nhóm duyệt.

| Mã và ưu tiên | Yêu cầu | Tiêu chí nghiệm thu |
|---|---|---|
| FR27 P1 | Bác sĩ ghi nhận kết luận lâm sàng hoặc chưa đủ bằng chứng và hướng xử trí | Phân biệt với gợi ý chưa xác nhận; lưu người/thời điểm. Nguồn chức năng 4.1 và US-30 |
| FR28 P1 | Bác sĩ lưu phản hồi đối với các gợi ý liên quan | Gắn đúng gợi ý/lần chạy; không sửa ngược đầu ra gốc. Nguồn US-31 |
| FR29 P1 | Bác sĩ lập dự thảo kế hoạch gồm phương pháp, thuốc, hướng dẫn, theo dõi và tái khám | Giữ trạng thái dự thảo trước xác nhận; liên kết căn cứ khi có. Nguồn chức năng 4.2 và US-32 |
| FR30 P1 | Bác sĩ điều chỉnh dự thảo kế hoạch trước khi xác nhận | Nội dung điều chỉnh thuộc đúng hồ sơ/lượt và dự thảo; không coi bản đang sửa là chính thức. Nguồn chức năng 4.2 và US-32 |
| FR31 P1 | Bác sĩ xác nhận phiên bản kế hoạch sau khi xem gợi ý và cảnh báo | Lưu phiên bản/người/thời điểm; chỉ bản đã xác nhận và được phép mới đủ điều kiện công bố/gửi. Nguồn US-33 |
| FR32 P1 | Ghi hướng chăm sóc ngoại trú hoặc tóm tắt nhập viện/chuyển tuyến/ra viện được cung cấp | Đúng hồ sơ, giữ liên kết lịch sử; không tự giả định quản lý giường hoặc chăm sóc nội trú. Nguồn US-34 |
| FR33 P3 | Người có quyền chọn phần kết quả/kế hoạch/thuốc/hướng dẫn đã xác nhận được phép cung cấp | Không chọn dự thảo; xác định đúng người bệnh và nội dung được phép. Nguồn chức năng 4.3 và US-35 |
| FR34 P3 | Công bố phần nội dung được chọn cho đúng bệnh nhân | Chỉ nội dung được phép hiển thị; không lộ dự thảo hoặc dữ liệu bệnh nhân khác. Nguồn chức năng 4.3, US-35 và BDD US-36 |

### 4.5 Hỗ trợ bệnh nhân ngoại trú

| Mã và ưu tiên | Yêu cầu | Tiêu chí nghiệm thu |
|---|---|---|
| FR35 P3 | Bệnh nhân nhập thông tin cơ bản, chọn khám mới/tái khám, cơ sở/đơn vị, ngày/khung giờ còn chỗ, xem mã/trạng thái | Lịch quầy/app thống nhất; chỉ xem lịch mình; đặt đồng thời chỗ cuối chỉ xác nhận một lịch |
| FR36 P3 | Bệnh nhân xem lượt khám, kết quả, kế hoạch thuốc, hướng dẫn/theo dõi/tái khám đã công bố | Đúng người/phạm vi, có ngày khám và thời điểm áp dụng; không lộ dự thảo, không sửa lâm sàng, không hiển thị bản cũ như hiện hành |
| FR37 P3 | Tạo/hiển thị thông báo theo sự kiện đã chọn; quản lý chưa đọc/đã đọc | Đúng người, không trùng sự kiện; mở nội dung kiểm quyền hiện hành; đã đọc không chứng minh đã thực hiện/uống thuốc |
| FR38 P3 | Nhắc lịch hẹn đã xác nhận theo thời điểm chọn; cập nhật/hủy nhắc tương lai khi lịch đổi | Đúng lịch/thời điểm; không nhắc lịch cũ đã đổi/hủy; trạng thái tạo/gửi đúng kênh kiểm thử |
| FR39 P3 | Nhắc theo kế hoạch thuốc hiện hành đã xác nhận, được phép cung cấp và đủ lịch dùng | Đúng thuốc/lịch; đổi/ngừng phải cập nhật/hủy nhắc tương lai; thiếu lịch yêu cầu bổ sung, không suy giờ hay đánh dấu đã uống |

### 4.6 Quản trị và truy cập

| Mã và ưu tiên | Yêu cầu | Tiêu chí nghiệm thu |
|---|---|---|
| FR40 P1 | Bệnh nhân đăng ký; người có quyền cấp/quản lý tài khoản nhân viên; đăng nhập/đăng xuất, cập nhật và khóa/mở | Tài khoản khóa bị chặn; bệnh nhân không tự thành bác sĩ; chỉ xem bệnh án sau liên kết xác minh |
| FR41 P1 | Mở đúng người bệnh/lượt từ HIS/EMR sau kiểm người dùng, ngữ cảnh và quyền | Màn hình mô phỏng mở đúng ca; giả ngữ cảnh không vượt quyền; hết phiên xác thực lại |
| FR42 P1 | Thiết lập, cấp, đổi, thu hồi vai trò/quyền theo công việc, hồ sơ và thao tác | Kiểm giao diện/giao tiếp dữ liệu/tệp; thu hồi áp dụng theo chính sách phiên; quyền kỹ thuật không tự cho xác nhận chuyên môn |
| FR43 P1 | Quản lý danh mục thuốc, xét nghiệm, đơn vị, cơ sở/khoa và mã ánh xạ; trạng thái/phiên bản khi cần | Mã ngừng dùng không chọn mới nhưng lịch sử đọc được; danh mục chuyên môn có nguồn và rà soát |
| FR44 P1 | Quản lý thiết lập kết nối, chính sách nhắc và phiên bản quy tắc/mô hình được phép | Thay đổi có dấu vết; bản chuyên môn mới chỉ dùng sau rà soát đúng thẩm quyền; truy bản kết quả cũ |
| FR45 P1 | Ghi/tra nhật ký thao tác, thay đổi, truy cập nhạy cảm, lỗi quyền theo sự kiện chọn | Tra theo người/thời gian/thao tác/đối tượng, thay đổi trước/sau và tham chiếu khi có; không lộ dữ liệu ngoài quyền |
| FR46 P2 | Khôi phục truy cập qua kênh xác minh hoặc người hỗ trợ có quyền | Thiếu bằng chứng không khôi phục/đổi liên kết; CCCD/mã hồ sơ đơn lẻ không đủ; hỗ trợ có dấu vết |

## 5 Yêu cầu chất lượng

Giữ nội dung và ưu tiên của 13 NFR trong báo cáo mới. Những tiêu chí chưa có ngưỡng số hoặc chính sách chốt phải được hoàn thiện trước nghiệm thu. Không kế thừa mặc định mục tiêu 2 giây, 10 giây, 30 phút hoặc số người dùng của SRS cũ.

| Mã và ưu tiên | Yêu cầu và tiêu chí kiểm tra | Thông tin còn cần chốt |
|---|---|---|
| NFR01 P1 | Đúng quyền, bảo vệ tài khoản/phiên; từ chối trái quyền, đăng xuất/hết hạn/khóa có hiệu lực | Ma trận quyền, chính sách phiên và hiệu lực thu hồi |
| NFR02 P1 | Bảo vệ dữ liệu khi truyền/lưu/log/thông báo; không lộ mật khẩu hoặc bệnh án ngoài quyền; môi trường thử tách biệt | Cấu hình bảo mật, lưu giữ, quyền sử dụng và kênh thông báo |
| NFR03 P1 | Đúng hồ sơ/lượt, nhất quán và kiểm soát sửa đồng thời; không ghi nhầm/ghi đè âm thầm khi lỗi | Bộ ca sai liên kết, cạnh tranh và lỗi giao dịch |
| NFR04 P1 | Nhận/gửi lại không trùng; nhắc không mất khi restart; trạng thái gửi đúng thực tế | Khóa chống trùng, lưu trạng thái, chính sách thử lại và đối soát |
| NFR05 P1 | Truy nguồn/thời điểm/phiên bản/người; xem dữ liệu cũ đúng phiên bản; người dùng nghiệp vụ không sửa/xóa audit | Danh sách sự kiện, lưu giữ và quyền bảo trì audit |
| NFR06 P1 | AI hỗ trợ theo điều kiện, bác sĩ quyết định; thiếu dữ liệu/lỗi không coi là an toàn; không tự kê/ngừng | Bộ ca an toàn và điều kiện cho phép xử lý tiếp |
| NFR07 P1 | Quy tắc chuyên môn có nguồn, phiên bản, test và rà soát; bản chưa duyệt không chạy; quay lại bản chấp thuận; không tự học lại | Người duyệt, quy trình chuyển phiên bản và bộ ca chuẩn |
| NFR08 P2 | Phản hồi, chạy module, tạo nhắc theo ngưỡng đã thống nhất; đo tải, dữ liệu, cấu hình, thời gian, lỗi và phụ thuộc ngoài | Toàn bộ ngưỡng số, tải đồng thời, tập dữ liệu, cách lấy mẫu và tiêu chí đạt là TBD |
| NFR09 P1 | Có backup/restore; nhận biết lỗi, không mất dữ liệu đã lưu; thử dừng dịch vụ, đối chiếu sau restore và chức năng độc lập | RTO, RPO, lịch backup, lưu giữ và kịch bản gián đoạn |
| NFR10 P2 | Tiếng Việt, rõ ca/trạng thái, thuận tiện; luồng chính dùng được khi phóng to 200%, cảnh báo không chỉ bằng màu | Danh sách luồng, môi trường và tiêu chí usability bổ sung |
| NFR11 P2 | Luồng chính hoạt động trên Chrome, Edge và nền tảng app được chọn | Phiên bản trình duyệt, hệ điều hành, thiết bị và bộ luồng |
| NFR12 P1 | Trao đổi đúng đặc tả; đổi nguồn mô phỏng sang nguồn viện trên cùng lõi; đúng trường/mã/đơn vị/phản hồi | Hợp đồng dữ liệu/adapter, chuẩn bản tin, nguồn thử và quyền kết nối |
| NFR13 P1 | Cài lại môi trường sạch; mỗi FR/NFR P1 đã chốt có ca thử và kết quả tương ứng | Bộ dependency, cấu hình triển khai và ma trận truy vết cuối |

NFR là yêu cầu chất lượng, không phải báo cáo kết quả đã đạt. Chưa đủ dữ liệu để tự công bố SLA, độ nhạy/đặc hiệu, tỷ lệ sai sót hay mục tiêu lâm sàng.

### 5.1 Đối chiếu nhóm chất lượng ISO 25010

Bảng sau đối chiếu nội dung yêu cầu với chín nhóm của ISO/IEC 25010:2023. Đây là cách phân nhóm phục vụ rà soát; không bổ sung ngưỡng nghiệm thu hoặc chứng nhận sản phẩm đã đáp ứng tiêu chuẩn.

| Nhóm chất lượng | Yêu cầu liên quan |
|---|---|
| Functional suitability là tính phù hợp chức năng | Danh mục FR và các tiêu chí về kết quả đúng, đặc biệt FR17, FR22; cần bộ ca chuẩn chuyên môn |
| Performance efficiency là hiệu năng | NFR08; các ngưỡng số còn phải chốt |
| Compatibility là khả năng cùng tồn tại và liên thông | NFR12 và hợp đồng trao đổi dữ liệu |
| Interaction capability là khả năng tương tác với người dùng | NFR10, gồm phóng to 200% và cảnh báo không chỉ bằng màu |
| Reliability là độ tin cậy | NFR03, NFR04, NFR09 |
| Security là bảo mật | NFR01, NFR02; phần trách nhiệm và bảo vệ nhật ký của NFR05 |
| Maintainability là khả năng bảo trì | NFR07, NFR13 và truy vết phiên bản |
| Flexibility là khả năng thích ứng | NFR11, NFR12, NFR13 trong việc thay môi trường hoặc nguồn |
| Safety là an toàn | NFR06, NFR07 và giới hạn sử dụng module chuyên môn |

Nguồn phân nhóm: [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) và [bản tiêu chuẩn được GSO tiếp nhận](https://gso-sims-preview-doc-aws.s3-eu-west-1.amazonaws.com/gso-iso-iec-25010-2025-en.html). Một yêu cầu có thể liên quan nhiều nhóm; việc có mặt trong bảng không thay thế kiểm chứng từng tiêu chí.

## 6 Dữ liệu và quy tắc nghiệp vụ

### 6.1 Các nhóm dữ liệu logic

| Nhóm | Nội dung phải quản lý theo yêu cầu |
|---|---|
| Tài khoản và quyền | Trạng thái tài khoản, vai trò/quyền công việc, phiên, liên kết hồ sơ và dấu vết xác minh |
| Bệnh nhân và lượt khám | Mã hồ sơ/định danh khi có, hành chính, tiền sử, lượt/đợt, trạng thái và dữ liệu theo thời gian |
| Lịch hẹn | Cơ sở/đơn vị, khung giờ/sức chứa, yêu cầu đặt, mã/trạng thái và thay đổi |
| Lâm sàng và cận lâm sàng | Giá trị, kiểu/trạng thái, đơn vị, thời điểm, nguồn, người ghi, chỉ định, kết quả và phiên bản |
| Thuốc và kế hoạch | Thuốc hiện dùng/dự kiến, dị ứng, phương án/dự thảo, bản xác nhận, hướng dẫn, lịch áp dụng và tái khám |
| Kết quả hỗ trợ | Module, lần chạy, snapshot/tham chiếu, điều kiện, đầu ra, thiếu dữ liệu, căn cứ, phiên bản, lỗi và phản hồi bác sĩ |
| Trao đổi dữ liệu | Nguồn/đích, tham chiếu gốc, dữ liệu gốc/chuẩn hóa, trạng thái, phản hồi, phiên bản thay thế, đối soát và lần thử |
| Công bố và thông báo | Nội dung được chọn, người bệnh được xem, thời điểm, sự kiện/nhắc, phiên bản kế hoạch, trạng thái tạo/gửi/đọc |
| Nhật ký | Người/dịch vụ, thời điểm, đối tượng, thao tác, trước/sau và tham chiếu theo sự kiện được chọn |

Đây là mô hình thông tin logic, không phải DDL hoặc cam kết số bảng. Kiểu, trường bắt buộc, danh mục, miền giá trị, phép đổi và chính sách lưu giữ sẽ được chốt trong Data Dictionary tương ứng SRS mới.

### 6.2 Quy tắc bất biến cần kiểm tra

1. Tài khoản, hồ sơ và lượt khám là ba khái niệm khác nhau; liên kết tài khoản cần xác minh, CCCD đơn lẻ không đủ để cấp quyền.
2. Đặt lịch không tự sinh lượt khám; hoàn tất lượt không đóng toàn bộ bệnh án.
3. Không dùng dữ liệu thiếu/không hợp lệ làm 0 hoặc bình thường; giữ phân biệt chưa có, không áp dụng và chưa đánh giá.
4. Dữ liệu đã đến sau không tự được ưu tiên hơn dữ liệu có nguồn/thời điểm phù hợp; bản sửa giữ lịch sử.
5. Gợi ý, chỉ định, kết quả thực đo, kết luận bác sĩ và kế hoạch chính thức không được thay thế lẫn nhau.
6. Đầu ra module cũ giữ đầu vào và phiên bản; dữ liệu liên quan đổi phải xem lại bản đang chờ xác nhận theo FR25.
7. Chỉ nội dung đã xác nhận và đủ quyền mới được gửi/công bố; xác nhận không tự cấp quyền công bố mọi nội dung.
8. Giao dịch thiếu phản hồi có trạng thái chưa rõ; không báo thành công khi chưa có bằng chứng đích và không gửi lại gây trùng.
9. Nhắc dựa trên lịch/kế hoạch hiện hành; không tự suy giờ uống, không đánh dấu bệnh nhân đã uống từ trạng thái gửi/đọc.
10. Quyền kỹ thuật và quyền chuyên môn tách biệt; không tự thêm quyền dựa vào chức danh hoặc vai trò bên liên quan.

## 7 Các Use Case chính

### 7.1 Danh mục

| Mã | Use Case | Tác nhân và FR liên quan |
|---|---|---|
| UC01 | Xác thực và khôi phục truy cập | Bệnh nhân, nhân viên, người hỗ trợ có quyền; FR40, FR46 |
| UC02 | Quản lý và liên kết hồ sơ | Nhân viên có quyền, bệnh nhân trong bước xác minh; FR01 đến FR02 |
| UC03 | Quản lý và đặt lịch | Bệnh nhân, nhân viên có quyền; FR03, FR35 |
| UC04 | Tiếp nhận và cập nhật lượt khám | Nhân viên/bác sĩ có quyền; FR04 đến FR07 |
| UC05 | Tiếp nhận và chuẩn hóa nguồn | Dịch vụ tích hợp, nhân viên có quyền; FR08 đến FR12 |
| UC06 | Gửi và đối soát dữ liệu đã xác nhận | Dịch vụ tích hợp, người có quyền; FR13 đến FR15 |
| UC07 | Yêu cầu hỗ trợ chuyên môn | Bác sĩ; FR16 đến FR26 |
| UC08 | Ghi kết luận và xác nhận kế hoạch | Bác sĩ, nhân viên có quyền ở bước bàn giao; FR27 đến FR32 |
| UC09 | Công bố và xem thông tin | Bác sĩ/nhân viên có quyền, bệnh nhân; FR33 đến FR34, FR36 |
| UC10 | Thông báo và nhắc | Bệnh nhân, worker trong nội bộ hệ thống; FR37 đến FR39 |
| UC11 | Mở từ ngữ cảnh viện | Người dùng viện có quyền, HIS/EMR mô phỏng; FR41 |
| UC12 | Quản trị và truy vết | Quản trị, người có thẩm quyền chuyên môn theo thao tác; FR42 đến FR45 |

Danh mục UC được dựng từ báo cáo để truy vết, chưa phải mã UC cũ đã phê duyệt. Worker và CSDL là thành phần nội bộ, không vẽ thành actor ngoài sản phẩm. Không đặt quan hệ include đăng nhập cho mọi thao tác vì phiên hợp lệ là tiền điều kiện.

### 7.2 UC05 Tiếp nhận và chuẩn hóa nguồn

- Tiền điều kiện: nguồn được cấu hình, danh tính/quyền dịch vụ và hợp đồng dữ liệu hợp lệ.
- Luồng chính: nhận bản tin; lưu nguồn/tham chiếu/thời điểm; kiểm trùng/bản sửa; đối chiếu hồ sơ/lượt; kiểm cấu trúc/kiểu/miền; chuẩn hóa theo ánh xạ; cập nhật khi đủ điều kiện; lưu dấu vết/trạng thái.
- Ngoại lệ: bản tin không đọc được báo lỗi; định danh mơ hồ giữ chờ; phép đổi/mã chưa rõ giữ chờ; bản tin lặp không tạo dữ liệu mới.
- Hậu điều kiện: dữ liệu hoặc trạng thái chờ/lỗi có thể tra cứu, truy được gốc và lịch sử; không ghi nhầm người bệnh.

### 7.3 UC06 Gửi và đối soát dữ liệu

- Tiền điều kiện: có nội dung được bác sĩ xác nhận, đúng phiên bản và được cho phép gửi; người/dịch vụ có quyền.
- Luồng chính: lấy bản được phép; gắn tham chiếu; gửi tới đích; lưu phản hồi; cập nhật kết quả có bằng chứng.
- Ngoại lệ: thiếu phản hồi ghi chưa rõ; người có quyền đối soát theo tham chiếu; xử lý lại sau khắc phục không tạo trùng. Sửa chuyên môn phải quay về bản/xác nhận tương ứng.
- Hậu điều kiện: nội dung đã gửi và trạng thái thực tế truy vết được; không gửi dự thảo hoặc báo thành công không căn cứ.

### 7.4 UC07 Hỗ trợ chuyên môn

- Tiền điều kiện: bác sĩ có quyền trên hồ sơ/lượt; module và phiên bản đủ điều kiện áp dụng.
- Luồng chính: chọn module phù hợp; lấy snapshot; kiểm đối tượng/dữ liệu; tạo đầu ra trong phạm vi; hiển thị căn cứ/thiếu dữ liệu; lưu lần chạy; cho xem lại và chạy lại khi cần.
- Ngoại lệ: thiếu dữ liệu hạn chế đầu ra; lỗi/hết thời gian/ngoài đối tượng thông báo rõ, giữ dữ liệu; không coi lỗi là âm tính hoặc an toàn.
- Hậu điều kiện: có kết quả hoặc trạng thái chưa đánh giá được cùng dấu vết; không tự tạo chỉ định/đơn chính thức.

### 7.5 UC08 và UC09 Kế hoạch và công bố

- Tiền điều kiện: đúng hồ sơ/lượt, người có quyền tương ứng; bác sĩ đã xem dữ liệu/gợi ý liên quan khi xác nhận.
- Luồng chính: ghi kết luận/phản hồi; lập hoặc điều chỉnh dự thảo; bác sĩ xác nhận phiên bản; chọn nội dung được phép; công bố cho đúng bệnh nhân; bệnh nhân xem theo quyền hiện hành.
- Ngoại lệ: nội dung chưa xác nhận không được công bố; dữ liệu ảnh hưởng đến bản chờ xác nhận phải xem lại; chưa liên kết tài khoản thì không cấp quyền xem.
- Hậu điều kiện: phân biệt rõ gợi ý, dự thảo, bản xác nhận và phần công bố; giữ người/thời điểm/phiên bản liên quan.

### 7.6 UC03 và UC10 Lịch và nhắc

- Tiền điều kiện: bệnh nhân có quyền, khung giờ được cung cấp; nhắc dựa trên lịch xác nhận hoặc kế hoạch thuốc đủ thông tin và được phép.
- Luồng chính: kiểm lại sức chứa khi đặt; cấp mã/trạng thái; tạo nhắc theo chính sách; lưu trạng thái tạo/gửi/đọc theo kênh.
- Ngoại lệ: tranh chấp chỗ cuối chỉ xác nhận một lịch; đổi/hủy lịch hoặc kế hoạch cập nhật/hủy nhắc tương lai; thiếu giờ dùng yêu cầu bổ sung.
- Hậu điều kiện: lịch quầy/app nhất quán; không nhắc bản cũ hoặc dùng đã đọc làm bằng chứng tuân thủ.

### 7.7 UC01 Xác thực và khôi phục truy cập

- Tác nhân: bệnh nhân, nhân viên và người hỗ trợ được cấp quyền khôi phục.
- Tiền điều kiện: phương thức xác thực và quy trình cấp hoặc khôi phục tài khoản đã được thống nhất.
- Luồng chính: người dùng đăng nhập theo thông tin hợp lệ; hệ thống kiểm trạng thái và quyền, tạo phiên; khi đăng xuất thì kết thúc phiên theo chính sách. Nếu cần khôi phục, người dùng thực hiện qua kênh xác minh hoặc người hỗ trợ có quyền; hệ thống ghi nhận kết quả và dấu vết.
- Ngoại lệ: tài khoản khóa, thông tin không hợp lệ hoặc chưa đủ bằng chứng khôi phục thì không cấp truy cập. Bệnh nhân không tự cấp vai trò nhân viên. CCCD hoặc mã hồ sơ đơn lẻ không đủ để đổi liên kết.
- Hậu điều kiện: tài khoản và phiên phản ánh đúng quyền; có thể truy lại thao tác hỗ trợ. Đăng nhập thành công không tự thay thế bước xác minh liên kết bệnh án.

### 7.8 UC02 Quản lý và liên kết hồ sơ

- Tác nhân: nhân viên có quyền quản lý hồ sơ; bệnh nhân tham gia bước xác minh liên kết tài khoản.
- Tiền điều kiện: người thao tác có quyền phù hợp; đã có thông tin người bệnh cần tra cứu hoặc tạo.
- Luồng chính: tra cứu theo thông tin hiện có; kiểm trùng; tạo hồ sơ khi cần và cấp mã; bổ sung thông tin sau nếu chưa đủ. Khi liên kết tài khoản, kiểm chứng theo quy trình được chốt rồi giới hạn quyền xem vào nội dung đã công bố của đúng hồ sơ.
- Ngoại lệ: định danh mơ hồ hoặc xác minh chưa hoàn tất thì không tự liên kết; không bắt buộc đủ dữ liệu chuyên môn để tạo hồ sơ.
- Hậu điều kiện: có hồ sơ và lịch sử bổ sung phù hợp; liên kết truy cập chỉ được cấp sau xác minh.

### 7.9 UC04 Tiếp nhận và cập nhật lượt khám

- Tác nhân: bác sĩ hoặc nhân viên được phân quyền cho từng thao tác.
- Tiền điều kiện: xác định đúng hồ sơ; người thao tác có quyền tiếp nhận, ghi dữ liệu hoặc xác nhận tương ứng.
- Luồng chính: mở hoặc liên kết lượt; cập nhật dữ liệu đúng nguồn và thời điểm; ghi chỉ định do bác sĩ quyết định; nhận kết quả; tra cứu diễn biến; hoàn tất khi đủ nội dung bắt buộc hoặc đã ghi lý do thiếu theo quy trình.
- Ngoại lệ: liên kết không đúng hoặc dữ liệu không hợp lệ thì không ghi nhầm; xung đột cập nhật không được ghi đè âm thầm. Người dùng được hướng dẫn kiểm tra dữ liệu trước khi thực hiện lại.
- Hậu điều kiện: dữ liệu và trạng thái gắn đúng lượt; thông tin cũ vẫn truy được; hoàn tất lượt không kết thúc toàn bộ hồ sơ.

### 7.10 UC11 Mở từ ngữ cảnh bệnh viện

- Tác nhân: người dùng bệnh viện có quyền và hệ thống HIS/EMR mô phỏng hoặc được phép kết nối.
- Tiền điều kiện: có hợp đồng truyền ngữ cảnh và cơ chế xác thực được thống nhất.
- Luồng chính: tiếp nhận thông tin người dùng, người bệnh và lượt; kiểm tính hợp lệ, liên kết và quyền; mở đúng ngữ cảnh được phép.
- Ngoại lệ: thông tin bị giả, không khớp hoặc vượt quyền thì không cho truy cập dữ liệu; hết phiên thì yêu cầu xác thực lại.
- Hậu điều kiện: thao tác tiếp theo nằm trong đúng hồ sơ/lượt và quyền hiện hành; không dùng ngữ cảnh bên ngoài làm bằng chứng tự cấp quyền.

### 7.11 UC12 Quản trị và truy vết

- Tác nhân: quản trị kỹ thuật, người được giao quyền quản lý danh mục hoặc người có thẩm quyền chuyên môn, tùy thao tác.
- Tiền điều kiện: có quyền cụ thể đối với tài khoản, danh mục, cấu hình, phiên bản hoặc nhật ký cần xử lý.
- Luồng chính: người có quyền thực hiện thay đổi; hệ thống kiểm phạm vi và điều kiện, lưu dấu vết. Phiên bản chuyên môn chỉ được phép áp dụng sau rà soát đúng thẩm quyền. Người có quyền tra cứu nhật ký theo tiêu chí được hỗ trợ.
- Ngoại lệ: quyền kỹ thuật không cho phép xác nhận y khoa; mã đã ngừng dùng không được chọn mới; người dùng nghiệp vụ không được tự sửa hoặc xóa audit.
- Hậu điều kiện: cấu hình và quyền có hiệu lực theo chính sách; lịch sử cũ vẫn đọc được và truy đúng phiên bản đã sử dụng.

## 8 User Stories và truy vết

Các User Stories US-01 đến US-45 giữ mục đích như báo cáo hiện tại. Bảng dưới là liên kết đề xuất với bộ FR đã chuẩn hóa; kết quả kiểm thử theo mã mới chưa được tự gán là đạt.

| User Stories | FR tương ứng | Use Case |
|---|---|---|
| US-01, US-04 | FR01, FR02 | UC02 |
| US-02, US-03 | FR40 | UC01, UC12 |
| US-05, US-06 | FR03, FR35 | UC03 |
| US-07, US-08, US-09, US-10 | FR04, FR05, FR06, FR07 tương ứng | UC04 |
| US-11, US-12, US-13, US-14, US-15 | FR08, FR09, FR10, FR11, FR12 tương ứng | UC05 |
| US-16, US-17, US-18 | FR13, FR14, FR15 tương ứng | UC06 |
| US-19 đến US-29 | FR16 đến FR26 tương ứng theo thứ tự | UC07 |
| US-30, US-31 | FR27, FR28 | UC08 |
| US-32 | FR29, FR30 | UC08 |
| US-33, US-34 | FR31, FR32 | UC08 |
| US-35 | FR33, FR34 | UC09 |
| US-36 | FR36 | UC09 |
| US-37, US-38, US-39 | FR37, FR38, FR39 tương ứng | UC10 |
| US-40 | FR41 | UC11 |
| US-41, US-42, US-43, US-44 | FR42, FR43, FR44, FR45 tương ứng | UC12 |
| US-45 | FR46 | UC01 |

Mỗi ca thử thực thi cần ghi mã yêu cầu, dữ liệu đầu vào, môi trường, kết quả mong đợi, kết quả thực tế và trạng thái đạt/lỗi/bỏ qua/chưa chạy. Liên kết tới bảng/CSDL và endpoint chỉ bổ sung sau khi hợp đồng mới được đồng bộ; không lấy tên bảng/endpoint cũ làm bằng chứng đã hiện thực yêu cầu mới.

Bản ma trận theo từng mã được lưu trong [RTM SRS phiên bản 2](RTM_SRS_v2_0.csv), gồm 46 FR và 13 NFR. Trạng thái nghiệm thu của bộ mã mới được để mở cho đến khi hoàn tất ánh xạ và chạy ca thử tương ứng.

## 9 Tiêu chí nghiệm thu theo tình huống

Các kịch bản sau chuẩn hóa một số BDD trọng yếu từ báo cáo, là tiêu chí nghiệm thu, không phải kết quả test đã chạy. Toàn bộ 45 User Stories và 45 BDD của báo cáo được giữ trong các phụ lục ở cuối tài liệu. Ngoài các tình huống này, mỗi FR/NFR P1 đã chốt phải có ca thử theo NFR13.

| Mã | Bối cảnh và hành động | Kết quả mong đợi và FR |
|---|---|---|
| AC01 | Có hồ sơ chưa đủ định danh/chuyên môn; người có quyền tạo hoặc bổ sung | Không bắt buộc đủ dữ liệu lâm sàng để tạo; kiểm trùng và giữ lịch sử; FR01 |
| AC02 | Chưa xác minh liên kết hoặc chỉ cung cấp CCCD; yêu cầu xem bệnh án | Không cấp quyền; FR02, FR40 |
| AC03 | Hai yêu cầu đồng thời đặt chỗ cuối | Chỉ xác nhận một lịch, quầy/app cùng dữ liệu, không tự tạo lượt; FR03, FR35 |
| AC04 | Chỉ mở xem hồ sơ hoặc hoàn tất một lượt | Không tự bắt đầu lượt; không đóng toàn bộ hồ sơ; FR04, FR07 |
| AC05 | Nhận dữ liệu có mã hồ sơ/lượt không khớp | Giữ chờ, không chọn bừa hoặc tạo trùng; FR09 |
| AC06 | Dữ liệu lỗi, thiếu hoặc phép đổi chưa rõ | Chỉ rõ trường; không tự điền 0/bình thường hay sửa bất thường; FR10, FR11 |
| AC07 | Gửi lại bản tin cũ hoặc bản sửa nguồn | Không trùng; bản sửa giữ lịch sử và quan hệ thay thế; FR12 |
| AC08 | Đích đã lưu nhưng mất phản hồi; thực hiện đối soát/gửi lại | Ghi chưa rõ trước đối soát, không gửi trùng và giữ tham chiếu; FR13 đến FR15 |
| AC09 | Diagnosis thiếu dữ liệu hoặc ngoài đối tượng | Thông báo điều kiện cụ thể, hạn chế đầu ra; FR16, FR17 |
| AC10 | Có gợi ý cận lâm sàng và sau đó có kết quả mới | Gợi ý không tự thành chỉ định/kết quả; đánh giá lại tạo lần mới; FR18, FR19 |
| AC11 | Có Treatment nhưng chưa quyết định bác sĩ | Không tạo đơn/kế hoạch xác nhận/lịch nhắc chính thức; FR20, FR21 |
| AC12 | Thiếu dữ liệu quan trọng khi rà soát thuốc | Nêu thiếu/căn cứ, không kết luận toàn bộ an toàn hoặc tự đổi thuốc; FR22, FR23 |
| AC13 | Chỉ một số module phù hợp hoặc module lỗi | Không buộc chạy đủ; lỗi không thành âm tính, dự thảo còn nguyên; FR24, FR26 |
| AC14 | Dữ liệu liên quan đổi sau lần chạy | Giữ lần chạy cũ, đánh dấu bản chờ xác nhận cần xem lại; FR25 |
| AC15 | Bác sĩ phản hồi gợi ý và xác nhận kế hoạch | Lưu liên kết/phiên bản/người/thời điểm; không sửa ngược gợi ý; FR27 đến FR31 |
| AC16 | Chọn công bố dự thảo hoặc xem nội dung người khác | Không công bố dự thảo, không cấp quyền sai bệnh nhân; FR33, FR34, FR36 |
| AC17 | Lịch/kế hoạch đã đổi hoặc thiếu giờ uống | Hủy/cập nhật nhắc tương lai; không đoán giờ hoặc đánh dấu đã uống; FR38, FR39 |
| AC18 | Truyền ngữ cảnh viện giả hoặc phiên hết hạn | Không vượt quyền; yêu cầu xác thực lại khi cần; FR41 |
| AC19 | Thu hồi quyền hoặc dùng bản quy tắc chưa duyệt | Áp dụng quyền theo chính sách phiên; bản chưa được phép không chạy; FR42, FR44 |
| AC20 | Người dùng nghiệp vụ sửa audit hoặc khôi phục không đủ bằng chứng | Không cho sửa/xóa nhật ký hoặc đổi liên kết không xác minh; FR45, FR46 |

Nghiệm thu module thật cần bộ ca và đáp án được rà soát chuyên môn. Test stub chỉ xác nhận hợp đồng, điều phối và giới hạn trạng thái demo.

## 10 Các điểm cần xác nhận trước khi chốt

| Mã | Nội dung | Ảnh hưởng |
|---|---|---|
| TBD01 | Người đại diện chấp nhận sản phẩm và người rà soát chuyên môn | Phê duyệt phạm vi và quy tắc |
| TBD02 | Duyệt mã/việc tách FR27 đến FR34 và ưu tiên phần công bố | RTM, backlog, UC và BDD |
| TBD03 | Ma trận quyền theo tiếp đón, điều dưỡng, dược sĩ, bác sĩ, quản trị và xử lý tích hợp | FR04 đến FR07, FR14 đến FR15, FR32 đến FR34, FR42 |
| TBD04 | Quy trình định danh, xác minh liên kết, cấp/khôi phục tài khoản và chính sách phiên | FR02, FR40, FR41, FR46; NFR01 |
| TBD05 | Đặc tả nguồn, mã, chuẩn bản tin, đối soát, quyền ghi trả và ngữ cảnh viện | FR08 đến FR15, FR41; NFR12 |
| TBD06 | Data Dictionary, miền/đơn vị, ngưỡng, nguồn và phiên bản quy tắc; bộ ca chuyên môn | FR05 đến FR06, FR10 đến FR11, FR16 đến FR26 |
| TBD07 | Khung giờ, sức chứa, điều kiện cập nhật/hủy lịch; không tự dùng slot 30 phút của demo cũ | FR03, FR35, FR38 |
| TBD08 | Chính sách công bố, sửa/thu hồi, hiệu lực kế hoạch và dữ liệu người bệnh được xem | FR31, FR33 đến FR36 |
| TBD09 | Nền tảng app, trình duyệt/thiết bị, kênh/múi giờ/chính sách nhắc, thử lại và lưu giữ | FR37 đến FR39; NFR02, NFR04, NFR11 |
| TBD10 | Tải, dữ liệu, cấu hình, ngưỡng thời gian, tỷ lệ lỗi và cách đo | NFR08 |
| TBD11 | RTO, RPO, lịch backup, phạm vi lỗi thành phần và lưu giữ | NFR09 |
| TBD12 | Danh sách luồng accessibility/usability, danh sách sự kiện audit và kiểm thử cài sạch | NFR05, NFR10, NFR13 |

## 11 Quan hệ với hiện trạng triển khai

Tại commit Git đối chiếu, demo có web HTML/CSS/JavaScript do FastAPI phục vụ, PostgreSQL, năm vai trò kỹ thuật và một số luồng hồ sơ/portal. Bốn module vẫn mock_not_evaluated; chưa có bằng chứng triển khai React/TypeScript, React Native, tích hợp viện hai chiều hoặc worker thông báo theo kiến trúc mới.

Lần kiểm tra ngày 21/10/2026 ghi nhận 59 ca Python đạt, 1 lỗi đối chiếu OpenAPI và 4 ca PostgreSQL bỏ qua; 28 ca SQL/PGlite đạt. Đây là bằng chứng cho mã nguồn demo, không phải nghiệm thu 46 FR và 13 NFR mới. Số liệu chi tiết thuộc chương Kiểm thử và đánh giá; không đưa trạng thái test cũ vào RTM mới khi chưa ánh xạ.

## 12 Điều kiện chấp nhận và quản lý thay đổi

- Trước khi chốt baseline SRS, nhóm rà soát FR27 đến FR34 và giải quyết các TBD ảnh hưởng tới yêu cầu được chọn triển khai.
- Với mỗi FR/NFR P1 đã chốt, phải có ca thử, môi trường và kết quả tương ứng; ca bỏ qua hoặc chưa triển khai không được đánh dấu đạt.
- Thống kê độ bao phủ chỉ thực hiện khi mã yêu cầu, ưu tiên và liên kết test đã thống nhất. Không dùng số ca Python đạt để tuyên bố tỷ lệ hoàn thành sản phẩm.
- Thay đổi phạm vi hoặc quy tắc phải cập nhật SRS, backlog/US, BDD, UC, hợp đồng dữ liệu/API và test bị ảnh hưởng. Người rà soát và quyết định chấp thuận phải được ghi nhận theo quy trình nhóm thống nhất.
- Nguồn/mô hình/chức năng chưa có quyền hoặc chưa kiểm chứng tiếp tục ở trạng thái chưa sẵn sàng; không phát sinh nội dung hoặc kết luận lâm sàng thay cho bằng chứng thiếu.

## Phụ lục đối chiếu thay đổi chính

| Chủ đề | Bộ SRS cũ | Báo cáo hiện tại và SRS này |
|---|---|---|
| Phạm vi người bệnh | Ưu tiên nội trú, có ngoại trú | Ưu tiên khám/theo dõi ngoại trú; nội trú ở mức tóm tắt/bàn giao |
| Vai trò | Bác sĩ, điều dưỡng, dược sĩ, admin, bệnh nhân | Bác sĩ, nhân viên y tế theo công việc, bệnh nhân, quản trị; quyền cụ thể cần chốt |
| Mã yêu cầu | FR-01 đến FR-34, FR-P01 đến FR-P04 | FR01 đến FR46, có đề xuất phục hồi FR27 đến FR34; NFR01 đến NFR13 mang nội dung mới |
| Tích hợp | Nhận API mô phỏng | Nhận, đối chiếu, chuẩn hóa, chống trùng, ghi trả, phản hồi và đối soát |
| Bệnh nhân | Có chỉ số tại nhà, phản hồi đã uống/bỏ qua | Đặt/xem lịch, xem thông tin đã công bố và thông báo/nhắc; chưa mặc định nhật ký tuân thủ hoặc tự ghi chỉ số |
| Thiết kế | Tài liệu đích cũ có thể tách module dịch vụ | Báo cáo mới đặt bốn module trong backend, web/app và worker theo định hướng mới |
| NFR định lượng | Có các mức số của môi trường demo cũ | Giữ 200% zoom và tiêu chí báo cáo mới; NFR08, RTO/RPO và một số chính sách chờ chốt |


## Phụ lục A User Stories

Nội dung nhu cầu, vai trò và ưu tiên dưới đây được giữ theo 45 User Stories trong báo cáo nguồn. Liên kết FR và UC được bổ sung theo bộ mã SRS này.


### US-01 Quản lý hồ sơ


Vai trò: Nhân viên y tế được phân quyền. Ưu tiên: P1.


Tôi muốn tra cứu hoặc tạo hồ sơ bệnh nhân bằng số định danh, mã hồ sơ hoặc thông tin hiện có để quản lý đúng người bệnh.


Liên kết: FR01; UC02.


### US-02 Tài khoản và truy cập


Vai trò: Bệnh nhân / nhân viên y tế. Ưu tiên: P1.


Tôi muốn đăng ký hoặc đăng nhập và đăng xuất theo vai trò của mình để truy cập đúng chức năng được cấp.


Liên kết: FR40; UC01 / UC12.


### US-03 Quản lý tài khoản


Vai trò: Quản trị hệ thống. Ưu tiên: P1.


Tôi muốn tạo, cập nhật, khóa hoặc mở khóa tài khoản nhân viên để quản lý quyền truy cập theo phân công.


Liên kết: FR40; UC01 / UC12.


### US-04 Liên kết hồ sơ


Vai trò: Bệnh nhân. Ưu tiên: P3.


Tôi muốn liên kết tài khoản của mình với đúng bệnh án sau khi được xác minh để xem thông tin đã công bố của bản thân.


Liên kết: FR02; UC02.


### US-05 Lịch hẹn


Vai trò: Nhân viên y tế được phân quyền. Ưu tiên: P3.


Tôi muốn quản lý khung giờ, sức chứa và đơn vị khám để lịch đặt tại quầy và trên ứng dụng sử dụng cùng dữ liệu.


Liên kết: FR03; UC03.


### US-06 Lịch hẹn


Vai trò: Bệnh nhân. Ưu tiên: P3.


Tôi muốn chọn khung giờ còn chỗ, đặt lịch và xem mã/trạng thái lịch hẹn để chủ động đăng ký khám hoặc tái khám.


Liên kết: FR03, FR35; UC03.


### US-07 Tiếp nhận lượt khám


Vai trò: Nhân viên y tế được phân quyền. Ưu tiên: P1.


Tôi muốn mở hoặc liên kết lượt khám với đúng hồ sơ và cập nhật trạng thái để theo dõi tiến trình tiếp nhận, xử lý và hoàn tất.


Liên kết: FR04; UC04.


### US-08 Ghi nhận lâm sàng


Vai trò: Bác sĩ / nhân viên y tế được phân quyền. Ưu tiên: P1.


Tôi muốn ghi nhận bệnh sử, triệu chứng, dấu hiệu sinh tồn, bệnh đồng mắc, dị ứng, thuốc và đánh giá lão khoa khi phù hợp để có dữ liệu đầy đủ cho lượt khám.


Liên kết: FR05; UC04.


### US-09 Chỉ định và kết quả


Vai trò: Bác sĩ / nhân viên y tế được phân quyền. Ưu tiên: P1.


Tôi muốn ghi chỉ định do bác sĩ quyết định và nhập/nhận kết quả xét nghiệm, thăm dò vào đúng lượt khám để có thể đánh giá lại người bệnh.


Liên kết: FR06; UC04.


### US-10 Lịch sử bệnh án


Vai trò: Bác sĩ / nhân viên y tế được phân quyền. Ưu tiên: P1.


Tôi muốn xem dữ liệu khám, thuốc, kết luận và kế hoạch theo dòng thời gian để đối chiếu diễn biến giữa các lần khám.


Liên kết: FR07; UC04.


### US-11 Tiếp nhận dữ liệu


Vai trò: Nhân viên y tế / dịch vụ tích hợp. Ưu tiên: P1.


Tôi muốn hệ thống tiếp nhận dữ liệu từ HIS/EMR, LIS, PACS/RIS hoặc nguồn mô phỏng để dùng dữ liệu bệnh viện trong quy trình quản lý bệnh nhân.


Liên kết: FR08; UC05.


### US-12 Đối chiếu dữ liệu


Vai trò: Nhân viên y tế được phân quyền. Ưu tiên: P1.


Tôi muốn dữ liệu đầu vào được đối chiếu bằng mã nguồn, số định danh khi có và liên kết đã xác minh để tránh gắn nhầm bệnh nhân hoặc lượt khám.


Liên kết: FR09; UC05.


### US-13 Kiểm tra dữ liệu


Vai trò: Nhân viên y tế được phân quyền. Ưu tiên: P1.


Tôi muốn hệ thống kiểm tra cấu trúc, kiểu dữ liệu, trường bắt buộc, giá trị và đơn vị để nhận biết dữ liệu hợp lệ, sai, thiếu, chưa có hoặc không áp dụng.


Liên kết: FR10; UC05.


### US-14 Chuẩn hóa dữ liệu


Vai trò: Nhân viên y tế / dịch vụ tích hợp. Ưu tiên: P1.


Tôi muốn dữ liệu được chuẩn hóa theo quy tắc có thể truy vết để đối chiếu thuốc, xét nghiệm, đơn vị và thời gian nhất quán.


Liên kết: FR11; UC05.


### US-15 Chống trùng và phiên bản


Vai trò: Nhân viên y tế / dịch vụ tích hợp. Ưu tiên: P1.


Tôi muốn hệ thống nhận biết dữ liệu đã xử lý và bản sửa từ nguồn để tránh tạo bản ghi trùng nhưng vẫn giữ được lịch sử phiên bản.


Liên kết: FR12; UC05.


### US-16 Gửi dữ liệu đã xác nhận


Vai trò: Bác sĩ / dịch vụ tích hợp. Ưu tiên: P1.


Tôi muốn gửi kết luận, kế hoạch hoặc đơn thuốc đã được bác sĩ xác nhận và cho phép gửi tới HIS/EMR để các hệ thống liên quan nhận đúng phiên bản chính thức.


Liên kết: FR13; UC06.


### US-17 Theo dõi giao dịch tích hợp


Vai trò: Nhân viên kỹ thuật được phân quyền. Ưu tiên: P1.


Tôi muốn tra cứu giao dịch theo tham chiếu, hồ sơ/lượt, nguồn/đích, thời gian và trạng thái để xác định kết quả hoặc nguyên nhân lỗi.


Liên kết: FR14; UC06.


### US-18 Đối soát và gửi lại


Vai trò: Nhân viên kỹ thuật được phân quyền. Ưu tiên: P1.


Tôi muốn đối soát giao dịch chưa rõ kết quả và gửi lại sau khi khắc phục lỗi để xử lý sự cố mà không tạo dữ liệu trùng.


Liên kết: FR15; UC06.


### US-19 Diagnosis; quản lý kết luận


Vai trò: Bác sĩ. Ưu tiên: P1.


Tôi muốn hệ thống kiểm tra đối tượng áp dụng và mức đầy đủ của dữ liệu trước khi chạy Diagnosis để tránh tạo đầu ra ngoài điều kiện hỗ trợ.


Liên kết: FR16; UC07.


### US-20 Diagnosis; quản lý kết luận


Vai trò: Bác sĩ. Ưu tiên: P1.


Tôi muốn xem nhận định/phân loại suy tim cùng căn cứ hoặc trạng thái chưa đủ bằng chứng để có cơ sở xem xét kết luận lâm sàng.


Liên kết: FR17; UC07.


### US-21 Lab/Test; quản lý kế hoạch


Vai trò: Bác sĩ. Ưu tiên: P1.


Tôi muốn nhận gợi ý xét nghiệm/thăm dò kèm lý do và mức ưu tiên dựa trên bệnh án, kết quả Diagnosis liên quan và xét nghiệm đã có để cân nhắc chỉ định tiếp theo.


Liên kết: FR18; UC07.


### US-22 Lab/Test; đánh giá lại


Vai trò: Bác sĩ. Ưu tiên: P1.


Tôi muốn hệ thống đánh giá lại gợi ý cận lâm sàng khi có kết quả mới để cân nhắc thông tin mới và thời điểm của kết quả đã có.


Liên kết: FR19; UC07.


### US-23 Treatment; quản lý kế hoạch


Vai trò: Bác sĩ. Ưu tiên: P1.


Tôi muốn xem gợi ý phương án điều trị dựa trên bệnh cảnh, phân loại, kết quả thực đo, bệnh đồng mắc, thuốc và quyết định liên quan để xây dựng kế hoạch phù hợp.


Liên kết: FR20; UC07.


### US-24 Treatment; quản lý kế hoạch


Vai trò: Bác sĩ. Ưu tiên: P1.


Tôi muốn xem các điều kiện cần cân nhắc, giới hạn áp dụng và yêu cầu theo dõi đi kèm gợi ý điều trị để cá thể hóa kế hoạch cho người bệnh cao tuổi.


Liên kết: FR21; UC07.


### US-25 MedSafety; quản lý kế hoạch


Vai trò: Bác sĩ. Ưu tiên: P1.


Tôi muốn rà soát tương tác, chống chỉ định, trùng lặp, liều và nguy cơ dựa trên thuốc hiện dùng/dự kiến, dị ứng, bệnh đồng mắc và xét nghiệm để cân nhắc an toàn thuốc.


Liên kết: FR22; UC07.


### US-26 MedSafety; quản lý kế hoạch


Vai trò: Bác sĩ. Ưu tiên: P1.


Tôi muốn xem yếu tố/thuốc liên quan, mức cảnh báo, lý do, căn cứ và gợi ý xử lý khi có nguồn để tự đánh giá và quyết định bước tiếp theo.


Liên kết: FR23; UC07.


### US-27 Điều phối các module AI-CDSS


Vai trò: Bác sĩ. Ưu tiên: P1.


Tôi muốn hệ thống sử dụng đầu ra liên quan theo chuỗi Diagnosis → Lab/Test → Treatment → MedSafety nhưng chỉ chạy module phù hợp với tình huống để hỗ trợ quy trình linh hoạt.


Liên kết: FR24; UC07.


### US-28 Lịch sử AI-CDSS; quản lý kết luận/kế hoạch


Vai trò: Bác sĩ. Ưu tiên: P1.


Tôi muốn xem lại từng lần chạy cùng đầu vào, tham chiếu, kết quả, căn cứ/cảnh báo, thời điểm và phiên bản quy tắc/mô hình để hiểu kết quả đã được tạo ra như thế nào.


Liên kết: FR25; UC07.


### US-29 Xử lý lỗi AI-CDSS


Vai trò: Bác sĩ. Ưu tiên: P1.


Tôi muốn được thông báo khi module lỗi, hết thời gian hoặc không hỗ trợ trường hợp đang xét để biết chưa có đánh giá và không mất dữ liệu đã nhập.


Liên kết: FR26; UC07.


### US-30 Quản lý kết luận; Diagnosis


Vai trò: Bác sĩ. Ưu tiên: P1.


Tôi muốn ghi nhận kết luận lâm sàng hoặc trạng thái chưa đủ bằng chứng và xác nhận hướng xử trí để phân biệt rõ kết quả hỗ trợ với quyết định chuyên môn.


Liên kết: FR27; UC08.


### US-31 Phản hồi gợi ý chuyên môn


Vai trò: Bác sĩ. Ưu tiên: P1.


Tôi muốn ghi lại cách mình xem xét/phản hồi các gợi ý liên quan để giữ được mối liên hệ giữa gợi ý hệ thống và quyết định cuối cùng.


Liên kết: FR28; UC08.


### US-32 Lập kế hoạch điều trị; Treatment


Vai trò: Bác sĩ. Ưu tiên: P1.


Tôi muốn lập hoặc điều chỉnh bản dự thảo kế hoạch gồm phương án điều trị, thuốc, hướng dẫn, theo dõi và tái khám để chuẩn bị xác nhận kế hoạch chăm sóc.


Liên kết: FR29, FR30; UC08.


### US-33 Xác nhận kế hoạch điều trị


Vai trò: Bác sĩ. Ưu tiên: P1.


Tôi muốn xác nhận phiên bản cuối cùng của kế hoạch sau khi xem xét gợi ý và cảnh báo để chỉ kế hoạch chính thức mới được dùng cho công bố hoặc gửi đi.


Liên kết: FR31; UC08.


### US-34 Hướng chăm sóc và bàn giao


Vai trò: Bác sĩ / nhân viên y tế được phân quyền. Ưu tiên: P1.


Tôi muốn ghi nhận hướng chăm sóc ngoại trú hoặc thông tin tóm tắt về nhập viện, chuyển tuyến, ra viện để duy trì liên kết với lịch sử người bệnh mà không quản lý nội trú toàn diện.


Liên kết: FR32; UC08.


### US-35 Công bố thông tin cho bệnh nhân


Vai trò: Bác sĩ / nhân viên y tế được phân quyền. Ưu tiên: P3.


Tôi muốn chọn phần kết quả, kế hoạch thuốc, hướng dẫn theo dõi và tái khám đã được xác nhận để công bố đúng nội dung cho đúng bệnh nhân.


Liên kết: FR33, FR34; UC09.


### US-36 Ứng dụng bệnh nhân


Vai trò: Bệnh nhân. Ưu tiên: P3.


Tôi muốn xem các lần khám, kết quả, kế hoạch thuốc và hướng dẫn theo dõi/tái khám đã công bố để theo dõi thông tin chăm sóc của bản thân.


Liên kết: FR36; UC09.


### US-37 Thông báo


Vai trò: Bệnh nhân. Ưu tiên: P3.


Tôi muốn nhận thông báo về lịch khám, kết quả đã công bố hoặc thay đổi kế hoạch theo sự kiện được chọn để biết thông tin mới.


Liên kết: FR37; UC10.


### US-38 Nhắc lịch khám


Vai trò: Bệnh nhân. Ưu tiên: P3.


Tôi muốn nhận nhắc lịch theo lịch hẹn đã xác nhận và để nhắc tương lai được cập nhật khi lịch thay đổi nhằm tránh nhận nhắc theo lịch cũ.


Liên kết: FR38; UC10.


### US-39 Nhắc thuốc


Vai trò: Bệnh nhân. Ưu tiên: P3.


Tôi muốn nhận nhắc thuốc dựa trên kế hoạch thuốc hiện hành đã xác nhận và được phép cung cấp để hỗ trợ nhớ thời điểm dùng thuốc.


Liên kết: FR39; UC10.


### US-40 Mở theo ngữ cảnh HIS/EMR


Vai trò: Bác sĩ / nhân viên y tế được phân quyền. Ưu tiên: P1.


Tôi muốn mở đúng người bệnh/lượt khám từ ngữ cảnh HIS/EMR sau khi kiểm tra xác thực và quyền để giảm nguy cơ thao tác nhầm ca.


Liên kết: FR41; UC11.


### US-41 Phân quyền


Vai trò: Quản trị hệ thống. Ưu tiên: P1.


Tôi muốn cấp, thay đổi và thu hồi vai trò/quyền theo công việc, thao tác và phạm vi hồ sơ để giới hạn truy cập đúng nhiệm vụ.


Liên kết: FR42; UC12.


### US-42 Danh mục dùng chung


Vai trò: Quản trị hệ thống / người được phân quyền. Ưu tiên: P1.


Tôi muốn quản lý danh mục thuốc, xét nghiệm, đơn vị đo, cơ sở/khoa và mã ánh xạ để dữ liệu được dùng nhất quán.


Liên kết: FR43; UC12.


### US-43 Cấu hình tích hợp và quy tắc


Vai trò: Quản trị kỹ thuật / người có thẩm quyền chuyên môn. Ưu tiên: P1.


Tôi muốn cấu hình kết nối, chính sách nhắc và phiên bản quy tắc/mô hình được phép áp dụng để kiểm soát thay đổi hệ thống.


Liên kết: FR44; UC12.


### US-44 Nhật ký kiểm toán


Vai trò: Quản trị hệ thống / người được phân quyền. Ưu tiên: P1.


Tôi muốn tra cứu nhật ký thao tác, thay đổi dữ liệu, truy cập nhạy cảm và lỗi quyền theo người, thời gian, thao tác hoặc đối tượng để phục vụ truy vết.


Liên kết: FR45; UC12.


### US-45 Khôi phục tài khoản


Vai trò: Bệnh nhân / người hỗ trợ có quyền. Ưu tiên: P2.


Tôi muốn khôi phục quyền truy cập qua kênh đã xác minh hoặc người hỗ trợ có thẩm quyền để lấy lại tài khoản mà không làm lộ bệnh án.


Liên kết: FR46; UC01.


## Phụ lục B Tiêu chí BDD theo User Stories

Các điều kiện Given, When, Then sau được giữ theo báo cáo nguồn. Đây là kết quả mong đợi để xây dựng và thực thi ca kiểm thử, chưa phải kết quả đã đạt.


### BDD US-01 Quản lý hồ sơ


Given: Thông tin người bệnh được nhập.

When: Người dùng tra cứu hoặc tạo hồ sơ.

Then: Hệ thống kiểm tra trùng; nếu tạo mới thì cấp mã hồ sơ và lưu thời điểm tạo.


Liên kết: FR01.


### BDD US-02 Tài khoản và truy cập


Given: Tài khoản hợp lệ và đang được phép truy cập.

When: Người dùng đăng nhập hoặc đăng xuất.

Then: Phiên truy cập được tạo/kết thúc đúng trạng thái; tài khoản bị khóa không thể tiếp tục truy cập.


Liên kết: FR40.


### BDD US-03 Quản lý tài khoản


Given: Người thao tác là quản trị viên có quyền.

When: Quản trị viên tạo, cập nhật, khóa hoặc mở khóa tài khoản nhân viên.

Then: Thay đổi được ghi nhận và áp dụng; tài khoản bị khóa bị chặn theo chính sách truy cập.


Liên kết: FR40.


### BDD US-04 Liên kết hồ sơ


Given: Việc xác minh chưa hoàn tất hoặc thông tin không khớp.

When: Bệnh nhân yêu cầu liên kết tài khoản hoặc xem bệnh án.

Then: Hệ thống không cấp quyền xem; CCCD đơn lẻ không được xem là bằng chứng đủ để cấp quyền.


Liên kết: FR02.


### BDD US-05 Lịch hẹn


Given: Khung giờ khám có sức chứa xác định.

When: Người có quyền tạo hoặc cập nhật khung giờ khám.

Then: Hệ thống kiểm soát sức chứa và đồng bộ dữ liệu lịch giữa các kênh.


Liên kết: FR03.


### BDD US-06 Lịch hẹn


Given: Khung giờ được chọn còn chỗ.

When: Bệnh nhân đặt lịch khám hoặc tái khám.

Then: Hệ thống kiểm tra lại sức chứa; nếu nhiều yêu cầu cùng đặt chỗ cuối thì chỉ xác nhận một lượt đặt; đặt lịch không tự tạo lượt khám.


Liên kết: FR03, FR35.


### BDD US-07 Tiếp nhận lượt khám


Given: Hồ sơ bệnh nhân đã được xác định.

When: Nhân viên mở hoặc liên kết một lượt khám và cập nhật trạng thái.

Then: Lượt khám gắn đúng hồ sơ và trạng thái thay đổi theo thao tác; chỉ xem hồ sơ không tự mở lượt khám.


Liên kết: FR04.


### BDD US-08 Ghi nhận lâm sàng


Given: Người dùng có quyền và đã chọn đúng lượt khám.

When: Người dùng lưu bệnh sử, triệu chứng, dấu hiệu, bệnh đồng mắc, dị ứng, thuốc hoặc đánh giá lão khoa.

Then: Dữ liệu gắn đúng hồ sơ/lượt khám, có người nhập và thời điểm; phân biệt “chưa đánh giá” với giá trị bình thường.


Liên kết: FR05.


### BDD US-09 Chỉ định và kết quả


Given: Lượt khám và dữ liệu nguồn đã được xác định.

When: Người có quyền lưu chỉ định hoặc nhập/nhận kết quả xét nghiệm, thăm dò.

Then: Hệ thống phân biệt gợi ý, chỉ định và kết quả thực tế; lưu nguồn, thời điểm và đơn vị phù hợp.


Liên kết: FR06.


### BDD US-10 Lịch sử bệnh án


Given: Bệnh nhân có dữ liệu từ nhiều lượt khám hoặc đợt điều trị.

When: Người dùng xem lịch sử khám, thuốc, kết luận và kế hoạch.

Then: Dữ liệu hiển thị theo đúng lượt/đợt và thời điểm; dữ liệu cũ không được trình bày như hiện hành; thông tin nội trú chỉ ở mức liên kết/tóm tắt được cung cấp.


Liên kết: FR07.


### BDD US-11 Tiếp nhận dữ liệu


Given: Một nguồn dữ liệu đã được cấu hình.

When: Hệ thống tiếp nhận bản tin từ HIS/EMR, LIS, PACS/RIS hoặc nguồn mô phỏng.

Then: Hệ thống lưu nguồn, tham chiếu và thời điểm; bản tin không đọc được có lỗi rõ ràng; không bắt buộc mỗi ca có đủ mọi nguồn.


Liên kết: FR08.


### BDD US-12 Đối chiếu dữ liệu


Given: Dữ liệu có mã không khớp hoặc còn mơ hồ.

When: Hệ thống đối chiếu dữ liệu với hồ sơ/lượt khám.

Then: Dữ liệu được giữ chờ xử lý; hệ thống không tự chọn lượt hoặc tạo hồ sơ trùng chỉ vì mã nguồn khác nhau.


Liên kết: FR09.


### BDD US-13 Kiểm tra dữ liệu


Given: Có bản tin đầu vào cần kiểm tra.

When: Hệ thống kiểm tra cấu trúc, kiểu dữ liệu, trường bắt buộc, giá trị và đơn vị.

Then: Hệ thống chỉ rõ trường lỗi/thiếu và không dùng dữ liệu lỗi hoặc tự điền dữ liệu thiếu thành 0/bình thường.


Liên kết: FR10.


### BDD US-14 Chuẩn hóa dữ liệu


Given: Có giá trị gốc và quy tắc chuẩn hóa/ánh xạ.

When: Hệ thống chuẩn hóa mã thuốc, xét nghiệm, đơn vị hoặc ngày giờ.

Then: Có thể truy về giá trị gốc và quy tắc đã dùng; mã/phép đổi chưa rõ được giữ chờ; hệ thống không tự sửa kết quả bất thường.


Liên kết: FR11.


### BDD US-15 Chống trùng và phiên bản


Given: Một bản tin đã được xử lý được gửi lại hoặc có bản sửa từ nguồn.

When: Hệ thống tiếp nhận bản tin gửi lại/bản sửa.

Then: Không tạo bản ghi trùng; bản sửa giữ quan hệ thay thế và lịch sử; không mặc định dữ liệu đến sau luôn đúng hơn.


Liên kết: FR12.


### BDD US-16 Gửi dữ liệu đã xác nhận


Given: Nội dung đã được bác sĩ xác nhận và được phép gửi.

When: Hệ thống gửi kết luận, kế hoạch hoặc đơn thuốc tới HIS/EMR.

Then: Không gửi bản dự thảo như nội dung chính thức; lưu tham chiếu và phản hồi từ hệ thống đích; thiếu phản hồi được ghi là chưa rõ.


Liên kết: FR13.


### BDD US-17 Theo dõi giao dịch tích hợp


Given: Có giao dịch tích hợp và người tra cứu được cấp quyền.

When: Người dùng tra cứu theo tham chiếu, hồ sơ/lượt, nguồn/đích, thời gian hoặc trạng thái.

Then: Hệ thống hiển thị trạng thái, phản hồi, lỗi và lịch sử xử lý; quyền tra cứu không tự bao gồm quyền gửi lại hoặc sửa nội dung chuyên môn.


Liên kết: FR14.


### BDD US-18 Đối soát và gửi lại


Given: Đích có thể đã lưu dữ liệu nhưng phản hồi bị mất hoặc chưa rõ.

When: Người có quyền đối soát và gửi lại sau khi khắc phục lỗi.

Then: Hệ thống kiểm tra tham chiếu, tránh tạo dữ liệu trùng và lưu lịch sử từng lần thử; thay đổi chuyên môn phải có phiên bản/xác nhận phù hợp.


Liên kết: FR15.


### BDD US-19 Diagnosis; quản lý kết luận


Given: Dữ liệu chưa đủ hoặc người bệnh nằm ngoài đối tượng áp dụng.

When: Bác sĩ yêu cầu chạy Diagnosis.

Then: Hệ thống thông báo cụ thể tình trạng thiếu/không phù hợp và chỉ tạo đầu ra được phép theo điều kiện.


Liên kết: FR16.


### BDD US-20 Diagnosis; quản lý kết luận


Given: Dữ liệu phù hợp; bộ ca thử đã được rà soát chuyên môn.

When: Bác sĩ yêu cầu Diagnosis.

Then: Hệ thống hiển thị nhận định/phân loại theo đặc tả cùng căn cứ hoặc trạng thái chưa đủ bằng chứng; chỉ bật dự báo nguy cơ khi có phương pháp và kiểm định phù hợp.


Liên kết: FR17.


### BDD US-21 Lab/Test; quản lý kế hoạch


Given: Có dữ liệu bệnh án, kết quả liên quan và xét nghiệm đã có.

When: Bác sĩ yêu cầu gợi ý Lab/Test.

Then: Hệ thống nêu xét nghiệm/thăm dò, lý do và mức ưu tiên theo quy tắc; gợi ý không tự trở thành chỉ định hoặc kết quả xét nghiệm.


Liên kết: FR18.


### BDD US-22 Lab/Test; đánh giá lại


Given: Đã có lần đánh giá trước và xuất hiện dữ liệu/kết quả mới.

When: Bác sĩ chạy đánh giá lại.

Then: Hệ thống tạo lần đánh giá mới và xem xét thời điểm/điều kiện sử dụng kết quả; không tự chặn xét nghiệm lặp nếu chưa có quy tắc phù hợp.


Liên kết: FR19.


### BDD US-23 Treatment; quản lý kế hoạch


Given: Dữ liệu đầu vào phù hợp với phạm vi hỗ trợ đã đặc tả.

When: Bác sĩ yêu cầu Treatment.

Then: Hệ thống đưa ra gợi ý trong phạm vi đặc tả, phân biệt đề xuất với kế hoạch đã xác nhận và không biến gợi ý xét nghiệm thành kết quả đo.


Liên kết: FR20.


### BDD US-24 Treatment; quản lý kế hoạch


Given: Đã có phương án Treatment được tạo.

When: Bác sĩ mở chi tiết phương án.

Then: Các điều kiện, yêu cầu theo dõi và giới hạn áp dụng gắn với đúng phương án; chưa có quyết định bác sĩ thì không tạo lịch hẹn/nhắc thuốc chính thức.


Liên kết: FR21.


### BDD US-25 MedSafety; quản lý kế hoạch


Given: Có phương án thuốc và dữ liệu bệnh nhân liên quan.

When: Bác sĩ yêu cầu chạy MedSafety.

Then: Hệ thống báo vấn đề theo quy tắc đã duyệt, chỉ rõ dữ liệu quan trọng còn thiếu và không kết luận toàn bộ phương án là an toàn khi căn cứ chưa đủ.


Liên kết: FR22.


### BDD US-26 MedSafety; quản lý kế hoạch


Given: MedSafety đã tạo cảnh báo.

When: Bác sĩ mở chi tiết cảnh báo.

Then: Hệ thống hiển thị căn cứ/dữ liệu và ngưỡng đã đặc tả; không tự ngừng thuốc, đổi thuốc hoặc thay liều.


Liên kết: FR23.


### BDD US-27 Điều phối các module AI-CDSS


Given: Chỉ một phần dữ liệu/module phù hợp với tình huống đang xét.

When: Bác sĩ yêu cầu hỗ trợ chuyên môn.

Then: Hệ thống không bắt buộc chạy đủ bốn module và luôn phân biệt dữ liệu đo thực tế, gợi ý hệ thống và quyết định bác sĩ.


Liên kết: FR24.


### BDD US-28 Lịch sử AI-CDSS; kết luận/kế hoạch


Given: Module đã chạy và có dữ liệu đầu vào/đầu ra được lưu.

When: Bác sĩ mở lịch sử lần chạy.

Then: Hệ thống hiển thị đầu vào, phiên bản và đầu ra tương ứng; nếu dữ liệu liên quan thay đổi, kết quả đang chờ xác nhận được đánh dấu cần xem lại.


Liên kết: FR25.


### BDD US-29 Xử lý lỗi AI-CDSS


Given: Module không chạy thành công, hết thời gian hoặc không hỗ trợ trường hợp.

When: Hệ thống kết thúc lần chạy module.

Then: Có thông báo rõ module chưa đánh giá được; dữ liệu/dự thảo đã nhập được giữ lại và lỗi không bị coi là kết quả bình thường/an toàn.


Liên kết: FR26.


### BDD US-30 Quản lý kết luận; Diagnosis


Given: Bác sĩ đã xem dữ liệu và gợi ý liên quan.

When: Bác sĩ lưu kết luận lâm sàng hoặc trạng thái chưa đủ bằng chứng.

Then: Trạng thái chưa đủ bằng chứng hoặc kết luận được ghi rõ; người xác nhận và thời điểm được lưu; không nhầm với gợi ý chưa xác nhận.


Liên kết: FR27.


### BDD US-31 Phản hồi gợi ý chuyên môn


Given: Có gợi ý chuyên môn cần bác sĩ xem xét.

When: Bác sĩ lưu phản hồi hoặc quyết định đối với gợi ý.

Then: Phản hồi gắn với gợi ý và lần chạy tương ứng; không sửa ngược đầu ra gốc của module.


Liên kết: FR28.


### BDD US-32 Lập kế hoạch điều trị; Treatment


Given: Bác sĩ có quyền và đã chọn đúng hồ sơ/lượt khám.

When: Bác sĩ lưu kế hoạch điều trị dự thảo.

Then: Kế hoạch giữ trạng thái dự thảo cho đến khi được xác nhận và liên kết với gợi ý/căn cứ liên quan khi có.


Liên kết: FR29, FR30.


### BDD US-33 Xác nhận kế hoạch điều trị


Given: Kế hoạch vẫn ở trạng thái dự thảo.

When: Bác sĩ xác nhận kế hoạch.

Then: Hệ thống lưu phiên bản chính thức, người và thời điểm xác nhận; chỉ nội dung đã xác nhận và được phép mới được gửi sang HIS/EMR hoặc cung cấp cho bệnh nhân.


Liên kết: FR31.


### BDD US-34 Hướng chăm sóc và bàn giao


Given: Lượt khám cần kết thúc hoặc chuyển hướng chăm sóc.

When: Người có quyền ghi nhận hướng xử trí hoặc thông tin bàn giao.

Then: Hướng xử trí/tóm tắt được lưu trong đúng hồ sơ; hệ thống không giả định có chức năng quản lý giường bệnh hoặc chăm sóc nội trú hằng ngày.


Liên kết: FR32.


### BDD US-35 Công bố thông tin cho bệnh nhân


Given: Nội dung đã được xác nhận và được phép cung cấp.

When: Người có quyền chọn và công bố nội dung cho bệnh nhân.

Then: Chỉ phần được chọn/cho phép hiển thị cho đúng bệnh nhân; bản dự thảo không được công bố.


Liên kết: FR33, FR34.


### BDD US-36 Ứng dụng bệnh nhân


Given: Tài khoản bệnh nhân đã liên kết và xác minh.

When: Bệnh nhân mở lịch sử hoặc thông tin chăm sóc.

Then: Chỉ dữ liệu của chính bệnh nhân đã được phép công bố được hiển thị cùng ngày khám/thời điểm áp dụng; không hiển thị dự thảo hoặc bản cũ như thông tin hiện hành.


Liên kết: FR36.


### BDD US-37 Thông báo


Given: Có sự kiện thông báo hợp lệ.

When: Hệ thống tạo hoặc gửi thông báo.

Then: Thông báo tới đúng người, không trùng sự kiện và có trạng thái chưa đọc/đã đọc; trạng thái đã đọc không chứng minh người bệnh đã làm theo hướng dẫn/uống thuốc.


Liên kết: FR37.


### BDD US-38 Nhắc lịch khám


Given: Có lịch hẹn đã xác nhận và thời điểm nhắc.

When: Lịch hẹn được thay đổi hoặc hủy.

Then: Các nhắc tương lai theo lịch cũ được cập nhật/hủy; trạng thái tạo/gửi phản ánh đúng kênh kiểm thử.


Liên kết: FR38.


### BDD US-39 Nhắc thuốc


Given: Kế hoạch thuốc hiện hành đã được xác nhận, được phép cung cấp và có đủ thời điểm dùng.

When: Hệ thống tạo nhắc tại thời điểm được thiết lập hoặc kế hoạch thuốc thay đổi.

Then: Nhắc theo kế hoạch hiện hành; khi kế hoạch đổi/ngừng thì cập nhật/hủy nhắc tương lai; thiếu lịch thì yêu cầu bổ sung, không tự suy ra giờ uống hoặc đánh dấu đã uống.


Liên kết: FR39.


### BDD US-40 Mở theo ngữ cảnh HIS/EMR


Given: Người dùng có phiên hợp lệ và thông tin ngữ cảnh được kiểm tra.

When: Người dùng mở màn hình viện mô phỏng từ ngữ cảnh HIS/EMR.

Then: Hệ thống mở đúng ca; dữ liệu giả không vượt quyền; hết phiên thì yêu cầu xác thực lại.


Liên kết: FR41.


### BDD US-41 Phân quyền


Given: Quyền được thay đổi bởi người có thẩm quyền.

When: Quản trị viên cấp, thay đổi hoặc thu hồi quyền.

Then: Thao tác xem/nhập/sửa/xác nhận/cung cấp dữ liệu được kiểm soát ở giao diện và giao tiếp dữ liệu; quyền kỹ thuật không tự cho phép xác nhận chuyên môn.


Liên kết: FR42.


### BDD US-42 Danh mục dùng chung


Given: Danh mục có mã đang hoạt động hoặc đã ngừng dùng.

When: Người có quyền cập nhật danh mục.

Then: Mã ngừng dùng không được chọn mới nhưng lịch sử vẫn đọc được; danh mục chuyên môn có nguồn và được rà soát trước khi áp dụng.


Liên kết: FR43.


### BDD US-43 Cấu hình tích hợp và quy tắc


Given: Có thay đổi cấu hình hoặc phiên bản cần áp dụng.

When: Người được phân quyền cập nhật cấu hình/phiên bản.

Then: Thay đổi có dấu vết; bản chuyên môn chỉ áp dụng sau rà soát đúng thẩm quyền; kết quả cũ vẫn truy được phiên bản đã dùng.


Liên kết: FR44.


### BDD US-44 Nhật ký kiểm toán


Given: Có sự kiện thuộc phạm vi ghi nhật ký và người tra cứu có quyền.

When: Người dùng tra cứu nhật ký theo người, thời gian, thao tác hoặc đối tượng.

Then: Có thể xem thay đổi trước/sau và tham chiếu giao dịch khi có; nhật ký không lộ dữ liệu ngoài quyền và người dùng nghiệp vụ không thể tự sửa/xóa nhật ký.


Liên kết: FR45.


### BDD US-45 Khôi phục tài khoản


Given: Bằng chứng xác minh còn thiếu hoặc chưa hợp lệ.

When: Bệnh nhân hoặc người hỗ trợ yêu cầu khôi phục truy cập/thay đổi liên kết.

Then: Hệ thống không thực hiện khi chưa đủ bằng chứng; CCCD hoặc mã hồ sơ đơn lẻ không đủ; thao tác hỗ trợ hợp lệ phải có dấu vết.


Liên kết: FR46.
