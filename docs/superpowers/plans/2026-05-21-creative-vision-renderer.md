# Creative Vision Renderer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the paperbanana-shaped internal renderer that takes an operator's free-form prose vision and produces a vision-faithful image at presentation quality, with internal critic loop, tier cascade, and per-slide budget control. Strategy enum value `creative_vision` always pairs with `full_bleed` assembly (issue #88).

**Architecture:** Three new agents (Director's Brief / Prompt Reviewer / Director's Critic) plus the existing `image-reviewer` (reused). Text-side gate before render (Brief ↔ Prompt Reviewer); image-side gates after render (image-reviewer then Director's Critic). Cascade ladder Ollama → Flash 1K → 2K → 4K → Pro 1K → 2K → 4K (or Recraft alternate when `brand_fidelity: exact`). Per-tier iteration caps + per-slide hard budget cap. Pure-logic Python modules (cascade state machine, manifest persistence, schema validation, input/output prep for agents); agent dispatch driven by SKILL.md instructions to Claude — the same kernel/shell split that `/iterate-slide` already uses.

**Tech Stack:** Python 3.10+, `jsonschema`, `python-pptx` (downstream consumer via `full_bleed` assembly), Claude Code Agent dispatch (Sonnet for Brief + Critic, Haiku for Reviewer + image-reviewer), Ollama (free draft tier), cloud image APIs (Nano Banana Flash/Pro via google-genai SDK, Recraft V4 via direct API or FAL).

**Companion spec:** [`docs/superpowers/specs/2026-05-21-creative-vision-renderer-design.md`](../specs/2026-05-21-creative-vision-renderer-design.md). All architectural decisions are documented there — this plan implements that design without rebudging it.

**Branch:** `feat/creative-page-renderer` (already cut from main at `d2253ad`).

**Plugin version:** bump `1.4.2` → `1.5.0` on landing.

---

## Phase 1 — Schemas and package skeleton

### Task 1: `parsed_vision.schema.json` + validation tests

**Files:**
- Create: `plugins/jack-tar-deckhand/src/schemas/parsed_vision.schema.json`
- Test: `plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py`

- [ ] **Step 1: Write the failing test**

```python
# plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py
"""Schema validation tests for the creative_vision pipeline (issue #105)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

SCHEMA_DIR = PLUGIN_ROOT / "src" / "schemas"


def _load(name):
    with open(SCHEMA_DIR / name) as f:
        return json.load(f)


# --- parsed_vision -----------------------------------------------------------


def _valid_parsed_vision():
    return {
        "schema_version": "1.0",
        "original_prose": "Four warships on a lake.",
        "prose_version": 1,
        "subjects": [
            {"name": "SAP", "role": "named_entity", "spatial_slot": "ship_NE"}
        ],
        "spatial_directives": {
            "setting": "lake",
            "layout": "four-way",
            "containment": None,
            "named_relationships": [],
        },
        "style": {"explicit": None, "implied": "naval", "register_inherited_from": None},
        "composition": {
            "progression_axis": None,
            "primary_focus": "centre",
            "compositional_rules": [],
        },
        "delivery": {
            "scale": "screen_16x9",
            "aspect": "16:9",
            "viewing_context": "projection",
        },
        "text_density_warning": {
            "estimated_text_elements": 4,
            "threshold_breach": False,
        },
    }


def test_parsed_vision_minimal_valid():
    validate(instance=_valid_parsed_vision(), schema=_load("parsed_vision.schema.json"))


def test_parsed_vision_missing_required_rejected():
    bad = _valid_parsed_vision()
    del bad["original_prose"]
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("parsed_vision.schema.json"))


def test_parsed_vision_progression_axis_optional():
    pv = _valid_parsed_vision()
    pv["composition"]["progression_axis"] = "spatial_horizontal"
    validate(instance=pv, schema=_load("parsed_vision.schema.json"))
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py -v
```

Expected: FAIL with `FileNotFoundError` on `parsed_vision.schema.json`.

- [ ] **Step 3: Write the schema**

```json
// plugins/jack-tar-deckhand/src/schemas/parsed_vision.schema.json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/parsed-vision.json",
  "title": "ParsedVision",
  "description": "Structured intermediate produced by Director's Brief from an operator's prose vision. Issue #105.",
  "type": "object",
  "required": [
    "schema_version", "original_prose", "prose_version",
    "subjects", "spatial_directives", "style", "composition",
    "delivery", "text_density_warning"
  ],
  "properties": {
    "schema_version": {"type": "string"},
    "original_prose": {"type": "string"},
    "prose_version": {"type": "integer", "minimum": 1},
    "subjects": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "role", "spatial_slot"],
        "properties": {
          "name": {"type": "string"},
          "role": {"type": "string", "enum": ["named_entity", "abstract_motif", "setting_element"]},
          "spatial_slot": {"type": ["string", "null"]}
        }
      }
    },
    "spatial_directives": {
      "type": "object",
      "required": ["setting", "layout", "containment", "named_relationships"],
      "properties": {
        "setting": {"type": ["string", "null"]},
        "layout": {"type": ["string", "null"]},
        "containment": {"type": ["string", "null"]},
        "named_relationships": {"type": "array", "items": {"type": "string"}}
      }
    },
    "style": {
      "type": "object",
      "required": ["explicit", "implied", "register_inherited_from"],
      "properties": {
        "explicit": {"type": ["string", "null"]},
        "implied": {"type": ["string", "null"]},
        "register_inherited_from": {"type": ["string", "null"]}
      }
    },
    "composition": {
      "type": "object",
      "required": ["progression_axis", "primary_focus", "compositional_rules"],
      "properties": {
        "progression_axis": {
          "type": ["string", "null"],
          "enum": [null, "spatial_horizontal", "spatial_vertical", "size_escalation", "radial", "diagonal"]
        },
        "primary_focus": {"type": ["string", "null"]},
        "compositional_rules": {"type": "array", "items": {"type": "string"}}
      }
    },
    "delivery": {
      "type": "object",
      "required": ["scale", "aspect", "viewing_context"],
      "properties": {
        "scale": {"type": "string"},
        "aspect": {"type": "string"},
        "viewing_context": {"type": "string"}
      }
    },
    "text_density_warning": {
      "type": "object",
      "required": ["estimated_text_elements", "threshold_breach"],
      "properties": {
        "estimated_text_elements": {"type": "integer", "minimum": 0},
        "threshold_breach": {"type": "boolean"}
      }
    }
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py -v
```

Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/src/schemas/parsed_vision.schema.json plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py
git commit -m "feat(creative-vision): add ParsedVision schema (#105)"
```

---

### Task 2: `directors_critic_verdict.schema.json` + tests

**Files:**
- Create: `plugins/jack-tar-deckhand/src/schemas/directors_critic_verdict.schema.json`
- Modify: `plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py` (add verdict tests)

- [ ] **Step 1: Append failing tests**

```python
# Append to plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py

# --- directors_critic_verdict ------------------------------------------------


def _valid_verdict():
    return {
        "verdict": "refine_at_tier",
        "per_axis_scores": {
            "entity_fidelity": 65,
            "spatial_fidelity": 85,
            "style_fidelity": 90,
            "quality": 80,
            "composition": 75,
        },
        "issues": [
            {"axis": "entity_fidelity", "detail": "Databricks ship missing"}
        ],
        "gap_location": "prompt",
        "recommended_action": "Re-emphasise Databricks as labelled fourth ship",
        "tier": "flash_2k",
        "iteration_index": 2,
        "plateau_signal": False,
    }


def test_verdict_minimal_valid():
    validate(instance=_valid_verdict(), schema=_load("directors_critic_verdict.schema.json"))


def test_verdict_rejects_unknown_verdict_enum():
    bad = _valid_verdict()
    bad["verdict"] = "made_up"
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("directors_critic_verdict.schema.json"))


def test_verdict_rejects_score_out_of_range():
    bad = _valid_verdict()
    bad["per_axis_scores"]["quality"] = 150
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("directors_critic_verdict.schema.json"))


@pytest.mark.parametrize("verdict", ["pass", "refine_at_tier", "escalate_tier", "abort"])
def test_verdict_accepts_all_verdicts(verdict):
    v = _valid_verdict()
    v["verdict"] = verdict
    validate(instance=v, schema=_load("directors_critic_verdict.schema.json"))


@pytest.mark.parametrize("gap", ["prose", "prompt", "tier", "unknown"])
def test_verdict_accepts_all_gap_locations(gap):
    v = _valid_verdict()
    v["gap_location"] = gap
    validate(instance=v, schema=_load("directors_critic_verdict.schema.json"))
```

- [ ] **Step 2: Run to verify failures**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py -v
```

Expected: 5 new FAIL with FileNotFoundError.

- [ ] **Step 3: Write the schema**

```json
// plugins/jack-tar-deckhand/src/schemas/directors_critic_verdict.schema.json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/directors-critic-verdict.json",
  "title": "DirectorsCriticVerdict",
  "description": "Verdict returned by Director's Critic after evaluating a rendered image against the ParsedVision. Issue #105.",
  "type": "object",
  "required": [
    "verdict", "per_axis_scores", "issues", "gap_location",
    "recommended_action", "tier", "iteration_index", "plateau_signal"
  ],
  "properties": {
    "verdict": {
      "type": "string",
      "enum": ["pass", "refine_at_tier", "escalate_tier", "abort"]
    },
    "per_axis_scores": {
      "type": "object",
      "required": ["entity_fidelity", "spatial_fidelity", "style_fidelity", "quality", "composition"],
      "properties": {
        "entity_fidelity": {"type": "integer", "minimum": 0, "maximum": 100},
        "spatial_fidelity": {"type": "integer", "minimum": 0, "maximum": 100},
        "style_fidelity": {"type": "integer", "minimum": 0, "maximum": 100},
        "quality": {"type": "integer", "minimum": 0, "maximum": 100},
        "composition": {"type": "integer", "minimum": 0, "maximum": 100}
      }
    },
    "issues": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["axis", "detail"],
        "properties": {
          "axis": {"type": "string"},
          "detail": {"type": "string"}
        }
      }
    },
    "gap_location": {
      "type": "string",
      "enum": ["prose", "prompt", "tier", "unknown"]
    },
    "recommended_action": {"type": "string"},
    "tier": {"type": "string"},
    "iteration_index": {"type": "integer", "minimum": 1},
    "plateau_signal": {"type": "boolean"}
  }
}
```

- [ ] **Step 4: Run to verify passes**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/src/schemas/directors_critic_verdict.schema.json plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py
git commit -m "feat(creative-vision): add DirectorsCriticVerdict schema (#105)"
```

---

### Task 3: `creative_vision_manifest.schema.json` + tests

**Files:**
- Create: `plugins/jack-tar-deckhand/src/schemas/creative_vision_manifest.schema.json`
- Modify: `plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py` (append manifest tests)

- [ ] **Step 1: Append failing tests**

```python
# Append to plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py

# --- creative_vision_manifest -----------------------------------------------


def _valid_manifest():
    return {
        "run_id": "cv-2026-05-21-093142-slide-3",
        "slide_number": 3,
        "strategy": "creative_vision",
        "prose_history": [
            {"version": 1, "timestamp": "2026-05-21T09:31:42Z", "prose": "Four ships..."}
        ],
        "attempts": [],
        "final": None,
        "iterate_slide_hooks": {
            "can_revise_prose": True,
            "can_refine_prompt": True,
            "can_escalate_tier": True,
            "current_tier": "ollama",
            "next_tier_available": "flash_1k",
            "remaining_budget_usd": 1.0,
        },
    }


def test_manifest_minimal_valid():
    validate(instance=_valid_manifest(), schema=_load("creative_vision_manifest.schema.json"))


def test_manifest_prose_revision_appended():
    m = _valid_manifest()
    m["prose_history"].append({
        "version": 2,
        "timestamp": "2026-05-21T10:00:00Z",
        "prose": "Four 1980s Cold-War warships...",
        "revised_by": "operator",
        "reason": "fishing-boat look in v1",
    })
    validate(instance=m, schema=_load("creative_vision_manifest.schema.json"))


def test_manifest_with_final_block():
    m = _valid_manifest()
    m["final"] = {
        "image_path": "runs/07-flash-4k.png",
        "accepted_at_tier": "flash_4k",
        "total_cost_usd": 0.43,
        "total_iterations": 7,
        "final_verdict": _valid_verdict(),
    }
    m["final"]["final_verdict"]["verdict"] = "pass"
    validate(instance=m, schema=_load("creative_vision_manifest.schema.json"))


def test_manifest_strategy_must_be_creative_vision():
    bad = _valid_manifest()
    bad["strategy"] = "full_bleed"
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("creative_vision_manifest.schema.json"))
```

- [ ] **Step 2: Run to verify failures**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py -v
```

Expected: 4 new FAIL with FileNotFoundError.

- [ ] **Step 3: Write the schema**

