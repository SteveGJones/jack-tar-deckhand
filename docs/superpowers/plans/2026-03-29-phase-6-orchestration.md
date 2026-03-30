# Phase 6: Orchestration -- Deck Conductor Agent (SUPERSEDED)

> **SUPERSEDED** by `docs/superpowers/plans/2026-03-29-phase-6-orchestration-v2.md`. Redesigned to reflect collaborative skill workflows and thin conductor utilities. This plan is retained for historical reference.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `deck-conductor` agent -- the top-level orchestrator that sequences the entire presentation engineering pipeline, manages the draft/production lifecycle, tracks cumulative cloud API cost, handles QA correction loops, and replaces the old `ollama-presentation` skill entirely.

**Architecture:** The deck-conductor is a Claude Code agent (`.claude/agents/deck-conductor.md`) with hybrid authority (autonomous at >= 0.8 confidence, escalates to Speaker below). It never generates content directly -- it always delegates to L1 skills. A supporting Python module (`src/conductor.py`) provides budget tracking, cost reporting, and QA finding routing utilities that the agent invokes via `Bash(python ...)`. The PipelineState schema is extended with fields for draft/production mode, budget, cycle counts, and available providers.

**Tech Stack:** Python 3.8+, jsonschema, pytest (same as Phase 1)

**Prerequisites:** Phase 1 (Foundation) must be implemented first. Phases 2-5 should be implemented but the conductor can be tested with mocked skill outputs using the fixtures from Phase 1.

**Phases overview (this is Phase 6 of 6):**
- Phase 1: Foundation -- DeckContext, schemas, utilities
- Phase 2: Design Services -- `slide-stylist`
- Phase 3: Content Services -- `narrative-architect`, `speaker-notes-writer`
- Phase 4: Image Services -- 8 skills + 1 agent
- Phase 5: Assembly & QA -- `deck-assembler`, `deck-qa`, `presentation-reviewer`
- **Phase 6: Orchestration** (this plan) -- `deck-conductor`

---

## File Structure

```
research/
  synthesis-deck-conductor.md         # Research synthesis (prerequisite)
src/
  conductor.py                        # Budget tracking, cost reporting, QA routing
  schemas/
    pipeline_state.schema.json        # Extended with mode, budget, cycle fields
tests/
  test_conductor.py                   # Tests for conductor utilities
  test_pipeline_state_extended.py     # Tests for extended PipelineState schema
  fixtures/
    valid_pipeline_state_extended.json # Extended PipelineState fixture
.claude/
  agents/
    deck-conductor.md                 # The agent definition (primary deliverable)
```

---

## Task 1: Research Synthesis Document

**Files:**
- Create: `research/synthesis-deck-conductor.md`

- [ ] **Step 1: Write the research synthesis**

Create `research/synthesis-deck-conductor.md`:

```markdown
# Research Synthesis: Deck Conductor

> Synthesised from: Research #05 (Multi-Model Routing Pipeline), #12 (DeckContext State Management), #13 (Cost Optimisation & Caching)
> Date: 2026-03-29
> Purpose: Consolidated design decisions for the deck-conductor agent implementation

---

## 1. Pipeline Sequencing (from Research #12)

The conductor follows a fixed dependency order with two modes:

### Draft Cycle (iterative, Speaker reviews each cycle)

1. validate-brief -- parse TalkBrief, validate schema, write to DeckContext
2. slide-stylist -- derive StyleGuide from TalkBrief + optional brand assets
3. narrative-architect -- produce SlideOutline from TalkBrief + StyleGuide
4. speaker-notes-writer -- generate SpeakerNotes from SlideOutline + TalkBrief
5. imagegen-bridge -- generate ImageManifest at draft quality (Ollama or reduced cloud)
6. chart-renderer -- render ChartManifest if include_charts is true
7. deck-assembler -- build draft .pptx
8. Speaker reviews draft, gives feedback, conductor re-runs affected steps

### Production Phase (single pass after Speaker approves draft)

1. imagegen-bridge -- re-render all images at full quality
2. deck-assembler -- rebuild .pptx with production images
3. deck-qa -- automated QA (25 anti-pattern checks)
4. QA correction loop (max 2 cycles): re-invoke producing service
5. presentation-reviewer -- structured review
6. Deliver: .pptx + QAReport + review + cost report

### Step Dependencies (from Research #12, Section 5)

- slide-stylist requires: talk-brief.json
- narrative-architect requires: talk-brief.json, style-guide.json
- speaker-notes-writer requires: talk-brief.json, outline.json
- imagegen-bridge requires: outline.json, style-guide.json
- chart-renderer requires: outline.json, style-guide.json, talk-brief.json (data_sources)
- deck-assembler requires: outline.json, style-guide.json, image-manifest.json, chart-manifest.json, speaker-notes.json
- deck-qa requires: output/presentation.pptx
- presentation-reviewer requires: presentation.pptx, outline.json, style-guide.json, speaker-notes.json, talk-brief.json

## 2. Budget Management (from Research #13)

### Budget State Machine

Four degradation states based on percentage of budget spent:
- ALLOW (0-70%): Full multi-model routing
- ALLOW_WITH_CAPS (70-90%): Switch heroes to Imagen 4 Fast, skip decorative images
- DEGRADE (90-100%): All remaining images via Ollama
- TYPOGRAPHY_ONLY (100%+): No image generation, shapes and typography only

### Cost Tracking

The conductor maintains a per-session cost ledger because no cloud provider offers real-time per-session spending caps. Each image generation call logs: model, cost, cumulative total, budget state.

### Cost Reporting at Review Points

At each Speaker review point, the conductor reports:
- Running total spend (USD)
- Budget remaining (USD)
- Budget state (ALLOW/CAPS/DEGRADE/TYPOGRAPHY_ONLY)
- Estimated cost to complete remaining work
- Cache hit rate

### Per-Deck Cost Report (from Research #13, Section 7.2)

Final delivery includes a DeckCostReport with: total cost, image cost, orchestration cost, cache savings, generation time, cost per slide, quality tier.

## 3. QA Correction Routing (from Research #12, Section 8.3)

The conductor maps QA finding categories to the upstream service that should fix them:

| Category | Error Action | Warning Action |
|---|---|---|
| overlap | Re-invoke deck-assembler with adjusted layout | Log, continue |
| contrast | Re-invoke slide-stylist to adjust palette, then re-assemble | Log, continue |
| text_overflow | Re-invoke narrative-architect to shorten body_points, then re-assemble | Re-invoke deck-assembler with smaller font |
| image_quality | Re-invoke imagegen-bridge for affected slides | Log, continue |
| placeholder_residue | Re-invoke deck-assembler | Log, continue |
| margin | Re-invoke deck-assembler with adjusted positions | Log, continue |
| consistency | Re-invoke deck-assembler | Log, continue |
| missing_content | Re-invoke producing service (narrative-architect or speaker-notes-writer) | Log, continue |
| accessibility | Re-invoke deck-assembler | Log, continue |

Maximum 2 QA correction cycles. After 2 failures, deliver best effort with outstanding issues noted.

## 4. Escalation Triggers (from Architecture Spec)

1. Budget will be exceeded by next generation request
2. QA finds critical issues after 2 correction cycles
3. No image generation providers available
4. Reviewer identifies structural narrative problems requiring Speaker input
5. Talk brief is ambiguous or missing required fields

## 5. Draft/Production Mode Switching (from Architecture Overview)

Key insight: image prompts are model-specific. A prompt tuned for Ollama flux2-klein produces different results on GPT Image 1.5.

- Early drafts: Ollama for composition/layout testing (free)
- Later drafts: target cloud provider at reduced quality (cheap, but prompt-accurate)
- Production: full quality on approved provider

The conductor tracks which mode the pipeline is in via the extended PipelineState.

## 6. Provider Discovery (from Architecture Overview, Research #05)

At pipeline start, the conductor invokes imagegen-bridge in probe mode to build the AvailableProviders manifest. The conductor then presents capabilities and cost estimates to the Speaker before proceeding.

Provider detection:
- Ollama: HTTP health check to localhost:11434
- OpenAI: OPENAI_API_KEY env var
- Google Vertex AI: GOOGLE_CLOUD_PROJECT env var
- FAL.ai: FAL_KEY env var
- Recraft: RECRAFT_API_KEY env var
```

