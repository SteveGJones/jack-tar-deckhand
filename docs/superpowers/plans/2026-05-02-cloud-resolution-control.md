# Cloud Resolution Control — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a unified `resolution` parameter to `generate_cloud_image()` so callers can request 1K / 2K / 4K outputs from any cloud provider that supports them, with the parameter mapping cleanly to each provider's native API field.

**Architecture:** Plugin-internal additive change to `plugins/jack-tar-cloud/src/`. New `resolution` kwarg threaded through provider functions; new `ProviderResolutionUnsupportedError` exception; cost tables extended for new tiers (including Imagen dual-pricing detection); `provider_discovery.py` reports `supported_resolutions` per model. SKILL.md surface and render-funnel integration are explicitly OUT of scope (those land in #60).

**Tech Stack:** Python 3.10+, `google-genai` SDK, `fal-client`, `openai` SDK, `pytest` with mock-based unit tests.

**Spec:** `docs/superpowers/specs/2026-05-02-cloud-resolution-control-design.md` (committed `6003978`)
**Issue:** #59 (parent EPIC #58)
**Branch:** `feat/cloud-resolution-control`

---

## File structure

| Path | Action | Responsibility |
|---|---|---|
| `plugins/jack-tar-cloud/src/generate_cloud_image.py` | Modify | Add `_normalise_resolution`, `ProviderResolutionUnsupportedError`, resolution kwarg through every provider, dual-pricing detection in `estimate_google_cost` |
| `plugins/jack-tar-cloud/src/provider_discovery.py` | Modify | Add `supported_resolutions` field per model in `_PROVIDER_DEFAULTS`; surface via `discover_providers()` |
| `plugins/jack-tar-cloud/tests/test_resolution_helpers.py` | Create | Tests for `_normalise_resolution` and `ProviderResolutionUnsupportedError` |
| `plugins/jack-tar-cloud/tests/test_resolution_openai.py` | Create | Tests for OpenAI resolution mapping |
| `plugins/jack-tar-cloud/tests/test_resolution_google.py` | Create | Tests for Imagen + Nano Banana resolution mapping + dual-pricing |
| `plugins/jack-tar-cloud/tests/test_resolution_fal.py` | Create | Tests for FAL FLUX 2 Pro resolution mapping |
| `plugins/jack-tar-cloud/tests/test_resolution_dispatch.py` | Create | End-to-end via `generate_cloud_image()` + provider_discovery surface |
| `plugins/jack-tar-cloud/.claude-plugin/plugin.json` | Modify | Version 1.1.0 → 1.2.0 |
| `.claude-plugin/marketplace.json` | Modify | Sync jack-tar-cloud version to 1.2.0 |
| `docs/spikes/2026-05-02-google-genai-image-config-spike.md` | Create | Phase-0 spike outcome record |
| `output/smoke-test-jack-tar-on-a-page/` | Create | Phase-8 smoke test artefacts |
| `docs/superpowers/dogfooding/2026-MM-DD-resolution-smoke-test.md` | Create | Phase-8 smoke test write-up |

**Test invocation pattern:** `python3 -m pytest plugins/jack-tar-cloud/tests/test_resolution_*.py -v` from the `feat/cloud-resolution-control` worktree root. The existing `test_plugin_imports.py` injects `PLUGIN_ROOT` into `sys.path`; new tests follow the same pattern.

---

## Phase 0: SDK Spike — Implementation Gate

### Task 0: Determine google-genai SDK image_config support

**Files:**
- Create: `docs/spikes/2026-05-02-google-genai-image-config-spike.md`

**Why this is task 0:** The Nano Banana 4K capability shipped in March 2026 and the typed SDK surface may lag. The implementation shape for Phase 4 depends on which path the SDK supports. Run this BEFORE writing any other code.

- [ ] **Step 1: Capture installed SDK version**

```bash
cd /Users/stevejones/Documents/Development/jack-tar-deckhand-resolution
python3 -c "from google import genai; print(genai.__version__)" 2>&1
```

Record the version output. If the import fails, the SDK isn't installed in this worktree's environment — install with `python3 -m pip install google-genai` first.

- [ ] **Step 2: Test PATH-A — raw dict on typed config**

```bash
python3 << 'EOF'
from google.genai.types import GenerateContentConfig
try:
    cfg = GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT'],
        image_config={'image_size': '4K'},
    )
    print(f"PATH-A: ACCEPTED — typed config takes image_config as dict")
    print(f"  cfg fields: {[f for f in dir(cfg) if not f.startswith('_')]}")
except (TypeError, AttributeError) as e:
    print(f"PATH-A: REJECTED — {e}")
EOF
```

Record stdout.

- [ ] **Step 3: Test PATH-B — typed ImageConfig**

```bash
python3 << 'EOF'
try:
    from google.genai.types import ImageConfig, GenerateContentConfig
    cfg = GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT'],
        image_config=ImageConfig(image_size='4K'),
    )
    print(f"PATH-B: ACCEPTED — typed ImageConfig available")
except (ImportError, TypeError, AttributeError) as e:
    print(f"PATH-B: NOT AVAILABLE — {type(e).__name__}: {e}")
EOF
```

Record stdout.

- [ ] **Step 4: Test PATH-C — raw dict via generate_content kwarg**

```bash
python3 << 'EOF'
import os
if not os.environ.get('GOOGLE_API_KEY') and not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
    print("PATH-C: SKIPPED — no Google credentials in env, cannot do live test")
    print("  (still record this in the spike report; PATH-C verification needs creds)")
else:
    from google import genai
    client = genai.Client()
    try:
        response = client.models.generate_content(
            model='gemini-3-pro-image-preview',
            contents='a small test image of a red square on a white background',
            generation_config={'image_config': {'image_size': '1K'}},
        )
        # Look for image bytes
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith('image/'):
                print(f"PATH-C: ACCEPTED — image returned ({len(part.inline_data.data)} bytes)")
                break
        else:
            print(f"PATH-C: PARTIAL — call succeeded but no image part")
    except Exception as e:
        print(f"PATH-C: REJECTED — {type(e).__name__}: {e}")
EOF
```

Record stdout. PATH-C is a live API call (~$0.13). If credentials aren't set, skip.

- [ ] **Step 5: Write spike report**

Create `docs/spikes/2026-05-02-google-genai-image-config-spike.md` with the following structure:

```markdown
# google-genai SDK image_config Support — Spike Report

**Date:** 2026-05-02
**Spec reference:** `docs/superpowers/specs/2026-05-02-cloud-resolution-control-design.md` §6
**Issue:** #59

## Result

**Chosen path:** PATH-A | PATH-B | PATH-C | NONE
**SDK version tested:** `<version from step 1>`

## Test outcomes

### PATH-A — raw dict on typed config
<paste step 2 stdout>

### PATH-B — typed ImageConfig class
<paste step 3 stdout>

### PATH-C — raw generation_config dict (live API)
<paste step 4 stdout>

## Decision

<one paragraph: which path the implementation will use and why>

## Implementation impact

<one paragraph: what code shape this implies for `_generate_via_nano_banana`>

## SDK version notes

<if a pin or upgrade is needed, document here>
```

Fill every section with actual content from steps 1-4. No placeholders.

- [ ] **Step 6: Commit the spike report**

```bash
cd /Users/stevejones/Documents/Development/jack-tar-deckhand-resolution
git add docs/spikes/2026-05-02-google-genai-image-config-spike.md
git commit -m "spike(cloud): google-genai image_config support — PATH-<X> chosen for #59"
```

### Phase 0 Verification Checkpoint

- [ ] **VERIFY:** Open the spike report. The "Chosen path" line is filled (not "TBD"). The SDK version is recorded. PATH-A/B/C outcomes have actual stdout, not placeholders.
- [ ] **VERIFY:** If PATH-NONE was the result, STOP and surface to the speaker — phase 4 is blocked. Either bump the SDK pin or fall back to raw HTTP REST.

---

## Phase 1: Foundation — Resolution Helper + Exception

### Task 1: Implement `_normalise_resolution` helper

**Files:**
- Modify: `plugins/jack-tar-cloud/src/generate_cloud_image.py` (add helper near top)
- Create: `plugins/jack-tar-cloud/tests/test_resolution_helpers.py`

- [ ] **Step 1: Write failing tests**

Create `plugins/jack-tar-cloud/tests/test_resolution_helpers.py`:

```python
"""Tests for resolution normalisation and ProviderResolutionUnsupportedError."""
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from src.generate_cloud_image import (
    _normalise_resolution,
    ProviderResolutionUnsupportedError,
)


class TestNormaliseResolution:
    def test_uppercase_already(self):
        assert _normalise_resolution("1K") == "1K"
        assert _normalise_resolution("2K") == "2K"
        assert _normalise_resolution("4K") == "4K"

    def test_lowercase_normalised(self):
        assert _normalise_resolution("1k") == "1K"
        assert _normalise_resolution("2k") == "2K"
        assert _normalise_resolution("4k") == "4K"

    def test_512_passes_through(self):
        assert _normalise_resolution("512") == "512"

    def test_whitespace_stripped(self):
        assert _normalise_resolution("  1K  ") == "1K"

    def test_unknown_value_raises(self):
        with pytest.raises(ValueError, match="not recognised"):
            _normalise_resolution("8K")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            _normalise_resolution("")

    def test_non_string_raises(self):
        with pytest.raises(TypeError, match="must be str"):
            _normalise_resolution(1024)

    def test_none_raises(self):
        with pytest.raises(TypeError):
            _normalise_resolution(None)
```

- [ ] **Step 2: Run tests, verify failures**

```bash
cd /Users/stevejones/Documents/Development/jack-tar-deckhand-resolution
python3 -m pytest plugins/jack-tar-cloud/tests/test_resolution_helpers.py -v
```

Expected: ImportError on `_normalise_resolution` and `ProviderResolutionUnsupportedError`.

- [ ] **Step 3: Implement helper and exception**

Edit `plugins/jack-tar-cloud/src/generate_cloud_image.py`. After the existing `ProviderNotImplementedError` class (line ~29), add:

```python
class ProviderResolutionUnsupportedError(ValueError):
    """Raised when a provider/model combination cannot honour the requested resolution.

    Carries the closest supported tier so callers can retry intelligently.
    """

    def __init__(self, provider, model, requested, supported):
        self.provider = provider
        self.model = model
        self.requested = requested
        self.supported = supported
        super().__init__(
            f"{provider}/{model} does not support resolution={requested!r}. "
            f"Supported: {supported}. Retry with one of those, or pick a "
            f"different model."
        )


# --- Resolution normalisation -----------------------------------------------

_VALID_RESOLUTIONS = ("512", "1K", "2K", "4K")


def _normalise_resolution(resolution):
    """Case-fold and validate a resolution string.

    '1k' -> '1K'.  '512' -> '512'.  '8K' raises ValueError.

    Args:
        resolution: str — one of '512', '1K', '2K', '4K' (case-insensitive
            for the K-suffixed values).

    Returns:
        str: normalised value.

    Raises:
        TypeError: resolution is not a string.
        ValueError: resolution is not one of the recognised values.
    """
    if not isinstance(resolution, str):
        raise TypeError(
            f"resolution must be str, got {type(resolution).__name__}"
        )
    stripped = resolution.strip()
    upper = stripped.upper()
    if upper in {"1K", "2K", "4K"}:
        return upper
    if stripped == "512":
        return "512"
    raise ValueError(
        f"resolution={resolution!r} not recognised. "
        f"Valid values: {_VALID_RESOLUTIONS}"
    )
```

- [ ] **Step 4: Run tests, verify pass**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/test_resolution_helpers.py -v
```

Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-cloud/src/generate_cloud_image.py plugins/jack-tar-cloud/tests/test_resolution_helpers.py
git commit -m "feat(cloud): add _normalise_resolution helper + ProviderResolutionUnsupportedError (#59)"
```

### Task 2: Test ProviderResolutionUnsupportedError shape

**Files:**
- Modify: `plugins/jack-tar-cloud/tests/test_resolution_helpers.py`

- [ ] **Step 1: Add tests for the exception class**

Append to `plugins/jack-tar-cloud/tests/test_resolution_helpers.py`:

```python
class TestProviderResolutionUnsupportedError:
    def test_carries_attributes(self):
        err = ProviderResolutionUnsupportedError(
            provider="openai",
            model="gpt-image-1.5",
            requested="4K",
            supported=["1K"],
        )
        assert err.provider == "openai"
        assert err.model == "gpt-image-1.5"
        assert err.requested == "4K"
        assert err.supported == ["1K"]

    def test_message_includes_supported(self):
        err = ProviderResolutionUnsupportedError(
            provider="google",
            model="gemini-3.1-flash-image-preview",
            requested="8K",
            supported=["512", "1K", "2K", "4K"],
        )
        msg = str(err)
        assert "google" in msg
        assert "8K" in msg
        assert "512" in msg
        assert "4K" in msg
        assert "Retry with one of those" in msg

    def test_is_value_error_subclass(self):
        # So callers can `except ValueError` if they want generic handling.
        err = ProviderResolutionUnsupportedError("p", "m", "4K", ["1K"])
        assert isinstance(err, ValueError)
```

- [ ] **Step 2: Run tests**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/test_resolution_helpers.py -v
```

Expected: 11 passed (8 from Task 1 + 3 from Task 2).

- [ ] **Step 3: Commit**

```bash
git add plugins/jack-tar-cloud/tests/test_resolution_helpers.py
git commit -m "test(cloud): assert ProviderResolutionUnsupportedError shape (#59)"
```

### Phase 1 Verification Checkpoint

- [ ] **VERIFY:** `python3 -m pytest plugins/jack-tar-cloud/tests/test_resolution_helpers.py -v` reports 11 passed.
- [ ] **VERIFY:** `python3 -c "from src.generate_cloud_image import _normalise_resolution, ProviderResolutionUnsupportedError; print('ok')"` from `plugins/jack-tar-cloud/` prints "ok".
- [ ] **VERIFY:** Existing `test_plugin_imports.py` still passes: `python3 -m pytest plugins/jack-tar-cloud/tests/test_plugin_imports.py -v`.

---

## Phase 2: OpenAI Plumbing

### Task 3: Test OpenAI resolution mapping

**Files:**
- Create: `plugins/jack-tar-cloud/tests/test_resolution_openai.py`

- [ ] **Step 1: Write failing tests**

Create `plugins/jack-tar-cloud/tests/test_resolution_openai.py`:

```python
"""Tests for OpenAI resolution mapping in generate_openai."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import os

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from src.generate_cloud_image import (
    generate_openai,
    ProviderResolutionUnsupportedError,
)


@pytest.fixture
def mock_openai_client(tmp_path, monkeypatch):
    """Mock the OpenAI client so no live API call is made."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    fake_response = MagicMock()
    fake_response.data = [MagicMock(b64_json="aGVsbG8=")]  # base64 for 'hello'
    with patch("src.generate_cloud_image.OpenAI") as mock_class:
        instance = mock_class.return_value
        instance.images.generate.return_value = fake_response
        yield instance


class TestOpenAIResolution:
    def test_default_1k_maps_to_1024_when_size_unset(self, mock_openai_client, tmp_path):
        out = tmp_path / "out.png"
        generate_openai(
            prompt="test", output_path=str(out), resolution="1K", size=None,
        )
        call_kwargs = mock_openai_client.images.generate.call_args.kwargs
        assert call_kwargs["size"] == "1024x1024"

    def test_explicit_size_wins_over_resolution(self, mock_openai_client, tmp_path):
        out = tmp_path / "out.png"
        generate_openai(
            prompt="test", output_path=str(out),
            resolution="1K", size="1536x1024",
        )
        call_kwargs = mock_openai_client.images.generate.call_args.kwargs
        assert call_kwargs["size"] == "1536x1024"

    def test_2k_raises_unsupported(self, mock_openai_client, tmp_path):
        out = tmp_path / "out.png"
        with pytest.raises(ProviderResolutionUnsupportedError) as excinfo:
            generate_openai(
                prompt="test", output_path=str(out), resolution="2K", size=None,
            )
        assert excinfo.value.provider == "openai"
        assert excinfo.value.requested == "2K"
        assert excinfo.value.supported == ["1K"]

    def test_4k_raises_unsupported(self, mock_openai_client, tmp_path):
        out = tmp_path / "out.png"
        with pytest.raises(ProviderResolutionUnsupportedError):
            generate_openai(
                prompt="test", output_path=str(out), resolution="4K", size=None,
            )

    def test_512_raises_unsupported(self, mock_openai_client, tmp_path):
        out = tmp_path / "out.png"
        with pytest.raises(ProviderResolutionUnsupportedError):
            generate_openai(
                prompt="test", output_path=str(out), resolution="512", size=None,
            )

    def test_lowercase_resolution_normalised(self, mock_openai_client, tmp_path):
        out = tmp_path / "out.png"
        generate_openai(
            prompt="test", output_path=str(out), resolution="1k", size=None,
        )
        call_kwargs = mock_openai_client.images.generate.call_args.kwargs
        assert call_kwargs["size"] == "1024x1024"

    def test_explicit_size_with_unsupported_resolution_warns_not_raises(
        self, mock_openai_client, tmp_path, caplog
    ):
        # Explicit size= wins; resolution=2K is unsupported on OpenAI but
        # since size= is given, we don't raise — we use the size and warn.
        out = tmp_path / "out.png"
        generate_openai(
            prompt="test", output_path=str(out),
            resolution="2K", size="1024x1024",
        )
        call_kwargs = mock_openai_client.images.generate.call_args.kwargs
        assert call_kwargs["size"] == "1024x1024"
        # Optional: assert a warning is logged. Depending on logger config,
        # caplog may or may not capture; the no-raise behaviour is the contract.
```

- [ ] **Step 2: Run tests, verify failures**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/test_resolution_openai.py -v
```

Expected: All fail because `generate_openai` doesn't yet accept `resolution=` parameter.

### Task 4: Implement OpenAI resolution support

**Files:**
- Modify: `plugins/jack-tar-cloud/src/generate_cloud_image.py:170-220` (`generate_openai`)

- [ ] **Step 1: Update generate_openai signature and body**

Replace the existing `generate_openai` function (currently at lines 170-220) with:

```python
def generate_openai(prompt, output_path, *, resolution='1K', size=None,
                    quality='medium', background='auto', model='gpt-image-1.5'):
    """Generate an image using OpenAI GPT Image API.

    Args:
        prompt: Text prompt for image generation.
        output_path: Where to save the generated PNG.
        resolution: '1K' only (gpt-image-1.5 caps at ~1.5MP). '2K'/'4K'/'512'
            raise ProviderResolutionUnsupportedError. Default '1K'.
        size: Explicit dimensions ('1024x1024', '1536x1024', '1024x1536').
            If provided, takes precedence over resolution. If None, derived
            from resolution.
        quality: Quality tier ('low', 'medium', 'high').
        background: Background type ('auto', 'transparent').
        model: Model name.

    Returns:
        dict: {file_path, provider, model_used, cost_usd, status, resolution}

    Raises:
        ProviderNotConfiguredError: If OPENAI_API_KEY is not set.
        ProviderResolutionUnsupportedError: resolution='2K'/'4K'/'512' and
            no explicit size provided.
    """
    if not os.environ.get('OPENAI_API_KEY'):
        raise ProviderNotConfiguredError(
            'OpenAI not configured: OPENAI_API_KEY environment variable is not set. '
            'See research/04-cloud-api-setup-licensing.md section A for setup.'
        )

    resolution = _normalise_resolution(resolution)

    # Validate resolution unless an explicit size is given.
    # When size is explicit, the user's intent overrides resolution semantics
    # — we use the size and log a warning if there's a mismatch.
    if size is None:
        if resolution != '1K':
            raise ProviderResolutionUnsupportedError(
                provider='openai', model=model,
                requested=resolution, supported=['1K'],
            )
        # Default 1K mapping for OpenAI
        size = '1024x1024'
    else:
        if resolution != '1K':
            logger.warning(
                'OpenAI: explicit size=%r overrides resolution=%r; '
                'using size, ignoring resolution. (gpt-image-1.5 caps at 1.5MP.)',
                size, resolution,
            )

    output_format = 'png' if background == 'transparent' else 'png'

    client = OpenAI()
    response = client.images.generate(
        model=model,
        prompt=prompt,
        size=size,
        quality=quality,
        output_format=output_format,
        background=background,
        n=1,
    )

    image_bytes = base64.b64decode(response.data[0].b64_json)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(image_bytes)

    cost = estimate_openai_cost(size=size, quality=quality)
    logger.info('OpenAI image generated: %s (cost: $%.3f)', output_path, cost)

    return {
        'file_path': str(output_path),
        'provider': 'openai',
        'model_used': model,
        'cost_usd': cost,
        'status': 'generated',
        'resolution': resolution,
    }
```

- [ ] **Step 2: Run tests, verify pass**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/test_resolution_openai.py -v
```

Expected: 7 passed.

- [ ] **Step 3: Verify existing tests still pass**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/ -v
```

Expected: All test files pass (helpers + openai + plugin_imports).

- [ ] **Step 4: Commit**

```bash
git add plugins/jack-tar-cloud/src/generate_cloud_image.py plugins/jack-tar-cloud/tests/test_resolution_openai.py
git commit -m "feat(cloud): wire resolution kwarg into generate_openai (#59)"
```

### Phase 2 Verification Checkpoint

- [ ] **VERIFY:** `python3 -m pytest plugins/jack-tar-cloud/tests/ -v` shows 11 helpers + 7 openai + 4 plugin imports = 22 passed.
- [ ] **VERIFY:** `generate_openai(prompt='x', output_path='/tmp/x.png')` (no kwargs) still works (the default flow is unchanged for callers passing no kwargs).

---

## Phase 3: Google Imagen Plumbing + Cost-Tier Detection

### Task 5: Test Imagen resolution mapping and cost-tier detection

**Files:**
- Create: `plugins/jack-tar-cloud/tests/test_resolution_google.py`

- [ ] **Step 1: Write failing tests**

Create `plugins/jack-tar-cloud/tests/test_resolution_google.py`:

```python
"""Tests for Google Imagen + Nano Banana resolution and pricing."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from src.generate_cloud_image import (
    generate_google,
    estimate_google_cost,
    ProviderResolutionUnsupportedError,
)


@pytest.fixture
def mock_google_client(monkeypatch):
    """Mock the google.genai client so no live API call is made."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    fake_image = MagicMock()
    fake_image.image.image_bytes = b"\x89PNG\r\n\x1a\n" + b"x" * 100
    fake_imagen_response = MagicMock()
    fake_imagen_response.generated_images = [fake_image]
    fake_part = MagicMock()
    fake_part.inline_data.mime_type = "image/png"
    fake_part.inline_data.data = b"\x89PNG\r\n\x1a\n" + b"x" * 100
    fake_nano_response = MagicMock()
    fake_nano_response.candidates = [MagicMock()]
    fake_nano_response.candidates[0].content.parts = [fake_part]
    with patch("src.generate_cloud_image.genai.Client") as mock_class:
        instance = mock_class.return_value
        instance.models.generate_images.return_value = fake_imagen_response
        instance.models.generate_content.return_value = fake_nano_response
        yield instance


class TestImagenResolution:
    def test_imagen_standard_1k_default(self, mock_google_client, tmp_path):
        out = tmp_path / "out.png"
        generate_google(
            prompt="test", output_path=str(out),
            model="imagen-4.0-generate-001",
            resolution="1K",
        )
        call_kwargs = mock_google_client.models.generate_images.call_args.kwargs
        config = call_kwargs["config"]
        # Verify image_size was set on the GenerateImagesConfig
        assert config.image_size == "1K"

    def test_imagen_standard_2k(self, mock_google_client, tmp_path):
        out = tmp_path / "out.png"
        generate_google(
            prompt="test", output_path=str(out),
            model="imagen-4.0-generate-001",
            resolution="2K",
        )
        call_kwargs = mock_google_client.models.generate_images.call_args.kwargs
        assert call_kwargs["config"].image_size == "2K"

    def test_imagen_standard_4k_raises(self, mock_google_client, tmp_path):
        out = tmp_path / "out.png"
        with pytest.raises(ProviderResolutionUnsupportedError) as excinfo:
            generate_google(
                prompt="test", output_path=str(out),
                model="imagen-4.0-generate-001",
                resolution="4K",
            )
        assert excinfo.value.supported == ["1K", "2K"]

    def test_imagen_fast_1k_only(self, mock_google_client, tmp_path):
        out = tmp_path / "out.png"
        # Fast supports 1K
        generate_google(
            prompt="test", output_path=str(out),
            model="imagen-4.0-fast-generate-001",
            resolution="1K",
        )
        # Fast does NOT support 2K
        with pytest.raises(ProviderResolutionUnsupportedError) as excinfo:
            generate_google(
                prompt="test", output_path=str(out),
                model="imagen-4.0-fast-generate-001",
                resolution="2K",
            )
        assert excinfo.value.supported == ["1K"]


class TestImagenCostDualPricing:
    def test_vertex_flat_pricing_when_adc_set(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/fake/path.json")
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        # Vertex flat: 2K is uniform within Standard tier ($0.04)
        cost = estimate_google_cost(
            model="imagen-4.0-generate-001", resolution="2K",
        )
        assert cost == 0.04

    def test_developer_api_token_pricing_when_only_api_key_set(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "test")
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        # Developer API token-based: 2K Standard = ~$0.101
        cost = estimate_google_cost(
            model="imagen-4.0-generate-001", resolution="2K",
        )
        assert cost == 0.101

    def test_imagen_1k_same_across_backends(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "test")
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        cost_dev = estimate_google_cost(
            model="imagen-4.0-generate-001", resolution="1K",
        )
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/fake/path.json")
        cost_vertex = estimate_google_cost(
            model="imagen-4.0-generate-001", resolution="1K",
        )
        assert cost_dev == cost_vertex == 0.04

    def test_imagen_ultra_2k(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/fake/path.json")
        cost = estimate_google_cost(
            model="imagen-4.0-ultra-generate-001", resolution="2K",
        )
        assert cost == 0.06

    def test_nano_banana_cost_unchanged_across_backends(self, monkeypatch):
        # Nano Banana bills identically on either backend.
        monkeypatch.setenv("GOOGLE_API_KEY", "test")
        cost_dev = estimate_google_cost(
            model="gemini-3-pro-image-preview", resolution="4K",
        )
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/fake/path.json")
        cost_vertex = estimate_google_cost(
            model="gemini-3-pro-image-preview", resolution="4K",
        )
        assert cost_dev == cost_vertex == 0.24
```

- [ ] **Step 2: Run tests, verify failures**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/test_resolution_google.py -v
```

Expected: All fail (`generate_google` doesn't yet accept `resolution=`; `estimate_google_cost` doesn't yet accept `resolution=`).

### Task 6: Implement Imagen resolution + cost-tier detection

**Files:**
- Modify: `plugins/jack-tar-cloud/src/generate_cloud_image.py` — `_GOOGLE_COSTS`, `estimate_google_cost`, `_generate_via_imagen`, `generate_google`

- [ ] **Step 1: Replace `_GOOGLE_COSTS` cost table**

Find the existing `_GOOGLE_COSTS = {...}` block (around line 70) and replace with:

```python
# Google Imagen has dual pricing depending on backend:
#   - Vertex AI (GOOGLE_APPLICATION_CREDENTIALS): flat per-image pricing
#   - Gemini Developer API (GOOGLE_API_KEY only): token-based, 2K is dearer
# Nano Banana Pro/Flash bill identically on both backends (per-image).

# Per-resolution costs (provider-agnostic, used for Nano Banana too).
# Sourced from research May 2026; see EPIC #58 pricing table.
_NANO_BANANA_COSTS = {
    ('gemini-3-pro-image-preview', '1K'): 0.134,
    ('gemini-3-pro-image-preview', '2K'): 0.134,
    ('gemini-3-pro-image-preview', '4K'): 0.24,
    ('gemini-3.1-flash-image-preview', '512'): 0.045,
    ('gemini-3.1-flash-image-preview', '1K'): 0.067,
    ('gemini-3.1-flash-image-preview', '2K'): 0.101,
    ('gemini-3.1-flash-image-preview', '4K'): 0.151,
}

# Imagen Vertex AI flat pricing (per-tier, uniform within tier).
_IMAGEN_VERTEX_COSTS = {
    ('imagen-4.0-fast-generate-001', '1K'): 0.020,
    ('imagen-4.0-generate-001', '1K'): 0.040,
    ('imagen-4.0-generate-001', '2K'): 0.040,
    ('imagen-4.0-ultra-generate-001', '1K'): 0.060,
    ('imagen-4.0-ultra-generate-001', '2K'): 0.060,
}

# Imagen Gemini Developer API token-based pricing.
# 1K matches Vertex flat; 2K is dearer (1680 tokens at the Imagen rate).
_IMAGEN_DEVELOPER_COSTS = {
    ('imagen-4.0-fast-generate-001', '1K'): 0.020,
    ('imagen-4.0-generate-001', '1K'): 0.040,
    ('imagen-4.0-generate-001', '2K'): 0.101,
    ('imagen-4.0-ultra-generate-001', '1K'): 0.060,
    ('imagen-4.0-ultra-generate-001', '2K'): 0.101,  # treat as token-based too
}

# Models that use generate_content API (Nano Banana) vs generate_images API (Imagen 4)
_NANO_BANANA_MODELS = {
    'gemini-3.1-flash-image-preview',
    'gemini-3-pro-image-preview',
}

_IMAGEN_MODELS = {
    'imagen-4.0-generate-001',
    'imagen-4.0-fast-generate-001',
    'imagen-4.0-ultra-generate-001',
}

# Per-model supported resolutions (used by validation and discovery).
_MODEL_RESOLUTIONS = {
    'imagen-4.0-fast-generate-001': ['1K'],
    'imagen-4.0-generate-001': ['1K', '2K'],
    'imagen-4.0-ultra-generate-001': ['1K', '2K'],
    'gemini-3.1-flash-image-preview': ['512', '1K', '2K', '4K'],
    'gemini-3-pro-image-preview': ['1K', '2K', '4K'],
}
```

(Keep the old `_GOOGLE_COSTS` dict for now as a fallback for any callers that didn't migrate; it can be removed in a later cleanup commit if no callers exist.)

- [ ] **Step 2: Replace `estimate_google_cost`**

Find `def estimate_google_cost(...)` (around line 89) and replace with:

```python
def estimate_google_cost(model='gemini-3.1-flash-image-preview', resolution='1K'):
    """Return estimated USD cost for a Google image generation call.

    For Imagen models, billing depends on which Google backend the SDK uses:
      - GOOGLE_APPLICATION_CREDENTIALS set -> Vertex AI flat per-image
      - GOOGLE_API_KEY only -> Gemini Developer API token-based

    Nano Banana Pro/Flash bill identically across both backends.

    Args:
        model: Google model name.
        resolution: '512' | '1K' | '2K' | '4K' (case-insensitive). Default '1K'.

    Returns:
        float: Estimated cost in USD.

    Raises:
        ValueError: If the model/resolution combination is unknown.
    """
    resolution = _normalise_resolution(resolution)

    if model in _NANO_BANANA_MODELS:
        key = (model, resolution)
        if key not in _NANO_BANANA_COSTS:
            raise ValueError(
                f"Unknown Nano Banana model/resolution: {model}/{resolution}. "
                f"Supported: {sorted(k for k in _NANO_BANANA_COSTS if k[0] == model)}"
            )
        return _NANO_BANANA_COSTS[key]

    if model in _IMAGEN_MODELS:
        # Detect backend: Vertex (ADC) wins over Developer API if both are set.
        backend = (
            'vertex'
            if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            else 'developer'
        )
        table = _IMAGEN_VERTEX_COSTS if backend == 'vertex' else _IMAGEN_DEVELOPER_COSTS
        key = (model, resolution)
        if key not in table:
            raise ValueError(
                f"Unknown Imagen model/resolution: {model}/{resolution} "
                f"(backend={backend}). Check supported_resolutions for this model."
            )
        return table[key]

    raise ValueError(
        f"Unknown Google model: {model}. "
        f"Valid models: {sorted(_NANO_BANANA_MODELS | _IMAGEN_MODELS)}"
    )
```

- [ ] **Step 3: Update `_generate_via_imagen`**

Find `def _generate_via_imagen(client, model, prompt, aspect_ratio):` (around line 319) and replace with:

```python
def _generate_via_imagen(client, model, prompt, aspect_ratio, resolution):
    """Generate image via Imagen 4 (generate_images API) at the given resolution.

    Returns:
        bytes: Raw image bytes from the response.
    """
    config = GenerateImagesConfig(
        number_of_images=1,
        aspect_ratio=aspect_ratio,
        output_mime_type='image/png',
        image_size=resolution,
    )
    response = client.models.generate_images(
        model=model,
        prompt=prompt,
        config=config,
    )

    return response.generated_images[0].image.image_bytes
```

- [ ] **Step 4: Update `generate_google` to validate + thread resolution**

Find `def generate_google(prompt, output_path, **kwargs):` (around line 223). Replace its body with:

```python
def generate_google(prompt, output_path, **kwargs):
    """Generate an image using Google Nano Banana or Imagen 4 APIs.

    Auth: GOOGLE_API_KEY (Gemini Developer API) or
          GOOGLE_APPLICATION_CREDENTIALS (Vertex AI).

    Args:
        prompt: Text prompt for image generation.
        output_path: Where to save the generated PNG.
        **kwargs: Optional arguments:
            model: Model name (default: 'gemini-3.1-flash-image-preview').
            aspect_ratio: Aspect ratio for Imagen 4 (e.g. '16:9', '1:1').
            resolution: '512' | '1K' | '2K' | '4K'. Default '1K'.
                Per-model support varies; see _MODEL_RESOLUTIONS.

    Returns:
        dict: {file_path, provider, model_used, cost_usd, status, resolution}

    Raises:
        ProviderNotConfiguredError: If neither Google auth env var is set.
        ProviderResolutionUnsupportedError: model doesn't support resolution.
    """
    api_key = os.environ.get('GOOGLE_API_KEY')
    has_adc = bool(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'))
    if not api_key and not has_adc:
        raise ProviderNotConfiguredError(
            'Google not configured: set GOOGLE_API_KEY (Gemini Developer API) or '
            'GOOGLE_APPLICATION_CREDENTIALS (Vertex AI). '
            'See research/04-cloud-api-setup-licensing.md section B for setup.'
        )

    model = kwargs.get('model', 'gemini-3.1-flash-image-preview')
    aspect_ratio = kwargs.get('aspect_ratio', '16:9')
    resolution = _normalise_resolution(kwargs.get('resolution', '1K'))

    # Validate resolution against per-model capability
    supported = _MODEL_RESOLUTIONS.get(model)
    if supported is None:
        raise ValueError(
            f"Unknown Google model: {model}. "
            f"Valid: {sorted(_NANO_BANANA_MODELS | _IMAGEN_MODELS)}"
        )
    if resolution not in supported:
        raise ProviderResolutionUnsupportedError(
            provider='google', model=model,
            requested=resolution, supported=supported,
        )

    # Build client — use API key if available, otherwise ADC
    client_kwargs = {}
    if api_key:
        client_kwargs['api_key'] = api_key
    client = genai.Client(**client_kwargs)

    if model in _NANO_BANANA_MODELS:
        image_bytes = _generate_via_nano_banana(client, model, prompt, resolution)
    elif model in _IMAGEN_MODELS:
        image_bytes = _generate_via_imagen(client, model, prompt, aspect_ratio, resolution)
    else:
        raise ValueError(
            f"Unknown Google model: {model}. "
            f"Valid models: {sorted(_NANO_BANANA_MODELS | _IMAGEN_MODELS)}"
        )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(image_bytes)

    cost = estimate_google_cost(model=model, resolution=resolution)
    logger.info(
        'Google image generated: %s (model: %s, resolution: %s, cost: $%.3f)',
        output_path, model, resolution, cost,
    )

    return {
        'file_path': str(output_path),
        'provider': 'google',
        'model_used': model,
        'cost_usd': cost,
        'status': 'generated',
        'resolution': resolution,
    }
```

NOTE: `_generate_via_nano_banana` is updated in Phase 4 (after the SDK spike). For now, leave it accepting the old 3-arg signature; Phase 4 will add the resolution parameter. This means Nano Banana Imagen tests in Phase 3 are scoped to Imagen models only — Nano Banana models route through the still-old function and `resolution` flows past it without effect. That's acceptable for Phase 3 because:
- The `generate_google` validation gate already rejects unsupported resolutions BEFORE reaching the dispatch.
- Nano Banana cost tests use `estimate_google_cost` directly, not `generate_google`.

Add a temporary 4-arg shim by making nano_banana accept and ignore `resolution`:

```python
def _generate_via_nano_banana(client, model, prompt, resolution=None):
    """Generate image via Nano Banana (generate_content API).

    NOTE: resolution parameter accepted but not yet wired (Phase 4 task).

    Returns:
        bytes: Raw image bytes from the response.

    Raises:
        RuntimeError: If no image part is found in the response.
    """
    config = GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT'],
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith('image/'):
            return part.inline_data.data

    raise RuntimeError(
        f'No image data returned from Nano Banana model {model}. '
        'The response contained only text parts.'
    )
```

- [ ] **Step 5: Run tests**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/test_resolution_google.py -v
```

Expected: 9 passed (4 Imagen + 5 cost-pricing).

- [ ] **Step 6: Run all cloud tests to verify no regression**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/ -v
```

Expected: 22 from earlier phases + 9 new = 31 passed.

- [ ] **Step 7: Commit**

```bash
git add plugins/jack-tar-cloud/src/generate_cloud_image.py plugins/jack-tar-cloud/tests/test_resolution_google.py
git commit -m "feat(cloud): wire resolution + dual-pricing detection for Google Imagen (#59)"
```

### Phase 3 Verification Checkpoint

- [ ] **VERIFY:** `python3 -m pytest plugins/jack-tar-cloud/tests/ -v` shows 31 passed.
- [ ] **VERIFY:** `python3 -c "import os; os.environ['GOOGLE_APPLICATION_CREDENTIALS']='/x'; from src.generate_cloud_image import estimate_google_cost; print(estimate_google_cost('imagen-4.0-generate-001', '2K'))"` from `plugins/jack-tar-cloud/` prints `0.04` (Vertex flat).
- [ ] **VERIFY:** Same command without ADC env var prints `0.101` (Developer API token-based).

---

## Phase 4: Google Nano Banana (Flash + Pro)

**SDK PATH:** Use the path determined by Task 0's spike report. The code below shows the most likely shape (PATH-A or PATH-B); if Task 0 found PATH-C only, the implementation uses raw dict on `generate_content(generation_config={...})` instead.

### Task 7: Test Nano Banana resolution mapping

**Files:**
- Modify: `plugins/jack-tar-cloud/tests/test_resolution_google.py` (append)

- [ ] **Step 1: Append Nano Banana tests**

Append to `plugins/jack-tar-cloud/tests/test_resolution_google.py`:

```python
class TestNanoBananaResolution:
    def test_pro_4k_sets_image_config(self, mock_google_client, tmp_path):
        out = tmp_path / "out.png"
        generate_google(
            prompt="test", output_path=str(out),
            model="gemini-3-pro-image-preview",
            resolution="4K",
        )
        call_kwargs = mock_google_client.models.generate_content.call_args.kwargs
        config = call_kwargs["config"]
        # The image_config presence and value depends on SDK PATH chosen.
        # Per spike: image_config should resolve to a dict-or-typed object
        # whose image_size field equals "4K".
        if hasattr(config, "image_config"):
            ic = config.image_config
            if isinstance(ic, dict):
                assert ic.get("image_size") == "4K"
            else:
                assert ic.image_size == "4K"
        else:
            pytest.fail("config.image_config not present — SDK doesn't expose it")

    def test_pro_2k_works(self, mock_google_client, tmp_path):
        out = tmp_path / "out.png"
        generate_google(
            prompt="test", output_path=str(out),
            model="gemini-3-pro-image-preview",
            resolution="2K",
        )
        # Just verify the call succeeded; no exception raised.
        assert mock_google_client.models.generate_content.called

    def test_pro_512_raises(self, mock_google_client, tmp_path):
        out = tmp_path / "out.png"
        with pytest.raises(ProviderResolutionUnsupportedError) as excinfo:
            generate_google(
                prompt="test", output_path=str(out),
                model="gemini-3-pro-image-preview",
                resolution="512",
            )
        assert "1K" in excinfo.value.supported
        assert "512" not in excinfo.value.supported

    def test_flash_full_ladder(self, mock_google_client, tmp_path):
        out = tmp_path / "out.png"
        for res in ("512", "1K", "2K", "4K"):
            generate_google(
                prompt="test", output_path=str(out),
                model="gemini-3.1-flash-image-preview",
                resolution=res,
            )
        # All four should succeed
        assert mock_google_client.models.generate_content.call_count == 4

    def test_flash_unsupported_raises(self, mock_google_client, tmp_path):
        out = tmp_path / "out.png"
        with pytest.raises(ValueError):
            # 8K isn't in _VALID_RESOLUTIONS
            generate_google(
                prompt="test", output_path=str(out),
                model="gemini-3.1-flash-image-preview",
                resolution="8K",
            )
```

- [ ] **Step 2: Run tests, verify failures**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/test_resolution_google.py::TestNanoBananaResolution -v
```

Expected: All fail because `_generate_via_nano_banana` doesn't yet thread resolution into config.

### Task 8: Implement Nano Banana resolution support

**Files:**
- Modify: `plugins/jack-tar-cloud/src/generate_cloud_image.py` — `_generate_via_nano_banana`

**Reference:** Read `docs/spikes/2026-05-02-google-genai-image-config-spike.md` to confirm the chosen PATH before editing.

- [ ] **Step 1: Update `_generate_via_nano_banana` per spike PATH**

Find `def _generate_via_nano_banana(...)` and replace:

**If PATH-A (raw dict on typed config):**

```python
def _generate_via_nano_banana(client, model, prompt, resolution='1K'):
    """Generate image via Nano Banana (generate_content API) at given resolution.

    Returns:
        bytes: Raw image bytes from the response.

    Raises:
        RuntimeError: If no image part is found in the response.
    """
    config = GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT'],
        image_config={'image_size': resolution},
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith('image/'):
            return part.inline_data.data

    raise RuntimeError(
        f'No image data returned from Nano Banana model {model}. '
        'The response contained only text parts.'
    )
```

**If PATH-B (typed ImageConfig):**

```python
from google.genai.types import ImageConfig  # add to imports at top

def _generate_via_nano_banana(client, model, prompt, resolution='1K'):
    """Generate image via Nano Banana (generate_content API) at given resolution."""
    config = GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT'],
        image_config=ImageConfig(image_size=resolution),
    )
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith('image/'):
            return part.inline_data.data

    raise RuntimeError(
        f'No image data returned from Nano Banana model {model}. '
        'The response contained only text parts.'
    )
```

**If PATH-C (raw generation_config dict — SDK doesn't expose typed surface):**

```python
def _generate_via_nano_banana(client, model, prompt, resolution='1K'):
    """Generate image via Nano Banana (raw generation_config dict, SDK fallback)."""
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        generation_config={
            'response_modalities': ['IMAGE', 'TEXT'],
            'image_config': {'image_size': resolution},
        },
    )
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith('image/'):
            return part.inline_data.data
    raise RuntimeError(
        f'No image data returned from Nano Banana model {model}. '
        'The response contained only text parts.'
    )
```

- [ ] **Step 2: Run Nano Banana tests**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/test_resolution_google.py::TestNanoBananaResolution -v
```

Expected: 5 passed.

- [ ] **Step 3: Run all cloud tests**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/ -v
```

Expected: All previously passing tests still pass + 5 new = 36 passed.

- [ ] **Step 4: Commit**

```bash
git add plugins/jack-tar-cloud/src/generate_cloud_image.py plugins/jack-tar-cloud/tests/test_resolution_google.py
git commit -m "feat(cloud): wire resolution into Nano Banana Pro/Flash via PATH-<X> (#59)"
```

(Substitute the actual PATH letter in the commit message.)

### Phase 4 Verification Checkpoint

- [ ] **VERIFY:** `python3 -m pytest plugins/jack-tar-cloud/tests/ -v` shows 36 passed.
- [ ] **VERIFY:** `_generate_via_nano_banana` no longer just discards `resolution`; the config object passed to `generate_content` carries the requested image_size.
- [ ] **VERIFY:** The spike report's "Implementation impact" matches what was committed.

---

## Phase 5: FAL FLUX 2 Pro

### Task 9: Test FAL resolution mapping

**Files:**
- Create: `plugins/jack-tar-cloud/tests/test_resolution_fal.py`

- [ ] **Step 1: Write failing tests**

Create `plugins/jack-tar-cloud/tests/test_resolution_fal.py`:

```python
"""Tests for FAL FLUX 2 Pro resolution mapping in generate_fal."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from src.generate_cloud_image import (
    generate_fal,
    ProviderResolutionUnsupportedError,
)


@pytest.fixture
def mock_fal(monkeypatch):
    monkeypatch.setenv("FAL_KEY", "test-key")
    fake_result = {"images": [{"url": "https://fake.example/img.png"}]}
    fake_response = MagicMock()
    fake_response.content = b"\x89PNG\r\n\x1a\n" + b"x" * 100
    fake_response.raise_for_status = MagicMock()
    with patch("src.generate_cloud_image.fal_client.subscribe") as mock_subscribe:
        with patch("src.generate_cloud_image.requests.get") as mock_get:
            mock_subscribe.return_value = fake_result
            mock_get.return_value = fake_response
            yield mock_subscribe


class TestFALResolution:
    def test_1k_uses_existing_preset_when_no_image_size(self, mock_fal, tmp_path):
        out = tmp_path / "out.png"
        generate_fal(
            prompt="test", output_path=str(out),
            model="fal-ai/flux-2-pro",
            resolution="1K",
        )
        args = mock_fal.call_args.kwargs["arguments"]
        assert args["image_size"] == "landscape_16_9"  # default preset

    def test_2k_maps_to_2048_dict(self, mock_fal, tmp_path):
        out = tmp_path / "out.png"
        generate_fal(
            prompt="test", output_path=str(out),
            model="fal-ai/flux-2-pro",
            resolution="2K",
        )
        args = mock_fal.call_args.kwargs["arguments"]
        assert args["image_size"] == {"width": 2048, "height": 2048}

    def test_4k_raises_unsupported(self, mock_fal, tmp_path):
        out = tmp_path / "out.png"
        with pytest.raises(ProviderResolutionUnsupportedError) as excinfo:
            generate_fal(
                prompt="test", output_path=str(out),
                model="fal-ai/flux-2-pro",
                resolution="4K",
            )
        assert excinfo.value.supported == ["1K", "2K"]

    def test_512_raises_unsupported(self, mock_fal, tmp_path):
        out = tmp_path / "out.png"
        with pytest.raises(ProviderResolutionUnsupportedError):
            generate_fal(
                prompt="test", output_path=str(out),
                model="fal-ai/flux-2-pro",
                resolution="512",
            )

    def test_explicit_image_size_wins(self, mock_fal, tmp_path):
        out = tmp_path / "out.png"
        custom = {"width": 1024, "height": 768}
        generate_fal(
            prompt="test", output_path=str(out),
            model="fal-ai/flux-2-pro",
            resolution="2K",
            image_size=custom,
        )
        args = mock_fal.call_args.kwargs["arguments"]
        assert args["image_size"] == custom
```

- [ ] **Step 2: Run, verify failures**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/test_resolution_fal.py -v
```

Expected: All fail.

### Task 10: Implement FAL resolution support

**Files:**
- Modify: `plugins/jack-tar-cloud/src/generate_cloud_image.py:339-395` (`generate_fal`)

- [ ] **Step 1: Add FAL resolution mapping table**

Near the existing `_FAL_*` constants, add:

```python
# FAL FLUX 2 Pro caps at 2048x2048. Higher tiers raise.
_FAL_RESOLUTION_TO_IMAGE_SIZE = {
    'fal-ai/flux-2-pro': {
        '1K': 'landscape_16_9',  # existing preset (~1MP)
        '2K': {'width': 2048, 'height': 2048},
    },
    'fal-ai/flux-2-klein': {
        '1K': 'landscape_16_9',
    },
    'fal-ai/ideogram/v3': {
        '1K': 'landscape_16_9',
    },
}

_FAL_SUPPORTED_RESOLUTIONS = {
    'fal-ai/flux-2-pro': ['1K', '2K'],
    'fal-ai/flux-2-klein': ['1K'],
    'fal-ai/ideogram/v3': ['1K'],
}
```

- [ ] **Step 2: Replace `generate_fal`**

Find `def generate_fal(...)` (around line 339) and replace its body with:

```python
def generate_fal(prompt, output_path, **kwargs):
    """Generate an image using FAL.ai (FLUX.2 Pro, Klein, Ideogram, etc.).

    Auth: FAL_KEY environment variable.

    Args:
        prompt: Text prompt for image generation.
        output_path: Where to save the generated PNG.
        **kwargs: Optional arguments:
            model: FAL endpoint (default: 'fal-ai/flux-2-pro').
            resolution: '1K' | '2K' (FLUX 2 Pro caps at 2048x2048; Klein and
                Ideogram support 1K only). Default '1K'.
            image_size: Explicit FAL image_size (preset string OR
                {'width': W, 'height': H} dict). When provided, takes
                precedence over resolution.

    Returns:
        dict: {file_path, provider, model_used, cost_usd, status, resolution}

    Raises:
        ProviderNotConfiguredError: If FAL_KEY is not set.
        ProviderResolutionUnsupportedError: model doesn't support resolution.
    """
    if not os.environ.get('FAL_KEY'):
        raise ProviderNotConfiguredError(
            'FAL.ai not configured: FAL_KEY environment variable is not set. '
            'See research/04-cloud-api-setup-licensing.md section C for setup.'
        )

    model = kwargs.get('model', 'fal-ai/flux-2-pro')
    resolution = _normalise_resolution(kwargs.get('resolution', '1K'))

    # Determine image_size: explicit kwarg wins; otherwise resolve from resolution.
    if 'image_size' in kwargs:
        image_size = kwargs['image_size']
        if resolution != '1K':
            logger.warning(
                'FAL: explicit image_size=%r overrides resolution=%r.',
                image_size, resolution,
            )
    else:
        # Validate the resolution against per-model capability
        supported = _FAL_SUPPORTED_RESOLUTIONS.get(model, ['1K'])
        if resolution not in supported:
            raise ProviderResolutionUnsupportedError(
                provider='fal', model=model,
                requested=resolution, supported=supported,
            )
        # Map resolution -> image_size
        mapping = _FAL_RESOLUTION_TO_IMAGE_SIZE.get(model, {})
        if resolution not in mapping:
            raise ProviderResolutionUnsupportedError(
                provider='fal', model=model,
                requested=resolution, supported=list(mapping.keys()),
            )
        image_size = mapping[resolution]

    result = fal_client.subscribe(model, arguments={
        'prompt': prompt,
        'image_size': image_size,
        'output_format': 'png',
    })

    image_url = result['images'][0]['url']
    response = requests.get(image_url, timeout=30)
    response.raise_for_status()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_bytes(response.content)

    cost = estimate_fal_cost(model=model, image_size=image_size)
    logger.info(
        'FAL.ai image generated: %s (model: %s, resolution: %s, cost: $%.3f)',
        output_path, model, resolution, cost,
    )

    return {
        'file_path': str(output_path),
        'provider': 'fal',
        'model_used': model,
        'cost_usd': cost,
        'status': 'generated',
        'resolution': resolution,
    }
```

- [ ] **Step 3: Run tests**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/test_resolution_fal.py -v
```

Expected: 5 passed.

- [ ] **Step 4: All cloud tests**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/ -v
```

Expected: 41 passed (36 + 5).

- [ ] **Step 5: Commit**

```bash
git add plugins/jack-tar-cloud/src/generate_cloud_image.py plugins/jack-tar-cloud/tests/test_resolution_fal.py
git commit -m "feat(cloud): wire resolution into FAL FLUX 2 Pro (1K/2K) (#59)"
```

### Phase 5 Verification Checkpoint

- [ ] **VERIFY:** `python3 -m pytest plugins/jack-tar-cloud/tests/ -v` reports 41 passed.

---

## Phase 6: Top-Level Dispatch + Provider Discovery

### Task 11: Test top-level dispatch + discovery surface

**Files:**
- Create: `plugins/jack-tar-cloud/tests/test_resolution_dispatch.py`

- [ ] **Step 1: Write failing tests**

Create `plugins/jack-tar-cloud/tests/test_resolution_dispatch.py`:

```python
"""Tests for generate_cloud_image() resolution wiring + provider_discovery surface."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from src.generate_cloud_image import (
    generate_cloud_image,
    ProviderResolutionUnsupportedError,
)
from src.provider_discovery import discover_providers


class TestDispatch:
    def test_default_resolution_is_1k(self, monkeypatch, tmp_path):
        # Caller doesn't pass resolution; default 1K reaches provider.
        monkeypatch.setenv("FAL_KEY", "test")
        with patch("src.generate_cloud_image.fal_client.subscribe") as sub:
            sub.return_value = {"images": [{"url": "x"}]}
            with patch("src.generate_cloud_image.requests.get") as get:
                get.return_value.content = b"x"
                get.return_value.raise_for_status = MagicMock()
                result = generate_cloud_image(
                    prompt="test", provider="fal",
                    output_path=str(tmp_path / "out.png"),
                )
        assert result["resolution"] == "1K"

    def test_explicit_resolution_threads_through(self, monkeypatch, tmp_path):
        monkeypatch.setenv("FAL_KEY", "test")
        with patch("src.generate_cloud_image.fal_client.subscribe") as sub:
            sub.return_value = {"images": [{"url": "x"}]}
            with patch("src.generate_cloud_image.requests.get") as get:
                get.return_value.content = b"x"
                get.return_value.raise_for_status = MagicMock()
                result = generate_cloud_image(
                    prompt="test", provider="fal",
                    output_path=str(tmp_path / "out.png"),
                    resolution="2K",
                )
        assert result["resolution"] == "2K"

    def test_unsupported_resolution_propagates(self, monkeypatch, tmp_path):
        monkeypatch.setenv("FAL_KEY", "test")
        with pytest.raises(ProviderResolutionUnsupportedError):
            generate_cloud_image(
                prompt="test", provider="fal",
                output_path=str(tmp_path / "out.png"),
                resolution="4K",  # FLUX caps at 2K
            )


class TestProviderDiscoveryResolutions:
    def test_supported_resolutions_per_google_model(self):
        providers = discover_providers()
        google = providers.get("google", {})
        models = google.get("models", {})
        # Nano Banana Pro supports 1K/2K/4K (no 512)
        pro = models.get("gemini-3-pro-image-preview", {})
        assert pro.get("supported_resolutions") == ["1K", "2K", "4K"]
        # Nano Banana Flash supports the full ladder
        flash = models.get("gemini-3.1-flash-image-preview", {})
        assert flash.get("supported_resolutions") == ["512", "1K", "2K", "4K"]
        # Imagen Standard supports 1K/2K
        std = models.get("imagen-4.0-generate-001", {})
        assert std.get("supported_resolutions") == ["1K", "2K"]
        # Imagen Fast supports 1K only
        fast = models.get("imagen-4.0-fast-generate-001", {})
        assert fast.get("supported_resolutions") == ["1K"]

    def test_supported_resolutions_per_openai_model(self):
        providers = discover_providers()
        openai_p = providers.get("openai", {})
        models = openai_p.get("models", {})
        gpt = models.get("gpt-image-1.5", {})
        assert gpt.get("supported_resolutions") == ["1K"]

    def test_supported_resolutions_per_fal_model(self):
        providers = discover_providers()
        fal_p = providers.get("fal", {})
        models = fal_p.get("models", {})
        flux = models.get("fal-ai/flux-2-pro", {})
        assert flux.get("supported_resolutions") == ["1K", "2K"]
```

- [ ] **Step 2: Run, verify failures**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/test_resolution_dispatch.py -v
```

Expected: dispatch tests pass (already wired in Phases 2-5); discovery tests fail (provider_discovery doesn't yet expose `supported_resolutions`).

### Task 12: Wire resolution kwarg into generate_cloud_image dispatcher

**Files:**
- Modify: `plugins/jack-tar-cloud/src/generate_cloud_image.py:406-end` (`generate_cloud_image`)

- [ ] **Step 1: Update `generate_cloud_image` signature**

Find the existing `generate_cloud_image` at the bottom of the file. Replace with:

```python
def generate_cloud_image(prompt, provider, output_path, *, resolution='1K', **kwargs):
    """Generate an image using the specified cloud provider at the requested resolution.

    Args:
        prompt: Text prompt for image generation.
        provider: Provider name ('openai', 'google', 'fal').
        output_path: Where to save the generated image.
        resolution: '512' | '1K' | '2K' | '4K' (case-insensitive, default '1K').
            Per-provider/model support varies; ProviderResolutionUnsupportedError
            is raised for unsupported combinations. See provider_discovery for
            per-model capability.
        **kwargs: Provider-specific arguments (size, model, image_size, etc.).
            If a kwarg conflicts with `resolution` semantics, the kwarg wins
            with a logger warning (provider-specific).

    Returns:
        dict: Result from the provider function. Includes 'resolution' field.

    Raises:
        ValueError: If provider is unknown or resolution string is invalid.
        ProviderNotConfiguredError: If provider credentials are missing.
        ProviderResolutionUnsupportedError: provider/model can't honour resolution.
    """
    if provider not in _PROVIDERS:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Available: {list(_PROVIDERS)}"
        )
    return _PROVIDERS[provider](
        prompt, output_path, resolution=resolution, **kwargs,
    )
```

- [ ] **Step 2: Run dispatch tests**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/test_resolution_dispatch.py::TestDispatch -v
```

Expected: 3 dispatch tests pass.

- [ ] **Step 3: Extend provider_discovery.py**

Edit `plugins/jack-tar-cloud/src/provider_discovery.py`. Find `_PROVIDER_DEFAULTS` (line ~30) and update each model entry to include `supported_resolutions`.

The existing structure looks like:

```python
_PROVIDER_DEFAULTS = {
    'openai': {
        'env_var': 'OPENAI_API_KEY',
        'model': 'gpt-image-1.5',
        ...
    },
    ...
}
```

Replace with a richer model-keyed structure that includes supported resolutions. Since the existing `_PROVIDER_DEFAULTS` may not have a per-model nested shape, add a new `_MODEL_RESOLUTIONS` constant and have `discover_providers()` merge it into the output:

```python
# Per-model supported resolutions — exposed via discover_providers().
_PROVIDER_MODEL_RESOLUTIONS = {
    'openai': {
        'gpt-image-1.5': ['1K'],
    },
    'google': {
        'imagen-4.0-fast-generate-001': ['1K'],
        'imagen-4.0-generate-001': ['1K', '2K'],
        'imagen-4.0-ultra-generate-001': ['1K', '2K'],
        'gemini-3.1-flash-image-preview': ['512', '1K', '2K', '4K'],
        'gemini-3-pro-image-preview': ['1K', '2K', '4K'],
    },
    'fal': {
        'fal-ai/flux-2-pro': ['1K', '2K'],
        'fal-ai/flux-2-klein': ['1K'],
        'fal-ai/ideogram/v3': ['1K'],
    },
}
```

Then in `discover_providers()`, add a final loop that attaches a `models` dict to each provider's result:

```python
def discover_providers(config_path='provider_config.json'):
    """... (existing docstring) ...

    Each provider entry now includes a 'models' dict mapping model name to
    {'supported_resolutions': [...]} so callers can filter resolution-tier
    requests against capability before dispatch.
    """
    # ... existing logic that builds the result dict ...

    # Attach per-model resolution capability metadata
    for provider_name, models in _PROVIDER_MODEL_RESOLUTIONS.items():
        if provider_name in result:
            result[provider_name]['models'] = {
                model: {'supported_resolutions': resolutions}
                for model, resolutions in models.items()
            }

    return result
```

(Adjust the variable name `result` if the existing implementation uses a different name. Read the function first to match the local style.)

- [ ] **Step 4: Run discovery tests**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/test_resolution_dispatch.py::TestProviderDiscoveryResolutions -v
```

Expected: 3 discovery tests pass.

- [ ] **Step 5: Run all cloud tests**

```bash
python3 -m pytest plugins/jack-tar-cloud/tests/ -v
```

Expected: 47 passed (41 + 6).

- [ ] **Step 6: Commit**

```bash
git add plugins/jack-tar-cloud/src/generate_cloud_image.py plugins/jack-tar-cloud/src/provider_discovery.py plugins/jack-tar-cloud/tests/test_resolution_dispatch.py
git commit -m "feat(cloud): top-level dispatch + provider_discovery resolutions (#59)"
```

### Phase 6 Verification Checkpoint

- [ ] **VERIFY:** `python3 -m pytest plugins/jack-tar-cloud/tests/ -v` reports 47 passed.
- [ ] **VERIFY:** Existing `test_plugin_imports.py` still passes — discovery output shape didn't break.
- [ ] **VERIFY:** A no-args call to `generate_cloud_image('prompt', 'fal', '/tmp/x.png')` succeeds with `result['resolution'] == '1K'`.

---

## Phase 7: Plugin Version Bump

### Task 13: Bump plugin version 1.1.0 → 1.2.0

**Files:**
- Modify: `plugins/jack-tar-cloud/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Bump plugin manifest**

Edit `plugins/jack-tar-cloud/.claude-plugin/plugin.json`. Change `"version": "1.1.0"` to `"version": "1.2.0"`.

- [ ] **Step 2: Sync marketplace manifest**

Edit `.claude-plugin/marketplace.json`. Find the `jack-tar-cloud` entry and update its `"version"` from `"1.1.0"` to `"1.2.0"`.

- [ ] **Step 3: Verify both files match**

```bash
grep -A 1 '"name": "jack-tar-cloud"' .claude-plugin/marketplace.json
grep '"version"' plugins/jack-tar-cloud/.claude-plugin/plugin.json
```

Expected: both show `1.2.0`.

- [ ] **Step 4: Commit**

```bash
git add plugins/jack-tar-cloud/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore(cloud): bump plugin version 1.1.0 -> 1.2.0 (resolution control, #59)"
```

### Phase 7 Verification Checkpoint

- [ ] **VERIFY:** Both manifest files show 1.2.0.
- [ ] **VERIFY:** All tests still pass: `python3 -m pytest plugins/jack-tar-cloud/tests/ -v` → 47 passed.

---

## Phase 8: Smoke Test (Manual Gate)

This phase is the merge gate per Issue #59 §6. Each step is manual; the agent records observations.

### Task 14: Run the Jack Tar smoke-test ladder

**Files:**
- Create: `output/smoke-test-jack-tar-on-a-page/` directory tree
- Create: `docs/superpowers/dogfooding/2026-MM-DD-resolution-smoke-test.md` (substitute today's date)

**Budget cap:** $3.00 total. Expected spend: ~$0.73.

- [ ] **Step 1: Set up output directory**

```bash
cd /Users/stevejones/Documents/Development/jack-tar-deckhand-resolution
mkdir -p output/smoke-test-jack-tar-on-a-page/{ollama,flash-1k,flash-4k,pro-1k,pro-4k}
```

- [ ] **Step 2: Initial Ollama iteration (free, ~5 rounds)**

Use the existing `jack-tar-ollama:image` skill to iterate on the Jack Tar mascot infographic prompt. Save each iteration to `output/smoke-test-jack-tar-on-a-page/ollama/iter-NN.png` with the prompt text in `output/smoke-test-jack-tar-on-a-page/ollama/iter-NN-prompt.md`. Goal: get the composition and subject right at no cost.

- [ ] **Step 3: Nano Banana Flash 1K iteration ($0.067 × ~3)**

Using the proven prompt from Step 2, generate at Flash 1K via:

```bash
python3 -c "
from src.generate_cloud_image import generate_cloud_image
result = generate_cloud_image(
    prompt='<your refined prompt>',
    provider='google',
    output_path='output/smoke-test-jack-tar-on-a-page/flash-1k/iter-01.png',
    model='gemini-3.1-flash-image-preview',
    resolution='1K',
)
print(result)
" 2>&1
```

(Adjust PYTHONPATH or working directory as needed for the cloud plugin.)

Iterate on the prompt up to 3 times based on output quality. Record each prompt and reviewer verdict.

- [ ] **Step 4: Flash 4K shot ($0.151)**

Generate the proven prompt at Flash 4K:

```bash
python3 -c "
from src.generate_cloud_image import generate_cloud_image
result = generate_cloud_image(
    prompt='<final prompt from step 3>',
    provider='google',
    output_path='output/smoke-test-jack-tar-on-a-page/flash-4k/render.png',
    model='gemini-3.1-flash-image-preview',
    resolution='4K',
)
print(result)
"
```

Verify the output is 4096×4096:

```bash
python3 -c "
from PIL import Image
img = Image.open('output/smoke-test-jack-tar-on-a-page/flash-4k/render.png')
print(f'Dimensions: {img.size}')
"
```

Expected: `(4096, 4096)`.

- [ ] **Step 5: Nano Banana Pro 1K pre-test shot ($0.134)**

Pre-test the prompt at Pro 1K before committing to 4K:

```bash
python3 -c "
from src.generate_cloud_image import generate_cloud_image
result = generate_cloud_image(
    prompt='<final prompt>',
    provider='google',
    output_path='output/smoke-test-jack-tar-on-a-page/pro-1k/render.png',
    model='gemini-3-pro-image-preview',
    resolution='1K',
)
print(result)
"
```

If Pro 1K reveals prompt issues that wouldn't appear at 4K, refine and re-shoot. If clean, proceed.

- [ ] **Step 6: Nano Banana Pro 4K final hero shot ($0.24)**

```bash
python3 -c "
from src.generate_cloud_image import generate_cloud_image
result = generate_cloud_image(
    prompt='<final prompt>',
    provider='google',
    output_path='output/smoke-test-jack-tar-on-a-page/pro-4k/render.png',
    model='gemini-3-pro-image-preview',
    resolution='4K',
)
print(result)
"
```

Verify dimensions match 4096×4096 and the output file is non-empty (>1MB for a 4K PNG).

- [ ] **Step 7: Write the dogfood report**

Create `docs/superpowers/dogfooding/<TODAY>-resolution-smoke-test.md` (substitute today's date in YYYY-MM-DD format):

```markdown
# Resolution Smoke Test — Jack Tar on a Page

**Date:** <YYYY-MM-DD>
**Issue:** #59 §6 (manual gate)
**Total spend:** $X.XX (cap was $3.00)
**Verdict:** GO | REVISE | STOP

## Subject
"Jack Tar on a page" — project mascot infographic, one-page visual summary.

## Ladder results

| Stage | Model | Resolution | Iterations | Spend | Outcome |
|---|---|---|---|---|---|
| Ollama | <model tag> | 1024×576 | <N> | $0 | ... |
| Flash 1K | gemini-3.1-flash-image-preview | 1K | <N> | $X.XX | ... |
| Flash 4K | gemini-3.1-flash-image-preview | 4K | 1 | $0.151 | ... |
| Pro 1K | gemini-3-pro-image-preview | 1K | 1 | $0.134 | ... |
| Pro 4K | gemini-3-pro-image-preview | 4K | 1 | $0.24 | ... |

## Prompt evolution
<paste the prompt at each stage; show how feedback drove changes>

## Flash 4K vs Pro 4K — quality comparison
<honest assessment: at $0.151 vs $0.24, is Flash 4K close enough? where does Pro 4K visibly win?>

## Findings / lessons
- Cross-tier prompt drift: <observations>
- File size deltas: 1K vs 4K
- Reviewer behaviour at higher resolutions
- Anything surprising

## Conclusion
The resolution control plumbing works end-to-end. <Verdict and rationale.>
```

- [ ] **Step 8: Commit smoke test artefacts**

```bash
git add output/smoke-test-jack-tar-on-a-page/ docs/superpowers/dogfooding/<TODAY>-resolution-smoke-test.md
git commit -m "test(cloud): smoke test — Jack Tar 5-step resolution ladder validates 4K plumbing (#59)"
```

### Phase 8 Verification Checkpoint

- [ ] **VERIFY:** `output/smoke-test-jack-tar-on-a-page/` contains all 5 stage subdirectories with renders.
- [ ] **VERIFY:** `pro-4k/render.png` is 4096×4096.
- [ ] **VERIFY:** Total spend (sum of cost_usd from each generate result) is under $3.00.
- [ ] **VERIFY:** Dogfood report has actual content in every section, not placeholders.
- [ ] **VERIFY:** Verdict line is filled (GO | REVISE | STOP).

---

## Phase 9: Speaker Review Gate

This is a manual checkpoint, not an executable task. The implementer hands off to the speaker.

- [ ] **Hand-off:** present to the speaker:
  - All commits on `feat/cloud-resolution-control` (run `git log --oneline main..HEAD`)
  - Test count: 47 passing in `plugins/jack-tar-cloud/tests/`
  - Smoke-test artefacts at `output/smoke-test-jack-tar-on-a-page/`
  - Dogfood report at `docs/superpowers/dogfooding/<TODAY>-resolution-smoke-test.md`

- [ ] **Speaker reviews:** GO / REVISE / STOP.

- [ ] **On GO:** open the PR.

```bash
git push -u origin feat/cloud-resolution-control
gh pr create --title "feat(cloud): wire per-provider resolution parameters into provider functions (#59)" --body "$(cat <<'EOF'
Closes #59. Part of EPIC #58.

## What
Adds a unified `resolution` parameter to `generate_cloud_image()` routing
1K/2K/4K to each provider's native API field. Plugin-internal only —
SKILL.md surface and render_funnel integration land in #60.

## Why
Three providers (Google Imagen 4 2K, Google Nano Banana Pro 4K, FAL FLUX 2 Pro 2K)
support higher resolutions than we currently expose. The deckhand pipeline
cannot escalate to 2K/4K even when a slide warrants it.

## Test coverage
- 47 unit tests passing (covering 4 providers, exception shape, dual pricing)
- Manual smoke test: Jack Tar mascot through Ollama → Flash 1K → Flash 4K
  → Pro 1K → Pro 4K ladder. Total spend $X.XX (cap $3.00). Pro 4K
  produces 4096×4096 output as expected.

## SDK spike outcome
PATH-<X> chosen for google-genai image_config wiring. See
`docs/spikes/2026-05-02-google-genai-image-config-spike.md`.

## Out of scope
- SKILL.md updates → #60
- render_funnel.py 2K/4K stages → #60
- Cross-tier refinement loop integration → #60
- Recraft V4 raster as first-class provider → #61

## Spec
`docs/superpowers/specs/2026-05-02-cloud-resolution-control-design.md`
EOF
)"
```

- [ ] **On REVISE:** capture the speaker's specific findings, address them, re-run relevant tests, request re-review.

- [ ] **On STOP:** discuss the structural concern with the speaker; the branch is preserved for future revisit.

### Phase 9 Verification Checkpoint

- [ ] **VERIFY:** PR opened (or REVISE/STOP path documented in conversation).
- [ ] **VERIFY:** PR body fields filled with actual values (test count, smoke spend, SDK PATH).

---

## Self-Review Notes

Spec coverage check:
- §3 Interface specification → Tasks 1, 2 (helper + exception); Tasks 4/6/8/10/12 (per-provider plumbing)
- §4 Per-provider mapping → Tasks 4 (OpenAI), 6 (Imagen), 8 (Nano Banana), 10 (FAL)
- §5 Cost model + dual-pricing → Task 6
- §6 SDK spike → Task 0 (gates everything)
- §7 Test strategy → Tests written in every task; verifies +25-35 new tests target (actual: 36 new — 11 helpers + 7 OpenAI + 9 Google Imagen + 5 Google Nano Banana + 5 FAL + 6 dispatch/discovery — adjust if your run counts differ)
- §8 Smoke test → Task 14
- §9 Backward compatibility → covered by "default behaviour unchanged" tests
- §10 Out of scope → respected throughout
- §12 Implementation plan hand-off → this document

Type / signature consistency:
- `_normalise_resolution(resolution: str) -> str` consistent across uses
- `ProviderResolutionUnsupportedError(provider, model, requested, supported)` four-arg constructor consistent
- All provider functions: `*, resolution='1K'` keyword-only with default '1K'
- Return dict shape gains `'resolution': resolution` key consistently
