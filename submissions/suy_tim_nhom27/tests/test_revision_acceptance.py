"""Independent acceptance scenarios for approved C01-C13/K01-K15.

Opt-in only. All writes require the exact dedicated synthetic QA schema.
No browser/visual or real hospital-file compatibility claims are made here.
"""
import base64
import json
import os
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg.conninfo import conninfo_to_dict
import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook

from src.gateway.main import create_app

DSN = os.getenv('FORM_TEST_DSN')
pytestmark = pytest.mark.skipif(not DSN, reason='Dedicated synthetic QA connection required')


class AcceptanceClient:
    def __repr__(self):
        return '<acceptance client; credentials and tokens redacted>'

    def __init__(self, client, headers):
        self.client, self.headers = client, headers

    def call(self, method, path, body=None, role='doctor', status=200):
        response = self.client.request(method, '/api/forms' + path,
                                       headers=self.headers[role], json=body)
        assert response.status_code == status, response.text
        return response.json()

    def patient(self, **extra):
        return self.call('POST', '/patients', {'id': str(uuid4()), **extra}, status=201)

    def visit(self, patient, **extra):
        return self.call('POST', '/patients/' + patient['id'] + '/visits',
                         {'id': str(uuid4()), 'external_id': 'QA-' + uuid4().hex, **extra}, status=201)

    def read(self, visit, role='doctor'):
        return self.call('GET', '/visits/' + visit['id'], role=role)

    def save(self, visit, values=None, role='doctor', status=200, **extra):
        old = self.read(visit, role)
        return self.call('PATCH', '/visits/' + visit['id'],
                         {'expected_revision': old['revision'], 'catalog_revision': old['catalog_revision'],
                          'mutation_id': str(uuid4()), 'values': values or {}, **extra}, role, status)

    def preview(self, rows):
        book = Workbook()
        book.active.title = 'QA_SYNTHETIC'
        for row in [['patient', 'visit', 'weight', 'orthopnea'], *rows]:
            book.active.append(row)
        output = BytesIO()
        book.save(output)
        book.close()
        body = {'filename': 'acceptance-synthetic.xlsx', 'content_base64': base64.b64encode(output.getvalue()).decode(),
                'sheet': 'QA_SYNTHETIC', 'header_row': 1, 'patient_column': 1, 'visit_column': 2,
                'mapping': [{'column': 3, 'target': 'can_nang', 'unit_confirmed': True},
                            {'column': 4, 'target': 'kho_tho_khi_nam'}]}
        return self.call('POST', '/imports/excel/preview', body)

    def commit(self, preview, indexes=(0,), status=200):
        return self.call('POST', '/imports/commit', {'preview_token': preview['preview_token'],
                         'records': [{'index': index} for index in indexes]}, status=status)


@pytest.fixture(scope='module')
def qa():
    options = conninfo_to_dict(DSN).get('options', '')
    assert options == '-csearch_path=d3_form_qa_20261023,public', 'Refuse writes outside dedicated QA schema'
    credentials = json.loads(Path(os.environ['FORM_TEST_CREDENTIALS']).read_text(encoding='utf-8'))
    with TestClient(create_app(database_url=DSN)) as client:
        headers = {}
        for role in ('doctor', 'admin'):
            account = credentials['accounts'][role]
            response = client.post('/api/v1/auth/token', json={key: account[key] for key in ('username', 'password')})
            assert response.status_code == 200, 'Synthetic login failed'
            headers[role] = {'Authorization': 'Bearer ' + response.json()['access_token']}
        yield AcceptanceClient(client, headers)


def test_k01_k02_minimal_identity_and_server_role_boundaries(qa):
    first, second = qa.patient(), qa.patient()
    assert re.fullmatch(r'BN-\d{5}', first['code']) and first['code'] != second['code']
    assert re.fullmatch(r'Người bệnh giả lập \d+', first['display_name'])
    assert all(first[key] is None for key in ('date_of_birth', 'sex', 'insurance_number'))
    saved = next(p for p in qa.call('GET', '/patients') if p['id'] == first['id'])
    assert saved['code'] == first['code']
    qa.call('POST', '/patients', {'id': str(uuid4())}, role='admin', status=403)
    qa.call('POST', '/patients', {'id': str(uuid4()), 'code': 'BN-00001'}, status=422)
    qa.call('POST', '/fields', {'code': 'qa_' + uuid4().hex, 'label': 'QA', 'group': 'Trường bổ sung', 'type': 'text'}, status=403)