- [ ] **Step 2: Commit**

```bash
git add research/synthesis-deck-conductor.md
git commit -m "docs: add deck-conductor research synthesis from papers 05, 12, 13"
```

---

## Task 2: Extend PipelineState Schema

**Files:**
- Modify: `src/schemas/pipeline_state.schema.json`
- Create: `tests/fixtures/valid_pipeline_state_extended.json`
- Create: `tests/test_pipeline_state_extended.py`

- [ ] **Step 1: Write the extended PipelineState tests**

Create `tests/test_pipeline_state_extended.py`:

```python
"""Tests for extended PipelineState schema with conductor fields."""

import json
import os
import pytest
from jsonschema import validate, ValidationError

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'schemas')
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def load_schema(name):
    path = os.path.join(SCHEMA_DIR, f'{name}.schema.json')
    with open(path) as f:
        return json.load(f)


def load_fixture(name):
    path = os.path.join(FIXTURE_DIR, f'{name}.json')
    with open(path) as f:
        return json.load(f)


class TestExtendedPipelineState:
    @pytest.fixture
    def schema(self):
        return load_schema('pipeline_state')

    def test_valid_extended_state(self, schema):
        state = load_fixture('valid_pipeline_state_extended')
        validate(instance=state, schema=schema)

    def test_mode_accepts_draft(self, schema):
        state = {
            "pipeline_id": "test",
            "created_at": "2026-03-29T12:00:00Z",
            "mode": "draft",
            "steps": {}
        }
        validate(instance=state, schema=schema)

    def test_mode_accepts_production(self, schema):
        state = {
            "pipeline_id": "test",
            "created_at": "2026-03-29T12:00:00Z",
            "mode": "production",
            "steps": {}
        }
        validate(instance=state, schema=schema)

    def test_invalid_mode_fails(self, schema):
        state = {
            "pipeline_id": "test",
            "created_at": "2026-03-29T12:00:00Z",
            "mode": "turbo",
            "steps": {}
        }
        with pytest.raises(ValidationError):
            validate(instance=state, schema=schema)

    def test_budget_fields_validate(self, schema):
        state = {
            "pipeline_id": "test",
            "created_at": "2026-03-29T12:00:00Z",
            "steps": {},
            "budget": {
                "total_budget_usd": 2.00,
                "spent_usd": 0.45,
                "budget_state": "allow"
            }
        }
        validate(instance=state, schema=schema)

    def test_invalid_budget_state_fails(self, schema):
        state = {
            "pipeline_id": "test",
            "created_at": "2026-03-29T12:00:00Z",
            "steps": {},
            "budget": {
                "total_budget_usd": 2.00,
                "spent_usd": 0.45,
                "budget_state": "turbo"
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=state, schema=schema)

    def test_cycle_counts_validate(self, schema):
        state = {
            "pipeline_id": "test",
            "created_at": "2026-03-29T12:00:00Z",
            "steps": {},
            "draft_cycle_count": 2,
            "qa_cycle_count": 1
        }
        validate(instance=state, schema=schema)

    def test_available_providers_validate(self, schema):
        state = {
            "pipeline_id": "test",
            "created_at": "2026-03-29T12:00:00Z",
            "steps": {},
            "available_providers": {
                "ollama": {"available": True, "models": ["x/z-image-turbo"]},
                "openai": {"available": False}
            }
        }
        validate(instance=state, schema=schema)

    def test_backward_compatible_minimal_state(self, schema):
        """Phase 1 minimal PipelineState still validates."""
        state = {
            "pipeline_id": "2026-03-29T12:00:00Z",
            "created_at": "2026-03-29T12:00:00Z",
            "status": "running",
            "steps": {
                "validate-brief": {"status": "completed"}
            }
        }
        validate(instance=state, schema=schema)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_pipeline_state_extended.py -v`

Expected: FAIL -- missing fixture, and schema does not yet have extended fields.

- [ ] **Step 3: Create the extended fixture**

Create `tests/fixtures/valid_pipeline_state_extended.json`:

```json
{
  "pipeline_id": "2026-03-29T14:00:00Z",
  "created_at": "2026-03-29T14:00:00Z",
  "updated_at": "2026-03-29T14:25:00Z",
  "status": "running",
  "mode": "draft",
  "current_step": "imagegen-bridge",
  "draft_cycle_count": 1,
  "qa_cycle_count": 0,
  "budget": {
    "total_budget_usd": 2.00,
    "spent_usd": 0.45,
    "budget_state": "allow",
    "api_calls": [
      {
        "model": "imagen-4-fast",
        "cost_usd": 0.02,
        "cumulative_usd": 0.02,
        "timestamp": "2026-03-29T14:10:00Z",
        "image_id": "slide-01-bg"
      },
      {
        "model": "recraft-v4-svg",
        "cost_usd": 0.08,
        "cumulative_usd": 0.10,
        "timestamp": "2026-03-29T14:11:00Z",
        "image_id": "slide-03-icon-1"
      }
    ],
    "cache_hits": 2,
    "cache_savings_usd": 0.10
  },
  "available_providers": {
    "ollama": {
      "available": true,
      "models": ["x/z-image-turbo", "x/flux2-klein"],
      "endpoint": "http://localhost:11434"
    },
    "openai": {
      "available": true,
      "model": "gpt-image-1.5"
    },
    "google_vertex": {
      "available": true,
      "model": "imagen-4"
    },
    "fal": {
      "available": true,
      "models": ["flux-2-pro", "recraft-v4", "ideogram-3"]
    },
    "recraft": {
      "available": false
    }
  },
  "steps": {
    "validate-brief": {
      "status": "completed",
      "started_at": "2026-03-29T14:00:01Z",
      "completed_at": "2026-03-29T14:00:02Z",
      "output_file": "talk-brief.json",
      "checksum": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    },
    "slide-stylist": {
      "status": "completed",
      "started_at": "2026-03-29T14:00:03Z",
      "completed_at": "2026-03-29T14:02:00Z",
      "output_file": "style-guide.json"
    },
    "narrative-architect": {
      "status": "completed",
      "started_at": "2026-03-29T14:02:01Z",
      "completed_at": "2026-03-29T14:05:00Z",
      "output_file": "outline.json"
    },
    "speaker-notes-writer": {
      "status": "completed",
      "started_at": "2026-03-29T14:05:01Z",
      "completed_at": "2026-03-29T14:08:00Z",
      "output_file": "speaker-notes.json"
    },
    "imagegen-bridge": {
      "status": "running",
      "started_at": "2026-03-29T14:08:01Z"
    },
    "chart-renderer": {
      "status": "pending"
    },
    "deck-assembler": {
      "status": "pending"
    },
    "deck-qa": {
      "status": "pending"
    }
  },
  "step_order": [
    "validate-brief",
    "slide-stylist",
    "narrative-architect",
    "speaker-notes-writer",
    "imagegen-bridge",
    "chart-renderer",
    "deck-assembler",
    "deck-qa"
  ]
}
```

- [ ] **Step 4: Extend the PipelineState schema**

