# Bridge Dogfood Run 3

**Date:** 2026-04-26
**Topic:** What we built and what we learned — quarter in review
**Audience:** Engineering leadership
**Duration:** 15 min
**Confidentiality:** internal
**Budget cap:** $2.00
**Visual personality:** Blueprint Retrospective (cream `#F5EFE0`, deep navy `#14213D`, muted rust `#B7410E`)
**Arc:** Dual-Track (Build · Learn · Act)

**Status:** Phase 1+2+3 complete. SMARTART verification (slides 3, 11) pending PowerPoint Mac manual gate.

**Why a third run:** Run 2 raised the bridge's value-over-/pptx by demonstrating discriminating marker placement and the cohesion-driven regen loop. Speaker observation after Run 2: *"the SmartArt is always used as a 'full page'; we don't allow the Superpower to specify a list of content and have the bridge translate it into an appropriate SmartArt."* Run 3 was framed to (a) test the unexercised cycle paths (refine_and_retry within Phase A; privacy gate at internal tier) and (b) deliberately try a third visual register to see whether the toolkit-framed marker grammar generalises.

## Phase 1 — `/bridge-brief`

- **Approval turns: 4** — first run with **zero persona drift**.
- **Brief saved to:** `output/dogfood-bridge-run-3/creative-brief.md`
- **Arc:** Dual-Track (Build · Learn · Act)
- **Visual personality:** Blueprint Retrospective (Speaker chose from 3 proposed; agent's recommendation was P3)
- **Takeaway (T3 verbatim):** *"This quarter's output earns the team credibility to push for the structural changes that will make next quarter materially better."*

### Phase 1 round-by-round behaviour

| Round | Strategy | Outcome |
|---|---|---|
| R1 — propose 3 arcs | Concise, no prescription | ✓ Three arcs (Evidence-Then-Judgment, Build-Up-Reveal Retrospective, Dual-Track) |
| R2 — propose 3 takeaways + 3 personalities | Concise, locked arc | ✓ Three takeaway phrasings, three personalities (Warm Slate, Engineering-Ink-Carryforward, Blueprint Retrospective) |
| R3a — Sections A+B only | Hard scope rules + verbatim three-movement quotation | ✓ Byte-perfect |
| R3b — Section C only | "Reproduce verbatim" with Section C content embedded | ✓ Byte-perfect |

**The split-dispatch protocol from Run 2 Finding #7 worked from the start.** Zero drift across two whole runs is the threshold to declare it the working pattern, not just a recovery technique.

### Phase 1 measurement entry

```json
{"kind":"brief","approval_turns":4,"structural_complete":true,"confidentiality":"internal"}
```

## Phase 2 — `/pptx`

- **Slides:** 12
- **Markers placed:** 5 (3 BG + 2 SMARTART) — at the lower bound of the brief's 5–7 range
- **`js_fallback_used`:** False
- **Duplicates:** none
- **Overlap warnings:** 2 (italic captions below SMARTART placeholders — same intentional pattern as Runs 1 and 2)
- **Native PptxGenJS used on 7 slides** — data table (slide 4), three-column spike layout (slide 5), big-stat callouts (slide 6), document-style finding/working-pattern blocks (slides 8-10)
- **Document register holds across the deck** — the visual continuity from cover to closing is the strongest of the three runs

### Markers placed by /pptx

| Slide | Marker | Beat |
|---|---|---|
| 1 | `BG:opening-document` | Title + three-part talk map |
| 3 | `SMARTART:capability-themes` | Three capability themes |
| 7 | `BG:build-learn-pivot` | Build → Learn pivot (II LEARN) |
| 11 | `SMARTART:forward-decisions` | Three forward decisions (III ACT) |
| 12 | `BG:closing-handover` | Quiet handover |

## Phase 3 — `/enrich-deck`

- **Generation backend:** Ollama 0.21.0 (`x/z-image-turbo:fp8`) — local, free
- **Total cost:** $0.045 (matches Run 2; well under the $2.00 cap)
- **Slides enriched:** 5 of 12 (3 BG + 2 SMARTART)
- **Cycle iterations:** **refine_and_retry fired three times** (slides 1, 12 image-review; slide 7 cohesion-review)
- **Privacy gate handshake:** **NOT exercised** — the cycle stayed in Phase A Ollama for all images; no cloud escalation triggered. Internal-tier handshake remains untested across all three runs.

### Per-image cycle summary

| Slide | Marker | Image-review iter 1 | Image-review iter 2 | Cohesion-review | Final |
|---|---|---|---|---|---|
| 1 | `BG:opening-document` | refine (3D bias, no rust, grey/metallic) | pass (0.92) | pass (0.95) | accepted |
| 7 | `BG:build-learn-pivot` | pass (0.89) | — | flag_contrast (BLOCKING) | regen v2 → accepted |
| 12 | `BG:closing-handover` | refine (no rust, too literal) | pass (0.92) | pass (0.95) | accepted |

**Three image regenerations were required** — two via image-review refine, one via cohesion-review flag_contrast. All recovered within Phase A Ollama (no cloud escalation needed).

### Phase 3 measurement entry

```json
{"kind":"enrichment","adherence_rate":1.0,"first_pass_acceptance":false,"slides_enriched":5,"slides_total":12}
```

`first_pass_acceptance: false` is again the honest signal — cohesion review needed a regen pass to converge.

### What Run 3 dogfooded that Runs 1 and 2 didn't

**The flagship: refine_and_retry cycle within Phase A Ollama.** Run 1 had no refine verdicts; Run 2 had no refine verdicts. Run 3 had two refine verdicts on iteration 1 (slides 1 and 12) — both addressed by composing refined prompts targeting the specific reviewer issues (3D bias, missing accent, too-literal subject) and regenerating. Both came back PASS on iteration 2. This proves the SKILL.md cycle's `refine_and_retry → next_attempt` branch works correctly end-to-end.

**Plus a different cohesion failure mode than Run 2.** Run 2's slide 15 was `flag_contrast` from a too-bright element (terminal monitor screen) overpowering text. Run 3's slide 7 was `flag_contrast` from too-dense detail (cross-section line-work) competing with text. Different fix shape too: image-review refine wants prompt-level guidance (palette / accent / register); cohesion-review flag_contrast wants layout-level guidance (where the detail can sit on the page so text overlays clean parchment).

### What's STILL not exercised after three runs

- **Cycle escalation Ollama → Flash (Phase B)** — Ollama recovered every flag with refine_and_retry; cloud never triggered.
- **Cycle escalation Flash → Pro (Phase C)** — never reached.
- **`terminate_pending_confirmation` privacy gate handshake** — internal tier set on Run 3 BUT gate only fires at first cloud escalation, which didn't happen.
- **`prompt-engineer` agent in `mode: "refine"` end-to-end** — Run 3 composed refined prompts inline; the bridge's prompt-engineer refine-mode contract still hasn't been dispatched in any dogfood.
- **Cohesion verdict `surface_to_user`** — never triggered (`flag_contrast` mapped to `regenerate` both times).

A future Run 4 could deliberately seed an Ollama-impossible subject (readable in-image text, photorealistic multi-figure portraits, brand-glyph reproduction) to force escalation and exercise the privacy gate + Phase B/C paths. **Without it, the cycle escalation paths remain test-uncovered in production-like dogfood.**

## Findings updated by Run 3

### Finding #3 — STATUS UPDATE: split-dispatch is now confirmed-reliable, not just recoverable

Run 3 used the split-dispatch protocol (R1 arcs → R2 intent+personality → R3a A+B → R3b C) from the start and produced **zero persona drift** across two whole runs (Run 2's R3a/R3b recovery was byte-perfect; Run 3's full Phase 1 was byte-perfect). Recommendation: SKILL.md should drive section-by-section dispatch as the default, not as a recovery pattern.

### Finding #9 — REINFORCED: SMARTART markers force a "full content zone takes a graphic" model

Run 3 reproduced what Run 2 surfaced: SMARTART placeholders consume the whole content zone, leaving SMARTART slides as "graphic with title only" — orphaned from the body-text register the rest of the deck holds. Slides 3 and 11 of Run 3 demonstrate this clearly.

**The richer model the Speaker has called for** (paraphrased from Run 2 + Run 3 conversations): /pptx writes a normal bulleted list at the slide's natural content position, marks it with a hint like `SMARTART-FROM-LIST:slug`, and the bridge replaces the list IN PLACE with a brand-coloured SmartArt graphic. Title and supporting prose remain untouched. Graceful degradation: if enrichment is skipped, the bullet list is still on the slide.

### Finding #10 — NEW: SmartArt carriers ship with default Microsoft palette, not the brief's

The msft-smartart engine extracts SmartArt fixtures from MIT-licensed `dotnet/Open-XML-SDK` test data. Each layout fixture ships three OOXML parts: `layout.xml` (algorithm), `quickStyle.xml` (default style), and **`colors.xml` (the colour scheme)**. That third file embeds Microsoft's default palette — Office-blue gradients with grey accents — which has nothing to do with our brief's Blueprint Retrospective cream/navy/rust.

Run 3's SMARTART slides 3 and 11, when opened in PowerPoint Mac, render in Microsoft default palette regardless of the brief's locked colour tokens. **The bridge currently passes brief palette to image-reviewer + cohesion-reviewer for VALIDATION but never INJECTS it into SmartArt's `colors.xml`.**

This compounds Finding #9: SmartArt slides are not just structurally orphaned (whole-slide); they're also chromatically orphaned (wrong palette). Together they make SMARTART feel like a different document inserted into the brief's document.

## Lesson learned — false dichotomy in framing

When I first surfaced Findings #9 and #10 to the Speaker, I framed them as alternatives:

> *"(A) is much cheaper and unlocks half the value immediately. (B) is the bigger architectural change but only matters once palettes are right."*

The Speaker corrected this:

> *"To me these sound like two separate issues not one, so A is required first then B, not that one or the other is optional."*

The Speaker was correct. The two findings are:

| | Concern | Code path |
|---|---|---|
| **#10 (palette)** | What colours SmartArt renders in | msft-smartart engine, `colors.xml` templating, bridge enrichment ops to wire brief palette through |
| **#9 (layout)** | How SmartArt is positioned in the slide | SKILL.md marker grammar, /pptx authoring guidance, bridge analyser (find adjacent list shapes), bridge enrichment ops (replace list with SmartArt at list position) |

These touch **different parts of the architecture** with **independent code paths**. They're not substitutable. They're sequentially dependent: **#10 is a prerequisite for #9 making sense.** Without #10, fixing #9 produces a well-positioned SmartArt in foreign colours — STILL orphaned. Without #9, fixing #10 produces correctly-coloured SmartArt that still consumes the whole slide — STILL "just a graphic with a title."

**Both required. Order: #10 first, #9 second.**

The lesson: when two findings touch different architectural concerns, frame them as separate ordered dependencies, not as cheaper-vs-bigger alternatives. The "alternatives" framing implicitly suggests one might be skippable, which is wrong when both are required for the desired outcome.

## Plan — making brand-native SmartArt the default

For SmartArt to feel native to the brief (the actual leading-practice goal), two contracts need to ship.

### Contract 1 — Palette flow (fixes Finding #10) — v0.1.x patch

**Goal:** every SmartArt graphic inherits the brief's palette automatically, regardless of authoring strategy.

**Surface area:**
- New module in `jack-tar-msft-smartart` (or a wrapper in `jack-tar-superpower-bridge`): generate brand `colors.xml` from a palette token map.
- Brief schema extension (Section B or a new C subsection): `smartart_palette_map` mapping brief tokens to SmartArt colour slots:
  ```yaml
  smartart_palette_map:
    primary_fill: structural   # main shape fill ← brief's structural token
    accent_fill: accent         # highlighted fill ← brief's accent token
    text_color: body_text       # text within shapes
    line_color: structural      # connectors / outlines
    background_fill: surface    # SmartArt overall ground
  ```
- Bridge enrichment pipeline change: before grafting SmartArt diagram parts into the host deck, generate brand `colors.xml` from the brief's palette + map, replace the carrier's default `colors.xml` with it.
- Sensible defaults: if the brief omits the map, derive from primary palette tokens automatically.

**Result:** every SmartArt in every deck respects brand colours. No code change required in /pptx authoring. Existing `SMARTART:slug` placeholders become brand-native immediately.

### Contract 2 — Authoring fidelity (fixes Finding #9) — v0.2 milestone

**Goal:** /pptx authors specify SmartArt the way they think about it (a list that should be a process diagram), and the bridge transforms it in place — preserving title, body prose, and slide layout.

**Surface area:**
- Marker grammar extension: `SMARTART-FROM-LIST:slug` — a hint shape that says "translate the bullet list at this position into SmartArt at the same position."
- /pptx authoring guidance: the brief's Section C now leads with `SMARTART-FROM-LIST` for content-driven SmartArt, demoting `SMARTART:slug` (full content zone) to a "graphic-only slide" pattern.
- Bridge analyser extension: detect `SMARTART-FROM-LIST` hint, find the nearest bullet-list shape on the same slide, extract items + structural metadata.
- Bridge smartart-selector agent: layout selection now driven by real list content (item count + semantic structure) — this is the agent's existing job in `/deck-conductor`, repurposed for `/enrich-deck`.
- Bridge enrichment ops: new operation `apply_smartart_from_list` — render SmartArt with brand `colors.xml` (Contract 1), REPLACE the list with the rendered SmartArt at the same position, preserve slide title + other shapes.
- Graceful degradation: if `apply_smartart_from_list` is skipped (e.g., budget exhausted), the bullet list remains on the slide. The author's intent isn't lost.

**Result:** SmartArt slides become content slides with graphics embedded, not graphic-only slides. Layout selection is intelligent (driven by content) and brand-native (palette inherited).

### Why Contract 1 first, Contract 2 second

- **Contract 2 without Contract 1** = well-positioned SmartArt in Microsoft default colours. Even worse than today, because the SmartArt is now embedded in a brand-coloured slide context, making the colour mismatch jarringly obvious.
- **Contract 1 without Contract 2** = correctly-coloured SmartArt that still consumes the whole slide. Better than today; partial fix.
- **Contract 1 + Contract 2** = the leading-practice outcome.

Contract 1 ships first because it benefits *every* SmartArt slide (current and future authoring patterns) without changing the authoring contract. Contract 2 builds on Contract 1 and changes the authoring contract — should ship only when the palette story is solid.

### How to make this normal practice

For brand-native SmartArt to become the default rather than a feature:

1. **Default SKILL.md guidance leads with the contracts.** Current `/enrich-deck` SKILL.md frames SmartArt as "fill the placeholder rectangle." Future SKILL.md should frame SmartArt as "transform a list into a diagram in the brief's palette." The SKILL.md's first paragraph on SmartArt should mention palette inheritance, not as an aspiration but as the contract.

2. **Brief template includes `smartart_palette_map` by default** — with reasonable derived values from the primary palette tokens. Brand managers can override; most won't need to. The presence of the map normalises the expectation that SmartArt colours are brand-controlled.

3. **`/bridge-brief` SKILL.md and the Narrative Brief Architect persona** lead Section C with `SMARTART-FROM-LIST:` examples. `SMARTART:` (full content zone) becomes the secondary pattern, mentioned for "graphic-only divider slides." This shifts /pptx's reach for SmartArt toward the in-list pattern.

4. **Cohesion-reviewer contract extension:** the cohesion review should explicitly assess SmartArt palette match (not just composition / contrast). Today's cohesion-reviewer manifest excludes SmartArt slides because LibreOffice can't render them. Once Contract 1 ships, the Speaker can verify in PowerPoint Mac and the cohesion-reviewer can dispatch on SmartArt slide screenshots taken from PowerPoint exports. Make palette-match a passable / flaggable verdict.

5. **Dogfood metric "% of SmartArt slides with verified palette match"** — added to `bridge-measurements.jsonl`. Target: 100% of SmartArt slides on every deck. Anything less is a finding.

6. **Default to brand-native rendering in tests.** Bridge tests today verify SmartArt injection works structurally; future tests should verify the rendered `colors.xml` matches the brief's palette. CI gate.

### Items for Task 35 verdict file

- Contract 1 + Contract 2 are both **release-affecting** (not nice-to-have).
- Recommend **Contract 1 ships as v0.1.x patch within 2 weeks of v0.1.0 release** — it's small surface-area and unblocks every brand-driven deck.
- Recommend **Contract 2 ships as v0.2 within 6 weeks**, paired with the Finding #4 SMARTART parser fix and Finding #5 process1 label-cap refinement (which Contract 2 partly obviates).

## Cost summary

| Phase | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| Phase 1 (off-budget per Finding #8) | 4 dispatches | 6 dispatches | **4 dispatches** |
| Phase 3 generation (Ollama, free) | $0.00 | $0.00 | $0.00 |
| Phase 3 reviews (Haiku image-reviewer) | $0.04 | $0.025 | $0.025 |
| Phase 3 cohesion (Sonnet) | $0.02 | $0.020 | $0.020 |
| **Phase 3 total** | **$0.06** | **$0.045** | **$0.045** |

Run 3 ran the same Phase 3 cost as Run 2 despite TWO regen rounds (refine_and_retry on slides 1 and 12, plus cohesion regen on slide 7). Reason: regenerations stayed in Ollama (free generation); only the additional reviews counted. The cycle's cost discipline holds even when iterations happen.

## Conclusion

Run 3 strengthens the case for the Task 35 GO verdict on the bridge's *core mechanics*. Three runs across three different visual personalities, three different audiences, three different arc shapes — and the bridge produced contract-correct decks in all three. The cycle has now exercised:
- Image-reviewer pass-through (Run 1)
- Cohesion-reviewer flag_contrast → regenerate (Run 2)
- Image-reviewer refine → refine_and_retry within Phase A (Run 3)
- AND a different cohesion failure mode (dense detail vs bright element) (Run 3)

What's still missing for full coverage:
- Cloud escalation paths (Phase B / Phase C)
- Privacy gate handshake (internal tier set in Run 3 but never reached)
- Prompt-engineer refine-mode contract end-to-end

What's exposed and needs fixing for brand-driven adoption:
- **Finding #10 — SmartArt palette** (release-affecting, v0.1.x patch)
- **Finding #9 — SmartArt-from-list** (release-affecting, v0.2 milestone)
- **Finding #3 — codify split-dispatch in SKILL.md** (release-affecting, v0.1.x patch)
- **Finding #8 — extend cost ledger to Phase 1** (matters for enterprise/API customers, v0.1.x patch)

The bridge as currently built is a working v0.1.0. The bridge as it should be — brand-native, list-driven SmartArt as default — needs Contracts 1 and 2 to ship. **The two contracts together are the difference between "a tool that produces decks" and "a tool that produces on-brand decks at scale."**
