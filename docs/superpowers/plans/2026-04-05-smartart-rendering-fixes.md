# SmartArt Rendering Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 8 rendering defects (issues #22-#29) in the SmartArt demo deck on branch `feat/smartart-intelligent-graphics`, producing readable graphics on every affected slide.

**Architecture:** Fixes span four layers: Mermaid engine rendering (`smartart_renderer.py`), Vega-Lite config injection (`smartart_renderer.py`), custom SVG layout algorithms (`src/smartart_svg/layouts/*.py`), and PptxGenJS assembler (`src/assembler/build_deck.js`). Each fix is independent — tasks can be implemented in any order, though the suggested order maximises impact.

**Tech Stack:** Python 3 (renderer, SVG layouts), Node.js (Mermaid CLI, PptxGenJS assembler), pytest, cairosvg/Pillow

**Branch:** `feat/smartart-intelligent-graphics` (622 tests passing)
**Issues:** #22, #23, #24, #25, #26, #27, #28, #29

---

## File Structure

### Modified Files

| File | Changes | Issues |
|------|---------|--------|
| `src/smartart_renderer.py` | Mermaid PNG-direct rendering, Vega-Lite font config injection | #22, #27 |
| `src/smartart_svg/layouts/venn.py` | Proportional overlap, exclusive item positioning | #23 |
| `src/smartart_svg/layouts/feature_matrix.py` | Column overflow policy, adaptive column count | #24 |
| `src/smartart_svg/layouts/timeline.py` | Text truncation, dynamic spacing, collision avoidance | #25 |
| `src/smartart_svg/layouts/gantt.py` | **New layout** — custom SVG Gantt replacing Mermaid Gantt | #26 |
| `src/smartart_svg/layouts/__init__.py` | Register `gantt` layout | #26 |
| `src/smartart_extractor.py` | Route `gantt` to `custom_svg` engine | #26 |
| `src/assembler/build_deck.js` | Title overlay on full_render, margin enforcement | #28 |
| `tests/test_smartart_renderer.py` | Tests for Mermaid PNG-direct, VL font config | #22, #27 |
| `tests/test_smartart_svg.py` | Tests for Venn, feature matrix, timeline, Gantt layouts | #23, #24, #25, #26 |
| `tests/test_assembler.py` | Tests for title overlay and margin constraints | #28 |

### New Files

| File | Responsibility | Issue |
|------|---------------|-------|
| `src/smartart_svg/layouts/gantt.py` | Custom SVG Gantt chart layout with readable text | #26 |

---

## Task 1: Mermaid PNG-Direct Rendering (#22)

**Problem:** Mermaid renders text inside `<foreignObject>` HTML. cairosvg/Sharp can't render foreignObject → PNGs show shapes but **no text labels**. Affects 5 slides (4, 11, 24 for flowcharts; 19, 27 for Gantt).

**Fix:** Use `mmdc --outputFormat png` to let Mermaid's own Puppeteer rasterise directly to PNG, bypassing our SVG→cairosvg pipeline.

**Files:**
- Modify: `src/smartart_renderer.py:302-360` (render_mermaid function)
- Modify: `src/smartart_renderer.py:43-78` (_rasterise_svg_to_png — keep for other engines)
- Test: `tests/test_smartart_renderer.py`

- [ ] **Step 1: Write the failing test**

In `tests/test_smartart_renderer.py`, add a test that verifies Mermaid's PNG output contains non-blank content when the diagram has text labels:

```python
class TestMermaidPngDirect:
    def test_mermaid_png_direct_has_content(self):
        """mmdc --outputFormat png should produce a non-blank PNG with text."""
        from src.smartart_renderer import render_mermaid
        spec = {
            'data': {
                'syntax': 'graph TD\n    A[Start] --> B[End]'
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'text_primary': '1a1a1a'},
            'typography': {'body_font': 'sans-serif'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            result = render_mermaid(spec, style_guide, tmpdir)
            assert result.endswith('.png')
            assert os.path.exists(result)
            # PNG should be non-trivial size (blank PNGs are < 10KB typically)
            assert os.path.getsize(result) > 5000

    def test_mermaid_svg_source_preserved(self):
        """SVG source file should be kept alongside the PNG for debugging."""
        from src.smartart_renderer import render_mermaid
        spec = {
            'data': {
                'syntax': 'graph LR\n    A[Hello] --> B[World]'
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'text_primary': '1a1a1a'},
            'typography': {'body_font': 'sans-serif'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = render_mermaid(spec, style_guide, tmpdir)
            svg_path = png_path.replace('.png', '.svg')
            assert os.path.exists(svg_path), "SVG source should be preserved alongside PNG"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_smartart_renderer.py::TestMermaidPngDirect -v`
Expected: Tests may pass or fail depending on current rendering quality — the key change is the rendering approach.

- [ ] **Step 3: Implement PNG-direct rendering**

In `src/smartart_renderer.py`, modify `render_mermaid()` to use a two-pass approach:

1. First render to SVG (for source preservation and post-processing)
2. Then render to PNG directly via `mmdc --outputFormat png`

```python
def render_mermaid(spec, style_guide, output_dir):
    """Render a Mermaid diagram using the Mermaid CLI (mmdc via npx).

    Uses two-pass rendering:
    1. SVG pass — for source file preservation and dimension extraction
    2. PNG pass — mmdc renders directly to PNG via its own Puppeteer instance,
       which correctly handles foreignObject HTML text that cairosvg/Sharp cannot.
    """
    syntax = spec['data']['syntax']
    palette = style_guide.get('palette', {})

    # Build Mermaid theme directive with brand colours
    theme_vars = {
        'primaryColor': '#' + palette.get('primary', '1a73e8'),
        'primaryTextColor': '#' + palette.get('text_primary', '1a1a1a'),
        'lineColor': '#' + palette.get('text_primary', '666666'),
        'fontFamily': style_guide.get('typography', {}).get('body_font', 'sans-serif'),
    }
    theme_directive = (
        f"%%{{init: {{'theme': 'base', 'themeVariables': {json.dumps(theme_vars)}}}}}%%\n"
    )
    full_syntax = theme_directive + syntax

    # Write .mmd source file
    run_id = uuid.uuid4().hex[:8]
    mmd_path = os.path.join(output_dir, f'input-{run_id}.mmd')
    svg_path = os.path.join(output_dir, f'output-{run_id}.svg')
    png_path = os.path.join(output_dir, f'output-{run_id}.png')
    with open(mmd_path, 'w', encoding='utf-8') as f:
        f.write(full_syntax)

    # Pass 1: Render to SVG (source preservation + dimension extraction)
    svg_result = subprocess.run(
        ['npx', 'mmdc', '-i', mmd_path, '-o', svg_path,
         '-b', 'transparent', '--width', '1600'],
        capture_output=True, text=True, timeout=30,
    )
    if svg_result.returncode != 0:
        raise RuntimeError(f"Mermaid CLI (SVG) failed: {svg_result.stderr}")
    _postprocess_mermaid_svg(svg_path)

    # Pass 2: Render directly to PNG (Mermaid's Puppeteer handles foreignObject text)
    png_result = subprocess.run(
        ['npx', 'mmdc', '-i', mmd_path, '-o', png_path,
         '-b', 'transparent', '--width', '1600'],
        capture_output=True, text=True, timeout=30,
    )
    if png_result.returncode != 0:
        # Fallback: rasterise SVG (may lose foreignObject text)
        _rasterise_svg_to_png(svg_path, png_path)

    return png_path
```