Replace `src/schemas/pipeline_state.schema.json` with:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/pipeline-state.json",
  "title": "PipelineState",
  "description": "Pipeline execution metadata, step tracking, budget, and mode. Extended in Phase 6 with conductor fields.",
  "type": "object",
  "required": ["pipeline_id", "created_at", "steps"],
  "properties": {
    "pipeline_id": {"type": "string"},
    "created_at": {"type": "string"},
    "updated_at": {"type": "string"},
    "talk_brief_hash": {"type": "string"},
    "status": {
      "type": "string",
      "enum": ["running", "completed", "failed", "paused"]
    },
    "mode": {
      "type": "string",
      "enum": ["draft", "production"],
      "description": "Whether the pipeline is in draft (iterative) or production (final render) mode."
    },
    "current_step": {"type": "string"},
    "draft_cycle_count": {
      "type": "integer",
      "minimum": 0,
      "description": "Number of draft review cycles completed."
    },
    "qa_cycle_count": {
      "type": "integer",
      "minimum": 0,
      "maximum": 2,
      "description": "Number of QA correction cycles in current phase. Max 2."
    },
    "budget": {
      "type": "object",
      "description": "Cumulative cloud API cost tracking across all cycles.",
      "properties": {
        "total_budget_usd": {
          "type": "number",
          "minimum": 0,
          "description": "Speaker-declared budget cap in USD."
        },
        "spent_usd": {
          "type": "number",
          "minimum": 0,
          "description": "Cumulative spend in USD across all draft and production cycles."
        },
        "budget_state": {
          "type": "string",
          "enum": ["allow", "allow_with_caps", "degrade", "typography_only"],
          "description": "Current budget degradation state."
        },
        "api_calls": {
          "type": "array",
          "description": "Ledger of all cloud API calls with cost.",
          "items": {
            "type": "object",
            "properties": {
              "model": {"type": "string"},
              "cost_usd": {"type": "number"},
              "cumulative_usd": {"type": "number"},
              "timestamp": {"type": "string"},
              "image_id": {"type": "string"}
            }
          }
        },
        "cache_hits": {
          "type": "integer",
          "minimum": 0
        },
        "cache_savings_usd": {
          "type": "number",
          "minimum": 0
        }
      }
    },
    "available_providers": {
      "type": "object",
      "description": "Provider discovery results from imagegen-bridge probe.",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "available": {"type": "boolean"},
          "models": {
            "type": "array",
            "items": {"type": "string"}
          },
          "model": {"type": "string"},
          "endpoint": {"type": "string"}
        }
      }
    },
    "steps": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["status"],
        "properties": {
          "status": {
            "type": "string",
            "enum": ["pending", "running", "completed", "failed", "skipped"]
          },
          "started_at": {"type": "string"},
          "completed_at": {"type": "string"},
          "output_file": {"type": "string"},
          "error": {"type": "string"},
          "retry_count": {"type": "integer"},
          "checksum": {"type": "string"}
        }
      }
    },
    "step_order": {
      "type": "array",
      "items": {"type": "string"}
    }
  }
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_pipeline_state_extended.py -v`

Expected: All 9 tests PASS.

- [ ] **Step 6: Run the full test suite to verify backward compatibility**

Run: `source .venv/bin/activate && python3 -m pytest tests/ -v`

Expected: All existing tests still PASS (schema extension is backward-compatible).

- [ ] **Step 7: Commit**

```bash
git add src/schemas/pipeline_state.schema.json tests/test_pipeline_state_extended.py tests/fixtures/valid_pipeline_state_extended.json
git commit -m "feat: extend PipelineState schema with mode, budget, cycle count, and provider fields"
```

---

## Task 3: Conductor Utilities Module

**Files:**
- Create: `src/conductor.py`
- Create: `tests/test_conductor.py`

- [ ] **Step 1: Write the conductor utility tests**

Create `tests/test_conductor.py`:

```python
"""Tests for deck-conductor utility functions: budget, cost report, QA routing."""

import json
import os
import shutil
import pytest

DECK_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'test-deck-conductor')


@pytest.fixture(autouse=True)
def clean_deck_dir():
    if os.path.exists(DECK_DIR):
        shutil.rmtree(DECK_DIR)
    yield
    if os.path.exists(DECK_DIR):
        shutil.rmtree(DECK_DIR)


class TestDeckBudget:
    def test_initial_state_is_allow(self):
        from src.conductor import DeckBudget
        budget = DeckBudget(total_budget=2.00)
        assert budget.state == 'allow'
        assert budget.remaining == 2.00
        assert budget.utilisation == 0.0

    def test_spending_updates_state(self):
        from src.conductor import DeckBudget
        budget = DeckBudget(total_budget=2.00)
        budget.log_api_call('imagen-4-fast', 0.02, 'slide-01-bg')
        assert budget.spent == 0.02
        assert budget.remaining == 1.98
        assert budget.state == 'allow'

    def test_allow_with_caps_at_70_percent(self):
        from src.conductor import DeckBudget
        budget = DeckBudget(total_budget=1.00)
        budget.log_api_call('flux-2-pro', 0.71, 'slide-01-hero')
        assert budget.state == 'allow_with_caps'

    def test_degrade_at_90_percent(self):
        from src.conductor import DeckBudget
        budget = DeckBudget(total_budget=1.00)
        budget.log_api_call('gpt-image-1.5', 0.91, 'slide-01-hero')
        assert budget.state == 'degrade'

    def test_typography_only_at_100_percent(self):
        from src.conductor import DeckBudget
        budget = DeckBudget(total_budget=1.00)
        budget.log_api_call('gpt-image-1.5', 1.01, 'slide-01-hero')
        assert budget.state == 'typography_only'

    def test_can_spend_checks_budget(self):
        from src.conductor import DeckBudget
        budget = DeckBudget(total_budget=1.00)
        assert budget.can_spend(0.50) is True
        budget.log_api_call('test', 0.80, 'test-img')
        assert budget.can_spend(0.50) is False
        assert budget.can_spend(0.20) is True

    def test_log_cache_hit(self):
        from src.conductor import DeckBudget
        budget = DeckBudget(total_budget=2.00)
        budget.log_cache_hit('cache-key-1', 0.08)
        assert budget.cache_hits == 1
        assert budget.cache_savings_usd == 0.08
        assert budget.spent == 0.0

    def test_zero_budget_is_typography_only(self):
        from src.conductor import DeckBudget
        budget = DeckBudget(total_budget=0.0)
        assert budget.state == 'typography_only'

    def test_to_dict_roundtrips(self):
        from src.conductor import DeckBudget
        budget = DeckBudget(total_budget=2.00)
        budget.log_api_call('test', 0.10, 'img-1')
        budget.log_cache_hit('key-1', 0.05)
        d = budget.to_dict()
        assert d['total_budget_usd'] == 2.00
        assert d['spent_usd'] == 0.10
        assert d['budget_state'] == 'allow'
        assert len(d['api_calls']) == 1
        assert d['cache_hits'] == 1
        assert d['cache_savings_usd'] == 0.05

    def test_cost_summary_markdown(self):
        from src.conductor import DeckBudget
        budget = DeckBudget(total_budget=2.00)
        budget.log_api_call('imagen-4-fast', 0.02, 'slide-01-bg')
        budget.log_api_call('recraft-v4-svg', 0.08, 'slide-03-icon')
        budget.log_cache_hit('key-1', 0.08)
        md = budget.cost_summary_markdown()
        assert '$0.10' in md
        assert '$1.90' in md
        assert 'allow' in md.lower()


class TestQARouting:
    def test_route_error_findings(self):
        from src.conductor import route_qa_findings
        findings = [
            {"slide_number": 5, "severity": "error", "category": "overlap",
             "description": "Text overlaps image"},
            {"slide_number": 7, "severity": "error", "category": "image_quality",
             "description": "Image is blurry"},
        ]
        routes = route_qa_findings(findings)
        assert len(routes) == 2
        assert routes[0]['target_service'] == 'deck-assembler'
        assert routes[1]['target_service'] == 'imagegen-bridge'

    def test_route_warning_findings(self):
        from src.conductor import route_qa_findings
        findings = [
            {"slide_number": 3, "severity": "warning", "category": "contrast",
             "description": "Low contrast"},
        ]
        routes = route_qa_findings(findings)
        assert len(routes) == 1
        assert routes[0]['action'] == 'log'

    def test_route_info_findings_are_logged(self):
        from src.conductor import route_qa_findings
        findings = [
            {"slide_number": 1, "severity": "info", "category": "consistency",
             "description": "Minor font size difference"},
        ]
        routes = route_qa_findings(findings)
        assert len(routes) == 1
        assert routes[0]['action'] == 'log'

    def test_empty_findings_returns_empty(self):
        from src.conductor import route_qa_findings
        routes = route_qa_findings([])
        assert routes == []

    def test_has_blocking_errors(self):
        from src.conductor import has_blocking_errors
        findings_with_errors = [
            {"slide_number": 5, "severity": "error", "category": "overlap",
             "description": "Text overlaps image"},
        ]
        findings_without_errors = [
            {"slide_number": 3, "severity": "warning", "category": "contrast",
             "description": "Low contrast"},
        ]
        assert has_blocking_errors(findings_with_errors) is True
        assert has_blocking_errors(findings_without_errors) is False
        assert has_blocking_errors([]) is False


