# Đặc tả yêu cầu phần mềm hệ thống quản lý bệnh nhân suy tim cao tuổi
 
**Nhóm:** 27  
**Môn học:** Kỹ thuật Phần mềm Ứng dụng ET3260  
**Phiên bản tài liệu:** v1.0    
**Trạng thái:** Bản nháp theo bộ 34 FR và 13 NFR đã thống nhất. Chưa hoàn tất User Stories, BDD, Use Cases, DFD và các liên kết RTM.

Tài liệu đặc tả yêu cầu cho một ứng dụng web quản lý bệnh nhân suy tim cao tuổi và hỗ trợ nhân viên y tế đánh giá, điều trị, theo dõi. Bản nháp tổng hợp phần đã thống nhất trong báo cáo hiện tại; các phần chưa có nội dung được ghi rõ, chưa dùng để xác nhận hoàn thành tuần 2.

Cấu trúc ba chương dựa trên khung IEEE 830 trong bài giảng.
## 1. Giới thiệu

### 1.1. Mục đích tài liệu

SRS thống nhất phạm vi, người dùng, yêu cầu chức năng, yêu cầu chất lượng và ràng buộc để nhóm thiết kế, lập trình và kiểm thử cùng một hệ thống. Giảng viên và người hỗ trợ chuyên môn dùng tài liệu để xem xét các yêu cầu, chỉ ra điểm cần điều chỉnh và đối chiếu khi nghiệm thu.

Mã FR và NFR là mã tham chiếu chung cho báo cáo, Product Backlog, Use Cases, RTM, thiết kế dữ liệu và API. Những chức năng được mô tả là yêu cầu cần thực hiện, không phải báo cáo kết quả đã triển khai.

34 FR và 13 NFR ở chương 3 là các yêu cầu bắt buộc đã thống nhất trong nhóm. 
### 1.2. Phạm vi sản phẩm

Hệ thống hướng đến quản lý bệnh nhân cao tuổi , gồm ca nghi ngờ và ca đã được chẩn đoán suy tim. Trong đồ án, hồ sơ và tình huống đều là dữ liệu giả lập. Hệ thống ưu tiên bối cảnh điều trị nội trú tại bệnh viện và hỗ trợ cả khám, theo dõi ngoại trú.

**Trong phạm vi MVP:**

- Quản lý tài khoản, vai trò, phạm vi truy cập, danh mục và phiên bản quy tắc.
- Quản lý hồ sơ, lần khám ngoại trú, đợt điều trị nội trú, dữ liệu lâm sàng, thuốc và diễn biến theo thời gian.
- Tiếp nhận dữ liệu bằng nhập thủ công, file theo mẫu và API mô phỏng; kiểm tra dữ liệu trước khi sử dụng để đánh giá.
- Cung cấp bốn module hỗ trợ: Diagnosis, Lab/Test, Treatment và MedSafety trong phạm vi quy tắc được lựa chọn và phê duyệt.
- Ghi nhận ý kiến dược sĩ, quyết định của bác sĩ, kế hoạch điều trị, ra viện, tái khám và lịch sử thao tác.

Treatment bao gồm gợi ý thuốc hoặc nhóm thuốc, liều khởi đầu, đường dùng, tần suất và điều chỉnh/tăng liều theo FR-24, FR-25. Việc chọn thuốc và liều cụ thể phải dựa trên danh mục quy tắc đã phê duyệt, không áp dụng cho mọi thuốc hoặc mọi tình huống bệnh.

**Ngoài phạm vi MVP:** kết nối hệ thống bệnh viện production; sử dụng hồ sơ bệnh nhân thật; tự động kê đơn, tạo y lệnh hoặc ngừng thuốc; mô hình ML dự báo tử vong/tái nhập viện; cổng đăng nhập bệnh nhân/người chăm sóc; triển khai lâm sàng thực tế.

Bệnh nhân và người chăm sóc là đối tượng hưởng lợi và cung cấp thông tin qua nhân viên y tế. Chức năng tự đăng nhập, tự nhập dữ liệu và nhận nhắc nhở thuộc hướng mở rộng, không phải chức năng của phiên bản này.

### 1.3. Định nghĩa và từ viết tắt

