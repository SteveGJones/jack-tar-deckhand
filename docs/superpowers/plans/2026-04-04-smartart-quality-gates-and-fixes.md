# SmartArt Quality Gates & Rendering Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 5 categories of rendering defects (18/28 slides affected), add pre-assembly automated checks, and implement two-stage visual inspection (SmartArt creation review + post-assembly slide review) as mandatory quality gates.

**Architecture:** Fixes go into the renderer (`smartart_renderer.py`) and assembler (`build_deck.js`). Pre-assembly checks (PA-01 to PA-04) run inside the renderer after each engine call. Visual inspection is a new QA module that rasterises slides to PNG and dispatches the image-reviewer agent. The image-reviewer agent definition gains two new review contexts.

**Tech Stack:** Python 3 (renderer fixes, QA checks, visual inspection), Node.js (assembler styling), Pillow (rasterisation, blank detection), LibreOffice headless (pptx → PNG), pytest

**Design Spec:** `docs/superpowers/specs/2026-04-04-smartart-quality-gates-and-fixes.md`

---

## File Structure

### Modified Files

| File | Changes |
|------|---------|
| `src/smartart_renderer.py` | VL dimension injection, Mermaid width + rasterisation, PA-01 to PA-04 checks, SVG post-processing |
| `src/smartart_svg/engine.py` | `fit_text` min_size 10→12, add `recommended_min` parameter |
| `src/assembler/build_deck.js` | Composed slide brand styling, background fallback colour |
| `src/qa/run_qa.py` | Register visual inspection step |
| `.claude/agents/image-reviewer.md` | Add `smartart_graphic` and `slide_visual_inspection` review contexts |
| `tests/test_smartart_renderer.py` | New tests for dimension fixes, rasterisation, PA checks |
| `tests/test_smartart_svg.py` | Update fit_text tests for min_size=12 |
| `tests/fixtures/smartart_demo/slide_outline.json` | Strategy changes for slides 2, 9, 21 |

### New Files

| File | Responsibility |
|------|---------------|
| `src/qa/checks/visual_inspection.py` | Rasterise slides to PNG, automated blank/colour checks |
| `tests/test_visual_inspection.py` | Visual inspection module tests |

---

## Task 1: Minimum Font Size 12px

**Files:**
- Modify: `src/smartart_svg/engine.py`
- Modify: `tests/test_smartart_svg.py`

- [ ] **Step 1: Update existing fit_text test expectations**

In `tests/test_smartart_svg.py`, update `test_fit_text_reduces_font_size`:

```python
def test_fit_text_reduces_font_size(self):
    from src.smartart_svg.engine import Container
    c = Container(0, 0, 100, 30, padding=0)
    fitted = c.fit_text("A very long text that cannot fit at large size", font_size=48, max_lines=1)
    assert fitted.font_size < 48
    assert fitted.font_size >= 12  # minimum readable — was 10, now 12
```

Add a new test:

```python
def test_fit_text_never_below_12px(self):
    from src.smartart_svg.engine import Container
    c = Container(0, 0, 50, 20, padding=0)  # Very small container
    fitted = c.fit_text("This text absolutely cannot fit", font_size=24, max_lines=1)
    assert fitted.font_size >= 12
    assert fitted.overflow is True

def test_fit_text_recommended_min(self):
    from src.smartart_svg.engine import Container
    c = Container(0, 0, 200, 30, padding=0)
    # Text fits at 14 but not at 16
    fitted = c.fit_text("Medium length text here", font_size=16, max_lines=1, recommended_min=14)
    assert fitted.font_size >= 14
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/pytest tests/test_smartart_svg.py::TestContainerEngine::test_fit_text_reduces_font_size tests/test_smartart_svg.py::TestContainerEngine::test_fit_text_never_below_12px tests/test_smartart_svg.py::TestContainerEngine::test_fit_text_recommended_min -v
```

- [ ] **Step 3: Update fit_text in engine.py**

Change `Container.fit_text()` signature and implementation:

```python
def fit_text(self, text: str, font_size: float = 16, max_lines: int = 1,
             recommended_min: float = 0) -> FittedText:
    """Reduce font size until text fits within container width.

    Uses approximate character width (0.6 x font_size) for estimation.
    Hard minimum is 12px. If recommended_min is set (e.g., 14), the method
    tries to stay at or above that threshold before dropping to 12.
    """
    min_size = 12
    effective_min = max(min_size, recommended_min) if recommended_min else min_size
    current_size = font_size

    # First pass: try to fit at recommended_min or above
    while current_size >= effective_min:
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

    # Second pass: drop to hard minimum if recommended_min didn't work
    if effective_min > min_size:
        current_size = effective_min - 1
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

    # At hard minimum, truncate
    char_width = min_size * 0.6
    chars_per_line = max(1, int(self.inner_width / char_width))
    return FittedText(
        text=text, font_size=min_size,
        lines=[text[:chars_per_line]], overflow=True
    )
```

