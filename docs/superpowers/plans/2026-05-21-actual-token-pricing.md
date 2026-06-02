# Actual-Token Pricing Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate whether catalog-flat-rate cost estimates over-state actual provider billing for Google Nano Banana, Google Imagen Developer API, and OpenAI GPT Image; if so, refactor `BudgetTracker` to record both estimated and actual costs from API-returned usage metadata.

**Architecture:** Three phases gated on evidence. Phase 0 = SDK discovery (read provider source, document field paths). Phase 1 = calibration script + real API calls up to $5 cap, emit delta report. Phase 2 (conditional on Phase 1 GO) = production refactor: `GenerationResult` dataclass returned from `generate_cloud_image()`, `BudgetTracker.log_api_call()` extended to carry both `cost_estimated` and `cost_actual`, pre-flight cap unchanged (uses estimate), cumulative ledger shows actual where available.

**Tech Stack:** Python 3, pytest, `google-genai` SDK, `openai` SDK, existing `src/` modules (`budget_tracker.py`, `generate_cloud_image.py`, `provider_discovery.py`), plugin copy at `plugins/jack-tar-cloud/src/generate_cloud_image.py`.

**Spec:** `docs/superpowers/specs/2026-05-21-actual-token-pricing-validation-design.md`

**Worktree note:** This plan executes in `.claude/worktrees/spike-actual-token-pricing/`. The Python virtual env lives in the parent repo at `../../../.venv/`. Task 1 symlinks it so the conventional `.venv/bin/pytest` invocation works from the worktree root.

**Discipline reminder:** This spike generates PNG images as calibration artefacts. The spike does NOT need to review image quality — the goal is cost data. Do **NOT** `Read` generated PNGs. If for any reason an image needs visual inspection, dispatch the `jack-tar-deckhand:image-reviewer` or `general-purpose` subagent per CLAUDE.md image-review discipline.

---

## File Structure

**Created during the spike:**

```
docs/spikes/2026-05-21-actual-token-pricing/
├── README.md                          # final summary + GO/NO-GO verdict
├── phase-0-discovery.md               # confirmed SDK usage field paths
├── token-pricing-rates.md             # per-provider token rates with sources
├── report.md                          # Phase 1 delta tables
├── calibration-results.json           # generated; structured per-call data
├── prompts/
│   ├── short_a.txt                    # ~50w hero closer
│   ├── short_b.txt                    # ~50w icon-style
│   ├── medium_a.txt                   # ~200w backdrop with composition directives
│   ├── medium_b.txt                   # ~200w photoreal portrait + palette
│   ├── long_a.txt                     # ~500w full pragmatic-composition brief
│   └── long_b.txt                     # ~500w paperbanana-style academic figure
└── raw-responses/<provider>/<model>/<cell>.json   # generated; image bytes stripped
```

**Source modules (Phase 2 refactor — gated):**

```
src/
├── actual_cost_calculator.py          # NEW: pure functions; token usage → USD
├── cloud_results.py                   # NEW: GenerationResult dataclass
├── budget_tracker.py                  # MODIFIED: log_api_call signature, cost_summary_markdown
├── generate_cloud_image.py            # MODIFIED: return GenerationResult
plugins/jack-tar-cloud/src/
└── generate_cloud_image.py            # MODIFIED: kept in sync with src/

tools/
└── spike_pricing_calibration.py       # NEW: runnable script (worktree only)

tests/
├── test_actual_cost_calculator.py     # NEW: uses Phase 1 fixtures
├── test_cloud_results.py              # NEW: GenerationResult contract
├── test_budget_tracker.py             # MODIFIED: extend for cost_actual column
└── test_pricing_freshness.py          # NEW: 90-day staleness advisory
```

**File responsibilities:**

- `actual_cost_calculator.py` — three pure functions (no I/O, no SDK imports): `compute_nano_banana_actual_cost`, `compute_imagen_actual_cost`, `compute_openai_image_actual_cost`. Each takes a `(model, usage)` pair and returns USD. Token rate tables live as module constants with source URL + `date_captured` comment per rate.
- `cloud_results.py` — `GenerationResult` dataclass implementing `__fspath__` and `__str__` so legacy callers that read it as a path keep working.
- `budget_tracker.py` — extended ledger schema. Pre-flight cap check (`would_exceed_cap`) unchanged; uses estimate. `_spent` accumulates `cost_actual` when present, `cost_estimated` otherwise.
- `tools/spike_pricing_calibration.py` — idempotent runnable script: reads existing `calibration-results.json`, runs only missing cells, halts before exceeding `--max-spend-usd`. Skips providers with no API key configured.

---

## Phase 0 — SDK Discovery

### Task 1: Bootstrap spike directory and venv symlink

**Files:**
- Create: `docs/spikes/2026-05-21-actual-token-pricing/README.md` (skeleton)
- Create: `docs/spikes/2026-05-21-actual-token-pricing/prompts/` (directory)
- Create: `docs/spikes/2026-05-21-actual-token-pricing/raw-responses/` (directory)
- Symlink: `.venv -> ../../../.venv`

- [ ] **Step 1: Create directory tree and venv symlink**

```bash
mkdir -p docs/spikes/2026-05-21-actual-token-pricing/prompts
mkdir -p docs/spikes/2026-05-21-actual-token-pricing/raw-responses
ln -s ../../../.venv .venv
```

- [ ] **Step 2: Verify the venv is reachable**

Run: `.venv/bin/pytest --version`
Expected: a version string like `pytest 8.x.y`.

- [ ] **Step 3: Write the spike README skeleton**

```bash
cat > docs/spikes/2026-05-21-actual-token-pricing/README.md <<'EOF'
# Spike: Actual-Token Pricing Validation

**Date:** 2026-05-21
**Spec:** `docs/superpowers/specs/2026-05-21-actual-token-pricing-validation-design.md`
**Plan:** `docs/superpowers/plans/2026-05-21-actual-token-pricing.md`
**Status:** in progress

## Verdict (filled at end of Phase 1)

TBD

## Findings

TBD
EOF
```

- [ ] **Step 4: Commit**

```bash
git add docs/spikes/2026-05-21-actual-token-pricing/ .venv
git commit -m "spike(token-pricing): scaffold spike directory + venv symlink"
```

### Task 2: Discover and document SDK usage field paths

**Files:**
- Create: `docs/spikes/2026-05-21-actual-token-pricing/phase-0-discovery.md`

- [ ] **Step 1: Read the google-genai SDK to confirm `generate_content` exposes `usage_metadata`**

```bash
.venv/bin/python -c "
import google.genai
print('google-genai version:', google.genai.__version__)
from google.genai import types
import inspect
# Inspect GenerateContentResponse fields
src = inspect.getsourcefile(types)
print('types module:', src)
"
```

Then grep the SDK for `usage_metadata`:

```bash
.venv/bin/python -c "import google.genai; import os; print(os.path.dirname(google.genai.__file__))" | xargs -I {} grep -rn "usage_metadata\|UsageMetadata" {} | head -20
```

Capture the exact attribute path (e.g. `response.usage_metadata.prompt_token_count`) and the list of fields inside `UsageMetadata`.

- [ ] **Step 2: Confirm `generate_images` (Imagen) response shape**

```bash
.venv/bin/python -c "import google.genai; import os; print(os.path.dirname(google.genai.__file__))" | xargs -I {} grep -rn "class GenerateImagesResponse\|generate_images" {} | head -10
```

Read the matching source file and document whether `GenerateImagesResponse` exposes a usage field. If it does, capture the path. If it does not, write that explicitly — Imagen will be excluded from Phase 2 refactor.

- [ ] **Step 3: Confirm OpenAI `images.generate` usage field for `gpt-image-1`**

```bash
.venv/bin/python -c "import openai; print('openai version:', openai.__version__); import inspect; from openai.types.images_response import ImagesResponse; print(ImagesResponse.model_fields.keys())"
```

If `usage` appears in `ImagesResponse.model_fields`, drill into its type and capture the inner fields. If it does not, document that gpt-image-1 likely does not return usage on the `images.generate` path and that this spike's OpenAI cell becomes catalog-only.

- [ ] **Step 4: Write `phase-0-discovery.md`**

Document for each of the three providers:

```markdown
## <provider> — <model>

- **SDK call:** `client.<...>(...)` (exact invocation)
- **Response object type:** `<TypeName>`
- **Usage field path:** `response.<attr>.<attr>` OR `none — defer from refactor`
- **Fields inside usage object:** `<field>: <type>`, ...
- **SDK version tested:** `<version>`
- **Date captured:** 2026-05-21
- **Notes:** any quirks discovered
```