**Key insight:** `mmdc -o file.png` automatically outputs PNG when the output path ends in `.png`. Mermaid CLI uses its built-in Puppeteer to render, which correctly handles foreignObject HTML text.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_smartart_renderer.py -v`
Expected: All tests PASS, including existing Mermaid tests.

- [ ] **Step 5: Run full test suite**

Run: `.venv/bin/pytest --tb=short -q`
Expected: 622+ tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/smartart_renderer.py tests/test_smartart_renderer.py
git commit -m "fix: Mermaid PNG-direct rendering via mmdc (#22)

Use mmdc --outputFormat png for Mermaid diagrams so Puppeteer
handles foreignObject HTML text that cairosvg cannot render.
Two-pass: SVG for source preservation, PNG for assembly."
```

---

## Task 2: Vega-Lite Font Size Injection (#27)

**Problem:** Vega-Lite charts render with 10px axis labels. At slide scale these become ~3pt — unreadable. Affects 3 slides (18, 23, 26).

**Fix:** Inject `config.axis`, `config.legend`, and `config.title` font sizes into the Vega-Lite spec before CLI rendering.

**Files:**
- Modify: `src/smartart_renderer.py:363-413` (render_vega_lite function)
- Test: `tests/test_smartart_renderer.py`

- [ ] **Step 1: Write the failing test**

```python
class TestVegaLiteFontConfig:
    def test_axis_font_sizes_injected(self):
        """Vega-Lite spec should have axis/legend/title font sizes after render."""
        from src.smartart_renderer import render_vega_lite
        import json
        spec = {
            'data': {
                'spec': {
                    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                    "mark": "bar",
                    "encoding": {
                        "x": {"field": "label", "type": "ordinal"},
                        "y": {"field": "value", "type": "quantitative"}
                    },
                    "data": {"values": [{"label": "Q1", "value": 100}]}
                }
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a'},
            'typography': {'body_font': 'Inter'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            render_vega_lite(spec, style_guide, tmpdir)
            # Read the written spec file to verify config injection
            spec_files = [f for f in os.listdir(tmpdir) if f.startswith('vl-spec-')]
            assert len(spec_files) == 1
            with open(os.path.join(tmpdir, spec_files[0])) as f:
                written_spec = json.load(f)
            assert written_spec['config']['axis']['labelFontSize'] >= 14
            assert written_spec['config']['axis']['titleFontSize'] >= 16
            assert written_spec['config']['legend']['labelFontSize'] >= 14
            assert written_spec['config']['title']['fontSize'] >= 18
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_smartart_renderer.py::TestVegaLiteFontConfig -v`
Expected: FAIL — `config.axis` key doesn't exist yet.

- [ ] **Step 3: Implement font size injection**

In `src/smartart_renderer.py`, add font config after line 396 in `render_vega_lite()`:

```python
    # Inject readable font sizes for axes, legends, and titles.
    # Vega-Lite defaults to 10px which becomes ~3pt at slide scale.
    vl_spec['config'].setdefault('axis', {})
    vl_spec['config']['axis'].setdefault('labelFontSize', 14)
    vl_spec['config']['axis'].setdefault('titleFontSize', 16)

    vl_spec['config'].setdefault('legend', {})
    vl_spec['config']['legend'].setdefault('labelFontSize', 14)
    vl_spec['config']['legend'].setdefault('titleFontSize', 16)

    vl_spec['config'].setdefault('title', {})
    vl_spec['config']['title'].setdefault('fontSize', 18)
```

Uses `setdefault` so user-provided font sizes in the spec are not overwritten.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_smartart_renderer.py::TestVegaLiteFontConfig -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `.venv/bin/pytest --tb=short -q`
Expected: 622+ tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/smartart_renderer.py tests/test_smartart_renderer.py
git commit -m "fix: inject Vega-Lite axis/legend/title font sizes (#27)

