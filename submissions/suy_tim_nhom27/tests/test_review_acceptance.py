"""Independent review acceptance; opt-in writes only to the dedicated QA schema.

Legacy records are inspected without mutation. New records are synthetic.
Frontend execution uses deterministic DOM doubles, not a browser/layout claim.
"""
import base64
import json
import os
import subprocess
from io import BytesIO
from pathlib import Path

import psycopg
import pytest
from fastapi import HTTPException
from openpyxl import Workbook

from src.gateway.forms.validation import value_for
from test_revision_acceptance import qa  # guarded exact-schema fixture

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {f['code']: f for f in json.loads((ROOT / 'src/gateway/forms/catalog.json').read_text(encoding='utf-8'))}
DB = pytest.mark.skipif(not os.getenv('FORM_TEST_DSN'), reason='Dedicated synthetic QA connection required')


def preview(qa, patient, visit, values, *, role='doctor', status=200):
    book = Workbook()
    book.active.title = 'REVIEW_QA'
    book.active.append(['patient', 'visit', *values])
    book.active.append([patient['code'], visit['external_id'], *values.values()])
    buffer = BytesIO()
    book.save(buffer)
    book.close()
    return qa.call('POST', '/imports/excel/preview', {
        'filename': 'review-synthetic.xlsx', 'content_base64': base64.b64encode(buffer.getvalue()).decode(),
        'sheet': 'REVIEW_QA', 'header_row': 1, 'patient_column': 1, 'visit_column': 2,
        'mapping': [{'column': i + 3, 'target': code, 'unit_confirmed': True}
                    for i, code in enumerate(values)],
    }, role=role, status=status)


@pytest.mark.parametrize('code', ['ha_nam_ngoi_tam_thu', 'ha_nam_ngoi_tam_truong', 'ha_dung_tam_thu', 'ha_dung_tam_truong', 'lvef'])
def test_physical_values_are_not_coerced_to_missing_or_normal_range(code):
    field = FIELDS[code]
    for value in (None, 0, 50):
        assert value_for(field, value) == value
    for value in (-1, False, '0', float('inf'), float('nan')):
        with pytest.raises(HTTPException):
            value_for(field, value)
    if code == 'lvef':
        assert value_for(field, 100) == 100
        with pytest.raises(HTTPException):
            value_for(field, 100.01)
    else:
        assert value_for(field, 350) == 350  # not a clinical-normality cutoff


def test_result_test_identity_is_not_inferred_from_name_or_converted():
    field = FIELDS['bnp_ntprobnp']
    rows = [dict(test_code=code, name='Tên gốc', value=0, unit='pg/mL',
                 observed_at='2026-10-01T00:15:00+07:00', source='Phiếu giả lập')
            for code in ('BNP', 'NT_PROBNP')]
    assert value_for(field, rows) == rows
    for patch in ({'test_code': None}, {'test_code': 'BNP/NT-proBNP'}, {'unit': 'mg/L'},
                  {'observed_at': '2026-10-01T00:15:00'}, {'value': True}):
        with pytest.raises(HTTPException):
            value_for(field, [{**rows[0], **patch}])
    assert value_for(field, None) is None
    assert value_for(field, []) == []


def test_shipped_frontend_executes_legacy_and_modern_contracts():
    # Reuse only the deterministic harness setup; execute independent assertions.
    harness = (ROOT / 'tests/forms_frontend_regression.cjs').read_text(encoding='utf-8').split('let count=0;')[0]
    checks = r'''
const env=environment(), api=env.api;
const catalog=JSON.parse(fs.readFileSync(path.join(__dirname,'../src/gateway/forms/catalog.json'),'utf8'));
const modern=catalog.find(f=>f.code==='bnp_ntprobnp');
const legacy={code:'legacy',label:'Legacy',group:'X',type:'results',active:true};
let html=api.fieldWidget(legacy,[{name:'Old BNP',value:0,unit:'gốc',observed_at:null}]);
assert(!html.includes('data-column="test_code"'));assert(!html.includes('data-column="source"'));
html=api.fieldWidget(modern,[{test_code:'BNP',name:'Tên gốc',value:0,unit:'pg/mL'}]);
assert(html.includes('data-column="test_code"'));assert(html.includes('value="NT_PROBNP"'));
assert(html.includes('data-column="source"'));assert(html.includes('value="0"'));
api.state.visit={...structuredClone(visit),fields:[modern],values_json:{bnp_ntprobnp:[{test_code:'BNP',name:'Tên gốc',value:0,unit:'pg/mL'}]}};
api.handleInput({target:{value:'NT_PROBNP',dataset:{repeat:'bnp_ntprobnp',index:'0',column:'test_code'}}});
assert.equal(api.state.dirty.bnp_ntprobnp[0].test_code,'NT_PROBNP');
assert.equal(api.state.dirty.bnp_ntprobnp[0].name,'Tên gốc');
assert.equal(api.state.dirty.bnp_ntprobnp[0].value,0);
api.state.actor.role='admin';html=api.fieldWidget(modern,[{test_code:'BNP',name:'Tên gốc',value:0,unit:'pg/mL'}]);
assert(!html.includes('data-repeat='));
console.log('independent frontend contracts passed');
'''
    # __dirname must point to the shipped harness directory when using node -e.
    script = "global.__dirname=" + json.dumps(str(ROOT / 'tests')) + ";\n" + harness + checks
    result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True, encoding='utf-8')
    assert result.returncode == 0, result.stdout + result.stderr


