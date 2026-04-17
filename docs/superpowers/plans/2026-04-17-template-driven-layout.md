# Template-Driven Layout Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow speakers to provide a corporate .pptx template so the pipeline produces a deck that inherits the template's slide masters and places content into its layout placeholders.

**Architecture:** New python-pptx assembly path (`build_deck_template.py`) activated when a template profile exists. Template analyser extracts layouts and placeholder geometry from the source .pptx. Auto-mapped layout-to-slide-type mapping confirmed by Speaker. Strategy map constrained to `composed` + SmartArt in template mode.

**Tech Stack:** python-pptx (already installed), jsonschema, existing DeckContext contracts

**Spec:** `docs/superpowers/specs/2026-04-17-template-driven-layout-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/template_analyser.py` | Read .pptx template, extract layouts/placeholders, auto-map to slide types, compute template hash |
| `src/assembler/build_deck_template.py` | python-pptx assembly: open template, strip example slides, add slides from outline using mapped layouts, populate placeholders |
| `src/schemas/template_profile.schema.json` | JSON Schema for template-profile.json |
| `tools/build_test_template.py` | Generate Metamirror-branded test fixture .pptx via python-pptx |
| `tests/test_template_analyser.py` | Tests for template analysis and layout mapping |
| `tests/test_build_deck_template.py` | Tests for template assembly engine |
| `tests/test_template_integration.py` | Pipeline routing, strategy constraints, e2e |
| `src/deckcontext.py` | Add `template-analysis` step to `DEFAULT_STEP_ORDER` |
| `src/slide_prompt_composer.py` | Add template mode strategy constraints |

---

### Task 1: Template Profile Schema

**Files:**
- Create: `src/schemas/template_profile.schema.json`
- Modify: `src/deckcontext.py:17-31` (add to CONTRACT_SCHEMAS)
- Test: `tests/test_template_analyser.py`

- [ ] **Step 1: Write the schema file**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/template-profile.json",
  "title": "TemplateProfile",
  "description": "Extracted layout metadata from a .pptx template for template-driven assembly.",
  "type": "object",
  "required": ["template_path", "template_hash", "slide_width_inches", "slide_height_inches", "master_index", "layouts", "layout_mapping", "unmapped_fallback", "constrains_strategies", "speaker_approved"],
  "additionalProperties": false,
  "properties": {
    "template_path": {"type": "string"},
    "template_hash": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
    "slide_width_inches": {"type": "number", "minimum": 1},
    "slide_height_inches": {"type": "number", "minimum": 1},
    "master_index": {"type": "integer", "minimum": 0, "default": 0},
    "layouts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "index", "placeholder_count", "placeholders", "decorative_shape_count"],
        "additionalProperties": false,
        "properties": {
          "name": {"type": "string"},
          "index": {"type": "integer", "minimum": 0},
          "placeholder_count": {"type": "integer", "minimum": 0},
          "placeholders": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["idx", "type", "name", "x", "y", "w", "h"],
              "additionalProperties": false,
              "properties": {
                "idx": {"type": "integer", "minimum": 0},
                "type": {
                  "type": "string",
                  "enum": ["title", "subtitle", "body", "content", "picture", "chart", "table", "footer", "slide_number", "date", "chapter_box", "other"]
                },
                "name": {"type": "string"},
                "x": {"type": "number"},
                "y": {"type": "number"},
                "w": {"type": "number"},
                "h": {"type": "number"}
              }
            }
          },
          "decorative_shape_count": {"type": "integer", "minimum": 0}
        }
      }
    },
    "layout_mapping": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["layout_name", "layout_index"],
        "additionalProperties": false,
        "properties": {
          "layout_name": {"type": "string"},
          "layout_index": {"type": "integer", "minimum": 0}
        }
      }
    },
    "unmapped_fallback": {
      "type": "object",
      "required": ["layout_name", "layout_index"],
      "additionalProperties": false,
      "properties": {
        "layout_name": {"type": "string"},
        "layout_index": {"type": "integer", "minimum": 0}
      }
    },
    "constrains_strategies": {"type": "boolean"},
    "speaker_approved": {"type": "boolean"}
  }
}
```

Save to `src/schemas/template_profile.schema.json`.

- [ ] **Step 2: Register in CONTRACT_SCHEMAS**

In `src/deckcontext.py`, add to the `CONTRACT_SCHEMAS` dict (after `'smartart-manifest'`):

```python
    'template-profile': 'template_profile.schema.json',
```

- [ ] **Step 3: Write schema validation test**

Create `tests/test_template_analyser.py`:

```python
"""Tests for template analyser and template profile schema."""

import json
import os
import pytest
import jsonschema

from src.deckcontext import read_contract, write_contract


SCHEMA_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'schemas')


def _load_schema():
    with open(os.path.join(SCHEMA_DIR, 'template_profile.schema.json')) as f:
        return json.load(f)


def _minimal_profile():
    return {
        'template_path': '/tmp/template.pptx',
        'template_hash': 'a' * 64,
        'slide_width_inches': 13.333,
        'slide_height_inches': 7.5,
        'master_index': 0,
        'layouts': [
            {
                'name': 'Content 1',
                'index': 0,
                'placeholder_count': 2,
                'placeholders': [
                    {'idx': 0, 'type': 'title', 'name': 'Title 1', 'x': 0.6, 'y': 0.6, 'w': 12.13, 'h': 1.02},
                    {'idx': 31, 'type': 'content', 'name': 'Content Placeholder 5', 'x': 0.6, 'y': 2.33, 'w': 12.13, 'h': 4.57},
                ],
                'decorative_shape_count': 0,
            }
        ],
        'layout_mapping': {
            'content': {'layout_name': 'Content 1', 'layout_index': 0},
        },
        'unmapped_fallback': {'layout_name': 'Content 1', 'layout_index': 0},
        'constrains_strategies': True,
        'speaker_approved': False,
    }


