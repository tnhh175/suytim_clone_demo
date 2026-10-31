"""Reviewable, atomic catalog upgrades; never rewrites pinned encounters or values.

Dry run by default. Existing Admin changes cause a conflict, never an overwrite.
Only dedicated synthetic d3_form_ schemas are accepted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / 'database/catalog-upgrades/005_review_20261030.json'


def definition_only(value):
    return {key: item for key, item in value.items() if key != 'version'}


def plan_changes(current, manifest):
    """Return exact replacements and conflicts, without mutating either input."""
    changes, conflicts, seen = [], [], set()
    for entry in manifest['changes']:
        code = entry['code']
        if code in seen or entry['after']['code'] != code:
            raise ValueError('Duplicate or mismatched catalog code')
        seen.add(code)
        row = current.get(code)
        present = definition_only(row['definition']) if row else None
        if present == entry['after']:
            continue
        if present != entry['before']:
            conflicts.append(code)
        else:
            changes.append({**entry, 'version': row['version'] + 1 if row else 1})
    return changes, conflicts


def private_path(path):
    resolved = Path(path).resolve()
    if 'local-data' not in resolved.parts:
        raise ValueError('Private files must be inside ignored local-data')
    return resolved


def upgrade(dsn, schema, manifest, *, apply=False, backup_file=None):
    if not re.fullmatch(r'd3_form_[a-z0-9_]{1,45}', schema):
        raise ValueError('Dedicated d3_form_ synthetic schema required')
    if apply and backup_file is None:
        raise ValueError('Apply requires a new private backup file')
    backup_path = private_path(backup_file) if backup_file else None
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        conn.execute('SET LOCAL ROLE hf_demo_owner')
        # Exclude public from table resolution: a missing sandbox must fail closed.
        conn.execute(sql.SQL('SET LOCAL search_path TO {}').format(sql.Identifier(schema)))
        revision = conn.execute('SELECT revision FROM form_catalog WHERE id=1 FOR UPDATE').fetchone()['revision']
        current = {row['code']: row for row in conn.execute('SELECT code,definition,version FROM form_field')}
        changes, conflicts = plan_changes(current, manifest)
        report = {'schema': schema, 'upgrade': manifest['id'], 'applied': False,
                  'catalog_revision': revision, 'changes': [row['code'] for row in changes],
                  'conflicts': conflicts, 'pinned_visits_changed': False}
        if conflicts or not apply or not changes:
            return report
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        with backup_path.open('x', encoding='utf-8') as output:
            json.dump({'schema': schema, 'created_at': datetime.now(timezone.utc).isoformat(),
                       'catalog_revision': revision, 'upgrade': manifest['id'],
                       'fields': list(current.values())}, output, ensure_ascii=False, indent=2)
        for change in changes:
            code, definition, version = change['code'], change['after'], change['version']
            conn.execute('''INSERT INTO form_field(code,definition,version) VALUES(%s,%s,%s)
              ON CONFLICT(code) DO UPDATE SET definition=EXCLUDED.definition,version=EXCLUDED.version,
                updated_by=NULL,updated_at=now()''', (code, Jsonb(definition), version))
            conn.execute('INSERT INTO form_field_history(code,version,definition) VALUES(%s,%s,%s)',
                         (code, version, Jsonb(definition)))
        conn.execute('UPDATE form_catalog SET revision=revision+1 WHERE id=1')
        conn.execute('INSERT INTO form_schema_migration(version) VALUES(%s) ON CONFLICT DO NOTHING', (manifest['id'],))
        return {**report, 'applied': True, 'catalog_revision': revision + 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config-file', required=True, help='Private local-data runtime JSON')
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--backup-file')
    args = parser.parse_args()
    config = json.loads(private_path(args.config_file).read_text(encoding='utf-8'))
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    result = upgrade(config['database_url'], config['schema'], manifest,
                     apply=args.apply, backup_file=args.backup_file)
    print(json.dumps(result, ensure_ascii=False))
    return 2 if result['conflicts'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
