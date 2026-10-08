"""Export the same contract to Swagger UI and OpenAPI 3.0.3 YAML."""
from copy import deepcopy
from fastapi.openapi.utils import get_openapi

def contract(app):
    spec=get_openapi(title=app.title,version=app.version,description=app.description,routes=app.routes,openapi_version='3.0.3')
    def convert(x):
        if isinstance(x,list): return [convert(v) for v in x]
        if not isinstance(x,dict): return x
        x={k:convert(v) for k,v in x.items()}
        if 'anyOf' in x:
            nonnull=[v for v in x['anyOf'] if v.get('type')!='null']
            if len(nonnull)<len(x['anyOf']):
                x['nullable']=True
                if len(nonnull)==1:
                    x.pop('anyOf')
                    if '$ref' in nonnull[0]: x['allOf']=[nonnull[0]]
                    else: x.update(nonnull[0])
                else:x['anyOf']=nonnull
        if 'const' in x:x['enum']=[x.pop('const')]
        for bound,key in [('exclusiveMinimum','minimum'),('exclusiveMaximum','maximum')]:
            if bound in x and not isinstance(x[bound],bool):
                x[key]=x[bound];x[bound]=True
        return x
    spec=convert(spec)
    spec['servers']=[{'url':'http://127.0.0.1:8000','description':'Local stub only; deployment requires HTTPS'}]
    spec['components']['securitySchemes']['HTTPBearer']['description']='Opaque demo token from /api/v1/auth/token; expires after 3600 seconds. Production identity adapter pending.'
    # This app has a custom 422 handler using the standard Error envelope.
    for path in spec['paths'].values():
        for op in path.values():
            if isinstance(op,dict) and 'responses' in op:
                op['responses']['422']={'description':'Dữ liệu không hợp lệ','content':{'application/json':{'schema':{'$ref':'#/components/schemas/Error'}}}}
    return spec
