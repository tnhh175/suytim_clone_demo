from pathlib import Path
import sys,yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.gateway.main import app
p=Path(__file__).resolve().parents[1]/'api/openapi.yaml'
p.write_text(yaml.safe_dump(app.openapi(),allow_unicode=True,sort_keys=False),encoding='utf-8')
print(p)
