# Keynote Pipeline Sub-Plan B: Render Funnel + Assembler

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the three-stage render funnel for keynote slides and add full_render/backdrop_render assembly paths to the deck assembler.

**Architecture:** A new Python module (`render_funnel.py`) orchestrates the Ollama→cloud_low→cloud_full render stages for each keynote slide, logging every attempt to a RenderLog. The assembler gains two new slide builders (`buildFullRenderSlide`, `buildBackdropRenderSlide`) and reads the strategy-map.json to decide which builder to use per slide.

**Tech Stack:** Python 3.14 (render funnel, render log), Node.js (assembler), PptxGenJS, pytest, existing BudgetTracker + manifest_utils + generate_image + generate_cloud_image

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `src/schemas/render_log.schema.json` | Create | JSON schema for RenderLog contract |
| `src/render_funnel.py` | Create | Three-stage render orchestration + render log management |
| `tests/test_render_funnel.py` | Create | Unit tests for render funnel |
| `src/assembler/build_deck.js` | Modify | Add buildFullRenderSlide, buildBackdropRenderSlide, strategy map loading |
| `tests/test_assembler.py` | Modify | Add keynote assembly tests |
| `tests/test_schemas.py` | Modify | Add RenderLog schema tests |

---

### Task 1: RenderLog JSON Schema

**Files:**
- Create: `src/schemas/render_log.schema.json`
- Modify: `tests/test_schemas.py`

- [ ] **Step 1: Write failing schema tests**

Append to `tests/test_schemas.py`:

```python
class TestRenderLogSchema:
    @pytest.fixture
    def schema(self):
        with open('src/schemas/render_log.schema.json') as f:
            return json.load(f)

    def test_valid_render_log(self, schema):
        data = {
            "entries": [
                {
                    "slide_number": 1,
                    "strategy": "full_render",
                    "funnel_stage": "ollama",
                    "prompt_hash": "abc123",
                    "model": "x/z-image-turbo",
                    "resolution": "1024x576",
                    "vision_score": 6.5,
                    "iteration": 1,
                    "cost_usd": 0.0,
                    "timestamp": "2026-03-29T12:00:00Z"
                }
            ]
        }
        jsonschema.Draft202012Validator(schema).validate(data)

    def test_missing_entries_fails(self, schema):
        data = {}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(data)

    def test_invalid_funnel_stage_fails(self, schema):
        data = {
            "entries": [
                {
                    "slide_number": 1,
                    "strategy": "full_render",
                    "funnel_stage": "invalid",
                    "prompt_hash": "abc",
                    "model": "test",
                    "resolution": "1024x576",
                    "iteration": 1,
                    "cost_usd": 0.0,
                    "timestamp": "2026-03-29T12:00:00Z"
                }
            ]
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(data)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/test_schemas.py::TestRenderLogSchema -v`
Expected: FAIL — FileNotFoundError

- [ ] **Step 3: Create the schema**

Create `src/schemas/render_log.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://jack-tar.dev/schemas/render-log.json",
  "title": "RenderLog",
  "description": "Append-only log of render attempts for cost and convergence analysis.",
  "type": "object",
  "required": ["entries"],
  "properties": {
    "entries": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["slide_number", "strategy", "funnel_stage", "prompt_hash", "model", "resolution", "iteration", "cost_usd", "timestamp"],
        "properties": {
          "slide_number": {"type": "integer", "minimum": 1},
          "strategy": {"type": "string", "enum": ["full_render", "backdrop_render"]},
          "funnel_stage": {"type": "string", "enum": ["ollama", "cloud_low", "cloud_full"]},
          "prompt_hash": {"type": "string"},
          "model": {"type": "string"},
          "resolution": {"type": "string"},
          "vision_score": {"type": ["number", "null"]},
          "iteration": {"type": "integer", "minimum": 1},
          "cost_usd": {"type": "number", "minimum": 0},
          "timestamp": {"type": "string"}
        }
      }
    }
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_schemas.py::TestRenderLogSchema -v`
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/schemas/render_log.schema.json tests/test_schemas.py
git commit -m "feat: add RenderLog JSON schema"
```

---

### Task 2: Render Log Manager

**Files:**
- Create: `src/render_funnel.py`
- Create: `tests/test_render_funnel.py`

- [ ] **Step 1: Write failing tests for render log management**

Create `tests/test_render_funnel.py`:

```python
"""Tests for render funnel orchestration."""

