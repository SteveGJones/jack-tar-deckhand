# Bridge Dogfood Run 5

**Date:** 2026-04-27
**Topic:** Our 2027 product strategy — what we'll build, what we won't
**Audience:** Senior leadership team
**Duration:** 15 min
**Confidentiality:** internal
**Budget cap:** $2.00
**Visual personality:** Boardroom Stone (warm parchment `#F4F1EC`, slate `#2C2F35`, single muted teal-green `#4A8C7E`, won't-build slate `#6B7280`)
**Arc:** Problem-Solution / Pruning Frame

**Status:** Phase 1+2+3 complete. PowerPoint Mac PDF export confirms all 4 SmartArt slides render with brand-coloured graphics; BG marker on the structural pivot renders correctly behind typography; both native charts (capacity allocation, ROI projection) read in brand palette without IMAGE markers. Cohesion verdict aggregate PASS.

**Why a fifth run:** Run 4's SMARTART-FROM-LIST contract worked but `/pptx` defaulted bullet shapes to full-content-zone width. Speaker observation after Run 4: *"Smart Art is still 'full slide' but the use of feature images is very strong"*. Run 4 Finding #15 also surfaced that 3 of 4 IMAGE markers in Run 4 were chart-shaped subjects (line graph, banner timing, density chart) where the deckhand pipeline's `src/render_chart.py` would have produced faithful output. Run 5 was framed to test (a) whether brief Section C alone could coach `/pptx` into authoring SMARTART-FROM-LIST markers at sub-page scales (the same way Run 4 proved for IMAGE), (b) whether Section C language redirects chart-shaped subjects to native charts and away from IMAGE markers, and (c) whether the BG marker — never exercised at marker level across the four prior runs — works end-to-end. The visual personality (Boardroom Stone) was deliberately distinct from the four prior runs' registers.

## Phase 1 — `/bridge-brief`

- **Approval turns: 4** — third consecutive run with **zero persona drift**. Split-dispatch is now codified working pattern.
- **Brief saved to:** `output/dogfood-bridge-run-5/creative-brief.md`
- **Arc:** Problem-Solution / Pruning Frame (chosen over Tension-Release and Build-Up-Reveal). Diagnoses fragmentation; presents the portfolio as deliberate pruning; elevates "what we won't build" to equal status with "what we will".
- **Personality + takeaway:** P1 Boardroom Stone + T2 ("We have identified three product areas worth full conviction, and everything outside them is a drag on the company's ability to win in any of them.")
- **Palette derivation:** Auto-derived correctly on first attempt. The "Structural / Primary fill" row pinned the Run 4 Finding #12 heuristic as expected. `BrandPalette(primary_fill_hex='2C2F35', text_on_primary_hex='F4F1EC', text_on_surface_hex='1E1E1C')`. No brief-side workaround needed; the fix from Finding #12's brief template guidance is now the natural authoring shape.
- **Section C marker typology coaching:** Substantially extended from Run 4's. New language for sub-page SMARTART-FROM-LIST scales (side-accent ~3.5×3.5, inline ~3.0×3.0, banner ~10.0×2.0) — directly mirroring Run 4's working IMAGE typology. New language for native-chart routing: *"For any slide whose subject is a data series with axes and category labels — market sizing, capacity allocation, revenue projection, initiative ROI — use a native PptxGenJS chart directly on the slide. Do not place an IMAGE marker on a chart-shaped subject."* New language for BG markers as single structural pivots only.

## Phase 2 — `/pptx` authoring

The thesis: brief Section C with explicit sub-page SmartArt scale typology, plus chart-routing language, would coach `/pptx` into the desired pattern.

**Result: thesis confirmed at every layer.**

13 slides authored with **7 markers + 2 native charts**, exactly matching Section C's coaching:

| Slide | Subject | Tool | Scale |
|---|---|---|---|
| 1 | Title | — | — |
| 2 | Diagnosis prose | — | — |
| 3 | Capacity allocation over time | **Native chart** (stacked bar) | Full content |
| 4 | Conviction-vs-drag schematic | Sub-page IMAGE side accent | 4.7 × 4.0 |
| 5 | Pivot — "From diagnosis. To decision." | **BG marker** (full-bleed) | 13.33 × 7.5 |
| 6 | Pruning principle (3 criteria) | Sub-page SMARTART-FROM-LIST inline | 3.5 × 3.5 |
| 7 | Three bets overview | Sub-page SMARTART-FROM-LIST banner | 10.9 × 2.2 |
| 8 | Bet A platform stack | Sub-page IMAGE side accent | 4.5 × 5.2 |
| 9 | Bet B differentiating attributes | Sub-page SMARTART-FROM-LIST side accent | 4.1 × 4.6 |
| 10 | ROI projection per bet | **Native chart** (line, 3 series) | Full content |
| 11 | What we won't build (5 initiatives) | Native table (won't-build slate) | — |
| 12 | What changes now (5 decisions) | Sub-page SMARTART-FROM-LIST side accent | 5.1 × 4.0 |
| 13 | Verdict (takeaway sentence) | — | — |

