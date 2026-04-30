# Bridge Dogfood Run 6

**Date:** 2026-04-29
**Topic:** Project Cardinal — Tessera AI acquisition recommendation
**Audience:** Board / M&A committee
**Duration:** 15 min
**Confidentiality:** internal
**Budget cap:** $5.00
**Visual personality:** Velvet Ledger (warm ivory `#FAF7F2`, ox-blood burgundy `#5C1A2A`, antique gold `#B8860B` reserved for affirmative/verdict, muted mauve-grey `#7A6E72` for risks/de-emphasis)
**Arc:** Investigation-Verdict

**Status:** Phase 1+2+3 complete. PowerPoint Mac PDF export confirms all enrichments render — 7 Pro-tier IMAGE markers, 1 Ollama BG, and 1 brand-coloured SmartArt-from-list inject in the side-accent zone with all five synergy items legible. Cohesion verdict aggregate PASS.

**Why a sixth run:** Runs 1–5 had never exercised three uncovered cycle paths — Phase A → Phase B Flash escalation, Phase B → Phase C Pro escalation, and the `terminate_pending_confirmation` privacy gate handshake. Run 6 was framed to force all three in a single deck by deliberately routing Ollama-impossible content (brand-glyph reproduction, photographic portraits, technical labels) at internal tier. The Velvet Ledger personality (ivory + ox-blood + antique gold + mauve-grey) was deliberately distinct from the five prior runs' registers and tuned for institutional / M&A board gravitas.

## Phase 1 — `/bridge-brief`

- **Approval turns: 4** — fourth consecutive run with **zero persona drift**. Split-dispatch is now codified working pattern.
- **Brief saved to:** `output/dogfood-bridge-run-6/creative-brief.md`
- **Arc:** Investigation-Verdict (chosen over Build-Up-Reveal and Tension-Release). Boards behave like judicial bodies, not narrative audiences; the conditional approval structure ("approve under these three conditions") maps naturally onto Investigation-Verdict's evidence-then-verdict flow.
- **Personality + takeaway:** P1 Velvet Ledger + T1 ("Tessera AI is the right acquisition at this window: we recommend conditional approval, contingent on IP warranty, founder retention lock-up, and edge-model revenue verification at close.")
- **Palette derivation:** Auto-derived correctly on first attempt. Run 4 Finding #12 brief-template heuristic worked with zero workaround. `BrandPalette(primary_fill_hex='5C1A2A', text_on_primary_hex='FAF7F2', text_on_surface_hex='1A0C10')`.
- **Section C marker typology coaching:** 6 IMAGE markers (slides 4 / 5×2 / 6 / 7 / 8 / 9) at sub-page scales, 1 SMARTART-FROM-LIST (slide 11 side-accent), 1 BG (slide 10 pivot full-bleed), 3 native charts (slides 3 / 8 / 13). Native chart routing language explicitly redirected chart-shaped subjects to `addChart()` (Run 5 pattern entrenched).

## Phase 2 — `/pptx` authoring

13 slides authored with **9 markers + 3 native charts + 1 native table**, exactly matching Section C's coaching:

| Slide | Subject | Tool | Scale |
|---|---|---|---|
| 1 | Title — Project Cardinal | — | — |
| 2 | Executive summary | — | — |
| 3 | Why now — TAM trajectory | **Native chart** (line, 2 series 2023–2030) | Full content |
| 4 | Target snapshot | Sub-page IMAGE (Tessera wordmark, side-accent right) + financial table left | 5.0 × 3.6 |
| 5 | Founders | **2× sub-page IMAGE** (CEO + CTO portraits, paired inline) | each 4.2 × 4.0 |
| 6 | Product — Edge Stack architecture | Full-content IMAGE (technical diagram with 4 labels + sidebar) | 12.13 × 5.0 |
| 7 | Customer footprint | Full-content IMAGE (7-logo grid, fintech + healthcare) | 12.13 × 5.0 |
| 8 | Comparables | Banner-top IMAGE (5-logo strip) + native chart (EV/ARR multiples) | banner 12.13 × 1.4 + chart 12.13 × 3.4 |
| 9 | Strategic fit | Full-content IMAGE (2 blocks + 3 arrow labels, gold seam) | 12.13 × 5.0 |
| 10 | Pivot — "From opportunity. To decision." | **BG marker** (full-bleed, atmospheric paper-grain) | 13.33 × 7.5 |
| 11 | Synergies | Sub-page SMARTART-FROM-LIST (5 bullets, side-accent right) | 5.6 × 4.5 |
| 12 | Risks + mitigations | Native table (4 rows × 2 cols, mauve-grey header) | — |
| 13 | Deal structure | Native chart (consideration breakdown bar) | 6.33 × 5.0 |
| 14 | Verdict | Text only — gold-styled key conditional terms | — |