```json
// plugins/jack-tar-deckhand/src/schemas/creative_vision_manifest.schema.json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/creative-vision-manifest.json",
  "title": "CreativeVisionManifest",
  "description": "Persisted state for a creative_vision slide. Mirror of paperbanana_run_id contract. Issue #105.",
  "type": "object",
  "required": [
    "run_id", "slide_number", "strategy", "prose_history",
    "attempts", "final", "iterate_slide_hooks"
  ],
  "properties": {
    "run_id": {"type": "string"},
    "slide_number": {"type": "integer", "minimum": 1},
    "strategy": {"type": "string", "const": "creative_vision"},
    "prose_history": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["version", "timestamp", "prose"],
        "properties": {
          "version": {"type": "integer", "minimum": 1},
          "timestamp": {"type": "string"},
          "prose": {"type": "string"},
          "revised_by": {"type": "string", "enum": ["operator", "system"]},
          "reason": {"type": "string"}
        }
      }
    },
    "attempts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "attempt_index", "prose_version", "tier", "text_iterations",
          "render", "image_reviewer_verdict", "directors_critic_verdict",
          "cumulative_cost_usd"
        ],
        "properties": {
          "attempt_index": {"type": "integer", "minimum": 1},
          "prose_version": {"type": "integer", "minimum": 1},
          "tier": {"type": "string"},
          "text_iterations": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["prompt_draft", "reviewer_verdict"],
              "properties": {
                "prompt_draft": {"type": "string"},
                "reviewer_verdict": {"type": "string", "enum": ["pass", "refine"]},
                "reviewer_feedback": {"type": "string"}
              }
            }
          },
          "render": {
            "type": "object",
            "required": ["model", "resolution", "cost_usd", "output_path"],
            "properties": {
              "model": {"type": "string"},
              "resolution": {"type": "string"},
              "cost_usd": {"type": "number", "minimum": 0},
              "output_path": {"type": "string"}
            }
          },
          "image_reviewer_verdict": {"type": "string", "enum": ["pass", "refine"]},
          "directors_critic_verdict": {"$ref": "directors_critic_verdict.schema.json"},
          "cumulative_cost_usd": {"type": "number", "minimum": 0}
        }
      }
    },
    "final": {
      "type": ["object", "null"],
      "required": ["image_path", "accepted_at_tier", "total_cost_usd", "total_iterations", "final_verdict"],
      "properties": {
        "image_path": {"type": "string"},
        "accepted_at_tier": {"type": "string"},
        "total_cost_usd": {"type": "number", "minimum": 0},
        "total_iterations": {"type": "integer", "minimum": 1},
        "final_verdict": {"$ref": "directors_critic_verdict.schema.json"}
      }
    },
    "iterate_slide_hooks": {
      "type": "object",
      "required": [
        "can_revise_prose", "can_refine_prompt", "can_escalate_tier",
        "current_tier", "remaining_budget_usd"
      ],
      "properties": {
        "can_revise_prose": {"type": "boolean"},
        "can_refine_prompt": {"type": "boolean"},
        "can_escalate_tier": {"type": "boolean"},
        "current_tier": {"type": "string"},
        "next_tier_available": {"type": ["string", "null"]},
        "remaining_budget_usd": {"type": "number", "minimum": 0}
      }
    }
  }
}
```

- [ ] **Step 4: Run to verify passes**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py -v
```

Expected: all 12 schema tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/src/schemas/creative_vision_manifest.schema.json plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py
git commit -m "feat(creative-vision): add CreativeVisionManifest schema (#105)"
```

---

### Task 4: Extend `strategy_map.schema.json` with `creative_vision` enum value + block

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/schemas/strategy_map.schema.json`
- Modify: `plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py` (append tests)

- [ ] **Step 1: Append failing tests**

```python
# Append to plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py

# --- strategy_map.creative_vision integration -------------------------------


def _valid_strategy_map_entry_creative_vision():
    return {
        "approval_mode": "review",
        "slides": [
            {
                "slide_number": 1,
                "strategy": "creative_vision",
                "rationale": "operator-directed",
                "render_funnel": ["ollama", "cloud_low", "cloud_full"],
                "creative_vision": {
                    "vision_prose": "Four warships on a lake.",
                    "budget_usd": 1.0,
                    "allowed_ceiling": "pro_4k",
                    "iteration_caps_override": None,
                },
            }
        ],
    }


def test_strategy_map_accepts_creative_vision_strategy():
    validate(
        instance=_valid_strategy_map_entry_creative_vision(),
        schema=_load("strategy_map.schema.json"),
    )


def test_strategy_map_creative_vision_block_required_when_strategy_set():
    bad = _valid_strategy_map_entry_creative_vision()
    del bad["slides"][0]["creative_vision"]
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("strategy_map.schema.json"))


def test_strategy_map_creative_vision_block_forbidden_when_strategy_other():
    bad = _valid_strategy_map_entry_creative_vision()
    bad["slides"][0]["strategy"] = "composed"
    # creative_vision block still present - must reject
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("strategy_map.schema.json"))


def test_strategy_map_vision_prose_required_inside_block():
    bad = _valid_strategy_map_entry_creative_vision()
    del bad["slides"][0]["creative_vision"]["vision_prose"]
    with pytest.raises(ValidationError):
        validate(instance=bad, schema=_load("strategy_map.schema.json"))
```

- [ ] **Step 2: Run to verify failures**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py -k "strategy_map" -v
```

Expected: 4 FAIL — `creative_vision` not yet in the enum.

- [ ] **Step 3: Extend the schema**

Edit `plugins/jack-tar-deckhand/src/schemas/strategy_map.schema.json`:

1. Add `"creative_vision"` to BOTH the `strategy` enum AND the `speaker_override` enum (mirror how `full_bleed` was added in v1.4.2).

2. Add the `creative_vision` block under the slide entry's `properties`:

```json
"creative_vision": {
  "type": "object",
  "required": ["vision_prose"],
  "properties": {
    "vision_prose": {"type": "string", "minLength": 1},
    "budget_usd": {"type": "number", "minimum": 0, "default": 1.0},
    "allowed_ceiling": {
      "type": "string",
      "enum": ["ollama", "flash_1k", "flash_2k", "flash_4k", "pro_1k", "pro_2k", "pro_4k",
              "recraft_standard_1k", "recraft_pro_2k", "recraft_pro_4k"],
      "default": "pro_4k"
    },
    "iteration_caps_override": {"type": ["object", "null"]}
  }
}
```

3. Add an `allOf` conditional at the slide-entry level enforcing the bidirectional rule (block required when strategy=creative_vision; forbidden otherwise):

```json
"allOf": [
  {
    "if": {"properties": {"strategy": {"const": "creative_vision"}}},
    "then": {"required": ["creative_vision"]},
    "else": {"not": {"required": ["creative_vision"]}}
  }
]
```

- [ ] **Step 4: Run to verify passes**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py -v
```

Expected: all schema tests PASS.

- [ ] **Step 5: Confirm existing strategy-map tests still pass**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/ -v
```

Expected: 204 (baseline) + new tests = all PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/jack-tar-deckhand/src/schemas/strategy_map.schema.json plugins/jack-tar-deckhand/tests/test_creative_vision_schemas.py
git commit -m "feat(creative-vision): extend strategy_map schema with creative_vision strategy + block (#105)"
```

---

### Task 5: `creative_vision/` package skeleton

**Files:**
- Create: `plugins/jack-tar-deckhand/src/creative_vision/__init__.py`
- Create: `plugins/jack-tar-deckhand/src/creative_vision/orchestrator.py` (empty stub)
- Create: `plugins/jack-tar-deckhand/src/creative_vision/brief.py` (empty stub)
- Create: `plugins/jack-tar-deckhand/src/creative_vision/prompt_reviewer.py` (empty stub)
- Create: `plugins/jack-tar-deckhand/src/creative_vision/critic.py` (empty stub)
- Create: `plugins/jack-tar-deckhand/src/creative_vision/cascade.py` (empty stub)
- Create: `plugins/jack-tar-deckhand/src/creative_vision/manifest.py` (empty stub)
- Create: `plugins/jack-tar-deckhand/src/creative_vision_dispatch.py` (empty stub)

- [ ] **Step 1: Write the failing import test**

```python
# plugins/jack-tar-deckhand/tests/test_creative_vision_package.py
"""Confirms the creative_vision package and its modules are importable."""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))


def test_package_imports():
    from src.creative_vision import brief, cascade, critic, manifest, orchestrator, prompt_reviewer  # noqa: F401


def test_top_level_dispatch_imports():
    from src import creative_vision_dispatch  # noqa: F401
```

- [ ] **Step 2: Run to verify failure**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_package.py -v
```

Expected: 2 FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Create the package + stubs**

Each stub file contains a single module docstring + `from __future__ import annotations` so import succeeds without functional code. Example for `brief.py`:

```python
# plugins/jack-tar-deckhand/src/creative_vision/brief.py
"""Director's Brief agent dispatch helpers.

Prepares the input prompt for the directors-brief agent and parses
its output back into a ParsedVision + render-ready prompt. Issue #105.
"""
from __future__ import annotations
```

Repeat for `cascade.py`, `critic.py`, `manifest.py`, `orchestrator.py`, `prompt_reviewer.py` (each with its own purpose-specific docstring). `__init__.py` is just `"""Creative vision renderer pipeline. Issue #105."""`.

For `creative_vision_dispatch.py`:

```python
# plugins/jack-tar-deckhand/src/creative_vision_dispatch.py
"""Top-level dispatch entry for creative_vision strategy.

Called by imagegen-bridge for each slide with strategy=creative_vision.
Mirror of paperbanana_dispatch.py. Issue #105.
"""
from __future__ import annotations
```

- [ ] **Step 4: Run to verify passes**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_package.py -v
```

Expected: 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/src/creative_vision/ plugins/jack-tar-deckhand/src/creative_vision_dispatch.py plugins/jack-tar-deckhand/tests/test_creative_vision_package.py
git commit -m "feat(creative-vision): scaffold package + module stubs (#105)"
```

---

## Phase 2 — Manifest module

### Task 6: `manifest.create_run_id` + `manifest.load` + `manifest.save`

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/creative_vision/manifest.py`
- Create: `plugins/jack-tar-deckhand/tests/test_creative_vision_manifest.py`

- [ ] **Step 1: Write failing tests**

```python
# plugins/jack-tar-deckhand/tests/test_creative_vision_manifest.py
"""Tests for the CreativeVisionManifest persistence module."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.manifest import (  # noqa: E402
    create_run_id,
    initialise_manifest,
    load_manifest,
    save_manifest,
)


def test_create_run_id_format():
    rid = create_run_id(slide_number=3)
    # cv-YYYY-MM-DD-HHMMSS-slide-N
    assert rid.startswith("cv-")
    assert rid.endswith("-slide-3")
    assert len(rid) > 20


def test_create_run_id_uniqueness_between_calls(monkeypatch):
    # Even at the same second-precision timestamp, calls must produce distinct ids
    rid1 = create_run_id(slide_number=3)
    rid2 = create_run_id(slide_number=3)
    assert rid1 != rid2


def test_initialise_manifest_minimum_shape():
    m = initialise_manifest(slide_number=3, vision_prose="Four ships.", budget_usd=1.0)
    assert m["slide_number"] == 3
    assert m["strategy"] == "creative_vision"
    assert len(m["prose_history"]) == 1
    assert m["prose_history"][0]["version"] == 1
    assert m["prose_history"][0]["prose"] == "Four ships."
    assert m["attempts"] == []
    assert m["final"] is None
    assert m["iterate_slide_hooks"]["remaining_budget_usd"] == 1.0


def test_save_and_load_roundtrip(tmp_path):
    deck_dir = tmp_path / "deck"
    deck_dir.mkdir()
    m = initialise_manifest(slide_number=3, vision_prose="Four ships.", budget_usd=1.0)
    save_manifest(str(deck_dir), m)
    loaded = load_manifest(str(deck_dir), slide_number=3)
    assert loaded == m


def test_save_creates_directory_structure(tmp_path):
    deck_dir = tmp_path / "deck"
    deck_dir.mkdir()
    m = initialise_manifest(slide_number=7, vision_prose="X", budget_usd=0.5)
    save_manifest(str(deck_dir), m)
    expected = deck_dir / "creative-vision" / "7" / "manifest.json"
    assert expected.is_file()
    # also creates runs/ subdir
    assert (deck_dir / "creative-vision" / "7" / "runs").is_dir()


def test_load_raises_when_missing(tmp_path):
    deck_dir = tmp_path / "deck"
    deck_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        load_manifest(str(deck_dir), slide_number=3)
```

- [ ] **Step 2: Run to verify failure**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_manifest.py -v
```

Expected: ImportError on `create_run_id`, etc.

- [ ] **Step 3: Write the implementation**

```python
# plugins/jack-tar-deckhand/src/creative_vision/manifest.py
"""CreativeVisionManifest persistence module. Issue #105."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone


def create_run_id(slide_number: int) -> str:
    """Return a fresh run_id of shape ``cv-YYYY-MM-DD-HHMMSS-<rand>-slide-N``."""
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    return f"cv-{stamp}-{suffix}-slide-{slide_number}"


