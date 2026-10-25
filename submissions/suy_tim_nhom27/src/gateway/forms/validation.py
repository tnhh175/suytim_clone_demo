"""Structural validation only; no inferred clinical ranges or calculations."""
from datetime import date, datetime
import math
import re
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Choice(Input):
    code: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,60}$')
    label: str = Field(min_length=1, max_length=200)


class FieldDefinition(Input):
    code: str = Field(pattern=r'^[a-z][a-z0-9_]{1,79}$')
    label: str = Field(min_length=1, max_length=200)
    group: str = Field(min_length=1, max_length=100)
    type: Literal['integer', 'number', 'boolean', 'select', 'multiselect', 'text', 'textarea', 'date', 'datetime']
    unit: str | None = Field(default=None, max_length=60)
    choices: list[Choice] = Field(default_factory=list, max_length=100)
    help: str = Field(default='', max_length=1000)
    order: int = Field(default=1000, ge=0, le=10000)
    active: bool = True

    @model_validator(mode='after')
    def check_definition(self):
        if not self.label.strip() or not self.group.strip():
            raise ValueError('Nhãn/nhóm không được trống')
        if self.code in {'id', 'patient_id', 'visit_id', 'role', 'owner_id', 'revision', 'external_id'} or self.code.startswith('pending_'):
            raise ValueError('Mã được dành cho hệ thống')
        if self.type in {'select', 'multiselect'}:
            if not self.choices or len({c.code for c in self.choices}) != len(self.choices):
                raise ValueError('Lựa chọn phải có mã duy nhất')
        elif self.choices:
            raise ValueError('Kiểu trường không sử dụng lựa chọn')
        return self


def fail(code, message):
    raise HTTPException(422, detail={'fields': {code: message}})


def with_constraints(field):
    """Source bound (TL06 row 2) and non-negative physical measurements, not normal ranges."""
    bounds = {'tuoi': {'minimum': 0, 'maximum': 120},
              'can_nang': {'minimum': 0}, 'chieu_cao': {'minimum': 0}}
    return {**field, **({'constraints': bounds[field['code']]} if field['code'] in bounds else {})}


def value_for(field: dict, value: Any):
    code, kind = field['code'], field['type']
    if isinstance(value, str):
        value = value.strip() or None
    if value is None:
        return None
    if kind == 'unavailable' or not field['active']:
        fail(code, 'Trường chưa được đặc tả hoặc đã ngừng dùng')
    if kind in {'integer', 'number'}:
        try:
            finite = type(value) in (int, float) and math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            fail(code, 'Cần giá trị số hữu hạn, không dùng chuỗi hoặc Có/Không')
        if kind == 'integer' and type(value) is not int:
            fail(code, 'Cần số nguyên')
        bounds = with_constraints(field).get('constraints', {})
        if 'minimum' in bounds and value < bounds['minimum']:
            fail(code, f"Giá trị không được nhỏ hơn {bounds['minimum']}")
        if 'maximum' in bounds and value > bounds['maximum']:
            fail(code, f"Giá trị không được lớn hơn {bounds['maximum']} theo đặc tả nguồn TL06")
    elif kind == 'boolean':
        if type(value) is not bool:
            fail(code, 'Cần Có/Không hoặc để trống')
    elif kind in {'select', 'multiselect'}:
        valid = {c['code'] for c in field['choices']}
        if kind == 'select':
            if not isinstance(value, str) or value not in valid:
                fail(code, 'Lựa chọn không có trong định nghĩa')
        elif not isinstance(value, list) or any(not isinstance(v, str) or v not in valid for v in value) or len(value) != len(set(value)):
            fail(code, 'Danh sách lựa chọn không hợp lệ')
    elif kind in {'text', 'textarea'}:
        if not isinstance(value, str) or len(value) > 5000:
            fail(code, 'Cần văn bản tối đa 5000 ký tự')
    elif kind in {'date', 'datetime'}:
        try:
            if not isinstance(value, str):
                raise ValueError()
            if kind == 'date':
                if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                    raise ValueError()
                date.fromisoformat(value)
            else:
                if datetime.fromisoformat(value).tzinfo is None:
                    raise ValueError()
        except ValueError:
            fail(code, 'Ngày ISO YYYY-MM-DD; thời điểm phải có múi giờ')
    elif kind in {'medications', 'results'}:
        if not isinstance(value, list) or len(value) > 200:
            fail(code, 'Cần danh sách tối đa 200 mục')
        columns = ({'name': 'text', 'ingredient': 'text', 'dose': 'text', 'route': 'text', 'frequency': 'text', 'observed_at': 'datetime'}
                   if kind == 'medications' else {'name': 'text', 'value': 'number', 'unit': 'text', 'observed_at': 'datetime'})
        cleaned = []
        for item in value:
            if not isinstance(item, dict) or set(item) - set(columns):
                fail(code, 'Mục có cấu trúc không hợp lệ')
            row = {k: value_for(dict(code=code, type=t, active=True), item.get(k)) for k, t in columns.items()}
            if not row['name']:
                fail(code, 'Mỗi mục cần tên để phân biệt kết quả/thuốc; chưa rõ để toàn bộ trường trống')
            cleaned.append(row)
        value = cleaned
    else:
        fail(code, 'Kiểu chưa được hỗ trợ')
    return value
