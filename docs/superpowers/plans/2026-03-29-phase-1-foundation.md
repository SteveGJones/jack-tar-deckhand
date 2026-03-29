# Phase 1: Foundation — DeckContext & Shared Infrastructure

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the shared DeckContext infrastructure that all skills and agents depend on — directory management, JSON schemas for all 10 data contracts, read/write utilities, caching, and TalkBrief validation.

**Architecture:** A single Python module (`src/deckcontext.py`) provides all DeckContext operations: initialise directories, read/write contract JSON files, validate against JSON Schemas, compute checksums, and manage a content-addressable image cache. JSON Schema files in `src/schemas/` define the contract interfaces between all skills. Everything operates on `./tmp/deck/` per CONSTITUTION Article 4.6.

**Tech Stack:** Python 3.8+, jsonschema, pytest

**Phases overview (this is Phase 1 of 6):**
- **Phase 1: Foundation** (this plan) — DeckContext, schemas, utilities
- Phase 2: Design Services — `slide-stylist`
- Phase 3: Content Services — `narrative-architect`, `speaker-notes-writer`
- Phase 4: Image Services — 8 skills + 1 agent
- Phase 5: Assembly & QA — `deck-assembler`, `deck-qa`, `presentation-reviewer`
- Phase 6: Orchestration — `deck-conductor`

---

## File Structure

```
src/
  schemas/
    talk_brief.schema.json        # TalkBrief validation schema
    pipeline_state.schema.json    # PipelineState tracking schema
    style_guide.schema.json       # StyleGuide design system schema
    slide_outline.schema.json     # SlideOutline narrative schema
    speaker_notes.schema.json     # SpeakerNotes per-slide schema
    image_manifest.schema.json    # ImageManifest registry schema
    chart_manifest.schema.json    # ChartManifest registry schema
    qa_report.schema.json         # QAReport findings schema
  deckcontext.py                  # DeckContext management (init, read, write, validate, cache)
tests/
  test_deckcontext.py             # Tests for deckcontext module
  test_schemas.py                 # Schema validation tests with sample data
  fixtures/
    valid_talk_brief.json         # Valid TalkBrief sample
    valid_style_guide.json        # Valid StyleGuide sample
    valid_slide_outline.json      # Valid SlideOutline sample
    valid_speaker_notes.json      # Valid SpeakerNotes sample
    valid_image_manifest.json     # Valid ImageManifest sample
    valid_chart_manifest.json     # Valid ChartManifest sample
    valid_qa_report.json          # Valid QAReport sample
requirements.txt                  # Python dependencies
```

---

## Task 1: Project Setup

**Files:**
- Modify: `.gitignore`
- Create: `requirements.txt`

- [ ] **Step 1: Add tmp/ to .gitignore**

Append to `.gitignore`:

```
# DeckContext working directory (CONSTITUTION Article 4.6)
tmp/
```

- [ ] **Step 2: Create requirements.txt**

```
jsonschema>=4.20.0
pytest>=8.0.0
```

- [ ] **Step 3: Set up Python virtual environment**

Run:
```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

Expected: Clean install, no errors.

- [ ] **Step 4: Verify setup**

Run:
```bash
source .venv/bin/activate && python3 -c "import jsonschema; print(f'jsonschema {jsonschema.__version__}')" && python3 -m pytest --version
```

Expected: Version numbers printed, no import errors.

- [ ] **Step 5: Commit**

```bash
git add .gitignore requirements.txt
git commit -m "chore: add tmp/ to gitignore and create requirements.txt"
```

---

## Task 2: TalkBrief Schema

**Files:**
- Create: `src/schemas/talk_brief.schema.json`
- Create: `tests/fixtures/valid_talk_brief.json`
- Create: `tests/test_schemas.py`

- [ ] **Step 1: Write the TalkBrief schema test**

Create `tests/test_schemas.py`:

```python
"""Tests for JSON Schema validation of data contracts."""

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