import hashlib
import json
import os
import shutil
import tempfile

import pytest


@pytest.fixture
def deck_dir():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, 'images'), exist_ok=True)
    yield d
    shutil.rmtree(d)


def test_init_render_log(deck_dir):
    from src.render_funnel import init_render_log, load_render_log
    init_render_log(deck_dir)
    log = load_render_log(deck_dir)
    assert log['entries'] == []


def test_append_render_entry(deck_dir):
    from src.render_funnel import init_render_log, append_render_entry, load_render_log
    init_render_log(deck_dir)
    append_render_entry(deck_dir, {
        'slide_number': 1,
        'strategy': 'full_render',
        'funnel_stage': 'ollama',
        'prompt_hash': 'abc123',
        'model': 'x/z-image-turbo',
        'resolution': '1024x576',
        'vision_score': 6.5,
        'iteration': 1,
        'cost_usd': 0.0,
        'timestamp': '2026-03-29T12:00:00Z',
    })
    log = load_render_log(deck_dir)
    assert len(log['entries']) == 1
    assert log['entries'][0]['slide_number'] == 1


def test_append_multiple_entries(deck_dir):
    from src.render_funnel import init_render_log, append_render_entry, load_render_log
    init_render_log(deck_dir)
    for i in range(3):
        append_render_entry(deck_dir, {
            'slide_number': 1,
            'strategy': 'full_render',
            'funnel_stage': 'ollama',
            'prompt_hash': f'hash_{i}',
            'model': 'x/z-image-turbo',
            'resolution': '1024x576',
            'vision_score': 5.0 + i,
            'iteration': i + 1,
            'cost_usd': 0.0,
            'timestamp': f'2026-03-29T12:0{i}:00Z',
        })
    log = load_render_log(deck_dir)
    assert len(log['entries']) == 3


def test_load_render_log_missing(deck_dir):
    from src.render_funnel import load_render_log
    with pytest.raises(FileNotFoundError):
        load_render_log(deck_dir)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/test_render_funnel.py -v`
Expected: FAIL — ModuleNotFoundError

- [ ] **Step 3: Write render log implementation**

Create `src/render_funnel.py`:

```python
"""Render funnel — three-stage render orchestration for keynote slides.

Orchestrates the Ollama → cloud_low → cloud_full render stages for
full_render and backdrop_render slides. Logs every render attempt to
render-log.json for cost and convergence analysis.
"""

import hashlib
import json
import os

from datetime import datetime, timezone


def init_render_log(deck_dir):
    """Create an empty render-log.json in the deck directory.

    Args:
        deck_dir: Path to the deck working directory.
    """
    path = os.path.join(deck_dir, 'render-log.json')
    with open(path, 'w') as f:
        json.dump({'entries': []}, f, indent=2)
        f.write('\n')


def load_render_log(deck_dir):
    """Load render-log.json from the deck directory.

    Args:
        deck_dir: Path to the deck working directory.

    Returns:
        dict: The parsed render log.

    Raises:
        FileNotFoundError: If render-log.json does not exist.
    """
    path = os.path.join(deck_dir, 'render-log.json')
    if not os.path.exists(path):
        raise FileNotFoundError(f'No render-log.json in {deck_dir}')
    with open(path) as f:
        return json.load(f)


def append_render_entry(deck_dir, entry):
    """Append a render attempt entry to the render log.

    Args:
        deck_dir: Path to the deck working directory.
        entry: dict with render attempt data (must conform to RenderLog entry schema).
    """
    log = load_render_log(deck_dir)
    log['entries'].append(entry)
    path = os.path.join(deck_dir, 'render-log.json')
    tmp_path = path + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(log, f, indent=2)
        f.write('\n')
    os.replace(tmp_path, path)


def hash_prompt(prompt_text):
    """Compute a short hash of a prompt for log deduplication.

    Args:
        prompt_text: The prompt string.

    Returns:
        str: First 16 chars of SHA-256 hex digest.
    """
    return hashlib.sha256(prompt_text.encode('utf-8')).hexdigest()[:16]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_render_funnel.py -v`
Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/render_funnel.py tests/test_render_funnel.py
git commit -m "feat: add render log init/load/append for keynote render tracking"
```

---

### Task 3: Render Funnel Stage Execution

