# Spike: python-pptx Editing of /pptx Superpower Output

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove — or disprove — that python-pptx can reliably (a) apply an AI-generated raster as a slide background, (b) find a named shape and replace it with an embedded image at the same position, and (c) that `assembler_patch.inject()` can graft pptx_native SmartArt into a .pptx produced by the `/pptx` superpower (PptxGenJS-emitted OOXML), producing files that open correctly in PowerPoint Mac.

**Architecture:** Start from a known-good /pptx-produced deck containing three named placeholder shapes. Run three independent prototypes — one per enrichment operation — each producing a modified .pptx that is opened in PowerPoint Mac and verified visually. OOXML round-trip is checked after each operation using python-pptx re-load + manual schema inspection. The spike succeeds if all three operations produce clean, openable files; it fails or requires redesign if any operation corrupts the deck, loses the superpower's theme/master, or produces visually-broken output.

**Tech Stack:** python-pptx (for background + image replacement), lxml (for raw XML inspection and any surgery python-pptx can't do), the pptx_native engine at `plugins/jack-tar-msft-smartart/src/` (`engine.py`, `assembler_patch.py`), PowerPoint Mac for visual validation, `tools/pptx_to_pdf.sh` + pdftoppm for rasterisation.

**Out of scope:**
- Automated enrichment pipeline — we hand-drive every operation.
- The Phase 1 creative brief — we hand-author the seed deck or reuse Spike 1's Variant C output if already present.
- Marker detection — we know the shape names up front.
- Any image generation — we use a pre-existing placeholder PNG.

---

## File Structure

```
docs/spikes/2026-04-23-python-pptx-enrichment/
  README.md                        # Findings (written last)
  seed/
    build_seed.py                  # Emit a deck with 3 named markers via python-pptx
                                   # OR: copy from docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-c/
    seed.pptx                      # The deck we will enrich
    placeholder.png                # Stand-in image for backgrounds + element replacement
  prototypes/
    op1_background.py              # Set slide background to image
    op2_replace_image_shape.py     # Replace IMAGE:* marker with embedded picture
    op3_inject_smartart.py         # Inject pptx_native SmartArt into SMARTART:* marker
  outputs/
    after_op1.pptx
    after_op2.pptx
    after_op3.pptx
    all_ops.pptx                   # All three operations applied in sequence
    all_ops.pdf                    # PDF of final deck for review
    all_ops_slides/                # PNG per slide
  results/
    ooxml_inspection.md            # Notes from eyeballing the XML before/after
    powerpoint_gate.md             # Manual gate: PowerPoint Mac open + visual check
    findings.json                  # Machine-readable: per-op pass/fail + notes
  tests/
    test_op1_background.py
    test_op2_replace_image.py
    test_op3_inject_smartart.py
```

**Files that matter beyond the spike:**
- `docs/spikes/2026-04-23-python-pptx-enrichment/README.md` — the findings report.
- `prototypes/*.py` — if the spike succeeds, these are the seeds for `plugins/jack-tar-superpower-bridge/src/enrichment.py`. Write them cleanly but do not over-engineer.

---

## Task 1: Scaffold the spike directory

**Files:**
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/{seed,prototypes,outputs,results,tests}/.gitkeep`

- [ ] **Step 1: Create the directory tree**

```bash
mkdir -p docs/spikes/2026-04-23-python-pptx-enrichment/{seed,prototypes,outputs,results,tests}
touch docs/spikes/2026-04-23-python-pptx-enrichment/{seed,prototypes,outputs,results,tests}/.gitkeep
```

- [ ] **Step 2: Commit**

```bash
git add docs/spikes/2026-04-23-python-pptx-enrichment
git commit -m "spike: scaffold python-pptx enrichment directory"
```

---

## Task 2: Produce the seed deck and placeholder image

Prefer Spike 1's Variant C output (real /pptx-emitted OOXML). Fall back to a hand-built deck if Spike 1 has not been run — both should expose the same python-pptx behaviour, but /pptx output is the higher-fidelity target.

**Files:**
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/seed/build_seed.py`
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/seed/seed.pptx`
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/seed/placeholder.png`

- [ ] **Step 1: Decide which seed source to use**

Check if `docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-c/presentation.pptx` exists.

```bash
ls docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-c/presentation.pptx 2>&1
```

If present AND it contains at least one of each marker (IMAGE, SMARTART, BG — check the Spike 1 report), copy it as the seed:

```bash
cp docs/spikes/2026-04-23-pptx-marker-adherence/outputs/variant-c/presentation.pptx \
   docs/spikes/2026-04-23-python-pptx-enrichment/seed/seed.pptx
```

Skip to Step 3. Otherwise continue to Step 2.

- [ ] **Step 2: Fallback — hand-build the seed deck**

Write `docs/spikes/2026-04-23-python-pptx-enrichment/seed/build_seed.py`:

```python
"""Build a seed deck with three named marker shapes.

Used only when Spike 1's Variant C output is unavailable. Produces a deck structurally
similar to what /pptx would emit — blank layout, named shapes with grey fill + dashed
border, text content in shape text_frames.
"""
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt


def add_marker(slide, name: str, left: float, top: float, width: float, height: float, label: str) -> None:
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.name = name
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(0xF0, 0xF0, 0xF0)
    shape.line.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
    shape.line.dash_style = 7  # dashed
    tf = shape.text_frame
    tf.text = label
    tf.paragraphs[0].runs[0].font.size = Pt(14)
    tf.paragraphs[0].runs[0].font.color.rgb = RGBColor(0x88, 0x88, 0x88)


def main() -> None:
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # Slide 1 — IMAGE marker on the right 40%
    s1 = prs.slides.add_slide(blank)
    s1.shapes.title is None  # blank layout has no title
    title = s1.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.8))
    title.text_frame.text = "Why most agents fail"
    body = s1.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(4.5), Inches(3))
    body.text_frame.text = "Prompt engineering hits a ceiling\nNo persistent memory\nTool use is brittle"
    add_marker(s1, "IMAGE:agents-failing", 5.5, 1.5, 4, 3, "IMAGE:agents-failing")

    # Slide 2 — SMARTART marker replacing bullet content
    s2 = prs.slides.add_slide(blank)
    title = s2.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.8))
    title.text_frame.text = "Three pillars of agent architecture"
    add_marker(s2, "SMARTART:flowchart", 1, 1.5, 8, 4.5, "SMARTART:flowchart\nPlanning → Memory → Tool use")

    # Slide 3 — BG corner label
    s3 = prs.slides.add_slide(blank)
    title = s3.shapes.add_textbox(Inches(0.5), Inches(2.5), Inches(9), Inches(1.5))
    title.text_frame.text = "AI Agents That Actually Work"
    title.text_frame.paragraphs[0].runs[0].font.size = Pt(48)
    add_marker(s3, "BG:dramatic-opening", 0.2, 6.9, 1.8, 0.3, "BG:dramatic-opening")

    prs.save("docs/spikes/2026-04-23-python-pptx-enrichment/seed/seed.pptx")
    print("Wrote seed.pptx — 3 slides, 3 named markers")


if __name__ == "__main__":
    main()
```

Run:
```bash
.venv/bin/python docs/spikes/2026-04-23-python-pptx-enrichment/seed/build_seed.py
```
Expected: `Wrote seed.pptx — 3 slides, 3 named markers`.

- [ ] **Step 3: Create the placeholder PNG**

Generate a 1600×900 solid-colour PNG with a centred label so it is obvious when it has been applied:

```bash
.venv/bin/python - <<'PY'
from PIL import Image, ImageDraw, ImageFont
img = Image.new("RGB", (1600, 900), color=(40, 60, 100))
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 80)
except OSError:
    font = ImageFont.load_default()
draw.text((400, 400), "PLACEHOLDER IMAGE", fill=(220, 220, 220), font=font)
img.save("docs/spikes/2026-04-23-python-pptx-enrichment/seed/placeholder.png")
print("wrote placeholder.png")
PY
```

Expected: `wrote placeholder.png`. Verify the file exists and is ~30–60 KB.

- [ ] **Step 4: Sanity-check seed with the Spike 1 analyser (if available)**

```bash
ls docs/spikes/2026-04-23-pptx-marker-adherence/tools/analyse_markers.py 2>/dev/null && \
  .venv/bin/python docs/spikes/2026-04-23-pptx-marker-adherence/tools/analyse_markers.py \
    docs/spikes/2026-04-23-python-pptx-enrichment/seed/seed.pptx
```

Expected: 3 markers reported, one of each kind. If analyser not available, skip — not worth writing a duplicate for the fallback path.

- [ ] **Step 5: Commit**

```bash
git add docs/spikes/2026-04-23-python-pptx-enrichment/seed/
git commit -m "spike: seed deck and placeholder image for enrichment spike"
```

---

## Task 3: Research python-pptx slide-background capabilities

Before writing the prototype, read enough of python-pptx to know what the API supports and where raw XML surgery will be needed. Record findings — they will go into the findings README.

**Files:**
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/results/ooxml_inspection.md`

- [ ] **Step 1: Inspect python-pptx slide background support**

```bash
.venv/bin/python - <<'PY'
import pptx
import pptx.slide
print("python-pptx version:", pptx.__version__)
print()
print("Slide attrs related to background:")
print([a for a in dir(pptx.slide.Slide) if "back" in a.lower() or "bg" in a.lower()])
print()
help(pptx.slide.Slide.background)
PY
```

Expected: a description of `Slide.background` returning a `_Background` object. Note whether it exposes a method for setting a picture fill.

- [ ] **Step 2: Write initial findings**

Start `docs/spikes/2026-04-23-python-pptx-enrichment/results/ooxml_inspection.md` with:

```markdown
# OOXML inspection notes

## python-pptx version

<paste from step 1>

## Slide.background capabilities

<Does it offer a picture-fill setter? If only solid/gradient, document the XML-level workaround required.>

## Expected XML for image-filled background

On the slide's XML element `<p:sld>`, the `<p:cSld>/<p:bg>` child should look like:

```xml
<p:bg>
  <p:bgPr>
    <a:blipFill dpi="0" rotWithShape="1">
      <a:blip r:embed="rId<N>"/>
      <a:srcRect/>
      <a:stretch><a:fillRect/></a:stretch>
    </a:blipFill>
    <a:effectLst/>
  </p:bgPr>
</p:bg>
```

Plus a new relationship entry on `slideN.xml.rels` pointing to `../media/imageN.png`.

## Plan

If `Slide.background` supports blipFill directly → use the API.
If not → construct the `<p:bg>` element via lxml and insert it into `slide.element.find(qn("p:cSld"))`, and add the image part via `slide.part.package.next_image_partname()` + `slide.part.relate_to(img_part, RT.IMAGE)`.
```

- [ ] **Step 3: Commit**

```bash
git add docs/spikes/2026-04-23-python-pptx-enrichment/results/ooxml_inspection.md
git commit -m "spike: python-pptx background capability research"
```

---

## Task 4: Prototype Op1 — apply slide background image — TDD

**Files:**
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/tests/test_op1_background.py`
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/prototypes/op1_background.py`

- [ ] **Step 1: Write the failing test**

```python
"""Verify op1 produces a deck where slide 3 has a blipFill background pointing at an image part."""
import shutil
import sys
from pathlib import Path

from pptx import Presentation
from pptx.oxml.ns import qn

SPIKE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE_DIR / "prototypes"))