class TestTalkBriefSchema:
    @pytest.fixture
    def schema(self):
        return load_schema('talk_brief')

    def test_valid_minimal_brief(self, schema):
        brief = {
            "topic": "Building AI Agents",
            "audience": "Software engineers",
            "duration_minutes": 30
        }
        validate(instance=brief, schema=schema)

    def test_valid_full_brief(self, schema):
        brief = load_fixture('valid_talk_brief')
        validate(instance=brief, schema=schema)

    def test_missing_topic_fails(self, schema):
        brief = {"audience": "Engineers", "duration_minutes": 30}
        with pytest.raises(ValidationError, match="topic"):
            validate(instance=brief, schema=schema)

    def test_missing_audience_fails(self, schema):
        brief = {"topic": "AI Agents", "duration_minutes": 30}
        with pytest.raises(ValidationError, match="audience"):
            validate(instance=brief, schema=schema)

    def test_missing_duration_fails(self, schema):
        brief = {"topic": "AI Agents", "audience": "Engineers"}
        with pytest.raises(ValidationError, match="duration_minutes"):
            validate(instance=brief, schema=schema)

    def test_invalid_duration_fails(self, schema):
        brief = {"topic": "AI Agents", "audience": "Engineers", "duration_minutes": 7}
        with pytest.raises(ValidationError):
            validate(instance=brief, schema=schema)

    def test_invalid_tone_fails(self, schema):
        brief = {
            "topic": "AI Agents",
            "audience": "Engineers",
            "duration_minutes": 30,
            "tone": "angry"
        }
        with pytest.raises(ValidationError):
            validate(instance=brief, schema=schema)

    def test_invalid_color_format_fails(self, schema):
        brief = {
            "topic": "AI Agents",
            "audience": "Engineers",
            "duration_minutes": 30,
            "branding": {"primary_color": "#FF0000"}
        }
        with pytest.raises(ValidationError):
            validate(instance=brief, schema=schema)

    def test_too_many_takeaways_fails(self, schema):
        brief = {
            "topic": "AI Agents",
            "audience": "Engineers",
            "duration_minutes": 30,
            "key_takeaways": ["one", "two", "three", "four", "five", "six"]
        }
        with pytest.raises(ValidationError):
            validate(instance=brief, schema=schema)

    def test_short_topic_fails(self, schema):
        brief = {"topic": "AI", "audience": "Engineers", "duration_minutes": 30}
        with pytest.raises(ValidationError):
            validate(instance=brief, schema=schema)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_schemas.py::TestTalkBriefSchema -v`

Expected: FAIL — schema file not found.

- [ ] **Step 3: Create the fixture file**

Create `tests/fixtures/valid_talk_brief.json`:

```json
{
  "topic": "Building Production AI Agents with Claude",
  "audience": "Senior software engineers familiar with LLMs but new to agent frameworks",
  "duration_minutes": 30,
  "tone": "technical",
  "key_takeaways": [
    "Agent loops are just tool-calling in a while loop",
    "State management is the hard part, not the AI",
    "Start with the simplest agent that could work"
  ],
  "branding": {
    "company_name": "Acme Corp",
    "primary_color": "1A365D",
    "secondary_color": "E2E8F0"
  },
  "preferences": {
    "style": "image-rich",
    "slide_count_hint": 20,
    "image_backend": "ollama",
    "resolution": "1080p",
    "include_speaker_notes": true,
    "include_charts": false
  },
  "data_sources": []
}
```

- [ ] **Step 4: Create the TalkBrief schema**

Create `src/schemas/talk_brief.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/talk-brief.json",
  "title": "TalkBrief",
  "description": "Speaker input defining the talk topic, audience, duration, and preferences.",
  "type": "object",
  "required": ["topic", "audience", "duration_minutes"],
  "additionalProperties": false,
  "properties": {
    "topic": {
      "type": "string",
      "minLength": 3,
      "description": "The talk topic or title."
    },
    "audience": {
      "type": "string",
      "description": "Description of the target audience."
    },
    "duration_minutes": {
      "type": "integer",
      "enum": [5, 10, 15, 20, 30, 45, 60, 90],
      "description": "Talk duration in minutes."
    },
    "tone": {
      "type": "string",
      "enum": ["professional", "conversational", "technical", "inspirational", "provocative", "storytelling"],
      "default": "professional"
    },
    "key_takeaways": {
      "type": "array",
      "items": {"type": "string"},
      "minItems": 1,
      "maxItems": 5
    },
    "branding": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "company_name": {"type": "string"},
        "logo_path": {"type": "string"},
        "primary_color": {"type": "string", "pattern": "^[0-9A-Fa-f]{6}$"},
        "secondary_color": {"type": "string", "pattern": "^[0-9A-Fa-f]{6}$"},
        "font_preference": {"type": "string"}
      }
    },
    "preferences": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "style": {
          "type": "string",
          "enum": ["minimalist", "data-heavy", "image-rich", "diagram-heavy", "corporate", "creative"],
          "default": "image-rich"
        },
        "slide_count_hint": {
          "type": "integer",
          "minimum": 3,
          "maximum": 60
        },
        "image_backend": {
          "type": "string",
          "enum": ["ollama", "dalle3", "flux-replicate", "stable-diffusion", "ideogram"],
          "default": "ollama"
        },
        "resolution": {
          "type": "string",
          "enum": ["1080p", "1440p"],
          "default": "1080p"
        },
        "include_speaker_notes": {
          "type": "boolean",
          "default": true
        },
        "include_charts": {
          "type": "boolean",
          "default": false
        }
      }
    },
    "data_sources": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["label", "type", "content"],
        "additionalProperties": false,
        "properties": {
          "label": {"type": "string"},
          "type": {
            "type": "string",
            "enum": ["inline_json", "csv_path", "description"]
          },
          "content": {"type": "string"}
        }
      }
    }
  }
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_schemas.py::TestTalkBriefSchema -v`

Expected: All 9 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/schemas/talk_brief.schema.json tests/test_schemas.py tests/fixtures/valid_talk_brief.json
git commit -m "feat: add TalkBrief JSON Schema with validation tests"
```

---

## Task 3: Remaining Data Contract Schemas

**Files:**
- Create: `src/schemas/pipeline_state.schema.json`
- Create: `src/schemas/style_guide.schema.json`
- Create: `src/schemas/slide_outline.schema.json`
- Create: `src/schemas/speaker_notes.schema.json`
- Create: `src/schemas/image_manifest.schema.json`
- Create: `src/schemas/chart_manifest.schema.json`
- Create: `src/schemas/qa_report.schema.json`
- Create: `tests/fixtures/valid_style_guide.json`
- Create: `tests/fixtures/valid_slide_outline.json`
- Create: `tests/fixtures/valid_speaker_notes.json`
- Create: `tests/fixtures/valid_image_manifest.json`
- Create: `tests/fixtures/valid_chart_manifest.json`
- Create: `tests/fixtures/valid_qa_report.json`
- Modify: `tests/test_schemas.py`

- [ ] **Step 1: Write schema validation tests for all remaining contracts**

Add to `tests/test_schemas.py`:

```python
class TestStyleGuideSchema:
    @pytest.fixture
    def schema(self):
        return load_schema('style_guide')

    def test_valid_style_guide(self, schema):
        guide = load_fixture('valid_style_guide')
        validate(instance=guide, schema=schema)

    def test_missing_palette_fails(self, schema):
        guide = {"typography": {"heading_font": "Inter", "body_font": "Inter"}, "layout": {}}
        with pytest.raises(ValidationError, match="palette"):
            validate(instance=guide, schema=schema)

    def test_invalid_color_format_fails(self, schema):
        guide = load_fixture('valid_style_guide')
        guide["palette"]["primary"] = "#FF0000"
        with pytest.raises(ValidationError):
            validate(instance=guide, schema=schema)


class TestSlideOutlineSchema:
    @pytest.fixture
    def schema(self):
        return load_schema('slide_outline')

    def test_valid_outline(self, schema):
        outline = load_fixture('valid_slide_outline')
        validate(instance=outline, schema=schema)

    def test_missing_slides_fails(self, schema):
        outline = {"narrative_arc": "problem-solution", "estimated_duration_minutes": 30}
        with pytest.raises(ValidationError, match="slides"):
            validate(instance=outline, schema=schema)

    def test_invalid_slide_type_fails(self, schema):
        outline = load_fixture('valid_slide_outline')
        outline["slides"][0]["slide_type"] = "invalid_type"
        with pytest.raises(ValidationError):
            validate(instance=outline, schema=schema)


class TestSpeakerNotesSchema:
    @pytest.fixture
    def schema(self):
        return load_schema('speaker_notes')

    def test_valid_notes(self, schema):
        notes = load_fixture('valid_speaker_notes')
        validate(instance=notes, schema=schema)

    def test_missing_notes_array_fails(self, schema):
        with pytest.raises(ValidationError, match="notes"):
            validate(instance={"target_pace_wpm": 130}, schema=schema)


class TestImageManifestSchema:
    @pytest.fixture
    def schema(self):
        return load_schema('image_manifest')

    def test_valid_manifest(self, schema):
        manifest = load_fixture('valid_image_manifest')
        validate(instance=manifest, schema=schema)

    def test_invalid_status_fails(self, schema):
        manifest = load_fixture('valid_image_manifest')
        manifest["images"][0]["status"] = "broken"
        with pytest.raises(ValidationError):
            validate(instance=manifest, schema=schema)


class TestChartManifestSchema:
    @pytest.fixture
    def schema(self):
        return load_schema('chart_manifest')

    def test_valid_manifest(self, schema):
        manifest = load_fixture('valid_chart_manifest')
        validate(instance=manifest, schema=schema)

    def test_invalid_chart_type_fails(self, schema):
        manifest = load_fixture('valid_chart_manifest')
        manifest["charts"][0]["chart_type"] = "sunburst"
        with pytest.raises(ValidationError):
            validate(instance=manifest, schema=schema)


class TestQAReportSchema:
    @pytest.fixture
    def schema(self):
        return load_schema('qa_report')

    def test_valid_report(self, schema):
        report = load_fixture('valid_qa_report')
        validate(instance=report, schema=schema)

    def test_invalid_verdict_fails(self, schema):
        report = {"verdict": "maybe", "findings": []}
        with pytest.raises(ValidationError):
            validate(instance=report, schema=schema)

    def test_invalid_severity_fails(self, schema):
        report = load_fixture('valid_qa_report')
        report["findings"][0]["severity"] = "critical"
        with pytest.raises(ValidationError):
            validate(instance=report, schema=schema)


class TestPipelineStateSchema:
    @pytest.fixture
    def schema(self):
        return load_schema('pipeline_state')

    def test_valid_state(self, schema):
        state = {
            "pipeline_id": "2026-03-29T12:00:00Z",
            "created_at": "2026-03-29T12:00:00Z",
            "status": "running",
            "current_step": "slide-stylist",
            "steps": {
                "validate-brief": {
                    "status": "completed",
                    "started_at": "2026-03-29T12:00:01Z",
                    "completed_at": "2026-03-29T12:00:02Z"
                },
                "slide-stylist": {
                    "status": "running",
                    "started_at": "2026-03-29T12:00:03Z"
                }
            }
        }
        validate(instance=state, schema=schema)

    def test_invalid_status_fails(self, schema):
        state = {
            "pipeline_id": "test",
            "created_at": "2026-03-29T12:00:00Z",
            "status": "crashed",
            "steps": {}
        }
        with pytest.raises(ValidationError):
            validate(instance=state, schema=schema)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_schemas.py -v`

Expected: TalkBrief tests pass, all new tests FAIL (missing schemas and fixtures).

- [ ] **Step 3: Create all fixture files**

Create `tests/fixtures/valid_style_guide.json`:

```json
{
  "palette": {
    "primary": "1A365D",
    "secondary": "2B6CB0",
    "accent": "ED8936",
    "background": "FFFFFF",
    "background_alt": "1A202C",
    "text_primary": "1A202C",
    "text_muted": "718096",
    "text_on_dark": "F7FAFC",
    "chart_series": ["2B6CB0", "ED8936", "38A169", "E53E3E", "805AD5"]
  },
  "typography": {
    "heading_font": "Inter",
    "body_font": "Inter",
    "mono_font": "JetBrains Mono",
    "heading_sizes": {
      "title_slide": 44,
      "section_divider": 36,
      "slide_heading": 28,
      "subheading": 20
    },
    "body_size": 16,
    "caption_size": 12,
    "line_spacing": 1.4
  },
  "layout": {
    "slide_width_inches": 10,
    "slide_height_inches": 5.625,
    "margin_inches": 0.5,
    "templates": {
      "content": {
        "description": "Standard content slide with text and optional image",
        "text_zone": {"x": 0.5, "y": 1.0, "w": 5.5, "h": 4.0},
        "image_zone": {"x": 6.5, "y": 0.5, "w": 3.0, "h": 4.625},
        "background_treatment": "solid_light"
      }
    }
  },
  "image_style_tokens": {
    "mood": "professional and calm",
    "color_direction": "predominantly deep blue and white tones",
    "style_modifiers": ["clean lines", "minimal", "corporate photography style"]
  }
}
```

Create `tests/fixtures/valid_slide_outline.json`:

```json
{
  "narrative_arc": "problem-solution",
  "estimated_duration_minutes": 30,
  "total_slides": 3,
  "slides": [
    {
      "slide_number": 1,
      "slide_type": "title",
      "headline": "Building Production AI Agents",
      "body_points": [],
      "narrative_beat": "hook",
      "visual_direction": "Abstract network of connected nodes in deep blue, conveying interconnected intelligence",
      "visual_type": "hero_image",
      "layout_template": "title"
    },
    {
      "slide_number": 2,
      "slide_type": "content",
      "headline": "The Agent Loop Is Simple",
      "body_points": [
        "Receive input from user",
        "Call tools in a loop",
        "Return results when done"
      ],
      "narrative_beat": "evidence-1",
      "visual_direction": "Simple flowchart showing a circular loop with three steps",
      "visual_type": "diagram",
      "layout_template": "content",
      "transition_note": "Now that we've set the stage, let's look at how agents actually work..."
    },
    {
      "slide_number": 3,
      "slide_type": "closing",
      "headline": "Start Simple, Iterate Fast",
      "body_points": [
        "Begin with the simplest agent that could work",
        "Add complexity only when you hit limits"
      ],
      "narrative_beat": "cta",
      "visual_type": "none",
      "layout_template": "closing"
    }
  ]
}
```

Create `tests/fixtures/valid_speaker_notes.json`:

```json
{
  "target_pace_wpm": 130,
  "total_estimated_minutes": 28,
  "notes": [
    {
      "slide_number": 1,
      "text": "Welcome everyone. Today we're going to demystify AI agents. By the end of this talk, you'll see that the core loop is surprisingly simple.",
      "estimated_seconds": 20,
      "timing_marker": "~0:00",
      "cues": [
        {"type": "pause", "text": "Let the title slide breathe for 3 seconds before speaking"}
      ]
    },
    {
      "slide_number": 2,
      "text": "Here's the thing that surprised me most when I started building agents. The loop is just: get input, call tools, return results. That's it.",
      "estimated_seconds": 45,
      "timing_marker": "~0:20",
      "cues": [
        {"type": "emphasis", "text": "Stress 'That's it' — this is the key insight"}
      ]
    }
  ]
}
```

Create `tests/fixtures/valid_image_manifest.json`:

```json
{
  "generated_at": "2026-03-29T12:00:00Z",
  "image_backend": "ollama",
  "images": [
    {
      "image_id": "slide-01-hero",
      "slide_number": 1,
      "file_path": "./tmp/deck/images/slide-01-hero.png",
      "placement_zone": "background",
      "dimensions": {"width": 1920, "height": 1080},
      "source_prompt": "Abstract network of connected nodes in deep blue, clean lines, minimal",
      "model_used": "x/z-image-turbo",
      "alt_text": "Abstract network visualization",
      "content_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
      "cache_key": "f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5",
      "status": "generated",
      "retry_count": 0,
      "generation_time_seconds": 12.5
    }
  ],
  "summary": {
    "total_images": 1,
    "generated_count": 1,
    "cached_count": 0,
    "placeholder_count": 0,
    "failed_count": 0,
    "total_generation_seconds": 12.5
  }
}
```

Create `tests/fixtures/valid_chart_manifest.json`:

```json
{
  "charts": [
    {
      "chart_id": "slide-05-bar",
      "slide_number": 5,
      "file_path": "./tmp/deck/images/slide-05-chart.png",
      "chart_type": "bar",
      "status": "rendered",
      "data_source_label": "quarterly_revenue",
      "alt_text": "Bar chart showing quarterly revenue growth",
      "dimensions": {"width": 1920, "height": 1080},
      "content_hash": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3"
    }
  ]
}
```

Create `tests/fixtures/valid_qa_report.json`:

```json
{
  "inspected_at": "2026-03-29T12:05:00Z",
  "pptx_path": "./tmp/deck/output/presentation.pptx",
  "verdict": "pass_with_warnings",
  "summary": {
    "total_slides": 20,
    "errors": 0,
    "warnings": 2,
    "info": 1
  },
  "findings": [
    {
      "slide_number": 7,
      "severity": "warning",
      "category": "contrast",
      "description": "Text contrast ratio 3.8:1 is below recommended 4.5:1 for body text",
      "suggested_fix": "Darken text color or lighten background",
      "affected_element": "body text",
      "auto_fixable": false
    },
    {
      "slide_number": 12,
      "severity": "warning",
      "category": "margin",
      "description": "Image extends within 0.3 inches of slide edge (minimum 0.5 inches)",
      "suggested_fix": "Resize or reposition image to respect safe margins",
      "affected_element": "hero image",
      "auto_fixable": true
    },
    {
      "slide_number": 15,
      "severity": "info",
      "category": "consistency",
      "description": "Body font size 14pt differs from deck standard 16pt",
      "suggested_fix": "Increase font size to 16pt for consistency",
      "affected_element": "body text",
      "auto_fixable": true
    }
  ]
}
```

- [ ] **Step 4: Create all remaining schema files**