**Files:**
- Modify: `src/render_funnel.py`
- Modify: `tests/test_render_funnel.py`

- [ ] **Step 1: Write failing tests for execute_funnel_stage**

Append to `tests/test_render_funnel.py`:

```python
from unittest.mock import patch, MagicMock
from PIL import Image


def _create_test_image(path, width=1024, height=576):
    """Helper to create a test image at the given path."""
    img = Image.new('RGB', (width, height), color=(0, 107, 94))
    img.save(path)
    return path


def test_execute_ollama_stage(deck_dir):
    from src.render_funnel import init_render_log, execute_funnel_stage
    init_render_log(deck_dir)
    output_path = os.path.join(deck_dir, 'images', 'slide-01-hero.png')

    with patch('src.render_funnel.subprocess.run') as mock_run:
        # Simulate generate_image.py writing a file
        def side_effect(*args, **kwargs):
            _create_test_image(output_path)
            result = MagicMock()
            result.stdout = output_path
            result.returncode = 0
            return result
        mock_run.side_effect = side_effect

        result = execute_funnel_stage(
            deck_dir=deck_dir,
            slide_number=1,
            strategy='full_render',
            prompt='Test prompt for slide 1',
            funnel_stage='ollama',
            model='x/z-image-turbo',
            output_path=output_path,
        )

    assert result['status'] == 'generated'
    assert result['file_path'] == output_path
    assert result['cost_usd'] == 0.0
    assert os.path.exists(output_path)


def test_execute_cloud_stage(deck_dir):
    from src.render_funnel import init_render_log, execute_funnel_stage
    init_render_log(deck_dir)
    output_path = os.path.join(deck_dir, 'images', 'slide-01-hero.png')

    with patch('src.render_funnel._generate_cloud') as mock_cloud:
        _create_test_image(output_path, 1280, 720)
        mock_cloud.return_value = {
            'file_path': output_path,
            'provider': 'google',
            'model_used': 'imagen-4-fast',
            'cost_usd': 0.02,
            'status': 'generated',
        }

        result = execute_funnel_stage(
            deck_dir=deck_dir,
            slide_number=1,
            strategy='full_render',
            prompt='Test prompt for slide 1',
            funnel_stage='cloud_low',
            model='imagen-4-fast',
            output_path=output_path,
            provider='google',
        )

    assert result['status'] == 'generated'
    assert result['cost_usd'] == 0.02


def test_execute_stage_logs_to_render_log(deck_dir):
    from src.render_funnel import init_render_log, execute_funnel_stage, load_render_log
    init_render_log(deck_dir)
    output_path = os.path.join(deck_dir, 'images', 'slide-01-hero.png')

    with patch('src.render_funnel.subprocess.run') as mock_run:
        def side_effect(*args, **kwargs):
            _create_test_image(output_path)
            result = MagicMock()
            result.stdout = output_path
            result.returncode = 0
            return result
        mock_run.side_effect = side_effect

        execute_funnel_stage(
            deck_dir=deck_dir,
            slide_number=1,
            strategy='full_render',
            prompt='Test prompt',
            funnel_stage='ollama',
            model='x/z-image-turbo',
            output_path=output_path,
        )

    log = load_render_log(deck_dir)
    assert len(log['entries']) == 1
    assert log['entries'][0]['funnel_stage'] == 'ollama'
    assert log['entries'][0]['slide_number'] == 1


def test_execute_stage_failed(deck_dir):
    from src.render_funnel import init_render_log, execute_funnel_stage
    init_render_log(deck_dir)
    output_path = os.path.join(deck_dir, 'images', 'slide-01-hero.png')

    with patch('src.render_funnel.subprocess.run') as mock_run:
        mock_run.side_effect = Exception('Ollama not running')

        result = execute_funnel_stage(
            deck_dir=deck_dir,
            slide_number=1,
            strategy='full_render',
            prompt='Test prompt',
            funnel_stage='ollama',
            model='x/z-image-turbo',
            output_path=output_path,
        )

    assert result['status'] == 'failed'
    assert 'error' in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/test_render_funnel.py -k execute -v`
Expected: FAIL — ImportError

- [ ] **Step 3: Write execute_funnel_stage implementation**

Add to `src/render_funnel.py`:

```python
import subprocess
import sys

from src.generate_cloud_image import generate_cloud_image as _generate_cloud_raw


# Ollama model → resolution defaults
_OLLAMA_RESOLUTIONS = {
    'ollama': {'width': 1024, 'height': 576},
    'cloud_low': {'width': 1280, 'height': 720},
    'cloud_full': {'width': 1920, 'height': 1080},
}

# Cloud provider mapping for funnel stages
_CLOUD_STAGE_QUALITY = {
    'cloud_low': 'low',
    'cloud_full': 'medium',
}

_CLOUD_STAGE_SIZE = {
    'cloud_low': '1024x1024',
    'cloud_full': '1536x1024',
}


def _generate_cloud(prompt, provider, output_path, funnel_stage):
    """Wrapper for cloud generation with funnel-stage-appropriate settings."""
    quality = _CLOUD_STAGE_QUALITY.get(funnel_stage, 'medium')
    size = _CLOUD_STAGE_SIZE.get(funnel_stage, '1536x1024')
    return _generate_cloud_raw(
        prompt=prompt,
        provider=provider,
        output_path=output_path,
        quality=quality,
        size=size,
    )


def execute_funnel_stage(deck_dir, slide_number, strategy, prompt, funnel_stage,
                         model, output_path, provider=None, iteration=1):
    """Execute a single render funnel stage for one slide.

    Args:
        deck_dir: Path to the deck working directory.
        slide_number: Which slide this render is for.
        strategy: 'full_render' or 'backdrop_render'.
        prompt: The image generation prompt text.
        funnel_stage: 'ollama', 'cloud_low', or 'cloud_full'.
        model: Model identifier (e.g., 'x/z-image-turbo', 'imagen-4-fast').
        output_path: Where to save the generated image.
        provider: Cloud provider name (required for cloud stages).
        iteration: Iteration number for this stage (default 1).

    Returns:
        dict: {status, file_path, cost_usd, model, resolution, error?}
    """
    prompt_h = hash_prompt(prompt)
    dims = _OLLAMA_RESOLUTIONS.get(funnel_stage, {'width': 1920, 'height': 1080})
    resolution = f'{dims["width"]}x{dims["height"]}'
    cost = 0.0

    try:
        if funnel_stage == 'ollama':
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            subprocess.run(
                [sys.executable, 'src/generate_image.py',
                 '--prompt', prompt,
                 '--model', model,
                 '--output', output_path,
                 '--width', str(dims['width']),
                 '--height', str(dims['height'])],
                check=True, capture_output=True, text=True,
            )
        else:
            result = _generate_cloud(prompt, provider, output_path, funnel_stage)
            cost = result.get('cost_usd', 0.0)
            resolution = _CLOUD_STAGE_SIZE.get(funnel_stage, '1536x1024')

        # Log the attempt
        append_render_entry(deck_dir, {
            'slide_number': slide_number,
            'strategy': strategy,
            'funnel_stage': funnel_stage,
            'prompt_hash': prompt_h,
            'model': model,
            'resolution': resolution,
            'vision_score': None,
            'iteration': iteration,
            'cost_usd': cost,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })

        return {
            'status': 'generated',
            'file_path': output_path,
            'cost_usd': cost,
            'model': model,
            'resolution': resolution,
        }

    except Exception as e:
        # Log the failure too
        append_render_entry(deck_dir, {
            'slide_number': slide_number,
            'strategy': strategy,
            'funnel_stage': funnel_stage,
            'prompt_hash': prompt_h,
            'model': model,
            'resolution': resolution,
            'vision_score': None,
            'iteration': iteration,
            'cost_usd': 0.0,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })

        return {
            'status': 'failed',
            'file_path': output_path,
            'cost_usd': 0.0,
            'model': model,
            'resolution': resolution,
            'error': str(e),
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_render_funnel.py -v`
Expected: 8 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/render_funnel.py tests/test_render_funnel.py
git commit -m "feat: add execute_funnel_stage for three-stage render orchestration"
```

---

### Task 4: Assembler — Full Render Slide Builder

**Files:**
- Modify: `src/assembler/build_deck.js`

- [ ] **Step 1: Add buildFullRenderSlide function**

Add this function after the existing `buildClosingSlide` function and before the `// Run` section at the bottom of `src/assembler/build_deck.js`:

```javascript
/**
 * Full-render keynote slide: entire slide is a single AI-generated image.
 * No text boxes, no shapes — just a full-bleed image + speaker notes.
 * Logo overlay is optional (controlled by style guide).
 */
function buildFullRenderSlide(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData } = ctx;

    const slide = pptx.addSlide();

    // Full-bleed image covering the entire slide
    if (imageData) {
        const imgPath = resolveImagePath(imageData.file_path);
        if (fs.existsSync(imgPath)) {
            slide.addImage({
                path: imgPath,
                x: 0,
                y: 0,
                w: SLIDE_W,
                h: SLIDE_H,
                sizing: { type: 'cover', w: SLIDE_W, h: SLIDE_H },
                altText: imageData.alt_text || '',
            });
        }
    }

    // Optional logo overlay (bottom-left, same position as title/closing slides)
    if (hasLogo) {
        const logoH = 0.55;
        const logoW = logoH * (169 / 200);
        slide.addImage({
            path: logoPath,
            x: MARGIN,
            y: SLIDE_H - MARGIN - logoH,
            w: logoW,
            h: logoH,
            altText: 'Logo',
        });
    }

    // Speaker notes
    if (noteData) {
        slide.addNotes(noteData.text);
    }
}
```

- [ ] **Step 2: Verify file is syntactically valid**

Run: `node -c src/assembler/build_deck.js && echo "Syntax OK"`
Expected: Syntax OK

- [ ] **Step 3: Commit**

```bash
git add src/assembler/build_deck.js
git commit -m "feat: add buildFullRenderSlide for keynote full-bleed slides"
```

---

### Task 5: Assembler — Backdrop Render Slide Builder

**Files:**
- Modify: `src/assembler/build_deck.js`

- [ ] **Step 1: Add buildBackdropRenderSlide function**

Add this function after `buildFullRenderSlide`:

```javascript
/**
 * Backdrop-render keynote slide: AI-generated background image with
 * programmatic text overlay. Text remains editable in PowerPoint.
 * A semi-transparent backing rectangle ensures text readability.
 */
function buildBackdropRenderSlide(pptx, slideData, ctx) {
    const { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData, imageData } = ctx;
    const textColor = slidePalette?.content_slides?.text || palette.text_primary;

    const slide = pptx.addSlide();

    // Full-bleed backdrop image
    if (imageData) {
        const imgPath = resolveImagePath(imageData.file_path);
        if (fs.existsSync(imgPath)) {
            slide.addImage({
                path: imgPath,
                x: 0,
                y: 0,
                w: SLIDE_W,
                h: SLIDE_H,
                sizing: { type: 'cover', w: SLIDE_W, h: SLIDE_H },
                altText: imageData.alt_text || '',
            });
        }
    }

    // Semi-transparent text backing — left third of the slide
    const textZoneW = SLIDE_W * 0.45;
    slide.addShape(pptx.ShapeType.rect, {
        x: 0,
        y: 0,
        w: textZoneW,
        h: SLIDE_H,
        fill: { color: '000000', transparency: 60 },
    });

    // Heading — white text for contrast against the dark backing
    const safeX = MARGIN;
    const headingY = Math.max(SLIDE_H * 0.15, MARGIN);
    const headingW = textZoneW - 2 * MARGIN;
    slide.addText(slideData.headline, {
        x: safeX,
        y: headingY,
        w: headingW,
        h: 1.0,
        fontSize: typo.heading_sizes?.slide_heading || 32,
        fontFace: typo.heading_font,
        color: 'FFFFFF',
        bold: true,
        valign: 'bottom',
        wrap: true,
    });

    // Body points — white text
    if (slideData.body_points && slideData.body_points.length > 0) {
        const bodyY = headingY + 1.2;
        const bodyH = SLIDE_H - bodyY - MARGIN;
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
            x: safeX,
            y: bodyY,
            w: headingW,
            h: bodyH,
            valign: 'top',
        });
    }

    // Speaker notes
    if (noteData) {
        slide.addNotes(noteData.text);
    }
}
```

- [ ] **Step 2: Verify file is syntactically valid**

Run: `node -c src/assembler/build_deck.js && echo "Syntax OK"`
Expected: Syntax OK

- [ ] **Step 3: Commit**

```bash
git add src/assembler/build_deck.js
git commit -m "feat: add buildBackdropRenderSlide for keynote text-over-image slides"
```

---

### Task 6: Assembler — Strategy Map Awareness