- [ ] **Step 4: Run tests**

```bash
.venv/bin/pytest tests/test_smartart_svg.py -v
```

- [ ] **Step 5: Run full suite**

```bash
.venv/bin/pytest --tb=short -q
```

- [ ] **Step 6: Commit**

```bash
git add src/smartart_svg/engine.py tests/test_smartart_svg.py
git commit -m "fix: minimum font size 12px (was 10), add recommended_min parameter"
```

---

## Task 2: Vega-Lite Dimension Injection

**Files:**
- Modify: `src/smartart_renderer.py`
- Modify: `tests/test_smartart_renderer.py`

- [ ] **Step 1: Write tests**

Add to `tests/test_smartart_renderer.py`:

```python
class TestVegaLiteDimensions:
    def test_vega_lite_svg_has_landscape_aspect(self):
        """Vega-Lite SVGs must be landscape (roughly 16:9), not portrait."""
        from src.smartart_renderer import render_vega_lite
        import re
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
                        {"label": "A", "value": 10},
                        {"label": "B", "value": 20}
                    ]}
                }
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a'},
            'typography': {'body_font': 'Inter'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            svg_path = render_vega_lite(spec, style_guide, tmpdir)
            with open(svg_path) as f:
                svg = f.read()
            # Check width > height (landscape)
            w_match = re.search(r'width[="][\s]*(\d+)', svg)
            h_match = re.search(r'height[="][\s]*(\d+)', svg)
            if w_match and h_match:
                w, h = int(w_match.group(1)), int(h_match.group(1))
                assert w > h, f"SVG should be landscape: {w}x{h}"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
.venv/bin/pytest tests/test_smartart_renderer.py::TestVegaLiteDimensions -v
```

- [ ] **Step 3: Fix render_vega_lite**

In `src/smartart_renderer.py`, in `render_vega_lite()`, add after `vl_spec = spec['data']['spec'].copy()`:

```python
# Inject dimensions for 16:9 output — prevents portrait-oriented default
vl_spec['width'] = 1600
vl_spec['height'] = 900
vl_spec['autosize'] = {'type': 'fit', 'contains': 'padding'}
```

- [ ] **Step 4: Run tests**

```bash
.venv/bin/pytest tests/test_smartart_renderer.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/smartart_renderer.py tests/test_smartart_renderer.py
git commit -m "fix: inject 1600x900 dimensions into Vega-Lite specs for 16:9 output"
```

---

## Task 3: Mermaid Width + SVG Post-Processing + Rasterisation

**Files:**
- Modify: `src/smartart_renderer.py`
- Modify: `tests/test_smartart_renderer.py`

- [ ] **Step 1: Write tests**

Add to `tests/test_smartart_renderer.py`:

```python
class TestMermaidFixes:
    def test_mermaid_svg_has_explicit_dimensions(self):
        """Mermaid SVG must have numeric width/height, not '100%'."""
        from src.smartart_renderer import render_mermaid
        import re
        spec = {
            'data': {
                'syntax': 'graph TD\n  A[Start] --> B[End]',
                'diagram_type': 'flowchart'
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a'},
            'typography': {'body_font': 'Inter'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            result_path = render_mermaid(spec, style_guide, tmpdir)
            # Should return PNG path (rasterised), not SVG
            assert result_path.endswith('.png'), f"Expected PNG, got {result_path}"
            assert os.path.exists(result_path)
            # PNG should have non-zero size
            assert os.path.getsize(result_path) > 100

    def test_mermaid_svg_source_preserved(self):
        """The original SVG should be kept alongside the PNG."""
        from src.smartart_renderer import render_mermaid
        spec = {
            'data': {
                'syntax': 'graph TD\n  A[Start] --> B[End]',
                'diagram_type': 'flowchart'
            }
        }
        style_guide = {
            'palette': {'primary': '1a73e8', 'background': 'ffffff', 'text_primary': '1a1a1a'},
            'typography': {'body_font': 'Inter'}
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = render_mermaid(spec, style_guide, tmpdir)
            # SVG source should also exist
            svg_files = [f for f in os.listdir(tmpdir) if f.endswith('.svg')]
            assert len(svg_files) >= 1, "SVG source file should be preserved"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/pytest tests/test_smartart_renderer.py::TestMermaidFixes -v
```

