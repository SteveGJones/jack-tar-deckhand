# Bridge Dogfood Run 2

**Date:** 2026-04-25 (Phase 1) → 2026-04-26 (Phase 2 + 3 completed)
**Topic:** Jack-Tar Engineering Status — quarterly briefing
**Audience:** Engineering leadership
**Duration:** 15 min
**Confidentiality:** public
**Budget cap:** $2.00 (raised from $1.50 default; Speaker decision)
**Visual personality:** Engineering Ink (charcoal `#1C1F24` ground, single teal accent `#2ABFBF`)
**Arc:** Tension-Release ("can the multi-plugin AI bridge produce production-quality output without a human in the loop at every step")

**Status:** Phase 1+2+3 complete. SMARTART verification (3 slides) pending PowerPoint Mac manual gate. No Task 35 verdict yet.

**Why a second run:** Run 1 validated the happy path on a conference-engineer aesthetic. Speaker observation after Run 1: *"the deck is good, but it's not much better than what /pptx alone would produce."* Run 2 was designed to **stress where the bridge actually earns its keep over /pptx** — different audience (executive), different palette register (Engineering Ink, no dark-industrial drama), and explicit toolkit-framing of marker grammar so /pptx could choose where (and where not) to use markers.

## Phase 1 — `/bridge-brief`

- **Approval turns: 6** (Run 1 was 4)
- **Brief saved to:** `output/dogfood-bridge-run-2/creative-brief.md`
- **Brief contains objectName note:** yes
- **Arc:** Tension-Release (Speaker selected from 3 proposed; agent had recommended Build-Up-Reveal)
- **Visual personality:** Engineering Ink (Speaker selected from 3 proposed: P1 Precision White, P2 Engineering Ink, P3 Executive Minimal)
- **Takeaway:** T3 — *"We have done everything a rigorous engineering team should do before calling a system ready — and the only thing we have not done yet is the one thing that cannot be faked: run the full pipeline in the wild."*

### Phase 1 round-by-round behaviour

| Round | Strategy | Outcome |
|---|---|---|
| R1 — propose 3 arcs | Concise dispatch, no prescription | ✓ Three thoughtful arcs; recommendation provided |
| R2 — propose 3 takeaways + 3 personalities | Concise dispatch, locked arc choice | ✓ Three takeaways + three personalities, trade-offs noted |
| R3 — full brief draft | Single-shot whole-brief dispatch with locked decisions | ✗ Wrong arc label ("Build-Up-Reveal"); no opening tension sentence |
| R4 — surgical fix to R3 | "Reproduce verbatim except 2 edits" with full prior brief embedded | ✗ **Severe drift** — rewrote Sections B and C entirely; replaced T3 takeaway, swapped palette to Executive Minimal-ish, added a fourth accent colour, prescribed marker placements |
| R3a — Sections A+B only | Tight scope, locked inputs, hard scope rules ("begin with `## Section A`, end after palette table, do not include Section C") | ✓ Byte-perfect |
| R3b — Section C only | "Reproduce this verbatim" with the approved C in the prompt; explicit start/end tokens | ✓ Byte-perfect |

**The pattern that works:** narrow each dispatch to one or two sections at most, lock prior decisions explicitly, tell the persona where to begin and end. **Whole-brief dispatches drift.** Surgical-edit-of-prior-output drifts EVEN HARDER (R4 was worse than R3, despite — or perhaps because of — the embedded prior brief).

The split-dispatch strategy used to recover (R3a + R3b) is the post-release SKILL.md pattern that should replace the whole-brief dispatch. See Finding #7.

### Phase 1 measurement entry

```json
{"kind": "brief", "timestamp": "2026-04-25T17:31:01.953547+00:00", "approval_turns": 6, "structural_complete": true, "confidentiality": "public"}
```

## Phase 2 — `/pptx`

- **Slides produced:** 15
- **Build script:** `output/dogfood-bridge-run-2/build.js` (~24 KB)
- **Output:** `output/dogfood-bridge-run-2/presentation.pptx` (256 KB)
- **Layout:** `LAYOUT_WIDE` (13.3" × 7.5")
- **Marker adherence (OOXML primary):** **7 markers** (3 BG + 1 IMAGE + 3 SMARTART)
- **Marker adherence (JS fallback):** N/A — `js_fallback_used: False`
- **Duplicate marker IDs:** none
- **Overlap warnings:** 3 (same italic-caption-below-SMARTART pattern as Run 1; intentional for verifier surfacing)

### Marker placement vs Run 1

| | Run 1 (25 slides) | Run 2 (15 slides) |
|---|---|---|
| Slides with markers | 11 (44%) | 7 (47%) — similar density |
| Slides leaning on native PptxGenJS | 14 | **8** |
| Marker counts | 4 BG + 4 IMAGE + 3 SMARTART | 3 BG + 1 IMAGE + 3 SMARTART |

