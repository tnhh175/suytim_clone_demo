from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import AwareDatetime, Field, ValidationError, model_validator
from psycopg.types.json import Jsonb

from ..authorization import Actor, get_current_actor, require_role
from ..database import staff_connection
from ..routers.auth import LoginPayload, TokenResponse, login
from .validation import Input, FieldDefinition, value_for, with_constraints

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
    return revision, {r['code']: with_constraints({**r['definition'], 'version': r['version']}) for r in fields}


def pinned_catalog(row):
    return row['catalog_revision'], {k: with_constraints(d) for k, d in row['definitions_json'].items()}


def patient_access(conn, actor, patient_id):
    p = conn.execute('''SELECT p.* FROM form_patient p WHERE p.id=%s AND
      (%s OR p.owner_id=%s OR EXISTS(SELECT 1 FROM form_access a WHERE a.patient_id=p.id AND a.user_id=%s))''',
      (patient_id, actor.role == 'admin', actor.user_id, actor.user_id)).fetchone()
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


class Demographics(Input):
    external_id: str | None = Field(default=None, min_length=1, max_length=100)
    display_name: str | None = Field(default=None, max_length=200, pattern=r'^Người bệnh giả lập [0-9]+$')
    date_of_birth: date | None = None
    sex: Literal['male', 'female', 'other'] | None = None
    insurance_number: str | None = Field(default=None, max_length=100)

    @model_validator(mode='after')
    def valid_birth(self):
        if self.date_of_birth and self.date_of_birth > date.today():
            raise ValueError('Ngày sinh không được ở tương lai')
        return self


class PatientCreate(Demographics):
    id: UUID


class PatientEdit(Demographics):
    expected_revision: int = Field(ge=0)
    mutation_id: UUID


def demographics(row):
    return {k: str(row[k]) if isinstance(row[k], date) else row[k]
            for k in ('display_name', 'date_of_birth', 'sex', 'insurance_number')}


def visit_date(when):
    return when.astimezone(ZoneInfo('Asia/Ho_Chi_Minh')).date()


def check_visit_birth(birth, when):
    if birth and when and visit_date(when) < date.fromisoformat(str(birth)):
        raise HTTPException(422, 'Thời điểm khám không được trước ngày sinh đã biết')


def identity_available(conn, code, patient_id):
    if code and conn.execute('''SELECT 1 FROM form_patient WHERE (code=%s OR external_id=%s) AND id<>%s
      UNION ALL SELECT 1 FROM form_patient_alias WHERE alias=%s AND patient_id<>%s''',
      (code, code, patient_id, code, patient_id)).fetchone():
        raise HTTPException(409, 'Mã nguồn đã liên kết với hồ sơ khác')


@router.get('/patients')
def patients(request: Request, actor=Depends(form_actor)):
    with staff_connection(request, actor) as conn:
        return conn.execute('''SELECT p.* FROM form_patient p WHERE %s OR p.owner_id=%s OR EXISTS
            (SELECT 1 FROM form_access a WHERE a.patient_id=p.id AND a.user_id=%s) ORDER BY p.created_at DESC''',
            (actor.role == 'admin', actor.user_id, actor.user_id)).fetchall()


@router.post('/patients', status_code=201)
def create_patient(body: PatientCreate, request: Request, actor=Depends(form_actor)):
    require_role(actor, {'doctor'})
    with staff_connection(request, actor) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(hashtextextended('form_patient_create',0))")
        if conn.execute('SELECT 1 FROM form_patient WHERE id=%s', (body.id,)).fetchone():
            row = patient_access(conn, actor, body.id)
            if row['owner_id'] != actor.user_id or any(row[k] != getattr(body, k) for k in ('external_id', 'date_of_birth', 'sex', 'insurance_number')) or (body.display_name and row['display_name'] != body.display_name):
                raise HTTPException(409, 'Mã yêu cầu đã được dùng với hồ sơ khác')
            return row
        identity_available(conn, body.external_id, body.id)
        while True:
            seq = conn.execute('SELECT last_value,is_called FROM form_patient_code_seq').fetchone()
            if seq['is_called'] and seq['last_value'] >= 99999:
                raise HTTPException(409, 'Đã hết phạm vi BN-xxxxx; cần đặc tả mở rộng trước khi cấp tiếp')
            number = conn.execute("SELECT nextval('form_patient_code_seq') AS n").fetchone()['n']
            code = f'BN-{number:05}'
            if not conn.execute('SELECT 1 FROM form_patient_alias WHERE alias=%s UNION ALL SELECT 1 FROM form_patient WHERE code=%s OR external_id=%s', (code, code, code)).fetchone():
                break
        row = conn.execute('''INSERT INTO form_patient(id,code,external_id,display_name,owner_id,date_of_birth,sex,insurance_number)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *''',
          (body.id, code, body.external_id, body.display_name or f'Người bệnh giả lập {number:05}', actor.user_id, body.date_of_birth, body.sex, body.insurance_number)).fetchone()
    return row


