# Image Pipeline Gaps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three modules that close gaps in the image pipeline: manifest utilities for surgical updates, SVG-to-PNG rasterisation, and draft-to-production image upgrading.

**Architecture:** Three focused modules with clear dependencies — `manifest_utils.py` provides the foundation (read/update/write manifest entries), `process_image.py` gains `rasterize_svg()` using `rsvg-convert` CLI, and `image_router.py` gains `plan_production_upgrade()` that uses both. All TDD with existing test patterns.

**Tech Stack:** Python 3.14, Pillow (existing), `rsvg-convert` CLI (installed at `/opt/homebrew/bin/rsvg-convert`), pytest, existing JSON schema validation.

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `src/manifest_utils.py` | Create | Read, update, validate, write image-manifest.json entries |
| `tests/test_manifest_utils.py` | Create | Unit tests for all manifest utility functions |
| `src/process_image.py` | Modify | Add `rasterize_svg()` function |
| `tests/test_process_image.py` | Modify | Add SVG rasterisation tests |
| `src/image_router.py` | Modify | Add `plan_production_upgrade()` function, `UpgradeDecision` namedtuple |
| `tests/test_image_router.py` | Modify | Add upgrade planning tests |

---

### Task 1: Manifest Utilities — Core Read/Write

**Files:**
- Create: `src/manifest_utils.py`
- Create: `tests/test_manifest_utils.py`

- [ ] **Step 1: Write failing test for `load_manifest`**

```python
"""Tests for manifest utilities."""

import json
import os
import shutil
import tempfile

import pytest
from PIL import Image


@pytest.fixture
def deck_dir():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, 'images'), exist_ok=True)
    yield d
    shutil.rmtree(d)


@pytest.fixture
def sample_image(deck_dir):
    """Create a 200x100 red PNG in the deck images dir."""
    path = os.path.join(deck_dir, 'images', 'slide-01-hero.png')
    img = Image.new('RGB', (200, 100), color=(255, 0, 0))
    img.save(path)
    return path


@pytest.fixture
def sample_manifest(deck_dir, sample_image):
    """Write a minimal valid image-manifest.json."""
    manifest = {
        'images': [
            {
                'image_id': 'slide-01-hero_image',
                'slide_number': 1,
                'file_path': sample_image,
                'status': 'generated',
                'dimensions': {'width': 200, 'height': 100},
                'model_used': 'x/z-image-turbo',
                'alt_text': 'Test image',
                'content_hash': 'abc123',
            }
        ],
        'summary': {
            'total_images': 1,
            'generated_count': 1,
            'cached_count': 0,
            'placeholder_count': 0,
            'failed_count': 0,
            'total_generation_seconds': 0.0,
        },
    }
    manifest_path = os.path.join(deck_dir, 'image-manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)
    return manifest_path


def test_load_manifest(deck_dir, sample_manifest):
    from src.manifest_utils import load_manifest
    manifest = load_manifest(deck_dir)
    assert len(manifest['images']) == 1
    assert manifest['images'][0]['image_id'] == 'slide-01-hero_image'


def test_load_manifest_missing_file(deck_dir):
    from src.manifest_utils import load_manifest
    with pytest.raises(FileNotFoundError):
        load_manifest(deck_dir)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && python -m pytest tests/test_manifest_utils.py::test_load_manifest -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.manifest_utils'`

- [ ] **Step 3: Write minimal implementation**

