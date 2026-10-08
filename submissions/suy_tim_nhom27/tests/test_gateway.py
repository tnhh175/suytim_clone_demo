import copy
from uuid import UUID
import pytest
from fastapi.testclient import TestClient
from src.gateway.main import create_app

@pytest.fixture
def ctx(monkeypatch):
    monkeypatch.setenv('DEMO_PASSWORD','test-only-not-a-deployment-secret')
    app=create_app();c=TestClient(app);headers={}
    for role in ['doctor','pharmacist','admin']:
        r=c.post('/api/v1/auth/token',json={'username':role,'password':'test-only-not-a-deployment-secret'})
        assert r.status_code==200;headers[role]={'Authorization':'Bearer '+r.json()['access_token']}
    return c,headers,app

def setup_case(ctx):
    c,h,app=ctx
    r=c.post('/api/v1/cases',headers=h['doctor'],json={'synthetic_code':'SYN-001','age':75,'sex':'female'});assert r.status_code==201
    cid=r.json()['id']
    e=c.post(f'/api/v1/cases/{cid}/encounters',headers=h['doctor'],json={'occurred_at':'2026-09-27T09:00:00+07:00'});assert e.status_code==201
    return cid,e.json()['id']

def evaluate(ctx,cid,eid,role='doctor',modules=None):
    c,h,app=ctx;revision=app.state.store.cases[cid]['revision']
    return c.post('/api/v1/evaluations',headers=h[role],json={'encounter_id':eid,'expected_revision':revision,'modules':modules or ['diagnosis','lab_test','treatment','medsafety']})

def test_full_workflow(ctx):
    c,h,app=ctx;cid,eid=setup_case(ctx)
    assert UUID(c.get(f'/api/v1/cases/{cid}',headers=h['doctor']).json()['owner_id'])
    r=evaluate(ctx,cid,eid);assert r.status_code==201
    data=r.json();assert len(data['results'])==4
    assert all(x['status']=='mock_not_evaluated' and x['clinical_recommendations']==[] for x in data['results'])
    assert 'ef' in data['results'][0]['missing_fields']
    rid=data['id']
    d=c.post(f'/api/v1/evaluations/{rid}/decisions',headers=h['doctor'],json={'action':'rejected','reason':'Demo review'})
    assert d.status_code==201 and d.json()['mode']=='stub'
    assert UUID(d.json()['doctor_id'])
    assert c.get(f'/api/v1/cases/{cid}/history',headers=h['doctor']).json()[0]['id']==rid
    assert len(c.get(f'/api/v1/cases/{cid}/export',headers=h['doctor']).json()['decisions'])==1
    audit=c.get('/api/v1/audit-events',headers=h['admin']).json()
    assert any(x['action']=='decision.created' for x in audit)
    assert all(UUID(x['actor_id']) and UUID(x['entity_id']) for x in audit)

def test_case_code_generated_and_preserved(ctx):
    c,h,_=ctx
    created=c.post('/api/v1/cases',headers=h['doctor'],json={'age':76,'sex':'female'})
    assert created.status_code==201
    item=created.json();code=item['synthetic_code'];assert code.startswith('SYN-')
    updated=c.put(f"/api/v1/cases/{item['id']}?expected_revision=1",headers=h['doctor'],json={'age':77,'sex':'female','synthetic_code':code})
    assert updated.status_code==200 and updated.json()['synthetic_code']==code
    assert c.post('/api/v1/cases',headers=h['doctor'],json={'age':75,'sex':'male','synthetic_code':code}).status_code==409

def test_auth_and_roles(ctx):
    c,h,app=ctx
    assert c.get('/api/v1/cases').status_code==401
    for role in ['pharmacist','admin']:
        assert c.post('/api/v1/cases',headers=h[role],json={'synthetic_code':'SYN-002','age':80,'sex':'unknown'}).status_code==403
    cid,eid=setup_case(ctx)
    assert evaluate(ctx,cid,eid,'pharmacist').status_code==403
    assert evaluate(ctx,cid,eid,'pharmacist',['medsafety']).status_code==201
    assert c.get('/api/v1/audit-events',headers=h['doctor']).status_code==403