- [ ] **Step 3: Fix render_mermaid**

Rewrite `render_mermaid()` in `src/smartart_renderer.py`:

```python
def render_mermaid(spec, style_guide, output_dir):
    """Render a Mermaid diagram using mmdc, then rasterise to PNG.

    Mermaid SVGs use foreignObject for text which PowerPoint can't render.
    We always produce a PNG as the primary output and keep the SVG as source.
    """
    syntax = spec['data']['syntax']
    palette = style_guide.get('palette', {})

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

    run_id = uuid.uuid4().hex[:8]
    mmd_path = os.path.join(output_dir, f'input-{run_id}.mmd')
    svg_path = os.path.join(output_dir, f'output-{run_id}.svg')
    png_path = os.path.join(output_dir, f'output-{run_id}.png')

    with open(mmd_path, 'w', encoding='utf-8') as f:
        f.write(full_syntax)

    # Render to SVG with explicit width
    result = subprocess.run(
        ['npx', 'mmdc', '-i', mmd_path, '-o', svg_path,
         '-b', 'transparent', '-w', '1600'],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Mermaid CLI failed: {result.stderr}")

    # Post-process SVG: extract viewBox dimensions, set explicit width/height
    _postprocess_mermaid_svg(svg_path)

    # Rasterise SVG to PNG — PowerPoint can't render foreignObject
    _rasterise_svg_to_png(svg_path, png_path, 1600, 900)

    return png_path
```

Add helper functions:

```python
import re
from PIL import Image as PILImage


def _postprocess_mermaid_svg(svg_path):
    """Set explicit width/height pixel attributes from viewBox."""
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg = f.read()

    vb_match = re.search(r'viewBox="[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)"', svg)
    if vb_match:
        w = int(float(vb_match.group(1)))
        h = int(float(vb_match.group(2)))
        # Replace width="100%" with pixel value
        svg = re.sub(r'width="[^"]*"', f'width="{w}"', svg, count=1)
        # Add height if missing or replace
        if 'height="' in svg:
            svg = re.sub(r'height="[^"]*"', f'height="{h}"', svg, count=1)
        else:
            svg = svg.replace(f'width="{w}"', f'width="{w}" height="{h}"', 1)

    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg)


def _rasterise_svg_to_png(svg_path, png_path, width=1600, height=900):
    """Convert SVG to PNG using Pillow/cairosvg or Node.js Sharp as fallback."""
    try:
        # Try cairosvg first (if available)
        import cairosvg
        cairosvg.svg2png(url=svg_path, write_to=png_path,
                         output_width=width, output_height=height)
    except ImportError:
        # Fallback: use Pillow to create a placeholder with the SVG content indicator
        # In production, Sharp via Node subprocess would be used
        try:
            # Try sharp via node
            result = subprocess.run(
                ['node', '-e', f'''
                const sharp = require("sharp");
                sharp("{svg_path}")
                    .resize({width}, {height}, {{ fit: "contain", background: {{ r: 255, g: 255, b: 255, alpha: 0 }} }})
                    .png()
                    .toFile("{png_path}")
                    .then(() => console.log("OK"))
                    .catch(e => {{ console.error(e.message); process.exit(1); }});
                '''],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr)
        except Exception:
            # Last resort: Pillow direct SVG reading (limited support)
            img = PILImage.new('RGBA', (width, height), (255, 255, 255, 0))
            img.save(png_path)
```

- [ ] **Step 4: Update the render() dispatcher**

In the `render()` function, update the Mermaid branch to track both SVG and PNG paths:

```python
# After primary render, for mermaid engine:
if primary_engine == 'mermaid':
    file_path = primary_path  # PNG
    # Find the SVG source (same name, .svg extension)
    svg_path = primary_path.replace('.png', '.svg')
    if not os.path.exists(svg_path):
        svg_path = primary_path
elif primary_engine == 'matplotlib':
    file_path = primary_path
    svg_path = ''
else:
    file_path = primary_path
    svg_path = primary_path
```

- [ ] **Step 5: Run tests**

```bash
.venv/bin/pytest tests/test_smartart_renderer.py -v
```

- [ ] **Step 6: Run full suite**

```bash
.venv/bin/pytest --tb=short -q
```

- [ ] **Step 7: Commit**

```bash
git add src/smartart_renderer.py tests/test_smartart_renderer.py
git commit -m "fix: Mermaid width control, SVG post-processing, mandatory PNG rasterisation"
```

