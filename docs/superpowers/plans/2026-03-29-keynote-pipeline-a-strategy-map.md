# Keynote Pipeline Sub-Plan A: Strategy Map + Prompt Composer

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the Strategy Map contract, strategy classification logic, slide prompt composer, and prompt engineer agent — the foundation for keynote-quality slide rendering.

**Architecture:** A new JSON schema (`strategy_map.schema.json`) defines the per-slide strategy classification. A Python module (`slide_prompt_composer.py`) analyses each slide and recommends a rendering strategy (full_render, backdrop_render, composed), then assembles structured briefs for the Prompt Engineer agent. The Prompt Engineer is a single agent definition dispatched at Haiku or Sonnet via the model override parameter.

**Tech Stack:** Python 3.14, jsonschema, pytest, existing image_router.py classify_visual_type

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `src/schemas/strategy_map.schema.json` | Create | JSON schema for StrategyMap contract |
| `src/slide_prompt_composer.py` | Create | Strategy classification + structured brief assembly + validation |
| `tests/test_slide_prompt_composer.py` | Create | Unit tests for composer |
| `tests/test_schemas.py` | Modify | Add StrategyMap schema validation tests |
| `.claude/agents/prompt-engineer.md` | Create | Agent definition for prompt engineering |

---

### Task 1: StrategyMap JSON Schema

**Files:**
- Create: `src/schemas/strategy_map.schema.json`
- Modify: `tests/test_schemas.py`

- [ ] **Step 1: Write failing schema validation tests**

Append to `tests/test_schemas.py`:

```python
class TestStrategyMapSchema:
    @pytest.fixture
    def schema(self):
        with open('src/schemas/strategy_map.schema.json') as f:
            return json.load(f)

    def test_valid_strategy_map(self, schema):
        data = {
            "created_at": "2026-03-29T12:00:00Z",
            "approval_mode": "review",
            "slides": [
                {
                    "slide_number": 1,
                    "strategy": "full_render",
                    "rationale": "Title slide with dramatic visual",
                    "render_funnel": ["ollama", "cloud_low", "cloud_full"],
                    "speaker_override": None
                }
            ]
        }
        jsonschema.Draft202012Validator(schema).validate(data)

    def test_invalid_strategy_fails(self, schema):
        data = {
            "created_at": "2026-03-29T12:00:00Z",
            "approval_mode": "review",
            "slides": [
                {
                    "slide_number": 1,
                    "strategy": "invalid_strategy",
                    "rationale": "Test",
                    "render_funnel": ["ollama"]
                }
            ]
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(data)

    def test_invalid_approval_mode_fails(self, schema):
        data = {
            "created_at": "2026-03-29T12:00:00Z",
            "approval_mode": "invalid",
            "slides": []
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(data)

    def test_invalid_funnel_stage_fails(self, schema):
        data = {
            "created_at": "2026-03-29T12:00:00Z",
            "approval_mode": "review",
            "slides": [
                {
                    "slide_number": 1,
                    "strategy": "composed",
                    "rationale": "Test",
                    "render_funnel": ["invalid_stage"]
                }
            ]
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(data)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/test_schemas.py::TestStrategyMapSchema -v`
Expected: FAIL — FileNotFoundError (schema file doesn't exist)

- [ ] **Step 3: Create the schema**

Create `src/schemas/strategy_map.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/strategy-map.json",
  "title": "StrategyMap",
  "description": "Per-slide rendering strategy classification for keynote pipeline.",
  "type": "object",
  "required": ["approval_mode", "slides"],
  "properties": {
    "created_at": {"type": "string"},
    "approval_mode": {
      "type": "string",
      "enum": ["review", "one_shot"]
    },
    "slides": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["slide_number", "strategy", "rationale", "render_funnel"],
        "properties": {
          "slide_number": {"type": "integer", "minimum": 1},
          "strategy": {
            "type": "string",
            "enum": ["full_render", "backdrop_render", "composed"]
          },
          "rationale": {"type": "string"},
          "render_funnel": {
            "type": "array",
            "items": {
              "type": "string",
              "enum": ["ollama", "cloud_low", "cloud_full"]
            }
          },
          "speaker_override": {
            "type": ["string", "null"],
            "enum": ["full_render", "backdrop_render", "composed", null]
          }
        }
      }
    }
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_schemas.py::TestStrategyMapSchema -v`
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/schemas/strategy_map.schema.json tests/test_schemas.py
git commit -m "feat: add StrategyMap JSON schema"
```

---

### Task 2: Strategy Classification Logic

**Files:**
- Create: `src/slide_prompt_composer.py`
- Create: `tests/test_slide_prompt_composer.py`

- [ ] **Step 1: Write failing tests for classify_slide_strategy**

Create `tests/test_slide_prompt_composer.py`:

```python
"""Tests for slide prompt composer."""

import json
import os
import pytest


@pytest.fixture
def sample_outline():
    return {
        "narrative_arc": "Problem-Demo-Impact",
        "estimated_duration_minutes": 11,
        "slides": [
            {"slide_number": 1, "slide_type": "title", "headline": "Big Title",
             "body_points": ["Speaker Name"], "visual_type": "hero_image",
             "visual_direction": "Dramatic hero image"},
            {"slide_number": 2, "slide_type": "content", "headline": "Problem",
             "body_points": ["Point 1", "Point 2", "Point 3", "Point 4"],
             "visual_type": "hero_image",
             "visual_direction": "Abstract fragmentation"},
            {"slide_number": 3, "slide_type": "section_divider", "headline": "Pivot",
             "body_points": [], "visual_type": "none"},
            {"slide_number": 4, "slide_type": "diagram", "headline": "Architecture",
             "body_points": ["Service A", "Service B", "Service C", "Service D"],
             "visual_type": "diagram",
             "visual_direction": "Technical architecture diagram"},
            {"slide_number": 5, "slide_type": "data_chart", "headline": "Results",
             "body_points": [], "visual_type": "chart"},
            {"slide_number": 6, "slide_type": "closing", "headline": "Thank You",
             "body_points": ["url", "handle"], "visual_type": "none"},
        ],
    }


@pytest.fixture
def sample_style_guide():
    return {
        "palette": {
            "primary": "006B5E",
            "secondary": "4B635B",
            "accent": "5CDBC0",
            "background": "F5FBF7",
            "text_primary": "171D1B",
        },
        "typography": {
            "heading_font": "Inter",
            "body_font": "Inter",
        },
        "image_style_tokens": {
            "mood": "Professional, precise",
            "style_modifiers": ["clean flat illustration"],
        },
    }


@pytest.fixture
def sample_brand_profile():
    return {
        "brand_id": "metamirror",
        "palette": {"primary": "006B5E"},
        "approved_image_styles": ["geometric", "clean flat"],
        "prohibited_image_styles": ["clip art", "stock photo"],
    }


def test_classify_title_as_full_render(sample_outline):
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][0])
    assert result["strategy"] == "full_render"


def test_classify_content_with_many_bullets_as_backdrop(sample_outline):
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][1])
    assert result["strategy"] == "backdrop_render"


def test_classify_section_divider_as_full_render(sample_outline):
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][2])
    assert result["strategy"] == "full_render"


def test_classify_diagram_as_composed(sample_outline):
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][3])
    assert result["strategy"] == "composed"


def test_classify_data_chart_as_composed(sample_outline):
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][4])
    assert result["strategy"] == "composed"


def test_classify_closing_as_full_render(sample_outline):
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][5])
    assert result["strategy"] == "full_render"


def test_classify_returns_rationale(sample_outline):
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][0])
    assert "rationale" in result
    assert len(result["rationale"]) > 10