@router.patch('/patients/{patient_id}')
def edit_patient(patient_id: UUID, body: PatientEdit, request: Request, actor=Depends(form_actor)):
    request_hash = fingerprint(body.model_dump())
    with staff_connection(request, actor) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(hashtextextended('form_patient_create',0))")
        patient_access(conn, actor, patient_id)
        row = conn.execute('SELECT * FROM form_patient WHERE id=%s FOR UPDATE', (patient_id,)).fetchone()
        previous = conn.execute('SELECT * FROM form_patient_history WHERE patient_id=%s AND mutation_id=%s', (patient_id, body.mutation_id)).fetchone()
        if previous:
            if previous['request_hash'] != request_hash or previous['actor_id'] != actor.user_id:
                raise HTTPException(409, 'Mã lần lưu đã dùng với nội dung khác')
            return {**row, 'replayed': True}
        if row['demographic_revision'] != body.expected_revision:
            raise HTTPException(409, 'Thông tin hành chính đã đổi; tải lại trước khi sửa')
        patch = body.model_dump(exclude={'expected_revision', 'mutation_id'}, exclude_unset=True)
        if 'display_name' in patch and patch['display_name'] is None:
            raise HTTPException(422, 'Tên hiển thị không được trống')
        if 'external_id' in patch:
            identity_available(conn, patch['external_id'], patient_id)
            if row['external_id'] and row['external_id'] != patch['external_id']:
                conn.execute("INSERT INTO form_patient_alias(alias,patient_id,origin) VALUES(%s,%s,'administrative_update') ON CONFLICT DO NOTHING", (row['external_id'], patient_id))
        updated = {**row, **patch}
        result = conn.execute('''UPDATE form_patient SET display_name=%s,date_of_birth=%s,sex=%s,insurance_number=%s,external_id=%s,
          demographic_revision=demographic_revision+1,updated_at=now() WHERE id=%s RETURNING *''',
          tuple(updated[k] for k in ('display_name','date_of_birth','sex','insurance_number','external_id')) + (patient_id,)).fetchone()
        conn.execute('''INSERT INTO form_patient_history(patient_id,revision,mutation_id,request_hash,actor_id,before_json,after_json)
          VALUES(%s,%s,%s,%s,%s,%s,%s)''', (patient_id,result['demographic_revision'],body.mutation_id,request_hash,actor.user_id,
          Jsonb({**demographics(row),'external_id':row['external_id']}),Jsonb({**demographics(result),'external_id':result['external_id']})))
        return result


@router.get('/patients/{patient_id}/history')
def patient_history(patient_id: UUID, request: Request, actor=Depends(form_actor)):
    with staff_connection(request, actor) as conn:
        patient_access(conn, actor, patient_id)
        return conn.execute('''SELECT h.*,u.username FROM form_patient_history h JOIN app_user u ON u.id=h.actor_id
          WHERE h.patient_id=%s ORDER BY h.revision DESC''',(patient_id,)).fetchall()