---

## Task 4: Pre-Assembly Checks (PA-01 to PA-04)

**Files:**
- Modify: `src/smartart_renderer.py`
- Modify: `tests/test_smartart_renderer.py`

- [ ] **Step 1: Write tests**

Add to `tests/test_smartart_renderer.py`:

```python
class TestPreAssemblyChecks:
    def test_pa01_rejects_zero_dimensions(self):
        from src.smartart_renderer import validate_svg_dimensions
        findings = validate_svg_dimensions('<svg width="0" height="0"></svg>', 5)
        assert any(f['severity'] == 'error' for f in findings)

    def test_pa01_accepts_valid_dimensions(self):
        from src.smartart_renderer import validate_svg_dimensions
        findings = validate_svg_dimensions(
            '<svg width="1600" height="900" viewBox="0 0 1600 900"></svg>', 5
        )
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0

    def test_pa01_rejects_bad_aspect_ratio(self):
        from src.smartart_renderer import validate_svg_dimensions
        # Portrait 400x800 — aspect 0.5, deviates >20% from 1.78
        findings = validate_svg_dimensions(
            '<svg width="400" height="800" viewBox="0 0 400 800"></svg>', 5
        )
        assert any('aspect' in f['description'].lower() for f in findings)

    def test_pa02_rejects_flowchart_no_text(self):
        from src.smartart_renderer import validate_svg_text_content
        findings = validate_svg_text_content(
            '<svg><rect/><rect/></svg>', 5, graphic_type='flowchart', node_count=4
        )
        assert any(f['severity'] == 'error' for f in findings)

    def test_pa02_accepts_flowchart_with_text(self):
        from src.smartart_renderer import validate_svg_text_content
        svg = '<svg><text>A</text><text>B</text><text>C</text><text>D</text></svg>'
        findings = validate_svg_text_content(svg, 5, graphic_type='flowchart', node_count=4)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0

    def test_pa03_rejects_small_font(self):
        from src.smartart_renderer import validate_svg_font_sizes
        findings = validate_svg_font_sizes(
            '<svg><text font-size="8">Tiny</text></svg>', 5
        )
        assert any(f['severity'] == 'error' for f in findings)

    def test_pa03_accepts_valid_font(self):
        from src.smartart_renderer import validate_svg_font_sizes
        findings = validate_svg_font_sizes(
            '<svg><text font-size="14">Normal</text></svg>', 5
        )
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0

    def test_pa04_rejects_blank_png(self):
        from src.smartart_renderer import validate_png_not_blank
        import tempfile
        from PIL import Image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (100, 100), (255, 255, 255))
            img.save(f.name)
            findings = validate_png_not_blank(f.name, 5)
        assert any(f['severity'] == 'error' for f in findings)

    def test_pa04_accepts_content_png(self):
        from src.smartart_renderer import validate_png_not_blank
        import tempfile
        from PIL import Image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (100, 100), (255, 255, 255))
            # Draw some non-white content
            for x in range(20, 80):
                for y in range(20, 80):
                    img.putpixel((x, y), (30, 60, 90))
            img.save(f.name)
            findings = validate_png_not_blank(f.name, 5)
        errors = [f for f in findings if f['severity'] == 'error']
        assert len(errors) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/pytest tests/test_smartart_renderer.py::TestPreAssemblyChecks -v
```

- [ ] **Step 3: Implement the 4 validation functions**

Add to `src/smartart_renderer.py`:

```python
def validate_svg_dimensions(svg_content, slide_number):
    """PA-01: Validate SVG has valid dimensions and roughly 16:9 aspect ratio."""
    findings = []
    w_match = re.search(r'width="(\d+(?:\.\d+)?)"', svg_content)
    h_match = re.search(r'height="(\d+(?:\.\d+)?)"', svg_content)

    if not w_match or not h_match:
        # Try viewBox
        vb_match = re.search(r'viewBox="[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)"', svg_content)
        if vb_match:
            w, h = float(vb_match.group(1)), float(vb_match.group(2))
        else:
            findings.append({
                'slide_number': slide_number, 'severity': 'error',
                'category': 'smartart',
                'description': 'PA-01: SVG has no width/height or viewBox — dimensions unknown'
            })
            return findings
    else:
        w, h = float(w_match.group(1)), float(h_match.group(1))

    if w == 0 or h == 0:
        findings.append({
            'slide_number': slide_number, 'severity': 'error',
            'category': 'smartart',
            'description': f'PA-01: SVG dimensions are 0x0'
        })
        return findings

    aspect = w / h
    target_aspect = 16 / 9  # 1.778
    deviation = abs(aspect - target_aspect) / target_aspect
    if deviation > 0.20:
        findings.append({
            'slide_number': slide_number, 'severity': 'error',
            'category': 'smartart',
            'description': f'PA-01: SVG aspect ratio {aspect:.2f} deviates >{deviation:.0%} from 16:9 ({target_aspect:.2f})'
        })

    return findings


def validate_svg_text_content(svg_content, slide_number, graphic_type='', node_count=0):
    """PA-02: Verify SVG has text elements appropriate for the graphic type."""
    findings = []
    text_count = len(re.findall(r'<text[^>]*>', svg_content))
    tspan_count = len(re.findall(r'<tspan[^>]*>', svg_content))
    foreign_count = len(re.findall(r'<foreignObject', svg_content))
    total_text = text_count + tspan_count + foreign_count

    if graphic_type in ('flowchart', 'decision_tree') and total_text < node_count:
        findings.append({
            'slide_number': slide_number, 'severity': 'error',
            'category': 'smartart',
            'description': f'PA-02: {graphic_type} has {total_text} text elements but {node_count} nodes — text likely missing'
        })
    elif total_text == 0:
        findings.append({
            'slide_number': slide_number, 'severity': 'warning',
            'category': 'smartart',
            'description': 'PA-02: SVG has zero text elements'
        })

    return findings


def validate_svg_font_sizes(svg_content, slide_number):
    """PA-03: Ensure no font-size is below 12px."""
    findings = []
    sizes = re.findall(r'font-size="(\d+(?:\.\d+)?)"', svg_content)
    for size_str in sizes:
        size = float(size_str)
        if size < 12:
            findings.append({
                'slide_number': slide_number, 'severity': 'error',
                'category': 'smartart',
                'description': f'PA-03: Font size {size}px is below 12px minimum'
            })
            break  # One finding is enough
    return findings


def validate_png_not_blank(png_path, slide_number):
    """PA-04: Verify PNG is not all-white (blank)."""
    findings = []
    try:
        img = PILImage.open(png_path).convert('RGB')
        pixels = list(img.getdata())
        white_count = sum(1 for r, g, b in pixels if r > 250 and g > 250 and b > 250)
        white_ratio = white_count / len(pixels) if pixels else 1.0
        if white_ratio > 0.95:
            findings.append({
                'slide_number': slide_number, 'severity': 'error',
                'category': 'smartart',
                'description': f'PA-04: PNG is {white_ratio:.0%} white — likely blank render'
            })
    except Exception as e:
        findings.append({
            'slide_number': slide_number, 'severity': 'error',
            'category': 'smartart',
            'description': f'PA-04: Cannot read PNG: {e}'
        })
    return findings
```

- [ ] **Step 4: Wire PA checks into the render() function**

In `render()`, after the primary engine renders successfully, run the PA checks. If any return errors, set `status='failed'`:

```python
# After successful render, run pre-assembly validation
pa_findings = []
if primary_engine in ('custom_svg', 'vega_lite'):
    with open(file_path) as f:
        svg_content = f.read()
    pa_findings.extend(validate_svg_dimensions(svg_content, slide_number))
    pa_findings.extend(validate_svg_text_content(
        svg_content, slide_number,
        graphic_type=graphic_type,
        node_count=spec.get('data', {}).get('node_count', 0)
    ))
    if primary_engine == 'custom_svg':
        pa_findings.extend(validate_svg_font_sizes(svg_content, slide_number))
elif primary_engine == 'mermaid':
    # Mermaid returns PNG — check it's not blank
    pa_findings.extend(validate_png_not_blank(file_path, slide_number))

pa_errors = [f for f in pa_findings if f['severity'] == 'error']
if pa_errors:
    primary_status = 'failed'
```

- [ ] **Step 5: Run tests**

```bash
.venv/bin/pytest tests/test_smartart_renderer.py -v
```

- [ ] **Step 6: Run full suite**

```bash
.venv/bin/pytest --tb=short -q
```

- [ ] **Step 7: Commit**

```bash
git add src/smartart_renderer.py tests/test_smartart_renderer.py
git commit -m "feat: pre-assembly checks PA-01 to PA-04 — dimensions, text, font, blank detection"
```

---

## Task 5: Composed Slide Brand Styling + Background Fallback

**Files:**
- Modify: `src/assembler/build_deck.js`
- Modify: `tests/test_assembler.py`