def test_k03_admin_shared_read_and_clinical_readonly(qa):
    patient = qa.patient()
    visit = qa.visit(patient)
    qa.save(visit, {'can_nang': 64, 'kho_tho_khi_nam': False})
    assert patient['id'] in {p['id'] for p in qa.call('GET', '/patients', role='admin')}
    assert qa.read(visit, 'admin')['values_json'] == qa.read(visit)['values_json']
    qa.save(visit, {'can_nang': 65}, role='admin', status=403)
    qa.call('POST', '/patients/' + patient['id'] + '/visits', {'id': str(uuid4())}, role='admin', status=403)
    assert qa.read(visit)['values_json']['can_nang'] == 64


def test_k03_doctor_cannot_read_or_write_out_of_scope(qa):
    patient = qa.patient()
    visit = qa.visit(patient)
    # Fixture setup changes ownership of only this freshly generated synthetic record.
    admin_id = qa.client.get('/api/v1/auth/me', headers=qa.headers['admin']).json()['user_id']
    with psycopg.connect(DSN) as connection:
        connection.execute('SET LOCAL ROLE hf_demo_owner')
        connection.execute('UPDATE form_patient SET owner_id=%s WHERE id=%s', (admin_id, patient['id']))
    for path in ('/patients/' + patient['id'] + '/visits', '/patients/' + patient['id'] + '/overview', '/visits/' + visit['id'], '/visits/' + visit['id'] + '/history'):
        qa.call('GET', path, status=404)
    qa.call('PATCH', '/visits/' + visit['id'], {'expected_revision': 0, 'catalog_revision': visit['catalog_revision'], 'mutation_id': str(uuid4()), 'values': {'can_nang': 60}}, status=404)
    assert qa.read(visit, 'admin')['revision'] == 0


def test_k05_k06_k07_chronology_and_scoped_demographics(qa):
    patient = qa.patient(date_of_birth='2000-10-26', sex='female', insurance_number='0001234567')
    old = qa.visit(patient, occurred_at='2024-10-25T10:00:00+07:00', metadata={'primary_diagnosis_code': 'I50', 'secondary_diagnosis_codes': ['E11'], 'reason': 'Ca kiểm thử giả lập', 'visit_type': 'new'})
    qa.save(old, {'can_nang': 60})
    changed = qa.call('PATCH', '/patients/' + patient['id'], {'expected_revision': patient['demographic_revision'], 'mutation_id': str(uuid4()), 'date_of_birth': '2000-10-25', 'sex': 'other'}, role='admin')
    new = qa.visit(patient, occurred_at='2025-10-25T10:00:00+07:00', metadata={'primary_diagnosis_code': 'I50.9', 'visit_type': 'followup'})
    undated = qa.visit(patient)
    qa.save(old, {'can_nang': 61})  # Last edited is deliberately not the latest clinical visit.
    overview = qa.call('GET', '/patients/' + patient['id'] + '/overview')
    assert [v['id'] for v in overview['visits']] == [new['id'], old['id'], undated['id']]
    assert overview['latest_visit']['id'] == new['id']
    assert overview['patient']['insurance_number'] == '0001234567'
    assert qa.read(old)['age_at_visit'] == 23 and qa.read(new)['age_at_visit'] == 25
    assert qa.read(old)['demographics_snapshot']['sex'] == 'female'
    assert qa.read(new)['demographics_snapshot']['sex'] == 'other'
    assert qa.read(old)['metadata']['primary_diagnosis_code'] == 'I50'
    assert qa.read(new)['values_json']['can_nang'] is None
    assert qa.read(undated)['occurred_at'] is None and qa.read(undated)['age_at_visit'] is None
    history = qa.call('GET', '/patients/' + patient['id'] + '/history', role='admin')
    assert history[0]['before_json']['sex'] == 'female' and history[0]['after_json']['sex'] == 'other'
    assert changed['demographic_revision'] == 1


