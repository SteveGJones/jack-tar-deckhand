# Spike: /pptx marker adherence — Findings

**Date:** 2026-04-23
**Related:** [docs/superpowers/specs/2026-04-22-superpower-bridge-design.md](../../superpowers/specs/2026-04-22-superpower-bridge-design.md), GitHub issue #53

## Question

Will the `/pptx` superpower reliably emit named placeholder shapes (`IMAGE:*`, `SMARTART:*`, `BG:*`) when instructed via a creative brief, and at what level of instruction specificity?

## Procedure

Three variant briefs were fed to `document-skills:pptx` via independent general-purpose subagents:

- **A:** Minimal — markers mentioned once in passing, no PptxGenJS specifics
- **B:** Explicit — full protocol table, naming rules, shape appearance (instructed to use a `name` property)
- **C:** Exemplar — protocol plus worked PptxGenJS code examples that explicitly write `name: "IMAGE:..."` inline on `addShape`

Each output was parsed with [tools/analyse_markers.py](tools/analyse_markers.py) and scored against the requested marker counts (2× IMAGE, 1× SMARTART, 1× BG).

## Results

| Variant | Emitted IMAGE | Emitted SMARTART | Emitted BG | Total markers in OOXML | Overall rate | Verdict |
|---------|---------------|------------------|------------|------------------------|--------------|---------|
| A       | 3             | 3                | 2          | 8                      | 100%         | full    |
| B       | 0             | 0                | 0          | 0                      | 0%           | none    |
| C       | 0             | 0                | 0          | 0                      | 0%           | none    |

### Headline finding

**PptxGenJS 4.0.1 silently drops the `name` property on `addShape()`. The correct API key is `objectName`.**

- Variant A's subagent independently chose `objectName` from its own PptxGenJS knowledge → shape names landed in OOXML as `<p:cNvPr @name>` → analyser found 8 markers.
- Variants B and C's subagents used `name` (because the brief told them to) → PptxGenJS silently discarded it → OOXML shapes are anonymous → analyser found 0 markers.

Confirmed by grepping the build scripts:

| Variant | `objectName:` occurrences | `name,` occurrences | Markers in OOXML |
|---------|---------------------------|---------------------|------------------|
| A       | 2                         | 0                   | 8                |
| B       | 0                         | 7                   | 0                |
| C       | 0                         | 6                   | 0                |

This is not a `/pptx` compliance problem. All three runs emitted the correct number of visually-labeled placeholder rectangles with the correct marker strings **as slide text**. The markers render beautifully. They simply don't survive into the OOXML `cNvPr @name` attribute because the brief told `/pptx` to use the wrong PptxGenJS property.

### Qualitative observations

- The `document-skills:pptx` skill is a generic pptx-authoring rubric. It does not read the brief, does not ask clarifying questions about marker protocols, and does not object to the instructions. It points the caller at `pptxgenjs.md` and lets them follow the brief themselves.
- All three subagents produced 10-slide decks on brand, well-paced, with plausible content. Visual review confirms marker rectangles are visible, dashed, correctly positioned, and labeled with their intended marker string as body text.
- Variant A's subagent ran markitdown + python-pptx round-trip to verify shape names — the only subagent that caught the OOXML-level concern. Variants B and C's subagents verified visually only, so they reported "high adherence" even though the markers were not in OOXML.
- The BG-in-bottom-left-corner pattern was followed by all three variants (visible in every title slide rendering). BG marker placement is trivially robust — it is a small rectangle label, no ambiguity.
- Variant C deliberately did not "fix" the `name` vs `objectName` bug — its subagent flagged the issue in `run-notes.md` as a real spike finding rather than silently correcting the brief.

### Variant-specific notes

**Variant A:** Minimal brief produced the highest adherence because the subagent filled in the PptxGenJS details from its own knowledge. This is counterintuitive — less-specific instructions led to better results, because the subagent had room to use correct API calls. Emitted 3+3+2 markers against 2+1+1 requested (150% over-emission, which is fine — `/pptx` decided more slides deserved visual enrichment than the brief required).

**Variant B:** Full protocol table with explicit "Use the PptxGenJS name property". The subagent faithfully transliterated `name:` into every `addShape()` call. Zero markers in OOXML. The on-slide text labels still carry the marker strings, so a fallback content-based analyser could still discover them, but the primary OOXML lookup path is dead.

