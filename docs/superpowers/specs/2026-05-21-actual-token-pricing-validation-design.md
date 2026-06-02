# Spike: Actual-Token Pricing Validation

**Date:** 2026-05-21
**Status:** Design approved — ready for implementation plan
**Worktree:** `.claude/worktrees/spike-actual-token-pricing` on branch `worktree-spike-actual-token-pricing`
**Budget cap:** $5 (Phase 1 calibration spend only)

## Problem

`BudgetTracker.cost_summary_markdown` predicted higher spend than Google Cloud Billing actually charged for image generation on a recent run. Hypothesis: catalog rates in `_NANO_BANANA_COSTS`, `_IMAGEN_DEVELOPER_COSTS`, and `_OPENAI_COSTS` are conservative worst-case flat-rate estimates, but actual provider billing for the three token-aware image APIs is computed from real token counts reported in each API response. If the discrepancy is material, pre-flight budget approvals are blocking deck runs that would not actually cost what we say.

## Hypothesis

For at least one of {Google Nano Banana Flash, Google Nano Banana Pro, Google Imagen Developer API, OpenAI GPT Image}, the API response exposes a usage field whose token-rate-translated cost is meaningfully (≥10%) below the catalog flat-rate estimate.

## Scope

**In scope**

- Google Nano Banana Flash + Pro (`gemini-3.1-flash-image-preview`, `gemini-3-pro-image-preview`) via `generate_content`
- Google Imagen on Developer API (`imagen-4.0-fast-generate-001`, `imagen-4.0-generate-001`, `imagen-4.0-ultra-generate-001`) via `generate_images`
- OpenAI GPT Image (`gpt-image-1` / `gpt-image-1.5`) via `images.generate`

**Out of scope**

- FAL.ai, Recraft, Ollama — flat-rate or local; no token surface
- Claude API spend for subagents (prompt-engineer, image-reviewer, etc.) — meaningful but distinct concern; file as follow-up
- Provider billing console reconciliation — API-reported usage is the spike's authoritative source of truth

## Source of truth

API response usage fields, captured in-band at call time. No billing-console crosscheck. Rationale: deterministic, no 24-48h lag, exposes the provider's real-time view of the bill it will charge.

## Phased approach

Three phases, gated. Each phase produces an artefact that determines whether the next phase fires.

### Phase 0 — Discovery (zero spend, ~30 min)

Read each provider SDK (`google-genai`, `openai`) to confirm exactly what each response object exposes:

- `client.models.generate_content(...)` → `response.usage_metadata.{prompt_token_count, candidates_token_count, total_token_count, cached_content_token_count}`
- `client.models.generate_images(...)` → does this return `usage_metadata`? Unknown; must verify
- `client.images.generate(model="gpt-image-1", ...)` → `response.usage.{input_tokens, output_tokens, total_tokens}`? Verify
- `client.images.generate(model="gpt-image-1.5", ...)` → same; verify

Document the exact field paths per provider in `docs/spikes/2026-05-21-actual-token-pricing/phase-0-discovery.md`. If a provider does not expose usage at all, mark it deferred and exclude from the Phase 2 refactor.

### Phase 1 — Calibration ($5 cap, ~25 API calls)

Build `tools/spike_pricing_calibration.py` — an idempotent script that reads any existing `calibration-results.json` and only fills missing cells. Matrix:

| Cell | Calls | Estimated catalog spend |
|---|---|---|
| Nano Banana Flash 1K × {short ~50w, medium ~200w, long ~500w} | 3 | $0.20 |
| Nano Banana Flash 2K × 3 prompt sizes | 3 | $0.30 |
| Nano Banana Flash 4K × 3 prompt sizes | 3 | $0.45 |
| Nano Banana Pro 1K × 3 prompt sizes | 3 | $0.40 |
| Nano Banana Pro 4K × long prompt only | 1 | $0.24 |
| Imagen Fast 1K × 3 prompt sizes | 3 | $0.06 |
| Imagen Standard 1K × 3 prompt sizes | 3 | $0.12 |
| Imagen Standard 2K × 3 prompt sizes | 3 | $0.30 |
| GPT Image medium × 3 prompt sizes | 3 | $0.18 |
| **Total** | **25** | **~$2.25** |

