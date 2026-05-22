# Spike: Actual-Token Pricing Validation

**Date:** 2026-05-21
**Spec:** `docs/superpowers/specs/2026-05-21-actual-token-pricing-validation-design.md`
**Plan:** `docs/superpowers/plans/2026-05-21-actual-token-pricing.md`
**Status:** Phase 1 complete — proceeding to Phase 2 (production refactor)

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