from op1_background import apply_background

SEED = SPIKE_DIR / "seed" / "seed.pptx"
IMAGE = SPIKE_DIR / "seed" / "placeholder.png"


def test_applies_blipfill_and_removes_marker(tmp_path):
    work = tmp_path / "op1.pptx"
    shutil.copy(SEED, work)

    apply_background(pptx_path=work, slide_index_1based=3, image_path=IMAGE, marker_name="BG:dramatic-opening")

    prs = Presentation(str(work))
    slide = prs.slides[2]  # 0-based
    cSld = slide.element.find(qn("p:cSld"))
    bg = cSld.find(qn("p:bg"))
    assert bg is not None, "slide 3 should have a <p:bg> element after op1"
    blip = bg.find(".//" + qn("a:blip"))
    assert blip is not None, "<p:bg> should contain a <a:blip> image reference"
    rid = blip.get(qn("r:embed"))
    assert rid, "<a:blip> must have r:embed"
    # The rId must resolve to an image part
    part = slide.part.related_part(rid)
    assert part.content_type.startswith("image/"), f"rId should resolve to an image part, got {part.content_type}"

    marker_names = [s.name for s in slide.shapes]
    assert "BG:dramatic-opening" not in marker_names, "BG marker shape must be removed after background applied"


def test_file_reopens_cleanly_in_python_pptx(tmp_path):
    work = tmp_path / "op1.pptx"
    shutil.copy(SEED, work)
    apply_background(pptx_path=work, slide_index_1based=3, image_path=IMAGE, marker_name="BG:dramatic-opening")
    # Round-trip
    prs = Presentation(str(work))
    assert len(prs.slides) >= 3
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/pytest docs/spikes/2026-04-23-python-pptx-enrichment/tests/test_op1_background.py -v`
Expected: ImportError on `op1_background`.

- [ ] **Step 3: Implement op1**

```python
"""Op1: apply a PNG as a slide background and remove the BG marker shape.

Uses python-pptx's part + relationship API for the image, and hand-constructs the
<p:bg> element via lxml because python-pptx's Background API does not expose picture fill
at the time of writing.
"""
from __future__ import annotations

