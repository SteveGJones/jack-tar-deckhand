# 2026-05-24 — Creative Vision GA-flow multi-slide dogfood (#113)

## Status

**Operator-validation pending.** This dogfood log is the AC5 deliverable for issue #113. The structural surrogate (the deterministic integration test in `plugins/jack-tar-deckhand/tests/test_creative_vision_ga_flow.py`) is green and exercises every helper invocation in the canonical conductor order, but the *live* multi-slide dogfood — running real Ollama drafts + real cloud renders + real operator gates across multiple creative_vision slides with a shared creative-anchor — gates on operator participation per F12 (every iteration fires a gate; only operator acceptance closes a slide) and so cannot be run autonomously.

This log will be **completed in-place** on the same branch (`feat/creative-vision-ga`) once the operator runs the validation deck described below.

## Scope

Validate that the GA flow from issue #113 — cost surface at strategy approval (AC1), pre-deck Creative Sprint (AC2), per-iteration operator gate for creative_vision (AC3), and deck-level creative anchors (AC4) — actually changes outcomes on a multi-slide deck. The sun-phases / data-supply-chain / naval-academy dogfoods each validated a single creative_vision slide; this dogfood is specifically about cross-slide consistency and phase ordering.

## Suggested validation deck — three slides + one shared anchor

Recommended shape for the operator-run dogfood (small, deliberate, exercises the full GA surface):

- **Slide 1 (creative_vision, ceiling `flash_1k`)** — single-moment scene. _Vision_: "The Customer enters a candlelit Wall Street bar at dusk, mid-trade. He glances at the cocktail napkin where the deal is being scribbled." Sets up the recurring character anchor.
- **Slide 2 (composed)** — standard chart/diagram slide. _Purpose_: confirm composed-slide work is BLOCKED until the sprint completes; once the sprint closes, this slide renders via the standard fast cadence.
- **Slide 3 (creative_vision, ceiling `flash_1k`)** — recurring character. _Vision_: "The Customer at his desk the next morning, reviewing the printed invoice. Same office, same blazer, same glasses as last night." Anchors continuity test — the character must look like the same person across slides 1 and 3.
- **Slide 4 (creative_vision, ceiling `pro_1k`)** — recurring character + escalation. _Vision_: "The Customer on the phone at dusk, furious about the missing delivery, crumpling the invoice in his fist." Final emotional beat in a 3-image arc.

### Required `creative_anchors.json`

```json
{
  "schema_version": "1.0.0",
  "deck_brief": "1980s Wall Street cinematic style, 35mm film grain throughout",
  "anchors": [
    {
      "name": "The Customer",
      "kind": "character",
      "description": "Mid-50s man, salt-and-pepper hair, tortoiseshell glasses, navy double-breasted blazer with crested buttons, no facial hair",
      "appears_in_slides": [1, 3, 4],
      "negative_traits": ["beard", "moustache"]
    },
    {
      "name": "Period Palette",
      "kind": "style_anchor",
      "description": "Saturated 35mm film grain, deep amber + cyan + bronze, dramatic chiaroscuro lighting"
    }
  ]
}
```

## What the operator validates

1. **AC1 cost surface fires BEFORE approval.** Running `/strategy-map` or the deck-conductor's Step 3.5 surfaces the per-slide table with three creative_vision lines + composed slide excluded + deck-level totals. The operator sees the projected `~$0.20-$0.80` envelope and either approves or steps down a slide.
2. **AC2 Sprint phase is serialised.** The conductor refuses to start the composed-slide render for slide 2 while slides 1, 3, 4 are unaccepted. Operator confirms via the sprint-progress markdown surface that the BLOCKED status is visible and accurate.
3. **AC3 gate fires every iteration.** During slide 1's cascade (e.g. Ollama → Ollama refinement → Flash 1K → Flash 1K refinement), the operator should be prompted at EVERY iteration regardless of cost transition. No auto-rendering.
4. **AC4 anchors hold the character.** Slides 1, 3, and 4 should render The Customer with consistent appearance. The Brief input (visible in the dispatch log) must contain the salt-and-pepper / tortoiseshell-glasses / navy-blazer description on every slide; the negative trait (no beard) should appear in the prompt as an explicit exclusion. The final images must agree on the character within plausible drift.
5. **AC5 / AC6 don't have dogfood signals** — AC5 is the docs the operator is reading now, AC6 is cost-table reconciliation already test-validated.

## Budget guardrail

Sprint ceiling: `$2.00` total across slides 1, 3, 4 (worst-case ~$1.00-$1.50 typical envelope from the data-supply-chain dogfood — operator decides if any slide warrants escalation to Pro 4K). The pre-PR Ralph loop's task spec set $3.00 as the hard ceiling for the whole GA work; this dogfood should fit comfortably under that.

## Results (operator to fill in)

| Slide | Cascade summary | Cost | Iterations | Gates fired | Anchor consistency |
|---|---|---|---|---|---|
| 1 | _TBD_ | _$X.YY_ | _N_ | _N_ | _yes/no_ |
| 3 | _TBD_ | _$X.YY_ | _N_ | _N_ | _yes/no_ |
| 4 | _TBD_ | _$X.YY_ | _N_ | _N_ | _yes/no_ |
| **Total** | — | **$X.YY** | — | **N** | — |

## Findings (operator to fill in)

_Capture any deviations from the GA-flow design here. Specifically: did the cost surface fire? Was the Sprint phase serialised? Did the per-iteration gate fire on cost-to-cost transitions? Did anchors hold across all three character slides? Were there any cross-slide visual drifts the anchors should have caught and didn't?_

## Cross-references

- Issue #113 — GA acceptance criteria
- Issue #105 — parent (creative_vision v1.5.0)
- PR #107 — parent PR (tested-but-not-GA shipment of creative_vision)
- Dogfood log [2026-05-21 sun-phases](2026-05-21-creative-vision-renderer.md) — first creative_vision dogfood (single-slide)
- Dogfood log [2026-05-21 data supply chain](2026-05-21-creative-vision-renderer-data-supply-chain.md) — F10/F11 evidence (single-slide multi-scene)
- Dogfood log [2026-05-23 Naval Academy](2026-05-23-creative-vision-agentic-naval-academy.md) — F12 evidence (single-slide single-moment)
- Structural surrogate test: `plugins/jack-tar-deckhand/tests/test_creative_vision_ga_flow.py` — 6 deterministic tests covering AC1 → AC4 invocation order