**Files:**
- Modify: `src/assembler/build_deck.js`
- Modify: `tests/test_assembler.py`

- [ ] **Step 1: Modify the assembleDeck function to load strategy map and route slides**

In `src/assembler/build_deck.js`, modify the `assembleDeck` function. After loading the existing contracts (around line 93), add:

```javascript
    // Load strategy map (optional — if absent, all slides use 'composed')
    const strategyMapPath = path.join(DECK_DIR, 'strategy-map.json');
    const strategyMap = fs.existsSync(strategyMapPath)
        ? JSON.parse(fs.readFileSync(strategyMapPath, 'utf-8'))
        : null;

    // Build a lookup: slide_number -> effective strategy
    const slideStrategies = {};
    if (strategyMap) {
        for (const entry of strategyMap.slides || []) {
            slideStrategies[entry.slide_number] = entry.speaker_override || entry.strategy;
        }
    }
```

Then modify the main slide loop (the `for (const slideData of outline.slides)` section). Replace the `switch (slideData.slide_type)` with a strategy-first check:

```javascript
    for (const slideData of outline.slides) {
        const noteData = findNote(speakerNotes, slideData.slide_number);
        const imageData = findImage(imageManifest, slideData.slide_number);
        const chartData = findChart(chartManifest, slideData.slide_number);
        const strategy = slideStrategies[slideData.slide_number] || 'composed';

        // Strategy-first routing: keynote strategies override slide-type routing
        if (strategy === 'full_render') {
            buildFullRenderSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData });
            continue;
        }
        if (strategy === 'backdrop_render') {
            buildBackdropRenderSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData, imageData });
            continue;
        }

        // Composed strategy: use existing slide-type routing
        switch (slideData.slide_type) {
            case 'title':
                buildTitleSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData, imageData });
                break;
            case 'section_divider':
                buildSectionDivider(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData });
                break;
            case 'closing':
                buildClosingSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, logoPath, hasLogo, noteData });
                break;
            case 'diagram':
                buildDiagramSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData, imageData });
                break;
            case 'data_chart':
                buildDataChartSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData, chartData });
                break;
            case 'code':
                buildCodeSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData });
                break;
            default:
                buildContentSlide(pptx, slideData, { palette, typo, slidePalette, layouts, SLIDE_W, SLIDE_H, MARGIN, noteData, imageData });
                break;
        }
    }
```

- [ ] **Step 2: Add a test for strategy-map-aware assembly**

Append to `tests/test_assembler.py`:

```python
def test_build_deck_without_strategy_map(tmp_path):
    """Assembler works when strategy-map.json is absent (backward compatible)."""
    import subprocess
    # Use the existing test deck at ./tmp/deck if available, otherwise skip
    deck_dir = './tmp/deck'
    if not os.path.exists(os.path.join(deck_dir, 'outline.json')):
        pytest.skip('No test deck available at ./tmp/deck')
    result = subprocess.run(
        ['node', 'src/assembler/build_deck.js', '--deck-dir', deck_dir],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert 'assembled successfully' in result.stdout.lower()
```

- [ ] **Step 3: Run tests**

Run: `source .venv/bin/activate && python -m pytest tests/test_assembler.py -v`
Expected: All PASSED (5 existing + 1 new = 6)

- [ ] **Step 4: Also verify with the existing deck**

Run: `node src/assembler/build_deck.js --deck-dir ./tmp/deck`
Expected: Assembly succeeds (backward compatible — no strategy-map.json means all slides use 'composed')

- [ ] **Step 5: Commit**

```bash
git add src/assembler/build_deck.js tests/test_assembler.py
git commit -m "feat: assembler reads strategy-map.json, routes to keynote builders"
```

---

### Task 7: Full Suite Verification + CLAUDE.md

- [ ] **Step 1: Run the complete test suite**

Run: `source .venv/bin/activate && python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 2: Update CLAUDE.md implementation table**

Add to the Implementation Status table:

| Module | Location | Tests | Status |
|--------|----------|-------|--------|
| RenderLog schema | `src/schemas/render_log.schema.json` | 3 | Done |
| Render funnel | `src/render_funnel.py` | 8 | Done |
| Assembler keynote paths | `src/assembler/build_deck.js` | 6 | Done |

Update the total test count in the header.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with keynote Sub-plan B modules"
```
