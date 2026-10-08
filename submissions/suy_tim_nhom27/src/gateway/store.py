"""Single-process demo store. Production repositories must use transactions."""
from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4, uuid5, NAMESPACE_URL

def now(): return datetime.now(timezone.utc)
def uid(): return str(uuid4())
def demo_user_id(role): return str(uuid5(NAMESPACE_URL, 'nhom27:synthetic-user:'+role))

class MemoryStore:
    def __init__(self):
        self.lock=RLock()
        self.cases={}; self.encounters={}; self.observations={}; self.medications={}
        self.evaluations={}; self.snapshots={}; self.decisions={}; self.rules={}; self.tokens={}; self.audit=[]
    def record(self,actor,action,entity):
        self.audit.append(dict(id=uid(),actor_id=demo_user_id(actor),action=action,entity_id=str(entity),created_at=now()))
    def snapshot(self,case_id,encounter_id):
        return deepcopy({'case':self.cases[case_id], 'encounter':self.encounters[encounter_id],
            'observations':[x for x in self.observations.values() if x['encounter_id']==encounter_id],
            'medications':[x for x in self.medications.values() if x['encounter_id']==encounter_id]})