The marker discipline lift is qualitative not quantitative: Run 2 used **native data tables, big-stat callouts, and structured prose with inline accent on 8 slides** — exactly the toolkit-framed Section C said /pptx should reach for those when they serve content better than markers. Examples:
- Slide 4 *"Surface area"* — real PptxGenJS table, six rows, teal-accented `deckhand` and `superpower-bridge` rows. No marker.
- Slide 5 *"Test coverage"* — `1,187` in 140pt teal monospace + three supporting stats. No marker.
- Slide 9 *"Run 1 — what the gate produced"* — three big-stat callouts (`11/11`, `$0.06`, `8/8`). No marker.
- Slide 12 *"What the gate proved"* — structured prose with teal accent on bold lead-ins. No marker.
- Slide 14 *"The takeaway"* — T3 verbatim as a single dramatic 36pt block, accent on the closing phrase. No marker.

### Marker breakdown (per analyser)

| Slide | Marker | Beat |
|---|---|---|
| 1 | `BG:opening-engineering` | Title + tension |
| 3 | `SMARTART:plugin-inventory` | Six plugins as chevron flow |
| 7 | `IMAGE:bridge-architecture` | The bridge as system metaphor |
| 8 | `SMARTART:dogfood-pipeline` | Phase 1 → 2 → 3 process |
| 10 | `SMARTART:findings-status` | 6 findings, fixed/tracked |
| 11 | `BG:verdict-pivot` | Tonal shift to verdict |
| 15 | `BG:closing-verdict` | Final challenge |

**Verdict on Phase 2:** /pptx interpreted the toolkit-framed Section C correctly and made discriminating choices about where markers earn their keep. This was the missing dogfood signal from Run 1 — Run 1 placed markers everywhere a marker *could* go; Run 2 placed markers where they *should* go.

## Phase 3 — `/enrich-deck`

- **Generation backend:** Ollama 0.21.0 (`x/z-image-turbo:fp8`) — local, free
- **Total cost:** **$0.045** (Run 1 was $0.06)
- **Slides enriched:** 7 of 15 (4 BG/IMAGE + 3 SMARTART)
- **Cohesion review (Round 1 — original images):** **`requires_revision`** — slide 15 flagged `flag_contrast` (BLOCKING)
- **Cohesion review (Round 2 — after slide-15 regeneration):** PASS
- **Regeneration cycles:** 1 (slide 15)
- **SMARTART verification:** deferred to PowerPoint Mac manual gate (same as Run 1)

### The cohesion-driven regenerate loop — Run 2's flagship dogfood signal

This is the single most important result from Run 2. **The bridge cycle that Run 1 never exercised — image-reviewer pass-through plus cohesion-reviewer-driven regenerate — fired correctly end-to-end.**

Here's what happened:

1. **Image-reviewer at draft time** approved all 4 images (confidence 0.88-0.92). Each image is on-brand, no artifacts, single accent — image-reviewer's contract is satisfied.
2. **Cohesion-reviewer at deck-assembly time** sees the images **with the deck text overlaid**. It flagged slide 15:
   > Title `Run it in the wild.` (white, 64pt) overlays the bright cyan terminal screen at ~1.5:1 contrast — below WCAG AA 4.5:1. Secondary: bright teal monitor content acts as decoration, violating "teal reserved for emphasis only" palette rule. **Verdict: `flag_contrast`, severity: `blocking`**.
3. **Decision:** regenerate (per the SKILL.md decision table for `flag_contrast`).
4. **Refined prompt** addressed both feedback points: keep the closing-verdict mood (weighty, direct) but move bright accents to the periphery so the centre frame is dark for text overlay.
5. **v2 attempt:** too empty — lost the compositional weight. Visually inspected, rejected by my judgment, regenerated v3.
6. **v3 attempt:** dramatic dark industrial corridor with structural weight on left/right edges, single faint teal pinpoint at the vanishing point — perfect.
7. **Image-reviewer re-review on v3:** PASS (confidence 0.92, no issues). "Centre frame uniformly dark — white text will have strong contrast. Teal accent reduced to single distant pinpoint at vanishing point — atmospheric, not competitive."
8. **Re-apply enrichment with v3** — single transactional call.
9. **Slide 15 re-rendered:** title and subtitle now read cleanly; the teal pinpoint at the corridor's vanishing point sits directly above the subtitle "Then we'll have the verdict." — they line up as if the composition was authored, not generated.

