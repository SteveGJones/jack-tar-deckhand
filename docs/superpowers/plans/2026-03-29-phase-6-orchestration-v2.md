# Phase 6: Orchestration — Deck Conductor Agent

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `deck-conductor` agent — the top-level orchestrator that sequences the presentation pipeline, manages draft/production lifecycle, tracks budget, handles QA correction loops, and delegates all content/design/image work to L1 skills that collaborate directly with the Speaker.

**Architecture:** The deck-conductor is a Claude Code agent (`.claude/agents/deck-conductor.md`) with hybrid authority. In Claude Code, the agent IS Claude — when it invokes a skill like `/brand-manager`, Claude follows that skill's instructions and talks to the Speaker directly. The Conductor doesn't relay messages. A thin Python module `src/conductor.py` handles state persistence (pipeline lifecycle, budget snapshots, QA cycle tracking, provider snapshots, approval logging). The existing `BudgetTracker` from Phase 4A is reused directly — `conductor.py` provides the persistence bridge.

**Tech Stack:** Python 3.8+, jsonschema, pytest, src/deckcontext.py (Phase 1), src/budget_tracker.py (Phase 4A)

**Dependencies:** All prior phases (1-5) must be complete. The Conductor invokes all skills built in those phases.

**Supersedes:** `docs/superpowers/plans/2026-03-29-phase-6-orchestration.md`

---

## File Structure

```
research/
  synthesis-deck-conductor.md             # Research synthesis
src/
  conductor.py                            # Pipeline lifecycle, budget persistence, QA tracking
  schemas/
    pipeline_state.schema.json            # Extended with phase, budget, cycles, approvals
.claude/
  agents/
    deck-conductor.md                     # The agent definition (primary deliverable)
tests/
  test_conductor.py                       # Conductor utility tests
  fixtures/
    valid_pipeline_state_extended.json    # Extended PipelineState fixture
```

---

## Task 1: Research Synthesis

**Files:**
- Create: `research/synthesis-deck-conductor.md`

- [ ] **Step 1: Read source material**

Read:
- `docs/architecture/ai-persona-summaries.md` (Section 1 — Deck Conductor)
- `docs/architecture/architecture-overview.md` (Pipeline Execution Flow)
- `src/budget_tracker.py` (existing budget tracking)
- `src/deckcontext.py` (existing state management)
- `src/schemas/pipeline_state.schema.json` (current schema)

- [ ] **Step 2: Write synthesis document**

Create `research/synthesis-deck-conductor.md` covering:
1. **Sequencing and state management role:** The Conductor sequences skills, each skill handles its own Speaker collaboration
2. **Draft/production lifecycle:** Draft iterates with low-quality images, production is single-pass full quality
3. **Budget management:** Reuse BudgetTracker, persist snapshots to pipeline state, 4-state degradation
4. **QA correction loop:** Max 2 autonomous cycles, then escalate. Reviewer feedback always goes to Speaker.
5. **Authority model:** 8 autonomous decision types, 10 escalated decision types (enumerate each)
6. **Pipeline step order:** brand-manager → slide-stylist → narrative-architect → speaker-notes-writer → imagegen-bridge → deck-assembler → deck-qa → presentation-reviewer

- [ ] **Step 3: Commit**

```bash
git add research/synthesis-deck-conductor.md
git commit -m "docs: add research synthesis for deck-conductor agent"
```

---

## Task 2: Extend Pipeline State Schema

**Files:**
- Modify: `src/schemas/pipeline_state.schema.json`
- Create: `tests/fixtures/valid_pipeline_state_extended.json`

- [ ] **Step 1: Extend the schema**

Add these properties to `src/schemas/pipeline_state.schema.json`:

