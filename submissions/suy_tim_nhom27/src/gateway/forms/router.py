from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import AwareDatetime, Field
from psycopg.types.json import Jsonb

from ..authorization import Actor, get_current_actor, require_role
from ..database import staff_connection
from ..routers.auth import LoginPayload, TokenResponse, login
from .validation import Input, FieldDefinition, value_for

router = APIRouter(prefix='/api/forms', tags=['Biểu mẫu suy tim'])


class Credentials(Input):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


@router.post('/auth/admin', response_model=TokenResponse)
def admin_login(body: Credentials, request: Request):
    return login(LoginPayload(**body.model_dump(), selected_role='admin'), request)


@router.post('/auth/doctor', response_model=TokenResponse)
def doctor_login(body: Credentials, request: Request):
    return login(LoginPayload(**body.model_dump(), selected_role='doctor'), request)


def form_actor(actor: Actor = Depends(get_current_actor)):
    require_role(actor, {'doctor', 'admin'})
    return actor


def catalog(conn, lock=False):
    revision = conn.execute('SELECT revision FROM form_catalog WHERE id=1' + (' FOR UPDATE' if lock else ' FOR SHARE')).fetchone()['revision']
    fields = conn.execute('SELECT code, definition, version FROM form_field ORDER BY code').fetchall()
    return revision, {r['code']: {**r['definition'], 'version': r['version']} for r in fields}


def patient_access(conn, actor, patient_id):
    p = conn.execute('''SELECT p.* FROM form_patient p WHERE p.id=%s AND
      (p.owner_id=%s OR EXISTS(SELECT 1 FROM form_access a WHERE a.patient_id=p.id AND a.user_id=%s))''',
      (patient_id, actor.user_id, actor.user_id)).fetchone()
    if p is None:
        raise HTTPException(404, 'Không tìm thấy hồ sơ trong phạm vi tài khoản')
    return p


def visit_access(conn, actor, visit_id, lock=False):
    v = conn.execute('SELECT * FROM form_visit WHERE id=%s' + (' FOR UPDATE' if lock else ''), (visit_id,)).fetchone()
    if v is None:
        raise HTTPException(404, 'Không tìm thấy lượt')
    patient_access(conn, actor, v['patient_id'])
    return v


@router.get('/fields')
def fields(request: Request, actor=Depends(form_actor)):
    with staff_connection(request, actor) as conn:
        revision, definitions = catalog(conn)
    return {'revision': revision, 'fields': sorted(definitions.values(), key=lambda d: (d['order'], d['code']))}


@router.post('/fields', status_code=201)
def add_field(body: FieldDefinition, request: Request, actor=Depends(form_actor)):
    require_role(actor, {'admin'})
    definition = body.model_dump()
    definition.update(source={'origin': 'admin_definition'}, data_role='recorded_input')
    with staff_connection(request, actor) as conn:
        catalog(conn, lock=True)
        if conn.execute('SELECT 1 FROM form_field WHERE code=%s', (body.code,)).fetchone():
            raise HTTPException(409, 'Mã trường đã tồn tại')
        conn.execute('INSERT INTO form_field(code,definition,updated_by) VALUES(%s,%s,%s)', (body.code, Jsonb(definition), actor.user_id))
        conn.execute('INSERT INTO form_field_history(code,version,definition,actor_id) VALUES(%s,1,%s,%s)', (body.code, Jsonb(definition), actor.user_id))
        conn.execute('UPDATE form_catalog SET revision=revision+1 WHERE id=1')
    return {**definition, 'version': 1}


class FieldEdit(Input):
    expected_version: int = Field(ge=1)
    label: str | None = Field(default=None, min_length=1, max_length=200)
    group: str | None = Field(default=None, min_length=1, max_length=100)
    help: str | None = Field(default=None, max_length=1000)
    order: int | None = Field(default=None, ge=0, le=10000)
    active: bool | None = None