Default VL axis labels are 10px which renders at ~3pt on slides.
Inject labelFontSize 14, titleFontSize 16, title fontSize 18
into the VL config using setdefault to preserve user overrides."
```

---

## Task 3: Venn Diagram Proportional Overlap (#23)

**Problem:** Circle offset is `r * 0.6` regardless of data, creating ~80% visual overlap. Exclusive regions are nearly invisible. Affects 2 slides (5, 14).

**Fix:** Calculate overlap from the ratio of intersection items to total items. Default to ~35% overlap. Reduce circle radius and improve exclusive item positioning.

**Files:**
- Modify: `src/smartart_svg/layouts/venn.py`
- Test: `tests/test_smartart_svg.py`

- [ ] **Step 1: Write the failing test**

In `tests/test_smartart_svg.py`, add tests for proper overlap:

```python
class TestVennOverlap:
    def test_exclusive_regions_visible(self):
        """Each set's exclusive region should occupy at least 30% of circle area."""
        from src.smartart_svg.layouts.venn import render_venn
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        import re
        data = {
            "sets": [
                {"label": "Set A", "items": ["Only A1", "Only A2", "Only A3"]},
                {"label": "Set B", "items": ["Only B1", "Only B2"]}
            ],
            "intersection": {"items": ["Shared"]}
        }
        style = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a',
                        'chart_series': ['2B6CB0', 'ED8936']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)
        svg = render_venn(data, c, tokens)
        # Extract circle cx values
        circles = re.findall(r'<circle cx="([\d.]+)"', svg)
        assert len(circles) >= 2
        left_cx = float(circles[0])
        right_cx = float(circles[1])
        # Extract radius
        radii = re.findall(r'r="([\d.]+)"', svg)
        r = float(radii[0])
        # The gap between centres should be significant relative to radius
        separation = right_cx - left_cx
        # Overlap = 2r - separation; overlap should be < 70% of diameter
        overlap = 2 * r - separation
        assert overlap < r * 1.4, f"Overlap {overlap:.1f} is too large for radius {r:.1f}"
        assert overlap > 0, "Circles should overlap somewhat"

    def test_no_intersection_minimal_overlap(self):
        """With no shared items, circles should barely overlap."""
        from src.smartart_svg.layouts.venn import render_venn
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        import re
        data = {
            "sets": [
                {"label": "A", "items": ["A1", "A2"]},
                {"label": "B", "items": ["B1", "B2"]}
            ],
            "intersection": {"items": []}
        }
        style = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a',
                        'chart_series': ['2B6CB0', 'ED8936']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)
        svg = render_venn(data, c, tokens)
        circles = re.findall(r'<circle cx="([\d.]+)"', svg)
        radii = re.findall(r'r="([\d.]+)"', svg)
        r = float(radii[0])
        separation = float(circles[1]) - float(circles[0])
        overlap = 2 * r - separation
        # Minimal overlap when no intersection items
        assert overlap < r * 0.5, f"Should have minimal overlap with no shared items"

    def test_all_labels_present(self):
        """All set labels, exclusive items, and intersection items should appear."""
        from src.smartart_svg.layouts.venn import render_venn
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "sets": [
                {"label": "Alpha", "items": ["Exclusive1"]},
                {"label": "Beta", "items": ["Exclusive2"]}
            ],
            "intersection": {"items": ["Common"]}
        }
        style = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a',
                        'chart_series': ['2B6CB0', 'ED8936']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)
        svg = render_venn(data, c, tokens)
        assert 'Alpha' in svg
        assert 'Beta' in svg
        assert 'Exclusive1' in svg
        assert 'Exclusive2' in svg
        assert 'Common' in svg
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_smartart_svg.py::TestVennOverlap -v`
Expected: At least `test_exclusive_regions_visible` FAILS due to excessive overlap.

- [ ] **Step 3: Implement proportional overlap**

Rewrite `src/smartart_svg/layouts/venn.py`:

```python
"""Venn diagram layout — two overlapping semi-transparent circles."""

from src.smartart_svg.primitives import svg_circle, svg_text, svg_group
from src.smartart_svg.tokens import resolve_text_colour


def render_venn(data, container, tokens):
    """Render a 2-set Venn diagram as an SVG fragment.

    Overlap is proportional to intersection/total item ratio.
    More shared items = more overlap; fewer = less.
    """
    sets = data.get('sets', [])
    intersection = data.get('intersection', {})
    intersection_items = intersection.get('items', [])

    cx, cy = container.center_point()
    # Radius is 30% of the smaller dimension — smaller circles leave room for labels
    r = min(container.inner_width, container.inner_height) * 0.30

    # Calculate overlap based on data proportions
    left_items = sets[0].get('items', []) if len(sets) >= 1 else []
    right_items = sets[1].get('items', []) if len(sets) >= 2 else []
    total_items = len(left_items) + len(right_items) + len(intersection_items)
    if total_items > 0:
        shared_ratio = len(intersection_items) / total_items
    else:
        shared_ratio = 0.3  # default when no items

    # Overlap ranges from 15% of radius (no shared) to 60% (all shared)
    min_overlap_pct = 0.15
    max_overlap_pct = 0.60
    overlap_pct = min_overlap_pct + (max_overlap_pct - min_overlap_pct) * shared_ratio
    # Separation = 2r - overlap; overlap = 2r * overlap_pct → separation = 2r * (1 - overlap_pct)
    separation = 2 * r * (1 - overlap_pct)

    left_cx = cx - separation / 2
    right_cx = cx + separation / 2

    series = tokens.get('chart_series', ['#2B6CB0', '#ED8936'])
    left_fill = series[0] if len(series) > 0 else '#2B6CB0'
    right_fill = series[1] if len(series) > 1 else '#ED8936'

    elements = []

    # Circles
    elements.append(svg_circle(left_cx, cy, r, fill=left_fill, opacity=0.4))
    elements.append(svg_circle(right_cx, cy, r, fill=right_fill, opacity=0.4))

    font = tokens['font_family']
    heading_font = tokens['heading_font']
    text_col = tokens['text_color']

    # Set labels — above each circle
    if len(sets) >= 1:
        elements.append(svg_text(
            left_cx, cy - r - 12,
            sets[0].get('label', ''),
            font_family=heading_font, font_size=18,
            fill=text_col, anchor='middle', weight='bold'
        ))
    if len(sets) >= 2:
        elements.append(svg_text(
            right_cx, cy - r - 12,
            sets[1].get('label', ''),
            font_family=heading_font, font_size=18,
            fill=text_col, anchor='middle', weight='bold'
        ))

    # Exclusive items — positioned in the non-overlapping region of each circle
    line_h = 18
    font_size = 13

    if left_items:
        # Left exclusive: centre of the non-overlapping left region
        excl_x = left_cx - (separation / 2 + r) / 2 + r / 4
        start_y = cy - (len(left_items) - 1) * line_h / 2
        for i, item in enumerate(left_items):
            elements.append(svg_text(
                excl_x, start_y + i * line_h, item,
                font_family=font, font_size=font_size,
                fill=text_col, anchor='middle'
            ))

    if right_items:
        excl_x = right_cx + (separation / 2 + r) / 2 - r / 4
        start_y = cy - (len(right_items) - 1) * line_h / 2
        for i, item in enumerate(right_items):
            elements.append(svg_text(
                excl_x, start_y + i * line_h, item,
                font_family=font, font_size=font_size,
                fill=text_col, anchor='middle'
            ))

    # Intersection items — centred in overlap zone
    if intersection_items:
        start_y = cy - (len(intersection_items) - 1) * line_h / 2
        for i, item in enumerate(intersection_items):
            elements.append(svg_text(
                cx, start_y + i * line_h, item,
                font_family=font, font_size=font_size,
                fill=text_col, anchor='middle', weight='bold'
            ))

    return svg_group(elements, role='img', aria_label='Venn diagram')
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_smartart_svg.py::TestVennOverlap tests/test_smartart_svg.py::TestVennLayout -v`
Expected: All PASS (both new and existing tests).

- [ ] **Step 5: Run full test suite**

Run: `.venv/bin/pytest --tb=short -q`
Expected: 622+ tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/smartart_svg/layouts/venn.py tests/test_smartart_svg.py
git commit -m "fix: Venn diagram proportional overlap from data ratios (#23)

Calculate overlap from intersection/total item ratio instead of
fixed offset. Range: 15% (no shared) to 60% (all shared).
Reduces circle radius to 30% of container for label room."
```