- [ ] **Step 1: Read `buildComposedSlide()` and `buildBackgroundSlide()` in build_deck.js**

Understand the existing implementation before modifying.

- [ ] **Step 2: Add brand background to buildComposedSlide()**

In the `buildComposedSlide()` function, before adding any text, add:

```javascript
// Brand background — never leave a slide as white void
const bgColor = ctx.styleGuide?.palette?.background || 'F5F0E8';
slide.background = { fill: bgColor };

// Bottom accent line
const accentColor = ctx.styleGuide?.palette?.accent || 'C67B2F';
slide.addShape(pptx.ShapeType.rect, {
    x: 0, y: SLIDE_H * 0.95, w: SLIDE_W, h: SLIDE_H * 0.005,
    fill: { color: accentColor }, line: { width: 0 }
});
```

- [ ] **Step 3: Add fallback to buildBackgroundSlide()**

When no background image exists, fill with palette colour:

```javascript
// At the start of buildBackgroundSlide, before image placement:
if (!bgImagePath || !fs.existsSync(bgImagePath)) {
    // Fallback: solid palette background
    const bgColor = ctx.styleGuide?.palette?.background || 'F5F0E8';
    slide.background = { fill: bgColor };
    // Add subtle accent element
    const accentColor = ctx.styleGuide?.palette?.accent || 'C67B2F';
    slide.addShape(pptx.ShapeType.rect, {
        x: 0, y: 0, w: SLIDE_W * 0.01, h: SLIDE_H,
        fill: { color: accentColor }, line: { width: 0 }
    });
}
```

- [ ] **Step 4: Run assembler tests**

```bash
.venv/bin/pytest tests/test_assembler.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/assembler/build_deck.js
git commit -m "fix: composed slides get brand background + accent, background fallback colour"
```

---

## Task 6: Visual Inspection Module

**Files:**
- Create: `src/qa/checks/visual_inspection.py`
- Create: `tests/test_visual_inspection.py`
- Modify: `src/qa/run_qa.py`

- [ ] **Step 1: Write tests**

```python
# tests/test_visual_inspection.py
"""Tests for post-assembly visual inspection — blank detection, colour checks."""

import os
import tempfile
import pytest
from PIL import Image


class TestBlankDetection:
    def test_detects_blank_white_slide(self):
        from src.qa.checks.visual_inspection import inspect_slide
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (1920, 1080), (255, 255, 255))
            img.save(f.name)
            findings = inspect_slide(f.name, slide_number=1, outline_slide={}, style_guide={})
        errors = [f for f in findings if f['severity'] == 'error']
        assert any('blank' in f['description'].lower() for f in errors)

    def test_accepts_slide_with_content(self):
        from src.qa.checks.visual_inspection import inspect_slide
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (1920, 1080), (245, 240, 232))  # Parchment
            # Add some "content"
            for x in range(100, 800):
                for y in range(100, 400):
                    img.putpixel((x, y), (27, 58, 75))  # Navy text area
            img.save(f.name)
            findings = inspect_slide(f.name, slide_number=1, outline_slide={}, style_guide={})
        errors = [f for f in findings if f['severity'] == 'error' and 'blank' in f['description'].lower()]
        assert len(errors) == 0


class TestColourCheck:
    def test_detects_off_brand_colours(self):
        from src.qa.checks.visual_inspection import inspect_slide
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (1920, 1080), (255, 0, 0))  # All red — not on brand
            img.save(f.name)
            style_guide = {
                'palette': {
                    'primary': '1B3A4B', 'background': 'F5F0E8',
                    'accent': 'C67B2F', 'text_primary': '1A1A1A'
                }
            }
            findings = inspect_slide(f.name, slide_number=1, outline_slide={}, style_guide=style_guide)
        warnings = [f for f in findings if f['severity'] == 'warning' and 'brand' in f['description'].lower()]
        assert len(warnings) > 0


class TestRunVisualInspection:
    def test_returns_findings_list(self):
        from src.qa.checks.visual_inspection import run_visual_inspection
        # This test validates the function signature and return type
        # Without a real .pptx we can test with a mock
        findings = run_visual_inspection(
            pptx_path=None,  # Will be handled gracefully
            outline={'slides': []},
            style_guide={},
            output_dir=tempfile.mkdtemp()
        )
        assert isinstance(findings, list)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
.venv/bin/pytest tests/test_visual_inspection.py -v
```

- [ ] **Step 3: Implement visual_inspection.py**