class VisitMetadata(Input):
    primary_diagnosis_code: str | None = Field(default=None, max_length=30)
    secondary_diagnosis_codes: list[str] | None = Field(default=None, max_length=100)
    reason: str | None = Field(default=None, max_length=5000)
    hpi: str | None = Field(default=None, max_length=5000)
    visit_type: Literal['new', 'followup'] | None = None
    examining_doctor: str | None = Field(default=None, max_length=200)
    department: str | None = Field(default=None, max_length=200)
    admitted_at: AwareDatetime | None = None
    ended_at: AwareDatetime | None = None
    allergy_status: Literal['unknown', 'none', 'known'] | None = None
    allergy_details: str | None = Field(default=None, max_length=5000)

    @model_validator(mode='after')
    def validate_details(self):
        codes = self.secondary_diagnosis_codes or []
        if any(not c.strip() or len(c) > 30 for c in codes) or len(set(codes)) != len(codes):
            raise ValueError('Mã bệnh kèm theo phải là danh sách mã riêng, không trùng')
        if self.admitted_at and self.ended_at and self.ended_at < self.admitted_at:
            raise ValueError('Thời điểm kết thúc không trước tiếp nhận')
        if self.allergy_status in ('none', 'unknown') and self.allergy_details:
            raise ValueError('Chi tiết dị ứng cần tình trạng đã ghi nhận dị ứng')
        return self


class VisitCreate(Input):
    id: UUID
    external_id: str | None = Field(default=None, min_length=1, max_length=100)
    occurred_at: AwareDatetime | None = None
    metadata: VisitMetadata = Field(default_factory=VisitMetadata)


@router.get('/patients/{patient_id}/visits')
def visits(patient_id: UUID, request: Request, actor=Depends(form_actor)):
    with staff_connection(request, actor) as conn:
        patient_access(conn, actor, patient_id)
        return conn.execute('SELECT id,patient_id,external_id,occurred_at,revision,updated_at,catalog_revision,metadata_json,created_at FROM form_visit WHERE patient_id=%s ORDER BY occurred_at DESC NULLS LAST,created_at DESC,id', (patient_id,)).fetchall()


@router.post('/patients/{patient_id}/visits', status_code=201)
def create_visit(patient_id: UUID, body: VisitCreate, request: Request, actor=Depends(form_actor)):
    require_role(actor, {'doctor'})
    with staff_connection(request, actor) as conn:
        patient = patient_access(conn, actor, patient_id)
        check_visit_birth(patient['date_of_birth'], body.occurred_at)
        revision, definitions = catalog(conn)
        meta = body.metadata.model_dump(mode='json')
        if body.external_id and conn.execute('SELECT 1 FROM form_visit WHERE patient_id=%s AND external_id=%s AND id<>%s', (patient_id,body.external_id,body.id)).fetchone():
            raise HTTPException(409, 'Mã lượt nguồn đã có trong hồ sơ')
        row = conn.execute('''INSERT INTO form_visit(id,patient_id,external_id,occurred_at,created_by,catalog_revision,definitions_json,demographics_snapshot,snapshot_origin,metadata_json)
          VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'creation',%s) ON CONFLICT(id) DO NOTHING RETURNING *''',
          (body.id,patient_id,body.external_id,body.occurred_at,actor.user_id,revision,Jsonb(definitions),Jsonb(demographics(patient)),Jsonb(meta))).fetchone()
        if row is None:
            row = visit_access(conn, actor, body.id)
            if row['patient_id'] != patient_id or row['created_by'] != actor.user_id or row['external_id'] != body.external_id or row['occurred_at'] != body.occurred_at or row['metadata_json'] != meta:
                raise HTTPException(409, 'Mã yêu cầu đã được dùng với lượt khác')
    return row


def present_visit(row, definitions, revision):
    birth = row['demographics_snapshot'].get('date_of_birth')
    age = None
    if birth and row['occurred_at']:
        born, when = date.fromisoformat(birth), visit_date(row['occurred_at'])
        age = when.year-born.year-((when.month,when.day)<(born.month,born.day)) if when >= born else None
    return {**row, 'values_json': {**{k: None for k in definitions}, **row['values_json']}, 'catalog_revision': revision,
            'metadata':row['metadata_json'], 'age_at_visit':age, 'fields':sorted(definitions.values(), key=lambda d:(d['order'],d['code']))}


@router.get('/visits/{visit_id}')
def get_visit(visit_id: UUID, request: Request, actor=Depends(form_actor)):
    with staff_connection(request, actor) as conn:
        row = visit_access(conn, actor, visit_id)
        revision, definitions = pinned_catalog(row)
        return present_visit(row, definitions, revision)


