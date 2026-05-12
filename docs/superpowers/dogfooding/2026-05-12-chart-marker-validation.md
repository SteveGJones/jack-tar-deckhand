# 2026-05-12 — CHART marker validation (issue #55 / PR #82)

Pre-merge dogfood verification gate for the new `CHART:slug` marker kind. CI green is necessary but not sufficient for a PR that introduces a new render path — this gate confirms the chart renders correctly in PowerPoint Mac before merge per `feedback_verification_before_merge.md`.

## Method

Single-slide round-trip through the bridge's chart marker path:

1. **Author fixture** (`output/chart-marker-verification/build_fixture.js`) — single-slide .pptx via PptxGenJS with one `CHART:quarterly-figures` placeholder rect (dashed grey border, 10×4.5 inches at x=1.5, y=1.8). Centred marker label addText shape inside the rect.
2. **Run enrichment** (`output/chart-marker-verification/run_enrichment.py`) — constructs an `EnrichmentItem(kind="chart")` with a realistic 4-quarter × 2-series column chart_spec, `palette_role="vital_and_mourning"`, BrandPalette primary `#1A4D7A`. Calls `apply_enrichment()` end-to-end.
3. **Rasterise output** — LibreOffice headless → PDF → PNG at 130 dpi for automated review.
4. **Automated review** — dispatched the image-reviewer / general-purpose agent (Sonnet, fresh context) against the rasterised slide with the full expected-behaviour checklist.
5. **Manual visual gate** — operator opened the enriched .pptx in PowerPoint Mac for the final eye-check.

## chart_spec used

```python
{
    "type": "column",
    "categories": ["Q1 2026", "Q2 2026", "Q3 2026", "Q4 2026"],
    "series": [
        {"name": "Revenue", "values": [12.5, 14.2, 15.8, 17.1]},
        {"name": "Costs",   "values": [8.1, 8.4, 8.9, 9.2]},
    ],
    "title": "Quarterly revenue vs costs (USD millions)",
    "x_axis_title": "Fiscal quarter",
    "y_axis_title": "USD millions",
    "show_legend": True,
    "value_format": "#,##0.0",
    "palette_role": "vital_and_mourning",
}
```

BrandPalette: `primary_fill_hex=#1A4D7A`, `text_on_primary_hex=#FFFFFF`, `text_on_surface_hex=#1A1A1A`.

## Results

### Automated review verdict — PASS

| Check | Result |
|---|---|
| Placeholder rect removed | ✓ |
| Marker label text removed | ✓ |
| Native column chart inserted | ✓ |
| Chart type appears correct | ✓ |
| 4 x-axis categories visible (Q1-Q4 2026) | ✓ |
| 2 series visible (Revenue, Costs) | ✓ |
| Chart title rendered correctly | ✓ |
| X-axis title visible ("Fiscal quarter") | ✓ |
| Y-axis title visible ("USD millions") | ✓ |
| Legend visible | ✓ |
| Series colours distinct (vital + mourning roles) | ✓ |
| Slide title intact | ✓ |
| Slide subtitle intact | ✓ |
| Slide footer intact | ✓ |
| Chart at expected coords | ✓ |

No blocking issues.

### Operator visual gate — PASS

Operator opened `chart-verify-enriched.pptx` in PowerPoint Mac and confirmed the chart renders as expected. PDF saved for record.

## Minor observations (not blocking)

- **Per-bar data labels** appeared on the rendered chart. Not specified in the chart_spec but not harmful — likely a python-pptx default. Could be wired through a future `chart_spec["show_data_labels"]` flag if operators want explicit control.
- **Costs series rendered very dark charcoal** — close to black at small sizes. The `vital_and_mourning` palette derivation produces a dark, desaturated tone for the de-emphasis series. Readable here against a light surface, but worth a future tweak if briefs need a warmer "mourning" tone (e.g. mauve-grey, ox-blood-de-saturated).

Neither of these is a v1 blocker. Both are candidates for v0.2.3 / v0.3 polish if real-user dogfood surfaces dissatisfaction.

## Verdict

**PASS** — both gates (automated review + operator PowerPoint Mac visual confirmation). PR #82 cleared for merge.

## Artefacts

- `output/chart-marker-verification/build_fixture.js` — PptxGenJS fixture authoring
- `output/chart-marker-verification/chart-verify-fixture.pptx` — pre-enrichment input
- `output/chart-marker-verification/run_enrichment.py` — enrichment driver
- `output/chart-marker-verification/chart-verify-enriched.pptx` — post-enrichment output
- `output/chart-marker-verification/chart-verify-enriched.pdf` — LibreOffice-rasterised render
- `output/chart-marker-verification/slide-1.png` — rasterised slide for the automated reviewer

## References

- Issue: [#55](https://github.com/SteveGJones/jack-tar-deckhand/issues/55)
- PR: [#82](https://github.com/SteveGJones/jack-tar-deckhand/pull/82)
- Plan: `docs/superpowers/plans/2026-05-12-bridge-chart-marker.md`
- EPIC: [#57](https://github.com/SteveGJones/jack-tar-deckhand/issues/57)
- Verification-before-merge rule: `~/.claude/projects/-Users-stevejones-Documents-Development-jack-tar-deckhand/memory/feedback_verification_before_merge.md`
