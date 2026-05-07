# Bridge Dogfood Run 9

**Date:** 2026-05-01
**Topic:** Saving endangered species — making the risks and impact real (Run 8 brief, re-used unchanged)
**Audience:** ~250 conference attendees (general engaged public)
**Duration:** 25 min
**Confidentiality:** public
**Budget cap:** $5.00
**Visual personality:** Field Notes at Dusk (warm vellum + expedition ink + dried-blood mourning + held fern-green + faded ink)
**Arc:** Lament-Resolve

**Status:** Phase 1 (re-used) + Phase 2 (re-used build.js) + Phase 3 (with picture-binding) + PowerPoint Mac PDF gate complete.

**Verdict: PARTIAL GO.** Picture-SmartArt image-binding (Finding #26 fix) **WORKS END-TO-END** on the species roll-call slide — six lost species rendered with portrait + name + extinction year in a pList1 gallery, exactly the brief intent. Loader semver fix (Finding #27) **CONFIRMED LIVE** — `/reload-plugins` re-created an obsolete `1.1.0` cache version of msft-smartart but the new `_candidate_roots()` correctly picked `1.2.1`. Verification escalation helper (Finding #28) shipped, deterministic-pattern detector tested.

**A NEW finding surfaced and is the v0.1.4 release-blocker:** picture-SmartArt media injection collides with slide-level IMAGE/BG markers' media filenames, causing 4 of 5 atmospheric image slots to silently render the wrong picture (species portraits leak into the silent-forest, bleached-reef, dawn-pivot, and closing-robin slots). The picture-binding mechanism itself is structurally correct; the collision is in the carrier-graft media-filename allocation.

## Why a ninth run

Run 8 (2026-05-01) returned GO for v0.1.2 + surfaced three v0.2 polish findings (#26 picture-SmartArt image-binding, #27 `/reload-plugins` re-creates obsolete cache versions, #28 image-reviewer character-level reliability gap). The user requested implementation of all three findings as v0.1.3, with the explicit constraint that #28 must be **verification escalation with confirmation**, not silent dual-dispatch.

v0.1.3 landed earlier today: 26 new tests across 3 files, plugin bumped 0.1.2→0.1.3, marketplace synced, cache refreshed. Run 9 was scoped to dogfood verify all three:

1. **Finding #27 verification** — pre-Run-9 the user invoked `/reload-plugins`, which historically had been the regression's trigger. Confirm the loader picks the highest-semver cache version.
2. **Finding #26 verification** — re-author the Run 8 deck with `per_item_image_paths` populated for the species roll-call. Path A (picture binding) end-to-end: six species, six portraits, one Picture SmartArt.
3. **Finding #28 verification** — text-bearing IMAGE markers on slides 4 + 13 carry EXACT-labels lists; observe whether the verification helper recommends escalation; whether the SKILL.md handshake surfaces correctly.

## Pre-flight Finding #27 verification

The user's `/reload-plugins` re-created `~/.claude/plugins/cache/jack-tar/jack-tar-msft-smartart/1.1.0/` AND `~/.claude/plugins/cache/jack-tar/jack-tar-cloud/1.1.0/` — exactly the regression Run 8 caught (Claude Code's reload re-extracts older versions for plugins where the marketplace has bumped). Then:

```python
>>> from src.msft_smartart_loader import _candidate_roots, load_msft_smartart_api
>>> _candidate_roots()
[Path('~/.claude/plugins/cache/jack-tar/jack-tar-msft-smartart/1.2.1'),
 Path('plugins/jack-tar-msft-smartart')]
>>> load_msft_smartart_api().engine.catalog.get_entry('vList2')['max_label_chars']
60
```

**Finding #27 fix CONFIRMED LIVE.** Despite the reload re-creating 1.1.0 alongside 1.2.1, the loader's new `_semver_tuple()`-based sort correctly picked 1.2.1. The regression Run 8 caught is now structurally impossible. No operator workaround needed.

## Phase 1 — re-used Run 8 brief unchanged

The deck topic + audience + arc + personality were all unchanged from Run 8 (saving endangered species / Field Notes at Dusk / Lament-Resolve / 250 conference attendees). Run 8's Phase 1 brief at `output/dogfood-bridge-run-8/creative-brief.md` was simply copied to `output/dogfood-bridge-run-9/creative-brief.md`. No new dispatches; no new brief_authoring cost charged.

This validates an under-appreciated property of the bridge — once a brief is written for a topic+register, it's reusable across iterations. The only thing that varies between Run 8 and Run 9 is the marker-application strategy.

## Phase 2 — re-used Run 8 build.js unchanged

`build.js` from Run 8 was copied unchanged. The 17-slide structure, the marker locations, the bullet text — all the same. The picture-binding extension is **driven entirely by the operator-side `apply_enrichment` call**, not by /pptx authoring decisions. /pptx doesn't need to know whether the SmartArt-from-list will be rendered as text-only chevron (Run 8 path B) or picture gallery (Run 9 path A).

This is the right separation: the operator decides at apply time how rich the SmartArt should be, based on the assets available. /pptx authors marker shapes; the bridge authors enrichments.

## Phase 3 — `/enrich-deck` with picture binding

### Species portraits — Phase A Ollama generation

Six lost species, six naturalist watercolour-and-ink portraits, all generated via Ollama z-image-turbo at 1024×1024 square (Picture SmartArt cell aspect):

| Species | Phase A outcome |
|---|---|
| Passenger Pigeon (1914) | **Pass.** Long tapered tail, slate-blue head, rusty pink breast — recognisable. |
| Great Auk (1844) | **Pass.** Penguin silhouette, black/white plumage, heavy hooked bill — recognisable. |
| Thylacine (1936) | **First-attempt fail** — Ollama rendered as a wallaby/kangaroo (sitting on hindquarters, no tiger stripes). Retried with tighter prompt emphasising "DOG-bodied four-legged" + "TIGER STRIPES across the back" + explicit anti-kangaroo guidance. Second attempt **passed** — proper Thylacine with stripes. **Run 9 finding:** species-specific identifying features need explicit anti-confusion guidance in the prompt for less common species. |
| Baiji River Dolphin (2006) | **Pass.** Sleek body, long upturned beak (the identifying feature). |
| Golden Toad (1989) | **Pass.** Bright orange-gold watercolour wash, perched on moss. |
| Spix's Macaw (2000) | **Pass.** All-blue plumage, hooked bill, perched on branch. |

**Generation cost:** 7 Phase A Ollama calls (1 retry on Thylacine), $0 (free).

### Picture-SmartArt apply_enrichment

`EnrichmentItem.per_item_image_paths` populated with the 6 portrait paths in the same order as the bullet items. Bridge:

1. Validated path count matches bullet count (6 == 6) ✓
2. Resolved every image path against the security allowlist (which now included the species-portraits subdirectory) ✓
3. Routed to `pList1` (since 6 items ≥ 5 threshold) ✓
4. Constructed the picture builder's expected `items: [{label, image_path}]` shape ✓
5. Carrier .pptx contains 12 `<a:blipFill>` elements + 12 image relationships + 6 embedded media files (×2 = the layout's `pictRect` reads each image via `presOf axis="ch"` from the data point's `spPr/blipFill`) ✓

### Slide 3 picture-SmartArt rendering — **GO**

PowerPoint Mac PDF render of slide 3:

> Six species. The last of their kind.
>
> [pList1 gallery — top row of 4: Passenger Pigeon, Great Auk, Thylacine, Baiji River Dolphin]
> [bottom row of 2: Golden Toad, Spix's Macaw]
>
> Each image rendered in its picture cell. Each species name + extinction year rendered below in EB Garamond serif (the deck's body typeface).

This is the load-bearing **Finding #26 verification.** Path A (picture binding) renders end-to-end through PowerPoint Mac. The bridge contract delivers what the brief asked for: a literal naming-of-losses with their faces, exactly the elegiac roll-call register the Lament beat needs.

**Compare to Run 8's same slide** (Path B fallback): a text-only `process1` chevron with 6 navy boxes. Run 9's gallery is a categorical visual upgrade — the difference between hearing names read aloud and seeing photographs of the missing.

### Other markers — **NO-GO** due to Finding #29 (NEW)

The picture-SmartArt media injection collided with slide-level IMAGE/BG markers' media filenames. Visual evidence:

| Slide | Marker | Expected | Rendered |
|---|---|---|---|
| 3 | `SMARTART-FROM-LIST:species-rollcall` | Picture gallery | ✅ **CORRECT** — six species portraits in pList1 |
| 4 | `IMAGE:emblematic-thylacine` (Phase B) | Thylacine portrait | ✅ Correct |
| 6 | `SMARTART-FROM-LIST:ecological-cascade` | vList2 4-bullet | ✅ Correct (text-only, no media collision) |
| 8 | `IMAGE:vignette-silent-forest` | Forest dawn watercolour | ❌ **WRONG** — passenger-pigeon portrait |
| 9 | `IMAGE:vignette-bleached-reef` | Bone-white coral | ❌ **WRONG** — great-auk portrait |
| 12 | `BG:dawn-pivot` | Watercolour dawn | ❌ **WRONG** — baiji portrait |
| 13 | `IMAGE:success-california-condor` (Phase B) | Condor + foliage | ✅ Correct |
| 15 | `SMARTART-FROM-LIST:interventions` | vList2 5-bullet | ✅ Correct (text-only) |
| 17 | `IMAGE:closing-living-species` | Robin on fern | ❌ **WRONG** — thylacine portrait |

**4 of 5 atmospheric image slots silently rendered the wrong image** — exclusively the slide-level IMAGE/BG markers; the SmartArt and text-only paths are unaffected.

## Finding #29 — Picture-SmartArt media-filename collision (NEW, v0.1.4 release-blocker)

### Root cause

The host pptx's media files are named `ppt/media/image1.png`, `image2.png`, etc. python-pptx auto-numbers media files in the host as it adds them. The slide-level IMAGE markers (silent-forest, bleached-reef, etc.) and the BG marker (dawn-pivot) get numbered first via `apply_background_in_memory` / `replace_image_marker_in_memory` at Phase 2 of `apply_enrichment`.

THEN in Phase 4 (`inject_smartart_into_file`), the carrier .pptx with picture binding is grafted into the host. The carrier carries 6 `image1.png` through `image6.png` files internally — and the inject path **overwrites the host's existing image1-6 with the carrier's** rather than allocating a fresh number range starting after the host's max.

Forensic evidence in `presentation-enriched.pptx`:

```
ppt/media/image1.png   1.51 MB  ← passenger pigeon (was: silent forest)
ppt/media/image2.png   1.40 MB  ← great auk      (was: bleached reef)
ppt/media/image3.png   1.34 MB  ← thylacine      (was: closing robin)
ppt/media/image4.png   1.25 MB  ← baiji          (was: dawn pivot)
ppt/media/image5.png   1.71 MB  ← golden toad
ppt/media/image6.png   1.32 MB  ← spix's macaw
ppt/media/image5.jpg   752 KB   ← original Phase B Thylacine emblematic
ppt/media/image6.jpg   952 KB   ← original Phase B condor
```

The slide-level rels still point to `image1.png`-`image4.png` for slides 8/9/17/12 — but those filenames now resolve to species portraits because the carrier graft overwrote them.

The original atmospheric images (silent forest, bleached reef, closing robin, dawn pivot) ARE NO LONGER PRESENT in the output deck — their bytes were replaced.

### Severity

**Release-blocking for v0.1.3.** Picture-binding is now structurally proven, but ANY deck that combines picture-SmartArt with slide-level IMAGE/BG markers will silently corrupt the slide-level markers. This is silent failure — `apply_enrichment` reports success, the .pptx file opens cleanly, the SmartArt looks beautiful, and the wrong images render across the rest of the deck without any error indicator.

### Fix paths

- **(a) — collision-safe filename allocation in `assembler_patch.inject()`.** Before grafting carrier media, scan the host's `ppt/media/` for the highest existing image number; allocate carrier media starting at `max(existing) + 1`. Update the carrier's data1.xml.rels to use the renamed targets before injection. This is the principled fix and matches how python-pptx itself avoids collisions when adding multiple images.
- **(b) — namespace carrier media under a subdirectory.** The carrier could embed media at `ppt/media/diagram1/imageN.png` instead of `ppt/media/imageN.png`. Less invasive than (a) but introduces a non-standard media layout that may confuse PowerPoint's drawing cache.
- **(c) — refuse picture-binding when host already has slide-level IMAGE/BG markers.** Defensive but wrong — denies the operator the combination most useful in real decks.

**Recommendation:** ship (a) as v0.1.4. Add a regression test that builds a deck with BOTH a slide-level IMAGE marker AND a picture-SmartArt, asserts both render correctly. The Run 9 spike-build is an exact reproduction recipe for the test fixture.

## Finding #28 — verification escalation handshake — NOT EXERCISED in this run

Run 9's text-bearing IMAGE markers (slides 4 + 13) used the Phase B Flash images already generated in Run 8 (Run 9 was a reapply of the same brief with Path A picture binding swapped in for slide 3). No new image-reviewer dispatches happened, so the verification escalation handshake didn't fire.

The helper itself is unit-test-covered (13 tests in `test_verify_review_evidences_comparison.py`). Run 9 didn't disprove the implementation; it simply didn't exercise the runtime path. Future runs that involve a fresh Phase A Haiku review of a text-bearing marker will exercise the handshake.

## Cost summary

| Phase | Run 9 |
|---|---|
| Phase 1 (re-used Run 8 brief, no new dispatch) | $0.000 |
| Phase 3 species portraits — Ollama (6 + 1 retry) | $0.000 |
| Phase 3 atmospheric IMAGE/BG markers — re-used from Run 8 | $0.000 |
| Phase 3 Phase B Flash markers — re-used from Run 8 | $0.000 |
| Phase 3 reviews | $0.000 (none dispatched in Run 9) |
| Phase 3 cohesion | $0.000 (skipped, due to Finding #29 verdict) |
| **Total Phase 3** | **$0.000** |

Run 9 ran cost-free because every dispatch-bearing artefact carried over from Run 8. The cost discipline of the bridge across iterations is a separate validated property: re-applying with new picture bindings does not require new generation OR new reviews.

## Patch verification table — Run 9

| Patch / Finding | Run 9 outcome | Notes |
|---|---|---|
| **#27 (v0.1.3)** — loader prefers highest semver | **CONFIRMED LIVE** | `/reload-plugins` re-created 1.1.0 mid-session; loader picked 1.2.1 correctly |
| **#26 (v0.1.3)** — picture-SmartArt image binding | **PARTIAL** — SmartArt itself perfect; introduced **Finding #29** media-collision regression |
| **#28 (v0.1.3)** — verification escalation | NOT EXERCISED — Run 9 reused Run 8 reviews; helper is unit-test-covered |
| **#22 (v0.1.2)** — vList2 routing | OBSERVED — slides 6 + 15 still route prose-length bullets cleanly |
| **#17 (v0.1.x)** — BG addText cleanup | OBSERVED — slide 12 has no residual addText label (the BG image itself is wrong, but the cleanup did its job) |
| **#19/#20 (v0.1.x)** — image-reviewer expected_text_content | NOT EXERCISED — re-used Run 8 reviews |

## Verdict — PARTIAL GO

**v0.1.3 ships #26 picture-binding mechanism correctly + #27 loader fix correctly + #28 helper correctly. The picture-binding mechanism then introduces a SECOND-ORDER media-collision bug — Finding #29 — that breaks slide-level IMAGE/BG markers when picture-SmartArt is also present. Cannot ship v0.1.3 as-is for any deck combining picture-SmartArt with atmospheric markers.**

**Path forward — v0.1.4:**
1. Implement Finding #29 fix (a) — collision-safe filename allocation in `msft-smartart/assembler_patch.inject()`. Estimate: ~30 lines + 1 regression test.
2. Re-run a Run 10 dogfood to verify the combined-markers case renders correctly. Use Run 9's deck as the test fixture (it's a known-bad reproduction).
3. If Run 10 GO, ship v0.1.0 with all four release findings closed (#22, #26, #27, #28, plus #29).

The good news: **Path A picture-binding works.** Slide 3 of Run 9 is the load-bearing evidence that the bridge can deliver picture-SmartArt rendering at production quality. The remaining work is plumbing-correctness in the inject path.

## Anti-pattern entrenched (Run 9)

### 16. Carrier graft must allocate fresh media filenames, not assume host is empty

The msft-smartart `inject_smartart_into_file` was originally validated against decks where the carrier was the ONLY picture-bearing content. Run 9 surfaces the assumption that breaks when the host already has slide-level images: the carrier graft naively reuses `image1.png` and downstream conflicts with whatever python-pptx assigned to slide-level markers.

**Entrench:** any time msft-smartart's inject path adds files to `ppt/media/`, scan the host for collisions and renumber. Same pattern as fresh-rId allocation already done elsewhere in the inject code.

## Patterns repeatable for new operators (Run 9 additions)

### 17. Picture-SmartArt + slide-level IMAGE/BG markers is the critical co-existence test

Run 9 proves picture-SmartArt is structurally possible AND surfaces the collision risk. Any future feature touching the carrier-graft injection path should be tested against a fixture that combines picture-SmartArt + at least one slide-level IMAGE marker + one slide-level BG marker. The Run 9 deck is that test fixture: 6-species pList1 picture + 4 atmospheric IMAGE markers + 1 BG marker + 2 vList2 SmartArt + 2 native charts + 1 native table + 6 plain-prose slides = full coverage.

### 18. Brief reuse across iterations is a real cost lever

Run 9 ran cost-free in Phase 1 + Phase 3 review costs because the brief was reused from Run 8 verbatim. When iterating on enrichment strategy (path A vs path B, image asset choice, marker scale tweaks), the brief itself rarely needs revising — only the apply-enrichment dispatch changes. Document this as a cost-discipline pattern: "iterate on enrichment, not on brief."

## Run 10 thesis

Run 10 = v0.1.4 verification gate.

Implement Finding #29 fix (a) — collision-safe filename allocation in `assembler_patch.py`. Add regression test. Use Run 9 build.js + species portraits as the test fixture. Re-run. If all 9 markers render their intended content (slide 3 picture-SmartArt + 4 atmospheric IMAGEs + 1 BG + 2 vList2 + 2 native charts + 1 native table), v0.1.4 GOES; v0.1.0 ships.

If Run 10 surfaces another second-order bug, v0.1.5 patches and Run 11 re-verifies. We are converging.
