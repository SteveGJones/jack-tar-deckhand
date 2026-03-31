# Rendering Strategy Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the rendering pipeline from 3 strategies (full_render, backdrop_render, composed) to 5 (+ background, backdrop, pragmatic_composition) with template zones, vision-analysed positioning, and multi-image element assembly.

**Architecture:** Four phases build on a shared foundation. Phase 1 updates schemas, strategy classification, and assembler routing stubs. Phases 2-4 implement each new rendering path independently. All image generation uses Ollama only (draft mode). Unit tests mock image/vision data; tagged integration tests hit Ollama.

**Tech Stack:** Python (strategy classification, QA checks), JavaScript/PptxGenJS (assembler), JSON Schema (contracts), Claude Code agents (vision analysis), Ollama (image generation)

**Spec:** `docs/superpowers/specs/2026-03-30-rendering-strategy-expansion.md`
**Spike:** `docs/spikes/backdrop-content-aware-positioning.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `src/schemas/strategy_map.schema.json` | Modify | Expand strategy enum, add backdrop_variant, element_layout |
| `src/schemas/image_manifest.schema.json` | Modify | Add detected_positions, element_id, placement_zone enums |
| `src/slide_prompt_composer.py` | Modify | 5-strategy classification, template selection, element brief splitting |
| `src/assembler/build_deck.js` | Modify | 5-path routing, buildBackgroundSlide, buildBackdropSlide, buildPragmaticSlide |
| `src/qa/run_qa.py` | Modify | Route new strategies, invoke AP-27/AP-28 |
| `src/qa/checks/element_layout.py` | Create | AP-27 element layout validation, AP-28 vision confidence |
| `.claude/agents/vision-analyst.md` | Create | Vision analysis agent for backDROP |
| `tests/test_slide_prompt_composer.py` | Modify | New classification, template, and brief tests |
| `tests/test_assembler.py` | Modify | New assembly path tests |
| `tests/test_qa_element_layout.py` | Create | AP-27 and AP-28 tests |
| `tests/fixtures/minimal_deck/strategy-map.json` | Create | Test fixture with new strategies |
| `tests/test_integration_rendering.py` | Create | Tagged Ollama integration tests |

---

## Phase 1: Foundation

### Task 1: Expand StrategyMap Schema

**Files:**
- Modify: `src/schemas/strategy_map.schema.json`
- Test: `tests/test_slide_prompt_composer.py`

- [ ] **Step 1: Write failing test for new strategy enum values**

Add to `tests/test_slide_prompt_composer.py`:

```python
def test_strategy_map_accepts_background_strategy(sample_outline):
    """StrategyMap schema should accept 'background' as a valid strategy."""
    from src.slide_prompt_composer import build_strategy_map
    import jsonschema
    result = build_strategy_map(sample_outline)
    # Manually set one slide to 'background' strategy
    result['slides'][1]['strategy'] = 'background'
    result['slides'][1]['backdrop_variant'] = 'bottom_bar'
    with open('src/schemas/strategy_map.schema.json') as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator(schema).validate(result)