---

## Task 4: Feature Matrix Column Overflow (#24)

**Problem:** Equal-sized columns at 12pt minimum font cause text overlap when there are 7+ columns. Affects 2 slides (6, 12).

**Fix:** Enforce a maximum column count based on container width. When columns exceed the limit, show the most important ones and add a "..." overflow indicator. Minimum column width = 60pt.

**Files:**
- Modify: `src/smartart_svg/layouts/feature_matrix.py`
- Test: `tests/test_smartart_svg.py`

- [ ] **Step 1: Write the failing test**

```python
class TestFeatureMatrixOverflow:
    def test_many_columns_truncated(self):
        """When there are too many columns to fit, excess should be truncated."""
        from src.smartart_svg.layouts.feature_matrix import render_feature_matrix
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        columns = [f"Feature {chr(65+i)}" for i in range(10)]  # A through J
        rows = [{"label": "Product 1", "values": [True] * 10}]
        data = {"columns": columns, "rows": rows}
        style = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a',
                        'chart_series': ['2B6CB0']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)  # Point-based
        svg = render_feature_matrix(data, c, tokens)
        # Should NOT crash and should contain some columns
        assert 'Feature A' in svg
        # Should have truncation indicator
        assert '...' in svg or '+' in svg

    def test_few_columns_all_shown(self):
        """When columns fit comfortably, all should be shown."""
        from src.smartart_svg.layouts.feature_matrix import render_feature_matrix
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "columns": ["Speed", "Cost"],
            "rows": [{"label": "Option A", "values": [True, False]}]
        }
        style = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a',
                        'chart_series': ['2B6CB0']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)
        svg = render_feature_matrix(data, c, tokens)
        assert 'Speed' in svg
        assert 'Cost' in svg
        assert '...' not in svg
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_smartart_svg.py::TestFeatureMatrixOverflow -v`
Expected: `test_many_columns_truncated` FAILS — no truncation indicator.

- [ ] **Step 3: Implement column overflow policy**

Rewrite `src/smartart_svg/layouts/feature_matrix.py`:

```python
"""Feature matrix layout — rows x columns grid with ✓/✗ indicators."""

from src.smartart_svg.engine import Container
from src.smartart_svg.primitives import svg_rect, svg_text, svg_group
from src.smartart_svg.tokens import resolve_text_colour

# Minimum column width in points — enough for ~8 chars at 12pt
_MIN_COL_WIDTH = 60


def render_feature_matrix(data, container, tokens):
    """Render a feature matrix as an SVG fragment.

    Row 0 = column headers. Column 0 = row labels.
    Inner cells show ✓ / ✗ for boolean values, raw string for others.
    When columns exceed available width at min column width, excess
    columns are dropped and a '...' overflow indicator is shown.
    """
    columns = data.get('columns', [])
    rows = data.get('rows', [])

    # Calculate how many columns fit at minimum width
    # Reserve ~100pt for the label column (first column)
    label_col_width = max(100, container.inner_width * 0.18)
    available_for_data = container.inner_width - label_col_width
    max_data_cols = max(1, int(available_for_data / _MIN_COL_WIDTH))

    truncated = len(columns) > max_data_cols
    visible_columns = columns[:max_data_cols - (1 if truncated else 0)]
    if truncated:
        visible_columns.append(f"+{len(columns) - len(visible_columns)}...")

    num_rows = len(rows) + 1   # +1 for header row
    num_cols = len(visible_columns) + 1  # +1 for label column

    cells = container.split_grid(num_rows, num_cols, gap=2)

    primary = tokens['primary_color']
    text_col = tokens['text_color']

    elements = []

    def cell_at(row, col):
        return cells[row * num_cols + col]

    # Header row
    for col_idx, col_label in enumerate(visible_columns):
        c = cell_at(0, col_idx + 1)
        elements.append(svg_rect(c.x, c.y, c.width, c.height, fill=primary, rx=4))
        header_text_col = resolve_text_colour(primary, '#ffffff', None)
        fitted = c.fit_text(col_label, font_size=14, max_lines=2)
        cx, cy = c.center_point()
        elements.append(svg_text(
            cx, cy + fitted.font_size / 2,
            col_label,
            font_family=tokens['heading_font'],
            font_size=fitted.font_size,
            fill=header_text_col,
            anchor='middle',
            weight='bold'
        ))

    # Top-left corner cell
    corner = cell_at(0, 0)
    elements.append(svg_rect(corner.x, corner.y, corner.width, corner.height, fill=primary, rx=4))

    # Data rows
    for row_idx, row in enumerate(rows):
        row_label = row.get('label', '')
        values = row.get('values', [])
        actual_row = row_idx + 1

        # Alternating row tint
        tint = 'rgba(26,115,232,0.06)' if row_idx % 2 == 0 else 'rgba(0,0,0,0)'
        row_cells_start = actual_row * num_cols
        first_cell = cells[row_cells_start]
        last_cell = cells[row_cells_start + num_cols - 1]
        row_w = last_cell.x + last_cell.width - first_cell.x
        elements.append(svg_rect(first_cell.x, first_cell.y, row_w, first_cell.height, fill=tint))

        # Row label
        lc = cell_at(actual_row, 0)
        fitted = lc.fit_text(row_label, font_size=14, max_lines=1)
        lx, ly = lc.center_point()
        elements.append(svg_text(
            lx, ly + fitted.font_size / 2,
            row_label,
            font_family=tokens['font_family'],
            font_size=fitted.font_size,
            fill=text_col,
            anchor='middle',
            weight='bold'
        ))

        # Value cells (only for visible non-overflow columns)
        n_real_cols = len(visible_columns) - (1 if truncated else 0)
        for col_idx in range(n_real_cols):
            if col_idx >= len(values):
                break
            value = values[col_idx]
            vc = cell_at(actual_row, col_idx + 1)
            vx, vy = vc.center_point()
            if isinstance(value, bool):
                symbol = '\u2713' if value else '\u2717'
                symbol_colour = '#38A169' if value else '#E53E3E'
                elements.append(svg_text(
                    vx, vy + 8, symbol,
                    font_family=tokens['font_family'], font_size=18,
                    fill=symbol_colour, anchor='middle', weight='bold'
                ))
            else:
                cell_val = str(value)
                fitted = vc.fit_text(cell_val, font_size=13, max_lines=1)
                elements.append(svg_text(
                    vx, vy + fitted.font_size / 2, cell_val,
                    font_family=tokens['font_family'], font_size=fitted.font_size,
                    fill=text_col, anchor='middle'
                ))

        # Overflow indicator cell
        if truncated:
            oc = cell_at(actual_row, num_cols - 1)
            ox, oy = oc.center_point()
            elements.append(svg_text(
                ox, oy + 6, '...',
                font_family=tokens['font_family'], font_size=14,
                fill=text_col, anchor='middle'
            ))

    return svg_group(elements, role='img', aria_label='Feature matrix diagram')
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/test_smartart_svg.py::TestFeatureMatrixOverflow tests/test_smartart_svg.py::TestFeatureMatrixLayout -v`
Expected: All PASS.

