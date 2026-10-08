import hmac, os, secrets, time
from copy import deepcopy
from pathlib import Path
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .models import *
from .store import MemoryStore,uid,now,demo_user_id
from .services import build_ports

security=HTTPBearer(auto_error=False)
ERRORS={n:{'model':Error,'description':d} for n,d in {401:'Token thiếu/hết hạn',403:'Không đúng vai trò hoặc quyền ca',404:'Không tìm thấy',409:'Xung đột phiên bản/trạng thái',422:'Dữ liệu không hợp lệ',503:'Chưa cấu hình demo'}.items()}

def create_app():
    app=FastAPI(title='Nhóm 27 — API Gateway stub',version='0.1.0',responses=ERRORS,
        description='Tuần 3. Chỉ dữ liệu synthetic, lưu trong RAM. Không trả chẩn đoán hay đơn thuốc thực.')
    app.state.store=MemoryStore(); app.state.ports=build_ports()
    app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173'],allow_methods=['GET','POST','PUT'],allow_headers=['Authorization','Content-Type'])

    @app.exception_handler(RequestValidationError)
    async def validation_error(request,exc):
        # Do not echo submitted input values into error responses/logs.
        return JSONResponse(status_code=422,content={'detail':'Dữ liệu không hợp lệ: '+', '.join('.'.join(map(str,e['loc'])) for e in exc.errors())})

    def actor(request:Request,credentials:HTTPAuthorizationCredentials|None=Depends(security)):
        s=request.app.state.store
        session=s.tokens.get(credentials.credentials) if credentials else None
        if not session or session['expires']<time.time(): raise HTTPException(401,'Token thiếu hoặc hết hạn')
        return session['actor']
    def role(a,allowed):
        if a not in allowed: raise HTTPException(403,'Không đúng vai trò')
    def case_access(s,cid,a):
        if cid not in s.cases: raise HTTPException(404,'Không tìm thấy ca')
        # Demo pharmacist has access to all synthetic cases for MedSafety only.
        role(a,['doctor','pharmacist'])
        if a=='doctor' and s.cases[cid]['owner_id']!=demo_user_id(a): raise HTTPException(403,'Không có quyền ca')
        return s.cases[cid]
    def encounter_access(s,eid,a):
        e=s.encounters.get(eid)
        if not e: raise HTTPException(404,'Không tìm thấy lượt khám')
        return case_access(s,e['case_id'],a)

    @app.get('/health',response_model=Health,tags=['System'])
    def health(): return Health()

    @app.post('/api/v1/auth/token',response_model=Token,tags=['Identity'])
    def login(body:Login,request:Request):
        password=os.getenv('DEMO_PASSWORD')
        if not password: raise HTTPException(503,'Cần thiết lập DEMO_PASSWORD')
        if not hmac.compare_digest(body.password.encode(),password.encode()): raise HTTPException(401,'Thông tin đăng nhập không hợp lệ')
        s=request.app.state.store; token=secrets.token_urlsafe(32)
        with s.lock:
            s.tokens[token]={'actor':body.username,'expires':time.time()+3600}
            s.record(body.username,'login',demo_user_id(body.username))
        return Token(access_token=token)

    @app.post('/api/v1/cases',response_model=CaseOut,status_code=201,tags=['Cases'])
    def create_case(body:CaseCreateInput,request:Request,a=Depends(actor)):
        role(a,['doctor']);s=request.app.state.store
        with s.lock:
            code=body.synthetic_code or 'SYN-'+uid().replace('-','')[:16].upper()
            if any(c['synthetic_code']==code for c in s.cases.values()): raise HTTPException(409,'Mã ca trùng')
            c=dict(synthetic_code=code,age=body.age,sex=body.sex,id=uid(),owner_id=demo_user_id(a),revision=1);s.cases[c['id']]=c;s.record(a,'case.created',c['id']);return deepcopy(c)

    @app.get('/api/v1/cases',response_model=list[CaseOut],tags=['Cases'])
    def list_cases(request:Request,a=Depends(actor)):
        role(a,['doctor']);return [c for c in request.app.state.store.cases.values() if c['owner_id']==demo_user_id(a)]

    @app.get('/api/v1/cases/{case_id}',response_model=CaseOut,tags=['Cases'])
    def get_case(case_id:UUID,request:Request,a=Depends(actor)):
        role(a,['doctor']);return case_access(request.app.state.store,str(case_id),a)

    @app.put('/api/v1/cases/{case_id}',response_model=CaseOut,tags=['Cases'])
    def update_case(case_id:UUID,body:CaseInput,expected_revision:int,request:Request,a=Depends(actor)):
        role(a,['doctor']);s=request.app.state.store;cid=str(case_id)
        with s.lock:
            c=case_access(s,cid,a)
            if c['revision']!=expected_revision: raise HTTPException(409,'Ca đã thay đổi')
            if any(x['id']!=cid and x['synthetic_code']==body.synthetic_code for x in s.cases.values()): raise HTTPException(409,'Mã ca trùng')
            c.update(body.model_dump());c['revision']+=1;s.record(a,'case.updated',cid);return deepcopy(c)

    @app.post('/api/v1/cases/{case_id}/encounters',response_model=EncounterOut,status_code=201,tags=['Cases'])
    def create_encounter(case_id:UUID,body:EncounterInput,request:Request,a=Depends(actor)):
        role(a,['doctor']);s=request.app.state.store;cid=str(case_id)
        with s.lock:
            c=case_access(s,cid,a);e=dict(id=uid(),case_id=cid,**body.model_dump());s.encounters[e['id']]=e;c['revision']+=1;s.record(a,'encounter.created',e['id']);return e

    @app.get('/api/v1/encounters/{encounter_id}',response_model=EncounterOut,tags=['Cases'])
    def get_encounter(encounter_id:UUID,request:Request,a=Depends(actor)):
        role(a,['doctor']);s=request.app.state.store;eid=str(encounter_id);encounter_access(s,eid,a);return s.encounters[eid]

    @app.post('/api/v1/encounters/{encounter_id}/observations',response_model=ObservationOut,status_code=201,tags=['Clinical data'])
    def observation(encounter_id:UUID,body:ObservationInput,request:Request,a=Depends(actor)):
        role(a,['doctor']);s=request.app.state.store;eid=str(encounter_id)
        with s.lock:
            c=encounter_access(s,eid,a);o=dict(id=uid(),encounter_id=eid,**body.model_dump());s.observations[o['id']]=o;c['revision']+=1;s.record(a,'observation.created',o['id']);return o

    @app.get('/api/v1/encounters/{encounter_id}/observations',response_model=list[ObservationOut],tags=['Clinical data'])
    def observations(encounter_id:UUID,request:Request,a=Depends(actor)):
        role(a,['doctor']);s=request.app.state.store;eid=str(encounter_id);encounter_access(s,eid,a);return [x for x in s.observations.values() if x['encounter_id']==eid]

    @app.post('/api/v1/encounters/{encounter_id}/medications',response_model=MedicationOut,status_code=201,tags=['Clinical data'])
    def medication(encounter_id:UUID,body:MedicationInput,request:Request,a=Depends(actor)):
        role(a,['doctor']);s=request.app.state.store;eid=str(encounter_id)
        with s.lock:
            c=encounter_access(s,eid,a);m=dict(id=uid(),encounter_id=eid,**body.model_dump());s.medications[m['id']]=m;c['revision']+=1;s.record(a,'medication.created',m['id']);return m

    @app.get('/api/v1/encounters/{encounter_id}/medications',response_model=list[MedicationOut],tags=['Clinical data'])
    def medications(encounter_id:UUID,request:Request,a=Depends(actor)):
        s=request.app.state.store;eid=str(encounter_id);encounter_access(s,eid,a);return [x for x in s.medications.values() if x['encounter_id']==eid]

    @app.post('/api/v1/evaluations',response_model=EvaluationOut,status_code=201,tags=['Evaluation'])
    def evaluate(body:EvaluationInput,request:Request,a=Depends(actor)):
        role(a,['doctor','pharmacist'])
        if a=='pharmacist' and body.modules!=['medsafety']: raise HTTPException(403,'Dược sĩ chỉ gọi MedSafety')
        s=request.app.state.store;eid=str(body.encounter_id)
        with s.lock:
            c=encounter_access(s,eid,a)
            if c['revision']!=body.expected_revision: raise HTTPException(409,'Cần tải lại phiên bản ca')
            snap=s.snapshot(c['id'],eid);rid=uid()
            result=EvaluationOut(id=rid,case_id=c['id'],encounter_id=eid,input_revision=c['revision'],rule_version='STUB-0.1',results=[request.app.state.ports[m].evaluate(snap) for m in body.modules],created_at=now()).model_dump(mode='json')
            s.snapshots[rid]=snap;s.evaluations[rid]=result;s.record(a,'evaluation.created',rid);return deepcopy(result)

    @app.get('/api/v1/evaluations/{evaluation_id}',response_model=EvaluationOut,tags=['Evaluation'])
    def get_evaluation(evaluation_id:UUID,request:Request,a=Depends(actor)):
        s=request.app.state.store;e=s.evaluations.get(str(evaluation_id))
        if not e: raise HTTPException(404,'Không tìm thấy đánh giá')
        case_access(s,e['case_id'],a)
        if a=='pharmacist' and any(r['module']!='medsafety' for r in e['results']): raise HTTPException(403,'Không có quyền kết quả ngoài MedSafety')
        return e

    @app.post('/api/v1/evaluations/{evaluation_id}/decisions',response_model=DecisionOut,status_code=201,tags=['Decision'])
    def decision(evaluation_id:UUID,body:DecisionInput,request:Request,a=Depends(actor)):
        role(a,['doctor']);s=request.app.state.store;rid=str(evaluation_id)
        with s.lock:
            e=s.evaluations.get(rid)
            if not e: raise HTTPException(404,'Không tìm thấy đánh giá')
            c=case_access(s,e['case_id'],a)
            if c['revision']!=e['input_revision']: raise HTTPException(409,'Đánh giá đã cũ; cần đánh giá lại')
            if any(x['evaluation_id']==rid for x in s.decisions.values()): raise HTTPException(409,'Đã ghi quyết định cho đánh giá')
            d=DecisionOut(id=uid(),evaluation_id=rid,doctor_id=demo_user_id(a),created_at=now(),**body.model_dump()).model_dump(mode='json')
            s.decisions[d['id']]=d;s.record(a,'decision.created',d['id']);return d

    @app.get('/api/v1/cases/{case_id}/history',response_model=list[HistoryEntry],tags=['History'])
    def history(case_id:UUID,request:Request,a=Depends(actor)):
        role(a,['doctor']);s=request.app.state.store;cid=str(case_id);case_access(s,cid,a);return [dict(**e,decision=next((d for d in s.decisions.values() if d['evaluation_id']==e['id']),None)) for e in s.evaluations.values() if e['case_id']==cid]

    @app.get('/api/v1/cases/{case_id}/export',response_model=ExportOut,tags=['History'])
    def export(case_id:UUID,request:Request,a=Depends(actor)):
        role(a,['doctor']);s=request.app.state.store;cid=str(case_id)
        with s.lock:
            c=case_access(s,cid,a);es=[e for e in s.evaluations.values() if e['case_id']==cid];ids={e['id'] for e in es};ds=[d for d in s.decisions.values() if d['evaluation_id'] in ids];s.record(a,'case.exported',cid)
            return dict(case=deepcopy(c),evaluations=deepcopy(es),decisions=deepcopy(ds),mode='stub')

    @app.get('/api/v1/rule-versions',response_model=list[RuleOut],tags=['Rules'])
    def rules(request:Request,a=Depends(actor)):
        role(a,['admin']);return list(request.app.state.store.rules.values())

    @app.post('/api/v1/rule-versions',response_model=RuleOut,status_code=201,tags=['Rules'])
    def create_rule(body:RuleInput,request:Request,a=Depends(actor)):
        role(a,['admin']);s=request.app.state.store
        with s.lock:
            v=1+max([x['version'] for x in s.rules.values() if x['code']==body.code],default=0)
            r=dict(id=uid(),version=v,status='draft',test_status='not_run',approval_ref=None,**body.model_dump());s.rules[r['id']]=r;s.record(a,'rule.drafted',r['id']);return r

    @app.post('/api/v1/rule-versions/{rule_id}/test',response_model=RuleTestOut,tags=['Rules'])
    def test_rule(rule_id:UUID,request:Request,a=Depends(actor)):
        role(a,['admin']);s=request.app.state.store;rid=str(rule_id)
        with s.lock:
            r=s.rules.get(rid)
            if not r: raise HTTPException(404,'Không tìm thấy quy tắc')
            r.update(status='tested',test_status='schema_passed');s.record(a,'rule.schema_tested',rid)
            return dict(rule_id=rid,result='schema_passed',clinical_validation='not_performed')

    @app.post('/api/v1/rule-versions/{rule_id}/activate',response_model=RuleOut,tags=['Rules'])
    def activate(rule_id:UUID,request:Request,a=Depends(actor)):
        role(a,['admin']);s=request.app.state.store;rid=str(rule_id)
        with s.lock:
            if rid not in s.rules: raise HTTPException(404,'Không tìm thấy quy tắc')
            # No trusted approval integration in the skeleton. Never let admin self-approve.
            s.record(a,'rule.activation_blocked',rid)
            raise HTTPException(409,'Chưa có phê duyệt chuyên môn được xác minh; không kích hoạt')

    @app.get('/api/v1/audit-events',response_model=list[AuditOut],tags=['Audit'])
    def audit(request:Request,a=Depends(actor)):
        role(a,['admin']);return list(request.app.state.store.audit)
    from .spec import contract
    app.openapi=lambda: contract(app)
    return app

app=create_app()
