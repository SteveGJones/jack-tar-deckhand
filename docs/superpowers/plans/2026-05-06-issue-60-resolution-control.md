# Issue #60 — Resolution Control Through Deckhand Pipeline + Cloud-Skill Drift Fix

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thread `jack-tar-cloud` v1.2.0's `resolution=` capability through the deckhand pipeline (render funnel, image router, imagegen-bridge, strategy map) so a slide can opt into 2K/4K rendering on Nano Banana Pro/Flash and Imagen — and concurrently fix four cloud-skill SKILL.md files where documented CLI flags are silently dropped.

**Architecture:** Two PRs under EPIC #58. PR A is a contained `jack-tar-cloud` patch (v1.2.0 → v1.2.1) that adds `--resolution` to the four cloud-image SKILL.md files and fixes pre-existing flag drift (fal-image's `--size`/`--quality`, google-image's `--size`). PR B is the larger `jack-tar-deckhand` minor (v1.1.0 → v1.2.0) that wires resolution through render funnel stages, image-router upgrade decisions, the cross-tier refinement loop, the strategy-map schema and skill prompts, and adds a resolution-selection guide to CLAUDE.md.

**Tech Stack:** Python 3.11 (pytest), Markdown SKILL.md format, JSON Schema (Draft 2020-12), bash skill invocation, existing `generate_cloud_image()` resolution surface from PR #65.

---

## Branch and Worktree

- Worktree: `~/Documents/Development/jack-tar-deckhand/.worktrees/issue-60-resolution-control` (already created, off origin/main).
- PR A branch: `feat/issue-60-cloud-skill-drift` (currently checked out).
- PR B branch: `feat/issue-60-resolution-plumbing` — created off updated main after PR A merges.
- Test runner: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest` (the main repo's venv; cross-worktree-safe because plugin tests are self-contained).

## File Structure

### PR A — cloud-skill drift fix (jack-tar-cloud v1.2.1)

| File | Action | Responsibility |
|------|--------|----------------|
| `plugins/jack-tar-cloud/skills/openai-image/SKILL.md` | Modify | Add `--resolution` flag, update Cost Reference table |
| `plugins/jack-tar-cloud/skills/google-image/SKILL.md` | Modify | Add `--resolution`, thread `--size` (currently dropped), update Cost Reference |
| `plugins/jack-tar-cloud/skills/fal-image/SKILL.md` | Modify | Add `--resolution`, translate `--size` → `image_size` dict (currently dropped), remove undocumented `--quality` |
| `plugins/jack-tar-cloud/skills/image/SKILL.md` | Modify | Add `--resolution`, thread through to per-provider skill dispatch |
| `plugins/jack-tar-cloud/tests/test_skill_md_flags.py` | Create | Static test: every flag in argument-hint appears in the Generate snippet |
| `plugins/integration_tests/test_cloud_skill_resolution.py` | Create | Subprocess-runs the skill snippet with `--resolution 4K` and verifies kwargs |
| `plugins/jack-tar-cloud/.claude-plugin/plugin.json` | Modify | 1.2.0 → 1.2.1 |
| `.claude-plugin/marketplace.json` | Modify | jack-tar-cloud 1.2.0 → 1.2.1 |

### PR B — resolution plumbing (jack-tar-deckhand v1.2.0)

| File | Action | Responsibility |
|------|--------|----------------|
| `plugins/jack-tar-deckhand/src/render_funnel.py` | Modify | Add `cloud_2k`/`cloud_4k` stages; pass `resolution=` through; default per-stage provider+model |
| `plugins/jack-tar-deckhand/src/image_router.py` | Modify | Add `resolution` to RoutingTarget/UpgradeDecision; rename + extend `_check_openai_dimension_warning` → `_check_resolution_compatibility`; add resolution-aware routing for 2K/4K |
| `plugins/jack-tar-deckhand/src/schemas/strategy_map.schema.json` | Modify | Add optional `resolution` per slide; extend `render_funnel` enum |
| `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` | Modify | Step 9A — Pro escalation honours requested resolution; optional Flash 4K pre-test for 4K asks |
| `plugins/jack-tar-deckhand/skills/strategy-map/SKILL.md` | Modify | Speaker can mark hero slides for 2K/4K; cost implications surfaced |
| `plugins/jack-tar-deckhand/skills/narrative-architect/SKILL.md` | Modify | Resolution annotation when authoring outline |
| `plugins/jack-tar-deckhand/tests/test_render_funnel_resolution.py` | Create | Stage progression tests for cloud_2k/cloud_4k |
| `plugins/jack-tar-deckhand/tests/test_image_router_resolution.py` | Create | RoutingTarget/UpgradeDecision resolution-field tests + capability checks |
| `plugins/jack-tar-deckhand/tests/test_strategy_map_resolution.py` | Create | Schema validates 4K/2K resolutions |
| `plugins/integration_tests/test_resolution_end_to_end.py` | Create | 4K request reaches Nano Banana Pro through full bridge |
| `CLAUDE.md` | Modify | Resolution selection guide section |
| `plugins/jack-tar-deckhand/.claude-plugin/plugin.json` | Modify | 1.1.0 → 1.2.0 |
| `.claude-plugin/marketplace.json` | Modify | jack-tar-deckhand 1.1.0 → 1.2.0 |

---

# PR A — `jack-tar-cloud` v1.2.1: SKILL.md drift fix + `--resolution`

## Task A1: Static test harness for SKILL.md flag drift

**Files:**
- Create: `plugins/jack-tar-cloud/tests/test_skill_md_flags.py`

The drift bugs (fal `--size`/`--quality`, google `--size`) escaped because we have no test that compares the documented argument-hint to what the Generate snippet actually passes. This task creates that test before we touch any SKILL.md.

- [ ] **Step 1: Write the failing test**

```python
# plugins/jack-tar-cloud/tests/test_skill_md_flags.py
"""Static drift detection: every flag in a SKILL.md argument-hint must appear
in the Generate snippet's Python invocation."""
import re
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SKILLS = ['openai-image', 'google-image', 'fal-image', 'image']


def _read_skill(name):
    return (PLUGIN_ROOT / 'skills' / name / 'SKILL.md').read_text()


def _argument_hint_flags(text):
    """Return the set of long-form CLI flags declared in argument-hint frontmatter."""
    match = re.search(r'^argument-hint:\s*"?(.+?)"?\s*$', text, re.MULTILINE)
    if not match:
        return set()
    hint = match.group(1)
    return set(re.findall(r'--([a-z][a-z0-9-]*)', hint))


def _generate_block_kwargs(text):
    """Return the set of Python kwargs used in the Generate code block.

    Looks for the first ```bash ... python3 -c ... ``` block that calls
    generate_cloud_image and returns the kwarg names from that call.
    """
    blocks = re.findall(
        r'generate_cloud_image\s*\((.*?)\)',
        text,
        re.DOTALL,
    )
    if not blocks:
        return set()
    body = blocks[0]
    return set(re.findall(r'\b([a-z_][a-z0-9_]*)\s*=', body))


# Map CLI flag name -> kwarg name expected in generate_cloud_image call.
# A flag may legitimately be consumed before generate_cloud_image (eg. --output,
# --provider) so it isn't required to appear as a kwarg.
_NON_KWARG_FLAGS = {'output', 'provider', 'tier', 'colors', 'format'}

# Some flags are CLI-named differently from the kwarg
_FLAG_TO_KWARG = {
    'size': 'size',
    'quality': 'quality',
    'background': 'background',
    'model': 'model',
    'resolution': 'resolution',
}


@pytest.mark.parametrize('skill', SKILLS)
def test_every_documented_flag_reaches_generate_call(skill):
    text = _read_skill(skill)
    flags = _argument_hint_flags(text)
    kwargs = _generate_block_kwargs(text)

    missing = []
    for flag in flags:
        if flag in _NON_KWARG_FLAGS:
            continue
        kwarg = _FLAG_TO_KWARG.get(flag, flag)
        if kwarg not in kwargs:
            missing.append((flag, kwarg))

    assert not missing, (
        f"SKILL.md drift in {skill}: documented flag(s) not threaded "
        f"to generate_cloud_image: {missing}. "
        f"argument-hint flags: {sorted(flags)}; kwargs in Generate: {sorted(kwargs)}"
    )