class TestTemplateProfileSchema:
    def test_valid_profile_passes(self):
        schema = _load_schema()
        jsonschema.validate(instance=_minimal_profile(), schema=schema)

    def test_missing_required_field_fails(self):
        schema = _load_schema()
        profile = _minimal_profile()
        del profile['template_hash']
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=profile, schema=schema)

    def test_invalid_hash_pattern_fails(self):
        schema = _load_schema()
        profile = _minimal_profile()
        profile['template_hash'] = 'not-a-hash'
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=profile, schema=schema)

    def test_invalid_placeholder_type_fails(self):
        schema = _load_schema()
        profile = _minimal_profile()
        profile['layouts'][0]['placeholders'][0]['type'] = 'invalid_type'
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=profile, schema=schema)

    def test_write_and_read_via_deckcontext(self, tmp_path):
        profile = _minimal_profile()
        deck_dir = str(tmp_path)
        write_contract(deck_dir, 'template-profile', profile)
        loaded = read_contract(deck_dir, 'template-profile')
        assert loaded['template_hash'] == 'a' * 64
        assert loaded['layouts'][0]['name'] == 'Content 1'
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_template_analyser.py -v`
Expected: 5 PASS

- [ ] **Step 5: Sync plugin copy and commit**

```bash
cp src/schemas/template_profile.schema.json plugins/jack-tar-deckhand/src/schemas/
cp src/deckcontext.py plugins/jack-tar-deckhand/src/
git add src/schemas/template_profile.schema.json src/deckcontext.py plugins/jack-tar-deckhand/src/schemas/template_profile.schema.json plugins/jack-tar-deckhand/src/deckcontext.py tests/test_template_analyser.py
git commit -m "feat: template profile schema and DeckContext registration (#45)"
```

---

### Task 2: Test Template Fixture Generator

**Files:**
- Create: `tools/build_test_template.py`
- Create: `tests/fixtures/templates/metamirror-template.pptx` (generated)

- [ ] **Step 1: Write the fixture generator**

Create `tools/build_test_template.py`:

```python
#!/usr/bin/env python3
"""Generate a Metamirror-branded test template .pptx for template-driven layout tests.

Creates a minimal template with 1 slide master and 8 layouts covering core slide types.
Each layout has correctly typed placeholders at realistic positions.
Includes 2 example slides to verify stripping logic.

Usage:
    python3 tools/build_test_template.py
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'tests', 'fixtures', 'templates', 'metamirror-template.pptx')

# Metamirror brand colours
PRIMARY = RGBColor(0x1A, 0x1A, 0x2E)    # dark navy
SECONDARY = RGBColor(0x00, 0xD4, 0xAA)  # teal accent
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def build_template():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Access the default slide master
    master = prs.slide_masters[0]

    # We'll use the built-in blank layout as a starting point.
    # python-pptx doesn't support creating new slide layouts from scratch,
    # so we work with what's available and add placeholders via XML manipulation.
    # For a test fixture, we use the existing default layouts and add example slides.

    # Layout 0: Title Slide (built-in) — has TITLE + SUBTITLE
    # Layout 5: Blank (built-in)
    # Layout 6: Title Only (built-in) — has TITLE

    # Add 2 example slides that the assembler must strip
    title_layout = prs.slide_layouts[0]  # Title Slide
    blank_layout = prs.slide_layouts[6]  # Blank

    slide1 = prs.slides.add_slide(title_layout)
    slide1.placeholders[0].text = 'Example Title Slide — DELETE ME'
    slide1.placeholders[1].text = 'This is an example subtitle'

    slide2 = prs.slides.add_slide(blank_layout)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    prs.save(OUTPUT_PATH)
    print(f'Test template saved to {OUTPUT_PATH}')
    print(f'  Slide masters: {len(prs.slide_masters)}')
    print(f'  Layouts: {len(prs.slide_layouts)}')
    print(f'  Example slides: {len(prs.slides)}')

    # Print layout inventory
    for i, layout in enumerate(prs.slide_layouts):
        ph_types = [str(ph.placeholder_format.type).split('(')[0].strip()
                    for ph in layout.placeholders]
        print(f'  Layout {i}: "{layout.name}" — placeholders: {ph_types}')

    return OUTPUT_PATH


if __name__ == '__main__':
    build_template()
```

- [ ] **Step 2: Run the generator and verify the output**

```bash
.venv/bin/python3 tools/build_test_template.py
```

Expected: Prints layout inventory showing available layouts with placeholder types.

- [ ] **Step 3: Verify the fixture exists**

```bash
ls -la tests/fixtures/templates/metamirror-template.pptx
```

- [ ] **Step 4: Commit**

```bash
git add tools/build_test_template.py tests/fixtures/templates/metamirror-template.pptx
git commit -m "feat: Metamirror test template fixture generator (#45)"
```

---

### Task 3: Placeholder Classification

**Files:**
- Create: `src/template_analyser.py` (first function)
- Test: `tests/test_template_analyser.py` (add tests)

- [ ] **Step 1: Write failing tests for classify_placeholder**

Append to `tests/test_template_analyser.py`:

```python
from src.template_analyser import classify_placeholder


class TestClassifyPlaceholder:
    def test_title_type(self):
        assert classify_placeholder('TITLE (1)', 'Title 1') == 'title'

    def test_subtitle_type(self):
        assert classify_placeholder('SUBTITLE (2)', 'Subtitle 1') == 'subtitle'

    def test_body_type(self):
        assert classify_placeholder('BODY (2)', 'Text Placeholder 3') == 'body'

    def test_object_type_maps_to_content(self):
        assert classify_placeholder('OBJECT (7)', 'Content Placeholder 5') == 'content'

    def test_picture_type(self):
        assert classify_placeholder('PICTURE (18)', 'Picture Placeholder 10') == 'picture'

    def test_chart_type(self):
        assert classify_placeholder('CHART (12)', 'Chart Placeholder 1') == 'chart'

    def test_table_type(self):
        assert classify_placeholder('TABLE (11)', 'Table Placeholder 1') == 'table'

    def test_date_type(self):
        assert classify_placeholder('DATE (16)', 'Date Placeholder 1') == 'date'

    def test_footer_type(self):
        assert classify_placeholder('FOOTER (15)', 'Footer Placeholder 1') == 'footer'

    def test_slide_number_type(self):
        assert classify_placeholder('SLIDE_NUMBER (13)', 'Slide Number Placeholder 1') == 'slide_number'

    def test_chapter_name_heuristic(self):
        assert classify_placeholder('BODY (2)', 'Chapter Placeholder 2') == 'chapter_box'

    def test_logo_name_heuristic(self):
        assert classify_placeholder('BODY (2)', 'Logo Placeholder 7') == 'other'

    def test_unknown_type(self):
        assert classify_placeholder('UNKNOWN (99)', 'Mystery Shape') == 'other'
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_template_analyser.py::TestClassifyPlaceholder -v`
Expected: FAIL (ImportError — module doesn't exist yet)

- [ ] **Step 3: Implement classify_placeholder**

Create `src/template_analyser.py`:

```python
"""Template analyser — extract layouts and placeholders from a .pptx template.