def initialise_manifest(slide_number: int, vision_prose: str, budget_usd: float) -> dict:
    """Build a fresh CreativeVisionManifest for a slide that has not yet rendered."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "run_id": create_run_id(slide_number),
        "slide_number": slide_number,
        "strategy": "creative_vision",
        "prose_history": [
            {"version": 1, "timestamp": now, "prose": vision_prose}
        ],
        "attempts": [],
        "final": None,
        "iterate_slide_hooks": {
            "can_revise_prose": True,
            "can_refine_prompt": True,
            "can_escalate_tier": True,
            "current_tier": "ollama",
            "next_tier_available": "flash_1k",
            "remaining_budget_usd": budget_usd,
        },
    }


def _manifest_dir(deck_dir: str, slide_number: int) -> str:
    return os.path.join(deck_dir, "creative-vision", str(slide_number))


def _manifest_path(deck_dir: str, slide_number: int) -> str:
    return os.path.join(_manifest_dir(deck_dir, slide_number), "manifest.json")


def save_manifest(deck_dir: str, manifest: dict) -> None:
    """Persist a manifest under <deck_dir>/creative-vision/<slide_number>/manifest.json.

    Also ensures the sibling runs/ subdirectory exists.
    """
    mdir = _manifest_dir(deck_dir, manifest["slide_number"])
    os.makedirs(mdir, exist_ok=True)
    os.makedirs(os.path.join(mdir, "runs"), exist_ok=True)
    with open(_manifest_path(deck_dir, manifest["slide_number"]), "w") as f:
        json.dump(manifest, f, indent=2)


def load_manifest(deck_dir: str, slide_number: int) -> dict:
    path = _manifest_path(deck_dir, slide_number)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"No creative_vision manifest at {path}")
    with open(path) as f:
        return json.load(f)
```

- [ ] **Step 4: Run to verify passes**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_manifest.py -v
```

Expected: 6 PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/src/creative_vision/manifest.py plugins/jack-tar-deckhand/tests/test_creative_vision_manifest.py
git commit -m "feat(creative-vision): manifest create/load/save with run-id generation (#105)"
```

---

### Task 7: `manifest.revise_prose` (versioning logic)

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/creative_vision/manifest.py`
- Modify: `plugins/jack-tar-deckhand/tests/test_creative_vision_manifest.py`

- [ ] **Step 1: Append failing tests**

```python
# Append to plugins/jack-tar-deckhand/tests/test_creative_vision_manifest.py

from src.creative_vision.manifest import revise_prose  # noqa: E402


def test_revise_prose_bumps_version():
    m = initialise_manifest(slide_number=3, vision_prose="v1 prose", budget_usd=1.0)
    revise_prose(m, new_prose="v2 prose", revised_by="operator", reason="too vague")
    assert len(m["prose_history"]) == 2
    assert m["prose_history"][1]["version"] == 2
    assert m["prose_history"][1]["prose"] == "v2 prose"
    assert m["prose_history"][1]["revised_by"] == "operator"
    assert m["prose_history"][1]["reason"] == "too vague"


def test_revise_prose_preserves_history():
    m = initialise_manifest(slide_number=3, vision_prose="v1", budget_usd=1.0)
    revise_prose(m, new_prose="v2", revised_by="operator", reason="x")
    revise_prose(m, new_prose="v3", revised_by="operator", reason="y")
    assert [h["version"] for h in m["prose_history"]] == [1, 2, 3]
    assert [h["prose"] for h in m["prose_history"]] == ["v1", "v2", "v3"]


def test_revise_prose_rejects_empty_string():
    m = initialise_manifest(slide_number=3, vision_prose="v1", budget_usd=1.0)
    with pytest.raises(ValueError):
        revise_prose(m, new_prose="", revised_by="operator", reason="x")
```

- [ ] **Step 2: Run to verify failure**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_manifest.py -v
```

Expected: 3 ImportError on `revise_prose`.

- [ ] **Step 3: Implement**

Append to `manifest.py`:

```python
def revise_prose(manifest: dict, new_prose: str, revised_by: str, reason: str) -> None:
    """Append a new prose version to manifest['prose_history'] in-place.

    Bumps the version number; preserves prior versions for audit.
    """
    if not new_prose:
        raise ValueError("new_prose must not be empty")
    next_version = manifest["prose_history"][-1]["version"] + 1
    manifest["prose_history"].append({
        "version": next_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prose": new_prose,
        "revised_by": revised_by,
        "reason": reason,
    })
```

- [ ] **Step 4: Run to verify passes**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_manifest.py -v
```

Expected: all 9 PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/src/creative_vision/manifest.py plugins/jack-tar-deckhand/tests/test_creative_vision_manifest.py
git commit -m "feat(creative-vision): manifest.revise_prose with versioned history (#105)"
```

---

### Task 8: `manifest.append_attempt` + `manifest.finalise`

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/creative_vision/manifest.py`
- Modify: `plugins/jack-tar-deckhand/tests/test_creative_vision_manifest.py`

- [ ] **Step 1: Append failing tests**

```python
# Append to plugins/jack-tar-deckhand/tests/test_creative_vision_manifest.py

from src.creative_vision.manifest import append_attempt, finalise_manifest  # noqa: E402


def _sample_attempt(idx=1, tier="ollama", cost=0.0, cumulative=0.0):
    return {
        "attempt_index": idx,
        "prose_version": 1,
        "tier": tier,
        "text_iterations": [{"prompt_draft": "p", "reviewer_verdict": "pass"}],
        "render": {
            "model": "flux-schnell",
            "resolution": "1024x576",
            "cost_usd": cost,
            "output_path": f"runs/{idx:02d}-{tier}.png",
        },
        "image_reviewer_verdict": "pass",
        "directors_critic_verdict": _valid_verdict_inline(),
        "cumulative_cost_usd": cumulative,
    }


def _valid_verdict_inline():
    return {
        "verdict": "refine_at_tier",
        "per_axis_scores": {"entity_fidelity": 80, "spatial_fidelity": 80, "style_fidelity": 80, "quality": 80, "composition": 80},
        "issues": [],
        "gap_location": "prompt",
        "recommended_action": "x",
        "tier": "ollama",
        "iteration_index": 1,
        "plateau_signal": False,
    }


_LADDER_FIXTURE = ["ollama", "flash_1k", "flash_2k", "flash_4k", "pro_1k", "pro_2k", "pro_4k"]


def test_append_attempt_updates_iterate_slide_hooks():
    m = initialise_manifest(slide_number=3, vision_prose="x", budget_usd=1.0)
    append_attempt(m, _sample_attempt(idx=1, tier="flash_1k", cost=0.067, cumulative=0.067), ladder=_LADDER_FIXTURE)
    assert m["iterate_slide_hooks"]["current_tier"] == "flash_1k"
    assert m["iterate_slide_hooks"]["next_tier_available"] == "flash_2k"
    assert m["iterate_slide_hooks"]["remaining_budget_usd"] == pytest.approx(0.933)
    assert len(m["attempts"]) == 1


def test_append_attempt_preserves_ordering():
    m = initialise_manifest(slide_number=3, vision_prose="x", budget_usd=1.0)
    append_attempt(m, _sample_attempt(idx=1, tier="ollama", cost=0.0, cumulative=0.0), ladder=_LADDER_FIXTURE)
    append_attempt(m, _sample_attempt(idx=2, tier="flash_1k", cost=0.067, cumulative=0.067), ladder=_LADDER_FIXTURE)
    assert [a["attempt_index"] for a in m["attempts"]] == [1, 2]


def test_append_attempt_at_top_of_ladder_clears_next_tier():
    m = initialise_manifest(slide_number=3, vision_prose="x", budget_usd=5.0)
    append_attempt(m, _sample_attempt(idx=1, tier="pro_4k", cost=0.24, cumulative=0.24), ladder=_LADDER_FIXTURE)
    assert m["iterate_slide_hooks"]["next_tier_available"] is None


def test_finalise_manifest_sets_final_block():
    m = initialise_manifest(slide_number=3, vision_prose="x", budget_usd=1.0)
    append_attempt(m, _sample_attempt(idx=1, tier="flash_1k", cost=0.067, cumulative=0.067), ladder=_LADDER_FIXTURE)
    final_verdict = _valid_verdict_inline()
    final_verdict["verdict"] = "pass"
    finalise_manifest(m, image_path="runs/01-flash-1k.png", final_verdict=final_verdict)
    assert m["final"] is not None
    assert m["final"]["image_path"] == "runs/01-flash-1k.png"
    assert m["final"]["accepted_at_tier"] == "flash_1k"
    assert m["final"]["total_cost_usd"] == pytest.approx(0.067)
    assert m["final"]["total_iterations"] == 1
    assert m["final"]["final_verdict"]["verdict"] == "pass"
```

- [ ] **Step 2: Run to verify failure**

Expected: 3 ImportError.

- [ ] **Step 3: Implement**

Append to `manifest.py`:

```python
def _next_tier(current: str, ladder: list[str]) -> str | None:
    if current not in ladder:
        return None
    idx = ladder.index(current)
    return ladder[idx + 1] if idx + 1 < len(ladder) else None


def append_attempt(manifest: dict, attempt: dict, ladder: list[str]) -> None:
    """Append an attempt record and update iterate_slide_hooks accordingly.

    The `ladder` is the cascade tier order — the manifest module is
    intentionally decoupled from cascade.LADDER_DEFAULT so cascade can be
    tested independently. The caller (orchestrator) passes the correct
    ladder based on brand_fidelity routing.

    Reads `manifest['_initial_budget_usd']` (stashed by `initialise_manifest`)
    and recomputes `remaining_budget_usd` as `initial - cumulative`. When
    remaining hits zero, `can_escalate_tier` is flipped off.
    """
    manifest["attempts"].append(attempt)
    hooks = manifest["iterate_slide_hooks"]
    hooks["current_tier"] = attempt["tier"]
    hooks["next_tier_available"] = _next_tier(attempt["tier"], ladder)
    initial_budget = manifest["_initial_budget_usd"]
    hooks["remaining_budget_usd"] = max(0.0, initial_budget - attempt["cumulative_cost_usd"])
    if hooks["remaining_budget_usd"] <= 0.001:
        hooks["can_escalate_tier"] = False


def finalise_manifest(manifest: dict, image_path: str, final_verdict: dict) -> None:
    """Stamp the final block from the manifest's last attempt and final verdict."""
    last = manifest["attempts"][-1]
    manifest["final"] = {
        "image_path": image_path,
        "accepted_at_tier": last["tier"],
        "total_cost_usd": last["cumulative_cost_usd"],
        "total_iterations": len(manifest["attempts"]),
        "final_verdict": final_verdict,
    }
```

**Also update `initialise_manifest` (in `manifest.py`)** to stash `_initial_budget_usd` for later use by `append_attempt`:

```python
def initialise_manifest(slide_number: int, vision_prose: str, budget_usd: float) -> dict:
    # ... existing body ...
    # Add this line just before the return:
    manifest["_initial_budget_usd"] = budget_usd
    return manifest
```

Update the existing Task 6 test `test_initialise_manifest_minimum_shape` to also assert `m["_initial_budget_usd"] == 1.0`. Update the schema validation test (if any) to allow this extra key (the schema doesn't `additionalProperties: false`, so it should still validate — confirm by running tests).

- [ ] **Step 4: Run to verify passes**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_manifest.py -v
```

Expected: all 12 PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/src/creative_vision/manifest.py plugins/jack-tar-deckhand/tests/test_creative_vision_manifest.py
git commit -m "feat(creative-vision): manifest append_attempt + finalise + iterate_slide_hooks update (#105)"
```

---

## Phase 3 — Cascade module

### Task 9: `cascade.ladder_for` — picks the right tier ladder

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/creative_vision/cascade.py`
- Create: `plugins/jack-tar-deckhand/tests/test_creative_vision_cascade.py`

- [ ] **Step 1: Write failing tests**

```python
# plugins/jack-tar-deckhand/tests/test_creative_vision_cascade.py
"""Tests for the creative_vision cascade module (tier ladder, plateau, budget)."""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.cascade import (  # noqa: E402
    DEFAULT_BUDGET_USD,
    DEFAULT_ITERATION_CAPS,
    LADDER_DEFAULT,
    LADDER_RECRAFT,
    TIER_COSTS,
    ladder_for,
)


def test_ladder_for_default_brand_fidelity():
    assert ladder_for("none") == LADDER_DEFAULT
    assert ladder_for("approximate") == LADDER_DEFAULT


def test_ladder_for_exact_brand_fidelity_returns_recraft():
    assert ladder_for("exact") == LADDER_RECRAFT


def test_ladder_default_order_matches_spec():
    assert LADDER_DEFAULT == [
        "ollama", "flash_1k", "flash_2k", "flash_4k",
        "pro_1k", "pro_2k", "pro_4k",
    ]


def test_ladder_recraft_order_matches_spec():
    assert LADDER_RECRAFT == [
        "ollama", "recraft_standard_1k", "recraft_pro_2k", "recraft_pro_4k",
    ]


def test_tier_costs_match_spec():
    assert TIER_COSTS["ollama"] == 0.0
    assert TIER_COSTS["flash_1k"] == 0.067
    assert TIER_COSTS["flash_2k"] == 0.101
    assert TIER_COSTS["flash_4k"] == 0.151
    assert TIER_COSTS["pro_1k"] == 0.134
    assert TIER_COSTS["pro_2k"] == 0.193
    assert TIER_COSTS["pro_4k"] == 0.240
    assert TIER_COSTS["recraft_standard_1k"] == 0.04
    assert TIER_COSTS["recraft_pro_2k"] == 0.25
    assert TIER_COSTS["recraft_pro_4k"] == 0.50


def test_default_iteration_caps_match_spec():
    assert DEFAULT_ITERATION_CAPS == {
        "ollama": 5,
        "flash_1k": 3, "flash_2k": 3, "flash_4k": 3,
        "pro_1k": 2, "pro_2k": 2, "pro_4k": 1,
        "recraft_standard_1k": 3, "recraft_pro_2k": 2, "recraft_pro_4k": 1,
    }


def test_default_budget_matches_spec():
    assert DEFAULT_BUDGET_USD == 1.00
```