```json
"phase": {
  "type": "string",
  "enum": ["draft", "production"],
  "description": "Current lifecycle phase"
},
"draft_cycle": {
  "type": "integer",
  "minimum": 0,
  "description": "Current draft iteration number"
},
"qa_correction_cycle": {
  "type": "integer",
  "minimum": 0,
  "maximum": 2,
  "description": "QA correction cycle within current draft (max 2)"
},
"budget": {
  "type": "object",
  "properties": {
    "total_budget_usd": {"type": "number"},
    "spent_usd": {"type": "number"},
    "remaining_usd": {"type": "number"},
    "utilisation": {"type": "number"},
    "budget_state": {
      "type": "string",
      "enum": ["allow", "allow_with_caps", "degrade", "typography_only"]
    },
    "api_call_count": {"type": "integer"},
    "cache_hits": {"type": "integer"},
    "cache_savings_usd": {"type": "number"}
  }
},
"available_providers": {
  "type": "object",
  "additionalProperties": {
    "type": "object",
    "properties": {
      "available": {"type": "boolean"}
    }
  }
},
"speaker_approvals": {
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "decision": {"type": "string"},
      "timestamp": {"type": "string"},
      "context": {"type": "string"}
    }
  }
}
```

- [ ] **Step 2: Create extended fixture**

Create `tests/fixtures/valid_pipeline_state_extended.json`:

```json
{
  "pipeline_id": "2026-03-29T14:00:00Z",
  "created_at": "2026-03-29T14:00:00Z",
  "status": "running",
  "phase": "draft",
  "draft_cycle": 1,
  "qa_correction_cycle": 0,
  "current_step": "imagegen-bridge",
  "budget": {
    "total_budget_usd": 5.00,
    "spent_usd": 1.20,
    "remaining_usd": 3.80,
    "utilisation": 0.24,
    "budget_state": "allow",
    "api_call_count": 8,
    "cache_hits": 2,
    "cache_savings_usd": 0.16
  },
  "available_providers": {
    "ollama": {"available": true},
    "openai": {"available": true},
    "google": {"available": false},
    "fal": {"available": true},
    "recraft": {"available": true}
  },
  "speaker_approvals": [
    {
      "decision": "budget_confirmed",
      "timestamp": "2026-03-29T14:00:05Z",
      "context": "Speaker confirmed $5.00 budget cap"
    },
    {
      "decision": "providers_confirmed",
      "timestamp": "2026-03-29T14:00:10Z",
      "context": "Proceeding with Ollama + OpenAI + FAL + Recraft (Google unavailable)"
    }
  ],
  "steps": {
    "brand-manager": {
      "status": "completed",
      "started_at": "2026-03-29T14:00:15Z",
      "completed_at": "2026-03-29T14:01:00Z"
    },
    "slide-stylist": {
      "status": "completed",
      "started_at": "2026-03-29T14:01:01Z",
      "completed_at": "2026-03-29T14:03:00Z"
    },
    "narrative-architect": {
      "status": "completed",
      "started_at": "2026-03-29T14:03:01Z",
      "completed_at": "2026-03-29T14:05:00Z"
    },
    "speaker-notes-writer": {
      "status": "completed",
      "started_at": "2026-03-29T14:05:01Z",
      "completed_at": "2026-03-29T14:06:00Z"
    },
    "imagegen-bridge": {
      "status": "running",
      "started_at": "2026-03-29T14:06:01Z"
    }
  },
  "step_order": [
    "brand-manager",
    "slide-stylist",
    "narrative-architect",
    "speaker-notes-writer",
    "imagegen-bridge",
    "deck-assembler",
    "deck-qa"
  ]
}
```

- [ ] **Step 3: Validate and run existing schema tests**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_schemas.py -v`

Expected: All existing tests PASS (the new fields are optional, so existing fixtures still validate).

- [ ] **Step 4: Commit**

```bash
git add src/schemas/pipeline_state.schema.json tests/fixtures/valid_pipeline_state_extended.json
git commit -m "feat: extend PipelineState schema with phase, budget, cycles, and approvals"
```

---

## Task 3: Conductor Utilities

**Files:**
- Create: `src/conductor.py`
- Create: `tests/test_conductor.py`

- [ ] **Step 1: Write tests**

Create `tests/test_conductor.py`:

```python
"""Tests for deck-conductor pipeline utilities."""

