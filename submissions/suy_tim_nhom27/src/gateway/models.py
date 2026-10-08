import math
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator

class Model(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Login(Model):
    username: Literal['doctor', 'pharmacist', 'admin']
    password: str = Field(min_length=1, max_length=200)

class Token(Model):
    access_token: str
    token_type: Literal['bearer'] = 'bearer'
    expires_in: int = 3600

class CaseInput(Model):
    synthetic_code: str = Field(pattern=r'^SYN-[A-Z0-9-]{1,24}$')
    age: int = Field(ge=0, le=120)
    sex: Literal['male', 'female', 'unknown']

class CaseCreateInput(Model):
    age: int = Field(ge=0, le=120)
    sex: Literal['male', 'female', 'unknown']
    synthetic_code: str | None = Field(default=None, pattern=r'^SYN-[A-Z0-9-]{1,24}$')

class CaseOut(CaseInput):
    id: UUID
    owner_id: UUID
    revision: int

class EncounterInput(Model):
    occurred_at: AwareDatetime

class EncounterOut(EncounterInput):
    id: UUID
    case_id: UUID

class ObservationInput(Model):
    code: Literal['ef','potassium','egfr','creatinine','bnp','nt_probnp','systolic_bp','heart_rate','dyspnea','frailty','comorbidity']
    value: float | str | bool | None = None
    unit: str | None = None
    status: Literal['present','not_measured','unknown']
    observed_at: AwareDatetime
    source: Literal['manual_synthetic','mock_his','mock_lis','mock_pacs']

    @model_validator(mode='after')
    def validate_value(self):
        units={'ef':'%','potassium':'mmol/L','egfr':'mL/min/1.73m2','creatinine':'umol/L','bnp':'pg/mL','nt_probnp':'pg/mL','systolic_bp':'mmHg','heart_rate':'bpm'}
        if self.status!='present':
            if self.value is not None or self.unit is not None:
                raise ValueError('Missing value must be null; do not replace with zero')
            return self
        if self.value is None:
            raise ValueError('Present observation requires a value')
        if self.code in units:
            if isinstance(self.value,bool) or not isinstance(self.value,(int,float)):
                raise ValueError('Numeric observation requires a number')
            if self.unit!=units[self.code]:
                raise ValueError('Unsupported unit for this code')
            if not math.isfinite(self.value) or self.value<0 or (self.code=='ef' and self.value>100):
                raise ValueError('Invalid numeric domain')
        elif self.code=='dyspnea':
            if not isinstance(self.value,bool) or self.unit is not None:
                raise ValueError('dyspnea requires boolean and no unit')
        elif not isinstance(self.value,str) or self.unit is not None:
            raise ValueError('Categorical observation requires text and no unit')
        return self

class ObservationOut(ObservationInput):
    id: UUID
    encounter_id: UUID

class MedicationInput(Model):
    ingredient_code: str = Field(pattern=r'^[a-z][a-z0-9_]{1,59}$')
    dose: float = Field(gt=0, allow_inf_nan=False)
    dose_unit: Literal['mg','mcg','g','mL']
    route: Literal['oral','iv','other']
    frequency_per_day: int = Field(ge=1,le=24)
    kind: Literal['current','proposed']

class MedicationOut(MedicationInput):
    id: UUID
    encounter_id: UUID

ModuleName=Literal['diagnosis','lab_test','treatment','medsafety']
class EvaluationInput(Model):
    encounter_id: UUID
    expected_revision: int = Field(ge=1)
    modules: list[ModuleName] = Field(min_length=1,max_length=4)

    @model_validator(mode='after')
    def no_duplicates(self):
        if len(set(self.modules))!=len(self.modules): raise ValueError('Duplicate module')
        return self

class Recommendation(Model):
    code: str
    description: str
    severity: Literal['info','warning','critical']
    source_ref: str
    rule_version: str
    triggered_fields: list[str]

class TestSuggestion(Model):
    test_code: str
    priority: Literal['emergency','within_24h','current_visit','routine']
    reason: str
    duplicate_detected: bool

class ModuleResult(Model):
    module: ModuleName
    status: Literal['mock_not_evaluated'] = 'mock_not_evaluated'
    message: str
    missing_fields: list[str]
    clinical_recommendations: list[Recommendation] = Field(default_factory=list)
    phenotype: Literal['HFrEF','HFmrEF','HFpEF','HFimpEF'] | None = None
    stage: Literal['A','B','C','D'] | None = None
    course: str | None = None
    suggested_tests: list[TestSuggestion] = Field(default_factory=list)
    treatment_strategies: list[str] = Field(default_factory=list)

class EvaluationOut(Model):
    id: UUID
    case_id: UUID
    encounter_id: UUID
    input_revision: int
    rule_version: str
    mode: Literal['stub'] = 'stub'
    results: list[ModuleResult]
    created_at: AwareDatetime

class DecisionInput(Model):
    action: Literal['accepted','adjusted','rejected']
    reason: str | None = Field(default=None,max_length=500)

    @model_validator(mode='after')
    def reason_required(self):
        if self.action in ('adjusted','rejected') and not (self.reason and self.reason.strip()):
            raise ValueError('Reason required for adjusted/rejected')
        return self

class DecisionOut(DecisionInput):
    id: UUID
    evaluation_id: UUID
    doctor_id: UUID
    created_at: AwareDatetime
    mode: Literal['stub'] = 'stub'

class RuleInput(Model):
    code: str = Field(pattern=r'^[A-Z][A-Z0-9_-]{2,50}$')
    module: ModuleName
    source_ref: str = Field(min_length=1,max_length=300)

class RuleOut(RuleInput):
    id: UUID
    version: int
    status: Literal['draft','tested','approved','active']
    test_status: Literal['not_run','schema_passed']
    approval_ref: str | None = None

class RuleTestOut(Model):
    rule_id: UUID
    result: Literal['schema_passed']
    clinical_validation: Literal['not_performed']

class AuditOut(Model):
    id: UUID
    actor_id: UUID
    action: str
    entity_id: UUID
    created_at: AwareDatetime

class ExportOut(Model):
    case: CaseOut
    evaluations: list[EvaluationOut]
    decisions: list[DecisionOut]
    mode: Literal['stub'] = 'stub'

class Health(Model):
    status: Literal['ok'] = 'ok'
    mode: Literal['stub'] = 'stub'
    persistence: Literal['memory'] = 'memory'

class Error(Model):
    detail: str

class HistoryEntry(EvaluationOut):
    decision: DecisionOut | None = None