```

- [ ] **Step 2: Run test to verify it fails for current drift**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/test_skill_md_flags.py -v`

Expected: FAIL with `fal-image: documented flag(s) not threaded — [('size','size'), ('quality','quality')]` and `google-image: [('size','size')]`. The openai-image case may pass (it threads everything).

- [ ] **Step 3: Commit the failing test**

```bash
cd /Users/stevejones/Documents/Development/jack-tar-deckhand/.worktrees/issue-60-resolution-control
git add plugins/jack-tar-cloud/tests/test_skill_md_flags.py
git commit -m "test(cloud): static drift detector for SKILL.md flags"
```

---

## Task A2: Fix `openai-image` — add `--resolution`

**Files:**
- Modify: `plugins/jack-tar-cloud/skills/openai-image/SKILL.md`

OpenAI maps to a fixed `size` parameter (3 values). `--resolution 1K` is the only legal tier; `--resolution 2K` / `--resolution 4K` should pass through and let the underlying function raise `ProviderResolutionUnsupportedError` with a clear message.

- [ ] **Step 1: Edit the argument-hint frontmatter**

In `argument-hint`, add `[--resolution 1K]`:

```yaml
argument-hint: "a description of the image" [--output PATH] [--size SIZE] [--quality low|medium|high] [--background auto|transparent] [--model MODEL] [--resolution 1K]
```

- [ ] **Step 2: Add resolution to the Parse Arguments section**

After the `--model` line:

```markdown
- **--resolution RES**: Tier preset (`1K`, `2K`, `4K`). Default: `1K`. Note: gpt-image-1.5 supports `1K` only; passing `2K`/`4K` raises `ProviderResolutionUnsupportedError` with a recommendation to switch provider.
```

- [ ] **Step 3: Thread resolution through the Generate block**

Modify the Python invocation to pass `resolution`:

```python
result = generate_cloud_image(
    prompt='''$PROMPT''',
    provider='openai',
    output_path='$OUTPUT',
    size='$SIZE',
    quality='$QUALITY',
    background='$BACKGROUND',
    resolution='$RESOLUTION',
)
```

- [ ] **Step 4: Refresh the Cost Reference table**

Replace the table with the EPIC #58 tier rows for OpenAI:

```markdown
## Cost Reference

| Provider | Model | Quality | Size | Resolution tier | Cost |
|----------|-------|---------|------|-----------------|------|
| OpenAI | gpt-image-1.5 | low | 1024x1024 | 1K | $0.009 |
| OpenAI | gpt-image-1.5 | medium | 1024x1024 | 1K | $0.034 |
| OpenAI | gpt-image-1.5 | medium | 1536x1024 | 1K | $0.051 |
| OpenAI | gpt-image-1.5 | high | 1024x1024 | 1K | $0.133 |
| OpenAI | gpt-image-1.5 | high | 1536x1024 | 1K | $0.200 |

OpenAI does not support 2K or 4K resolution tiers; route to Google Nano Banana for those.
```

- [ ] **Step 5: Run the drift detector**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/test_skill_md_flags.py::test_every_documented_flag_reaches_generate_call[openai-image] -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/jack-tar-cloud/skills/openai-image/SKILL.md
git commit -m "feat(cloud/openai-image): add --resolution flag"
```

---

## Task A3: Fix `google-image` — add `--resolution`, thread `--size`

**Files:**
- Modify: `plugins/jack-tar-cloud/skills/google-image/SKILL.md`

Google's `generate_cloud_image` ignores `size` (it consumes `model` + `resolution` + optional `aspect_ratio`). The current SKILL.md declares `--size` in argument-hint but never passes it. Two reasonable fixes: (a) translate `--size 1024x1024` to a synthetic aspect-ratio + resolution pair, or (b) drop the `--size` flag from the argument-hint since Google has no equivalent. We pick (b) — Google selects size via `--resolution` tier, not by explicit pixel dimensions, and pretending otherwise is misleading. Add a `--aspect-ratio` flag instead, since that's what the underlying API actually accepts.

- [ ] **Step 1: Edit the argument-hint frontmatter**

```yaml
argument-hint: "a description of the image" [--output PATH] [--aspect-ratio 16:9|1:1|4:3|9:16|3:4] [--model MODEL] [--tier draft|standard|premium] [--resolution 1K|2K|4K]
```

Note: `--size` removed (was silently dropped); `--aspect-ratio` added (real underlying parameter).

- [ ] **Step 2: Update Parse Arguments**

Replace the `--size` bullet with:

```markdown
- **--aspect-ratio RATIO**: Image aspect ratio (`16:9`, `1:1`, `4:3`, `9:16`, `3:4`). Default: `16:9`. Imagen 4 honours this; Nano Banana ignores it (resolution alone determines output dimensions).
- **--resolution RES**: Tier (`1K`, `2K`, `4K`). Default: `1K`. Per-model support:
  - `imagen-4.0-fast-generate-001`: 1K only
  - `imagen-4.0-generate-001` / `imagen-4.0-ultra-generate-001`: 1K, 2K
  - `gemini-3.1-flash-image-preview`: 512, 1K, 2K, 4K
  - `gemini-3-pro-image-preview`: 1K, 2K, 4K
```

- [ ] **Step 3: Thread arguments through the Generate block**

```python
result = generate_cloud_image(
    prompt='$PROMPT',
    provider='google',
    output_path='$OUTPUT_PATH',
    model='$MODEL',
    aspect_ratio='$ASPECT_RATIO',
    resolution='$RESOLUTION',
)
```

- [ ] **Step 4: Add a Cost Reference table**

```markdown
## Cost Reference

| Model | 512 | 1K | 2K | 4K |
|---|---|---|---|---|
| imagen-4.0-fast-generate-001 (Vertex) | — | $0.020 | n/a | n/a |
| imagen-4.0-generate-001 (Vertex) | — | $0.040 | $0.040 | n/a |
| imagen-4.0-generate-001 (Dev API) | — | $0.040 | $0.101 | n/a |
| imagen-4.0-ultra-generate-001 (Vertex) | — | $0.060 | $0.060 | n/a |
| gemini-3.1-flash-image-preview | $0.045 | $0.067 | $0.101 | $0.151 |
| gemini-3-pro-image-preview | — | $0.134 | $0.134 | $0.240 |

Imagen pricing depends on backend: `GOOGLE_APPLICATION_CREDENTIALS` set → Vertex AI flat per-image; `GOOGLE_API_KEY` only → Gemini Developer API token-based.
```

- [ ] **Step 5: Run the drift detector**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/test_skill_md_flags.py::test_every_documented_flag_reaches_generate_call[google-image] -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/jack-tar-cloud/skills/google-image/SKILL.md
git commit -m "feat(cloud/google-image): add --resolution; replace silently-dropped --size with --aspect-ratio"
```

---

## Task A4: Fix `fal-image` — add `--resolution`, translate `--size`, drop bogus `--quality`

**Files:**
- Modify: `plugins/jack-tar-cloud/skills/fal-image/SKILL.md`

FAL's `generate_cloud_image` takes `image_size` (string preset OR `{'width':W, 'height':H}` dict) — it has no `size` or `quality` parameter, so both flags are silently dropped today. We honour `--size 1920x1080` by translating to the dict form, and remove `--quality` from documentation since FAL has no quality knob.

- [ ] **Step 1: Edit the argument-hint frontmatter**

```yaml
argument-hint: "a description of the image" [--output PATH] [--size WxH] [--model MODEL] [--resolution 1K|2K]
```

Note: `--quality` removed; `--size` retained (we now actually thread it); `--resolution` added.

- [ ] **Step 2: Update Parse Arguments**

