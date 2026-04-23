# Spike: python-pptx editing of /pptx superpower output — Findings

**Date:** 2026-04-23
**Related:** [docs/superpowers/specs/2026-04-22-superpower-bridge-design.md](../../superpowers/specs/2026-04-22-superpower-bridge-design.md), GitHub issue #53
**Seed source:** Spike 1 Variant A output — real PptxGenJS-produced OOXML

## Question

Can python-pptx and the existing pptx_native injection module reliably apply three enrichment operations to a .pptx produced by the `/pptx` superpower, producing a file that opens cleanly in PowerPoint Mac?

- **Op1** — set slide background to an AI-generated image
- **Op2** — replace a named shape (`IMAGE:*`) with an embedded picture at the same position
- **Op3** — graft a pptx_native SmartArt diagram into a slide, replacing a `SMARTART:*` marker

## Answer

**Yes.** All three operations work. All six unit tests pass. PowerPoint Mac opens, saves, and PDF-exports the enriched deck on the first try. Visual review of the PDF confirms every operation renders correctly.

## Procedure

1. Variant A from Spike 1 (real PptxGenJS-produced, with `objectName`-based marker shapes) was copied as the seed deck.
2. Three prototype scripts applied each op in isolation, validated by unit tests against OOXML-level structure (Tasks 4–6).
3. All three ops were then applied sequentially to a single copy of the seed (Task 7).
4. The resulting deck was opened in PowerPoint Mac via [tools/pptx_to_pdf.sh](../../../tools/pptx_to_pdf.sh), save-cycled (forces SmartArt cache regen), and exported to PDF (Task 8).
5. Every slide in the enriched deck was rendered and visually reviewed (Task 8).
6. OOXML was inspected post-mutation for anomalies ([results/post_op_inspection.md](results/post_op_inspection.md), Task 9).

## Results

### Unit tests

| Op | Tests | Pass |
|----|-------|------|
| Op1 background | 2 | 2 |
| Op2 image replacement | 2 | 2 |
| Op3 SmartArt injection | 2 | 2 |
| **Total** | **6** | **6** |

### PowerPoint Mac gate

- Open behaviour: **clean** — no repair prompt, no error dialog
- Save cycle: **succeeded**
- PDF export: **succeeded** (277 KB PDF, 10 slides)

### Visual review

- **Slide 1 (Op1 background):** ✅ Background image visible behind title. Title remains readable. The navy-on-navy overlap between original title and placeholder PNG creates faint text bleed-through — purely because both are the same colour family; real AI backgrounds with contrast-aware palettes would avoid this.
- **Slide 2 (Op2 image replacement):** ✅ Picture present at exact marker geometry (right half of slide). Title, bullets, footer all preserved. This is the cleanest result of the three.
- **Slide 4 (Op3 SmartArt injection):** ✅ PowerPoint rendered the injected Basic Process SmartArt correctly — three blue rounded rectangles "Planning → Memory → Tool use" with arrow connectors between them. Minor cosmetic: faint residual text fragments from body elements that happened to neighbour the SMARTART marker remain visible behind the SmartArt. The marker shape itself was cleanly removed; the fragments are from other text elements on the same slide.

### OOXML structural integrity

See [results/post_op_inspection.md](results/post_op_inspection.md) for the full check. Summary:

- Slide 1: `<p:cSld>/<p:bg>` present with `<a:blipFill>` pointing at `rId3 → ../media/image1.png`.
- Slide 4: one `<p:graphicFrame>` with `<dgm:relIds>` referencing all four diagram parts. `slide4.xml.rels` contains `diagramData`, `diagramLayout`, `diagramQuickStyle`, `diagramColors` relationships.
- Slide masters, layouts, and theme are preserved byte-for-byte from the seed.
- python-pptx deduped identical image blobs (op1 + op2 both used `placeholder.png`) into a single `image1.png` part — correct behaviour.

## API corrections discovered during implementation

The plan anticipated three API guesses that turned out wrong, captured here so the spec's Phase 3 section can be updated with accurate signatures:

1. **`ImagePart.new(package, blob, content_type, ext)`** — plan's guess. **Actual:** `ImagePart.new(package, image)` where `image` is a `pptx.parts.image.Image` built via `Image.from_file(path)`.

2. **`assembler_patch.inject(host_pptx, [{"slide_number": N, "carrier_path": ..., "placeholder_name": ...}])`** — plan's guess. **Actual:** the second argument is `list[InjectionRequest]` where `InjectionRequest` is a dataclass with fields `slide_number`, `carrier_pptx`, `placeholder_name`. Critically, `placeholder_name` accepts the full marker string directly — the plan's "rename SMARTART marker to `pptx_native_placeholder_<N>` before injection" step is unnecessary.

3. **Flat-list SmartArt spec data shape** — plan used `{"items": [{"text": "Planning"}, ...]}`. **Actual:** items must be a list of plain strings: `{"items": ["Planning", "Memory", "Tool use"]}`. Dict items raise `FlatListBuildError: flat_list items must be strings`.