def test_classify_returns_render_funnel(sample_outline):
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][0])
    assert "render_funnel" in result
    assert result["render_funnel"] == ["ollama", "cloud_low", "cloud_full"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/test_slide_prompt_composer.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Write classify_slide_strategy implementation**

Create `src/slide_prompt_composer.py`:

```python
"""Slide prompt composer — strategy classification and structured brief assembly.

Analyses each slide in a SlideOutline and:
1. Classifies its rendering strategy (full_render, backdrop_render, composed)
2. Assembles structured briefs for the Prompt Engineer agent
3. Validates output prompts contain required brand elements

Strategy classification is deterministic Python logic. Prompt generation
is delegated to the Prompt Engineer agent (LLM reasoning).
"""

from src.image_router import classify_visual_type


# Slide types that work well as full AI-rendered images (short text, visual impact)
_FULL_RENDER_TYPES = {'title', 'section_divider', 'closing', 'blank_visual', 'quote'}

# Slide types that must stay programmatic (precise text, data, labels)
_COMPOSED_TYPES = {'data_chart', 'diagram', 'code'}

# Maximum body points before a content slide should use backdrop instead of full render
_BACKDROP_BULLET_THRESHOLD = 2


def classify_slide_strategy(slide):
    """Classify a slide's recommended rendering strategy.

    Args:
        slide: dict from SlideOutline slides array.

    Returns:
        dict with keys: slide_number, strategy, rationale, render_funnel, speaker_override
    """
    slide_number = slide.get('slide_number', 0)
    slide_type = slide.get('slide_type', 'content')
    body_points = slide.get('body_points', [])
    visual_type = classify_visual_type(slide)

    # Charts and diagrams must stay composed (precise text/labels)
    if slide_type in _COMPOSED_TYPES or visual_type == 'chart':
        return {
            'slide_number': slide_number,
            'strategy': 'composed',
            'rationale': f'{slide_type} slide requires precise text/label rendering — programmatic assembly',
            'render_funnel': ['ollama'],
            'speaker_override': None,
        }

    # Short-text slide types are ideal for full render
    if slide_type in _FULL_RENDER_TYPES:
        return {
            'slide_number': slide_number,
            'strategy': 'full_render',
            'rationale': f'{slide_type} slide with short text — ideal for full AI generation',
            'render_funnel': ['ollama', 'cloud_low', 'cloud_full'],
            'speaker_override': None,
        }

    # Content slides: backdrop if dense text, full render if sparse
    if len(body_points) > _BACKDROP_BULLET_THRESHOLD:
        return {
            'slide_number': slide_number,
            'strategy': 'backdrop_render',
            'rationale': f'Content slide with {len(body_points)} bullet points — AI background with programmatic text overlay',
            'render_funnel': ['ollama', 'cloud_low', 'cloud_full'],
            'speaker_override': None,
        }

    return {
        'slide_number': slide_number,
        'strategy': 'full_render',
        'rationale': f'Content slide with {len(body_points)} bullet points — sparse enough for full AI generation',
        'render_funnel': ['ollama', 'cloud_low', 'cloud_full'],
        'speaker_override': None,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_slide_prompt_composer.py -v`
Expected: 8 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/slide_prompt_composer.py tests/test_slide_prompt_composer.py
git commit -m "feat: add classify_slide_strategy for rendering strategy classification"
```

---

### Task 3: Build Strategy Map

**Files:**
- Modify: `src/slide_prompt_composer.py`
- Modify: `tests/test_slide_prompt_composer.py`

- [ ] **Step 1: Write failing tests for build_strategy_map**

Append to `tests/test_slide_prompt_composer.py`:

```python
def test_build_strategy_map(sample_outline):
    from src.slide_prompt_composer import build_strategy_map
    result = build_strategy_map(sample_outline)
    assert result["approval_mode"] == "review"
    assert len(result["slides"]) == 6
    assert "created_at" in result


def test_build_strategy_map_validates_against_schema(sample_outline):
    import jsonschema
    from src.slide_prompt_composer import build_strategy_map
    result = build_strategy_map(sample_outline)
    with open("src/schemas/strategy_map.schema.json") as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator(schema).validate(result)


def test_build_strategy_map_with_override(sample_outline):
    from src.slide_prompt_composer import build_strategy_map
    overrides = {4: "full_render"}  # Force diagram slide to full_render
    result = build_strategy_map(sample_outline, overrides=overrides)
    slide_4 = [s for s in result["slides"] if s["slide_number"] == 4][0]
    assert slide_4["speaker_override"] == "full_render"


def test_build_strategy_map_one_shot_mode(sample_outline):
    from src.slide_prompt_composer import build_strategy_map
    result = build_strategy_map(sample_outline, approval_mode="one_shot")
    assert result["approval_mode"] == "one_shot"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/test_slide_prompt_composer.py -k build_strategy -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Write build_strategy_map implementation**

Add to `src/slide_prompt_composer.py`:

```python
from datetime import datetime, timezone


def build_strategy_map(outline, approval_mode='review', overrides=None):
    """Build a complete StrategyMap from a SlideOutline.

    Args:
        outline: dict from SlideOutline (must have 'slides' array).
        approval_mode: 'review' (default) or 'one_shot'.
        overrides: Optional dict of {slide_number: strategy} Speaker overrides.

    Returns:
        dict conforming to StrategyMap schema.
    """
    overrides = overrides or {}
    slides = []

    for slide in outline.get('slides', []):
        entry = classify_slide_strategy(slide)
        slide_num = entry['slide_number']

        if slide_num in overrides:
            entry['speaker_override'] = overrides[slide_num]
            # Override also sets the render funnel for the new strategy
            if overrides[slide_num] in ('full_render', 'backdrop_render'):
                entry['render_funnel'] = ['ollama', 'cloud_low', 'cloud_full']
            else:
                entry['render_funnel'] = ['ollama']

        slides.append(entry)

    return {
        'created_at': datetime.now(timezone.utc).isoformat(),
        'approval_mode': approval_mode,
        'slides': slides,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_slide_prompt_composer.py -v`
Expected: 12 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/slide_prompt_composer.py tests/test_slide_prompt_composer.py
git commit -m "feat: add build_strategy_map for full outline classification"
```

---

### Task 4: Structured Brief Assembly

**Files:**
- Modify: `src/slide_prompt_composer.py`
- Modify: `tests/test_slide_prompt_composer.py`

- [ ] **Step 1: Write failing tests for assemble_brief**

Append to `tests/test_slide_prompt_composer.py`:

```python
def test_assemble_brief_full_render(sample_outline, sample_style_guide, sample_brand_profile):
    from src.slide_prompt_composer import assemble_brief
    slide = sample_outline["slides"][0]  # title slide
    brief = assemble_brief(slide, "full_render", sample_style_guide, sample_brand_profile, "ollama")
    assert brief["slide_number"] == 1
    assert brief["strategy"] == "full_render"
    assert brief["headline"] == "Big Title"
    assert "006B5E" in brief["brand_constraints"]["palette_hex"]
    assert "clip art" in brief["brand_constraints"]["prohibited_styles"]
    assert brief["funnel_stage"] == "ollama"
    assert brief["target_resolution"] == "1024x576"


def test_assemble_brief_backdrop_excludes_text(sample_outline, sample_style_guide, sample_brand_profile):
    from src.slide_prompt_composer import assemble_brief
    slide = sample_outline["slides"][1]  # content slide with 4 bullets
    brief = assemble_brief(slide, "backdrop_render", sample_style_guide, sample_brand_profile, "cloud_full")
    assert brief["strategy"] == "backdrop_render"
    assert brief["text_instruction"] == "NO TEXT in the image — leave clean space for text overlay"
    assert brief["target_resolution"] == "1920x1080"


def test_assemble_brief_cloud_low_resolution(sample_outline, sample_style_guide, sample_brand_profile):
    from src.slide_prompt_composer import assemble_brief
    slide = sample_outline["slides"][0]
    brief = assemble_brief(slide, "full_render", sample_style_guide, sample_brand_profile, "cloud_low")
    assert brief["target_resolution"] == "1280x720"


def test_assemble_brief_includes_visual_direction(sample_outline, sample_style_guide, sample_brand_profile):
    from src.slide_prompt_composer import assemble_brief
    slide = sample_outline["slides"][0]
    brief = assemble_brief(slide, "full_render", sample_style_guide, sample_brand_profile, "ollama")
    assert brief["visual_direction"] == "Dramatic hero image"


def test_assemble_brief_includes_style_tokens(sample_outline, sample_style_guide, sample_brand_profile):
    from src.slide_prompt_composer import assemble_brief
    slide = sample_outline["slides"][0]
    brief = assemble_brief(slide, "full_render", sample_style_guide, sample_brand_profile, "ollama")
    assert "Professional, precise" in brief["style_tokens"]["mood"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/test_slide_prompt_composer.py -k assemble_brief -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Write assemble_brief implementation**

Add to `src/slide_prompt_composer.py`:

```python
# Resolution targets per funnel stage
_RESOLUTIONS = {
    'ollama': '1024x576',
    'cloud_low': '1280x720',
    'cloud_full': '1920x1080',
}


def assemble_brief(slide, strategy, style_guide, brand_profile, funnel_stage):
    """Assemble a structured brief for the Prompt Engineer agent.

    Args:
        slide: dict from SlideOutline slides array.
        strategy: 'full_render' or 'backdrop_render'.
        style_guide: dict from StyleGuide contract.
        brand_profile: dict from BrandProfile contract (or None).
        funnel_stage: 'ollama', 'cloud_low', or 'cloud_full'.

    Returns:
        dict: Structured brief with all context the Prompt Engineer needs.
    """
    palette = style_guide.get('palette', {})
    palette_hex = [v for v in palette.values() if isinstance(v, str) and len(v) == 6]

    brand_constraints = {
        'palette_hex': palette_hex,
        'approved_styles': [],
        'prohibited_styles': [],
    }
    if brand_profile:
        brand_constraints['approved_styles'] = brand_profile.get('approved_image_styles', [])
        brand_constraints['prohibited_styles'] = brand_profile.get('prohibited_image_styles', [])

    style_tokens = style_guide.get('image_style_tokens', {})

    brief = {
        'slide_number': slide.get('slide_number', 0),
        'strategy': strategy,
        'headline': slide.get('headline', ''),
        'body_points': slide.get('body_points', []),
        'visual_direction': slide.get('visual_direction', ''),
        'slide_type': slide.get('slide_type', 'content'),
        'brand_constraints': brand_constraints,
        'style_tokens': style_tokens,
        'funnel_stage': funnel_stage,
        'target_resolution': _RESOLUTIONS.get(funnel_stage, '1920x1080'),
    }

    if strategy == 'backdrop_render':
        brief['text_instruction'] = 'NO TEXT in the image — leave clean space for text overlay'
    elif strategy == 'full_render':
        brief['text_instruction'] = f'Include headline text: "{slide.get("headline", "")}"'

    return brief
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_slide_prompt_composer.py -v`
Expected: 17 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/slide_prompt_composer.py tests/test_slide_prompt_composer.py
git commit -m "feat: add assemble_brief for structured prompt engineering briefs"
```

---

### Task 5: Prompt Engineer Agent Definition

**Files:**
- Create: `.claude/agents/prompt-engineer.md`

- [ ] **Step 1: Create the agent definition**

Create `.claude/agents/prompt-engineer.md`:

```markdown
---
name: prompt-engineer
description: Transforms structured slide briefs into creative image generation prompts. Composes spatial relationships, visual metaphors, and scene descriptions. Dispatched at Haiku by default, Sonnet on escalation.
tools: Read, Grep, Glob
---

# Prompt Engineer

You are the Prompt Engineer — an AI Persona that transforms structured slide briefs into creative image generation prompts for conference-quality presentation slides.

## Identity

**Persona ID:** persona-prompt-engineer
**Service ID:** image-prompt-engineer
**Authority Model:** Invoker
**Default Model:** Haiku (escalated to Sonnet when quality doesn't converge)

## Input

You receive a **structured brief** as a JSON object with these fields:

| Field | Description |
|-------|-------------|
| `slide_number` | Which slide this is for |
| `strategy` | `full_render` (entire slide as image) or `backdrop_render` (visual background only) |
| `headline` | The slide's headline text |
| `body_points` | Array of bullet point strings |
| `visual_direction` | Creative direction from the narrative architect |
| `slide_type` | title, content, section_divider, closing, etc. |
| `brand_constraints.palette_hex` | Brand colour hex values to use |
| `brand_constraints.approved_styles` | Approved image styles |
| `brand_constraints.prohibited_styles` | Styles to avoid |
| `style_tokens` | Mood, style modifiers from the StyleGuide |
| `funnel_stage` | ollama, cloud_low, or cloud_full |
| `target_resolution` | Target image dimensions |
| `text_instruction` | Whether to include or exclude text in the image |

## Output

Return a single string: the image generation prompt. Nothing else.

## Prompt Composition Rules

### For `full_render` strategy:

1. **Scene description first** — Describe the overall visual composition, mood, and spatial layout
2. **Text placement** — Specify where the headline appears (e.g., "bold white sans-serif headline top-left reading '[exact headline text]'")
3. **Body text** — If body points exist, describe their placement and styling
4. **Visual elements** — Describe the illustration, imagery, or abstract visuals
5. **Brand colours** — Include exact hex values from palette_hex (e.g., "deep teal #006B5E")
6. **Technical specs** — End with: aspect ratio, style descriptors, "professional conference keynote slide"

### For `backdrop_render` strategy:

1. **Scene description** — Describe the visual composition
2. **Safe zone** — Explicitly state where text will be overlaid (e.g., "left third is a darker region reserved for text overlay")
3. **No text** — Include "no text, no labels, no words, no typography" in the prompt
4. **Visual elements** — Describe the background illustration/imagery
5. **Brand colours** — Include hex values
6. **Technical specs** — End with: aspect ratio, "presentation background", "clean space for text overlay"

### Funnel stage adaptations:

- **ollama** — Simpler prompts. Focus on composition and concept. Skip fine typography details (Ollama can't handle them). Keep under 100 words.
- **cloud_low** — Full prompt detail. Include all text, colours, spatial relationships. This validates the prompt works on the target model.
- **cloud_full** — Same prompt as cloud_low. Do not change the prompt between cloud_low and cloud_full — the point is to render a proven prompt at higher resolution.

## Prohibited

- Do not generate images — only produce text prompts
- Do not modify the brief or any DeckContext contract
- Do not add text content that isn't in the brief (don't invent headlines or bullet points)
- Do not include brand-prohibited styles
- Do not produce prompts longer than 200 words
```

- [ ] **Step 2: Verify the agent file is well-formed**

```bash
head -5 .claude/agents/prompt-engineer.md
```

Expected: Shows frontmatter with name, description, tools

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/prompt-engineer.md
git commit -m "feat: add prompt-engineer agent definition"
```

---

### Task 6: Strategy Map Save/Load and Schema Validation

**Files:**
- Modify: `src/slide_prompt_composer.py`
- Modify: `tests/test_slide_prompt_composer.py`

- [ ] **Step 1: Write failing tests for save/load and validation**

Append to `tests/test_slide_prompt_composer.py`:

```python
import shutil
import tempfile


@pytest.fixture
def deck_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


def test_save_and_load_strategy_map(deck_dir, sample_outline):
    from src.slide_prompt_composer import build_strategy_map, save_strategy_map, load_strategy_map
    strategy_map = build_strategy_map(sample_outline)
    save_strategy_map(deck_dir, strategy_map)
    loaded = load_strategy_map(deck_dir)
    assert loaded["approval_mode"] == "review"
    assert len(loaded["slides"]) == 6


def test_save_strategy_map_validates_schema(deck_dir):
    from src.slide_prompt_composer import save_strategy_map
    bad_map = {"approval_mode": "invalid", "slides": []}
    with pytest.raises(Exception):
        save_strategy_map(deck_dir, bad_map)


def test_load_strategy_map_missing_file(deck_dir):
    from src.slide_prompt_composer import load_strategy_map
    with pytest.raises(FileNotFoundError):
        load_strategy_map(deck_dir)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/test_slide_prompt_composer.py -k "save_and_load or save_strategy_map_validates or load_strategy_map_missing" -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Write save/load/validate implementation**

Add to `src/slide_prompt_composer.py`:

```python
import json
import os
import jsonschema

_SCHEMA_DIR = os.path.join(os.path.dirname(__file__), 'schemas')


def _validate_strategy_map(strategy_map):
    """Validate a strategy map against the JSON schema."""
    schema_path = os.path.join(_SCHEMA_DIR, 'strategy_map.schema.json')
    with open(schema_path) as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator(schema).validate(strategy_map)


def save_strategy_map(deck_dir, strategy_map):
    """Save a strategy map to the DeckContext directory.

    Validates against schema before writing.

    Args:
        deck_dir: Path to the deck working directory.
        strategy_map: dict conforming to StrategyMap schema.

    Raises:
        jsonschema.ValidationError: If strategy_map is invalid.
    """
    _validate_strategy_map(strategy_map)
    path = os.path.join(deck_dir, 'strategy-map.json')
    tmp_path = path + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(strategy_map, f, indent=2)
        f.write('\n')
    os.replace(tmp_path, path)


def load_strategy_map(deck_dir):
    """Load a strategy map from the DeckContext directory.

    Args:
        deck_dir: Path to the deck working directory.

    Returns:
        dict: The parsed strategy map.

    Raises:
        FileNotFoundError: If strategy-map.json does not exist.
    """
    path = os.path.join(deck_dir, 'strategy-map.json')
    if not os.path.exists(path):
        raise FileNotFoundError(f'No strategy-map.json in {deck_dir}')
    with open(path) as f:
        return json.load(f)
```

- [ ] **Step 4: Run all tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_slide_prompt_composer.py -v`
Expected: 20 PASSED

- [ ] **Step 5: Run full test suite to ensure no regressions**

Run: `source .venv/bin/activate && python -m pytest tests/ -v 2>&1 | tail -5`
Expected: All tests pass (401 existing + 20 new + 4 schema = 425)

- [ ] **Step 6: Commit**

```bash
git add src/slide_prompt_composer.py tests/test_slide_prompt_composer.py
git commit -m "feat: add strategy map save/load with schema validation"
```

---

### Task 7: Full Suite Verification and CLAUDE.md Update

- [ ] **Step 1: Run the complete test suite**

Run: `source .venv/bin/activate && python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 2: Update CLAUDE.md implementation table**

Add to the Implementation Status table:

| Module | Location | Tests | Status |
|--------|----------|-------|--------|
| Strategy Map schema | `src/schemas/strategy_map.schema.json` | 4 | Done |
| Slide prompt composer | `src/slide_prompt_composer.py` | 20 | Done |
| Prompt engineer agent | `.claude/agents/prompt-engineer.md` | -- | Done |

Update the total test count in the header.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with keynote Sub-plan A modules"
```