```markdown
- **Prompt**: The quoted description
- **--output PATH**: Where to save (default: `output/fal-YYYYMMDD-HHMMSS.png`)
- **--size WxH**: Explicit pixel dimensions (e.g. `1920x1080` or `2048x2048`). Translated to FAL `image_size={"width":W, "height":H}`. If omitted, `--resolution` selects a sensible preset.
- **--model MODEL**: FAL endpoint (default: `fal-ai/flux-2-pro`). Other options: `fal-ai/flux-2-klein`, `fal-ai/ideogram/v3`.
- **--resolution RES**: Tier (`1K`, `2K`). Default: `1K`. FLUX 2 Pro supports both; Klein and Ideogram support 1K only.
```

- [ ] **Step 3: Translate `--size` and thread arguments through Generate**

Replace the Generate block with:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.generate_cloud_image import generate_cloud_image

kwargs = dict(
    prompt='$PROMPT',
    provider='fal',
    output_path='$OUTPUT_PATH',
    model='$MODEL',
    resolution='$RESOLUTION',
)

# --size 1920x1080 translates to image_size dict
size = '$SIZE'
if size and 'x' in size:
    w, h = size.split('x')
    kwargs['image_size'] = {'width': int(w), 'height': int(h)}

result = generate_cloud_image(**kwargs)
print(json.dumps(result, indent=2))
"
```

- [ ] **Step 4: Add a Cost Reference table**

```markdown
## Cost Reference

| Model | 1K (1MP) | 2K (4MP) | Notes |
|---|---|---|---|
| fal-ai/flux-2-pro | $0.030 | $0.075 | tiered: $0.030 first MP + $0.015/extra MP |
| fal-ai/flux-2-klein | $0.014 | n/a | flat |
| fal-ai/ideogram/v3 | $0.060 | n/a | flat |
```

- [ ] **Step 5: Run the drift detector**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/test_skill_md_flags.py::test_every_documented_flag_reaches_generate_call[fal-image] -v`

Expected: PASS. The `image_size` kwarg appears in the dict construction so the regex finds it via the `kwargs[...] =` assignment — extend `_generate_block_kwargs` if the test fails on the regex form. (Verify; if needed, add `image_size` to detection.)

- [ ] **Step 6: Update the static drift detector if needed**

If the `image_size` assignment isn't picked up by the regex, broaden it:

```python
def _generate_block_kwargs(text):
    blocks = re.findall(r'generate_cloud_image\s*\((.*?)\)', text, re.DOTALL)
    kwargs = set()
    if blocks:
        kwargs.update(re.findall(r'\b([a-z_][a-z0-9_]*)\s*=', blocks[0]))
    # Also recognise kwargs[...] = ... assignments before the call
    kwargs.update(re.findall(r"kwargs\[['\"]([a-z_][a-z0-9_]*)['\"]\]\s*=", text))
    return kwargs
```

- [ ] **Step 7: Commit**

```bash
git add plugins/jack-tar-cloud/skills/fal-image/SKILL.md plugins/jack-tar-cloud/tests/test_skill_md_flags.py
git commit -m "feat(cloud/fal-image): add --resolution; translate --size to image_size dict; drop bogus --quality"
```

---

## Task A5: Fix `image` smart router — pass `--resolution` through

**Files:**
- Modify: `plugins/jack-tar-cloud/skills/image/SKILL.md`

The smart router dispatches to per-provider skills. It needs to forward `--resolution` to whichever skill it picks.

- [ ] **Step 1: Edit the argument-hint frontmatter**

```yaml
argument-hint: "a description of the image" [--output PATH] [--size WxH] [--quality low|medium|high] [--provider openai|google|fal] [--model MODEL] [--resolution 1K|2K|4K]
```

- [ ] **Step 2: Update Parse Arguments**

Add after the `--provider` bullet:

```markdown
- **--resolution RES**: Tier (`1K`, `2K`, `4K`). Default: `1K`. Forwarded to the chosen per-provider skill. Provider must support the requested tier — see EPIC #58 capability matrix.
```

- [ ] **Step 3: Update the Select Provider and Route section**

Add after "Pass through all arguments":

```markdown
**Resolution-aware routing:** when `--resolution 4K` is requested, restrict to providers that support it (Google Nano Banana Pro/Flash). When `--resolution 2K`, restrict to Google (Imagen Standard, Nano Banana Pro/Flash) or FAL FLUX 2 Pro. When `--resolution 1K` (default), all available providers are eligible.

Forward the flag to the dispatched per-provider skill:
- `--resolution 1K` (or omitted) → no change to existing routing
- `--resolution 2K` → fal-image (FLUX 2 Pro) or google-image (Imagen Standard / Nano Banana Pro)
- `--resolution 4K` → google-image with `--model gemini-3.1-flash-image-preview` (Flash 4K, $0.151) or `--model gemini-3-pro-image-preview` (Pro 4K, $0.240)
```

- [ ] **Step 4: Run the drift detector**

Note: `image` is a router skill, not a direct caller of `generate_cloud_image`. The static test in A1 only inspects skills that contain a `generate_cloud_image` call. Mark this skill as router-only by adding a SKILL-level annotation or extending the test:

```python
# In test_skill_md_flags.py — at top of test file:
_ROUTER_SKILLS = {'image'}  # routes to per-provider skills, doesn't call generate_cloud_image directly

@pytest.mark.parametrize('skill', SKILLS)
def test_every_documented_flag_reaches_generate_call(skill):
    if skill in _ROUTER_SKILLS:
        # Router skills are validated by separate forwarding test, not this one
        pytest.skip(f"{skill} is a router; use test_router_forwards_flag instead")
    # ... existing body
```

Then add a router-specific test:

```python
def test_image_router_forwards_resolution_flag():
    text = _read_skill('image')
    # Resolution flag must appear in argument-hint and in the routing description
    flags = _argument_hint_flags(text)
    assert 'resolution' in flags, "image router missing --resolution in argument-hint"
    assert '--resolution' in text and 'forward' in text.lower(), (
        "image router SKILL.md must document forwarding --resolution to dispatched skills"
    )
```

- [ ] **Step 5: Run the new tests**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/test_skill_md_flags.py -v`

Expected: 4 PASS (openai/google/fal direct + image router), 0 FAIL.

- [ ] **Step 6: Commit**

```bash
git add plugins/jack-tar-cloud/skills/image/SKILL.md plugins/jack-tar-cloud/tests/test_skill_md_flags.py
git commit -m "feat(cloud/image): forward --resolution; resolution-aware provider restriction"
```

---

## Task A6: Cross-plugin integration test — `--resolution 4K` reaches `generate_cloud_image`

**Files:**
- Create: `plugins/integration_tests/test_cloud_skill_resolution.py`

The static drift test catches naming mismatches. This integration test catches behavioural drift — actually invoking the SKILL.md's Generate snippet (with mocked credentials) and verifying the `resolution` kwarg arrives at `generate_cloud_image`.

- [ ] **Step 1: Write the failing test**

```python
# plugins/integration_tests/test_cloud_skill_resolution.py
"""Integration: SKILL.md --resolution flag reaches generate_cloud_image kwargs."""
from pathlib import Path
from unittest import mock

import pytest

CLOUD_PLUGIN = Path(__file__).resolve().parent.parent / 'jack-tar-cloud'


def _exec_generate_block(skill_name, env_substitutions):
    """Extract and exec the Generate Python snippet from a SKILL.md file.

    Substitutes $PROMPT, $OUTPUT_PATH, etc. into the snippet, mocks
    generate_cloud_image to capture kwargs without making an API call,
    and returns the captured kwargs.
    """
    import re
    skill_text = (CLOUD_PLUGIN / 'skills' / skill_name / 'SKILL.md').read_text()
    # Find the Generate block — first ```bash that contains "from src.generate_cloud_image"
    blocks = re.findall(r'```bash\n(.*?)```', skill_text, re.DOTALL)
    gen_block = next((b for b in blocks if 'generate_cloud_image' in b), None)
    assert gen_block, f"{skill_name}: no generate_cloud_image bash block"

    # Pull the python3 -c "..." body out of the bash heredoc
    py_match = re.search(r'python3 -c "(.+?)"\s*$', gen_block, re.DOTALL)
    assert py_match, f"{skill_name}: no python3 -c body found"
    py_body = py_match.group(1)

    # Substitute placeholders
    for k, v in env_substitutions.items():
        py_body = py_body.replace(f'${k}', v)

    # Mock and exec
    captured = {}
    def fake_generate(**kwargs):
        captured.update(kwargs)
        return {'file_path': kwargs.get('output_path', '/tmp/x'), 'cost_usd': 0.0}

    import sys
    sys.path.insert(0, str(CLOUD_PLUGIN))
    try:
        with mock.patch('src.generate_cloud_image.generate_cloud_image', fake_generate):
            ns = {'__name__': '__main__'}
            exec(py_body, ns)
    finally:
        sys.path.remove(str(CLOUD_PLUGIN))
    return captured


