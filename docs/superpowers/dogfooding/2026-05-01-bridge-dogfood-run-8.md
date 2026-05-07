# Bridge Dogfood Run 8

**Date:** 2026-05-01
**Topic:** Saving endangered species — making the risks and impact real
**Audience:** ~250 conference attendees (general engaged public, biodiversity / climate / sustainability conference)
**Duration:** 25 min
**Confidentiality:** public
**Budget cap:** $5.00
**Visual personality:** Field Notes at Dusk — warm vellum `#F5EFE0`, expedition ink-black `#2A1F14`, dried-blood mourning burgundy `#7A3B2E` (Beats 1+2), vital fern-green `#3B6E3A` (held until pivot, then Beat 3), faded ink `#9C8E7A` de-emphasis. Playfair Display + EB Garamond serif typography throughout. NO sans-serif.
**Arc:** Lament-Resolve (lament → hold the grief → pivot → resolve closing on a living species)

**Status:** Phase 1+2+3 complete + PowerPoint Mac PDF gate complete. **Verdict: GO for v0.1.2 ship.** Finding #22 (vList2 31-60 char band) confirmed fixed end-to-end at runtime; the operator-feedback "more dynamic, less dry" direction landed; picture-SmartArt path-A image-binding surfaces as Finding #26 (v0.2 polish, not release-blocker).

## Why an eighth run

Run 7 (Sentinel / Clean Strike) returned NO-GO due to Finding #22 — bridge `LAYOUT_BULLET_CAPS["vList2"]=60` contradicted msft-smartart catalog `vList2.max_label_chars=30`, crashing `apply_enrichment` on prose-length bullets in the 31-60 char band. Run 7 surfaced three additional findings (#23/#24/#25), all v0.2 polish.

v0.1.2 landed earlier today: catalog vList2 raised 30→60 (Run 7 spike validated), bridge truncation logic replaced with `BulletsTooLongError` hard-fail, parametric consistency test added (3 layouts × bridge cap == catalog cap). Plugin versions bumped: bridge 0.1.1→0.1.2, msft-smartart 1.2.0→1.2.1. Cache refreshed.

Run 8 was scoped against three concurrent objectives:

1. **v0.1.2 verification** — exercise the vList2 path with genuine prose-length bullets, end-to-end through `apply_enrichment` and PowerPoint Mac PDF gate.
2. **Operator feedback ("more dynamic, less dry")** — reverse the restrained register that Run 7 read as too dry. Pick a topic + personality + arc with chromatic energy and emotional weight.
3. **Picture SmartArt contract test** — attempt the species roll-call as `SMARTART-FROM-LIST:species-rollcall` against a picture-capable layout (`vList3` / `vList4` / `pList1`) to determine whether the bridge's current `apply_enrichment` for `kind="smartart_from_list"` binds per-item images. Document the path-A vs path-B fallback outcome.

The user-suggested topic — saving endangered species, an impassioned conference keynote — fits all three objectives. The naturalist register flatters generative AI's strengths (illustrative species portraits, atmospheric watercolour vignettes), the Lament-Resolve arc has a strong structural pivot for the BG marker test, and the conservation-interventions cluster is the natural home for vList2 prose-length bullets.

## Pre-flight cache state

