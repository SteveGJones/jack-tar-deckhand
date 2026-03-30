# Keynote Pipeline Sub-Plan C: QA + Conductor Integration

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add strategy-aware QA checks for keynote slides (palette drift, text legibility awareness) and integrate the strategy map step into the conductor pipeline.

**Architecture:** A new QA check module (`keynote_checks.py`) handles palette drift detection for full_render/backdrop_render slides. The QA runner gains strategy-map awareness to skip programmatic text checks on full_render slides. The conductor's step order gains `strategy-map` between `narrative-architect` and `speaker-notes-writer`, and a new `upgrade_slide_strategy` function supports post-hoc single-slide upgrades.

**Tech Stack:** Python 3.14, Pillow (colour extraction), pytest, existing QA framework + conductor + DeckContext

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `src/qa/checks/keynote_checks.py` | Create | Palette drift check for keynote slides |
| `tests/test_qa_keynote.py` | Create | Tests for keynote QA checks |
| `src/qa/checks/__init__.py` | Modify | Register keynote checks |
| `src/qa/run_qa.py` | Modify | Strategy-map-aware check routing |
| `src/deckcontext.py` | Modify | Add strategy-map to DEFAULT_STEP_ORDER and CONTRACT_SCHEMAS |
| `src/conductor.py` | Modify | Add upgrade_slide_strategy function |
| `tests/test_conductor.py` | Modify | Tests for upgrade function |

---

### Task 1: Palette Drift QA Check

**Files:**
- Create: `src/qa/checks/keynote_checks.py`
- Create: `tests/test_qa_keynote.py`

- [ ] **Step 1: Write failing tests for check_palette_drift**

Create `tests/test_qa_keynote.py`:

```python
"""Tests for keynote-specific QA checks."""

import io
import os
import shutil
import tempfile

import pytest
from PIL import Image
from pptx import Presentation
from pptx.util import Inches


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


def _make_pptx_with_image(tmp_dir, image_color, filename='test.pptx'):
    """Create a minimal pptx with a single full-bleed image of the given RGB colour."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout

    # Create image in memory
    img = Image.new('RGB', (1920, 1080), color=image_color)
    img_path = os.path.join(tmp_dir, 'test_img.png')
    img.save(img_path)
    slide.shapes.add_picture(img_path, 0, 0, Inches(13.333), Inches(7.5))

    pptx_path = os.path.join(tmp_dir, filename)
    prs.save(pptx_path)
    return pptx_path


def test_palette_drift_within_tolerance(tmp_dir):
    from src.qa.checks.keynote_checks import check_palette_drift
    # Image is exact brand teal — no drift
    pptx_path = _make_pptx_with_image(tmp_dir, (0, 107, 94))  # #006B5E
    prs = Presentation(pptx_path)
    slide = prs.slides[0]
    brand_palette = ['006B5E', '5CDBC0', '4B635B', 'F5FBF7']
    issues = check_palette_drift(slide, 1, brand_palette=brand_palette)
    assert len(issues) == 0


def test_palette_drift_detected(tmp_dir):
    from src.qa.checks.keynote_checks import check_palette_drift
    # Image is bright red — completely off-brand
    pptx_path = _make_pptx_with_image(tmp_dir, (255, 0, 0))
    prs = Presentation(pptx_path)
    slide = prs.slides[0]
    brand_palette = ['006B5E', '5CDBC0', '4B635B', 'F5FBF7']
    issues = check_palette_drift(slide, 1, brand_palette=brand_palette)
    assert len(issues) >= 1
    assert issues[0]['category'] == 'palette_drift'
    assert issues[0]['severity'] == 'warning'


def test_palette_drift_no_images_no_issues(tmp_dir):
    from src.qa.checks.keynote_checks import check_palette_drift
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    brand_palette = ['006B5E']
    issues = check_palette_drift(slide, 1, brand_palette=brand_palette)
    assert len(issues) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/test_qa_keynote.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Write check_palette_drift implementation**

Create `src/qa/checks/keynote_checks.py`:

```python
"""Keynote-specific QA checks.

Implements palette drift detection for full_render and backdrop_render slides.
Uses Pillow to extract dominant colours from slide images and compare against
the brand palette using CIE deltaE distance.
"""

