# SmartArt in PPTX: Landscape & Specification Briefing
*Phase 1 of 2 — research executed 2026-04-07*

> Methodology note: this briefing was assembled from public specifications, vendor documentation, library issue trackers, and community write-ups. Every non-trivial claim is footnoted. Where the public documentation is silent or contradictory, the text says so explicitly. Nothing in this report was hand-verified against a live PowerPoint installation — that is the job of Phase 2.

---

## 1. Executive summary

A "SmartArt graphic" is not a single shape. Inside a `.pptx` (an Open Packaging Convention zip), it is a **DrawingML Diagram**: a graphic frame on a slide that points, via a `<dgm:relIds>` element, at **four sibling XML parts** stored in the `/ppt/diagrams/` folder of the package — a *data model*, a *layout definition*, a *quick style*, and a *colour transform*. Modern PowerPoint also writes a **fifth, cached "drawing" part** (`drawing#.xml`) that contains the pre-rendered shapes so that consumers which cannot run the layout algorithms (older PowerPoint, Mac, mobile, web, third-party viewers) still see something sensible. The drawing part is *not* the SmartArt — it is a fallback render of it. Editability lives entirely in the data + layout pair [1][2][3].

This four-part split is the source of every difficulty in generating SmartArt from outside PowerPoint. To produce a file that PowerPoint opens as *editable* SmartArt (the "SmartArt Design" ribbon tab appears, the Text Pane works, nodes can be added) the generator must emit a coherent dataModel, reference a layout PowerPoint understands (either built-in by URI or embedded in full), and either omit the cached drawing or keep it consistent with the data. Generators that only emit a flat group of shapes produce something that *looks* like SmartArt but is locked — the failure mode most third-party tools exhibit.

The viable paths, in rough descending order of practicality, are:

1. **Template injection** — ship a seed `.pptx` containing an empty SmartArt of the desired layout, then mutate `data1.xml` (and optionally invalidate `drawing1.xml`) with python-pptx + lxml, Open XML SDK, docx4j, or any package-level OOXML toolkit.
2. **Commercial library with first-class SmartArt API** — Aspose.Slides is currently the only widely-cited commercial library that exposes a `SmartArt`/`SmartArtNode` object model and claims to emit real diagram parts [4][5][6]. Spire.Presentation also offers an `AppendSmartArt` API [7].
3. **Raw OOXML authoring** with the Open XML SDK's `DocumentFormat.OpenXml.Drawing.Diagrams` namespace — possible but very poorly documented; the official `dotnet/Open-XML-SDK` discussion thread on the topic (#1535) explicitly notes the absence of a worked example [8].
4. **Reference-oracle automation**: drive a hidden PowerPoint via COM (`Shapes.AddSmartArt Application.SmartArtLayouts("urn:…/orgChart1")`) [9][10]. Reliable but requires Windows + a licensed PowerPoint, so it is a baseline rather than a production option for most teams.
5. **Headless office suites** — LibreOffice/Impress import is improving but historically depends on the cached fallback render and cannot create SmartArt from scratch [11][12][13].
6. **Approaches that do *not* work** for editable SmartArt: python-pptx [14], PptxGenJS [15], officegen, and most "PPTX from JSON" libraries — these can only emit flat shape groups.

The recommended primary approach for most teams is **template injection** (path 1) using a small set of curated seed files plus python-pptx or Open XML SDK; the recommended fallback when layout coverage matters more than cost is **Aspose.Slides** (path 2). The COM oracle (path 4) is the validation tool, not the production tool.

---

## 2. SmartArt in ECMA-376 / ISO/IEC 29500

### 2.1 Where it lives in the spec
SmartArt is specified in **ECMA-376 Part 1, §21.4 — "DrawingML — Diagrams"**, with the schemas in the diagram namespace `http://schemas.openxmlformats.org/drawingml/2006/diagram` (conventionally prefixed `dgm:`) and a sibling drawing-shape namespace `http://schemas.microsoft.com/office/drawing/2008/diagram` (`dsp:`) for the cached render [1][16]. The standard parallel reference for implementers is the OfficeOpenXML.com walkthrough [2] and the Liquid Technologies schema browser [16].

