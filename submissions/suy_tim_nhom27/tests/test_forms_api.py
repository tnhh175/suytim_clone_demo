"""Real PostgreSQL tests; opt in with FORM_TEST_DSN and ignored credentials file."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from psycopg.conninfo import conninfo_to_dict
from src.gateway.main import create_app

DSN = os.getenv('FORM_TEST_DSN')
pytestmark = pytest.mark.skipif(not DSN, reason='FORM_TEST_DSN dedicated synthetic schema required')


@pytest.fixture(scope='module')
def live():
    assert 'd3_form_' in conninfo_to_dict(DSN).get('options', ''), 'Refuse real/public schema'
    credentials = json.loads(Path(os.environ['FORM_TEST_CREDENTIALS']).read_text(encoding='utf-8'))
    with TestClient(create_app(database_url=DSN)) as client:
        headers = {}
        for role in ('admin', 'doctor'):
            account = credentials['accounts'][role]
            response = client.post('/api/forms/auth/' + role, json={'username': account['username'], 'password': account['password']})
            assert response.status_code == 200
            headers[role] = {'Authorization': 'Bearer ' + response.json()['access_token']}
        yield client, headers, credentials


def checked(response, status=200):
    assert response.status_code == status, response.text
    return response.json()


def case(live, role='doctor'):
    client, headers, _ = live
    identity = str(uuid4())
    p = checked(client.post('/api/forms/patients', headers=headers[role], json={'id': identity, 'code': 'QA-' + identity}), 201)
    v = checked(client.post('/api/forms/patients/' + p['id'] + '/visits', headers=headers[role], json={'id': str(uuid4()), 'external_id': 'V-' + identity}), 201)
    return p, v


def snapshot(live, visit):
    return checked(live[0].get('/api/forms/visits/' + visit['id'], headers=live[1]['doctor']))


def patch(live, visit, values, **extra):
    current = snapshot(live, visit)
    body = {'expected_revision': current['revision'], 'catalog_revision': current['catalog_revision'], 'mutation_id': str(uuid4()), 'values': values, **extra}
    return live[0].patch('/api/forms/visits/' + visit['id'], headers=live[1]['doctor'], json=body), body


def test_two_portals_and_spoofed_role(live):
    c, h, credentials = live
    for actual, wrong in [('doctor', 'admin'), ('admin', 'doctor')]:
        account = credentials['accounts'][actual]
        checked(c.post('/api/forms/auth/' + wrong, json={k: account[k] for k in ('username', 'password')}), 401)
        checked(c.post('/api/forms/auth/' + actual, json={**{k: account[k] for k in ('username', 'password')}, 'role': wrong}), 422)
    checked(c.get('/api/forms/patients'), 401)


def test_doctor_cannot_manage_fields(live):
    c, h, _ = live
    checked(c.post('/api/forms/fields', headers=h['doctor'], json={'code': 'qa_' + uuid4().hex, 'label': 'QA', 'group': 'QA', 'type': 'text'}), 403)
    checked(c.patch('/api/forms/fields/tuoi', headers=h['doctor'], json={'expected_version': 1, 'label': 'Sai quyền'}), 403)


def test_two_patients_two_visits_and_owner_scope(live):
    c, h, _ = live
    p1, v1 = case(live)
    p2, v2 = case(live)
    for p in (p1, p2):
        checked(c.post('/api/forms/patients/' + p['id'] + '/visits', headers=h['doctor'], json={'id': str(uuid4())}), 201)
        assert len(checked(c.get('/api/forms/patients/' + p['id'] + '/visits', headers=h['doctor']))) == 2
        checked(c.get('/api/forms/patients/' + p['id'] + '/visits', headers=h['admin']), 404)
    checked(patch(live, v1, {'can_nang': 0})[0])
    assert snapshot(live, v2)['values_json']['can_nang'] is None


def test_null_false_zero_partial_save_clear_and_idempotent_retry(live):
    c, h, _ = live
    _, visit = case(live)
    fields = checked(c.get('/api/forms/fields', headers=h['doctor']))['fields']
    boolean = next(f['code'] for f in fields if f['type'] == 'boolean' and f['active'])
    response, body = patch(live, visit, {'can_nang': 0, boolean: False, 'chieu_cao': None})
    saved = checked(response)
    assert saved['revision'] == 1
    replay = checked(c.patch('/api/forms/visits/' + visit['id'], headers=h['doctor'], json=body))
    assert replay['replayed'] is True
    assert snapshot(live, visit)['values_json'][boolean] is False
    assert snapshot(live, visit)['values_json']['can_nang'] == 0
    checked(patch(live, visit, {'chieu_cao': 170})[0])
    assert snapshot(live, visit)['values_json'][boolean] is False
    checked(patch(live, visit, {'can_nang': None})[0])
    assert snapshot(live, visit)['values_json']['can_nang'] is None
    checked(c.patch('/api/forms/visits/' + visit['id'], headers=h['doctor'], json={**body, 'values': {'can_nang': 12}}), 409)
    history = checked(c.get('/api/forms/visits/' + visit['id'] + '/history', headers=h['doctor']))
    assert len(history) == 3
    assert history[-1]['values_json'][boolean] is False
    assert history[-1]['sources_json'][boolean]['kind'] == 'manual'
    assert history[-1]['actor_id'] == live[2]['accounts']['doctor']['id']


@pytest.mark.parametrize('values', [{'can_nang': '4'}, {'can_nang': False}, {'gioi_tinh': 'unknown'}, {'unknown_field': 1}])
def test_invalid_values_rejected_without_mutation(live, values):
    _, visit = case(live)
    checked(patch(live, visit, values)[0], 422)
    assert snapshot(live, visit)['revision'] == 0


def test_dynamic_field_rename_retire_history_and_type_unit_block(live):
    c, h, _ = live
    _, visit = case(live)
    code = 'qa_' + uuid4().hex
    definition = {'code': code, 'label': 'Ghi chú giả lập QA', 'group': 'QA', 'type': 'textarea'}
    new = checked(c.post('/api/forms/fields', headers=h['admin'], json=definition), 201)
    checked(c.post('/api/forms/fields', headers=h['admin'], json=definition), 409)
    assert snapshot(live, visit)['values_json'][code] is None
    checked(patch(live, visit, {code: 'Giả lập'})[0])
    checked(c.patch('/api/forms/fields/' + code, headers=h['admin'], json={'expected_version': 1, 'label': 'Nhãn thay đổi QA'}))
    assert snapshot(live, visit)['values_json'][code] == 'Giả lập'
    checked(c.patch('/api/forms/fields/' + code, headers=h['admin'], json={'expected_version': 2, 'type': 'number'}), 422)
    checked(c.patch('/api/forms/fields/' + code, headers=h['admin'], json={'expected_version': 2, 'unit': 'kg'}), 422)
    history = checked(c.get('/api/forms/visits/' + visit['id'] + '/history', headers=h['doctor']))
    assert history[0]['definitions_json'][code]['label'] == definition['label']
    checked(c.patch('/api/forms/fields/' + code, headers=h['admin'], json={'expected_version': 2, 'active': False}))
    checked(patch(live, visit, {code: 'Không được nhập'})[0], 422)
    assert snapshot(live, visit)['values_json'][code] == 'Giả lập'


def test_concurrent_save_one_wins_and_catalog_stale(live):
    c, h, _ = live
    _, visit = case(live)
    current = snapshot(live, visit)
    def submit(number):
        return c.patch('/api/forms/visits/' + visit['id'], headers=h['doctor'], json={'expected_revision': current['revision'], 'catalog_revision': current['catalog_revision'], 'mutation_id': str(uuid4()), 'values': {'can_nang': number}}).status_code
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(submit, [10, 20])) == [200, 409]
    checked(patch(live, visit, {'chieu_cao': 180}, catalog_revision=current['catalog_revision'] - 1)[0], 409)


def test_recreate_app_persists_and_logout_revokes(live):
    c, h, _ = live
    _, visit = case(live)
    checked(patch(live, visit, {'can_nang': 42})[0])
    with TestClient(create_app(database_url=DSN)) as restarted:
        assert checked(restarted.get('/api/forms/visits/' + visit['id'], headers=h['doctor']))['values_json']['can_nang'] == 42
    for path in ('/', '/admin/login', '/bac-si/login', '/forms'):
        response = c.get(path)
        assert response.status_code == 200 and 'forms.js' in response.text
