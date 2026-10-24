"""Reproduce the reviewed form catalog from the supplied v0.2 source bundle.

Only field metadata is exported. Never pass the patient workbook to this script.
"""
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]


def build(bundle):
    with zipfile.ZipFile(bundle) as z:
        base = 'Bo-prompt-dev-demo-bieu-mau-v0.2/'
        source = json.loads(z.read(base + 'data-reference/TL06_fields_source.json'))
        raw = z.read(base + source['source_file'])
        assert hashlib.sha256(raw).hexdigest() == source['source_sha256']
        wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        sheet = wb[source['sheet']]
        rows = list(sheet.values)
        # Cross-check original names against the supplied extracted reference.
        for f in source['fields']:
            assert tuple(rows[f['source_excel_row'] - 1][:8]) == tuple(f[k] for k in ('stt','variable_name','label','source_type','choices_or_structure','source_origin','module','direction'))
        wb.close()
    assert len(source['fields']) == 206
    assert max(f['stt'] for f in source['fields']) == 211
    definitions = []
    for f in source['fields']:
        row = f['source_excel_row']
        kind, choices, unit, reason = 'unavailable', [], None, ''
        detail = f['choices_or_structure'] or ''
        group = ('Thông tin nền' if row <= 6 else 'Triệu chứng và dấu hiệu' if row <= 36
                 else 'Lão khoa và hỗ trợ' if row <= 43 else 'Tiền sử và bệnh đồng mắc' if row <= 67
                 else 'Thuốc đang sử dụng' if row <= 69 else 'Cận lâm sàng và theo dõi' if row <= 82
                 else 'Lão khoa và hỗ trợ')
        if row >= 89:
            reason = 'Đầu ra/liên kết module hoặc vai trò dữ liệu cần xác nhận; chưa nhập tay, chưa có AI.'
            group = 'Chờ đặc tả module'
        elif row == 2:
            kind, unit = 'integer', 'tuổi'
        elif row in (4, 5, 26, 27, 28):
            kind, unit = 'number', detail
        elif detail in ('Có; Không', 'Có; Không; Chưa xác định'):
            kind = 'boolean'
        elif row in (3, 42, 43, 77, 79, 84, 85, 86, 88):
            kind = 'select'
            labels = [x.strip() for x in detail.split(';') if x.strip() != 'Chưa đánh giá']
            choices = [{'code': f'v{i+1}', 'label': label} for i, label in enumerate(labels)]
        elif row == 68:
            kind = 'medications'
        elif row in (71, 72, 75, 76):
            kind = 'results'
        elif row in (70, 74):
            kind = 'textarea'
            reason = 'Chỉ lưu báo cáo bằng chữ; chưa nhận tệp đính kèm.'
        else:
            reason = 'Cần làm rõ cấu trúc/thang đo/đơn vị/nguồn dẫn xuất; giữ NULL, không tự tính.'
        role = ('ai_output' if f['direction'] == 'Đầu ra' else
                'module_linked' if f['source_origin'].startswith('AI') else
                'derived' if row in (6, 69) else
                'measured_input' if row in (4,5,24,25,26,27,28,70,71,72,73,74,75,76) else
                'recorded_input')
        code = f['variable_name'] if row < 89 else f'pending_tl06_{row}'
        definitions.append(dict(code=code, label=f['label'], group=group, type=kind, unit=unit,
                                choices=choices, help=reason, order=row, active=True,
                                source=dict(file=source['source_file'], sheet=source['sheet'], row=row,
                                            sha256=source['source_sha256'], variable=f['variable_name'],
                                            module=f['module'], direction=f['direction'],
                                            source_type=f['source_type'], structure=detail, origin=f['source_origin'], stt=f['stt']),
                                data_role=role, implementation_status='unresolved' if kind == 'unavailable' else 'supported', definition_version=1))
    target = ROOT / 'src/gateway/forms/catalog.json'
    target.write_text(json.dumps(definitions, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lines = ['# Đối chiếu TL06 → biểu mẫu v0.2', '',
             'Nguồn: TL06_DataDictionary.xlsx, sheet Trường dữ liệu; đã kiểm SHA-256 và tên biến với workbook gốc.',
             'Không gộp các biến gần tên ở các module. Nhóm/widget/mã lựa chọn là thiết kế kỹ thuật, chưa là quy tắc lâm sàng được duyệt.',
             'Số 0/false là dữ liệu; trường chưa đủ đặc tả luôn NULL. Không tính BMI/eGFR hoặc sinh đầu ra AI.', '',
             '| Dòng | Biến nguồn | Nhãn | Kiểu triển khai | Đơn vị | Ghi chú |', '|---|---|---|---|---|---|']
    for d in definitions:
        lines.append('| ' + ' | '.join(str(x or '').replace('|', '/') for x in
            [d['source']['row'], d['source']['variable'], d['label'], d['type'], d['unit'], d['help']]) + ' |')
    (ROOT / 'docs/form-field-mapping.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print({'source_rows': len(definitions), 'supported': sum(d['type'] != 'unavailable' for d in definitions)})


if __name__ == '__main__':
    build(sys.argv[1])