**Why this matters for the bridge's value proposition:** image-reviewer and cohesion-reviewer are doing different jobs. Image-reviewer judges an image *in isolation* against a brief; cohesion-reviewer judges the *composition* (image + text overlay + palette + sister slides). Without cohesion review, the slide-15 contrast violation would have shipped — looking great in the image library, failing on stage. Run 1's perfect cohesion result was actually a missed test of this loop; Run 2 caught what Run 1 couldn't have caught.

### Phase 3 measurement entry

```json
{"kind": "enrichment", "timestamp": "...", "adherence_rate": 1.0, "first_pass_acceptance": false, "slides_enriched": 7, "slides_total": 15}
```

`first_pass_acceptance: false` is the honest signal: cohesion review needed a regen pass to converge.

### Per-image cycle summary

| Slide | Marker | Phase A attempts | Cohesion | Final tier |
|---|---|---|---|---|
| 1 | `BG:opening-engineering` | 1 | pass | ollama |
| 7 | `IMAGE:bridge-architecture` | 1 | pass | ollama |
| 11 | `BG:verdict-pivot` | 1 | pass (0.88, borderline) | ollama |
| 15 | `BG:closing-verdict` | **2** (v1 → v3 after cohesion `flag_contrast`) | pass | ollama |

### Visual spot-check of enriched deck