- **9 markers detected by analyser** via OOXML primary path (zero JS fallback, zero duplicates, zero overlap warnings)
- **`objectName` API correctly used** throughout — Spike 1 pattern entrenched
- **BG marker Finding #17 caveat respected** — slide 10 has rect only, no `addText` label. Pivot text "FROM OPPORTUNITY. To decision." authored as separate text shapes on top of the BG image.
- **Verdict slide gold styling** — the four conditional terms ("conditional approval", "IP warranty", "founder retention lock-up", "edge-model revenue verification") rendered in `#B8860B` via PptxGenJS rich-text runs

## Phase 3 — `/enrich-deck`

**The headline result: all three uncovered cycle paths fired in one run.**

### Cycle path 1 — Phase A → Phase B Flash escalation ✓

Four text-bearing IMAGE markers (slides 6 / 7 / 8 / 9) exhausted Phase A across three Ollama attempts each because `x/z-image-turbo:fp8` corrupted the brand-glyph text reliably:
- Slide 6 attempt 1: "Client Edge **Nodies**" / "**Inforance Laber**" / "Cloud **Sygec Eepidnt**" / "**Cegjlator** Engagement"
- Slide 7 attempt 1: "**Merian** Bank" / "Regio Health **Systenas**" / "Procyon **Phema**" / "**Nivera Diagnoostics**"
- Slide 8 attempt 1: "**Modurar** Labs" / "**Fatic** AI" / "Prism **Inforence**" / "Apex **Cempute**"
- Slide 9 attempt 1: "API **Getbowt**" / "Bolling **Playck**" / "Model **Regustry**"

Refinement attempt 2 (single-word labels) improved but did not fix: "INFORE" / "MODUAR" / "OIURS" / "SE ARGENT" all surfaced. Attempt 3 was fast-forwarded based on the consistent visual-inspection pattern.

After 3 Phase A attempts, all 4 markers reached the cycle's escalation decision.

### Cycle path 2 — `terminate_pending_confirmation` privacy gate handshake ✓ (FIRST TIME)

This was the first run across the six-run series to fire the privacy gate. With `confidentiality: internal` and `privacy.confirmation_received=False`, all 4 escalating markers terminated at `terminate_pending_confirmation`. The orchestrator surfaced a single explicit handshake to the Speaker before any cloud spend:

> Confidentiality tier: internal
> The first cloud image generation will send the prompt and visual brief context to Google Nanobanana Flash. Subsequent cloud calls in this run will not re-prompt.
> Confirm cloud escalation for this run? (yes/no)

Speaker confirmed → `gate.confirmation_received=True` → cycle restarted at Phase B Flash for all 4 markers.

### Cycle path 3 — Phase B → Phase C Pro escalation ✓

All 4 Flash generations (`gemini-3.1-flash-image-preview`, $0.067 each) returned visually flawless output on first attempt — every label spelled correctly, palette exact, layout matching the brief. The cycle's `_phase_b_decision` automatically escalates to Pro when Flash passes AND budget allows (cross-tier prompt refinement design — Flash proves the prompt; Pro renders the proven prompt at highest fidelity). All 4 escalated to Phase C Pro (`gemini-3-pro-image-preview`, $0.134 each); all 4 returned `terminate_pass` at Pro tier.

### Other markers

