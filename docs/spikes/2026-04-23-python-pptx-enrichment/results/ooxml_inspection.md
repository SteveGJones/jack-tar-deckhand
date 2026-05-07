# OOXML inspection notes

## python-pptx version

**1.0.2**

## Slide.background capabilities

`Slide.background` returns a `_Background` instance with only `.element` (the underlying `<p:bg>` XML element) and `.fill` (a `FillFormat` facade for solid/gradient/no-fill).

**The public API does NOT expose a picture-fill setter for slide backgrounds.** `FillFormat.blip_fill()` doesn't exist on `_Background.fill` (it only has `solid`, `gradient`, `patterned`, `background`).

Therefore op1 must do raw XML surgery:

1. Build an `<a:blipFill>` sub-tree with `<a:blip r:embed="rIdN">` referring to the image rId.
2. Wrap it in `<p:bg><p:bgPr>...</p:bgPr></p:bg>`.
3. Insert as the first child of `<p:cSld>` on the target slide (removing any existing `<p:bg>` first).

## Image part creation — correct API for python-pptx 1.0.2

```python
from pptx.parts.image import Image, ImagePart
from pptx.opc.constants import RELATIONSHIP_TYPE as RT

img = Image.from_file(image_path)                         # reads file, computes sha1, content_type
image_part = ImagePart.new(slide.part.package, img)       # reuses part if same sha1 already present
rid = slide.part.relate_to(image_part, RT.IMAGE)          # adds rels entry, returns rId
```

This is the same code path used internally by `slide.shapes.add_picture()`.

## Expected XML for image-filled background

```xml
<p:cSld>
  <p:bg>
    <p:bgPr>
      <a:blipFill dpi="0" rotWithShape="1">
        <a:blip r:embed="rIdN"/>
        <a:srcRect/>
        <a:stretch><a:fillRect/></a:stretch>
      </a:blipFill>
      <a:effectLst/>
    </p:bgPr>
  </p:bg>
  <p:spTree>...</p:spTree>
</p:cSld>
```

Plus one new entry in `ppt/slides/_rels/slideN.xml.rels` pointing at `../media/imageN.png`.

## Constants

- `CONTENT_TYPE.PNG = "image/png"`
- `CONTENT_TYPE.JPEG = "image/jpeg"`
- `RELATIONSHIP_TYPE.IMAGE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"`

## Seed provenance

The seed .pptx in `seed/seed.pptx` is a **direct copy of Spike 1 Variant A's output** — real PptxGenJS-produced OOXML. This is the highest-fidelity test available for python-pptx/PptxGenJS OOXML compatibility.

### Marker inventory on seed

| Slide | Marker name | Kind | Geometry (EMU: l,t,w,h) |
|-------|-------------|------|--------------------------|
| 1 | `BG:title-hero-dark-grid` | BG | 0, 0, 9144000, 5143500 (full slide) |
| 2 | `IMAGE:demo-vs-prod-split` | IMAGE | 5486400, 1143000, 3200400, 3200400 |
| 4 | `SMARTART:three-pillars-relationship` | SMARTART | 685800, 1463040, 7772400, 3017520 |
| 5 | `SMARTART:planning-replan-loop` | SMARTART | 5669280, 1143000, 3108960, 3200400 |
| 6 | `IMAGE:memory-layers-illustration` | IMAGE | 5669280, 1143000, 3108960, 3200400 |
| 7 | `SMARTART:tool-call-sequence` | SMARTART | 5669280, 1143000, 3108960, 3200400 |
| 8 | `BG:case-study-server-room` | BG | 0, 0, 9144000, 5143500 (full slide) |
| 9 | `IMAGE:case-study-dashboard` | IMAGE | 457200, 4023360, 8229600, 502920 |

Spike 2 prototypes target one of each kind:
- Op1 (background) — slide 1, `BG:title-hero-dark-grid`
- Op2 (image replacement) — slide 2, `IMAGE:demo-vs-prod-split`
- Op3 (SmartArt injection) — slide 4, `SMARTART:three-pillars-relationship`

### BG marker shape — note

Variant A's subagent rendered BG markers as full-slide rectangles, not the small corner labels specified in the brief. This is strictly better for op1 testing — we prove background application works when the marker footprint covers the whole slide (the maximum case).
