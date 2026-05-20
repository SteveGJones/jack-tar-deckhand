# Plan — `CHART:slug` marker kind for jack-tar-superpower-bridge (issue #55)

**Status:** ready for operator review of design decisions before implementation
**Created:** 2026-05-12
**Issue:** #55
**Parent EPIC:** #57 (Bridge v0.2 polish backlog)
**Sibling:** #56 (inline `·` separator fix) — landed via PR #81

## Goal

Add `CHART:slug` as a first-class marker kind alongside `IMAGE` / `BG` / `SMARTART` / `SMARTART-FROM-LIST`. This replaces the Section C "language workaround" that successfully redirected chart-shaped subjects away from `IMAGE:` markers across dogfood Runs 5–10 — but is documentation-driven and fragile.

When a brief's Section C identifies a chart-shaped subject (X-vs-Y, time series, projection, comparison bars), /pptx authors a `CHART:slug` placeholder rect. /enrich-deck reads the marker, renders a native PptxGenJS chart at the same coordinates using the brief's brand palette, and removes the placeholder.

## Why this matters

Run 4 evidence: 3 of 4 chart-shaped IMAGE markers produced garbled axis labels — generative AI cannot render axis tick values, category labels, or data-series annotations faithfully at slide scale. The workaround works but every brief author must remember to use it.

A marker grammar makes the redirection structural rather than discretionary.

## Design decisions (operator review needed)

### Decision 1 — `chart_spec` schema

The spec needs enough information to drive PptxGenJS's native `addChart()` while staying compact. Proposed shape:

```python
chart_spec = {
    # Chart type — mirrors PptxGenJS chart types
    "type": "bar" | "column" | "line" | "area" | "pie" | "doughnut" | "scatter",

    # Categories — x-axis labels (or pie/doughnut slice labels)
    "categories": ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"],

    # Series — one or more named data series
    "series": [
        {"name": "Revenue", "values": [12.5, 14.2, 15.8, 17.1]},
        {"name": "Costs",   "values": [8.1, 8.4, 8.9, 9.2]},
    ],

    # Optional metadata
    "title": "Quarterly revenue vs costs",          # if absent, no chart title (slide already has one)
    "x_axis_title": "Fiscal quarter",                # if absent, no axis title
    "y_axis_title": "USD millions",
    "show_legend": True,                              # default True for multi-series, False for single
    "value_format": "#,##0.0",                        # excel-style format string for value labels
    "palette_role": "default" | "vital_and_mourning" | "data_categorical",
}
```

**Open question (operator):** is `palette_role` the right abstraction? Three roles I propose:
- `default` — series colours derived from `BrandPalette.primary_fill_hex` + lighter shades
- `vital_and_mourning` — the bridge's two-accent register (e.g. ox-blood for emphasis, vellum for de-emphasis) — for 2-series charts where one is the "focus" series
- `data_categorical` — distinct hues from the palette's accent family (for 3+ unrelated series)

Alternative: drop `palette_role` and just have `series_colours: list[hex]` for explicit override. More flexible but more authoring burden.

**Recommendation**: ship with `palette_role` enum + optional explicit `series_colours` override. Defaults to `"default"`; operator can override.

### Decision 2 — chart rendering engine

PptxGenJS native `addChart()` is the recommended path per the issue ("Chart rendering engine choice — PptxGenJS native is sufficient; matplotlib/Vega substitution is a separate decision").

**Confirmed**: native PptxGenJS only. matplotlib/Vega-Lite paths exist in `jack-tar-custom-smartart` but those produce rasterised PNGs — using them here would defeat the "editable, native" virtue of the CHART marker. Native it is.

### Decision 3 — marker rect cleanup

