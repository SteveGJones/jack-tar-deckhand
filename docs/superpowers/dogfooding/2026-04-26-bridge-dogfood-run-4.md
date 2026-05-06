# Bridge Dogfood Run 4

**Date:** 2026-04-26
**Topic:** Reading the build log — a quarter in incidents and lessons
**Audience:** Engineering leadership
**Duration:** 15 min
**Confidentiality:** internal
**Budget cap:** $2.00
**Visual personality:** Redline (warm light `#F5F4F0` paper, near-black `#1A1A1A` body, failure red `#B91C1C`)
**Arc:** Build-Up-Reveal

**Status:** Phase 1+2+3 complete. Cohesion verdict aggregate PASS (4 image PASS, 3 SmartArt `unassessable_rasterisation`). PowerPoint Mac manual gate run by user — confirmed deck assembles correctly; surfaced two design observations that shape Run 5.

**Why a fourth run:** Run 3 demonstrated brand-native SmartArt (Contract 1 implemented + validated) but every SmartArt still consumed the whole slide. Speaker observation after Run 3: *"these are all still just full slides though, there isn't a case of using SmartArt within a subsection of a page (or of using an image within a subsection of a page come to think of it)."* Run 4 was framed to (a) test whether brief Section C alone could coach `/pptx` into sub-page markers (both SMARTART-FROM-LIST and IMAGE), (b) exercise the Contract 2 SMARTART-FROM-LIST contract end-to-end, and (c) deliberately try a fourth visual register (Redline / data-led incident report) to see whether the brief language scales to prose-heavy decks.

## Phase 1 — `/bridge-brief`

- **Approval turns: 4** — same as Run 3, **zero persona drift**.
- **Brief saved to:** `output/dogfood-bridge-run-4/creative-brief.md`
- **Arc:** Build-Up-Reveal (chosen over Audit-Plus-Action and three-act dramatic)
- **Personality / takeaway:** Visual personality P3 (Redline) + Takeaway A3 ("Every incident we had this quarter was visible in the build log before it became an incident.")
- **Split-dispatch held**: R1 (arcs) → R2 (personality + takeaway) → R3a (Sections A+B) → R3b (Section C). Codified as Finding #7's working pattern; now reproduced across two consecutive runs without drift.

### Finding #11 (NEW — fixed in same session)

**Issue:** First R3 dispatch produced a clean draft with a palette table inline. After approval, `parse_brief_markdown` → `write_brief_markdown` round-trip dropped the palette table from Section B. The bridge's `_VISUAL_RE` regex was single-line and stopped at the first heading-or-table line, capturing only the visual_personality prose paragraph.

**Fix:** Added `_VISUAL_BLOCK_RE` — multiline-mode regex that captures everything between `**Visual personality:**` and the next `## ` heading. Falls back to single-line capture if the block doesn't match (preserves backward compat with old briefs that lacked palette tables). Brief writer now round-trips palette tables faithfully.

**Verification:** 19 colors_xml_builder tests added covering markdown table format and palette derivation tiers; full bridge suite at 225 tests passing.

### Finding #12 (NEW — worked around in brief, deferred bridge fix)

**Issue:** Run 4's Redline palette is structurally minimal — surface (warm light), body text (near-black), failure red (single accent), nominal grey, divider, marker placeholders. No "primary fill" or "structural fill" semantic role appears in the typical accent-led palette tokens. The heuristic in `derive_palette_from_brief_text` returned an incorrect mapping on first attempt because "primary " keyword in the row labelled "Primary slide background" matched the `primary_fill_hex` slot (intended for the structural near-black, not the surface).

**Brief-side workaround:** Added explicit row "Structural / Primary fill | `#1A1A1A`" to the palette table, pinning the heuristic. With this row present, derivation correctly produces `BrandPalette(primary_fill_hex='1A1A1A', text_on_primary_hex='F5F4F0', text_on_surface_hex='1A1A1A')`.

**Bridge-side fix deferred to v0.1.x:** The heuristic is keyword-based with tiered priorities. For accent-only palettes (no explicit "structural" or "primary fill" token), the heuristic should infer structural from "body text" + "near-black" + presence of a single saturated accent. Captured as Finding #12 backlog.

## Phase 2 — `/pptx` authoring

The thesis: brief Section C, with no per-slide pre-prescription, should be enough to coach `/pptx` into the desired sub-page marker pattern.

**Result: thesis confirmed.** `/pptx` authored 13 slides with 7 markers at varied sub-page scales:

| Slide | Marker | Scale | Author's choice |
|---|---|---|---|
| 2 | `SMARTART-FROM-LIST:reading-rules` | 12.1 × 2.7 (content-zone) | full-zone bullet shape between title and supporting prose |
| 4 | `IMAGE:drift-recall-curve` | 5.2 × 4.0 | side accent, right margin alongside body |
| 6 | `IMAGE:retry-storm-state` | 3.0 × 3.0 | inline accent, right of body prose, paired with big-stat below |
| 7 | `IMAGE:retry-cascade-timeline` | 12.1 × 1.7 | banner across content width above body prose |
| 9 | `IMAGE:eval-distribution-shift` | 4.0 × 4.0 | side accent in right margin alongside body |
| 10 | `SMARTART-FROM-LIST:root-cause-clustering` | 12.1 × 3.4 (content-zone) | full-zone |
| 12 | `SMARTART-FROM-LIST:closing-practice` | 12.1 × 3.5 (content-zone) | full-zone |

- **0 BG markers** — Redline brief told `/pptx` the warm-paper surface IS the atmosphere; honoured.
- **Native layouts** for everything that wasn't a marker: severity table (slide 3), monospace log fragments (slides 5, 7, 8), stat callouts (slide 6), text-only reveal (slides 11, 13).
- Marker count 7 / 13 = 54% — within the brief's 5–8 budget across ~13 slides.

**The IMAGE pattern worked at every scale.** Side accent, inline accent, and banner all placed correctly with body prose flowing around them. This is the core sub-page contract holding under varied geometry.

**The SMARTART-FROM-LIST pattern preserved title + supporting prose** but `/pptx` defaulted to full-content-zone width for the bullet shapes. The brief's coaching language for SmartArt didn't include sub-page scale guidance the way the IMAGE coaching did. Captured as Finding #16.

### Finding #13 (NEW — Run 4 fix-by-hand)

**Issue:** `process1` (Basic Process / chevron) caps labels at 24 chars; `list1` (Basic List) caps at 30. Run 4's SMARTART-FROM-LIST bullets ranged 50–70 chars (prose rules, root-cause statements, closing practices). The bridge's `smartart_from_list` spec auto-build path did not truncate — `apply_enrichment` failed at `_check_constraints` with `FlatListBuildError`.

**Workaround for Run 4:** Hand-supplied `smartart_spec` per item with abbreviated 25–30 char labels using `list1` layout. Meaning preserved; nuance lost.

**Fix path:** `smartart_bridge.build_spec_from_slide` already has `_truncate_to_cap` for the `smartart` kind. The `smartart_from_list` branch in `enrichment.py` should call the same truncation, OR the smartart-selector should pick a layout based on item-length distribution (long-prose lists → vList variants with no per-line cap). Both options surface text fidelity tradeoffs that should be made explicit, not silent.

### Finding #14 (NEW — cosmetic)

**Issue:** `EnrichmentReport.summary` counts `kind=="smartart"` only; a deck with 3 SMARTART-FROM-LIST enrichments shows `smartart=0` in the report header. The per-enrichment ledger table is correct.

**Fix:** Aggregate both kinds, or add a `smartart_from_list=N` row.

## Phase 3 — `/enrich-deck`

