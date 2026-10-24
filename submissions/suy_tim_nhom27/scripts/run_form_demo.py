"""Run the existing Gateway against a dedicated synthetic forms schema."""
import argparse
import json
import logging
import os
from pathlib import Path
import re
import sys
from psycopg.conninfo import make_conninfo
import uvicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
parser = argparse.ArgumentParser()
parser.add_argument('--schema')
parser.add_argument('--port', type=int, default=8001)
parser.add_argument('--config-file', help='Private local-data JSON config for detached pythonw launch')
args = parser.parse_args()
dsn = os.environ.get('DATABASE_URL')
log_config = uvicorn.config.LOGGING_CONFIG
if args.config_file:
    config_path = Path(args.config_file).resolve()
    if 'local-data' not in config_path.parts:
        raise ValueError('Configuration must be in ignored local-data')
    config = json.loads(config_path.read_text(encoding='utf-8'))
    args.schema, args.port, dsn = config['schema'], config.get('port', args.port), config['database_url']
    logfile = config_path.with_suffix('.log')
    stream = logfile.open('a', encoding='utf-8')
    sys.stdout = sys.stderr = stream
    logging.basicConfig(stream=stream, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    log_config = None
if not args.schema or not re.fullmatch(r'd3_form_[a-z0-9_]{1,45}', args.schema):
    raise ValueError('Dedicated d3_form_ schema required')
if not dsn:
    raise ValueError('DATABASE_URL or private config database_url is required')
os.environ['DATABASE_URL'] = make_conninfo(dsn, options=f'-csearch_path={args.schema},public')
uvicorn.run('src.gateway.main:app', host='127.0.0.1', port=args.port, workers=1, log_config=log_config)