from pathlib import Path
from typing import Union

from lxml import etree
from pptx import Presentation
from pptx.opc.constants import CONTENT_TYPE as CT
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.package import Package
from pptx.parts.image import ImagePart


def _remove_existing_bg(cSld_elem) -> None:
    existing = cSld_elem.find(qn("p:bg"))
    if existing is not None:
        cSld_elem.remove(existing)


def _build_bg_element(rid: str):
    nsmap = {
        "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }
    xml = f"""
    <p:bg xmlns:p="{nsmap['p']}" xmlns:a="{nsmap['a']}" xmlns:r="{nsmap['r']}">
      <p:bgPr>
        <a:blipFill dpi="0" rotWithShape="1">
          <a:blip r:embed="{rid}"/>
          <a:srcRect/>
          <a:stretch><a:fillRect/></a:stretch>
        </a:blipFill>
        <a:effectLst/>
      </p:bgPr>
    </p:bg>
    """.strip()
    return etree.fromstring(xml)


def apply_background(
    pptx_path: Union[str, Path],
    slide_index_1based: int,
    image_path: Union[str, Path],
    marker_name: str | None = None,
) -> None:
    pptx_path = Path(pptx_path)
    image_path = Path(image_path)

    prs = Presentation(str(pptx_path))
    if slide_index_1based < 1 or slide_index_1based > len(prs.slides):
        raise IndexError(f"slide {slide_index_1based} out of range (1..{len(prs.slides)})")
    slide = prs.slides[slide_index_1based - 1]

    # Add the image as a part and relate it to the slide
    with open(image_path, "rb") as f:
        image_blob = f.read()
    ext = image_path.suffix.lstrip(".").lower()
    content_type = {"png": CT.PNG, "jpg": CT.JPEG, "jpeg": CT.JPEG}[ext]
    image_part = ImagePart.new(slide.part.package, image_blob, content_type, ext)
    rid = slide.part.relate_to(image_part, RT.IMAGE)

    # Insert <p:bg> right after <p:cSld>'s opening (must be first child of <p:cSld>)
    cSld = slide.element.find(qn("p:cSld"))
    _remove_existing_bg(cSld)
    bg = _build_bg_element(rid)
    cSld.insert(0, bg)

    # Remove marker shape if requested
    if marker_name:
        spTree = cSld.find(qn("p:spTree"))
        for sp in list(spTree):
            nvSpPr = sp.find(qn("p:nvSpPr"))
            if nvSpPr is None:
                continue
            cNvPr = nvSpPr.find(qn("p:cNvPr"))
            if cNvPr is not None and cNvPr.get("name") == marker_name:
                spTree.remove(sp)

    prs.save(str(pptx_path))


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 5:
        print("usage: op1_background.py <pptx> <slide_1based> <image_png> <marker_name_or_->")
        sys.exit(2)
    mn = sys.argv[4] if sys.argv[4] != "-" else None
    apply_background(sys.argv[1], int(sys.argv[2]), sys.argv[3], mn)
    print("ok")
```

Notes on the implementation:
- `ImagePart.new(...)` signature varies across python-pptx versions. If it differs in the installed version, consult `pptx/parts/image.py` — the usual alternatives are `ImagePart(package, partname, content_type, image_blob)` or using `package.image_part_for(image_blob, content_type, ext)`. Discover the actual signature before implementing.
- `p:cNvPr/@name` is where python-pptx stores the shape name.

- [ ] **Step 4: Discover the correct ImagePart API for this python-pptx version**

Before trusting the code above, check what the installed version offers:

```bash
.venv/bin/python - <<'PY'
from pptx.parts.image import ImagePart
import inspect
print("ImagePart signature(s):")
for name in dir(ImagePart):
    if name.startswith("_") or name == "new":
        pass
print("Classmethods on ImagePart:")
for name, member in inspect.getmembers(ImagePart, predicate=inspect.isfunction):
    print(" ", name, inspect.signature(member))
PY
```

Adjust the `ImagePart.new(...)` call in op1_background.py to match the discovered signature.

- [ ] **Step 5: Run the tests**

Run: `.venv/bin/pytest docs/spikes/2026-04-23-python-pptx-enrichment/tests/test_op1_background.py -v`
Expected: 2 passed.

If it fails, do not plaster over the failure — the spike is answering whether this works. A genuine failure here is a finding for the report.

- [ ] **Step 6: Produce the single-op artefact**

```bash
cp docs/spikes/2026-04-23-python-pptx-enrichment/seed/seed.pptx \
   docs/spikes/2026-04-23-python-pptx-enrichment/outputs/after_op1.pptx
.venv/bin/python docs/spikes/2026-04-23-python-pptx-enrichment/prototypes/op1_background.py \
   docs/spikes/2026-04-23-python-pptx-enrichment/outputs/after_op1.pptx \
   3 \
   docs/spikes/2026-04-23-python-pptx-enrichment/seed/placeholder.png \
   BG:dramatic-opening
```

Expected: prints `ok`, and `after_op1.pptx` retains 3 slides, slide 3 has a background image.

- [ ] **Step 7: Commit**

```bash
git add docs/spikes/2026-04-23-python-pptx-enrichment/prototypes/op1_background.py \
        docs/spikes/2026-04-23-python-pptx-enrichment/tests/test_op1_background.py \
        docs/spikes/2026-04-23-python-pptx-enrichment/outputs/after_op1.pptx
git commit -m "spike: op1 — apply slide background image via python-pptx"
```

---

## Task 5: Prototype Op2 — replace IMAGE marker with embedded picture — TDD

**Files:**
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/tests/test_op2_replace_image.py`
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/prototypes/op2_replace_image_shape.py`

- [ ] **Step 1: Write the failing test**

```python
"""Verify op2 removes the IMAGE marker and replaces it with an embedded picture at the same position."""
import shutil
import sys
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn

SPIKE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE_DIR / "prototypes"))