```python
"""Manifest utilities for surgical image-manifest.json updates.

Provides functions to load, update individual entries, and save
the image manifest without requiring a full pipeline re-run.
Uses process_image.py primitives for dimension/hash computation.
"""

import json
import os


def load_manifest(deck_dir):
    """Load image-manifest.json from a deck directory.

    Args:
        deck_dir: Path to the deck working directory.

    Returns:
        dict: The parsed manifest.

    Raises:
        FileNotFoundError: If manifest does not exist.
    """
    path = os.path.join(deck_dir, 'image-manifest.json')
    if not os.path.exists(path):
        raise FileNotFoundError(f'No image-manifest.json in {deck_dir}')
    with open(path) as f:
        return json.load(f)


def save_manifest(deck_dir, manifest):
    """Write image-manifest.json atomically.

    Args:
        deck_dir: Path to the deck working directory.
        manifest: The manifest dict to write.
    """
    path = os.path.join(deck_dir, 'image-manifest.json')
    tmp_path = path + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(manifest, f, indent=2)
        f.write('\n')
    os.replace(tmp_path, path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_manifest_utils.py -v`
Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/manifest_utils.py tests/test_manifest_utils.py
git commit -m "feat: add manifest_utils with load/save functions"
```

---

### Task 2: Manifest Utilities — Update Entry

**Files:**
- Modify: `src/manifest_utils.py`
- Modify: `tests/test_manifest_utils.py`

- [ ] **Step 1: Write failing tests for `update_manifest_entry` and `replace_image_in_manifest`**

```python
def test_update_manifest_entry(deck_dir, sample_manifest, sample_image):
    from src.manifest_utils import load_manifest, update_manifest_entry
    entry = update_manifest_entry(
        deck_dir,
        image_id='slide-01-hero_image',
        model_used='openai/gpt-image-1.5',
        alt_text='Updated alt text',
    )
    assert entry['model_used'] == 'openai/gpt-image-1.5'
    assert entry['alt_text'] == 'Updated alt text'
    assert entry['dimensions'] == {'width': 200, 'height': 100}
    assert len(entry['content_hash']) == 64  # SHA-256 hex

    # Verify persisted
    manifest = load_manifest(deck_dir)
    assert manifest['images'][0]['model_used'] == 'openai/gpt-image-1.5'


def test_update_manifest_entry_unknown_id(deck_dir, sample_manifest):
    from src.manifest_utils import update_manifest_entry
    with pytest.raises(KeyError, match='no-such-id'):
        update_manifest_entry(deck_dir, image_id='no-such-id')


def test_replace_image_in_manifest(deck_dir, sample_manifest, sample_image):
    from src.manifest_utils import load_manifest, replace_image_in_manifest
    # Create a new replacement image
    new_path = os.path.join(deck_dir, 'images', 'slide-01-hero-v2.png')
    img = Image.new('RGB', (400, 300), color=(0, 255, 0))
    img.save(new_path)

    entry = replace_image_in_manifest(
        deck_dir,
        slide_number=1,
        new_file_path=new_path,
        model_used='svg-convert',
    )
    assert entry['file_path'] == new_path
    assert entry['dimensions'] == {'width': 400, 'height': 300}
    assert entry['model_used'] == 'svg-convert'

    manifest = load_manifest(deck_dir)
    assert manifest['images'][0]['file_path'] == new_path


def test_replace_image_unknown_slide(deck_dir, sample_manifest):
    from src.manifest_utils import replace_image_in_manifest
    with pytest.raises(KeyError, match='slide 99'):
        replace_image_in_manifest(deck_dir, slide_number=99, new_file_path='/x', model_used='test')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/test_manifest_utils.py -v`
Expected: 4 FAIL — `ImportError: cannot import name 'update_manifest_entry'`

- [ ] **Step 3: Write implementation**

```python
from src.process_image import get_dimensions, compute_content_hash


def _find_entry(manifest, *, image_id=None, slide_number=None):
    """Find an entry in the manifest by image_id or slide_number."""
    for entry in manifest.get('images', []):
        if image_id and entry.get('image_id') == image_id:
            return entry
        if slide_number is not None and entry.get('slide_number') == slide_number:
            return entry
    key = image_id if image_id else f'slide {slide_number}'
    raise KeyError(f'No manifest entry for {key}')


def update_manifest_entry(deck_dir, image_id, model_used=None, alt_text=None):
    """Update a single entry in the manifest by image_id.

    Recomputes dimensions and content_hash from the file on disk.
    Only updates model_used and alt_text if provided.

    Args:
        deck_dir: Path to the deck working directory.
        image_id: The image_id to update.
        model_used: Optional new model attribution.
        alt_text: Optional new alt text.

    Returns:
        dict: The updated entry.

    Raises:
        KeyError: If image_id not found.
    """
    manifest = load_manifest(deck_dir)
    entry = _find_entry(manifest, image_id=image_id)

    file_path = entry['file_path']
    w, h = get_dimensions(file_path)
    entry['dimensions'] = {'width': w, 'height': h}
    entry['content_hash'] = compute_content_hash(file_path)

    if model_used is not None:
        entry['model_used'] = model_used
    if alt_text is not None:
        entry['alt_text'] = alt_text

    save_manifest(deck_dir, manifest)
    return entry


