# Generating Editable PowerPoint SmartArt from Outside PowerPoint
## Implementation, Validation & Recommendation
*Phase 2 of 2 — research executed 2026-04-07*

> **Honesty preface.** This report is the output of a research agent operating without a Windows host, without a licensed Microsoft Office, and without a way to open `.pptx` files in PowerPoint to verify the SmartArt Design ribbon visually. Every claim that *would* be a "I ran it and saw a green tick in PowerPoint" claim in a real engineering report is therefore marked **[unverified — requires PowerPoint desktop]**. The code, XML structures, library APIs, and decision rationale are based on the public spec, vendor docs, GitHub issue trackers, and the Phase 1 briefing. A human engineer should re-run the bake-off on a Windows + Office machine before committing to a production path. Treat this document as a high-quality, opinionated *blueprint* — not a test report.

---

## 1. Reference scenarios

We anchor every approach to the same three concrete deliverables. They were chosen to exercise the three structurally different SmartArt algorithm families.

| ID | Layout category | Layout URI | Algorithm | Reference content |
|---|---|---|---|---|
| **A** | Hierarchy → Organization Chart | `urn:microsoft.com/office/officeart/2005/8/layout/orgChart1` | `hierChild` / `hierRoot` | 25 nodes, 4 levels deep, populated from `org.json`. |
| **B** | Process → Basic Process | `urn:microsoft.com/office/officeart/2005/8/layout/process1` | `lin` (linear) | 7 steps, custom accent colour per step. |
| **C** | Cycle → Basic Cycle | `urn:microsoft.com/office/officeart/2005/8/layout/cycle1` | `cycle` | 6 nodes, built dynamically. |

`org.json` shape (used throughout):

```json
{
  "id": "ceo", "title": "CEO",
  "children": [
    { "id": "cto", "title": "CTO", "children": [ … ] },
    { "id": "cfo", "title": "CFO", "children": [ … ] },
    …
  ]
}
```

---

## 2. The reference oracle (COM-automated PowerPoint)

We treat a Windows + PowerPoint 365 + COM automation pipeline as the **ground-truth oracle**. Every other approach is judged by how closely its `data1.xml` and `[Content_Types].xml` match the oracle's, after canonicalisation.

`oracle/build_oracle.ps1`:

```powershell
param([string]$OutPath = ".\oracle\scenarioA.pptx")

$ppt  = New-Object -ComObject PowerPoint.Application
$ppt.Visible = [Microsoft.Office.Core.MsoTriState]::msoFalse
$pres = $ppt.Presentations.Add()
$slide = $pres.Slides.Add(1, 12)   # 12 = ppLayoutBlank

$layout = $ppt.SmartArtLayouts.Item("urn:microsoft.com/office/officeart/2005/8/layout/orgChart1")
$shp = $slide.Shapes.AddSmartArt($layout, 50, 50, 600, 400)

# Walk org.json and call AddNode(msoSmartArtNodeBelow / NodeAfter)
$org = Get-Content .\org.json -Raw | ConvertFrom-Json
function Populate($parent, $data) {
    $parent.TextFrame2.TextRange.Text = $data.title
    foreach ($c in $data.children) {
        $child = $parent.AddNode(2)   # 2 = msoSmartArtNodeBelow
        Populate $child $c
    }
}
Populate $shp.SmartArt.AllNodes.Item(1) $org

$pres.SaveAs((Resolve-Path $OutPath).Path, 24)  # 24 = ppSaveAsOpenXMLPresentation
$pres.Close(); $ppt.Quit()
```

The `pywin32` equivalent is in `oracle/build_oracle.py`. Both target the *same* `Shapes.AddSmartArt` API documented at Microsoft Learn (Phase 1 ref [10]) and the same `Application.SmartArtLayouts` collection (ref [26]).

The oracle output is unzipped and stored in `oracle/expanded/` so that downstream approaches can be diffed against it.

---

## 3. The XML diffing protocol

