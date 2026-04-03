# SmartArt Intelligent Graphics — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement AI-driven templated graphic generation that renders flowcharts, matrices, charts, diagrams, and infographics from structured data using three rendering engines (Mermaid.js, Vega-Lite, Custom SVG) with optional AI enrichment.

**Architecture:** Federated approach — new SmartArt selector agent + extractor/renderer Python modules + custom SVG engine, integrated with the existing deck-conductor pipeline. Reuses imagegen-bridge for enrichment, image-reviewer for quality scoring, and budget/provider infrastructure. Draft-phase comparator runs competing engines, locks winner for production.

**Tech Stack:** Python 3 (extractor, renderer, SVG engine, QA), Node.js (Mermaid CLI, Vega-Lite CLI, assembler), JSON Schema, Sharp (compositing), pytest

**Design Spec:** `docs/superpowers/specs/2026-04-03-smartart-intelligent-graphics-design.md`
**GitHub Issue:** #17
**BSA Version:** v1.4.0 (canonical model and architecture docs already updated)

---

## File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `src/schemas/smartart_recommendations.schema.json` | Selector output contract |
| `src/schemas/smartart_spec.schema.json` | Extractor output contract |
| `src/schemas/smartart_manifest.schema.json` | Renderer output contract |
| `src/schemas/smartart_comparator.schema.json` | Comparator results (embedded in manifest) |
| `src/smartart_extractor.py` | Content → engine-specific data transformation |
| `src/smartart_renderer.py` | Engine dispatch, comparator, enrichment compositing |
| `src/smartart_svg/__init__.py` | Public API: `render_custom_svg(spec, style)` |
| `src/smartart_svg/engine.py` | Container constraint engine |
| `src/smartart_svg/primitives.py` | SVG element builders |
| `src/smartart_svg/tokens.py` | StyleGuide → SVG attributes + contrast resolver |
| `src/smartart_svg/layouts/__init__.py` | Layout registry |
| `src/smartart_svg/layouts/swot.py` | SWOT 2×2 quadrant layout |
| `src/smartart_svg/layouts/feature_matrix.py` | N×M grid layout |
| `src/smartart_svg/layouts/venn.py` | 2-3 circle overlap layout |
| `src/smartart_svg/layouts/timeline.py` | Horizontal sequential layout |
| `src/smartart_svg/layouts/pipeline_funnel.py` | Tapered funnel layout |
| `src/qa/checks/smartart_checks.py` | 5 SmartArt QA checks (SA-01 to SA-05) |
| `.claude/agents/smartart-selector.md` | SmartArt Selector AI persona definition |
| `tests/test_smartart_extractor.py` | Extractor tests |
| `tests/test_smartart_renderer.py` | Renderer tests |
| `tests/test_smartart_svg.py` | Custom SVG engine tests |
| `tests/test_smartart_qa.py` | SmartArt QA check tests |
| `tests/test_smartart_schemas.py` | Schema validation tests |

### Modified Files

| File | Change |
|------|--------|
| `src/schemas/slide_outline.schema.json` | Add optional `visual_intent` field |
| `src/schemas/strategy_map.schema.json` | Add `smartart` strategy + `smartart_config` |
| `src/schemas/image_manifest.schema.json` | Add optional `smartart_ref` field |
| `src/schemas/qa_report.schema.json` | Add `smartart` to category enum |
| `src/deckcontext.py` | Add 3 new steps to DEFAULT_STEP_ORDER, 3 new contract schemas |
| `src/conductor.py` | Register new steps in state machine |
| `src/slide_prompt_composer.py` | Add `smartart` strategy classification |
| `src/image_router.py` | Add enrichment routing with `smartart_ref` |
| `src/assembler/build_deck.js` | Add `buildSmartArtSlide()` function |
| `src/qa/run_qa.py` | Register SmartArt checks |
| `package.json` | Add mermaid-cli, vega-lite, vega-cli dependencies |

---

## Task 1: Install Node.js Dependencies

**Files:**
- Modify: `package.json`

- [ ] **Step 1: Install mermaid-cli, vega-lite, and vega-cli**

```bash
cd /Users/stevejones/Documents/Development/jack-tar-deckhand
npm install @mermaid-js/mermaid-cli vega-lite vega-cli vega
```

- [ ] **Step 2: Verify CLI tools are accessible**

```bash
npx mmdc --version
npx vl2svg --help 2>&1 | head -1
```

Expected: Version numbers for both tools.

- [ ] **Step 3: Commit**

```bash
git add package.json package-lock.json
git commit -m "chore: add mermaid-cli, vega-lite, vega-cli dependencies for SmartArt"
```

---

## Task 2: New Schemas (4) + Modified Schemas (4)

**Files:**
- Create: `src/schemas/smartart_recommendations.schema.json`
- Create: `src/schemas/smartart_spec.schema.json`
- Create: `src/schemas/smartart_manifest.schema.json`
- Create: `src/schemas/smartart_comparator.schema.json`
- Modify: `src/schemas/slide_outline.schema.json`
- Modify: `src/schemas/strategy_map.schema.json`
- Modify: `src/schemas/image_manifest.schema.json`
- Modify: `src/schemas/qa_report.schema.json`
- Create: `tests/test_smartart_schemas.py`

- [ ] **Step 1: Write schema validation tests**

```python
# tests/test_smartart_schemas.py
"""Tests for SmartArt JSON schemas — validates both structure and sample data."""

import json
import os
import pytest
import jsonschema

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'schemas')


def _load_schema(name):
    with open(os.path.join(SCHEMA_DIR, name)) as f:
        return json.load(f)


class TestSmartArtRecommendationsSchema:
    def test_valid_recommendation(self):
        schema = _load_schema('smartart_recommendations.schema.json')
        doc = {
            "slides": [
                {
                    "slide_number": 5,
                    "recommendations": [
                        {
                            "graphic_type": "flowchart",
                            "enrichment_tier": "ai_background",
                            "engine": "mermaid",
                            "rationale": "Sequential process suits flowchart",
                            "confidence": 0.85,
                            "data_hint": "4 sequential steps"
                        }
                    ],
                    "approval_status": "approved",
                    "selected_index": 0
                }
            ]
        }
        jsonschema.validate(doc, schema)

    def test_rejects_invalid_graphic_type(self):
        schema = _load_schema('smartart_recommendations.schema.json')
        doc = {
            "slides": [
                {
                    "slide_number": 1,
                    "recommendations": [
                        {
                            "graphic_type": "invalid_type",
                            "enrichment_tier": "pure_programmatic",
                            "engine": "mermaid",
                            "rationale": "test",
                            "confidence": 0.5,
                            "data_hint": "test"
                        }
                    ],
                    "approval_status": "pending"
                }
            ]
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(doc, schema)


class TestSmartArtSpecSchema:
    def test_valid_mermaid_spec(self):
        schema = _load_schema('smartart_spec.schema.json')
        doc = {
            "specs": [
                {
                    "slide_number": 5,
                    "graphic_type": "flowchart",
                    "engine": "mermaid",
                    "enrichment_tier": "ai_background",
                    "data": {
                        "syntax": "graph TD\n  A[Research] --> B[Design]",
                        "diagram_type": "flowchart",
                        "node_count": 2
                    },
                    "overflow_applied": "none",
                    "style_tokens": {
                        "primary_color": "#1a73e8",
                        "font_family": "Inter"
                    },
                    "validation_status": "valid",
                    "comparator_engines": ["mermaid", "custom_svg"]
                }
            ]
        }
        jsonschema.validate(doc, schema)

    def test_valid_custom_svg_spec(self):
        schema = _load_schema('smartart_spec.schema.json')
        doc = {
            "specs": [
                {
                    "slide_number": 3,
                    "graphic_type": "swot",
                    "engine": "custom_svg",
                    "enrichment_tier": "pure_programmatic",
                    "data": {
                        "quadrants": [
                            {"label": "Strengths", "position": "top_left", "items": ["Brand"]},
                            {"label": "Weaknesses", "position": "top_right", "items": ["Scale"]},
                            {"label": "Opportunities", "position": "bottom_left", "items": ["AI"]},
                            {"label": "Threats", "position": "bottom_right", "items": ["Regulation"]}
                        ]
                    },
                    "overflow_applied": "none",
                    "style_tokens": {"primary_color": "#2B6CB0", "font_family": "Arial"},
                    "validation_status": "valid",
                    "comparator_engines": []
                }
            ]
        }
        jsonschema.validate(doc, schema)


class TestSmartArtManifestSchema:
    def test_valid_manifest_entry(self):
        schema = _load_schema('smartart_manifest.schema.json')
        doc = {
            "graphics": [
                {
                    "smartart_id": "sa-slide-5-flowchart",
                    "slide_number": 5,
                    "graphic_type": "flowchart",
                    "engine_used": "mermaid",
                    "enrichment_tier": "ai_background",
                    "file_path": "./tmp/deck/smartart/slide-5-flowchart.png",
                    "status": "rendered",
                    "dimensions": {"width": 1920, "height": 1080},
                    "alt_text": "Flowchart showing process"
                }
            ]
        }
        jsonschema.validate(doc, schema)


class TestModifiedSchemas:
    def test_slide_outline_accepts_visual_intent(self):
        schema = _load_schema('slide_outline.schema.json')
        doc = {
            "narrative_arc": "situation-complication-resolution",
            "estimated_duration_minutes": 20,
            "slides": [
                {
                    "slide_number": 1,
                    "slide_type": "content",
                    "headline": "Our Process",
                    "visual_intent": "Show the 4-step process as a flowchart",
                    "body_points": ["Research", "Design", "Build", "Launch"]
                }
            ]
        }
        jsonschema.validate(doc, schema)

    def test_strategy_map_accepts_smartart_strategy(self):
        schema = _load_schema('strategy_map.schema.json')
        doc = {
            "approval_mode": "review",
            "slides": [
                {
                    "slide_number": 5,
                    "strategy": "smartart",
                    "rationale": "Process flow suits flowchart",
                    "render_funnel": [],
                    "smartart_config": {
                        "graphic_type": "flowchart",
                        "enrichment_tier": "ai_background",
                        "engine": "mermaid",
                        "comparator_engines": ["mermaid", "custom_svg"]
                    }
                }
            ]
        }
        jsonschema.validate(doc, schema)

    def test_image_manifest_accepts_smartart_ref(self):
        schema = _load_schema('image_manifest.schema.json')
        doc = {
            "images": [
                {
                    "image_id": "img-slide-5-bg-001",
                    "slide_number": 5,
                    "file_path": "./tmp/deck/images/slide-5-bg.png",
                    "status": "generated",
                    "smartart_ref": "sa-slide-5-flowchart"
                }
            ]
        }
        jsonschema.validate(doc, schema)

    def test_qa_report_accepts_smartart_category(self):
        schema = _load_schema('qa_report.schema.json')
        doc = {
            "verdict": "pass",
            "findings": [
                {
                    "slide_number": 5,
                    "severity": "warning",
                    "category": "smartart",
                    "description": "SA-02: Font size 15px below recommended 16px minimum"
                }
            ]
        }
        jsonschema.validate(doc, schema)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/pytest tests/test_smartart_schemas.py -v
```