Create `src/schemas/style_guide.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/style-guide.json",
  "title": "StyleGuide",
  "description": "Visual design system derived from TalkBrief and brand assets.",
  "type": "object",
  "required": ["palette", "typography", "layout"],
  "properties": {
    "palette": {
      "type": "object",
      "required": ["primary", "secondary", "accent", "background", "background_alt", "text_primary", "text_muted"],
      "properties": {
        "primary": {"type": "string", "pattern": "^[0-9A-Fa-f]{6}$"},
        "secondary": {"type": "string", "pattern": "^[0-9A-Fa-f]{6}$"},
        "accent": {"type": "string", "pattern": "^[0-9A-Fa-f]{6}$"},
        "background": {"type": "string", "pattern": "^[0-9A-Fa-f]{6}$"},
        "background_alt": {"type": "string", "pattern": "^[0-9A-Fa-f]{6}$"},
        "text_primary": {"type": "string", "pattern": "^[0-9A-Fa-f]{6}$"},
        "text_muted": {"type": "string", "pattern": "^[0-9A-Fa-f]{6}$"},
        "text_on_dark": {"type": "string", "pattern": "^[0-9A-Fa-f]{6}$"},
        "chart_series": {
          "type": "array",
          "items": {"type": "string", "pattern": "^[0-9A-Fa-f]{6}$"},
          "minItems": 3,
          "maxItems": 8
        }
      }
    },
    "typography": {
      "type": "object",
      "required": ["heading_font", "body_font"],
      "properties": {
        "heading_font": {"type": "string"},
        "body_font": {"type": "string"},
        "mono_font": {"type": "string"},
        "heading_sizes": {
          "type": "object",
          "properties": {
            "title_slide": {"type": "number"},
            "section_divider": {"type": "number"},
            "slide_heading": {"type": "number"},
            "subheading": {"type": "number"}
          }
        },
        "body_size": {"type": "number"},
        "caption_size": {"type": "number"},
        "line_spacing": {"type": "number"}
      }
    },
    "layout": {
      "type": "object",
      "properties": {
        "slide_width_inches": {"type": "number"},
        "slide_height_inches": {"type": "number"},
        "margin_inches": {"type": "number"},
        "templates": {
          "type": "object",
          "additionalProperties": {
            "type": "object",
            "properties": {
              "description": {"type": "string"},
              "text_zone": {
                "type": "object",
                "properties": {
                  "x": {"type": "number"},
                  "y": {"type": "number"},
                  "w": {"type": "number"},
                  "h": {"type": "number"}
                }
              },
              "image_zone": {
                "type": "object",
                "properties": {
                  "x": {"type": "number"},
                  "y": {"type": "number"},
                  "w": {"type": "number"},
                  "h": {"type": "number"}
                }
              },
              "background_treatment": {
                "type": "string",
                "enum": ["solid_light", "solid_dark", "image_bleed", "pattern_tile", "gradient"]
              }
            }
          }
        }
      }
    },
    "image_style_tokens": {
      "type": "object",
      "properties": {
        "mood": {"type": "string"},
        "color_direction": {"type": "string"},
        "style_modifiers": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    }
  }
}
```

Create `src/schemas/slide_outline.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/slide-outline.json",
  "title": "SlideOutline",
  "description": "Structured slide plan with per-slide type, content, and visual direction.",
  "type": "object",
  "required": ["narrative_arc", "estimated_duration_minutes", "slides"],
  "properties": {
    "narrative_arc": {"type": "string"},
    "estimated_duration_minutes": {"type": "number"},
    "total_slides": {"type": "integer"},
    "slides": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["slide_number", "slide_type", "headline"],
        "properties": {
          "slide_number": {"type": "integer", "minimum": 1},
          "slide_type": {
            "type": "string",
            "enum": ["title", "section_divider", "content", "two_column", "image_feature", "data_chart", "stat_callout", "quote", "icon_grid", "diagram", "closing", "blank_visual"]
          },
          "headline": {"type": "string"},
          "body_points": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 5
          },
          "narrative_beat": {"type": "string"},
          "visual_direction": {"type": "string"},
          "visual_type": {
            "type": "string",
            "enum": ["hero_image", "diagram", "chart", "icon_set", "pattern_background", "none"]
          },
          "data": {
            "type": "object",
            "properties": {
              "chart_type": {
                "type": "string",
                "enum": ["bar", "line", "area", "pie", "donut", "scatter", "comparison_table", "timeline", "stat_card"]
              },
              "data_source_label": {"type": "string"},
              "inline_data": {"type": "object"}
            }
          },
          "layout_template": {"type": "string"},
          "transition_note": {"type": "string"}
        }
      }
    }
  }
}
```

Create `src/schemas/speaker_notes.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/speaker-notes.json",
  "title": "SpeakerNotes",
  "description": "Per-slide timed speaker notes with cues.",
  "type": "object",
  "required": ["notes"],
  "properties": {
    "target_pace_wpm": {"type": "integer"},
    "total_estimated_minutes": {"type": "number"},
    "notes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["slide_number", "text"],
        "properties": {
          "slide_number": {"type": "integer"},
          "text": {"type": "string"},
          "estimated_seconds": {"type": "integer"},
          "timing_marker": {"type": "string"},
          "cues": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "type": {
                  "type": "string",
                  "enum": ["transition", "pause", "audience_interaction", "emphasis", "demo", "build_animation"]
                },
                "text": {"type": "string"}
              }
            }
          }
        }
      }
    }
  }
}
```

Create `src/schemas/image_manifest.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/image-manifest.json",
  "title": "ImageManifest",
  "description": "Registry of generated image assets with provenance and status.",
  "type": "object",
  "required": ["images"],
  "properties": {
    "generated_at": {"type": "string"},
    "image_backend": {"type": "string"},
    "images": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["image_id", "slide_number", "file_path", "status"],
        "properties": {
          "image_id": {"type": "string"},
          "slide_number": {"type": "integer"},
          "file_path": {"type": "string"},
          "placement_zone": {"type": "string"},
          "dimensions": {
            "type": "object",
            "properties": {
              "width": {"type": "integer"},
              "height": {"type": "integer"}
            }
          },
          "source_prompt": {"type": "string"},
          "model_used": {"type": "string"},
          "alt_text": {"type": "string"},
          "content_hash": {"type": "string"},
          "cache_key": {"type": "string"},
          "status": {
            "type": "string",
            "enum": ["generated", "cached", "placeholder", "failed"]
          },
          "retry_count": {"type": "integer"},
          "generation_time_seconds": {"type": "number"}
        }
      }
    },
    "summary": {
      "type": "object",
      "properties": {
        "total_images": {"type": "integer"},
        "generated_count": {"type": "integer"},
        "cached_count": {"type": "integer"},
        "placeholder_count": {"type": "integer"},
        "failed_count": {"type": "integer"},
        "total_generation_seconds": {"type": "number"}
      }
    }
  }
}
```