- [ ] **Step 5: Commit**

```bash
git add docs/spikes/2026-05-21-actual-token-pricing/phase-0-discovery.md
git commit -m "spike(token-pricing): phase 0 — sdk usage field discovery"
```

---

## Phase 1 — Calibration

### Task 3: Author six calibration prompt files

**Files:**
- Create: `docs/spikes/2026-05-21-actual-token-pricing/prompts/short_a.txt`
- Create: `docs/spikes/2026-05-21-actual-token-pricing/prompts/short_b.txt`
- Create: `docs/spikes/2026-05-21-actual-token-pricing/prompts/medium_a.txt`
- Create: `docs/spikes/2026-05-21-actual-token-pricing/prompts/medium_b.txt`
- Create: `docs/spikes/2026-05-21-actual-token-pricing/prompts/long_a.txt`
- Create: `docs/spikes/2026-05-21-actual-token-pricing/prompts/long_b.txt`

- [ ] **Step 1: Source representative prompts from real dogfood logs**

Re-read the following for actual production prompt text to lift:

- `docs/superpowers/dogfooding/2026-05-07-blog-post-asset-run.md`
- `docs/superpowers/dogfooding/2026-05-18-paperbanana-integration.md`

Lift two short (~50w), two medium (~200w), and two long (~500w) prompts. Aim for variety in subject matter — at least one each: scene, portrait, schematic, icon, academic figure.

- [ ] **Step 2: Write the six prompt files**

Each file contains the raw prompt text only (no front matter). Word counts roughly:

- `short_a.txt`: ~50 words — scene-led hero closer
- `short_b.txt`: ~50 words — icon request
- `medium_a.txt`: ~200 words — composed backdrop
- `medium_b.txt`: ~200 words — portrait with palette constraints
- `long_a.txt`: ~500 words — full pragmatic-composition brief with positional callouts
- `long_b.txt`: ~500 words — paperbanana-style academic figure brief

- [ ] **Step 3: Verify word counts**

```bash
for f in docs/spikes/2026-05-21-actual-token-pricing/prompts/*.txt; do
  echo -n "$f: "; wc -w < "$f"
done
```

Expected output: short_*.txt ≈ 40-60w, medium_*.txt ≈ 180-220w, long_*.txt ≈ 450-550w.

- [ ] **Step 4: Commit**

```bash
git add docs/spikes/2026-05-21-actual-token-pricing/prompts/
git commit -m "spike(token-pricing): calibration prompt files"
```

### Task 4: Document token-pricing rates with sources

**Files:**
- Create: `docs/spikes/2026-05-21-actual-token-pricing/token-pricing-rates.md`

- [ ] **Step 1: Capture token rates from official provider docs**

Open the following URLs and extract the per-token (or per-MTok) rates for the three in-scope providers:

- Google Gemini pricing: <https://ai.google.dev/gemini-api/docs/pricing>
- Google Imagen pricing: <https://cloud.google.com/vertex-ai/generative-ai/pricing#imagen-models>
- OpenAI pricing: <https://openai.com/api/pricing/>

- [ ] **Step 2: Write `token-pricing-rates.md`**

Format (one section per provider):

```markdown
## Google Gemini Nano Banana

- **Model:** `gemini-3.1-flash-image-preview` (Flash) / `gemini-3-pro-image-preview` (Pro)
- **Text input rate:** $X.YY per 1M tokens
- **Image output rate:** $X.YY per 1M tokens
- **Source:** https://ai.google.dev/gemini-api/docs/pricing
- **Date captured:** 2026-05-21
- **Notes:** ...
```

Repeat for Imagen Developer API and OpenAI GPT Image.

- [ ] **Step 3: Commit**

```bash
git add docs/spikes/2026-05-21-actual-token-pricing/token-pricing-rates.md
git commit -m "spike(token-pricing): token-pricing rates per provider"
```

### Task 5: TDD `compute_nano_banana_actual_cost`

**Files:**
- Create: `src/actual_cost_calculator.py`
- Create: `tests/test_actual_cost_calculator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_actual_cost_calculator.py
import pytest
from src.actual_cost_calculator import compute_nano_banana_actual_cost


def test_nano_banana_flash_minimal_prompt():
    """A short prompt billed at Flash rates returns expected cost."""
    usage = {
        "prompt_token_count": 100,
        "candidates_token_count": 1290,  # one 1K image at Flash rate
        "total_token_count": 1390,
    }
    cost = compute_nano_banana_actual_cost("gemini-3.1-flash-image-preview", usage)
    # Flash text input $0.30/MTok, image output $30/MTok (placeholder rates,
    # update from token-pricing-rates.md). With placeholder rates:
    # 100 / 1e6 * 0.30 + 1290 / 1e6 * 30 = 0.00003 + 0.0387 = 0.03873
    assert cost == pytest.approx(0.03873, rel=1e-3)


def test_nano_banana_pro_higher_image_token_rate():
    """Pro charges more per image-output token than Flash."""
    usage = {
        "prompt_token_count": 100,
        "candidates_token_count": 1290,
        "total_token_count": 1390,
    }
    pro_cost = compute_nano_banana_actual_cost("gemini-3-pro-image-preview", usage)
    flash_cost = compute_nano_banana_actual_cost("gemini-3.1-flash-image-preview", usage)
    assert pro_cost > flash_cost


def test_nano_banana_unknown_model_raises():
    usage = {"prompt_token_count": 100, "candidates_token_count": 1290, "total_token_count": 1390}
    with pytest.raises(ValueError, match="Unknown Nano Banana model"):
        compute_nano_banana_actual_cost("gemini-99-fictional", usage)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_actual_cost_calculator.py::test_nano_banana_flash_minimal_prompt -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.actual_cost_calculator'`.

- [ ] **Step 3: Write minimal implementation**

```python
# src/actual_cost_calculator.py
"""Compute actual USD cost from API-returned usage metadata.

Pure functions; no I/O, no SDK imports. Token rates are sourced from the
official provider pricing pages — see token-pricing-rates.md in the spike
directory for current values and source URLs.
"""

# Replace placeholder values below with rates from token-pricing-rates.md.
# Each rate carries a source URL and date_captured.

# Source: https://ai.google.dev/gemini-api/docs/pricing  (captured 2026-05-21)
_NANO_BANANA_RATES = {
    "gemini-3.1-flash-image-preview": {
        "text_input_per_mtok": 0.30,      # TODO from token-pricing-rates.md
        "image_output_per_mtok": 30.00,   # TODO from token-pricing-rates.md
    },
    "gemini-3-pro-image-preview": {
        "text_input_per_mtok": 0.50,      # TODO from token-pricing-rates.md
        "image_output_per_mtok": 60.00,   # TODO from token-pricing-rates.md
    },
}


def compute_nano_banana_actual_cost(model: str, usage: dict) -> float:
    """Compute actual cost for a Nano Banana image generation call.

    Args:
        model: Gemini image model name.
        usage: Verbatim usage_metadata dict from the API response with keys
            'prompt_token_count', 'candidates_token_count', 'total_token_count'.

    Returns:
        Cost in USD.

    Raises:
        ValueError: If the model has no rate entry.
    """
    if model not in _NANO_BANANA_RATES:
        raise ValueError(f"Unknown Nano Banana model: {model}")
    rates = _NANO_BANANA_RATES[model]
    text_cost = usage["prompt_token_count"] / 1_000_000 * rates["text_input_per_mtok"]
    image_cost = usage["candidates_token_count"] / 1_000_000 * rates["image_output_per_mtok"]
    return text_cost + image_cost
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_actual_cost_calculator.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Replace placeholder rates with values from `token-pricing-rates.md`**

Open `docs/spikes/2026-05-21-actual-token-pricing/token-pricing-rates.md` and copy the actual rates into `_NANO_BANANA_RATES`. If the test math no longer matches, update the test's expected value to match the documented rates (the test exists to lock the formula, not the rates themselves).

- [ ] **Step 6: Re-run tests; commit**

```bash
.venv/bin/pytest tests/test_actual_cost_calculator.py -v
git add src/actual_cost_calculator.py tests/test_actual_cost_calculator.py
git commit -m "feat(actual-cost): compute_nano_banana_actual_cost"
```

### Task 6: TDD `compute_imagen_actual_cost`

**Files:**
- Modify: `src/actual_cost_calculator.py`
- Modify: `tests/test_actual_cost_calculator.py`

- [ ] **Step 1: Write the failing tests**

If Phase 0 discovery confirmed Imagen exposes usage metadata, write:

```python
def test_imagen_standard_2k_token_based():
    """Imagen on Developer API bills per-image tokens; 2K is the dearer cell."""
    from src.actual_cost_calculator import compute_imagen_actual_cost
    usage = {"prompt_token_count": 50, "candidates_token_count": 1680, "total_token_count": 1730}
    cost = compute_imagen_actual_cost("imagen-4.0-generate-001", usage)
    # Use rate from token-pricing-rates.md; placeholder formula:
    # 50 * text_rate + 1680 * image_rate
    assert cost > 0
    assert cost < 0.50  # sanity upper bound

