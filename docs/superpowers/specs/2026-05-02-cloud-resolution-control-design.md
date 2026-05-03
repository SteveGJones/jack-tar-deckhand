# Cloud Resolution Control — Design Specification

**Date:** 2026-05-02
**Status:** Draft — pending speaker review.
**EPIC:** [#58 — Cloud image resolution control — 2K / 4K support across providers](https://github.com/SteveGJones/jack-tar-deckhand/issues/58)
**Issue:** [#59 — feat(jack-tar-cloud): wire per-provider resolution parameters into provider functions](https://github.com/SteveGJones/jack-tar-deckhand/issues/59)
**Successor work:** Issue #60 (deckhand integration + skill drift) and #61 (Recraft promotion) close the EPIC after this lands.
**Branch:** `feat/cloud-resolution-control` (worktree at `../jack-tar-deckhand-resolution`)

---

## 1. Overview

Add a unified `resolution` parameter to `generate_cloud_image()` so callers can request `"1K"` / `"2K"` / `"4K"` outputs from any cloud provider that supports them, with the parameter mapping cleanly to each provider's native API field. Today the four registered providers (OpenAI, Google Imagen, Google Nano Banana, FAL FLUX) all default to roughly 1K outputs because the per-provider resolution fields are never set, leaving the recently-shipped Nano Banana Pro 4K (4096×4096) and Imagen 4 2K (2048×2048) capabilities unreachable from the deckhand pipeline.

This work is **plugin-internal**. It changes only `plugins/jack-tar-cloud/src/`, adds tests, and updates plugin metadata. SKILL.md surface, `render_funnel.py` integration, and image-router upgrade decisions are explicitly out of scope — those land in #60.

The deliverable also includes a real-world smoke test (Issue #59 §6) that exercises the full Ollama → Flash 1K → Flash 4K → Pro 1K → Pro 4K escalation ladder on the Jack Tar mascot infographic, validating that the plumbing produces correct output at each tier and that the cross-tier prompt refinement loop benefits from the higher-resolution targets.

---

## 2. Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Parameter name | `resolution` | Reads naturally; doesn't collide with provider-specific `size` / `image_size` / `aspect_ratio` kwargs. |
| Accepted values | `"512"` | `"1K"` | `"2K"` | `"4K"` (case-insensitive on input, normalised to uppercase-K on output) | Matches Google's `imageConfig.imageSize` vocabulary exactly (uppercase K is required by their API). The `"512"` tier exists only on Nano Banana Flash; included for completeness rather than defaulting to it. |
| Default value | `"1K"` | Preserves existing behaviour. Callers that don't pass `resolution=` see no change. |
| Provider/resolution incompatibility | Raise `ProviderResolutionUnsupportedError(provider, model, resolution, supported)` | Silent fall-back to nearest tier would surprise callers (especially for cost). Explicit error with actionable supported-tier list is safer. |
| Precedence vs provider-specific kwargs | If caller passes BOTH `resolution=` AND a provider-specific size kwarg (`size=`, `image_size=`), provider-specific wins, with a logger warning. | Power-users can keep their existing call sites unchanged. The `resolution` parameter is the high-level abstraction; explicit provider-specific overrides are still honoured. |
| Cost-table dispatch | Cost lookup keys on (provider, model, resolution). For Google Imagen, additionally on auth tier (Vertex flat vs Developer API token). | Imagen 4 has dual pricing depending on which Google API the SDK reaches. The `google-genai` SDK auto-selects the backend by env var; the cost function must mirror that logic to bill correctly. |
| Backend detection for Imagen pricing | Sniff `os.environ` for `GOOGLE_APPLICATION_CREDENTIALS` (→ Vertex flat) vs `GOOGLE_API_KEY` (→ Developer API token). | The same pattern already exists in `generate_google()` for client construction; we extend it to cost estimation. No new dependency or config file. |
| Error-type scope | New module-level exception class, not stdlib `ValueError`. | Callers may want to catch resolution-unsupported specifically (to retry at lower tier) without catching unrelated value errors. |
| SDK approach for `google-genai` | Use typed `ImageConfig` if the installed SDK exposes it; fall back to raw `image_config={"image_size": "4K"}` dict if the SDK is older. **A spike (Task 0 in the plan) verifies which path is needed before any other code lands.** | The Nano Banana Pro 4K capability shipped in March 2026 and the SDK's typed surface lags real API support. Without the spike we risk writing code against a field that doesn't exist in the pinned SDK version. |
| Resolution capability metadata | Each provider/model exposes `supported_resolutions: list[str]` via `provider_discovery.py`. | Lets `image_router.py` (in #60) make routing decisions WITHOUT calling the provider — purely from the discovery surface. |
| Aspect ratio interaction | `resolution` and `aspect_ratio` are independent. `aspect_ratio` semantics unchanged. Resolution defines the longest-dimension target; aspect ratio still controls shape. | Matches Google's API model where `imageConfig.imageSize` and `imageConfig.aspectRatio` are independent fields. Avoids forcing callers to choose. |
| FAL 4K fall-back | FAL FLUX 2 Pro caps at 2048². Raise `ProviderResolutionUnsupportedError` for `"4K"` on FAL — DO NOT silently composite or upscale. | Upscaling is a different operation with different cost and quality. Keeping the abstraction honest. (Recraft's Creative Upscale 4K path lands in #61, not here.) |

---

## 3. Interface Specification

### 3.1 Public function signature

```python
# plugins/jack-tar-cloud/src/generate_cloud_image.py

def generate_cloud_image(
    prompt: str,
    provider: str,
    output_path: str | Path,
    *,
    resolution: str = "1K",
    **kwargs,
) -> dict:
    """Generate an image via the named cloud provider at the requested resolution.

    Args:
        prompt: text prompt for image generation.
        provider: 'openai' | 'google' | 'fal' (Recraft raster lands in #61).
        output_path: where to save the generated image.
        resolution: '512' | '1K' | '2K' | '4K' (case-insensitive; normalised
            to uppercase). Default '1K' preserves prior behaviour.
        **kwargs: provider-specific arguments passed through. If a kwarg
            conflicts with `resolution` (e.g. an explicit `size=` for OpenAI),
            the kwarg wins and a warning is logged.

    Returns:
        dict with keys: file_path, provider, model_used, cost_usd, status,
        resolution (the actual resolution used).

    Raises:
        ValueError: unknown provider.
        ProviderNotConfiguredError: missing credentials.
        ProviderResolutionUnsupportedError: provider/model cannot honour
            the requested resolution. Exception carries the closest
            supported tier so the caller can retry.
    """
```

### 3.2 New exception class

```python
class ProviderResolutionUnsupportedError(ValueError):
    """Raised when a provider/model combination cannot honour the requested resolution."""

    def __init__(
        self,
        provider: str,
        model: str,
        requested: str,
        supported: list[str],
    ):
        self.provider = provider
        self.model = model
        self.requested = requested
        self.supported = supported
        super().__init__(
            f"{provider}/{model} does not support resolution={requested!r}. "
            f"Supported: {supported}. Retry with one of those, or pick a "
            f"different model."
        )
```

### 3.3 Resolution normalisation

```python
_VALID_RESOLUTIONS = ("512", "1K", "2K", "4K")

def _normalise_resolution(resolution: str) -> str:
    """Case-fold and validate. '1k' -> '1K'. '512' -> '512'."""
    if not isinstance(resolution, str):
        raise TypeError(f"resolution must be str, got {type(resolution).__name__}")
    upper = resolution.strip().upper()
    if upper in {"1K", "2K", "4K"}:
        return upper
    if upper == "512" or resolution.strip() == "512":
        return "512"
    raise ValueError(
        f"resolution={resolution!r} not recognised. "
        f"Valid values: {_VALID_RESOLUTIONS}"
    )
```

---

## 4. Per-Provider Mapping

### 4.1 OpenAI (`gpt-image-1.5`)

| `resolution` | OpenAI `size` | Behaviour |
|---|---|---|
| `"1K"` | `"1024x1024"` (or honour caller's explicit `size=`) | Default. |
| `"2K"` | — | Raise `ProviderResolutionUnsupportedError(supported=["1K"])`. gpt-image-1.5 caps at 1536×1024 (~1.5 MP). |
| `"4K"` | — | Same. |
| `"512"` | — | Same. (OpenAI doesn't expose 512.) |

If caller passes `size="1536x1024"` explicitly alongside `resolution="1K"`, the explicit size wins.

### 4.2 Google Imagen (Standard / Ultra)

| `resolution` | `GenerateImagesConfig` field | Cost (Vertex flat / Dev API token) |
|---|---|---|
| `"1K"` | `image_size="1K"` (default; current behaviour) | Standard $0.04 / token-based ~$0.04 |
| `"2K"` | `image_size="2K"` | Standard $0.04 (uniform within tier on Vertex) / **~$0.101** (token-based on Dev API) |
| `"4K"` | — | Raise `ProviderResolutionUnsupportedError(supported=["1K", "2K"])` |
| `"512"` | — | Same. (Imagen doesn't expose 512.) |

`imagen-4.0-fast-generate-001` only supports `"1K"`; raise on `"2K"`.

### 4.3 Google Nano Banana Pro (`gemini-3-pro-image-preview`)

| `resolution` | `image_config.image_size` | Cost |
|---|---|---|
| `"1K"` | `"1K"` | $0.134 |
| `"2K"` | `"2K"` | $0.134 |
| `"4K"` | `"4K"` | $0.24 |
| `"512"` | — | Raise (Pro doesn't support 512). |

### 4.4 Google Nano Banana Flash (`gemini-3.1-flash-image-preview`)

Full ladder supported.

| `resolution` | `image_config.image_size` | Cost |
|---|---|---|
| `"512"` | `"512"` | $0.045 |
| `"1K"` | `"1K"` | $0.067 |
| `"2K"` | `"2K"` | $0.101 |
| `"4K"` | `"4K"` | $0.151 |

### 4.5 FAL FLUX 2 Pro (`fal-ai/flux-2-pro`)

| `resolution` | FAL `image_size` | Cost |
|---|---|---|
| `"1K"` | preset (existing behaviour) | $0.030 + tiered MP |
| `"2K"` | `{"width": 2048, "height": 2048}` | ~$0.075 ($0.030 + 3MP × $0.015) |
| `"4K"` | — | Raise `ProviderResolutionUnsupportedError(supported=["1K", "2K"])`. FLUX 2 Pro caps at 2048². |
| `"512"` | — | Raise (no 512 preset path). |

If caller passes `image_size=` explicitly, that wins over the `resolution`-derived dict.

---

## 5. Cost Model

`estimate_<provider>_cost()` functions are extended to accept `resolution=` and return the right tier. For Google specifically, `estimate_google_cost()` also detects which backend is in use and bills accordingly:

```python
def estimate_google_cost(model: str, resolution: str = "1K") -> float:
    """Return USD cost for a Google image generation call.

    For Imagen models, billing depends on the auth tier:
      - GOOGLE_APPLICATION_CREDENTIALS set -> Vertex AI flat per-image pricing
      - Otherwise (GOOGLE_API_KEY only)    -> Gemini Developer API token-based

    Nano Banana models bill identically across both tiers (per-image pricing).
    """
    if model in _NANO_BANANA_MODELS:
        return _NANO_BANANA_COSTS[(model, resolution)]
    if model in _IMAGEN_MODELS:
        backend = "vertex" if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") else "developer"
        return _IMAGEN_COSTS[(model, resolution, backend)]
    raise ValueError(f"Unknown Google model: {model}")
```

The cost-table constants are maintained in `generate_cloud_image.py` alongside the existing `_OPENAI_COSTS` etc. Source citations live in code comments referencing this spec.

---

## 6. SDK Spike (Task 0 — Implementation Gate)

**This MUST run before any other implementation work.** Result determines the code shape for the Google provider functions.

### 6.1 The risk

The `google-genai` SDK exposes typed config objects (`GenerateImagesConfig`, `GenerateContentConfig`). Whether those objects expose an `image_config` field or `image_size` field for the Nano Banana 4K capability depends on the SDK version. The capability shipped to the Gemini API in early 2026; the typed SDK surface may lag.

### 6.2 Spike protocol

```python
# spike: does the installed SDK support image_config?
from google import genai
from google.genai.types import GenerateContentConfig

# Test 1: typed surface
try:
    cfg = GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT'],
        image_config={'image_size': '4K'},  # raw dict on a typed config
    )
    print("PATH-A: SDK accepts image_config as dict on typed config")
except TypeError:
    print("PATH-A: typed config rejects image_config")

# Test 2: native typed ImageConfig
try:
    from google.genai.types import ImageConfig
    cfg = GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT'],
        image_config=ImageConfig(image_size='4K'),
    )
    print("PATH-B: SDK has typed ImageConfig")
except (ImportError, TypeError) as e:
    print(f"PATH-B: not available — {e}")

# Test 3: raw dict via generation_config kwarg
try:
    client = genai.Client()
    response = client.models.generate_content(
        model='gemini-3-pro-image-preview',
        contents='a small test image of a red square',
        generation_config={'image_config': {'image_size': '1K'}},
    )
    # If this returns image bytes at all, the raw-dict path works.
    print("PATH-C: raw generation_config dict works")
except Exception as e:
    print(f"PATH-C: failed — {e}")
```

### 6.3 Decision matrix

| Outcome | Action |
|---|---|
| PATH-B works (typed `ImageConfig` available) | Use it. Cleanest code, type-safe. |
| PATH-A works but PATH-B doesn't | Use PATH-A (dict on typed config). Document SDK version pin. |
| Only PATH-C works | Use raw `generation_config` dict throughout. Add an SDK upgrade backlog item. |
| All fail | Either bump SDK pin or fall back to raw HTTP REST call. Surface to spec for re-design. |

The spike runs in <5 minutes. Result is recorded as a comment in `generate_cloud_image.py` near the Nano Banana code path AND in the implementation plan's task-0 completion note.

### 6.4 If the spike fails

If none of the three paths work with the currently-pinned `google-genai`:

1. Try `pip install google-genai --upgrade` and re-run the spike.
2. If the upgraded version works, pin to that version in `pyproject.toml` for `jack-tar-cloud` and document the bump.
3. If even the latest version doesn't expose the capability, this issue is blocked on Google. Surface to user, decide whether to raw-HTTP it or wait.

---

## 7. Test Strategy

### 7.1 Unit tests (mock SDK calls)

| Test | Provider | Scenarios |
|---|---|---|
| `test_resolution_normalisation` | n/a | `"1k"` → `"1K"`, `"4K"` → `"4K"`, `"foo"` raises ValueError, `512` (int) raises TypeError |
| `test_openai_resolution_passthrough` | OpenAI | `"1K"` calls SDK with `size="1024x1024"`; `"2K"` raises; explicit `size=` overrides |
| `test_imagen_resolution_passthrough` | Google Imagen | `"1K"` and `"2K"` set `image_size`; `"4K"` raises; Fast model raises on `"2K"` |
| `test_nano_banana_pro_resolution` | Google Nano Banana Pro | `"1K"`/`"2K"`/`"4K"` set `imageConfig.imageSize`; `"512"` raises |
| `test_nano_banana_flash_resolution` | Google Nano Banana Flash | full `"512"`/`"1K"`/`"2K"`/`"4K"` ladder works |
| `test_fal_resolution_passthrough` | FAL FLUX 2 Pro | `"1K"` uses preset; `"2K"` uses `{width:2048, height:2048}`; `"4K"` raises |
| `test_resolution_unsupported_error_shape` | all | `ProviderResolutionUnsupportedError` carries provider, model, requested, supported |
| `test_default_behaviour_unchanged` | all | Calls without `resolution=` produce identical kwargs to current code |
| `test_explicit_kwarg_wins` | OpenAI, FAL | `size=` / `image_size=` overrides `resolution`; warning logged |

### 7.2 Cost estimation tests

| Test | Coverage |
|---|---|
| `test_nano_banana_pro_cost_table` | All 3 resolutions return the documented prices |
| `test_nano_banana_flash_cost_table` | All 4 resolutions including 512 |
| `test_imagen_cost_vertex_backend` | Mock env var → flat pricing returned |
| `test_imagen_cost_developer_backend` | Mock env var → token-based pricing returned |
| `test_fal_pro_2k_cost` | 2K returns ~$0.075 from existing tiered formula |

### 7.3 Provider discovery tests

```python
def test_provider_discovery_reports_resolutions():
    providers = discover_providers()
    assert "1K" in providers["google"]["models"]["gemini-3-pro-image-preview"]["supported_resolutions"]
    assert "4K" in providers["google"]["models"]["gemini-3-pro-image-preview"]["supported_resolutions"]
    assert "4K" not in providers["openai"]["models"]["gpt-image-1.5"]["supported_resolutions"]
```

### 7.4 Targets

- **Existing 12 cloud + 40 cross-plugin tests pass unchanged.**
- **+25-35 new tests** in `plugins/jack-tar-cloud/tests/`.
- All SDK calls mocked. No live API hits in unit tests.

---

## 8. Smoke Test (Manual Gate)

Per Issue #59 §6, a real-world smoke test is a merge gate. The test:

1. Subject: "Jack Tar on a page" infographic — project mascot on a one-page visual summary.
2. Budget cap: $3.00 (Max contract; budget is for spiral protection, not realistic spend — expected ~$0.73).
3. Ladder: Ollama (free, ~5 iterations) → Nano Banana Flash 1K (3 iterations, $0.067 each) → Flash 4K (1 shot, $0.151) → Pro 1K (1 shot, $0.134) → Pro 4K (1 shot, $0.24).
4. Cross-tier prompt refinement at each stage drives prompt evolution from cheap proof-of-prompt to final 4K hero render.
5. Artefacts committed:
   - `output/smoke-test-jack-tar-on-a-page/` containing all images at each tier, prompt evolution log, reviewer verdicts.
   - `docs/superpowers/dogfooding/2026-MM-DD-resolution-smoke-test.md` documenting findings, especially Flash-4K-vs-Pro-4K quality comparison and any cross-tier prompt drift.

The smoke test artefacts seed documentation for #60's "Resolution selection guide — when to use 2K, when to use 4K" section.

**This is a manual gate.** The implementer runs the ladder, the speaker reviews artefacts, the speaker decides GO before merge.

---

## 9. Migration / Backward Compatibility

| Caller pattern | Behaviour after this change |
|---|---|
| `generate_cloud_image(prompt, "openai", path)` | Unchanged — defaults to `"1K"` mapping to existing `1024x1024` |
| `generate_cloud_image(prompt, "openai", path, size="1536x1024")` | Unchanged — `size` kwarg passes through; `resolution="1K"` default is implicit but doesn't override `size` |
| `generate_cloud_image(prompt, "google", path, model="gemini-3.1-flash-image-preview")` | Unchanged — defaults to `"1K"` mapping to current Flash behaviour |
| `generate_cloud_image(prompt, "fal", path, image_size="landscape_16_9")` | Unchanged — `image_size` kwarg wins over default `resolution` |

No existing call site in `plugins/jack-tar-deckhand/src/` needs modification. The render funnel (#60) will start passing `resolution=` once stages are added.

---

## 10. Out of Scope (deferred to #60, #61, or future)

- SKILL.md updates (`--resolution` flag) → #60
- `render_funnel.py` `cloud_2k`/`cloud_4k` stages → #60
- `image_router.py` upgrade-decision changes → #60
- Cross-tier refinement loop integration in deckhand pipeline → #60
- Strategy map / slide outline `resolution` field → #60
- Skill-drift fixes (FAL `--size`/`--quality`, Google `--size`) → #60
- Recraft V4 raster as first-class provider → #61
- Imagen 4 Ultra registration as separate provider entry → future
- FLUX 2 Max model registration → future
- Ideogram v3 explicit resolution control → future

---

## 11. Open Questions / Risks

### R1 — SDK support for `image_config` (mitigated by Task 0 spike)
The biggest unknown. Spike runs before implementation; result determines code shape. Three fallback paths documented in §6.

### R2 — Imagen pricing ambiguity at 2K
Two billing models report different 2K costs ($0.04 Vertex flat vs ~$0.101 Developer API token). Cost estimation must detect backend and bill correctly. Verified mitigation: env-var sniff in §5. Risk if the user's env has both vars set: code uses `GOOGLE_APPLICATION_CREDENTIALS` first (matches existing client construction logic).

### R3 — Smoke test budget overrun
$3.00 cap on a Max contract is generous, but a runaway prompt-engineer iteration could burn it. Mitigation: hard cap enforced by existing `budget_tracker.py` pattern; smoke test runs a fresh budget context.

### R4 — Nano Banana Pro 4K availability per region
Google has region-restricted preview rollouts for some Gemini features. If 4K isn't available in the speaker's project region, the spike will surface this. Fallback: degrade to Flash 4K with a logger warning.

### R5 — Test fragility around mocked SDK shape
If we mock the SDK at too low a level (raw response objects), tests pass while real integration breaks. Mitigation: mock at the public client method level (`client.models.generate_content`), and add ONE end-to-end smoke test that hits the real API at the cheapest tier as part of CI (separate from the manual smoke test gate).

---

## 12. Implementation Plan Hand-Off

After this spec is approved by the speaker, the next step is to invoke `superpowers:writing-plans` to produce a phased task list. The expected phasing:

1. **Phase 0** — SDK spike (Task 0). Gates everything else.
2. **Phase 1** — `_normalise_resolution` helper + `ProviderResolutionUnsupportedError` class + tests.
3. **Phase 2** — OpenAI provider plumbing + tests.
4. **Phase 3** — Google Imagen plumbing + cost-tier detection + tests.
5. **Phase 4** — Google Nano Banana (Flash + Pro) plumbing + tests. *Spike outcome decides PATH-A/B/C here.*
6. **Phase 5** — FAL FLUX 2 Pro plumbing + tests.
7. **Phase 6** — `provider_discovery.py` extension + tests.
8. **Phase 7** — Plugin version bump (1.1.1 → 1.2.0) + marketplace sync.
9. **Phase 8** — Manual smoke test (Issue #59 §6). Artefacts committed.
10. **Phase 9** — Speaker review. GO/REVISE/STOP. PR opened on GO.

Total estimated implementation time: 1-2 days excluding smoke test (~30 min more for the smoke test ladder itself, plus speaker-review time).