**Variant C:** Worked PptxGenJS examples with `name:` in the code. Same outcome as B. The subagent correctly identified this as a PptxGenJS API bug and flagged it in its run-notes. The exemplar pattern was followed exactly — which is why it failed the same way as Variant B.

## Decision

- [ ] **GO as designed** — Variant B hits ≥95%. NOT CHOSEN.
- [x] **GO with adjusted protocol** — The headline finding is fixable. Specific adjustments required:
  - **Update the Superpower Bridge spec's Phase 1 marker protocol to specify `objectName:` instead of `name:` as the PptxGenJS shape-name property.** This is the primary change. Variant A's successful adherence is the existence proof.
  - Update the brief's worked example code blocks (the Variant C-style exemplars) to use `objectName: "IMAGE:..."` in every `addShape()` call.
  - Update [docs/superpowers/specs/2026-04-22-superpower-bridge-design.md](../../superpowers/specs/2026-04-22-superpower-bridge-design.md) Section "Placeholder Instructions" and any exemplar code to match.
  - Optionally: have the enrichment Phase 3 analyser fall back to scanning slide **text** for marker strings when OOXML shape names are absent. This gives the bridge a safety net for briefs that get the API wrong. But this is secondary — the primary fix is to get the API key correct in the brief.
  - **Re-run the spike with a `name → objectName` fix in briefs B and C to confirm adherence rises to 100%.** This is the only remaining empirical question. (Variant A already proves `objectName` works.)
- [ ] **PIVOT** — Not required; the `/pptx` → marker path is viable after the `objectName` correction.
- [ ] **NO-GO** — Not required.

## Recommended next steps

1. **Update the Superpower Bridge spec.** Replace `name:` with `objectName:` in the marker protocol section and every exemplar code block. Add a one-line note that PptxGenJS `name` is silently dropped and `objectName` is the correct API. [docs/superpowers/specs/2026-04-22-superpower-bridge-design.md](../../superpowers/specs/2026-04-22-superpower-bridge-design.md)
2. **Re-run Variants B and C after the spec update** to confirm adherence rises to 100% with the corrected API key. This is a ~30-minute task using the same subagent scaffolding.
3. **File follow-up issue** to add a fallback marker-scanner in the bridge enrichment phase (scan slide text for `(IMAGE|SMARTART|BG):*` when OOXML shape names are missing) — defensive safety net for future briefs that drift.
4. **Optional learning for `/pptx` upstream:** File a friendly issue on `document-skills:pptx` pointing out that the PptxGenJS API key is `objectName`, not `name`. This isn't a blocker — we're adjusting our brief — but may help other skill consumers.

## Files

| Path | Purpose |
|------|---------|
| [briefs/brief-a-minimal.md](briefs/brief-a-minimal.md) | Variant A brief (minimal) |
| [briefs/brief-b-explicit.md](briefs/brief-b-explicit.md) | Variant B brief (explicit protocol) |
| [briefs/brief-c-exemplar.md](briefs/brief-c-exemplar.md) | Variant C brief (protocol + worked example) |
| [outputs/variant-a/](outputs/variant-a/) | A's deck, build script, run notes, slide rasters |
| [outputs/variant-b/](outputs/variant-b/) | B's deck, build script, run notes, slide rasters |
| [outputs/variant-c/](outputs/variant-c/) | C's deck, build script, run notes, slide rasters |
| [tools/analyse_markers.py](tools/analyse_markers.py) | Parse .pptx → list named shapes + marker counts |
| [tools/score_adherence.py](tools/score_adherence.py) | Compare requested vs. actual markers |
| [results/variant-*-analysis.json](results/) | Per-variant analyser output |
| [results/variant-*-report.json](results/) | Per-variant scored adherence report |
| [results/summary.json](results/summary.json) | Aggregate summary across all three variants |

## Test suite

10 tests total, all passing:

```
docs/spikes/2026-04-23-pptx-marker-adherence/tests/test_analyse_markers.py .....  (6)
docs/spikes/2026-04-23-pptx-marker-adherence/tests/test_score_adherence.py ....   (4)
```

Run: `.venv/bin/pytest docs/spikes/2026-04-23-pptx-marker-adherence/tests/ -v`