`tools/diff_pptx.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
A="$1"; B="$2"
DIR=$(mktemp -d)
unzip -q "$A" -d "$DIR/a"
unzip -q "$B" -d "$DIR/b"
for f in $(cd "$DIR/a" && find ppt/diagrams '[Content_Types].xml' ppt/slides/_rels -type f); do
  if [ -f "$DIR/b/$f" ]; then
    xmllint --c14n "$DIR/a/$f" > "$DIR/a.c14n" 2>/dev/null || cp "$DIR/a/$f" "$DIR/a.c14n"
    xmllint --c14n "$DIR/b/$f" > "$DIR/b.c14n" 2>/dev/null || cp "$DIR/b/$f" "$DIR/b.c14n"
    diff -u "$DIR/a.c14n" "$DIR/b.c14n" | sed "s|$DIR|.|g" || true
  else
    echo "MISSING in B: $f"
  fi
done
```

The protocol: canonicalise with `xmllint --c14n`, diff each diagram part, and treat any divergence in `data1.xml` element ordering or `cxnLst` membership as a defect. `drawing1.xml` divergence is tolerated (it is a render cache); `quickStyle1.xml` and `colors1.xml` should be byte-identical when copied from a seed. The CI gate fails the build if `ppt/diagrams/data1.xml` differs in anything other than `modelId` GUIDs (which are randomised).

---

## 4. The five approaches, bake-off

### 4.1 Approach A — Template injection with python-pptx + lxml *(recommended primary)*

**Idea.** Author one seed `.pptx` per layout in PowerPoint by hand (each containing exactly one empty SmartArt of the target layout), check the seeds into source control, and at runtime copy a seed, rewrite `ppt/diagrams/data1.xml` from the input data, and delete `ppt/diagrams/drawing1.xml` so PowerPoint regenerates the cached render on first open.

**Why this wins.** It piggy-backs on PowerPoint's own `layout1.xml`/`quickStyle1.xml`/`colors1.xml`, so layout coverage is automatically equal to PowerPoint's. The generator only has to understand `dgm:dataModel` — the simplest of the four parts.

**Generator skeleton** (`generator/inject.py`):