def test_imagen_unknown_model_raises():
    from src.actual_cost_calculator import compute_imagen_actual_cost
    with pytest.raises(ValueError, match="Unknown Imagen model"):
        compute_imagen_actual_cost("imagen-99-fictional", {"prompt_token_count": 0, "candidates_token_count": 0, "total_token_count": 0})
```

If Phase 0 confirmed Imagen does **not** expose usage, skip this task and write a one-line note in `phase-0-discovery.md` that the Imagen branch is catalog-only. Then jump to Task 7.

- [ ] **Step 2: Run tests; expect FAIL**

Run: `.venv/bin/pytest tests/test_actual_cost_calculator.py::test_imagen_standard_2k_token_based -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement**

```python
# Append to src/actual_cost_calculator.py

# Source: https://cloud.google.com/vertex-ai/generative-ai/pricing  (captured 2026-05-21)
_IMAGEN_RATES = {
    "imagen-4.0-fast-generate-001": {
        "text_input_per_mtok": 0.30,      # update from token-pricing-rates.md
        "image_output_per_mtok": 30.00,   # update from token-pricing-rates.md
    },
    "imagen-4.0-generate-001": {
        "text_input_per_mtok": 0.30,
        "image_output_per_mtok": 30.00,
    },
    "imagen-4.0-ultra-generate-001": {
        "text_input_per_mtok": 0.30,
        "image_output_per_mtok": 60.00,
    },
}


def compute_imagen_actual_cost(model: str, usage: dict) -> float:
    """Compute actual cost for an Imagen image generation call (Developer API).

    Raises:
        ValueError: If model has no rate entry.
    """
    if model not in _IMAGEN_RATES:
        raise ValueError(f"Unknown Imagen model: {model}")
    rates = _IMAGEN_RATES[model]
    text_cost = usage["prompt_token_count"] / 1_000_000 * rates["text_input_per_mtok"]
    image_cost = usage["candidates_token_count"] / 1_000_000 * rates["image_output_per_mtok"]
    return text_cost + image_cost
```

- [ ] **Step 4: Run tests; commit**

```bash
.venv/bin/pytest tests/test_actual_cost_calculator.py -v
git add src/actual_cost_calculator.py tests/test_actual_cost_calculator.py
git commit -m "feat(actual-cost): compute_imagen_actual_cost"
```

### Task 7: TDD `compute_openai_image_actual_cost`

**Files:**
- Modify: `src/actual_cost_calculator.py`
- Modify: `tests/test_actual_cost_calculator.py`

- [ ] **Step 1: Write the failing tests**

If Phase 0 confirmed OpenAI exposes `usage`:

```python
def test_openai_gpt_image_token_based():
    from src.actual_cost_calculator import compute_openai_image_actual_cost
    usage = {"input_tokens": 100, "output_tokens": 4160, "total_tokens": 4260}
    cost = compute_openai_image_actual_cost("gpt-image-1", usage)
    assert cost > 0

def test_openai_image_unknown_model_raises():
    from src.actual_cost_calculator import compute_openai_image_actual_cost
    with pytest.raises(ValueError, match="Unknown OpenAI image model"):
        compute_openai_image_actual_cost("gpt-image-99", {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0})
```

If Phase 0 confirmed OpenAI does not expose `usage` on `images.generate`, skip this task and document OpenAI as catalog-only.

- [ ] **Step 2: Run; expect FAIL**

Run: `.venv/bin/pytest tests/test_actual_cost_calculator.py::test_openai_gpt_image_token_based -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

```python
# Append to src/actual_cost_calculator.py

# Source: https://openai.com/api/pricing/  (captured 2026-05-21)
_OPENAI_IMAGE_RATES = {
    "gpt-image-1": {
        "input_per_mtok": 5.00,       # update from token-pricing-rates.md
        "output_per_mtok": 40.00,     # update from token-pricing-rates.md
    },
    "gpt-image-1.5": {
        "input_per_mtok": 5.00,       # update from token-pricing-rates.md
        "output_per_mtok": 40.00,     # update from token-pricing-rates.md
    },
}


def compute_openai_image_actual_cost(model: str, usage: dict) -> float:
    """Compute actual cost for an OpenAI image generation call."""
    if model not in _OPENAI_IMAGE_RATES:
        raise ValueError(f"Unknown OpenAI image model: {model}")
    rates = _OPENAI_IMAGE_RATES[model]
    input_cost = usage["input_tokens"] / 1_000_000 * rates["input_per_mtok"]
    output_cost = usage["output_tokens"] / 1_000_000 * rates["output_per_mtok"]
    return input_cost + output_cost
```

- [ ] **Step 4: Run; commit**

```bash
.venv/bin/pytest tests/test_actual_cost_calculator.py -v
git add src/actual_cost_calculator.py tests/test_actual_cost_calculator.py
git commit -m "feat(actual-cost): compute_openai_image_actual_cost"
```

### Task 8: TDD 90-day rate-freshness advisory test

**Files:**
- Create: `tests/test_pricing_freshness.py`

- [ ] **Step 1: Write the test**

```python
# tests/test_pricing_freshness.py
"""Advisory test: warn (don't fail) when token pricing rates are >90 days old."""
import datetime
import re
import warnings
from pathlib import Path


_RATE_FILE = Path("src/actual_cost_calculator.py")
_DATE_RE = re.compile(r"captured (\d{4}-\d{2}-\d{2})")
_STALENESS_DAYS = 90


def test_token_rates_not_stale():
    """Each 'captured YYYY-MM-DD' marker in the rate file is within 90 days.

    This test never FAILS — it emits warnings via pytest.warns when stale.
    Run with `-W error` to escalate locally.
    """
    text = _RATE_FILE.read_text()
    today = datetime.date.today()
    stale = []
    for match in _DATE_RE.finditer(text):
        captured = datetime.date.fromisoformat(match.group(1))
        if (today - captured).days > _STALENESS_DAYS:
            stale.append(match.group(1))
    if stale:
        warnings.warn(
            f"Token rates older than {_STALENESS_DAYS} days: {stale}. "
            f"Refresh from provider docs.",
            UserWarning,
            stacklevel=2,
        )
```

- [ ] **Step 2: Run; verify it passes (rates were just captured)**

Run: `.venv/bin/pytest tests/test_pricing_freshness.py -v`
Expected: PASS (no warning fires when rates are fresh).

- [ ] **Step 3: Commit**

```bash
git add tests/test_pricing_freshness.py
git commit -m "test(actual-cost): 90-day token rate staleness advisory"
```

### Task 9: TDD calibration script — prompt loader

**Files:**
- Create: `tools/spike_pricing_calibration.py`
- Create: `tests/test_spike_pricing_calibration.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_spike_pricing_calibration.py
from pathlib import Path
from tools.spike_pricing_calibration import load_prompts, PromptSet


def test_load_prompts_returns_six_buckets(tmp_path):
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    for name in ("short_a", "short_b", "medium_a", "medium_b", "long_a", "long_b"):
        (prompts_dir / f"{name}.txt").write_text(f"prompt body {name}")
    result = load_prompts(prompts_dir)
    assert isinstance(result, PromptSet)
    assert result.short_a == "prompt body short_a"
    assert result.medium_a == "prompt body medium_a"
    assert result.long_a == "prompt body long_a"


def test_load_prompts_missing_file_raises(tmp_path):
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "short_a.txt").write_text("only one")
    import pytest
    with pytest.raises(FileNotFoundError):
        load_prompts(prompts_dir)
