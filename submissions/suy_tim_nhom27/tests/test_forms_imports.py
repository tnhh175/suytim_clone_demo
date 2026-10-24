"""Real PostgreSQL import transaction, replay, parser and preview boundary tests."""
import base64
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
import re

import psycopg
from openpyxl import Workbook
import pytest
from test_forms_api import DSN, live, checked, case, patch, snapshot
from src.gateway.forms import imports

pytestmark = pytest.mark.skipif(not DSN, reason='FORM_TEST_DSN dedicated schema required')


def xlsx(rows, name='QA.xlsx', no_dimension=False):
    book = Workbook()
    sheet = book.active
    sheet.title = 'GIA_LAP'
    for row in rows:
        sheet.append(row)
    out = BytesIO()
    book.save(out)
    book.close()
    content = out.getvalue()
    if no_dimension:
        out = BytesIO()
        with ZipFile(BytesIO(content)) as old, ZipFile(out, 'w') as new:
            for member in old.infolist():
                value = old.read(member.filename)
                if member.filename.startswith('xl/worksheets/'):
                    value = re.sub(rb'<dimension[^>]*/>', b'', value)
                new.writestr(member, value)
        content = out.getvalue()
    return {'filename': name, 'content_base64': base64.b64encode(content).decode()}


def body_for(live, rows=None):
    p, v = case(live)
    rows = rows or [['patient', 'visit', 'weight', 'boolean'], [p['code'], v['external_id'], 0, False]]
    return {**xlsx(rows), 'sheet': 'GIA_LAP', 'header_row': 1, 'patient_column': 1, 'visit_column': 2,
            'mapping': [{'column': 3, 'target': 'can_nang', 'unit_confirmed': True}, {'column': 4, 'target': 'kho_tho_khi_nam'}]}, p, v


def preview(live, body):
    return checked(live[0].post('/api/forms/imports/excel/preview', headers=live[1]['doctor'], json=body))


def commit(live, plan, records=None):
    return live[0].post('/api/forms/imports/commit', headers=live[1]['doctor'], json={'preview_token': plan['preview_token'], 'records': records or [{'index': 0}]})


def db_counts():
    with psycopg.connect(DSN) as conn:
        conn.execute('SET LOCAL ROLE hf_demo_owner')
        return tuple(conn.execute('SELECT count(*) FROM ' + table).fetchone()[0] for table in ('form_patient', 'form_visit', 'form_history', 'form_import_batch'))


def test_preview_inspect_cancel_no_business_writes_and_dimensionless_emptycells(live):
    c, h, _ = live
    body, p, v = body_for(live)
    before = db_counts()
    plan = preview(live, body)
    assert plan['business_writes'] is False and plan['eligible'] == 1
    assert db_counts() == before
    dimensionless = xlsx([[None, 'Header'], [None, 'Value']], no_dimension=True)
    inspect = checked(c.post('/api/forms/imports/excel/inspect', headers=h['doctor'], json={**dimensionless, 'sheet': 'GIA_LAP', 'header_row': 1}))
    assert inspect['columns'][0]['letter'] == 'A' and inspect['sample'][0]['row'] == 2
    empty = checked(c.post('/api/forms/imports/excel/inspect', headers=h['doctor'], json={**xlsx([]), 'sheet': 'GIA_LAP'}))
    assert empty['columns'] == [] or len(empty['columns']) == 1
    assert db_counts() == before


def test_typed_zero_false_null_exact_source_history_and_replay(live):
    c, h, _ = live
    body, p, v = body_for(live)
    plan = preview(live, body)
    result = checked(commit(live, plan))
    assert result['written_fields'] == 2
    current = snapshot(live, v)
    assert current['values_json']['can_nang'] == 0
    assert current['values_json']['kho_tho_khi_nam'] is False
    assert current['sources_json']['can_nang']['location'] == 'GIA_LAP!C2'
    before = db_counts()
    assert checked(commit(live, plan))['replayed'] is True
    renamed = preview(live, {**body, 'filename': 'Renamed.xlsx'})
    assert checked(commit(live, renamed))['replayed'] is True
    assert db_counts() == before