def test_k09_k10_draft_and_saved_visit_pin_label_group_options_and_retirement(qa):
    code = 'qa_accept_' + uuid4().hex
    field = {'code': code, 'label': 'Nhãn trước', 'group': 'Trường bổ sung', 'type': 'select', 'choices': [{'code': 'v1', 'label': 'Lựa chọn trước'}]}
    qa.call('POST', '/fields', field, role='admin', status=201)
    patient = qa.patient()
    saved, draft = qa.visit(patient), qa.visit(patient)
    qa.save(saved, {code: 'v1'})
    before = qa.read(saved)
    extra = 'qa_added_' + uuid4().hex
    qa.call('POST', '/fields', {'code': extra, 'label': 'Trường mới', 'group': 'Trường bổ sung', 'type': 'text'}, role='admin', status=201)
    qa.call('PATCH', '/fields/' + code, {'expected_version': 1, 'label': 'Nhãn sau', 'group': 'Thông tin nền'}, role='admin')
    qa.call('PATCH', '/fields/' + code, {'expected_version': 2, 'active': False}, role='admin')
    new = qa.visit(patient)
    for visit in (saved, draft):
        for role in ('doctor', 'admin'):
            snapshot = qa.read(visit, role)
            assert snapshot['catalog_revision'] == before['catalog_revision']
            definition = next(f for f in snapshot['fields'] if f['code'] == code)
            assert definition['label'] == 'Nhãn trước' and definition['group'] == 'Trường bổ sung'
            assert definition['choices'] == field['choices'] and definition['active'] is True
            assert extra not in snapshot['values_json']
        qa.save(visit, {code: 'v1'})  # Retiring globally must not make an old pinned draft unsavable.
    assert extra in qa.read(new)['values_json']
    assert qa.read(new)['catalog_revision'] > before['catalog_revision']
    qa.save(new, {code: 'v1'}, status=422)
    qa.call('PATCH', '/fields/' + code, {'expected_version': 3, 'type': 'number'}, role='admin', status=422)
    historical = qa.call('GET', '/visits/' + saved['id'] + '/history')
    assert all(h['definitions_json'][code]['label'] == 'Nhãn trước' for h in historical)


@pytest.mark.parametrize('invalid', [{'tuoi': 150}, {'can_nang': -1}])
def test_k13_invalid_value_rejects_entire_atomic_save(qa, invalid):
    visit = qa.visit(qa.patient())
    qa.save(visit, {'chieu_cao': 170, **invalid}, status=422)
    assert qa.read(visit)['revision'] == 0 and qa.read(visit)['values_json']['chieu_cao'] is None


def test_k13_null_false_zero_and_recorded_age_not_birthdate(qa):
    patient = qa.patient()
    visit = qa.visit(patient, occurred_at='2026-10-01T09:00:00+07:00')
    qa.save(visit, {'can_nang': 0, 'kho_tho_khi_nam': False, 'chieu_cao': None, 'tuoi': 48})
    current = qa.read(visit)
    assert current['values_json']['can_nang'] == 0 and current['values_json']['kho_tho_khi_nam'] is False
    assert current['values_json']['chieu_cao'] is None
    assert current['demographics_snapshot']['date_of_birth'] is None and current['age_at_visit'] is None
    qa.save(visit, {'kho_tho_khi_nam': None})
    assert qa.read(visit)['values_json']['kho_tho_khi_nam'] is None


def test_k06_k07_medication_provenance_and_no_copy_to_new_visit(qa):
    patient = qa.patient()
    old = qa.visit(patient, occurred_at='2025-05-01T10:00:00+07:00')
    field = next(f['code'] for f in qa.read(old)['fields'] if f['type'] == 'medications' and f['active'])
    qa.save(old, {field: [{'name': 'Thuốc giả lập kiểm thử', 'dose': 'Giá trị kiểm thử', 'observed_at': '2025-05-01T10:00:00+07:00'}]})
    new = qa.visit(patient, occurred_at='2026-05-01T10:00:00+07:00')
    assert qa.read(new)['values_json'][field] is None
    assert qa.read(old)['values_json'][field][0]['observed_at'] == '2025-05-01T10:00:00+07:00'
    assert qa.read(old)['sources_json'][field]['kind'] == 'manual'


def test_k07_age_at_vietnam_local_birthday_after_midnight(qa):
    patient = qa.patient(date_of_birth='2000-10-26')
    visit = qa.visit(patient, occurred_at='2024-10-26T00:30:00+07:00')
    current = qa.read(visit)
    assert datetime.fromisoformat(current['occurred_at']) == datetime.fromisoformat('2024-10-26T00:30:00+07:00')
    assert current['age_at_visit'] == 24, 'Age must use clinical date in Asia/Ho_Chi_Minh, not the preceding UTC date'