### 2.2 The four (really five) parts
A single SmartArt graphic contributes the following parts to the package, all under `/ppt/diagrams/`:

| Part | Content type | Root element | Purpose |
|---|---|---|---|
| `data1.xml` | `application/vnd.openxmlformats-officedocument.drawingml.diagramData+xml` | `<dgm:dataModel>` | Authoritative content: the list of points (`ptLst`) and connections (`cxnLst`). |
| `layout1.xml` | `…drawingml.diagramLayout+xml` | `<dgm:layoutDef>` | The algorithm graph that turns the data model into shapes. |
| `quickStyle1.xml` | `…drawingml.diagramStyle+xml` | `<dgm:styleDef>` | Quick-style (effects, fills) transform. |
| `colors1.xml` | `…drawingml.diagramColors+xml` | `<dgm:colorsDef>` | Colour transform. |
| `drawing1.xml` | `…drawingml.diagramDrawing+xml` | `<dsp:drawing>` | **Cached** render in `dsp:` shapes — present from PowerPoint 2010 onwards [11]. |

The slide references the diagram via a graphic frame:

```xml
<p:graphicFrame>
  <p:nvGraphicFramePr>…</p:nvGraphicFramePr>
  <p:xfrm>…</p:xfrm>
  <a:graphic>
    <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/diagram">
      <dgm:relIds xmlns:dgm="…/diagram"
                  xmlns:r="…/officeDocument/2006/relationships"
                  r:dm="rId2"   <!-- data    -->
                  r:lo="rId3"   <!-- layout  -->
                  r:qs="rId4"   <!-- quickStyle -->
                  r:cs="rId5"/> <!-- colors  -->
    </a:graphicData>
  </a:graphic>
</p:graphicFrame>
```

The slide's `.rels` file binds those four ids to the four diagram parts, and `data1.xml`'s own `.rels` adds a fifth relationship to `drawing1.xml` (relationship type `…/diagramDrawing`) [2][3][17].

### 2.3 The data model in detail
`<dgm:dataModel>` contains:

- `<dgm:ptLst>` — an ordered list of `<dgm:pt>` points. Each `pt` has a `modelId` (a GUID-like string), a `type` attribute drawn from {`doc`, `node`, `asst` (assistant in hierarchies), `parTrans`, `sibTrans`, `pres`}, and a `<dgm:t>` text body containing one or more `<a:p>` paragraphs. `parTrans`/`sibTrans` points represent parent and sibling *transitions* (the lines/arrows between nodes); they always come in pairs and the layout algorithm assumes their presence for non-leaf nodes [2][16].
- `<dgm:cxnLst>` — an ordered list of `<dgm:cxn>` connections. Each `cxn` has a `modelId`, a `type` (`parOf`, `presOf`, `presParOf`, `unknownRelationship`), `srcId`/`destId` referring to point `modelId`s, and `srcOrd`/`destOrd` ordinals.
- `<dgm:bg>` and `<dgm:whole>` — optional background fill and overall formatting.
- `<dgm:extLst>` — extension list. Modern PowerPoint stores a `<dsp:dataModelExt>` here that points back to `drawing1.xml` and carries the `relId` and a `minVer` attribute; this is the hook PowerPoint uses to decide whether the cached drawing is current [2][16].

### 2.4 The layout definition
`<dgm:layoutDef>` is, in effect, a small declarative program. It contains:

- A header (`title`, `desc`, `catLst`) — the human-readable category and description shown in the SmartArt picker.
- `<dgm:sampData>` and `<dgm:styleData>` — sample data used by the picker preview.
- `<dgm:layoutNode>` — a recursive tree of layout nodes, each with a `name`, an optional `styleLbl` (which colour transform slot to use), and children: `<dgm:alg>` (algorithm — `hierChild`, `hierRoot`, `tree`, `cycle`, `lin`, `snake`, `composite`, `pyra`, `sp`), `<dgm:shape>` (the shape to draw), `<dgm:presOf>` (which data points this node presents), `<dgm:constrLst>` (numeric constraints), `<dgm:ruleLst>` (font/size rules), `<dgm:varLst>` (variables), `<dgm:choose>`/`<dgm:if>`/`<dgm:else>` (conditional layout), and `<dgm:forEach>` (iteration over data points) [1 §21.4.2; 16].

It is this mini-language, not the data model, that defines whether you have an org chart or a radial cycle. **Layouts are typically authoritative — PowerPoint runs the algorithm at render time, populating the cached drawing from data + layout.**

### 2.5 Quick styles and colours
`<dgm:styleDef>` and `<dgm:colorsDef>` are similar declarative transforms keyed by `styleLbl`. They are documented in ECMA-376 §21.4.3 and §21.4.4 and indexed at OOXML.info §14.2.6 [18]. Both can be referenced by `uniqueId` (a URI in the same `urn:microsoft.com/office/officeart/2005/8/…` family).

### 2.6 The cached drawing and the `modified` flag
`drawing1.xml` is a `<dsp:drawing>` that contains `<dsp:spTree>` with concrete `<dsp:sp>` shapes — positions, sizes, geometry, fills. PowerPoint 2007 did *not* write this part; PowerPoint 2010+ writes it on first save and updates it when the diagram is edited. Crucially, **if the data model changes but the cached drawing is not invalidated, PowerPoint 2010+ may render the stale cached drawing instead of recomputing from the layout** — this is the single biggest gotcha for generators that mutate `data1.xml` in place [11][12]. The `<dsp:dataModelExt>` extension carries a `modified` flag PowerPoint uses to decide; in practice, simply deleting `drawing1.xml` (and its relationship) forces PowerPoint to regenerate from the layout on next open. LibreOffice's SmartArt import has the opposite bias: it relies heavily on the cached drawing because its native layout-engine support for `dgm:layoutDef` is incomplete [11][12][13].

---

## 3. Built-in layouts and `.glox` files