def replace_image_in_manifest(deck_dir, slide_number, new_file_path, model_used, alt_text=None):
    """Replace an image entry by slide_number with a new file.

    Args:
        deck_dir: Path to the deck working directory.
        slide_number: Slide number to update.
        new_file_path: Path to the replacement image.
        model_used: Model/tool attribution string.
        alt_text: Optional new alt text.

    Returns:
        dict: The updated entry.

    Raises:
        KeyError: If slide_number not found.
    """
    manifest = load_manifest(deck_dir)
    entry = _find_entry(manifest, slide_number=slide_number)

    entry['file_path'] = new_file_path
    w, h = get_dimensions(new_file_path)
    entry['dimensions'] = {'width': w, 'height': h}
    entry['content_hash'] = compute_content_hash(new_file_path)
    entry['model_used'] = model_used

    if alt_text is not None:
        entry['alt_text'] = alt_text

    save_manifest(deck_dir, manifest)
    return entry
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_manifest_utils.py -v`
Expected: 6 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/manifest_utils.py tests/test_manifest_utils.py
git commit -m "feat: add update_manifest_entry and replace_image_in_manifest"
```

---

### Task 3: Manifest Utilities — Rebuild Hashes

**Files:**
- Modify: `src/manifest_utils.py`
- Modify: `tests/test_manifest_utils.py`

- [ ] **Step 1: Write failing test for `rebuild_manifest_hashes`**

```python
def test_rebuild_manifest_hashes(deck_dir, sample_manifest, sample_image):
    from src.manifest_utils import load_manifest, rebuild_manifest_hashes
    from src.process_image import compute_content_hash

    result = rebuild_manifest_hashes(deck_dir)
    assert len(result['images']) == 1

    expected_hash = compute_content_hash(sample_image)
    assert result['images'][0]['content_hash'] == expected_hash
    assert result['images'][0]['dimensions'] == {'width': 200, 'height': 100}

    # Verify persisted
    manifest = load_manifest(deck_dir)
    assert manifest['images'][0]['content_hash'] == expected_hash
```

- [ ] **Step 2: Run test to verify it fails**

Run: `source .venv/bin/activate && python -m pytest tests/test_manifest_utils.py::test_rebuild_manifest_hashes -v`
Expected: FAIL — `ImportError: cannot import name 'rebuild_manifest_hashes'`

- [ ] **Step 3: Write implementation**

```python
def rebuild_manifest_hashes(deck_dir):
    """Recompute dimensions and content_hash for every image in the manifest.

    Useful after bulk image replacement (e.g., production re-render).

    Args:
        deck_dir: Path to the deck working directory.

    Returns:
        dict: The full updated manifest.
    """
    manifest = load_manifest(deck_dir)
    for entry in manifest.get('images', []):
        file_path = entry.get('file_path', '')
        if os.path.exists(file_path):
            w, h = get_dimensions(file_path)
            entry['dimensions'] = {'width': w, 'height': h}
            entry['content_hash'] = compute_content_hash(file_path)
    save_manifest(deck_dir, manifest)
    return manifest
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_manifest_utils.py -v`
Expected: 7 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/manifest_utils.py tests/test_manifest_utils.py
git commit -m "feat: add rebuild_manifest_hashes for bulk updates"
```

---

### Task 4: SVG Rasterisation

**Files:**
- Modify: `src/process_image.py`
- Modify: `tests/test_process_image.py`

- [ ] **Step 1: Write failing tests for `rasterize_svg`**

```python
# Add to tests/test_process_image.py

@pytest.fixture
def test_svg(tmp_dir):
    """Create a minimal valid SVG file."""
    path = os.path.join(tmp_dir, 'test.svg')
    with open(path, 'w') as f:
        f.write(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">'
            '<rect width="400" height="300" fill="#006B5E"/>'
            '</svg>'
        )
    return path


def test_rasterize_svg_basic(tmp_dir, test_svg):
    from src.process_image import rasterize_svg
    output = os.path.join(tmp_dir, 'output.png')
    result = rasterize_svg(test_svg, output, width=800)
    assert result['path'] == output
    assert os.path.exists(output)
    assert result['width'] == 800
    assert result['height'] == 600  # maintains 4:3 aspect
    assert len(result['content_hash']) == 64