| Thuật ngữ | Ý nghĩa trong tài liệu |
| --- | --- |
| SRS | Software Requirements Specification, tài liệu đặc tả yêu cầu phần mềm. |
| MVP | Phiên bản tối thiểu thực hiện phạm vi đã chọn của đồ án. |
| FR / NFR | Yêu cầu chức năng / yêu cầu phi chức năng. |
| Customer | Bên quyết định hoặc xác nhận nhu cầu, phạm vi và việc chấp nhận sản phẩm. |
| End-user | Người trực tiếp thao tác trên hệ thống. |
| CDSS | Hệ thống hỗ trợ quyết định lâm sàng. |
| Diagnosis | Module hỗ trợ đánh giá suy tim và mô tả tình trạng bệnh khi đủ dữ liệu. |
| Lab/Test | Module gợi ý xét nghiệm hoặc thăm dò bổ sung. |
| Treatment | Module gợi ý điều trị, thuốc/liều và theo dõi theo quy tắc đã chọn. |
| MedSafety | Module rà soát thuốc và đưa ra cảnh báo an toàn. |
| Synthetic | Dữ liệu giả lập phục vụ phát triển, kiểm thử và demo. |
| Rule Engine | Thành phần áp dụng các quy tắc có điều kiện, kết quả và căn cứ được khai báo. |
| HIS / EMR | Hệ thống thông tin bệnh viện / hồ sơ bệnh án điện tử. |
| LIS / PACS | Hệ thống thông tin xét nghiệm / hệ thống lưu trữ và truyền hình ảnh y khoa. |
| EF | Phân suất tống máu thất trái. |
| HFrEF / HFmrEF / HFpEF | Suy tim có EF giảm / giảm nhẹ / bảo tồn; không đồng nghĩa chẩn đoán chỉ từ EF. |
| BNP / NT-proBNP | Các xét nghiệm được dùng trong đánh giá suy tim. |
| eGFR | Mức lọc cầu thận ước tính. |
| BP / HR / SpO₂ | Huyết áp / nhịp tim / độ bão hòa oxy ngoại vi. |
| Frailty | Tình trạng dễ bị tổn thương ở người cao tuổi. |
| ADL / IADL | Đánh giá hoạt động sinh hoạt hằng ngày / hoạt động sinh hoạt có sử dụng công cụ. |
| RBAC | Kiểm soát truy cập dựa trên vai trò, kết hợp phạm vi hồ sơ được cấp. |
| BDD / Gherkin | Mô tả tiêu chí nghiệm thu bằng Given, When, Then. |
| RTM | Ma trận liên kết yêu cầu với User Story, Use Case, dữ liệu và API. |
| Audit Trail | Nhật ký giúp truy lại người, thời điểm, đối tượng và hành động. |

### 1.4. Tài liệu tham chiếu

| Mã | Tài liệu | Cách sử dụng |
| --- | --- | --- |
| REF-01 | Bài giảng KTPMUD và hướng dẫn Sprint 1 tuần 2–3 do giảng viên cung cấp. | Cấu trúc SRS, cách đặc tả yêu cầu và sản phẩm bàn giao. |
| REF-02 | Hướng dẫn chẩn đoán và điều trị suy tim cấp và mạn của Bộ Y tế, bản năm 2022 đã cung cấp. | Nguồn chuyên môn ưu tiên khi xây dựng quy tắc. |
| REF-03 | Quy trình chẩn đoán và điều trị bệnh suy tim ở người cao tuổi, tài liệu có tên Bệnh viện Hữu Nghị do nhóm nhận. | Bổ sung đặc điểm và các vấn đề chăm sóc người cao tuổi; không coi tên file là bằng chứng đã khảo sát bệnh viện. |
| REF-04 | `SUY TIM.docx`. | Mô tả đầu vào, đầu ra của bốn module hỗ trợ. |
| REF-05 | `DATA_DICTIONARY_SUY_TIM_AI_CDSS` bản được cung cấp. | Đối chiếu trường dữ liệu, kiểu, đơn vị và danh mục đầu vào phần suy tim. |
| REF-06 | Bảng biến bác sĩ AI-CDSS cho 5 mặt bệnh, phần suy tim. | Đối chiếu thông tin được trình bày và trao đổi trong luồng nghiệp vụ. |
| REF-07 | Schema tối thiểu AI-CDSS cho 5 mặt bệnh, phần suy tim. | Đối chiếu dữ liệu và các nguồn tích hợp tối thiểu. |