from op2_replace_image_shape import replace_image_marker

SEED = SPIKE_DIR / "seed" / "seed.pptx"
IMAGE = SPIKE_DIR / "seed" / "placeholder.png"


def test_marker_replaced_with_picture_at_same_position(tmp_path):
    work = tmp_path / "op2.pptx"
    shutil.copy(SEED, work)

    # Capture target geometry before mutation
    before = Presentation(str(work))
    target = next(
        (s for s in before.slides[0].shapes if s.name == "IMAGE:agents-failing"),
        None,
    )
    assert target is not None, "seed deck must have an IMAGE:agents-failing shape on slide 1"
    left, top, width, height = target.left, target.top, target.width, target.height

    replace_image_marker(pptx_path=work, marker_name="IMAGE:agents-failing", image_path=IMAGE)

    after = Presentation(str(work))
    slide = after.slides[0]
    # Marker must be gone
    names = [s.name for s in slide.shapes]
    assert "IMAGE:agents-failing" not in names
    # Exactly one new picture shape at the captured geometry
    pictures = [s for s in slide.shapes if s.shape_type == MSO_SHAPE_TYPE.PICTURE]
    assert len(pictures) >= 1
    match = [p for p in pictures if p.left == left and p.top == top and p.width == width and p.height == height]
    assert len(match) == 1, f"expected one picture at {(left, top, width, height)}, got {[(p.left, p.top, p.width, p.height) for p in pictures]}"


def test_file_reopens_cleanly(tmp_path):
    work = tmp_path / "op2.pptx"
    shutil.copy(SEED, work)
    replace_image_marker(pptx_path=work, marker_name="IMAGE:agents-failing", image_path=IMAGE)
    prs = Presentation(str(work))
    assert len(prs.slides) == 3
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/pytest docs/spikes/2026-04-23-python-pptx-enrichment/tests/test_op2_replace_image.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement op2**

```python
"""Op2: find a shape by name on any slide, replace it with an embedded picture at the same position."""
from __future__ import annotations

from pathlib import Path
from typing import Union

from pptx import Presentation
from pptx.oxml.ns import qn


def _find_shape_on_any_slide(prs, name: str):
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.name == name:
                return slide, shape
    return None, None


def replace_image_marker(
    pptx_path: Union[str, Path],
    marker_name: str,
    image_path: Union[str, Path],
) -> None:
    pptx_path = Path(pptx_path)
    image_path = Path(image_path)

    prs = Presentation(str(pptx_path))
    slide, shape = _find_shape_on_any_slide(prs, marker_name)
    if shape is None:
        raise LookupError(f"shape {marker_name!r} not found on any slide")
    left, top, width, height = shape.left, shape.top, shape.width, shape.height

    # Remove the marker shape (via XML so we are not fooled by python-pptx wrappers)
    sp_elem = shape._element
    sp_elem.getparent().remove(sp_elem)

    # Add a new picture at the captured geometry
    slide.shapes.add_picture(str(image_path), left, top, width=width, height=height)

    prs.save(str(pptx_path))


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("usage: op2_replace_image_shape.py <pptx> <marker_name> <image_path>")
        sys.exit(2)
    replace_image_marker(sys.argv[1], sys.argv[2], sys.argv[3])
    print("ok")
```

- [ ] **Step 4: Run the tests**

Run: `.venv/bin/pytest docs/spikes/2026-04-23-python-pptx-enrichment/tests/test_op2_replace_image.py -v`
Expected: 2 passed.

- [ ] **Step 5: Produce the single-op artefact**

```bash
cp docs/spikes/2026-04-23-python-pptx-enrichment/seed/seed.pptx \
   docs/spikes/2026-04-23-python-pptx-enrichment/outputs/after_op2.pptx
.venv/bin/python docs/spikes/2026-04-23-python-pptx-enrichment/prototypes/op2_replace_image_shape.py \
   docs/spikes/2026-04-23-python-pptx-enrichment/outputs/after_op2.pptx \
   IMAGE:agents-failing \
   docs/spikes/2026-04-23-python-pptx-enrichment/seed/placeholder.png
```

- [ ] **Step 6: Commit**

```bash
git add docs/spikes/2026-04-23-python-pptx-enrichment/prototypes/op2_replace_image_shape.py \
        docs/spikes/2026-04-23-python-pptx-enrichment/tests/test_op2_replace_image.py \
        docs/spikes/2026-04-23-python-pptx-enrichment/outputs/after_op2.pptx
git commit -m "spike: op2 — replace IMAGE marker with embedded picture"
```

---

## Task 6: Prototype Op3 — inject pptx_native SmartArt into SMARTART marker — TDD