Create `src/schemas/chart_manifest.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/chart-manifest.json",
  "title": "ChartManifest",
  "description": "Registry of rendered chart images.",
  "type": "object",
  "required": ["charts"],
  "properties": {
    "charts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["chart_id", "slide_number", "file_path", "chart_type", "status"],
        "properties": {
          "chart_id": {"type": "string"},
          "slide_number": {"type": "integer"},
          "file_path": {"type": "string"},
          "chart_type": {
            "type": "string",
            "enum": ["bar", "line", "area", "pie", "donut", "scatter", "comparison_table", "timeline", "stat_card"]
          },
          "status": {
            "type": "string",
            "enum": ["rendered", "cached", "failed"]
          },
          "data_source_label": {"type": "string"},
          "alt_text": {"type": "string"},
          "dimensions": {
            "type": "object",
            "properties": {
              "width": {"type": "integer"},
              "height": {"type": "integer"}
            }
          },
          "content_hash": {"type": "string"}
        }
      }
    }
  }
}
```

Create `src/schemas/qa_report.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/qa-report.json",
  "title": "QAReport",
  "description": "Automated QA findings with verdict and per-slide issues.",
  "type": "object",
  "required": ["verdict", "findings"],
  "properties": {
    "inspected_at": {"type": "string"},
    "pptx_path": {"type": "string"},
    "verdict": {
      "type": "string",
      "enum": ["pass", "pass_with_warnings", "fail"]
    },
    "summary": {
      "type": "object",
      "properties": {
        "total_slides": {"type": "integer"},
        "errors": {"type": "integer"},
        "warnings": {"type": "integer"},
        "info": {"type": "integer"}
      }
    },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["slide_number", "severity", "category", "description"],
        "properties": {
          "slide_number": {"type": "integer"},
          "severity": {
            "type": "string",
            "enum": ["error", "warning", "info"]
          },
          "category": {
            "type": "string",
            "enum": ["overlap", "contrast", "margin", "text_overflow", "consistency", "image_quality", "placeholder_residue", "missing_content", "accessibility"]
          },
          "description": {"type": "string"},
          "suggested_fix": {"type": "string"},
          "affected_element": {"type": "string"},
          "auto_fixable": {"type": "boolean"}
        }
      }
    }
  }
}
```

Create `src/schemas/pipeline_state.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/pipeline-state.json",
  "title": "PipelineState",
  "description": "Pipeline execution metadata and step tracking.",
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
    "current_step": {"type": "string"},
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

- [ ] **Step 5: Run all schema tests**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_schemas.py -v`

Expected: All tests PASS (TalkBrief + 7 new contract test classes).

- [ ] **Step 6: Commit**

```bash
git add src/schemas/ tests/fixtures/ tests/test_schemas.py
git commit -m "feat: add JSON Schemas and fixtures for all 8 data contracts"
```

---

## Task 4: DeckContext Management Module

**Files:**
- Create: `src/deckcontext.py`
- Create: `tests/test_deckcontext.py`

- [ ] **Step 1: Write the DeckContext tests**

Create `tests/test_deckcontext.py`:

```python
"""Tests for DeckContext directory and state management."""

import json
import os
import shutil
import pytest

# All tests use a temporary deck dir to avoid polluting ./tmp/deck/
DECK_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'test-deck')


@pytest.fixture(autouse=True)
def clean_deck_dir():
    """Remove and recreate test deck directory for each test."""
    if os.path.exists(DECK_DIR):
        shutil.rmtree(DECK_DIR)
    yield
    if os.path.exists(DECK_DIR):
        shutil.rmtree(DECK_DIR)


class TestInit:
    def test_init_creates_directory_structure(self):
        from src.deckcontext import init_deck
        init_deck(DECK_DIR)
        assert os.path.isdir(DECK_DIR)
        assert os.path.isdir(os.path.join(DECK_DIR, 'images'))
        assert os.path.isdir(os.path.join(DECK_DIR, 'output'))

    def test_init_creates_pipeline_state(self):
        from src.deckcontext import init_deck
        init_deck(DECK_DIR)
        state_path = os.path.join(DECK_DIR, 'pipeline-state.json')
        assert os.path.isfile(state_path)
        with open(state_path) as f:
            state = json.load(f)
        assert state['status'] == 'running'
        assert 'steps' in state

    def test_init_is_idempotent(self):
        from src.deckcontext import init_deck
        init_deck(DECK_DIR)
        # Write a file, then re-init — file should survive
        marker = os.path.join(DECK_DIR, 'images', 'test.txt')
        with open(marker, 'w') as f:
            f.write('keep me')
        init_deck(DECK_DIR)
        assert os.path.isfile(marker)


class TestReadWrite:
    def test_write_and_read_contract(self):
        from src.deckcontext import init_deck, write_contract, read_contract
        init_deck(DECK_DIR)
        brief = {"topic": "Test Talk", "audience": "Testers", "duration_minutes": 30}
        write_contract(DECK_DIR, 'talk-brief', brief)
        loaded = read_contract(DECK_DIR, 'talk-brief')
        assert loaded == brief

    def test_write_validates_against_schema(self):
        from src.deckcontext import init_deck, write_contract
        from jsonschema import ValidationError
        init_deck(DECK_DIR)
        invalid = {"audience": "Testers"}  # missing required 'topic'
        with pytest.raises(ValidationError):
            write_contract(DECK_DIR, 'talk-brief', invalid)

    def test_read_nonexistent_returns_none(self):
        from src.deckcontext import init_deck, read_contract
        init_deck(DECK_DIR)
        result = read_contract(DECK_DIR, 'talk-brief')
        assert result is None

    def test_write_skips_validation_when_no_schema(self):
        from src.deckcontext import init_deck, write_contract, read_contract
        init_deck(DECK_DIR)
        # pipeline-state has a schema, but custom names shouldn't crash
        data = {"custom": "data"}
        write_contract(DECK_DIR, 'custom-data', data, validate=False)
        assert read_contract(DECK_DIR, 'custom-data') == data


class TestChecksum:
    def test_compute_file_checksum(self):
        from src.deckcontext import init_deck, write_contract, compute_checksum
        init_deck(DECK_DIR)
        brief = {"topic": "Test Talk", "audience": "Testers", "duration_minutes": 30}
        write_contract(DECK_DIR, 'talk-brief', brief)
        checksum = compute_checksum(os.path.join(DECK_DIR, 'talk-brief.json'))
        assert len(checksum) == 64  # SHA-256 hex digest
        # Same content = same checksum
        checksum2 = compute_checksum(os.path.join(DECK_DIR, 'talk-brief.json'))
        assert checksum == checksum2


class TestPipelineState:
    def test_update_step_status(self):
        from src.deckcontext import init_deck, update_step, read_contract
        init_deck(DECK_DIR)
        update_step(DECK_DIR, 'slide-stylist', 'running')
        state = read_contract(DECK_DIR, 'pipeline-state')
        assert state['steps']['slide-stylist']['status'] == 'running'
        assert state['current_step'] == 'slide-stylist'

    def test_complete_step(self):
        from src.deckcontext import init_deck, update_step, read_contract
        init_deck(DECK_DIR)
        update_step(DECK_DIR, 'slide-stylist', 'running')
        update_step(DECK_DIR, 'slide-stylist', 'completed',
                    output_file='style-guide.json')
        state = read_contract(DECK_DIR, 'pipeline-state')
        step = state['steps']['slide-stylist']
        assert step['status'] == 'completed'
        assert step['output_file'] == 'style-guide.json'
        assert 'completed_at' in step
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_deckcontext.py -v`