def test_strategy_map_accepts_backdrop_strategy(sample_outline):
    """StrategyMap schema should accept 'backdrop' with element_layout."""
    from src.slide_prompt_composer import build_strategy_map
    import jsonschema
    result = build_strategy_map(sample_outline)
    result['slides'][1]['strategy'] = 'backdrop'
    result['slides'][1]['element_layout'] = {
        'template': 'three_across',
        'elements': [
            {'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.08, 'y': 0.25, 'w': 0.25, 'h': 0.50},
            {'id': 'elem_2', 'label_source': 'body_points[1]', 'x': 0.38, 'y': 0.25, 'w': 0.25, 'h': 0.50},
            {'id': 'elem_3', 'label_source': 'body_points[2]', 'x': 0.67, 'y': 0.25, 'w': 0.25, 'h': 0.50},
        ],
        'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
    }
    with open('src/schemas/strategy_map.schema.json') as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator(schema).validate(result)


def test_strategy_map_accepts_pragmatic_composition(sample_outline):
    """StrategyMap schema should accept 'pragmatic_composition'."""
    from src.slide_prompt_composer import build_strategy_map
    import jsonschema
    result = build_strategy_map(sample_outline)
    result['slides'][1]['strategy'] = 'pragmatic_composition'
    result['slides'][1]['element_layout'] = {
        'template': 'two_column',
        'elements': [
            {'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.05, 'y': 0.20, 'w': 0.40, 'h': 0.60},
            {'id': 'elem_2', 'label_source': 'body_points[1]', 'x': 0.55, 'y': 0.20, 'w': 0.40, 'h': 0.60},
        ],
        'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
    }
    with open('src/schemas/strategy_map.schema.json') as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator(schema).validate(result)


def test_strategy_map_accepts_backdrop_variant(sample_outline):
    """StrategyMap schema should accept backdrop_variant field."""
    from src.slide_prompt_composer import build_strategy_map
    import jsonschema
    result = build_strategy_map(sample_outline)
    result['slides'][1]['strategy'] = 'background'
    for variant in ['left_panel', 'right_panel', 'bottom_bar', 'top_band', 'center_float']:
        result['slides'][1]['backdrop_variant'] = variant
        with open('src/schemas/strategy_map.schema.json') as f:
            schema = json.load(f)
        jsonschema.Draft202012Validator(schema).validate(result)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/test_slide_prompt_composer.py::test_strategy_map_accepts_background_strategy -v`
Expected: FAIL — schema rejects 'background' as a strategy value

- [ ] **Step 3: Update the schema**

In `src/schemas/strategy_map.schema.json`, replace the strategy enum and add new fields:

```json
{
  "strategy": {
    "type": "string",
    "enum": ["full_render", "backdrop_render", "composed", "background", "backdrop", "pragmatic_composition"]
  }
}
```

Add after `speaker_override`:

```json
"backdrop_variant": {
  "type": "string",
  "enum": ["left_panel", "right_panel", "bottom_bar", "top_band", "center_float"]
},
"element_layout": {
  "type": "object",
  "properties": {
    "template": {"type": "string"},
    "elements": {
      "type": "array",
      "maxItems": 5,
      "items": {
        "type": "object",
        "required": ["id", "label_source", "x", "y", "w", "h"],
        "properties": {
          "id": {"type": "string"},
          "label_source": {"type": "string"},
          "x": {"type": "number", "minimum": 0, "maximum": 1},
          "y": {"type": "number", "minimum": 0, "maximum": 1},
          "w": {"type": "number", "minimum": 0, "maximum": 1},
          "h": {"type": "number", "minimum": 0, "maximum": 1}
        }
      }
    },
    "title_region": {
      "type": "object",
      "properties": {
        "x": {"type": "number"},
        "y": {"type": "number"},
        "w": {"type": "number"},
        "h": {"type": "number"}
      }
    }
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && pytest tests/test_slide_prompt_composer.py -k "strategy_map_accepts" -v`
Expected: 4 PASS

- [ ] **Step 5: Run full test suite to check nothing broke**

Run: `source .venv/bin/activate && pytest -x -q`
Expected: All 446 tests pass

- [ ] **Step 6: Commit**

```bash
git add src/schemas/strategy_map.schema.json tests/test_slide_prompt_composer.py
git commit -m "feat: expand StrategyMap schema with background, backdrop, pragmatic_composition strategies"
```

---

### Task 2: Expand ImageManifest Schema

**Files:**
- Modify: `src/schemas/image_manifest.schema.json`
- Test: `tests/test_schemas.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_schemas.py`:

```python
def test_image_manifest_accepts_detected_positions():
    """ImageManifest should accept detected_positions array on image entries."""
    import jsonschema
    with open('src/schemas/image_manifest.schema.json') as f:
        schema = json.load(f)
    manifest = {
        'images': [{
            'image_id': 'slide-05-hero',
            'slide_number': 5,
            'file_path': './tmp/deck/images/slide-05-hero.png',
            'status': 'generated',
            'detected_positions': [
                {'element_id': 'elem_1', 'x': 0.10, 'y': 0.28, 'w': 0.22, 'h': 0.45, 'confidence': 0.92},
                {'element_id': 'elem_2', 'x': 0.39, 'y': 0.26, 'w': 0.24, 'h': 0.48, 'confidence': 0.88},
            ],
        }],
    }
    jsonschema.Draft202012Validator(schema).validate(manifest)


def test_image_manifest_accepts_element_placement():
    """ImageManifest should accept element_id and placement_zone for pragmatic composition."""
    import jsonschema
    with open('src/schemas/image_manifest.schema.json') as f:
        schema = json.load(f)
    manifest = {
        'images': [
            {'image_id': 'slide-11-bg', 'slide_number': 11, 'file_path': './bg.png',
             'status': 'generated', 'placement_zone': 'background'},
            {'image_id': 'slide-11-elem-1', 'slide_number': 11, 'file_path': './e1.png',
             'status': 'generated', 'placement_zone': 'element', 'element_id': 'elem_1'},
        ],
    }
    jsonschema.Draft202012Validator(schema).validate(manifest)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/test_schemas.py::test_image_manifest_accepts_detected_positions -v`
Expected: FAIL — `detected_positions` not in schema

- [ ] **Step 3: Update the schema**

In `src/schemas/image_manifest.schema.json`, add to the image item properties:

```json
"element_id": {"type": "string"},
"detected_positions": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["element_id", "x", "y", "w", "h", "confidence"],
    "properties": {
      "element_id": {"type": "string"},
      "x": {"type": "number"},
      "y": {"type": "number"},
      "w": {"type": "number"},
      "h": {"type": "number"},
      "confidence": {"type": "number", "minimum": 0, "maximum": 1}
    }
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && pytest tests/test_schemas.py -k "image_manifest_accepts" -v`
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add src/schemas/image_manifest.schema.json tests/test_schemas.py
git commit -m "feat: expand ImageManifest schema with detected_positions and element_id"
```

---

### Task 3: Expand Strategy Classification

**Files:**
- Modify: `src/slide_prompt_composer.py`
- Test: `tests/test_slide_prompt_composer.py`

- [ ] **Step 1: Write failing tests for new classification logic**

Add to `tests/test_slide_prompt_composer.py`:

```python
def test_classify_content_with_many_bullets_as_background():
    """Content slide with >2 bullets should classify as 'background' (not backdrop_render)."""
    from src.slide_prompt_composer import classify_slide_strategy
    slide = {'slide_number': 2, 'slide_type': 'content',
             'body_points': ['A', 'B', 'C', 'D'], 'visual_type': 'hero_image'}
    result = classify_slide_strategy(slide)
    assert result['strategy'] == 'background'


def test_classify_backdrop_render_still_accepted():
    """Backward compat: existing code producing backdrop_render should still work."""
    # This tests that the overrides dict accepts backdrop_render
    from src.slide_prompt_composer import build_strategy_map
    outline = {'slides': [
        {'slide_number': 1, 'slide_type': 'content',
         'body_points': ['A', 'B', 'C'], 'visual_type': 'hero_image'},
    ]}
    overrides = {1: 'backdrop_render'}
    result = build_strategy_map(outline, overrides=overrides)
    assert result['slides'][0]['speaker_override'] == 'backdrop_render'
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/test_slide_prompt_composer.py::test_classify_content_with_many_bullets_as_background -v`
Expected: FAIL — returns 'backdrop_render' not 'background'

- [ ] **Step 3: Update classify_slide_strategy**

In `src/slide_prompt_composer.py`, change the dense-content branch (lines 67-74):

```python
    # Content slides: background if dense text, full render if sparse
    if len(body_points) > _BACKDROP_BULLET_THRESHOLD:
        return {
            'slide_number': slide_number,
            'strategy': 'background',
            'rationale': f'Content slide with {len(body_points)} bullet points — AI background with programmatic text overlay',
            'render_funnel': ['ollama', 'cloud_low', 'cloud_full'],
            'speaker_override': None,
        }
```

Also update the overrides funnel logic in `build_strategy_map` (lines 109-112) to handle new strategies:

```python
        if slide_num in overrides:
            entry['speaker_override'] = overrides[slide_num]
            if overrides[slide_num] in ('full_render', 'backdrop_render', 'background', 'backdrop'):
                entry['render_funnel'] = ['ollama', 'cloud_low', 'cloud_full']
            else:
                entry['render_funnel'] = ['ollama']
```

- [ ] **Step 4: Update the existing test that expects backdrop_render**

In `tests/test_slide_prompt_composer.py`, update `test_classify_content_with_many_bullets_as_backdrop`:

```python
def test_classify_content_with_many_bullets_as_backdrop(sample_outline):
    """Content with many bullets should now classify as 'background'."""
    from src.slide_prompt_composer import classify_slide_strategy
    result = classify_slide_strategy(sample_outline["slides"][1])
    assert result["strategy"] == "background"
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `source .venv/bin/activate && pytest tests/test_slide_prompt_composer.py -v`
Expected: All pass (existing + new)

- [ ] **Step 6: Run full suite**

Run: `source .venv/bin/activate && pytest -x -q`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add src/slide_prompt_composer.py tests/test_slide_prompt_composer.py
git commit -m "feat: classify dense content slides as 'background' strategy"
```

---

### Task 4: Add Element Layout Template Library

**Files:**
- Modify: `src/slide_prompt_composer.py`
- Test: `tests/test_slide_prompt_composer.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_slide_prompt_composer.py`:

```python
def test_element_layout_three_across():
    """three_across template should produce 3 evenly-spaced columns."""
    from src.slide_prompt_composer import get_element_layout
    layout = get_element_layout('three_across', 3)
    assert layout['template'] == 'three_across'
    assert len(layout['elements']) == 3
    assert all(0 <= e['x'] <= 1 and 0 <= e['y'] <= 1 for e in layout['elements'])
    assert 'title_region' in layout
    # Elements should be horizontally spaced
    xs = [e['x'] for e in layout['elements']]
    assert xs[0] < xs[1] < xs[2]


def test_element_layout_two_column():
    """two_column template should produce 2 wide columns."""
    from src.slide_prompt_composer import get_element_layout
    layout = get_element_layout('two_column', 2)
    assert len(layout['elements']) == 2


def test_element_layout_grid_2x2():
    """grid_2x2 template should produce 4 elements in a 2x2 grid."""
    from src.slide_prompt_composer import get_element_layout
    layout = get_element_layout('grid_2x2', 4)
    assert len(layout['elements']) == 4


def test_element_layout_process_flow():
    """process_flow template should produce a horizontal row."""
    from src.slide_prompt_composer import get_element_layout
    layout = get_element_layout('process_flow', 4)
    assert len(layout['elements']) == 4
    xs = [e['x'] for e in layout['elements']]
    assert xs == sorted(xs)


def test_element_layout_hub_and_spoke():
    """hub_and_spoke template should have 1 centre + surrounding elements."""
    from src.slide_prompt_composer import get_element_layout
    layout = get_element_layout('hub_and_spoke', 4)
    assert len(layout['elements']) == 4


def test_element_layout_caps_at_5():
    """Element count must be capped at 5."""
    from src.slide_prompt_composer import get_element_layout
    layout = get_element_layout('process_flow', 5)
    assert len(layout['elements']) == 5
    with pytest.raises(ValueError):
        get_element_layout('process_flow', 6)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && pytest tests/test_slide_prompt_composer.py -k "element_layout" -v`
Expected: FAIL — `get_element_layout` not defined

- [ ] **Step 3: Implement get_element_layout**

Add to `src/slide_prompt_composer.py`:

```python
_ELEMENT_LAYOUTS = {
    'three_across': {
        'regions': lambda n: [
            {'x': 0.05 + i * 0.32, 'y': 0.22, 'w': 0.27, 'h': 0.50}
            for i in range(n)
        ],
        'title_region': {'x': 0.05, 'y': 0.03, 'w': 0.90, 'h': 0.12},
    },
    'two_column': {
        'regions': lambda n: [
            {'x': 0.05 + i * 0.50, 'y': 0.22, 'w': 0.42, 'h': 0.55}
            for i in range(n)
        ],
        'title_region': {'x': 0.05, 'y': 0.03, 'w': 0.90, 'h': 0.12},
    },
    'grid_2x2': {
        'regions': lambda n: [
            {'x': 0.05 + (i % 2) * 0.50, 'y': 0.18 + (i // 2) * 0.40, 'w': 0.42, 'h': 0.35}
            for i in range(n)
        ],
        'title_region': {'x': 0.05, 'y': 0.03, 'w': 0.90, 'h': 0.10},
    },
    'process_flow': {
        'regions': lambda n: [
            {'x': 0.03 + i * (0.94 / n), 'y': 0.25, 'w': 0.94 / n - 0.03, 'h': 0.45}
            for i in range(n)
        ],
        'title_region': {'x': 0.05, 'y': 0.03, 'w': 0.90, 'h': 0.12},
    },
    'hub_and_spoke': {
        'regions': lambda n: [
            {'x': 0.37, 'y': 0.28, 'w': 0.26, 'h': 0.40},  # centre hub
        ] + [
            {'x': [0.05, 0.70, 0.05, 0.70][i], 'y': [0.15, 0.15, 0.55, 0.55][i], 'w': 0.22, 'h': 0.28}
            for i in range(n - 1)
        ],
        'title_region': {'x': 0.05, 'y': 0.03, 'w': 0.90, 'h': 0.10},
    },
}


def get_element_layout(template_name, element_count):
    """Return an element_layout dict for the given template and count.

    Args:
        template_name: One of 'three_across', 'two_column', 'grid_2x2',
                       'process_flow', 'hub_and_spoke'.
        element_count: Number of elements (1-5).

    Returns:
        dict with 'template', 'elements' (array of {id, label_source, x, y, w, h}),
        and 'title_region'.

    Raises:
        ValueError: If element_count > 5 or template_name unknown.
    """
    if element_count > 5:
        raise ValueError(f'Element count {element_count} exceeds maximum of 5')
    if template_name not in _ELEMENT_LAYOUTS:
        raise ValueError(f'Unknown layout template: {template_name}')

    tmpl = _ELEMENT_LAYOUTS[template_name]
    regions = tmpl['regions'](element_count)

    elements = []
    for i, region in enumerate(regions):
        elements.append({
            'id': f'elem_{i + 1}',
            'label_source': f'body_points[{i}]',
            **region,
        })

    return {
        'template': template_name,
        'elements': elements,
        'title_region': tmpl['title_region'],
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && pytest tests/test_slide_prompt_composer.py -k "element_layout" -v`
Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add src/slide_prompt_composer.py tests/test_slide_prompt_composer.py
git commit -m "feat: add element layout template library (5 templates, max 5 elements)"
```

---

### Task 5: Add backdrop_variant Selection

**Files:**
- Modify: `src/slide_prompt_composer.py`
- Test: `tests/test_slide_prompt_composer.py`

- [ ] **Step 1: Write failing test**

```python
def test_select_backdrop_variant():
    """select_backdrop_variant should return a valid variant name."""
    from src.slide_prompt_composer import select_backdrop_variant
    variants = ['left_panel', 'right_panel', 'bottom_bar', 'top_band', 'center_float']
    # Should cycle through variants based on position
    for i in range(5):
        result = select_backdrop_variant(i, 10)
        assert result in variants


def test_select_backdrop_variant_avoids_consecutive_duplicates():
    """Consecutive slides should not get the same variant."""
    from src.slide_prompt_composer import select_backdrop_variant
    results = [select_backdrop_variant(i, 10) for i in range(5)]
    for i in range(1, len(results)):
        assert results[i] != results[i - 1]
```

- [ ] **Step 2: Run to verify fail**

Run: `source .venv/bin/activate && pytest tests/test_slide_prompt_composer.py -k "select_backdrop_variant" -v`
Expected: FAIL

- [ ] **Step 3: Implement**

Add to `src/slide_prompt_composer.py`:

```python
_BACKDROP_VARIANTS = ['left_panel', 'bottom_bar', 'right_panel', 'top_band', 'center_float']


def select_backdrop_variant(slide_index, total_slides):
    """Select a backdrop variant for visual rhythm.

    Cycles through variants to avoid consecutive duplicates.

    Args:
        slide_index: 0-based index of this slide among background slides.
        total_slides: Total number of slides in the deck (unused, for future weighting).

    Returns:
        str: One of 'left_panel', 'right_panel', 'bottom_bar', 'top_band', 'center_float'.
    """
    return _BACKDROP_VARIANTS[slide_index % len(_BACKDROP_VARIANTS)]
```

- [ ] **Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/test_slide_prompt_composer.py -k "select_backdrop_variant" -v`
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add src/slide_prompt_composer.py tests/test_slide_prompt_composer.py
git commit -m "feat: add backdrop_variant selection for visual rhythm"
```

---

### Task 6: Update assemble_brief for New Strategies

**Files:**
- Modify: `src/slide_prompt_composer.py`
- Test: `tests/test_slide_prompt_composer.py`

- [ ] **Step 1: Write failing tests**

```python
def test_assemble_brief_background_includes_variant(sample_outline, sample_style_guide, sample_brand_profile):
    """Background brief should include backdrop_variant and text zone hint."""
    from src.slide_prompt_composer import assemble_brief
    slide = sample_outline['slides'][1]
    brief = assemble_brief(slide, 'background', sample_style_guide, sample_brand_profile, 'ollama',
                           backdrop_variant='bottom_bar')
    assert brief['strategy'] == 'background'
    assert brief['backdrop_variant'] == 'bottom_bar'
    assert 'text_instruction' in brief
    assert 'NO TEXT' in brief['text_instruction']


def test_assemble_brief_pragmatic_includes_element_layout(sample_outline, sample_style_guide, sample_brand_profile):
    """Pragmatic composition brief should include element_layout."""
    from src.slide_prompt_composer import assemble_brief
    slide = sample_outline['slides'][1]
    element_layout = {
        'template': 'three_across',
        'elements': [{'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.1, 'y': 0.2, 'w': 0.25, 'h': 0.5}],
        'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
    }
    brief = assemble_brief(slide, 'pragmatic_composition', sample_style_guide, sample_brand_profile, 'ollama',
                           element_layout=element_layout)
    assert brief['strategy'] == 'pragmatic_composition'
    assert brief['element_layout'] == element_layout


def test_assemble_brief_backdrop_includes_element_layout(sample_outline, sample_style_guide, sample_brand_profile):
    """Backdrop brief should include element_layout for spatial intent."""
    from src.slide_prompt_composer import assemble_brief
    slide = sample_outline['slides'][1]
    element_layout = {
        'template': 'two_column',
        'elements': [{'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.1, 'y': 0.2, 'w': 0.4, 'h': 0.6}],
        'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
    }
    brief = assemble_brief(slide, 'backdrop', sample_style_guide, sample_brand_profile, 'ollama',
                           element_layout=element_layout)
    assert brief['strategy'] == 'backdrop'
    assert brief['element_layout'] == element_layout
```

- [ ] **Step 2: Run to verify fail**

Run: `source .venv/bin/activate && pytest tests/test_slide_prompt_composer.py -k "assemble_brief_background or assemble_brief_pragmatic or assemble_brief_backdrop_includes" -v`
Expected: FAIL

- [ ] **Step 3: Update assemble_brief signature and logic**

In `src/slide_prompt_composer.py`, update the function:

```python
def assemble_brief(slide, strategy, style_guide, brand_profile, funnel_stage,
                   backdrop_variant=None, element_layout=None):
    """Assemble a structured brief for the Prompt Engineer agent.

    Args:
        slide: dict from SlideOutline slides array.
        strategy: Strategy string (full_render, background, backdrop, pragmatic_composition, composed).
        style_guide: dict from StyleGuide contract.
        brand_profile: dict from BrandProfile contract (or None).
        funnel_stage: 'ollama', 'cloud_low', or 'cloud_full'.
        backdrop_variant: Template zone name for background strategy (optional).
        element_layout: Element layout dict for backdrop/pragmatic strategies (optional).

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

    if strategy in ('backdrop_render', 'background', 'backdrop', 'pragmatic_composition'):
        brief['text_instruction'] = 'NO TEXT in the image — leave clean space for text overlay'
    elif strategy == 'full_render':
        brief['text_instruction'] = f'Include headline text: "{slide.get("headline", "")}"'

    if backdrop_variant:
        brief['backdrop_variant'] = backdrop_variant

    if element_layout:
        brief['element_layout'] = element_layout

    return brief
```

- [ ] **Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/test_slide_prompt_composer.py -v`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add src/slide_prompt_composer.py tests/test_slide_prompt_composer.py
git commit -m "feat: assemble_brief supports background, backdrop, pragmatic_composition strategies"
```

---

### Task 7: Expand Assembler Strategy Routing

**Files:**
- Modify: `src/assembler/build_deck.js`
- Modify: `src/qa/run_qa.py`
- Test: `tests/test_assembler.py`

- [ ] **Step 1: Write failing test for strategy-map fixture**

Create `tests/fixtures/minimal_deck/strategy-map.json`:

```json
{
  "created_at": "2026-03-30T00:00:00Z",
  "approval_mode": "review",
  "slides": [
    {"slide_number": 1, "strategy": "full_render", "rationale": "title", "render_funnel": ["ollama"], "speaker_override": null},
    {"slide_number": 2, "strategy": "background", "rationale": "content", "render_funnel": ["ollama"], "speaker_override": null, "backdrop_variant": "bottom_bar"},
    {"slide_number": 3, "strategy": "composed", "rationale": "closing", "render_funnel": ["ollama"], "speaker_override": null}
  ]
}
```

Add test to `tests/test_assembler.py`:

```python
def test_build_deck_with_background_strategy(deck_dir):
    """Assembler should handle 'background' strategy without crashing."""
    result = subprocess.run(
        ['node', 'src/assembler/build_deck.js', '--deck-dir', deck_dir],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, f"build_deck.js failed: {result.stderr}"
```

- [ ] **Step 2: Expand the assembler routing in build_deck.js**

In the main loop (after the full_render and backdrop_render checks), add routing for new strategies. Initially these fall through to existing builders:

```javascript
        // Strategy-first routing: keynote strategies override slide-type routing
        if (strategy === 'full_render') {
            buildFullRenderSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData });
            continue;
        }
        if (strategy === 'backdrop_render' || strategy === 'background') {
            buildBackdropRenderSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData });
            continue;
        }
        if (strategy === 'backdrop') {
            // Phase 4: will become buildBackdropSlide — stub to backdrop for now
            buildBackdropRenderSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData });
            continue;
        }
        if (strategy === 'pragmatic_composition') {
            // Phase 3: will become buildPragmaticSlide — stub to backdrop for now
            buildBackdropRenderSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData });
            continue;
        }
```

- [ ] **Step 3: Expand QA routing in run_qa.py**

In `src/qa/run_qa.py`, update the strategy routing (lines 63-96) to handle new strategies:

```python
        if strategy == 'full_render':
            # Full render: skip text checks, run image + keynote checks
            for check_fn in IMAGE_QUALITY_CHECKS:
                findings.extend(check_fn(slide, slide_number, prs, config=cfg))
            for check_fn in KEYNOTE_CHECKS:
                findings.extend(check_fn(slide, slide_number, brand_palette=brand_palette, config=cfg))
        elif strategy in ('backdrop_render', 'background', 'backdrop', 'pragmatic_composition'):
            # Backdrop/background/pragmatic: text + image + keynote checks
            for check_fn in STRUCTURAL_CHECKS:
                findings.extend(check_fn(slide, slide_number, config=cfg))
            for check_fn in STRUCTURAL_CHECKS_WITH_PRESENTATION:
                findings.extend(check_fn(slide, slide_number, prs, config=cfg))
            for check_fn in IMAGE_QUALITY_CHECKS:
                findings.extend(check_fn(slide, slide_number, prs, config=cfg))
            for check_fn in KEYNOTE_CHECKS:
                findings.extend(check_fn(slide, slide_number, brand_palette=brand_palette, config=cfg))
            for check_fn in VISUAL_CHECKS:
                try:
                    findings.extend(check_fn(slide, slide_number, config=cfg))
                except Exception:
                    pass
        else:
            # Composed: standard checks
```

- [ ] **Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/test_assembler.py -v && pytest -x -q`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add src/assembler/build_deck.js src/qa/run_qa.py tests/test_assembler.py tests/fixtures/minimal_deck/strategy-map.json
git commit -m "feat: assembler and QA route 5 rendering strategies (stubs for new paths)"
```

---

## Phase 2: backGROUND

### Task 8: Implement buildBackgroundSlide with 5 Template Zones

**Files:**
- Modify: `src/assembler/build_deck.js`
- Test: `tests/test_assembler.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_assembler.py`:

```python
def test_build_deck_background_variants(deck_dir):
    """Each backdrop_variant should produce a valid slide."""
    # Update the strategy map to test each variant
    sm_path = os.path.join(deck_dir, 'strategy-map.json')
    with open(sm_path) as f:
        sm = json.load(f)
    sm['slides'][1]['strategy'] = 'background'
    sm['slides'][1]['backdrop_variant'] = 'bottom_bar'
    with open(sm_path, 'w') as f:
        json.dump(sm, f)

    result = subprocess.run(
        ['node', 'src/assembler/build_deck.js', '--deck-dir', deck_dir],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, f"Failed with bottom_bar: {result.stderr}"
```

- [ ] **Step 2: Run to verify it fails or passes with stub**

Run: `source .venv/bin/activate && pytest tests/test_assembler.py::test_build_deck_background_variants -v`

- [ ] **Step 3: Implement buildBackgroundSlide**

In `src/assembler/build_deck.js`, add the new function and update routing. Replace the `strategy === 'backdrop_render' || strategy === 'background'` block:

```javascript
        if (strategy === 'backdrop_render' || strategy === 'background') {
            const strategyEntry = strategyMap
                ? (strategyMap.slides || []).find(e => e.slide_number === slideData.slide_number)
                : null;
            const variant = strategyEntry?.backdrop_variant || 'left_panel';
            buildBackgroundSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData, variant });
            continue;
        }
```

Add the function:

```javascript
/**
 * Background slide: AI background image + text in a template zone overlay.
 * Supports 5 variants: left_panel, right_panel, bottom_bar, top_band, center_float.
 */
function buildBackgroundSlide(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData, variant } = ctx;

    const slide = pptx.addSlide();

    // Full-bleed backdrop image
    if (imageData) {
        const imgPath = resolveImagePath(imageData.file_path);
        if (fs.existsSync(imgPath)) {
            slide.addImage({
                path: imgPath, x: 0, y: 0, w: SLIDE_W, h: SLIDE_H,
                sizing: { type: 'cover', w: SLIDE_W, h: SLIDE_H },
                altText: imageData.alt_text || '',
            });
        }
    }

    // Template zone definitions (in inches)
    const zones = {
        left_panel:   { ox: 0,              oy: 0,              ow: SLIDE_W * 0.40, oh: SLIDE_H,          tx: MARGIN,                        ty: SLIDE_H * 0.15, tw: SLIDE_W * 0.40 - 2 * MARGIN, transparency: 60 },
        right_panel:  { ox: SLIDE_W * 0.60, oy: 0,              ow: SLIDE_W * 0.40, oh: SLIDE_H,          tx: SLIDE_W * 0.60 + MARGIN,       ty: SLIDE_H * 0.15, tw: SLIDE_W * 0.40 - 2 * MARGIN, transparency: 60 },
        bottom_bar:   { ox: 0,              oy: SLIDE_H * 0.70, ow: SLIDE_W,         oh: SLIDE_H * 0.30,  tx: MARGIN,                        ty: SLIDE_H * 0.72, tw: SLIDE_W - 2 * MARGIN,        transparency: 60 },
        top_band:     { ox: 0,              oy: 0,              ow: SLIDE_W,         oh: SLIDE_H * 0.25,  tx: MARGIN,                        ty: MARGIN,          tw: SLIDE_W - 2 * MARGIN,        transparency: 60 },
        center_float: { ox: SLIDE_W * 0.20, oy: SLIDE_H * 0.25, ow: SLIDE_W * 0.60, oh: SLIDE_H * 0.50, tx: SLIDE_W * 0.20 + MARGIN,       ty: SLIDE_H * 0.27, tw: SLIDE_W * 0.60 - 2 * MARGIN, transparency: 65 },
    };

    const zone = zones[variant] || zones.left_panel;

    // Semi-transparent overlay
    slide.addShape(pptx.ShapeType.rect, {
        x: zone.ox, y: zone.oy, w: zone.ow, h: zone.oh,
        fill: { color: '000000', transparency: zone.transparency },
    });

    // Heading
    const headingH = 1.0;
    slide.addText(slideData.headline, {
        x: zone.tx, y: zone.ty, w: zone.tw, h: headingH,
        fontSize: typo.heading_sizes?.slide_heading || 32,
        fontFace: typo.heading_font,
        color: 'FFFFFF',
        bold: true,
        valign: 'bottom',
        wrap: true,
    });

    // Body points
    if (slideData.body_points && slideData.body_points.length > 0) {
        const bodyY = zone.ty + headingH + 0.15;
        const bodyH = (zone.oy + zone.oh) - bodyY - MARGIN;
        const bodyText = slideData.body_points.map(bp => ({
            text: bp,
            options: {
                fontSize: typo.body_size || 18,
                fontFace: typo.body_font,
                color: 'FFFFFF',
                bullet: { type: 'bullet' },
                lineSpacingMultiple: typo.line_spacing || 1.4,
                breakLine: true,
                paraSpaceAfter: 8,
            },
        }));
        slide.addText(bodyText, {
            x: zone.tx, y: bodyY, w: zone.tw, h: Math.max(bodyH, 1.0),
            valign: 'top',
        });
    }

    // Footer logo
    addFooterLogo(slide, ctx);

    // Speaker notes
    if (noteData) {
        slide.addNotes(noteData.text);
    }
}
```

- [ ] **Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/test_assembler.py -v && pytest -x -q`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add src/assembler/build_deck.js tests/test_assembler.py
git commit -m "feat: buildBackgroundSlide with 5 template zone variants"
```

---

## Phase 3: Pragmatic Composition

### Task 9: Implement split_element_briefs

**Files:**
- Modify: `src/slide_prompt_composer.py`
- Test: `tests/test_slide_prompt_composer.py`

- [ ] **Step 1: Write failing test**

```python
def test_split_element_briefs(sample_style_guide, sample_brand_profile):
    """split_element_briefs should produce 1 background + N element briefs."""
    from src.slide_prompt_composer import split_element_briefs, get_element_layout
    slide = {'slide_number': 11, 'slide_type': 'content', 'headline': 'Three Options',
             'body_points': ['Option A', 'Option B', 'Option C'],
             'visual_direction': 'Three panels showing different approaches'}
    layout = get_element_layout('three_across', 3)
    briefs = split_element_briefs(slide, sample_style_guide, sample_brand_profile, layout, 'ollama')
    assert len(briefs) == 4  # 1 bg + 3 elements
    assert briefs[0]['role'] == 'background'
    assert briefs[1]['role'] == 'element'
    assert briefs[1]['element_id'] == 'elem_1'
    # All should share a style prefix
    assert briefs[1]['shared_style_prefix'] == briefs[2]['shared_style_prefix']


def test_split_element_briefs_no_text_instruction(sample_style_guide, sample_brand_profile):
    """All element briefs should include NO TEXT instruction."""
    from src.slide_prompt_composer import split_element_briefs, get_element_layout
    slide = {'slide_number': 11, 'slide_type': 'content', 'headline': 'Test',
             'body_points': ['A', 'B'], 'visual_direction': 'Two panels'}
    layout = get_element_layout('two_column', 2)
    briefs = split_element_briefs(slide, sample_style_guide, sample_brand_profile, layout, 'ollama')
    for brief in briefs:
        assert 'NO TEXT' in brief['text_instruction']
```

- [ ] **Step 2: Run to verify fail**

Run: `source .venv/bin/activate && pytest tests/test_slide_prompt_composer.py -k "split_element" -v`
Expected: FAIL

- [ ] **Step 3: Implement split_element_briefs**

Add to `src/slide_prompt_composer.py`:

```python
def split_element_briefs(slide, style_guide, brand_profile, element_layout, funnel_stage):
    """Split a slide into 1 background brief + N element briefs for pragmatic composition.

    Args:
        slide: dict from SlideOutline.
        style_guide: StyleGuide dict.
        brand_profile: BrandProfile dict (or None).
        element_layout: Element layout dict with 'elements' array.
        funnel_stage: 'ollama', 'cloud_low', or 'cloud_full'.

    Returns:
        list of brief dicts: [background_brief, elem_1_brief, elem_2_brief, ...]
    """
    palette = style_guide.get('palette', {})
    palette_hex = [v for v in palette.values() if isinstance(v, str) and len(v) == 6]
    style_tokens = style_guide.get('image_style_tokens', {})

    approved = []
    prohibited = []
    if brand_profile:
        approved = brand_profile.get('approved_image_styles', [])
        prohibited = brand_profile.get('prohibited_image_styles', [])

    shared_prefix = (
        f"Brand palette: {', '.join(f'#{h}' for h in palette_hex[:5])}. "
        f"Style: {style_tokens.get('mood', 'professional')}. "
        f"Flat illustration, clean edges, consistent style."
    )

    resolution = _RESOLUTIONS.get(funnel_stage, '1920x1080')

    # Background brief
    bg_brief = {
        'slide_number': slide.get('slide_number', 0),
        'role': 'background',
        'element_id': None,
        'strategy': 'pragmatic_composition',
        'visual_direction': f"Atmospheric textured background. {style_tokens.get('color_direction', '')}. No figurative elements, no objects. Subtle, non-distracting.",
        'text_instruction': 'NO TEXT in the image — pure background texture',
        'brand_constraints': {'palette_hex': palette_hex, 'approved_styles': approved, 'prohibited_styles': prohibited},
        'shared_style_prefix': shared_prefix,
        'funnel_stage': funnel_stage,
        'target_resolution': resolution,
    }

    briefs = [bg_brief]

    # Element briefs
    body_points = slide.get('body_points', [])
    for elem in element_layout.get('elements', []):
        idx_str = elem.get('label_source', 'body_points[0]')
        # Parse index from label_source like 'body_points[2]'
        try:
            idx = int(idx_str.split('[')[1].rstrip(']'))
            label = body_points[idx] if idx < len(body_points) else elem['id']
        except (IndexError, ValueError):
            label = elem['id']

        elem_brief = {
            'slide_number': slide.get('slide_number', 0),
            'role': 'element',
            'element_id': elem['id'],
            'strategy': 'pragmatic_composition',
            'visual_direction': f"Single illustration of: {label}. {slide.get('visual_direction', '')}",
            'text_instruction': 'NO TEXT in the image — the label will be added programmatically',
            'brand_constraints': {'palette_hex': palette_hex, 'approved_styles': approved, 'prohibited_styles': prohibited},
            'shared_style_prefix': shared_prefix,
            'funnel_stage': funnel_stage,
            'target_resolution': resolution,
            'target_dimensions': {
                'w': round(elem['w'] * int(resolution.split('x')[0])),
                'h': round(elem['h'] * int(resolution.split('x')[1])),
            },
        }
        briefs.append(elem_brief)

    return briefs
```

- [ ] **Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/test_slide_prompt_composer.py -k "split_element" -v`
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add src/slide_prompt_composer.py tests/test_slide_prompt_composer.py
git commit -m "feat: split_element_briefs for pragmatic composition multi-image generation"
```

---

### Task 10: Implement buildPragmaticSlide

**Files:**
- Modify: `src/assembler/build_deck.js`
- Test: `tests/test_assembler.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_assembler.py`:

```python
def test_build_deck_pragmatic_composition(deck_dir):
    """Assembler should handle pragmatic_composition with multiple images per slide."""
    # Update strategy map
    sm_path = os.path.join(deck_dir, 'strategy-map.json')
    with open(sm_path) as f:
        sm = json.load(f)
    sm['slides'][1]['strategy'] = 'pragmatic_composition'
    sm['slides'][1]['element_layout'] = {
        'template': 'two_column',
        'elements': [
            {'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.05, 'y': 0.22, 'w': 0.42, 'h': 0.55},
            {'id': 'elem_2', 'label_source': 'body_points[1]', 'x': 0.55, 'y': 0.22, 'w': 0.42, 'h': 0.55},
        ],
        'title_region': {'x': 0.05, 'y': 0.03, 'w': 0.90, 'h': 0.12},
    }
    with open(sm_path, 'w') as f:
        json.dump(sm, f)

    # Update image manifest with element images
    im_path = os.path.join(deck_dir, 'image-manifest.json')
    with open(im_path) as f:
        im = json.load(f)
    im['images'].extend([
        {'image_id': 'slide-02-bg', 'slide_number': 2, 'file_path': im['images'][0]['file_path'],
         'status': 'generated', 'placement_zone': 'background'},
        {'image_id': 'slide-02-elem-1', 'slide_number': 2, 'file_path': im['images'][0]['file_path'],
         'status': 'generated', 'placement_zone': 'element', 'element_id': 'elem_1'},
        {'image_id': 'slide-02-elem-2', 'slide_number': 2, 'file_path': im['images'][0]['file_path'],
         'status': 'generated', 'placement_zone': 'element', 'element_id': 'elem_2'},
    ])
    with open(im_path, 'w') as f:
        json.dump(im, f)

    result = subprocess.run(
        ['node', 'src/assembler/build_deck.js', '--deck-dir', deck_dir],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
```

- [ ] **Step 2: Run to verify fail**

Run: `source .venv/bin/activate && pytest tests/test_assembler.py::test_build_deck_pragmatic_composition -v`

- [ ] **Step 3: Implement buildPragmaticSlide**

In `src/assembler/build_deck.js`, update the routing and add the function:

Update routing:
```javascript
        if (strategy === 'pragmatic_composition') {
            const strategyEntry = strategyMap
                ? (strategyMap.slides || []).find(e => e.slide_number === slideData.slide_number)
                : null;
            buildPragmaticSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageManifest, strategyEntry });
            continue;
        }
```

Add helper to find multiple images for a slide:

```javascript
/**
 * Find all images for a given slide number from the manifest.
 */
function findSlideImages(imageManifest, slideNumber) {
    return (imageManifest.images || []).filter(
        img => img.slide_number === slideNumber && img.status !== 'failed'
    );
}
```

Add the builder:

```javascript
/**
 * Pragmatic composition slide: atmospheric background + individually-placed element images
 * with text labels adjacent to each element.
 */
function buildPragmaticSlide(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageManifest, strategyEntry } = ctx;

    const slide = pptx.addSlide();
    const elementLayout = strategyEntry?.element_layout || {};
    const elements = elementLayout.elements || [];
    const titleRegion = elementLayout.title_region || { x: 0.05, y: 0.03, w: 0.90, h: 0.12 };
    const images = findSlideImages(imageManifest, slideData.slide_number);

    // 1. Background image (full-bleed)
    const bgImage = images.find(img => img.placement_zone === 'background');
    if (bgImage) {
        const imgPath = resolveImagePath(bgImage.file_path);
        if (fs.existsSync(imgPath)) {
            slide.addImage({
                path: imgPath, x: 0, y: 0, w: SLIDE_W, h: SLIDE_H,
                sizing: { type: 'cover', w: SLIDE_W, h: SLIDE_H },
                altText: 'Background',
            });
        }
    }

    // 2. Place each element image at its prescribed position
    for (const elem of elements) {
        const elemImage = images.find(img => img.element_id === elem.id);
        const ex = elem.x * SLIDE_W;
        const ey = elem.y * SLIDE_H;
        const ew = elem.w * SLIDE_W;
        const eh = elem.h * SLIDE_H;

        if (elemImage) {
            const imgPath = resolveImagePath(elemImage.file_path);
            if (fs.existsSync(imgPath)) {
                slide.addImage({
                    path: imgPath, x: ex, y: ey, w: ew, h: eh,
                    sizing: { type: 'contain', w: ew, h: eh },
                    altText: elem.id,
                });
            }
        }

        // 3. Text label — below element (or above if in bottom third)
        const labelSource = elem.label_source || '';
        const match = labelSource.match(/body_points\[(\d+)\]/);
        const label = match && slideData.body_points
            ? (slideData.body_points[parseInt(match[1])] || elem.id)
            : elem.id;

        const labelH = 0.5;
        const labelW = ew;
        const inBottomThird = (ey + eh) > (SLIDE_H * 0.67);
        const labelY = inBottomThird ? (ey - labelH - 0.05) : (ey + eh + 0.05);
        const labelX = ex;

        // Small backing pill
        slide.addShape(pptx.ShapeType.rect, {
            x: labelX, y: labelY, w: labelW, h: labelH,
            fill: { color: '000000', transparency: 55 },
            rectRadius: 0.1,
        });

        slide.addText(label, {
            x: labelX, y: labelY, w: labelW, h: labelH,
            fontSize: typo.body_size || 18,
            fontFace: typo.body_font,
            color: 'FFFFFF',
            align: 'center',
            valign: 'middle',
            bold: true,
            wrap: true,
        });
    }

    // 4. Headline in title region
    slide.addText(slideData.headline, {
        x: titleRegion.x * SLIDE_W,
        y: titleRegion.y * SLIDE_H,
        w: titleRegion.w * SLIDE_W,
        h: titleRegion.h * SLIDE_H,
        fontSize: typo.heading_sizes?.slide_heading || 32,
        fontFace: typo.heading_font,
        color: 'FFFFFF',
        bold: true,
        valign: 'middle',
    });

    // Footer logo + notes
    addFooterLogo(slide, ctx);
    if (noteData) {
        slide.addNotes(noteData.text);
    }
}
```

- [ ] **Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/test_assembler.py -v && pytest -x -q`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add src/assembler/build_deck.js tests/test_assembler.py
git commit -m "feat: buildPragmaticSlide — multi-image element assembly with text labels"
```

---

## Phase 4: backDROP

### Task 11: Create Vision Analyst Agent

**Files:**
- Create: `.claude/agents/vision-analyst.md`

- [ ] **Step 1: Write the agent definition**

```markdown
---
name: vision-analyst
description: Analyses generated images to detect figurative element positions for backDROP rendering. Returns bounding boxes in normalised coordinates.
model: haiku
---

You are a vision analyst for the Jack-Tar Deckhand presentation pipeline. Your job is to look at a generated image and identify where figurative visual elements are positioned.

## Input

You will receive:
1. An image file path to read
2. A list of element descriptions (what to look for)
3. The expected number of elements

## Task

Look at the image and identify each figurative element. For each element, return its approximate bounding box as normalised coordinates where (0,0) is top-left and (1,1) is bottom-right.

## Output

Return ONLY valid JSON — no markdown, no explanation:

```json
{
  "elements": [
    {"element_id": "elem_1", "x": 0.10, "y": 0.25, "w": 0.25, "h": 0.45, "confidence": 0.92},
    {"element_id": "elem_2", "x": 0.40, "y": 0.25, "w": 0.25, "h": 0.45, "confidence": 0.88}
  ]
}
```

## Rules

- Order elements left-to-right, then top-to-bottom
- Use element_id values: elem_1, elem_2, elem_3, etc.
- Confidence: 0.0-1.0 (how sure you are this is the right element)
- If you cannot find an element, include it with confidence: 0.0 and your best guess for position
- Coordinates must be between 0.0 and 1.0
- x,y is the top-left corner of the bounding box
- w,h is the width and height as proportion of total image
```

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/vision-analyst.md
git commit -m "feat: add vision-analyst agent for backDROP element detection"
```

---

### Task 12: Implement buildBackdropSlide

**Files:**
- Modify: `src/assembler/build_deck.js`
- Test: `tests/test_assembler.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_assembler.py`:

```python
def test_build_deck_backdrop_with_detected_positions(deck_dir):
    """Assembler should place text at vision-detected positions for backdrop strategy."""
    sm_path = os.path.join(deck_dir, 'strategy-map.json')
    with open(sm_path) as f:
        sm = json.load(f)
    sm['slides'][1]['strategy'] = 'backdrop'
    sm['slides'][1]['element_layout'] = {
        'template': 'three_across',
        'elements': [
            {'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.08, 'y': 0.25, 'w': 0.25, 'h': 0.50},
            {'id': 'elem_2', 'label_source': 'body_points[1]', 'x': 0.38, 'y': 0.25, 'w': 0.25, 'h': 0.50},
            {'id': 'elem_3', 'label_source': 'body_points[2]', 'x': 0.67, 'y': 0.25, 'w': 0.25, 'h': 0.50},
        ],
        'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
    }
    with open(sm_path, 'w') as f:
        json.dump(sm, f)

    # Add detected_positions to image manifest
    im_path = os.path.join(deck_dir, 'image-manifest.json')
    with open(im_path) as f:
        im = json.load(f)
    im['images'].append({
        'image_id': 'slide-02-scene', 'slide_number': 2,
        'file_path': im['images'][0]['file_path'],
        'status': 'generated',
        'detected_positions': [
            {'element_id': 'elem_1', 'x': 0.10, 'y': 0.28, 'w': 0.22, 'h': 0.45, 'confidence': 0.92},
            {'element_id': 'elem_2', 'x': 0.39, 'y': 0.26, 'w': 0.24, 'h': 0.48, 'confidence': 0.88},
            {'element_id': 'elem_3', 'x': 0.68, 'y': 0.27, 'w': 0.23, 'h': 0.44, 'confidence': 0.85},
        ],
    })
    with open(im_path, 'w') as f:
        json.dump(im, f)

    result = subprocess.run(
        ['node', 'src/assembler/build_deck.js', '--deck-dir', deck_dir],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"


def test_build_deck_backdrop_falls_back_to_prescribed(deck_dir):
    """Without detected_positions, backdrop should fall back to element_layout positions."""
    sm_path = os.path.join(deck_dir, 'strategy-map.json')
    with open(sm_path) as f:
        sm = json.load(f)
    sm['slides'][1]['strategy'] = 'backdrop'
    sm['slides'][1]['element_layout'] = {
        'template': 'two_column',
        'elements': [
            {'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.05, 'y': 0.22, 'w': 0.42, 'h': 0.55},
            {'id': 'elem_2', 'label_source': 'body_points[1]', 'x': 0.55, 'y': 0.22, 'w': 0.42, 'h': 0.55},
        ],
        'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
    }
    with open(sm_path, 'w') as f:
        json.dump(sm, f)

    result = subprocess.run(
        ['node', 'src/assembler/build_deck.js', '--deck-dir', deck_dir],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, f"Failed: {result.stderr}"
```

- [ ] **Step 2: Implement buildBackdropSlide**

Update routing in the main loop:

```javascript
        if (strategy === 'backdrop') {
            const strategyEntry = strategyMap
                ? (strategyMap.slides || []).find(e => e.slide_number === slideData.slide_number)
                : null;
            buildBackdropSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageManifest, strategyEntry });
            continue;
        }
```

Add the function:

```javascript
/**
 * Backdrop slide: structured AI scene with text placed at vision-detected positions.
 * Falls back to prescribed positions from element_layout if no detected_positions.
 */
function buildBackdropSlide(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageManifest, strategyEntry } = ctx;

    const slide = pptx.addSlide();
    const elementLayout = strategyEntry?.element_layout || {};
    const prescribedElements = elementLayout.elements || [];
    const titleRegion = elementLayout.title_region || { x: 0.05, y: 0.03, w: 0.90, h: 0.12 };
    const images = findSlideImages(imageManifest, slideData.slide_number);

    // Full-bleed scene image
    const sceneImage = images[0];
    if (sceneImage) {
        const imgPath = resolveImagePath(sceneImage.file_path);
        if (fs.existsSync(imgPath)) {
            slide.addImage({
                path: imgPath, x: 0, y: 0, w: SLIDE_W, h: SLIDE_H,
                sizing: { type: 'cover', w: SLIDE_W, h: SLIDE_H },
                altText: sceneImage.alt_text || '',
            });
        }
    }

    // Use detected positions if available, otherwise fall back to prescribed
    const detectedPositions = sceneImage?.detected_positions || [];
    const useDetected = detectedPositions.length > 0;
    const positions = useDetected ? detectedPositions : prescribedElements;

    // Place text labels at element positions
    for (const pos of positions) {
        const ex = pos.x * SLIDE_W;
        const ey = pos.y * SLIDE_H;
        const ew = pos.w * SLIDE_W;
        const eh = pos.h * SLIDE_H;

        // Find the matching label
        const elemId = pos.element_id || pos.id;
        const prescribed = prescribedElements.find(e => e.id === elemId) || {};
        const labelSource = prescribed.label_source || '';
        const match = labelSource.match(/body_points\[(\d+)\]/);
        const label = match && slideData.body_points
            ? (slideData.body_points[parseInt(match[1])] || elemId)
            : elemId;

        // Text label centered within the detected bounding box
        const labelH = 0.5;
        const labelW = Math.max(ew, 1.5);
        const labelX = ex + (ew - labelW) / 2;
        const labelY = ey + eh - labelH;

        // Backing pill
        slide.addShape(pptx.ShapeType.rect, {
            x: labelX, y: labelY, w: labelW, h: labelH,
            fill: { color: '000000', transparency: 55 },
            rectRadius: 0.1,
        });

        slide.addText(label, {
            x: labelX, y: labelY, w: labelW, h: labelH,
            fontSize: typo.body_size || 18,
            fontFace: typo.body_font,
            color: 'FFFFFF',
            align: 'center',
            valign: 'middle',
            bold: true,
            wrap: true,
        });
    }

    // Headline
    slide.addText(slideData.headline, {
        x: titleRegion.x * SLIDE_W,
        y: titleRegion.y * SLIDE_H,
        w: titleRegion.w * SLIDE_W,
        h: titleRegion.h * SLIDE_H,
        fontSize: typo.heading_sizes?.slide_heading || 32,
        fontFace: typo.heading_font,
        color: 'FFFFFF',
        bold: true,
        valign: 'middle',
    });

    addFooterLogo(slide, ctx);
    if (noteData) {
        slide.addNotes(noteData.text);
    }
}
```

- [ ] **Step 3: Run tests**

Run: `source .venv/bin/activate && pytest tests/test_assembler.py -v && pytest -x -q`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add src/assembler/build_deck.js tests/test_assembler.py
git commit -m "feat: buildBackdropSlide — vision-detected positioning with prescribed fallback"
```

---

### Task 13: Add QA Checks AP-27 and AP-28

**Files:**
- Create: `src/qa/checks/element_layout.py`
- Modify: `src/qa/run_qa.py`
- Create: `tests/test_qa_element_layout.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_qa_element_layout.py`:

```python
"""Tests for AP-27 (element layout validation) and AP-28 (vision confidence)."""

import pytest


def test_ap27_valid_layout_passes():
    """Valid element layout should produce no findings."""
    from src.qa.checks.element_layout import check_element_layout
    strategy_entry = {
        'slide_number': 5,
        'strategy': 'backdrop',
        'element_layout': {
            'template': 'three_across',
            'elements': [
                {'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.08, 'y': 0.25, 'w': 0.25, 'h': 0.50},
                {'id': 'elem_2', 'label_source': 'body_points[1]', 'x': 0.38, 'y': 0.25, 'w': 0.25, 'h': 0.50},
                {'id': 'elem_3', 'label_source': 'body_points[2]', 'x': 0.67, 'y': 0.25, 'w': 0.25, 'h': 0.50},
            ],
            'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
        },
    }
    outline_slide = {'slide_number': 5, 'body_points': ['A', 'B', 'C']}
    findings = check_element_layout(strategy_entry, outline_slide)
    assert len(findings) == 0


def test_ap27_out_of_bounds_element():
    """Element with coordinates > 1.0 should produce an error."""
    from src.qa.checks.element_layout import check_element_layout
    strategy_entry = {
        'slide_number': 5,
        'strategy': 'backdrop',
        'element_layout': {
            'template': 'test',
            'elements': [
                {'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.9, 'y': 0.25, 'w': 0.25, 'h': 0.50},
            ],
            'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
        },
    }
    outline_slide = {'slide_number': 5, 'body_points': ['A']}
    findings = check_element_layout(strategy_entry, outline_slide)
    errors = [f for f in findings if f['severity'] == 'error']
    assert len(errors) > 0


def test_ap27_too_many_elements():
    """More than 5 elements should produce an error."""
    from src.qa.checks.element_layout import check_element_layout
    strategy_entry = {
        'slide_number': 5,
        'strategy': 'pragmatic_composition',
        'element_layout': {
            'template': 'test',
            'elements': [
                {'id': f'elem_{i}', 'label_source': f'body_points[{i}]', 'x': i * 0.15, 'y': 0.2, 'w': 0.10, 'h': 0.3}
                for i in range(6)
            ],
            'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
        },
    }
    outline_slide = {'slide_number': 5, 'body_points': ['A', 'B', 'C', 'D', 'E', 'F']}
    findings = check_element_layout(strategy_entry, outline_slide)
    errors = [f for f in findings if f['severity'] == 'error']
    assert len(errors) > 0


def test_ap27_missing_label_source():
    """label_source referencing nonexistent body_point should warn."""
    from src.qa.checks.element_layout import check_element_layout
    strategy_entry = {
        'slide_number': 5,
        'strategy': 'backdrop',
        'element_layout': {
            'template': 'test',
            'elements': [
                {'id': 'elem_1', 'label_source': 'body_points[5]', 'x': 0.1, 'y': 0.2, 'w': 0.3, 'h': 0.4},
            ],
            'title_region': {'x': 0.05, 'y': 0.02, 'w': 0.90, 'h': 0.12},
        },
    }
    outline_slide = {'slide_number': 5, 'body_points': ['A', 'B']}
    findings = check_element_layout(strategy_entry, outline_slide)
    warnings = [f for f in findings if f['severity'] == 'warning']
    assert len(warnings) > 0


def test_ap28_low_vision_confidence():
    """Low confidence detected position should produce a warning."""
    from src.qa.checks.element_layout import check_vision_confidence
    image_entry = {
        'slide_number': 5,
        'detected_positions': [
            {'element_id': 'elem_1', 'x': 0.1, 'y': 0.2, 'w': 0.3, 'h': 0.4, 'confidence': 0.5},
            {'element_id': 'elem_2', 'x': 0.5, 'y': 0.2, 'w': 0.3, 'h': 0.4, 'confidence': 0.9},
        ],
    }
    findings = check_vision_confidence(image_entry)
    warnings = [f for f in findings if f['severity'] == 'warning']
    assert len(warnings) >= 1  # elem_1 is below 0.7 threshold


def test_ap28_all_high_confidence():
    """All high-confidence detections should produce no findings."""
    from src.qa.checks.element_layout import check_vision_confidence
    image_entry = {
        'slide_number': 5,
        'detected_positions': [
            {'element_id': 'elem_1', 'x': 0.1, 'y': 0.2, 'w': 0.3, 'h': 0.4, 'confidence': 0.92},
        ],
    }
    findings = check_vision_confidence(image_entry)
    assert len(findings) == 0
```

- [ ] **Step 2: Run to verify fail**

Run: `source .venv/bin/activate && pytest tests/test_qa_element_layout.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement the checks**

Create `src/qa/checks/element_layout.py`:

```python
"""AP-27: Element layout validation and AP-28: Vision confidence checks."""

_VISION_CONFIDENCE_THRESHOLD = 0.7
_MAX_ELEMENTS = 5


def check_element_layout(strategy_entry, outline_slide):
    """AP-27: Validate element layout for backdrop and pragmatic_composition slides.

    Args:
        strategy_entry: Dict from StrategyMap.slides with element_layout.
        outline_slide: Dict from SlideOutline.slides (for body_points reference).

    Returns:
        list of finding dicts.
    """
    findings = []
    slide_number = strategy_entry.get('slide_number', 0)
    layout = strategy_entry.get('element_layout')
    if not layout:
        return findings

    elements = layout.get('elements', [])
    body_points = outline_slide.get('body_points', [])

    # Check element count
    if len(elements) > _MAX_ELEMENTS:
        findings.append({
            'slide_number': slide_number,
            'severity': 'error',
            'category': 'element_layout',
            'description': f'Element count {len(elements)} exceeds maximum of {_MAX_ELEMENTS}',
            'suggested_fix': f'Reduce to {_MAX_ELEMENTS} or fewer elements, or use background strategy.',
            'affected_element': 'element_layout',
            'auto_fixable': False,
        })

    # Check each element
    for elem in elements:
        eid = elem.get('id', 'unknown')
        x, y, w, h = elem.get('x', 0), elem.get('y', 0), elem.get('w', 0), elem.get('h', 0)

        # Bounds check (x+w and y+h must be <= 1.0)
        if x + w > 1.0 or y + h > 1.0 or x < 0 or y < 0:
            findings.append({
                'slide_number': slide_number,
                'severity': 'error',
                'category': 'element_layout',
                'description': f'Element {eid} extends outside slide bounds (x={x}, y={y}, w={w}, h={h})',
                'suggested_fix': 'Adjust element coordinates to stay within 0.0-1.0 range.',
                'affected_element': eid,
                'auto_fixable': False,
            })

        # Check label_source reference
        label_source = elem.get('label_source', '')
        match = None
        try:
            if 'body_points[' in label_source:
                idx = int(label_source.split('[')[1].rstrip(']'))
                if idx >= len(body_points):
                    findings.append({
                        'slide_number': slide_number,
                        'severity': 'warning',
                        'category': 'element_layout',
                        'description': f'Element {eid} label_source {label_source} references nonexistent body_point (only {len(body_points)} exist)',
                        'suggested_fix': 'Update label_source to reference an existing body_point index.',
                        'affected_element': eid,
                        'auto_fixable': False,
                    })
        except (ValueError, IndexError):
            pass

    return findings


def check_vision_confidence(image_entry):
    """AP-28: Check vision detection confidence for backdrop slides.

    Args:
        image_entry: Dict from ImageManifest.images with detected_positions.

    Returns:
        list of finding dicts.
    """
    findings = []
    slide_number = image_entry.get('slide_number', 0)
    detected = image_entry.get('detected_positions', [])

    for pos in detected:
        confidence = pos.get('confidence', 0)
        eid = pos.get('element_id', 'unknown')
        if confidence < _VISION_CONFIDENCE_THRESHOLD:
            findings.append({
                'slide_number': slide_number,
                'severity': 'warning',
                'category': 'vision_confidence',
                'description': f'Element {eid} detected with low confidence {confidence:.2f} (threshold {_VISION_CONFIDENCE_THRESHOLD})',
                'suggested_fix': 'Re-generate the image or use prescribed fallback positions.',
                'affected_element': eid,
                'auto_fixable': False,
            })

    return findings
```

- [ ] **Step 4: Run tests**

Run: `source .venv/bin/activate && pytest tests/test_qa_element_layout.py -v`
Expected: 6 PASS

- [ ] **Step 5: Wire into run_qa.py**

In `src/qa/run_qa.py`, add import and invocation. After the per-slide loop (around line 98), add:

```python
    # Step 1b: Element layout checks (AP-27, AP-28)
    from src.qa.checks.element_layout import check_element_layout, check_vision_confidence

    if os.path.exists(strategy_map_path):
        with open(strategy_map_path) as f:
            strategy_map_data = json.load(f)
        outline_path = os.path.join(deck_dir, 'outline.json')
        with open(outline_path) as f:
            outline_data = json.load(f)
        outline_slides = {s['slide_number']: s for s in outline_data.get('slides', [])}

        for entry in strategy_map_data.get('slides', []):
            if entry.get('strategy') in ('backdrop', 'pragmatic_composition') or \
               entry.get('speaker_override') in ('backdrop', 'pragmatic_composition'):
                outline_slide = outline_slides.get(entry['slide_number'], {})
                findings.extend(check_element_layout(entry, outline_slide))

    # AP-28: Check vision confidence on image manifest
    im_path = os.path.join(deck_dir, 'image-manifest.json')
    if os.path.exists(im_path):
        with open(im_path) as f:
            im_data = json.load(f)
        for img in im_data.get('images', []):
            if img.get('detected_positions'):
                findings.extend(check_vision_confidence(img))
```

- [ ] **Step 6: Run full suite**

Run: `source .venv/bin/activate && pytest -x -q`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add src/qa/checks/element_layout.py src/qa/run_qa.py tests/test_qa_element_layout.py
git commit -m "feat: AP-27 element layout validation and AP-28 vision confidence QA checks"
```

---

### Task 14: Integration Tests (Tagged, Require Ollama)

**Files:**
- Create: `tests/test_integration_rendering.py`

- [ ] **Step 1: Write tagged integration tests**

Create `tests/test_integration_rendering.py`:

```python
"""Integration tests for new rendering strategies. Require Ollama running.

Run with: pytest tests/test_integration_rendering.py -m ollama -v
Skip in CI with: pytest -m "not ollama"
"""

import json
import os
import shutil
import subprocess
import tempfile

import pytest
import requests

# Mark all tests in this module as requiring Ollama
pytestmark = pytest.mark.ollama


def ollama_available():
    try:
        resp = requests.get('http://localhost:11434/api/tags', timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


@pytest.fixture(autouse=True)
def skip_without_ollama():
    if not ollama_available():
        pytest.skip('Ollama not running')


@pytest.fixture
def integration_deck_dir():
    d = tempfile.mkdtemp(prefix='jtd-render-test-')
    # Copy minimal deck fixture
    fixture_dir = os.path.join(os.path.dirname(__file__), 'fixtures', 'minimal_deck')
    for fname in os.listdir(fixture_dir):
        src = os.path.join(fixture_dir, fname)
        dst = os.path.join(d, fname)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
    os.makedirs(os.path.join(d, 'output'), exist_ok=True)
    yield d
    shutil.rmtree(d)


def generate_test_image(prompt, output_path, w=512, h=288):
    """Generate a small test image via Ollama."""
    import base64
    resp = requests.post('http://localhost:11434/api/generate', json={
        'model': 'x/z-image-turbo:fp8',
        'prompt': prompt,
        'stream': False,
        'width': w,
        'height': h,
        'steps': 4,
    }, timeout=120)
    if resp.status_code == 200:
        data = resp.json()
        img_b64 = data.get('image')
        if img_b64:
            with open(output_path, 'wb') as f:
                f.write(base64.b64decode(img_b64))
            return True
    return False


def test_background_variant_full_pipeline(integration_deck_dir):
    """Generate background image + assemble with bottom_bar variant."""
    img_path = os.path.join(integration_deck_dir, 'images', 'slide-02-hero.png')
    assert generate_test_image('abstract teal geometric shapes', img_path)

    # Set up strategy map with background strategy
    sm = {
        'created_at': '2026-03-30T00:00:00Z', 'approval_mode': 'review',
        'slides': [
            {'slide_number': 1, 'strategy': 'full_render', 'rationale': '', 'render_funnel': ['ollama'], 'speaker_override': None},
            {'slide_number': 2, 'strategy': 'background', 'rationale': '', 'render_funnel': ['ollama'], 'speaker_override': None, 'backdrop_variant': 'bottom_bar'},
            {'slide_number': 3, 'strategy': 'composed', 'rationale': '', 'render_funnel': ['ollama'], 'speaker_override': None},
        ],
    }
    with open(os.path.join(integration_deck_dir, 'strategy-map.json'), 'w') as f:
        json.dump(sm, f)

    # Update image manifest
    im = {
        'images': [
            {'image_id': 'slide-01-hero', 'slide_number': 1, 'file_path': img_path, 'status': 'generated'},
            {'image_id': 'slide-02-hero', 'slide_number': 2, 'file_path': img_path, 'status': 'generated'},
        ],
    }
    with open(os.path.join(integration_deck_dir, 'image-manifest.json'), 'w') as f:
        json.dump(im, f)

    result = subprocess.run(
        ['node', 'src/assembler/build_deck.js', '--deck-dir', integration_deck_dir],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"Assembly failed: {result.stderr}"
    assert os.path.exists(os.path.join(integration_deck_dir, 'output', 'presentation.pptx'))


def test_pragmatic_composition_full_pipeline(integration_deck_dir):
    """Generate bg + 2 elements + assemble with pragmatic_composition."""
    img_dir = os.path.join(integration_deck_dir, 'images')
    bg_path = os.path.join(img_dir, 'slide-02-bg.png')
    e1_path = os.path.join(img_dir, 'slide-02-elem-1.png')
    e2_path = os.path.join(img_dir, 'slide-02-elem-2.png')

    assert generate_test_image('subtle teal gradient background', bg_path)
    assert generate_test_image('flat illustration of a laptop computer', e1_path)
    assert generate_test_image('flat illustration of a server rack', e2_path)

    sm = {
        'created_at': '2026-03-30T00:00:00Z', 'approval_mode': 'review',
        'slides': [
            {'slide_number': 1, 'strategy': 'full_render', 'rationale': '', 'render_funnel': ['ollama'], 'speaker_override': None},
            {'slide_number': 2, 'strategy': 'pragmatic_composition', 'rationale': '', 'render_funnel': ['ollama'], 'speaker_override': None,
             'element_layout': {
                 'template': 'two_column',
                 'elements': [
                     {'id': 'elem_1', 'label_source': 'body_points[0]', 'x': 0.05, 'y': 0.22, 'w': 0.42, 'h': 0.55},
                     {'id': 'elem_2', 'label_source': 'body_points[1]', 'x': 0.55, 'y': 0.22, 'w': 0.42, 'h': 0.55},
                 ],
                 'title_region': {'x': 0.05, 'y': 0.03, 'w': 0.90, 'h': 0.12},
             }},
            {'slide_number': 3, 'strategy': 'composed', 'rationale': '', 'render_funnel': ['ollama'], 'speaker_override': None},
        ],
    }
    with open(os.path.join(integration_deck_dir, 'strategy-map.json'), 'w') as f:
        json.dump(sm, f)

    im = {
        'images': [
            {'image_id': 'slide-01-hero', 'slide_number': 1, 'file_path': bg_path, 'status': 'generated'},
            {'image_id': 'slide-02-bg', 'slide_number': 2, 'file_path': bg_path, 'status': 'generated', 'placement_zone': 'background'},
            {'image_id': 'slide-02-elem-1', 'slide_number': 2, 'file_path': e1_path, 'status': 'generated', 'placement_zone': 'element', 'element_id': 'elem_1'},
            {'image_id': 'slide-02-elem-2', 'slide_number': 2, 'file_path': e2_path, 'status': 'generated', 'placement_zone': 'element', 'element_id': 'elem_2'},
        ],
    }
    with open(os.path.join(integration_deck_dir, 'image-manifest.json'), 'w') as f:
        json.dump(im, f)

    result = subprocess.run(
        ['node', 'src/assembler/build_deck.js', '--deck-dir', integration_deck_dir],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"Assembly failed: {result.stderr}"
```

- [ ] **Step 2: Add pytest marker configuration**

Add to `pyproject.toml` (or `pytest.ini`) if not already present:

```ini
[tool.pytest.ini_options]
markers = [
    "ollama: requires Ollama running locally",
]
```

- [ ] **Step 3: Run integration tests (requires Ollama)**

Run: `source .venv/bin/activate && pytest tests/test_integration_rendering.py -m ollama -v`
Expected: PASS (if Ollama running), SKIP (if not)

- [ ] **Step 4: Verify unit tests still pass without Ollama marker**

Run: `source .venv/bin/activate && pytest -m "not ollama" -x -q`
Expected: All non-Ollama tests pass

- [ ] **Step 5: Commit**

```bash
git add tests/test_integration_rendering.py pyproject.toml
git commit -m "feat: tagged integration tests for background and pragmatic_composition rendering"
```

---

## Summary

| Phase | Tasks | New Tests (est.) |
|-------|-------|-----------------|
| Phase 1: Foundation | Tasks 1-7 | ~18 |
| Phase 2: backGROUND | Task 8 | ~4 |
| Phase 3: Pragmatic Composition | Tasks 9-10 | ~6 |
| Phase 4: backDROP | Tasks 11-13 | ~10 |
| Integration | Task 14 | ~3 |
| **Total** | **14 tasks** | **~41 unit + ~3 integration** |