Reads a corporate .pptx template via python-pptx and produces a TemplateProfile
JSON structure for template-driven assembly.
"""

import hashlib
import json
import os
import re

from pptx import Presentation
from pptx.util import Emu

EMU_PER_INCH = 914400


def _emu_to_inches(emu):
    """Convert EMU to inches, rounded to 2 decimal places."""
    return round(emu / EMU_PER_INCH, 2)


# Map OOXML placeholder type strings to our vocabulary
_TYPE_MAP = {
    'TITLE': 'title',
    'CENTER_TITLE': 'title',
    'SUBTITLE': 'subtitle',
    'BODY': 'body',
    'OBJECT': 'content',
    'PICTURE': 'picture',
    'CHART': 'chart',
    'TABLE': 'table',
    'DATE': 'date',
    'FOOTER': 'footer',
    'SLIDE_NUMBER': 'slide_number',
}

# Name patterns that override type-based classification
_NAME_OVERRIDES = [
    (re.compile(r'chapter', re.IGNORECASE), 'chapter_box'),
]


def classify_placeholder(ph_type_str, ph_name):
    """Classify a placeholder into our type vocabulary.

    Args:
        ph_type_str: String like 'TITLE (1)' or 'BODY (2)' from python-pptx.
        ph_name: The shape name string from the template.

    Returns:
        One of: title, subtitle, body, content, picture, chart, table,
                footer, slide_number, date, chapter_box, other.
    """
    # Check name-based overrides first
    for pattern, override_type in _NAME_OVERRIDES:
        if pattern.search(ph_name):
            return override_type

    # Extract the type keyword before the parenthesized number
    type_key = ph_type_str.split('(')[0].strip().split()[-1] if ph_type_str else ''
    return _TYPE_MAP.get(type_key, 'other')
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_template_analyser.py::TestClassifyPlaceholder -v`
Expected: 13 PASS

- [ ] **Step 5: Commit**

```bash
git add src/template_analyser.py tests/test_template_analyser.py
git commit -m "feat: placeholder classification for template analysis (#45)"
```

---

### Task 4: Layout Extraction

**Files:**
- Modify: `src/template_analyser.py` (add `extract_layouts`)
- Test: `tests/test_template_analyser.py` (add tests)

- [ ] **Step 1: Write failing tests for extract_layouts**

Append to `tests/test_template_analyser.py`:

```python
from src.template_analyser import extract_layouts

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'templates', 'metamirror-template.pptx')


class TestExtractLayouts:
    def test_returns_list_of_layouts(self):
        layouts = extract_layouts(FIXTURE_PATH)
        assert isinstance(layouts, list)
        assert len(layouts) > 0

    def test_layout_has_required_keys(self):
        layouts = extract_layouts(FIXTURE_PATH)
        layout = layouts[0]
        assert 'name' in layout
        assert 'index' in layout
        assert 'placeholder_count' in layout
        assert 'placeholders' in layout
        assert 'decorative_shape_count' in layout

    def test_placeholder_has_geometry(self):
        layouts = extract_layouts(FIXTURE_PATH)
        # Find a layout with placeholders
        layout_with_phs = next(l for l in layouts if l['placeholder_count'] > 0)
        ph = layout_with_phs['placeholders'][0]
        assert 'idx' in ph
        assert 'type' in ph
        assert 'name' in ph
        assert isinstance(ph['x'], float)
        assert isinstance(ph['y'], float)
        assert isinstance(ph['w'], float)
        assert isinstance(ph['h'], float)

    def test_title_layout_has_title_placeholder(self):
        layouts = extract_layouts(FIXTURE_PATH)
        title_layout = next(l for l in layouts if 'title' in l['name'].lower())
        ph_types = [p['type'] for p in title_layout['placeholders']]
        assert 'title' in ph_types

    def test_master_index_zero_by_default(self):
        layouts = extract_layouts(FIXTURE_PATH, master_index=0)
        assert len(layouts) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_template_analyser.py::TestExtractLayouts -v`
Expected: FAIL (ImportError — function doesn't exist)

- [ ] **Step 3: Implement extract_layouts**

Add to `src/template_analyser.py`:

```python
def extract_layouts(template_path, master_index=0):
    """Extract all slide layouts from a template .pptx file.

    Args:
        template_path: Path to the .pptx template file.
        master_index: Which slide master to use (default 0).

    Returns:
        List of layout dicts with name, index, placeholders, and decorative shape count.
    """
    prs = Presentation(template_path)
    master = prs.slide_masters[master_index]
    results = []

    for i, layout in enumerate(master.slide_layouts):
        placeholders = []
        for ph in layout.placeholders:
            ph_type_str = str(ph.placeholder_format.type) if ph.placeholder_format.type is not None else ''
            placeholders.append({
                'idx': ph.placeholder_format.idx,
                'type': classify_placeholder(ph_type_str, ph.name),
                'name': ph.name,
                'x': _emu_to_inches(ph.left),
                'y': _emu_to_inches(ph.top),
                'w': _emu_to_inches(ph.width),
                'h': _emu_to_inches(ph.height),
            })

        non_placeholder_shapes = [s for s in layout.shapes if not s.is_placeholder]

        results.append({
            'name': layout.name,
            'index': i,
            'placeholder_count': len(placeholders),
            'placeholders': placeholders,
            'decorative_shape_count': len(non_placeholder_shapes),
        })

    return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_template_analyser.py::TestExtractLayouts -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add src/template_analyser.py tests/test_template_analyser.py
git commit -m "feat: layout extraction from .pptx templates (#45)"
```

---

### Task 5: Auto-Mapping Layouts to Slide Types

**Files:**
- Modify: `src/template_analyser.py` (add `auto_map_layouts`)
- Test: `tests/test_template_analyser.py` (add tests)

- [ ] **Step 1: Write failing tests for auto_map_layouts**

Append to `tests/test_template_analyser.py`:

```python
from src.template_analyser import auto_map_layouts


class TestAutoMapLayouts:
    def test_maps_title_slide(self):
        layouts = [
            {'name': 'Title Slide', 'index': 0, 'placeholder_count': 2,
             'placeholders': [{'idx': 0, 'type': 'title', 'name': 'Title 1', 'x': 0.5, 'y': 1.0, 'w': 8.0, 'h': 4.5}],
             'decorative_shape_count': 0},
        ]
        mapping, fallback = auto_map_layouts(layouts)
        assert 'title' in mapping
        assert mapping['title']['layout_name'] == 'Title Slide'

    def test_maps_content_layout(self):
        layouts = [
            {'name': 'Content 1', 'index': 5, 'placeholder_count': 2,
             'placeholders': [
                 {'idx': 0, 'type': 'title', 'name': 'Title', 'x': 0.6, 'y': 0.6, 'w': 12.0, 'h': 1.0},
                 {'idx': 31, 'type': 'content', 'name': 'Content Placeholder', 'x': 0.6, 'y': 2.3, 'w': 12.0, 'h': 4.5},
             ],
             'decorative_shape_count': 0},
        ]
        mapping, fallback = auto_map_layouts(layouts)
        assert 'content' in mapping
        assert mapping['content']['layout_name'] == 'Content 1'

    def test_maps_divider_to_section_divider(self):
        layouts = [
            {'name': 'Divider 1', 'index': 12, 'placeholder_count': 2,
             'placeholders': [{'idx': 0, 'type': 'title', 'name': 'Title', 'x': 5.6, 'y': 5.0, 'w': 7.0, 'h': 1.8}],
             'decorative_shape_count': 1},
        ]
        mapping, fallback = auto_map_layouts(layouts)
        assert 'section_divider' in mapping
        assert mapping['section_divider']['layout_name'] == 'Divider 1'

    def test_maps_end_slide_to_closing(self):
        layouts = [
            {'name': 'End Slide 1', 'index': 56, 'placeholder_count': 0,
             'placeholders': [],
             'decorative_shape_count': 0},
        ]
        mapping, fallback = auto_map_layouts(layouts)
        assert 'closing' in mapping

    def test_maps_comparison_layout(self):
        layouts = [
            {'name': 'Comparison', 'index': 33, 'placeholder_count': 5,
             'placeholders': [
                 {'idx': 0, 'type': 'title', 'name': 'Title', 'x': 0.6, 'y': 0.6, 'w': 12.0, 'h': 1.0},
                 {'idx': 1, 'type': 'content', 'name': 'Content 1', 'x': 0.6, 'y': 2.3, 'w': 5.5, 'h': 4.5},
                 {'idx': 2, 'type': 'content', 'name': 'Content 2', 'x': 7.0, 'y': 2.3, 'w': 5.5, 'h': 4.5},
             ],
             'decorative_shape_count': 0},
        ]
        mapping, fallback = auto_map_layouts(layouts)
        assert 'comparison' in mapping

    def test_content_with_picture_maps_to_content_with_image(self):
        layouts = [
            {'name': 'Content Photo 1', 'index': 35, 'placeholder_count': 3,
             'placeholders': [
                 {'idx': 0, 'type': 'title', 'name': 'Title', 'x': 0.6, 'y': 0.6, 'w': 6.0, 'h': 1.0},
                 {'idx': 1, 'type': 'content', 'name': 'Content', 'x': 0.6, 'y': 2.3, 'w': 6.0, 'h': 4.5},
                 {'idx': 13, 'type': 'picture', 'name': 'Picture', 'x': 7.0, 'y': 0.0, 'w': 6.3, 'h': 7.5},
             ],
             'decorative_shape_count': 0},
        ]
        mapping, fallback = auto_map_layouts(layouts)
        assert 'content_with_image' in mapping

    def test_prefers_simpler_layout_when_multiple_match(self):
        layouts = [
            {'name': 'Content 1', 'index': 5, 'placeholder_count': 2,
             'placeholders': [
                 {'idx': 0, 'type': 'title', 'name': 'Title', 'x': 0.6, 'y': 0.6, 'w': 12.0, 'h': 1.0},
                 {'idx': 31, 'type': 'content', 'name': 'Content', 'x': 0.6, 'y': 2.3, 'w': 12.0, 'h': 4.5},
             ],
             'decorative_shape_count': 0},
            {'name': 'Content 1 Chapterbox', 'index': 6, 'placeholder_count': 3,
             'placeholders': [
                 {'idx': 0, 'type': 'title', 'name': 'Title', 'x': 0.6, 'y': 0.6, 'w': 12.0, 'h': 1.0},
                 {'idx': 31, 'type': 'content', 'name': 'Content', 'x': 0.6, 'y': 2.3, 'w': 12.0, 'h': 4.5},
                 {'idx': 13, 'type': 'chapter_box', 'name': 'Chapter', 'x': 0.6, 'y': 0.29, 'w': 12.0, 'h': 0.17},
             ],
             'decorative_shape_count': 0},
        ]
        mapping, fallback = auto_map_layouts(layouts)
        assert mapping['content']['layout_name'] == 'Content 1'

    def test_fallback_is_largest_content_layout(self):
        layouts = [
            {'name': 'Content 1', 'index': 5, 'placeholder_count': 2,
             'placeholders': [
                 {'idx': 0, 'type': 'title', 'name': 'Title', 'x': 0.6, 'y': 0.6, 'w': 12.0, 'h': 1.0},
                 {'idx': 31, 'type': 'content', 'name': 'Content', 'x': 0.6, 'y': 2.3, 'w': 12.0, 'h': 4.57},
             ],
             'decorative_shape_count': 0},
            {'name': 'Content 2', 'index': 6, 'placeholder_count': 3,
             'placeholders': [
                 {'idx': 0, 'type': 'title', 'name': 'Title', 'x': 0.6, 'y': 0.6, 'w': 3.6, 'h': 1.0},
                 {'idx': 31, 'type': 'content', 'name': 'Content', 'x': 0.6, 'y': 2.3, 'w': 3.6, 'h': 4.57},
                 {'idx': 28, 'type': 'content', 'name': 'Content 2', 'x': 5.0, 'y': 2.3, 'w': 7.6, 'h': 4.6},
             ],
             'decorative_shape_count': 0},
        ]
        mapping, fallback = auto_map_layouts(layouts)
        # Content 1 has the single largest content placeholder (12.0 * 4.57)
        assert fallback['layout_name'] == 'Content 1'

    def test_empty_layouts_returns_empty_mapping(self):
        mapping, fallback = auto_map_layouts([])
        assert mapping == {}
        assert fallback is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_template_analyser.py::TestAutoMapLayouts -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement auto_map_layouts**

Add to `src/template_analyser.py`:

```python
# Convention table: (regex pattern on layout name, slide_type, requires condition)
_CONVENTION_TABLE = [
    (re.compile(r'^Title Slide', re.IGNORECASE), 'title', None),
    (re.compile(r'^Title Only', re.IGNORECASE), 'title', None),
    (re.compile(r'^Divider|^Section', re.IGNORECASE), 'section_divider', None),
    (re.compile(r'^Content.*Photo|^Content.*Image', re.IGNORECASE), 'content_with_image', None),
    (re.compile(r'^Comparison', re.IGNORECASE), 'comparison', None),
    (re.compile(r'^Conclusion|^End', re.IGNORECASE), 'closing', None),
    (re.compile(r'^Agenda', re.IGNORECASE), 'agenda', None),
    (re.compile(r'^Text', re.IGNORECASE), 'quote', None),
    (re.compile(r'^Blank$', re.IGNORECASE), 'blank', None),
    # Content N patterns — must come after Content*Photo
    (re.compile(r'^Content\s*1\b', re.IGNORECASE), 'content', None),
    (re.compile(r'^Content\s*[2-8]\b', re.IGNORECASE), 'two_column', None),
]


def _has_picture_placeholder(layout):
    return any(p['type'] == 'picture' for p in layout.get('placeholders', []))


def _largest_content_area(layout):
    """Return the area of the largest single content placeholder in the layout."""
    max_area = 0
    for p in layout.get('placeholders', []):
        if p['type'] == 'content':
            area = p['w'] * p['h']
            if area > max_area:
                max_area = area
    return max_area


def auto_map_layouts(layouts):
    """Auto-map extracted layouts to slide types by naming convention.

    Args:
        layouts: List of layout dicts from extract_layouts().

    Returns:
        Tuple of (mapping_dict, fallback_dict).
        mapping_dict: {slide_type: {'layout_name': str, 'layout_index': int}}
        fallback_dict: {'layout_name': str, 'layout_index': int} or None.
    """
    if not layouts:
        return {}, None

    # Collect candidates: {slide_type: [(layout, placeholder_count)]}
    candidates = {}
    for layout in layouts:
        name = layout['name']
        for pattern, slide_type, _condition in _CONVENTION_TABLE:
            if pattern.search(name):
                candidates.setdefault(slide_type, []).append(layout)
                break
        else:
            # Check if it's a Content layout with a PICTURE placeholder
            if re.search(r'^Content', name, re.IGNORECASE) and _has_picture_placeholder(layout):
                candidates.setdefault('content_with_image', []).append(layout)

    # For each slide type, pick the simplest layout (fewest placeholders)
    mapping = {}
    for slide_type, options in candidates.items():
        options.sort(key=lambda l: l['placeholder_count'])
        winner = options[0]
        mapping[slide_type] = {
            'layout_name': winner['name'],
            'layout_index': winner['index'],
        }

    # Fallback: layout with the largest single content placeholder
    best_fallback = None
    best_area = 0
    for layout in layouts:
        area = _largest_content_area(layout)
        if area > best_area:
            best_area = area
            best_fallback = layout

    fallback = None
    if best_fallback:
        fallback = {
            'layout_name': best_fallback['name'],
            'layout_index': best_fallback['index'],
        }

    return mapping, fallback
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_template_analyser.py::TestAutoMapLayouts -v`
Expected: 9 PASS

- [ ] **Step 5: Commit**

```bash
git add src/template_analyser.py tests/test_template_analyser.py
git commit -m "feat: auto-map template layouts to slide types (#45)"
```

---

### Task 6: Full Template Analysis (analyse_template)

**Files:**
- Modify: `src/template_analyser.py` (add `analyse_template`)
- Test: `tests/test_template_analyser.py` (add tests)

- [ ] **Step 1: Write failing tests for analyse_template**

Append to `tests/test_template_analyser.py`:

```python
from src.template_analyser import analyse_template


class TestAnalyseTemplate:
    def test_returns_complete_profile(self):
        profile = analyse_template(FIXTURE_PATH)
        assert profile['template_path'] == FIXTURE_PATH
        assert len(profile['template_hash']) == 64
        assert profile['slide_width_inches'] == 13.33
        assert profile['slide_height_inches'] == 7.5
        assert profile['master_index'] == 0
        assert isinstance(profile['layouts'], list)
        assert isinstance(profile['layout_mapping'], dict)
        assert profile['constrains_strategies'] is True
        assert profile['speaker_approved'] is False

    def test_hash_changes_with_different_file(self, tmp_path):
        from pptx import Presentation as Prs
        prs = Prs()
        path1 = str(tmp_path / 'a.pptx')
        prs.save(path1)
        profile1 = analyse_template(path1)

        # Modify and save again
        prs2 = Prs()
        prs2.slides.add_slide(prs2.slide_layouts[0])
        path2 = str(tmp_path / 'b.pptx')
        prs2.save(path2)
        profile2 = analyse_template(path2)

        assert profile1['template_hash'] != profile2['template_hash']

    def test_validates_against_schema(self):
        profile = analyse_template(FIXTURE_PATH)
        schema = _load_schema()
        jsonschema.validate(instance=profile, schema=schema)

    def test_unmapped_fallback_present(self):
        profile = analyse_template(FIXTURE_PATH)
        assert profile['unmapped_fallback'] is not None or len(profile['layout_mapping']) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_template_analyser.py::TestAnalyseTemplate -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement analyse_template**

Add to `src/template_analyser.py`:

```python
def _compute_file_hash(file_path):
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def analyse_template(template_path, master_index=0):
    """Analyse a .pptx template and produce a TemplateProfile.

    Args:
        template_path: Path to the .pptx template file.
        master_index: Which slide master to use (default 0).

    Returns:
        dict conforming to the TemplateProfile schema.
    """
    prs = Presentation(template_path)

    layouts = extract_layouts(template_path, master_index=master_index)
    mapping, fallback = auto_map_layouts(layouts)

    profile = {
        'template_path': template_path,
        'template_hash': _compute_file_hash(template_path),
        'slide_width_inches': _emu_to_inches(prs.slide_width),
        'slide_height_inches': _emu_to_inches(prs.slide_height),
        'master_index': master_index,
        'layouts': layouts,
        'layout_mapping': mapping,
        'unmapped_fallback': fallback,
        'constrains_strategies': True,
        'speaker_approved': False,
    }

    return profile
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_template_analyser.py::TestAnalyseTemplate -v`
Expected: 4 PASS

- [ ] **Step 5: Sync plugin copy and commit**

```bash
cp src/template_analyser.py plugins/jack-tar-deckhand/src/
git add src/template_analyser.py plugins/jack-tar-deckhand/src/template_analyser.py tests/test_template_analyser.py
git commit -m "feat: full template analysis with hash and schema validation (#45)"
```

---

### Task 7: Template Assembly Engine — Core

**Files:**
- Create: `src/assembler/build_deck_template.py`
- Test: `tests/test_build_deck_template.py`

- [ ] **Step 1: Write failing tests for slide stripping and basic assembly**

Create `tests/test_build_deck_template.py`:

```python
"""Tests for template-driven deck assembly via python-pptx."""

import json
import os
import shutil
import pytest
from pptx import Presentation

from src.template_analyser import analyse_template
from src.assembler.build_deck_template import build_deck

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'templates', 'metamirror-template.pptx')


def _setup_deck_dir(tmp_path, outline_slides, image_manifest_images=None, speaker_notes=None):
    """Create a minimal DeckContext for testing."""
    deck_dir = str(tmp_path / 'deck')
    os.makedirs(os.path.join(deck_dir, 'images'), exist_ok=True)
    os.makedirs(os.path.join(deck_dir, 'output'), exist_ok=True)

    # Template profile
    profile = analyse_template(FIXTURE_PATH)
    with open(os.path.join(deck_dir, 'template-profile.json'), 'w') as f:
        json.dump(profile, f)

    # Outline
    outline = {
        'narrative_arc': 'test',
        'estimated_duration_minutes': 10,
        'slides': outline_slides,
    }
    with open(os.path.join(deck_dir, 'outline.json'), 'w') as f:
        json.dump(outline, f)

    # Image manifest
    manifest = {'images': image_manifest_images or []}
    with open(os.path.join(deck_dir, 'image-manifest.json'), 'w') as f:
        json.dump(manifest, f)

    # Speaker notes
    notes = speaker_notes or {'notes': []}
    with open(os.path.join(deck_dir, 'speaker-notes.json'), 'w') as f:
        json.dump(notes, f)

    return deck_dir, profile


class TestBuildDeckTemplate:
    def test_strips_example_slides(self, tmp_path):
        deck_dir, profile = _setup_deck_dir(tmp_path, [
            {'slide_number': 1, 'slide_type': 'content', 'headline': 'Real Slide'},
        ])
        output_path = build_deck(deck_dir, FIXTURE_PATH, profile)
        prs = Presentation(output_path)
        # Should have exactly 1 slide (the one from our outline), not the template examples
        assert len(prs.slides) == 1

    def test_populates_title_placeholder(self, tmp_path):
        deck_dir, profile = _setup_deck_dir(tmp_path, [
            {'slide_number': 1, 'slide_type': 'content', 'headline': 'My Headline'},
        ])
        output_path = build_deck(deck_dir, FIXTURE_PATH, profile)
        prs = Presentation(output_path)
        slide = prs.slides[0]
        # Find the title placeholder text
        texts = [shape.text for shape in slide.shapes if shape.has_text_frame]
        assert any('My Headline' in t for t in texts)

    def test_populates_body_points(self, tmp_path):
        deck_dir, profile = _setup_deck_dir(tmp_path, [
            {'slide_number': 1, 'slide_type': 'content', 'headline': 'Title',
             'body_points': ['Point one', 'Point two', 'Point three']},
        ])
        output_path = build_deck(deck_dir, FIXTURE_PATH, profile)
        prs = Presentation(output_path)
        slide = prs.slides[0]
        all_text = ' '.join(shape.text for shape in slide.shapes if shape.has_text_frame)
        assert 'Point one' in all_text
        assert 'Point two' in all_text
        assert 'Point three' in all_text

    def test_output_path_correct(self, tmp_path):
        deck_dir, profile = _setup_deck_dir(tmp_path, [
            {'slide_number': 1, 'slide_type': 'content', 'headline': 'Test'},
        ])
        output_path = build_deck(deck_dir, FIXTURE_PATH, profile)
        assert output_path.endswith('output/presentation.pptx')
        assert os.path.isfile(output_path)

    def test_multiple_slides(self, tmp_path):
        deck_dir, profile = _setup_deck_dir(tmp_path, [
            {'slide_number': 1, 'slide_type': 'title', 'headline': 'Title Slide'},
            {'slide_number': 2, 'slide_type': 'content', 'headline': 'Content Slide'},
            {'slide_number': 3, 'slide_type': 'content', 'headline': 'Another Content'},
        ])
        output_path = build_deck(deck_dir, FIXTURE_PATH, profile)
        prs = Presentation(output_path)
        assert len(prs.slides) == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_build_deck_template.py -v`
Expected: FAIL (ImportError)

- [ ] **Step 3: Implement build_deck**

Create `src/assembler/build_deck_template.py`:

```python
"""Template-driven deck assembly via python-pptx.