Expected: FAIL — schema files don't exist yet.

- [ ] **Step 3: Create the 4 new schemas**

Create `src/schemas/smartart_recommendations.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/smartart-recommendations.json",
  "title": "SmartArtRecommendations",
  "description": "Per-slide graphic type and enrichment tier recommendations from the SmartArt selector.",
  "type": "object",
  "required": ["slides"],
  "properties": {
    "created_at": {"type": "string"},
    "slides": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["slide_number", "recommendations", "approval_status"],
        "properties": {
          "slide_number": {"type": "integer", "minimum": 1},
          "recommendations": {
            "type": "array",
            "minItems": 1,
            "maxItems": 3,
            "items": {
              "type": "object",
              "required": ["graphic_type", "enrichment_tier", "engine", "rationale", "confidence", "data_hint"],
              "properties": {
                "graphic_type": {
                  "type": "string",
                  "enum": ["flowchart", "decision_tree", "bar_chart", "line_chart", "radar_chart", "swot", "feature_matrix", "venn", "timeline", "pipeline_funnel", "gantt", "none"]
                },
                "enrichment_tier": {
                  "type": "string",
                  "enum": ["pure_programmatic", "ai_background", "ai_elements", "full_ai_render"]
                },
                "engine": {
                  "type": "string",
                  "enum": ["mermaid", "vega_lite", "matplotlib", "custom_svg"]
                },
                "rationale": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "data_hint": {"type": "string"}
              }
            }
          },
          "approval_status": {
            "type": "string",
            "enum": ["pending", "approved", "rejected", "fallback_composed"]
          },
          "selected_index": {"type": "integer", "minimum": 0},
          "narrative_feedback": {"type": "string"}
        }
      }
    }
  }
}
```

Create `src/schemas/smartart_spec.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/smartart-spec.json",
  "title": "SmartArtSpec",
  "description": "Engine-specific structured data for SmartArt rendering.",
  "type": "object",
  "required": ["specs"],
  "properties": {
    "created_at": {"type": "string"},
    "specs": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["slide_number", "graphic_type", "engine", "enrichment_tier", "data", "overflow_applied", "style_tokens", "validation_status"],
        "properties": {
          "slide_number": {"type": "integer", "minimum": 1},
          "graphic_type": {
            "type": "string",
            "enum": ["flowchart", "decision_tree", "bar_chart", "line_chart", "radar_chart", "swot", "feature_matrix", "venn", "timeline", "pipeline_funnel", "gantt"]
          },
          "engine": {
            "type": "string",
            "enum": ["mermaid", "vega_lite", "matplotlib", "custom_svg"]
          },
          "enrichment_tier": {
            "type": "string",
            "enum": ["pure_programmatic", "ai_background", "ai_elements", "full_ai_render"]
          },
          "data": {"type": "object"},
          "overflow_applied": {
            "type": "string",
            "enum": ["none", "truncate", "paginate", "summarise", "reject"]
          },
          "style_tokens": {
            "type": "object",
            "properties": {
              "primary_color": {"type": "string"},
              "font_family": {"type": "string"},
              "node_shape": {"type": "string"}
            }
          },
          "validation_status": {
            "type": "string",
            "enum": ["valid", "invalid", "overflow"]
          },
          "comparator_engines": {
            "type": "array",
            "items": {
              "type": "string",
              "enum": ["mermaid", "vega_lite", "matplotlib", "custom_svg"]
            }
          }
        }
      }
    }
  }
}
```

Create `src/schemas/smartart_manifest.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/smartart-manifest.json",
  "title": "SmartArtManifest",
  "description": "Registry of rendered SmartArt graphics with comparator results.",
  "type": "object",
  "required": ["graphics"],
  "properties": {
    "generated_at": {"type": "string"},
    "graphics": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["smartart_id", "slide_number", "graphic_type", "engine_used", "enrichment_tier", "file_path", "status"],
        "properties": {
          "smartart_id": {"type": "string"},
          "slide_number": {"type": "integer", "minimum": 1},
          "graphic_type": {
            "type": "string",
            "enum": ["flowchart", "decision_tree", "bar_chart", "line_chart", "radar_chart", "swot", "feature_matrix", "venn", "timeline", "pipeline_funnel", "gantt"]
          },
          "engine_used": {
            "type": "string",
            "enum": ["mermaid", "vega_lite", "matplotlib", "custom_svg"]
          },
          "enrichment_tier": {
            "type": "string",
            "enum": ["pure_programmatic", "ai_background", "ai_elements", "full_ai_render"]
          },
          "file_path": {"type": "string"},
          "svg_source_path": {"type": "string"},
          "status": {
            "type": "string",
            "enum": ["rendered", "compared", "enriched", "failed"]
          },
          "dimensions": {
            "type": "object",
            "properties": {
              "width": {"type": "integer"},
              "height": {"type": "integer"}
            }
          },
          "node_count": {"type": "integer"},
          "alt_text": {"type": "string"},
          "content_hash": {"type": "string"},
          "comparator_results": {
            "$ref": "#/$defs/comparator"
          },
          "enrichment_refs": {
            "type": "array",
            "items": {"type": "string"}
          },
          "review_summary": {"type": "string"}
        }
      }
    }
  },
  "$defs": {
    "comparator": {
      "type": "object",
      "properties": {
        "candidates": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["engine", "score"],
            "properties": {
              "engine": {"type": "string"},
              "score": {"type": "number", "minimum": 0, "maximum": 1},
              "file_path": {"type": "string"}
            }
          }
        },
        "winner": {"type": "string"},
        "phase": {
          "type": "string",
          "enum": ["draft", "production"]
        }
      }
    }
  }
}
```

Create `src/schemas/smartart_comparator.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/smartart-comparator.json",
  "title": "SmartArtComparator",
  "description": "Comparator results for draft-phase multi-engine rendering.",
  "type": "object",
  "required": ["candidates", "winner", "phase"],
  "properties": {
    "candidates": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["engine", "score"],
        "properties": {
          "engine": {
            "type": "string",
            "enum": ["mermaid", "vega_lite", "matplotlib", "custom_svg"]
          },
          "score": {"type": "number", "minimum": 0, "maximum": 1},
          "file_path": {"type": "string"},
          "criteria_scores": {
            "type": "object",
            "properties": {
              "data_legibility": {"type": "number"},
              "layout_clarity": {"type": "number"},
              "aesthetic_quality": {"type": "number"},
              "style_compliance": {"type": "number"}
            }
          }
        }
      }
    },
    "winner": {
      "type": "string",
      "enum": ["mermaid", "vega_lite", "matplotlib", "custom_svg"]
    },
    "phase": {
      "type": "string",
      "enum": ["draft", "production"]
    }
  }
}
```

- [ ] **Step 4: Modify the 4 existing schemas**

In `src/schemas/slide_outline.schema.json`, add `visual_intent` to the per-slide properties:

```json
"visual_intent": {
  "type": "string",
  "description": "Natural language description of the visual the speaker wants for this slide, used by smartart-selector"
}
```

In `src/schemas/strategy_map.schema.json`:
- Add `"smartart"` to the `strategy` enum array
- Add `"smartart"` to the `speaker_override` enum array
- Add `smartart_config` property to the per-slide object:

```json
"smartart_config": {
  "type": "object",
  "properties": {
    "graphic_type": {
      "type": "string",
      "enum": ["flowchart", "decision_tree", "bar_chart", "line_chart", "radar_chart", "swot", "feature_matrix", "venn", "timeline", "pipeline_funnel", "gantt", "none"]
    },
    "enrichment_tier": {
      "type": "string",
      "enum": ["pure_programmatic", "ai_background", "ai_elements", "full_ai_render"]
    },
    "engine": {
      "type": "string",
      "enum": ["mermaid", "vega_lite", "matplotlib", "custom_svg"]
    },
    "comparator_engines": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["mermaid", "vega_lite", "matplotlib", "custom_svg"]
      }
    }
  }
}
```

In `src/schemas/image_manifest.schema.json`, add to per-image properties:

```json
"smartart_ref": {
  "type": "string",
  "description": "Links this enrichment image to a SmartArt graphic ID"
}
```

In `src/schemas/qa_report.schema.json`, add `"smartart"` to the `category` enum array.

- [ ] **Step 5: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_smartart_schemas.py -v
```

Expected: All tests PASS.

- [ ] **Step 6: Run existing schema tests to verify no regressions**

```bash
.venv/bin/pytest tests/test_schemas.py tests/test_deckcontext.py -v
```

Expected: All existing tests still PASS.

- [ ] **Step 7: Commit**

```bash
git add src/schemas/ tests/test_smartart_schemas.py
git commit -m "feat: add 4 SmartArt schemas + extend 4 existing schemas"
```

---

## Task 3: Pipeline Integration — DeckContext + Conductor

**Files:**
- Modify: `src/deckcontext.py`
- Modify: `src/conductor.py`
- Modify: `tests/test_deckcontext.py`
- Modify: `tests/test_conductor.py`

- [ ] **Step 1: Write tests for new step order and contract schemas**

Add to `tests/test_deckcontext.py`:

```python
def test_default_step_order_includes_smartart_steps():
    from src.deckcontext import DEFAULT_STEP_ORDER
    assert 'smartart-selector' in DEFAULT_STEP_ORDER
    assert 'smartart-extractor' in DEFAULT_STEP_ORDER
    assert 'smartart-renderer' in DEFAULT_STEP_ORDER
    # Verify ordering
    selector_idx = DEFAULT_STEP_ORDER.index('smartart-selector')
    strategy_idx = DEFAULT_STEP_ORDER.index('strategy-map')
    extractor_idx = DEFAULT_STEP_ORDER.index('smartart-extractor')
    renderer_idx = DEFAULT_STEP_ORDER.index('smartart-renderer')
    bridge_idx = DEFAULT_STEP_ORDER.index('imagegen-bridge')
    assert selector_idx < strategy_idx, "selector must be before strategy-map"
    assert extractor_idx > strategy_idx, "extractor must be after strategy-map"
    assert renderer_idx > bridge_idx, "renderer must be after imagegen-bridge"


def test_contract_schemas_include_smartart():
    from src.deckcontext import CONTRACT_SCHEMAS
    assert 'smartart-recommendations' in CONTRACT_SCHEMAS
    assert 'smartart-spec' in CONTRACT_SCHEMAS
    assert 'smartart-manifest' in CONTRACT_SCHEMAS
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/pytest tests/test_deckcontext.py::test_default_step_order_includes_smartart_steps tests/test_deckcontext.py::test_contract_schemas_include_smartart -v
```

Expected: FAIL — steps and schemas not registered yet.

- [ ] **Step 3: Update deckcontext.py**

In `src/deckcontext.py`, update `CONTRACT_SCHEMAS` to add:

```python
'smartart-recommendations': 'smartart_recommendations.schema.json',
'smartart-spec': 'smartart_spec.schema.json',
'smartart-manifest': 'smartart_manifest.schema.json',
```

Update `DEFAULT_STEP_ORDER` to:

```python
DEFAULT_STEP_ORDER = [
    'validate-brief',
    'brand-manager',
    'slide-stylist',
    'narrative-architect',
    'smartart-selector',
    'strategy-map',
    'smartart-extractor',
    'speaker-notes-writer',
    'imagegen-bridge',
    'smartart-renderer',
    'chart-renderer',
    'deck-assembler',
    'deck-qa',
]
```

In `init_deck()`, add smartart output directory:

```python
os.makedirs(os.path.join(deck_dir, 'smartart'), exist_ok=True)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_deckcontext.py -v
```

Expected: All tests PASS (new + existing).

- [ ] **Step 5: Write conductor test for new step registration**

Add to `tests/test_conductor.py`:

```python
def test_init_pipeline_includes_smartart_steps():
    import tempfile, os
    from src.conductor import init_pipeline
    with tempfile.TemporaryDirectory() as d:
        init_pipeline(d)
        import json
        with open(os.path.join(d, 'pipeline-state.json')) as f:
            state = json.load(f)
        assert 'smartart-selector' in state['steps']
        assert 'smartart-extractor' in state['steps']
        assert 'smartart-renderer' in state['steps']
        assert state['steps']['smartart-selector']['status'] == 'pending'
```

- [ ] **Step 6: Run test, verify it passes** (conductor reads DEFAULT_STEP_ORDER from deckcontext, so it should pass with no changes to conductor.py)

```bash
.venv/bin/pytest tests/test_conductor.py::test_init_pipeline_includes_smartart_steps -v
```

Expected: PASS — conductor already reads from DEFAULT_STEP_ORDER.

- [ ] **Step 7: Run full test suite to verify no regressions**

```bash
.venv/bin/pytest -v
```

Expected: All tests PASS.

- [ ] **Step 8: Commit**

```bash
git add src/deckcontext.py tests/test_deckcontext.py tests/test_conductor.py
git commit -m "feat: register SmartArt pipeline steps and contract schemas"
```

---

## Task 4: Strategy Map Extension

**Files:**
- Modify: `src/slide_prompt_composer.py`
- Modify: `tests/test_slide_prompt_composer.py` (or relevant test file)

- [ ] **Step 1: Write test for smartart strategy classification**

Add to the relevant test file:

```python
def test_classify_smartart_strategy():
    """Slides with visual_type='smartart' in strategy-map get smartart strategy."""
    from src.slide_prompt_composer import classify_slide_strategy
    slide = {
        'slide_number': 5,
        'slide_type': 'content',
        'headline': 'Our Process',
        'body_points': ['Research', 'Design', 'Build', 'Launch'],
        'visual_intent': 'Show as a flowchart'
    }
    # When smartart_config is present from selector, strategy should be smartart
    strategy_entry = {
        'slide_number': 5,
        'strategy': 'smartart',
        'rationale': 'SmartArt selector chose flowchart',
        'render_funnel': [],
        'smartart_config': {
            'graphic_type': 'flowchart',
            'enrichment_tier': 'ai_background',
            'engine': 'mermaid',
            'comparator_engines': ['mermaid', 'custom_svg']
        }
    }
    # The smartart strategy should be passthrough — it's set by the selector,
    # not by classify_slide_strategy. Verify classify doesn't override it.
    result = classify_slide_strategy(slide)
    # Without explicit smartart_config, classify should return composed/full_render/background as before
    assert result['strategy'] != 'smartart', "classify_slide_strategy should not produce smartart — that comes from the selector"
```

- [ ] **Step 2: Run test to verify it passes**

The existing `classify_slide_strategy` shouldn't produce `smartart` — that strategy is injected by the selector skill. This test confirms the boundary.

```bash
.venv/bin/pytest tests/test_slide_prompt_composer.py::test_classify_smartart_strategy -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_slide_prompt_composer.py
git commit -m "test: verify smartart strategy boundary in slide prompt composer"
```

---

## Task 5: Custom SVG Engine — Primitives + Tokens + Constraint Engine

**Files:**
- Create: `src/smartart_svg/__init__.py`
- Create: `src/smartart_svg/primitives.py`
- Create: `src/smartart_svg/tokens.py`
- Create: `src/smartart_svg/engine.py`
- Create: `tests/test_smartart_svg.py`

- [ ] **Step 1: Write tests for SVG primitives**

```python
# tests/test_smartart_svg.py
"""Tests for the custom SVG engine — primitives, tokens, and constraint engine."""

import pytest


class TestSvgPrimitives:
    def test_svg_rect_basic(self):
        from src.smartart_svg.primitives import svg_rect
        result = svg_rect(10, 20, 100, 50, rx=5, fill="#FF0000", stroke="#000000")
        assert '<rect' in result
        assert 'x="10"' in result
        assert 'width="100"' in result
        assert 'fill="#FF0000"' in result
        assert 'rx="5"' in result

    def test_svg_text_basic(self):
        from src.smartart_svg.primitives import svg_text
        result = svg_text(50, 30, "Hello World", font_family="Inter", font_size=16, fill="#000")
        assert '<text' in result
        assert 'Hello World' in result
        assert 'font-family="Inter"' in result

    def test_svg_circle_basic(self):
        from src.smartart_svg.primitives import svg_circle
        result = svg_circle(100, 100, 50, fill="#0000FF", opacity=0.5)
        assert '<circle' in result
        assert 'cx="100"' in result
        assert 'r="50"' in result
        assert 'opacity="0.5"' in result

    def test_svg_document_has_accessibility(self):
        from src.smartart_svg.primitives import svg_document
        result = svg_document(1920, 1080, ["<rect/>"], title="Test Chart", desc="A test chart")
        assert '<title>Test Chart</title>' in result
        assert '<desc>A test chart</desc>' in result
        assert 'xmlns="http://www.w3.org/2000/svg"' in result

    def test_svg_group_has_aria(self):
        from src.smartart_svg.primitives import svg_group
        result = svg_group(["<rect/>"], role="img", aria_label="Process flow")
        assert '<g' in result
        assert 'role="img"' in result
        assert 'aria-label="Process flow"' in result

    def test_svg_arrow(self):
        from src.smartart_svg.primitives import svg_arrow
        result = svg_arrow(0, 0, 100, 100, stroke="#333")
        assert '<line' in result or '<path' in result


