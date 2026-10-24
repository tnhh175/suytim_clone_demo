"""Additive, synthetic forms sandbox. Never resets or touches existing public data."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from src.gateway.routers.auth import hash_password
from src.gateway.authorization import Actor
from src.gateway.forms.router import persist, fingerprint


def prepare(dsn, schema, credentials_path):
    if not re.fullmatch(r'd3_form_[a-z0-9_]{1,45}', schema):
        raise ValueError('Use a dedicated d3_form_ sandbox schema')
    credentials_path = Path(credentials_path).resolve()
    if 'local-data' not in credentials_path.parts:
        raise ValueError('Credentials must be in ignored local-data')
    if credentials_path.exists():
        credentials = json.loads(credentials_path.read_text(encoding='utf-8'))
        if credentials['schema'] != schema:
            raise ValueError('Existing credentials belong to another schema')
    else:
        credentials = {'synthetic': True, 'schema': schema, 'accounts': {
            role: {'username': 'forms_' + role, 'password': secrets.token_urlsafe(18)}
            for role in ('admin', 'doctor')}}
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        conn.execute('SET LOCAL ROLE hf_demo_owner')
        conn.execute(sql.SQL('CREATE SCHEMA IF NOT EXISTS {}').format(sql.Identifier(schema)))
        conn.execute(sql.SQL('SET LOCAL search_path TO {}, public').format(sql.Identifier(schema)))
        for table in ('app_user', 'role', 'user_role', 'user_permission', 'auth_session'):
            conn.execute(sql.SQL('CREATE TABLE IF NOT EXISTS {} (LIKE public.{} INCLUDING ALL)').format(sql.Identifier(table), sql.Identifier(table)))
        conn.execute('CREATE TABLE IF NOT EXISTS patient_case(id uuid PRIMARY KEY)')
        conn.execute("INSERT INTO role(code) VALUES('admin'),('doctor') ON CONFLICT DO NOTHING")
        for role, account in credentials['accounts'].items():
            row = conn.execute('INSERT INTO app_user(username,password_hash) VALUES(%s,%s) ON CONFLICT(username) DO UPDATE SET active=true,password_hash=EXCLUDED.password_hash RETURNING id',
                (account['username'], hash_password(account['password']))).fetchone()
            conn.execute('INSERT INTO user_role(user_id,role_code) VALUES(%s,%s) ON CONFLICT DO NOTHING', (row['id'], role))
            account['id'] = str(row['id'])
        # Migrations contain their own transaction boundaries: execute each on a
        # fresh transaction below, keeping the schema scoped to this connection.
    with psycopg.connect(dsn, autocommit=True, row_factory=dict_row) as conn:
        conn.execute('SET ROLE hf_demo_owner')
        conn.execute(sql.SQL('SET search_path TO {}, public').format(sql.Identifier(schema)))
        for migration in sorted((ROOT / 'database/migrations').glob('00[23]_*.sql')):
            conn.execute(migration.read_text(encoding='utf-8'))
        with conn.transaction():
            for definition in json.loads((ROOT / 'src/gateway/forms/catalog.json').read_text(encoding='utf-8')):
                conn.execute('INSERT INTO form_field(code,definition) VALUES(%s,%s) ON CONFLICT DO NOTHING', (definition['code'], Jsonb(definition)))
                conn.execute('INSERT INTO form_field_history(code,version,definition) VALUES(%s,1,%s) ON CONFLICT DO NOTHING', (definition['code'], Jsonb(definition)))
            dynamic = {'code': 'ghi_chu_demo_qa', 'label': 'Ghi chú bổ sung demo', 'group': 'Trường bổ sung', 'type': 'textarea',
                       'unit': None, 'choices': [], 'help': 'Trường giả lập do Admin bổ sung; không phải quy tắc y khoa.', 'order': 1000,
                       'active': True, 'source': {'origin': 'admin_definition'}, 'data_role': 'recorded_input'}
            added = conn.execute('INSERT INTO form_field(code,definition,updated_by) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING RETURNING code',
                                 (dynamic['code'], Jsonb(dynamic), credentials['accounts']['admin']['id'])).fetchone()
            if added:
                conn.execute('INSERT INTO form_field_history(code,version,definition,actor_id) VALUES(%s,1,%s,%s)', (dynamic['code'], Jsonb(dynamic), credentials['accounts']['admin']['id']))
                conn.execute('UPDATE form_catalog SET revision=revision+1 WHERE id=1')
            for number in (1, 2):
                code = f'SYN-FORM-{number:03}'
                row = conn.execute('INSERT INTO form_patient(id,code,display_name,owner_id) VALUES(%s,%s,%s,%s) ON CONFLICT(code) DO UPDATE SET code=EXCLUDED.code RETURNING id',
                    (uuid4(), code, f'Người bệnh giả lập {number}', credentials['accounts']['doctor']['id'])).fetchone()
                for account in credentials['accounts'].values():
                    conn.execute('INSERT INTO form_access(patient_id,user_id) VALUES(%s,%s) ON CONFLICT DO NOTHING', (row['id'], account['id']))
                for visit in (1, 2):
                    conn.execute('INSERT INTO form_visit(id,patient_id,external_id,created_by) VALUES(%s,%s,%s,%s) ON CONFLICT(patient_id,external_id) DO NOTHING',
                        (uuid4(), row['id'], f'VISIT-{number:03}-{visit}', credentials['accounts']['doctor']['id']))
            definitions = {r['code']: {**r['definition'], 'version': r['version']} for r in conn.execute('SELECT code,definition,version FROM form_field').fetchall()}
            catalog_revision = conn.execute('SELECT revision FROM form_catalog WHERE id=1').fetchone()['revision']
            actor = Actor(credentials['accounts']['doctor']['id'], credentials['accounts']['doctor']['username'], 'doctor', frozenset())
            visit = conn.execute("SELECT v.* FROM form_visit v JOIN form_patient p ON p.id=v.patient_id WHERE p.code='SYN-FORM-001' AND v.external_id='VISIT-001-1'").fetchone()
            if visit['revision'] == 0:
                for changes in ({'can_nang': 0, 'kho_tho_khi_nam': False, 'chieu_cao': None, dynamic['code']: 'Ghi chú giả lập lần đầu.'},
                                {dynamic['code']: 'Ghi chú giả lập đã chỉnh sửa để xem lịch sử.'}):
                    persist(conn, actor, visit, catalog_revision, definitions, changes,
                            {k: {'kind': 'synthetic_seed', 'actor_id': str(actor.user_id)} for k in changes}, uuid4(), fingerprint(changes))
                    visit = conn.execute('SELECT * FROM form_visit WHERE id=%s', (visit['id'],)).fetchone()
            conn.execute(sql.SQL('GRANT USAGE ON SCHEMA {} TO hf_demo_runtime').format(sql.Identifier(schema)))
            conn.execute('GRANT SELECT ON app_user,role,user_role,user_permission TO hf_demo_runtime')
            conn.execute('GRANT SELECT,INSERT,UPDATE ON auth_session TO hf_demo_runtime')
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(json.dumps(credentials, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'schema': schema, 'synthetic': True, 'credentials_file': str(credentials_path), 'patients': 2, 'visits': 4}))
    return credentials


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--schema', required=True)
    parser.add_argument('--credentials-file', required=True)
    args = parser.parse_args()
    prepare(os.environ['DATABASE_URL'], args.schema, args.credentials_file)
