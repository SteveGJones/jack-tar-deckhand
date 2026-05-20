# 2026-05-20 — full_bleed scale dogfood (issue #88, v1.4.2)

## Scope

Verify the new `full_bleed` rendering strategy makes the image fill the slide with ZERO chrome — no title overlay, no body, no footer logo — while leaving every other strategy unchanged.

## Method

Synthetic 4-slide deck built from JSON contracts (no AI generation; reused `tests/fixtures/minimal_deck/images/slide-01-hero.png` as the picture for every image-bearing slide). One slide per representative strategy:

| # | Strategy      | Expected behaviour |
|---|---------------|--------------------|
| 1 | `full_render` | Image + title overlay near the bottom + footer logo |
| 2 | `composed`    | Standard chrome — title + bullets, no image |
| 3 | `background`  | Image as backdrop + `left_panel` text overlay + footer logo |
| 4 | `full_bleed`  | Image edge-to-edge, NO title, NO body, NO footer — image IS the slide |

Pipeline:

1. `tmp/full-bleed-dogfood/setup_deck.py` writes outline / style-guide / image-manifest / chart-manifest / speaker-notes / strategy-map.
2. `node plugins/jack-tar-deckhand/src/assembler/build_deck.js --deck-dir tmp/full-bleed-dogfood/deck` produces `presentation.pptx`.
3. `soffice --headless --convert-to pdf` followed by `pdftoppm -png -r 96` rasterises each slide to a PNG for review.
4. `general-purpose` subagent (Sonnet) dispatched with the 4 PNG paths and explicit pass/fail criteria. Subagent read the PNGs into its own context and returned a text verdict — no direct PNG read in the orchestration session.

## Spend

$0.00 — image generation skipped, only existing fixture used. Sonnet subagent dispatch cost ~$0.01.

## Subagent verdict

```
Slide 1 (full_render): PASS — Image fill with title overlay "Slide 1 — full_render"
                              in white on a dark band near the bottom. Chrome matches
                              full_render contract.
Slide 2 (composed):    PASS — White content slide with red left rule and bottom rule,
                              title "Slide 2 — composed", three bullets, no image.
                              Matches composed contract.
Slide 3 (background):  PASS — Image filling the canvas with a darker left_panel
                              containing white title "Slide 3 — background" and three
                              light-grey bullets. Matches background+left_panel
                              contract.
Slide 4 (FULL_BLEED):  PASS — Pure edge-to-edge image. ZERO text visible.
                              No "Slide 4", no "NOTHING SHOULD APPEAR", no body
                              bullets, no title bar, no footer logo, no chrome of any
                              kind. [gate satisfied]
Overall verdict: SHIP
```

## Findings to entrench

1. **The `full_bleed` branch correctly strips ALL chrome** including footer logo. The contrast with `full_render` (which keeps a title overlay and the logo) confirms the two strategies are distinguishable to the eye, not just to the schema.
2. **No backward-compat regression.** Slides 1–3 render identically to baseline; the new branch is purely additive on the dispatcher (an `if strategy === 'full_bleed'` clause that returns early).
3. **The python-pptx template path was not exercised in the visual dogfood** — covered exclusively by the integration tests in `test_full_bleed_scale.py`. Acceptable for the merge gate because the path is small (one new helper `_apply_full_bleed` plus a four-line wiring branch) and the unit + integration tests inspect both the shape count and the OOXML spTree ordering after `_apply_full_bleed` runs. A template-mode dogfood is a candidate for the v1.4 end-to-end dogfood (PR #105).
4. **No upstream review cost.** Because the image is a known fixture and the rendering strategies are deterministic, the subagent was acting as a contract verifier, not a quality scorer. The image-reviewer agent (Haiku, scoring rubric) was not the right tool here — `general-purpose` (Sonnet, text+image semantics) gave a precise verdict in one round.

## Out of scope for this PR

- Auto-classification of `full_bleed` (operator-opt-in only by design — see issue #88 plan and the verification tests in `test_outline_classifier_never_emits_full_bleed`).
- Bridge-side `FULLBLEED:` marker kind in `placeholder.py` (would require coordinated work in the bridge's `enrichment.py`, separate ticket).
- Final v1.4 end-to-end dogfood mixing #88 + #90 + #91 (PR #105 candidate).