- **slide 4 IMAGE:tessera-wordmark** — Phase A pass. Reviewer (Haiku) returned `pass` despite the rendered subtitle reading "EDGE INFORENCE INFRASTRUCTURE" (should be INFERENCE). **This was the first Run 6 finding — see Finding #19 below.**
- **slides 5 IMAGE:founder-portrait-ceo + IMAGE:founder-portrait-cto** — both Phase A pass. The brief explicitly said "schematic / institutional-register illustrations, not photographs"; the prompt-engineer composed prompts in editorial-illustration register with sepia-ink wash on warm vellum, and Ollama produced surprisingly competent results that passed first attempt.
- **slide 10 BG:pivot-moment** — Phase A pass. Atmospheric warm vellum texture is exactly what Ollama is good at.
- **slide 11 SMARTART-FROM-LIST:synergy-pillars** — first apply failed because all 5 bullets exceeded the `process1` 24-char cap (52 / 43 / 48 / 42 / 38 chars). Rebuilt build.js with shortened bullets ("Edge inference capacity", "Operator playbook", "Customer overlap 3 of 7", "GPU procurement, $8M", "Registry + billing seam") to ≤24 chars and re-ran apply. Finding #13 reaffirmed for the third consecutive run.

### Cohesion review

8 of 9 enriched slides PASSED. Slide 11 SmartArt rendered as `unassessable_rasterisation` per Finding #6 (LibreOffice cannot render injected SmartArt — known limitation; PowerPoint Mac PDF export confirms it renders correctly with brand-coloured boxes and arrow connectors).

Aggregate verdict: **PASS**.

## Cost summary