@router.get('/patients/{patient_id}/overview')
def overview(patient_id: UUID, request: Request, actor=Depends(form_actor)):
    with staff_connection(request, actor) as conn:
        patient = patient_access(conn, actor, patient_id)
        rows = conn.execute('SELECT * FROM form_visit WHERE patient_id=%s ORDER BY occurred_at DESC NULLS LAST,created_at DESC,id', (patient_id,)).fetchall()
        presented = [present_visit(row, pinned_catalog(row)[1], row['catalog_revision']) for row in rows]
        dated = [v for v in presented if v['occurred_at'] is not None]
        disease = next((v for v in dated if v['metadata'].get('primary_diagnosis_code') or v['metadata'].get('secondary_diagnosis_codes') or v['metadata'].get('reason') or v['metadata'].get('hpi')),None)
        medications = next((v for v in dated if any(f['type']=='medications' and v['values_json'].get(f['code']) is not None for f in v['fields'])),None)
        allergy = next((v for v in dated if v['metadata'].get('allergy_status') is not None or v['metadata'].get('allergy_details')),None)
        return {'patient':patient, 'latest_visit':dated[0] if dated else None, 'visits':presented,
                'summary_visits':{'disease':disease,'medications':medications,'allergy':allergy}}


class Save(Input):
    expected_revision: int = Field(ge=0)
    catalog_revision: int = Field(ge=1)
    mutation_id: UUID
    values: dict = Field(default_factory=dict, max_length=500)
    metadata: VisitMetadata | None = None
    occurred_at: AwareDatetime | None = None


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str).encode()).hexdigest()


def persist(conn, actor, row, revision, definitions, changes, sources, mutation_id, request_hash, metadata=None, occurred_at=None, change_time=False):
    values = {**row['values_json'], **changes}
    origins = {**row['sources_json'], **sources}
    new_revision = row['revision'] + 1
    meta = row.get('metadata_json', {}) if metadata is None else metadata
    when = occurred_at if change_time else row['occurred_at']
    conn.execute('UPDATE form_visit SET values_json=%s,sources_json=%s,revision=%s,metadata_json=%s,occurred_at=%s,updated_at=now() WHERE id=%s',
                 (Jsonb(values), Jsonb(origins), new_revision, Jsonb(meta), when, row['id']))
    conn.execute('''INSERT INTO form_history(visit_id,revision,mutation_id,request_hash,actor_id,values_json,sources_json,definitions_json,catalog_revision,metadata_json,occurred_at)
      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
      (row['id'], new_revision, mutation_id, request_hash, actor.user_id, Jsonb(values), Jsonb(origins), Jsonb(definitions), revision,Jsonb(meta),when))
    return {'revision': new_revision, 'mutation_id': mutation_id, 'saved': True}


@router.patch('/visits/{visit_id}')
def save(visit_id: UUID, body: Save, request: Request, actor=Depends(form_actor)):
    require_role(actor, {'doctor'})
    request_hash = fingerprint(body.model_dump())
    with staff_connection(request, actor) as conn:
        row = visit_access(conn, actor, visit_id, lock=True)
        revision, definitions = pinned_catalog(row)
        if 'occurred_at' in body.model_fields_set:
            check_visit_birth(row['demographics_snapshot'].get('date_of_birth'), body.occurred_at)
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
        meta = None
        if body.metadata is not None:
            try:
                meta = VisitMetadata.model_validate({**row['metadata_json'], **body.metadata.model_dump(mode='json',exclude_unset=True)}).model_dump(mode='json')
            except ValidationError as exc:
                raise HTTPException(422, 'Thông tin lượt không hợp lệ: ' + str(exc)) from None
        result = persist(conn, actor, row, revision, definitions, changes, sources, body.mutation_id, request_hash,
                         meta,body.occurred_at,'occurred_at' in body.model_fields_set)
    return result


@router.get('/visits/{visit_id}/history')
def history(visit_id: UUID, request: Request, actor=Depends(form_actor)):
    with staff_connection(request, actor) as conn:
        visit_access(conn, actor, visit_id)
        return conn.execute('''SELECT h.*,u.username FROM form_history h JOIN app_user u ON u.id=h.actor_id
          WHERE visit_id=%s ORDER BY revision DESC''', (visit_id,)).fetchall()