- [ ] **Step 2: Run to verify failure**

Expected: ImportError.

- [ ] **Step 3: Implement**

```python
# plugins/jack-tar-deckhand/src/creative_vision/cascade.py
"""Cascade state machine — tier ladders, plateau detection, budget enforcement.

Implements §5 of the spec. Issue #105.
"""
from __future__ import annotations

LADDER_DEFAULT: list[str] = [
    "ollama", "flash_1k", "flash_2k", "flash_4k",
    "pro_1k", "pro_2k", "pro_4k",
]

LADDER_RECRAFT: list[str] = [
    "ollama", "recraft_standard_1k", "recraft_pro_2k", "recraft_pro_4k",
]

TIER_COSTS: dict[str, float] = {
    "ollama": 0.0,
    "flash_1k": 0.067,
    "flash_2k": 0.101,
    "flash_4k": 0.151,
    "pro_1k": 0.134,
    "pro_2k": 0.193,
    "pro_4k": 0.240,
    "recraft_standard_1k": 0.04,
    "recraft_pro_2k": 0.25,
    "recraft_pro_4k": 0.50,
}

DEFAULT_ITERATION_CAPS: dict[str, int] = {
    "ollama": 5,
    "flash_1k": 3, "flash_2k": 3, "flash_4k": 3,
    "pro_1k": 2, "pro_2k": 2, "pro_4k": 1,
    "recraft_standard_1k": 3, "recraft_pro_2k": 2, "recraft_pro_4k": 1,
}

DEFAULT_BUDGET_USD: float = 1.00


def ladder_for(brand_fidelity: str) -> list[str]:
    """Return the cascade tier ladder for the given brand_fidelity value.

    'exact' routes through the Recraft ladder; everything else through the
    default Nano Banana ladder. The two ladders are mutually exclusive per
    slide — mixing within one cascade would shift style mid-iteration.
    """
    if brand_fidelity == "exact":
        return LADDER_RECRAFT
    return LADDER_DEFAULT
```

- [ ] **Step 4: Run to verify passes**

Expected: 7 PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/src/creative_vision/cascade.py plugins/jack-tar-deckhand/tests/test_creative_vision_cascade.py
git commit -m "feat(creative-vision): cascade tier ladders + cost table + iteration cap defaults (#105)"
```

---

### Task 10: `cascade.detect_plateau`

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/creative_vision/cascade.py`
- Modify: `plugins/jack-tar-deckhand/tests/test_creative_vision_cascade.py`

- [ ] **Step 1: Append failing tests**

```python
# Append to plugins/jack-tar-deckhand/tests/test_creative_vision_cascade.py

from src.creative_vision.cascade import detect_plateau  # noqa: E402


def _scores(entity=80, spatial=80, style=80, quality=80, composition=80):
    return {
        "entity_fidelity": entity,
        "spatial_fidelity": spatial,
        "style_fidelity": style,
        "quality": quality,
        "composition": composition,
    }


def test_plateau_false_with_improvement():
    history = [_scores(entity=60), _scores(entity=72)]
    assert detect_plateau(history) is False


def test_plateau_true_when_no_axis_improves_by_5():
    history = [_scores(entity=60, spatial=60), _scores(entity=62, spatial=63), _scores(entity=63, spatial=64)]
    # max delta is 3 on any axis — under 5-point threshold
    assert detect_plateau(history) is True


def test_plateau_false_with_only_one_prior_iteration():
    # Need at least 2 priors to compute a window — return False
    assert detect_plateau([_scores()]) is False


def test_plateau_true_when_scores_degrade():
    history = [_scores(entity=80, spatial=80), _scores(entity=78, spatial=78), _scores(entity=77, spatial=79)]
    # No 5-point improvement on any axis across 2 iterations
    assert detect_plateau(history) is True


def test_plateau_false_when_any_axis_improves_by_5_plus():
    history = [_scores(entity=70), _scores(entity=70), _scores(entity=76)]
    assert detect_plateau(history) is False
```

- [ ] **Step 2: Run to verify failure**

Expected: ImportError.

- [ ] **Step 3: Implement**

Append to `cascade.py`:

```python
_AXES = ("entity_fidelity", "spatial_fidelity", "style_fidelity", "quality", "composition")

PLATEAU_THRESHOLD = 5  # points per axis
PLATEAU_WINDOW = 2     # number of prior iterations to look back


def detect_plateau(score_history: list[dict]) -> bool:
    """Return True if no axis has improved by ≥PLATEAU_THRESHOLD across the last PLATEAU_WINDOW iterations.

    Requires at least PLATEAU_WINDOW+1 entries (current + that many priors).
    Returns False when there's insufficient history to judge.
    """
    if len(score_history) < PLATEAU_WINDOW + 1:
        return False
    window = score_history[-(PLATEAU_WINDOW + 1):]
    earliest = window[0]
    latest = window[-1]
    for axis in _AXES:
        if latest[axis] - earliest[axis] >= PLATEAU_THRESHOLD:
            return False
    return True
```

- [ ] **Step 4: Run to verify passes**

Expected: 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/src/creative_vision/cascade.py plugins/jack-tar-deckhand/tests/test_creative_vision_cascade.py
git commit -m "feat(creative-vision): cascade plateau detection across iteration windows (#105)"
```

---

### Task 11: `cascade.can_afford` + `cascade.next_tier`

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/creative_vision/cascade.py`
- Modify: `plugins/jack-tar-deckhand/tests/test_creative_vision_cascade.py`

- [ ] **Step 1: Append failing tests**

```python
# Append to plugins/jack-tar-deckhand/tests/test_creative_vision_cascade.py

from src.creative_vision.cascade import can_afford, next_tier  # noqa: E402


def test_can_afford_when_budget_covers_next_render():
    assert can_afford(remaining_budget_usd=0.50, tier="flash_2k") is True


def test_can_afford_false_when_budget_short():
    assert can_afford(remaining_budget_usd=0.10, tier="flash_2k") is False


def test_can_afford_ollama_always_true():
    assert can_afford(remaining_budget_usd=0.0, tier="ollama") is True


def test_next_tier_default_ladder():
    assert next_tier("flash_1k", LADDER_DEFAULT) == "flash_2k"


def test_next_tier_top_of_ladder_returns_none():
    assert next_tier("pro_4k", LADDER_DEFAULT) is None


def test_next_tier_clamped_by_allowed_ceiling():
    assert next_tier("flash_1k", LADDER_DEFAULT, allowed_ceiling="flash_4k") == "flash_2k"
    # At the ceiling, no further escalation
    assert next_tier("flash_4k", LADDER_DEFAULT, allowed_ceiling="flash_4k") is None
```

- [ ] **Step 2: Run to verify failure**

Expected: ImportError.

- [ ] **Step 3: Implement**

Append to `cascade.py`:

```python
def can_afford(remaining_budget_usd: float, tier: str) -> bool:
    """Return True when the budget has room for one more render at the given tier."""
    return remaining_budget_usd >= TIER_COSTS[tier] or TIER_COSTS[tier] == 0.0


def next_tier(current: str, ladder: list[str], allowed_ceiling: str | None = None) -> str | None:
    """Return the next tier above ``current`` in the ladder, or None if at top/ceiling."""
    if current not in ladder:
        return None
    idx = ladder.index(current)
    if idx + 1 >= len(ladder):
        return None
    candidate = ladder[idx + 1]
    if allowed_ceiling is not None and allowed_ceiling in ladder:
        if ladder.index(candidate) > ladder.index(allowed_ceiling):
            return None
    return candidate
```

- [ ] **Step 4: Run to verify passes**

Expected: 6 PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/src/creative_vision/cascade.py plugins/jack-tar-deckhand/tests/test_creative_vision_cascade.py
git commit -m "feat(creative-vision): cascade can_afford + next_tier with ceiling clamp (#105)"
```

---

## Phase 4 — Agent definitions + dispatch helpers

### Task 12: `directors-brief.md` agent definition

**Files:**
- Create: `plugins/jack-tar-deckhand/agents/directors-brief.md`
- Create: `plugins/jack-tar-deckhand/tests/test_creative_vision_agent_definitions.py`

- [ ] **Step 1: Write failing test**

```python
# plugins/jack-tar-deckhand/tests/test_creative_vision_agent_definitions.py
"""Smoke tests for the creative_vision agent definition files."""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

AGENTS_DIR = PLUGIN_ROOT / "agents"


def _load_agent(name):
    path = AGENTS_DIR / f"{name}.md"
    assert path.is_file(), f"agent file missing: {path}"
    return path.read_text()


def test_directors_brief_agent_exists_and_has_required_sections():
    content = _load_agent("directors-brief")
    assert "Director's Brief" in content or "Directors Brief" in content
    assert "ParsedVision" in content
    assert "model: sonnet" in content.lower() or "sonnet" in content.lower()
    assert "operator's prose" in content.lower() or "vision prose" in content.lower()
```

- [ ] **Step 2: Run to verify failure**

Expected: FAIL — file missing.

- [ ] **Step 3: Write the agent definition**

Create `plugins/jack-tar-deckhand/agents/directors-brief.md` with content covering: role (Director's Brief), responsibility (consume operator prose + accumulated feedback + tier capabilities → emit ParsedVision + render-ready prompt), model (Sonnet), input contract, output contract, principles (verbatim prose preservation, named-entity fidelity, never grades own output). Reference §3.1 of the spec.

Required content:
- Frontmatter with `name: directors-brief`, `description: ...`, `model: sonnet`
- A section titled "Role" naming "Director's Brief"
- A section "Output contract" referencing the ParsedVision schema and the render-ready prompt
- A section "Inputs" listing: operator's vision prose (verbatim), parsed_vision from prior iteration (if any), accumulated feedback (from Prompt Reviewer / image-reviewer / Critic), current tier + model capabilities, brand-fidelity routing hint
- A section "Principles" with: (a) the prose is verbatim ground truth, (b) preserve named entities across rewrites (catch elements-dropped failure mode), (c) maker is not the judge — never grade own output
- A section "Anti-patterns" with at least: dropping a named entity during refinement; collapsing the prose into a paraphrase; ignoring tier capability hints

- [ ] **Step 4: Run to verify passes**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/agents/directors-brief.md plugins/jack-tar-deckhand/tests/test_creative_vision_agent_definitions.py
git commit -m "feat(creative-vision): directors-brief agent definition (#105)"
```

---

### Task 13: `brief.py` — input preparation + output parsing helpers

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/creative_vision/brief.py`
- Create: `plugins/jack-tar-deckhand/tests/test_creative_vision_brief.py`

- [ ] **Step 1: Write failing tests**

```python
# plugins/jack-tar-deckhand/tests/test_creative_vision_brief.py
"""Tests for the Director's Brief dispatch helper (input/output marshalling)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.brief import build_brief_input, parse_brief_output  # noqa: E402


def test_build_brief_input_includes_prose_verbatim():
    input_blob = build_brief_input(
        vision_prose="Four warships SAP/Databricks/OpenAI/Anthropic.",
        prior_parsed_vision=None,
        accumulated_feedback=[],
        current_tier="ollama",
        brand_fidelity="none",
    )
    assert "Four warships SAP/Databricks/OpenAI/Anthropic." in input_blob


def test_build_brief_input_includes_tier_and_brand_fidelity():
    blob = build_brief_input(
        vision_prose="x",
        prior_parsed_vision=None,
        accumulated_feedback=[],
        current_tier="flash_2k",
        brand_fidelity="exact",
    )
    assert "flash_2k" in blob
    assert "exact" in blob


def test_build_brief_input_carries_feedback():
    blob = build_brief_input(
        vision_prose="x",
        prior_parsed_vision=None,
        accumulated_feedback=["Databricks ship missing", "ensure 4 labels visible"],
        current_tier="ollama",
        brand_fidelity="none",
    )
    assert "Databricks ship missing" in blob
    assert "ensure 4 labels visible" in blob


def test_parse_brief_output_extracts_parsed_vision_and_prompt():
    agent_response = """
```json
{
  "parsed_vision": {
    "schema_version": "1.0",
    "original_prose": "Four warships.",
    "prose_version": 1,
    "subjects": [],
    "spatial_directives": {"setting": null, "layout": null, "containment": null, "named_relationships": []},
    "style": {"explicit": null, "implied": null, "register_inherited_from": null},
    "composition": {"progression_axis": null, "primary_focus": null, "compositional_rules": []},
    "delivery": {"scale": "screen_16x9", "aspect": "16:9", "viewing_context": "projection"},
    "text_density_warning": {"estimated_text_elements": 0, "threshold_breach": false}
  },
  "prompt": "Render four warships..."
}
```
"""
    pv, prompt = parse_brief_output(agent_response)
    assert pv["original_prose"] == "Four warships."
    assert prompt == "Render four warships..."


def test_parse_brief_output_raises_on_missing_keys():
    with pytest.raises(ValueError):
        parse_brief_output('```json\n{"parsed_vision": {}}\n```')
```

- [ ] **Step 2: Run to verify failure**

Expected: ImportError.

- [ ] **Step 3: Implement**

```python
# plugins/jack-tar-deckhand/src/creative_vision/brief.py (overwrite the stub)
"""Director's Brief agent dispatch helpers.