class TestTokenMapping:
    def test_extract_style_tokens(self):
        from src.smartart_svg.tokens import extract_style_tokens
        style_guide = {
            'palette': {
                'primary': '1a73e8',
                'accent': 'e8710a',
                'background': 'ffffff',
                'text_primary': '1a1a1a',
                'chart_series': ['2B6CB0', 'ED8936', '38A169', 'E53E3E']
            },
            'typography': {
                'heading_font': 'Inter',
                'body_font': 'Inter'
            }
        }
        tokens = extract_style_tokens(style_guide)
        assert tokens['primary_color'] == '#1a73e8'
        assert tokens['font_family'] == 'Inter'
        assert len(tokens['chart_series']) == 4

    def test_resolve_text_colour_good_contrast(self):
        from src.smartart_svg.tokens import resolve_text_colour
        # White text on dark blue — good contrast
        result = resolve_text_colour('#1a1a1a', '#ffffff', None)
        assert result == '#ffffff'

    def test_resolve_text_colour_bad_contrast_fallback(self):
        from src.smartart_svg.tokens import resolve_text_colour
        # Teal text on teal background — bad contrast, should fallback
        result = resolve_text_colour('#2B6CB0', '#3B7CC0', None)
        assert result in ('#ffffff', '#000000'), f"Expected fallback to white or black, got {result}"


class TestContainerEngine:
    def test_container_split_grid(self):
        from src.smartart_svg.engine import Container
        c = Container(0, 0, 1000, 800, padding=10)
        cells = c.split_grid(2, 2, gap=10)
        assert len(cells) == 4
        # All cells should be inside parent bounds
        for cell in cells:
            assert cell.x >= 0
            assert cell.y >= 0
            assert cell.x + cell.width <= 1000
            assert cell.y + cell.height <= 800

    def test_container_split_horizontal(self):
        from src.smartart_svg.engine import Container
        c = Container(0, 0, 1000, 500, padding=0)
        parts = c.split_horizontal([1, 2, 1], gap=10)
        assert len(parts) == 3
        # Second part should be roughly twice as wide as first
        assert parts[1].width > parts[0].width

    def test_container_split_vertical(self):
        from src.smartart_svg.engine import Container
        c = Container(0, 0, 500, 1000, padding=0)
        parts = c.split_vertical([1, 4], gap=10)
        assert len(parts) == 2
        assert parts[1].height > parts[0].height

    def test_container_center_point(self):
        from src.smartart_svg.engine import Container
        c = Container(100, 200, 300, 400, padding=0)
        cx, cy = c.center_point()
        assert cx == 250  # 100 + 300/2
        assert cy == 400  # 200 + 400/2

    def test_fit_text_reduces_font_size(self):
        from src.smartart_svg.engine import Container
        c = Container(0, 0, 100, 30, padding=0)
        fitted = c.fit_text("A very long text that cannot fit at large size", font_size=48, max_lines=1)
        assert fitted.font_size < 48
        assert fitted.font_size >= 10  # minimum readable
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/pytest tests/test_smartart_svg.py -v
```

Expected: FAIL — modules don't exist.

- [ ] **Step 3: Implement primitives.py**

Create `src/smartart_svg/__init__.py`:

```python
"""Custom SVG engine for SmartArt graphics — constraint-based layout."""

from src.smartart_svg.engine import Container
from src.smartart_svg.primitives import svg_document
```

Create `src/smartart_svg/primitives.py`:

```python
"""SVG building blocks — rect, circle, text, arrow, group, document.

All functions return SVG markup strings. The svg_document wrapper
adds accessibility tags (title, desc) for WCAG 2.2 compliance.
"""


def svg_rect(x, y, w, h, rx=0, fill="#cccccc", stroke=None, class_name=None):
    attrs = f'x="{x}" y="{y}" width="{w}" height="{h}"'
    if rx:
        attrs += f' rx="{rx}"'
    attrs += f' fill="{fill}"'
    if stroke:
        attrs += f' stroke="{stroke}" stroke-width="1"'
    if class_name:
        attrs += f' class="{class_name}"'
    return f'<rect {attrs}/>'


def svg_circle(cx, cy, r, fill="#cccccc", opacity=1.0):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" opacity="{opacity}"/>'


def svg_text(x, y, text, font_family="sans-serif", font_size=16, fill="#000000",
             anchor="start", weight="normal"):
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x}" y="{y}" font-family="{font_family}" font-size="{font_size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{escaped}</text>')


def svg_arrow(x1, y1, x2, y2, stroke="#333333", stroke_width=2):
    mid = "arrow-marker"
    marker = (f'<defs><marker id="{mid}" markerWidth="10" markerHeight="7" '
              f'refX="10" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" '
              f'fill="{stroke}"/></marker></defs>')
    line = (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
            f'stroke-width="{stroke_width}" marker-end="url(#{mid})"/>')
    return marker + line


def svg_group(children, transform=None, role=None, aria_label=None):
    attrs = ""
    if transform:
        attrs += f' transform="{transform}"'
    if role:
        attrs += f' role="{role}"'
    if aria_label:
        attrs += f' aria-label="{aria_label}"'
    inner = "\n".join(children)
    return f'<g{attrs}>\n{inner}\n</g>'


def svg_document(width, height, children, title="", desc=""):
    inner = "\n".join(children)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">\n'
            f'<title>{title}</title>\n'
            f'<desc>{desc}</desc>\n'
            f'{inner}\n'
            f'</svg>')
```

- [ ] **Step 4: Implement tokens.py**

Create `src/smartart_svg/tokens.py`:

```python
"""StyleGuide to SVG attribute mapping + WCAG contrast resolver."""

import math


def _hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))


def _relative_luminance(rgb):
    """WCAG 2.2 relative luminance from sRGB."""
    vals = []
    for c in rgb:
        s = c / 255.0
        vals.append(s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4)
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