- **0 BG markers across all four prior runs at marker level → 1 BG marker in Run 5.** First time exercised end-to-end.
- **4 sub-page SMARTART-FROM-LIST markers across 4 different scales (inline / banner / side-accent ×2)** — Run 5's primary thesis. The bullet-list shape is authored at sub-page coordinates with `objectName="SMARTART-FROM-LIST:slug"`; the bridge replaces it in place at the same coordinates.
- **2 native charts, ZERO IMAGE markers on chart-shaped subjects.** Run 4 Finding #15 principle in action: the brief Section C language *"do not place IMAGE markers on chart-shaped subjects"* successfully steered `/pptx`.
- **2 sub-page IMAGE markers** for the genuinely-illustrative subjects (conviction-vs-drag schematic, platform-stack architecture).
- **Marker count 7 + 2 native charts across 13 slides** = within budget; native-first principle applied.

### Finding #13 reaffirmed (Run 4)

`process1` (24-char cap) and `list1` (30-char cap) both rejected one of slide 12's bullets ("Sunset pruned initiatives by Q2" — 32 chars). Run 4's hand-abbreviation workaround was used again — this time only 2 of 5 bullets needed shortening. Confirmation that the fix is real v0.1.x patch territory: the bridge should auto-truncate (or layout-route by item-length distribution) when `smartart_from_list` items exceed the cap.

## Phase 3 — `/enrich-deck`