def test_validation_and_stale_decision(ctx):
    c,h,app=ctx;cid,eid=setup_case(ctx);rid=evaluate(ctx,cid,eid).json()['id']
    body={'code':'ef','value':140,'unit':'%','status':'present','observed_at':'2026-09-27T09:00:00Z','source':'manual_synthetic'}
    assert c.post(f'/api/v1/encounters/{eid}/observations',headers=h['doctor'],json=body).status_code==422
    body['value']=35
    assert c.post(f'/api/v1/encounters/{eid}/observations',headers=h['doctor'],json=body).status_code==201
    # Saved input was deep-copied, not silently modified by later data entry.
    assert app.state.store.snapshots[rid]['observations']==[]
    assert c.post(f'/api/v1/evaluations/{rid}/decisions',headers=h['doctor'],json={'action':'accepted'}).status_code==409
    new=evaluate(ctx,cid,eid).json();assert new['results'][0]['missing_fields']==[]
    assert new['results'][0]['clinical_recommendations']==[] # EF alone never emits phenotype.

def test_no_duplicate_or_reasonless_decision(ctx):
    c,h,app=ctx;cid,eid=setup_case(ctx);rid=evaluate(ctx,cid,eid).json()['id'];url=f'/api/v1/evaluations/{rid}/decisions'
    assert c.post(url,headers=h['doctor'],json={'action':'rejected'}).status_code==422
    assert c.post(url,headers=h['doctor'],json={'action':'accepted'}).status_code==201
    assert c.post(url,headers=h['doctor'],json={'action':'accepted'}).status_code==409
    assert c.post(url,headers=h['pharmacist'],json={'action':'accepted'}).status_code==403

def test_rule_guard(ctx):
    c,h,app=ctx
    r=c.post('/api/v1/rule-versions',headers=h['admin'],json={'code':'DEMO_RULE','module':'diagnosis','source_ref':'Synthetic fixture, not a clinical rule'})
    assert r.status_code==201;rid=r.json()['id']
    assert c.post(f'/api/v1/rule-versions/{rid}/test',headers=h['admin']).json()['clinical_validation']=='not_performed'
    assert c.post(f'/api/v1/rule-versions/{rid}/activate',headers=h['admin']).status_code==409

def test_extra_fields_unknown_and_expiry(ctx):
    c,h,app=ctx;cid,eid=setup_case(ctx)
    assert c.post('/api/v1/cases',headers=h['doctor'],json={'synthetic_code':'SYN-003','age':80,'sex':'male','patient_name':'FORBIDDEN'}).status_code==422
    body={'code':'potassium','value':0,'unit':'mmol/L','status':'unknown','observed_at':'2026-09-27T10:00:00Z','source':'mock_lis'}
    assert c.post(f'/api/v1/encounters/{eid}/observations',headers=h['doctor'],json=body).status_code==422
    body.update(value=None,unit=None)
    assert c.post(f'/api/v1/encounters/{eid}/observations',headers=h['doctor'],json=body).status_code==201
    token=h['doctor']['Authorization'].split()[1];app.state.store.tokens[token]['expires']=0
    assert c.get('/api/v1/cases',headers=h['doctor']).status_code==401

def test_contract_and_sql():
    from pathlib import Path
    import yaml
    from openapi_spec_validator import validate
    from pglast import parse_sql
    root=Path(__file__).resolve().parents[1]
    spec=yaml.safe_load((root/'api/openapi.yaml').read_text())
    assert spec==create_app().openapi()
    assert spec['openapi']=='3.0.3';validate(spec)
    parse_sql((root/'database/schema.sql').read_text());parse_sql((root/'database/seed.sql').read_text())
