import { writeFile } from 'node:fs/promises';

const descriptions = {
  allergy_status: 'Trạng thái dị ứng/phản ứng: chưa rõ, xác nhận không có hoặc đã biết (FR-14).',
  app_user: 'Tài khoản; chỉ lưu password hash. Nhân viên có thể thuộc khoa (FR-01,02).',
  appointment: 'Lịch hẹn 30 phút do bệnh nhân yêu cầu; xác nhận, hoàn thành hoặc hủy (FR-P02).',
  audit_event: 'Nhật ký bất biến: người hoặc tiến trình hệ thống, đối tượng, hành động và thời gian (FR-34).',
  auth_session: 'Phiên xác thực có hạn dùng và trạng thái thu hồi; chỉ lưu hash token (FR-01).',
  case_access: 'Phạm vi hồ sơ cấp riêng cho bác sĩ, điều dưỡng hoặc dược sĩ (FR-03).',
  clinical_decision: 'Quyết định bất biến của bác sĩ; điều chỉnh phải có nội dung và lý do (FR-31,33).',
  clinical_note: 'Ghi nhận chăm sóc, khám, chẩn đoán hoặc đánh giá lão khoa theo lần khám (FR-09,10,11).',
  department: 'Danh mục khoa giả lập (FR-04,07).',
  drug_product: 'Danh mục sản phẩm thuốc: hoạt chất, hàm lượng và dạng bào chế (FR-04,13).',
  drug_reaction: 'Chi tiết dị ứng hoặc phản ứng có hại với hoạt chất, chỉ khi trạng thái là known (FR-14).',
  encounter: 'Lần khám ngoại trú/đợt nội trú, khoa, bác sĩ, trạng thái và thời điểm kết thúc (FR-07).',
  evaluation: 'Snapshot bất biến của một lần đánh giá cùng revision nguồn và người yêu cầu (FR-18,33).',
  import_batch: 'Lần nhập file/API mô phỏng, mã nguồn, trạng thái và số dòng thành công/lỗi (FR-16,17).',
  import_error: 'Lỗi nhập theo dòng, trường và thông báo (FR-16,18).',
  ingredient: 'Danh mục hoạt chất; seed chỉ có hoạt chất giả lập (FR-04).',
  medication: 'Thuốc hiện dùng/đề xuất, liều, đường dùng, tần suất, khoảng ngày và liên kết đơn (FR-13).',
  medication_reminder: 'Một nhắc uống cho một giờ trong một ngày; pending/taken/skipped/cancelled (FR-P04).',
  medication_schedule: 'Giờ uống hằng ngày của từng thuốc trong đơn, theo múi giờ của đơn (FR-13,FR-P04).',
  module_result: 'Kết quả một module: phiên bản quy tắc, trạng thái và diễn giải (FR-19..29).',
  observation: 'Chỉ số theo lần khám, có loại giá trị, trạng thái thiếu, nguồn và người ghi (FR-09,11,12).',
  observation_type: 'Danh mục chỉ số, kiểu và đơn vị; giới hạn biểu diễn, không phải ngưỡng cảnh báo (FR-04,18).',
  patient_account: 'Liên kết duy nhất tài khoản patient với một hồ sơ synthetic (FR-P01).',
  patient_case: 'Hồ sơ synthetic, bác sĩ phụ trách và revision; không lưu định danh thật (FR-06).',
  patient_history: 'Tiền sử, bệnh đồng mắc, gia đình và xã hội theo hồ sơ (FR-08).',
  patient_measurement: 'Chỉ số tự nhập tại nhà; không tự trở thành dữ liệu đã được nhân viên xác minh (FR-P03).',
  permission: 'Danh mục quyền đặc biệt, gồm quyền phê duyệt chuyên môn rule.approve (FR-05).',
  pharmacist_review: 'Nhận xét và đề xuất của dược sĩ được phân công về một lần đánh giá (FR-30).',
  prescription: 'Đơn thuốc do bác sĩ xác nhận; ngày dùng và múi giờ; bản xác nhận được giữ bất biến (FR-13,32,FR-P04).',
  recommendation: 'Gợi ý/cảnh báo có mức độ và nguồn tham chiếu; không tự tạo y lệnh (FR-21..29).',
  result_missing_field: 'Các chỉ số còn thiếu cho một kết quả module (FR-18,29).',
  role: 'Năm vai trò: doctor, nurse, pharmacist, admin, patient (FR-03,FR-P01).',
  rule_approval: 'Bằng chứng duyệt nội dung đã kiểm thử, hash, người duyệt có quyền và thời điểm (FR-05).',
  rule_required_field: 'Chỉ số bắt buộc của phiên bản quy tắc; giữ nguyên từ trạng thái tested (FR-18).',
  rule_version: 'Nội dung JSON, hash SHA-256, module, nguồn và vòng đời phiên bản quy tắc (FR-05).',
  test_report: 'Báo cáo xét nghiệm, siêu âm, ECG hoặc thăm dò, có thời điểm và nguồn (FR-12).',
  treatment_plan: 'Kế hoạch điều trị, theo dõi, ra viện hoặc tái khám do bác sĩ nhập (FR-32).',
  user_permission: 'Cấp quyền đặc biệt theo tài khoản; admin không tự có quyền phê duyệt chuyên môn (FR-05).',
  user_role: 'Các vai trò tài khoản; tài khoản bệnh nhân tách khỏi tài khoản nhân viên (FR-03,FR-P01).',
};
const fields = {
  id: 'Định danh nội bộ UUID.', user_id: 'Tài khoản liên quan.', username: 'Tên đăng nhập giả lập.',
  password_hash: 'Hash mật khẩu; seed dùng PBKDF2-SHA256, không chứa mật khẩu rõ.',
  active: 'Trạng thái được phép sử dụng.', department_code: 'Mã khoa.', code: 'Mã danh mục/quy tắc.',
  role_code: 'Mã vai trò.', permission_code: 'Mã quyền đặc biệt.', token_hash: 'SHA-256 của token phiên, không lưu token rõ.',
  expires_at: 'Thời điểm hết hạn phiên.', revoked_at: 'Thời điểm thu hồi phiên.', case_id: 'Hồ sơ bệnh nhân liên quan.',
  synthetic_code: 'Mã hồ sơ giả lập duy nhất bắt đầu bằng SYN-.', age: 'Tuổi ghi nhận trong hồ sơ.', sex: 'Giới tính hoặc chưa rõ.',
  owner_id: 'Bác sĩ phụ trách hồ sơ.', revision: 'Tăng khi dữ liệu lâm sàng liên quan thay đổi.',
  access_scope: 'Phạm vi clinical, nursing hoặc medsafety.', encounter_id: 'Lần khám/đợt điều trị liên quan.',
  occurred_at: 'Thời điểm bắt đầu lần khám/đợt điều trị.', doctor_id: 'Bác sĩ phụ trách/xác nhận.', ended_at: 'Thời điểm kết thúc.',
  label: 'Nhãn hiển thị.', value_kind: 'Kiểu number, boolean hoặc text.', unit: 'Đơn vị chuẩn của chỉ số.',
  min_value: 'Giới hạn biểu diễn dưới; không phải ngưỡng y khoa.', max_value: 'Giới hạn biểu diễn trên nếu áp dụng.',
  value_number: 'Giá trị số; không nhận NaN/Infinity.', value_boolean: 'Giá trị có/không.', value_text: 'Giá trị văn bản.',
  observed_at: 'Thời điểm đo/đánh giá.', source: 'Nguồn nhập giả lập hoặc nguồn mô phỏng.',
  recorded_by: 'Người ghi nhận dữ liệu.', recorded_at: 'Thời điểm ghi nhận dữ liệu.', display_name: 'Tên hiển thị danh mục.',
  ingredient_code: 'Hoạt chất liên quan.', strength: 'Hàm lượng sản phẩm.', strength_unit: 'Đơn vị hàm lượng.',
  dosage_form: 'Dạng bào chế.', prescription_id: 'Đơn thuốc liên quan.', starts_on: 'Ngày bắt đầu dùng.', ends_on: 'Ngày kết thúc nếu có.',
  timezone: 'Múi giờ IANA của các giờ uống; mặc định Asia/Ho_Chi_Minh.', instructions: 'Hướng dẫn dạng văn bản.',
  confirmed_at: 'Thời điểm bác sĩ xác nhận đơn.', drug_product_code: 'Sản phẩm thuốc; phải thuộc đúng hoạt chất.',
  dose: 'Liều của một lần dùng.', dose_unit: 'Đơn vị liều.', route: 'Đường dùng.', frequency_per_day: 'Số lần dùng mỗi ngày.',
  medication_id: 'Thuốc trong đơn liên quan.', dose_time: 'Giờ uống địa phương hằng ngày; một dòng cho mỗi lần uống.',
  schedule_id: 'Giờ uống liên quan.', scheduled_on: 'Ngày uống địa phương.', due_at: 'Thời điểm nhắc thực tế có múi giờ.',
  responded_at: 'Thời điểm đánh dấu đã uống/bỏ qua, do trigger ghi.', notified_at: 'Thời điểm worker đã gửi thông báo nếu có.',
  version: 'Số phiên bản quy tắc.', module: 'Module diagnosis, lab_test, treatment hoặc medsafety.',
  source_ref: 'Nguồn tham chiếu của nội dung.', content_hash: 'SHA-256 của chuỗi JSONB content chuẩn hóa bởi PostgreSQL.',
  created_by: 'Người tạo phiên bản.', rule_version_id: 'Phiên bản quy tắc liên quan.', field_code: 'Mã chỉ số/trường dữ liệu.',
  approval_ref: 'Tham chiếu bằng chứng phê duyệt.', approved_content_hash: 'Hash của nội dung được duyệt.', approved_at: 'Thời điểm duyệt.',
  input_revision: 'Revision của hồ sơ nguồn khi đánh giá.', input_snapshot: 'Bản sao JSONB bất biến dữ liệu được dùng.',
  requested_by: 'Tài khoản yêu cầu thao tác.', mode: 'Chế độ stub hoặc validated; seed chỉ dùng stub.',
  evaluation_id: 'Lần đánh giá liên quan.', message: 'Thông báo diễn giải/lỗi.', module_result_id: 'Kết quả module liên quan.',
  severity: 'Mức info, warning hoặc critical.', description: 'Mô tả nội dung.', reason: 'Lý do yêu cầu/quyết định.',
  adjustment_details: 'Nội dung bác sĩ điều chỉnh dưới dạng JSONB, bắt buộc khi adjusted.',
  external_ref: 'Mã bản tin/báo cáo/batch nguồn giả lập.', performed_at: 'Thời điểm thực hiện xét nghiệm/thăm dò.',
  accepted_rows: 'Số dòng nhập thành công.', rejected_rows: 'Số dòng nhập lỗi.', imported_by: 'Người nhập batch.',
  batch_id: 'Batch nhập dữ liệu liên quan.', row_number: 'Số dòng gây lỗi.', pharmacist_id: 'Dược sĩ nhận xét.',
  comment: 'Nhận xét dược sĩ.', proposal: 'Đề xuất để bác sĩ xem xét.', decision_id: 'Quyết định gốc nếu kế hoạch dùng kết quả hỗ trợ.',
  follow_up_at: 'Thời điểm tái khám dự kiến.', slot_at: 'Thời điểm bắt đầu slot khám 30 phút.',
  systolic_bp: 'Huyết áp tâm thu, mmHg; phải nhập cùng tâm trương.', diastolic_bp: 'Huyết áp tâm trương, mmHg.',
  heart_rate: 'Nhịp tim, bpm.', weight_kg: 'Cân nặng, kg.', spo2: 'Độ bão hòa oxy, %. Giới hạn biểu diễn 0–100.',
  temperature_c: 'Nhiệt độ, độ C.', symptoms: 'Triệu chứng/ghi chú tự nhập, tối đa 500 ký tự.',
  actor_id: 'Tài khoản thao tác; null cho tiến trình hệ thống không gắn tài khoản.', actor_kind: 'user hoặc system.',
  action: 'Hành động/quyết định.', entity_type: 'Loại đối tượng nhật ký.', entity_id: 'UUID đối tượng nhật ký.',
  created_at: 'Thời điểm tạo.', updated_at: 'Thời điểm cập nhật gần nhất.', name: 'Tên danh mục.',
  status: 'Trạng thái; các giá trị hợp lệ được ghi trong CHECK bên dưới.', kind: 'Loại bản ghi; xem CHECK của bảng.',
  content: 'Nội dung ghi nhận hoặc JSONB; xem kiểu và ràng buộc của bảng.',
};

