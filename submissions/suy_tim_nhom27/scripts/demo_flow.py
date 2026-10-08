"""Run against the live local server. Uses only synthetic input."""
import os,secrets
import httpx

password=os.environ.get('DEMO_PASSWORD')
if not password:raise SystemExit('Set DEMO_PASSWORD to match the server first')
with httpx.Client(base_url=os.environ.get('DEMO_BASE_URL','http://127.0.0.1:8000'),timeout=15,trust_env=False) as c:
    r=c.post('/api/v1/auth/token',json={'username':'doctor','password':password});r.raise_for_status()
    c.headers['Authorization']='Bearer '+r.json()['access_token']
    r=c.post('/api/v1/cases',json={'synthetic_code':'SYN-'+secrets.token_hex(4).upper(),'age':75,'sex':'female'});r.raise_for_status();cid=r.json()['id']
    r=c.post(f'/api/v1/cases/{cid}/encounters',json={'occurred_at':'2026-09-27T09:00:00+07:00'});r.raise_for_status();eid=r.json()['id']
    revision=c.get(f'/api/v1/cases/{cid}').json()['revision']
    r=c.post('/api/v1/evaluations',json={'encounter_id':eid,'expected_revision':revision,'modules':['diagnosis','lab_test','treatment','medsafety']});r.raise_for_status();evaluation=r.json()
    r=c.post(f"/api/v1/evaluations/{evaluation['id']}/decisions",json={'action':'rejected','reason':'Demo workflow only'});r.raise_for_status()
    print('OK: case → encounter → four stub results → doctor decision')
    print('mode:',evaluation['mode'],'modules:',len(evaluation['results']))