def test_k11_k12_source_alias_leading_zero_null_and_replay(qa):
    source = '000' + uuid4().hex
    patient = qa.patient(external_id=source, insurance_number='00000123')
    visit = qa.visit(patient, external_id='00001')
    qa.save(visit, {'can_nang': 64})
    qa.call('PATCH', '/patients/' + patient['id'], {'expected_revision': 0, 'mutation_id': str(uuid4()), 'external_id': 'NEW-' + source}, role='admin')
    plan = qa.preview([[source, '00001', None, False]])
    assert plan['eligible'] == 1
    assert plan['records'][0]['target_patient_code'] == patient['code']
    assert plan['records'][0]['target_patient_name'] == patient['display_name']
    assert plan['records'][0]['patient_code'] == source
    result = qa.commit(plan)
    assert result['records'][0]['target_patient_code'] == patient['code']
    assert result['written_records'] == 1
    current = qa.read(visit)
    assert current['values_json']['can_nang'] == 64 and current['values_json']['kho_tho_khi_nam'] is False
    assert current['sources_json']['kho_tho_khi_nam']['location'] == 'QA_SYNTHETIC!D2'
    assert qa.commit(plan)['replayed'] is True
    assert qa.read(visit)['revision'] == current['revision']
    qa.call('POST', '/patients', {'id': str(uuid4()), 'external_id': source}, status=409)


def test_k12_missing_wrong_pair_unknown_patient_and_invalid_selection_no_write(qa):
    p1, p2 = qa.patient(), qa.patient()
    v1, v2 = qa.visit(p1), qa.visit(p2)
    plan = qa.preview([[p1['code'], v1['external_id'], 50, None],
                       [None, v1['external_id'], 51, None],
                       [p1['code'], v2['external_id'], 52, None],
                       ['NO-SUCH-' + uuid4().hex, v1['external_id'], 53, None]])
    assert plan['eligible'] == 1 and plan['errors'] == 3
    qa.commit(plan, indexes=(0, 1), status=422)
    assert qa.read(v1)['revision'] == 0 and qa.read(v2)['revision'] == 0
    qa.commit(plan)
    assert qa.read(v1)['values_json']['can_nang'] == 50 and qa.read(v2)['revision'] == 0


def test_k12_stale_second_record_rolls_back_first_record(qa):
    p1, p2 = qa.patient(), qa.patient()
    v1, v2 = qa.visit(p1), qa.visit(p2)
    plan = qa.preview([[p1['code'], v1['external_id'], 50, None], [p2['code'], v2['external_id'], 51, None]])
    qa.save(v2, {'can_nang': 70})
    qa.commit(plan, indexes=(0, 1), status=409)
    assert qa.read(v1)['revision'] == 0 and qa.read(v1)['values_json']['can_nang'] is None
    assert qa.read(v2)['values_json']['can_nang'] == 70


def test_k04_legacy_saved_catalog_matches_latest_history_readonly():
    """Run after migration replay; reads only, does not create a migration fixture.

    This proves observable legacy snapshot consistency, not historical row-count
    preservation (which needs an independent pre-migration backup comparison).
    """
    assert conninfo_to_dict(DSN).get('options', '') == '-csearch_path=d3_form_qa_20261023,public'
    with psycopg.connect(DSN) as connection:
        connection.execute('SET TRANSACTION READ ONLY')
        connection.execute('SET LOCAL ROLE hf_demo_owner')
        remaining = connection.execute("SELECT count(*) FROM form_visit WHERE snapshot_origin='migration_004_first_saved_catalog'").fetchone()[0]
        assert remaining == 0, 'Replay corrected migration 004 before acceptance'
        rows = connection.execute('''SELECT v.definitions_json, v.catalog_revision, v.values_json,
                  h.definitions_json, h.catalog_revision
              FROM form_visit v JOIN LATERAL
                  (SELECT definitions_json,catalog_revision FROM form_history
                   WHERE visit_id=v.id ORDER BY revision DESC LIMIT 1) h ON true
              WHERE v.snapshot_origin='migration_004_last_saved_catalog' ''').fetchall()
    assert rows, 'Expected pre-migration saved QA visits as migration evidence'
    for definitions, revision, values, historical_definitions, historical_revision in rows:
        assert definitions == historical_definitions and revision == historical_revision
        assert set(values).issubset(definitions), 'Legacy saved values must not become invisible after migration'