class TestConductorStateHelpers:
    def test_init_conductor_state(self):
        from src.deckcontext import init_deck, read_contract
        from src.conductor import init_conductor_state
        init_deck(DECK_DIR)
        init_conductor_state(DECK_DIR, total_budget_usd=2.00)
        state = read_contract(DECK_DIR, 'pipeline-state')
        assert state['mode'] == 'draft'
        assert state['draft_cycle_count'] == 0
        assert state['qa_cycle_count'] == 0
        assert state['budget']['total_budget_usd'] == 2.00
        assert state['budget']['spent_usd'] == 0.0
        assert state['budget']['budget_state'] == 'allow'

    def test_switch_to_production(self):
        from src.deckcontext import init_deck, read_contract
        from src.conductor import init_conductor_state, switch_to_production
        init_deck(DECK_DIR)
        init_conductor_state(DECK_DIR, total_budget_usd=2.00)
        switch_to_production(DECK_DIR)
        state = read_contract(DECK_DIR, 'pipeline-state')
        assert state['mode'] == 'production'
        assert state['qa_cycle_count'] == 0

    def test_increment_draft_cycle(self):
        from src.deckcontext import init_deck, read_contract
        from src.conductor import init_conductor_state, increment_draft_cycle
        init_deck(DECK_DIR)
        init_conductor_state(DECK_DIR, total_budget_usd=2.00)
        increment_draft_cycle(DECK_DIR)
        state = read_contract(DECK_DIR, 'pipeline-state')
        assert state['draft_cycle_count'] == 1

    def test_increment_qa_cycle(self):
        from src.deckcontext import init_deck, read_contract
        from src.conductor import init_conductor_state, increment_qa_cycle
        init_deck(DECK_DIR)
        init_conductor_state(DECK_DIR, total_budget_usd=2.00)
        count = increment_qa_cycle(DECK_DIR)
        assert count == 1
        count = increment_qa_cycle(DECK_DIR)
        assert count == 2

    def test_save_budget_to_state(self):
        from src.deckcontext import init_deck, read_contract
        from src.conductor import DeckBudget, init_conductor_state, save_budget
        init_deck(DECK_DIR)
        init_conductor_state(DECK_DIR, total_budget_usd=2.00)
        budget = DeckBudget(total_budget=2.00)
        budget.log_api_call('test-model', 0.15, 'slide-01-hero')
        save_budget(DECK_DIR, budget)
        state = read_contract(DECK_DIR, 'pipeline-state')
        assert state['budget']['spent_usd'] == 0.15
        assert len(state['budget']['api_calls']) == 1

    def test_save_available_providers(self):
        from src.deckcontext import init_deck, read_contract
        from src.conductor import init_conductor_state, save_providers
        init_deck(DECK_DIR)
        init_conductor_state(DECK_DIR, total_budget_usd=2.00)
        providers = {
            "ollama": {"available": True, "models": ["x/z-image-turbo"]},
            "openai": {"available": False}
        }
        save_providers(DECK_DIR, providers)
        state = read_contract(DECK_DIR, 'pipeline-state')
        assert state['available_providers']['ollama']['available'] is True
        assert state['available_providers']['openai']['available'] is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_conductor.py -v`

Expected: FAIL -- `src.conductor` module not found.

- [ ] **Step 3: Implement the conductor utilities module**

Create `src/conductor.py`:

```python
"""Deck Conductor utilities -- budget tracking, cost reporting, QA routing.

These functions are called by the deck-conductor agent via Bash(python ...)
during pipeline orchestration. They operate on the DeckContext state files.
"""

import json
import os
from datetime import datetime, timezone

from src.deckcontext import read_contract, write_contract


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Budget tracking
# ---------------------------------------------------------------------------

class DeckBudget:
    """Per-session budget tracker with graceful degradation.

    Implements the four-state budget state machine from Research #13:
    ALLOW (0-70%) -> ALLOW_WITH_CAPS (70-90%) -> DEGRADE (90-100%) -> TYPOGRAPHY_ONLY (100%+)
    """

    def __init__(self, total_budget):
        self.total_budget = total_budget
        self.spent = 0.0
        self.api_calls = []
        self.cache_hits = 0
        self.cache_savings_usd = 0.0

    @property
    def remaining(self):
        return max(0.0, self.total_budget - self.spent)

    @property
    def utilisation(self):
        if self.total_budget <= 0:
            return 1.0
        return self.spent / self.total_budget

    @property
    def state(self):
        if self.utilisation >= 1.0:
            return 'typography_only'
        elif self.utilisation >= 0.9:
            return 'degrade'
        elif self.utilisation >= 0.7:
            return 'allow_with_caps'
        return 'allow'

    def can_spend(self, amount):
        """Check if spending this amount stays within budget."""
        return self.spent + amount <= self.total_budget

    def log_api_call(self, model, cost_usd, image_id):
        """Record a cloud API call and its cost."""
        self.spent += cost_usd
        self.api_calls.append({
            'model': model,
            'cost_usd': cost_usd,
            'cumulative_usd': self.spent,
            'timestamp': _now_iso(),
            'image_id': image_id,
        })

    def log_cache_hit(self, cache_key, saved_usd):
        """Record a cache hit and the cost it saved."""
        self.cache_hits += 1
        self.cache_savings_usd += saved_usd

    def to_dict(self):
        """Serialize budget state for PipelineState."""
        return {
            'total_budget_usd': self.total_budget,
            'spent_usd': self.spent,
            'budget_state': self.state,
            'api_calls': self.api_calls,
            'cache_hits': self.cache_hits,
            'cache_savings_usd': self.cache_savings_usd,
        }

    def cost_summary_markdown(self):
        """Generate a Markdown cost summary for Speaker review points."""
        lines = [
            '## Cost Summary',
            '',
            '| Metric | Value |',
            '|---|---|',
            f'| Budget | ${self.total_budget:.2f} |',
            f'| Spent | ${self.spent:.2f} |',
            f'| Remaining | ${self.remaining:.2f} |',
            f'| Budget state | {self.state} |',
            f'| API calls | {len(self.api_calls)} |',
            f'| Cache hits | {self.cache_hits} |',
            f'| Cache savings | ${self.cache_savings_usd:.2f} |',
        ]
        if self.api_calls:
            lines.append('')
            lines.append('### API Call Ledger')
            lines.append('')
            lines.append('| Model | Cost | Cumulative | Image |')
            lines.append('|---|---|---|---|')
            for call in self.api_calls:
                lines.append(
                    f'| {call["model"]} '
                    f'| ${call["cost_usd"]:.3f} '
                    f'| ${call["cumulative_usd"]:.3f} '
                    f'| {call["image_id"]} |'
                )
        return '\n'.join(lines)


# ---------------------------------------------------------------------------
# QA finding routing
# ---------------------------------------------------------------------------

# Maps QA finding category -> target service for error-severity findings
_ERROR_ROUTE_MAP = {
    'overlap': 'deck-assembler',
    'contrast': 'slide-stylist',
    'text_overflow': 'narrative-architect',
    'image_quality': 'imagegen-bridge',
    'placeholder_residue': 'deck-assembler',
    'margin': 'deck-assembler',
    'consistency': 'deck-assembler',
    'missing_content': 'narrative-architect',
    'accessibility': 'deck-assembler',
}


def route_qa_findings(findings):
    """Route QA findings to the upstream service responsible for fixing them.

    Args:
        findings: List of QA finding dicts from qa-report.json.

    Returns:
        List of routing dicts with: slide_number, category, severity,
        description, target_service, action ('reinvoke' or 'log').
    """
    routes = []
    for finding in findings:
        severity = finding.get('severity', 'info')
        category = finding.get('category', '')

        if severity == 'error':
            target = _ERROR_ROUTE_MAP.get(category, 'deck-assembler')
            routes.append({
                'slide_number': finding.get('slide_number'),
                'category': category,
                'severity': severity,
                'description': finding.get('description', ''),
                'target_service': target,
                'action': 'reinvoke',
            })
        else:
            routes.append({
                'slide_number': finding.get('slide_number'),
                'category': category,
                'severity': severity,
                'description': finding.get('description', ''),
                'target_service': None,
                'action': 'log',
            })
    return routes