def test_openai_skill_threads_resolution():
    captured = _exec_generate_block('openai-image', {
        'PROMPT': 'a lighthouse',
        'OUTPUT': '/tmp/o.png',
        'SIZE': '1024x1024',
        'QUALITY': 'medium',
        'BACKGROUND': 'auto',
        'RESOLUTION': '1K',
    })
    assert captured['resolution'] == '1K'
    assert captured['provider'] == 'openai'


def test_google_skill_threads_resolution_4k():
    captured = _exec_generate_block('google-image', {
        'PROMPT': 'a lighthouse',
        'OUTPUT_PATH': '/tmp/g.png',
        'MODEL': 'gemini-3-pro-image-preview',
        'ASPECT_RATIO': '16:9',
        'RESOLUTION': '4K',
    })
    assert captured['resolution'] == '4K'
    assert captured['model'] == 'gemini-3-pro-image-preview'


def test_fal_skill_translates_size_and_threads_resolution():
    captured = _exec_generate_block('fal-image', {
        'PROMPT': 'a lighthouse',
        'OUTPUT_PATH': '/tmp/f.png',
        'SIZE': '2048x2048',
        'MODEL': 'fal-ai/flux-2-pro',
        'RESOLUTION': '2K',
    })
    assert captured['resolution'] == '2K'
    assert captured.get('image_size') == {'width': 2048, 'height': 2048}, (
        f"fal --size should translate to image_size dict, got {captured.get('image_size')!r}"
    )
```

- [ ] **Step 2: Run the test**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/integration_tests/test_cloud_skill_resolution.py -v`

Expected: All 3 PASS.

- [ ] **Step 3: Commit**

```bash
git add plugins/integration_tests/test_cloud_skill_resolution.py
git commit -m "test(integration): SKILL.md --resolution reaches generate_cloud_image"
```

---

## Task A7: Bump cloud plugin to 1.2.1 and sync marketplace

**Files:**
- Modify: `plugins/jack-tar-cloud/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Bump plugin.json**

In `plugins/jack-tar-cloud/.claude-plugin/plugin.json`, change `"version": "1.2.0"` → `"version": "1.2.1"`.

- [ ] **Step 2: Bump marketplace manifest**

In `.claude-plugin/marketplace.json`, find the `jack-tar-cloud` entry and bump `"version": "1.2.0"` → `"version": "1.2.1"`.

- [ ] **Step 3: Run JSON validation**

Run: `python3 -c "import json; json.load(open('.claude-plugin/marketplace.json')); json.load(open('plugins/jack-tar-cloud/.claude-plugin/plugin.json')); print('OK')"`

Expected: `OK`

- [ ] **Step 4: Run all cloud plugin tests**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-cloud/tests/ -v`

Expected: 50 (existing) + new drift tests, all PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-cloud/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore(cloud): bump 1.2.0 → 1.2.1 (skill drift fixes + --resolution)"
```

---

## Task A8: Push and open PR A

- [ ] **Step 1: Push branch**

```bash
git push -u origin feat/issue-60-cloud-skill-drift
```

- [ ] **Step 2: Open PR**

```bash
gh pr create --title "feat(jack-tar-cloud): SKILL.md --resolution flag + drift fixes" --body "$(cat <<'EOF'
## Summary
- Add `--resolution` flag to all four cloud-image SKILL.md files (openai/google/fal/image router)
- Fix silent-drop drift: `fal-image --size`, `fal-image --quality`, `google-image --size`
- Add static drift detector test (would have caught the original drift) + cross-plugin integration test
- Bump jack-tar-cloud 1.2.0 → 1.2.1

Refs #60 (section 4 — drift fixes only). Larger deckhand-side resolution plumbing follows in a second PR.

## Test plan
- [x] Static drift detector passes for all 4 skills
- [x] Cross-plugin integration test verifies kwargs reach generate_cloud_image
- [x] Existing 50 cloud plugin tests pass
- [x] CI: code-quality, plugin-tests-cloud, integration-tests, json-validation
EOF
)"
```

- [ ] **Step 3: Wait for CI green, then merge**

```bash
# After CI passes (do not use --admin)
gh pr merge <N> --merge
```

- [ ] **Step 4: Update local main, switch worktree to PR B branch**

```bash
git fetch origin main
git checkout -b feat/issue-60-resolution-plumbing origin/main
```

---

# PR B — `jack-tar-deckhand` v1.2.0: resolution plumbing through pipeline

## Task B1: Render funnel — add `cloud_2k`/`cloud_4k` stages

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/render_funnel.py:82-110`
- Create: `plugins/jack-tar-deckhand/tests/test_render_funnel_resolution.py`

- [ ] **Step 1: Write the failing test**

```python
# plugins/jack-tar-deckhand/tests/test_render_funnel_resolution.py
"""Resolution-aware funnel stages: cloud_2k and cloud_4k."""
from unittest import mock
import pytest

from src import render_funnel


def test_cloud_2k_stage_calls_generate_with_resolution_2k(tmp_path):
    render_funnel.init_render_log(str(tmp_path))
    fake = mock.Mock(return_value={
        'file_path': str(tmp_path / 'out.png'),
        'cost_usd': 0.101,
    })
    with mock.patch('src.render_funnel._generate_cloud_raw', fake):
        result = render_funnel.execute_funnel_stage(
            deck_dir=str(tmp_path),
            slide_number=1,
            strategy='full_render',
            prompt='a lighthouse',
            funnel_stage='cloud_2k',
            model='gemini-3.1-flash-image-preview',
            output_path=str(tmp_path / 'out.png'),
            provider='google',
        )
    assert result['status'] == 'generated'
    call_kwargs = fake.call_args.kwargs
    assert call_kwargs['resolution'] == '2K'
    assert call_kwargs['provider'] == 'google'


def test_cloud_4k_stage_calls_generate_with_resolution_4k(tmp_path):
    render_funnel.init_render_log(str(tmp_path))
    fake = mock.Mock(return_value={
        'file_path': str(tmp_path / 'out.png'),
        'cost_usd': 0.240,
    })
    with mock.patch('src.render_funnel._generate_cloud_raw', fake):
        result = render_funnel.execute_funnel_stage(
            deck_dir=str(tmp_path),
            slide_number=1,
            strategy='full_render',
            prompt='a lighthouse',
            funnel_stage='cloud_4k',
            model='gemini-3-pro-image-preview',
            output_path=str(tmp_path / 'out.png'),
            provider='google',
        )
    assert result['status'] == 'generated'
    assert fake.call_args.kwargs['resolution'] == '4K'


def test_cloud_full_default_passes_1k(tmp_path):
    """Default cloud_full stage preserves prior behaviour: resolution='1K'."""
    render_funnel.init_render_log(str(tmp_path))
    fake = mock.Mock(return_value={'file_path': str(tmp_path / 'out.png'), 'cost_usd': 0.05})
    with mock.patch('src.render_funnel._generate_cloud_raw', fake):
        render_funnel.execute_funnel_stage(
            deck_dir=str(tmp_path),
            slide_number=1,
            strategy='full_render',
            prompt='x',
            funnel_stage='cloud_full',
            model='gemini-3.1-flash-image-preview',
            output_path=str(tmp_path / 'out.png'),
            provider='google',
        )
    assert fake.call_args.kwargs['resolution'] == '1K'
```