Expected: FAIL — `src.deckcontext` module not found.

- [ ] **Step 3: Implement the DeckContext module**

Create `src/deckcontext.py`:

```python
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

# Map contract names to their schema files
CONTRACT_SCHEMAS = {
    'talk-brief': 'talk_brief.schema.json',
    'pipeline-state': 'pipeline_state.schema.json',
    'style-guide': 'style_guide.schema.json',
    'outline': 'slide_outline.schema.json',
    'speaker-notes': 'speaker_notes.schema.json',
    'image-manifest': 'image_manifest.schema.json',
    'chart-manifest': 'chart_manifest.schema.json',
    'qa-report': 'qa_report.schema.json',
}

DEFAULT_STEP_ORDER = [
    'validate-brief',
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
    """Load the JSON Schema for a contract, or return None if not found."""
    schema_file = CONTRACT_SCHEMAS.get(contract_name)
    if not schema_file:
        return None
    path = os.path.join(SCHEMA_DIR, schema_file)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def init_deck(deck_dir='./tmp/deck'):
    """Initialise the DeckContext directory structure.

    Creates the directory, images/ and output/ subdirectories,
    and a fresh pipeline-state.json if one doesn't already exist.
    Idempotent — safe to call multiple times.
    """
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
    """Write a data contract JSON file, optionally validating against its schema.

    Args:
        deck_dir: Path to the DeckContext directory.
        contract_name: Contract name (e.g., 'talk-brief', 'style-guide').
        data: Dictionary to write as JSON.
        validate: If True, validate against the contract's JSON Schema.
                  Raises jsonschema.ValidationError on failure.
    """
    if validate:
        schema = _load_schema(contract_name)
        if schema:
            jsonschema.validate(instance=data, schema=schema)

    path = os.path.join(deck_dir, f'{contract_name}.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def read_contract(deck_dir, contract_name):
    """Read a data contract JSON file. Returns None if file doesn't exist."""
    path = os.path.join(deck_dir, f'{contract_name}.json')
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def compute_checksum(file_path):
    """Compute SHA-256 hex digest of a file's contents."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def update_step(deck_dir, step_name, status, output_file=None, error=None):
    """Update a pipeline step's status in pipeline-state.json.

    Args:
        deck_dir: Path to the DeckContext directory.
        step_name: Step name (e.g., 'slide-stylist').
        status: New status ('pending', 'running', 'completed', 'failed', 'skipped').
        output_file: Optional path to the step's output file.
        error: Optional error message for failed steps.
    """
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

    # Write without schema validation since we're updating internal state
    write_contract(deck_dir, 'pipeline-state', state, validate=False)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_deckcontext.py -v`

Expected: All 9 tests PASS.

- [ ] **Step 5: Run all tests together**

Run: `source .venv/bin/activate && python3 -m pytest tests/ -v`

Expected: All tests PASS (schema tests + deckcontext tests).

- [ ] **Step 6: Commit**

```bash
git add src/deckcontext.py tests/test_deckcontext.py
git commit -m "feat: add DeckContext management module with init, read, write, validate, checksum"
```

---

## Task 5: Integration Test — Full DeckContext Lifecycle

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write the integration test**

Create `tests/test_integration.py`:

```python
"""Integration test: full DeckContext lifecycle from init to QA report."""

import json
import os
import shutil
import pytest

DECK_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'test-deck-integration')
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


def test_full_pipeline_lifecycle():
    """Simulate a complete pipeline run through DeckContext:
    init -> write brief -> update steps -> write all contracts -> verify checksums.
    """
    from src.deckcontext import (
        init_deck, write_contract, read_contract,
        update_step, compute_checksum,
    )

    # 1. Init
    init_deck(DECK_DIR)
    state = read_contract(DECK_DIR, 'pipeline-state')
    assert state['status'] == 'running'

    # 2. Write TalkBrief
    brief = load_fixture('valid_talk_brief')
    write_contract(DECK_DIR, 'talk-brief', brief)
    update_step(DECK_DIR, 'validate-brief', 'completed', output_file='talk-brief.json')

    # 3. Write StyleGuide
    update_step(DECK_DIR, 'slide-stylist', 'running')
    guide = load_fixture('valid_style_guide')
    write_contract(DECK_DIR, 'style-guide', guide)
    update_step(DECK_DIR, 'slide-stylist', 'completed', output_file='style-guide.json')

    # 4. Write SlideOutline
    update_step(DECK_DIR, 'narrative-architect', 'running')
    outline = load_fixture('valid_slide_outline')
    write_contract(DECK_DIR, 'outline', outline)
    update_step(DECK_DIR, 'narrative-architect', 'completed', output_file='outline.json')

    # 5. Write SpeakerNotes
    update_step(DECK_DIR, 'speaker-notes-writer', 'running')
    notes = load_fixture('valid_speaker_notes')
    write_contract(DECK_DIR, 'speaker-notes', notes)
    update_step(DECK_DIR, 'speaker-notes-writer', 'completed', output_file='speaker-notes.json')

    # 6. Write ImageManifest
    update_step(DECK_DIR, 'imagegen-bridge', 'running')
    manifest = load_fixture('valid_image_manifest')
    write_contract(DECK_DIR, 'image-manifest', manifest)
    update_step(DECK_DIR, 'imagegen-bridge', 'completed', output_file='image-manifest.json')

    # 7. Write ChartManifest
    update_step(DECK_DIR, 'chart-renderer', 'running')
    charts = load_fixture('valid_chart_manifest')
    write_contract(DECK_DIR, 'chart-manifest', charts)
    update_step(DECK_DIR, 'chart-renderer', 'completed', output_file='chart-manifest.json')

    # 8. Write QAReport
    update_step(DECK_DIR, 'deck-qa', 'running')
    report = load_fixture('valid_qa_report')
    write_contract(DECK_DIR, 'qa-report', report)
    update_step(DECK_DIR, 'deck-qa', 'completed', output_file='qa-report.json')

    # Verify final state
    final_state = read_contract(DECK_DIR, 'pipeline-state')
    completed_steps = [
        name for name, step in final_state['steps'].items()
        if step.get('status') == 'completed'
    ]
    assert len(completed_steps) == 7

    # Verify all contract files exist and have valid checksums
    expected_files = [
        'talk-brief.json', 'style-guide.json', 'outline.json',
        'speaker-notes.json', 'image-manifest.json',
        'chart-manifest.json', 'qa-report.json', 'pipeline-state.json',
    ]
    for filename in expected_files:
        filepath = os.path.join(DECK_DIR, filename)
        assert os.path.isfile(filepath), f'Missing: {filename}'
        checksum = compute_checksum(filepath)
        assert len(checksum) == 64, f'Invalid checksum for {filename}'

    # Verify each contract can be read back and matches what was written
    assert read_contract(DECK_DIR, 'talk-brief') == brief
    assert read_contract(DECK_DIR, 'style-guide') == guide
    assert read_contract(DECK_DIR, 'outline') == outline
    assert read_contract(DECK_DIR, 'speaker-notes') == notes
    assert read_contract(DECK_DIR, 'image-manifest') == manifest
    assert read_contract(DECK_DIR, 'chart-manifest') == charts
    assert read_contract(DECK_DIR, 'qa-report') == report
```

- [ ] **Step 2: Run the integration test**

Run: `source .venv/bin/activate && python3 -m pytest tests/test_integration.py -v`

Expected: PASS — full lifecycle works end-to-end.

- [ ] **Step 3: Run the complete test suite**

Run: `source .venv/bin/activate && python3 -m pytest tests/ -v --tb=short`

Expected: All tests PASS across all test files.

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration test for full DeckContext lifecycle"
```

---

## Task 6: Create __init__.py and Verify Imports

**Files:**
- Create: `src/__init__.py`
- Create: `src/schemas/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/fixtures/.gitkeep` (if not already tracked)

- [ ] **Step 1: Create init files**

Create `src/__init__.py` (empty file):
```python
```

Create `src/schemas/__init__.py` (empty file):
```python
```

Create `tests/__init__.py` (empty file):
```python
```

- [ ] **Step 2: Verify the full test suite passes with proper imports**

Run: `source .venv/bin/activate && python3 -m pytest tests/ -v --tb=short`

Expected: All tests PASS.

- [ ] **Step 3: Verify Python syntax is clean**

Run: `source .venv/bin/activate && python3 -m py_compile src/deckcontext.py && echo "Syntax OK"`

Expected: "Syntax OK"

- [ ] **Step 4: Commit**

```bash
git add src/__init__.py src/schemas/__init__.py tests/__init__.py
git commit -m "chore: add __init__.py files for proper Python package imports"
```

---

## Summary

After completing all 6 tasks, Foundation provides:

| Artifact | Purpose |
|----------|---------|
| 8 JSON Schema files | Define contract interfaces for all skills |
| 7 fixture files | Valid sample data for testing |
| `src/deckcontext.py` | Init, read, write, validate, checksum, step tracking |
| Full test suite | Schema validation + unit tests + integration test |
| `.gitignore` update | Excludes `tmp/` from version control |
| `requirements.txt` | Python dependencies |

**All subsequent phases use this infrastructure:**
- Phase 2 (Design): `slide-stylist` reads TalkBrief, writes StyleGuide via `deckcontext.write_contract()`
- Phase 3 (Content): `narrative-architect` reads TalkBrief + StyleGuide, writes SlideOutline
- Phase 4 (Image): `imagegen-bridge` writes ImageManifest, reads StyleGuide + SlideOutline
- Phase 5 (Assembly): `deck-assembler` reads all contracts, `deck-qa` writes QAReport
- Phase 6 (Orchestration): `deck-conductor` manages PipelineState via `deckcontext.update_step()`