Prompt-size buckets are drawn from real dogfood logs (the 2026-05-07 blog-post asset run and the v1.4 paperbanana run) so the calibration reflects production prompts, not synthetic strings.

Per call, capture and persist:

- `provider`, `model`, `resolution`, `prompt_chars`, `prompt_words`
- `catalog_estimate_usd` (current code path: `estimate_*_cost(...)`)
- `raw_usage_metadata` (verbatim from the response object, JSON-serialised)
- `computed_actual_usd` (token counts × token rates from `token-pricing-rates.md`)
- `delta_usd = catalog_estimate - computed_actual`
- `delta_pct = delta_usd / catalog_estimate × 100`
- `timestamp`

Stop here if the report shows median delta < 5% in every cell — catalog rates are already accurate enough.

### Phase 2 — Production refactor (zero additional API spend, gated)

Fires only if Phase 1 GO criteria are met (see Success Criteria below).

## Architecture (Phase 2)

### New module: `src/actual_cost_calculator.py`

Pure functions, no I/O:

```python
def compute_nano_banana_actual_cost(model: str, usage_metadata: dict) -> float
def compute_imagen_actual_cost(model: str, usage_metadata: dict) -> float
def compute_openai_image_actual_cost(model: str, usage: dict) -> float
```

Token-rate tables live as module-level constants. Each rate carries a comment with source URL and `date_captured`:

```python
# Source: https://ai.google.dev/gemini-api/docs/pricing  (captured 2026-05-21)
_GEMINI_FLASH_TEXT_INPUT_PER_MTOK = 0.30
_GEMINI_FLASH_IMAGE_OUTPUT_PER_MTOK = 30.00
```

A unit test (`tests/test_pricing_freshness.py`) emits a warning when any rate is older than 90 days. Advisory, not blocking.

### `generate_cloud_image()` return shape

Currently returns `path: str`. Evolved to a `GenerationResult` dataclass in a new `src/cloud_results.py`:

```python
@dataclass
class GenerationResult:
    path: str
    cost_estimated: float
    cost_actual: Optional[float]      # None when provider exposes no usage field
    usage_metadata: Optional[dict]    # raw verbatim for audit
    provider: str
    model: str
    resolution: str

    def __fspath__(self) -> str: return self.path  # callers that used path keep working
    def __str__(self) -> str: return self.path
```

Existing callers that pass the return into `Path(...)` or `open(...)` keep working unchanged through `__fspath__`. Callers that interpolate it into strings or pass to `addImage` keep working through `__str__`. New callers can access `.cost_actual` and `.usage_metadata`.

### `BudgetTracker.log_api_call()` extended

```python
def log_api_call(
    self,
    model_key: str,
    cost_estimated: float,
    image_id: str,
    cost_actual: Optional[float] = None,
    usage_metadata: Optional[dict] = None,
) -> None:
```

`self._spent` accumulates `cost_actual` when present, `cost_estimated` otherwise. `cost_summary_markdown()` adds an `Actual $` column alongside the existing `Cost $` column (renamed `Estimated $`). When a row has no actual, the cell shows `—` and the Δ cell shows `n/a`.

Pre-flight cap check is unchanged: it still uses `estimate_cost(model_key)` because we cannot know actual cost before the call returns. This is intentional and matches the design Q4 answer.

### Provider plumbing

Each provider branch in `plugins/jack-tar-cloud/src/generate_cloud_image.py` (and the legacy `src/generate_cloud_image.py`) returns the raw usage field alongside the file. Where Phase 0 confirms no usage field is exposed (likely the Imagen Vertex flat path; possibly Imagen Developer), we set `cost_actual = cost_estimated` and `usage_metadata = None` so the dataclass shape is uniform.

## Calibration prompts

Drawn from real dogfood logs. Each prompt is checksummed and stored in `docs/spikes/2026-05-21-actual-token-pricing/prompts/` so calibration is reproducible.

- **short_a** (~50 words): hero closer slide, simple noun-led scene
- **short_b** (~50 words): icon-style request
- **medium_a** (~200 words): backdrop with composition directives
- **medium_b** (~200 words): photoreal portrait with brand-palette constraints
- **long_a** (~500 words): full pragmatic-composition brief with positional callouts
- **long_b** (~500 words): paperbanana-style academic figure brief