```

- [ ] **Step 2: Run; verify FAIL**

Run: `.venv/bin/pytest tests/test_spike_pricing_calibration.py::test_load_prompts_returns_six_buckets -v`
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement minimum**

```python
# tools/spike_pricing_calibration.py
"""Spike: actual-token pricing calibration.

Runs a calibration matrix of real API calls against in-scope providers,
captures usage metadata, computes actual cost via src.actual_cost_calculator,
and emits a delta report. Idempotent: skips cells already in results.json.

Usage:
    .venv/bin/python tools/spike_pricing_calibration.py \
        --max-spend-usd 5.0 \
        --results docs/spikes/2026-05-21-actual-token-pricing/calibration-results.json \
        --prompts docs/spikes/2026-05-21-actual-token-pricing/prompts \
        --dry-run    # print matrix without calling APIs
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PromptSet:
    short_a: str
    short_b: str
    medium_a: str
    medium_b: str
    long_a: str
    long_b: str


def load_prompts(prompts_dir: Path) -> PromptSet:
    """Load the six calibration prompts from a directory.

    Raises:
        FileNotFoundError: if any required prompt file is missing.
    """
    required = ("short_a", "short_b", "medium_a", "medium_b", "long_a", "long_b")
    bodies = {}
    for name in required:
        path = prompts_dir / f"{name}.txt"
        if not path.is_file():
            raise FileNotFoundError(f"Missing prompt file: {path}")
        bodies[name] = path.read_text().strip()
    return PromptSet(**bodies)
```

- [ ] **Step 4: Run; verify PASS**

Run: `.venv/bin/pytest tests/test_spike_pricing_calibration.py -v`
Expected: 2 PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/spike_pricing_calibration.py tests/test_spike_pricing_calibration.py
git commit -m "feat(spike): calibration script — prompt loader"
```

### Task 10: TDD calibration script — idempotency and spend cap

**Files:**
- Modify: `tools/spike_pricing_calibration.py`
- Modify: `tests/test_spike_pricing_calibration.py`

- [ ] **Step 1: Write failing tests**

```python
# Append to tests/test_spike_pricing_calibration.py
import json
import pytest
from tools.spike_pricing_calibration import (
    load_results, missing_cells, SpendCapExceeded, MatrixCell, ALL_CELLS
)


def test_missing_cells_returns_all_when_no_prior_results(tmp_path):
    results_path = tmp_path / "results.json"
    cells = missing_cells(results_path)
    assert set(cells) == set(ALL_CELLS)


def test_missing_cells_skips_completed(tmp_path):
    results_path = tmp_path / "results.json"
    completed = ALL_CELLS[0]
    results_path.write_text(json.dumps([{
        "provider": completed.provider,
        "model": completed.model,
        "resolution": completed.resolution,
        "prompt_key": completed.prompt_key,
        "catalog_estimate_usd": 0.067,
        "computed_actual_usd": 0.040,
        "raw_usage": {},
        "timestamp": "2026-05-21T10:00:00Z",
    }]))
    cells = missing_cells(results_path)
    assert completed not in cells


def test_load_results_returns_empty_when_file_absent(tmp_path):
    assert load_results(tmp_path / "noexist.json") == []


def test_spend_cap_exceeded_raises():
    with pytest.raises(SpendCapExceeded):
        # 25 cells × estimated ~$0.10 average = $2.50 — well under cap.
        # But if next call would push past cap, raise.
        from tools.spike_pricing_calibration import check_spend_cap
        check_spend_cap(spent=4.95, next_estimate=0.10, cap=5.0)


def test_spend_cap_allows_under_cap():
    from tools.spike_pricing_calibration import check_spend_cap
    check_spend_cap(spent=4.85, next_estimate=0.10, cap=5.0)  # should not raise
```

- [ ] **Step 2: Run; verify FAIL**

Run: `.venv/bin/pytest tests/test_spike_pricing_calibration.py -v`
Expected: ImportError or AttributeError for the new functions.

- [ ] **Step 3: Implement**

```python
# Append to tools/spike_pricing_calibration.py

import json
from datetime import datetime, timezone


@dataclass(frozen=True)
class MatrixCell:
    provider: str       # 'google_nano_banana', 'google_imagen', 'openai'
    model: str
    resolution: str
    prompt_key: str     # 'short_a' | 'medium_a' | 'long_a' (use _b on re-runs)


ALL_CELLS: tuple[MatrixCell, ...] = (
    # Nano Banana Flash 1K
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "1K", "short_a"),
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "1K", "medium_a"),
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "1K", "long_a"),
    # Nano Banana Flash 2K
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "2K", "short_a"),
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "2K", "medium_a"),
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "2K", "long_a"),
    # Nano Banana Flash 4K
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "4K", "short_a"),
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "4K", "medium_a"),
    MatrixCell("google_nano_banana", "gemini-3.1-flash-image-preview", "4K", "long_a"),
    # Nano Banana Pro 1K
    MatrixCell("google_nano_banana", "gemini-3-pro-image-preview", "1K", "short_a"),
    MatrixCell("google_nano_banana", "gemini-3-pro-image-preview", "1K", "medium_a"),
    MatrixCell("google_nano_banana", "gemini-3-pro-image-preview", "1K", "long_a"),
    # Nano Banana Pro 4K (long only)
    MatrixCell("google_nano_banana", "gemini-3-pro-image-preview", "4K", "long_a"),
    # Imagen Fast 1K
    MatrixCell("google_imagen", "imagen-4.0-fast-generate-001", "1K", "short_a"),
    MatrixCell("google_imagen", "imagen-4.0-fast-generate-001", "1K", "medium_a"),
    MatrixCell("google_imagen", "imagen-4.0-fast-generate-001", "1K", "long_a"),
    # Imagen Standard 1K
    MatrixCell("google_imagen", "imagen-4.0-generate-001", "1K", "short_a"),
    MatrixCell("google_imagen", "imagen-4.0-generate-001", "1K", "medium_a"),
    MatrixCell("google_imagen", "imagen-4.0-generate-001", "1K", "long_a"),
    # Imagen Standard 2K
    MatrixCell("google_imagen", "imagen-4.0-generate-001", "2K", "short_a"),
    MatrixCell("google_imagen", "imagen-4.0-generate-001", "2K", "medium_a"),
    MatrixCell("google_imagen", "imagen-4.0-generate-001", "2K", "long_a"),
    # OpenAI GPT Image medium
    MatrixCell("openai", "gpt-image-1", "1K", "short_a"),
    MatrixCell("openai", "gpt-image-1", "1K", "medium_a"),
    MatrixCell("openai", "gpt-image-1", "1K", "long_a"),
)


class SpendCapExceeded(Exception):
    """Raised when the next API call would push cumulative spend past the cap."""


def check_spend_cap(*, spent: float, next_estimate: float, cap: float) -> None:
    if spent + next_estimate > cap:
        raise SpendCapExceeded(
            f"Spend ${spent:.3f} + next ${next_estimate:.3f} > cap ${cap:.3f}"
        )


def load_results(results_path: Path) -> list[dict]:
    if not results_path.is_file():
        return []
    return json.loads(results_path.read_text())


def missing_cells(results_path: Path) -> list[MatrixCell]:
    done = load_results(results_path)
    done_keys = {(r["provider"], r["model"], r["resolution"], r["prompt_key"]) for r in done}
    return [c for c in ALL_CELLS if (c.provider, c.model, c.resolution, c.prompt_key) not in done_keys]
```

- [ ] **Step 4: Run; verify PASS**

Run: `.venv/bin/pytest tests/test_spike_pricing_calibration.py -v`
Expected: 7 PASS (3 prior + 4 new).

- [ ] **Step 5: Commit**

```bash
git add tools/spike_pricing_calibration.py tests/test_spike_pricing_calibration.py
git commit -m "feat(spike): calibration matrix, idempotency, spend cap"
```

### Task 11: TDD calibration script — provider-skip on missing key

**Files:**
- Modify: `tools/spike_pricing_calibration.py`
- Modify: `tests/test_spike_pricing_calibration.py`

- [ ] **Step 1: Write failing tests**

```python
def test_skip_provider_missing_key(monkeypatch):
    from tools.spike_pricing_calibration import providers_with_keys
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert providers_with_keys() == set()


def test_provider_keys_detected(monkeypatch):
    from tools.spike_pricing_calibration import providers_with_keys
    monkeypatch.setenv("GOOGLE_API_KEY", "fake")
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    detected = providers_with_keys()
    assert "google_nano_banana" in detected
    assert "google_imagen" in detected
    assert "openai" in detected
```

- [ ] **Step 2: Run; FAIL**

Run: `.venv/bin/pytest tests/test_spike_pricing_calibration.py -v`
Expected: ImportError for `providers_with_keys`.

- [ ] **Step 3: Implement**

```python
# Append to tools/spike_pricing_calibration.py
import os


def providers_with_keys() -> set[str]:
    """Return the set of providers reachable in the current environment.

    'google_nano_banana' and 'google_imagen' both require a Google credential —
    either GOOGLE_API_KEY (Developer API) or GOOGLE_CLOUD_PROJECT (Vertex).
    'openai' requires OPENAI_API_KEY.
    """
    detected = set()
    if os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_CLOUD_PROJECT"):
        detected.add("google_nano_banana")
        detected.add("google_imagen")
    if os.environ.get("OPENAI_API_KEY"):
        detected.add("openai")
    return detected
```

- [ ] **Step 4: Run; verify PASS**

Run: `.venv/bin/pytest tests/test_spike_pricing_calibration.py -v`
Expected: 9 PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/spike_pricing_calibration.py tests/test_spike_pricing_calibration.py
git commit -m "feat(spike): skip providers with no API key"
```

### Task 12: Wire calibration script main entry — real API dispatch

**Files:**
- Modify: `tools/spike_pricing_calibration.py`

This task is **not TDD** — it integrates the real SDK calls. Unit testing live SDKs is out of scope. The dry-run mode (Task 13) provides a no-spend sanity check.

- [ ] **Step 1: Add the dispatch glue**

Append to `tools/spike_pricing_calibration.py`:

```python
import argparse
import sys
from typing import Optional

from src.provider_discovery import (
    estimate_google_cost,
    estimate_openai_cost,
)
from src.actual_cost_calculator import (
    compute_nano_banana_actual_cost,
    compute_imagen_actual_cost,
    compute_openai_image_actual_cost,
)


def _call_nano_banana(model: str, resolution: str, prompt: str) -> tuple[dict, bytes]:
    """Call Nano Banana via google-genai, return (usage_metadata_dict, image_bytes)."""
    from google import genai
    from google.genai import types
    client = genai.Client()
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(image_size=resolution),
    )
    response = client.models.generate_content(model=model, contents=[prompt], config=config)
    usage = {
        "prompt_token_count": response.usage_metadata.prompt_token_count,
        "candidates_token_count": response.usage_metadata.candidates_token_count,
        "total_token_count": response.usage_metadata.total_token_count,
    }
    # Image bytes intentionally captured but not retained — we strip them before
    # writing raw-responses JSON. This keeps disk footprint small.
    image_bytes = b""
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            image_bytes = part.inline_data.data
            break
    return usage, image_bytes


def _call_imagen(model: str, resolution: str, prompt: str) -> tuple[Optional[dict], bytes]:
    """Call Imagen via google-genai. Return (usage_or_None, image_bytes).

    If Phase 0 confirmed Imagen has no usage_metadata, this returns None for usage
    and the caller falls back to catalog estimate as the actual.
    """
    from google import genai
    from google.genai import types
    client = genai.Client()
    config_kwargs = {}
    # Imagen Fast rejects image_size — see CLAUDE.md issue #74.
    if model != "imagen-4.0-fast-generate-001":
        config_kwargs["image_size"] = resolution
    response = client.models.generate_images(
        model=model, prompt=prompt, config=types.GenerateImagesConfig(**config_kwargs)
    )
    usage = None
    if hasattr(response, "usage_metadata") and response.usage_metadata is not None:
        usage = {
            "prompt_token_count": getattr(response.usage_metadata, "prompt_token_count", 0),
            "candidates_token_count": getattr(response.usage_metadata, "candidates_token_count", 0),
            "total_token_count": getattr(response.usage_metadata, "total_token_count", 0),
        }
    image_bytes = response.generated_images[0].image.image_bytes if response.generated_images else b""
    return usage, image_bytes


def _call_openai(model: str, resolution: str, prompt: str) -> tuple[Optional[dict], bytes]:
    """Call OpenAI images.generate. Return (usage_or_None, image_bytes)."""
    import base64
    from openai import OpenAI
    client = OpenAI()
    response = client.images.generate(
        model=model, prompt=prompt, size="1024x1024", quality="medium", n=1
    )
    usage = None
    if hasattr(response, "usage") and response.usage is not None:
        usage = {
            "input_tokens": getattr(response.usage, "input_tokens", 0),
            "output_tokens": getattr(response.usage, "output_tokens", 0),
            "total_tokens": getattr(response.usage, "total_tokens", 0),
        }
    image_bytes = base64.b64decode(response.data[0].b64_json) if response.data and response.data[0].b64_json else b""
    return usage, image_bytes


def _estimate_for_cell(cell: MatrixCell) -> float:
    if cell.provider == "google_nano_banana":
        return estimate_google_cost(model=cell.model, resolution=cell.resolution)
    if cell.provider == "google_imagen":
        return estimate_google_cost(model=cell.model, resolution=cell.resolution)
    if cell.provider == "openai":
        return estimate_openai_cost(size="1024x1024", quality="medium")
    raise ValueError(f"Unknown provider: {cell.provider}")


def _actual_for_cell(cell: MatrixCell, usage: Optional[dict], estimated: float) -> float:
    if usage is None:
        return estimated
    if cell.provider == "google_nano_banana":
        return compute_nano_banana_actual_cost(cell.model, usage)
    if cell.provider == "google_imagen":
        return compute_imagen_actual_cost(cell.model, usage)
    if cell.provider == "openai":
        return compute_openai_image_actual_cost(cell.model, usage)
    raise ValueError(f"Unknown provider: {cell.provider}")


def run_cell(cell: MatrixCell, prompts: PromptSet) -> dict:
    prompt = getattr(prompts, cell.prompt_key)
    estimated = _estimate_for_cell(cell)
    if cell.provider == "google_nano_banana":
        usage, _img = _call_nano_banana(cell.model, cell.resolution, prompt)
    elif cell.provider == "google_imagen":
        usage, _img = _call_imagen(cell.model, cell.resolution, prompt)
    elif cell.provider == "openai":
        usage, _img = _call_openai(cell.model, cell.resolution, prompt)
    else:
        raise ValueError(f"Unknown provider: {cell.provider}")
    actual = _actual_for_cell(cell, usage, estimated)
    return {
        "provider": cell.provider,
        "model": cell.model,
        "resolution": cell.resolution,
        "prompt_key": cell.prompt_key,
        "prompt_chars": len(prompt),
        "prompt_words": len(prompt.split()),
        "catalog_estimate_usd": estimated,
        "raw_usage": usage,
        "computed_actual_usd": actual,
        "delta_usd": estimated - actual,
        "delta_pct": (estimated - actual) / estimated * 100 if estimated else 0.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def append_result(results_path: Path, row: dict) -> None:
    """Append a row to results.json, creating the file if needed."""
    existing = load_results(results_path)
    existing.append(row)
    results_path.write_text(json.dumps(existing, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-spend-usd", type=float, default=5.0)
    parser.add_argument("--results", type=Path, default=Path("docs/spikes/2026-05-21-actual-token-pricing/calibration-results.json"))
    parser.add_argument("--prompts", type=Path, default=Path("docs/spikes/2026-05-21-actual-token-pricing/prompts"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    prompts = load_prompts(args.prompts)
    detected = providers_with_keys()
    cells = [c for c in missing_cells(args.results) if c.provider in detected]
    skipped = [c for c in missing_cells(args.results) if c.provider not in detected]
    if skipped:
        print(f"SKIPPED {len(skipped)} cells — missing API keys for: {sorted({c.provider for c in skipped})}")
    spent = sum(r["computed_actual_usd"] for r in load_results(args.results))
    print(f"Spent so far: ${spent:.3f}; cap ${args.max_spend_usd:.3f}; {len(cells)} cells pending")

    if args.dry_run:
        print("--- DRY RUN — matrix preview ---")
        for c in cells:
            est = _estimate_for_cell(c)
            print(f"  {c.provider}/{c.model}/{c.resolution}/{c.prompt_key} ~${est:.3f}")
        print(f"Total estimated: ${sum(_estimate_for_cell(c) for c in cells):.3f}")
        return 0

    for cell in cells:
        est = _estimate_for_cell(cell)
        try:
            check_spend_cap(spent=spent, next_estimate=est, cap=args.max_spend_usd)
        except SpendCapExceeded as exc:
            print(f"HALT: {exc}")
            return 1
        print(f"Calling {cell.provider}/{cell.model}/{cell.resolution}/{cell.prompt_key} (est ${est:.3f})...")
        row = run_cell(cell, prompts)
        append_result(args.results, row)
        spent += row["computed_actual_usd"]
        print(f"  actual ${row['computed_actual_usd']:.3f}  delta {row['delta_pct']:+.1f}%  cumulative ${spent:.3f}")

    print(f"Done. Cumulative actual: ${spent:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run existing tests to confirm no regression**

Run: `.venv/bin/pytest tests/test_spike_pricing_calibration.py tests/test_actual_cost_calculator.py tests/test_pricing_freshness.py -v`
Expected: all PASS.

- [ ] **Step 3: Commit**

```bash
git add tools/spike_pricing_calibration.py
git commit -m "feat(spike): wire calibration script to real provider SDKs"
```

### Task 13: Dry-run the calibration matrix

**Files:** (no file changes — operational verification)

- [ ] **Step 1: Execute dry-run mode**

```bash
.venv/bin/python tools/spike_pricing_calibration.py --dry-run
```

Expected output: each pending cell listed with its catalog estimate; total estimated spend printed. No API calls made.

- [ ] **Step 2: Sanity-check the total**

The printed total should be ≈$2.25 (matching the spec's calibration matrix table). If it deviates by more than 25%, investigate before proceeding:

- Have any catalog rates changed since the spec was written?
- Are all 25 cells listed?
- Are any cells from providers without API keys?

- [ ] **Step 3: Capture dry-run output**

Save the dry-run output to the spike directory for the report:

```bash
.venv/bin/python tools/spike_pricing_calibration.py --dry-run > docs/spikes/2026-05-21-actual-token-pricing/dry-run.txt
git add docs/spikes/2026-05-21-actual-token-pricing/dry-run.txt
git commit -m "spike(token-pricing): dry-run calibration matrix preview"
```

### Task 14: Live calibration run (real spend)

**Files:**
- Will populate: `docs/spikes/2026-05-21-actual-token-pricing/calibration-results.json`

- [ ] **Step 1: Confirm API keys are configured**

```bash
echo "GOOGLE_API_KEY: ${GOOGLE_API_KEY:+set}${GOOGLE_API_KEY:-MISSING}"
echo "GOOGLE_CLOUD_PROJECT: ${GOOGLE_CLOUD_PROJECT:+set}${GOOGLE_CLOUD_PROJECT:-MISSING}"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+set}${OPENAI_API_KEY:-MISSING}"
```

Expected: at least one Google key and the OpenAI key set. If only one is configured, the script will SKIP the others (acceptable; report will note it).

- [ ] **Step 2: Pause and confirm with the user before spending**

The next command makes real API calls up to a $5 budget. Confirm with the user before running. If running unattended, the `--max-spend-usd 5.0` argument is the hard cap.

- [ ] **Step 3: Execute the live calibration**

```bash
.venv/bin/python tools/spike_pricing_calibration.py --max-spend-usd 5.0
```

Per-cell output lines look like:

```
Calling google_nano_banana/gemini-3.1-flash-image-preview/1K/short_a (est $0.067)...
  actual $0.040  delta +40.3%  cumulative $0.040
```

The script writes each row to `calibration-results.json` immediately after the call returns, so a crash mid-run does not lose spent money's data.

- [ ] **Step 4: Verify results file**

```bash
.venv/bin/python -c "import json; rows = json.load(open('docs/spikes/2026-05-21-actual-token-pricing/calibration-results.json')); print(f'{len(rows)} rows'); print('cumulative actual:', sum(r['computed_actual_usd'] for r in rows))"
```

Expected: 25 rows (or fewer if any cells were skipped due to missing keys); cumulative actual under $5.

- [ ] **Step 5: Commit results**

```bash
git add docs/spikes/2026-05-21-actual-token-pricing/calibration-results.json
git commit -m "spike(token-pricing): live calibration run results"
```

### Task 15: Generate the Phase 1 report

**Files:**
- Create: `docs/spikes/2026-05-21-actual-token-pricing/report.md`

- [ ] **Step 1: Read calibration results and aggregate per cell**

For each unique (provider, model, resolution) tuple, compute over its three prompt-size rows:

- Mean catalog estimate
- Mean actual
- Median delta %
- Min delta %
- Max delta %

A small helper script makes this reproducible:

```python
# tools/spike_pricing_report.py
"""Aggregate calibration results into report.md."""
import json
import statistics
from collections import defaultdict
from pathlib import Path

RESULTS = Path("docs/spikes/2026-05-21-actual-token-pricing/calibration-results.json")
REPORT = Path("docs/spikes/2026-05-21-actual-token-pricing/report.md")


def main():
    rows = json.loads(RESULTS.read_text())
    grouped = defaultdict(list)
    for r in rows:
        grouped[(r["provider"], r["model"], r["resolution"])].append(r)

    lines = ["# Phase 1 — Calibration Report", "", "## Delta per (provider, model, resolution)", "", "| Provider | Model | Resolution | Mean estimate | Mean actual | Median Δ% | Min Δ% | Max Δ% | N |", "|---|---|---|---|---|---|---|---|---|"]
    overall_estimate = 0.0
    overall_actual = 0.0
    for (provider, model, res), bucket in sorted(grouped.items()):
        est_mean = statistics.mean(r["catalog_estimate_usd"] for r in bucket)
        act_mean = statistics.mean(r["computed_actual_usd"] for r in bucket)
        deltas = [r["delta_pct"] for r in bucket]
        lines.append(f"| {provider} | {model} | {res} | ${est_mean:.4f} | ${act_mean:.4f} | {statistics.median(deltas):+.1f}% | {min(deltas):+.1f}% | {max(deltas):+.1f}% | {len(bucket)} |")
        overall_estimate += sum(r["catalog_estimate_usd"] for r in bucket)
        overall_actual += sum(r["computed_actual_usd"] for r in bucket)

    lines.extend([
        "",
        f"**Cumulative catalog estimate:** ${overall_estimate:.3f}",
        f"**Cumulative actual:**           ${overall_actual:.3f}",
        f"**Overall delta:**               {(overall_estimate - overall_actual) / overall_estimate * 100:+.1f}%",
        "",
        "## GO/NO-GO verdict",
        "",
        "Criteria from spec:",
        "- GO if any cell's median Δ ≥ 10%, OR cumulative actual is >10% below cumulative estimate.",
        "- NO-GO if all median Δ < 5%.",
        "- AMBIGUOUS if any cell is 5–10% — extend matrix with _b prompts (budget permitting), then re-evaluate.",
        "",
        "**Verdict:** _TBD — fill in based on the table above before committing._",
    ])

    REPORT.write_text("\n".join(lines))
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the report generator**

```bash
.venv/bin/python tools/spike_pricing_report.py
```

- [ ] **Step 3: Manually fill in the Verdict section**

Open `docs/spikes/2026-05-21-actual-token-pricing/report.md`, replace `_TBD_` with one of: `GO`, `NO-GO`, `AMBIGUOUS`. Justify in 1-2 sentences referencing the table.

- [ ] **Step 4: Commit**

```bash
git add tools/spike_pricing_report.py docs/spikes/2026-05-21-actual-token-pricing/report.md
git commit -m "spike(token-pricing): phase 1 calibration report + verdict"
```

### Task 16: Decision gate — update spike README and decide Phase 2

**Files:**
- Modify: `docs/spikes/2026-05-21-actual-token-pricing/README.md`

- [ ] **Step 1: Update the README**

Replace the `## Verdict` placeholder with the actual verdict and key findings from `report.md`. Include:

- Overall cumulative delta %
- Worst-deviating cell (highest median Δ)
- Best-aligning cell (lowest median Δ)
- Whether the spike proceeds to Phase 2

- [ ] **Step 2: Commit**

```bash
git add docs/spikes/2026-05-21-actual-token-pricing/README.md
git commit -m "spike(token-pricing): decision gate — README updated with verdict"
```

- [ ] **Step 3: Branch on verdict**

- If **NO-GO**: jump to Task 22 (finalisation). Phase 2 tasks 17–21 are skipped.
- If **AMBIGUOUS**: extend the matrix with `_b` prompt variants up to remaining budget. Re-run report. Re-evaluate. If still ambiguous, present findings to operator and ask which way to call it.
- If **GO**: continue to Task 17.

---

## Phase 2 — Production Refactor (Gated)

Tasks 17–21 run only if Task 16 declared **GO**.

### Task 17: TDD `GenerationResult` dataclass

**Files:**
- Create: `src/cloud_results.py`
- Create: `tests/test_cloud_results.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cloud_results.py
import os
from pathlib import Path

from src.cloud_results import GenerationResult


def test_generation_result_path_is_fspath_compatible(tmp_path):
    f = tmp_path / "image.png"
    f.write_bytes(b"fake")
    result = GenerationResult(
        path=str(f),
        cost_estimated=0.067,
        cost_actual=0.040,
        usage_metadata={"prompt_token_count": 100, "candidates_token_count": 1290, "total_token_count": 1390},
        provider="google_nano_banana",
        model="gemini-3.1-flash-image-preview",
        resolution="1K",
    )
    # legacy callers reading the result as a path:
    assert Path(result).name == "image.png"
    assert os.fspath(result) == str(f)
    assert str(result) == str(f)


def test_generation_result_no_usage_keeps_actual_optional():
    result = GenerationResult(
        path="/tmp/x.png",
        cost_estimated=0.04,
        cost_actual=None,
        usage_metadata=None,
        provider="fal",
        model="flux-2-pro",
        resolution="1K",
    )
    assert result.cost_actual is None
```

- [ ] **Step 2: Run; verify FAIL**

Run: `.venv/bin/pytest tests/test_cloud_results.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement**

```python
# src/cloud_results.py
"""GenerationResult — the return value of generate_cloud_image().