- [ ] **Step 2: Run test to verify failure**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_render_funnel_resolution.py -v`

Expected: FAIL with `funnel_stage 'cloud_2k'` not in `_OLLAMA_RESOLUTIONS` (or test that resolution kwarg isn't passed).

- [ ] **Step 3: Implement — extend render_funnel module dictionaries and `_generate_cloud`**

In `plugins/jack-tar-deckhand/src/render_funnel.py`, replace the resolution/quality/size tables and the `_generate_cloud` helper:

```python
# Resolution defaults per funnel stage (used for legacy width/height logging).
_OLLAMA_RESOLUTIONS = {
    'ollama': {'width': 1024, 'height': 576},
    'cloud_low': {'width': 1280, 'height': 720},
    'cloud_full': {'width': 1920, 'height': 1080},
    'cloud_2k': {'width': 2048, 'height': 2048},
    'cloud_4k': {'width': 4096, 'height': 4096},
}

# Cloud provider quality settings per stage (OpenAI 'quality' kwarg).
_CLOUD_STAGE_QUALITY = {
    'cloud_low': 'low',
    'cloud_full': 'medium',
    'cloud_2k': 'medium',  # n/a for non-OpenAI; ignored when provider != 'openai'
    'cloud_4k': 'medium',
}

_CLOUD_STAGE_SIZE = {
    'cloud_low': '1024x1024',
    'cloud_full': '1536x1024',
    # cloud_2k/cloud_4k do not set size — they use resolution kwarg directly.
}

# Per-stage resolution tier — drives generate_cloud_image's resolution kwarg.
_CLOUD_STAGE_RESOLUTION = {
    'cloud_low': '1K',
    'cloud_full': '1K',
    'cloud_2k': '2K',
    'cloud_4k': '4K',
}

# Per-stage default provider+model when the caller doesn't specify.
# 2K/4K force Google because Nano Banana Pro/Flash are the only models
# that support those tiers across the matrix.
_CLOUD_STAGE_DEFAULT_PROVIDER_MODEL = {
    'cloud_2k': ('google', 'gemini-3.1-flash-image-preview'),
    'cloud_4k': ('google', 'gemini-3-pro-image-preview'),
}


def _generate_cloud(prompt, provider, output_path, funnel_stage, model=None):
    """Wrapper for cloud generation with funnel-stage-appropriate settings.

    For cloud_2k / cloud_4k stages, falls back to a default provider+model
    if caller passes None/'' — these stages are tier-defined, not provider-defined.
    """
    if not provider and funnel_stage in _CLOUD_STAGE_DEFAULT_PROVIDER_MODEL:
        provider, default_model = _CLOUD_STAGE_DEFAULT_PROVIDER_MODEL[funnel_stage]
        if not model:
            model = default_model

    kwargs = {
        'prompt': prompt,
        'provider': provider,
        'output_path': output_path,
        'resolution': _CLOUD_STAGE_RESOLUTION.get(funnel_stage, '1K'),
    }
    if funnel_stage in _CLOUD_STAGE_SIZE:
        kwargs['size'] = _CLOUD_STAGE_SIZE[funnel_stage]
    if funnel_stage in _CLOUD_STAGE_QUALITY and provider == 'openai':
        kwargs['quality'] = _CLOUD_STAGE_QUALITY[funnel_stage]
    if model:
        kwargs['model'] = model
    return _generate_cloud_raw(**kwargs)
```

Update the call site in `execute_funnel_stage`:

```python
        else:
            result = _generate_cloud(
                prompt, provider, output_path, funnel_stage, model=model,
            )
            cost = result.get('cost_usd', 0.0)
            resolution = _CLOUD_STAGE_RESOLUTION.get(funnel_stage, '1K')
```

- [ ] **Step 4: Run test to verify pass**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_render_funnel_resolution.py -v`

Expected: 3 PASS.

- [ ] **Step 5: Run all existing render_funnel tests to confirm no regression**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-deckhand/tests/ -k render_funnel -v`

Expected: existing 8 + new 3 PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/jack-tar-deckhand/src/render_funnel.py plugins/jack-tar-deckhand/tests/test_render_funnel_resolution.py
git commit -m "feat(deckhand/render-funnel): add cloud_2k/cloud_4k stages with resolution kwarg"
```

---

## Task B2: Image router — add `resolution` to RoutingTarget and UpgradeDecision

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/image_router.py:17-46`
- Create: `plugins/jack-tar-deckhand/tests/test_image_router_resolution.py`

- [ ] **Step 1: Write the failing test**

```python
# plugins/jack-tar-deckhand/tests/test_image_router_resolution.py
"""Resolution-aware routing: RoutingTarget/UpgradeDecision carry resolution
field and the router prefers Nano Banana Pro for 4K asks."""
import pytest

from src import image_router


def test_routing_target_has_resolution_field():
    t = image_router.RoutingTarget(
        skill='cloud-generate-image',
        provider='google',
        model='gemini-3-pro-image-preview',
        cost_per_image=0.24,
        resolution='4K',
    )
    assert t.resolution == '4K'


def test_routing_target_resolution_defaults_to_1k():
    """Backwards compat: existing call sites that don't pass resolution
    still construct a valid RoutingTarget."""
    t = image_router.RoutingTarget(
        skill='cloud-generate-image',
        provider='fal',
        model='fal-ai/flux-2-pro',
        cost_per_image=0.03,
    )
    assert t.resolution == '1K'


def test_upgrade_decision_has_resolution_field():
    u = image_router.UpgradeDecision(
        slide_number=1,
        image_id='slide-01-hero',
        action='upgrade',
        reason='hero benefits from 4K',
        draft_prompt='a lighthouse',
        target_provider='google',
        target_model='gemini-3-pro-image-preview',
        target_size='4096x4096',
        target_resolution='4K',
        estimated_cost_usd=0.24,
        warnings=[],
    )
    assert u.target_resolution == '4K'


def test_check_resolution_compatibility_warns_for_unsupported_tier():
    """OpenAI doesn't support 4K — router must surface a warning."""
    warning = image_router._check_resolution_compatibility(
        provider='openai', model='gpt-image-1.5', resolution='4K',
    )
    assert warning is not None
    assert '4K' in warning and 'openai' in warning.lower()


def test_check_resolution_compatibility_silent_for_supported_tier():
    warning = image_router._check_resolution_compatibility(
        provider='google', model='gemini-3-pro-image-preview', resolution='4K',
    )
    assert warning is None


def test_router_prefers_nano_banana_pro_for_4k_hero():
    """When a hero slide requests 4K production, route to Nano Banana Pro."""
    slide = {'slide_number': 1, 'visual_type': 'hero_image', 'resolution': '4K'}
    available = {
        'google': {'available': True},
        'openai': {'available': True},
        'fal': {'available': True},
    }
    decision = image_router.route_slide(
        slide, mode='production',
        available_providers=available,
        budget_state='allow',
    )
    assert decision.provider == 'google'
    assert decision.model == 'gemini-3-pro-image-preview'
    assert decision.resolution == '4K'
```

- [ ] **Step 2: Run to verify failure**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_image_router_resolution.py -v`

Expected: FAIL — `RoutingTarget` doesn't have `resolution`, `_check_resolution_compatibility` doesn't exist.

- [ ] **Step 3: Implement — extend namedtuples with default `resolution`**

In `plugins/jack-tar-deckhand/src/image_router.py`, change RoutingTarget and UpgradeDecision:

```python
RoutingTarget = namedtuple(
    'RoutingTarget',
    ['skill', 'provider', 'model', 'cost_per_image', 'resolution'],
    defaults=['1K'],  # resolution defaults to 1K so existing callers work unchanged
)

UpgradeDecision = namedtuple(
    'UpgradeDecision',
    [
        'slide_number', 'image_id', 'action', 'reason', 'draft_prompt',
        'target_provider', 'target_model', 'target_size',
        'target_resolution',  # new
        'estimated_cost_usd', 'warnings',
    ],
    defaults=['1K', 0.0, []],  # target_resolution, estimated_cost_usd, warnings
)
```

Note: any existing `UpgradeDecision(...)` call sites that pass positional arguments now need to keep `target_resolution` before the cost/warnings tail. Check the file for existing constructors and update.