```python
"""
Editable SmartArt generator via template injection.
Requires: python-pptx==1.0.2, lxml==5.2.2
"""
from __future__ import annotations
import json, shutil, uuid, zipfile, io, os
from pathlib import Path
from lxml import etree

NSMAP = {
    "dgm": "http://schemas.openxmlformats.org/drawingml/2006/diagram",
    "a":   "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r":   "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
DGM = "{%s}" % NSMAP["dgm"]
A   = "{%s}" % NSMAP["a"]

def _mid() -> str:
    return "{%s}" % uuid.uuid4()

def _pt(model_id: str, type_: str, text: str | None = None) -> etree._Element:
    pt = etree.Element(DGM + "pt", attrib={"modelId": model_id, "type": type_})
    prSet = etree.SubElement(pt, DGM + "prSet")
    spPr  = etree.SubElement(pt, DGM + "spPr")
    if text is not None:
        t = etree.SubElement(pt, DGM + "t")
        p = etree.SubElement(t, A + "p")
        r = etree.SubElement(p, A + "r")
        rPr = etree.SubElement(r, A + "rPr"); rPr.set("lang", "en-US")
        tt = etree.SubElement(r, A + "t"); tt.text = text
    return pt

def _cxn(src: str, dst: str, type_: str, src_ord: int, dst_ord: int) -> etree._Element:
    return etree.Element(DGM + "cxn", attrib={
        "modelId": _mid(), "type": type_,
        "srcId": src, "destId": dst,
        "srcOrd": str(src_ord), "destOrd": str(dst_ord),
    })

def build_data_model(root_node: dict) -> bytes:
    """Walk a tree -> dgm:dataModel bytes for a Hierarchy / orgChart layout."""
    dm = etree.Element(DGM + "dataModel", nsmap=NSMAP)
    ptLst  = etree.SubElement(dm, DGM + "ptLst")
    cxnLst = etree.SubElement(dm, DGM + "cxnLst")

    # Mandatory document point.
    doc_id = _mid()
    ptLst.append(_pt(doc_id, "doc"))

    def walk(node: dict, parent_id: str, sib_ord: int) -> None:
        node_id = _mid()
        ptLst.append(_pt(node_id, "node", node["title"]))
        # parTrans + sibTrans pair (required by hierChild)
        par_t = _mid(); sib_t = _mid()
        ptLst.append(_pt(par_t, "parTrans"))
        ptLst.append(_pt(sib_t, "sibTrans"))
        cxnLst.append(_cxn(parent_id, node_id, "parOf", sib_ord, sib_ord))
        cxnLst.append(_cxn(parent_id, par_t,  "presParOf", sib_ord, sib_ord))
        cxnLst.append(_cxn(parent_id, sib_t,  "presParOf", sib_ord, sib_ord))
        for i, child in enumerate(node.get("children", [])):
            walk(child, node_id, i)

    walk(root_node, doc_id, 0)

    # Background + whole + extLst stubs (PowerPoint tolerates empties)
    etree.SubElement(dm, DGM + "bg")
    etree.SubElement(dm, DGM + "whole")
    return etree.tostring(dm, xml_declaration=True, encoding="UTF-8", standalone=True)

def inject(seed_pptx: Path, out_pptx: Path, data_model_bytes: bytes) -> None:
    shutil.copyfile(seed_pptx, out_pptx)
    # Rewrite ppt/diagrams/data1.xml; drop drawing1.xml + its rel.
    tmp = out_pptx.with_suffix(".tmp.pptx")
    with zipfile.ZipFile(out_pptx, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            name = item.filename
            if name == "ppt/diagrams/data1.xml":
                zout.writestr(item, data_model_bytes); continue
            if name == "ppt/diagrams/drawing1.xml":
                continue                                 # force regeneration
            if name == "ppt/diagrams/_rels/data1.xml.rels":
                # strip the relationship pointing at drawing1.xml
                rels = etree.fromstring(zin.read(name))
                for rel in list(rels):
                    if rel.get("Type", "").endswith("/diagramDrawing"):
                        rels.remove(rel)
                zout.writestr(item, etree.tostring(rels, xml_declaration=True, encoding="UTF-8", standalone=True))
                continue
            zout.writestr(item, zin.read(name))
    os.replace(tmp, out_pptx)

if __name__ == "__main__":
    org = json.loads(Path("org.json").read_text())
    inject(
        seed_pptx=Path("seeds/orgChart1_seed.pptx"),
        out_pptx=Path("out/scenarioA.pptx"),
        data_model_bytes=build_data_model(org),
    )
```

**Seed creation.** A human opens PowerPoint once, inserts a SmartArt of each target layout with no real content, deletes the placeholder text, and saves three seed files: `seeds/orgChart1_seed.pptx`, `seeds/process1_seed.pptx`, `seeds/cycle1_seed.pptx`. Each seed is checked in. Total seed payload: ~30 KB each.

**Scenario B (Process)** uses the same `inject()` but a different `build_data_model()` that emits a flat list of `node` points with `lin`-friendly `parTrans`/`sibTrans` pairs. **Scenario C (Cycle)** is identical to B but with `cycle1_seed.pptx` — `cycle` algorithm has the same data-model shape as `lin`.

**Editable in PowerPoint?** **[unverified — requires PowerPoint desktop]** Theoretically yes, because the layout part is untouched and the data model is well-formed. The Phase 1 §7 failure modes that this approach intentionally avoids are: stale `drawing1.xml` (deleted), missing parts (seed has them), wrong content types (seed has them), unbalanced parTrans/sibTrans (generator emits pairs).

**Editable in PowerPoint for Mac?** **[unverified]** Expected yes — same code paths.

**Pros.** Cheapest, simplest, smallest blast radius, layout coverage = PowerPoint's. CI-friendly: pure Python, no native dependencies.
**Cons.** Requires one seed per layout. The licensing of shipping PowerPoint-authored seed files inside your repo is the same question as shipping `.glox` content (Phase 1 §8) — review with legal.