def has_blocking_errors(findings):
    """Check whether QA findings contain any error-severity issues."""
    return any(f.get('severity') == 'error' for f in findings)


# ---------------------------------------------------------------------------
# Conductor state helpers (operate on pipeline-state.json)
# ---------------------------------------------------------------------------

def init_conductor_state(deck_dir, total_budget_usd):
    """Extend the PipelineState with conductor-specific fields.

    Call this after init_deck() to add mode, budget, and cycle tracking.
    """
    state = read_contract(deck_dir, 'pipeline-state')
    if state is None:
        raise FileNotFoundError(f'pipeline-state.json not found in {deck_dir}')

    state['mode'] = 'draft'
    state['draft_cycle_count'] = 0
    state['qa_cycle_count'] = 0
    state['budget'] = {
        'total_budget_usd': total_budget_usd,
        'spent_usd': 0.0,
        'budget_state': 'allow',
        'api_calls': [],
        'cache_hits': 0,
        'cache_savings_usd': 0.0,
    }
    state['available_providers'] = {}
    state['updated_at'] = _now_iso()

    write_contract(deck_dir, 'pipeline-state', state, validate=False)


def switch_to_production(deck_dir):
    """Switch the pipeline from draft mode to production mode."""
    state = read_contract(deck_dir, 'pipeline-state')
    state['mode'] = 'production'
    state['qa_cycle_count'] = 0
    state['updated_at'] = _now_iso()
    write_contract(deck_dir, 'pipeline-state', state, validate=False)


def increment_draft_cycle(deck_dir):
    """Increment the draft cycle counter. Returns the new count."""
    state = read_contract(deck_dir, 'pipeline-state')
    state['draft_cycle_count'] = state.get('draft_cycle_count', 0) + 1
    state['updated_at'] = _now_iso()
    write_contract(deck_dir, 'pipeline-state', state, validate=False)
    return state['draft_cycle_count']


def increment_qa_cycle(deck_dir):
    """Increment the QA cycle counter. Returns the new count."""
    state = read_contract(deck_dir, 'pipeline-state')
    state['qa_cycle_count'] = state.get('qa_cycle_count', 0) + 1
    state['updated_at'] = _now_iso()
    write_contract(deck_dir, 'pipeline-state', state, validate=False)
    return state['qa_cycle_count']


def save_budget(deck_dir, budget):
    """Persist the current DeckBudget state to pipeline-state.json."""
    state = read_contract(deck_dir, 'pipeline-state')
    state['budget'] = budget.to_dict()
    state['updated_at'] = _now_iso()
    write_contract(deck_dir, 'pipeline-state', state, validate=False)


def save_providers(deck_dir, providers):
    """Save the AvailableProviders manifest to pipeline-state.json."""
    state = read_contract(deck_dir, 'pipeline-state')
    state['available_providers'] = providers
    state['updated_at'] = _now_iso()
    write_contract(deck_dir, 'pipeline-state', state, validate=False)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_conductor.py -v`

Expected: All 21 tests PASS.

- [ ] **Step 5: Run the full test suite**

Run: `source .venv/bin/activate && python3 -m pytest tests/ -v`

Expected: All tests PASS across all test files.

- [ ] **Step 6: Commit**

```bash
git add src/conductor.py tests/test_conductor.py
git commit -m "feat: add conductor utilities — budget tracking, QA routing, state helpers"
```

---

## Task 4: Deck Conductor Agent Definition

**Files:**
- Create: `.claude/agents/deck-conductor.md`

This is the primary deliverable of Phase 6 -- the complete agent definition that replaces the old `ollama-presentation` skill.

- [ ] **Step 1: Create the agent definition**

Create `.claude/agents/deck-conductor.md`:

```markdown
---
name: deck-conductor
description: Top-level orchestrator for the Jack-Tar Deckhand presentation engineering pipeline. Sequences all L1 services, manages draft/production lifecycle, tracks cloud API budget, and handles QA correction loops. Replaces the old ollama-presentation skill.
---

# Deck Conductor

You are the Deck Conductor -- the top-level orchestration agent for Jack-Tar Deckhand. You sequence the entire presentation engineering pipeline from talk brief to finished .pptx. You NEVER generate content, images, or style decisions directly. You ALWAYS delegate to the appropriate L1 service skill.

## Authority Model

**Hybrid authority:** Act autonomously for routine pipeline decisions (confidence >= 0.8). Escalate to the Speaker for ambiguous, high-cost, or creative decisions (confidence < 0.8).

## Core Principles

1. **Delegate, never create.** You invoke skills. You do not write slide content, generate images, or make design choices.
2. **Budget is sacred.** Track every cloud API dollar. Report running cost at every review point. Never exceed the declared cap without Speaker approval.
3. **State lives on disk.** The DeckContext (`./tmp/deck/`) is the source of truth. Conversation context is a convenience cache.
4. **QA is mandatory.** Never skip the QA step. Never deliver without running deck-qa.
5. **Correction loops are bounded.** Maximum 2 QA correction cycles. After 2, deliver best effort with outstanding issues noted.
6. **Provider discovery before spending.** Never proceed past provider discovery without confirming capabilities and cost to the Speaker.

## Prohibited Actions

- Must NOT generate content, images, or style decisions directly
- Must NOT spend above the declared budget cap without Speaker approval
- Must NOT skip the QA step
- Must NOT modify generated artefacts -- only re-invoke the producing service with corrective instructions
- Must NOT proceed past provider discovery without confirming to the Speaker

## Escalation Triggers

Escalate to the Speaker when:
1. The next generation request would exceed the remaining budget
2. QA finds critical issues (errors) after 2 correction cycles
3. No image generation providers are available
4. The Presentation Reviewer identifies structural narrative problems requiring Speaker direction
5. The talk brief is ambiguous or missing required fields (topic, audience, duration_minutes)

---

## Pipeline Execution

### Phase 0: Initialise

1. **Parse the Speaker's request.** Extract topic, audience, duration, tone, preferences, branding, data sources. If the Speaker provides conversational input, structure it into TalkBrief fields.

2. **Validate the TalkBrief.** Run:
   ```bash
   python3 -c "
   from src.deckcontext import init_deck, write_contract
   import json, sys
   brief = json.loads(sys.argv[1])
   init_deck('./tmp/deck')
   write_contract('./tmp/deck', 'talk-brief', brief)
   print('TalkBrief validated and written to ./tmp/deck/talk-brief.json')
   " '$TALK_BRIEF_JSON'
   ```
   If validation fails, tell the Speaker which fields are missing or invalid and ask them to provide the information.

3. **Initialise conductor state.** Ask the Speaker for their budget cap in USD (suggest $2.00 as a reasonable default for a standard deck). Then run:
   ```bash
   python3 -c "
   from src.deckcontext import init_deck
   from src.conductor import init_conductor_state
   init_deck('./tmp/deck')
   init_conductor_state('./tmp/deck', total_budget_usd=$BUDGET)
   print('Conductor state initialised: draft mode, budget \$$BUDGET')
   "
   ```

4. **Provider discovery.** Invoke the `imagegen-bridge` skill in probe mode to discover available providers. Save the results:
   ```bash
   python3 -c "
   from src.conductor import save_providers
   import json
   providers = json.loads('$PROVIDERS_JSON')
   save_providers('./tmp/deck', providers)
   print('Available providers saved to pipeline state')
   "
   ```

5. **Present to Speaker.** Show the Speaker:
   - Available image generation providers (Ollama, cloud APIs)
   - Estimated cost for this deck (Draft: ~$0.16, Standard: ~$1.95, Premium: ~$9.26)
   - Budget cap and degradation thresholds
   - Ask for confirmation before proceeding

   **Do NOT proceed without Speaker confirmation.**