import json
import os
import shutil
import pytest

from src.conductor import (
    init_pipeline,
    get_pipeline_state,
    set_phase,
    advance_draft_cycle,
    increment_qa_cycle,
    can_correct,
    save_budget_snapshot,
    load_budget_tracker,
    log_speaker_approval,
    has_draft_approval,
    pipeline_summary_markdown,
)
from src.budget_tracker import BudgetTracker

TEST_DECK_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'test-conductor')


@pytest.fixture(autouse=True)
def clean_deck_dir():
    os.makedirs(TEST_DECK_DIR, exist_ok=True)
    yield
    if os.path.exists(TEST_DECK_DIR):
        shutil.rmtree(TEST_DECK_DIR)


class TestInitPipeline:
    def test_creates_pipeline_state(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        state = get_pipeline_state(TEST_DECK_DIR)
        assert state is not None
        assert state['phase'] == 'draft'
        assert state['draft_cycle'] == 0
        assert state['qa_correction_cycle'] == 0
        assert state['status'] == 'running'

    def test_initialises_budget(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=10.0)
        state = get_pipeline_state(TEST_DECK_DIR)
        assert state['budget']['total_budget_usd'] == 10.0
        assert state['budget']['spent_usd'] == 0.0

    def test_initialises_step_order(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        state = get_pipeline_state(TEST_DECK_DIR)
        assert 'brand-manager' in state['step_order']
        assert 'deck-qa' in state['step_order']


class TestPhaseManagement:
    def test_set_phase_to_production(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        set_phase(TEST_DECK_DIR, 'production')
        state = get_pipeline_state(TEST_DECK_DIR)
        assert state['phase'] == 'production'

    def test_advance_draft_cycle(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        advance_draft_cycle(TEST_DECK_DIR)
        state = get_pipeline_state(TEST_DECK_DIR)
        assert state['draft_cycle'] == 1
        assert state['qa_correction_cycle'] == 0


class TestQACycles:
    def test_can_correct_initially(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        assert can_correct(TEST_DECK_DIR) is True

    def test_increment_qa_cycle(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        count = increment_qa_cycle(TEST_DECK_DIR)
        assert count == 1
        assert can_correct(TEST_DECK_DIR) is True

    def test_cannot_correct_after_max(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        increment_qa_cycle(TEST_DECK_DIR)
        increment_qa_cycle(TEST_DECK_DIR)
        assert can_correct(TEST_DECK_DIR) is False

    def test_increment_raises_at_max(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        increment_qa_cycle(TEST_DECK_DIR)
        increment_qa_cycle(TEST_DECK_DIR)
        with pytest.raises(ValueError):
            increment_qa_cycle(TEST_DECK_DIR)


class TestBudgetPersistence:
    def test_save_and_load_budget(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=10.0)
        tracker = BudgetTracker(10.0)
        tracker.log_api_call('gpt-image-1.5-low', 0.009, 'test-img-1')
        save_budget_snapshot(TEST_DECK_DIR, tracker)
        loaded = load_budget_tracker(TEST_DECK_DIR)
        assert loaded.spent == pytest.approx(0.009, abs=0.001)
        assert loaded._total_budget_usd == 10.0


class TestSpeakerApprovals:
    def test_log_approval(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        log_speaker_approval(TEST_DECK_DIR, 'budget_confirmed', '$5 budget approved')
        state = get_pipeline_state(TEST_DECK_DIR)
        assert len(state['speaker_approvals']) == 1
        assert state['speaker_approvals'][0]['decision'] == 'budget_confirmed'

    def test_has_draft_approval_false(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        assert has_draft_approval(TEST_DECK_DIR) is False

    def test_has_draft_approval_true(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        log_speaker_approval(TEST_DECK_DIR, 'draft_approved', 'Looks good')
        assert has_draft_approval(TEST_DECK_DIR) is True


class TestSummary:
    def test_produces_markdown(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        md = pipeline_summary_markdown(TEST_DECK_DIR)
        assert '## Pipeline Status' in md
        assert 'draft' in md.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_conductor.py -v`

Expected: FAIL — `src.conductor` not found.

- [ ] **Step 3: Implement conductor utilities**

Create `src/conductor.py`:

```python
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
        f'| Metric | Value |',
        f'|--------|-------|',
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_conductor.py -v`

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/conductor.py tests/test_conductor.py
git commit -m "feat: add deck-conductor pipeline utilities (lifecycle, budget, QA tracking)"
```

---

## Task 4: Deck Conductor Agent Definition

**Files:**
- Create: `.claude/agents/deck-conductor.md`

- [ ] **Step 1: Read source material**

Read:
- `research/synthesis-deck-conductor.md`
- `docs/architecture/ai-persona-summaries.md` (Section 1)
- `docs/architecture/architecture-overview.md` (Pipeline Execution Flow)

- [ ] **Step 2: Write the agent definition**

Create `.claude/agents/deck-conductor.md` — the primary deliverable of Phase 6. This is a Claude Code agent definition that sequences the full pipeline. It should cover:

1. **Identity:** Persona ID, authority model (hybrid), escalation target (Speaker)
2. **Pipeline sequence:** brand-manager → slide-stylist → narrative-architect → speaker-notes-writer → imagegen-bridge → deck-assembler → deck-qa → presentation-reviewer
3. **Draft/production lifecycle:** How to manage iterative drafts with low-quality images, Speaker approval gate, single production pass
4. **Budget management:** Init BudgetTracker, track costs, report to Speaker, handle degradation states
5. **QA correction loop:** Max 2 autonomous cycles, then escalate. Reviewer feedback always goes to Speaker.
6. **Autonomous decisions:** Sequencing, draft quality tiers, provider routing, QA corrections 1-2
7. **Escalated decisions:** Budget confirmation, provider availability, draft approval, budget override, QA escalation after 2 cycles, ambiguous brief, reviewer structural concerns
8. **Prohibited actions:** Never generate content/images directly, never skip QA, never exceed budget without approval, never modify outputs — only re-invoke producing skill
9. **State management commands:** Python commands for init_pipeline, save_budget_snapshot, increment_qa_cycle, log_speaker_approval, pipeline_summary_markdown
10. **Skill invocation pattern:** Use `/skill-name` to invoke each skill in sequence

The agent should be comprehensive — this is the master orchestrator that a Speaker interacts with to produce a complete deck from a TalkBrief.

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/deck-conductor.md
git commit -m "feat: add deck-conductor agent — top-level pipeline orchestrator"
```

---

## Task 5: Full Test Suite + CLAUDE.md Update

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Run full test suite**

Run: `source .venv/bin/activate && python3 -m pytest tests/ -v`

Expected: All tests PASS.

- [ ] **Step 2: Update CLAUDE.md**

Add to implementation table:
```
| Conductor utils | `src/conductor.py` | N | Done |
```

Update Phase 6 status to "COMPLETE".

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with Phase 6 completion — all phases done"
```

---

### Critical Files for Implementation

- `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/agents/deck-conductor.md` — the agent definition: pipeline sequencing, draft/production lifecycle, budget management, QA loops, authority model
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/src/conductor.py` — thin utilities: pipeline state persistence, budget bridge, QA cycle tracking, approval logging
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/src/schemas/pipeline_state.schema.json` — extended with phase, draft_cycle, qa_correction_cycle, budget, available_providers, speaker_approvals
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/docs/architecture/ai-persona-summaries.md` — authoritative Deck Conductor persona specification
