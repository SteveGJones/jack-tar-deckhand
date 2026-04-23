# Spike 3: Analyser Source Comparison — JS Build Script vs .pptx OOXML

**Date:** 2026-04-23
**Related:** [Superpower Bridge spec](../../superpowers/specs/2026-04-22-superpower-bridge-design.md), [team review](../../superpowers/specs/2026-04-23-superpower-bridge-team-review.md), GitHub issue #53.

## Question

For the Section 3.1 analyser's actual needs (marker shape names, geometries, text content, element types, background state, slide classification), should the primary analysis source be the `/pptx` JavaScript build script, the .pptx OOXML, or both?

The team review's #1 critical theme claimed OOXML should be primary because "OOXML is stable, JS is LLM-variable." But neither Spike 1 nor Spike 2 actually tested JS parsing — both used OOXML only. This spike closes that empirical gap.

## Procedure

Built two parsers against a shared `SlideFacts` contract and ran them on four cases:

| Case | Source | Brief used | OOXML markers | build.js present |
|------|--------|------------|---------------|------------------|
| Variant A | Spike 1 | `objectName:` (implicit correction by subagent) | 8 | yes |
| Variant B | Spike 1 | `name:` (as originally specified — WRONG per Spike 1) | 0 | yes |
| Variant C | Spike 1 | `name:` (same as B) | 0 | yes |
| Control | Hand-built via python-pptx | n/a (no build.js) | 1 | no |

Both parsers emit `list[SlideFacts]`. The comparison harness runs both and produces a per-slide field agreement matrix for three signal fields: `markers`, `background_kind`, `text_content_len`.

## Results

Source: [results/summary.json](results/summary.json).

### Marker extraction — the headline finding

| Case | OOXML markers | JS markers | Marker agreement | Interpretation |
|------|---------------|------------|------------------|----------------|
| Variant A | 8 | 8 | **10/10 slides** | Both parsers agree — brief used correct API |
| Variant B | 0 | 8 | 2/10 slides | **JS parser recovers markers OOXML lost.** Brief used `name:` which PptxGenJS dropped, but the JS parser reads `name:` directly from the AST. |
| Variant C | 0 | 10 | 0/10 slides | Same as B — JS parser rescues the data OOXML never received. |
| Control | 1 | n/a | 0/3 slides (JS side absent) | **OOXML works without build.js. JS parser cannot.** |

Marker extraction is the single most important signal the analyser needs. The results show a clear asymmetry: each source has a failure mode the other doesn't cover.

- **OOXML fails silently** when the brief uses the wrong PptxGenJS API key (the `name` vs `objectName` bug that Spike 1 surfaced). The shape rectangles render; the names don't persist into OOXML. OOXML-only analysis produces zero markers and silently under-matches.
- **JS parsing fails hard** when no build.js exists. Corporate templates, Keynote exports, user-edited decks — any deck that didn't come from /pptx. The control case is the simplest possible test: python-pptx built a 3-slide deck with one named marker shape. JS parser has nothing to read.

### Text content length — minor finding

Agreement rates on `text_content_len` (two values agree if within ±20 chars):

- Variant A: 7/10
- Variant B: 9/10
- Variant C: 3/10
- Control: 0/3 (JS absent)

The parsers extract text differently. OOXML reads rendered text from `<a:t>` nodes in all text frames. The JS parser collates arguments to `addText()` calls. The disagreement is mostly from:
- PptxGenJS helper functions that concatenate text before calling `addText` (OOXML sees the concatenated result; JS sees the pieces).
- Variant C's template-literal marker construction — JS parser evaluates templates, OOXML sees only the rendered label.

Neither is "wrong"; they measure different things. For the analyser's purpose (classifying slides as text-heavy / list / already-rich), either works. Text-content classification is robust to ±20% drift.

### Background state — unexpected finding

Agreement on `background_kind` is 0/10 for Variants A and B, 10/10 for Variant C, and n/a for control. Investigation:

- OOXML parser reports `"default"` (no `<p:bg>` element) for all three variants' slides because PptxGenJS doesn't emit `<p:bg>` for colour-only backgrounds — it just sets `bgColor` on the slide element.
- JS parser reports `"solid"` when it sees `slide.background = { color: "..." }` assignments.

Both are correct reads of their respective sources, but they disagree on what to *call* a colour background. For the analyser's needs, either signal is sufficient to classify "this slide has/doesn't have a custom background." Field definition needs minor alignment.

### JS parsing complexity — an important methodology observation

The plan's template JS parser passed tests only after the implementer added three non-trivial features that weren't in the template:

1. **Block-scope isolation** — Variant A declares `{ const s = pres.addSlide(); ... }` per-slide blocks. Without deep-copying `slide_bindings` on block entry, all 10 slides collided into one.
2. **Helper-function parameter binding** — Variant A uses `addMarker(slide, name, opts)` helpers. Pure AST walk on `slide.addShape(...)` misses everything; parser must descend into helper bodies with param aliasing.
3. **ObjectPattern destructuring + template literals** — Variant C uses `const { x, y, w, h, slug } = opts; const name = \`IMAGE:${slug}\`;`. Parser must resolve destructuring and evaluate the template literal to recover the marker string.

These aren't hypothetical; they were encountered in real /pptx output from three variants run 48 hours apart. Each variant's subagent chose a different JS idiom for the same job. That variability is the core robustness concern the team review flagged — confirmed empirically.

## Field-by-field scoring

For each `SlideFacts` field the analyser needs, what does each parser get right?

| Field | OOXML | JS | Notes |
|-------|-------|----|-------|
| **Marker shape name** | ✅ when brief is correct; ❌ silently when brief uses `name:` | ✅ from AST (reads both `name` and `objectName`) but ❌ unusable without build.js | Complementary failure modes |
| **Marker geometry** | ✅ exact (EMU) | ✅ after inches→EMU conversion; depends on literal values being parseable | OOXML more robust for computed geometry |
| **Text content** | ✅ authoritative (rendered) | ✅ different semantics (raw call args) | ±20% drift, classification-safe |
| **Background kind** | ✅ for images; ⚠️ misses PptxGenJS colour-only (no `<p:bg>`) | ✅ for `slide.background =` assignments | Neither is complete alone |
| **Element types (shapes, images, charts, tables)** | ✅ stable via `MSO_SHAPE_TYPE` | ✅ via method name (`addImage`, `addChart`, etc.) | Both reliable for counting |
| **Slide count + ordering** | ✅ | ✅ | Both reliable |

## Robustness observations

- **JS parser handled all three /pptx variants after adding AST features**, but each variant needed something new. A fourth variant could easily introduce a pattern neither the current parser nor the template handles (e.g., arrow functions, class methods, `async`/`await`, dynamic method names, PptxGenJS options built by spreading).
- **OOXML parser handled all four cases including the non-PptxGenJS control unchanged.** No idiom-specific features needed. The OOXML schema is a contract between PowerPoint, python-pptx, and us — stable.
- **JS parser raised zero exceptions in the four tested cases.** esprima with `tolerant: True` is robust at the tokenisation level. But "no exception" is not the same as "correct extraction" — silent under-matching is the real risk, and we saw it's possible.
- **The control case is the critical empirical check.** OOXML: 1 marker, everything else extracted cleanly. JS: unusable, cannot proceed. Any design that requires the build script cannot handle corporate templates or non-/pptx-authored decks.

## Richness observations (does JS expose anything OOXML doesn't?)

The team spec claimed "the JS build script has richer semantic information." Empirically, what does JS expose that OOXML doesn't?

- **Variable names** (e.g., `titleBox`, `heroImage`). The JS parser can see them; OOXML can't. For the analyser's Section 3.1 needs, variable names aren't consumed.
- **Function names / helper names** (e.g., `addMarker`, `addFooter`). Same observation — JS has them, analyser doesn't need them.
- **Comments** (e.g., `// Slide 3: "Why most agents fail"`). Same.
- **Programmatic structure** (loops, conditionals, helper compositions). Same — visible in JS, absent from OOXML, not consumed by the analyser.

**The richness claim is true, but the richer information is not in the analyser's requirements.** The analyser asks only: what's on the slide, where, what's in the text, what's the background? OOXML has all of it in a stable, schema-defined location.

## Decision

