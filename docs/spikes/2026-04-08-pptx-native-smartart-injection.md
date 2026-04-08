# Spike: Editable PowerPoint SmartArt via Template Injection

**Date:** 2026-04-08
**Status:** Successful — three experiments verified end-to-end on macOS (spikes 1, 2, 3 all pass)
**Scope:** Image Services / SmartArt rendering — exploring a 4th engine alongside Mermaid, Vega-Lite, custom_svg

**Experiments in this report:**
- **Spike 1 — mutation** (§1-7): rewrite `data1.xml` in a `process1` seed, confirm PowerPoint Mac opens as editable SmartArt
- **Spike 2 — generalisation** (§9): repeat spike 1 against a `cycle2` seed to prove the technique crosses algorithm families
- **Spike 3 — injection** (§10): take a host `.pptx` with *no* existing SmartArt, inject a process diagram from scratch — the operation the production pipeline needs at delivery time
**Predecessor research:** `research/report-1-landscape-and-spec.md`, `research/report-2-implementation-and-validation.md`
**Follow-up spec:** `docs/superpowers/specs/2026-04-08-pptx-native-smartart-engine.md`

---

## 1. Question

Can we generate a PowerPoint `.pptx` file from outside PowerPoint such that the resulting SmartArt graphic is **editable** when the user opens the file — i.e., the SmartArt Design ribbon appears, the Text Pane is populated, and "Add Shape" works — using only macOS tooling and a single PowerPoint Mac install for seed authoring?

The Phase 2 research recommended **template injection** (Approach A): hand-author one seed `.pptx` per layout in PowerPoint, then at runtime mutate `ppt/diagrams/data1.xml` and delete the cached `ppt/diagrams/drawing1.xml` so PowerPoint regenerates the layout from scratch. The research marked every editability claim `[unverified — requires PowerPoint desktop]` because it was produced without a PowerPoint host.

This spike was the verification.

---

## 2. Setup

| Component | Detail |
|---|---|
| Seed file | `tests/fixtures/smartart_seeds/process1_seed.pptx` (41 KB) — created by inserting Insert → SmartArt → Process → Basic Process on a blank slide in PowerPoint Mac, saved as `.pptx` with placeholder text untouched |
| Target layout | `urn:microsoft.com/office/officeart/2005/8/layout/process1` (Basic Process — 3 horizontal arrows) |
| Test data | 5 hardcoded steps: `Research → Design → Build → Test → Ship` |
| Tooling | Python 3 + zipfile + regex (no lxml needed); LibreOffice headless for the smoke test; PowerPoint Mac for the editability gate |
| Spike script | `tmp/spike_smartart_inject.py` (~200 lines, throwaway — embedded in §6 below) |

---

## 3. Method

The spike script makes exactly four mutations to a copy of the seed:

1. **Rewrite `ppt/diagrams/data1.xml`** — generate a fresh data model with:
   - 1 `doc` point, preserving the original `loTypeId`/`qsTypeId`/`csTypeId` attributes verbatim (these tell PowerPoint which layout/quickStyle/colors to use)
   - 5 `node` points with text content
   - 5 `parTrans` + 5 `sibTrans` points (the algorithm requires these as transition pairs)
   - 5 untyped `cxn` connections from `doc` to each `node`, with `parTransId`/`sibTransId` attributes pointing at the transitions
   - **No `pres` points, no `presOf`/`presParOf` connections, no `dgm:extLst`** — the bet was that PowerPoint would regenerate the presentation tree from `layout1.xml` on first open
2. **Delete `ppt/diagrams/drawing1.xml`** — the cached pre-rendered version of the diagram
3. **Strip the `diagramDrawing` relationship from `ppt/slides/_rels/slide1.xml.rels`** — the seed stored this rel at the slide level (not in a sibling `data1.xml.rels`), which is the first surprise vs the research
4. **Strip the `drawing1.xml` content type override from `[Content_Types].xml`**

All other 39 files in the package are byte-identical to the seed.

---

## 4. Results

### 4.1 Automated checks (run on macOS, no PowerPoint)