The Director's Brief is the only agent that touches the prompt. This module
prepares its input blob and parses its output back into a (ParsedVision, prompt)
tuple ready for downstream consumers (Prompt Reviewer, Visualizer). Issue #105.
"""
from __future__ import annotations

import json
import re


def build_brief_input(
    vision_prose: str,
    prior_parsed_vision: dict | None,
    accumulated_feedback: list[str],
    current_tier: str,
    brand_fidelity: str,
) -> str:
    """Compose the input blob to dispatch to the directors-brief agent.

    The agent reads a single text input and returns a JSON object. We marshal
    everything it needs (prose verbatim, prior parse if any, feedback, tier,
    brand_fidelity routing hint) into a sectioned blob.
    """
    lines = [
        "# Operator's vision prose (VERBATIM — preserve named entities)",
        vision_prose.strip(),
        "",
        f"# Current tier: {current_tier}",
        f"# Brand fidelity: {brand_fidelity}",
    ]
    if prior_parsed_vision is not None:
        lines.append("")
        lines.append("# Prior ParsedVision (from previous iteration):")
        lines.append("```json")
        lines.append(json.dumps(prior_parsed_vision, indent=2))
        lines.append("```")
    if accumulated_feedback:
        lines.append("")
        lines.append("# Accumulated feedback to address:")
        for item in accumulated_feedback:
            lines.append(f"- {item}")
    lines.append("")
    lines.append("Return a single fenced ```json``` block with keys `parsed_vision` and `prompt`.")
    return "\n".join(lines)


_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def parse_brief_output(agent_response: str) -> tuple[dict, str]:
    """Extract (parsed_vision, prompt) from the agent's response.

    Raises ValueError when the response doesn't contain a JSON fence with both keys.
    """
    m = _FENCE_RE.search(agent_response)
    if m is None:
        raise ValueError("directors-brief response did not contain a ```json``` fence")
    try:
        payload = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"directors-brief JSON parse failed: {e}") from e
    if "parsed_vision" not in payload or "prompt" not in payload:
        raise ValueError("directors-brief response missing parsed_vision or prompt key")
    return payload["parsed_vision"], payload["prompt"]
```

- [ ] **Step 4: Run to verify passes**

Expected: 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/src/creative_vision/brief.py plugins/jack-tar-deckhand/tests/test_creative_vision_brief.py
git commit -m "feat(creative-vision): brief.py input prep + output parse helpers (#105)"
```

---

### Task 14: `prompt-reviewer.md` + `prompt_reviewer.py`

**Files:**
- Create: `plugins/jack-tar-deckhand/agents/prompt-reviewer.md`
- Modify: `plugins/jack-tar-deckhand/src/creative_vision/prompt_reviewer.py`
- Modify: `plugins/jack-tar-deckhand/tests/test_creative_vision_agent_definitions.py`
- Create: `plugins/jack-tar-deckhand/tests/test_creative_vision_prompt_reviewer.py`

- [ ] **Step 1: Append failing test for agent file**

```python
# Append to plugins/jack-tar-deckhand/tests/test_creative_vision_agent_definitions.py


def test_prompt_reviewer_agent_exists_and_has_required_sections():
    content = _load_agent("prompt-reviewer")
    assert "Prompt Reviewer" in content
    assert "haiku" in content.lower()
    assert "pass" in content.lower() and "refine" in content.lower()
    assert "elements" in content.lower()  # checks for dropped-elements detection
```

- [ ] **Step 2: Write failing tests for the dispatch helper**

```python
# plugins/jack-tar-deckhand/tests/test_creative_vision_prompt_reviewer.py
"""Tests for the Prompt Reviewer dispatch helper."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.prompt_reviewer import (  # noqa: E402
    build_reviewer_input,
    parse_reviewer_output,
)


def test_build_reviewer_input_includes_prose_and_prompt():
    blob = build_reviewer_input(
        original_prose="Four warships.",
        proposed_prompt="Render four warships in a battle.",
        parsed_vision={"original_prose": "Four warships."},
    )
    assert "Four warships." in blob
    assert "Render four warships in a battle." in blob


def test_parse_reviewer_output_pass_verdict():
    response = '```json\n{"verdict": "pass", "issues": []}\n```'
    verdict, issues = parse_reviewer_output(response)
    assert verdict == "pass"
    assert issues == []


def test_parse_reviewer_output_refine_with_issues():
    response = '```json\n{"verdict": "refine", "issues": ["Databricks ship label missing"]}\n```'
    verdict, issues = parse_reviewer_output(response)
    assert verdict == "refine"
    assert issues == ["Databricks ship label missing"]


def test_parse_reviewer_output_rejects_invalid_verdict():
    response = '```json\n{"verdict": "maybe", "issues": []}\n```'
    with pytest.raises(ValueError):
        parse_reviewer_output(response)
```

- [ ] **Step 3: Run to verify failure**

Expected: 4 ImportError + 1 file-missing FAIL.

- [ ] **Step 4: Write the agent definition**

Create `plugins/jack-tar-deckhand/agents/prompt-reviewer.md` with:
- Frontmatter: `name: prompt-reviewer`, `model: haiku`
- Role: text-side gate — review the Director's Brief's prompt against the operator's vision and ParsedVision
- Inputs: operator's original prose (verbatim), proposed prompt, parsed vision intermediate
- Output contract: a fenced `json` block with `verdict` ∈ `{pass, refine}` and `issues: string[]`
- Principles: catch dropped named entities (this is the load-bearing failure mode); check density against #91 threshold; check spatial directives preserved; check style cues retained
- Anti-patterns: rubber-stamping; suggesting renderings (not the Reviewer's job — only flag gaps)

- [ ] **Step 5: Implement the dispatch helper**

```python
# plugins/jack-tar-deckhand/src/creative_vision/prompt_reviewer.py (overwrite stub)
"""Prompt Reviewer agent dispatch helpers.

Prepares the input blob for the prompt-reviewer agent and parses its output
into a (verdict, issues) tuple. Issue #105.
"""
from __future__ import annotations

import json
import re


def build_reviewer_input(original_prose: str, proposed_prompt: str, parsed_vision: dict) -> str:
    return "\n".join([
        "# Operator's original vision prose (VERBATIM):",
        original_prose.strip(),
        "",
        "# Proposed render prompt (from Director's Brief):",
        proposed_prompt.strip(),
        "",
        "# Parsed intermediate:",
        "```json",
        json.dumps(parsed_vision, indent=2),
        "```",
        "",
        "Return a single fenced ```json``` block with keys `verdict` (pass|refine) and `issues` (string array).",
    ])


_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def parse_reviewer_output(agent_response: str) -> tuple[str, list[str]]:
    m = _FENCE_RE.search(agent_response)
    if m is None:
        raise ValueError("prompt-reviewer response missing ```json``` fence")
    payload = json.loads(m.group(1))
    verdict = payload.get("verdict")
    if verdict not in ("pass", "refine"):
        raise ValueError(f"prompt-reviewer verdict invalid: {verdict!r}")
    issues = payload.get("issues", [])
    return verdict, issues
```

- [ ] **Step 6: Run to verify passes**

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add plugins/jack-tar-deckhand/agents/prompt-reviewer.md plugins/jack-tar-deckhand/src/creative_vision/prompt_reviewer.py plugins/jack-tar-deckhand/tests/test_creative_vision_agent_definitions.py plugins/jack-tar-deckhand/tests/test_creative_vision_prompt_reviewer.py
git commit -m "feat(creative-vision): prompt-reviewer agent + dispatch helper (#105)"
```

---

### Task 15: `directors-critic.md` + `critic.py`

**Files:**
- Create: `plugins/jack-tar-deckhand/agents/directors-critic.md`
- Modify: `plugins/jack-tar-deckhand/src/creative_vision/critic.py`
- Modify: `plugins/jack-tar-deckhand/tests/test_creative_vision_agent_definitions.py`
- Create: `plugins/jack-tar-deckhand/tests/test_creative_vision_critic.py`

- [ ] **Step 1: Append failing test for agent file**

```python
# Append to plugins/jack-tar-deckhand/tests/test_creative_vision_agent_definitions.py


def test_directors_critic_agent_exists_and_has_required_sections():
    content = _load_agent("directors-critic")
    assert "Director's Critic" in content or "Directors Critic" in content
    assert "sonnet" in content.lower()
    for axis in ("entity_fidelity", "spatial_fidelity", "style_fidelity", "quality", "composition"):
        assert axis in content
    for verdict in ("pass", "refine_at_tier", "escalate_tier", "abort"):
        assert verdict in content
```

- [ ] **Step 2: Write failing tests for the dispatch helper**

```python
# plugins/jack-tar-deckhand/tests/test_creative_vision_critic.py
"""Tests for the Director's Critic dispatch helper."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.critic import build_critic_input, parse_critic_output  # noqa: E402


def test_build_critic_input_includes_prose_image_intermediate():
    blob = build_critic_input(
        original_prose="Four warships.",
        image_path="/tmp/render.png",
        parsed_vision={"original_prose": "Four warships."},
        prior_scores_history=[],
        tier="flash_1k",
        iteration_index=1,
    )
    assert "Four warships." in blob
    assert "/tmp/render.png" in blob
    assert "flash_1k" in blob


def test_parse_critic_output_pass_verdict():
    response = '''```json
{
  "verdict": "pass",
  "per_axis_scores": {"entity_fidelity": 90, "spatial_fidelity": 90, "style_fidelity": 90, "quality": 90, "composition": 90},
  "issues": [],
  "gap_location": "unknown",
  "recommended_action": "ship it",
  "tier": "flash_1k",
  "iteration_index": 1,
  "plateau_signal": false
}
```'''
    verdict = parse_critic_output(response)
    assert verdict["verdict"] == "pass"
    assert verdict["per_axis_scores"]["entity_fidelity"] == 90


def test_parse_critic_output_validates_against_schema():
    response = '''```json
{"verdict": "invalid_value"}
```'''
    with pytest.raises(ValueError):
        parse_critic_output(response)
```

- [ ] **Step 3: Run to verify failure**

Expected: ImportError + file-missing FAIL.

- [ ] **Step 4: Write the agent definition**

Create `plugins/jack-tar-deckhand/agents/directors-critic.md` with:
- Frontmatter: `name: directors-critic`, `model: sonnet`
- Role: image-side vision-fidelity gate
- Inputs: rendered image (path), operator's original prose, ParsedVision, prior score history, current tier, iteration index
- Output contract: a fenced JSON conforming to `directors_critic_verdict.schema.json`
- Per-axis scoring rubric (entity_fidelity / spatial_fidelity / style_fidelity / quality / composition, each 0–100)
- Verdict semantics: pass / refine_at_tier / escalate_tier / abort — define when each fires
- gap_location semantics: prose | prompt | tier | unknown
- Principles: maker is not the judge (Critic never proposes the renderer or the prompt — only evaluates); ground truth is the operator's prose, not the prior iteration
- Anti-patterns: scoring "looks good" without per-axis breakdown; recommending prose revision the operator didn't request

- [ ] **Step 5: Implement the dispatch helper**

```python
# plugins/jack-tar-deckhand/src/creative_vision/critic.py (overwrite stub)
"""Director's Critic agent dispatch helpers. Issue #105."""
from __future__ import annotations

import json
import re
from pathlib import Path

from jsonschema import ValidationError, validate

_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "directors_critic_verdict.schema.json"


def _load_schema():
    with open(_SCHEMA_PATH) as f:
        return json.load(f)


def build_critic_input(
    original_prose: str,
    image_path: str,
    parsed_vision: dict,
    prior_scores_history: list[dict],
    tier: str,
    iteration_index: int,
) -> str:
    return "\n".join([
        "# Operator's original vision prose (VERBATIM):",
        original_prose.strip(),
        "",
        f"# Image to evaluate: {image_path}",
        f"# Current tier: {tier}",
        f"# Iteration index: {iteration_index}",
        "",
        "# Parsed intermediate:",
        "```json",
        json.dumps(parsed_vision, indent=2),
        "```",
        "",
        "# Score history (chronological, most recent last):",
        "```json",
        json.dumps(prior_scores_history, indent=2),
        "```",
        "",
        "Return a single fenced ```json``` block conforming to the DirectorsCriticVerdict schema.",
    ])


_FENCE_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def parse_critic_output(agent_response: str) -> dict:
    m = _FENCE_RE.search(agent_response)
    if m is None:
        raise ValueError("directors-critic response missing ```json``` fence")
    try:
        payload = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"directors-critic JSON parse failed: {e}") from e
    try:
        validate(instance=payload, schema=_load_schema())
    except ValidationError as e:
        raise ValueError(f"directors-critic verdict failed schema: {e.message}") from e
    return payload
```

- [ ] **Step 6: Run to verify passes**

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add plugins/jack-tar-deckhand/agents/directors-critic.md plugins/jack-tar-deckhand/src/creative_vision/critic.py plugins/jack-tar-deckhand/tests/test_creative_vision_agent_definitions.py plugins/jack-tar-deckhand/tests/test_creative_vision_critic.py
git commit -m "feat(creative-vision): directors-critic agent + dispatch helper with schema validation (#105)"
```