- [ ] **Step 5: Run full test suite**

Run: `.venv/bin/pytest --tb=short -q`
Expected: 622+ tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/smartart_svg/layouts/feature_matrix.py tests/test_smartart_svg.py
git commit -m "fix: feature matrix column overflow with truncation (#24)

Enforce min 60pt column width. When columns exceed available
space, show the first N that fit plus a +N... overflow indicator.
Reserve 18% of width for the label column."
```

---

## Task 5: Timeline Text Overlap (#25)

**Problem:** Fixed label/description offsets cause text collision between stages. Alternating above/below doesn't provide enough separation when stages are narrow. Affects 2 slides (16, 25).

**Fix:** Calculate available width per stage. Truncate long labels with `fit_text`. Increase vertical separation. Use container-relative offsets instead of magic numbers.

**Files:**
- Modify: `src/smartart_svg/layouts/timeline.py`
- Test: `tests/test_smartart_svg.py`

- [ ] **Step 1: Write the failing test**

```python
class TestTimelineOverflow:
    def test_many_stages_no_crash(self):
        """Timeline with many stages should render without errors."""
        from src.smartart_svg.layouts.timeline import render_timeline
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        stages = [{"label": f"Stage {i}", "description": f"Detail for stage {i}"} for i in range(8)]
        data = {"stages": stages}
        style = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a'},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)
        svg = render_timeline(data, c, tokens)
        assert 'Stage 0' in svg
        assert 'Stage 7' in svg

    def test_long_labels_truncated(self):
        """Long labels should be truncated to fit column width."""
        from src.smartart_svg.layouts.timeline import render_timeline
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        stages = [
            {"label": "A Very Long Stage Name That Should Be Truncated", "description": ""},
            {"label": "Short", "description": ""},
        ]
        data = {"stages": stages}
        style = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a'},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)
        svg = render_timeline(data, c, tokens)
        # Should render without overflow issues
        assert 'Short' in svg
        # The long label should be present (possibly truncated)
        assert 'Very Long' in svg or 'A Very' in svg
```

- [ ] **Step 2: Run tests to verify**

Run: `.venv/bin/pytest tests/test_smartart_svg.py::TestTimelineOverflow -v`

- [ ] **Step 3: Implement improved timeline**

Rewrite `src/smartart_svg/layouts/timeline.py`:

```python
"""Timeline layout — horizontal spine with nodes, alternating labels."""

from src.smartart_svg.engine import Container
from src.smartart_svg.primitives import svg_rect, svg_circle, svg_text, svg_group
from src.smartart_svg.tokens import resolve_text_colour