def _contrast_ratio(hex1, hex2):
    l1 = _relative_luminance(_hex_to_rgb(hex1))
    l2 = _relative_luminance(_hex_to_rgb(hex2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def resolve_text_colour(background_colour, preferred_colour, style_guide):
    """Return preferred_colour if WCAG contrast passes, else fallback to white or black."""
    ratio = _contrast_ratio(background_colour, preferred_colour)
    if ratio >= 4.5:
        return preferred_colour
    # Fallback: pick white or black based on which has better contrast
    white_ratio = _contrast_ratio(background_colour, '#ffffff')
    black_ratio = _contrast_ratio(background_colour, '#000000')
    return '#ffffff' if white_ratio > black_ratio else '#000000'


def extract_style_tokens(style_guide):
    """Map StyleGuide fields to flat token dict for SVG rendering."""
    palette = style_guide.get('palette', {})
    typo = style_guide.get('typography', {})
    series = palette.get('chart_series', [])
    return {
        'primary_color': '#' + palette.get('primary', '1a73e8'),
        'accent_color': '#' + palette.get('accent', 'e8710a'),
        'background_color': '#' + palette.get('background', 'ffffff'),
        'text_color': '#' + palette.get('text_primary', '1a1a1a'),
        'font_family': typo.get('body_font', 'sans-serif'),
        'heading_font': typo.get('heading_font', 'sans-serif'),
        'chart_series': ['#' + c for c in series],
        'border_radius': style_guide.get('image_style_tokens', {}).get('border_radius', 8),
    }
```

- [ ] **Step 5: Implement engine.py**

Create `src/smartart_svg/engine.py`:

```python
"""Constraint-based container engine for SVG layout.

Provides a Container class that can be subdivided into grids, rows, or columns
with proportional sizing. Text fitting with automatic font size reduction.
"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class FittedText:
    text: str
    font_size: float
    lines: List[str]
    overflow: bool


@dataclass
class Container:
    """A rectangular region that can be subdivided."""
    x: float
    y: float
    width: float
    height: float
    padding: float = 0

    @property
    def inner_x(self):
        return self.x + self.padding

    @property
    def inner_y(self):
        return self.y + self.padding

    @property
    def inner_width(self):
        return max(0, self.width - 2 * self.padding)

    @property
    def inner_height(self):
        return max(0, self.height - 2 * self.padding)

    def center_point(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)

    def split_grid(self, rows: int, cols: int, gap: float = 0) -> List['Container']:
        """Split into a rows×cols grid of equal-sized containers."""
        iw = self.inner_width - gap * (cols - 1)
        ih = self.inner_height - gap * (rows - 1)
        cell_w = iw / cols
        cell_h = ih / rows
        cells = []
        for r in range(rows):
            for c in range(cols):
                cx = self.inner_x + c * (cell_w + gap)
                cy = self.inner_y + r * (cell_h + gap)
                cells.append(Container(cx, cy, cell_w, cell_h))
        return cells

    def split_horizontal(self, ratios: List[float], gap: float = 0) -> List['Container']:
        """Split horizontally by proportional ratios."""
        total = sum(ratios)
        available = self.inner_width - gap * (len(ratios) - 1)
        parts = []
        cx = self.inner_x
        for ratio in ratios:
            w = available * (ratio / total)
            parts.append(Container(cx, self.inner_y, w, self.inner_height))
            cx += w + gap
        return parts

    def split_vertical(self, ratios: List[float], gap: float = 0) -> List['Container']:
        """Split vertically by proportional ratios."""
        total = sum(ratios)
        available = self.inner_height - gap * (len(ratios) - 1)
        parts = []
        cy = self.inner_y
        for ratio in ratios:
            h = available * (ratio / total)
            parts.append(Container(self.inner_x, cy, self.inner_width, h))
            cy += h + gap
        return parts

    def fit_text(self, text: str, font_size: float = 16, max_lines: int = 1) -> FittedText:
        """Reduce font size until text fits within container width.

        Uses approximate character width (0.6 × font_size) for estimation.
        Minimum font size is 10px.
        """
        min_size = 10
        current_size = font_size
        while current_size >= min_size:
            char_width = current_size * 0.6
            chars_per_line = max(1, int(self.inner_width / char_width))
            lines = []
            words = text.split()
            current_line = ""
            for word in words:
                test = (current_line + " " + word).strip()
                if len(test) <= chars_per_line:
                    current_line = test
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            if len(lines) <= max_lines:
                return FittedText(text=text, font_size=current_size, lines=lines, overflow=False)
            current_size -= 1

        # At minimum size, just truncate
        char_width = min_size * 0.6
        chars_per_line = max(1, int(self.inner_width / char_width))
        return FittedText(
            text=text, font_size=min_size,
            lines=[text[:chars_per_line]], overflow=True
        )
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_smartart_svg.py -v
```

Expected: All tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/smartart_svg/ tests/test_smartart_svg.py
git commit -m "feat: custom SVG engine — primitives, tokens, constraint containers"
```

---

## Task 6: Custom SVG Layouts (5 graphic types)

**Files:**
- Create: `src/smartart_svg/layouts/__init__.py`
- Create: `src/smartart_svg/layouts/swot.py`
- Create: `src/smartart_svg/layouts/feature_matrix.py`
- Create: `src/smartart_svg/layouts/venn.py`
- Create: `src/smartart_svg/layouts/timeline.py`
- Create: `src/smartart_svg/layouts/pipeline_funnel.py`
- Modify: `tests/test_smartart_svg.py`

This is a large task — implement one layout at a time, each with its own test, commit after all 5 are done. Each layout function takes `(data, container, tokens)` and returns an SVG string.

- [ ] **Step 1: Write tests for all 5 layouts**

Add to `tests/test_smartart_svg.py`:

```python
class TestSwotLayout:
    def test_renders_4_quadrants(self):
        from src.smartart_svg.layouts.swot import render_swot
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "quadrants": [
                {"label": "Strengths", "position": "top_left", "items": ["Brand", "Team"]},
                {"label": "Weaknesses", "position": "top_right", "items": ["Scale"]},
                {"label": "Opportunities", "position": "bottom_left", "items": ["AI"]},
                {"label": "Threats", "position": "bottom_right", "items": ["Regulation"]}
            ]
        }
        style = {
            'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                        'text_primary': '1a1a1a', 'chart_series': ['2B6CB0', 'ED8936', '38A169', 'E53E3E']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 1920, 1080, padding=40)
        svg = render_swot(data, c, tokens)
        assert '<svg' not in svg  # layout returns fragment, not full doc
        assert 'Strengths' in svg
        assert 'Weaknesses' in svg
        assert 'Brand' in svg


class TestFeatureMatrixLayout:
    def test_renders_grid(self):
        from src.smartart_svg.layouts.feature_matrix import render_feature_matrix
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "columns": ["Feature A", "Feature B"],
            "rows": [
                {"label": "Product 1", "values": [True, False]},
                {"label": "Product 2", "values": [True, True]}
            ]
        }
        style = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a',
                        'chart_series': ['2B6CB0']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 1920, 1080, padding=40)
        svg = render_feature_matrix(data, c, tokens)
        assert 'Feature A' in svg
        assert 'Product 1' in svg


class TestVennLayout:
    def test_renders_2_circles(self):
        from src.smartart_svg.layouts.venn import render_venn
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "sets": [
                {"label": "Set A", "items": ["Only A"]},
                {"label": "Set B", "items": ["Only B"]}
            ],
            "intersection": {"items": ["Shared"]}
        }
        style = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a',
                        'chart_series': ['2B6CB0', 'ED8936']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 1920, 1080, padding=40)
        svg = render_venn(data, c, tokens)
        assert '<circle' in svg
        assert 'Set A' in svg
        assert 'Shared' in svg


class TestTimelineLayout:
    def test_renders_stages(self):
        from src.smartart_svg.layouts.timeline import render_timeline
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "stages": [
                {"label": "Q1 2025", "description": "Research"},
                {"label": "Q2 2025", "description": "Design"},
                {"label": "Q3 2025", "description": "Build"}
            ]
        }
        style = {
            'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                        'text_primary': '1a1a1a', 'chart_series': ['2B6CB0']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 1920, 1080, padding=40)
        svg = render_timeline(data, c, tokens)
        assert 'Q1 2025' in svg
        assert 'Research' in svg


class TestPipelineFunnelLayout:
    def test_renders_stages(self):
        from src.smartart_svg.layouts.pipeline_funnel import render_pipeline_funnel
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "stages": [
                {"label": "Leads", "value": 1000},
                {"label": "Qualified", "value": 500},
                {"label": "Proposals", "value": 200},
                {"label": "Closed", "value": 50}
            ]
        }
        style = {
            'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                        'text_primary': '1a1a1a', 'chart_series': ['2B6CB0']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 1920, 1080, padding=40)
        svg = render_pipeline_funnel(data, c, tokens)
        assert 'Leads' in svg
        assert 'Closed' in svg
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/pytest tests/test_smartart_svg.py -k "Layout or Swot or FeatureMatrix or Venn or Timeline or PipelineFunnel" -v
```

Expected: FAIL — layout modules don't exist.

- [ ] **Step 3: Implement each layout module**

Create `src/smartart_svg/layouts/__init__.py`:

```python
"""Layout registry — maps graphic_type to render function."""

from src.smartart_svg.layouts.swot import render_swot
from src.smartart_svg.layouts.feature_matrix import render_feature_matrix
from src.smartart_svg.layouts.venn import render_venn
from src.smartart_svg.layouts.timeline import render_timeline
from src.smartart_svg.layouts.pipeline_funnel import render_pipeline_funnel

LAYOUT_REGISTRY = {
    'swot': render_swot,
    'feature_matrix': render_feature_matrix,
    'venn': render_venn,
    'timeline': render_timeline,
    'pipeline_funnel': render_pipeline_funnel,
}
```

Implement each layout file. Each follows the same signature:

```python
def render_<type>(data, container, tokens) -> str:
    """Render a <type> graphic as an SVG fragment."""
```

The layouts use `Container.split_grid/split_horizontal/split_vertical` for positioning, `svg_rect/svg_text/svg_circle` from primitives for drawing, and `resolve_text_colour` from tokens for contrast safety.

**Implementation guidance per layout:**

- **swot.py**: Split container into title (top 10%) + 2×2 grid. Each quadrant gets a coloured `svg_rect` background from `chart_series[0..3]`, a header `svg_text` with the quadrant label, and bullet `svg_text` items. Use `resolve_text_colour` for text on each coloured quadrant.

- **feature_matrix.py**: Split container into (rows+1) × (cols+1) grid. Cell [0][0] is empty. First row = column headers. First column = row labels. Inner cells use checkmark (✓) or cross (✗) unicode characters for boolean values, or the value text for non-boolean. Alternating row tint via `svg_rect` with low-opacity fill.

- **venn.py**: Place 2 or 3 circles with semi-transparent fills from `chart_series`. For 2 sets, offset horizontally with ~30% overlap. Labels go outside the circles for exclusive items, in the overlap region for shared items. Use `svg_circle` with `opacity=0.4`.

- **timeline.py**: Horizontal spine line via `svg_rect` (thin, wide). Equal-width columns via `split_horizontal`. Circle nodes at each stage centre on the spine. Labels alternate above/below. Connector arrows via `svg_arrow` between nodes.

- **pipeline_funnel.py**: N trapezoids stacked vertically, widest at top. Each trapezoid rendered as `svg_rect` with decreasing widths (centred). Width proportional to `value` if present. Stage labels centred in each trapezoid. Colour gradient from `primary_color` to `accent_color` using interpolation.

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_smartart_svg.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Add render_custom_svg public API to __init__.py**

Update `src/smartart_svg/__init__.py`:

```python
"""Custom SVG engine for SmartArt graphics — constraint-based layout."""

from src.smartart_svg.engine import Container
from src.smartart_svg.primitives import svg_document
from src.smartart_svg.tokens import extract_style_tokens
from src.smartart_svg.layouts import LAYOUT_REGISTRY


def render_custom_svg(spec, style_guide, width=1920, height=1080):
    """Render a SmartArt spec as a complete SVG document.

    Args:
        spec: SmartArtSpec entry with graphic_type, data, style_tokens
        style_guide: Full StyleGuide for token extraction
        width: SVG width in pixels
        height: SVG height in pixels

    Returns:
        SVG string
    """
    graphic_type = spec['graphic_type']
    render_fn = LAYOUT_REGISTRY.get(graphic_type)
    if not render_fn:
        raise ValueError(f"Unsupported graphic type: {graphic_type}")

    tokens = extract_style_tokens(style_guide)
    container = Container(0, 0, width, height, padding=40)
    fragment = render_fn(spec['data'], container, tokens)

    alt_text = f"{graphic_type} diagram"
    return svg_document(width, height, [fragment], title=alt_text, desc=alt_text)
```

- [ ] **Step 6: Commit**

```bash
git add src/smartart_svg/ tests/test_smartart_svg.py
git commit -m "feat: 5 custom SVG layouts — SWOT, feature matrix, Venn, timeline, funnel"
```

---

## Task 7: SmartArt Extractor

**Files:**
- Create: `src/smartart_extractor.py`
- Create: `tests/test_smartart_extractor.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_smartart_extractor.py
"""Tests for SmartArt data extraction — content to engine-specific data."""

import pytest


class TestExtractGraphData:
    def test_extract_flowchart_from_sequential_points(self):
        from src.smartart_extractor import extract_graph_data
        body_points = ["Research the market", "Design the solution", "Build the product", "Launch to customers"]
        result = extract_graph_data(body_points, "flowchart")
        assert result['engine'] == 'mermaid'
        assert 'syntax' in result
        assert result['node_count'] == 4
        assert 'graph' in result['syntax']  # Mermaid flowchart starts with graph

    def test_extract_gantt_data(self):
        from src.smartart_extractor import extract_graph_data
        body_points = ["Research: Jan-Mar", "Design: Mar-May", "Build: May-Aug"]
        result = extract_graph_data(body_points, "gantt")
        assert result['engine'] == 'mermaid'
        assert 'gantt' in result['syntax']


class TestExtractSeriesData:
    def test_extract_bar_chart_data(self):
        from src.smartart_extractor import extract_series_data
        body_points = ["Q1: $120K revenue", "Q2: $150K revenue", "Q3: $180K revenue"]
        result = extract_series_data(body_points, "bar_chart")
        assert result['engine'] == 'vega_lite'
        assert '$schema' in result['spec']

    def test_extract_matplotlib_comparator_data(self):
        from src.smartart_extractor import extract_series_data
        body_points = ["Q1: 120", "Q2: 150"]
        result = extract_series_data(body_points, "bar_chart", engine="matplotlib")
        assert result['engine'] == 'matplotlib'
        assert 'labels' in result['data']
        assert 'values' in result['data']


class TestExtractSpatialData:
    def test_extract_swot_data(self):
        from src.smartart_extractor import extract_spatial_data
        body_points = [
            "Strengths: Brand recognition, Strong team",
            "Weaknesses: Limited scale",
            "Opportunities: AI market growth",
            "Threats: Regulatory changes"
        ]
        result = extract_spatial_data(body_points, "swot")
        assert result['engine'] == 'custom_svg'
        assert len(result['data']['quadrants']) == 4
        assert result['data']['quadrants'][0]['label'] == 'Strengths'

    def test_extract_timeline_data(self):
        from src.smartart_extractor import extract_spatial_data
        body_points = ["Q1 2025: Research phase", "Q2 2025: Design phase", "Q3 2025: Build phase"]
        result = extract_spatial_data(body_points, "timeline")
        assert result['engine'] == 'custom_svg'
        assert len(result['data']['stages']) == 3


class TestExtractFunction:
    def test_extract_dispatches_to_correct_extractor(self):
        from src.smartart_extractor import extract
        slide = {
            'slide_number': 5,
            'headline': 'Our Process',
            'body_points': ['Research', 'Design', 'Build', 'Launch']
        }
        selection = {
            'slide_number': 5,
            'graphic_type': 'flowchart',
            'enrichment_tier': 'pure_programmatic',
            'engine': 'mermaid'
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'text_primary': '1a1a1a', 'chart_series': []},
            'typography': {'body_font': 'Inter', 'heading_font': 'Inter'}
        }
        result = extract(slide, selection, style_guide)
        assert result['slide_number'] == 5
        assert result['graphic_type'] == 'flowchart'
        assert result['engine'] == 'mermaid'
        assert result['validation_status'] == 'valid'


class TestValidateSpec:
    def test_valid_spec_passes(self):
        from src.smartart_extractor import validate_spec
        spec = {
            'engine': 'mermaid',
            'data': {'syntax': 'graph TD\n  A --> B', 'node_count': 2},
            'graphic_type': 'flowchart'
        }
        valid, errors = validate_spec(spec)
        assert valid is True
        assert errors == []

    def test_missing_syntax_fails(self):
        from src.smartart_extractor import validate_spec
        spec = {
            'engine': 'mermaid',
            'data': {'node_count': 2},
            'graphic_type': 'flowchart'
        }
        valid, errors = validate_spec(spec)
        assert valid is False
        assert len(errors) > 0


class TestOverflow:
    def test_truncation_adds_indicator(self):
        from src.smartart_extractor import extract_spatial_data
        # Create a SWOT with too many items
        items = [f"Item {i}" for i in range(10)]
        body_points = [
            f"Strengths: {', '.join(items)}",
            "Weaknesses: One",
            "Opportunities: One",
            "Threats: One"
        ]
        result = extract_spatial_data(body_points, "swot")
        strengths = result['data']['quadrants'][0]
        assert len(strengths['items']) <= 5
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/pytest tests/test_smartart_extractor.py -v
```

- [ ] **Step 3: Implement smartart_extractor.py**

Create `src/smartart_extractor.py` with:

- `extract(slide, selection, style_guide)` → SmartArtSpec entry (dispatches to the right extractor based on engine)
- `extract_graph_data(body_points, graphic_type)` → Mermaid syntax dict
- `extract_series_data(body_points, chart_type, engine='vega_lite')` → Vega-Lite spec or Matplotlib data
- `extract_spatial_data(body_points, graphic_type)` → Custom SVG data structure
- `validate_spec(spec)` → (bool, errors list)

Each function parses body_points using regex patterns (colon-separated key-value, arrow-separated sequences, comma-separated lists). The Mermaid extractor builds `graph TD\n  A[label] --> B[label]` syntax from sequential items. The Vega-Lite extractor builds a complete Vega-Lite JSON spec. The SWOT extractor looks for "Strengths:", "Weaknesses:", etc. prefixes.

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_smartart_extractor.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/smartart_extractor.py tests/test_smartart_extractor.py
git commit -m "feat: SmartArt data extractor — content to engine-specific structured data"
```

---

## Task 8: SmartArt Renderer

**Files:**
- Create: `src/smartart_renderer.py`
- Create: `tests/test_smartart_renderer.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_smartart_renderer.py
"""Tests for SmartArt renderer — engine dispatch, comparator, manifest."""

import os
import json
import tempfile
import pytest


class TestRenderMermaid:
    def test_render_mermaid_produces_svg(self):
        from src.smartart_renderer import render_mermaid
        spec = {
            'data': {
                'syntax': 'graph TD\n  A[Research] --> B[Design]\n  B --> C[Build]',
                'diagram_type': 'flowchart'
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'text_primary': '1a1a1a', 'chart_series': []},
            'typography': {'body_font': 'Inter', 'heading_font': 'Inter'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_mermaid(spec, style_guide, tmpdir)
            assert result.endswith('.svg')
            assert os.path.exists(result)
            with open(result) as f:
                content = f.read()
            assert '<svg' in content


class TestRenderVegaLite:
    def test_render_vega_lite_produces_svg(self):
        from src.smartart_renderer import render_vega_lite
        spec = {
            'data': {
                'spec': {
                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                    "mark": "bar",
                    "encoding": {
                        "x": {"field": "label", "type": "ordinal"},
                        "y": {"field": "value", "type": "quantitative"}
                    },
                    "data": {"values": [
                        {"label": "Q1", "value": 120},
                        {"label": "Q2", "value": 150}
                    ]}
                }
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a'},
            'typography': {'body_font': 'Inter'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_vega_lite(spec, style_guide, tmpdir)
            assert result.endswith('.svg')
            assert os.path.exists(result)


class TestRenderCustomSvg:
    def test_render_custom_svg_produces_svg(self):
        from src.smartart_renderer import render_custom_svg_engine
        spec = {
            'graphic_type': 'swot',
            'data': {
                'quadrants': [
                    {'label': 'Strengths', 'position': 'top_left', 'items': ['Brand']},
                    {'label': 'Weaknesses', 'position': 'top_right', 'items': ['Scale']},
                    {'label': 'Opportunities', 'position': 'bottom_left', 'items': ['AI']},
                    {'label': 'Threats', 'position': 'bottom_right', 'items': ['Risk']}
                ]
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                        'text_primary': '1a1a1a', 'chart_series': ['2B6CB0', 'ED8936', '38A169', 'E53E3E']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_custom_svg_engine(spec, style_guide, tmpdir)
            assert result.endswith('.svg')
            assert os.path.exists(result)


class TestRender:
    def test_render_dispatches_by_engine(self):
        from src.smartart_renderer import render
        spec = {
            'slide_number': 5,
            'graphic_type': 'swot',
            'engine': 'custom_svg',
            'enrichment_tier': 'pure_programmatic',
            'data': {
                'quadrants': [
                    {'label': 'S', 'position': 'top_left', 'items': ['a']},
                    {'label': 'W', 'position': 'top_right', 'items': ['b']},
                    {'label': 'O', 'position': 'bottom_left', 'items': ['c']},
                    {'label': 'T', 'position': 'bottom_right', 'items': ['d']}
                ]
            },
            'style_tokens': {'primary_color': '#1a73e8', 'font_family': 'Inter'},
            'comparator_engines': []
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                        'text_primary': '1a1a1a', 'chart_series': ['2B6CB0', 'ED8936', '38A169', 'E53E3E']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            entry = render(spec, style_guide, 'draft', tmpdir)
            assert entry['smartart_id'].startswith('sa-slide-5')
            assert entry['status'] in ('rendered', 'compared')
            assert os.path.exists(os.path.join(tmpdir, os.path.basename(entry['file_path'])))


class TestManifestGeneration:
    def test_build_manifest_entry(self):
        from src.smartart_renderer import build_manifest_entry
        entry = build_manifest_entry(
            slide_number=5,
            graphic_type='flowchart',
            engine='mermaid',
            enrichment_tier='pure_programmatic',
            file_path='./tmp/deck/smartart/slide-5.png',
            svg_path='./tmp/deck/smartart/slide-5.svg',
            dimensions={'width': 1920, 'height': 1080},
            alt_text='Flowchart',
            node_count=4
        )
        assert entry['smartart_id'] == 'sa-slide-5-flowchart'
        assert entry['status'] == 'rendered'
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/pytest tests/test_smartart_renderer.py -v
```

- [ ] **Step 3: Implement smartart_renderer.py**

Create `src/smartart_renderer.py` with:

- `render(spec, style_guide, phase, output_dir)` → manifest entry dict
- `render_mermaid(spec, style_guide, output_dir)` → SVG file path (calls `npx mmdc` via subprocess)
- `render_vega_lite(spec, style_guide, output_dir)` → SVG file path (calls `npx vl2svg` via subprocess)
- `render_custom_svg_engine(spec, style_guide, output_dir)` → SVG file path (calls `render_custom_svg` from smartart_svg package)
- `render_matplotlib(spec, style_guide, output_dir)` → PNG file path (calls `render_chart` from existing module)
- `build_manifest_entry(...)` → dict matching SmartArtManifest schema
- `rasterise(svg_path, output_path, width, height)` → PNG path (calls Sharp or Pillow as fallback)

For Mermaid rendering, write the syntax to a temp `.mmd` file, inject theme config, then run:
```bash
npx mmdc -i input.mmd -o output.svg -t dark --configFile config.json
```

For Vega-Lite rendering, write the spec to a temp `.json` file, then run:
```bash
npx vl2svg input.json output.svg
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_smartart_renderer.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/smartart_renderer.py tests/test_smartart_renderer.py
git commit -m "feat: SmartArt renderer — Mermaid, Vega-Lite, custom SVG engine dispatch"
```

---

## Task 9: SmartArt QA Checks (SA-01 through SA-05)

**Files:**
- Create: `src/qa/checks/smartart_checks.py`
- Modify: `src/qa/run_qa.py`
- Create: `tests/test_smartart_qa.py`

- [ ] **Step 1: Write tests for each QA check**

```python
# tests/test_smartart_qa.py
"""Tests for SmartArt QA checks — data integrity, legibility, enrichment, overflow, accessibility."""

import pytest


class TestSA01DataIntegrity:
    def test_all_data_points_present(self):
        from src.qa.checks.smartart_checks import check_data_integrity
        outline_slide = {
            'body_points': ['Research', 'Design', 'Build', 'Launch']
        }
        spec = {
            'data': {'syntax': 'graph TD\n  A[Research] --> B[Design]\n  B --> C[Build]\n  C --> D[Launch]', 'node_count': 4},
            'overflow_applied': 'none'
        }
        findings = check_data_integrity(outline_slide, spec, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0

    def test_missing_data_point_fails(self):
        from src.qa.checks.smartart_checks import check_data_integrity
        outline_slide = {
            'body_points': ['Research', 'Design', 'Build', 'Launch']
        }
        spec = {
            'data': {'syntax': 'graph TD\n  A[Research] --> B[Design]', 'node_count': 2},
            'overflow_applied': 'none'
        }
        findings = check_data_integrity(outline_slide, spec, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) > 0


class TestSA02LabelLegibility:
    def test_good_font_size_passes(self):
        from src.qa.checks.smartart_checks import check_label_legibility
        svg_content = '<text font-size="18" fill="#000000">Label</text>'
        bg_color = '#ffffff'
        findings = check_label_legibility(svg_content, bg_color, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0

    def test_small_font_fails(self):
        from src.qa.checks.smartart_checks import check_label_legibility
        svg_content = '<text font-size="10" fill="#000000">Tiny</text>'
        bg_color = '#ffffff'
        findings = check_label_legibility(svg_content, bg_color, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) > 0

    def test_low_contrast_fails(self):
        from src.qa.checks.smartart_checks import check_label_legibility
        svg_content = '<text font-size="18" fill="#cccccc">Low contrast</text>'
        bg_color = '#dddddd'
        findings = check_label_legibility(svg_content, bg_color, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) > 0


class TestSA05Accessibility:
    def test_accessible_svg_passes(self):
        from src.qa.checks.smartart_checks import check_accessibility
        svg_content = '<svg><title>SWOT Analysis</title><desc>Four quadrant diagram</desc><g role="img" aria-label="Strengths quadrant"></g></svg>'
        manifest_entry = {'alt_text': 'SWOT Analysis diagram'}
        findings = check_accessibility(svg_content, manifest_entry, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0

    def test_missing_title_fails(self):
        from src.qa.checks.smartart_checks import check_accessibility
        svg_content = '<svg><desc>Description</desc></svg>'
        manifest_entry = {'alt_text': 'Chart'}
        findings = check_accessibility(svg_content, manifest_entry, slide_number=5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/pytest tests/test_smartart_qa.py -v
```

- [ ] **Step 3: Implement smartart_checks.py**

Create `src/qa/checks/smartart_checks.py` with 5 check functions:
- `check_data_integrity(outline_slide, spec, slide_number)` → list of findings
- `check_label_legibility(svg_content, bg_color, slide_number)` → list of findings
- `check_enrichment_alignment(manifest_entry, image_manifest, slide_number)` → list of findings
- `check_overflow_handling(spec, svg_content, slide_number)` → list of findings
- `check_accessibility(svg_content, manifest_entry, slide_number)` → list of findings

Each returns a list of finding dicts matching the QAReport schema: `{slide_number, severity, category: "smartart", description}`.

The legibility check uses regex to parse `<text font-size="X" fill="Y">` attributes and the WCAG contrast formula from `tokens.py`.

- [ ] **Step 4: Register SmartArt checks in run_qa.py**

Add import and registration of SmartArt checks in `src/qa/run_qa.py`. The checks run when a SmartArtManifest is present in the DeckContext.

- [ ] **Step 5: Run tests to verify they pass**

```bash
.venv/bin/pytest tests/test_smartart_qa.py -v
```

- [ ] **Step 6: Run full QA test suite**

```bash
.venv/bin/pytest tests/ -k "qa" -v
```

Expected: All QA tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/qa/checks/smartart_checks.py src/qa/run_qa.py tests/test_smartart_qa.py
git commit -m "feat: 5 SmartArt QA checks — data integrity, legibility, contrast, accessibility"
```

---

## Task 10: Assembler Extension — buildSmartArtSlide()

**Files:**
- Modify: `src/assembler/build_deck.js`
- Modify: `tests/test_assembler.py`

- [ ] **Step 1: Add buildSmartArtSlide function to build_deck.js**

Add a new function that handles the `smartart` strategy:

```javascript
function buildSmartArtSlide(pptx, slideData, smartartEntry, enrichmentImages, styleGuide, notes) {
    const slide = pptx.addSlide();
    const tier = smartartEntry.enrichment_tier;

    if (tier === 'full_ai_render') {
        // T3: same as full_render — single full-bleed AI image
        const imgPath = resolveImagePath(smartartEntry.file_path);
        if (fs.existsSync(imgPath)) {
            slide.addImage({ path: imgPath, x: 0, y: 0, w: '100%', h: '100%' });
        }
    } else if (tier === 'ai_background') {
        // T1: background image + SmartArt centred with backing
        const bgImage = enrichmentImages.find(i => i.smartart_ref === smartartEntry.smartart_id);
        if (bgImage) {
            const bgPath = resolveImagePath(bgImage.file_path);
            if (fs.existsSync(bgPath)) {
                slide.addImage({ path: bgPath, x: 0, y: 0, w: '100%', h: '100%' });
            }
        }
        // Semi-transparent backing
        slide.addShape(pptx.shapes.RECTANGLE, {
            x: '12.5%', y: '14%', w: '75%', h: '80%',
            fill: { color: styleGuide.palette?.background || 'FFFFFF', transparency: 15 },
            line: { color: 'CCCCCC', width: 0.5 }
        });
        // SmartArt graphic
        const saPath = resolveImagePath(smartartEntry.file_path);
        if (fs.existsSync(saPath)) {
            slide.addImage({ path: saPath, x: '12.5%', y: '14%', w: '75%', h: '80%' });
        }
    } else {
        // T0 and T2: SmartArt graphic centred (T2 has icons already composited)
        const saPath = resolveImagePath(smartartEntry.file_path);
        if (fs.existsSync(saPath)) {
            slide.addImage({ path: saPath, x: '7.5%', y: '14%', w: '85%', h: '80%' });
        }
    }

    // Title
    slide.addText(slideData.headline || '', {
        x: '5%', y: '2%', w: '90%', h: '10%',
        fontSize: 28, fontFace: styleGuide.typography?.heading_font || 'Arial',
        color: styleGuide.palette?.text_primary || '1A1A1A',
        bold: true
    });

    // Footer logo
    addFooterLogo(slide);

    // Speaker notes
    if (notes) {
        slide.addNotes(notes);
    }
}
```

Update the main slide dispatch to include `smartart`:

```javascript
// In the main build loop, add:
case 'smartart':
    const saEntry = smartartManifest?.graphics?.find(g => g.slide_number === slideData.slide_number);
    const enrichmentImgs = imageManifest?.images?.filter(i => i.smartart_ref === saEntry?.smartart_id) || [];
    if (saEntry) {
        buildSmartArtSlide(pptx, slideData, saEntry, enrichmentImgs, styleGuide, noteText);
    }
    break;
```

Also load the SmartArtManifest at the top of the main function:

```javascript
const smartartManifest = fs.existsSync(path.join(DECK_DIR, 'smartart-manifest.json'))
    ? loadContract('smartart-manifest')
    : { graphics: [] };
```

- [ ] **Step 2: Write a test to verify buildSmartArtSlide integration**

Add to `tests/test_assembler.py`:

```python
def test_assembler_handles_smartart_strategy(tmp_path):
    """Verify assembler loads SmartArtManifest and dispatches to buildSmartArtSlide."""
    # Create minimal DeckContext with smartart strategy
    import json
    deck_dir = str(tmp_path)
    # Write required contracts...
    # (Follow existing test patterns in test_assembler.py)
    # Verify the .pptx is produced without errors
```

- [ ] **Step 3: Run tests**

```bash
.venv/bin/pytest tests/test_assembler.py -v
```

- [ ] **Step 4: Commit**

```bash
git add src/assembler/build_deck.js tests/test_assembler.py
git commit -m "feat: buildSmartArtSlide() — assembler support for smartart strategy"
```

---

## Task 11: SmartArt Selector Agent Definition

**Files:**
- Create: `.claude/agents/smartart-selector.md`

- [ ] **Step 1: Write the agent definition**

Create `.claude/agents/smartart-selector.md` following the patterns established in the existing agent files (prompt-engineer.md, image-reviewer.md). The agent definition should include:

- Identity (name, model, authority)
- Input contract (SlideOutline with visual_intent, StyleGuide, TalkBrief, BudgetState)
- Output contract (SmartArtRecommendations schema)
- Selection heuristics (graphic type mapping from content patterns)
- Enrichment tier decision logic
- Negotiation protocol (propose → approve/reject → retry → fallback)
- Budget awareness rules
- Adjacency awareness (don't repeat the same graphic type on consecutive slides)

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/smartart-selector.md
git commit -m "feat: SmartArt Selector agent definition"
```

---

## Task 12: SmartArt Skills (3)

**Files:**
- Create: `.claude/skills/smartart-selector/SKILL.md`
- Create: `.claude/skills/smartart-extractor/SKILL.md`
- Create: `.claude/skills/smartart-renderer/SKILL.md`

- [ ] **Step 1: Write the 3 skill definitions**

Each skill follows the existing pattern (see brand-manager, imagegen-bridge skills for reference). Each reads DeckContext contracts, invokes the appropriate Python module or agent, and writes the output contract.

**smartart-selector** skill:
- Reads: SlideOutline, StyleGuide, TalkBrief, BudgetState
- Dispatches: smartart-selector agent
- Writes: smartart-recommendations.json
- Handles: negotiation loop with narrative-architect

**smartart-extractor** skill:
- Reads: SlideOutline, SmartArtRecommendations, StrategyMap
- Invokes: `src/smartart_extractor.py` via Python
- Writes: smartart-spec.json
- Handles: overflow policies, schema validation

**smartart-renderer** skill:
- Reads: SmartArtSpec, StyleGuide, ImageManifest (enrichment), PipelineState (phase)
- Invokes: `src/smartart_renderer.py` via Python
- Writes: smartart-manifest.json
- Handles: engine dispatch, comparator in draft, enrichment compositing

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/smartart-selector/ .claude/skills/smartart-extractor/ .claude/skills/smartart-renderer/
git commit -m "feat: 3 SmartArt skills — selector, extractor, renderer"
```

---

## Task 13: Integration Test

**Files:**
- Create: `tests/test_smartart_integration.py`

- [ ] **Step 1: Write end-to-end integration test**

```python
# tests/test_smartart_integration.py
"""Integration test — SmartArt extraction + rendering pipeline."""

import json
import os
import tempfile
import pytest


def test_extract_and_render_swot():
    """Full pipeline: extract SWOT data from body_points, render via custom SVG."""
    from src.smartart_extractor import extract
    from src.smartart_renderer import render

    slide = {
        'slide_number': 3,
        'headline': 'SWOT Analysis',
        'body_points': [
            'Strengths: Strong brand, Great team',
            'Weaknesses: Limited funding',
            'Opportunities: AI market growth, Global expansion',
            'Threats: Regulatory risk'
        ]
    }
    selection = {
        'slide_number': 3,
        'graphic_type': 'swot',
        'enrichment_tier': 'pure_programmatic',
        'engine': 'custom_svg'
    }
    style_guide = {
        'palette': {
            'primary': '1a73e8', 'accent': 'e8710a',
            'background': 'ffffff', 'text_primary': '1a1a1a',
            'chart_series': ['2B6CB0', 'ED8936', '38A169', 'E53E3E']
        },
        'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
    }

    # Extract
    spec = extract(slide, selection, style_guide)
    assert spec['validation_status'] == 'valid'
    assert spec['graphic_type'] == 'swot'
    assert len(spec['data']['quadrants']) == 4

    # Render
    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, style_guide, 'draft', tmpdir)
        assert entry['status'] == 'rendered'
        assert os.path.exists(os.path.join(tmpdir, os.path.basename(entry['file_path'])))
        # Check SVG source was saved
        if entry.get('svg_source_path'):
            svg_path = os.path.join(tmpdir, os.path.basename(entry['svg_source_path']))
            assert os.path.exists(svg_path)
            with open(svg_path) as f:
                svg = f.read()
            assert 'Strengths' in svg
            assert '<title>' in svg  # Accessibility


def test_extract_and_render_flowchart_mermaid():
    """Full pipeline: extract flowchart, render via Mermaid CLI."""
    from src.smartart_extractor import extract
    from src.smartart_renderer import render

    slide = {
        'slide_number': 5,
        'headline': 'Our Process',
        'body_points': ['Research', 'Design', 'Build', 'Launch']
    }
    selection = {
        'slide_number': 5,
        'graphic_type': 'flowchart',
        'enrichment_tier': 'pure_programmatic',
        'engine': 'mermaid'
    }
    style_guide = {
        'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a', 'chart_series': []},
        'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
    }

    spec = extract(slide, selection, style_guide)
    assert spec['engine'] == 'mermaid'
    assert 'graph' in spec['data']['syntax']

    with tempfile.TemporaryDirectory() as tmpdir:
        entry = render(spec, style_guide, 'draft', tmpdir)
        assert entry['status'] == 'rendered'
        assert entry['engine_used'] == 'mermaid'
```

- [ ] **Step 2: Run integration tests**

```bash
.venv/bin/pytest tests/test_smartart_integration.py -v
```

- [ ] **Step 3: Run full test suite to verify no regressions**

```bash
.venv/bin/pytest -v
```

Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_smartart_integration.py
git commit -m "test: SmartArt end-to-end integration tests"
```

---

## Task 14: Final Verification + Full Test Run

- [ ] **Step 1: Run complete test suite**

```bash
.venv/bin/pytest -v --tb=short
```

Expected: All tests PASS — existing 518 + new SmartArt tests.

- [ ] **Step 2: Verify JSON schema validity**

```bash
.venv/bin/python -c "
import json, os
schema_dir = 'src/schemas'
for f in os.listdir(schema_dir):
    if f.endswith('.json'):
        with open(os.path.join(schema_dir, f)) as fh:
            json.load(fh)
        print(f'OK: {f}')
"
```

- [ ] **Step 3: Verify Node.js dependencies work**

```bash
npx mmdc --version
npx vl2svg --help 2>&1 | head -1
```

- [ ] **Step 4: Final commit with test count update**

```bash
git add -A
git commit -m "feat: SmartArt intelligent graphics — complete implementation"
```