This is the riskiest op: `assembler_patch.inject()` was designed for jack-tar's own PptxGenJS output. Here we exercise it on seed-produced OOXML that may differ structurally.

**Files:**
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/tests/test_op3_inject_smartart.py`
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/prototypes/op3_inject_smartart.py`

- [ ] **Step 1: Verify the pptx_native engine API from the plugin**

```bash
.venv/bin/python - <<'PY'
import sys
sys.path.insert(0, "plugins/jack-tar-msft-smartart/src")
from engine import render
from assembler_patch import inject
import inspect
print("engine.render signature:", inspect.signature(render))
print("assembler_patch.inject signature:", inspect.signature(inject))
PY
```

Note the signatures — the test and prototype must match them exactly. The expected shapes per the jack-tar docs:
- `render(spec, output_dir) -> Path` producing a carrier .pptx.
- `inject(host_pptx, requests)` where each request specifies slide + carrier + placeholder_name.

If signatures differ from expectation, adjust the prototype accordingly.

- [ ] **Step 2: Convert the SMARTART marker to a pptx_native placeholder rect**

The existing pattern in jack-tar is that the JS assembler emits a shape named `pptx_native_placeholder_<slide_num>`. `assembler_patch.inject()` looks for that name. Our seed uses a `SMARTART:` prefix. Op3 must rename the marker to the expected convention before calling `inject()`.

- [ ] **Step 3: Write the failing test**

```python
"""Verify op3 grafts a pptx_native diagram onto the slide that had the SMARTART marker."""
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile

SPIKE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE_DIR / "prototypes"))
sys.path.insert(0, "plugins/jack-tar-msft-smartart/src")

from op3_inject_smartart import inject_smartart

SEED = SPIKE_DIR / "seed" / "seed.pptx"


def test_inject_adds_diagram_parts(tmp_path):
    work = tmp_path / "op3.pptx"
    shutil.copy(SEED, work)

    spec = {
        "engine": "pptx_native",
        "layout_id": "process1",
        "data": {"items": [{"text": "Planning"}, {"text": "Memory"}, {"text": "Tool use"}]},
    }

    inject_smartart(
        pptx_path=work,
        marker_name="SMARTART:flowchart",
        slide_index_1based=2,
        spec=spec,
        carriers_dir=tmp_path / "carriers",
    )

    # After injection, the package MUST contain diagram parts
    with ZipFile(work) as z:
        names = z.namelist()
    diagram_parts = [n for n in names if "/diagrams/" in n and n.endswith(".xml")]
    assert len(diagram_parts) >= 3, f"expected at least layout1.xml + data1.xml + colors1.xml + quickStyle1.xml; got {diagram_parts}"

    # The SMARTART marker shape must be gone (replaced by graphicFrame)
    from pptx import Presentation
    prs = Presentation(str(work))
    names_on_slide = [s.name for s in prs.slides[1].shapes]
    assert "SMARTART:flowchart" not in names_on_slide


def test_file_still_openable_after_injection(tmp_path):
    work = tmp_path / "op3.pptx"
    shutil.copy(SEED, work)
    spec = {
        "engine": "pptx_native",
        "layout_id": "process1",
        "data": {"items": [{"text": "Planning"}, {"text": "Memory"}, {"text": "Tool use"}]},
    }
    inject_smartart(
        pptx_path=work,
        marker_name="SMARTART:flowchart",
        slide_index_1based=2,
        spec=spec,
        carriers_dir=tmp_path / "carriers",
    )
    from pptx import Presentation
    prs = Presentation(str(work))
    assert len(prs.slides) == 3
```

- [ ] **Step 4: Run to verify it fails**

Run: `.venv/bin/pytest docs/spikes/2026-04-23-python-pptx-enrichment/tests/test_op3_inject_smartart.py -v`
Expected: ImportError on `op3_inject_smartart`.

- [ ] **Step 5: Implement op3**

```python
"""Op3: inject a pptx_native SmartArt carrier into a slide replacing a SMARTART marker.

Two-step: (1) rename the SMARTART marker shape to the pptx_native_placeholder_<N> convention
so assembler_patch.inject() can find it; (2) render the carrier and inject.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Union

from pptx import Presentation
from pptx.oxml.ns import qn

# Plugin import — relies on caller having added plugins/jack-tar-msft-smartart/src to sys.path.
# For the spike we add it unconditionally here to keep the prototype self-contained.
PLUGIN_SRC = Path(__file__).resolve().parents[3] / "plugins" / "jack-tar-msft-smartart" / "src"
if str(PLUGIN_SRC) not in sys.path:
    sys.path.insert(0, str(PLUGIN_SRC))

from engine import render as pptx_native_render  # type: ignore
from assembler_patch import inject as pptx_native_inject  # type: ignore


def _rename_marker_to_placeholder(pptx_path: Path, marker_name: str, slide_index_1based: int) -> None:
    prs = Presentation(str(pptx_path))
    slide = prs.slides[slide_index_1based - 1]
    placeholder_name = f"pptx_native_placeholder_{slide_index_1based}"
    renamed = False
    for shape in slide.shapes:
        if shape.name == marker_name:
            shape.name = placeholder_name
            renamed = True
            break
    if not renamed:
        raise LookupError(f"marker {marker_name!r} not found on slide {slide_index_1based}")
    prs.save(str(pptx_path))


def inject_smartart(
    pptx_path: Union[str, Path],
    marker_name: str,
    slide_index_1based: int,
    spec: dict[str, Any],
    carriers_dir: Union[str, Path],
) -> None:
    pptx_path = Path(pptx_path)
    carriers_dir = Path(carriers_dir)
    carriers_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: rename marker to the placeholder convention the injector expects
    _rename_marker_to_placeholder(pptx_path, marker_name, slide_index_1based)

    # Step 2: render carrier
    carrier_path = pptx_native_render(spec, carriers_dir)

    # Step 3: call inject. Request schema follows jack-tar convention:
    # {slide_number, carrier_path, placeholder_name}
    requests = [
        {
            "slide_number": slide_index_1based,
            "carrier_path": str(carrier_path),
            "placeholder_name": f"pptx_native_placeholder_{slide_index_1based}",
        }
    ]
    pptx_native_inject(str(pptx_path), requests)


if __name__ == "__main__":
    import json

    if len(sys.argv) != 6:
        print("usage: op3_inject_smartart.py <pptx> <marker_name> <slide_1based> <spec.json> <carriers_dir>")
        sys.exit(2)
    with open(sys.argv[4]) as f:
        spec = json.load(f)
    inject_smartart(sys.argv[1], sys.argv[2], int(sys.argv[3]), spec, sys.argv[5])
    print("ok")
```