Backwards-compatible: implements __fspath__ and __str__ so legacy callers
that pass the result to Path(), open(), or string interpolation keep working.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class GenerationResult:
    path: str
    cost_estimated: float
    cost_actual: Optional[float]
    usage_metadata: Optional[dict]
    provider: str
    model: str
    resolution: str

    def __fspath__(self) -> str:
        return self.path

    def __str__(self) -> str:
        return self.path
```

- [ ] **Step 4: Run; verify PASS; commit**

```bash
.venv/bin/pytest tests/test_cloud_results.py -v
git add src/cloud_results.py tests/test_cloud_results.py
git commit -m "feat(cloud-results): GenerationResult dataclass with fspath compat"
```

### Task 18: TDD BudgetTracker — record `cost_actual`

**Files:**
- Modify: `src/budget_tracker.py`
- Modify: `tests/test_budget_tracker.py` (or wherever existing tracker tests live)

- [ ] **Step 1: Find existing tests**

```bash
grep -l "BudgetTracker\|log_api_call" tests/ | head -5
```

Open the first match.

- [ ] **Step 2: Write a failing test for the new behaviour**

```python
def test_log_api_call_records_cost_actual_when_provided():
    from src.budget_tracker import BudgetTracker
    tracker = BudgetTracker(cap_usd=10.0)
    tracker.log_api_call(
        model_key="gemini-3.1-flash-image-preview-1K",
        cost_estimated=0.067,
        image_id="img-1",
        cost_actual=0.040,
        usage_metadata={"prompt_token_count": 100, "candidates_token_count": 1290},
    )
    # cumulative tracks actual when present
    assert tracker.spent_usd == 0.040
    # ledger row carries both
    rows = tracker.ledger
    assert len(rows) == 1
    assert rows[0]["cost_estimated"] == 0.067
    assert rows[0]["cost_actual"] == 0.040


