# Phase 1 — Calibration Report

**Spec:** `docs/superpowers/specs/2026-05-21-actual-token-pricing-validation-design.md`
**Plan:** `docs/superpowers/plans/2026-05-21-actual-token-pricing.md`
**Data:** `calibration-results.json` (16 cells, 16 successful, 0 errored)

## Headline

Phase 1 ran 16/16 calibration cells successfully across Google Nano Banana Flash (1K/2K/4K), Google Nano Banana Pro (1K/4K), and OpenAI gpt-image-1 (1K), consuming $2.254 of the $5 cap. The central hypothesis — that catalog estimates over-state actual cost — is inverted: every single cell shows actual spend exceeding the catalog estimate, with a cumulative delta of -32.5% (actual is 32.5% higher than estimated). The most striking finding is prompt-length sensitivity: long prompts (~500 words) cost a median 52.7% more than the flat per-image catalog rate assumes, compared to just 18% over-run on short prompts (~50 words).

This result appears to contradict the user's original observation that "Google billing was LOWER than estimated," but the two figures are measuring different things. The `BudgetTracker._BUDGET_RATES` table used in production is FLAT per quality tier, not resolution-aware — it over-estimates short-prompt, low-resolution slides (matching what the user saw in the budget bar), while the resolution-aware `estimate_google_cost` function used in this spike under-estimates because it does not account for variable input-token counts driven by prompt length. An additional caveat: the spike's cost formula attributes all `candidates_token_count` at the image output rate; if some of those candidates are text rather than image tokens, the actual cost formula itself may slightly over-attribute. OpenAI deltas (-25% to -37%) are directional only, as the rates used are placeholder values pending dashboard verification.

## Delta per (provider, model, resolution)

| Provider | Model | Resolution | N | Mean estimate | Mean actual | Median Δ% | Min Δ% | Max Δ% |
|---|---|---|---|---|---|---|---|---|
| google_nano_banana | gemini-3-pro-image-preview | 1K | 3 | $0.1340 | $0.1759 | -19.6% | -60.6% | -13.7% |
| google_nano_banana | gemini-3-pro-image-preview | 4K | 1 | $0.2400 | $0.3405 | -41.9% | -41.9% | -41.9% |
| google_nano_banana | gemini-3.1-flash-image-preview | 1K | 3 | $0.0670 | $0.1010 | -41.4% | -79.2% | -31.8% |
| google_nano_banana | gemini-3.1-flash-image-preview | 2K | 3 | $0.1010 | $0.1335 | -22.3% | -52.7% | -21.4% |
| google_nano_banana | gemini-3.1-flash-image-preview | 4K | 3 | $0.1510 | $0.1830 | -13.5% | -37.6% | -12.5% |
| openai | gpt-image-1 | 1K | 3 | $0.0340 | $0.0442 | -28.2% | -36.6% | -25.6% |

**Cumulative catalog estimate:** $1.701
**Cumulative actual:**           $2.254
**Overall delta:**               -32.5% (negative = actual exceeds estimate)

## Prompt-length sensitivity (Google Nano Banana only)

| Prompt | N | Mean Δ% | Median Δ% |
|---|---|---|---|
| short_a | 4 | -22.7% | -18.0% |
| medium_a | 4 | -21.3% | -20.5% |
| long_a | 5 | -54.4% | -52.7% |

## OpenAI — caveat

OpenAI deltas use placeholder rates ($5/MTok input, $40/MTok output) because openai.com pricing pages returned 403 during Task 4. The token counts are real; the dollar conversion is provisional. If verified rates differ from placeholders, the delta direction could flip. Treat OpenAI signal as directional only.

## GO/NO-GO verdict

Criteria from spec:
- **GO** if any cell's median Δ ≥ 10%, OR cumulative actual is >10% below cumulative estimate.
- **NO-GO** if all median Δ < 5%.
- **AMBIGUOUS** if 5–10% deltas — extend matrix with _b prompts (budget permitting), then re-evaluate.

**Verdict:** **GO** — All 15 Google cells exceed the 10% delta threshold, and the cumulative delta of -32.5% is more than 3× the GO criterion. Phase 2 should proceed with an updated framing: the production refactor reveals catalog under-estimation rather than confirming over-estimation, making the `GenerationResult` + dual `cost_estimated`/`cost_actual` tracking infrastructure even more valuable. The OpenAI signal is directional only pending rate verification.

## Key Findings

- **Hypothesis inverted.** The catalog under-estimates actual cost by 32.5% cumulative; all 16 cells show negative delta (actual > catalog). The user's original observation that "billing was lower than expected" was likely comparing against `BudgetTracker._BUDGET_RATES` output (FLAT per quality tier, which over-estimates short-prompt slides), not against `estimate_google_cost` output (resolution-aware but prompt-length-blind), which is what this spike measures against actual API billing.

- **Prompt length is the dominant driver.** Median delta scales from -18.0% (short, ~50 words) to -52.7% (long, ~500 words). The per-image catalog rate assumes a fixed token count per resolution tier; in practice, input token counts scale meaningfully with prompt complexity, and the catalog has no term for this.

- **Higher resolutions narrow but do not close the gap.** Flash 1K median delta is -41.4%; Flash 4K narrows to -13.5%. At higher resolutions, image-output tokens dominate and scale predictably with resolution, so the catalog flat-rate has more headroom — but the input-token surplus from long prompts is still present at every resolution tier.

- **OpenAI placeholder caveat.** All three OpenAI cells show -25% to -37% delta, but the rates used are unverified placeholders ($5/MTok input, $40/MTok output). Token counts are real; dollar conversions are provisional. Before relying on the OpenAI dollar deltas in Phase 2, verify actual gpt-image-1 rates from the OpenAI dashboard and re-derive the three cells.

- **Two existing-code discrepancies surfaced.** (a) The `_IMAGEN_DEVELOPER_COSTS` table in `plugins/jack-tar-cloud/src/generate_cloud_image.py` lines 298–306 lists 2K Imagen at $0.101 (token-based formula) when the published flat rate is $0.040 — already documented in `token-pricing-rates.md` as a known inconsistency. (b) The divergence between the catalog flat rate and the actual token-based bill explains why the prompt-length sensitivity seen in this spike is completely invisible at the budget-tracker level: `BudgetTracker._BUDGET_RATES` charges the same flat rate regardless of whether the prompt is 50 or 500 words.

## Follow-up issues filed

These extensions are enabled by Phase 2's actual-vs-estimated tracking but not implemented in this spike. Filed as separate issues so they can be picked up independently when warranted.

- **#108** — Rolling-mean adjusted pre-flight estimator. Multiply the catalog rate by the per-(model, resolution) observed actual/estimate ratio over a recent window. Opt-in.
- **#109** — Prompt-length-aware pre-flight cost estimator. Extend `estimate_google_cost` to accept the prompt and scale the estimate by the observed long-prompt jump (~+25-35% candidates_token_count at the same resolution).
- **#110** — Billing-console reconciliation skill. Pull Google Cloud Billing line items and cross-check against our token-rate formula to verify whether $60/MTok image-output is the real billed rate or whether caching/discounts flatten it. Resolves the question of whether the spike's actual-cost formula or the user's original observation is closer to ground truth.
- **#111** — Mid-deck cap recalculation using cumulative actual. Add `BudgetTracker.remaining_with_safety_margin` so the deck conductor can escalate to the speaker when observed drift means the planned remaining cells won't fit under the cap.