- [ ] **GO with JS primary** — Not justified. JS parser cannot work without build.js; fails the control case outright; requires per-variant feature additions.
- [ ] **GO with OOXML primary** (team review's recommendation) — Necessary but not sufficient. Handles the control case, but fails silently when the brief uses the wrong PptxGenJS API. Leaves Variants B and C as unusable.
- [x] **GO with HYBRID: OOXML primary + JS fallback for markers when OOXML-marker-count is zero and build.js exists.**

The hybrid approach exploits each source's strengths:

1. **OOXML is the primary source for all fields** — it's available in every case including non-/pptx decks, handles every field the analyser needs, and has a stable schema.
2. **JS parser runs only as a fallback for marker extraction** when three conditions all hold: (a) OOXML found zero markers; (b) the deck is a /pptx output (`build.js` exists alongside); (c) the brief *intended* markers (determinable from the brief itself or via a prompt to the user).
3. **The JS parser's complexity is quarantined** behind the fallback trigger. If the JS parser fails (new idiom, minified script, missing build.js), we degrade to "no markers found" plus a user-facing note — the same failure mode as OOXML-only.

This matches the team review's consensus (OOXML primary) while keeping the JS fallback as the Spike 1-recommended safety net. The text-scan fallback mentioned in Spike 1 is NOT needed separately — the JS fallback subsumes it for /pptx-authored decks, and non-/pptx decks don't have the problem (OOXML is the only source anyway).

## Spec update list

Concrete changes to the Superpower Bridge spec from this spike's decision:

1. **Section 3.1 — Deck Analysis.** Rewrite the opening paragraph. Replace "The skill accepts the .pptx path and looks for the build script in the same directory (the superpower leaves it alongside the output)" with:

   > The skill accepts the .pptx path and parses OOXML via python-pptx as the primary source. Per-slide information extracted: marker shape names (via `<p:cNvPr @name>` matching `(IMAGE|SMARTART|BG):<identifier>`), marker geometry (via `<a:xfrm>`), text content (via `<a:t>`), background state (`<p:bg>`), element types. The build script (if present alongside the .pptx) serves as a targeted fallback for marker extraction when OOXML returns zero markers — this covers briefs that used `name:` instead of `objectName:` per Spike 1's finding. All other fields come from OOXML.

2. **Section 3.1 — Classification table.** No change needed; the extracted fields are the same.

3. **Section 3.1 — new subsection "Fallback for marker extraction":**

   > When OOXML yields zero markers AND `build.js` exists in the .pptx's directory, attempt JS parsing via esprima as a fallback. Extract marker shapes from `addShape(..., { objectName|name: "...", x, y, w, h })` calls, resolving helper-function indirection via AST walk with slide-parameter aliasing. If JS parsing raises or also finds zero markers, the analyser reports "no markers" and proceeds with unmarked-slide classification heuristics.

4. **Key Design Decision #2.** Replace "Analyse the build script, not the .pptx. The JS script has richer semantic information than the compiled binary" with:

   > Primary source is the .pptx OOXML (stable schema, always available, covers non-/pptx decks). The build script (if present) serves as a targeted fallback for marker extraction when OOXML finds zero markers. This combination handles both the `objectName` vs `name` API bug (Spike 1) and non-/pptx-authored decks (control case in Spike 3).

5. **Risk Register.** Update the "Build script format changes" row — mitigation is now "parser used only as fallback; primary path is OOXML which has a stable schema". Reduce severity accordingly.

6. **Plugin Structure.** `src/analyser.py` imports both `python-pptx` and `esprima`. Declare `esprima` as a dependency in the plugin's `requirements.txt`.

## Next steps

1. Apply the 6 spec edits above to [docs/superpowers/specs/2026-04-22-superpower-bridge-design.md](../../superpowers/specs/2026-04-22-superpower-bridge-design.md).
2. Cross the "Parse the .pptx, not the JS build script" theme off the team review's critical-gaps list (it's now resolved with evidence-based nuance).
3. Continue with the other 5 team-review themes (text-scan fallback is now subsumed by the JS fallback; AI persona definitions, SMARTART verifier, transactional semantics, security hardening, marker grammar still open).

## Files

| Path | Purpose |
|------|---------|
| [parsers/slide_facts.py](parsers/slide_facts.py) | Shared contract — `SlideFacts` + `Marker` dataclasses |
| [parsers/pptx_parser.py](parsers/pptx_parser.py) | OOXML parser via python-pptx |
| [parsers/js_parser.py](parsers/js_parser.py) | JS AST parser via esprima |
| [harness/compare.py](harness/compare.py) | Runs both parsers, produces per-slide agreement |
| [harness/aggregate.py](harness/aggregate.py) | Aggregates matrices into summary |
| [fixtures/build_control.py](fixtures/build_control.py) | Builder for the non-/pptx control deck |
| [fixtures/control.pptx](fixtures/control.pptx) | Non-/pptx 3-slide control deck |
| [tests/test_slide_facts.py](tests/test_slide_facts.py) | Contract roundtrip + validation (2 tests) |
| [tests/test_pptx_parser.py](tests/test_pptx_parser.py) | OOXML parser on Variant A (4 tests) |
| [tests/test_js_parser.py](tests/test_js_parser.py) | JS parser on Variants A+C (4 tests) |
| [tests/test_compare.py](tests/test_compare.py) | Harness contract (2 tests) |
| [results/matrix-variant-*.json](results/) | Per-case agreement matrices |
| [results/summary.json](results/summary.json) | Aggregated summary |

## Test suite

12 tests, all passing:

```
tests/test_slide_facts.py  ..  (2)
tests/test_pptx_parser.py  ....  (4)
tests/test_js_parser.py    ....  (4)
tests/test_compare.py      ..  (2)
```

Run: `PYTHONPATH=docs/spikes/2026-04-23-analyser-source-comparison/parsers:docs/spikes/2026-04-23-analyser-source-comparison/harness .venv/bin/pytest docs/spikes/2026-04-23-analyser-source-comparison/tests/ -v`

(The `PYTHONPATH` is not required for the tests themselves — they manage sys.path internally — but it is needed for the CLI stubs in `compare.py`.)
