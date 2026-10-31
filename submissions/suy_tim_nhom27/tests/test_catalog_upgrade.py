"""Catalog operator changes must not overwrite Admin edits or require patient writes."""
import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / 'scripts/upgrade_form_catalog.py'
SPEC = importlib.util.spec_from_file_location('catalog_upgrade', PATH)
UPGRADE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UPGRADE)


def test_upgrade_plan_is_idempotent_and_rejects_admin_conflicts():
    old = {'code': 'measurement', 'type': 'number', 'label': 'Old'}
    new = {**old, 'label': 'New'}
    manifest = {'changes': [{'code': old['code'], 'before': old, 'after': new}]}
    current = {'measurement': {'definition': old, 'version': 4}}
    changes, conflicts = UPGRADE.plan_changes(current, manifest)
    assert conflicts == [] and changes[0]['version'] == 5
    assert current['measurement']['definition'] == old
    assert UPGRADE.plan_changes({'measurement': {'definition': new, 'version': 5}}, manifest) == ([], [])
    assert UPGRADE.plan_changes({'measurement': {'definition': {**old, 'label': 'Admin'}, 'version': 5}}, manifest) == ([], ['measurement'])


def test_upgrade_additions_do_not_replace_existing_custom_codes():
    new = {'code': 'new_measurement', 'type': 'number'}
    manifest = {'changes': [{'code': new['code'], 'before': None, 'after': new}]}
    assert UPGRADE.plan_changes({}, manifest)[0][0]['version'] == 1
    assert UPGRADE.plan_changes({'new_measurement': {'definition': {**new, 'type': 'text'}, 'version': 1}}, manifest)[1] == ['new_measurement']
    with pytest.raises(ValueError):
        UPGRADE.plan_changes({}, {'changes': manifest['changes'] * 2})


@pytest.mark.parametrize('schema', ['public', 'd3_form_', 'd3_form_fake;public', 'hf_demo'])
def test_upgrade_refuses_outside_synthetic_schema_without_connecting(schema):
    with pytest.raises(ValueError):
        UPGRADE.upgrade('never-connect', schema, {})


def test_upgrade_apply_requires_private_backup_before_connecting(tmp_path):
    with pytest.raises(ValueError):
        UPGRADE.upgrade('never-connect', 'd3_form_test', {}, apply=True)
    with pytest.raises(ValueError):
        UPGRADE.upgrade('never-connect', 'd3_form_test', {}, apply=True, backup_file=tmp_path / 'backup.json')


def test_upgrade_manifest_matches_shipped_definitions_and_replays_without_changes():
    manifest = json.loads(UPGRADE.DEFAULT_MANIFEST.read_text(encoding='utf-8'))
    fields = json.loads((PATH.parents[1] / 'src/gateway/forms/catalog.json').read_text(encoding='utf-8'))
    current = {field['code']: {'definition': field, 'version': 1} for field in fields}
    assert UPGRADE.plan_changes(current, manifest) == ([], [])
    assert sum(entry['before'] is None for entry in manifest['changes']) == 16
    assert all(entry['before'] is None or entry['before']['code'] == entry['code'] for entry in manifest['changes'])