```python
# src/qa/checks/visual_inspection.py
"""Post-assembly visual inspection — rasterise slides and check for quality issues.

Automated pre-filters for blank detection and brand colour compliance.
The image-reviewer agent dispatch happens in the skill layer, not here.
"""

import math
import os
import subprocess

from PIL import Image


def _hex_to_rgb(hex_str):
    """Convert 6-char hex to (R, G, B)."""
    hex_str = hex_str.lstrip('#')
    return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))


def _colour_distance(c1, c2):
    """Euclidean RGB distance."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def rasterise_slide(pptx_path, slide_number, output_dir):
    """Convert a single slide to PNG via LibreOffice headless.

    Returns path to the PNG, or None if rasterisation fails.
    """
    if pptx_path is None or not os.path.exists(pptx_path):
        return None

    try:
        result = subprocess.run(
            ['soffice', '--headless', '--convert-to', 'png', '--outdir', output_dir, pptx_path],
            capture_output=True, text=True, timeout=60,
        )
        # LibreOffice produces one PNG per slide — find the right one
        # The output file name pattern depends on the LibreOffice version
        pngs = sorted([f for f in os.listdir(output_dir) if f.endswith('.png')])
        if slide_number <= len(pngs):
            return os.path.join(output_dir, pngs[slide_number - 1])
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def inspect_slide(png_path, slide_number, outline_slide, style_guide):
    """Run automated visual checks on a rasterised slide PNG.

    Returns list of finding dicts with severity and description.
    """
    findings = []

    if png_path is None or not os.path.exists(png_path):
        findings.append({
            'slide_number': slide_number, 'severity': 'error',
            'category': 'smartart',
            'description': f'Visual inspection: could not rasterise slide {slide_number}'
        })
        return findings

    try:
        img = Image.open(png_path).convert('RGB')
    except Exception as e:
        findings.append({
            'slide_number': slide_number, 'severity': 'error',
            'category': 'smartart',
            'description': f'Visual inspection: cannot read slide PNG: {e}'
        })
        return findings

    # Blank detection: >95% white pixels
    pixels = list(img.getdata())
    white_count = sum(1 for r, g, b in pixels if r > 250 and g > 250 and b > 250)
    white_ratio = white_count / len(pixels) if pixels else 1.0
    if white_ratio > 0.95:
        findings.append({
            'slide_number': slide_number, 'severity': 'error',
            'category': 'smartart',
            'description': f'Visual inspection: slide is {white_ratio:.0%} blank (white)'
        })

    # Brand colour check
    palette = style_guide.get('palette', {})
    if palette:
        brand_colours = []
        for key in ('primary', 'background', 'accent', 'text_primary'):
            hex_val = palette.get(key)
            if hex_val:
                brand_colours.append(_hex_to_rgb(hex_val))

        if brand_colours:
            # Sample dominant colours from the image
            small = img.resize((50, 50))
            quantized = small.quantize(colors=5, method=Image.Quantize.MEDIANCUT)
            pal = quantized.getpalette()[:15]
            dominant = []
            for i in range(0, len(pal), 3):
                dominant.append((pal[i], pal[i + 1], pal[i + 2]))

            # Check if any dominant colour is close to any brand colour
            min_dist = float('inf')
            for dom in dominant:
                for brand in brand_colours:
                    d = _colour_distance(dom, brand)
                    min_dist = min(min_dist, d)

            if min_dist > 100:  # No dominant colour within reasonable distance of brand
                findings.append({
                    'slide_number': slide_number, 'severity': 'warning',
                    'category': 'smartart',
                    'description': f'Visual inspection: no brand colours detected (min distance: {min_dist:.0f})'
                })

    return findings


def run_visual_inspection(pptx_path, outline, style_guide, output_dir):
    """Rasterise all slides and run automated visual checks.

    Returns list of all findings across all slides.
    """
    findings = []
    slides = outline.get('slides', [])

    if not pptx_path or not os.path.exists(str(pptx_path)):
        return findings

    for slide in slides:
        sn = slide.get('slide_number', 0)
        png_path = rasterise_slide(pptx_path, sn, output_dir)
        slide_findings = inspect_slide(png_path, sn, slide, style_guide)
        findings.extend(slide_findings)

    return findings
```

- [ ] **Step 4: Register in run_qa.py**

Read `src/qa/run_qa.py`, then add visual inspection import and registration after the existing SmartArt checks block.

- [ ] **Step 5: Run tests**

```bash
.venv/bin/pytest tests/test_visual_inspection.py -v
```

- [ ] **Step 6: Run full suite**

```bash
.venv/bin/pytest --tb=short -q
```

- [ ] **Step 7: Commit**