**Verify assumption:** Before finalising, confirm `assembler_patch.inject()` actually accepts the `requests` schema used here. Read `plugins/jack-tar-msft-smartart/src/assembler_patch.py` — if the schema differs (e.g. it uses `carrier` instead of `carrier_path`, or numbers slides 0-based), update the prototype to match.

- [ ] **Step 6: Run the tests**

Run: `.venv/bin/pytest docs/spikes/2026-04-23-python-pptx-enrichment/tests/test_op3_inject_smartart.py -v`
Expected: 2 passed.

If tests fail because of schema mismatch on `inject()`, fix op3 to match the real API and rerun. A failure that reveals the real API is a spike win.

- [ ] **Step 7: Produce the single-op artefact**

```bash
cp docs/spikes/2026-04-23-python-pptx-enrichment/seed/seed.pptx \
   docs/spikes/2026-04-23-python-pptx-enrichment/outputs/after_op3.pptx
cat > /tmp/spike_spec.json <<'JSON'
{
  "engine": "pptx_native",
  "layout_id": "process1",
  "data": {"items": [{"text": "Planning"}, {"text": "Memory"}, {"text": "Tool use"}]}
}
JSON
.venv/bin/python docs/spikes/2026-04-23-python-pptx-enrichment/prototypes/op3_inject_smartart.py \
   docs/spikes/2026-04-23-python-pptx-enrichment/outputs/after_op3.pptx \
   SMARTART:flowchart \
   2 \
   /tmp/spike_spec.json \
   /tmp/spike_carriers
```

Expected: prints `ok`. The resulting .pptx contains `ppt/diagrams/` parts.

- [ ] **Step 8: Commit**

```bash
git add docs/spikes/2026-04-23-python-pptx-enrichment/prototypes/op3_inject_smartart.py \
        docs/spikes/2026-04-23-python-pptx-enrichment/tests/test_op3_inject_smartart.py \
        docs/spikes/2026-04-23-python-pptx-enrichment/outputs/after_op3.pptx
git commit -m "spike: op3 — inject pptx_native SmartArt into SMARTART marker"
```

---

## Task 7: Apply all three operations in sequence

The real bridge will apply multiple enrichments to the same deck. Prove that ordering doesn't break anything.

**Files:**
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops.pptx`

- [ ] **Step 1: Run op1 → op2 → op3 in sequence**

```bash
cp docs/spikes/2026-04-23-python-pptx-enrichment/seed/seed.pptx \
   docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops.pptx

# op1 — slide 3 background
.venv/bin/python docs/spikes/2026-04-23-python-pptx-enrichment/prototypes/op1_background.py \
   docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops.pptx \
   3 \
   docs/spikes/2026-04-23-python-pptx-enrichment/seed/placeholder.png \
   BG:dramatic-opening

# op2 — slide 1 image replacement
.venv/bin/python docs/spikes/2026-04-23-python-pptx-enrichment/prototypes/op2_replace_image_shape.py \
   docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops.pptx \
   IMAGE:agents-failing \
   docs/spikes/2026-04-23-python-pptx-enrichment/seed/placeholder.png

# op3 — slide 2 SmartArt injection
.venv/bin/python docs/spikes/2026-04-23-python-pptx-enrichment/prototypes/op3_inject_smartart.py \
   docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops.pptx \
   SMARTART:flowchart \
   2 \
   /tmp/spike_spec.json \
   /tmp/spike_carriers_all
```

Expected: each command prints `ok`. Final `all_ops.pptx` has:
- Slide 1: picture instead of IMAGE marker
- Slide 2: SmartArt diagram instead of SMARTART marker
- Slide 3: full-slide background, BG marker gone

- [ ] **Step 2: Commit**

```bash
git add docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops.pptx
git commit -m "spike: sequential op1+op2+op3 applied to seed deck"
```

---

## Task 8: Visual review — the only authoritative validation

Constitution Article 9.4 — visual review is mandatory.

**Files:**
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops.pdf`
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops_slides/`
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/results/powerpoint_gate.md`

- [ ] **Step 1: PowerPoint Mac open + save (forces SmartArt cache regen)**

Run the project's PowerPoint-driven conversion — it opens the file, forces a save, exports PDF:

```bash
tools/pptx_to_pdf.sh \
  docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops.pptx \
  docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops.pdf
```

Expected: PDF produced, no errors. If PowerPoint throws an error dialog (corrupt file, repair prompt, missing relationships), screenshot it and capture the message in `powerpoint_gate.md` — **this is a critical finding**.

- [ ] **Step 2: Rasterise PDF to per-slide PNGs**

```bash
mkdir -p docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops_slides
pdftoppm -r 96 \
  docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops.pdf \
  docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops_slides/slide \
  -png
ls docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops_slides/
```

Expected: `slide-1.png`, `slide-2.png`, `slide-3.png`.

- [ ] **Step 3: View every PNG with the Read tool**

Use the Read tool on each of:
- `docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops_slides/slide-1.png`
- `docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops_slides/slide-2.png`
- `docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops_slides/slide-3.png`

Observe for each slide:
- Does the operation's visible effect appear? (picture visible, SmartArt diagram rendered, background filled)
- Is the superpower's original theme / typography preserved?
- Any layout corruption — text squashed, placeholders empty, master elements missing?
- For slide 2: does the SmartArt show the 3 items in a Basic Process layout, or does PowerPoint show a broken/empty diagram frame?