| Slide | Verdict |
|---|---|
| 1 (BG opening) | Stunning. Backlit circuit-board macro, teal LED highlights on traces, "Six plugins. One open question." reads cleanly over the chip's centred dark surface. |
| 3 (SMARTART plugin-inventory) | LibreOffice render shows blank where SmartArt should be (Finding #6). PowerPoint Mac gate required. |
| 7 (IMAGE bridge-architecture) | Excellent. Cable-stayed bridge in cool grey on charcoal, single teal accent at midspan connection. The architectural drawing aesthetic carries the "what's new" framing perfectly. |
| 11 (BG verdict-pivot) | Server room with rows of racks, teal indicator lights. Title contrast borderline per cohesion reviewer; passable due to font weight. |
| 15 (BG closing-verdict, v3) | After regen: dark industrial corridor with structural weight, single teal pinpoint at vanishing point, title and subtitle read cleanly. Cohesion fix end-to-end. |

## Verdict

(Task 35 — pending PowerPoint Mac SMARTART verification + Speaker review of both Run 1 and Run 2 enriched decks.)

---

## Findings updated by Run 2

### Finding #3 — ELEVATED to release blocker (was: persona-prompt hardening recommendation)

Run 1 had one drift incident (Round 3) recovered by Round 4 verbatim-prompting. Run 2 reproduced drift in Round 3 *and* Round 4 — and Round 4's drift was *worse* than Round 3's, despite the explicit verbatim-preservation prompt with the prior brief embedded.

**The persona contract cannot be relied on for whole-brief or surgical-edit dispatches.** Multi-section dispatches drift. This is not flaky behaviour — it's reproducible across two runs.

**Resolution:** see Finding #7 for the prompting pattern that works. The persona contract should bake this in.

### Finding #7 (NEW) — Split-dispatch is the working pattern for the Narrative Brief Architect

After R3 and R4 both drifted in Run 2, recovery came from splitting the brief into two dispatches: R3a (Sections A + B with locked inputs and explicit start/end tokens) and R3b (Section C only, with the approved-section content quoted in the prompt and "reproduce verbatim" as the instruction). Both came back byte-perfect.

The pattern:
- **One section per dispatch** (or at most two tightly-coupled sections like A + B which share the arc/takeaway/palette commitments).
- **Hard scope rules at the top of the prompt** — "begin your output with `## Section X — Title`" and "end your output with `<specific closing token>`".
- **All upstream decisions explicitly locked** — "ARC: Tension-Release", "TAKEAWAY (use verbatim)", "VISUAL PERSONALITY (with these hex values)" — not "you previously selected X".
- **For sections being preserved from a prior round, embed the section content verbatim in the prompt** with a "reproduce this verbatim" instruction, AND name the start/end tokens.

**Recommendation:** the SKILL.md `/bridge-brief` orchestration should drive section-by-section dispatch from the start, not whole-brief drafting. The persona contract should document the pattern. The 4-turn target stays achievable: R1 arcs, R2 intent+personality, R3a Section A+B, R3b Section C. The persona's existing temptation to "rewrite to revise" is then designed-out rather than fought-against.

### Finding #8 (NEW) — Phase 1 LLM costs are unmeasured (matters for API/enterprise customers)

The bridge's `BUDGET_CAP_USD` (set in the brief, default $1.00, raised to $2.00 in this run) covers Phase 3 only — `kind: generation` and `kind: review` events. The narrative-brief-architect dispatches in Phase 1, and the prompt-engineer compose dispatches in Phase 3, are off-budget. They are real LLM API costs, but the bridge does not track or cap them.

**For Max subscribers (this dogfood):** zero practical impact — subscription absorbs the cost.

**For enterprise/API customers shipping the bridge in their own pipelines:** the budget cap they set in the brief gives them **false confidence** that cost is controlled. A drifty persona round (caught in this run) consumes real tokens off-budget. With Run 2 needing 6 brief-architect dispatches at growing context size, Phase 1 cost can plausibly equal or exceed Phase 3 cost — invisible to the cap.

**Recommendation:** extend the cost ledger to record `kind: composition` events for narrative-brief-architect and prompt-engineer compose/refine dispatches. Surface them in the enrichment report as a separate counter. Either roll into the budget cap or keep separate, but stop being silent about them.

---

## What Run 2 dogfooded that Run 1 didn't

The flagship: **the cohesion-driven regenerate loop** (image-reviewer pass → cohesion `flag_contrast` → prompt refinement → regen → re-review pass → re-apply). Run 1's images all passed cohesion first time; Run 2's slide 15 didn't, and the path forward worked end-to-end.

Other previously-not-exercised paths that Run 2 added:
- /pptx using the toolkit-framed Section C to *not place markers* on 8 slides (Run 1 effectively had a marker on every slide that could carry one).
- Native PptxGenJS table rendering with palette-aware row styling (the surface-area table on slide 4 — teal-accented in deckhand and bridge rows).
- Big-stat numerical callouts as the dominant slide content (slides 5, 9, 14) — proves /pptx native is actually strong on data dramatisation, the bridge doesn't need to handle this.

## What's still not exercised after both runs

These cycle paths have never fired in either run:
- **Cycle escalation Ollama → Flash (Phase B)** — every Ollama draft passed first review (or first cohesion review after one regen).
- **Cycle escalation Flash → Pro (Phase C)** — never reached.
- **Cross-tier prompt refinement loop** — no image needed inter-tier refinement.
- **`terminate_pending_confirmation` privacy gate** — both runs were public tier; no internal/restricted handshake exercised.
- **`apply_clear_overlap` action** — both runs declined it on first pass to test the verifier; never applied.
- **Cohesion verdict `surface_to_user`** — Run 1 had no flags; Run 2's `flag_contrast` mapped to `regenerate` in the orchestrator, not `surface_to_user`.
- **`prompt-engineer` agent in `mode: "refine"`** — Run 2 composed the slide-15 refinement prompt by hand rather than dispatching prompt-engineer. The contract for refine mode hasn't been exercised end-to-end.
- **Persona-cohesion edge case where regen v1 → v3 fails twice** — would force `surface_to_user`. Run 2 succeeded on v3 (after v2 was rejected by my visual judgment, not by an agent).

A future Run 3 could deliberately seed a hard-to-render brief or set `confidentiality: internal` to exercise the remaining paths.

## Cost summary

| Phase | Run 1 | Run 2 |
|---|---|---|
| Phase 1 (off-budget — see Finding #8) | ~4 dispatches | ~6 dispatches (drift cost +50%) |
| Phase 3 generation (Ollama, free) | $0.00 | $0.00 |
| Phase 3 reviews (Haiku image-reviewer) | $0.04 | $0.025 |
| Phase 3 cohesion (Sonnet) | $0.02 | $0.020 |
| **Phase 3 total (bridge-tracked)** | **$0.06** | **$0.045** |

Run 2 ran ~25% cheaper than Run 1 in Phase 3 despite needing a regeneration. Reason: fewer markers (7 vs 11) means fewer image-reviewer dispatches.

## Conclusion

Run 2 strengthens the case for the GO verdict. The bridge's value over vanilla /pptx is now visible: the toolkit-framed marker grammar produces *discriminating* marker placement (Run 2's 8 unmarked slides), and the cohesion review catches deck-assembly bugs that image-review alone cannot (Run 2's slide-15 contrast violation, caught and resolved end-to-end).

The persona contract has a known brittleness on multi-section dispatches (Findings #3 + #7) that the SKILL.md should address before public release. It is not a blocker for an internal v0.1.0 — the working pattern (split-dispatch) is documented and reproducible — but it is a material rough edge for any third-party customer.

Findings list after Run 2:
- **Fixed in flight:** #1 (rglob), #2 (namespace), #3 (persona drift soft-fix attempt — now insufficient)
- **Open / release-affecting:** #3 (escalated), #4 (SMARTART parser), #5 (process1 label cap), #7 (split-dispatch pattern needs codifying), #8 (Phase 1 cost tracking)
- **Known limitation, accepted:** #6 (LibreOffice cannot render injected SmartArt — handled via PowerPoint Mac manual gate)