All three corrections are captured in the prototype code as-shipped.

## Python-pptx capability summary

| Operation | Covered by public API | Required XML surgery | Complexity |
|-----------|----------------------|----------------------|------------|
| Background image | No | Yes — hand-build `<p:bg><p:bgPr><a:blipFill>` via lxml, insert as first child of `<p:cSld>` | Medium — 30 lines, deterministic |
| Shape replacement with picture | Partial — `slide.shapes.add_picture()` works; shape removal is XML-level | Yes — remove marker shape via `sp._element.getparent().remove(sp._element)` | Low |
| SmartArt graft via assembler_patch | Plugin-provided, used as-is | No | Low (from our side; the plugin is where the surgery lives) |

## Non-blocking follow-ups for the real bridge

1. **Marker-adjacent text clearing contract.** Slide 4 showed faint residual text fragments behind the injected SmartArt — they were body text in neighbouring text boxes, not part of the marker itself. Decide: does enrichment clear bullet text that happens to live inside the marker's geometry? Does the brief dictate that SMARTART-marker slides contain only title + marker? Document the contract.

2. **Empty-directory artefacts in PptxGenJS seed.** python-pptx drops empty directory entries (`ppt/embeddings/`, `ppt/charts/`) when re-saving. No functional impact but worth noting so the enrichment report can set correct expectations about byte-level file diffs.

3. **Image blob deduplication is default-on.** Two ops using the same image path = one `image1.png` part. This is free efficiency, but document it — if future ops want "identical image, different rId" they'd need to force uniqueness.

## Decision

- [x] **GO** — All three ops pass tests + PowerPoint gate + visual review + OOXML inspection. Prototypes are ready to migrate into `plugins/jack-tar-superpower-bridge/src/enrichment.py` once that plugin exists. Bridge Phase 3 can be built as designed.
- [ ] GO with adjustments — not required
- [ ] PIVOT — not required
- [ ] NO-GO — not required

## Recommended next steps

1. **Update the Superpower Bridge spec** with the three API corrections documented above (Section 3.4 image application; the SmartArt data-shape paragraph).
2. **Fold Spike 1's `name → objectName` correction** into the spec's Phase 1 placeholder protocol and exemplar code.
3. **Draft the enrichment contract for marker-adjacent text** (see Non-blocking follow-up #1). One sentence in the spec is enough to prevent ambiguity.
4. **Move on to the smaller design concerns** from the original critical review (build-script-parsing-vs-pptx-parsing, title slide classification, v1 scope, slide addressing, cost tracking, rollback semantics). None require a spike.
5. **Then the spec is ready for a final critical review pass** before the bridge plugin implementation plan can be written.

## Files

| Path | Purpose |
|------|---------|
| [seed/seed.pptx](seed/seed.pptx) | Variant A copy — real PptxGenJS OOXML |
| [seed/placeholder.png](seed/placeholder.png) | Stand-in image for op1/op2 |
| [prototypes/op1_background.py](prototypes/op1_background.py) | Apply slide background image |
| [prototypes/op2_replace_image_shape.py](prototypes/op2_replace_image_shape.py) | Replace named shape with picture |
| [prototypes/op3_inject_smartart.py](prototypes/op3_inject_smartart.py) | Graft pptx_native SmartArt |
| [tests/test_op1_background.py](tests/test_op1_background.py) | Op1 tests |
| [tests/test_op2_replace_image.py](tests/test_op2_replace_image.py) | Op2 tests |
| [tests/test_op3_inject_smartart.py](tests/test_op3_inject_smartart.py) | Op3 tests |
| [outputs/after_op1.pptx](outputs/after_op1.pptx) | Seed + op1 only |
| [outputs/after_op2.pptx](outputs/after_op2.pptx) | Seed + op2 only |
| [outputs/after_op3.pptx](outputs/after_op3.pptx) | Seed + op3 only |
| [outputs/all_ops.pptx](outputs/all_ops.pptx) | Seed + all three ops applied in sequence |
| [outputs/all_ops.pdf](outputs/all_ops.pdf) | PowerPoint-generated PDF of enriched deck |
| [outputs/all_ops_slides/](outputs/all_ops_slides/) | Per-slide PNGs of enriched deck |
| [results/ooxml_inspection.md](results/ooxml_inspection.md) | Pre-op capability research |
| [results/post_op_inspection.md](results/post_op_inspection.md) | Post-op OOXML structural check |
| [results/findings.json](results/findings.json) | Machine-readable findings |

## Test suite

6 tests, all passing:

```
docs/spikes/2026-04-23-python-pptx-enrichment/tests/test_op1_background.py ..   (2)
docs/spikes/2026-04-23-python-pptx-enrichment/tests/test_op2_replace_image.py .. (2)
docs/spikes/2026-04-23-python-pptx-enrichment/tests/test_op3_inject_smartart.py .. (2)
```

Run: `.venv/bin/pytest docs/spikes/2026-04-23-python-pptx-enrichment/tests/ -v`