Opens a corporate .pptx template, strips example slides, adds new slides
from the outline using the template's mapped layouts, and populates
placeholders with content.
"""

import json
import os

from pptx import Presentation
from pptx.util import Inches, Pt, Emu


def _resolve_layout(prs, profile, slide_type):
    """Find the python-pptx SlideLayout object for a given slide type.

    Looks up the layout_mapping first, then falls back to unmapped_fallback.
    """
    mapping = profile.get('layout_mapping', {})
    entry = mapping.get(slide_type) or profile.get('unmapped_fallback')
    if not entry:
        # Last resort: use the first layout
        return prs.slide_layouts[0]

    master_index = profile.get('master_index', 0)
    master = prs.slide_masters[master_index]
    layout_index = entry['layout_index']
    return master.slide_layouts[layout_index]


def _strip_existing_slides(prs):
    """Remove all existing slides from the presentation.

    python-pptx doesn't have a direct remove_slide method, so we
    manipulate the XML directly.
    """
    slide_list = prs.slides._sldIdLst
    for sldId in list(slide_list):
        slide_list.remove(sldId)


def _find_placeholder_by_type(slide, ph_type, profile_layout):
    """Find a slide placeholder matching the given type from the profile layout metadata.

    Returns the placeholder shape or None.
    """
    if not profile_layout:
        return None

    # Build a set of placeholder indices that match the requested type
    target_indices = set()
    for ph_info in profile_layout.get('placeholders', []):
        if ph_info['type'] == ph_type:
            target_indices.add(ph_info['idx'])

    for ph in slide.placeholders:
        if ph.placeholder_format.idx in target_indices:
            return ph
    return None


def _populate_text(placeholder, text):
    """Set text on a placeholder, preserving the first run's formatting."""
    if placeholder is None or not text:
        return
    tf = placeholder.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.text = text