- [ ] **Step 4: Write the PowerPoint gate report**

```markdown
# PowerPoint Mac gate

**Test deck:** outputs/all_ops.pptx
**Date:** 2026-04-23

## Open behaviour

- PowerPoint open: <clean / repair prompt / error dialog — screenshot if the latter>
- Save cycle: <succeeded / prompted / failed>
- PDF export: <succeeded / failed — error message>

## Per-slide visual observations

### Slide 1 (op2: IMAGE replaced with picture)
<observation>

### Slide 2 (op3: SMARTART injected)
<observation — diagram visible? items correct? styled correctly?>

### Slide 3 (op1: BG background applied)
<observation — background covers slide? text readable over it?>

## Verdict per op

- Op1 (background): PASS / FAIL / PARTIAL — <reason>
- Op2 (image replacement): PASS / FAIL / PARTIAL — <reason>
- Op3 (SmartArt injection): PASS / FAIL / PARTIAL — <reason>
```

- [ ] **Step 5: Commit**

```bash
git add docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops.pdf \
        docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops_slides/ \
        docs/spikes/2026-04-23-python-pptx-enrichment/results/powerpoint_gate.md
git commit -m "spike: visual review and PowerPoint Mac gate for sequenced ops"
```

---

## Task 9: Inspect the final OOXML

Even if the deck opens cleanly, check for leftover junk, broken relationships, or theme drift.

**Files:**
- Modify: `docs/spikes/2026-04-23-python-pptx-enrichment/results/ooxml_inspection.md`

- [ ] **Step 1: Dump the final .pptx structure**

```bash
unzip -l docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops.pptx \
  > /tmp/spike_zip_listing.txt
head -80 /tmp/spike_zip_listing.txt
```

Note: presence of `ppt/diagrams/*`, `ppt/media/*`, and that no part names collide. Paste the listing into the inspection doc.

- [ ] **Step 2: Verify slide 3's `<p:bg>` element**

```bash
.venv/bin/python - <<'PY'
from zipfile import ZipFile
from lxml import etree
with ZipFile("docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops.pptx") as z:
    xml = z.read("ppt/slides/slide3.xml")
root = etree.fromstring(xml)
ns = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
bg = root.find(".//p:cSld/p:bg", ns)
print(etree.tostring(bg, pretty_print=True).decode() if bg is not None else "NO <p:bg> FOUND")
PY
```

- [ ] **Step 3: Verify slide 2 has a graphicFrame referencing a diagram**

```bash
.venv/bin/python - <<'PY'
from zipfile import ZipFile
from lxml import etree
with ZipFile("docs/spikes/2026-04-23-python-pptx-enrichment/outputs/all_ops.pptx") as z:
    xml = z.read("ppt/slides/slide2.xml")
root = etree.fromstring(xml)
ns = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "dgm": "http://schemas.openxmlformats.org/drawingml/2006/diagram",
}
frames = root.findall(".//p:graphicFrame", ns)
print(f"graphicFrames on slide 2: {len(frames)}")
for fr in frames:
    dataModel = fr.find(".//dgm:relIds", ns)
    print(etree.tostring(dataModel, pretty_print=True).decode() if dataModel is not None else "no dgm:relIds")
PY
```

Expected: at least one graphicFrame with a `<dgm:relIds>` element referencing layout/data/colors/quickStyle rIds.

- [ ] **Step 4: Append findings to inspection doc**

Append to `docs/spikes/2026-04-23-python-pptx-enrichment/results/ooxml_inspection.md`:

```markdown
## Post-op inspection — all_ops.pptx

### Zip listing (excerpt)
<paste or summarise>

### Slide 3 <p:bg>
<paste the XML or note NOT PRESENT>

### Slide 2 graphicFrame
<paste the XML, note rId values>

### Anomalies / concerns
<anything surprising>
```

- [ ] **Step 5: Commit**

```bash
git add docs/spikes/2026-04-23-python-pptx-enrichment/results/ooxml_inspection.md
git commit -m "spike: OOXML post-op inspection"
```

---

## Task 10: Findings JSON (machine-readable)

**Files:**
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/results/findings.json`

- [ ] **Step 1: Write the findings file**

Hand-write based on test results + PowerPoint gate:

```json
{
  "spike": "python-pptx-enrichment",
  "date": "2026-04-23",
  "seed_source": "<spike-1-variant-c | hand-built-fallback>",
  "python_pptx_version": "<from Task 3 output>",
  "operations": [
    {
      "id": "op1_background",
      "tests_pass": true,
      "powerpoint_open": true,
      "visual_pass": true,
      "notes": "<one-liner>"
    },
    {
      "id": "op2_replace_image",
      "tests_pass": true,
      "powerpoint_open": true,
      "visual_pass": true,
      "notes": ""
    },
    {
      "id": "op3_inject_smartart",
      "tests_pass": true,
      "powerpoint_open": true,
      "visual_pass": true,
      "notes": ""
    }
  ],
  "sequenced_apply": {
    "tests_pass": true,
    "powerpoint_open": true,
    "visual_pass": true
  },
  "decision": "<go | go-with-adjustments | pivot | no-go>"
}
```

- [ ] **Step 2: Commit**

```bash
git add docs/spikes/2026-04-23-python-pptx-enrichment/results/findings.json
git commit -m "spike: machine-readable findings for enrichment operations"
```

---

## Task 11: Findings README and decision gate

**Files:**
- Create: `docs/spikes/2026-04-23-python-pptx-enrichment/README.md`

- [ ] **Step 1: Write the findings report**

```markdown
# Spike: python-pptx editing of /pptx superpower output — Findings

**Date:** 2026-04-23
**Related:** [docs/superpowers/specs/2026-04-22-superpower-bridge-design.md](../../superpowers/specs/2026-04-22-superpower-bridge-design.md), GitHub issue #53
**Seed source:** <Spike 1 Variant C output | hand-built fallback>

## Question