---

## Phase 5 — Orchestrator

### Task 16: `orchestrator.advance_text_loop` — Brief ↔ Prompt Reviewer state transitions

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/creative_vision/orchestrator.py`
- Create: `plugins/jack-tar-deckhand/tests/test_creative_vision_orchestrator.py`

- [ ] **Step 1: Write failing tests**

```python
# plugins/jack-tar-deckhand/tests/test_creative_vision_orchestrator.py
"""Tests for the creative_vision orchestrator state machine."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.orchestrator import (  # noqa: E402
    TEXT_ITERATION_CAP,
    TextLoopState,
    advance_text_loop,
)


def test_text_loop_pass_immediately():
    state = TextLoopState(iterations=[])
    state = advance_text_loop(state, reviewer_verdict="pass", reviewer_issues=[], current_prompt="p")
    assert state.terminal is True
    assert state.forced_pass is False
    assert state.approved_prompt == "p"


def test_text_loop_refine_then_pass():
    state = TextLoopState(iterations=[])
    state = advance_text_loop(state, reviewer_verdict="refine", reviewer_issues=["x"], current_prompt="p1")
    assert state.terminal is False
    state = advance_text_loop(state, reviewer_verdict="pass", reviewer_issues=[], current_prompt="p2")
    assert state.terminal is True
    assert state.approved_prompt == "p2"


def test_text_loop_forces_pass_at_cap():
    state = TextLoopState(iterations=[])
    for i in range(TEXT_ITERATION_CAP):
        state = advance_text_loop(state, reviewer_verdict="refine", reviewer_issues=[f"x{i}"], current_prompt=f"p{i}")
    assert state.terminal is True
    assert state.forced_pass is True
```

- [ ] **Step 2: Run to verify failure**

Expected: ImportError.

- [ ] **Step 3: Implement**

```python
# plugins/jack-tar-deckhand/src/creative_vision/orchestrator.py (overwrite stub)
"""Creative-vision orchestrator state machine.

Pure logic — knows nothing about agent dispatch. The SKILL.md drives the agent
calls and invokes these helpers to advance state between dispatches. Issue #105.
"""
from __future__ import annotations

from dataclasses import dataclass, field

TEXT_ITERATION_CAP = 3


@dataclass
class TextLoopState:
    iterations: list[dict] = field(default_factory=list)
    terminal: bool = False
    forced_pass: bool = False
    approved_prompt: str | None = None


def advance_text_loop(
    state: TextLoopState,
    *,
    reviewer_verdict: str,
    reviewer_issues: list[str],
    current_prompt: str,
) -> TextLoopState:
    """Advance the text-side state given the latest Prompt Reviewer verdict.

    Returns a NEW state object; state should be treated as immutable by the caller.
    """
    iterations = state.iterations + [
        {"prompt_draft": current_prompt, "reviewer_verdict": reviewer_verdict,
         "reviewer_feedback": "; ".join(reviewer_issues) if reviewer_issues else ""}
    ]
    if reviewer_verdict == "pass":
        return TextLoopState(iterations=iterations, terminal=True, forced_pass=False, approved_prompt=current_prompt)
    if len(iterations) >= TEXT_ITERATION_CAP:
        return TextLoopState(iterations=iterations, terminal=True, forced_pass=True, approved_prompt=current_prompt)
    return TextLoopState(iterations=iterations, terminal=False, forced_pass=False, approved_prompt=None)
```

- [ ] **Step 4: Run to verify passes**

Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/src/creative_vision/orchestrator.py plugins/jack-tar-deckhand/tests/test_creative_vision_orchestrator.py
git commit -m "feat(creative-vision): orchestrator text-side state machine (#105)"
```

---

### Task 17: `orchestrator.decide_next_action` — image-side decision based on Critic verdict + cascade state

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/creative_vision/orchestrator.py`
- Modify: `plugins/jack-tar-deckhand/tests/test_creative_vision_orchestrator.py`

- [ ] **Step 1: Append failing tests**

```python
# Append to plugins/jack-tar-deckhand/tests/test_creative_vision_orchestrator.py

from src.creative_vision.orchestrator import (  # noqa: E402
    NextAction,
    decide_next_action,
)


def _verdict(verdict="pass", plateau=False):
    return {
        "verdict": verdict,
        "per_axis_scores": {"entity_fidelity": 80, "spatial_fidelity": 80, "style_fidelity": 80, "quality": 80, "composition": 80},
        "issues": [],
        "gap_location": "unknown",
        "recommended_action": "x",
        "tier": "flash_1k",
        "iteration_index": 1,
        "plateau_signal": plateau,
    }


def test_decide_next_action_pass_returns_accept():
    action = decide_next_action(
        critic_verdict=_verdict("pass"),
        current_tier="flash_1k",
        ladder=["ollama", "flash_1k", "flash_2k"],
        remaining_budget_usd=0.5,
        per_tier_iteration_count=1,
        per_tier_cap=3,
        allowed_ceiling="flash_2k",
    )
    assert action.kind == "accept"


def test_decide_next_action_refine_below_cap_returns_refine():
    action = decide_next_action(
        critic_verdict=_verdict("refine_at_tier"),
        current_tier="flash_1k",
        ladder=["ollama", "flash_1k", "flash_2k"],
        remaining_budget_usd=0.5,
        per_tier_iteration_count=1,
        per_tier_cap=3,
        allowed_ceiling="flash_2k",
    )
    assert action.kind == "refine_at_tier"


def test_decide_next_action_refine_at_cap_returns_escalate():
    action = decide_next_action(
        critic_verdict=_verdict("refine_at_tier"),
        current_tier="flash_1k",
        ladder=["ollama", "flash_1k", "flash_2k"],
        remaining_budget_usd=0.5,
        per_tier_iteration_count=3,
        per_tier_cap=3,
        allowed_ceiling="flash_2k",
    )
    assert action.kind == "escalate_tier"
    assert action.next_tier == "flash_2k"


def test_decide_next_action_escalate_when_budget_insufficient_returns_abort():
    action = decide_next_action(
        critic_verdict=_verdict("escalate_tier"),
        current_tier="flash_2k",
        ladder=["ollama", "flash_1k", "flash_2k", "flash_4k"],
        remaining_budget_usd=0.05,  # below flash_4k cost
        per_tier_iteration_count=3,
        per_tier_cap=3,
        allowed_ceiling="flash_4k",
    )
    assert action.kind == "abort"
    assert action.abort_reason == "budget_exhausted"


def test_decide_next_action_escalate_at_top_of_ladder_returns_accept_with_warning():
    action = decide_next_action(
        critic_verdict=_verdict("refine_at_tier"),
        current_tier="pro_4k",
        ladder=["ollama", "flash_1k", "flash_2k", "flash_4k", "pro_1k", "pro_2k", "pro_4k"],
        remaining_budget_usd=10.0,
        per_tier_iteration_count=1,
        per_tier_cap=1,
        allowed_ceiling="pro_4k",
    )
    assert action.kind == "accept"
    assert action.forced is True  # accepted because we're at ceiling and out of iterations


def test_decide_next_action_critic_abort_returns_abort():
    action = decide_next_action(
        critic_verdict=_verdict("abort"),
        current_tier="flash_1k",
        ladder=["ollama", "flash_1k"],
        remaining_budget_usd=0.5,
        per_tier_iteration_count=1,
        per_tier_cap=3,
        allowed_ceiling=None,
    )
    assert action.kind == "abort"
```

- [ ] **Step 2: Run to verify failure**

Expected: ImportError.

- [ ] **Step 3: Implement**

Append to `orchestrator.py`:

```python
from dataclasses import dataclass

from src.creative_vision.cascade import TIER_COSTS, can_afford, next_tier


@dataclass
class NextAction:
    kind: str  # 'refine_at_tier' | 'escalate_tier' | 'accept' | 'abort'
    next_tier: str | None = None
    abort_reason: str | None = None
    forced: bool = False


def decide_next_action(
    *,
    critic_verdict: dict,
    current_tier: str,
    ladder: list[str],
    remaining_budget_usd: float,
    per_tier_iteration_count: int,
    per_tier_cap: int,
    allowed_ceiling: str | None,
) -> NextAction:
    """Decide what to do next based on the Director's Critic verdict + cascade state."""
    verdict = critic_verdict["verdict"]

    if verdict == "pass":
        return NextAction(kind="accept")

    if verdict == "abort":
        return NextAction(kind="abort", abort_reason="critic_abort")

    # refine_at_tier OR escalate_tier — check whether we can stay at this tier
    cap_reached = per_tier_iteration_count >= per_tier_cap

    if verdict == "refine_at_tier" and not cap_reached:
        return NextAction(kind="refine_at_tier")

    # We need to escalate (either Critic said so OR cap reached on refine)
    candidate = next_tier(current_tier, ladder, allowed_ceiling=allowed_ceiling)
    if candidate is None:
        # At the ceiling — forced accept
        return NextAction(kind="accept", forced=True)
    if not can_afford(remaining_budget_usd, candidate):
        return NextAction(kind="abort", abort_reason="budget_exhausted")
    return NextAction(kind="escalate_tier", next_tier=candidate)
```

- [ ] **Step 4: Run to verify passes**

Expected: 6 PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/src/creative_vision/orchestrator.py plugins/jack-tar-deckhand/tests/test_creative_vision_orchestrator.py
git commit -m "feat(creative-vision): orchestrator decide_next_action (image-side state machine) (#105)"
```

---

## Phase 6 — Top-level dispatch

### Task 18: `creative_vision_dispatch.run` — entry-point contract

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/creative_vision_dispatch.py`
- Create: `plugins/jack-tar-deckhand/tests/test_creative_vision_dispatch.py`

- [ ] **Step 1: Write failing tests**

```python
# plugins/jack-tar-deckhand/tests/test_creative_vision_dispatch.py
"""Tests for the top-level creative_vision dispatch entry."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision_dispatch import (  # noqa: E402
    DispatchRequest,
    initialise_dispatch,
)


def test_dispatch_request_minimum_fields():
    req = DispatchRequest(
        deck_dir="/tmp/deck",
        slide_number=3,
        vision_prose="Four ships.",
        budget_usd=1.0,
        allowed_ceiling="pro_4k",
        brand_fidelity="none",
    )
    assert req.deck_dir == "/tmp/deck"
    assert req.slide_number == 3


def test_initialise_dispatch_creates_manifest_on_disk(tmp_path):
    req = DispatchRequest(
        deck_dir=str(tmp_path),
        slide_number=3,
        vision_prose="Four ships.",
        budget_usd=1.0,
        allowed_ceiling="pro_4k",
        brand_fidelity="none",
    )
    manifest = initialise_dispatch(req)
    assert manifest["slide_number"] == 3
    assert (tmp_path / "creative-vision" / "3" / "manifest.json").is_file()


def test_initialise_dispatch_picks_recraft_ladder_when_brand_fidelity_exact(tmp_path):
    req = DispatchRequest(
        deck_dir=str(tmp_path),
        slide_number=3,
        vision_prose="x",
        budget_usd=1.0,
        allowed_ceiling="recraft_pro_4k",
        brand_fidelity="exact",
    )
    manifest = initialise_dispatch(req)
    # next_tier_available should be recraft_standard_1k (next after ollama in the recraft ladder)
    assert manifest["iterate_slide_hooks"]["next_tier_available"] == "recraft_standard_1k"
```

- [ ] **Step 2: Run to verify failure**

Expected: ImportError.

- [ ] **Step 3: Implement**

```python
# plugins/jack-tar-deckhand/src/creative_vision_dispatch.py (overwrite stub)
"""Top-level dispatch entry for creative_vision strategy.

Called by imagegen-bridge for each slide with strategy=creative_vision.
Mirror of paperbanana_dispatch.py — provides a single function the bridge
calls AND a dataclass describing the request. The actual orchestration
loop runs inside SKILL.md (imagegen-bridge), invoking the helpers in
src/creative_vision/ between agent dispatches. Issue #105.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.creative_vision.cascade import ladder_for
from src.creative_vision.manifest import initialise_manifest, save_manifest


@dataclass
class DispatchRequest:
    deck_dir: str
    slide_number: int
    vision_prose: str
    budget_usd: float
    allowed_ceiling: str
    brand_fidelity: str


def initialise_dispatch(req: DispatchRequest) -> dict:
    """Persist a fresh manifest for this slide and return it.

    The orchestration loop (driven by SKILL.md) takes over from here, reading
    the manifest, dispatching agents, and updating the manifest between
    attempts. Pure-logic helpers in src/creative_vision/ are the kernel; the
    SKILL.md is the shell.
    """
    manifest = initialise_manifest(
        slide_number=req.slide_number,
        vision_prose=req.vision_prose,
        budget_usd=req.budget_usd,
    )
    ladder = ladder_for(req.brand_fidelity)
    # Update hooks with the correct ladder's next tier from ollama
    manifest["iterate_slide_hooks"]["next_tier_available"] = ladder[1] if len(ladder) > 1 else None
    save_manifest(req.deck_dir, manifest)
    return manifest
```

- [ ] **Step 4: Run to verify passes**

Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/src/creative_vision_dispatch.py plugins/jack-tar-deckhand/tests/test_creative_vision_dispatch.py
git commit -m "feat(creative-vision): top-level dispatch entry (initialise_dispatch) (#105)"
```