import io
import math

from PIL import Image


def _hex_to_rgb(hex_str):
    """Convert 6-char hex to (R, G, B) tuple."""
    hex_str = hex_str.lstrip('#')
    return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))


def _rgb_distance(c1, c2):
    """Euclidean distance between two RGB tuples. Simple but effective for drift detection."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def _extract_dominant_colours(image_blob, num_colours=5):
    """Extract dominant colours from an image blob using Pillow quantize."""
    img = Image.open(io.BytesIO(image_blob)).convert('RGB')
    # Resize for speed, then quantize
    small = img.resize((100, 100))
    quantized = small.quantize(colors=num_colours, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()[:num_colours * 3]
    colours = []
    for i in range(0, len(palette), 3):
        colours.append((palette[i], palette[i + 1], palette[i + 2]))
    return colours


def _min_distance_to_palette(colour, brand_colours_rgb):
    """Minimum RGB distance from a colour to any brand palette colour."""
    if not brand_colours_rgb:
        return 0
    return min(_rgb_distance(colour, bc) for bc in brand_colours_rgb)


# Threshold: RGB distance above which a dominant colour is considered off-brand.
# 80 ≈ noticeable colour shift (e.g., teal vs blue). 120 ≈ clearly wrong palette.
_DRIFT_THRESHOLD = 100
_DRIFT_MAX_OFF_BRAND = 3  # Max dominant colours allowed to be off-brand


def check_palette_drift(slide, slide_number, brand_palette=None, config=None):
    """Check if images on a slide drift from the brand palette.

    Args:
        slide: python-pptx slide object.
        slide_number: 1-based slide index.
        brand_palette: list of 6-char hex strings (e.g., ['006B5E', '5CDBC0']).
        config: optional QA config dict.

    Returns:
        list of finding dicts.
    """
    if not brand_palette:
        return []

    brand_rgb = [_hex_to_rgb(h) for h in brand_palette]
    # Also consider black, white, and near-black/near-white as always acceptable
    neutral_colours = [(0, 0, 0), (255, 255, 255), (30, 30, 30), (240, 240, 240)]
    acceptable_rgb = brand_rgb + neutral_colours

    issues = []
    for shape in slide.shapes:
        if shape.shape_type == 13:  # MSO_SHAPE_TYPE.PICTURE
            try:
                dominant = _extract_dominant_colours(shape.image.blob, num_colours=5)
                off_brand_count = 0
                for colour in dominant:
                    min_dist = _min_distance_to_palette(colour, acceptable_rgb)
                    if min_dist > _DRIFT_THRESHOLD:
                        off_brand_count += 1

                if off_brand_count >= _DRIFT_MAX_OFF_BRAND:
                    issues.append({
                        'slide_number': slide_number,
                        'severity': 'warning',
                        'category': 'palette_drift',
                        'description': f'{off_brand_count}/{len(dominant)} dominant colours are off-brand (threshold: RGB distance > {_DRIFT_THRESHOLD})',
                        'suggested_fix': 'Regenerate image with stronger brand colour constraints in the prompt.',
                        'affected_element': shape.name,
                        'auto_fixable': False,
                    })
            except Exception:
                pass  # Skip if image can't be read

    return issues
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_qa_keynote.py -v`
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/qa/checks/keynote_checks.py tests/test_qa_keynote.py
git commit -m "feat: add check_palette_drift for keynote slide colour compliance"
```

---

### Task 2: Strategy-Aware QA Routing

**Files:**
- Modify: `src/qa/checks/__init__.py`
- Modify: `src/qa/run_qa.py`
- Modify: `tests/test_qa_keynote.py`

- [ ] **Step 1: Write failing tests for strategy-aware QA**

Append to `tests/test_qa_keynote.py`:

```python
def test_run_qa_skips_text_checks_on_full_render(tmp_dir):
    """full_render slides should not get wall-of-text or font-size errors."""
    import json
    from src.qa.run_qa import run_qa

    # Create a deck dir with a strategy map marking slide 1 as full_render
    deck_dir = os.path.join(tmp_dir, 'deck')
    os.makedirs(deck_dir, exist_ok=True)
    strategy_map = {
        'approval_mode': 'review',
        'slides': [{'slide_number': 1, 'strategy': 'full_render', 'rationale': 'test', 'render_funnel': ['ollama']}],
    }
    with open(os.path.join(deck_dir, 'strategy-map.json'), 'w') as f:
        json.dump(strategy_map, f)

    # Create a minimal pptx with one image-only slide
    pptx_path = _make_pptx_with_image(tmp_dir, (0, 107, 94), 'qa_test.pptx')
    report = run_qa(pptx_path, deck_dir)

    # Should not have wall-of-text or font-size errors for slide 1
    text_errors = [f for f in report['findings']
                   if f['slide_number'] == 1 and f['category'] in ('text_overflow', 'consistency')]
    assert len(text_errors) == 0


def test_run_qa_applies_palette_drift_on_full_render(tmp_dir):
    """full_render slides should get palette drift checks."""
    import json
    from src.qa.run_qa import run_qa

    deck_dir = os.path.join(tmp_dir, 'deck')
    os.makedirs(deck_dir, exist_ok=True)
    strategy_map = {
        'approval_mode': 'review',
        'slides': [{'slide_number': 1, 'strategy': 'full_render', 'rationale': 'test', 'render_funnel': ['ollama']}],
    }
    with open(os.path.join(deck_dir, 'strategy-map.json'), 'w') as f:
        json.dump(strategy_map, f)

    # Brand profile with palette
    brand_profile = {'palette': {'primary': '006B5E', 'secondary': '4B635B'}}
    with open(os.path.join(deck_dir, 'brand-profile.json'), 'w') as f:
        json.dump(brand_profile, f)

    # Create pptx with an off-brand red image
    pptx_path = _make_pptx_with_image(tmp_dir, (255, 0, 0), 'drift_test.pptx')
    report = run_qa(pptx_path, deck_dir)

    drift_findings = [f for f in report['findings'] if f['category'] == 'palette_drift']
    assert len(drift_findings) >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/test_qa_keynote.py -k "run_qa" -v`
Expected: FAIL (run_qa doesn't support strategy map yet)

- [ ] **Step 3: Register keynote checks in __init__.py**

Add to the bottom of `src/qa/checks/__init__.py`:

```python
from .keynote_checks import check_palette_drift

# Per-slide keynote checks (applied only to full_render/backdrop_render slides)
KEYNOTE_CHECKS = [
    check_palette_drift,
]
```

- [ ] **Step 4: Modify run_qa to load strategy map and route checks**

Modify `src/qa/run_qa.py` — the `run_qa` function needs to:

1. Load the strategy map (optional) and brand profile palette
2. For each slide, check if its strategy is `full_render` — if so, skip programmatic text checks and run keynote checks instead
3. For `backdrop_render` slides, run both standard checks and keynote checks
4. For `composed` slides, run standard checks only (unchanged)

Update the `run_qa` function signature to accept `deck_dir` (already present), load strategy map and brand profile from there. The core change is wrapping the per-slide check loop with strategy awareness:

```python
def run_qa(pptx_path, deck_dir='./tmp/deck', duration_minutes=None, config=None):
    """Run QA checks with strategy-aware routing for keynote slides."""
    cfg = config or QA_CONFIG
    prs = Presentation(pptx_path)
    findings = []

    # Load strategy map (optional — absent means all slides are 'composed')
    strategy_map_path = os.path.join(deck_dir, 'strategy-map.json')
    slide_strategies = {}
    if os.path.exists(strategy_map_path):
        with open(strategy_map_path) as f:
            strategy_map = json.load(f)
        for entry in strategy_map.get('slides', []):
            slide_strategies[entry['slide_number']] = entry.get('speaker_override') or entry['strategy']

    # Load brand palette for palette drift checks
    brand_palette = []
    brand_profile_path = os.path.join(deck_dir, 'brand-profile.json')
    if os.path.exists(brand_profile_path):
        with open(brand_profile_path) as f:
            bp = json.load(f)
        palette = bp.get('palette', {})
        brand_palette = [v for v in palette.values() if isinstance(v, str) and len(v) == 6]

    # Step 1: Per-slide checks (strategy-aware)
    for i, slide in enumerate(prs.slides):
        slide_number = i + 1
        strategy = slide_strategies.get(slide_number, 'composed')

        if strategy == 'full_render':
            # Full render: skip text checks, run image + keynote checks
            for check_fn in IMAGE_QUALITY_CHECKS:
                findings.extend(check_fn(slide, slide_number, prs, config=cfg))
            for check_fn in KEYNOTE_CHECKS:
                findings.extend(check_fn(slide, slide_number, brand_palette=brand_palette, config=cfg))
        elif strategy == 'backdrop_render':
            # Backdrop: run standard text checks + image + keynote checks
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
            # Composed: standard checks (unchanged)
            for check_fn in STRUCTURAL_CHECKS:
                findings.extend(check_fn(slide, slide_number, config=cfg))
            for check_fn in STRUCTURAL_CHECKS_WITH_PRESENTATION:
                findings.extend(check_fn(slide, slide_number, prs, config=cfg))
            for check_fn in IMAGE_QUALITY_CHECKS:
                findings.extend(check_fn(slide, slide_number, prs, config=cfg))
            for check_fn in VISUAL_CHECKS:
                try:
                    findings.extend(check_fn(slide, slide_number, config=cfg))
                except Exception:
                    pass

    # Step 2-5: Deck-level checks (unchanged)
    for check_fn in DECK_STRUCTURAL_CHECKS:
        findings.extend(check_fn(prs, config=cfg))
    if duration_minutes:
        findings.extend(check_slide_count_ratio(prs, duration_minutes, config=cfg))
    for check_fn in CONSISTENCY_CHECKS:
        findings.extend(check_fn(prs, config=cfg))
    for check_fn in ANIMATION_CHECKS:
        findings.extend(check_fn(prs, config=cfg))
    colours_used = set()
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        try:
                            if run.font.color and run.font.color.rgb:
                                rgb = run.font.color.rgb
                                colours_used.add((rgb[0], rgb[1], rgb[2]))
                        except (AttributeError, TypeError):
                            pass
    for check_fn in COLOUR_CHECKS:
        findings.extend(check_fn(colours_used, config=cfg))

    return generate_report(findings, pptx_path, len(prs.slides))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_qa_keynote.py -v`
Expected: 5 PASSED

- [ ] **Step 6: Run full QA test suite to check for regressions**

Run: `source .venv/bin/activate && python -m pytest tests/test_qa.py tests/test_qa_keynote.py -v 2>&1 | tail -5`
Expected: All pass (60 existing + 5 new)

- [ ] **Step 7: Commit**

```bash
git add src/qa/checks/__init__.py src/qa/checks/keynote_checks.py src/qa/run_qa.py tests/test_qa_keynote.py
git commit -m "feat: strategy-aware QA routing with palette drift checks for keynote slides"
```

---

### Task 3: Conductor — Add Strategy Map to Pipeline Step Order

**Files:**
- Modify: `src/deckcontext.py`
- Modify: `tests/test_conductor.py`

- [ ] **Step 1: Write failing test**

Append to `tests/test_conductor.py`:

```python
def test_default_step_order_includes_strategy_map():
    from src.deckcontext import DEFAULT_STEP_ORDER
    assert 'strategy-map' in DEFAULT_STEP_ORDER
    # Strategy map should come after narrative-architect and before speaker-notes-writer
    arch_idx = DEFAULT_STEP_ORDER.index('narrative-architect')
    strat_idx = DEFAULT_STEP_ORDER.index('strategy-map')
    notes_idx = DEFAULT_STEP_ORDER.index('speaker-notes-writer')
    assert arch_idx < strat_idx < notes_idx
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && python -m pytest tests/test_conductor.py::test_default_step_order_includes_strategy_map -v`
Expected: FAIL — 'strategy-map' not in list

- [ ] **Step 3: Update DEFAULT_STEP_ORDER and CONTRACT_SCHEMAS**

In `src/deckcontext.py`, add `'strategy-map'` to DEFAULT_STEP_ORDER after `'narrative-architect'`:

```python
DEFAULT_STEP_ORDER = [
    'validate-brief',
    'brand-manager',
    'slide-stylist',
    'narrative-architect',
    'strategy-map',
    'speaker-notes-writer',
    'imagegen-bridge',
    'chart-renderer',
    'deck-assembler',
    'deck-qa',
]
```

Also add the strategy map to CONTRACT_SCHEMAS:

```python
CONTRACT_SCHEMAS = {
    'talk-brief': 'talk_brief.schema.json',
    'pipeline-state': 'pipeline_state.schema.json',
    'style-guide': 'style_guide.schema.json',
    'outline': 'slide_outline.schema.json',
    'speaker-notes': 'speaker_notes.schema.json',
    'image-manifest': 'image_manifest.schema.json',
    'chart-manifest': 'chart_manifest.schema.json',
    'qa-report': 'qa_report.schema.json',
    'brand-profile': 'brand_profile.schema.json',
    'strategy-map': 'strategy_map.schema.json',
}
```

- [ ] **Step 4: Run tests to verify pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_conductor.py -v`
Expected: All pass (19 existing + 1 new = 20)

- [ ] **Step 5: Commit**

```bash
git add src/deckcontext.py tests/test_conductor.py
git commit -m "feat: add strategy-map to pipeline step order and contract schemas"
```

---

### Task 4: Conductor — Upgrade Slide Strategy Function

**Files:**
- Modify: `src/conductor.py`
- Modify: `tests/test_conductor.py`

- [ ] **Step 1: Write failing tests for upgrade_slide_strategy**

Append to `tests/test_conductor.py`:

```python
def test_upgrade_slide_strategy(tmp_path):
    import json
    from src.conductor import init_pipeline
    from src.slide_prompt_composer import build_strategy_map, save_strategy_map
    from src.conductor import upgrade_slide_strategy

    deck_dir = str(tmp_path)
    init_pipeline(deck_dir, budget_usd=10.0)

    # Create a minimal outline and strategy map
    outline = {
        'narrative_arc': 'test',
        'estimated_duration_minutes': 10,
        'slides': [
            {'slide_number': 1, 'slide_type': 'title', 'headline': 'Title', 'visual_type': 'hero_image'},
            {'slide_number': 2, 'slide_type': 'content', 'headline': 'Content',
             'body_points': ['A', 'B', 'C', 'D'], 'visual_type': 'hero_image'},
        ],
    }
    strategy_map = build_strategy_map(outline)
    save_strategy_map(deck_dir, strategy_map)

    # Slide 2 should be backdrop_render (4 bullets)
    assert strategy_map['slides'][1]['strategy'] == 'backdrop_render'

    # Upgrade slide 2 to full_render
    updated = upgrade_slide_strategy(deck_dir, slide_number=2, new_strategy='full_render')
    assert updated['slides'][1]['speaker_override'] == 'full_render'
    assert updated['slides'][1]['render_funnel'] == ['ollama', 'cloud_low', 'cloud_full']


def test_upgrade_slide_strategy_logs_approval(tmp_path):
    import json
    from src.conductor import init_pipeline, get_pipeline_state
    from src.slide_prompt_composer import build_strategy_map, save_strategy_map
    from src.conductor import upgrade_slide_strategy

    deck_dir = str(tmp_path)
    init_pipeline(deck_dir, budget_usd=10.0)

    outline = {
        'narrative_arc': 'test',
        'estimated_duration_minutes': 10,
        'slides': [
            {'slide_number': 1, 'slide_type': 'title', 'headline': 'Title', 'visual_type': 'hero_image'},
        ],
    }
    strategy_map = build_strategy_map(outline)
    save_strategy_map(deck_dir, strategy_map)

    upgrade_slide_strategy(deck_dir, slide_number=1, new_strategy='backdrop_render')
    state = get_pipeline_state(deck_dir)
    approvals = [a for a in state['speaker_approvals'] if a['decision'] == 'strategy_override']
    assert len(approvals) == 1
    assert 'slide 1' in approvals[0]['context'].lower()


def test_upgrade_slide_strategy_invalid_slide(tmp_path):
    import json
    from src.conductor import init_pipeline
    from src.slide_prompt_composer import build_strategy_map, save_strategy_map
    from src.conductor import upgrade_slide_strategy

    deck_dir = str(tmp_path)
    init_pipeline(deck_dir, budget_usd=10.0)

    outline = {
        'narrative_arc': 'test',
        'estimated_duration_minutes': 10,
        'slides': [
            {'slide_number': 1, 'slide_type': 'title', 'headline': 'Title', 'visual_type': 'hero_image'},
        ],
    }
    strategy_map = build_strategy_map(outline)
    save_strategy_map(deck_dir, strategy_map)

    with pytest.raises(KeyError, match='slide 99'):
        upgrade_slide_strategy(deck_dir, slide_number=99, new_strategy='full_render')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/test_conductor.py -k upgrade -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Write upgrade_slide_strategy implementation**

Add to `src/conductor.py`:

```python
from src.slide_prompt_composer import load_strategy_map, save_strategy_map


def upgrade_slide_strategy(deck_dir, slide_number, new_strategy):
    """Upgrade a single slide's rendering strategy (post-hoc).

    Updates the strategy map with a speaker_override and adjusts the
    render funnel. Logs a speaker approval entry.

    Args:
        deck_dir: Path to the deck working directory.
        slide_number: Which slide to upgrade.
        new_strategy: 'full_render', 'backdrop_render', or 'composed'.

    Returns:
        dict: The updated strategy map.

    Raises:
        KeyError: If slide_number is not in the strategy map.
    """
    strategy_map = load_strategy_map(deck_dir)
    found = False
    for entry in strategy_map.get('slides', []):
        if entry['slide_number'] == slide_number:
            entry['speaker_override'] = new_strategy
            if new_strategy in ('full_render', 'backdrop_render'):
                entry['render_funnel'] = ['ollama', 'cloud_low', 'cloud_full']
            else:
                entry['render_funnel'] = ['ollama']
            found = True
            break

    if not found:
        raise KeyError(f'No strategy map entry for slide {slide_number}')

    save_strategy_map(deck_dir, strategy_map)
    log_speaker_approval(
        deck_dir,
        'strategy_override',
        f'Slide {slide_number} upgraded to {new_strategy}',
    )
    return strategy_map
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_conductor.py -v`
Expected: All pass (19 existing + 1 step order + 3 upgrade = 23)

- [ ] **Step 5: Commit**

```bash
git add src/conductor.py tests/test_conductor.py
git commit -m "feat: add upgrade_slide_strategy for post-hoc keynote upgrades"
```

---

### Task 5: Full Suite Verification + CLAUDE.md

- [ ] **Step 1: Run the complete test suite**

Run: `source .venv/bin/activate && python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 2: Verify existing deck still assembles and QAs correctly**

Run: `node src/assembler/build_deck.js --deck-dir ./tmp/deck && source .venv/bin/activate && python -m src.qa.run_qa --pptx-path ./tmp/deck/output/presentation.pptx --deck-dir ./tmp/deck --duration 11`
Expected: Assembly succeeds, QA runs (same accepted findings as before)

- [ ] **Step 3: Update CLAUDE.md**

Add to the Implementation Status table:

| Module | Location | Tests | Status |
|--------|----------|-------|--------|
| Keynote QA checks | `src/qa/checks/keynote_checks.py` | 5 | Done |
| Strategy-aware QA routing | `src/qa/run_qa.py` | 5 | Done |
| Pipeline step order update | `src/deckcontext.py` | 1 | Done |
| Upgrade slide strategy | `src/conductor.py` | 3 | Done |

Update the total test count.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with keynote Sub-plan C modules"
```