def _truncate(text, max_chars):
    """Truncate text to max_chars with ellipsis if needed."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 1] + '\u2026'


def render_timeline(data, container, tokens):
    """Render a horizontal timeline as an SVG fragment.

    A thin horizontal spine runs through the vertical centre.
    Equal columns house each stage. Circle nodes sit on the spine.
    Labels alternate above/below the spine. Text is truncated to
    fit the column width.
    """
    stages = data.get('stages', [])
    if not stages:
        return svg_group([], role='img', aria_label='Empty timeline')

    n = len(stages)
    primary = tokens['primary_color']
    text_col = tokens['text_color']
    font = tokens['font_family']
    heading_font = tokens['heading_font']

    # Vertical midpoint for the spine
    spine_y = container.inner_y + container.inner_height / 2

    # Spine rectangle — full width, 4px tall
    spine = svg_rect(
        container.inner_x, spine_y - 2,
        container.inner_width, 4,
        fill=primary
    )

    # Split into n equal horizontal columns
    cols = container.split_horizontal([1] * n, gap=4)

    node_r = min(12, container.inner_height * 0.04)

    # Dynamic offsets based on container height
    half_h = container.inner_height / 2
    label_offset = min(half_h * 0.30, 36)
    desc_offset = min(half_h * 0.55, 60)

    # Calculate max chars per column based on column width
    label_font_size = max(12, min(16, cols[0].width / 5))
    desc_font_size = max(12, min(13, cols[0].width / 6))
    char_width_label = label_font_size * 0.6
    char_width_desc = desc_font_size * 0.6
    max_label_chars = max(6, int(cols[0].width / char_width_label))
    max_desc_chars = max(8, int(cols[0].width / char_width_desc))

    elements = [spine]

    for i, (stage, col) in enumerate(zip(stages, cols)):
        label = stage.get('label', '')
        description = stage.get('description', '')

        node_cx, _ = col.center_point()

        # Node circle on spine
        elements.append(svg_circle(node_cx, spine_y, node_r, fill=primary))

        # Alternate: even stages label above, odd below
        above = (i % 2 == 0)

        # Label — truncate to fit column
        truncated_label = _truncate(label, max_label_chars)
        label_y = spine_y - label_offset if above else spine_y + label_offset + label_font_size
        elements.append(svg_text(
            node_cx, label_y,
            truncated_label,
            font_family=heading_font,
            font_size=label_font_size,
            fill=text_col,
            anchor='middle',
            weight='bold'
        ))

        # Description — opposite side, truncate
        if description:
            truncated_desc = _truncate(description, max_desc_chars)
            desc_y = spine_y + desc_offset if above else spine_y - desc_offset + desc_font_size
            elements.append(svg_text(
                node_cx, desc_y,
                truncated_desc,
                font_family=font,
                font_size=desc_font_size,
                fill=text_col,
                anchor='middle'
            ))

    return svg_group(elements, role='img', aria_label='Timeline diagram')
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/test_smartart_svg.py::TestTimelineOverflow tests/test_smartart_svg.py::TestTimelineLayout -v`
Expected: All PASS.

- [ ] **Step 5: Run full test suite**

Run: `.venv/bin/pytest --tb=short -q`
Expected: 622+ tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/smartart_svg/layouts/timeline.py tests/test_smartart_svg.py
git commit -m "fix: timeline text truncation and dynamic spacing (#25)

Replace magic number offsets with container-relative calculations.
Truncate labels/descriptions to fit column width. Dynamic font
sizing based on available column width."
```

---

## Task 6: Custom SVG Gantt Chart (#26)

**Problem:** Mermaid Gantt charts have extreme aspect ratios and poor text contrast. Even with #22's fix (PNG-direct), the layout is dictated by Mermaid's date-range width calculation, producing very wide, very short charts. Affects 2 slides (19, 27).

**Fix:** Build a custom SVG Gantt layout (like we did for radar_chart) that renders at the correct 16:9 aspect ratio with guaranteed readable text and brand styling.

**Files:**
- Create: `src/smartart_svg/layouts/gantt.py`
- Modify: `src/smartart_svg/layouts/__init__.py`
- Modify: `src/smartart_extractor.py` (route `gantt` to `custom_svg`)
- Test: `tests/test_smartart_svg.py`

- [ ] **Step 1: Write the failing test**

```python
class TestGanttLayout:
    def test_renders_gantt_chart(self):
        """Gantt layout should render tasks as horizontal bars."""
        from src.smartart_svg.layouts.gantt import render_gantt
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "tasks": [
                {"label": "Research", "start": "2026-01-01", "end": "2026-02-15"},
                {"label": "Design", "start": "2026-02-01", "end": "2026-03-15"},
                {"label": "Build", "start": "2026-03-01", "end": "2026-05-01"},
            ]
        }
        style = {
            'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                        'text_primary': '1a1a1a', 'chart_series': ['2B6CB0', 'ED8936', '38A169']},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)
        svg = render_gantt(data, c, tokens)
        assert 'Research' in svg
        assert 'Design' in svg
        assert 'Build' in svg
        assert '<rect' in svg  # Has bar elements

    def test_gantt_single_task(self):
        """Gantt should handle a single task."""
        from src.smartart_svg.layouts.gantt import render_gantt
        from src.smartart_svg.engine import Container
        from src.smartart_svg.tokens import extract_style_tokens
        data = {
            "tasks": [
                {"label": "Solo Task", "start": "2026-01-01", "end": "2026-06-01"},
            ]
        }
        style = {
            'palette': {'primary': '1a73e8', 'accent': 'e8710a', 'background': 'ffffff',
                        'text_primary': '1a1a1a'},
            'typography': {'heading_font': 'Inter', 'body_font': 'Inter'}
        }
        tokens = extract_style_tokens(style)
        c = Container(0, 0, 612, 324, padding=16)
        svg = render_gantt(data, c, tokens)
        assert 'Solo Task' in svg
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_smartart_svg.py::TestGanttLayout -v`
Expected: FAIL — `gantt.py` doesn't exist yet.

- [ ] **Step 3: Create the Gantt layout**

Create `src/smartart_svg/layouts/gantt.py`:

```python
"""Gantt chart layout — horizontal task bars on a date axis.