- [ ] **Step 4: Update existing UpgradeDecision constructions in image_router.py**

Find each `UpgradeDecision(` constructor in the file and add `target_resolution='1K'` (or carry from route) as a keyword arg. Existing code at lines ~398, 412, 437, 457 need updating. Example for the 'upgrade' branch around line 457:

```python
        decisions.append(UpgradeDecision(
            slide_number=slide_num,
            image_id=image_id,
            action='upgrade',
            reason=f'{visual_type} benefits from cloud quality',
            draft_prompt=draft_prompt,
            target_provider=route.provider,
            target_model=route.model,
            target_size=target_size,
            target_resolution=route.resolution,
            estimated_cost_usd=route.cost_per_image,
            warnings=warnings,
        ))
```

For the 'keep' branches, set `target_resolution='1K'` (or the slide's prior resolution).

- [ ] **Step 5: Implement `_check_resolution_compatibility` (rename + extend)**

Replace `_check_openai_dimension_warning` with the renamed and extended version. Keep the old function as a thin shim for backwards compat:

```python
# Per-provider/model resolution capability — mirrors the cloud plugin's
# _MODEL_RESOLUTIONS so the deckhand can validate without importing across plugins.
_PROVIDER_MODEL_RESOLUTIONS = {
    ('openai', 'gpt-image-1.5'): ['1K'],
    ('openai', 'gpt-image-1.5-low'): ['1K'],
    ('openai', 'gpt-image-1.5-med'): ['1K'],
    ('google', 'imagen-4-fast'): ['1K'],
    ('google', 'imagen-4.0-fast-generate-001'): ['1K'],
    ('google', 'imagen-4-standard'): ['1K', '2K'],
    ('google', 'imagen-4.0-generate-001'): ['1K', '2K'],
    ('google', 'imagen-4.0-ultra-generate-001'): ['1K', '2K'],
    ('google', 'gemini-3.1-flash-image-preview'): ['512', '1K', '2K', '4K'],
    ('google', 'gemini-3-pro-image-preview'): ['1K', '2K', '4K'],
    ('fal', 'fal-ai/flux-2-pro'): ['1K', '2K'],
    ('fal', 'flux-2-pro'): ['1K', '2K'],
    ('fal', 'fal-ai/flux-2-klein'): ['1K'],
    ('fal', 'fal-ai/ideogram/v3'): ['1K'],
}


def _check_resolution_compatibility(provider, model, resolution):
    """Return a warning string if provider/model doesn't support the tier.

    Returns None if the tier is supported or the provider/model is unknown
    (unknown is not an error — the underlying call will surface the failure).
    """
    if not resolution:
        return None
    supported = _PROVIDER_MODEL_RESOLUTIONS.get((provider, model))
    if supported is None:
        return None  # unknown — let the cloud plugin surface the error
    if resolution in supported:
        return None
    return (
        f"{provider}/{model} does not support resolution={resolution!r}. "
        f"Supported tiers: {supported}. "
        f"Pick a different model or downgrade the slide's resolution request."
    )


def _check_openai_dimension_warning(provider, target_dims):
    """Backwards-compat shim — preserved so existing call sites still work."""
    if provider != 'openai':
        return None
    if target_dims is None:
        return None
    if target_dims in OPENAI_SUPPORTED_SIZES:
        return None
    return (
        f'OpenAI supports only 1024x1024, 1536x1024, 1024x1536. '
        f'Target {target_dims} requires cropping or a different provider '
        f'(FLUX Pro supports arbitrary dimensions).'
    )
```

- [ ] **Step 6: Add resolution-aware routing matrix entries**

Extend ROUTING_MATRIX to include `(hero_image, 'production_2k')` and `(hero_image, 'production_4k')` modes that prefer Google Nano Banana, and update `route_slide` to read `slide.resolution` when present.

In ROUTING_MATRIX, add:

```python
    ('hero_image', 'production_2k'): [
        RoutingTarget('cloud-generate-image', 'google', 'gemini-3.1-flash-image-preview', 0.101, '2K'),
        RoutingTarget('cloud-generate-image', 'fal', 'fal-ai/flux-2-pro', 0.075, '2K'),
        RoutingTarget('cloud-generate-image', 'google', 'imagen-4.0-generate-001', 0.04, '2K'),
    ],
    ('hero_image', 'production_4k'): [
        RoutingTarget('cloud-generate-image', 'google', 'gemini-3-pro-image-preview', 0.24, '4K'),
        RoutingTarget('cloud-generate-image', 'google', 'gemini-3.1-flash-image-preview', 0.151, '4K'),
    ],
```

In `route_slide`, before the budget-state branch, derive the effective mode:

```python
    # Resolution-aware mode: a slide-level resolution hint upgrades the
    # mode key so we hit the high-res routing rows in ROUTING_MATRIX.
    requested_resolution = slide.get('resolution', '1K')
    effective_mode = mode
    if mode == 'production' and requested_resolution in ('2K', '4K'):
        effective_mode = f'production_{requested_resolution.lower()}'
```

Replace `mode` with `effective_mode` in the subsequent ROUTING_MATRIX lookups.

- [ ] **Step 7: Run all router tests**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_image_router_resolution.py plugins/jack-tar-deckhand/tests/ -k image_router -v`

Expected: new 6 tests PASS, existing 35 router tests PASS.

- [ ] **Step 8: Commit**

```bash
git add plugins/jack-tar-deckhand/src/image_router.py plugins/jack-tar-deckhand/tests/test_image_router_resolution.py
git commit -m "feat(deckhand/image-router): resolution-aware routing for 2K/4K hero slides"
```

---

## Task B3: Strategy map schema — optional `resolution` per slide; extended `render_funnel` enum

**Files:**
- Modify: `plugins/jack-tar-deckhand/src/schemas/strategy_map.schema.json`
- Create: `plugins/jack-tar-deckhand/tests/test_strategy_map_resolution.py`

- [ ] **Step 1: Write the failing test**

```python
# plugins/jack-tar-deckhand/tests/test_strategy_map_resolution.py
import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / 'src' / 'schemas' / 'strategy_map.schema.json'
)


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text())


def _base_slide():
    return {
        'slide_number': 1,
        'strategy': 'full_render',
        'rationale': 'hero opener',
        'render_funnel': ['ollama', 'cloud_low', 'cloud_full'],
    }


def test_4k_resolution_allowed(schema):
    sm = {
        'approval_mode': 'review',
        'slides': [{**_base_slide(), 'resolution': '4K'}],
    }
    jsonschema.validate(sm, schema)  # should not raise


def test_2k_resolution_allowed(schema):
    sm = {
        'approval_mode': 'review',
        'slides': [{**_base_slide(), 'resolution': '2K'}],
    }
    jsonschema.validate(sm, schema)