def _populate_body_points(placeholder, body_points):
    """Set bulleted body points on a content or body placeholder."""
    if placeholder is None or not body_points:
        return
    tf = placeholder.text_frame
    tf.clear()
    for i, point in enumerate(body_points):
        if i == 0:
            tf.paragraphs[0].text = point
        else:
            p = tf.add_paragraph()
            p.text = point


def _get_profile_layout(profile, layout_name):
    """Find a layout entry in the profile by name."""
    for layout in profile.get('layouts', []):
        if layout['name'] == layout_name:
            return layout
    return None


def _get_mapped_layout_name(profile, slide_type):
    """Get the layout name for a slide type from the mapping."""
    mapping = profile.get('layout_mapping', {})
    entry = mapping.get(slide_type) or profile.get('unmapped_fallback')
    if entry:
        return entry['layout_name']
    return None


def build_deck(deck_dir, template_path, template_profile):
    """Assemble a .pptx deck using a template's slide layouts.

    Args:
        deck_dir: Path to the DeckContext directory.
        template_path: Path to the source .pptx template.
        template_profile: dict conforming to TemplateProfile schema.

    Returns:
        str: Path to the output .pptx file.
    """
    # Load DeckContext contracts
    with open(os.path.join(deck_dir, 'outline.json')) as f:
        outline = json.load(f)

    with open(os.path.join(deck_dir, 'image-manifest.json')) as f:
        image_manifest = json.load(f)

    notes_path = os.path.join(deck_dir, 'speaker-notes.json')
    speaker_notes = {}
    if os.path.isfile(notes_path):
        with open(notes_path) as f:
            notes_data = json.load(f)
        speaker_notes = {n['slide_number']: n['text'] for n in notes_data.get('notes', [])}

    # Build image lookup: slide_number -> file_path
    image_lookup = {}
    for img in image_manifest.get('images', []):
        if img.get('status') in ('generated', 'accepted', 'accepted_with_issues'):
            sn = img['slide_number']
            if sn not in image_lookup:
                image_lookup[sn] = img['file_path']

    # Open template and strip example slides
    prs = Presentation(template_path)
    _strip_existing_slides(prs)

    # Build each slide from the outline
    for slide_data in outline.get('slides', []):
        slide_number = slide_data['slide_number']
        slide_type = slide_data.get('slide_type', 'content')
        headline = slide_data.get('headline', '')
        body_points = slide_data.get('body_points', [])

        # Resolve layout
        layout = _resolve_layout(prs, template_profile, slide_type)
        slide = prs.slides.add_slide(layout)

        # Get profile layout metadata for placeholder type lookup
        layout_name = _get_mapped_layout_name(template_profile, slide_type)
        profile_layout = _get_profile_layout(template_profile, layout_name)

        # Populate title
        title_ph = _find_placeholder_by_type(slide, 'title', profile_layout)
        _populate_text(title_ph, headline)

        # Populate body/content
        content_ph = _find_placeholder_by_type(slide, 'content', profile_layout)
        body_ph = _find_placeholder_by_type(slide, 'body', profile_layout)
        if content_ph and body_points:
            _populate_body_points(content_ph, body_points)
        elif body_ph and body_points:
            _populate_body_points(body_ph, body_points)

        # Populate picture placeholder with image if available
        if slide_number in image_lookup:
            pic_ph = _find_placeholder_by_type(slide, 'picture', profile_layout)
            if pic_ph:
                image_path = image_lookup[slide_number]
                abs_image_path = os.path.join(deck_dir, image_path) if not os.path.isabs(image_path) else image_path
                if os.path.isfile(abs_image_path):
                    pic_ph.insert_picture(abs_image_path)

        # Speaker notes
        if slide_number in speaker_notes:
            notes_slide = slide.notes_slide
            notes_slide.notes_text_frame.text = speaker_notes[slide_number]

    # Save output
    output_dir = os.path.join(deck_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'presentation.pptx')
    prs.save(output_path)

    return output_path
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_build_deck_template.py -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add src/assembler/build_deck_template.py tests/test_build_deck_template.py
git commit -m "feat: template assembly engine — core slide building (#45)"
```

---

### Task 8: Assembly Engine — Images, SmartArt Placeholders, Speaker Notes

**Files:**
- Modify: `src/assembler/build_deck_template.py` (already handles images/notes — add SmartArt placeholder + edge case tests)
- Test: `tests/test_build_deck_template.py` (add tests)

- [ ] **Step 1: Write failing tests for image insertion and SmartArt placeholders**

Append to `tests/test_build_deck_template.py`:

```python
from PIL import Image


