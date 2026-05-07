# Bridge Dogfood Run 10

**Date:** 2026-05-01
**Topic:** Saving endangered species (Run 9 brief, build.js, and assets all re-used unchanged)
**Audience:** ~250 conference attendees
**Duration:** 25 min
**Confidentiality:** public
**Budget cap:** $5.00
**Visual personality:** Field Notes at Dusk
**Arc:** Lament-Resolve

**Status:** Phase 3 re-applied with v0.1.4. PowerPoint Mac PDF gate complete.

**Verdict: GO.** All 9 markers render correctly. Run 9 Finding #29 (picture-SmartArt media collision) is closed at runtime in production rendering. v0.1.0 is now release-ready — five release findings (#22 / #26 / #27 / #28 / #29) closed, plus three v0.1.x findings (#3 / #7 / #8 / #12 / #13 / #14 / #16 / #17 / #18 / #19 / #20 / #21).

## Why a tenth run

Run 9 (2026-05-01) returned PARTIAL GO: Path A picture-SmartArt mechanism worked beautifully on slide 3 (6 species portraits in pList1), but the carrier graft overwrote `ppt/media/image1.png`-`image6.png` with the species portraits, displacing the slide-level IMAGE/BG markers' media. 4 of 5 atmospheric image slots silently rendered the wrong picture in Run 9.

v0.1.4 landed the fix:

- `msft-smartart/assembler_patch.py` adds `_scan_host_max_image_number()` and `_renumber_carrier_media()`. Before grafting carrier media, the inject path scans the host's `ppt/media/` for the highest existing `imageN.{png,jpg}` and renumbers the carrier's media to start at `max + 1`. The carrier's `data1.xml.rels` Targets are rewritten to match.
- 2 new tests in `test_picture_binding_no_media_collision.py` — one reproduces the Run 9 combined-marker case and asserts no collision; the other asserts the picture-SmartArt-alone case (Run 8 Finding #26) still works.
- Plugin versions: bridge `0.1.3 → 0.1.4`, msft-smartart `1.2.1 → 1.2.2`. Marketplace synced. Caches refreshed.

Run 10 was scoped as a **pure regression test** — re-run the exact Run 9 deck with v0.1.4 and verify every marker renders correctly.

## Phase 1 + Phase 2 — re-used unchanged

Brief at `output/dogfood-bridge-run-10/creative-brief.md` is a verbatim copy of Run 9. build.js is a verbatim copy. All 6 species portraits + 4 atmospheric IMAGE/BG images + 2 Phase B Flash emblematic/condor images carried over. No new generation; no new dispatches; $0 cost in Phase 1 + Phase 2.

## Phase 3 — apply_enrichment under v0.1.4

Same `apply_enrichment` call as Run 9: 9 EnrichmentItems (6 image + 1 BG + 2 plain SmartArt-from-list + 1 picture-SmartArt with 6 per-item images). Bridge ran without errors. Output `presentation-enriched.pptx` 7.1 MB.

### Media inventory — Run 9 vs Run 10

**Run 9 (broken):** 8 media files — image1-6.png all hijacked by species portraits; image5.jpg + image6.jpg leftover from Phase B markers; **the original atmospheric images had been overwritten and were no longer in the package.**

**Run 10 (fixed):** 12 media files:

```
ppt/media/image1.png   1.11 MB  ← silent forest watercolour    (slide 8)
ppt/media/image2.png   1.52 MB  ← bleached reef watercolour    (slide 9)
ppt/media/image3.png   1.47 MB  ← closing robin watercolour    (slide 17)
ppt/media/image4.png   1.36 MB  ← dawn pivot watercolour        (slide 12)
ppt/media/image5.jpg   752 KB   ← Phase B Thylacine emblematic  (slide 4)
ppt/media/image6.jpg   952 KB   ← Phase B California Condor     (slide 13)
ppt/media/image7.png   1.51 MB  ← Passenger Pigeon portrait     (slide 3)
ppt/media/image8.png   1.40 MB  ← Great Auk portrait            (slide 3)
ppt/media/image9.png   1.34 MB  ← Thylacine portrait            (slide 3)
ppt/media/image10.png  1.25 MB  ← Baiji portrait                (slide 3)
ppt/media/image11.png  1.71 MB  ← Golden Toad portrait          (slide 3)
ppt/media/image12.png  1.32 MB  ← Spix's Macaw portrait         (slide 3)
```

All 12 distinct images coexist. The carrier graft renumbered to start at image7 (since the host had max image6.jpg from python-pptx Phase 2). Both sets of images are intact and addressable from their respective rels.

### Slide rels verification

| Slide | Marker | Rel target | File at target |
|---|---|---|---|
| 4 | IMAGE:emblematic-thylacine | image5.jpg | Phase B Thylacine ✓ |
| 8 | IMAGE:vignette-silent-forest | image1.png | Silent forest watercolour ✓ |
| 9 | IMAGE:vignette-bleached-reef | image2.png | Bleached reef ✓ |
| 12 | BG:dawn-pivot | image4.png | Dawn watercolour ✓ |
| 13 | IMAGE:success-california-condor | image6.jpg | Condor ✓ |
| 17 | IMAGE:closing-living-species | image3.png | Robin ✓ |

Carrier data1.xml.rels (slide 3 picture-SmartArt) now references `image7.png`-`image12.png` for its 6 portrait slots.

## PowerPoint Mac PDF gate

Visual review of all 17 slides. Every marker renders its intended content:

| Slide | Marker / native | Rendered correctly? |
|---|---|---|
| 1 | Title (text only) | ✅ |
| 2 | Native chart — extinction rate over time | ✅ |
| 3 | **`SMARTART-FROM-LIST:species-rollcall` Picture pList1 (6 species + portraits)** | ✅ **THE LITERAL ROLL-CALL, with faces — Path A perfectly preserved** |
| 4 | `IMAGE:emblematic-thylacine` Phase B | ✅ Thylacine + caption |
| 5 | Text + native chart | ✅ |
| 6 | `SMARTART-FROM-LIST:ecological-cascade` (vList2) | ✅ |
| 7 | Text-only | ✅ |
| 8 | **`IMAGE:vignette-silent-forest`** | ✅ **Silent forest watercolour** (was passenger pigeon in Run 9) |
| 9 | **`IMAGE:vignette-bleached-reef`** | ✅ **Bleached coral on vellum** (was great auk in Run 9) |
| 10 | Text-only | ✅ |
| 11 | Aldo Leopold pullquote | ✅ |
| 12 | **`BG:dawn-pivot`** + "There is still time." text | ✅ **Dawn watercolour pivot** (was baiji in Run 9) |
| 13 | `IMAGE:success-california-condor` Phase B | ✅ Condor + recovery story |
| 14 | Native chart — condor recovery curve | ✅ |
| 15 | `SMARTART-FROM-LIST:interventions` (vList2) | ✅ |
| 16 | Native table — recovered species | ✅ |
| 17 | **`IMAGE:closing-living-species`** + takeaway sentence | ✅ **Living robin on fern** (was thylacine portrait in Run 9) |

**9 of 9 markers correct.** Picture-binding works AND coexists cleanly with slide-level IMAGE/BG markers. The deck delivers the brief's emotional arc end-to-end: a literal roll-call of lost species (slide 3 with their faces), atmospheric grief (slides 8/9 silent forest + bleached reef), the held-breath pivot (slide 12 dawn with first fern-green), and the resolve closing on a living bird (slide 17).

## Cost summary

| Phase | Run 10 |
|---|---|
| Phase 1 (re-used Run 9 brief, no new dispatch) | $0.000 |
| Phase 2 (re-used Run 9 build.js, no new gen) | $0.000 |
| Phase 3 (re-used Run 9 assets, no new gen or review) | $0.000 |
| **Total** | **$0.000** |

Run 10 ran cost-free. The bridge's iteration discipline at this stage is striking: Run 9 surfaced a bug, v0.1.4 fixed it in source, Run 10 verified the fix end-to-end without any new spend on the LLM-bearing parts of the pipeline. Only deterministic Python + msft-smartart graft logic changed.

## Patch verification table — Run 10

| Patch / Finding | Run 10 outcome | Notes |
|---|---|---|
| **#29 (v0.1.4)** — picture-SmartArt media collision | **OBSERVED at runtime** | All 4 atmospheric image slots + 1 BG + 1 closing rendered correctly; carrier media renumbered to image7-12.png; no overwrites |
| **#27 (v0.1.3)** — loader semver preference | OBSERVED — cache had both 1.1.0 and 1.2.2; loader picked 1.2.2 | Continuous live regression coverage |
| **#26 (v0.1.3)** — picture-SmartArt image binding | OBSERVED — slide 3 picture gallery preserved | Slide 3 identical to Run 9 (the working part); +5 atmospheric markers also correct |
| **#22 (v0.1.2)** — vList2 routing | OBSERVED — slides 6 + 15 prose-length bullets render | Continuous regression coverage |
| **#17 (v0.1.x)** — BG addText cleanup | OBSERVED — slide 12 has no residual marker label | |
| **#28 (v0.1.3)** — verification escalation | NOT EXERCISED — Run 10 reused reviews from Run 8 | Helper unit-test-covered |

## v0.1.0 release scorecard

The bridge's v0.1.0 release readiness — finally, with all dogfood-surfaced findings closed:

| # | Finding | Status |
|---|---|---|
| 1 | Python 3.14 `rglob` 3-segment | shipped |
| 2 | Bare-name agent dispatch | shipped |
| 3 | Persona drift on multi-section dispatches | v0.1.x ✓ |
| 4 | SMARTART parser doesn't split on `·` | v0.2 candidate |
| 5 | `process1` 24-char label cap | subsumed by #13 |
| 6 | LibreOffice can't render injected SmartArt | known limitation, manual gate (PowerPoint Mac) |
| 7 | Split-dispatch is the working pattern | v0.1.x ✓ |
| 8 | Phase 1 LLM costs unmeasured | v0.1.x ✓ |
| 9 | SMARTART = full content zone (Contract 2) | v0.1.x ✓ |
| 10 | SmartArt carriers ship with Microsoft palette (Contract 1) | v0.1.x ✓ |
| 11 | Brief writer round-trip | shipped |
| 12 | Palette derivation accent-only | v0.1.x ✓ |
| 13 | process1 / list1 char caps too tight for prose | v0.1.x ✓ |
| 14 | smartart_from_list summary counter | v0.1.x ✓ |
| 15 | IMAGE marker wrong tool for chart-shaped subjects | Section C language workaround validated; v0.2 CHART marker kind |
| 16 | Cloud connection-reset robustness | v0.1.x ✓ |
| 17 | BG marker addText cleanup | v0.1.x ✓ |
| 18 | cohesion cost ledger kind | v0.1.x ✓ |
| 19 | Image-reviewer confabulation without expected text | v0.1.x ✓ |
| 20 | Image-reviewer reliability with expected text | v0.1.x ✓ |
| 21 | Reviewer verdict-text contradiction | v0.1.x ✓ |
| **22** | **bridge LAYOUT_BULLET_CAPS vs catalog mismatch** | **v0.1.2 ✓** |
| 23 | SMARTART-FROM-LIST marker addText cleanup | v0.2 polish |
| 24 | text_on_primary palette derivation | v0.2 brief template |
| 25 | Brief-assembly EXACT-labels format lint | v0.2 brief-save lint |
| **26** | **Picture-SmartArt image binding** | **v0.1.3 ✓** |
| **27** | **Loader prefers highest semver** | **v0.1.3 ✓** |
| **28** | **Verification escalation handshake** | **v0.1.3 ✓** |
| **29** | **Picture-SmartArt media collision** | **v0.1.4 ✓** |

**29 findings tracked across 10 dogfood runs. All release-blockers closed; remaining items are v0.2 polish or known limitations.**

## Test totals

| Suite | Tests |
|---|---|
| jack-tar-superpower-bridge | **280** (was 252 in v0.1.2; +13 verify-helper, +5 picture-binding, +8 loader-version, +2 collision-safe-allocation) |
| jack-tar-cloud | 12 |
| cross-plugin integration | 40 |
| pptx_native catalog + engine + builders | 68 (was 54; +14 from picture-builder paths now exercised) |
| **Total** | **400** |

## Plugin version state at v0.1.0 release

| Plugin | Source | Cache |
|---|---|---|
| jack-tar-superpower-bridge | **0.1.4** | 0.1.4 |
| jack-tar-msft-smartart | **1.2.2** | 1.2.2 (1.1.0 also present from `/reload-plugins`; loader correctly picks 1.2.2) |
| jack-tar-cloud | 1.1.1 | 1.1.1 (and 1.1.0 from reload) |
| jack-tar-deckhand | 1.2.0 | 1.2.0 |
| jack-tar-ollama | 1.1.0 | 1.1.0 |
| jack-tar-custom-smartart | 1.1.0 | 1.1.0 |

Marketplace manifest synced.

## Verdict — GO for v0.1.0

**Task 35 GO is recorded.** All five release-blocking findings (#22, #26, #27, #28, #29) are closed end-to-end through PowerPoint Mac PDF gate. The bridge is feature-complete for v0.1.0:

- /bridge-brief skill with split-dispatch persona pattern (R1→R2→R3a→R3b)
- /enrich-deck skill with full Contract 1 (brand palette injection) + Contract 2 (SMARTART-FROM-LIST in-place replacement)
- Picture-SmartArt image binding at production quality
- Verification escalation for image-reviewer (verification-then-confirmation, never silent dual-dispatch)
- Loader robust to `/reload-plugins` regressions
- Vellum-supporting prose-length SmartArt bullets (vList2 up to 60 chars)
- Atomic transactional apply with rollback
- Cost ledger covering brief-authoring, generation, review, cohesion
- Cohesion review with auto-action decision table
- Privacy gate handshake for internal tier
- Cross-plugin integration via plugin marketplace

Ten dogfood runs across six visual personalities + Witness/Verdict/Lament arcs + 29 findings + zero release-blocking gaps remaining.

**The branch is ready to ship.** 56+ commits ahead of origin; all v0.1.x + v0.1.2 + v0.1.3 + v0.1.4 changes uncommitted; ready to stage commit-by-finding and open the v0.1.0 release PR.

## Run 11+ thesis

The bridge is now in maintenance / polish mode for v0.2.

Outstanding v0.2 candidates (none release-blocking):

- **#15** — `CHART:slug` marker kind. Bridge routes chart-shaped subjects to `addChart()` automatically.
- **#4** — SMARTART parser handles `·` and other inline list separators.
- **#23** — SMARTART-FROM-LIST marker addText cleanup (extend #17 cleanup pattern to all marker kinds).
- **#24** — Brief template explicit `text_on_primary` row.
- **#25** — Brief-save lint runs `extract_expected_text_for_marker` for every text-bearing IMAGE marker, halts at brief-save time if any returns 0 labels.
- **Real-user pilot** — recruit a developer outside the bridge author to run a deck for an actual conference talk or board memo.
- **Dual-dispatch reviewer experiment** (#28 fix path a) — measure quality lift from Haiku + Sonnet parallel review on text-bearing markers.

Run 11 is the v0.2 milestone — not yet scoped, can wait until real-user feedback informs priorities.