def test_invalid_resolution_rejected(schema):
    sm = {
        'approval_mode': 'review',
        'slides': [{**_base_slide(), 'resolution': '8K'}],
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(sm, schema)


def test_render_funnel_accepts_cloud_2k_and_cloud_4k(schema):
    sm = {
        'approval_mode': 'review',
        'slides': [{
            **_base_slide(),
            'render_funnel': ['ollama', 'cloud_low', 'cloud_full', 'cloud_2k', 'cloud_4k'],
            'resolution': '4K',
        }],
    }
    jsonschema.validate(sm, schema)


def test_resolution_omitted_still_valid(schema):
    sm = {'approval_mode': 'review', 'slides': [_base_slide()]}
    jsonschema.validate(sm, schema)
```

- [ ] **Step 2: Run test to verify failure**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_strategy_map_resolution.py -v`

Expected: FAIL — `cloud_2k`/`cloud_4k` not in enum, `resolution` not declared.

- [ ] **Step 3: Edit the schema**

In `plugins/jack-tar-deckhand/src/schemas/strategy_map.schema.json`, modify `render_funnel`:

```json
          "render_funnel": {
            "type": "array",
            "items": {
              "type": "string",
              "enum": ["ollama", "cloud_low", "cloud_full", "cloud_2k", "cloud_4k"]
            }
          },
```

Add a new property in the slide object's `properties` block (alongside `backdrop_variant`):

```json
          "resolution": {
            "type": "string",
            "enum": ["512", "1K", "2K", "4K"],
            "default": "1K",
            "description": "Optional slide-level resolution tier. Default '1K'. Hero slides may opt into '2K' or '4K' via Google Nano Banana Pro/Flash. Cost implications are surfaced in the strategy-map skill."
          },
```

- [ ] **Step 4: Run test to verify pass**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-deckhand/tests/test_strategy_map_resolution.py -v`

Expected: 5 PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-deckhand/src/schemas/strategy_map.schema.json plugins/jack-tar-deckhand/tests/test_strategy_map_resolution.py
git commit -m "feat(deckhand/schema): strategy-map slide.resolution + cloud_2k/cloud_4k stages"
```

---

## Task B4: Imagegen-bridge SKILL.md — Step 9A honours requested resolution

**Files:**
- Modify: `plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md` (Step 9A — Pro escalation block, ~lines 444-454)

The current Step 9A Pro escalation calls `--width WIDTH --height HEIGHT` with hardcoded WIDTH/HEIGHT placeholders. We rewrite to honour the slide's `resolution` from the strategy map.

- [ ] **Step 1: Modify Step 9A Phase 2 (Pro escalation)**

Replace the Phase 2 block (around line 444-454) with:

```markdown
**Phase 2 — Pro escalation (single shot, resolution-aware)**

7. Read `slide.resolution` from the strategy map (defaults to `1K` if absent). If the slide opted into `2K` or `4K`, the Pro escalation uses that tier — not always `1K`.

8. **Optional Flash 4K pre-test (only when slide.resolution == '4K')** — before paying for Pro 4K ($0.240), do a Flash 4K validation render at $0.151:
   ```
   /jack-tar-cloud:google-image "REFINED_PROMPT" --model gemini-3.1-flash-image-preview --resolution 4K --output ./tmp/deck/images/slide-NN-hero-flash4k.png
   ```
   Dispatch image-reviewer. If pass: stop, use Flash 4K as final. If refine: proceed to Pro 4K. (This pattern was validated by the resolution smoke test in #59 — Flash 4K caught prompt issues that 1K Flash missed because text rendering scales differently.)

9. If Flash passes (on any iteration) and the slide opted into 2K or 4K, take the prompt that produced the passing Flash result and generate once with Pro at the requested tier:
   ```
   /jack-tar-cloud:google-image "REFINED_PROMPT" --model gemini-3-pro-image-preview --resolution {slide.resolution} --output ./tmp/deck/images/slide-NN-hero.png
   ```
   For 1K slides (the default), keep the existing single-shot Pro 1K behaviour.

10. Dispatch `image-reviewer` on the Pro output. Pro gets ONE shot — no iterations.
    - If pass: use Pro as final output.
    - If refine: flag for Speaker with `status: "flag_for_speaker"` in the manifest.
```

- [ ] **Step 2: Add a Cost Projection paragraph at the start of Step 9A**

Insert after the `for entry in plan['entries']:` example block:

```markdown
**Resolution-aware cost projection.** Before Phase 1, compute the projected spend for each entry using `slide.resolution`:

| Tier | Flash draft (up to 3) | Pro escalation | Total (best case) | Total (worst case) |
|------|------------------------|----------------|-------------------|--------------------|
| 1K | $0.067 × 1-3 | $0.134 | $0.201 | $0.535 |
| 2K | $0.101 × 1-3 | $0.134 | $0.235 | $0.437 |
| 4K | $0.151 × 1-3 (Flash 4K pre-test) | $0.240 | $0.391 | $0.693 |

Surface the per-slide projection to the speaker before Step 9A executes — a deck with three 4K hero slides represents up to ~$2.08 of generation spend. Compare against `budget_tracker.remaining_usd` and surface a warning if projected spend exceeds remaining budget.
```

- [ ] **Step 3: Smoke test by reading the file back**

Run: `grep -A2 "Phase 2 — Pro escalation" plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md`

Expected: see "resolution-aware" and `--resolution {slide.resolution}` in the output.

- [ ] **Step 4: Commit**

```bash
git add plugins/jack-tar-deckhand/skills/imagegen-bridge/SKILL.md
git commit -m "feat(deckhand/imagegen-bridge): Step 9A Pro escalation honours slide.resolution; optional Flash 4K pre-test"
```

---

## Task B5: Strategy-map and narrative-architect SKILL.md — speaker can request 2K/4K

**Files:**
- Modify: `plugins/jack-tar-deckhand/skills/strategy-map/SKILL.md`
- Modify: `plugins/jack-tar-deckhand/skills/narrative-architect/SKILL.md`

- [ ] **Step 1: Add a "Resolution selection" section to strategy-map/SKILL.md**

Append before the Output section (or after the strategy classification description):

```markdown
## Resolution selection

By default every slide renders at `1K` — economical, sufficient for most slides on a projector. The speaker may opt specific slides into `2K` or `4K` via the `resolution` field in the StrategyMap entry.

**When to choose 4K:**
- Hero opener with detailed photographic imagery
- Closing slide that will be photographed by attendees and shared on social
- Slides where text rendering at small body sizes is critical (Nano Banana Pro 4K renders text noticeably better than Flash 1K)

**When to choose 2K:**
- Section dividers with mid-detail imagery
- Diagrams that may be projected on very large screens (>120")

**Cost implications (per slide, single Pro escalation):**
- `1K` (default): ~$0.13 (Nano Banana Pro)
- `2K`: ~$0.13 (Nano Banana Pro — same flat rate within tier)
- `4K`: ~$0.24 (Nano Banana Pro). Plus an optional Flash 4K pre-test at $0.151.

Mark a slide for 2K/4K by including `"resolution": "4K"` in its StrategyMap entry. Confirm the cost with the speaker before proceeding — a deck with three 4K hero slides is ~$2 of generation spend.
```

- [ ] **Step 2: Add a parallel paragraph to narrative-architect/SKILL.md**

In the section that produces the SlideOutline, append:

```markdown
## Optional: hero-slide resolution annotation

If the speaker is shooting for a memorable opener or closing slide, ask: "Would you like this slide rendered at 4K (Nano Banana Pro, ~$0.24) or 2K?" Annotate the slide with a `resolution` field in the SlideOutline if so — the strategy-map step will carry it through to the StrategyMap entry. Default `1K` unchanged.
```

- [ ] **Step 3: Smoke test**

Run: `grep -c "Resolution selection" plugins/jack-tar-deckhand/skills/strategy-map/SKILL.md`

Expected: `1`

- [ ] **Step 4: Commit**

```bash
git add plugins/jack-tar-deckhand/skills/strategy-map/SKILL.md plugins/jack-tar-deckhand/skills/narrative-architect/SKILL.md
git commit -m "docs(deckhand/skills): speakers can mark slides for 2K/4K rendering"
```

---

## Task B6: Cross-plugin integration — 4K request reaches Nano Banana Pro

**Files:**
- Create: `plugins/integration_tests/test_resolution_end_to_end.py`

- [ ] **Step 1: Write the test**

```python
# plugins/integration_tests/test_resolution_end_to_end.py
"""End-to-end: a slide with resolution='4K' routes through deckhand router
to Nano Banana Pro and reaches generate_cloud_image with resolution='4K'."""
import sys
from pathlib import Path
from unittest import mock

import pytest

DECKHAND = Path(__file__).resolve().parent.parent / 'jack-tar-deckhand'
CLOUD = Path(__file__).resolve().parent.parent / 'jack-tar-cloud'


@pytest.fixture
def deckhand_path():
    sys.path.insert(0, str(DECKHAND))
    yield
    sys.path.remove(str(DECKHAND))


def test_4k_hero_slide_routes_to_nano_banana_pro(deckhand_path):
    from src import image_router

    slide = {
        'slide_number': 1,
        'visual_type': 'hero_image',
        'resolution': '4K',
    }
    available = {
        'google': {'available': True},
        'fal': {'available': True},
        'openai': {'available': True},
    }
    decision = image_router.route_slide(
        slide, mode='production',
        available_providers=available,
        budget_state='allow',
    )
    assert decision.provider == 'google'
    assert decision.model == 'gemini-3-pro-image-preview'
    assert decision.resolution == '4K'


def test_4k_request_reaches_generate_cloud_image_with_resolution_4k(deckhand_path):
    """Through the render funnel, a cloud_4k stage call must arrive at
    generate_cloud_image with resolution='4K'."""
    from src import render_funnel

    fake = mock.Mock(return_value={'file_path': '/tmp/x.png', 'cost_usd': 0.24})
    with mock.patch('src.render_funnel._generate_cloud_raw', fake):
        # init a deck dir with the log
        import tempfile
        with tempfile.TemporaryDirectory() as deck_dir:
            render_funnel.init_render_log(deck_dir)
            render_funnel.execute_funnel_stage(
                deck_dir=deck_dir,
                slide_number=1,
                strategy='full_render',
                prompt='a lighthouse at sunset',
                funnel_stage='cloud_4k',
                model='gemini-3-pro-image-preview',
                output_path='/tmp/x.png',
                provider='google',
            )
    assert fake.call_args.kwargs['resolution'] == '4K'
    assert fake.call_args.kwargs['provider'] == 'google'
    assert fake.call_args.kwargs['model'] == 'gemini-3-pro-image-preview'
```

- [ ] **Step 2: Run the test**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/integration_tests/test_resolution_end_to_end.py -v`

Expected: 2 PASS.

- [ ] **Step 3: Commit**

```bash
git add plugins/integration_tests/test_resolution_end_to_end.py
git commit -m "test(integration): 4K request routes through deckhand to Nano Banana Pro"
```

---

## Task B7: CLAUDE.md — resolution selection guide section

**Files:**
- Modify: `CLAUDE.md` (root)

- [ ] **Step 1: Add a new section under "Production Rendering Engine Strategy"**

Find the "Production Rendering Engine Strategy (2026-03-31)" section. After the existing bullet list, append:

```markdown
- **Resolution selection guide (issue #60, 2026-05-06):**
  - Default `1K` covers the vast majority of slides — projector resolution maxes out around 1080p, so 1K is sufficient.
  - Choose `2K` when: large display (>120"), mid-detail diagrams, photographic backgrounds with subtle gradients.
  - Choose `4K` when: hero opener / closer that may be photographed and re-shared; text-heavy slides where Nano Banana Pro's better text rendering matters.
  - **Flash 4K vs Pro 4K decision rule:** for `4K` slides, the imagegen-bridge runs an optional Flash 4K pre-test at $0.151 before escalating to Pro 4K at $0.240. If Flash 4K passes review, stop — Flash text rendering at 4K is often comparable to Pro 1K. If Flash 4K refines, proceed to Pro 4K (single shot). This pattern was validated end-to-end during the #59 smoke test ($0.659 spend on a 5-stage ladder).
  - **Cost ladder per slide (worst case, 3 Flash refinements + Pro escalation):**
    - 1K: ~$0.535
    - 2K: ~$0.437 (Pro flat-rate within tier)
    - 4K: ~$0.693
  - A deck with three 4K hero slides represents up to ~$2.08 of image generation spend.
```

- [ ] **Step 2: Smoke test**

Run: `grep -c "Resolution selection guide" CLAUDE.md`

Expected: `1`

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude): resolution selection guide for 2K/4K tiers"
```

---

## Task B8: Bump deckhand plugin to 1.2.0 and sync marketplace

**Files:**
- Modify: `plugins/jack-tar-deckhand/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Bump plugin.json**

In `plugins/jack-tar-deckhand/.claude-plugin/plugin.json`, change `"version": "1.1.0"` → `"version": "1.2.0"`.

- [ ] **Step 2: Bump marketplace manifest**

In `.claude-plugin/marketplace.json`, find the `jack-tar-deckhand` entry and bump `"version": "1.1.0"` → `"version": "1.2.0"`.

- [ ] **Step 3: Run JSON validation**

Run: `python3 -c "import json; json.load(open('.claude-plugin/marketplace.json')); json.load(open('plugins/jack-tar-deckhand/.claude-plugin/plugin.json')); print('OK')"`

Expected: `OK`

- [ ] **Step 4: Run all deckhand plugin tests**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/jack-tar-deckhand/tests/ -v 2>&1 | tail -5`

Expected: existing baseline + new resolution tests, all PASS.

- [ ] **Step 5: Run cross-plugin integration suite**

Run: `/Users/stevejones/Documents/Development/jack-tar-deckhand/.venv/bin/pytest plugins/integration_tests/ -v 2>&1 | tail -5`

Expected: 33 baseline + 2 new (Task B6) + 3 new (Task A6 already merged), all PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/jack-tar-deckhand/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore(deckhand): bump 1.1.0 → 1.2.0 (resolution control through pipeline)"
```

---

## Task B9: Push and open PR B

- [ ] **Step 1: Push branch**

```bash
git push -u origin feat/issue-60-resolution-plumbing
```

- [ ] **Step 2: Open PR**

```bash
gh pr create --title "feat(jack-tar-deckhand): resolution control through render funnel + image router" --body "$(cat <<'EOF'
## Summary
- Render funnel: new `cloud_2k` and `cloud_4k` stages; `_generate_cloud()` threads `resolution=` to generate_cloud_image
- Image router: `RoutingTarget`/`UpgradeDecision` carry `resolution` field; `_check_resolution_compatibility` replaces dimension-warning helper; new routing rows for `production_2k`/`production_4k` modes
- Strategy-map schema: optional `resolution` per slide; `render_funnel` enum extended
- Imagegen-bridge Step 9A: Pro escalation honours slide.resolution; optional Flash 4K pre-test
- Strategy-map and narrative-architect SKILL.md: speaker UX for opting slides into 2K/4K
- CLAUDE.md: resolution selection guide
- Bumps jack-tar-deckhand 1.1.0 → 1.2.0

Closes #60. Builds on #59 (cloud-side resolution) and the cloud-skill drift fix PR.

## Test plan
- [x] Render funnel: 3 new tests for cloud_2k/cloud_4k stage progression
- [x] Image router: 6 new tests for resolution-aware routing
- [x] Strategy map schema: 5 new tests for resolution + extended enum
- [x] Cross-plugin integration: 2 new tests verifying 4K reaches Nano Banana Pro
- [x] Existing tests pass: cloud (50 + drift fixes), deckhand baseline, integration baseline
EOF
)"
```

- [ ] **Step 3: Wait for CI green; merge with `gh pr merge <N> --merge`**

- [ ] **Step 4: Update memory entries**

After merge, update memory:
- `project_implementation_progress.md` — note EPIC #58 at 3/4 children closed, only #61 (Recraft) remaining.
- Note that deckhand v1.2.0 is now on main; bridge branch reconciliation pending.

---

## Self-review checklist (run after writing the plan)

**Spec coverage:**
- [x] §1 Render funnel `cloud_2k`/`cloud_4k` stages — Task B1
- [x] §2 Image router `resolution` field + `_check_resolution_compatibility` — Task B2
- [x] §3 Cross-tier refinement Pro escalation — Task B4
- [x] §4 Cloud-skill SKILL.md drift fixes (4 files) — Tasks A2-A5
- [x] §5 Imagegen-bridge resolution acceptance — Task B4
- [x] §6 Strategy map schema + skill prompt updates — Tasks B3, B5
- [x] §7 Tests — Tasks A1, A6, B1, B2, B3, B6 (≈19 tests; below the 25-35 target — may add a budget-projection test in B4)
- [x] §8 Version bumps — Tasks A7, B8
- [x] §9 Documentation — Task B7

**Placeholder scan:** None remaining. Every step has explicit code or commands.

**Type consistency:**
- `resolution` is a string ('1K'/'2K'/'4K'/'512') everywhere
- `RoutingTarget.resolution` and `UpgradeDecision.target_resolution` use defaults to preserve backwards compat
- `_CLOUD_STAGE_RESOLUTION` matches the `_VALID_RESOLUTIONS` from the cloud plugin