### 4.2 Approach B — Raw OOXML authoring with Open XML SDK 3.x (.NET / C#)

**Idea.** No seed file. Build all four diagram parts and the slide graphic frame from scratch using `DocumentFormat.OpenXml.Drawing.Diagrams`.

**Skeleton** (`generator/dotnet/SmartArtBuilder.cs`):

```csharp
using DocumentFormat.OpenXml;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Presentation;
using Dgm = DocumentFormat.OpenXml.Drawing.Diagrams;
using A   = DocumentFormat.OpenXml.Drawing;
using P   = DocumentFormat.OpenXml.Presentation;

public static class SmartArtBuilder
{
    public static void AddOrgChart(SlidePart slidePart, OrgNode root)
    {
        var dataPart  = slidePart.AddNewPart<DiagramDataPart>();
        var layoutPart= slidePart.AddNewPart<DiagramLayoutDefinitionPart>();
        var stylePart = slidePart.AddNewPart<DiagramStylePart>();
        var colorPart = slidePart.AddNewPart<DiagramColorsPart>();

        // 1. Layout: load orgChart1 layout XML from an embedded resource.
        //    (We extracted it once from a hand-built seed pptx and committed
        //     it to /Resources/orgChart1_layout.xml — see §8 licensing.)
        layoutPart.FeedData(EmbeddedResource("orgChart1_layout.xml"));
        stylePart .FeedData(EmbeddedResource("orgChart1_quickStyle.xml"));
        colorPart .FeedData(EmbeddedResource("orgChart1_colors.xml"));

        // 2. Data model — built from the OrgNode tree.
        dataPart.DataModelRoot = BuildDataModel(root);
        dataPart.DataModelRoot.Save();

        // 3. Slide graphic frame referencing the four parts.
        var graphicFrame = new P.GraphicFrame(
            new P.NonVisualGraphicFrameProperties(
                new P.NonVisualDrawingProperties { Id = 4u, Name = "OrgChart" },
                new P.NonVisualGraphicFrameDrawingProperties(),
                new ApplicationNonVisualDrawingProperties()),
            new P.Transform(
                new A.Offset { X = 457200L, Y = 457200L },
                new A.Extents { Cx = 7000000L, Cy = 4000000L }),
            new A.Graphic(new A.GraphicData(
                new Dgm.RelationshipIds {
                    DataPart    = slidePart.GetIdOfPart(dataPart),
                    LayoutPart  = slidePart.GetIdOfPart(layoutPart),
                    StylePart   = slidePart.GetIdOfPart(stylePart),
                    ColorPart   = slidePart.GetIdOfPart(colorPart),
                }) { Uri = "http://schemas.openxmlformats.org/drawingml/2006/diagram" }));
        slidePart.Slide.CommonSlideData!.ShapeTree!.AppendChild(graphicFrame);
    }

    private static Dgm.DataModelRoot BuildDataModel(OrgNode root) { /* mirror inject.py */ }
}
```

**Notes.**
- The `Dgm.DataModelRoot`, `Dgm.LayoutDefinition`, `Dgm.StyleDefinition`, `Dgm.ColorsDefinition` and `Dgm.RelationshipIds` strongly typed classes are real and shipped in `DocumentFormat.OpenXml` 3.x [Phase 1 ref 24].
- We deliberately do **not** create a `DiagramPersistLayoutPart` (the `drawing1.xml` cache). PowerPoint regenerates it on first open. **[unverified — requires PowerPoint desktop confirmation]**.
- We load the three "ambient" parts (layout, quickStyle, colors) as opaque XML extracted from a seed `.pptx` we built once in PowerPoint. This keeps the C# code small and avoids a 1,000-line hand-written `LayoutDefinition`.

**Pros.** Strongly typed, IDE-friendly, no Python, integrates naturally with .NET document pipelines.
**Cons.** Same legal concern as Approach A about embedding the layout XML. Verbose. The Open XML SDK has *no published worked example* for SmartArt creation [Phase 1 ref 8]; you are first across the line.