def test_rasterize_svg_explicit_height(tmp_dir, test_svg):
    from src.process_image import rasterize_svg
    output = os.path.join(tmp_dir, 'output.png')
    result = rasterize_svg(test_svg, output, width=800, height=800, keep_aspect=False)
    assert result['width'] == 800
    assert result['height'] == 800


def test_rasterize_svg_missing_file(tmp_dir):
    from src.process_image import rasterize_svg
    with pytest.raises(FileNotFoundError):
        rasterize_svg('/no/such/file.svg', os.path.join(tmp_dir, 'out.png'))


def test_rasterize_svg_no_rsvg(tmp_dir, test_svg, monkeypatch):
    from src import process_image
    monkeypatch.setattr(process_image, '_RSVG_CONVERT_PATH', None)
    output = os.path.join(tmp_dir, 'output.png')
    with pytest.raises(RuntimeError, match='rsvg-convert'):
        process_image.rasterize_svg(test_svg, output)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/test_process_image.py::test_rasterize_svg_basic -v`
Expected: FAIL — `ImportError: cannot import name 'rasterize_svg'`

- [ ] **Step 3: Write implementation**

Add to `src/process_image.py`:

```python
import shutil
import subprocess

# Detect rsvg-convert at module load
_RSVG_CONVERT_PATH = shutil.which('rsvg-convert')