def test_log_api_call_uses_estimate_when_actual_absent():
    from src.budget_tracker import BudgetTracker
    tracker = BudgetTracker(cap_usd=10.0)
    tracker.log_api_call(
        model_key="fal-flux-2-pro-1K",
        cost_estimated=0.030,
        image_id="img-2",
    )
    assert tracker.spent_usd == 0.030
    assert tracker.ledger[0]["cost_estimated"] == 0.030
    assert tracker.ledger[0]["cost_actual"] is None


def test_cost_summary_markdown_shows_both_columns():
    from src.budget_tracker import BudgetTracker
    tracker = BudgetTracker(cap_usd=10.0)
    tracker.log_api_call("gemini-3.1-flash-image-preview-1K", 0.067, "img-1", cost_actual=0.040)
    tracker.log_api_call("fal-flux-2-pro-1K", 0.030, "img-2")
    md = tracker.cost_summary_markdown()
    assert "Estimated $" in md
    assert "Actual $" in md
    assert "0.067" in md
    assert "0.040" in md
```

- [ ] **Step 3: Run; verify FAIL**

Run: `.venv/bin/pytest tests/test_budget_tracker.py -v -k "cost_actual or cost_summary_markdown_shows_both"`
Expected: FAIL with `TypeError: log_api_call() got an unexpected keyword argument 'cost_actual'`.

- [ ] **Step 4: Implement the changes**

Open `src/budget_tracker.py` and modify `log_api_call`:

```python
def log_api_call(
    self,
    model_key: str,
    cost_estimated: float,
    image_id: str,
    cost_actual: Optional[float] = None,
    usage_metadata: Optional[dict] = None,
) -> None:
    """Record a cloud API call.

    Args:
        model_key: provider+model+resolution identifier.
        cost_estimated: pre-flight catalog estimate (used for cap check).
        image_id: stable identifier for this call.
        cost_actual: actual cost computed from API-returned usage metadata.
            When None, the ledger uses cost_estimated as the spent amount.
        usage_metadata: verbatim usage dict from the API for audit.
    """
    spent_amount = cost_actual if cost_actual is not None else cost_estimated
    self._spent += spent_amount
    self._calls.append({
        "model_key": model_key,
        "cost_estimated": cost_estimated,
        "cost_actual": cost_actual,
        "image_id": image_id,
        "usage_metadata": usage_metadata,
    })