### Phase 1: Draft Cycle

Each draft cycle runs the full pipeline to produce a reviewable deck. Repeat until the Speaker approves.

**Step 1: Design (slide-stylist)**
- Invoke the `slide-stylist` skill with the TalkBrief
- Input: `./tmp/deck/talk-brief.json`, optional brand assets
- Output: `./tmp/deck/style-guide.json`
- Update pipeline state:
  ```bash
  python3 -c "
  from src.deckcontext import update_step
  update_step('./tmp/deck', 'slide-stylist', 'completed', output_file='style-guide.json')
  "
  ```

**Step 2: Content -- Outline (narrative-architect)**
- Invoke the `narrative-architect` skill
- Input: `./tmp/deck/talk-brief.json`, `./tmp/deck/style-guide.json`
- Output: `./tmp/deck/outline.json`
- Update pipeline state for narrative-architect

**Step 3: Content -- Speaker Notes (speaker-notes-writer)**
- Invoke the `speaker-notes-writer` skill
- Input: `./tmp/deck/talk-brief.json`, `./tmp/deck/outline.json`
- Output: `./tmp/deck/speaker-notes.json`
- Update pipeline state for speaker-notes-writer

**Step 4: Images (imagegen-bridge)**
- Invoke the `imagegen-bridge` skill in **draft mode**
- Pass budget constraints and available providers
- Input: `./tmp/deck/outline.json`, `./tmp/deck/style-guide.json`
- Output: `./tmp/deck/image-manifest.json`, `./tmp/deck/images/`
- After generation, update budget state:
  ```bash
  python3 -c "
  from src.conductor import save_budget, DeckBudget
  import json
  # Reconstruct budget from pipeline state + new costs from imagegen-bridge
  # The imagegen-bridge skill reports costs in its output
  budget = DeckBudget(total_budget=$BUDGET)
  # ... add all API calls from the image-manifest ...
  save_budget('./tmp/deck', budget)
  "
  ```

**Step 5: Charts (chart-renderer) -- conditional**
- Only run if `include_charts` is true in TalkBrief preferences AND the outline contains `data_chart` slides
- Invoke the `chart-renderer` skill
- Input: `./tmp/deck/outline.json`, `./tmp/deck/style-guide.json`, `./tmp/deck/talk-brief.json` (data_sources)
- Output: `./tmp/deck/chart-manifest.json`, `./tmp/deck/images/`

**Step 6: Assembly (deck-assembler)**
- Invoke the `deck-assembler` skill
- Input: ALL contract files (outline, style-guide, image-manifest, chart-manifest, speaker-notes)
- Output: `./tmp/deck/output/presentation.pptx`

**Step 7: Speaker Review**
- Present the draft deck to the Speaker
- Report current cost:
  ```bash
  python3 -c "
  from src.conductor import DeckBudget
  from src.deckcontext import read_contract
  state = read_contract('./tmp/deck', 'pipeline-state')
  b = state.get('budget', {})
  budget = DeckBudget(total_budget=b.get('total_budget_usd', 0))
  budget.spent = b.get('spent_usd', 0)
  budget.cache_hits = b.get('cache_hits', 0)
  budget.cache_savings_usd = b.get('cache_savings_usd', 0)
  budget.api_calls = b.get('api_calls', [])
  print(budget.cost_summary_markdown())
  "
  ```
- Tell the Speaker: "Draft cycle N complete. Here is the deck and cost summary. You can: (a) approve and move to production, (b) give feedback for another draft cycle, or (c) stop here."
- If the Speaker gives feedback:
  - Increment the draft cycle counter:
    ```bash
    python3 -c "
    from src.conductor import increment_draft_cycle
    count = increment_draft_cycle('./tmp/deck')
    print(f'Starting draft cycle {count + 1}')
    "
    ```
  - Re-run only the affected steps based on the feedback (e.g., if they want a different narrative, re-run narrative-architect + downstream; if they want different images, re-run imagegen-bridge + downstream)
  - Return to Step 1 of this phase

### Phase 2: Production

Once the Speaker approves the draft:

1. **Switch to production mode:**
   ```bash
   python3 -c "
   from src.conductor import switch_to_production
   switch_to_production('./tmp/deck')
   print('Switched to production mode')
   "
   ```

2. **Re-render images at full quality.** Invoke `imagegen-bridge` in production mode (full quality, full resolution, approved providers).

3. **Rebuild the deck.** Invoke `deck-assembler` with production images.

4. **Run QA.** Invoke `deck-qa` to inspect the production .pptx.

5. **Handle QA results:**
   ```bash
   python3 -c "
   from src.deckcontext import read_contract
   from src.conductor import route_qa_findings, has_blocking_errors
   report = read_contract('./tmp/deck', 'qa-report')
   if report is None:
       print('ERROR: No QA report found')
   else:
       verdict = report.get('verdict', 'unknown')
       print(f'QA verdict: {verdict}')
       if has_blocking_errors(report.get('findings', [])):
           routes = route_qa_findings(report.get('findings', []))
           for r in routes:
               if r['action'] == 'reinvoke':
                   print(f'  REINVOKE {r[\"target_service\"]} for slide {r[\"slide_number\"]}: {r[\"description\"]}')
               else:
                   print(f'  LOG: slide {r[\"slide_number\"]}: {r[\"description\"]}')
       else:
           print('No blocking errors. Proceeding to review.')
   "
   ```

6. **QA correction loop (max 2 cycles):**
   - If QA verdict is `fail`:
     - Increment QA cycle counter:
       ```bash
       python3 -c "
       from src.conductor import increment_qa_cycle
       count = increment_qa_cycle('./tmp/deck')
       print(f'QA correction cycle {count} of 2')
       if count > 2:
           print('ESCALATE: Max QA cycles reached. Delivering best effort.')
       "
       ```
     - Route error findings to the responsible service (use the routing table above)
     - Re-invoke the identified service(s) with corrective instructions
     - Re-run deck-assembler and deck-qa
     - If still failing after 2 cycles, escalate to the Speaker
   - If QA verdict is `pass` or `pass_with_warnings`, proceed to review

7. **Presentation review.** Invoke `presentation-reviewer` (the advisory AI persona).
   - Input: `./tmp/deck/output/presentation.pptx`, outline, style-guide, speaker-notes, talk-brief
   - Present the review to the Speaker. The review is informational -- the Speaker decides whether to act on it.

8. **Deliver.** Present the Speaker with:
   - Path to the finished `.pptx` file
   - QA report summary
   - Presentation review
   - Final cost report:
     ```bash
     python3 -c "
     from src.conductor import DeckBudget
     from src.deckcontext import read_contract
     state = read_contract('./tmp/deck', 'pipeline-state')
     b = state.get('budget', {})
     budget = DeckBudget(total_budget=b.get('total_budget_usd', 0))
     budget.spent = b.get('spent_usd', 0)
     budget.cache_hits = b.get('cache_hits', 0)
     budget.cache_savings_usd = b.get('cache_savings_usd', 0)
     budget.api_calls = b.get('api_calls', [])
     print(budget.cost_summary_markdown())
     print()
     print(f'Draft cycles: {state.get(\"draft_cycle_count\", 0)}')
     print(f'QA correction cycles: {state.get(\"qa_cycle_count\", 0)}')
     print(f'Mode: {state.get(\"mode\", \"unknown\")}')
     "
     ```
   - Mark pipeline complete:
     ```bash
     python3 -c "
     from src.deckcontext import read_contract, write_contract
     state = read_contract('./tmp/deck', 'pipeline-state')
     state['status'] = 'completed'
     from datetime import datetime, timezone
     state['updated_at'] = datetime.now(timezone.utc).isoformat()
     write_contract('./tmp/deck', 'pipeline-state', state, validate=False)
     print('Pipeline complete.')
     "
     ```

---

## Resumability

If a pipeline run is interrupted (conversation ends, crash, timeout), the conductor can resume:

1. Check if `./tmp/deck/pipeline-state.json` exists
2. Read it and inspect which steps have `status: completed` with valid checksums
3. Skip completed steps, resume from the first pending/running/failed step
4. Tell the Speaker: "Found an existing pipeline run from [timestamp]. Steps completed: [list]. Resuming from [next step]."