---

## Phase 7 — Skill integrations

### Task 19: Extend `imagegen-bridge/SKILL.md` to dispatch creative_vision

**Files:**
- Modify: `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md`
- Create: `plugins/jack-tar-deckhand/tests/test_creative_vision_skill_integration.py`

- [ ] **Step 1: Write failing test**

```python
# plugins/jack-tar-deckhand/tests/test_creative_vision_skill_integration.py
"""Confirm SKILL.md surfaces document creative_vision dispatch paths."""
from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = PLUGIN_ROOT / "skills"


def _load_skill(name):
    path = SKILLS_DIR / name / "SKILL.md"
    assert path.is_file(), f"SKILL.md missing: {path}"
    return path.read_text()


def test_imagegen_bridge_documents_creative_vision_dispatch():
    text = _load_skill("imagegen-bridge")
    assert "creative_vision" in text
    assert "creative_vision_dispatch" in text or "creative_vision/" in text
    # Must describe the full pipeline loop, not just call the dispatch
    for keyword in ("Director's Brief", "Prompt Reviewer", "Director's Critic", "tier", "cascade"):
        assert keyword in text, f"imagegen-bridge SKILL.md missing keyword: {keyword!r}"
```

- [ ] **Step 2: Run to verify failure**

Expected: FAIL — keywords missing from SKILL.md.

- [ ] **Step 3: Extend `imagegen-bridge/SKILL.md`**

Add a new section near the existing dispatch branches (after the academic_figure / paperbanana branch) titled "Creative vision strategy (#105)" containing:

1. When to enter: `strategy_map.slides[*].strategy == "creative_vision"`.
2. Pre-flight: call `initialise_dispatch(req)` from `src.creative_vision_dispatch`. This creates the manifest at `<deck_dir>/creative-vision/<slide_number>/manifest.json`.
3. The orchestration loop SKILL.md drives, step by step:
   - Loop over cascade tiers starting from `ollama`.
   - At each tier:
     - Build the Brief input via `brief.build_brief_input(...)` — dispatch the `directors-brief` agent (Sonnet) with that input.
     - Parse the Brief output via `brief.parse_brief_output(...)` → `(parsed_vision, prompt)`.
     - Build the Reviewer input via `prompt_reviewer.build_reviewer_input(...)` — dispatch `prompt-reviewer` (Haiku).
     - Parse via `prompt_reviewer.parse_reviewer_output(...)` → `(verdict, issues)`.
     - Advance the text-side state via `orchestrator.advance_text_loop(...)`. If not terminal, re-dispatch the Brief with reviewer issues as feedback. If forced-pass at cap, warn and proceed.
     - When the text loop terminates, render the image at the current tier (Ollama via `jack-tar-ollama:image`; cloud via `jack-tar-cloud:image` with model + resolution from the tier).
     - Dispatch `image-reviewer` on the rendered image. If `refine`, return to the Brief with the visual-quality issues as feedback (NOT directly re-render). Repeat until image-reviewer passes or the per-tier iteration cap is reached.
     - Dispatch `directors-critic`. Parse via `critic.parse_critic_output(...)` (schema-validates).
     - Call `orchestrator.decide_next_action(...)` with the verdict + cascade state.
     - Record the attempt via `manifest.append_attempt(...)` and persist via `save_manifest(...)`.
     - Branch on the next-action kind: `accept` → finalise; `refine_at_tier` → loop back to Brief at same tier; `escalate_tier` → bump tier; `abort` → finalise with best-so-far image, set `final.verdict` from last critic verdict.
4. After loop terminates: fold the final image into the standard ImageManifest entry for this slide so deck-assembler treats it as a normal image.

Document the discipline-hook rule explicitly: never `Read` a generated PNG in this orchestration context — always dispatch image-reviewer to evaluate.

- [ ] **Step 4: Run to verify passes**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md plugins/jack-tar-deckhand/tests/test_creative_vision_skill_integration.py
git commit -m "feat(creative-vision): imagegen-bridge SKILL.md drives creative_vision pipeline loop (#105)"
```

---

### Task 20: Extend `strategy-map/SKILL.md` with vision-aware authoring

**Files:**
- Modify: `plugins/jack-tar-deckhand/skills/strategy-map/SKILL.md`
- Modify: `plugins/jack-tar-deckhand/tests/test_creative_vision_skill_integration.py`

- [ ] **Step 1: Append failing test**

```python
# Append to plugins/jack-tar-deckhand/tests/test_creative_vision_skill_integration.py


def test_strategy_map_documents_creative_vision_authoring():
    text = _load_skill("strategy-map")
    assert "creative_vision" in text
    assert "vision_prose" in text
    # Must explain cost banner / operator opt-in
    for keyword in ("budget", "operator-opt-in", "prose"):
        assert keyword in text.lower(), f"strategy-map SKILL.md missing keyword: {keyword!r}"
```

- [ ] **Step 2: Run to verify failure**

Expected: FAIL — keywords missing.

- [ ] **Step 3: Extend `strategy-map/SKILL.md`**

Add a new section titled "Creative vision authoring (#105)" covering:

1. When to assign `creative_vision`: operator describes a specific rich vision (named entities, spatial directives, style cues, optional within-frame progression). Examples: "four ships SAP/Databricks/OpenAI/Anthropic in a sea battle"; "framework components as cabins inside a man-o-war, 1950s cartoon style".

2. Strategy enum value: `creative_vision`. Always pairs with `full_bleed` assembly. Operator-opt-in only — never auto-classified.

3. Required block on the strategy-map entry:
   ```json
   {
     "strategy": "creative_vision",
     "creative_vision": {
       "vision_prose": "<free-form prose>",
       "budget_usd": 1.00,
       "allowed_ceiling": "pro_4k",
       "iteration_caps_override": null
     }
   }
   ```

4. Cost banner the skill MUST surface before recording the choice:
   ```
   Slide N marked creative_vision. Worst-case spend ~$X.YY per slide.
   Deck currently has K creative_vision slides; deck worst case ~$Z.ZZ.
   Provide vision prose:
   ```

5. Defer-prose pattern: operator may set strategy but leave prose empty with `pending_vision_prose: true` flag; pipeline halts at that slide until prose is provided.

6. Decision tree:
   - **Operator has a specific vision in their head** (named entities / extended metaphor / particular composition) → `creative_vision`.
   - **Operator just wants edge-to-edge chrome stripping with whatever the generic imagegen-bridge produces** → `full_bleed`.
   - **Operator wants generic chrome with overlay text on AI background** → `backdrop_render` / `background`.

- [ ] **Step 4: Run to verify passes**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/skills/strategy-map/SKILL.md plugins/jack-tar-deckhand/tests/test_creative_vision_skill_integration.py
git commit -m "feat(creative-vision): strategy-map SKILL.md vision-aware authoring with cost banner (#105)"
```

---

### Task 21: Extend `iterate_slide_dispatch.py` and `iterate-slide/SKILL.md` for three-channel feedback

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/iterate_slide_dispatch.py`
- Modify: `plugins/jack-tar-deckhand/skills/iterate-slide/SKILL.md`
- Modify: `plugins/jack-tar-deckhand/tests/test_creative_vision_skill_integration.py`
- Create: `plugins/jack-tar-deckhand/tests/test_creative_vision_iterate_slide.py`

- [ ] **Step 1: Append failing test for SKILL.md**

```python
# Append to plugins/jack-tar-deckhand/tests/test_creative_vision_skill_integration.py


def test_iterate_slide_documents_three_channels():
    text = _load_skill("iterate-slide")
    assert "creative_vision" in text
    for channel in ("revise prose", "refine prompt", "escalate tier"):
        assert channel in text.lower()
```

- [ ] **Step 2: Write failing tests for the dispatch helper**

```python
# plugins/jack-tar-deckhand/tests/test_creative_vision_iterate_slide.py
"""Tests for iterate-slide's creative_vision branch."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision.manifest import initialise_manifest, save_manifest  # noqa: E402
from src.iterate_slide_dispatch import (  # noqa: E402
    available_channels_for_creative_vision,
    is_creative_vision_slide,
    revise_prose_action,
)


def test_is_creative_vision_slide_true_when_manifest_present(tmp_path):
    manifest = initialise_manifest(slide_number=3, vision_prose="x", budget_usd=1.0)
    save_manifest(str(tmp_path), manifest)
    assert is_creative_vision_slide(str(tmp_path), slide_number=3) is True


def test_is_creative_vision_slide_false_when_no_manifest(tmp_path):
    assert is_creative_vision_slide(str(tmp_path), slide_number=99) is False


def test_available_channels_returns_all_three_when_budget_remains(tmp_path):
    manifest = initialise_manifest(slide_number=3, vision_prose="x", budget_usd=1.0)
    manifest["iterate_slide_hooks"]["remaining_budget_usd"] = 0.5
    save_manifest(str(tmp_path), manifest)
    channels = available_channels_for_creative_vision(str(tmp_path), slide_number=3)
    assert set(channels) == {"revise_prose", "refine_prompt", "escalate_tier"}


def test_available_channels_excludes_escalate_tier_when_budget_out(tmp_path):
    manifest = initialise_manifest(slide_number=3, vision_prose="x", budget_usd=1.0)
    manifest["iterate_slide_hooks"]["remaining_budget_usd"] = 0.0
    manifest["iterate_slide_hooks"]["can_escalate_tier"] = False
    save_manifest(str(tmp_path), manifest)
    channels = available_channels_for_creative_vision(str(tmp_path), slide_number=3)
    assert "escalate_tier" not in channels
    assert "revise_prose" in channels
    assert "refine_prompt" in channels


def test_revise_prose_action_bumps_version(tmp_path):
    manifest = initialise_manifest(slide_number=3, vision_prose="v1", budget_usd=1.0)
    save_manifest(str(tmp_path), manifest)
    revise_prose_action(str(tmp_path), slide_number=3, new_prose="v2", reason="too vague")
    with open(tmp_path / "creative-vision" / "3" / "manifest.json") as f:
        m = json.load(f)
    assert len(m["prose_history"]) == 2
    assert m["prose_history"][-1]["prose"] == "v2"
```

- [ ] **Step 3: Run to verify failure**

Expected: ImportError / SKILL.md missing keywords.

- [ ] **Step 4: Implement the dispatch helpers**

Append to `plugins/jack-tar-deckhand/src/iterate_slide_dispatch.py` (preserving existing functions — append, do not overwrite):

```python
# --- creative_vision three-channel branch (#105) ---

from src.creative_vision.manifest import load_manifest, revise_prose, save_manifest


def is_creative_vision_slide(deck_dir: str, slide_number: int) -> bool:
    """True when a CreativeVisionManifest exists for this slide."""
    try:
        load_manifest(deck_dir, slide_number)
        return True
    except FileNotFoundError:
        return False


def available_channels_for_creative_vision(deck_dir: str, slide_number: int) -> list[str]:
    """List of channels the operator can choose between right now.

    Channels: 'revise_prose', 'refine_prompt', 'escalate_tier'. The third
    is excluded when the manifest says we're out of budget OR at the ceiling.
    """
    m = load_manifest(deck_dir, slide_number)
    hooks = m["iterate_slide_hooks"]
    channels = []
    if hooks.get("can_revise_prose", True):
        channels.append("revise_prose")
    if hooks.get("can_refine_prompt", True):
        channels.append("refine_prompt")
    if hooks.get("can_escalate_tier", True):
        channels.append("escalate_tier")
    return channels


def revise_prose_action(deck_dir: str, slide_number: int, new_prose: str, reason: str) -> dict:
    """Append a new prose version to the manifest and return the updated manifest.

    Does NOT re-run the pipeline — the caller (SKILL.md) re-invokes the dispatch
    after the prose is updated, which will produce a fresh attempt with the new prose.
    """
    m = load_manifest(deck_dir, slide_number)
    revise_prose(m, new_prose=new_prose, revised_by="operator", reason=reason)
    save_manifest(deck_dir, m)
    return m
```

- [ ] **Step 5: Extend `iterate-slide/SKILL.md`**

Add a new section titled "Creative vision feedback (#105)" with:

1. Detect creative_vision via `is_creative_vision_slide(deck_dir, slide_number)`.
2. If creative_vision, use `available_channels_for_creative_vision(...)` to determine which of the three channels are usable.
3. Channel semantics:
   - **revise_prose** — show current prose to operator; collect revision; call `revise_prose_action(...)` which appends a new prose version. Then re-invoke `creative_vision_dispatch.initialise_dispatch(...)` and run the orchestration loop on the new prose.
   - **refine_prompt** — same tier, same prose; collect operator's note; pass note as additional feedback to the Director's Brief on the next attempt.
   - **escalate_tier** — bump to the next tier in the cascade ladder (gated on remaining budget); continue from the saved manifest state.
4. Mode mapping (existing iterate-slide modes onto these channels):
   - `enumerate` — present all three channels, annotated with the Director's Critic's most recent diagnosis (especially `gap_location`).
   - `auto` — use `gap_location` to pick: `prose` → prompt operator (revise channel needs explicit consent); `prompt` → auto-route to refine; `tier` → auto-route to escalate if budget allows.
   - `draft` — operator writes free-form text; SKILL.md heuristically classifies as prose-revision vs prompt-refinement and confirms with operator.

- [ ] **Step 6: Run to verify passes**

Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add plugins/jack-tar-deckhand/src/iterate_slide_dispatch.py plugins/jack-tar-deckhand/skills/iterate-slide/SKILL.md plugins/jack-tar-deckhand/tests/test_creative_vision_skill_integration.py plugins/jack-tar-deckhand/tests/test_creative_vision_iterate_slide.py
git commit -m "feat(creative-vision): iterate-slide three-channel branch (revise prose / refine prompt / escalate tier) (#105)"
```

---

## Phase 8 — ADR + version bump

### Task 22: ADR `docs/architecture/creative-vision-renderer.md`

**Files:**
- Create: `docs/architecture/creative-vision-renderer.md`
- Create: `tests/test_creative_vision_adr.py` (project-root tests dir, sibling to other ADR tests)

- [ ] **Step 1: Write failing test**

```python
# tests/test_creative_vision_adr.py
"""Smoke test confirming the creative_vision ADR exists and covers required sections."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ADR = REPO_ROOT / "docs" / "architecture" / "creative-vision-renderer.md"