def test_multi_identity_leading_zero_and_missing_identity_pending(live):
    c, h, _ = live
    p1, v1 = case(live)
    p2, v2 = case(live)
    body = {**xlsx([['patient', 'visit', 'weight'], [p1['code'], v1['external_id'], 5], [p2['code'], v2['external_id'], 6], ['missing', 'missing', 7]]),
            'sheet': 'GIA_LAP', 'header_row': 1, 'patient_column': 1, 'visit_column': 2, 'mapping': [{'column': 3, 'target': 'can_nang', 'unit_confirmed': True}]}
    plan = preview(live, body)
    assert plan['eligible'] == 2 and plan['errors'] == 1
    checked(commit(live, plan, [{'index': 2}]), 422)
    result = checked(commit(live, plan, [{'index': 0}, {'index': 1}]))
    assert result['written_records'] == 2 and result['unselected_records'] == 1
    assert snapshot(live, v1)['values_json']['can_nang'] == 5
    assert snapshot(live, v2)['values_json']['can_nang'] == 6
    unique = uuid4().hex[:8]
    p = checked(c.post('/api/forms/patients', headers=h['doctor'], json={'id': str(uuid4()), 'code': '000' + unique}), 201)
    v = checked(c.post('/api/forms/patients/' + p['id'] + '/visits', headers=h['doctor'], json={'id': str(uuid4()), 'external_id': '0001'}), 201)
    body.update(xlsx([['patient', 'visit', 'weight'], [p['code'], '0001', 0]]))
    assert preview(live, body)['eligible'] == 1
    body.update(xlsx([['patient', 'visit', 'weight'], [123, '0001', 0]]))
    assert preview(live, body)['errors'] == 1


def test_conflict_keep_override_null_nondelete_and_manual_supplement(live):
    body, p, v = body_for(live)
    checked(patch(live, v, {'can_nang': 50})[0])
    plan = preview(live, body)
    assert plan['records'][0]['fields'][0]['status'] == 'conflict'
    result = checked(commit(live, plan))
    assert result['written_fields'] == 1 and result['skipped_fields'] == 1
    assert snapshot(live, v)['values_json']['can_nang'] == 50
    plan = preview(live, body)
    checked(commit(live, plan, [{'index': 0, 'override_fields': ['can_nang']}]))
    assert snapshot(live, v)['values_json']['can_nang'] == 0
    null_body = {**body, **xlsx([['patient', 'visit', 'weight', 'boolean'], [p['code'], v['external_id'], None, None]])}
    checked(commit(live, preview(live, null_body)))
    checked(patch(live, v, {'chieu_cao': 170})[0])
    current = snapshot(live, v)
    assert current['values_json']['can_nang'] == 0 and current['values_json']['chieu_cao'] == 170
    assert current['sources_json']['can_nang']['kind'] == 'excel' and current['sources_json']['chieu_cao']['kind'] == 'manual'


@pytest.mark.parametrize('value,conversion,unit', [('1,2','dot_number',True), ('x','native',True), (0,'native',False), ('=1+2','native',True)])
def test_bad_value_unit_formula_error_no_write(live, value, conversion, unit):
    body, p, v = body_for(live)
    body.update(xlsx([['patient', 'visit', 'weight', 'boolean'], [p['code'], v['external_id'], value, False]]))
    body['mapping'][0].update(conversion=conversion, unit_confirmed=unit)
    plan = preview(live, body)
    assert plan['errors'] == 1
    checked(commit(live, plan), 422)
    assert snapshot(live, v)['revision'] == 0


def test_explicit_single_row_no_visit_id_and_duplicate_identity(live):
    body, p, v = body_for(live)
    body.update(xlsx([['name', 'age'], ['Other unrelated source row', 20], ['Selected source row', 0]]))
    body.update(mapping=[{'column': 2, 'target': 'tuoi', 'unit_confirmed': True}], patient_column=None, visit_column=None,
                explicit_target={'row': 3, 'visit_id': v['id'], 'confirmed': True})
    plan = preview(live, body)
    assert len(plan['records']) == 1 and plan['eligible'] == 1
    checked(commit(live, plan))
    assert snapshot(live, v)['values_json']['tuoi'] == 0
    duplicate, p2, v2 = body_for(live)
    duplicate.update(xlsx([['patient','visit','weight','boolean'], [p2['code'],v2['external_id'],1,False], [p2['code'],v2['external_id'],2,True]]))
    assert preview(live, duplicate)['errors'] == 2