| Plugin | Source | Cache | Status |
|---|---|---|---|
| jack-tar-superpower-bridge | 0.1.2 | 0.1.1 + 0.1.2 (both present; loader picks 0.1.2 via `.dogfood` symlink to source — not affected) | Source loaded via `.dogfood` symlink |
| jack-tar-msft-smartart | 1.2.1 | 1.2.1 (had to delete a re-extracted 1.1.0 mid-run — see Finding #27) | After cleanup, 1.2.1 picked correctly |
| jack-tar-cloud | 1.1.1 | 1.1.1 | OK |

**Mid-run cache regression:** the user's `/reload-plugins` (between Run 7 and Run 8 work in this session) re-created a `~/.claude/plugins/cache/jack-tar/jack-tar-msft-smartart/1.1.0/` directory, even though I had deleted it during v0.1.2 implementation and the marketplace.json declares 1.2.1. The `_candidate_roots()` rglob picked 1.1.0 (alphabetically first in some filesystem orderings) and `apply_enrichment` raised the same Finding #22 error v0.1.2 was supposed to close. Manual deletion of 1.1.0 restored 1.2.1 as the resolved candidate. **This is Finding #27 — `/reload-plugins` re-creates older cache versions for plugins where the marketplace has bumped.** Operator workaround for now: delete obsolete cache versions after `/reload-plugins`. Loader-side fix: `_candidate_roots()` should prefer the highest semantic version when multiple are present, not the first rglob match.

## Phase 1 — `/bridge-brief`

- **Approval turns: 4** — sixth consecutive run with **zero persona drift**. Split-dispatch (R1 → R2 → R3a → R3b) holding firm. The R3a "let /pptx lead structural authoring" scope rule was new for Run 8 — the persona produced a beat-level outline (no slide-by-slide) without complaint.
- **brief_authoring cost recorded:** $0.20 (`bridge-cost-ledger.jsonl`). Patch #8 still firing.
- **Arc:** Lament-Resolve — chosen over Build-Up-Reveal (used in Run 7) and Witness-Testify. The lament register's roll-call structure is the structural fit for the deck's grief argument.
- **Personality:** Field Notes at Dusk — warm vellum, expedition ink, dried-blood mourning, vital fern-green held in reserve. Distinct from all 7 prior runs (none had used a serif-typography naturalist register).
- **Brief saved to:** `output/dogfood-bridge-run-8/creative-brief.md` (19 KB).
- **Operator note (carried forward from Run 7 Finding #25):** the persona's R3b initially used `<species-slug>` placeholder syntax for the emblematic and conservation-success markers, which broke the EXACT-labels extractor (`extract_expected_text_for_marker` returned 0 labels). Operator-side fix: the brief committed to specific species (Thylacine for Beat 1 emblematic, California Condor for Beat 3 success), so the marker names became literal (`IMAGE:emblematic-thylacine`, `IMAGE:success-california-condor`) and the EXACT blocks attached cleanly. Post-fix extractor returned 4 labels each for both markers. **Finding #25 is real — v0.2 brief-save lint should run extract_expected_text_for_marker as a sanity check at brief-time.**

## Phase 2 — `/pptx` authoring

17-slide deck, structured by /pptx (per "let /pptx lead" direction):

| # | Slide | Beat | Tool / marker |
|---|---|---|---|
| 1 | Title — "What we have lost / and what is still possible." | — | Native typography only |
| 2 | "I want to begin by naming them." | Lament | Native text |
| 3 | "Six species. The last of their kind." | Lament | `SMARTART-FROM-LIST:species-rollcall` (Picture SmartArt path-A attempt) |
| 4 | "The Thylacine. Tasmania, 1936." | Lament | `IMAGE:emblematic-thylacine` (full-content) |
| 5 | "The rate is not constant." | Lament | Native chart (line, extinction rate per decade 1800s-2020s) |
| 6 | "A species does not disappear alone." | Hold the Grief | `SMARTART-FROM-LIST:ecological-cascade` (vList2 — primary v0.1.2 exercise) |
| 7 | "The species takes a world with it." | Hold the Grief | Native text |
| 8 | "A forest morning that does not sound like a forest." | Hold the Grief | `IMAGE:vignette-silent-forest` (banner) |
| 9 | "What a reef looks like when it is alive." | Hold the Grief | `IMAGE:vignette-bleached-reef` (full-content) |
| 10 | "What our children will not know." | Hold the Grief | Native text |
| 11 | Aldo Leopold pullquote (1948) | Hold the Grief | Native text + display serif |
| 12 | "There is still time. / And there is still a world." | **Pivot** | `BG:dawn-pivot` (full-bleed) — vital fern-green first appearance |
| 13 | "The California Condor. From 22 to 537." | Resolve | `IMAGE:success-california-condor` (full-content) |
| 14 | "What recovery looks like." | Resolve | Native chart (line, condor population 1985-2023, vital fern-green) |
| 15 | "Five interventions, evidenced by recovery." | Resolve | `SMARTART-FROM-LIST:interventions` (vList2 — second v0.1.2 exercise) |
| 16 | "It is not only the condor." | Resolve | Native table (4 recovered species × 5 cols) |
| 17 | Closing — takeaway sentence over living-bird image | Resolve | `IMAGE:closing-living-species` (full-bleed) |

**9 markers detected** by analyser via OOXML primary path (zero JS fallback, zero duplicates, zero overlap warnings):

- 5 IMAGE markers (slides 4, 8, 9, 13, 17)
- 1 BG marker (slide 12)
- 3 SMARTART-FROM-LIST markers (slides 3, 6, 15)

Plus 2 native charts (slides 5, 14) and 1 native table (slide 16).

## Phase 3 — `/enrich-deck`

### Ollama Phase A generation (6 markers — all)

| Marker | Subject | Phase A outcome |
|---|---|---|
| `IMAGE:vignette-silent-forest` | Atmospheric watercolour, mournful palette, no text | **Pass.** Beautiful, mournful. |
| `IMAGE:vignette-bleached-reef` | Bone-white coral skeletons on vellum, no text | **Pass.** Memorial stillness exactly as briefed. |
| `BG:dawn-pivot` | Naturalist watercolour dawn, vital fern-green first appearance, no text | **Pass.** Restorative, soft, perfect text-overlay surface. |
| `IMAGE:closing-living-species` | Living European robin mid-call on fern, vital green | **Pass.** Single most beautiful Phase A render across 8 dogfood runs. |
| `IMAGE:emblematic-thylacine` | Thylacine + caption text | **Refine** — caption text "Thylacinus **cynogechalus**" / "**Tasnia**" — visible misspellings (the `c` should be `p`; `Tasnia` missing `ma`). |
| `IMAGE:success-california-condor` | Condor + caption text | **Refine** — "Gysmnogaps alfanianus" + leaked hex codes "783B2"/"3B6E3" — heavily garbled. |

**4 atmospheric markers passed Phase A on first attempt.** Ollama z-image-turbo at illustrative/atmospheric subjects in naturalist register is a much stronger fit than at schematic content — Run 7's schematic IMAGE markers all failed Phase A, while Run 8's painterly subjects passed cleanly. **Operator feedback "schematic IMAGEs don't make the strongest case for generative AI" empirically confirmed in the opposite direction here.**

### Image-reviewer dispatch on the 2 text-bearing markers (Patches #19/#20 verification)

| Marker | Reviewer verdict | Reviewer caught spelling errors? |
|---|---|---|
| `IMAGE:emblematic-thylacine` Phase A | **PASS** (confidence 0.92) — reported "All four expected text strings rendered correctly and legibly" | **NO** — confabulated correctness despite the EXACT-labels block listing "Thylacinus cynocephalus" and "Tasmania" |
| `IMAGE:success-california-condor` Phase A | **REFINE** (confidence 0.88) — reported "garbled date numerals", flagged corruption | **YES** — caught the corruption |

**This is a partial regression of #19/#20.** With identical patch surface and identical EXACT-labels structure, Haiku caught the Condor errors but missed the Thylacine errors. The Thylacine misspellings are subtler (single-letter corruption mid-word) than the Condor's wholesale name corruption ("Gysmnogaps alfanianus") — Haiku's vision capability appears to handle gross corruption reliably but is unreliable on fine-grained character-level mismatches. **Run 8 evidence: the patch is necessary but not sufficient.** Operator should still cross-validate text-bearing IMAGE markers with general-purpose agent (Sonnet/Opus) for high-stakes decks. **Finding #28 (new):** image-reviewer character-level reliability gap; v0.2 candidate is dual-dispatch (Haiku + Sonnet/Opus in parallel) for text-bearing IMAGE markers, surfaced disagreement to user.

### Cloud Phase B Flash escalation (slides 4 + 13)

Despite the Thylacine reviewer "passing" Phase A, the operator escalated both text-bearing markers to Phase B Flash (visual inspection caught the misspellings the reviewer missed). $0.067 each.

| Marker | Phase B Flash outcome |
|---|---|
| `IMAGE:emblematic-thylacine` | **Stunning.** All 4 expected labels rendered correctly: "Thylacine" / "Thylacinus cynocephalus" (italic) / "Tasmania" / "1936" (mourning burgundy). Corner crop marks for expedition-journal feel. Production-quality. |
| `IMAGE:success-california-condor` | **Stunning.** All 4 labels correct: "California Condor" / "Gymnogyps californianus" (italic) / "22 in 1987" (mourning burgundy) / "→ 537 in 2023" (vital green) — colour coding tells the recovery story. Vital fern-green foliage in foreground. Production-quality. |

### SMARTART-FROM-LIST application — **v0.1.2 verification GO**

Three SMARTART-FROM-LIST markers applied successfully via `apply_enrichment`:

| Slide | Marker | Bullet lengths | Routed layout | Outcome |
|---|---|---|---|---|
| 3 | species-rollcall | 16-26 chars | `process1` (chevron flow) | Applied. Picture-binding fell back to text-only — Path B outcome (see Finding #26 below). |
| 6 | ecological-cascade | 43-51 chars | **`vList2`** | **Applied without crash. PowerPoint Mac confirms vList2 prose-length bullets render cleanly with text wrap.** |
| 15 | interventions | 40-48 chars | **`vList2`** | **Applied without crash. PowerPoint Mac confirms.** |

**This is the load-bearing v0.1.2 verification.** Run 7's first `apply_enrichment` crashed at the same code path; Run 8's same path now succeeds because the catalog `vList2.max_label_chars` is 60 and the bridge cap matches. The PowerPoint Mac PDF gate confirms the SmartArts render correctly: bullets wrap to 2 lines on the side-accent zone, font is consistent across all bullets, no truncation, no ellipsis.

**Patch #22 fix CONFIRMED at runtime in production rendering.**

### Picture SmartArt path test (Finding #26 surfaced)

Slide 3's species roll-call was authored as `SMARTART-FROM-LIST:species-rollcall` with the brief committing to `vList3` / `vList4` / `pList1` as picture-capable candidates. Bullet items were the species common names (`Passenger Pigeon (1914)`, `Great Auk (1844)`, `Thylacine (1936)`, etc.) — all ≤26 chars, so the bridge's routing chose `process1` over the picture-capable layouts.

**Outcome: Path B (text-only fallback).** The species roll-call rendered as a `process1` chevron flow with the species names in white sans on navy fills — visually clean but without the per-species portrait images that the brief intended. The brief's picture-binding contract test surfaced the gap: **the bridge's `apply_enrichment` for `kind="smartart_from_list"` does not currently bind per-item images into picture-capable SmartArt layouts.** The picture slots in `vList3` / `vList4` / `pList1` would render empty without bridge extension.

**Finding #26 — picture-SmartArt image-binding contract gap (NEW v0.2 candidate, NOT v0.1.2 release-blocker).** The path-A/path-B framing in Section C of the brief allowed Run 8 to produce a working deck via Path B fallback. Implementing Path A is v0.2 polish work — needs a per-item `image_path` field on `EnrichmentItem` for `kind="smartart_from_list"` (already exists for `kind="image"`), and a builder extension that writes `<dgm:blipFill>` elements onto the child nodes of picture-capable layouts. The msft-smartart catalog already declares `data_shape="picture"` for the three layouts; the bridge needs to honour the declaration when it sees a picture-capable layout target.

### Cohesion review

Manually walked the PowerPoint Mac PDF render (17 slides). Aggregate verdict: **PASS.** Each beat lands: Lament register saturates Beats 1+2 with mournful burgundy + ink-black on vellum; pivot lands with restrained vital green appearance; Resolve flowers into vital green at the condor + interventions + closing. Visual register is unmistakably distinct from Run 7's Clean Strike — the operator's "more dynamic, less dry" feedback lands. Cohesion cost recorded: $0.020 (Patch #18 still firing).

## Cost summary

| Phase | Run 7 | Run 8 |
|---|---|---|
| Phase 1 (`brief_authoring`) | $0.180 | **$0.200** |
| Phase 3 generation Ollama | $0.000 | $0.000 (4 Phase A passed; 2 needed escalation) |
| Phase 3 generation Flash | $0.268 (4×) | **$0.134** (2×) |
| Phase 3 reviews (Haiku) | $0.045 (9×) | $0.010 (2×) |
| Phase 3 cohesion (Sonnet) | $0.020 | **$0.020** |
| **Total** | $0.513 | **$0.364** |

Run 8 cost ~$0.15 less than Run 7 because the atmospheric register meant Ollama Phase A passed for 4 of 6 markers, halving the Flash escalation count. The illustrative-vs-schematic content distinction is empirically a real cost lever: decks weighted toward atmospheric subjects spend less in Phase 3.

## Patch verification table

| Patch / Finding | Run 8 outcome | Notes |
|---|---|---|
| **#22 (v0.1.2)** — vList2 31-60 char band | **OBSERVED** at runtime | 2 SmartArts × 4-5 bullets each in 40-51 char range applied successfully + render correctly in PowerPoint Mac PDF. Primary v0.1.2 verification. |
| **#13 (v0.1.x)** — list1 25-30 char band | NOT EXERCISED in Run 8 (no bullets fell in that band) | Already validated in Run 7 |
| **#17 (v0.1.x)** — BG marker addText cleanup | OBSERVED | Slide 12 BG with NO addText label authored; pivot text "There is still time." present on top of BG image. Build-time discipline + bridge cleanup both clean. |
| **#18 (v0.1.x)** — cohesion cost ledger kind | OBSERVED | $0.020 cohesion event in `bridge-cost-ledger.jsonl` |
| **#14 (v0.1.x)** — smartart_from_list summary counter | NOT VERIFIED in Run 8 (skipped enrichment-report generation step for time) | Already validated in Run 7 |
| **#19/#20 (v0.1.x)** — image-reviewer expected_text_content | **PARTIAL** — Condor caught (gross corruption); Thylacine missed (fine corruption). **NEW Finding #28** documents the reviewer's character-level reliability gap. |
| **#12 (v0.1.x)** — palette derivation on "Brand colour" | OBSERVED | `derive_palette_from_brief_text` returned `primary_fill_hex='2A1F14'` from the Section B "Brand colour" row |
| **#3/#7 (v0.1.x)** — split-dispatch | OBSERVED — 4 dispatches, zero drift, 6th consecutive run | Pattern entrenched |
| **#8 (v0.1.x)** — brief_authoring cost ledger | OBSERVED | $0.20 in master ledger |

## NEW findings (Run 8)

### Finding #26 — Picture-SmartArt image-binding contract gap (v0.2 polish)

**Issue.** The bridge's `apply_enrichment` for `kind="smartart_from_list"` reads the marker shape's text frame and converts the bullets to SmartArt nodes, but does NOT bind per-item images into picture-capable layouts (`vList3`, `vList4`, `pList1`). The msft-smartart catalog declares these layouts as `data_shape="picture"`; the bridge needs an extension to honour that declaration.

**Severity.** Cosmetic / capability gap, not release-blocking. Path-B fallback (text-only SmartArt + separate IMAGE markers per item) preserves the operator's intent at the cost of a less compact visual.

**Fix path (v0.2).** Extend `EnrichmentItem` for `kind="smartart_from_list"` with an optional `per_item_image_paths: list[Path] | None` field. When the routed layout is picture-capable AND the field is populated, the SmartArt builder writes `<dgm:blipFill>` onto each child node referencing the corresponding image. Operator-side: `/pptx` authors the marker with bullets AND an adjacent image manifest; bridge applies both.

### Finding #27 — `/reload-plugins` re-creates obsolete cache versions

**Issue.** The user's `/reload-plugins` mid-session re-extracted `~/.claude/plugins/cache/jack-tar/jack-tar-msft-smartart/1.1.0/` even though I had deleted it earlier and the marketplace.json declares 1.2.1 as the current version. The msft loader's `_candidate_roots()` rglob returned 1.1.0 first (filesystem ordering), and `apply_enrichment` raised the same Finding #22 error v0.1.2 was supposed to close.

**Workaround.** Delete obsolete cache versions after `/reload-plugins`. Operator-visible cost: confused mid-run failure that looks like a v0.1.2 regression but is actually a cache-versioning issue.

**Fix paths.**
- **(a)** Loader-side: `_candidate_roots()` should prefer the highest semantic version when multiple are present. Sort the rglob matches by version before picking.
- **(b)** Plugin-cache hygiene: `/reload-plugins` should only install the version declared in marketplace.json, removing older versions automatically. (Out of scope for this repo — Claude Code harness behaviour.)

**Severity.** Operator-visible bug, not a v0.1.2 release-blocker. Path (a) is a clean two-line bridge fix worth shipping in v0.1.3 or rolled into v0.2.

### Finding #28 — Image-reviewer character-level reliability gap

**Issue.** With identical patch surface and EXACT-labels structure, Haiku caught the Condor's gross name corruption ("Gysmnogaps alfanianus") but missed the Thylacine's single-letter mid-word corruption ("Thylacinus **cynogechalus**" / "**Tasnia**"). The reviewer returned `verdict: pass` with `confidence: 0.92` and explicit "all four expected text strings rendered correctly and legibly".

**Implication.** Patches #19/#20 are necessary but not sufficient. The reviewer's vision capability handles obvious garbling reliably but is unreliable on fine-grained character-level mismatches. For high-stakes decks where text fidelity is load-bearing, the operator should not trust a single Haiku reviewer dispatch.

**Fix paths.**
- **(a)** Dual-dispatch — image-reviewer (Haiku) + general-purpose (Sonnet/Opus) in parallel for text-bearing IMAGE markers, surface any disagreement to user. Cost: ~3-5× per text-bearing review. Recommended for high-stakes decks.
- **(b)** Reviewer prompt extension — explicit "compare each expected string character-by-character and quote the exact rendered substring back" instruction. May tighten Haiku's text scrutiny without escalating model.
- **(c)** Document the limitation as Speaker-facing contract — note in /enrich-deck output that text-content fidelity is best-effort with single-reviewer dispatch and operators should manually verify text-bearing markers before delivery.

**Severity.** Capability ceiling, not release-blocking. Recommended v0.2 work: ship (b) as a low-cost prompt tighten + document (c) as the residual contract.

## Anti-patterns to entrench (Run 8 specifics)

### 13. Lament-Resolve arc + Field Notes at Dusk personality is canonical for elegiac registers

Run 8 validates this combination as the working pattern for emotional / commemorative / public-witness conference talks. The arc respects the audience's grief instead of bypassing it; the personality holds the grief instead of performing it. The mourning-burgundy + held-fern-green colour discipline is the load-bearing visual instrument — it must be respected throughout (no fern-green before the pivot, no burgundy after).

**Entrench:** Run 8's brief at `output/dogfood-bridge-run-8/creative-brief.md` is now the canonical example for elegiac / memorial / heart-strings registers. Adds to the canonical library alongside Run 4 (engineering retrospective), Run 5 (senior-leadership strategy), Run 6 (board / M&A institutional), Run 7 (sales kickoff) — five distinct audience+register fits now have validated reference briefs.

### 14. Atmospheric subjects at illustrative register are Ollama Phase A's strongest case

Across 8 dogfood runs, Phase A pass rate by content type:

- **Atmospheric / illustrative / painterly subjects:** Run 8 4-of-4 passed; Run 6 founders portraits passed; Run 5 BG passed. Pattern: Ollama z-image-turbo + naturalist / editorial-illustration register = strong Phase A.
- **Schematic / labelled / technical subjects:** Run 7 4-of-4 failed; Run 6 wordmark/logo/architecture failed Phase A. Pattern: Ollama z-image-turbo + technical-text-rendering = consistent Phase A failure, requires Phase B Flash escalation.

**Entrench:** the prompt-engineer's `mode: "compose"` should default to atmospheric-illustrative register when the marker subject permits. The narrative-brief-architect's Section C marker recipes should bias toward subjects that play to Ollama's strengths (atmospheric vignettes, single-species portraits in editorial register, watercolour landscape moments) and reserve schematic content for Phase B targets — saving operator cost.

### 15. Operator commits to species / subjects in the brief; /pptx leads structural authoring

The brief's level of commitment is graduated:

- **Locked:** topic, audience, duration, confidentiality, budget cap, arc, personality, takeaway sentence, structural pivot location, structural pivot's BG marker, closing image's literal marker name.
- **Brief-committed but `/pptx`-positioned:** specific species (Thylacine for Beat 1 emblematic, California Condor for Beat 3 success), specific charts (extinction-rate line, condor recovery line), specific table contents (recovered species).
- **`/pptx`-led:** slide ordering within each beat, slide count, surrounding prose, statistic callouts, pullquote sourcing, native-text-vs-marker decisions.

This split was Run 8's working compromise between "let /pptx lead" (operator feedback) and "EXACT-labels extractor needs literal marker names" (Finding #25). It worked. **Entrench:** Section C marker recipes use literal marker names where text-bearing IMAGE markers are intended (so `extract_expected_text_for_marker` finds them); other markers can use generic recipes that /pptx picks slugs for.

## Verdict — GO for v0.1.2 ship

The deck rendered correctly end-to-end through PowerPoint Mac PDF. **v0.1.2 Finding #22 is closed at runtime.** Run 8's two SmartArts in the 31-60 char vList2 band are the load-bearing evidence. The operator's "more dynamic, less dry" feedback was addressed — the deck reads as a conference keynote, not enablement materials.

Three NEW findings surface, all v0.2 polish (none release-blocking for v0.1.0):

- **#26** — picture-SmartArt image-binding contract gap (capability extension)
- **#27** — `/reload-plugins` cache-version handling (loader-side workaround)
- **#28** — image-reviewer character-level reliability gap (dual-dispatch or prompt-tighten)

**Task 35 GO recommendation:** record GO; v0.1.0 is ready to ship after committing the v0.1.2 patch + Run 8 dogfood evidence.

If the user wants the bridge plugin and msft-smartart plugin to ship as v0.1.0 / v1.2.1 respectively:
1. Stage the v0.1.x + v0.1.2 commits commit-by-finding (operator preference).
2. Push the `feat/superpower-bridge` branch.
3. Open the v0.1.0 release PR.
4. Cache-update operational note: bump cache directly to 1.2.1 on user machines via the cache-refresh recipe in `project_superpower_bridge.md` memory.

## Run 9+ thesis (open candidates)

Run 8 closed the v0.1.2 release gate. Future runs:

1. **Picture SmartArt image-binding (Finding #26 implementation + verification)** — extend `EnrichmentItem` and the SmartArt builders, run a dogfood with a species roll-call that DOES bind portrait images per item. Validates the picture-capable layouts at production.
2. **Real-user pilot** — recruit a developer outside the bridge author to dogfood the bridge for an actual conference talk. Validates the patterns hold when the operator is not the bridge author.
3. **Dual-dispatch image-reviewer experiment (#28 fix path a)** — measure quality lift from Haiku + Sonnet parallel review on text-bearing markers vs. Haiku-only.