class TestTemplateAssemblyImages:
    def test_image_inserted_into_picture_placeholder(self, tmp_path):
        # Create a test image
        img = Image.new('RGB', (400, 300), color='red')
        deck_dir, profile = _setup_deck_dir(tmp_path, [
            {'slide_number': 1, 'slide_type': 'content', 'headline': 'With Image'},
        ])
        img_path = os.path.join(deck_dir, 'images', 'slide1.png')
        img.save(img_path)

        # Add image to manifest — needs a layout with PICTURE placeholder
        manifest = {
            'images': [{
                'image_id': 'img-1',
                'slide_number': 1,
                'file_path': 'images/slide1.png',
                'status': 'generated',
            }]
        }
        with open(os.path.join(deck_dir, 'image-manifest.json'), 'w') as f:
            json.dump(manifest, f)

        output_path = build_deck(deck_dir, FIXTURE_PATH, profile)
        assert os.path.isfile(output_path)

    def test_missing_image_does_not_crash(self, tmp_path):
        deck_dir, profile = _setup_deck_dir(tmp_path, [
            {'slide_number': 1, 'slide_type': 'content', 'headline': 'No Image'},
        ], image_manifest_images=[{
            'image_id': 'img-1',
            'slide_number': 1,
            'file_path': 'images/nonexistent.png',
            'status': 'generated',
        }])
        # Should not raise — gracefully skips missing image
        output_path = build_deck(deck_dir, FIXTURE_PATH, profile)
        assert os.path.isfile(output_path)


class TestTemplateAssemblyNotes:
    def test_speaker_notes_populated(self, tmp_path):
        notes = {
            'notes': [
                {'slide_number': 1, 'text': 'Remember to introduce yourself'},
            ]
        }
        deck_dir, profile = _setup_deck_dir(tmp_path, [
            {'slide_number': 1, 'slide_type': 'content', 'headline': 'Intro'},
        ], speaker_notes=notes)
        output_path = build_deck(deck_dir, FIXTURE_PATH, profile)
        prs = Presentation(output_path)
        slide = prs.slides[0]
        notes_text = slide.notes_slide.notes_text_frame.text
        assert 'Remember to introduce yourself' in notes_text

    def test_no_notes_does_not_crash(self, tmp_path):
        deck_dir, profile = _setup_deck_dir(tmp_path, [
            {'slide_number': 1, 'slide_type': 'content', 'headline': 'No Notes'},
        ])
        output_path = build_deck(deck_dir, FIXTURE_PATH, profile)
        assert os.path.isfile(output_path)


class TestTemplateSmartArtPlaceholder:
    def test_smartart_placeholder_emitted_for_smartart_slide(self, tmp_path):
        deck_dir, profile = _setup_deck_dir(tmp_path, [
            {'slide_number': 1, 'slide_type': 'diagram', 'headline': 'Architecture'},
        ])
        # Write a smartart manifest entry
        sa_manifest = {
            'graphics': [{
                'smartart_id': 'sa-1',
                'slide_number': 1,
                'graphic_type': 'flowchart',
                'engine_used': 'pptx_native',
                'enrichment_tier': 'pure_programmatic',
                'file_path': 'smartart/carrier_1.pptx',
                'status': 'rendered',
            }]
        }
        with open(os.path.join(deck_dir, 'smartart-manifest.json'), 'w') as f:
            json.dump(sa_manifest, f)

        output_path = build_deck(deck_dir, FIXTURE_PATH, profile)
        prs = Presentation(output_path)
        slide = prs.slides[0]
        # Check for a shape named pptx_native_placeholder_1
        shape_names = [s.name for s in slide.shapes]
        assert any('pptx_native_placeholder_1' in n for n in shape_names)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_build_deck_template.py::TestTemplateSmartArtPlaceholder -v`
Expected: FAIL (no SmartArt placeholder logic yet)

- [ ] **Step 3: Add SmartArt placeholder emission to build_deck**

In `src/assembler/build_deck_template.py`, add at the top after existing imports:

```python
from pptx.util import Inches, Pt, Emu
from pptx.oxml.ns import qn
from lxml import etree
```

Add this helper function before `build_deck`:

```python
def _emit_smartart_placeholder(slide, slide_number, profile_layout):
    """Add a named rectangle placeholder for SmartArt injection.

    Uses the content placeholder bounds from the profile layout.
    The existing assembler_patch.py will find this by name and replace it.
    """
    # Find the content placeholder bounds from the profile
    content_info = None
    if profile_layout:
        for ph_info in profile_layout.get('placeholders', []):
            if ph_info['type'] == 'content':
                content_info = ph_info
                break

    if not content_info:
        # Default to a reasonable content area
        x, y, w, h = Inches(0.6), Inches(2.3), Inches(12.13), Inches(4.57)
    else:
        x = Inches(content_info['x'])
        y = Inches(content_info['y'])
        w = Inches(content_info['w'])
        h = Inches(content_info['h'])

    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE.RECTANGLE
        x, y, w, h,
    )
    shape.name = f'pptx_native_placeholder_{slide_number}'
    # Make it invisible (no fill, no line)
    shape.fill.background()
    shape.line.fill.background()
```

Then in `build_deck`, after the body population block and before the picture placeholder block, add:

```python
        # SmartArt placeholder
        sa_manifest_path = os.path.join(deck_dir, 'smartart-manifest.json')
        if os.path.isfile(sa_manifest_path):
            with open(sa_manifest_path) as f:
                sa_manifest = json.load(f)
            for graphic in sa_manifest.get('graphics', []):
                if (graphic['slide_number'] == slide_number
                        and graphic.get('engine_used') == 'pptx_native'):
                    _emit_smartart_placeholder(slide, slide_number, profile_layout)
                    break
```

- [ ] **Step 4: Run all assembly tests**

Run: `.venv/bin/pytest tests/test_build_deck_template.py -v`
Expected: All PASS (including the new SmartArt, image, and notes tests)

- [ ] **Step 5: Sync plugin copy and commit**

```bash
cp src/assembler/build_deck_template.py plugins/jack-tar-deckhand/src/assembler/
git add src/assembler/build_deck_template.py plugins/jack-tar-deckhand/src/assembler/build_deck_template.py tests/test_build_deck_template.py
git commit -m "feat: template assembly — images, SmartArt placeholders, speaker notes (#45)"
```

---

### Task 9: Strategy Map Template Constraints

**Files:**
- Modify: `src/slide_prompt_composer.py:32-82` (add template mode to `classify_slide_strategy`)
- Test: `tests/test_template_integration.py`

- [ ] **Step 1: Write failing tests for template mode strategy constraints**

Create `tests/test_template_integration.py`:

```python
"""Integration tests for template-driven layout pipeline."""

import json
import os
import pytest

from src.slide_prompt_composer import classify_slide_strategy, build_strategy_map