@DB
def test_patient_list_latest_visit_is_clinical_date_not_creation_or_edit(qa):
    patient = qa.patient()
    latest = qa.visit(patient, occurred_at='2026-02-01T10:00:00+07:00')
    older = qa.visit(patient, occurred_at='2025-01-01T10:00:00+07:00')
    undated = qa.visit(patient)
    qa.save(older, {'lvef': 30})
    for role in ('doctor', 'admin'):
        row = next(p for p in qa.call('GET', '/patients', role=role) if p['id'] == patient['id'])
        assert row['latest_visit_external_id'] == latest['external_id']
        assert row['latest_visit_at'] == qa.read(latest)['occurred_at']
    unknown = qa.patient()
    qa.visit(unknown)
    row = next(p for p in qa.call('GET', '/patients') if p['id'] == unknown['id'])
    assert row['latest_visit_at'] is None and row['latest_visit_external_id'] is None
    assert qa.read(undated)['age_at_visit'] is None


@DB
def test_new_fields_manual_excel_same_validation_atomicity_provenance_and_roles(qa):
    patient = qa.patient()
    visit = qa.visit(patient)
    codes = {'lvef': 0, 'ha_dung_tam_thu': 350, 'benh_mach_vanh_da_biet': False}
    current = qa.read(visit)
    assert all(current['values_json'][code] is None for code in codes)
    qa.save(visit, {'lvef': 101, 'ha_dung_tam_thu': 120}, status=422)
    assert qa.read(visit)['revision'] == 0
    bad = preview(qa, patient, visit, {'lvef': 101, 'ha_dung_tam_thu': 120})
    assert bad['eligible'] == 0 and bad['errors'] == 1
    qa.commit(bad, status=422)
    assert qa.read(visit)['revision'] == 0
    good = preview(qa, patient, visit, codes)
    assert good['eligible'] == 1 and good['business_writes'] is False
    assert qa.read(visit)['revision'] == 0
    qa.commit(good)
    saved = qa.read(visit)
    for code, value in codes.items():
        assert saved['values_json'][code] == value
        assert saved['sources_json'][code]['kind'] == 'excel'
        assert saved['sources_json'][code]['location'].startswith('REVIEW_QA!')
    qa.save(visit, {'lvef': None, 'bnp_ntprobnp': []})
    assert qa.read(visit)['values_json']['lvef'] is None
    assert qa.read(visit)['values_json']['bnp_ntprobnp'] == []
    qa.save(visit, {'lvef': 50}, role='admin', status=403)
    preview(qa, patient, visit, {'lvef': 50}, role='admin', status=403)


@DB
def test_excel_structured_results_fail_closed_without_patient_write(qa):
    patient = qa.patient()
    visit = qa.visit(patient)
    plan = preview(qa, patient, visit, {'bnp_ntprobnp': '[{"test_code":"BNP","value":1}]'})
    assert plan['eligible'] == 0 and plan['errors'] == 1
    qa.commit(plan, status=422)
    assert qa.read(visit)['revision'] == 0


@DB
def test_actual_pre_review_pinned_record_retains_old_result_and_medication_shape(qa):
    # Exact schema is validated by the shared fixture before reaching this query.
    with psycopg.connect(os.environ['FORM_TEST_DSN']) as connection:
        connection.execute('SET TRANSACTION READ ONLY')
        connection.execute('SET LOCAL ROLE hf_demo_owner')
        row = connection.execute("""SELECT id FROM form_visit
            WHERE definitions_json ? 'bnp_ntprobnp'
            AND NOT (definitions_json->'bnp_ntprobnp' ? 'contract_version')
            ORDER BY created_at LIMIT 1""").fetchone()
    assert row, 'Need an actual pre-upgrade pinned visit as regression evidence'
    old = qa.read({'id': str(row[0])}, 'admin')
    fields = {f['code']: f for f in old['fields']}
    assert 'lvef' not in fields and 'lvef' not in old['values_json']
    result = {'name': 'Phiếu cũ', 'value': 0, 'unit': 'gốc', 'observed_at': None}
    assert value_for(fields['bnp_ntprobnp'], [result]) == [result]
    with pytest.raises(HTTPException):
        value_for(fields['bnp_ntprobnp'], [{**result, 'test_code': 'BNP'}])
    medication = value_for(fields['danh_sach_thuoc'], [{'name': 'Thuốc cũ'}])[0]
    assert set(medication) == {'name', 'ingredient', 'dose', 'route', 'frequency', 'observed_at'}
    assert qa.read({'id': str(row[0])}, 'admin') == old