Liên kết học phần: [Hướng dẫn đồ án KTPMUD](https://fossbk-spec.github.io/ktpmud-book/do_an_mon_hoc). Sáu tài liệu đầu vào chuyên môn và dữ liệu tương ứng REF-02 đến REF-07. Chỉ sử dụng phần suy tim trong các tài liệu chứa nhiều bệnh.

Nhóm ưu tiên hướng dẫn Bộ Y tế, sau đó đối chiếu tài liệu tổng hợp về người cao tuổi. Khi có khác biệt về nội dung áp dụng, nhóm phải ghi nhận để xác nhận trước khi đưa thành quy tắc; không tự kết hợp các ngưỡng không thống nhất.

## 2. Mô tả tổng quan

### 2.1. Bối cảnh sản phẩm và vấn đề cần giải quyết

Quản lý bệnh nhân suy tim cao tuổi cần theo dõi nhiều nhóm thông tin: triệu chứng, sinh hiệu, khám lâm sàng, xét nghiệm, thăm dò tim mạch, thuốc, bệnh đồng mắc và yếu tố lão khoa. Một hồ sơ có thể tiếp tục được cập nhật trong đợt điều trị và qua các lần khám sau. Vì vậy, dữ liệu phải gắn đúng bệnh nhân, đúng lần khám hoặc đợt điều trị, có nguồn và thời điểm ghi nhận.

Hệ thống tập hợp những thông tin này, giúp nhân viên y tế xem diễn biến, nhận diện dữ liệu còn thiếu và đối chiếu gợi ý hỗ trợ với dữ liệu đã có. Mục tiêu là hỗ trợ việc quản lý và cá thể hóa chăm sóc; bác sĩ vẫn chịu trách nhiệm đánh giá và quyết định lâm sàng.

Nhóm chưa khảo sát trực tiếp tại bệnh viện. Những khó khăn và quy trình trong bản này được phân tích từ tài liệu, cần được xác nhận với người có chuyên môn. Chưa có số liệu để khẳng định hệ thống đã giảm thời gian thao tác, sai sót hoặc cải thiện kết quả điều trị.

Hệ thống dự kiến là ứng dụng web có phân quyền. Trong môi trường đồ án, HIS/LIS/PACS/EMR là các nguồn mô phỏng bên ngoài. Yêu cầu web độc lập hay Smart Panel nhúng vào EMR cần được xác nhận theo tài liệu tích hợp của giảng viên.

### 2.2. Mục tiêu và tóm tắt chức năng

| Mục tiêu nghiệp vụ | Nội dung hệ thống cần hỗ trợ | FR liên quan |
| --- | --- | --- |
| OB1. Quản lý hồ sơ tập trung | Tổ chức hồ sơ, lần khám/đợt điều trị, dữ liệu lâm sàng, thuốc và các nguồn nhập dữ liệu. | FR-06 đến FR-14, FR-16, FR-17 |
| OB2. Theo dõi diễn biến theo thời gian | Xem lịch sử, so sánh dữ liệu và phân biệt các lần đánh giá. | FR-15, FR-33 |
| OB3. Phân tầng và mô tả tình trạng | Kiểm tra dữ liệu, hỗ trợ đánh giá suy tim và gợi ý thăm dò bổ sung. | FR-18 đến FR-22 |
| OB4. Hỗ trợ an toàn và cá thể hóa điều trị | Gợi ý điều trị/thuốc/liều, rà soát an toàn và trình bày căn cứ. | FR-23 đến FR-29 |
| OB5. Phối hợp chăm sóc và theo dõi | Ghi nhận ý kiến dược sĩ, quyết định và kế hoạch của bác sĩ. | FR-09, FR-11, FR-30 đến FR-32 |

Các chức năng tài khoản, quyền, danh mục, quy tắc và nhật ký tại FR-01 đến FR-05, FR-34 phục vụ kiểm soát và truy vết các hoạt động trên.

Hệ thống gồm các nhóm chức năng: quản trị; quản lý hồ sơ và quá trình khám/điều trị; tiếp nhận và kiểm tra dữ liệu; bốn module hỗ trợ chuyên môn; ghi nhận ý kiến, quyết định và lịch sử.

**Luồng nghiệp vụ dự kiến:**

1. Tìm hoặc tạo hồ sơ giả lập; tạo lần khám ngoại trú hoặc đợt điều trị nội trú.
2. Nhân viên y tế ghi nhận thông tin theo quyền; tiếp nhận thêm kết quả từ file hoặc API mô phỏng khi cần.
3. Bác sĩ yêu cầu đánh giá. Hệ thống kiểm tra dữ liệu của module/quy tắc; phần dữ liệu thiếu không ngăn việc lưu hồ sơ hợp lệ, nhưng hạn chế gợi ý phụ thuộc vào dữ liệu đó.
4. Hệ thống trả kết quả hỗ trợ kèm căn cứ. Dược sĩ rà soát thuốc và ghi nhận ý kiến trong phạm vi được phân công.
5. Bác sĩ chấp nhận, điều chỉnh hoặc từ chối gợi ý, lập kế hoạch và tiếp tục theo dõi. Hệ thống lưu các lần đánh giá và quyết định.

Luồng trên mô tả hoạt động chung, không bắt buộc bốn module chạy tuần tự như một dây chuyền. Các module sử dụng dữ liệu liên quan và chỉ đưa ra đầu ra khi đáp ứng điều kiện của quy tắc.

### 2.3. Người dùng và các bên liên quan

| Nhóm | Vai trò và phạm vi |
| --- | --- |
| Bác sĩ | Người dùng trực tiếp, ghi nhận khám/chẩn đoán, yêu cầu đánh giá, xem diễn biến và cảnh báo, quyết định cuối cùng và lập kế hoạch điều trị. |
| Điều dưỡng | Người dùng trực tiếp, cập nhật sinh hiệu, cân nặng, triệu chứng và diễn biến chăm sóc theo quyền. |
| Dược sĩ lâm sàng | Người dùng trực tiếp, xem dữ liệu liên quan, rà soát thuốc và ghi nhận ý kiến để bác sĩ xem xét. |
| Quản trị hệ thống | Người dùng trực tiếp, quản lý tài khoản, quyền, danh mục và cấu hình kỹ thuật. Quyền quản trị không tự kèm quyền quyết định y khoa. |
| Người được cấp quyền phê duyệt chuyên môn | Quyền đặc biệt để duyệt nội dung y khoa của quy tắc theo FR-05. Có thể được gán cho người dùng đủ chuyên môn; không mặc định là một vai trò thứ năm hoặc mọi bác sĩ đều có quyền này. |
| Bệnh nhân và người chăm sóc | Đối tượng hưởng lợi và cung cấp thông tin qua nhân viên y tế; chưa có tài khoản trong MVP. |
| Giảng viên | Bên giao yêu cầu và đánh giá đồ án; hỗ trợ xác nhận phạm vi và kết nối người có chuyên môn. |
| Customer trong bối cảnh bệnh viện | Đại diện có thẩm quyền quyết định phạm vi và chấp nhận hệ thống; chưa xác định cá nhân, khoa hoặc bệnh viện cụ thể. |

Bác sĩ, điều dưỡng, dược sĩ và quản trị viên là bốn vai trò MVP. Một tài khoản có thể được cấp nhiều quyền phù hợp, nhưng từng thao tác vẫn phải kiểm tra vai trò và phạm vi hồ sơ ở phía máy chủ. Quyền chi tiết đối với cập nhật thuốc, nhập dữ liệu và phê duyệt quy tắc sẽ được thống nhất trong đặc tả Use Case và phân quyền.

### 2.4. Ràng buộc chung

- Chỉ sử dụng dữ liệu giả lập trong phát triển, kiểm thử và demo; không chứa tên, số điện thoại, CCCD, BHYT hoặc địa chỉ thật.
- Dữ liệu lâm sàng được tổ chức theo bệnh nhân và lần khám/đợt điều trị. Danh mục dữ liệu nghiệp vụ chưa đồng nghĩa với các bảng CSDL.
- Lưu hồ sơ và chạy đánh giá là hai thao tác khác nhau. Hồ sơ thiếu dữ liệu lâm sàng vẫn được lưu nếu định danh và liên kết bắt buộc hợp lệ.
- Kết quả hỗ trợ phải nêu căn cứ, dữ liệu thiếu, thời điểm và phiên bản quy tắc; dữ liệu thiết yếu thiếu không được coi là âm tính hoặc giá trị bình thường.
- Quyết định của bác sĩ phải được lưu cùng gợi ý ban đầu và lý do. Hệ thống không tự tạo y lệnh hoặc ngừng thuốc.
- Việc quản lý kỹ thuật và phê duyệt chuyên môn của quy tắc phải tách quyền.

### 2.5. Giả định và phụ thuộc

| Nội dung | Trạng thái |
| --- | --- |
| Bối cảnh nội trú ưu tiên, có ngoại trú; đối tượng người cao tuổi; bốn vai trò MVP; bệnh nhân/người chăm sóc ở phần mở rộng. | Đã thống nhất trong nhóm; chưa xác nhận qua khảo sát trực tiếp. |
| Dữ liệu nhập tay, file theo mẫu và API mô phỏng. | Phạm vi đã chọn; cấu trúc file, bản tin và quy tắc đối chiếu định danh còn cần đặc tả. |
| Rule Engine có thể giải thích là hướng thực hiện ban đầu. | Yêu cầu bắt buộc ML/LLM còn chờ giảng viên xác nhận. |
| Web độc lập có phân quyền và mô phỏng tích hợp. | Cần xác nhận yêu cầu Smart Panel, vị trí nhúng và hợp đồng tích hợp. |
| Danh mục quy tắc, thuốc/liều, ngưỡng và dữ liệu bắt buộc theo từng module. | Cần đối chiếu tài liệu đầu vào, ghi nguồn/phiên bản và xác nhận chuyên môn trước khi sử dụng làm quy tắc chuẩn. |
| Ca bệnh giả lập và kết quả kỳ vọng dùng nghiệm thu. | Chưa ghi nhận bộ ca và đáp án đã được chuyên môn duyệt trong báo cáo hiện tại. |
| Customer và người hỗ trợ xác nhận nghiệp vụ. | Chưa xác định đại diện bệnh viện cụ thể. |

Các điểm còn mở không làm mất phạm vi 34 FR/13 NFR đã chọn, nhưng phải được làm rõ khi đặc tả trường dữ liệu, quy tắc, hợp đồng API và các tình huống nghiệm thu liên quan.

## 3. Yêu cầu chi tiết

### 3.1. Các giao diện bên ngoài

| Giao diện | Yêu cầu |
| --- | --- |
| Giao diện web | Cung cấp thao tác phù hợp quyền bác sĩ, điều dưỡng, dược sĩ và quản trị. Trên màn hình hồ sơ/đánh giá phải nhận diện bệnh nhân và lần khám/đợt điều trị đang thao tác theo NFR-08. |
| File nhập dữ liệu | Tiếp nhận file theo mẫu tại FR-16; thông báo dòng/trường lỗi và kết quả nhập. Loại file, tên cột, mã danh mục và cách xử lý bản ghi trùng chưa được chốt trong bản nháp. |
| API nguồn dữ liệu mô phỏng | Tiếp nhận dữ liệu HIS/LIS/PACS/EMR, gắn đúng bệnh nhân và lần khám/đợt điều trị theo FR-17. Định dạng và cơ chế trao đổi phải được đối chiếu tài liệu đầu vào và đặc tả API tuần 3. |
| API của ứng dụng | Khung REST API Gateway và OpenAPI được thiết kế trong tuần 3. Khi truyền qua mạng phải sử dụng HTTPS theo NFR-03; HTTP tại localhost chỉ phục vụ phát triển. |
| Trình duyệt và thiết bị | Kiểm thử các luồng chính trên Chrome/Edge ở chiều rộng 1.366 px và 768 px theo NFR-13. Chưa cam kết cổng bệnh nhân hoặc ứng dụng di động riêng. |

Danh mục endpoints, request/response và mã HTTP thuộc đặc tả OpenAPI. SRS quy định hành vi và ràng buộc mà các giao diện đó phải đáp ứng, không thay thế OpenAPI.

### 3.2. Yêu cầu chức năng và mô hình nghiệp vụ

#### 3.2.1. Danh mục yêu cầu chức năng

Các mã và phạm vi FR giữ theo bảng đã chốt trong báo cáo. Cách diễn đạt được chuẩn hóa bằng từ “phải” để thể hiện yêu cầu bắt buộc.

| Mã | Phân hệ | Yêu cầu chức năng |
| --- | --- | --- |
| FR-01 | Tài khoản/phân quyền | Hệ thống phải cho phép người dùng đăng nhập, đăng xuất bằng tài khoản được cấp |
| FR-02 | Tài khoản/phân quyền | Hệ thống phải cho phép quản trị viên tạo, cập nhật, khóa và mở khóa tài khoản. |
| FR-03 | Tài khoản/phân quyền | Hệ thống phải cho phép gán vai trò và phạm vi truy cập hồ sơ; kiểm soát thao tác theo quyền được cấp. |
| FR-04 | Danh mục | Hệ thống phải cho phép quản trị viên quản lý danh mục khoa, chỉ số và đơn vị đo, thuốc và hoạt chất. |
| FR-05 | Quy tắc hỗ trợ | Hệ thống phải quản lý nội dung, phiên bản, nguồn tham chiếu và trạng thái phê duyệt của quy tắc. Chỉ người được cấp quyền phê duyệt chuyên môn mới được duyệt nội dung y khoa; quyền quản lý kỹ thuật không mặc nhiên bao gồm quyền này. |
| FR-06 | Hồ sơ bệnh nhân | Hệ thống phải cho phép tạo, tìm kiếm và cập nhật hồ sơ bệnh nhân giả lập bằng mã định danh duy nhất. Cho phép lưu hồ sơ chưa đầy đủ thông tin lâm sàng khi các trường định danh và liên kết bắt buộc hợp lệ; hiển thị thông tin còn thiếu. |
| FR-07 | Lần khám / đợt điều trị | Hệ thống phải cho phép tạo, cập nhật và kết thúc lần khám ngoại trú hoặc đợt điều trị nội trú; gắn với bệnh nhân, khoa, bác sĩ phụ trách, trạng thái và thời gian bắt đầu/kết thúc. |
| FR-08 | Tiền sử | Hệ thống phải cho phép ghi nhận và cập nhật tiền sử, bệnh đồng mắc của bệnh nhân. |
| FR-09 | Theo dõi và chăm sóc | Hệ thống phải cho phép điều dưỡng cập nhật sinh hiệu, cân nặng, triệu chứng và diễn biến chăm sóc trong phạm vi được phân quyền. |
| FR-10 | Khám và chẩn đoán | Hệ thống phải cho phép bác sĩ ghi nhận dấu hiệu khám, đánh giá lâm sàng và chẩn đoán của từng lần khám hoặc đợt điều trị. |
| FR-11 | Đánh giá lão khoa | Hệ thống phải cho phép ghi nhận frailty, nhận thức, ADL/IADL, dinh dưỡng và các nguy cơ theo danh mục đã chọn. |
| FR-12 | Cận lâm sàng | Hệ thống phải cho phép lưu và xem xét nghiệm, siêu âm, điện tim và báo cáo liên quan, kèm nguồn, thời điểm và đơn vị khi áp dụng. |
| FR-13 | Thuốc | Hệ thống phải cho phép cập nhật danh sách thuốc đang dùng, gồm hoạt chất, hàm lượng, liều, đường dùng, tần suất và thời gian sử dụng. |
| FR-14 | Dị ứng/phản ứng thuốc | Hệ thống phải cho phép ghi nhận dị ứng và phản ứng có hại của thuốc; phân biệt “chưa rõ” với “đã xác nhận không có”. |
| FR-15 | Theo dõi diễn biến | Hệ thống phải cho phép xem lịch sử và so sánh triệu chứng, chỉ số và thuốc giữa các thời điểm, lần khám hoặc đợt điều trị. |
| FR-16 | Nhập dữ liệu | Hệ thống phải cho phép nhập file theo mẫu; thông báo dòng/trường lỗi và kết quả nhập dữ liệu. |
| FR-17 | Tiếp nhận qua API | Hệ thống phải cho phép nhận dữ liệu từ API mô phỏng HIS/LIS/PACS/EMR và liên kết với đúng bệnh nhân, lần khám hoặc đợt điều trị. |
| FR-18 | Kiểm tra dữ liệu | Hệ thống phải kiểm tra trường bắt buộc, kiểu dữ liệu, giá trị, đơn vị và liên kết hồ sơ theo từng module/quy tắc. Chỉ rõ dữ liệu thiếu hoặc không hợp lệ; không đưa ra kết luận hoặc gợi ý phụ thuộc vào dữ liệu thiết yếu chưa có. |
| FR-19 | Diagnosis | Khi bác sĩ yêu cầu, hệ thống phải sử dụng dữ liệu hiện có để đưa ra đánh giá hỗ trợ suy tim và căn cứ; trả trạng thái chưa đủ dữ liệu khi không thể đánh giá. |
| FR-20 | Diagnosis | Hệ thống phải hỗ trợ mô tả thể suy tim và giai đoạn A-D khi đủ điều kiện của quy tắc; không kết luận mắc suy tim chỉ từ EF. |
| FR-21 | Lab/Test | Hệ thống phải gợi ý xét nghiệm hoặc thăm dò cần bổ sung, kèm lý do và mức ưu tiên theo quy tắc áp dụng. |
| FR-22 | Lab/Test | Hệ thống phải đối chiếu kết quả đã có và thời điểm thực hiện để nhận diện đề xuất có thể trùng lặp; nêu lý do nếu vẫn cần thực hiện lại. |
| FR-23 | Treatment | Hệ thống phải đưa ra gợi ý hướng điều trị và theo dõi dựa trên tình trạng bệnh, thuốc, bệnh đồng mắc và các chỉ số liên quan, theo bộ quy tắc được chọn. |
| FR-24 | Treatment | Hệ thống phải gợi ý thuốc/nhóm thuốc, liều khởi đầu, đường dùng và tần suất trong danh mục quy tắc được phê duyệt khi đủ dữ liệu; kèm căn cứ, điều kiện áp dụng và lưu ý. |
| FR-25 | Treatment | Hệ thống phải gợi ý điều chỉnh hoặc tăng liều theo quy tắc được phê duyệt, dựa trên diễn biến và khả năng dung nạp; kèm điều kiện và thời điểm đánh giá lại. |
| FR-26 | MedSafety | Hệ thống phải rà soát thuốc đang dùng hoặc được đề xuất để phát hiện trùng lặp, tương tác, dị ứng và chống chỉ định trong phạm vi bộ quy tắc. |
| FR-27 | MedSafety | Hệ thống phải cảnh báo nguy cơ liên quan đến thuốc và dữ liệu người bệnh, như chức năng thận, điện giải, huyết áp hoặc nhịp tim; nêu mức độ và căn cứ. |
| FR-28 | MedSafety | Hệ thống phải kiểm tra liều đang dùng hoặc được đề xuất theo quy tắc; chỉ rõ thuốc, liều và dữ liệu khiến liều cần được bác sĩ xem xét. |
| FR-29 | Hiển thị kết quả hỗ trợ | Mỗi kết quả phải thể hiện module, gợi ý/cảnh báo, căn cứ, dữ liệu thiếu, thời điểm đánh giá và phiên bản quy tắc. |
| FR-30 | Ý kiến dược sĩ | Hệ thống phải cho phép dược sĩ xem thông tin liên quan và ghi nhận nhận xét, đề xuất để bác sĩ xem xét. |
| FR-31 | Quyết định bác sĩ | Hệ thống phải cho phép bác sĩ chấp nhận, điều chỉnh hoặc từ chối gợi ý; lưu gợi ý ban đầu, quyết định, nội dung điều chỉnh, lý do, người xác nhận và thời điểm. |
| FR-32 | Kế hoạch điều trị | Hệ thống phải cho phép bác sĩ lập và cập nhật kế hoạch điều trị, theo dõi, ra viện và tái khám. Gợi ý của hệ thống chỉ được đưa vào kế hoạch sau khi bác sĩ xác nhận; không tự động tạo y lệnh hoặc ngừng thuốc. |
| FR-33 | Lịch sử đánh giá | Hệ thống phải lưu các lần đánh giá, dữ liệu đầu vào đã sử dụng và quyết định liên quan; cho phép đánh giá lại khi dữ liệu thay đổi, đồng thời phân biệt kết quả cũ với kết quả mới. |
| FR-34 | Nhật ký | Hệ thống phải ghi nhận người thực hiện, thời gian, đối tượng và hành động đối với các thay đổi quan trọng; cho phép tra cứu theo quyền. |

#### 3.2.2. User Stories và Product Backlog

**Chưa hoàn thiện.** Mục 4.4.1 trong báo cáo hiện tại mới có tiêu đề, chưa có danh sách User Stories để đưa vào SRS.

Nội dung cần có là mã User Story, vai trò, hành động và lợi ích, FR/NFR liên quan và mức ưu tiên trong Product Backlog. Các stories phải đủ nhỏ để thực hiện và kiểm thử, phù hợp INVEST. Chưa gán mã US hoặc tạo liên kết RTM thay cho nội dung chưa được nhóm thống nhất.

#### 3.2.3. Tiêu chí nghiệm thu BDD

**Chưa hoàn thiện.** Mục 4.4.2 trong báo cáo hiện tại chưa có kịch bản nghiệm thu.

Mỗi User Story phải có tiêu chí Given–When–Then cho luồng chuẩn và ngoại lệ/ca biên tương ứng. Giá trị và kết quả y khoa trong kịch bản phải dựa trên quy tắc và đáp án đã được duyệt; không lấy thiếu dữ liệu làm căn cứ tạo một kết luận giả định.

#### 3.2.4. Use Case Diagram

**Chưa hoàn thiện.** Các mục 4.3.1 và 4.3.2 trong báo cáo hiện tại chưa có sơ đồ.

Cần sơ đồ tổng thể và phân rã theo bốn vai trò MVP. Sơ đồ phải phân biệt chức năng người dùng với các nguồn dữ liệu/hệ thống ngoài. Các quyền phê duyệt chuyên môn phải được thể hiện phù hợp FR-05.

Tệp ảnh và nguồn chỉnh sửa sẽ đặt trong `docs/architecture/`; chỉ chèn liên kết ảnh khi đã có tệp thực tế và đã kiểm tra đường dẫn.

#### 3.2.5. Đặc tả Use Case

**Chưa hoàn thiện.** Mục 4.3.3 trong báo cáo hiện tại chưa có bảng đặc tả.

Mỗi Use Case cần mã, mục tiêu, tác nhân, tiền điều kiện, hậu điều kiện, luồng chính và luồng phụ/ngoại lệ. Quyền truy cập và liên kết hồ sơ phải nhất quán với FR-03, FR-06, FR-07 và NFR-01, NFR-04. Chưa dùng lại mã UC của tài liệu cũ trước khi đối chiếu bộ yêu cầu mới.

#### 3.2.6. DFD Context và DFD Level 1

**Chưa hoàn thiện.** Mục 3.3.2 và 3.3.3 trong báo cáo hiện tại chưa có sơ đồ.

DFD Context phải mô tả dữ liệu trao đổi giữa hệ thống và các tác nhân/nguồn ngoài. DFD Level 1 phải thể hiện tiến trình và kho dữ liệu, cân bằng luồng với sơ đồ Context. Các mũi tên biểu diễn dữ liệu; không dùng DFD để buộc bốn module chạy tuần tự.

Sơ đồ phân cấp chức năng đã có trong báo cáo không thay thế Use Case Diagram hoặc DFD.

### 3.3. Yêu cầu phi chức năng

Các yêu cầu sau áp dụng cho môi trường thử nghiệm đồ án. Đây là tiêu chí phải kiểm tra, chưa phải kết quả kiểm thử đã đạt hoặc cam kết vận hành bệnh viện. Nhóm chất lượng giữ theo bảng đã thống nhất.

| Mã | Nhóm chất lượng | Yêu cầu và tiêu chí kiểm tra |
| --- | --- | --- |
| NFR-01 | Bảo mật truy cập | Kiểm tra quyền ở phía máy chủ cho mọi API được bảo vệ. Toàn bộ ca kiểm thử truy cập trái quyền phải bị từ chối và không trả dữ liệu hồ sơ. |
| NFR-02 | Bảo vệ thông tin xác thực | Không lưu mật khẩu dạng rõ; không ghi mật khẩu hoặc token vào log. Kiểm tra dữ liệu lưu và log trong các kịch bản đăng nhập. |
| NFR-03 | Bảo mật truyền dữ liệu | Khi triển khai qua mạng, sử dụng HTTPS cho truy cập và trao đổi dữ liệu. HTTP tại localhost chỉ dùng để phát triển. |
| NFR-04 | Toàn vẹn dữ liệu | Không chấp nhận bản ghi tham chiếu đến bệnh nhân/lần khám không tồn tại. Các kiểm thử vi phạm liên kết và ràng buộc bắt buộc phải bị từ chối. |
| NFR-05 | Độ tin cậy lưu trữ | Dữ liệu đã thông báo lưu thành công phải còn nguyên sau khi khởi động lại ứng dụng và CSDL; kiểm tra với hồ sơ, kết quả và quyết định bác sĩ. |
| NFR-06 | Hiệu năng thao tác | Với 10 người dùng đồng thời và 1.000 hồ sơ giả lập, ít nhất 95% yêu cầu xem/tìm hồ sơ hoàn thành trong 2 giây. Ghi rõ cấu hình máy và dữ liệu khi đo. |
| NFR-07 | Hiệu năng đánh giá | Trong bộ thử nghiệm đã chọn, yêu cầu hỗ trợ phải trả kết quả hoặc trạng thái lỗi/không đủ dữ liệu trong tối đa 10 giây. Nếu quá hạn, giao diện phải thông báo thay vì chờ vô thời hạn. |
| NFR-08 | Khả năng sử dụng | Mỗi màn hình hồ sơ và đánh giá phải hiển thị mã bệnh nhân, lần khám/đợt điều trị đang thao tác. Lỗi nhập liệu phải chỉ rõ trường và cách sửa. |
| NFR-09 | Khả năng giải thích | 100% kết quả hỗ trợ trong bộ kiểm thử phải truy được dữ liệu đầu vào, quy tắc và nguồn tham chiếu đã sử dụng; không hiển thị phần trăm tin cậy chưa có phương pháp xác định. |
| NFR-10 | An toàn chức năng | Các kịch bản thiếu dữ liệu thiết yếu phải hạn chế gợi ý tương ứng và nêu lý do. Không có thao tác nào tự biến gợi ý thành đơn thuốc hoặc tự ngừng thuốc. |
| NFR-11 | Khả năng phục hồi | Hệ thống phải hỗ trợ sao lưu và phục hồi CSDL thử nghiệm; sau phục hồi, số bản ghi và các liên kết phải khớp bản sao lưu. Mục tiêu phục hồi demo: tối đa 30 phút. |
| NFR-12 | Khả năng bảo trì | Quy tắc có mã và phiên bản. Thay đổi quy tắc phải kiểm thử được mà không sửa giao diện; kết quả cũ vẫn truy được phiên bản đã dùng. |
| NFR-13 | Khả năng tương thích | Các luồng chính hoạt động trên Chrome và Edge tại thời điểm kiểm thử. Giao diện sử dụng được ở chiều rộng 1.366 px và 768 px, không che nút thao tác chính. |

### 3.4. Ràng buộc thiết kế và tuân thủ

- Thiết kế và hiện thực phải giữ các ràng buộc tại mục 2.4 và đáp ứng 34 FR, 13 NFR. Công nghệ hoặc cách chia thành phần không được làm mất chức năng đã chọn.
- Mỗi quy tắc y khoa dùng trong đánh giá phải quản lý nội dung, phiên bản, nguồn và trạng thái phê duyệt theo FR-05. Mỗi kết quả phải truy lại dữ liệu và quy tắc đã dùng theo FR-29, FR-33, NFR-09, NFR-12.
- Thuốc, liều, ngưỡng và điều kiện áp dụng trong Treatment/MedSafety phải có phạm vi được lựa chọn và phê duyệt. Bản này chưa ban hành một danh mục ngưỡng hay bảng liều lâm sàng thay cho tài liệu chuyên môn.
- Phân quyền phải thực hiện phía máy chủ; kiểm tra quyền quyết định lâm sàng và quyền phê duyệt nội dung quy tắc độc lập với quyền quản trị kỹ thuật.
- Không sử dụng dữ liệu bệnh nhân thật trong đồ án và không coi kết quả demo là đủ điều kiện triển khai lâm sàng.
- IEC 62304 trong ví dụ bài giảng không tự động trở thành yêu cầu đã áp dụng cho đề tài. Nếu giảng viên yêu cầu tiêu chuẩn cụ thể, nhóm sẽ bổ sung phạm vi và tiêu chí tương ứng sau khi xác nhận.

### 3.5. Ma trận truy vết yêu cầu

Ma trận đầy đủ nằm trong [RTM.md](RTM.md):

**Mã yêu cầu → User Story → Use Case → Schema CSDL → API.**

Mỗi FR/NFR có một dòng riêng. NFR liên kết với các luồng chịu ảnh hưởng; trường hợp không áp dụng trực tiếp với schema hoặc API phải ghi lý do. Danh mục FR ở mục 3.2.1 vẫn xác định phân hệ của yêu cầu.

**Trạng thái đối chiếu:** đã có 34 FR và 13 NFR, nhưng chưa có mã US/UC được đối chiếu theo bộ yêu cầu mới trong báo cáo này. RTM hiện chưa chứng minh độ phủ 100%. Schema và API ở tuần 3 cần đối chiếu lại với bộ yêu cầu đã chốt trước khi ghi thành liên kết hoàn chỉnh.