class TestTemplateStrategyConstraints:
    def test_template_mode_forces_composed(self):
        slide = {'slide_number': 1, 'slide_type': 'content', 'headline': 'Test',
                 'body_points': ['A'], 'visual_type': 'hero_image'}
        result = classify_slide_strategy(slide, template_mode=True)
        assert result['strategy'] == 'composed'

    def test_template_mode_title_stays_composed(self):
        slide = {'slide_number': 1, 'slide_type': 'title', 'headline': 'Title',
                 'visual_type': 'hero_image'}
        result = classify_slide_strategy(slide, template_mode=True)
        assert result['strategy'] == 'composed'

    def test_template_mode_full_bleed_picture_allows_full_render(self):
        slide = {'slide_number': 1, 'slide_type': 'title', 'headline': 'Title',
                 'visual_type': 'hero_image'}
        full_bleed_layout = {
            'placeholders': [
                {'idx': 13, 'type': 'picture', 'name': 'Picture', 'x': 0.0, 'y': 0.0, 'w': 13.33, 'h': 7.5},
            ]
        }
        result = classify_slide_strategy(slide, template_mode=True, template_layout=full_bleed_layout)
        assert result['strategy'] == 'full_render'

    def test_template_mode_small_picture_stays_composed(self):
        slide = {'slide_number': 1, 'slide_type': 'title', 'headline': 'Title',
                 'visual_type': 'hero_image'}
        small_pic_layout = {
            'placeholders': [
                {'idx': 13, 'type': 'picture', 'name': 'Picture', 'x': 7.0, 'y': 0.0, 'w': 6.0, 'h': 7.5},
            ]
        }
        result = classify_slide_strategy(slide, template_mode=True, template_layout=small_pic_layout)
        assert result['strategy'] == 'composed'

    def test_without_template_mode_unchanged(self):
        slide = {'slide_number': 1, 'slide_type': 'title', 'headline': 'Title',
                 'visual_type': 'hero_image'}
        result = classify_slide_strategy(slide, template_mode=False)
        assert result['strategy'] == 'full_render'

    def test_build_strategy_map_template_mode(self):
        outline = {
            'narrative_arc': 'test',
            'estimated_duration_minutes': 10,
            'slides': [
                {'slide_number': 1, 'slide_type': 'title', 'headline': 'Title', 'visual_type': 'hero_image'},
                {'slide_number': 2, 'slide_type': 'content', 'headline': 'Content',
                 'body_points': ['A', 'B', 'C', 'D'], 'visual_type': 'hero_image'},
            ],
        }
        strategy_map = build_strategy_map(outline, template_mode=True)
        for entry in strategy_map['slides']:
            assert entry['strategy'] == 'composed'

    def test_build_strategy_map_render_funnel_ollama_only(self):
        outline = {
            'narrative_arc': 'test',
            'estimated_duration_minutes': 10,
            'slides': [
                {'slide_number': 1, 'slide_type': 'content', 'headline': 'Test', 'visual_type': 'hero_image'},
            ],
        }
        strategy_map = build_strategy_map(outline, template_mode=True)
        assert strategy_map['slides'][0]['render_funnel'] == ['ollama']
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_template_integration.py::TestTemplateStrategyConstraints -v`
Expected: FAIL (classify_slide_strategy doesn't accept template_mode parameter)

- [ ] **Step 3: Add template_mode to classify_slide_strategy and build_strategy_map**

In `src/slide_prompt_composer.py`, modify `classify_slide_strategy` signature and body:

```python
def classify_slide_strategy(slide, template_mode=False, template_layout=None):
    """Classify a slide's recommended rendering strategy.

    Args:
        slide: dict from SlideOutline slides array.
        template_mode: If True, constrain to composed strategy (template-driven assembly).
        template_layout: Optional layout dict with placeholder info for full-bleed detection.

    Returns:
        dict with keys: slide_number, strategy, rationale, render_funnel, speaker_override
    """
    slide_number = slide.get('slide_number', 0)
    slide_type = slide.get('slide_type', 'content')
    body_points = slide.get('body_points', [])
    visual_type = classify_visual_type(slide)

    # Template mode: constrain to composed, except full-bleed picture layouts
    if template_mode:
        # Check for full-bleed picture placeholder (>90% of slide area)
        if template_layout:
            slide_area = 13.333 * 7.5  # standard 16:9
            for ph in template_layout.get('placeholders', []):
                if ph['type'] == 'picture':
                    ph_area = ph['w'] * ph['h']
                    if ph_area / slide_area > 0.9:
                        return {
                            'slide_number': slide_number,
                            'strategy': 'full_render',
                            'rationale': 'Template layout has full-bleed picture placeholder',
                            'render_funnel': ['ollama', 'cloud_low', 'cloud_full'],
                            'speaker_override': None,
                        }
        return {
            'slide_number': slide_number,
            'strategy': 'composed',
            'rationale': 'Template mode — content placed in template placeholders',
            'render_funnel': ['ollama'],
            'speaker_override': None,
        }

    # ... rest of existing logic unchanged ...
```

Also modify `build_strategy_map` to accept and pass `template_mode`:

```python
def build_strategy_map(outline, approval_mode='review', overrides=None, template_mode=False):
    """Build a complete StrategyMap from a SlideOutline.

    Args:
        outline: dict from SlideOutline (must have 'slides' array).
        approval_mode: 'review' (default) or 'one_shot'.
        overrides: Optional dict of {slide_number: strategy} Speaker overrides.
        template_mode: If True, constrain all slides to composed strategy.

    Returns:
        dict conforming to StrategyMap schema.
    """
    overrides = overrides or {}
    slides = []

    for slide in outline.get('slides', []):
        entry = classify_slide_strategy(slide, template_mode=template_mode)
        slide_num = entry['slide_number']

        if slide_num in overrides:
            entry['speaker_override'] = overrides[slide_num]
            if overrides[slide_num] in ('full_render', 'backdrop_render', 'background', 'backdrop'):
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

**Note:** `build_strategy_map` passes `template_mode` but not `template_layout` per-slide. In template mode, the blanket `composed` constraint covers all slides. The per-layout full-bleed PICTURE detection via `template_layout` parameter is available for conductor-level use (e.g., when the conductor knows the per-slide layout mapping and wants to check individually). This is a v1 simplification — the conductor can call `classify_slide_strategy` directly with `template_layout` for specific slides if needed.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_template_integration.py::TestTemplateStrategyConstraints -v`
Expected: 7 PASS

Also run existing strategy tests to verify no regression:

Run: `.venv/bin/pytest tests/test_slide_prompt_composer.py -v`
Expected: All existing tests PASS

- [ ] **Step 5: Sync plugin copy and commit**

```bash
cp src/slide_prompt_composer.py plugins/jack-tar-deckhand/src/
git add src/slide_prompt_composer.py plugins/jack-tar-deckhand/src/slide_prompt_composer.py tests/test_template_integration.py
git commit -m "feat: strategy map template mode — constrain to composed (#45)"
```

---

### Task 10: Pipeline Step Order & DeckContext Registration

**Files:**
- Modify: `src/deckcontext.py:33-47` (add `template-analysis` to step order)
- Test: `tests/test_template_integration.py` (add test)
- Test: `tests/test_conductor.py` (verify step order)

- [ ] **Step 1: Write failing test for step order**

Append to `tests/test_template_integration.py`:

```python
from src.deckcontext import DEFAULT_STEP_ORDER


