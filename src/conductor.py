"""Deck Conductor pipeline utilities — state persistence, budget bridge, QA tracking.

This module handles ONLY mechanical state management:
- Pipeline lifecycle (init, phase transitions, draft cycles)
- QA correction cycle tracking (max 2)
- Budget persistence (save/load BudgetTracker snapshots)
- Provider snapshot persistence
- Speaker approval logging
- Progress summary formatting

All orchestration decisions (what to invoke next, when to escalate)
live in the agent definition at .claude/agents/deck-conductor.md.
"""

import json
import os
from datetime import datetime, timezone

from src.budget_tracker import BudgetTracker
from src.deckcontext import DEFAULT_STEP_ORDER

MAX_QA_CYCLES = 2


def _state_path(deck_dir):
    return os.path.join(deck_dir, 'pipeline-state.json')


def _read_state(deck_dir):
    path = _state_path(deck_dir)
    with open(path) as f:
        return json.load(f)


def _write_state(deck_dir, state):
    state['updated_at'] = datetime.now(timezone.utc).isoformat()
    path = _state_path(deck_dir)
    with open(path, 'w') as f:
        json.dump(state, f, indent=2)


def init_pipeline(deck_dir, budget_usd=0.0):
    """Create pipeline-state.json with initial values."""
    os.makedirs(deck_dir, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    state = {
        'pipeline_id': now,
        'created_at': now,
        'updated_at': now,
        'status': 'running',
        'phase': 'draft',
        'draft_cycle': 0,
        'qa_correction_cycle': 0,
        'current_step': None,
        'budget': {
            'total_budget_usd': budget_usd,
            'spent_usd': 0.0,
            'remaining_usd': budget_usd,
            'utilisation': 0.0,
            'budget_state': 'allow',
            'api_call_count': 0,
            'cache_hits': 0,
            'cache_savings_usd': 0.0,
        },
        'available_providers': {},
        'speaker_approvals': [],
        'steps': {step: {'status': 'pending'} for step in DEFAULT_STEP_ORDER},
        'step_order': list(DEFAULT_STEP_ORDER),
    }
    _write_state(deck_dir, state)
    return state


def get_pipeline_state(deck_dir):
    """Read pipeline state. Returns None if not found."""
    path = _state_path(deck_dir)
    if not os.path.isfile(path):
        return None
    return _read_state(deck_dir)


def set_phase(deck_dir, phase):
    """Set phase to 'draft' or 'production'. Resets qa_correction_cycle."""
    state = _read_state(deck_dir)
    state['phase'] = phase
    state['qa_correction_cycle'] = 0
    _write_state(deck_dir, state)


def advance_draft_cycle(deck_dir):
    """Increment draft_cycle, reset qa_correction_cycle and step statuses."""
    state = _read_state(deck_dir)
    state['draft_cycle'] = state.get('draft_cycle', 0) + 1
    state['qa_correction_cycle'] = 0
    for step in state.get('steps', {}):
        state['steps'][step]['status'] = 'pending'
    _write_state(deck_dir, state)


def increment_qa_cycle(deck_dir):
    """Increment qa_correction_cycle. Raises ValueError if already at max."""
    state = _read_state(deck_dir)
    current = state.get('qa_correction_cycle', 0)
    if current >= MAX_QA_CYCLES:
        raise ValueError(f'QA correction cycle already at maximum ({MAX_QA_CYCLES})')
    state['qa_correction_cycle'] = current + 1
    _write_state(deck_dir, state)
    return current + 1


def can_correct(deck_dir):
    """Return True if QA correction cycles remain."""
    state = _read_state(deck_dir)
    return state.get('qa_correction_cycle', 0) < MAX_QA_CYCLES


def save_budget_snapshot(deck_dir, budget_tracker):
    """Write BudgetTracker summary into pipeline state (not full api_calls)."""
    state = _read_state(deck_dir)
    full = budget_tracker.to_dict()
    state['budget'] = {
        'total_budget_usd': full['total_budget_usd'],
        'spent_usd': full['spent_usd'],
        'remaining_usd': full['remaining_usd'],
        'utilisation': full['utilisation'],
        'budget_state': full['budget_state'],
        'api_call_count': len(full.get('api_calls', [])),
        'cache_hits': full.get('cache_hits', 0),
        'cache_savings_usd': full.get('cache_savings_usd', 0.0),
    }
    _write_state(deck_dir, state)


def load_budget_tracker(deck_dir):
    """Reconstruct a BudgetTracker from persisted state."""
    state = _read_state(deck_dir)
    budget = state.get('budget', {})
    tracker = BudgetTracker(budget.get('total_budget_usd', 0.0))
    spent = budget.get('spent_usd', 0.0)
    if spent > 0:
        tracker._spent = spent
    return tracker


def save_provider_snapshot(deck_dir, providers_dict):
    """Write AvailableProviders to pipeline state."""
    state = _read_state(deck_dir)
    state['available_providers'] = providers_dict
    _write_state(deck_dir, state)


def log_speaker_approval(deck_dir, decision, context):
    """Append to speaker_approvals array with timestamp."""
    state = _read_state(deck_dir)
    state.setdefault('speaker_approvals', []).append({
        'decision': decision,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'context': context,
    })
    _write_state(deck_dir, state)


def has_draft_approval(deck_dir):
    """Return True if speaker_approvals contains a draft_approved decision."""
    state = _read_state(deck_dir)
    return any(a['decision'] == 'draft_approved'
               for a in state.get('speaker_approvals', []))


def pipeline_summary_markdown(deck_dir):
    """Generate a Markdown status summary for Speaker review."""
    state = _read_state(deck_dir)
    budget = state.get('budget', {})
    lines = [
        '## Pipeline Status',
        '',
        f'**Phase:** {state.get("phase", "unknown")}',
        f'**Draft Cycle:** {state.get("draft_cycle", 0)}',
        f'**QA Corrections:** {state.get("qa_correction_cycle", 0)}/{MAX_QA_CYCLES}',
        '',
        '### Budget',
        '',
        '| Metric | Value |',
        '|--------|-------|',
        f'| Total | ${budget.get("total_budget_usd", 0):.2f} |',
        f'| Spent | ${budget.get("spent_usd", 0):.2f} |',
        f'| Remaining | ${budget.get("remaining_usd", 0):.2f} |',
        f'| State | {budget.get("budget_state", "unknown")} |',
        '',
        '### Steps',
        '',
        '| Step | Status |',
        '|------|--------|',
    ]
    for step in state.get('step_order', []):
        step_data = state.get('steps', {}).get(step, {})
        lines.append(f'| {step} | {step_data.get("status", "unknown")} |')
    return '\n'.join(lines)
