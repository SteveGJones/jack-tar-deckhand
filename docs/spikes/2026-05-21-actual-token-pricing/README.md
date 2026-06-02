# Spike: Actual-Token Pricing Validation

**Date:** 2026-05-21
**Spec:** `docs/superpowers/specs/2026-05-21-actual-token-pricing-validation-design.md`
**Plan:** `docs/superpowers/plans/2026-05-21-actual-token-pricing.md`
**Status:** Complete — Phase 1 and Phase 2 both shipped

## Spike outcome summary

We tested whether `estimate_google_cost` (the resolution-aware catalog formula in `jack-tar-cloud`) produces reliable cost forecasts by running a 16-cell live calibration matrix against real Google Nano Banana and OpenAI APIs and comparing token-derived actual cost against catalog estimates. The hypothesis was that catalog estimates might over-state cost (explaining a user-reported billing discrepancy). The result inverted this: **catalog under-estimates actual cost by 32.5% cumulative**. Every one of the 16 cells showed actual > estimated, and the median per-cell delta for Google Nano Banana was −31% to −53% (actual exceeds estimate). The under-estimation stems from uncounted text-input tokens — the catalog formula assumes a fixed image-token count but does not account for the prompt-length component of the input charge. The `BudgetTracker._BUDGET_RATES` flat-rate table (a separate code path) does over-estimate certain cases and is the probable source of the user's original observation.

The spike shipped four production-ready infrastructure pieces. `GenerationResult` is a new dataclass (in `src/cloud_results.py` and `plugins/jack-tar-cloud/src/cloud_results.py`) that wraps the existing image-path return value and adds `cost_actual`, `usage_metadata`, and `provider` fields. `BudgetTracker` gained dual-column tracking — every `log_api_call` now accepts both `cost_estimated` and `cost_actual`, and `cost_summary_markdown()` renders a two-column table showing both. `actual_cost_calculator.py` provides pure functions (`compute_nano_banana_actual_cost`, `compute_openai_image_actual_cost`) that derive actual cost from raw `usage_metadata` dicts without touching SDK objects. A 90-day freshness test (`test_pricing_freshness.py`) fails CI if the embedded token rates go stale. The calibration and smoke-test scripts (`tools/spike_pricing_calibration.py`, `tools/spike_dogfood_smoke.py`) live in `tools/` as one-shot reproducible experiments.

Three follow-ups are deferred to a post-spike PR. First, verify OpenAI image token rates against the OpenAI dashboard — the calibration used $5/$40 per MTok placeholder rates because openai.com returned 403 during Task 4, so the OpenAI delta figures are directional only. Second, reconcile the $60/MTok image-output rate used in `compute_nano_banana_actual_cost` against the Google Cloud billing console on a real run — the rate matches the published Gemini Developer API image-generation pricing but has not been cross-checked against an actual invoice line item. Third, the flat-rate `BudgetTracker._BUDGET_RATES` table should be replaced or deprecated in favour of the resolution-aware `estimate_google_cost` path to eliminate the over/under inconsistency that likely caused the user's original confusion.

## Verdict

**GO** — all Google cells exceed the 10% delta threshold; cumulative actual ($2.254) exceeds cumulative catalog estimate ($1.701) by 32.5%, more than 3× the GO criterion.

## Key findings

1. **Hypothesis inverted.** Catalog UNDER-estimates actual cost by 32.5% cumulative. Every one of 16 cells shows actual > catalog. The user's original observation ("Google billing came in lower than estimated") most likely referenced `BudgetTracker._BUDGET_RATES` (FLAT per-quality) which over-estimates short-prompt 1K cells — not the resolution-aware `estimate_google_cost` we calibrated against.

2. **Prompt length is the dominant driver.** Long prompts (~500 words) cost a median 53% more than catalog assumes. Short prompts (~50 words) cost ~18% more. The per-image catalog flat rate assumes a fixed token count that real responses materially exceed for complex prompts.

3. **Higher resolutions narrow but don't close the gap.** Flash 1K median -41%, 2K -22%, 4K -14%. Image-output tokens dominate at higher resolutions and scale predictably; the under-estimation comes mostly from text-input tokens being uncounted.

4. **OpenAI deltas are directional only.** OpenAI domain returned 403 during Task 4, so `_OPENAI_IMAGE_RATES` uses widely-cited placeholder rates ($5/$40 per MTok). All three OpenAI cells showed -26-37% delta but the dollar conversion is provisional. Token counts ARE real.

5. **Two existing-code discrepancies surfaced.**
   - `plugins/jack-tar-cloud/src/generate_cloud_image.py:298-306` lists Imagen 2K at $0.101 (token-based per comment) when the published rate is flat $0.040. Documented in `token-pricing-rates.md`.
   - `src/budget_tracker.py:_BUDGET_RATES` uses flat per-(model, quality) rates that don't track resolution; combined with the actual-vs-catalog delta, this is likely the source of the user's "billing was lower" observation.

## Decision gate

**Phase 2 proceeds** with the actual-token capture refactor (`GenerationResult` dataclass + dual `cost_estimated`/`cost_actual` columns in `BudgetTracker`). The infrastructure is valuable regardless of delta direction — it surfaces actual cost truthfully and is the foundation for later reconciliation against billing console.

**Plan acceptance criterion (e) revised** from "cumulative actual ≤ estimated" to "cost_summary_markdown shows both estimated and actual columns on a dogfood run" — direction-agnostic.

## Phase 1 artefacts

- `report.md` — delta tables, prompt-length sensitivity, full verdict justification
- `calibration-results.json` — 16 cells, all successful, raw usage_metadata captured
- `live-run.log` — verbatim stdout/stderr from the live calibration
- `token-pricing-rates.md` — verified rates (Google) + UNVERIFIED placeholders (OpenAI)
- `phase-0-discovery.md` — SDK usage field paths
- `dry-run.txt` — pre-spend matrix preview

## Phase 1 spend

$2.254 of $5 cap (45%). 13 Google cells + 3 OpenAI cells, all successful after one retry round (graceful per-cell error handling added during Task 14 fix-up).

## Phase 2 dogfood (Task 21)

- Date: 2026-05-21
- Brief: single-image smoke test (Nano Banana Flash 1K)
- Estimated: $0.0670, Actual: $0.0895, Delta: -33.6%
- `cost_summary_markdown` confirmed to show both columns: `dogfood-cost-summary.md`
- Plumbing verified: `generate_cloud_image()` → `GenerationResult` → `BudgetTracker.log_api_call(cost_estimated, cost_actual, usage_metadata)` → markdown with two-column table.