PowerPoint ships its built-in layouts as **`.glox` files** — themselves zip packages containing a `diagrams/layout1.xml`, `colors1.xml`, `quickStyle1.xml` and the surrounding rels [19][20][21]. They live under `%ProgramFiles%\Microsoft Office\rootX\Office16\SmartArt Graphics\` for the shipped set and `%APPDATA%\Microsoft\Templates\SmartArt Graphics\` for user-installed ones [21][22].

Layouts are identified by a **layout URI** in the `urn:microsoft.com/office/officeart/2005/8/layout/<name>` namespace (and a newer `2008/layout/<name>` namespace for layouts added later), e.g.:

- `urn:microsoft.com/office/officeart/2005/8/layout/orgChart1` — Hierarchy → Organization Chart
- `urn:microsoft.com/office/officeart/2005/8/layout/hierarchy1` — Hierarchy → Hierarchy
- `urn:microsoft.com/office/officeart/2005/8/layout/cycle1` — Cycle → Basic Cycle
- `urn:microsoft.com/office/officeart/2005/8/layout/process1` — Process → Basic Process
- `urn:microsoft.com/office/officeart/2008/layout/NameandTitleOrganizationalChart`
- `urn:microsoft.com/office/officeart/2005/8/layout/pictureOrgChart+Icon` [9][23]

**Important practical fact: a `uniqueId` URI alone is not enough to make PowerPoint render the diagram.** The layout XML must be present in the package (or the consumer must have a built-in layout with the same `uniqueId` and the consumer must be willing to substitute it). In practice, PowerPoint matches by `uniqueId` *and* embeds the layout in the saved file — so generators should always embed a complete `layout1.xml`. The simplest source of that XML is to copy it out of an existing `.pptx` (or out of a `.glox`) at build time. Whether that copying is permitted by Microsoft's licensing is a separate question — see §8.

The eight categories visible in the SmartArt picker are **List, Process, Cycle, Hierarchy, Relationship, Matrix, Pyramid, Picture**, plus the "Office.com" online category. The category is purely metadata in `layoutDef/catLst` and does not affect rendering [21].

---

## 4. Library and tooling survey

Editability key:
**Create-Editable** = library can produce a new SmartArt graphic that PowerPoint opens with a working SmartArt Design ribbon and Text Pane.
**Round-trip** = library preserves SmartArt on read+write but cannot create one.
**Read-only** = library exposes the data model for inspection.
**Flatten** = library only emits a grouped set of static shapes that look like SmartArt.
**None** = no SmartArt support at all.

| Library / tool | Language | Status | Notes |
|---|---|---|---|
| python-pptx | Python | None / partial read | Issue #83 (open since 2014) is the canonical "no SmartArt" tracker [14]. `GraphicFrame` exposes `has_smart_art` but no creation API. Users hand-edit XML via `shape.part.related_parts`. |
| python-pptx-ng | Python | None | Fork; same limitation. |
| Open XML SDK 3.x (`DocumentFormat.OpenXml.Drawing.Diagrams`) | .NET / C# | Create-Editable (in principle) | Full strongly-typed classes for `DataModelRoot`, `LayoutDefinition`, `StyleDefinition`, `ColorsDefinition` exist [24]. No worked sample in MS docs; community discussion #1535 confirms the gap [8]. |
| Apache POI (XSLF) | Java | Round-trip (limited) | Can read but not create the diagram parts; users typically do template injection. |
| docx4j / pptx4j | Java | Round-trip + low-level create | Provides marshalled JAXB classes for the diagram namespace; community thread shows people building dataModel by hand [25]. |
| **Aspose.Slides** | .NET / Java / Python / C++ / Node | **Create-Editable** | First-class `SmartArt` and `ISmartArtNode` API; `slide.shapes.add_smart_art(x, y, w, h, SmartArtLayoutType.OrganizationChart)` and `node.add_node()` [4][5][6]. Commercial; per-developer licensing. |
| Spire.Presentation (E-iceblue) | .NET / Java / Python | Create-Editable | `ISlide.Shapes.AppendSmartArt` API [7]. Commercial. |
| Syncfusion Presentation | .NET | Round-trip; limited create | Supports preserving SmartArt; create API more limited than Aspose. Commercial. |
| GemBox.Presentation | .NET | Round-trip | No documented create-from-scratch SmartArt API. Commercial. |
| Telerik Document Processing | .NET | Round-trip | Similar story. |
| ONLYOFFICE Document Builder | Server-side JS | None / Flatten | No SmartArt API. |
| LibreOffice / Impress headless | C++ | Round-trip (improving), no create | Import has been the focus of work since 6.3; still depends on cached drawing for many layouts [11][12][13]. Cannot create SmartArt natively. |
| PptxGenJS | Node / browser | None | Maintainer has explicitly stated SmartArt is not on the roadmap [15]. |
| officegen | Node | None | Same. |
| docxtemplater pptx module | Node | None / template-based | Can substitute text inside an existing SmartArt by treating its `<a:t>` runs as template variables. |
| Microsoft Graph + Office Scripts | Cloud | Unverified for SmartArt | Office Scripts target Excel; PowerPoint scripting via Graph is limited. No documented `addSmartArt` equivalent at time of writing. |
| Office.js add-ins | JS in PowerPoint | Create-Editable (inside PowerPoint) | Only works *inside* a running PowerPoint host — fails the "from outside" test. |
| Power Automate | Cloud | None | No SmartArt action. |
| COM automation (`pywin32`, PowerShell, VBScript) | Any → Windows PowerPoint | **Create-Editable (oracle)** | `Shapes.AddSmartArt Application.SmartArtLayouts("urn:…/orgChart1")` [9][10]. Requires installed PowerPoint. |
| AppleScript on macOS PowerPoint | macOS | Partial | The PowerPoint Mac scripting dictionary exposes Shapes but SmartArt creation is unreliable historically. |

The headline is stark: **for "outside PowerPoint, no commercial license, full editability" the only path is template injection or hand-authoring the diagram parts.** Everything else either flattens, costs money, or requires a running PowerPoint.

---

## 5. The reference oracle: COM / VBA

The canonical pattern is:

```vba
Dim sld As Slide
Set sld = ActivePresentation.Slides(1)
Dim shp As Shape
Set shp = sld.Shapes.AddSmartArt( _
    Application.SmartArtLayouts("urn:microsoft.com/office/officeart/2005/8/layout/orgChart1"), _
    Left:=50, Top:=50, Width:=600, Height:=400)