@router.patch('/fields/{code}')
def edit_field(code: str, body: FieldEdit, request: Request, actor=Depends(form_actor)):
    require_role(actor, {'admin'})
    with staff_connection(request, actor) as conn:
        _, definitions = catalog(conn, lock=True)
        old = definitions.get(code)
        if not old:
            raise HTTPException(404, 'Không tìm thấy trường')
        if old['version'] != body.expected_version:
            raise HTTPException(409, 'Định nghĩa đã thay đổi, tải lại trước khi sửa')
        patch = body.model_dump(exclude={'expected_version'}, exclude_unset=True)
        if any(v is None or (isinstance(v, str) and k in {'label', 'group'} and not v.strip()) for k, v in patch.items()):
            raise HTTPException(422, 'Thuộc tính không được để trống')
        updated = {**old, **patch}
        updated.pop('version')
        version = old['version'] + 1
        conn.execute('UPDATE form_field SET definition=%s,version=%s,updated_by=%s,updated_at=now() WHERE code=%s',
                     (Jsonb(updated), version, actor.user_id, code))
        conn.execute('INSERT INTO form_field_history(code,version,definition,actor_id) VALUES(%s,%s,%s,%s)',
                     (code, version, Jsonb(updated), actor.user_id))
        conn.execute('UPDATE form_catalog SET revision=revision+1 WHERE id=1')
    return {**updated, 'version': version}


class PatientCreate(Input):
    id: UUID
    code: str = Field(min_length=1, max_length=60, pattern=r'^[A-Za-z0-9_-]+$')
    external_id: str | None = Field(default=None, min_length=1, max_length=100)
    display_name: str | None = Field(default=None, max_length=200)


@router.get('/patients')
def patients(request: Request, actor=Depends(form_actor)):
    with staff_connection(request, actor) as conn:
        return conn.execute('''SELECT p.* FROM form_patient p WHERE p.owner_id=%s OR EXISTS
            (SELECT 1 FROM form_access a WHERE a.patient_id=p.id AND a.user_id=%s) ORDER BY p.created_at DESC''',
            (actor.user_id, actor.user_id)).fetchall()


@router.post('/patients', status_code=201)
def create_patient(body: PatientCreate, request: Request, actor=Depends(form_actor)):
    with staff_connection(request, actor) as conn:
        row = conn.execute('''INSERT INTO form_patient(id,code,external_id,display_name,owner_id) VALUES(%s,%s,%s,%s,%s)
          ON CONFLICT(id) DO NOTHING RETURNING *''', (body.id, body.code, body.external_id, body.display_name, actor.user_id)).fetchone()
        if row is None:
            row = patient_access(conn, actor, body.id)
            if row['owner_id'] != actor.user_id or any(row[k] != getattr(body, k) for k in ('code', 'external_id', 'display_name')):
                raise HTTPException(409, 'Mã yêu cầu đã được dùng với hồ sơ khác')
    return row


class VisitCreate(Input):
    id: UUID
    external_id: str | None = Field(default=None, min_length=1, max_length=100)
    occurred_at: AwareDatetime | None = None


@router.get('/patients/{patient_id}/visits')
def visits(patient_id: UUID, request: Request, actor=Depends(form_actor)):
    with staff_connection(request, actor) as conn:
        patient_access(conn, actor, patient_id)
        return conn.execute('SELECT id,patient_id,external_id,occurred_at,revision,updated_at FROM form_visit WHERE patient_id=%s ORDER BY updated_at DESC', (patient_id,)).fetchall()


@router.post('/patients/{patient_id}/visits', status_code=201)
def create_visit(patient_id: UUID, body: VisitCreate, request: Request, actor=Depends(form_actor)):
    with staff_connection(request, actor) as conn:
        patient_access(conn, actor, patient_id)
        row = conn.execute('''INSERT INTO form_visit(id,patient_id,external_id,occurred_at,created_by) VALUES(%s,%s,%s,%s,%s)
          ON CONFLICT(id) DO NOTHING RETURNING *''', (body.id, patient_id, body.external_id, body.occurred_at, actor.user_id)).fetchone()
        if row is None:
            row = visit_access(conn, actor, body.id)
            if row['patient_id'] != patient_id or row['created_by'] != actor.user_id or row['external_id'] != body.external_id or row['occurred_at'] != body.occurred_at:
                raise HTTPException(409, 'Mã yêu cầu đã được dùng với lượt khác')
    return row