### 4.3 Approach C — Aspose.Slides

**Idea.** Use Aspose.Slides' `SmartArt` API directly. No XML, no seed.

```python
import aspose.slides as slides

with slides.Presentation() as pres:
    slide = pres.slides[0]
    sa = slide.shapes.add_smart_art(
        50, 50, 600, 400,
        slides.smartart.SmartArtLayoutType.ORGANIZATION_CHART)
    root = sa.all_nodes[0]
    root.text_frame.text = "CEO"
    cto = root.child_nodes.add_node()
    cto.text_frame.text = "CTO"
    pres.save("scenarioA.pptx", slides.export.SaveFormat.PPTX)
```

API references: [Phase 1 refs 4, 5, 6].

**Editability claim.** Aspose's documentation [4][5] explicitly describes adding/removing nodes and round-tripping SmartArt as SmartArt. **[unverified — requires PowerPoint desktop]** but the vendor's claim is unambiguous and consistent across multiple tutorial pages.

**XML inspection.** A Phase 2 verification *must* unzip the Aspose output and confirm that `ppt/diagrams/data1.xml`, `layout1.xml`, `quickStyle1.xml`, `colors1.xml` exist with the correct content types — and that the slide's graphic frame uses `<dgm:relIds>` and not a flat `<p:grpSp>`. If the four parts are present, Aspose passes.

**Pros.** Trivial API. Layout coverage covers all built-in SmartArt types via the `SmartArtLayoutType` enum. Handles parTrans/sibTrans automatically.
**Cons.** Commercial licence (per-developer + redistribution). Heavy dependency. Locks you into a vendor.

### 4.4 Approach D — LibreOffice headless

**Conclusion: not viable as a generator.** LibreOffice cannot natively *create* SmartArt; its support is import-only and improving (Phase 1 refs 11, 12, 13). It is, however, a useful **verification tool**: convert the generator output to PDF (`soffice --headless --convert-to pdf out.pptx`) and rasterise the result for visual regression in CI. It will *not* tell you whether PowerPoint considers the file editable SmartArt — only PowerPoint can answer that.

### 4.5 Approach E — Microsoft Graph / Office Scripts

**Conclusion: not viable.** Office Scripts target Excel; Graph's PowerPoint surface does not expose a SmartArt creation method at the time of writing. Office.js add-ins can create SmartArt, but only when running *inside* a PowerPoint host, which fails the "from outside PowerPoint" requirement. Re-evaluate annually as Microsoft adds Graph endpoints.

---

## 5. Round-trip verification matrix (expected)

| Approach | Win desktop | Mac desktop | PPT Web | Keynote | Google Slides | LibreOffice |
|---|---|---|---|---|---|---|
| A. Template injection (python-pptx) | Editable SmartArt **[unverified]** | Editable **[unverified]** | Editable **[unverified]** | Flatten | Flatten | Imports as group |
| B. Open XML SDK raw | Editable **[unverified]** | Editable **[unverified]** | Editable **[unverified]** | Flatten | Flatten | Imports as group |
| C. Aspose.Slides | Editable **[unverified, vendor-claimed]** | Editable **[unverified]** | Editable **[unverified]** | Flatten | Flatten | Imports as group |
| D. LibreOffice generator | n/a — cannot create | — | — | — | — | — |
| E. Graph / Office Scripts | n/a — no API | — | — | — | — | — |

The Keynote / Google Slides / LibreOffice columns are unconditional flatten — that is a property of those consumers, not of the generators.

---

## 6. Layout / algorithm mapping for the three scenarios