| Phase | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Run 6 |
|---|---|---|---|---|---|---|
| Phase 1 (off-budget per Finding #8) | 4 | 6 | 4 | 4 | 4 | **4** |
| Phase 3 generation Ollama | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 | **$0.00** |
| Phase 3 generation Flash | — | — | — | — | — | **$0.268** (4×) |
| Phase 3 generation Pro | — | — | — | — | — | **$0.670** (5× — 1 ConnectionReset retry) |
| Phase 3 reviews (Haiku, image-reviewer) | $0.04 | $0.025 | $0.025 | $0.020 | $0.015 | **$0.080** (16×) |
| Phase 3 cohesion (Sonnet) | $0.02 | $0.020 | $0.020 | $0.020 | $0.020 | **$0.020** |
| **Phase 3 total** | $0.06 | $0.045 | $0.045 | $0.040 | $0.035 | **$1.078** |

Run 6 is the most expensive Phase 3 to date (~30× Run 5) — the cost is the cloud escalation thesis incarnate. Still well under the $5.00 cap; ~78% headroom unused. The cost ledger demonstrates that internal-tier decks with cloud-impossible subjects scale gracefully under the cycle's budget gates.

---

## New findings (Run 6)

### Finding #19 — Image-reviewer (Haiku) misses misspellings without explicit expected-text reference

**Issue:** Slide 4's tessera-wordmark Phase A draft rendered "EDGE **INFORENCE** INFRASTRUCTURE" as the subtitle (should be "EDGE INFERENCE INFRASTRUCTURE"). The image-reviewer agent (Haiku) returned `verdict: pass` with `confidence: 0.92` and explicitly said *"Text spelling correct across all elements"* and *"all three text layers rendered clearly: wordmark serif, rule, subtitle small caps. No garbling, no clipping, no distortion"*. Haiku confabulated correctness.

**Root cause:** Haiku's vision capability has documented limitations for fine text scrutiny. Without an explicit expected-text reference in the dispatch prompt, the reviewer reads the image as "looks like a wordmark" and returns pass without performing character-by-character comparison against intended text.

**Manifestation in Run 6:** Slide 4 enriched with the misspelled image and shipped because the cycle terminated at Phase A. The deck went through the bridge with an INFORENCE typo.

**Fix paths:**
- (a) **Image-reviewer dispatch contract extension** — add `expected_text_content: list[str]` field to the dispatch payload. The reviewer's instructions require it to read every word in the image and compare against the expected list, flagging any mismatch as a critical issue. (Recommended — small surface, applies to all text-bearing markers.)
- (b) **Cross-validation with general-purpose agent** — for high-stakes decks, dispatch image-reviewer (Haiku) AND general-purpose (Sonnet/Opus) in parallel, surface any disagreement to the user. (Defensive but doubles review cost.)
- (c) **Document the limitation as Speaker-facing contract** — note in /enrich-deck output that text-content fidelity is best-effort at Phase A and Speakers should manually verify text-bearing IMAGE markers before delivery. (Weakest fix — pushes work onto Speakers.)

**Recommendation:** ship (a) as a v0.1.x bridge patch + image-reviewer contract update. Document (b) as advisory for high-stakes runs.

---

### Finding #20 — Image-reviewer catches misspellings reliably WHEN expected text is provided

**Issue (positive form of #19):** When the dispatch prompt explicitly listed expected text strings — *"Compare every wordmark against expected EXACT labels: 'Halberd Capital', 'Meridian Bank', ..."* — the reviewer caught **all 4** misspellings on slide 7 (4-of-7 wordmarks wrong), **all 4** on slide 8, and **2 of 2** correctly identified misspellings on slide 9 (the third arrow label "Model Regustry" was mistakenly called correct — partial blind spot remains).

**Implication:** the fix for Finding #19 is mechanical, not architectural. Haiku's capability is sufficient when given the comparison reference; the gap is purely in dispatch-prompt structure. Finding #20 is the empirical evidence that Finding #19's recommended fix path (a) will work.

**Concrete pattern that worked in Run 6:**

```
**Subject intent:** [description]. EXACT spelled labels REQUIRED:
- [list of expected strings, one per line]

CRITICAL CHECK: Read every word visible in this image. Compare each rendered word
against the expected labels above. Report ANY misspellings or garbled letterforms
as issues.
```

**Where to entrench:** the image-reviewer agent definition (`plugins/jack-tar-deckhand/agents/image-reviewer.md`) needs a contract clause that text-bearing markers receive `expected_text_content` and apply this comparison. The /enrich-deck SKILL.md needs to extract expected text from the marker's subject brief in the creative brief and pass it on dispatch.

---

### Finding #21 — Reviewer can return verdict-text contradiction (verdict label disagrees with own analysis)

**Issue:** Slide 8's comparables-logo-strip Phase B Flash review returned `verdict: refine` but the reviewer's own structured fields said:
- `strengths`: *"All five company names are correctly rendered and legible"*
- `composition_notes.text_rendering`: *"All five labels legible: Replix, Modular Labs, Fabric AI, Prism Inference, Apex Compute — exact match to specification"*
- `summary`: *"Logo strip renders five correct company names in correct Velvet Ledger palette and layout, all labels verified against spec."*
- `issues[0]`: *"First wordmark reads 'Replix' (correct) but should be verified against source brief — label appears clipped or truncated visually ('Rep' prominent, 'lix' minimal)"*

The verdict label said `refine` but the reasoning said pass with one cosmetic concern.

**Impact:** the cycle would have refined-and-retried unnecessarily (cost: another $0.067 Flash gen). In Run 6 the orchestrator overrode this to pass based on visual inspection, but in production a fully automated cycle would burn budget on a no-op refinement.

**Fix paths:**
- (a) **Verdict coherence post-check** — image-reviewer agent contract requires a final self-consistency check: "if your strengths/notes/summary do not surface a substantive issue that would justify regeneration, your verdict MUST be pass." Fail-safe coherence guard. (Recommended — small contract change.)
- (b) **Issue severity threshold** — bridge cycle ignores `verdict: refine` if the reviewer's `issues[]` list contains zero items with severity >= "blocking" or contains only items the reviewer's own text contradicts. (More work — bridge has to second-guess reviewer.)
- (c) **Reviewer-tier auto-escalation** — when Haiku returns a refine verdict that the orchestrator's heuristic cannot reconcile, dispatch a Sonnet/Opus second opinion. Last resort.

**Recommendation:** ship (a). The agent contract is the load-bearing element here; the cycle should not need to second-guess the reviewer.

---

### Finding #13 reaffirmed (Run 4, Run 5, now Run 6)

`process1` 24-char label cap rejected all 5 synergy bullets in Run 6 (52 / 43 / 48 / 42 / 38 chars). Hand-shortened to ≤24 chars to ship — exactly the same pattern as Runs 4 + 5. The fix is now well-overdue v0.1.x patch territory:
- Auto-truncate when items exceed cap (with a Speaker-visible warning in the report)
- OR layout-route by item-length distribution: pick `list1` (30 chars) or `vList2` (50+ chars) when items are longer
- OR pre-flight check at Phase 1 brief authoring time — Section C SMARTART-FROM-LIST guidance should specify ≤24 chars per bullet

Layered defense recommended — pre-flight check at brief time AND auto-truncation at apply time.

---

## Leading practices to entrench (additions from Run 6)

These add to the ten leading practices already entrenched after Runs 4–5. Each is a Run 6 pattern that should become default for future runs and real users.

### 11. Image-reviewer dispatch must list expected text strings for text-bearing markers

For any IMAGE marker whose subject contains specific text (logos, wordmarks, technical labels, named blocks, named arrows, name captions), the dispatch prompt MUST include the exact expected text strings in a comparison list and instruct the reviewer to read every visible word and compare against the list. Without this, Haiku's vision capability confabulates correctness (Finding #19). With this, Haiku catches misspellings reliably (Finding #20).

**Entrench:** image-reviewer agent definition + /enrich-deck SKILL.md dispatch template require an `expected_text_content` field. The narrative-brief-architect persona's Section C subject-brief format should call out expected text strings explicitly so /enrich-deck can extract them.

### 12. Investigation-Verdict arc + Velvet Ledger personality is canonical for institutional / M&A registers

Run 6 validates this combination as the working pattern for board / M&A committee / fiduciary-audience decks. The arc treats the audience as a judicial body; the personality (warm ivory + ox-blood + antique gold + mauve-grey, mixed serif typography) carries institutional gravitas without selling. The conditional-approval structure ("approve under these three conditions") closes the arc with auditable gates rather than open-ended urgency.

**Entrench:** Run 6's brief at `output/dogfood-bridge-run-6/creative-brief.md` is now the canonical example for institutional / M&A registers — added alongside Run 5 (senior leadership strategy / Boardroom Stone / Pruning Frame) and Run 4 (engineering retrospective / Redline / data-led). Plugin CLAUDE.md should reference Run 6 for board-deck guidance.

### 13. Privacy gate handshake works correctly — production confidence

Run 6 was the first run to exercise the privacy gate end-to-end. The flow:
1. Deck has `confidentiality: internal`
2. Phase A exhausts on cloud-impossible markers
3. Cycle returns `terminate_pending_confirmation` for each escalating marker
4. Orchestrator surfaces ONE explicit confirmation prompt to the Speaker
5. Speaker confirms → `gate.confirmation_received=True`
6. Cycle restarts at Phase B for all pending markers (no re-prompting per marker)

This is exactly the design intent. Subsequent cloud calls within the same run pass through silently. Production confidence: high.

**Entrench:** the gate handshake pattern is now the documented working sequence. /enrich-deck SKILL.md Step 5d describes the exact behaviour Run 6 demonstrated.

### 14. Cross-tier prompt refinement: Flash-passing prompts go to Pro for free

The cycle's `_phase_b_decision` auto-escalates Flash-passing prompts to Pro when budget allows. Run 6 demonstrated that Flash and Pro produce equivalent label fidelity at this scale (no Pro re-renders failed where Flash succeeded), but Pro adds geometric polish (cleaner edges, more even border treatment, better composition discipline). The auto-escalation costs $0.134 per marker on top of the $0.067 Flash gen — non-trivial, but for a deck that has crossed the privacy gate the marginal cost is justified by the visual-fidelity uplift.

**Entrench:** keep this default. Document it in the report — Speaker should know that Pro-tier images shipped because Flash passed cleanly. If budget is tighter, set `budget_cap_usd` to ~$0.50 per anticipated text-bearing IMAGE marker to gate Pro escalation; the cycle's `can_afford` check will degrade gracefully to Flash-only.

### 15. Editorial-illustration prompt register works for portraits at Phase A

Founders portraits passed Ollama review on first attempt despite Run 6's framing as a "force escalation" run. The prompt-engineer composed prompts in editorial-illustration register (warm vellum + sepia-ink wash + dark tailored jacket + three-quarter pose, deliberately NOT photorealistic) and Ollama's z-image-turbo produced competent results. The lesson is that "human face = Ollama-impossible" is overcalibrated; what's actually impossible is photorealistic human face. Editorial-illustration register is well within Ollama's capability.

**Entrench:** for institutional decks, prompt-engineer should default to editorial-illustration for portrait subjects unless the brief specifically calls for photorealism. This saves cloud spend on portrait markers.

### 16. Connection retry handling is a robustness gap

Run 6's Phase C Pro batch hit `ConnectionResetError` on the 3rd of 4 generations (strategic-fit-diagram). The orchestrator manually retried; the bridge has no built-in retry. For production runs this is a robustness gap.

**Entrench:** v0.1.x patch — wrap `generate_cloud_image` calls in a tenacity-style retry decorator with exponential backoff (3 attempts, 1s / 2s / 5s). Real-world TCP connection resets are a routine operational event when calling a third-party API.

---

## Anti-patterns to avoid (Run 6 specifics)

### 8. Dispatching image-reviewer without expected text reference for text-bearing markers

The Run 6 tessera-wordmark Phase A reviewer dispatched without "compare against [expected list]" instructions and missed the INFORENCE typo. The deck shipped with the typo because the cycle accepted the verdict.

**Deprecate by:** Finding #19 fix (a) — image-reviewer contract requires `expected_text_content` for any text-bearing marker. /enrich-deck SKILL.md extracts the field from the marker's subject brief and passes it in the dispatch payload.

### 9. SMARTART-FROM-LIST bullets exceeding 24 characters

Three consecutive runs (4, 5, 6) have hit the `process1` 24-char cap with prose-style bullets and required hand-truncation to ship.

**Deprecate by:** Finding #13 fix layered — Section C brief guidance specifies "SmartArt bullets ≤24 chars (process1) or ≤30 chars (list1)" + bridge auto-truncates with a warning when items exceed cap + Phase 1 narrative-brief-architect surfaces this constraint when writing Section C subject briefs that include SmartArt.

### 10. Verdict-text contradictions in reviewer output

Run 6's slide 8 Phase B Flash review returned verdict=refine but its own analysis confirmed pass. Cycle would refine-and-retry unnecessarily, burning budget on a no-op.

**Deprecate by:** Finding #21 fix (a) — image-reviewer contract requires final self-consistency check: if strengths/notes/summary do not surface a substantive blocking issue, verdict MUST be pass.

---

## Run 7 thesis (open candidates)

Six runs across six distinct visual personalities + one full cloud-escalation run have validated all known cycle paths. The bridge is functionally complete for v0.1.0; remaining work is polish + the v0.1.x patches surfaced across the dogfood series. Run 7+ candidates:

1. **CHART marker kind spike (v0.2 work)** — implement `CHART:slug` marker; Run 7 deck uses CHART markers for chart-shaped subjects instead of the Section C language workaround. Validates whether the marker kind is materially better than language-only routing. Genuine v0.2 work, doesn't gate v0.1.0.
2. **`surface_to_user` cohesion verdict** — the only cycle path still uncovered. Requires a regenerated image to STILL fail cohesion review after one auto-regen attempt. Hard to engineer deliberately; may be best left to organic occurrence in real-user runs.
3. **Real-user pilot** — recruit one developer to dogfood the bridge for an actual conference talk or board memo. Validates the patterns hold when the operator is not the bridge author.

Recommendation: **after the v0.1.x patch backlog ships (Findings #3 / #7 / #8 / #12 / #13 / #14 / #17 / #18 / #19 / #20 / #21 / #16), ship v0.1.0**. Run 7 is the v0.2 milestone work.

If Run 6 + the v0.1.x patches land cleanly, the v0.1.0 release scorecard's Item 5 flips green and the bridge is ready to ship.