```

If the existing signature uses a positional `cost_usd` argument that callers rely on, support both — accept `cost_usd` as a deprecated alias:

```python
def log_api_call(
    self,
    model_key: str,
    cost_estimated: float = None,
    image_id: str = None,
    cost_actual: Optional[float] = None,
    usage_metadata: Optional[dict] = None,
    *,
    cost_usd: Optional[float] = None,  # legacy alias
) -> None:
    if cost_estimated is None and cost_usd is not None:
        cost_estimated = cost_usd
    if cost_estimated is None:
        raise TypeError("cost_estimated (or legacy cost_usd) is required")
    # ... rest unchanged
```

Update `cost_summary_markdown` to render both columns:

```python
def cost_summary_markdown(self) -> str:
    lines = ["| Model | Image | Estimated $ | Actual $ |", "|---|---|---|---|"]
    for row in self._calls:
        actual = f"${row['cost_actual']:.4f}" if row["cost_actual"] is not None else "—"
        lines.append(f"| {row['model_key']} | {row['image_id']} | ${row['cost_estimated']:.4f} | {actual} |")
    lines.append("")
    lines.append(f"**Total spent:** ${self._spent:.3f} / cap ${self._cap:.3f}")
    return "\n".join(lines)
```

Expose `self._calls` as `self.ledger` (property) and `self._spent` as `self.spent_usd` if not already:

```python
@property
def ledger(self) -> list:
    return list(self._calls)

@property
def spent_usd(self) -> float:
    return self._spent
```

- [ ] **Step 5: Run all tracker tests; verify PASS**

Run: `.venv/bin/pytest tests/test_budget_tracker.py -v`
Expected: all tests PASS, including the three new ones.

- [ ] **Step 6: Run the full suite to catch regressions**

Run: `.venv/bin/pytest tests/ -q`
Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add src/budget_tracker.py tests/test_budget_tracker.py
git commit -m "feat(budget): record cost_estimated + cost_actual; ledger api"
```

### Task 19: Plumb GenerationResult through `src/generate_cloud_image.py`

**Files:**
- Modify: `src/generate_cloud_image.py`

This task changes the return shape of `generate_google`, `generate_openai`, `generate_fal`, `generate_recraft_*` to a `GenerationResult`. Callers that read it as `path: str` keep working via `__fspath__`/`__str__`.

- [ ] **Step 1: Locate the return statements**

```bash
grep -n "return " src/generate_cloud_image.py | grep -v "^[[:space:]]*#" | head -30
```

Identify each provider branch's final return.

- [ ] **Step 2: Modify the Google branch**

Find the Google branch (look for `generate_google` or `if provider == "google"`). Replace its current return with:

```python
from src.cloud_results import GenerationResult
from src.actual_cost_calculator import compute_nano_banana_actual_cost, compute_imagen_actual_cost

# Inside generate_google after the SDK call returns `response` and `image_path`:
usage_dict = None
cost_actual: Optional[float] = None
if model in _NANO_BANANA_MODELS:
    if hasattr(response, "usage_metadata") and response.usage_metadata is not None:
        usage_dict = {
            "prompt_token_count": response.usage_metadata.prompt_token_count,
            "candidates_token_count": response.usage_metadata.candidates_token_count,
            "total_token_count": response.usage_metadata.total_token_count,
        }
        try:
            cost_actual = compute_nano_banana_actual_cost(model, usage_dict)
        except ValueError:
            cost_actual = None
elif model in _IMAGEN_MODELS:
    if hasattr(response, "usage_metadata") and response.usage_metadata is not None:
        usage_dict = {
            "prompt_token_count": getattr(response.usage_metadata, "prompt_token_count", 0),
            "candidates_token_count": getattr(response.usage_metadata, "candidates_token_count", 0),
            "total_token_count": getattr(response.usage_metadata, "total_token_count", 0),
        }
        try:
            cost_actual = compute_imagen_actual_cost(model, usage_dict)
        except ValueError:
            cost_actual = None

return GenerationResult(
    path=str(image_path),
    cost_estimated=cost,
    cost_actual=cost_actual,
    usage_metadata=usage_dict,
    provider="google",
    model=model,
    resolution=resolution,
)
```