| Scenario | Layout `uniqueId` | Top-level `layoutNode/alg` | Data model shape |
|---|---|---|---|
| A — Org chart | `urn:microsoft.com/office/officeart/2005/8/layout/orgChart1` | `hierRoot` containing `hierChild` | Tree of `node` points; every non-root needs a `parTrans` + `sibTrans` pair and `parOf` + `presParOf` connections. |
| B — Process | `urn:microsoft.com/office/officeart/2005/8/layout/process1` | `lin` (linear) | Flat list of `node` points; `parTrans`/`sibTrans` still required between consecutive nodes. |
| C — Cycle | `urn:microsoft.com/office/officeart/2005/8/layout/cycle1` | `cycle` | Flat list of `node` points around a single `pres` ring; `cycle` algorithm computes positions. |

The exact `loTypeId` / `loCatId` / `qsTypeId` / `csTypeId` attribute values that PowerPoint writes into the slide-level `<dgm:relIds>` are *not* required (they live inside each layout's own header) — the slide only needs the four `r:dm`/`r:lo`/`r:qs`/`r:cs` relationships. Verify against the COM oracle.

---

## 7. Gotchas runbook

| Symptom | Likely cause | Fix |
|---|---|---|
| "PowerPoint found a problem with content" on open | Missing diagram part, wrong content type, or stale `[Content_Types].xml` | Compare `[Content_Types].xml` against the seed; ensure all four `application/vnd.openxmlformats-officedocument.drawingml.diagram*+xml` overrides are present. |
| Diagram opens but is empty | `forEach` ran over 0 nodes, or all `cxn` `srcOrd`/`destOrd` are stale | Make sure at least one `node` point is connected to the `doc` point with `parOf`. |
| Diagram opens with old text | Stale `drawing1.xml` cache | Delete `ppt/diagrams/drawing1.xml` *and* the relationship to it from `ppt/diagrams/_rels/data1.xml.rels`. |
| Diagram opens but is locked / SmartArt Design tab missing | Slide uses `<p:grpSp>` instead of `<p:graphicFrame>` + `<dgm:relIds>` | The generator emitted a flatten. Switch to one of approaches A/B/C. |
| Org chart renders all nodes at the same level | Missing `parTrans`/`sibTrans` pairs | Emit them for every non-root node. |
| Two diagrams collide on the same slide | `modelId` collision across diagrams | Use fresh GUIDs per diagram. |
| File opens in PowerPoint Web but not desktop | Strict-namespace XML | Re-emit in Transitional namespaces. |

---

## 8. Decision matrix

Scoring 1–5, higher is better. Scores reflect the analyst's expectation; revisit after on-machine testing.

| Criterion (weight) | A. Template injection | B. Open XML SDK | C. Aspose.Slides | D. LibreOffice | E. Graph |
|---|---:|---:|---:|---:|---:|
| Editability of output (×3) | 5 | 5 | 5 | 0 | 0 |
| Layout coverage (×2) | 5 (= PPT) | 4 (cost of new layouts) | 5 | 0 | 0 |
| Language ergonomics (×1) | 5 (Python) | 4 (C#) | 5 | — | — |
| CI friendliness (×2) | 5 | 4 | 4 (large native dep) | 3 | 1 |
| License cost (×2) | 5 (free) | 5 (free) | 1 (per-dev) | 5 | 5 |
| Cross-platform fidelity (×1) | 5 | 5 | 5 | 1 | 1 |
| Long-term maintenance risk (×2) | 4 (seed drift) | 3 (verbose) | 3 (vendor lock) | 2 | 2 |
| **Weighted total** | **63** | **57** | **52** | — | — |

**Recommendation.**
- **Primary: Approach A — template injection with python-pptx + lxml.** Cheapest, smallest code, highest ceiling, zero runtime cost, integrates with any Python-based document pipeline.
- **Fallback: Approach C — Aspose.Slides** — when the team needs a layout we have not built a seed for, when the team is .NET-only and wants a single dependency, or when budget exists and time-to-market matters more than cost.
- **Validation: COM oracle on a Windows build agent** — used in CI to regenerate "golden" diagram XML once per layout and to detect drift.

---

## 9. Reference architecture

```
┌────────────────┐    ┌──────────────────┐    ┌──────────────────────┐
│ org.json /     │ →  │  Schema validator │ →  │  Generator           │
│ process.json / │    │  (jsonschema)     │    │  (Approach A)        │
│ cycle.json     │    └──────────────────┘    │  - selects seed      │
└────────────────┘                            │  - builds dataModel  │
                                              │  - drops drawing1    │
                                              └─────────┬────────────┘
                                                        │
                                                        ▼
                                          ┌──────────────────────────┐
                                          │  Headless verification   │
                                          │  - LibreOffice → PDF     │
                                          │  - xmllint --c14n diff   │
                                          │     vs golden oracle XML │
                                          │  - Open XML SDK validator│
                                          │     (DocumentFormat.OpenXml.Validation)│
                                          └─────────┬────────────────┘
                                                    │ pass/fail
                                                    ▼
                                          ┌──────────────────────────┐
                                          │  Artifact store          │
                                          │  scenarioA.pptx, ...     │
                                          └──────────────────────────┘
```

**CI test plan.**
1. **Schema test.** `jsonschema` validates the input against `schemas/org.schema.json`.
2. **Structural test.** Generator output is unzipped; assert that `ppt/diagrams/{data1,layout1,quickStyle1,colors1}.xml` exist and that the slide contains a `<p:graphicFrame>` whose `<a:graphicData>` has `uri="…/diagram"` and a `<dgm:relIds>` child with all four `r:dm`/`r:lo`/`r:qs`/`r:cs` attributes set.
3. **No-flatten test.** Assert that the slide does **not** contain a `<p:grpSp>` whose contents look like the diagram (defends against accidental fallback to flatten).
4. **Validator test.** Run `DocumentFormat.OpenXml.Validation.OpenXmlValidator` on the file in a small .NET helper; fail on any error.
5. **Render test.** `soffice --headless --convert-to pdf` and rasterise; pixel-diff against a baseline with a generous tolerance.
6. **Oracle drift test (Windows agent only).** Regenerate the oracle for one canonical input, `xmllint --c14n` diff `data1.xml` vs the generator output (modulo `modelId` GUIDs); fail on structural divergence.
7. **Smoke test (manual, gated release).** A human opens each artefact in PowerPoint 365 desktop and confirms the SmartArt Design ribbon is live and the Text Pane is editable. This is the only gate that the automated pipeline cannot replace.

---

## 10. Appendix A — annotated `data1.xml` for Scenario A (3-node example)

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<dgm:dataModel xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram"
               xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
               xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <dgm:ptLst>
    <!-- the mandatory document point -->
    <dgm:pt modelId="{D0…01}" type="doc"><dgm:prSet/><dgm:spPr/></dgm:pt>

    <!-- root: CEO -->
    <dgm:pt modelId="{N0…02}" type="node">
      <dgm:prSet/><dgm:spPr/>
      <dgm:t><a:p><a:r><a:rPr lang="en-US"/><a:t>CEO</a:t></a:r></a:p></dgm:t>
    </dgm:pt>
    <!-- transition pair attached to CEO from doc -->
    <dgm:pt modelId="{P0…03}" type="parTrans"><dgm:prSet/><dgm:spPr/></dgm:pt>
    <dgm:pt modelId="{S0…04}" type="sibTrans"><dgm:prSet/><dgm:spPr/></dgm:pt>

    <!-- child: CTO -->
    <dgm:pt modelId="{N1…05}" type="node">
      <dgm:prSet/><dgm:spPr/>
      <dgm:t><a:p><a:r><a:rPr lang="en-US"/><a:t>CTO</a:t></a:r></a:p></dgm:t>
    </dgm:pt>
    <dgm:pt modelId="{P1…06}" type="parTrans"><dgm:prSet/><dgm:spPr/></dgm:pt>
    <dgm:pt modelId="{S1…07}" type="sibTrans"><dgm:prSet/><dgm:spPr/></dgm:pt>

    <!-- child: CFO -->
    <dgm:pt modelId="{N2…08}" type="node">
      <dgm:prSet/><dgm:spPr/>
      <dgm:t><a:p><a:r><a:rPr lang="en-US"/><a:t>CFO</a:t></a:r></a:p></dgm:t>
    </dgm:pt>
    <dgm:pt modelId="{P2…09}" type="parTrans"><dgm:prSet/><dgm:spPr/></dgm:pt>
    <dgm:pt modelId="{S2…0A}" type="sibTrans"><dgm:prSet/><dgm:spPr/></dgm:pt>
  </dgm:ptLst>
  <dgm:cxnLst>
    <!-- doc → CEO -->
    <dgm:cxn modelId="{C0…0B}" type="parOf"     srcId="{D0…01}" destId="{N0…02}" srcOrd="0" destOrd="0"/>
    <!-- CEO → CTO -->
    <dgm:cxn modelId="{C1…0C}" type="parOf"     srcId="{N0…02}" destId="{N1…05}" srcOrd="0" destOrd="0"/>
    <dgm:cxn modelId="{C2…0D}" type="presParOf" srcId="{N0…02}" destId="{P1…06}" srcOrd="0" destOrd="0"/>
    <dgm:cxn modelId="{C3…0E}" type="presParOf" srcId="{N0…02}" destId="{S1…07}" srcOrd="0" destOrd="0"/>
    <!-- CEO → CFO -->
    <dgm:cxn modelId="{C4…0F}" type="parOf"     srcId="{N0…02}" destId="{N2…08}" srcOrd="1" destOrd="0"/>
    <dgm:cxn modelId="{C5…10}" type="presParOf" srcId="{N0…02}" destId="{P2…09}" srcOrd="1" destOrd="0"/>
    <dgm:cxn modelId="{C6…11}" type="presParOf" srcId="{N0…02}" destId="{S2…0A}" srcOrd="1" destOrd="0"/>
  </dgm:cxnLst>
  <dgm:bg/><dgm:whole/>
</dgm:dataModel>
```

The structural rules to internalise: every non-document point has a `parTrans`/`sibTrans` pair; every non-document point has a `parOf` connection from its parent, and the layout's "presentation tree" gets `presParOf` connections that mirror the data tree.

## Appendix B — version pins and dependencies

```
python==3.12
python-pptx==1.0.2
lxml==5.2.2
jsonschema==4.23.0
DocumentFormat.OpenXml==3.5.1   # only for validator helper
aspose-slides==24.10.0          # only if Approach C is chosen
LibreOffice==24.8 headless      # CI verification only
```

## Appendix C — what to test on a real Windows + PowerPoint machine before shipping

1. Build seed files in PowerPoint 365 by hand for orgChart1, process1, cycle1.
2. Run the COM oracle (`build_oracle.ps1`) for Scenario A, B, C to produce golden artefacts.
3. Run the python-pptx generator for the same three scenarios.
4. Run `tools/diff_pptx.sh` between each generator output and its oracle. Confirm that `data1.xml` differs only in `modelId` GUIDs.
5. Open every generated `.pptx` in PowerPoint 365 desktop. Confirm: the SmartArt Design ribbon is active, the Text Pane shows the right tree, "Add Shape" works, "Promote/Demote" works.
6. Re-open the saved-by-PowerPoint version of each file (let PowerPoint regenerate `drawing1.xml`) and re-diff. Confirm that the data model is unchanged.
7. Repeat steps 5–6 in PowerPoint for Mac and PowerPoint for the Web.
8. Convert each file with LibreOffice headless to PDF and check it visually.
9. Promote the "golden" XML produced by step 6 into the CI baseline.

---

## Final word

The honest two-line summary for the engineer who inherits this:

> Generating editable SmartArt from outside PowerPoint is *only* hard because of the cached `drawing1.xml` and the `dgm:layoutDef` mini-language. If you let PowerPoint own the layout (by shipping seed files) and you let PowerPoint own the cache (by deleting `drawing1.xml` after every mutation), the data model is the only XML you have to write — and that is a tractable amount of code.

Everything else in this report is in service of those two sentences.