```bash
python3 -c "
from src.deckcontext import read_contract
state = read_contract('./tmp/deck', 'pipeline-state')
if state is None:
    print('No existing pipeline found. Starting fresh.')
else:
    completed = [name for name, step in state['steps'].items() if step.get('status') == 'completed']
    pending = [name for name in state.get('step_order', []) if state['steps'].get(name, {}).get('status') != 'completed']
    print(f'Pipeline ID: {state[\"pipeline_id\"]}')
    print(f'Status: {state[\"status\"]}')
    print(f'Mode: {state.get(\"mode\", \"unknown\")}')
    print(f'Completed: {completed}')
    print(f'Remaining: {pending}')
"
```

---

## Error Handling

### Critical Steps (must succeed, abort after 2 retries)
- validate-brief
- narrative-architect (no meaningful fallback for "no outline")

### Recoverable Steps (retry up to 3 times, then apply fallback)
- slide-stylist: fallback to neutral gray palette with one accent
- imagegen-bridge: fallback to placeholders (coloured rectangles with alt text)
- chart-renderer: fallback to stat-card layout
- speaker-notes-writer: fallback to minimal notes (headline restated)

### Non-Blocking Steps (never abort)
- deck-qa: informs retry decisions but never causes abort
- presentation-reviewer: feedback is informational only

### Fallback Chain for Image Generation
1. Retry with same prompt (up to 2 retries)
2. Retry with simplified prompt (strip style modifiers)
3. Retry with different model (e.g., z-image-turbo -> flux2-klein)
4. Insert placeholder (solid colour rectangle with alt text)
5. Mark slide for manual intervention

---

## Budget Escalation Protocol

Before any cloud API call, check the budget:

```bash
python3 -c "
from src.deckcontext import read_contract
state = read_contract('./tmp/deck', 'pipeline-state')
b = state.get('budget', {})
remaining = b.get('total_budget_usd', 0) - b.get('spent_usd', 0)
estimated_cost = $ESTIMATED_COST
if remaining < estimated_cost:
    print(f'ESCALATE: Next request costs ~\${estimated_cost:.2f} but only \${remaining:.2f} remains.')
    print('Ask Speaker: increase budget, switch to Ollama, or skip?')
else:
    print(f'OK: \${remaining:.2f} remaining, \${estimated_cost:.2f} needed.')
"
```

If the budget will be exceeded:
1. Tell the Speaker the remaining budget and the estimated cost
2. Offer three options: (a) increase budget, (b) switch to Ollama (free), (c) skip remaining images
3. Wait for Speaker decision before proceeding
```

- [ ] **Step 2: Verify the agent file is valid YAML frontmatter + markdown**

Read the file back with the Read tool and verify:
- YAML frontmatter has `name` and `description` fields
- No stray YAML syntax errors
- Markdown renders correctly

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/deck-conductor.md
git commit -m "feat: add deck-conductor agent — top-level pipeline orchestrator"
```

---

## Task 5: Integration Test -- Conductor State Lifecycle

**Files:**
- Create: `tests/test_conductor_integration.py`

- [ ] **Step 1: Write the integration test**

Create `tests/test_conductor_integration.py`:

```python
"""Integration test: conductor state lifecycle from init through production."""

import json
import os
import shutil
import pytest

DECK_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'test-conductor-integration')
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.fixture(autouse=True)
def clean_deck_dir():
    if os.path.exists(DECK_DIR):
        shutil.rmtree(DECK_DIR)
    yield
    if os.path.exists(DECK_DIR):
        shutil.rmtree(DECK_DIR)


def load_fixture(name):
    path = os.path.join(FIXTURE_DIR, f'{name}.json')
    with open(path) as f:
        return json.load(f)


def test_full_conductor_lifecycle():
    """Simulate a complete conductor lifecycle:
    init -> draft cycle -> production -> QA -> delivery.
    """
    from src.deckcontext import init_deck, write_contract, read_contract, update_step
    from src.conductor import (
        DeckBudget, init_conductor_state, switch_to_production,
        increment_draft_cycle, increment_qa_cycle,
        save_budget, save_providers,
        route_qa_findings, has_blocking_errors,
    )

    # 1. Init
    init_deck(DECK_DIR)
    init_conductor_state(DECK_DIR, total_budget_usd=2.00)
    state = read_contract(DECK_DIR, 'pipeline-state')
    assert state['mode'] == 'draft'
    assert state['budget']['total_budget_usd'] == 2.00

    # 2. Save providers
    providers = {
        "ollama": {"available": True, "models": ["x/z-image-turbo"]},
        "openai": {"available": True, "model": "gpt-image-1.5"},
        "google_vertex": {"available": False},
        "fal": {"available": True, "models": ["flux-2-pro"]},
        "recraft": {"available": False},
    }
    save_providers(DECK_DIR, providers)

    # 3. Write TalkBrief
    brief = load_fixture('valid_talk_brief')
    write_contract(DECK_DIR, 'talk-brief', brief)
    update_step(DECK_DIR, 'validate-brief', 'completed', output_file='talk-brief.json')

    # 4. Draft cycle 1 -- simulate running all steps
    update_step(DECK_DIR, 'slide-stylist', 'running')
    guide = load_fixture('valid_style_guide')
    write_contract(DECK_DIR, 'style-guide', guide)
    update_step(DECK_DIR, 'slide-stylist', 'completed', output_file='style-guide.json')

    update_step(DECK_DIR, 'narrative-architect', 'running')
    outline = load_fixture('valid_slide_outline')
    write_contract(DECK_DIR, 'outline', outline)
    update_step(DECK_DIR, 'narrative-architect', 'completed', output_file='outline.json')

    update_step(DECK_DIR, 'speaker-notes-writer', 'running')
    notes = load_fixture('valid_speaker_notes')
    write_contract(DECK_DIR, 'speaker-notes', notes)
    update_step(DECK_DIR, 'speaker-notes-writer', 'completed', output_file='speaker-notes.json')

    # 5. Track budget during image generation
    budget = DeckBudget(total_budget=2.00)
    budget.log_api_call('imagen-4-fast', 0.02, 'slide-01-bg')
    budget.log_api_call('recraft-v4-svg', 0.08, 'slide-03-icon')
    budget.log_cache_hit('cached-bg-key', 0.02)
    save_budget(DECK_DIR, budget)

    update_step(DECK_DIR, 'imagegen-bridge', 'running')
    manifest = load_fixture('valid_image_manifest')
    write_contract(DECK_DIR, 'image-manifest', manifest)
    update_step(DECK_DIR, 'imagegen-bridge', 'completed', output_file='image-manifest.json')

    update_step(DECK_DIR, 'deck-assembler', 'running')
    update_step(DECK_DIR, 'deck-assembler', 'completed', output_file='output/presentation.pptx')

    # 6. Speaker approves draft, increment cycle
    cycle = increment_draft_cycle(DECK_DIR)
    assert cycle == 1

    # 7. Verify cost summary
    md = budget.cost_summary_markdown()
    assert '$0.10' in md
    assert 'allow' in md.lower()

    # 8. Switch to production
    switch_to_production(DECK_DIR)
    state = read_contract(DECK_DIR, 'pipeline-state')
    assert state['mode'] == 'production'
    assert state['qa_cycle_count'] == 0

    # 9. Simulate QA with errors
    qa_report = load_fixture('valid_qa_report')
    write_contract(DECK_DIR, 'qa-report', qa_report)
    update_step(DECK_DIR, 'deck-qa', 'completed', output_file='qa-report.json')

    # 10. Route QA findings
    routes = route_qa_findings(qa_report['findings'])
    error_routes = [r for r in routes if r['action'] == 'reinvoke']
    # The fixture has warnings and info, no errors
    assert len(error_routes) == 0

    # 11. QA cycle tracking
    qa_count = increment_qa_cycle(DECK_DIR)
    assert qa_count == 1
    qa_count = increment_qa_cycle(DECK_DIR)
    assert qa_count == 2

    # 12. Verify final state
    final_state = read_contract(DECK_DIR, 'pipeline-state')
    assert final_state['mode'] == 'production'
    assert final_state['draft_cycle_count'] == 1
    assert final_state['qa_cycle_count'] == 2
    assert final_state['budget']['spent_usd'] == 0.10
    assert final_state['available_providers']['ollama']['available'] is True
    assert final_state['available_providers']['google_vertex']['available'] is False


def test_budget_escalation_scenario():
    """Test that budget state transitions correctly through degradation."""
    from src.deckcontext import init_deck
    from src.conductor import DeckBudget, init_conductor_state, save_budget, read_contract

    init_deck(DECK_DIR)
    init_conductor_state(DECK_DIR, total_budget_usd=1.00)

    budget = DeckBudget(total_budget=1.00)

    # ALLOW state
    budget.log_api_call('imagen-4-fast', 0.10, 'img-1')
    assert budget.state == 'allow'

    # ALLOW_WITH_CAPS at 70%
    budget.log_api_call('flux-2-pro', 0.61, 'img-2')
    assert budget.state == 'allow_with_caps'

    # DEGRADE at 90%
    budget.log_api_call('gpt-image-1.5', 0.20, 'img-3')
    assert budget.state == 'degrade'

    # TYPOGRAPHY_ONLY at 100%
    budget.log_api_call('gpt-image-1.5', 0.10, 'img-4')
    assert budget.state == 'typography_only'

    # Save and verify persistence
    save_budget(DECK_DIR, budget)
    from src.deckcontext import read_contract as rc
    state = rc(DECK_DIR, 'pipeline-state')
    assert state['budget']['budget_state'] == 'typography_only'
    assert state['budget']['spent_usd'] == 1.01
    assert len(state['budget']['api_calls']) == 4


def test_qa_error_routing_scenario():
    """Test QA error findings are routed to correct upstream services."""
    from src.conductor import route_qa_findings, has_blocking_errors

    findings = [
        {"slide_number": 3, "severity": "error", "category": "overlap",
         "description": "Title text overlaps hero image on slide 3"},
        {"slide_number": 7, "severity": "error", "category": "image_quality",
         "description": "Hero image on slide 7 is blurry (BRISQUE > 40)"},
        {"slide_number": 7, "severity": "error", "category": "contrast",
         "description": "Body text contrast ratio 2.1:1 on slide 7"},
        {"slide_number": 12, "severity": "error", "category": "text_overflow",
         "description": "Body text overflows text box on slide 12"},
        {"slide_number": 15, "severity": "warning", "category": "margin",
         "description": "Image within 0.3in of edge on slide 15"},
        {"slide_number": 20, "severity": "info", "category": "consistency",
         "description": "Font size varies on slide 20"},
    ]

    assert has_blocking_errors(findings) is True

    routes = route_qa_findings(findings)
    reinvoke = [r for r in routes if r['action'] == 'reinvoke']
    log_only = [r for r in routes if r['action'] == 'log']

    assert len(reinvoke) == 4
    assert len(log_only) == 2

    # Verify correct service routing
    service_map = {r['category']: r['target_service'] for r in reinvoke}
    assert service_map['overlap'] == 'deck-assembler'
    assert service_map['image_quality'] == 'imagegen-bridge'
    assert service_map['contrast'] == 'slide-stylist'
    assert service_map['text_overflow'] == 'narrative-architect'
```