' Populate nodes
Dim root As SmartArtNode
Set root = shp.SmartArt.AllNodes(1)
root.TextFrame2.TextRange.Text = "CEO"
root.AddNode(msoSmartArtNodeBelow).TextFrame2.TextRange.Text = "CTO"
```

`Shapes.AddSmartArt(Layout, Left, Top, Width, Height)` is documented at Microsoft Learn [10]. The `Application.SmartArtLayouts` collection [26] can be indexed by integer or by layout URI; the URI is the same string PowerPoint writes into the layout's `uniqueId` attribute. Output is then a `Shape.SmartArt` whose `AllNodes` collection mirrors the `dgm:ptLst` and supports `Add`, `Promote`, `Demote`, `MoveUp`, `MoveDown`, etc.

Saving the file produces a `.pptx` whose `diagrams/` folder contains exactly the four parts described in §2 plus the cached `drawing1.xml`. **This output is the ground truth for Phase 2 XML diffing.**

The same automation is reachable from Python:

```python
import win32com.client as win32
ppt = win32.gencache.EnsureDispatch("PowerPoint.Application")
pres = ppt.Presentations.Add()
slide = pres.Slides.Add(1, 12)  # 12 = ppLayoutBlank
layout = ppt.SmartArtLayouts("urn:microsoft.com/office/officeart/2005/8/layout/orgChart1")
shp = slide.Shapes.AddSmartArt(layout, 50, 50, 600, 400)
```

and from PowerShell with `New-Object -ComObject PowerPoint.Application`.

---

## 6. Cross-platform fidelity

| Consumer | SmartArt fidelity on open | On save |
|---|---|---|
| PowerPoint for Windows (365) | Full — runs the layout algorithm, regenerates cached drawing as needed. | Writes all five parts including up-to-date cached drawing. |
| PowerPoint for Mac (365) | Full — same code paths as Windows for several years. | Same. |
| PowerPoint for the Web | Mostly full; some less common layouts fall back to the cached drawing. | Writes all five parts. |
| PowerPoint Mobile (iOS/Android) | Mostly full; relies more heavily on cached drawing than desktop. | Same. |
| Keynote (macOS/iOS) | Imports as a flat group of shapes. SmartArt-ness is lost on save back to `.pptx`. |
| Google Slides | Imports as a flat group of shapes. Conversion is one-way. |
| LibreOffice Impress | Imports — uses cached drawing where present, runs partial layout engine where not. Has been improving since 6.3 [11][12]. Saving back to `.pptx` may *lose* the dgm:layoutDef and emit only flattened shapes for layouts the engine doesn't fully support. |
| Apache POI viewers | Read-only structure access; no rendering. |

The practical implication: **a generator must produce content that PowerPoint Windows accepts**, because every other consumer either reads what PowerPoint writes or flattens. There is no need to optimise for Keynote or Google Slides — they will flatten regardless.

---

## 7. Known failure modes

The following are the recurring causes of "PowerPoint found a problem with content" or "SmartArt opened as a locked group" reported in community channels and the docx4j / Open-XML-SDK trackers:

1. **Stale cached drawing.** Mutating `data1.xml` without invalidating `drawing1.xml` → PowerPoint shows the old shapes. Fix: delete `drawing1.xml` and the relationship to it; PowerPoint regenerates on open.
2. **Missing parts.** Forgetting `quickStyle1.xml` or `colors1.xml` → content-repair dialog. All four parts are mandatory even if the colours/styles are defaults.
3. **Mismatched relationship targets.** `dgm:relIds/@r:dm` pointing at the wrong part type → silent failure or repair dialog.
4. **Unbalanced parTrans/sibTrans pairs.** Algorithms like `hierChild` and `lin` assume each non-root node has both a `parTrans` and a `sibTrans` connection. Hand-built data models that omit one cause the layout engine to crash silently and PowerPoint to render an empty canvas.
5. **Wrong `presOf` mapping.** `layoutNode/presOf` axes like `desOrSelf::node` must match what `forEach` actually iterates; mismatches cause "no shapes" output.
6. **`modelId` collisions.** Two points sharing a `modelId` → undefined behaviour.
7. **Wrong content types.** Forgetting to register the four diagram content types in `[Content_Types].xml` → repair dialog before parsing even begins.
8. **Mixing Strict and Transitional namespaces.** ECMA-376 has Strict and Transitional namespaces; Strict is rejected by older PowerPoint. Always emit Transitional.
9. **Cached drawing references shapes not in the data.** When using a seed file you must keep the dataModel and the cached drawing's `dsp:sp` ids in sync, or simply delete the cached drawing.
10. **`forEach` over an empty collection.** Some layouts fail to render at all if `ptLst` has only the root `doc` node and no `node` children — always seed with at least one real node.

---

## 8. Licensing

The OOXML file format specification itself is freely implementable under ECMA-376 / ISO/IEC 29500 and Microsoft's Open Specification Promise. The schemas, namespace URIs, and the structural pattern of the diagram parts are therefore fair game for any generator.

Less clear is the redistribution of **the content of Microsoft's built-in `.glox` layout files** — the actual XML inside `Office16\SmartArt Graphics\*.glox`. Those files are part of the licensed Office installation; copying them into a third-party generator's source tree is plausibly an Office EULA issue, not an OOXML issue. The safest pattern in production is:

- At install/build time on a developer machine that has a licensed Office, *copy* the layout XML out of the user's `.pptx` seed files (not directly out of `.glox`) into your generator's runtime resources, and treat the layout as opaque data.
- Or, ship only a small set of *custom* layouts you authored yourself (the `dgm:layoutDef` mini-language is fully documented in ECMA-376; you can write your own org-chart layout from scratch).
- Or, accept the dependency on a licensed Office and use COM automation.

Flag this for legal review before shipping. This briefing cannot give legal advice.

---

## 9. Open questions for Phase 2

1. Produce a minimum-viable hand-authored `data1.xml` + `layout1.xml` + `quickStyle1.xml` + `colors1.xml` + `[Content_Types].xml` patch + slide rels that PowerPoint 365 opens as editable Hierarchy SmartArt. What is the smallest passing set?
2. What does the COM oracle write into `drawing1.xml` for a 25-node org chart, and can the generator omit that part entirely without triggering a repair dialog?
3. Does Aspose.Slides actually emit the `dgm:` parts, or does it emit a `dsp:` flatten dressed up as SmartArt? Confirm by unzipping its output.
4. Can the same template-injection generator handle Hierarchy, Process and Cycle, or do `parTrans`/`sibTrans` requirements force per-layout code?
5. What is the LibreOffice headless round-trip behaviour for each of the three reference scenarios?
6. What is the maximum-fidelity verification step for CI: `xmllint --c14n` diff against the COM oracle, or a render+screenshot diff via LibreOffice?

---

## 10. Bibliography

1. ECMA International — *Office Open XML File Formats — ECMA-376*, Part 1, §21.4 *DrawingML — Diagrams*. https://ecma-international.org/publications-and-standards/standards/ecma-376/
2. OfficeOpenXML.com — *DrawingML Overview / Diagrams*. http://officeopenxml.com/drwOverview.php
3. Apache OpenOffice Wiki — *DrawingML*. https://wiki.openoffice.org/wiki/DrawingML
4. Aspose — *Manage SmartArt Graphics in Presentations Using Python*. https://docs.aspose.com/slides/python-net/manage-smartart-shape/
5. Aspose Tutorials — *Master SmartArt in PowerPoint Using Aspose.Slides for Python*. https://tutorials.aspose.com/slides/python-net/smart-art-diagrams/aspose-slides-python-smartart-presentation-guide/
6. Aspose — *Manage SmartArt Shape Nodes in Presentations in .NET*. https://docs.aspose.com/slides/net/manage-smartart-shape-node/
7. e-iceblue — *Python: Create, Read or Delete SmartArt in PowerPoint*. https://www.e-iceblue.com/Tutorials/Python/Spire.Presentation-for-Python/Program-Guide/SmartArt/Python-Create-Read-or-Delete-SmartArt-in-PowerPoint.html
8. dotnet/Open-XML-SDK Discussion #1535 — *How to create a SmartArt organization chart into PowerPoint programmatically?*. https://github.com/dotnet/Open-XML-SDK/discussions/1535
9. SK Hub / OfficeTips — *Insert custom SmartArt programmatically*. http://skp.mvps.org/2013/insert-custom-smartart.htm
10. Microsoft Learn — *Shapes.AddSmartArt method (PowerPoint VBA)*. https://learn.microsoft.com/en-us/office/vba/api/powerpoint.shapes.addsmartart
11. Miklós Vajna — *SmartArt improvements in LibreOffice*. https://vmiklos.hu/blog/smartart-improvements.html
12. The Document Foundation — *Improvements in LibreOffice's PowerPoint presentation support*. https://blog.documentfoundation.org/blog/2021/05/08/improvements-in-libreoffices-powerpoint-presentation-support-3/
13. Hossein Nourikhah — *SmartArt Support for LibreOffice* (FOSDEM 2023). https://archive.fosdem.org/2023/schedule/event/lotech_smartart/
14. scanny/python-pptx Issue #83 — *feature set: SmartArt support*. https://github.com/scanny/python-pptx/issues/83
15. PptxGenJS — *Introduction / Roadmap*. https://gitbrent.github.io/PptxGenJS/docs/introduction/
16. Liquid Technologies — *Schema docs for `dgm` namespace*. https://schemas.liquid-technologies.com/officeopenxml/2006/dgm.html
17. Microsoft Learn — *Structure of a PresentationML document*. https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document
18. OOXML.info — *14.2.6 Diagram Style Part*. https://ooxml.info/docs/14/14.2/14.2.6/
19. FileInfo — *GLOX File*. https://fileinfo.com/extension/glox
20. FilExt — *GLOX File Extension*. https://filext.com/file-extension/GLOX
21. Indezine — *Get More SmartArt Graphics*. https://www.indezine.com/products/powerpoint/learn/chartsdiagrams/get-more-smartart-graphics.html
22. Microsoft Q&A — *Is importing .glox for custom SmartArt still possible?*. https://learn.microsoft.com/en-us/answers/questions/5115584/is-importing-glox-for-custom-smartart-still-possib
23. Microsoft Learn (archive) — *Create Custom SmartArt Graphics For Use In The 2007 Office System*. https://learn.microsoft.com/en-us/archive/msdn-magazine/2007/february/create-custom-smartart-graphics-for-use-in-the-2007-office-system
24. Microsoft Learn — *DocumentFormat.OpenXml.Drawing.Diagrams Namespace*. https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.drawing.diagrams
25. docx4java forum — *OpenXML Diagram (SmartArt) related Parts*. https://www.docx4java.org/forums/docx-java-f6/diagram-smartart-related-parts-t307.html
26. MicrosoftDocs/VBA-Docs — *Office.SmartArtLayouts*. https://github.com/MicrosoftDocs/VBA-Docs/blob/main/api/Office.SmartArtLayouts.md