def test_adr_exists():
    assert ADR.is_file()


def test_adr_covers_required_sections():
    text = ADR.read_text()
    for heading in (
        "# Creative Vision Renderer", "## 1. Context", "## 2. Decision",
        "## 3. Architecture", "## 4. Contracts", "## 5. Cascade",
        "## 6. Operator surface", "## 7. Risks", "## 8. Related decisions",
    ):
        assert heading in text, f"ADR missing heading: {heading!r}"


def test_adr_references_companion_documents():
    text = ADR.read_text()
    assert "paperbanana-integration-v2.md" in text
    assert "#88" in text  # full_bleed
    assert "#105" in text
```

- [ ] **Step 2: Run to verify failure**

Expected: file missing.

- [ ] **Step 3: Write the ADR**

Create `docs/architecture/creative-vision-renderer.md` mirroring the structure of `paperbanana-integration-v2.md`. Headings:
- Title + frontmatter (status: Accepted, date 2026-05-21, issue #105)
- `## 1. Context` — the gap (paperbanana for technical, full_bleed for assembly, this for creative vision); summarise the producer/consumer boundary
- `## 2. Decision` — paperbanana-shaped internal pipeline with 3 new agents, `creative_vision` strategy enum value, full_bleed pairing
- `## 3. Architecture` — 4 agents, 2 gates, cascade (link to spec for diagrams)
- `## 4. Contracts` — schemas (link to schemas/ dir)
- `## 5. Cascade economics` — ladder summary + budget defaults
- `## 6. Operator surface` — strategy-map block + /iterate-slide three channels
- `## 7. Risks and trade-offs` — Sonnet × 2 cost, plateau heuristic, Critic calibration
- `## 8. Related decisions` — list of issues + ADRs (paperbanana, full_bleed, register presets)

The ADR is shorter than the spec (the spec is the implementation reference; the ADR is the persistent decision record). 300-500 lines is appropriate.

- [ ] **Step 4: Run to verify passes**

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/architecture/creative-vision-renderer.md tests/test_creative_vision_adr.py
git commit -m "docs(creative-vision): architecture decision record (#105)"
```

---

### Task 23: Plugin version bump 1.4.2 → 1.5.0

**Files:**
- Modify: `plugins/jack-tar-deckhand/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Edit plugin.json**

Change `"version": "1.4.2"` → `"version": "1.5.0"`. Update the description to append `+ creative vision renderer`:

```json
"description": "Full presentation pipeline — brand, style, narrative, images, SmartArt, assembly, QA + academic-figure rendering (optional paperbanana CLI) + /iterate-slide single-slide critique-driven refinement + full_bleed image-is-the-slide strategy + creative vision renderer (#105)",
"version": "1.5.0",
```

- [ ] **Step 2: Edit marketplace.json**

Change deckhand version to 1.5.0; update description to match.

- [ ] **Step 3: Verify versions align**

```bash
grep -E '"version"' plugins/jack-tar-deckhand/.claude-plugin/plugin.json
grep -A 1 "jack-tar-deckhand" .claude-plugin/marketplace.json
```

Expected: both show `1.5.0`.

- [ ] **Step 4: Run the full plugin test suite**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/ -v 2>&1 | tail -10
```

Expected: all tests PASS (baseline 204 + new from this plan ≈ 300+).

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore(jack-tar-deckhand): bump 1.4.2 → 1.5.0 for creative vision renderer (#105)"
```

---

## Phase 9 — End-to-end smoke test + dogfood

### Task 24: Ollama-only E2E smoke test

**Files:**
- Create: `plugins/jack-tar-deckhand/tests/test_creative_vision_e2e.py`

- [ ] **Step 1: Write the test (skipif unless ENABLE_E2E)**

```python
# plugins/jack-tar-deckhand/tests/test_creative_vision_e2e.py
"""End-to-end smoke test for creative_vision pipeline (Ollama-only — $0 spend).

Gated by ENABLE_E2E=1 env var. CI default: skipped.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision_dispatch import DispatchRequest, initialise_dispatch  # noqa: E402

ENABLE_E2E = os.environ.get("ENABLE_E2E") == "1"


@pytest.mark.skipif(not ENABLE_E2E, reason="set ENABLE_E2E=1 to run")
def test_creative_vision_ollama_only_e2e(tmp_path):
    """Spin up a real Ollama dispatch and confirm a manifest is created + at least one Ollama attempt persists.

    Does NOT dispatch real agents (those happen in SKILL.md). This is an integration-of-the-pure-logic test
    that proves DispatchRequest + initialise_dispatch + manifest persistence work end-to-end with a real
    file system + real schemas.
    """
    req = DispatchRequest(
        deck_dir=str(tmp_path),
        slide_number=1,
        vision_prose="A solitary lighthouse on a rocky coast, dramatic stormy sky, watercolor style.",
        budget_usd=0.0,  # Ollama-only — no paid tier reachable
        allowed_ceiling="ollama",
        brand_fidelity="none",
    )
    manifest = initialise_dispatch(req)
    assert manifest["slide_number"] == 1
    assert manifest["iterate_slide_hooks"]["current_tier"] == "ollama"

    # Validate the persisted manifest against its schema
    from jsonschema import validate
    schema_path = PLUGIN_ROOT / "src" / "schemas" / "creative_vision_manifest.schema.json"
    with open(schema_path) as f:
        schema = json.load(f)
    persisted_path = tmp_path / "creative-vision" / "1" / "manifest.json"
    with open(persisted_path) as f:
        persisted = json.load(f)
    validate(instance=persisted, schema=schema)
```

- [ ] **Step 2: Run to verify it skips by default**

```bash
.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_e2e.py -v
```

Expected: 1 SKIPPED.

- [ ] **Step 3: Run it with ENABLE_E2E=1**

```bash
ENABLE_E2E=1 .venv/bin/pytest plugins/jack-tar-deckhand/tests/test_creative_vision_e2e.py -v
```

Expected: 1 PASS.

- [ ] **Step 4: Commit**

```bash
git add plugins/jack-tar-deckhand/tests/test_creative_vision_e2e.py
git commit -m "test(creative-vision): Ollama-only e2e smoke test (gated by ENABLE_E2E) (#105)"
```

---

### Task 25: Dogfood — first real render with a creative vision prose

**Files:**
- Create: `tmp/creative-vision-dogfood/setup_deck.py`
- Create: `docs/superpowers/dogfooding/2026-05-21-creative-vision-renderer.md`

This task validates the pipeline end-to-end with a REAL creative vision prose. Use the **sun-phases example** (operator's third founding example) because it exercises within-frame compositional progression. Budget cap: $0.30 (Flash 1K only — no Pro escalation; confirms cascade works without burning full budget).

- [ ] **Step 1: Create the dogfood setup script**

Mirror the structure of `tmp/full-bleed-dogfood/setup_deck.py` (committed in PR #104) but for a single creative_vision slide. The script writes:
- `outline.json` with one slide (`slide_type: content`, `headline: "Sun phases"`)
- `style-guide.json` (minimal)
- `chart-manifest.json` (empty)
- `speaker-notes.json` (one note)
- `strategy-map.json` with one entry:
  ```json
  {
    "slide_number": 1,
    "strategy": "creative_vision",
    "rationale": "operator-directed: sun phases progression",
    "render_funnel": ["ollama", "cloud_low", "cloud_full"],
    "brand_fidelity": "none",
    "creative_vision": {
      "vision_prose": "A horizontal progression showing the phases of a sun's life: protostar, main sequence, red giant, supernova, neutron star. Five distinct stages reading left-to-right, each visibly larger and more dramatic than the previous. Watercolour or oil-painting style, deep cosmic backdrop, scientifically evocative not literal.",
      "budget_usd": 0.30,
      "allowed_ceiling": "flash_1k",
      "iteration_caps_override": null
    }
  }
  ```

- [ ] **Step 2: Initialise the manifest via dispatch**

```bash
.venv/bin/python tmp/creative-vision-dogfood/setup_deck.py
.venv/bin/python -c "
import sys; sys.path.insert(0, 'plugins/jack-tar-deckhand')
from src.creative_vision_dispatch import DispatchRequest, initialise_dispatch
req = DispatchRequest(
    deck_dir='tmp/creative-vision-dogfood/deck',
    slide_number=1,
    vision_prose=open('tmp/creative-vision-dogfood/deck/strategy-map.json').read() and __import__('json').load(open('tmp/creative-vision-dogfood/deck/strategy-map.json'))['slides'][0]['creative_vision']['vision_prose'],
    budget_usd=0.30, allowed_ceiling='flash_1k', brand_fidelity='none',
)
m = initialise_dispatch(req)
print('manifest run_id:', m['run_id'])
"
```

Expected: manifest persisted at `tmp/creative-vision-dogfood/deck/creative-vision/1/manifest.json`.

- [ ] **Step 3: Manually dispatch one full cascade tier (operator-driven)**

Per the SKILL.md instructions in imagegen-bridge, dispatch the Director's Brief → Prompt Reviewer → Visualizer (Ollama) → image-reviewer → Director's Critic loop ONCE for slide 1 at the Ollama tier. Update the manifest after each step.

In Claude Code, the operator runs the orchestration manually (or via a wrapper skill that drives the loop). This task is the FIRST manual rehearsal — discover any SKILL.md ambiguities and fix them in-flight.

- [ ] **Step 4: Inspect the rendered image via subagent**

Dispatch a `general-purpose` subagent to evaluate the Ollama-rendered image against the vision prose. Subagent reads the PNG (it's their job — the discipline hook applies to the orchestration session, not to the subagent's session). Subagent verdict captured.

- [ ] **Step 5: Log the dogfood**

Create `docs/superpowers/dogfooding/2026-05-21-creative-vision-renderer.md` documenting:
- Method, expected behaviour, actual behaviour
- Subagent verdict on the rendered image
- Findings — anything ambiguous in SKILL.md that needed clarification mid-flight
- Total spend ($0 for Ollama-only; potentially $0.067 if cascade escalated to Flash 1K)
- Whether the manifest captured the run faithfully (load it, schema-validate it, sanity-check the prose history + attempts + iterate_slide_hooks)
- Any code paths the dogfood exposed as buggy → file follow-up issues

- [ ] **Step 6: Commit the dogfood artifacts**

```bash
git add docs/superpowers/dogfooding/2026-05-21-creative-vision-renderer.md
# Note: tmp/ is gitignored; only the log gets committed
git commit -m "docs(dogfood): first creative_vision render — sun phases progression (#105)"
```

---

## Self-review checklist

After completing all tasks, verify:

- [ ] **Spec coverage:** Every section of `2026-05-21-creative-vision-renderer-design.md` has at least one task implementing it.
  - §2 Design principles → enforced through structure of subsequent tasks
  - §3 Architecture → Tasks 12–17 (agents + orchestrator)
  - §4 Contracts → Tasks 1–4 (schemas)
  - §5 Cascade economics → Tasks 9–11 (cascade module)
  - §6 Operator surface → Tasks 19–21 (skill integrations)
  - §7 Code organisation → Tasks 5, 18 (skeleton + dispatch)
  - §8 Testing → present at every task
  - §9 Future paths → not implemented (deferred); §10 Risks → ADR Task 22
- [ ] **No placeholders:** No `TBD` / `TODO` / `add error handling later` anywhere.
- [ ] **Type consistency:** `ParsedVision` fields used consistently. `DirectorsCriticVerdict` field names match across schema, parser, orchestrator. `TIER_COSTS` keys match the cascade ladder identifiers used in strategy-map schema's `allowed_ceiling` enum.
- [ ] **Test count target:** Plan adds ~80 unit + ~20 integration + 1 e2e (skipped by default). Verify by running `.venv/bin/pytest plugins/jack-tar-deckhand/tests/ -v 2>&1 | tail -5` after all tasks.
- [ ] **Plugin version aligned:** plugin.json AND marketplace.json both at 1.5.0; CI JSON-validation passes.
- [ ] **Branch state:** `feat/creative-page-renderer` has 25 atomic commits, all tests green, ready for PR.

## Execution handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-21-creative-vision-renderer.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — Dispatch a fresh subagent per task. Review between tasks. Fast iteration. Best for the heavier tasks (12–17) where the agent definitions need careful prompt writing.

2. **Inline Execution** — Execute tasks in this session using executing-plans. Batch execution with checkpoints for review.

Which approach?
