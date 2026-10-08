"""Four independent ports; in week 3 their implementations are explicit stubs."""
from abc import ABC, abstractmethod
from .models import ModuleResult

class ModulePort(ABC):
    @abstractmethod
    def evaluate(self, snapshot: dict) -> ModuleResult: ...

class StubModule(ModulePort):
    def __init__(self,name,required): self.name=name; self.required=required
    def evaluate(self,snapshot):
        # Latest result per code; a later unknown overrides an earlier value.
        latest={}
        for obs in sorted(snapshot['observations'],key=lambda x:x['observed_at']): latest[obs['code']]=obs
        missing=[c for c in self.required if c not in latest or latest[c]['status']!='present']
        return ModuleResult(module=self.name,missing_fields=missing,
            message='Dữ liệu giả lập để kiểm thử giao diện; chưa thực hiện đánh giá lâm sàng.')

def build_ports():
    # Demo completeness only: these are NOT clinical diagnostic criteria.
    return {n:StubModule(n,r) for n,r in {'diagnosis':['ef'],'lab_test':[],
        'treatment':['systolic_bp','egfr','potassium'],'medsafety':['egfr','potassium']}.items()}