- [ ] **Step 2: Run the integration tests**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_conductor_integration.py -v`

Expected: All 3 tests PASS.

- [ ] **Step 3: Run the complete test suite**

Run: `source .venv/bin/activate && python3 -m pytest tests/ -v --tb=short`

Expected: All tests PASS across all test files.

- [ ] **Step 4: Commit**

```bash
git add tests/test_conductor_integration.py
git commit -m "test: add conductor integration tests — lifecycle, budget escalation, QA routing"
```

---

## Task 6: Deprecate Old ollama-presentation Skill

**Files:**
- Modify: `.claude/skills/ollama-presentation/SKILL.md`

- [ ] **Step 1: Add deprecation notice to the old skill**

Add the following to the very top of `.claude/skills/ollama-presentation/SKILL.md`, immediately after the YAML frontmatter closing `---`:

```markdown

> **DEPRECATED:** This skill has been replaced by the `deck-conductor` agent (`.claude/agents/deck-conductor.md`). The deck-conductor provides the full pipeline with narrative architecture, speaker notes, multi-model image routing, automated QA, presentation review, budget tracking, and draft/production lifecycle management. Use `/deck-conductor` instead of `/ollama-presentation` for all new presentations.
>
> This skill remains available for backward compatibility but will not receive updates.
```

- [ ] **Step 2: Verify the deprecation notice renders correctly**

Read the file with the Read tool. Verify the deprecation notice appears at the top, after the frontmatter.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/ollama-presentation/SKILL.md
git commit -m "docs: deprecate ollama-presentation skill in favour of deck-conductor agent"
```

---

## Task 7: Final Verification

- [ ] **Step 1: Run the complete test suite**

Run: `source .venv/bin/activate && python3 -m pytest tests/ -v --tb=short`

Expected: All tests PASS.

- [ ] **Step 2: Verify all new files exist**

Run:
```bash
ls -la research/synthesis-deck-conductor.md src/conductor.py .claude/agents/deck-conductor.md tests/test_conductor.py tests/test_conductor_integration.py tests/test_pipeline_state_extended.py tests/fixtures/valid_pipeline_state_extended.json
```

Expected: All 7 files exist.

- [ ] **Step 3: Verify Python syntax is clean**

Run:
```bash
source .venv/bin/activate && python3 -m py_compile src/conductor.py && echo "Syntax OK"
```

Expected: "Syntax OK"

- [ ] **Step 4: Verify the agent file has valid frontmatter**

Run:
```bash
head -5 .claude/agents/deck-conductor.md
```

Expected: YAML frontmatter with `name: deck-conductor` and `description:` field.

---

## Summary

After completing all 7 tasks, Phase 6 provides:

| Artifact | Purpose |
|----------|---------|
| `research/synthesis-deck-conductor.md` | Consolidated design decisions from papers 05, 12, 13 |
| `src/schemas/pipeline_state.schema.json` | Extended with mode, budget, cycle counts, providers |
| `src/conductor.py` | Budget tracking, cost reporting, QA routing, state helpers |
| `.claude/agents/deck-conductor.md` | The agent definition -- primary deliverable |
| `tests/test_conductor.py` | Unit tests for conductor utilities (21 tests) |
| `tests/test_pipeline_state_extended.py` | Schema validation for extended PipelineState (9 tests) |
| `tests/test_conductor_integration.py` | Integration tests for full lifecycle (3 tests) |
| `tests/fixtures/valid_pipeline_state_extended.json` | Extended PipelineState sample data |
| `.claude/skills/ollama-presentation/SKILL.md` | Deprecation notice added |

**The deck-conductor agent replaces the old ollama-presentation skill** and provides:
- Full pipeline orchestration with dependency-aware step sequencing
- Draft/production lifecycle with iterative Speaker review cycles
- Cumulative cloud API cost tracking with four-state budget degradation
- QA correction loop routing (max 2 cycles) with per-category service targeting
- Provider discovery and Speaker confirmation before spending
- Pipeline resumability from checkpointed DeckContext state
- Escalation triggers for budget, QA, provider, and narrative issues
- Cost reporting at every Speaker review point and final delivery

---

### Critical Files for Implementation

- `/Users/stevejones/Documents/Development/jack-tar-deckhand/.claude/agents/deck-conductor.md` -- the agent definition, primary deliverable that replaces ollama-presentation
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/src/conductor.py` -- budget tracking (DeckBudget), QA finding routing (route_qa_findings), state helpers (init/switch/increment/save)
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/src/schemas/pipeline_state.schema.json` -- extended PipelineState schema with mode, budget, cycle count, and available_providers fields
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/tests/test_conductor_integration.py` -- integration tests covering full lifecycle, budget escalation, and QA error routing scenarios
- `/Users/stevejones/Documents/Development/jack-tar-deckhand/research/synthesis-deck-conductor.md` -- prerequisite research synthesis consolidating papers 05, 12, 13