def present_visit(row, definitions, revision):
    return {**row, 'values_json': {**{k: None for k in definitions}, **row['values_json']}, 'catalog_revision': revision}


@router.get('/visits/{visit_id}')
def get_visit(visit_id: UUID, request: Request, actor=Depends(form_actor)):
    with staff_connection(request, actor) as conn:
        revision, definitions = catalog(conn)
        return present_visit(visit_access(conn, actor, visit_id), definitions, revision)


class Save(Input):
    expected_revision: int = Field(ge=0)
    catalog_revision: int = Field(ge=1)
    mutation_id: UUID
    values: dict = Field(max_length=500)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()


def persist(conn, actor, row, revision, definitions, changes, sources, mutation_id, request_hash):
    values = {**row['values_json'], **changes}
    origins = {**row['sources_json'], **sources}
    new_revision = row['revision'] + 1
    conn.execute('UPDATE form_visit SET values_json=%s,sources_json=%s,revision=%s,updated_at=now() WHERE id=%s',
                 (Jsonb(values), Jsonb(origins), new_revision, row['id']))
    conn.execute('''INSERT INTO form_history(visit_id,revision,mutation_id,request_hash,actor_id,values_json,sources_json,definitions_json,catalog_revision)
      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
      (row['id'], new_revision, mutation_id, request_hash, actor.user_id, Jsonb(values), Jsonb(origins), Jsonb(definitions), revision))
    return {'revision': new_revision, 'mutation_id': mutation_id, 'saved': True}


@router.patch('/visits/{visit_id}')
def save(visit_id: UUID, body: Save, request: Request, actor=Depends(form_actor)):
    request_hash = fingerprint(body.model_dump())
    with staff_connection(request, actor) as conn:
        revision, definitions = catalog(conn)
        row = visit_access(conn, actor, visit_id, lock=True)
        previous = conn.execute('SELECT revision,request_hash,actor_id FROM form_history WHERE visit_id=%s AND mutation_id=%s', (visit_id, body.mutation_id)).fetchone()
        if previous:
            if previous['request_hash'] != request_hash or previous['actor_id'] != actor.user_id:
                raise HTTPException(409, 'Mã lần lưu đã dùng với nội dung khác')
            return {'revision': previous['revision'], 'mutation_id': body.mutation_id, 'saved': True, 'replayed': True}
        if row['revision'] != body.expected_revision or revision != body.catalog_revision:
            raise HTTPException(409, 'Dữ liệu hoặc danh mục đã thay đổi; tải lại và đối chiếu trước khi lưu')
        changes = {}
        for code, value in body.values.items():
            if code not in definitions:
                raise HTTPException(422, detail={'fields': {code: 'Mã trường không tồn tại'}})
            if not definitions[code]['active']:
                raise HTTPException(422, detail={'fields': {code: 'Trường đã ngừng dùng'}})
            changes[code] = value_for(definitions[code], value)
        sources = {k: {'kind': 'manual', 'actor_id': str(actor.user_id), 'recorded_at': datetime.now(timezone.utc).isoformat()} for k in changes}
        result = persist(conn, actor, row, revision, definitions, changes, sources, body.mutation_id, request_hash)
    return result


@router.get('/visits/{visit_id}/history')
def history(visit_id: UUID, request: Request, actor=Depends(form_actor)):
    with staff_connection(request, actor) as conn:
        visit_access(conn, actor, visit_id)
        return conn.execute('''SELECT h.*,u.username FROM form_history h JOIN app_user u ON u.id=h.actor_id
          WHERE visit_id=%s ORDER BY revision DESC''', (visit_id,)).fetchall()