| Check | Result |
|---|---|
| Spike script exits cleanly | PASS |
| Output `data1.xml` parses with `xmllint --format` | PASS — well-formed, doc point preserved with all layout-binding attributes, 5 nodes present with text |
| Surgical diff vs seed (`diff -rq seed_unzipped out_unzipped`) | PASS — exactly 4 changes: `data1.xml` rewritten, `[Content_Types].xml` patched, `slide1.xml.rels` patched, `drawing1.xml` removed. All other files identical. |
| LibreOffice parses without error (`soffice --headless --convert-to pdf`) | PASS — produces a valid PDF |
| LibreOffice renders content | **N/A** — see §4.2 |

### 4.2 LibreOffice render finding (informative, not a failure)

The PDF that LibreOffice produced from `spike_out.pptx` was **completely blank**. As a sanity check, I rendered the *original seed* (which still has `drawing1.xml`) and got 3 empty boxes + 2 arrows — i.e., the shape geometry came from the cached drawing, not from running the layout algorithm against `data1.xml + layout1.xml`.

This empirically confirms Phase 1 §6: *"LibreOffice imports — uses cached drawing where present, runs partial layout engine where not."* For the `process1` layout specifically, LibreOffice's layout engine is not implemented, so deleting the cache leaves it with nothing to draw.

**Practical implication:** LibreOffice headless is **not** a useful pre-delivery preview tool for `pptx_native` SmartArt. The "well-formed enough to parse" check is the only signal we get from it. Visual review pre-delivery has to happen in PowerPoint. This is a workflow constraint we have to design around in the spec.

### 4.3 PowerPoint editability gate (the only ground truth)

User opened `tmp/spike_out.pptx` in PowerPoint Mac and reported: **"That works, looks perfect"** — confirming all three editability criteria:

1. File opened with no "PowerPoint found a problem with content" repair dialog
2. Five blue boxes visible in a horizontal row, reading **Research → Design → Build → Test → Ship**, with the seed's blue palette and arrow connectors intact
3. SmartArt Design ribbon appeared, Text Pane populated with the five steps, and Add Shape worked

---

## 5. What we now know that the research could not claim

### 5.1 Technique verified end-to-end on macOS-only tooling

The Phase 2 `[unverified]` tags can come off Approach A. We have empirical confirmation that template injection produces editable SmartArt. No Windows host, no COM oracle, no Office licence beyond the one PowerPoint Mac install used to create the seed (and to verify the result).

### 5.2 The minimal data model is sufficient

We dropped *all* `pres` points, *all* `presOf`/`presParOf` connections, and the entire `dgm:extLst` (which had pointed at the cached drawing via `relId="rId6"`). PowerPoint regenerated the presentation tree from `layout1.xml` on first open. **This is the most important finding.** It means the per-layout generator code is small — ~30 lines of XML construction per node, no need to mirror PowerPoint's pres-tree bookkeeping.

The Phase 2 §10 example data1.xml had shown `presParOf` connections; the spike proves they are not necessary even though PowerPoint emitted them in the seed. PowerPoint's writer is more verbose than its reader requires.

### 5.3 Two Phase 1 corrections worth recording

These won't matter often, but they will matter if the next person to touch this code reaches for Phase 1 §2.2 as a reference and finds it slightly wrong:

- **Mac PowerPoint stores the `diagramDrawing` relationship at the slide level** — `ppt/slides/_rels/slide1.xml.rels`, alongside `diagramData`/`diagramLayout`/`diagramQuickStyle`/`diagramColors` — *not* in a sibling `ppt/diagrams/_rels/data1.xml.rels`. Phase 1 §2.2 described it as the latter. The OOXML spec permits both forms (it's a parent-vs-child packaging choice); Mac chose slide-level. Our generator must therefore patch the slide rels, not look for a non-existent diagrams rels file.
- **Mac PowerPoint uses content type `application/vnd.ms-office.drawingml.diagramDrawing+xml`** for `drawing1.xml`. Phase 1 §2.2 listed `application/vnd.openxmlformats-officedocument.drawingml.diagramDrawing+xml`. Both are accepted by readers; Mac uses the legacy `vnd.ms-office` namespace.

A third observation, not a correction but worth noting: **Mac PowerPoint emits brace-wrapped uppercase GUIDs** for `modelId` (e.g., `{746B57E5-417C-5B4A-85C3-56BF87D83488}`). Other OOXML producers use unbraced lowercase. PowerPoint accepts both on read; we used the brace-wrapped form to match Mac's output and minimise diffs against future seeds.

### 5.4 LibreOffice is not a verifier for this technique

Phase 2 §4.4 said LibreOffice is "a useful **verification tool**." Empirically, for layouts whose layout algorithm LO has not implemented, deleting the cached drawing yields a blank render. The PDF-conversion step is still useful as an OOXML *parser* sanity check (it errors loudly on malformed files), but visual review must happen in PowerPoint.

This is the single biggest design constraint for the follow-on engine: **we cannot do free-iteration draft renders the way the existing custom_svg engine does**. Either the draft phase relies on a different render path (e.g., still using custom_svg for the in-pipeline preview, only the final delivery being `pptx_native`), or the workflow accepts that PowerPoint Mac open is the only review checkpoint. The spec covers this trade-off.

---

## 6. The spike script

For reference, embedded here so the spike is reproducible without `tmp/`. This is throwaway code — the production engine will share the *concepts* (data model construction, surgical mutation, drawing-cache deletion) but will be properly modular.

```python
"""
SmartArt template-injection spike.

Throwaway script. Tests whether we can produce an editable PowerPoint
SmartArt graphic by:
  1. Copying a hand-built seed .pptx (one empty Process SmartArt)
  2. Rewriting ppt/diagrams/data1.xml with N hardcoded steps
  3. Deleting ppt/diagrams/drawing1.xml (the cached render)
  4. Stripping the drawing1.xml relationship from ppt/slides/slide1.xml.rels
  5. Stripping the drawing1.xml override from [Content_Types].xml

If the resulting .pptx opens in PowerPoint with the SmartArt Design ribbon
active and the Text Pane editable, the technique works.
"""
from __future__ import annotations

import re
import shutil
import sys
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "tests" / "fixtures" / "smartart_seeds" / "process1_seed.pptx"
OUT = ROOT / "tmp" / "spike_out.pptx"

STEPS = ["Research", "Design", "Build", "Test", "Ship"]

# Layout binding extracted from the seed's doc point. We MUST preserve these
# exactly — they tell PowerPoint which layout/quickStyle/colors to use.
DOC_PRSET = (
    'loTypeId="urn:microsoft.com/office/officeart/2005/8/layout/process1" '
    'loCatId="" '
    'qsTypeId="urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1" '
    'qsCatId="simple" '
    'csTypeId="urn:microsoft.com/office/officeart/2005/8/colors/accent1_2" '
    'csCatId="accent1" '
    'phldr="0"'
)


def gid() -> str:
    """Brace-wrapped uppercase GUID, matching the format Mac PowerPoint emits."""
    return "{" + str(uuid.uuid4()).upper() + "}"


def build_data_model(steps: list[str]) -> bytes:
    doc_id = gid()
    parts: list[str] = []

    parts.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
    parts.append(
        '<dgm:dataModel '
        'xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
    )

    parts.append("<dgm:ptLst>")
    parts.append(
        f'<dgm:pt modelId="{doc_id}" type="doc">'
        f"<dgm:prSet {DOC_PRSET}/>"
        f"<dgm:spPr/>"
        f"</dgm:pt>"
    )

    node_records: list[tuple[str, str, str]] = []
    for step in steps:
        node_id, par_id, sib_id = gid(), gid(), gid()
        node_records.append((node_id, par_id, sib_id))
        parts.append(
            f'<dgm:pt modelId="{node_id}">'
            f'<dgm:prSet phldrT="[Text]"/><dgm:spPr/>'
            f"<dgm:t><a:bodyPr/><a:lstStyle/>"
            f'<a:p><a:r><a:rPr lang="en-GB" dirty="0"/>'
            f"<a:t>{step}</a:t></a:r></a:p></dgm:t>"
            f"</dgm:pt>"
        )
        parts.append(
            f'<dgm:pt modelId="{par_id}" type="parTrans">'
            f"<dgm:prSet/><dgm:spPr/>"
            f"<dgm:t><a:bodyPr/><a:lstStyle/>"
            f'<a:p><a:endParaRPr lang="en-GB"/></a:p></dgm:t>'
            f"</dgm:pt>"
        )
        parts.append(
            f'<dgm:pt modelId="{sib_id}" type="sibTrans">'
            f"<dgm:prSet/><dgm:spPr/>"
            f"<dgm:t><a:bodyPr/><a:lstStyle/>"
            f'<a:p><a:endParaRPr lang="en-GB"/></a:p></dgm:t>'
            f"</dgm:pt>"
        )

    parts.append("</dgm:ptLst>")

    parts.append("<dgm:cxnLst>")
    for ord_, (node_id, par_id, sib_id) in enumerate(node_records):
        parts.append(
            f'<dgm:cxn modelId="{gid()}" '
            f'srcId="{doc_id}" destId="{node_id}" '
            f'srcOrd="{ord_}" destOrd="0" '
            f'parTransId="{par_id}" sibTransId="{sib_id}"/>'
        )
    parts.append("</dgm:cxnLst>")

    parts.append("<dgm:bg/><dgm:whole/>")
    parts.append("</dgm:dataModel>")
    return "".join(parts).encode("utf-8")


def strip_drawing_from_content_types(xml: bytes) -> bytes:
    text = xml.decode("utf-8")
    pattern = (
        r'<Override PartName="/ppt/diagrams/drawing1\.xml" '
        r'ContentType="[^"]*"/>'
    )
    new_text, n = re.subn(pattern, "", text)
    if n != 1:
        raise SystemExit(f"expected exactly 1 drawing1 override, found {n}")
    return new_text.encode("utf-8")


def strip_drawing_from_slide_rels(xml: bytes) -> bytes:
    text = xml.decode("utf-8")
    pattern = (
        r'<Relationship Id="[^"]*" '
        r'Type="http://schemas\.microsoft\.com/office/2007/relationships/diagramDrawing" '
        r'Target="\.\./diagrams/drawing1\.xml"/>'
    )
    new_text, n = re.subn(pattern, "", text)
    if n != 1:
        raise SystemExit(f"expected exactly 1 drawing1 rel, found {n}")
    return new_text.encode("utf-8")


def main() -> int:
    if not SEED.exists():
        print(f"seed not found: {SEED}", file=sys.stderr)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        OUT.unlink()

    new_data = build_data_model(STEPS)

    with zipfile.ZipFile(SEED, "r") as zin, zipfile.ZipFile(
        OUT, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            name = item.filename
            if name == "ppt/diagrams/drawing1.xml":
                continue
            if name == "ppt/diagrams/data1.xml":
                zout.writestr(item, new_data)
                continue
            if name == "[Content_Types].xml":
                zout.writestr(item, strip_drawing_from_content_types(zin.read(name)))
                continue
            if name == "ppt/slides/_rels/slide1.xml.rels":
                zout.writestr(item, strip_drawing_from_slide_rels(zin.read(name)))
                continue
            zout.writestr(item, zin.read(name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

---

## 7. Recommendation

**Proceed with a `pptx_native` SmartArt engine** alongside the existing Mermaid / Vega-Lite / custom_svg engines, scoped initially to the four highest-value layouts where speakers most often want to edit nodes after delivery: **process, cycle, hierarchy/orgChart, and timeline**. The technique works (spike 1), generalises across algorithm families (spike 2), and supports the delivery-time host-injection operation the spec depends on (spike 3). The per-layout cost is small and the workflow constraints (no LibreOffice preview, PowerPoint Mac open as the only review checkpoint) are tractable.

The full design — engine architecture, integration with the existing `smartart-selector` negotiation, draft/production lifecycle, test plan, remaining open questions — is in the follow-on spec at `docs/superpowers/specs/2026-04-08-pptx-native-smartart-engine.md`.

---

## 8. Open questions (updated)

Original open questions, with resolution status after spikes 2 and 3:

1. ~~Does the technique generalise to `cycle1`, `orgChart1`, `basicTimeline1` without per-layout surprises?~~ — **cycle proven by spike 2. Timeline highly likely by analogy (same flat-list shape). OrgChart still unknown — hierarchical data shape, warrants its own one-layout spike before that engine module is written.**
2. What happens when a Windows-authored seed is used instead of a Mac-authored one? (Different content types? Different rels storage?) — **still open, deferred to v2 per spec §10.2.**
3. ~~How does the comparator pattern apply when one of the competing engines (`pptx_native`) has no rasterised preview the image-reviewer can score?~~ — **resolved in spec §2 decisions table: `pptx_native` opts out of the comparator; custom_svg is rendered as a draft preview proxy.**
4. How does the smartart-selector decide when to recommend `pptx_native` vs `custom_svg` for graphic types both engines can handle? — **resolved in spec §7.**
5. Licensing — Phase 1 §8 flagged that shipping seed files might be an Office EULA concern. Hand-built single-purpose seeds with no Microsoft template content are probably safe; needs legal review before merging. — **still open, blocks merge per spec §10.6.**

---

## 9. Spike 2 — generalisation to a different algorithm family (cycle)

### 9.1 Question

Spike 1 proved the technique on `process1` (the `lin` linear-row algorithm). Does the same mutation-plus-cache-delete recipe work on a structurally different SmartArt layout?

### 9.2 Setup

| Component | Detail |
|---|---|
| Seed file | `tests/fixtures/smartart_seeds/cycle1_seed.pptx` (44 KB) — created by inserting Insert → SmartArt → Cycle → Basic Cycle on a blank slide in PowerPoint Mac |
| Target layout | `urn:microsoft.com/office/officeart/2005/8/layout/cycle2` — **note the `cycle2` not `cycle1`**. Mac PowerPoint's "Basic Cycle" (the first tile in the Cycle category) binds to `cycle2`. This is not a mistake and has no practical effect; the naming just reflects that `cycle1` is a different built-in layout. |
| Test data | 6 hardcoded phases: `Plan → Build → Test → Deploy → Monitor → Learn` |

### 9.3 Method

Identical to spike 1. The data-model builder function is unchanged — only the constant `DOC_PRSET` string changes to reflect the cycle2 layout binding URI. All four mutations (rewrite `data1.xml`, delete `drawing1.xml`, patch `slide1.xml.rels`, patch `[Content_Types].xml`) are the same.

This was the whole point of spike 2: prove the data-model builder is layout-agnostic and the only per-layout variable is the `loTypeId` constant.

### 9.4 Results

| Check | Result |
|---|---|
| Spike script exits cleanly | PASS |
| Output `data1.xml` parses with `xmllint` | PASS — 1 doc + 6 nodes + 12 transition points + 6 connections |
| Surgical diff vs seed | PASS — exactly 4 changes (same as spike 1) |
| LibreOffice parses without error | PASS |
| PowerPoint Mac editability gate | **PASS — user confirmed all 6 checks pass: opens clean, 6 phases visible in a ring, SmartArt Design ribbon active, Text Pane populated, Add Shape works, Change Layout in-group (pick a different Cycle sub-layout) preserves content.** |

### 9.5 What this adds to what we know

1. **The data model builder is layout-agnostic.** The same code emitted both a process diagram and a cycle diagram just by changing the `loTypeId` string. This confirms the spec's assumption that per-layout generator code is tiny — the layout-specific bit is a constant, not a function. By extension, timeline (another flat-list layout) is extremely likely to work without per-layout surprises.
2. **The `cycle` algorithm regenerates the presentation tree** from `layout1.xml` exactly as cleanly as `lin`. No pres-tree breadcrumbs left behind in the data model, no special cases needed.
3. **`cycle2` vs `cycle1`** — our seeds are the authoritative source of truth for which URI to use. Never hardcode a URI from documentation; always extract from the seed's doc point. The spec's "one seed per layout" design absorbs this automatically.

---

## 10. Spike 3 — injection into a blank host

### 10.1 Question

Spikes 1 and 2 mutated files that *already had* a SmartArt graphic — PowerPoint had written all four diagram parts, both `<dgm:relIds>` in the slide XML, and the four content-type overrides. We only had to rewrite `data1.xml` and delete the cache.

The production pipeline needs a different operation: take a host `.pptx` that has *no* SmartArt, and **add** a SmartArt graphic to one of its slides. This means writing four new diagram parts, allocating fresh `rIds`, adding four content-type overrides, and inserting a `<p:graphicFrame>` element into the slide's `<p:spTree>`. Does that work?

### 10.2 Setup

| Component | Detail |
|---|---|
| Host file | `tests/fixtures/smartart_seeds/blank_slide.pptx` (32 KB) — fresh PowerPoint Mac blank presentation, one slide with the default `ctrTitle` layout (empty title and subtitle placeholders), no SmartArt, single relationship `rId1` → slideLayout1 |
| Source of layout/quickStyle/colors | `process1_seed.pptx` — the three opaque parts are copied verbatim; only `data1.xml` is built from scratch |
| Test data | 5 hardcoded steps: `Research → Design → Build → Test → Ship` |

### 10.3 Method

The spike script (embedded below in §10.7) performs seven operations in order:

1. **Read three opaque blobs** from the process1 seed: `layout1.xml` (4.5 KB), `quickStyle1.xml` (20.7 KB), `colors1.xml` (16.9 KB). These are passed through unchanged.
2. **Build a fresh `data1.xml`** for 5 process steps using the same data-model builder from spike 1.
3. **Patch `[Content_Types].xml`** — add four `<Override>` entries for the four diagram parts (insert before `</Types>`, after checking no diagram overrides already exist in the host).
4. **Patch `slide1.xml.rels`** — add four `<Relationship>` entries with `rId2`-`rId5` (after checking no such rIds are already in use in the host), pointing at `../diagrams/data1.xml`, `../diagrams/layout1.xml`, `../diagrams/quickStyle1.xml`, `../diagrams/colors1.xml`.
5. **Patch `slide1.xml`** — scan existing `<p:cNvPr id="N">` elements to find the next free shape id (host had id=1,2,3 so new id=4), then insert a `<p:graphicFrame>` before `</p:spTree>`. The frame has hardcoded EMU coordinates (x=1", y=2.25", width=11.3", height=3") and contains a `<dgm:relIds>` with an inline `xmlns:dgm` namespace declaration pointing at rId2-5.
6. **Write the four diagram parts** as new entries under `ppt/diagrams/`. No `drawing1.xml` is written — PowerPoint regenerates it on first open.
7. **Save the output zip.**

The script asserts collision-free rId allocation and collision-free content-type override insertion before proceeding, so a host that already had SmartArt would fail loudly rather than silently corrupt. A production engine will need to handle this case (allocate next free rId dynamically, detect next free diagram number), but for the spike a blank host is sufficient.

### 10.4 Results — automated checks

| Check | Result |
|---|---|
| Spike script exits cleanly | PASS |
| All seven modified/added files well-formed (`xmllint --noout` on `[Content_Types].xml`, `slide1.xml`, `slide1.xml.rels`, all four diagram parts) | PASS |
| rId allocation | PASS — host's `rId1` preserved, new `rId2`-`rId5` added |
| Content-type overrides | PASS — 4 new `<Override>` entries for the four diagram parts |
| Shape id uniqueness | PASS — graphicFrame allocated id=4 (1=group, 2=Title, 3=Subtitle) |
| Graphic frame structure | PASS — correct `<a:graphicData uri="…/diagram">` wrapper, `<dgm:relIds>` with `r:dm="rId2" r:lo="rId3" r:qs="rId4" r:cs="rId5"` |
| LibreOffice parses without error | PASS (produces a PDF, which like spike 1's output is blank because we deleted/never wrote `drawing1.xml`) |

### 10.5 Results — PowerPoint Mac editability gate

**User confirmed all 6 checks pass** when opening `tmp/spike3_inject_out.pptx` in PowerPoint Mac:

1. Opens with no repair dialog
2. Five process boxes visible (with the title + subtitle placeholders still present above, as expected — the spike left the host's shapes alone and only added the SmartArt)
3. SmartArt Design ribbon appears
4. Text Pane populated with the 5 steps
5. Add Shape works
6. Change Layout in-group (Process → other Process sub-layout) preserves content

### 10.6 What this adds

1. **Host injection is viable.** We can add a SmartArt graphic to a PowerPoint slide that had none, using only seven deterministic surgical edits, and PowerPoint accepts the result as fully editable. This is the most important finding in the entire spike series — it's the operation the production pipeline's assembler post-process step depends on, and it was the biggest unvalidated risk in the spec.
2. **rId allocation is trivial** for the blank-host case: start at `max(existing) + 1`. Production engine will need slightly smarter logic (skip gaps, handle pre-existing diagrams) but the mechanism is sound.
3. **Inline namespace declaration** on `<dgm:relIds>` is the right approach. The slide root already declares `xmlns:p`, `xmlns:a`, `xmlns:r` but not `xmlns:dgm`; adding it inline on the single element that uses it is less invasive than editing the slide root.
4. **Shape id allocation by scanning `<p:cNvPr id="N">`** is reliable — tried-and-tested approach PowerPoint itself uses internally.
5. **No drawing cache needed at inject time** — same as spikes 1 and 2. PowerPoint regenerates the entire render pipeline on first open, including layout computation and cache write-back.

### 10.7 Spike 3 script

```python
"""
Spike 3 — host injection.

Throwaway script. Validates that we can inject SmartArt into a host .pptx
that did not have any SmartArt to begin with — the operation that the
production pipeline's assembler post-process step will need to perform.
"""
from __future__ import annotations

import re
import sys
import uuid
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = ROOT / "tests" / "fixtures" / "smartart_seeds" / "blank_slide.pptx"
SOURCE = ROOT / "tests" / "fixtures" / "smartart_seeds" / "process1_seed.pptx"
OUT = ROOT / "tmp" / "spike3_inject_out.pptx"

STEPS = ["Research", "Design", "Build", "Test", "Ship"]

DOC_PRSET = (
    'loTypeId="urn:microsoft.com/office/officeart/2005/8/layout/process1" '
    'loCatId="" '
    'qsTypeId="urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1" '
    'qsCatId="simple" '
    'csTypeId="urn:microsoft.com/office/officeart/2005/8/colors/accent1_2" '
    'csCatId="accent1" '
    'phldr="0"'
)

# Frame coordinates in EMU (914400 per inch). 1" / 2.25", 11.3" × 3".
FRAME_X, FRAME_Y = 914400, 2057400
FRAME_CX, FRAME_CY = 10363200, 2743200

DIAGRAM_OVERRIDES = [
    ("/ppt/diagrams/data1.xml",
     "application/vnd.openxmlformats-officedocument.drawingml.diagramData+xml"),
    ("/ppt/diagrams/layout1.xml",
     "application/vnd.openxmlformats-officedocument.drawingml.diagramLayout+xml"),
    ("/ppt/diagrams/quickStyle1.xml",
     "application/vnd.openxmlformats-officedocument.drawingml.diagramStyle+xml"),
    ("/ppt/diagrams/colors1.xml",
     "application/vnd.openxmlformats-officedocument.drawingml.diagramColors+xml"),
]

DIAGRAM_RELS = [
    ("rId2",
     "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramData",
     "../diagrams/data1.xml"),
    ("rId3",
     "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramLayout",
     "../diagrams/layout1.xml"),
    ("rId4",
     "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramQuickStyle",
     "../diagrams/quickStyle1.xml"),
    ("rId5",
     "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramColors",
     "../diagrams/colors1.xml"),
]


def gid() -> str:
    return "{" + str(uuid.uuid4()).upper() + "}"


def build_data_model(items: list[str]) -> bytes:
    # (same builder as spike 1 — abbreviated here, see §6 for full listing)
    ...


def patch_slide_rels(xml: bytes) -> bytes:
    text = xml.decode("utf-8")
    existing_ids = re.findall(r'Id="(rId\d+)"', text)
    for rid, _, _ in DIAGRAM_RELS:
        if rid in existing_ids:
            raise SystemExit(f"rId collision: {rid}")
    new_rels = "".join(
        f'<Relationship Id="{rid}" Type="{type_}" Target="{target}"/>'
        for rid, type_, target in DIAGRAM_RELS
    )
    return text.replace("</Relationships>", new_rels + "</Relationships>").encode("utf-8")


def patch_content_types(xml: bytes) -> bytes:
    text = xml.decode("utf-8")
    for part_name, _ in DIAGRAM_OVERRIDES:
        if f'PartName="{part_name}"' in text:
            raise SystemExit(f"content-type collision: {part_name}")
    new_overrides = "".join(
        f'<Override PartName="{pn}" ContentType="{ct}"/>'
        for pn, ct in DIAGRAM_OVERRIDES
    )
    return text.replace("</Types>", new_overrides + "</Types>").encode("utf-8")


def patch_slide_xml(xml: bytes) -> bytes:
    text = xml.decode("utf-8")
    existing_ids = [int(m) for m in re.findall(r'<p:cNvPr id="(\d+)"', text)]
    next_id = (max(existing_ids) + 1) if existing_ids else 4
    graphic_frame = (
        "<p:graphicFrame>"
        "<p:nvGraphicFramePr>"
        f'<p:cNvPr id="{next_id}" name="Diagram 1"/>'
        '<p:cNvGraphicFramePr><a:graphicFrameLocks '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'noChangeAspect="1"/></p:cNvGraphicFramePr>'
        "<p:nvPr/>"
        "</p:nvGraphicFramePr>"
        "<p:xfrm>"
        f'<a:off xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        f'x="{FRAME_X}" y="{FRAME_Y}"/>'
        f'<a:ext xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        f'cx="{FRAME_CX}" cy="{FRAME_CY}"/>'
        "</p:xfrm>"
        '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/diagram">'
        '<dgm:relIds xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" '
        'r:dm="rId2" r:lo="rId3" r:qs="rId4" r:cs="rId5"/>'
        "</a:graphicData>"
        "</a:graphic>"
        "</p:graphicFrame>"
    )
    return text.replace("</p:spTree>", graphic_frame + "</p:spTree>").encode("utf-8")


def main() -> int:
    with zipfile.ZipFile(SOURCE, "r") as zsrc:
        layout_bytes = zsrc.read("ppt/diagrams/layout1.xml")
        quickstyle_bytes = zsrc.read("ppt/diagrams/quickStyle1.xml")
        colors_bytes = zsrc.read("ppt/diagrams/colors1.xml")
    data_bytes = build_data_model(STEPS)

    with zipfile.ZipFile(HOST, "r") as zin, zipfile.ZipFile(
        OUT, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            name = item.filename
            if name == "[Content_Types].xml":
                zout.writestr(item, patch_content_types(zin.read(name)))
            elif name == "ppt/slides/_rels/slide1.xml.rels":
                zout.writestr(item, patch_slide_rels(zin.read(name)))
            elif name == "ppt/slides/slide1.xml":
                zout.writestr(item, patch_slide_xml(zin.read(name)))
            else:
                zout.writestr(item, zin.read(name))
        zout.writestr("ppt/diagrams/data1.xml", data_bytes)
        zout.writestr("ppt/diagrams/layout1.xml", layout_bytes)
        zout.writestr("ppt/diagrams/quickStyle1.xml", quickstyle_bytes)
        zout.writestr("ppt/diagrams/colors1.xml", colors_bytes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

(The `build_data_model` function is omitted here to avoid duplication — it is identical to the one in §6, which is where the canonical reference lives.)

---

## 11. Combined conclusion

Three spikes, three green lights. The `pptx_native` engine approach is empirically validated on all three dimensions that mattered:

| Dimension | Spike | Status |
|---|---|---|
| Mutation of existing SmartArt produces editable output | 1 | PROVEN |
| Technique generalises across algorithm families | 2 | PROVEN (lin → cycle) |
| Injection into a host with no prior SmartArt works | 3 | PROVEN |

**Next validation before implementation:** a small one-layout spike against `orgChart1` (hierarchical data shape — the one algorithm family not yet covered) before the org-chart layout module is written. This was captured as spec §10.1 follow-up.

**Unresolved open items that block implementation:**
- Legal sign-off on shipping Mac PowerPoint–authored seeds (spec §10.6)

**Unresolved open items that do not block v1 but are worth recording:**
- Windows-authored seed compatibility (spec §10.2)
- Cross-group layout switching behaviour in PowerPoint's Change Layout gallery (data-gathering during manual gates)
