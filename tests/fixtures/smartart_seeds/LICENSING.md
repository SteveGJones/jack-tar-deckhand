# SmartArt Seed Fixtures — Provenance and Licensing

**Legal review status:** ⚠️ **Pending** — spec §11.6 requires legal sign-off before these fixtures ship in a merged v1 release of `pptx_native`.

---

## Background

This directory contains `.pptx` files used as seeds by the `pptx_native` SmartArt engine. The engine reads each seed at runtime, extracts its four diagram parts (`layout1.xml`, `quickStyle1.xml`, `colors1.xml`, and the binding URIs on `data1.xml`'s doc point), and uses them as opaque templates against which the engine generates a fresh data model for each rendered graphic.

**What the engine does with each seed:**

1. Reads `ppt/diagrams/layout1.xml`, `quickStyle1.xml`, and `colors1.xml` as opaque bytes — these are passed through unchanged into the generated output
2. Reads `ppt/diagrams/data1.xml`'s doc point to extract the `loTypeId`/`qsTypeId`/`csTypeId` URIs that tell PowerPoint which layout to render
3. Generates a fresh `data1.xml` from the caller's input data, carrying the seed's URIs verbatim

**What the engine does NOT use from each seed:**

- The placeholder text in the seed's default nodes (the engine replaces `data1.xml` wholesale)
- The slide's other content (title, body text, images, theme customisations)
- Any Office.com clip art, theme imports, or fonts beyond the default blank template

## Licensing concern

The OOXML file format specification itself is freely implementable under ECMA-376 / ISO/IEC 29500 and Microsoft's Open Specification Promise. The schemas, namespace URIs, and the structural pattern of the diagram parts are fair game for any generator.

**The concern:** the `layout1.xml`, `quickStyle1.xml`, and `colors1.xml` files inside each seed are produced by Microsoft PowerPoint. They are part of the licensed Office installation. Redistributing them alongside an independent implementation *may* be covered by:

- Microsoft's Open Specification Promise (covers the format but not the particular XML content)
- Fair use (each seed is a minimal single-purpose example with no Office.com clip art or theme customisations)
- A specific clause in the Office Mac EULA we haven't yet reviewed

**This needs legal review** — a non-lawyer cannot make the call. The spec (`docs/superpowers/specs/2026-04-08-pptx-native-smartart-engine.md` §11.6) blocks merge of any pptx_native engine PR until legal signs off.

If legal says we cannot ship the Microsoft-authored XML, the fallback path is to hand-author a `dgm:layoutDef` from scratch per ECMA-376 Part 1 §21.4. That is a significant engineering effort but entirely within the OSP's safe harbour.

---

## Per-seed provenance

Every committed seed must have an entry in this table documenting how it was created, who created it, and what it contains.

### `process1_seed.pptx`

| Field | Value |
|---|---|
| **Author** | Steve Jones |
| **Created** | 2026-04-07 |
| **PowerPoint version** | Microsoft PowerPoint for Mac (version at time of creation; see "PowerPoint → About PowerPoint" if unsure) |
| **Creation method** | New blank presentation → Insert → SmartArt → Process → Basic Process → Save As `.pptx` |
| **Placeholder content** | Empty — default PowerPoint placeholder text only; no real content |
| **Customisations** | None — default theme, default colours, default fonts |
| **Fonts embedded** | None |
| **Clip art / images** | None |
| **Size** | 41 KB |
| **Layout URI bound** | `urn:microsoft.com/office/officeart/2005/8/layout/process1` |
| **Validation spike** | Spike 1 (`docs/spikes/2026-04-08-pptx-native-smartart-injection.md` §4) |

### `cycle1_seed.pptx`

| Field | Value |
|---|---|
| **Author** | Steve Jones |
| **Created** | 2026-04-07 |
| **PowerPoint version** | Microsoft PowerPoint for Mac |
| **Creation method** | New blank presentation → Insert → SmartArt → Cycle → Basic Cycle → Save As `.pptx` |
| **Placeholder content** | Empty — default PowerPoint placeholder text only |
| **Customisations** | None |
| **Fonts embedded** | None |
| **Clip art / images** | None |
| **Size** | 44 KB |
| **Layout URI bound** | `urn:microsoft.com/office/officeart/2005/8/layout/cycle2` (note: Mac PowerPoint's "Basic Cycle" binds to `cycle2`, not `cycle1` — the filename is historical) |
| **Validation spike** | Spike 2 (`docs/spikes/2026-04-08-pptx-native-smartart-injection.md` §9) |

### `orgChart1_seed.pptx`

| Field | Value |
|---|---|
| **Author** | Steve Jones |
| **Created** | 2026-04-08 |
| **PowerPoint version** | Microsoft PowerPoint for Mac |
| **Creation method** | New blank presentation → Insert → SmartArt → Hierarchy → Organization Chart → Save As `.pptx` |
| **Placeholder content** | Empty — default PowerPoint placeholder text + default assistant node |
| **Customisations** | None |
| **Fonts embedded** | None |
| **Clip art / images** | None |
| **Size** | 47 KB |
| **Layout URI bound** | `urn:microsoft.com/office/officeart/2005/8/layout/orgChart1` |
| **Validation spike** | Spike 4 (`docs/spikes/2026-04-08-pptx-native-smartart-injection.md` §11) |

### `blank_slide.pptx`

| Field | Value |
|---|---|
| **Author** | Steve Jones |
| **Created** | 2026-04-07 |
| **Purpose** | Test fixture for Phase 3.1 injection path — NOT a SmartArt seed. This file has zero diagram parts; its purpose is to exercise `assembler_patch.inject()` against a clean host. |
| **PowerPoint version** | Microsoft PowerPoint for Mac |
| **Creation method** | New blank presentation → Save As `.pptx` (no SmartArt inserted) |
| **Placeholder content** | Default title + subtitle placeholders from the `ctrTitle` slide layout (empty text) |
| **Customisations** | None |
| **Fonts embedded** | None |
| **Clip art / images** | None |
| **Size** | 32 KB |

---

## Adding a new seed

When committing a new `<layout>_seed.pptx` file to this directory:

1. Follow the step-by-step in `docs/dev/smartart-seed-authoring.md`
2. Add a provenance entry to this file matching the format above
3. Verify the seed passes `.venv/bin/pytest tests/test_pptx_native_seeds.py`
4. Do not commit the seed (or any engine PR that depends on it) until legal review is complete per spec §11.6

## Removing a seed

If a seed must be withdrawn (e.g., legal determines it cannot ship):

1. Delete the `.pptx` file from this directory
2. Remove the corresponding entry from `src/smartart_pptx_native/layouts/catalog.json`
3. Regenerate the catalog markdown: `python -m src.smartart_pptx_native.layouts.catalog_markdown`
4. Update this file's "Per-seed provenance" section to note the withdrawal and the reason
5. Update `docs/superpowers/specs/2026-04-08-pptx-native-smartart-engine.md` if the layout was in v1 scope