def test_explicit_known_uuid_with_two_visits_missing_external_codes(live):
    c, h, _ = live
    p, _ = case(live)
    visits = [checked(c.post('/api/forms/patients/' + p['id'] + '/visits', headers=h['doctor'], json={'id': str(uuid4())}), 201) for _ in range(2)]
    body = {**xlsx([['weight'], [12]]), 'sheet': 'GIA_LAP', 'header_row': 1,
            'mapping': [{'column': 1, 'target': 'can_nang', 'unit_confirmed': True}],
            'explicit_target': {'row': 2, 'visit_id': visits[0]['id'], 'confirmed': True}}
    plan = preview(live, body)
    assert plan['eligible'] == 1 and plan['records'][0]['visit_id'] == visits[0]['id']
    checked(commit(live, plan))
    assert snapshot(live, visits[0])['values_json']['can_nang'] == 12
    assert snapshot(live, visits[1])['values_json']['can_nang'] is None
    body['explicit_target']['visit_id'] = visits[1]['id']
    result = checked(commit(live, preview(live, body)))
    assert result['replayed'] is False and result['written_fields'] == 1


def test_dynamic_mapping_stale_revision_and_concurrent_retry(live):
    c, h, _ = live
    body, p, v = body_for(live)
    code = 'qa_import_' + uuid4().hex
    checked(c.post('/api/forms/fields', headers=h['admin'], json={'code': code, 'label': 'Excel QA', 'type': 'text', 'group': 'QA'}), 201)
    body.update(xlsx([['patient','visit','new'], [p['code'],v['external_id'],'GIA LAP']]))
    body['mapping'] = [{'column': 3, 'target': code}]
    plan = preview(live, body)
    checked(patch(live, v, {'can_nang': 10})[0])
    checked(commit(live, plan), 409)
    plan = preview(live, body)
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: checked(commit(live, plan)), [1, 2]))
    assert sorted(r['replayed'] for r in results) == [False, True]
    assert snapshot(live, v)['values_json'][code] == 'GIA LAP'


def test_transaction_rollback_if_late_write_fails(live, monkeypatch):
    body, p, v = body_for(live)
    p2, v2 = case(live)
    body.update(xlsx([['patient','visit','weight','boolean'], [p['code'],v['external_id'],1,False], [p2['code'],v2['external_id'],2,True]]))
    plan = preview(live, body)
    original = imports.persist
    count = 0
    def fail_second(*args, **kwargs):
        nonlocal count
        count += 1
        if count == 2:
            raise RuntimeError('Synthetic injected late transaction failure')
        return original(*args, **kwargs)
    monkeypatch.setattr(imports, 'persist', fail_second)
    before = db_counts()
    with pytest.raises(RuntimeError, match='Synthetic injected'):
        commit(live, plan, [{'index': 0}, {'index': 1}])
    assert db_counts() == before
    assert snapshot(live, v)['revision'] == 0 and snapshot(live, v2)['revision'] == 0
    monkeypatch.setattr(imports, 'persist', original)
    assert checked(commit(live, plan, [{'index': 0}, {'index': 1}]))['written_records'] == 2


def test_replay_current_scope_and_token_tamper(live):
    c, h, cred = live
    p, v = case(live, 'admin')
    with psycopg.connect(DSN) as conn:
        conn.execute('SET LOCAL ROLE hf_demo_owner')
        conn.execute('INSERT INTO form_access(patient_id,user_id) VALUES(%s,%s)', (p['id'], cred['accounts']['doctor']['id']))
    body = {**xlsx([['patient','visit','weight'],[p['code'],v['external_id'],12]]), 'sheet':'GIA_LAP','header_row':1,'patient_column':1,'visit_column':2,
            'mapping':[{'column':3,'target':'can_nang','unit_confirmed':True}]}
    plan = preview(live, body)
    checked(commit(live, {**plan, 'preview_token': plan['preview_token'][:-1] + ('0' if plan['preview_token'][-1] != '0' else '1')}), 409)
    checked(commit(live, plan))
    with psycopg.connect(DSN) as conn:
        conn.execute('SET LOCAL ROLE hf_demo_owner')
        conn.execute('DELETE FROM form_access WHERE patient_id=%s AND user_id=%s', (p['id'], cred['accounts']['doctor']['id']))
    checked(commit(live, plan), 404)


def test_no_json_import_routes_and_fixture_download(live):
    c, h, _ = live
    paths = c.get('/openapi.json').json()['paths']
    assert '/api/forms/imports/json/preview' not in paths and '/api/forms/imports/template.json' not in paths
    response = c.get('/api/forms/imports/template.xlsx', headers=h['doctor'])
    assert response.status_code == 200 and response.content[:2] == b'PK'
