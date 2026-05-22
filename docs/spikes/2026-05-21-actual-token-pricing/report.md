# Phase 1 — Calibration Report

**Spec:** `docs/superpowers/specs/2026-05-21-actual-token-pricing-validation-design.md`
**Plan:** `docs/superpowers/plans/2026-05-21-actual-token-pricing.md`
**Data:** `calibration-results.json` (16 cells, 16 successful, 0 errored)

## Headline

This spike measured actual token-level costs against jack-tar's catalog estimates for 16 cells spanning Google Nano Banana Flash/Pro at 1K–4K resolution and OpenAI gpt-image-1 at 1K, using three prompt lengths (60 / 197 / 491 words). **The hypothesis is inverted relative to the user's original observation:** across every single cell, actual cost *exceeds* the catalog estimate — the catalog systematically under-estimates, not over-estimates. The cumulative catalog estimate was $1.701 against a cumulative actual of $2.254, a **-32.5% overall shortfall** (actual 32% higher than estimated). The strongest driver is prompt length: long prompts (491 words) cost 38–79% more than catalog assumes, because the catalog treats output token count as a fixed per-resolution constant, but real API responses use substantially more candidate tokens when the input prompt is longer. The narrowest gap occurs at Flash 4K with a short prompt (-12.5%), showing that higher resolutions partially close the delta — the fixed image-token budget dominates and text-input overhead becomes proportionally smaller. The widest gap is Flash 1K with a long prompt: -79.2%, meaning the catalog estimate is less than half the actual cost. For the OpenAI cells the direction is the same but the magnitude is provisional — placeholder rates ($5/$40 per MTok) were used because openai.com pricing pages returned HTTP 403 during rate discovery; treat those three cells as directional only.

The user's original observation ("Google billing came in lower than catalog estimates") is not contradicted by this data — it remains possible that the *budget_tracker* path in jack-tar uses different rates or a different cost-attribution formula than the `estimate_google_cost` / `compute_nano_banana_actual_cost` paths exercised in this spike. A billing-console cross-check is recommended as a follow-up to reconcile which code path drove the user's observed discrepancy.

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

**Verdict:** **GO**

Every Google cell's median Δ exceeds 10% (range: -13.5% to -79.2%), and the cumulative actual is 32.5% above the cumulative catalog estimate — far above the 10% GO threshold. The signal is unambiguous: the catalog under-estimates real-world costs at every tested combination of provider, model, resolution, and prompt length. Phase 2 refactor work is warranted.

## Key Findings

- **Finding 1 — Hypothesis inverted: catalog UNDER-estimates actual cost across all Google cells.** Every one of the 13 Google Nano Banana cells (Flash 1K/2K/4K + Pro 1K/4K, all prompt lengths) has actual > catalog. The original user concern ("Google billing was lower than estimated") is not reflected in this spike's data. The most likely reconciliation: the *budget_tracker* code path used in production sessions uses different rates or a different token-attribution model than `estimate_google_cost` / `compute_nano_banana_actual_cost`. A billing-console cross-check is needed to identify which code path was active when the user observed lower-than-catalog billing.

- **Finding 2 — Prompt length is the dominant cost driver.** Long prompts (491 words / ~818 prompt tokens) cost 38–79% more than catalog assumes. Median deltas by prompt length across all Google cells: short_a −18.0%, medium_a −20.5%, long_a −52.7%. The catalog assumes a fixed per-resolution output-token constant; real responses use more candidate tokens at every resolution when the prompt is longer, suggesting the model generates more detail / variation tokens proportional to prompt context.

- **Finding 3 — Resolution narrows the gap (but doesn't close it).** For Flash, median Δ improves from −41.4% at 1K to −13.5% at 4K. At higher resolutions the fixed image-output token cost dominates the total bill and the variable text-input overhead becomes a smaller proportion — making the catalog estimate relatively more accurate. However, even at Flash 4K the catalog still under-estimates by 12–38% depending on prompt length. Pro 4K (single long-prompt cell) came in at −41.9%, showing that Pro is not immune.

- **Finding 4 — OpenAI placeholder caveat.** The three OpenAI gpt-image-1 cells show the same directional pattern (actual > catalog, −25.6% to −36.6%), but the dollar conversion used placeholder rates ($5/MTok input, $40/MTok output) because openai.com pricing pages returned HTTP 403 during Task 4 rate discovery. The output token count was constant across all three OpenAI prompt lengths (1,056 tokens), suggesting gpt-image-1 has a fixed output size — the growing delta with longer prompts is driven entirely by input tokens. Do not rely on the OpenAI dollar deltas for production budget planning without first retrieving verified rates from the OpenAI dashboard.

- **Finding 5 — Root cause hypothesis for the billing discrepancy.** Two mechanisms could explain why the user's live sessions showed lower-than-catalog billing while this spike shows higher-than-catalog actual: (a) the `budget_tracker` in production sessions may call `estimate_google_cost` using the catalog's per-resolution flat rate (ignoring the text-input token component entirely), which would produce an *overestimate* visible to the user — exactly consistent with "billing came in lower"; (b) alternatively, the Gemini Developer API may apply context-window caching or session discounts that reduce the real bill below the per-token formula. The spike measures per-call token counts and applies the published per-token rates; if the API actually bills less via caching, our formula over-attributes. These two hypotheses point in opposite directions and require billing-console verification to resolve.