// Metadata is introspected from the running schema, not parsed from hand-maintained DDL.
export async function exportMetadata(db) {
  const query = async (s, p = []) => (await db.query(s, p)).rows;
  const tables = await query("SELECT tablename AS name FROM pg_tables WHERE schemaname='public' ORDER BY tablename");
  for (const table of tables) {
    if (!descriptions[table.name]) throw new Error(`Missing description for ${table.name}`);
    table.description = descriptions[table.name];
    table.columns = await query(`SELECT a.attname AS name, format_type(a.atttypid,a.atttypmod) AS type,
      NOT a.attnotnull AS nullable, pg_get_expr(d.adbin,d.adrelid) AS default_value
      FROM pg_attribute a LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
      WHERE a.attrelid=$1::regclass AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum`, [table.name]);
    table.constraints = await query(`SELECT conname AS name, pg_get_constraintdef(oid) AS definition,
      ARRAY(SELECT attname FROM pg_attribute WHERE attrelid=conrelid AND attnum=ANY(conkey) ORDER BY attnum) AS columns
      FROM pg_constraint WHERE conrelid=$1::regclass AND contype <> 'n' ORDER BY conname`, [table.name]);
    for (const c of table.columns) {
      if (!fields[c.name]) throw new Error(`Missing description for ${table.name}.${c.name}`);
      c.description = fields[c.name];
      c.constraint = [c.nullable ? 'NULL' : 'NOT NULL', c.default_value === null ? '' : `DEFAULT ${c.default_value}`,
        ...table.constraints.filter(k => k.columns.includes(c.name)).map(k => k.definition)].filter(Boolean).join('; ');
    }
    table.indexes = await query("SELECT indexname AS name,indexdef AS definition FROM pg_indexes WHERE schemaname='public' AND tablename=$1 ORDER BY indexname", [table.name]);
    table.triggers = await query(`SELECT tgname AS name,pg_get_triggerdef(oid) AS definition FROM pg_trigger
      WHERE tgrelid=$1::regclass AND NOT tgisinternal ORDER BY tgname`, [table.name]);
    table.row_level_security = await query(`SELECT policyname AS name,cmd AS command,qual AS using_expression,
      with_check AS check_expression FROM pg_policies WHERE schemaname='public' AND tablename=$1 ORDER BY policyname`, [table.name]);
  }
  await writeFile(new URL('../schema_metadata.json', import.meta.url), JSON.stringify(tables, null, 2) + '\n');
  const escape = s => String(s ?? '').replaceAll('|', '\\|').replaceAll('\n', ' ');
  const doc = ['# Từ điển dữ liệu — schema cập nhật theo SRS và cổng bệnh nhân', '',
    `PostgreSQL 16+. Có ${tables.length} bảng. Metadata và bảng cột được xuất từ schema đã khởi tạo, cùng kiểm thử SQL.`, '',
    'UUID là định danh nội bộ; thời gian sự kiện dùng timestamptz. Null biểu thị chưa có dữ liệu. Giới hạn số trong CHECK là kiểm tra biểu diễn, không phải ngưỡng chẩn đoán.', '',
    'Hướng dẫn tài khoản, phân quyền, đơn thuốc và giờ uống nằm trong [README database](README.md). Các bảng bệnh nhân có RLS cho vai trò DB `hf_patient_portal`; staff backend phải kiểm tra quyền theo phiên và hồ sơ. Gateway hiện tại vẫn dùng RAM.', ''];
  for (const t of tables) {
    doc.push(`## ${t.name}`, '', t.description, '', '| Trường | Kiểu | Nullable | Mặc định | Ý nghĩa |', '|---|---|---|---|---|');
    for (const c of t.columns) doc.push(`| ${c.name} | ${escape(c.type)} | ${c.nullable ? 'Có' : 'Không'} | ${escape(c.default_value)} | ${escape(c.description)} |`);
    doc.push('', 'Ràng buộc bảng:', '', ...t.constraints.map(k => `- \`${k.name}\`: \`${k.definition}\``), '');
    if (t.indexes.length) doc.push('Index:', '', ...t.indexes.map(k => `- \`${k.definition}\``), '');
    if (t.triggers.length) doc.push('Trigger:', '', ...t.triggers.map(k => `- \`${k.name}\`: \`${k.definition}\``), '');
    if (t.row_level_security.length) doc.push('RLS:', '', ...t.row_level_security.map(k => `- \`${k.name}\`: ${k.command}; USING \`${k.using_expression ?? ''}\`; WITH CHECK \`${k.check_expression ?? ''}\`.`), '');
  }
  doc.push('## Chuẩn hóa và snapshot', '',
    'Vai trò, quyền, hồ sơ, lần khám, danh mục chỉ số, thuốc, giờ uống và nhắc theo ngày có bảng riêng. Ngày/giờ uống không được ghép thành chuỗi trong bản ghi thuốc. Múi giờ thuộc đơn; thời điểm nhắc được suy ra từ ngày, giờ uống và múi giờ.', '',
    '`evaluation.input_snapshot` là bản sao bất biến để truy vết, không phải nguồn cập nhật. `audit_event.entity_id` là liên kết đa hình, trigger ghi đối tượng đang thay đổi; không dùng FK tới một bảng duy nhất. Không tuyên bố các payload JSONB tự đạt 3NF.', '');
  await writeFile(new URL('../data_dictionary.md', import.meta.url), doc.join('\n'));
}