- **7 enrichments planned, 7 applied** (4 SmartArt-from-list + 2 sub-page images + 1 BG).
- **Brand palette derivation worked on first attempt.** No brief-side workaround needed for the heuristic — Boardroom Stone's "Structural / Primary fill" row pinned the slot mapping cleanly.
- **Brand palette injection across 4 SmartArt carriers.** OOXML inspection: 16 diagram parts, 131 srgbClr per carrier, 0 unconverted scheme refs, 68 hits on `#2C2F35` + 38 hits on `#F4F1EC` per `colors.xml`. Contract 1 holds across 4 SmartArt graphics simultaneously.
- **Sub-page SMARTART-FROM-LIST injection at exact coordinates** — verified via PowerPoint Mac render. Each carrier's `data1.xml` references `list1` layout + brand colors; each rendered slate-on-parchment SmartArt sits at the coordinates the bullet-list shape originally occupied. Title and surrounding prose intact on every SmartArt slide.
- **BG marker at marker level — first run to exercise.** The `BG:diagnosis-to-pruning-pivot` placeholder rect was replaced with the Ollama-generated paper-grain texture on slide 5. Typography ("FROM DIAGNOSIS", "To decision.", italic teal subhead) sits cleanly on top.
- **Image-reviewer pass-through:** 1 PASS (slide 5 BG), 2 REFINE (slides 4, 8 — garbled text labels, Run 4 Finding #15 territory). The dogfood thesis isn't image-text fidelity, so iter1 was kept and applied with `accepted_with_issues` semantics. A production deck would escalate to Phase B Cloud Flash.
- **Cohesion verdict aggregate PASS** — 3 image/background PASS, 4 SmartArt `unassessable_rasterisation` (Finding #6 expected — the LibreOffice limitation).
- **Output:** `output/dogfood-bridge-run-5/presentation-enriched.pptx` (3.5 MB). User-confirmed via PowerPoint Mac PDF export.

### Finding #17 (NEW — release-shaping for build.js authoring)

**Issue:** When the build.js author supplies a BG marker as both an `addShape` (rect with `objectName`) AND a separate `addText` label for visual identification at authoring time, the `addText` survives enrichment because `apply_background_in_memory` only replaces the rect with the image — the `addText` is a separate shape on the slide that the bridge doesn't know to remove. For IMAGE markers this works because the generated image visually covers the addText label inside its rect. For BG markers covering the full slide, the addText sits ON TOP of the BG image and shows in the final deck.

**Manifestation:** Slide 5 of the Run 5 enriched deck shows the literal string "BG:diagnosis-to-pruning-pivot" in italic monospace at the top-left, sitting on top of the paper-grain BG image. Cosmetic only — does not break the marker contract.

**Fix paths:**
- (a) Bridge auto-detects and removes any `addText` shapes whose text content matches the marker `objectName`. Cleanest UX, generic fix.
- (b) Document the build.js authoring pattern for BG markers explicitly: "rect only, no addText label" — and update the `addBgMarker` helper in dogfood build.js scripts.
- (c) Both — bridge does the cleanup AND the helper documentation pre-empts.

Recommendation: ship (a) in v0.1.x and document (b) as good practice. (a) is small surface — the bridge already iterates shapes on the slide; it can recognise and drop the marker-label addText with the same shape-name check it already does for the rect.

### Finding #18 (NEW — cosmetic but matters for cost reporting)

**Issue:** `VALID_COST_KINDS` in `src/measurement.py` is `{'generation', 'review'}`. Cohesion review is conceptually different — it's a deck-level review, not a per-image review. Run 5 had to record cohesion cost as `kind="review"` with `provider="sonnet-cohesion"` as a workaround.

**Fix:** Add `'cohesion'` to `VALID_COST_KINDS` so the bridge can track deck-level review cost separately from per-image review. Trivial change.

**Why it matters:** Enterprise customers need to attribute costs accurately. Today the report rolls up cohesion cost into the same bucket as image reviews; tomorrow that conflation gets cited in a costing argument.

## Cost summary

| Phase | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 |
|---|---|---|---|---|---|
| Phase 1 (off-budget per Finding #8) | 4 dispatches | 6 dispatches | 4 dispatches | 4 dispatches | **4 dispatches** |
| Phase 3 generation (Ollama, free) | $0.00 | $0.00 | $0.00 | $0.00 | **$0.00** |
| Phase 3 reviews (Haiku image-reviewer) | $0.04 | $0.025 | $0.025 | $0.020 | **$0.015** (3 images) |
| Phase 3 cohesion (Sonnet) | $0.02 | $0.020 | $0.020 | $0.020 | **$0.020** |
| **Phase 3 total** | **$0.06** | **$0.045** | **$0.045** | **$0.040** | **$0.035** |

Run 5 is the cheapest Phase 3 yet ($0.035) despite running 7 enrichments + cohesion review. Reason: 3 image generations vs Run 4's 4 (Run 5 substituted IMAGE markers for native charts on 2 slides per Finding #15 — fewer Ollama calls, fewer reviews, no fidelity loss).

---

## Leading practices to entrench (additions from Run 5)

These add to the six leading practices already entrenched after Run 4. Each one is a pattern Run 5 proved works and that should become the default for future runs.

### 7. Sub-page SMARTART-FROM-LIST coaching is sufficient when Section C provides explicit scale typology

Run 5's primary thesis. The bullet-list shape is authored at sub-page coordinates by `/pptx`; the bridge replaces it in place at the same coordinates with the brand-coloured SmartArt graphic. Title and surrounding prose stay intact. Validated at four scales in Run 5 (inline 3.5×3.5, banner 10.9×2.2, side-accent 4.1×4.6, side-accent 5.1×4.0).

**Entrench:** Run 5's brief Section C (`output/dogfood-bridge-run-5/creative-brief.md`) is now the canonical example for sub-page SmartArt coaching. The Narrative Brief Architect persona's Section C output template should always include sub-page SmartArt scale typology with explicit inch dimensions, mirroring the IMAGE typology. Full-content-zone SmartArt becomes the secondary pattern (reserved for graphic-only divider slides).

### 8. Native-chart routing via Section C language

When Section C explicitly states *"for chart-shaped subjects (X-vs-Y with axes and labels) use a native PptxGenJS chart, not an IMAGE marker"* — `/pptx` honours it. Run 5 produced 2 native charts (capacity allocation stacked bar, ROI projection line chart), zero IMAGE markers on chart-shaped subjects. The chart-shaped subjects in this deck (capacity allocation, ROI projection) read in brand palette without text corruption.

**Entrench:** Section C marker typology should always include the chart-routing paragraph. Until the bridge ships a `CHART:slug` marker kind (v0.2 milestone), this Section C language IS the chart-routing mechanism. Run 5's Section C native-charts subsection is the canonical wording.

### 9. BG marker at marker level works for the structural pivot pattern

Run 5 was the first run to exercise BG markers at marker level across five attempts. The pattern: ONE BG marker on the single structural-pivot slide, scoped to atmospheric institutional-document texture (not photographic, not cinematic), warm-palette only, sits beneath typography. Validated end-to-end: paper-grain texture renders behind the "FROM DIAGNOSIS / To decision." pivot without competing with the typography.

**Entrench:** The brief Section C BG marker subsection should be reproduced for any deck where the narrative has a structural register-shift pivot (Pruning Frame's diagnosis-to-intervention; Tension-Release's tension-to-release; Build-Up-Reveal's accumulation-to-reveal — most arcs have one). Default brief recipe: "0–1 BG markers, on the single structural pivot slide if it exists. The deck's surface colour IS the atmosphere on every other slide."

### 10. `/pptx` "won't-build" semantic encoding via colour reservation

Run 5's brief reserved teal accent (`#4A8C7E`) for "will build" emphasis only and pushed the "won't build" tier into won't-build slate (`#6B7280`) — the same slate as structural chrome, formally drawn but de-energised. `/pptx` honoured this on slide 11's pruning table (every "PRUNED" / "DEFERRED" status in slate, every rationale in slate, no teal anywhere on the won't-build slide). The visual semantic carries the strategic argument: the pruned items are visually present and respected, but they don't get the colour that signals commitment.

**Entrench:** When a deck has a strategic dichotomy (will / won't, ship / defer, in-scope / out-of-scope), brief Section B should explicitly map ONE accent colour to the affirmative side and reserve a structural-chrome-adjacent slate for the negative side. The semantic encoding lets `/pptx` produce slides where the visual makes the argument before the text does.

---

## Anti-patterns to avoid (Run 5 specifics)

### 6. BG marker placeholder pattern with addText label

The build.js helper that authored Run 5's BG marker placed both an `addShape(rect, objectName=BG:slug)` AND a separate `addText("BG:slug", ...)` label for visual identification during authoring. The addText survives enrichment and shows up in the final deck on top of the BG image (Finding #17).

**Deprecate by:**
- Bridge auto-detects and removes addText shapes whose text matches the marker `objectName` (Finding #17 fix path A — recommended)
- Update the dogfood `addBgMarker` helper to omit the addText label (Finding #17 fix path B — immediate workaround)
- Both, ideally

**Practical rule for now:** when authoring a BG marker in build.js, omit any standalone addText label. The placeholder rect's `objectName` is enough for the bridge analyser to find it.

### 7. Cost ledger conflates cohesion with image review

`VALID_COST_KINDS = {'generation', 'review'}` doesn't have a `cohesion` bucket. Run 5 recorded cohesion as `kind="review", provider="sonnet-cohesion"`. Cosmetic for individuals on Max contracts; substantive for enterprise cost attribution.

**Deprecate by:** v0.1.x patch — add `'cohesion'` to `VALID_COST_KINDS`. Update enrichment-report summary to surface cohesion cost as its own line.

---

## Run 6 thesis (open candidates)

Five runs across five distinct visual personalities have validated the bridge's core mechanics and authoring contracts. The remaining cycle paths still NOT exercised are:

- **Phase A → Phase B cloud escalation (Ollama → Flash).** Every Ollama refine_and_retry has recovered in Phase A across all five runs; cloud has never triggered. Run 6 could deliberately route an Ollama-impossible subject (text-heavy diagram, photographic portrait, brand-glyph reproduction) to force the escalation path.
- **Phase B → Phase C escalation (Flash → Pro).** Never reached.
- **`terminate_pending_confirmation` privacy gate handshake.** Internal tier set in Runs 3, 4, 5 — but the gate only fires at first cloud escalation, which has never happened.
- **`prompt-engineer` agent in `mode: "refine"`.** Run 4 USED this mode (slides 4/7/9 refinement) — already covered. Skip.
- **Cohesion verdict `surface_to_user`.** Never triggered (`flag_contrast` mapped to `regenerate` both times). Run 6+ target — needs a regenerated image that STILL fails cohesion to surface.

Two viable Run 6 directions:

1. **Cloud escalation run.** Author a deck with Ollama-impossible content (deliberate text-rendering subjects, photographic portraits, or precise-glyph requirements) at internal tier. Forces image-reviewer refine → Ollama still fails → escalate Phase B → privacy gate fires → first cloud confirmation handshake. May trigger Phase C on hardest cases. Validates three uncovered cycle paths in one run.
2. **CHART marker kind spike.** Implement the v0.2 `CHART:slug` marker (Finding #15) as a small bridge change; Run 6 deck uses CHART markers for chart-shaped subjects (instead of relying on Section C language to redirect). Validates whether the marker kind is materially better than Section C-only routing, or whether the language was sufficient.

Recommendation for Run 6: option 1 (cloud escalation). It clears three uncovered cycle paths in a single run and unblocks Task 35's GO verdict. Option 2 is genuine v0.2 work that doesn't gate on the v0.1.0 release. Run 7 can do option 2 with the bridge changes already shipped.

If Run 6 lands cleanly, the v0.1.0 release scorecard's Item 5 flips green and the bridge is ready to ship.