def rasterize_svg(svg_path, output_path, width=2048, height=None, keep_aspect=True):
    """Convert an SVG file to a PNG using rsvg-convert.

    Args:
        svg_path: Path to the source SVG file.
        output_path: Where to save the PNG.
        width: Target width in pixels.
        height: Target height in pixels. If None and keep_aspect is True,
                height is computed from the SVG's native aspect ratio.
        keep_aspect: If True (default), maintain the SVG's aspect ratio.

    Returns:
        dict: {path, width, height, content_hash}

    Raises:
        FileNotFoundError: If svg_path does not exist.
        RuntimeError: If rsvg-convert is not installed.
    """
    if not os.path.exists(svg_path):
        raise FileNotFoundError(f'SVG not found: {svg_path}')
    if _RSVG_CONVERT_PATH is None:
        raise RuntimeError(
            'rsvg-convert is not installed. '
            'Install via: brew install librsvg (macOS) or apt install librsvg2-bin (Linux)'
        )

    cmd = [_RSVG_CONVERT_PATH, '-w', str(width)]
    if height is not None:
        cmd.extend(['-h', str(height)])
    if keep_aspect:
        cmd.append('--keep-aspect-ratio')
    cmd.extend([svg_path, '-o', output_path])

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    subprocess.run(cmd, check=True, capture_output=True)

    w, h = get_dimensions(output_path)
    content_hash = compute_content_hash(output_path)

    return {
        'path': output_path,
        'width': w,
        'height': h,
        'content_hash': content_hash,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_process_image.py -k rasterize -v`
Expected: 4 PASSED

- [ ] **Step 5: Run full process_image test suite**

Run: `source .venv/bin/activate && python -m pytest tests/test_process_image.py -v`
Expected: All PASSED (19 existing + 4 new = 23)

- [ ] **Step 6: Commit**

```bash
git add src/process_image.py tests/test_process_image.py
git commit -m "feat: add rasterize_svg using rsvg-convert"
```

---

### Task 5: Production Upgrade Planning

**Files:**
- Modify: `src/image_router.py`
- Modify: `tests/test_image_router.py`

- [ ] **Step 1: Write failing tests for `plan_production_upgrade`**

```python
# Add to tests/test_image_router.py

import pytest
from src.image_router import plan_production_upgrade, UpgradeDecision


@pytest.fixture
def draft_manifest():
    return {
        'images': [
            {
                'image_id': 'slide-01-hero_image',
                'slide_number': 1,
                'file_path': '/tmp/deck/images/slide-01-hero.png',
                'status': 'generated',
                'model_used': 'x/z-image-turbo',
                'source_prompt': 'Dramatic teal composition',
                'dimensions': {'width': 1024, 'height': 576},
            },
            {
                'image_id': 'slide-04-diagram',
                'slide_number': 4,
                'file_path': '/tmp/deck/images/slide-04-diagram.png',
                'status': 'generated',
                'model_used': 'svg-convert',
                'dimensions': {'width': 1705, 'height': 1536},
            },
            {
                'image_id': 'slide-05-hero_image',
                'slide_number': 5,
                'file_path': '/tmp/deck/images/slide-05-hero.png',
                'status': 'generated',
                'model_used': 'x/z-image-turbo',
                'source_prompt': 'Abstract collaboration',
                'dimensions': {'width': 1024, 'height': 576},
            },
        ],
    }


@pytest.fixture
def outline():
    return {
        'slides': [
            {'slide_number': 1, 'visual_type': 'hero_image'},
            {'slide_number': 4, 'visual_type': 'diagram'},
            {'slide_number': 5, 'visual_type': 'hero_image'},
        ],
    }


@pytest.fixture
def all_providers():
    return {
        'ollama': {'available': True, 'models': ['x/z-image-turbo']},
        'openai': {'available': True, 'model': 'gpt-image-1.5'},
        'google': {'available': True, 'model': 'imagen-4'},
        'fal': {'available': True, 'models': ['flux-2-pro']},
    }


@pytest.fixture
def budget_allow():
    return {'budget_state': 'allow', 'remaining_usd': 5.0}


def test_plan_upgrade_upgrades_hero_images(draft_manifest, outline, all_providers, budget_allow):
    decisions = plan_production_upgrade(draft_manifest, outline, all_providers, budget_allow)
    heroes = [d for d in decisions if d.action == 'upgrade']
    assert len(heroes) == 2
    assert heroes[0].slide_number == 1
    assert heroes[1].slide_number == 5


def test_plan_upgrade_keeps_svg_diagrams(draft_manifest, outline, all_providers, budget_allow):
    decisions = plan_production_upgrade(draft_manifest, outline, all_providers, budget_allow)
    kept = [d for d in decisions if d.action == 'keep']
    assert len(kept) == 1
    assert kept[0].slide_number == 4
    assert 'already' in kept[0].reason.lower()


def test_plan_upgrade_respects_budget(draft_manifest, outline, all_providers):
    tight_budget = {'budget_state': 'allow', 'remaining_usd': 0.02}
    decisions = plan_production_upgrade(draft_manifest, outline, all_providers, tight_budget)
    # Should skip upgrades that exceed remaining budget
    upgrades = [d for d in decisions if d.action == 'upgrade']
    total_cost = sum(d.estimated_cost_usd for d in upgrades)
    assert total_cost <= 0.02


def test_plan_upgrade_carries_source_prompt(draft_manifest, outline, all_providers, budget_allow):
    decisions = plan_production_upgrade(draft_manifest, outline, all_providers, budget_allow)
    slide_1 = [d for d in decisions if d.slide_number == 1][0]
    assert slide_1.draft_prompt == 'Dramatic teal composition'


def test_plan_upgrade_returns_upgrade_decisions(draft_manifest, outline, all_providers, budget_allow):
    decisions = plan_production_upgrade(draft_manifest, outline, all_providers, budget_allow)
    assert all(isinstance(d, UpgradeDecision) for d in decisions)
    assert len(decisions) == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/test_image_router.py -k plan_upgrade -v`
Expected: FAIL — `ImportError: cannot import name 'plan_production_upgrade'`

- [ ] **Step 3: Write implementation**

Add to `src/image_router.py`:

```python
UpgradeDecision = namedtuple('UpgradeDecision', [
    'slide_number',
    'image_id',
    'action',           # 'upgrade' or 'keep'
    'reason',
    'draft_prompt',     # carried from draft manifest (None if absent)
    'target_provider',  # provider for upgrade (None if keep)
    'target_model',     # model for upgrade (None if keep)
    'target_size',      # size string e.g. '1536x1024' (None if keep)
    'estimated_cost_usd',
])

# Models/tools that already produce high-quality output
_PRODUCTION_QUALITY_SOURCES = {'svg-convert', 'matplotlib', 'render_chart'}

# Visual types that benefit from cloud upgrade
_UPGRADEABLE_VISUAL_TYPES = {'hero_image', 'pattern_background', 'icon_set'}


def plan_production_upgrade(draft_manifest, outline, available_providers, budget_state):
    """Plan which images to upgrade from draft to production quality.

    Args:
        draft_manifest: dict from image-manifest.json.
        outline: dict from outline.json with 'slides' array.
        available_providers: dict from provider_discovery.
        budget_state: dict with 'budget_state' and 'remaining_usd'.

    Returns:
        list[UpgradeDecision]: One decision per manifest entry.
    """
    remaining = budget_state.get('remaining_usd', 0.0)
    slide_types = {
        s['slide_number']: classify_visual_type(s)
        for s in outline.get('slides', [])
    }

    decisions = []
    for entry in draft_manifest.get('images', []):
        slide_num = entry.get('slide_number', 0)
        image_id = entry.get('image_id', '')
        model_used = entry.get('model_used', '')
        visual_type = slide_types.get(slide_num, 'none')
        draft_prompt = entry.get('source_prompt')

        # Already production quality?
        if model_used in _PRODUCTION_QUALITY_SOURCES:
            decisions.append(UpgradeDecision(
                slide_number=slide_num,
                image_id=image_id,
                action='keep',
                reason=f'Already production quality ({model_used})',
                draft_prompt=draft_prompt,
                target_provider=None,
                target_model=None,
                target_size=None,
                estimated_cost_usd=0.0,
            ))
            continue

        # Not a type that benefits from upgrade?
        if visual_type not in _UPGRADEABLE_VISUAL_TYPES:
            decisions.append(UpgradeDecision(
                slide_number=slide_num,
                image_id=image_id,
                action='keep',
                reason=f'Visual type {visual_type} does not benefit from cloud upgrade',
                draft_prompt=draft_prompt,
                target_provider=None,
                target_model=None,
                target_size=None,
                estimated_cost_usd=0.0,
            ))
            continue

        # Find the best production route
        route = route_slide(
            {'slide_number': slide_num, 'visual_type': visual_type},
            'production',
            available_providers,
            budget_state.get('budget_state', 'allow'),
        )

        # Budget check
        if route.cost_per_image > remaining:
            decisions.append(UpgradeDecision(
                slide_number=slide_num,
                image_id=image_id,
                action='keep',
                reason=f'Upgrade cost ${route.cost_per_image:.3f} exceeds remaining ${remaining:.2f}',
                draft_prompt=draft_prompt,
                target_provider=None,
                target_model=None,
                target_size=None,
                estimated_cost_usd=0.0,
            ))
            continue

        remaining -= route.cost_per_image
        decisions.append(UpgradeDecision(
            slide_number=slide_num,
            image_id=image_id,
            action='upgrade',
            reason=f'{visual_type} benefits from cloud quality',
            draft_prompt=draft_prompt,
            target_provider=route.provider,
            target_model=route.model,
            target_size='1536x1024',
            estimated_cost_usd=route.cost_per_image,
        ))

    return decisions
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `source .venv/bin/activate && python -m pytest tests/test_image_router.py -k plan_upgrade -v`
Expected: 5 PASSED

- [ ] **Step 5: Run full image_router test suite**

Run: `source .venv/bin/activate && python -m pytest tests/test_image_router.py -v`
Expected: All PASSED (35 existing + 5 new = 40)

- [ ] **Step 6: Commit**

```bash
git add src/image_router.py tests/test_image_router.py
git commit -m "feat: add plan_production_upgrade for surgical draft-to-production upgrade"
```

---

### Task 6: Full Suite Verification

- [ ] **Step 1: Run the complete test suite**

Run: `source .venv/bin/activate && python -m pytest tests/ -v`
Expected: All tests pass (385 existing + 16 new = 401)

- [ ] **Step 2: Run QA on the current deck to verify nothing regressed**

Run: `node src/assembler/build_deck.js --deck-dir ./tmp/deck && source .venv/bin/activate && python -m src.qa.run_qa --pptx-path ./tmp/deck/output/presentation.pptx --deck-dir ./tmp/deck --duration 11`
Expected: Same QA output as before (7 accepted contrast errors, 5 accepted warnings)

- [ ] **Step 3: Final commit with updated CLAUDE.md module table**

Update the Implementation Status table in CLAUDE.md to add:

| Module | Location | Tests | Status |
|--------|----------|-------|--------|
| Manifest utilities | `src/manifest_utils.py` | 7 | Done |
| SVG rasterisation | `src/process_image.py` | 23 | Done |
| Production upgrade planner | `src/image_router.py` | 40 | Done |

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with new image pipeline modules"
```
