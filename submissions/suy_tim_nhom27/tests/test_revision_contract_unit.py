"""Pure boundary checks; no shared QA writes or guessed medical normal ranges."""
from datetime import datetime

import pytest
from fastapi import HTTPException

from src.gateway.forms.router import VisitMetadata, check_visit_birth, present_visit
from src.gateway.forms.validation import value_for


def test_age_at_vietnam_calendar_boundary_and_birth_validation():
    when = datetime.fromisoformat('2026-05-01T00:30:00+07:00')
    row = {'demographics_snapshot': {'date_of_birth': '2000-05-01'},
           'occurred_at': when.astimezone(__import__('datetime').timezone.utc),
           'values_json': {}, 'metadata_json': {}}
    assert present_visit(row, {}, 1)['age_at_visit'] == 26
    check_visit_birth('2026-05-01', row['occurred_at'])
    with pytest.raises(HTTPException) as exc:
        check_visit_birth('2026-05-02', row['occurred_at'])
    assert exc.value.status_code == 422


def test_unknown_and_explicit_empty_secondary_codes_are_distinct():
    assert VisitMetadata().secondary_diagnosis_codes is None
    assert VisitMetadata(secondary_diagnosis_codes=[]).secondary_diagnosis_codes == []


@pytest.mark.parametrize('code,value', [('tuoi',150),('can_nang',-1),('chieu_cao',-1)])
def test_source_and_physical_bounds(code,value):
    with pytest.raises(HTTPException):
        value_for({'code':code,'type':'integer' if code=='tuoi' else 'number','active':True},value)


def test_bounds_do_not_invent_normal_ranges_or_conflate_zero_null_false():
    weight={'code':'can_nang','type':'number','active':True}
    assert value_for(weight,0)==0
    assert value_for(weight,1000)==1000
    assert value_for(weight,None) is None
    with pytest.raises(HTTPException):
        value_for(weight,False)