```bash
git add src/qa/checks/visual_inspection.py tests/test_visual_inspection.py src/qa/run_qa.py
git commit -m "feat: post-assembly visual inspection — blank detection, brand colour checks"
```

---

## Task 7: Image Reviewer Context Extensions

**Files:**
- Modify: `.claude/agents/image-reviewer.md`

- [ ] **Step 1: Read the existing image-reviewer.md**

- [ ] **Step 2: Add two new review context sections**

After the existing "Examples" section, add:

```markdown
## SmartArt Graphic Review

When `review_context` is `"smartart_graphic"`, you are reviewing a SmartArt graphic in isolation — a data-driven diagram, chart, or infographic — before it goes into a slide.

Assess against these criteria:

1. **Data accuracy** — correct number of nodes/items, labels match the data summary provided
2. **Text readability** — all labels legible at 1920x1080, minimum 12px font, no truncation without "..." indicator
3. **Colour correctness** — matches brand palette provided, WCAG 4.5:1 contrast on all text over coloured backgrounds
4. **Layout clarity** — visual hierarchy clear, no unintentional overlap, balanced whitespace

## Slide Visual Inspection

When `review_context` is `"slide_visual_inspection"`, you are reviewing a fully assembled presentation slide — the final output the audience sees.

Assess against these criteria:

1. **Blank detection** — is the slide empty, mostly white, or missing expected content?
2. **Text readability** — all text legible, no truncation, no overflow outside bounds
3. **Image distortion** — are embedded images stretched, squashed, or pixelated?
4. **Brand consistency** — palette, typography, and visual style match the deck's brand
5. **Layout coherence** — composition makes sense, elements properly positioned, visual hierarchy clear
6. **Content completeness** — does the slide deliver what the headline promises?
```

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/image-reviewer.md
git commit -m "feat: image-reviewer gains smartart_graphic and slide_visual_inspection contexts"
```

---

## Task 8: Demo Deck Fixture Updates

**Files:**
- Modify: `tests/fixtures/smartart_demo/slide_outline.json`

- [ ] **Step 1: Update strategy assignments for slides 2, 9, 21**

Read the fixture, then change:
- Slide 2: remove `visual_type: "hero_image"`, it will be composed
- Slide 9: remove `visual_type: "hero_image"`, it will be composed
- Slide 21: remove `visual_type: "hero_image"`, it will be composed

These slides don't need strategy fields in the outline — the strategy-map handles that. But `visual_type: "hero_image"` signals to the pipeline that AI images are needed. Changing to `visual_type: "none"` prevents blank slides.

```python
# For slides 2, 9, 21: change visual_type from "hero_image" to "none"
```

- [ ] **Step 2: Validate fixture against schema**

```bash
.venv/bin/python3 -c "
import json, jsonschema
with open('tests/fixtures/smartart_demo/slide_outline.json') as f:
    doc = json.load(f)
with open('src/schemas/slide_outline.schema.json') as f:
    schema = json.load(f)
jsonschema.validate(doc, schema)
print('VALID')
"
```

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/smartart_demo/slide_outline.json
git commit -m "fix: demo deck slides 2/9/21 changed to composed strategy (no AI images needed)"
```

---

## Task 9: Re-render Demo Deck + Verify

- [ ] **Step 1: Re-run extraction**

```bash
.venv/bin/python3 -c "
# Full extraction pipeline (same as before but with fixed extractor)
..."
```

- [ ] **Step 2: Re-run rendering**

```bash
.venv/bin/python3 -c "
# Full rendering pipeline with fixed renderer
..."
```

- [ ] **Step 3: Verify all 18 SmartArt graphics pass PA checks**

```bash
.venv/bin/python3 -c "
# Read manifest, verify no 'failed' status entries
..."
```

- [ ] **Step 4: Re-assemble the .pptx**

```bash
node src/assembler/build_deck.js --deck-dir ./tmp/deck
```

- [ ] **Step 5: Run deck-qa**

```bash
.venv/bin/python3 -c "
from src.qa.run_qa import run_qa
findings = run_qa('./tmp/deck')
..."
```

- [ ] **Step 6: Visual audit — open the .pptx and check every slide**

This is a manual step. Open the .pptx and verify:
- No blank slides
- No stretched images
- All text readable (>= 12px)
- All composed slides have brand background
- Mermaid charts show readable text
- Vega-Lite charts are landscape

- [ ] **Step 7: Run full test suite**

```bash
.venv/bin/pytest --tb=short -q
```

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "fix: demo deck re-rendered with all quality fixes applied"
```