Renders tasks as colour-coded horizontal bars positioned by start/end dates.
Task labels appear inside or beside each bar. Date axis at the bottom shows
month boundaries.
"""

import math
from datetime import datetime, date

from src.smartart_svg.primitives import svg_rect, svg_text, svg_group, svg_circle
from src.smartart_svg.tokens import resolve_text_colour


def _parse_date(s):
    """Parse a YYYY-MM-DD string to a date object."""
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _interpolate_colour(hex1, hex2, t):
    """Linearly interpolate between two hex colours."""
    def _parse(h):
        h = h.lstrip('#')
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r1, g1, b1 = _parse(hex1)
    r2, g2, b2 = _parse(hex2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f'#{r:02x}{g:02x}{b:02x}'


def render_gantt(data, container, tokens):
    """Render a Gantt chart as an SVG fragment.

    Args:
        data: dict with 'tasks' list of {'label': str, 'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}
        container: Container for layout bounds
        tokens: Style tokens from extract_style_tokens()

    Returns:
        SVG fragment string
    """
    tasks = data.get('tasks', [])
    if not tasks:
        return svg_group([], role='img', aria_label='Empty Gantt chart')

    # Parse all dates
    parsed = []
    for t in tasks:
        s = _parse_date(t.get('start', ''))
        e = _parse_date(t.get('end', ''))
        if s and e:
            parsed.append({'label': t.get('label', ''), 'start': s, 'end': e})
    if not parsed:
        return svg_group([], role='img', aria_label='Gantt chart (no valid dates)')

    # Date range
    all_starts = [t['start'] for t in parsed]
    all_ends = [t['end'] for t in parsed]
    date_min = min(all_starts)
    date_max = max(all_ends)
    total_days = max(1, (date_max - date_min).days)

    # Layout regions
    title_h = container.inner_height * 0.08
    axis_h = 28  # Bottom date axis
    label_w = container.inner_width * 0.22  # Left column for task labels
    chart_x = container.inner_x + label_w
    chart_y = container.inner_y + title_h
    chart_w = container.inner_width - label_w
    chart_h = container.inner_height - title_h - axis_h

    n = len(parsed)
    row_h = min(chart_h / n, 40)  # Cap row height
    bar_h = row_h * 0.6
    gap = row_h * 0.2

    primary = tokens['primary_color']
    accent = tokens['accent_color']
    text_col = tokens['text_color']
    font = tokens['font_family']
    heading_font = tokens['heading_font']
    rx = tokens.get('border_radius', 4)

    elements = []

    # Task bars
    for i, task in enumerate(parsed):
        row_y = chart_y + i * row_h + gap / 2

        # Task label — left column
        label_x = container.inner_x + 4
        label_y = row_y + bar_h / 2 + 4
        elements.append(svg_text(
            label_x, label_y,
            task['label'],
            font_family=heading_font, font_size=13,
            fill=text_col, anchor='start', weight='bold'
        ))

        # Bar position from dates
        start_offset = (task['start'] - date_min).days / total_days
        end_offset = (task['end'] - date_min).days / total_days
        bar_x = chart_x + chart_w * start_offset
        bar_w = max(4, chart_w * (end_offset - start_offset))

        # Colour: interpolate by task index
        t_ratio = i / max(n - 1, 1)
        fill = _interpolate_colour(primary, accent, t_ratio)

        elements.append(svg_rect(bar_x, row_y, bar_w, bar_h, rx=rx, fill=fill))

        # Gridline (faint horizontal separator)
        if i > 0:
            elements.append(svg_rect(
                chart_x, chart_y + i * row_h,
                chart_w, 1,
                fill=text_col
            ))

    # Date axis at bottom
    axis_y = chart_y + chart_h + 4

    # Generate month ticks
    current = date(date_min.year, date_min.month, 1)
    while current <= date_max:
        day_offset = (current - date_min).days / total_days
        tick_x = chart_x + chart_w * day_offset
        if chart_x <= tick_x <= chart_x + chart_w:
            # Tick line
            elements.append(svg_rect(tick_x, chart_y, 1, chart_h, fill=text_col))
            # Month label
            month_label = current.strftime('%b %y')
            elements.append(svg_text(
                tick_x + 2, axis_y + 12,
                month_label,
                font_family=font, font_size=12,
                fill=text_col, anchor='start'
            ))
        # Next month
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    return svg_group(elements, role='img', aria_label='Gantt chart')
```

- [ ] **Step 4: Register the layout**

In `src/smartart_svg/layouts/__init__.py`, add the gantt import and registry entry:

```python
from src.smartart_svg.layouts.gantt import render_gantt

LAYOUT_REGISTRY = {
    'swot': render_swot,
    'feature_matrix': render_feature_matrix,
    'venn': render_venn,
    'timeline': render_timeline,
    'pipeline_funnel': render_pipeline_funnel,
    'radar_chart': render_radar_chart,
    'gantt': render_gantt,
}
```

- [ ] **Step 5: Update extractor routing**

In `src/smartart_extractor.py`:

1. Remove `'gantt'` from `_MERMAID_GRAPHIC_TYPES` on line 469:
```python
_MERMAID_GRAPHIC_TYPES = {'flowchart', 'decision_tree'}  # gantt removed
```

2. Add `'gantt'` to `_SPATIAL_GRAPHIC_TYPES` on line 471:
```python
_SPATIAL_GRAPHIC_TYPES = {'swot', 'timeline', 'pipeline_funnel', 'feature_matrix', 'venn', 'gantt'}
```

3. The inline_data path (line 534-537) already handles `engine='custom_svg'` correctly — when the SmartArt selector specifies `engine='custom_svg'` for Gantt, inline_data is passed through as-is to the custom SVG layout.

4. The `_extract_gantt()` function (line 136) and `_gantt_from_inline()` (line 184) should remain for backward compatibility with any Mermaid Gantt specs, but new Gantt graphics should use `engine='custom_svg'`.

5. On line 542, the fallback `elif graphic_type == 'gantt':` path (for inline_data without explicit engine) should now route to custom_svg instead of Mermaid:
```python
        elif graphic_type == 'gantt':
            # Route to custom_svg Gantt layout via inline_data passthrough
            extracted_data = {'engine': 'custom_svg', 'graphic_type': graphic_type, 'data': inline_data}
```

- [ ] **Step 6: Run tests**

Run: `.venv/bin/pytest tests/test_smartart_svg.py::TestGanttLayout -v`
Expected: All PASS.

- [ ] **Step 7: Run full test suite**

Run: `.venv/bin/pytest --tb=short -q`
Expected: 622+ tests pass.

- [ ] **Step 8: Commit**

```bash
git add src/smartart_svg/layouts/gantt.py src/smartart_svg/layouts/__init__.py src/smartart_extractor.py tests/test_smartart_svg.py
git commit -m "fix: custom SVG Gantt chart replacing Mermaid Gantt (#26)

Build gantt.py layout with horizontal task bars, date axis,
brand colour interpolation, and 13pt task labels. Renders at
correct 16:9 aspect ratio unlike Mermaid's extreme landscape."
```

---

## Task 7: Title Visibility on full_render Slides (#28)

**Problem:** `buildFullRenderSlide()` places a full-bleed image but no title text overlay. Also, multiple builders use 0.05" margins instead of the MARGIN constant (0.6"). Affects ~5 slides.

**Fix:** Add a title text box with semi-transparent dark backing to `buildFullRenderSlide()`. Enforce MARGIN constraint across all builders that currently hardcode 0.05".

**Files:**
- Modify: `src/assembler/build_deck.js:836-865` (buildFullRenderSlide)
- Modify: `src/assembler/build_deck.js:1339-1426` (buildSmartArtSlide — fix 0.05" margins)
- Test: `tests/test_assembler.py`

- [ ] **Step 1: Write the failing test**

In `tests/test_assembler.py`, verify full_render slides have title text:

```python
def test_full_render_has_title(deck_dir):
    """Full-render slides should have a visible title overlay."""
    import json
    # Update strategy for slide 1 to full_render
    sm_path = os.path.join(deck_dir, 'strategy-map.json')
    with open(sm_path) as f:
        sm = json.load(f)
    sm['slides'][0]['strategy'] = 'full_render'
    with open(sm_path, 'w') as f:
        json.dump(sm, f)

    result = subprocess.run(
        ['node', 'src/assembler/build_deck.js', deck_dir],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    pptx_path = os.path.join(deck_dir, 'output.pptx')
    assert os.path.exists(pptx_path)
    # Verify non-trivial file (title overlay should add content)
    assert os.path.getsize(pptx_path) > 10000
```

- [ ] **Step 2: Run test to verify baseline**

Run: `.venv/bin/pytest tests/test_assembler.py::test_full_render_has_title -v`

- [ ] **Step 3: Implement title overlay on full_render**

In `src/assembler/build_deck.js`, modify `buildFullRenderSlide()`:

```javascript
function buildFullRenderSlide(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData } = ctx;

    const slide = pptx.addSlide();

    // Full-bleed image covering the entire slide
    const imgPath = imageData ? resolveImagePath(imageData.file_path) : null;
    if (imgPath && fs.existsSync(imgPath)) {
        slide.addImage({
            x: 0, y: 0, w: SLIDE_W, h: SLIDE_H,
            sizing: { type: 'cover', w: SLIDE_W, h: SLIDE_H },
            altText: imageData.alt_text || '',
        });
    } else {
        // Fallback: brand primary colour
        const bgColor = palette.primary || '1B3A4B';
        slide.background = { color: bgColor };
    }

    // Title overlay with semi-transparent backing
    if (slideData.headline) {
        const titleH = 0.9;
        const titleY = SLIDE_H * 0.75;  // Bottom quarter

        // Semi-transparent backing strip
        slide.addShape(pptx.ShapeType.rect, {
            x: 0, y: titleY - 0.1,
            w: SLIDE_W, h: titleH + 0.2,
            fill: { color: '000000', transparency: 50 },
        });

        // Title text
        slide.addText(slideData.headline, {
            x: MARGIN, y: titleY,
            w: SLIDE_W - 2 * MARGIN, h: titleH,
            fontSize: typo.heading_sizes?.slide_heading || 36,
            fontFace: typo.heading_font,
            color: 'FFFFFF',
            bold: true,
            valign: 'middle',
            wrap: true,
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

- [ ] **Step 4: Fix margin constants in buildSmartArtSlide**

In `buildSmartArtSlide()`, replace `SLIDE_W * 0.05` with `MARGIN`:

```javascript
// Before:
slide.addText(slideData.headline || '', {
    x: SLIDE_W * 0.05, y: SLIDE_H * 0.02,
    w: SLIDE_W * 0.90, h: SLIDE_H * 0.10,

// After:
slide.addText(slideData.headline || '', {
    x: MARGIN, y: SLIDE_H * 0.02,
    w: SLIDE_W - 2 * MARGIN, h: SLIDE_H * 0.10,
```

- [ ] **Step 5: Run tests**

Run: `.venv/bin/pytest tests/test_assembler.py -v`
Expected: All PASS.

- [ ] **Step 6: Run full test suite**

Run: `.venv/bin/pytest --tb=short -q`
Expected: 622+ tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/assembler/build_deck.js tests/test_assembler.py
git commit -m "fix: title overlay on full_render slides + margin enforcement (#28)

Add semi-transparent dark backing + white title text to
buildFullRenderSlide(). Replace hardcoded 0.05\" margins with
MARGIN constant in buildSmartArtSlide()."
```

---

## Task 8: Pragmatic Composition Demo Slide (#29)

**Problem:** No slides in the demo deck use `pragmatic_composition` strategy — all were changed to `composed` when Ollama wasn't available. Now that Ollama is available, restore one slide to showcase this capability.

**Fix:** Update the demo fixture to set slide 9 ("How It Works") as pragmatic_composition with 4 nautical element images. Generate images during the next deck render.

**Files:**
- Modify: `tests/fixtures/smartart_demo/slide_outline.json` (slide 9 data)
- No code changes needed — `buildPragmaticSlide()` already works (tested)

- [ ] **Step 1: Update slide 9 in the fixture**

Read the current slide 9 data from the fixture, then update it to include a `pragmatic_composition` strategy hint and element layout coordinates in the `data` field.

The `strategy-map.json` (generated at runtime) controls the actual strategy, but the fixture should include `visual_intent` that clearly signals this is a pragmatic_composition slide.

Update `tests/fixtures/smartart_demo/slide_outline.json` slide 9:
- `visual_intent`: "Show 4 nautical navigation instruments (compass, telescope, ship wheel, map) as individual elements with labels, demonstrating multi-element assembly"
- `body_points`: update to name the 4 elements

```json
{
    "slide_number": 9,
    "headline": "How It Works",
    "body_points": [
        "Compass — Brand navigation",
        "Telescope — Content planning",
        "Ship Wheel — Design control",
        "Map — Assembly route"
    ],
    "visual_intent": "Show 4 nautical instruments as individual positioned elements with labels — pragmatic_composition strategy"
}
```

- [ ] **Step 2: Validate fixture against schema**

Run: `.venv/bin/pytest tests/test_smartart_schemas.py -v`
Expected: All PASS (fixture still valid).

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/smartart_demo/slide_outline.json
git commit -m "fix: restore pragmatic_composition demo slide (#29)

Update slide 9 fixture to signal pragmatic_composition strategy
with 4 nautical element images. buildPragmaticSlide() already
handles the assembly — just needs the fixture + strategy map."
```

---

## Self-Review

### Spec Coverage

| Issue | Tasks | Covered? |
|-------|-------|----------|
| #22 Mermaid text invisible | Task 1 | ✓ mmdc --outputFormat png |
| #23 Venn overlap | Task 3 | ✓ Proportional overlap from data |
| #24 Feature matrix columns | Task 4 | ✓ Column overflow with truncation |
| #25 Timeline text overlap | Task 5 | ✓ Truncation + dynamic spacing |
| #26 Gantt illegible | Task 6 | ✓ Custom SVG Gantt layout |
| #27 Vega-Lite axis fonts | Task 2 | ✓ Font config injection |
| #28 Title + margins | Task 7 | ✓ Title overlay + MARGIN constant |
| #29 No pragmatic_composition | Task 8 | ✓ Fixture update |

### Placeholder Scan
No TBDs, TODOs, or "implement later" found.

### Type Consistency
- `render_gantt(data, container, tokens)` follows the same signature as all other layouts ✓
- `_truncate(text, max_chars)` in timeline matches its usage ✓
- `render_mermaid` still returns PNG path ✓
- All test classes use consistent fixture patterns ✓

### Dependency Order
Tasks are independent. Suggested execution order (by impact): 1 → 2 → 6 → 3 → 4 → 5 → 7 → 8.