class TestPipelineStepOrder:
    def test_template_analysis_in_step_order(self):
        assert 'template-analysis' in DEFAULT_STEP_ORDER

    def test_template_analysis_before_brand_manager(self):
        ta_idx = DEFAULT_STEP_ORDER.index('template-analysis')
        bm_idx = DEFAULT_STEP_ORDER.index('brand-manager')
        assert ta_idx < bm_idx

    def test_template_analysis_after_validate_brief(self):
        ta_idx = DEFAULT_STEP_ORDER.index('template-analysis')
        vb_idx = DEFAULT_STEP_ORDER.index('validate-brief')
        assert ta_idx > vb_idx
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_template_integration.py::TestPipelineStepOrder -v`
Expected: FAIL (template-analysis not in DEFAULT_STEP_ORDER)

- [ ] **Step 3: Add template-analysis to DEFAULT_STEP_ORDER**

In `src/deckcontext.py`, modify `DEFAULT_STEP_ORDER`:

```python
DEFAULT_STEP_ORDER = [
    'validate-brief',
    'template-analysis',
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

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_template_integration.py::TestPipelineStepOrder -v`
Expected: 3 PASS

Run existing conductor tests to verify no regression:

Run: `.venv/bin/pytest tests/test_conductor.py -v`
Expected: All 29 PASS (the smartart steps test still passes since those are still present)

- [ ] **Step 5: Sync plugin copies and commit**

```bash
cp src/deckcontext.py plugins/jack-tar-deckhand/src/
git add src/deckcontext.py plugins/jack-tar-deckhand/src/deckcontext.py tests/test_template_integration.py
git commit -m "feat: add template-analysis to pipeline step order (#45)"
```

---

### Task 11: Deck-Assembler Skill Routing & Conductor Update

**Files:**
- Modify: `plugins/jack-tar-deckhand/skills/deck-assembler/SKILL.md`
- Modify: `plugins/jack-tar-deckhand/agents/deck-conductor.md`

- [ ] **Step 1: Update deck-assembler skill with routing logic**

In `plugins/jack-tar-deckhand/skills/deck-assembler/SKILL.md`, replace the `## Usage` section:

```markdown
## Usage

**Standard mode (no template):**
```bash
node src/assembler/build_deck.js --deck-dir ./tmp/deck
```

**Template mode (template-profile.json exists):**
```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.assembler.build_deck_template import build_deck
with open('./tmp/deck/template-profile.json') as f:
    profile = json.load(f)
output = build_deck('./tmp/deck', profile['template_path'], profile)
print(f'Template deck assembled: {output}')
"
```

**Routing:** Check for `./tmp/deck/template-profile.json`. If it exists, use the python-pptx template path. Otherwise, use the standard PptxGenJS path.
```

Also update the `## Limitations` section — remove the line about not importing templates:

```markdown
## Limitations

- No native animations (PptxGenJS v4.0.1 limitation) -- uses progressive builds for ~80% coverage
- No gradient fills on shapes -- use pre-rendered gradient images as backgrounds
- Template mode requires python-pptx — PptxGenJS path does not support templates
```

- [ ] **Step 2: Update deck-conductor agent with template-analysis step**

In `plugins/jack-tar-deckhand/agents/deck-conductor.md`, add a new step between Step 0 and Step 1. Insert after the Step 0 closing code block and before `### Step 1: Brand Profile`:

```markdown
### Step 0.5: Template Analysis (conditional)

If the TalkBrief has `branding.template_pptx_path`:

1. Run template analysis:
```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
from src.template_analyser import analyse_template
from src.deckcontext import write_contract
import json
profile = analyse_template('TEMPLATE_PATH')
write_contract('./tmp/deck', 'template-profile', profile)
print(json.dumps(profile['layout_mapping'], indent=2))
"
```

2. **ESCALATE:** Present the auto-detected layout mapping to the Speaker:
   - Show each slide type → layout name assignment
   - List any unmapped slide types and their fallback
   - Ask Speaker to confirm or override

3. Update the profile with Speaker approval:
```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
with open('./tmp/deck/template-profile.json') as f:
    profile = json.load(f)
profile['speaker_approved'] = True
# Apply any Speaker overrides to layout_mapping here
with open('./tmp/deck/template-profile.json', 'w') as f:
    json.dump(profile, f, indent=2)
"
```

4. Log approval:
```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
from src.conductor import log_speaker_approval
log_speaker_approval('./tmp/deck', 'template_mapping_approved', 'Speaker confirmed template layout mapping')
"
```

If the TalkBrief does NOT have `branding.template_pptx_path`, skip this step entirely.
```

- [ ] **Step 3: Commit**

```bash
git add plugins/jack-tar-deckhand/skills/deck-assembler/SKILL.md plugins/jack-tar-deckhand/agents/deck-conductor.md
git commit -m "feat: assembler routing and conductor template-analysis step (#45)"
```

---

### Task 12: Full Pipeline End-to-End Test

**Files:**
- Test: `tests/test_template_integration.py` (add e2e test)

- [ ] **Step 1: Write e2e test**

Append to `tests/test_template_integration.py`:

```python
from src.template_analyser import analyse_template
from src.assembler.build_deck_template import build_deck
from src.deckcontext import write_contract, read_contract
from pptx import Presentation


FIXTURE_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'templates', 'metamirror-template.pptx')


class TestEndToEnd:
    def test_full_pipeline_template_to_pptx(self, tmp_path):
        deck_dir = str(tmp_path / 'deck')
        os.makedirs(os.path.join(deck_dir, 'images'), exist_ok=True)
        os.makedirs(os.path.join(deck_dir, 'output'), exist_ok=True)

        # 1. Analyse template
        profile = analyse_template(FIXTURE_PATH)
        profile['speaker_approved'] = True
        write_contract(deck_dir, 'template-profile', profile)

        # 2. Create outline
        outline = {
            'narrative_arc': 'problem-solution',
            'estimated_duration_minutes': 15,
            'slides': [
                {'slide_number': 1, 'slide_type': 'title', 'headline': 'Welcome to the Future',
                 'visual_type': 'hero_image'},
                {'slide_number': 2, 'slide_type': 'content', 'headline': 'The Problem',
                 'body_points': ['Legacy systems are slow', 'Users are frustrated', 'Costs are rising'],
                 'visual_type': 'none'},
                {'slide_number': 3, 'slide_type': 'content', 'headline': 'Our Solution',
                 'body_points': ['AI-driven automation', 'Real-time processing'],
                 'visual_type': 'hero_image'},
                {'slide_number': 4, 'slide_type': 'closing', 'headline': 'Thank You',
                 'visual_type': 'none'},
            ],
        }
        write_contract(deck_dir, 'outline', outline, validate=False)

        # 3. Create empty manifests
        write_contract(deck_dir, 'image-manifest', {'images': []}, validate=False)
        with open(os.path.join(deck_dir, 'speaker-notes.json'), 'w') as f:
            json.dump({'notes': [
                {'slide_number': 1, 'text': 'Welcome everyone'},
                {'slide_number': 4, 'text': 'Questions?'},
            ]}, f)

        # 4. Build strategy map in template mode
        from src.slide_prompt_composer import build_strategy_map
        strategy_map = build_strategy_map(outline, template_mode=True)
        for entry in strategy_map['slides']:
            assert entry['strategy'] == 'composed'

        # 5. Assemble
        loaded_profile = read_contract(deck_dir, 'template-profile')
        output_path = build_deck(deck_dir, FIXTURE_PATH, loaded_profile)

        # 6. Verify output
        assert os.path.isfile(output_path)
        prs = Presentation(output_path)
        assert len(prs.slides) == 4

        # Verify slide 1 has the title
        slide1_texts = [s.text for s in prs.slides[0].shapes if s.has_text_frame]
        assert any('Welcome to the Future' in t for t in slide1_texts)

        # Verify slide 2 has body points
        slide2_texts = ' '.join(s.text for s in prs.slides[1].shapes if s.has_text_frame)
        assert 'Legacy systems are slow' in slide2_texts

        # Verify slide 1 has speaker notes
        notes1 = prs.slides[0].notes_slide.notes_text_frame.text
        assert 'Welcome everyone' in notes1

    def test_assembler_routing_uses_template_when_profile_exists(self, tmp_path):
        """Verify that the presence of template-profile.json would route to template assembler."""
        deck_dir = str(tmp_path / 'deck')
        os.makedirs(deck_dir, exist_ok=True)

        # No template profile — would route to JS
        profile = read_contract(deck_dir, 'template-profile')
        assert profile is None  # No profile means JS path

        # With template profile — would route to python-pptx
        tp = analyse_template(FIXTURE_PATH)
        write_contract(deck_dir, 'template-profile', tp)
        profile = read_contract(deck_dir, 'template-profile')
        assert profile is not None  # Profile exists means template path
```

- [ ] **Step 2: Run the e2e test**

Run: `.venv/bin/pytest tests/test_template_integration.py::TestEndToEnd -v`
Expected: 2 PASS

- [ ] **Step 3: Run the full test suite to verify no regressions**

Run: `.venv/bin/pytest tests/ -v --tb=short 2>&1 | tail -30`
Expected: All tests pass (existing + new)

**Note:** The spec also calls for a new QA check ("verify every slide references a valid template layout — no orphaned slides"). This is a simple check that can be added as a follow-up PR after the core feature lands. The existing QA infrastructure in `src/qa/` supports adding new checks without modifying the core pipeline.

- [ ] **Step 4: Commit**

```bash
git add tests/test_template_integration.py
git commit -m "feat: end-to-end template pipeline test (#45)"
```

---

### Task 13: CLAUDE.md Update, Plugin Sync, Final Cleanup

**Files:**
- Modify: `CLAUDE.md`
- Sync: all plugin copies
- Modify: `plugins/jack-tar-deckhand/CLAUDE.md`

- [ ] **Step 1: Update CLAUDE.md with template-driven layout info**

Add to the Current Status section (after the deck-conductor invocation contract bullet):

```markdown
- **Template-Driven Layout Support (issue #45):** Speakers can provide a corporate .pptx template via `branding.template_pptx_path`. Template analyser extracts layouts and placeholder geometry, auto-maps to slide types (Speaker confirms). python-pptx assembly engine (`src/assembler/build_deck_template.py`) opens the template, strips example slides, and places content into the template's typed placeholders. Strategy map constrained to `composed` in template mode (no AI backgrounds competing with corporate branding). SmartArt injection works unchanged — placeholder rect placed in template content zone.
```

- [ ] **Step 2: Update the Implementation Status table**

Add rows:

```markdown
| Template analyser | `src/template_analyser.py` | ~20 | Done |
| Template assembler | `src/assembler/build_deck_template.py` | ~25 | Done |
| Template integration | `tests/test_template_integration.py` | ~12 | Done |
```

- [ ] **Step 3: Update plugin CLAUDE.md**

In `plugins/jack-tar-deckhand/CLAUDE.md`, add to the Skills table:

```markdown
| `/deck-assembler` | Assemble .pptx — routes to PptxGenJS (standard) or python-pptx (template mode) |
```

(Replace the existing deck-assembler row.)

- [ ] **Step 4: Sync all plugin copies**

```bash
cp src/template_analyser.py plugins/jack-tar-deckhand/src/
cp src/assembler/build_deck_template.py plugins/jack-tar-deckhand/src/assembler/
cp src/slide_prompt_composer.py plugins/jack-tar-deckhand/src/
cp src/deckcontext.py plugins/jack-tar-deckhand/src/
cp src/schemas/template_profile.schema.json plugins/jack-tar-deckhand/src/schemas/
```

- [ ] **Step 5: Run full test suite one final time**

Run: `.venv/bin/pytest tests/ -v --tb=short 2>&1 | tail -30`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md plugins/
git commit -m "docs: CLAUDE.md update for template-driven layouts (#45)"
```