Can python-pptx and the existing pptx_native injection module reliably apply three enrichment operations to a .pptx produced by the `/pptx` superpower, producing a file that opens cleanly in PowerPoint Mac?

- **Op1** — set slide background to an AI-generated image
- **Op2** — replace a named shape (`IMAGE:*`) with an embedded picture at the same position
- **Op3** — graft a pptx_native SmartArt diagram into a slide, replacing a `SMARTART:*` marker

## Procedure

1. A seed deck with three named markers was produced (Task 2 — preferred from Spike 1; fallback hand-built).
2. Three prototype scripts applied each op in isolation, validated by unit tests asserting OOXML-level structure (Tasks 4–6).
3. All three ops were then applied sequentially to a single copy of the seed (Task 7).
4. The final deck was opened in PowerPoint Mac, save-cycled, and exported to PDF (Task 8).
5. Every slide PNG was reviewed visually (Task 8 Step 3).
6. OOXML was inspected post-mutation for anomalies (Task 9).

## Results

### Unit tests

| Op | Tests | Pass |
|----|-------|------|
| Op1 background | 2 | <n> |
| Op2 image replacement | 2 | <n> |
| Op3 SmartArt injection | 2 | <n> |

### PowerPoint Mac gate

- Open behaviour: <clean / repair prompt / error>
- Save cycle: <...>
- PDF export: <...>

### Visual review

- Slide 1 (Op2): <pass/fail + description>
- Slide 2 (Op3): <pass/fail + description — SmartArt rendered? items visible? layout correct?>
- Slide 3 (Op1): <pass/fail + description>

### Critical issues encountered (if any)

- <e.g. "python-pptx 1.0.2's ImagePart.new() signature differs from expected — see op1_background.py for the adjustment">
- <e.g. "assembler_patch.inject() required the placeholder shape to have text content, not just a name — added text before injection">
- <e.g. "theme was lost on slide 3 after background application — root cause: python-pptx's save reformatted `<p:cSld>`">

## Python-pptx capability summary

| Operation | Covered by public API | Required XML surgery | Complexity |
|-----------|----------------------|----------------------|------------|
| Background image | <yes/no> | <description if yes> | <low/med/high> |
| Shape replacement with picture | <yes/no> | <description if yes> | <low/med/high> |
| SmartArt graft via assembler_patch | N/A (plugin-provided) | N/A | low — existing code worked as-is / required fixes |

## Decision

Choose ONE:

- [ ] **GO** — All three ops pass tests + PowerPoint gate + visual review. Prototypes are ready to migrate into `plugins/jack-tar-superpower-bridge/src/enrichment.py`. Bridge Phase 3 can be built as designed.

- [ ] **GO with adjustments** — Ops work but require scope changes or extra safety:
  - <e.g. "background application must strip existing `<p:bg>` first to avoid double-background conditions">
  - <e.g. "image replacement must preserve shape rotation/effects from the marker — add geometry copy for more than just left/top/w/h">
  - <e.g. "SmartArt injection requires the marker shape to be deleted explicitly before inject() rather than renamed">
  - Spec update ticket: <link>

- [ ] **PIVOT** — One or more ops do not work against /pptx-produced OOXML. Redesign required:
  - <describe which op failed and why>
  - <propose alternative — e.g. "use PptxGenJS on the Node side instead of python-pptx" or "wrap /pptx output in a jack-tar re-emit step">

- [ ] **NO-GO** — Structural incompatibility between /pptx output and the target enrichment toolchain. The bridge concept needs a different architecture. Blockers:
  - <list>

## Recommended next steps

<Concrete actions — e.g. "Update superpower-bridge spec Section 3.4 with the ImagePart.new() adjustment and document assembler_patch requirements for seed deck compatibility">
```

- [ ] **Step 2: Confirm decision with user**

Present the completed README. Ask: "Based on the observed results I've picked `<decision>`. Agree, or revise?"

Do not proceed to commit until the user confirms.

- [ ] **Step 3: Commit**

```bash
git add docs/spikes/2026-04-23-python-pptx-enrichment/README.md
git commit -m "spike: findings and decision gate for python-pptx enrichment ops"
```

- [ ] **Step 4: Close out**

If any op produced actionable spec updates, open a GitHub issue or file a PR amending `docs/superpowers/specs/2026-04-22-superpower-bridge-design.md`. If the decision is NO-GO, mark the spec with a `Status: Blocked by spike` banner.

---

## Self-review checklist (done after writing the plan — do not remove)

- [x] Every task has exact file paths
- [x] Every code step has full code — no placeholders
- [x] Every command has expected output stated
- [x] Visual review step present (Article 9.4)
- [x] PowerPoint Mac gate present (memory: reference_pptx_to_pdf)
- [x] OOXML inspection step (the deck opening is not enough)
- [x] Decision gate at end
- [x] No step forward-references undefined functions
- [x] Risks from the spec's "python-pptx + PptxGenJS OOXML divergence" row explicitly addressed in the PowerPoint gate + OOXML inspection
- [x] Spec requirements covered: background application (Task 4), image replacement (Task 5), SmartArt injection (Task 6), sequencing (Task 7), PowerPoint validation (Task 8), findings + decision (Task 11)

---

## Notes for the executor

**On the ImagePart.new() signature:** python-pptx versions vary. If Task 4 Step 4's discovery doesn't match the assumed `ImagePart.new(package, blob, content_type, ext)`, adjust the call — do not fudge it. The spike is a truth-test; the adjustment itself is a finding.

**On assembler_patch.inject():** Read the source before trusting the request schema in op3. If the schema in this plan is wrong, use the real one — and note the drift in the findings report.

**On theme preservation:** After every op, re-save the file in python-pptx. If the superpower's theme (colours, fonts) disappears or changes, that is a headline finding — do not quietly work around it.

**On falling back to the hand-built seed:** This is acceptable for the python-pptx-level questions, but it is a weaker test of /pptx/python-pptx compatibility than the Variant C deck. If you used the fallback, note that clearly in the findings and recommend re-running the spike after Spike 1 is done.
