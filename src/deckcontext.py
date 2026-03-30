"""DeckContext management — init, read, write, validate, checksum.

All deck state lives in a directory of JSON files (default: ./tmp/deck/).
Each file corresponds to one data contract. This module provides the
shared infrastructure that all skills use to interact with DeckContext.
"""

import hashlib
import json
import os
from datetime import datetime, timezone

import jsonschema

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), 'schemas')

CONTRACT_SCHEMAS = {
    'talk-brief': 'talk_brief.schema.json',
    'pipeline-state': 'pipeline_state.schema.json',
    'style-guide': 'style_guide.schema.json',
    'outline': 'slide_outline.schema.json',
    'speaker-notes': 'speaker_notes.schema.json',
    'image-manifest': 'image_manifest.schema.json',
    'chart-manifest': 'chart_manifest.schema.json',
    'qa-report': 'qa_report.schema.json',
    'brand-profile': 'brand_profile.schema.json',
}

DEFAULT_STEP_ORDER = [
    'validate-brief',
    'brand-manager',
    'slide-stylist',
    'narrative-architect',
    'speaker-notes-writer',
    'imagegen-bridge',
    'chart-renderer',
    'deck-assembler',
    'deck-qa',
]


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _load_schema(contract_name):
    schema_file = CONTRACT_SCHEMAS.get(contract_name)
    if not schema_file:
        return None
    path = os.path.join(SCHEMA_DIR, schema_file)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def init_deck(deck_dir='./tmp/deck'):
    os.makedirs(os.path.join(deck_dir, 'images'), exist_ok=True)
    os.makedirs(os.path.join(deck_dir, 'output'), exist_ok=True)
    state_path = os.path.join(deck_dir, 'pipeline-state.json')
    if not os.path.exists(state_path):
        state = {
            'pipeline_id': _now_iso(),
            'created_at': _now_iso(),
            'status': 'running',
            'current_step': None,
            'steps': {name: {'status': 'pending'} for name in DEFAULT_STEP_ORDER},
            'step_order': DEFAULT_STEP_ORDER,
        }
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)


def write_contract(deck_dir, contract_name, data, validate=True):
    if validate:
        schema = _load_schema(contract_name)
        if schema:
            jsonschema.validate(instance=data, schema=schema)
    path = os.path.join(deck_dir, f'{contract_name}.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def read_contract(deck_dir, contract_name):
    path = os.path.join(deck_dir, f'{contract_name}.json')
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def compute_checksum(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def update_step(deck_dir, step_name, status, output_file=None, error=None):
    state = read_contract(deck_dir, 'pipeline-state')
    if state is None:
        raise FileNotFoundError(f'pipeline-state.json not found in {deck_dir}')
    if step_name not in state['steps']:
        state['steps'][step_name] = {}
    step = state['steps'][step_name]
    step['status'] = status
    if status == 'running':
        step['started_at'] = _now_iso()
        state['current_step'] = step_name
    elif status == 'completed':
        step['completed_at'] = _now_iso()
        if output_file:
            step['output_file'] = output_file
    elif status == 'failed':
        step['completed_at'] = _now_iso()
        if error:
            step['error'] = error
    state['updated_at'] = _now_iso()
    state['status'] = 'running'
    write_contract(deck_dir, 'pipeline-state', state, validate=False)
