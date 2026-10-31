"""P1 data contracts; pure tests without database writes or clinical algorithms."""
import json
from pathlib import Path

import pytest
from fastapi import HTTPException

from src.gateway.forms.validation import value_for

CATALOG = json.loads((Path(__file__).parents[1] / 'src/gateway/forms/catalog.json').read_text(encoding='utf-8'))
FIELDS = {f['code']: f for f in CATALOG}


def test_source_parents_remain_traceable_and_children_have_no_imputed_values():
    assert len([f for f in CATALOG if 'stt' in f.get('source', {})]) == 206
    for code in ['ha_t_the_nam_ngoi', 'ha_t_the_dung', 'sieu_am_tim_ef', 'benh_mach_vanh_nhoi_mau_co_tim']:
        assert FIELDS[code]['type'] == 'unavailable'
        assert FIELDS[code]['supported_by']
        for child in FIELDS[code]['supported_by']:
            assert value_for(FIELDS[child], None) is None
    assert value_for(FIELDS['benh_mach_vanh_da_biet'], False) is False
    assert FIELDS['bmi']['type'] == 'unavailable'


@pytest.mark.parametrize('code,value', [('lvef', 101), ('lvef', -1), ('spo2', 101), ('ha_dung_tam_thu', -1)])
def test_physical_limits_only(code, value):
    with pytest.raises(HTTPException):
        value_for(FIELDS[code], value)


def test_not_normal_range_and_zero_not_missing():
    assert value_for(FIELDS['ha_dung_tam_thu'], 350) == 350
    assert value_for(FIELDS['lvef'], 0) == 0
    assert value_for(FIELDS['bnp_ntprobnp'], []) == []
    assert value_for(FIELDS['bnp_ntprobnp'], None) is None


def test_result_identity_units_source_time():
    row = {'test_code': 'BNP', 'name': 'Tên gốc trên phiếu', 'value': 0, 'unit': 'pg/mL',
           'observed_at': None, 'source': 'Phiếu xét nghiệm'}
    result = value_for(FIELDS['bnp_ntprobnp'], [row])[0]
    assert result == row
    for patch in [{'test_code': 'BNP_NT_PROBNP'}, {'unit': 'mmol/L'}, {'unit': None}, {'value': False}]:
        with pytest.raises(HTTPException):
            value_for(FIELDS['bnp_ntprobnp'], [{**row, **patch}])


def test_unconfirmed_units_preserve_report_not_invented_allowlist():
    row = {'test_code': 'NA', 'name': 'Natri', 'unit': 'đơn vị trên phiếu', 'value': 123}
    assert value_for(FIELDS['dien_giai'], [row])[0]['unit'] == row['unit']


def test_pinned_legacy_result_shape_unchanged():
    field = {**FIELDS['bnp_ntprobnp']}
    field.pop('contract_version')
    value = [{'name': 'BNP cũ', 'value': 0, 'unit': 'gốc', 'observed_at': None}]
    assert value_for(field, value) == value
    with pytest.raises(HTTPException):
        value_for(field, [{**value[0], 'test_code': 'BNP'}])


def test_medication_partial_record_no_status_default():
    field = FIELDS['danh_sach_thuoc']
    row = value_for(field, [{'name': 'Thuốc ghi nhận', 'dose': 'mô tả gốc'}])[0]
    assert row['status'] is None and row['observed_at'] is None
    assert row['dose_value'] is None and row['dose'] == 'mô tả gốc'
    for patch in [{'dose_value': -1}, {'dose_value': 2}, {'status': 'active'},
                  {'start_date': '2026-10-30', 'end_date': '2026-10-29'}]:
        with pytest.raises(HTTPException):
            value_for(field, [{**row, **patch}])