The v0.2 `_drop_residual_marker_label_shapes` helper (Finding #17/#23 fix path) removes the placeholder rect AND the small "CHART:slug" addText label after enrichment. Already exists for IMAGE/SMARTART; reuse for CHART unchanged.

### Decision 4 — chart_spec sourcing

Two viable patterns:

**(a) Pre-supplied chart_spec on `EnrichmentItem`** — operator passes `chart_spec` when constructing the EnrichmentItem in /enrich-deck. The spec must come from somewhere — either the brief's Section C contains it inline, or /enrich-deck prompts the operator interactively for the data.

**(b) Extract from marker shape text** — like SMARTART-FROM-LIST, the marker shape's body text encodes the data in a structured form (e.g. `Q1 | 12.5\nQ2 | 14.2`). The bridge parses it.

**Recommendation**: pattern (a) for v1. Reasoning:
- Charts have richer structure than bulleted lists; encoding categories + multiple series in plain text gets ugly fast.
- The brief's Section C should specify chart subjects but the **data** is operator-supplied at /enrich-deck time — keeps briefs lean and lets operators paste real data without re-running /pptx.
- /enrich-deck prompts the operator for `chart_spec` per CHART marker (similar to the SmartArt overlap-warning prompt). Default empty values prompt for the minimum: type, categories, series.

Pattern (b) is a v2 candidate if the workflow becomes painful.

### Decision 5 — brand-palette injection

`BrandPalette` exists with `primary_fill_hex`, `text_on_primary_hex`, `text_on_surface_hex`. For charts the series colours need MORE colours than the palette provides — at least 4-5 distinct hues.

**Proposed approach**: derive a chart palette from `BrandPalette` at apply time:
- Single-series: primary fill colour
- Two-series with `palette_role="vital_and_mourning"`: primary + a derived "mourning" colour (HSL desaturate + darken)
- Multi-series with `palette_role="data_categorical"`: primary + an algorithmically-derived 4-colour palette (hue rotation in HSL space, fixed saturation/lightness for visual coherence)
- Operator override: explicit `series_colours: [hex, hex, ...]` always wins

Helper module: `src/chart_palette.py` with `derive_chart_palette(brand: BrandPalette, role: str, n_series: int) -> list[str]`.

### Decision 6 — persona Section C contract update

The narrative-brief-architect persona doc gets a new authoring recipe:

> **CHART markers** — for chart-shaped subjects (X-vs-Y, time series, projection curves, comparison bars), use `CHART:slug` not `IMAGE:slug`. The bridge renders a native PowerPoint chart at the marker's coordinates using the brief's brand palette. Operator supplies the chart data at /enrich-deck time; the brief just declares the marker.

Replaces the existing Section C language workaround (Runs 5-10) which redirected to native `addChart()` via Section C instructions — now redundant.

### Decision 7 — `EnrichmentItem` schema extension

Add to `EnrichmentItem`:

```python
chart_spec: dict[str, Any] | None = None  # required when kind="chart" and action!="skip"
```

Mirrors `smartart_spec`. No breaking changes to existing items.

## Implementation plan

### Phase 1 — marker grammar (~30 min)

`plugins/jack-tar-superpower-bridge/src/placeholder.py`:
- Update `MARKER_RE` regex to include `CHART`: `^(IMAGE|SMARTART-FROM-LIST|SMARTART|CHART|BG):([a-z0-9_-]+)$`
- Add CHART to the docstring's "Marker kinds" list
- Tests: parse_marker accepts `CHART:slug`, rejects `CHART:UPPER`, treats it as distinct from IMAGE

### Phase 2 — `EnrichmentItem.kind = "chart"` route (~1 hour)

`plugins/jack-tar-superpower-bridge/src/enrichment.py`:
- Extend `EnrichmentItem.kind` allowed values to include `"chart"` (update docstring)
- Add `chart_spec` field as proposed
- In `apply_enrichment`, add the chart dispatch branch

New file: `plugins/jack-tar-superpower-bridge/src/enrichment_ops/chart.py`:
- `apply_chart_enrichment(prs, slide_index, marker_name, chart_spec, brand_palette)` function
- Inside: find marker shape, read coordinates, drop marker + addText label via existing `_drop_residual_marker_label_shapes` helper, generate chart XML, insert chart graphicFrame at marker coords

PptxGenJS approach (Stage 1 — the JS assembler authored the placeholder; /enrich-deck now needs to insert a real chart). Three options:

- **(i)** Python-only via `python-pptx`'s `slide.shapes.add_chart()` — preserves the bridge's all-Python apply path. Recommended.
- **(ii)** Round-trip through PptxGenJS — invoke a Node helper script. Heavier; adds Node dependency to the bridge apply step.
- **(iii)** Direct OOXML XML construction — most control, most code. Probably overkill.

**Recommendation**: (i) python-pptx chart insertion. Library is already a bridge dependency.

### Phase 3 — chart palette derivation (~30 min)

New file: `plugins/jack-tar-superpower-bridge/src/chart_palette.py`:
- `derive_chart_palette(brand, role, n_series) -> list[str]`
- HSL-based hue rotation for `data_categorical`
- Vital/mourning pair derivation for two-accent register
- Tests covering each role × series-count combination

### Phase 4 — persona doc + brief contract (~30 min)

`plugins/jack-tar-superpower-bridge/agents/narrative-brief-architect.md`:
- Add CHART recipe to Section C marker grammar listing
- Replace the Section C "language workaround" guidance with the canonical CHART marker pattern
- Note: the workaround can still be used as a fallback (e.g. when operator wants a chart but doesn't yet have the data)

### Phase 5 — analyser + tests (~1 hour)

`plugins/jack-tar-superpower-bridge/src/analyser/`:
- Confirm OOXML primary analyser already picks up CHART:slug objectName entries (the existing `MARKER_RE` integration should Just Work)
- Add a CHART marker test fixture: a small .pptx with one CHART placeholder rect

End-to-end test:
- Fixture .pptx with CHART marker
- Call `apply_enrichment` with a `chart_spec`
- Open output, assert chart present at correct coords, marker rect removed, label text removed

### Phase 6 — dogfood validation (~30 min wall, more for the run)

Run a small end-to-end dogfood:
- Brief with 1 CHART marker (use the Run 5/6 pattern as template)
- /pptx authors the placeholder
- /enrich-deck applies the chart
- Open in PowerPoint Mac, confirm native-editable chart with brand colours

Document the run as `docs/superpowers/dogfooding/2026-05-12-chart-marker-validation.md`.

### Phase 7 — version + marketplace (~5 min)

- `plugins/jack-tar-superpower-bridge/.claude-plugin/plugin.json`: 0.2.1 → 0.2.2
- `.claude-plugin/marketplace.json`: sync

## Test count estimate

- Grammar tests: ~4 new
- Schema validation: ~5 new
- Apply path: ~6 new
- Palette derivation: ~6 new
- End-to-end: ~2 new
- **Total: ~23 new tests**

## Out of scope (per issue)

- Chart rendering engine choice (matplotlib/Vega substitution)
- Compound markers (CHART + IMAGE on same slide)
- Live data feeds — `chart_spec` is static at apply time
- Multi-axis charts (single y-axis is sufficient for v1)
- Stacked vs grouped bar variants (v1: grouped only; stacked is a `series_layout` field for v2 if needed)

## Risks

| Risk | Mitigation |
|---|---|
| python-pptx chart insertion has rougher API than PptxGenJS | Both produce OOXML; python-pptx's chart support is solid for the chart types we need |
| Operator UX for supplying chart_spec at /enrich-deck time is clunky | v1 accepts dict via the apply call; SKILL.md prompts the operator with a clear template |
| Brand palette doesn't have enough distinct hues for >5 series | Soft fail: derive_chart_palette falls back to a default categorical scheme with a logged warning; operator can supply explicit `series_colours` |
| CHART marker proliferation tempts operators to author charts where text would do | Persona doc emphasises "use CHART when the data demands it, not by default" |

## Acceptance criteria (from issue + plan)

- [ ] `placeholder.parse_marker()` recognises `CHART:slug` grammar; existing kinds unchanged
- [ ] `EnrichmentItem.kind == "chart"` route in `apply_enrichment`
- [ ] `chart_spec` schema defined and validated (chart type, categories, series, optional palette, optional formatting)
- [ ] Marker rect + addText label cleanup via existing v0.2 #23 cleanup helper
- [ ] Brand-palette injection — chart series colours derived from BrandPalette via `derive_chart_palette`
- [ ] End-to-end test fixture: deck with CHART marker renders correctly
- [ ] PowerPoint Mac PDF gate passed on dogfood run
- [ ] narrative-brief-architect.md Section C recipe lists CHART as canonical pattern for chart-shaped subjects
- [ ] Bridge version bumped 0.2.1 → 0.2.2
- [ ] Marketplace manifest synced
- [ ] All existing tests pass; +~23 new tests

## Estimated effort

**~4-5 hours** total for implementation + tests + dogfood + version bump. Single delegated session feasible.

## Open questions for operator review (BEFORE implementation starts)

1. **`palette_role` enum vs explicit `series_colours`**: my recommendation is "both — enum is the default, explicit override always wins". Confirm or override.

2. **chart_spec sourcing — pattern (a) operator-supplied at /enrich-deck vs (b) extract from marker shape text**: my recommendation is (a). Confirm or override.

3. **python-pptx vs PptxGenJS round-trip for chart insertion**: my recommendation is python-pptx. Confirm or override.

4. **Chart types in v1**: I propose `bar | column | line | area | pie | doughnut | scatter`. Drop any? Add `stacked_bar` / `stacked_column`?

5. **Should the existing Section C language workaround be DEPRECATED in the persona doc, or kept as a fallback for when operators don't have data yet?** My recommendation: keep as fallback; mark CHART as canonical.

Once you've answered the 5 questions above, the agent can implement against the plan with no further design back-and-forth.