Three prompts per cell drawn from these six; the script picks `short_a, medium_a, long_a` by default and falls back to the `_b` variants if any cell needs re-runs.

## Output artefacts

Location: `docs/spikes/2026-05-21-actual-token-pricing/`

- `README.md` — spike summary, methodology, key findings, **GO/NO-GO verdict for Phase 2**
- `phase-0-discovery.md` — confirmed field paths per provider
- `token-pricing-rates.md` — token rates per provider with source URLs and `date_captured`
- `tools/calibration.py` — idempotent runnable script
- `calibration-results.json` — structured per-call data (see Phase 1 fields above)
- `raw-responses/<provider>/<model>/<cell>.json` — sanitised response dumps (image bytes stripped) used as Phase 2 test fixtures
- `report.md` — delta tables per (provider, model, resolution) with mean / median / min / max

## Success criteria

**Phase 0 done** when each in-scope provider's usage field path is documented or marked deferred.

**Phase 1 → GO Phase 2** if median delta ≥ 10% in any (provider, model, resolution) cell, OR cumulative actual across the matrix is more than 10% below cumulative catalog estimate.

**Phase 1 → NO-GO** if all median deltas are < 5%. Spike closes; report serves as evidence that catalog rates are accurate enough.

**Phase 1 → AMBIGUOUS (5%-10% deltas)** — extend matrix with `_b` prompt variants up to remaining budget, then re-evaluate. If still ambiguous, present findings and let speaker decide.

**Phase 2 done** when:

- `GenerationResult` returned end-to-end from `generate_cloud_image()` for all in-scope providers
- `BudgetTracker` shows both columns in `cost_summary_markdown()`
- Phase 1 raw responses power deterministic unit tests in `tests/test_actual_cost_calculator.py` (no live API calls in tests)
- Full existing test suite green (183/183 + new spike tests)
- One dogfooded mini-deck render shows `cumulative_actual ≤ cumulative_estimated` in the rendered cost summary

## Risks & mitigations

1. **Imagen Developer API may not return usage_metadata.** Mitigation: Phase 0 confirms before spending. If absent, Imagen is deferred from the refactor and the catalog remains the truth-of-record for that provider.
2. **Token rates drift.** Mitigation: comments record source URL + date-captured; advisory 90-day staleness test in CI.
3. **Sample of 3 prompts per cell is low for statistical confidence.** Acknowledged; this is order-of-magnitude validation, not a published study. AMBIGUOUS branch above handles borderline cases.
4. **`gpt-image-1` vs `gpt-image-1.5` may bill differently.** Mitigation: test exactly the model wired in production; record version explicitly per row in results.
5. **Spike scope creep into Claude subagent costs.** Explicitly out-of-scope per design. If Phase 1 surprises us with a tangentially-Claude-related discovery, file a follow-up issue and stay disciplined.
6. **API key absence.** Script reports SKIPPED per missing provider rather than failing; spike can complete a partial matrix if one provider key is missing.
7. **Provider response object stability.** Field paths may change between SDK versions. Mitigation: pin SDK versions in `tools/calibration.py` requirements comment and document the exact versions tested in Phase 0.

## Open questions (resolve at plan-time)

- Where `GenerationResult` lives — new `src/cloud_results.py` module vs. extending `provider_discovery.py`. Leaning new module to keep `provider_discovery` discovery-focused.
- Whether `cost_summary_markdown` keeps a separate `Δ %` column or just side-by-side `Estimated $` / `Actual $`. Leaning side-by-side; readers can compute Δ.
- Whether the 90-day rate-staleness test belongs in `tests/test_pricing_freshness.py` (new file) or extends an existing test module.

## Non-goals

- Real-time switching of provider/model based on actual-cost trend
- Predictive cost models based on prompt characteristics
- Reconciliation against provider billing invoices
- Refactoring FAL, Recraft, or Ollama cost paths (these are flat-rate by design)

## Follow-ups (not this spike)

- Claude subagent (prompt-engineer, image-reviewer) actual-token capture — likely larger delta than image APIs, separate concern
- Provider billing-console reconciliation skill (would compare cumulative actual against monthly billing CSV)
- Prompt-length-aware pre-flight estimator (would learn from accumulated actual data over time)