If Phase 0 confirmed Imagen exposes no usage_metadata, the `elif model in _IMAGEN_MODELS` block leaves `usage_dict = None` and `cost_actual = None` — the dataclass shape is uniform.

- [ ] **Step 3: Modify the OpenAI branch similarly**

```python
from src.actual_cost_calculator import compute_openai_image_actual_cost

# In generate_openai after the SDK call:
usage_dict = None
cost_actual: Optional[float] = None
if hasattr(response, "usage") and response.usage is not None:
    usage_dict = {
        "input_tokens": getattr(response.usage, "input_tokens", 0),
        "output_tokens": getattr(response.usage, "output_tokens", 0),
        "total_tokens": getattr(response.usage, "total_tokens", 0),
    }
    try:
        cost_actual = compute_openai_image_actual_cost(model, usage_dict)
    except ValueError:
        cost_actual = None

return GenerationResult(
    path=str(image_path),
    cost_estimated=cost,
    cost_actual=cost_actual,
    usage_metadata=usage_dict,
    provider="openai",
    model=model,
    resolution=resolution,
)
```

- [ ] **Step 4: Wrap FAL and Recraft branches without usage capture**

For providers that have no usage field (FAL, Recraft), return the dataclass with `cost_actual = cost_estimated` and `usage_metadata = None`:

```python
return GenerationResult(
    path=str(image_path),
    cost_estimated=cost,
    cost_actual=cost,  # no usage surface; actual == estimate by definition
    usage_metadata=None,
    provider="fal",   # or "recraft"
    model=model,
    resolution=resolution,
)
```

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/pytest tests/ -q`
Expected: all green. The `__fspath__`/`__str__` shims should keep all path-consuming callers happy.

- [ ] **Step 6: Run an end-to-end smoke test**

Pick one fast smoke test that exercises the cloud image path (look in `tests/test_phase5_integration.py` or similar):

```bash
.venv/bin/pytest tests/test_phase5_integration.py -v
```

Expected: green.

- [ ] **Step 7: Commit**

```bash
git add src/generate_cloud_image.py
git commit -m "feat(cloud-image): return GenerationResult with cost_actual"
```

### Task 20: Sync the plugin copy

**Files:**
- Modify: `plugins/jack-tar-cloud/src/generate_cloud_image.py`

Per CLAUDE.md, the plugin copy of `generate_cloud_image.py` lives at `plugins/jack-tar-cloud/src/` and is the distributable copy. It must stay in sync with `src/generate_cloud_image.py`.

- [ ] **Step 1: Diff the two files**

```bash
diff src/generate_cloud_image.py plugins/jack-tar-cloud/src/generate_cloud_image.py | head -40
```

- [ ] **Step 2: Apply the same changes to the plugin copy**

Re-apply Steps 2–4 of Task 19 to the plugin copy, importing from `src.cloud_results` and `src.actual_cost_calculator` the same way. If the plugin copy uses a different import convention (e.g. relative imports), follow that convention but reach the same module.

- [ ] **Step 3: Run plugin tests**

```bash
.venv/bin/pytest plugins/jack-tar-cloud/tests/ -v
```

Expected: green.

- [ ] **Step 4: Commit**

```bash
git add plugins/jack-tar-cloud/src/generate_cloud_image.py
git commit -m "feat(cloud-image): sync plugin copy with src/"
```

### Task 21: Mini-deck dogfood — verify cumulative actual ≤ estimated

**Files:**
- Will produce: `output/spike-token-pricing-dogfood-2026-05-21/deck.pptx` (or similar)
- Will produce: `output/spike-token-pricing-dogfood-2026-05-21/cost_summary.md`

- [ ] **Step 1: Build a minimal TalkBrief**

Write a 2-slide test brief that exercises Nano Banana Flash 1K (the cheapest token-aware path) twice. Total expected spend: ~$0.14.

```bash
cat > /tmp/spike_dogfood_brief.json <<'EOF'
{
  "title": "Token pricing spike dogfood",
  "duration_minutes": 2,
  "audience": "internal",
  "preferences": {
    "image_backend": "cloud",
    "budget_cap_usd": 1.0,
    "providers": {"primary": "google_nano_banana", "tier": "flash", "resolution": "1K"}
  },
  "slides": [
    {"title": "Hello", "kind": "title", "image_prompt": "minimal abstract lighthouse, navy and gold, vector-clean"},
    {"title": "Goodbye", "kind": "closing", "image_prompt": "minimal abstract sunset over harbour, navy and gold, vector-clean"}
  ]
}
EOF
```

Then run it through the conductor. Reuse the existing conductor invocation pattern from `tools/build_demo_deck.py` (look at how it dispatches the brief) — the spike dogfood doesn't need the full keynote pipeline, just the cloud-image + budget-tracker path. If `build_demo_deck.py` accepts a `--brief` arg, use it; otherwise call `src.conductor.run_pipeline(brief_path)` directly via `.venv/bin/python -c '...'`.

- [ ] **Step 2: Inspect the rendered cost summary**

The deck conductor emits a `cost_summary.md` artefact alongside the .pptx. Confirm it shows both columns:

```bash
cat output/spike-token-pricing-dogfood-2026-05-21/cost_summary.md
```

Expected: `Estimated $` and `Actual $` columns; `Total spent` reflects the actual sum.

- [ ] **Step 3: Confirm the actual ≤ estimated invariant**

The cumulative actual should be ≤ cumulative estimated. If actual > estimated, investigate — this would invert the spike's hypothesis and warrants re-examining the token rates in `actual_cost_calculator.py`.

- [ ] **Step 4: Document the dogfood in the spike README**

Append to `docs/spikes/2026-05-21-actual-token-pricing/README.md`:

```markdown
## Phase 2 dogfood

- Date: 2026-05-21
- Brief: <one-line description>
- Cumulative estimated: $X.XX
- Cumulative actual:    $X.XX
- Delta: -X.X% (negative = actual below estimate, hypothesis confirmed)
```

- [ ] **Step 5: Commit**

```bash
git add docs/spikes/2026-05-21-actual-token-pricing/README.md output/spike-token-pricing-dogfood-2026-05-21/cost_summary.md
git commit -m "spike(token-pricing): phase 2 dogfood — actual <= estimated confirmed"
```

---

## Finalisation

### Task 22: Finalise the spike and prepare for PR

**Files:**
- Modify: `docs/spikes/2026-05-21-actual-token-pricing/README.md`

- [ ] **Step 1: Finalise the README**

Ensure the README contains:

- Phase 0 outcome summary
- Phase 1 outcome (link to report.md)
- Phase 2 outcome (only if Phase 2 ran)
- Final verdict
- Links to all artefacts
- "Next steps" — what follow-up work this surfaces

- [ ] **Step 2: Run the full suite one last time**

Run: `.venv/bin/pytest tests/ plugins/jack-tar-cloud/tests/ -q`
Expected: all green; new tests included.

- [ ] **Step 3: Confirm no lint regressions**

Run: `.venv/bin/flake8 src/ tools/ tests/ --max-line-length 120` (or whatever the project's lint command is — check `.github/workflows/validation.yml`)
Expected: clean.

- [ ] **Step 4: Final commit**

```bash
git add docs/spikes/2026-05-21-actual-token-pricing/README.md
git commit -m "spike(token-pricing): finalise readme and pre-PR cleanup"
```

- [ ] **Step 5: Use the finishing-a-development-branch skill**

Invoke `superpowers:finishing-a-development-branch` to decide whether this spike merges to main as a single PR, splits Phase 1 (measurement-only) from Phase 2 (refactor), or stays on the worktree as documentation only.

---

## Risk register (cross-referenced from spec §Risks)

| Risk | Mitigation in this plan |
|---|---|
| Imagen Developer API exposes no usage_metadata | Task 2 confirms before spending; Task 6 conditionally skipped; provider-uniform dataclass with `usage_metadata=None` |
| Token rates drift | Task 4 captures source URL + date; Task 8 ships advisory test |
| Sample of 3 prompts per cell is low | Spec acknowledges; Task 16 AMBIGUOUS branch extends with `_b` variants |
| gpt-image-1 vs 1.5 may bill differently | Task 2 confirms version; Task 14 records version per row |
| Scope creep into Claude subagent costs | Out-of-scope per spec; resist; file follow-up issue if surfaced |
| API key absence | Task 11 provider-skip; Task 14 confirms keys before spending |
| Provider SDK response shape changes | Tasks 19-20 catch via test suite regression; SDK versions recorded in Task 2 |