- **7 enrichments planned, 7 applied** (3 SmartArt-from-list + 4 sub-page images).
- **Brand palette derivation worked end-to-end** — derived from brief automatically, passed through `apply_enrichment`, patched into all three SmartArt carriers' `colors.xml`. Verified: 131 srgbClr per carrier, 0 unconverted scheme refs, 93 hits on `#1A1A1A` + 38 hits on `#F5F4F0`. Contract 1 holds across all three SmartArt graphics.
- **Sub-page IMAGE placement at exact coordinates** — all 4 images sit at the marker's exact rectangle. Body prose preserved alongside. Cohesion review confirmed PASS on all 4.
- **Image generation cycle**: 4 initial Ollama generations + 3 prompt-engineer refine dispatches + 3 iter2 generations. Slide 6 PASS on iter1; slides 4/7/9 ran refine_and_retry within Phase A. For slide 4 iter2 was worse (Ollama interpreted "step function" as a vertical spike) so iter1 was kept; iter2 used for slides 7 and 9. No cloud escalation needed for the dogfood thesis (Phase B / Phase C still untested in any run).
- **Cohesion review verdict: aggregate PASS** — 4 image PASS, 3 SmartArt `unassessable_rasterisation` (Finding #6 LibreOffice limitation, expected).
- **Output:** `output/dogfood-bridge-run-4/presentation-enriched.pptx` (3.0 MB).

### What user-side validation surfaced (PowerPoint Mac PDF export)

User exported the enriched deck to PDF from PowerPoint and reviewed it in full. Two observations that shape Run 5:

#### Finding #15 (NEW — release-shaping)

**Observation:** *"the generated images aren't always text clear, and I'm unsure why we didn't use our graphing capabilities in these cases rather than generative, unless the images are purely indicative not actuals."*

**Root cause:** Three of the four IMAGE markers in Run 4 were chart-shaped subjects:
- Slide 4 `drift-recall-curve` — line graph (recall vs version-bumps over a quarter)
- Slide 7 `retry-cascade-timeline` — banner timing diagram (retry events over 11 minutes)
- Slide 9 `eval-distribution-shift` — overlapping density distributions (eval-set vs production query frequency)

Charts have factual values that need rendering, not approximation. Generative AI (Ollama z-image-turbo at 8 steps, 1024×1024 to 1280×256) produced output that looked clinically right at thumbnail scale but corrupted at slide scale: hex codes bleeding into tick labels (`1A1A`, `B91A`, `BB1A` instead of `Jan`, `Feb`, `Mar`), category names garbled (`duuation` instead of `production`), log-fragment text reading `request_acconot 99theld >` instead of `request_timeout 99p > threshold`.

The fourth image (slide 6 `retry-storm-state`) is a system-state line-art diagram — that one is a legitimate generative candidate, and it PASSED on iter1 with no garbled text.

**The deckhand pipeline already has `src/render_chart.py`.** Native chart rendering would have produced faithful axes, faithful labels, and the same Redline palette. We routed three chart subjects to generative AI when we had a chart renderer.

**Implication for v0.2:** Either (a) introduce a `CHART:slug` marker kind in the bridge that takes structured data + routes to `render_chart.py`, OR (b) update the brief's Section C marker typology guidance to differentiate generative-appropriate (system-state, photographic, atmospheric) from chart-appropriate (factual data with axes/labels), with explicit "use a native chart, not an IMAGE marker" language. Recommendation is (a) — the bridge should encode the routing rather than relying on the persona to make the right call every time.

#### Finding #16 (NEW — release-shaping)

**Observation:** *"Smart Art is still 'full slide' but the use of feature images is very strong"*

**Root cause:** Even though the bullets-IS-the-marker contract preserves title + supporting prose around the bullet shape, `/pptx` authored all three SMARTART-FROM-LIST bullet shapes at content-zone width (12.1 × 2.7 / 3.4 / 3.5). The resulting SmartArt graphic dominated each slide visually — same problem as Run 3, just with prose on either side. By contrast, the IMAGE markers worked beautifully at sub-page scales (3×3 / 4×4 / banner / 5.2×4) because the brief's Section C explicitly coached scale variety with size guidance ("inline accent ~1.5–2.0 inches square", "side accent ~2.5–3.5 inches wide", "banner ~10 inches wide × ~1.5–2.0 inches tall").

The brief's SmartArt guidance had no equivalent scale typology. SMARTART-FROM-LIST appeared as a "preferred pattern" but with no instruction that the bullet shape itself can be authored at sub-page scale — small bullet list in the right margin alongside body prose, replaced by sub-page SmartArt at the same coordinates.

**Implication for Run 5:** The thesis is whether brief Section C can coach `/pptx` into sub-page SMARTART-FROM-LIST markers — e.g., a 4×4 bullet list in the right margin that the bridge replaces with a sub-page SmartArt graphic at the same coordinates. Tests whether the bullets-IS-the-marker contract holds at varied scales the same way IMAGE markers did. If it works, sub-page SmartArt becomes the default visual recipe; full-zone becomes reserved for synthesis/divider slides.

## Cost summary

| Phase | Run 1 | Run 2 | Run 3 | Run 4 |
|---|---|---|---|---|
| Phase 1 (off-budget per Finding #8) | 4 dispatches | 6 dispatches | 4 dispatches | **4 dispatches** |
| Phase 3 generation (Ollama, free) | $0.00 | $0.00 | $0.00 | **$0.00** |
| Phase 3 reviews (Haiku image-reviewer) | $0.04 | $0.025 | $0.025 | **$0.020** |
| Phase 3 cohesion (Sonnet) | $0.02 | $0.020 | $0.020 | **$0.020** (1 dispatch) |
| **Phase 3 total** | **$0.06** | **$0.045** | **$0.045** | **$0.040** |

Run 4 is the cheapest end-to-end so far despite running 7 enrichments (vs Run 3's 6 and Run 2's 5). Phase A iteration in Ollama remains free; the marginal cost per additional enrichment is one Haiku review at $0.005.

---

## Leading practices to entrench (the "good" from Runs 1–4)

These are patterns that worked across all four runs. They should become defaults — codified in SKILL.md, brief templates, persona guidance, or test cases — so future authors fall into them rather than rediscover them.

### 1. Split-dispatch persona collaboration (codified after Run 1, validated Runs 2–4)

The Narrative Brief Architect persona drifts when asked to deliver multiple sections in a single dispatch. The four-dispatch pattern (R1 arcs → R2 intent + personality → R3a Sections A+B → R3b Section C) yields zero drift across consecutive runs. Already in `/bridge-brief` SKILL.md as Finding #7's working pattern.

**Entrench:** keep this as the SKILL.md default. Tests should assert the four-dispatch shape in `creative-brief-measurement.jsonl` (current `approval_turns` metric captures this).

### 2. Brief Section C coaching is sufficient for marker placement (validated Run 4)

Run 4's thesis was that brief Section C alone, with no per-slide pre-prescription, could coach `/pptx` into the desired marker pattern. It did. The brief told `/pptx`:
- The marker scale typology (inline accent / side accent / banner / sub-page)
- The marker count budget (5–8 across ~13 slides)
- Which marker kinds to default to (SMARTART-FROM-LIST is "preferred pattern", BG is "nearly absent" in the Redline register)
- Native-first guidance ("for tables, charts, log fragments — use native layouts")

`/pptx` placed 7 markers at the right scales without further coaching.

**Entrench:** the Narrative Brief Architect persona's Section C output template should always include marker scale typology with explicit inch dimensions, marker count budget, and marker kind defaults per visual personality. Run 4's brief is the cleanest example of this so far — preserve it as a reference.

### 3. Sub-page IMAGE marker placement at exact coordinates (validated Runs 3+4)

The bridge places generated images at the marker rectangle's exact coordinates with body prose preserved around them. Validated at four scales in Run 4 (5.2×4 side, 3×3 inline, 12.1×1.7 banner, 4×4 side). This is the strongest single feature surfaced in dogfooding.

**Entrench:** make sub-page IMAGE the default Section C example pattern. The brief Run 4 used (`output/dogfood-bridge-run-4/creative-brief.md`) is the canonical example.

### 4. Brand palette injection is automatic and complete (validated Run 4)

`derive_palette_from_brief_text` produces a `BrandPalette` from the brief's palette table; `apply_enrichment` patches every SmartArt carrier's `colors.xml` before injection; every `schemeClr` becomes the brand `srgbClr`. Run 4 produced 131 srgbClr entries × 3 carriers, 0 unconverted scheme refs, all in `#1A1A1A` + `#F5F4F0`. Brief authors don't pass anything; the SKILL.md does it.

**Entrench:** existing test coverage at 225 bridge tests with 19 colors_xml_builder tests. Maintain CI gate: any change to `apply_enrichment` must preserve the brand-palette path.

### 5. Cohesion review correctly handles `unassessable_rasterisation` (validated Run 4)

The cohesion reviewer was given explicit context that LibreOffice cannot render injected SmartArt and that those slides should be marked `unassessable_rasterisation` not `flag_*`. It honoured that. Verdict aggregate PASS even with 3 of 7 enriched slides unassessable.

**Entrench:** the SKILL.md cohesion-review prompt template should always include the LibreOffice-SmartArt limitation as a known-issue paragraph, even after the limitation is resolved (a fallback for future cases where rasterisation legitimately fails).

### 6. Cycle's cost discipline holds under iteration (validated Runs 3+4)

Phase A refine_and_retry within Ollama costs nothing for generation (free local) — only the additional Haiku review charges. Run 4 ran 4 initial generations + 3 refine generations and the cost delta vs Run 3 was zero on the generation side. Caveat #6's unconditional-review-charge prevents Phase B/C escalation on unpaid verdicts; that gate has held.

**Entrench:** `BudgetCap.charge` and `record_cost_event` invariants are tested. Maintain them.

---

## Anti-patterns to avoid (the "bad" from Run 4 specifically)

These are choices that we made or that the system pushed us toward, that we should NOT repeat. Each one has a recommended deprecation path.

### 1. IMAGE markers for chart-shaped subjects

**What we did wrong:** Coached `/pptx` to author IMAGE markers for line graph, banner timing diagram, and density distribution chart subjects (Slides 4, 7, 9). All three subjects are chart-shaped — factual values rendered as axes + labels — and the deckhand pipeline has `src/render_chart.py` for native chart rendering. Generative AI produced approximate visuals that corrupted at slide scale.

**Deprecate by:**
- Adding a `CHART:slug` marker kind (Finding #15 v0.2 milestone)
- Brief Section C marker typology distinguishes chart-shaped from generative-appropriate subjects, with explicit "use a native chart, not an IMAGE marker" language for the former
- Failing CI test on a chart-routing test deck where IMAGE marker is placed on a chart-shaped subject and we expect a routing redirect

**Practical rule for now:** if the IMAGE marker subject is "X over Y" with axes and labels, it should be a native chart on the slide, not an IMAGE marker.

### 2. Full-content-zone SMARTART-FROM-LIST as default

**What we did wrong:** All 3 SMARTART-FROM-LIST markers ended up at content-zone width (12.1 wide) because the brief's SmartArt guidance had no scale typology equivalent to the IMAGE guidance. SmartArt continues to dominate slides even when title + supporting prose are present.

**Deprecate by:**
- Run 5 thesis: brief Section C coaches sub-page SMARTART-FROM-LIST markers (4×4 inline, side-accent, etc.)
- Once sub-page SmartArt validates, the brief's "SMARTART-FROM-LIST is preferred" paragraph gains a scale typology paragraph mirroring the IMAGE typology
- Full-zone SmartArt becomes reserved for synthesis / divider slides where the graphic IS the slide content

**Practical rule for now:** when authoring a SMARTART-FROM-LIST in the brief or in `/pptx`, ask whether the slide actually needs a full-zone diagram. If body prose is present, prefer sub-page.

### 3. Process1 / list1 layouts for prose-heavy lists

**What we did wrong:** Run 4's bullets ranged 50–70 chars per item; auto-default `process1` (cap 24) and the alternative `list1` (cap 30) both rejected the content. Workaround was hand-abbreviation.

**Deprecate by:**
- Bridge auto-truncation in the `smartart_from_list` spec auto-build path (Finding #13)
- OR smartart-selector picks layout based on item-length distribution (long-prose → vList variants)
- Either way, the failure mode "engine.render failed: layout 'process1' labels must be <= 24 chars" should never reach the SKILL.md user

**Practical rule for now:** if list items exceed 30 chars, supply explicit `smartart_spec` with abbreviated labels OR override layout to a vList variant.

### 4. Brief writer round-trip dropping multiline blocks

**What we did wrong:** Run 4's first brief round-trip dropped the palette table from Section B because the regex was single-line.

**Deprecate by:** already fixed in this session — `_VISUAL_BLOCK_RE` captures multiline content. Regression test added.

### 5. Heuristic palette derivation on accent-only palettes

**What we did wrong:** Run 4's palette structure (no explicit "structural" or "primary fill" token) produced an incorrect mapping; brief-side workaround was an explicit "Structural / Primary fill" row.

**Deprecate by:** Finding #12 backlog — `derive_palette_from_brief_text` should infer structural slot from contextual signals when explicit tokens are absent (e.g., body-text + single-accent palettes).

**Practical rule for now:** brief authors should include an explicit "Structural / Primary fill" row in the palette table. Captured in updated brief template guidance.

---

## Run 5 thesis

Run 5 should test:

1. **Sub-page SMARTART-FROM-LIST coaching.** Can the brief's Section C coach `/pptx` into authoring SMARTART-FROM-LIST markers at sub-page scales (4×4 side accent, 3×3 inline, banner, etc.)? Validates that the bullets-IS-the-marker contract holds at varied scales the same way IMAGE markers did. If it works, sub-page SmartArt becomes the default visual recipe.

2. **Marker typology differentiation for chart-shaped subjects.** Either via (a) a new `CHART:slug` marker kind that the bridge routes to `render_chart.py`, or (b) Section C language that explicitly redirects chart-shaped subjects away from IMAGE markers toward native chart authoring. Run 5 tests whichever path we choose first.

3. **Visual personality choice:** something distinct from Runs 1–4 (Dark Industrial, Engineering Ink, Blueprint Retrospective, Redline) — maybe a presentation-led personality (warmer, less data-led) so the SmartArt sub-page coaching gets exercised on a different register.

The Run 5 deck should produce a richer mix of marker patterns:
- Sub-page SMARTART-FROM-LIST × at least 2 (to validate the new scale variety)
- Sub-page IMAGE × at least 2 (continuing what Run 4 proved works)
- A native chart on at least one slide (no IMAGE marker — to validate the chart-routing principle even before the bridge implements it)
- 1 BG marker (continues to be unexercised across all four runs at the marker level — Run 1's full-zone background was the closest)

If Run 5 lands cleanly, the v0.1.0 release scorecard's Item 5 flips green, and we have an evidence-backed brief template that's ready to ship as the canonical example.
