"""pptx_native engine entry point.

`render(spec, output_dir)` is the single function this module exposes.
Given a spec describing a graphic type and its extracted data, it
produces a complete editable `.pptx` file at `output_dir` containing
exactly one slide with the SmartArt graphic.

Architecture (Phase 8):

  1. Look up the target layout in the catalog via graphic_type
  2. Dispatch to the generic builder matching the layout's data_shape
     (flat_list / hierarchical / picture). Builder returns data1.xml bytes.
  3. Read layout.xml, quickStyle.xml, colors.xml from the layout's
     extracted fixture directory (tests/fixtures/smartart_layouts/<id>/)
  4. Build a minimal carrier .pptx from scratch containing one slide
     with the four diagram parts and a <p:graphicFrame> reference.

The engine no longer unzips a seed .pptx at runtime — it reads the
three layout XML files directly from the extracted fixtures and
constructs the carrier package programmatically. This is the
"unwrapped" architecture: no binary seed files, just plain XML +
Python.
"""
from __future__ import annotations

import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.smartart_pptx_native import builders
from src.smartart_pptx_native.layouts import catalog


class RenderError(Exception):
    """Raised when the engine cannot produce an editable output."""


@dataclass
class RenderResult:
    output_path: Path
    layout_id: str
    layout_uri: str
    node_count: int
    engine: str = "pptx_native"


# ---------------------------------------------------------------------------
# Minimal carrier .pptx template parts
# ---------------------------------------------------------------------------
# These are the fixed parts of a one-slide .pptx that contain no
# layout-specific content. They're generic PowerPoint scaffolding:
# content types, package rels, presentation.xml, theme, slide master,
# slide layout, and the single slide that references a diagram.
#
# Everything layout-specific (layout.xml, quickStyle.xml, colors.xml,
# data1.xml) is inserted at render time from the extracted fixtures +
# the generic builder output.

_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/><Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/><Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/><Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/><Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/><Override PartName="/ppt/diagrams/data1.xml" ContentType="application/vnd.openxmlformats-officedocument.drawingml.diagramData+xml"/><Override PartName="/ppt/diagrams/layout1.xml" ContentType="application/vnd.openxmlformats-officedocument.drawingml.diagramLayout+xml"/><Override PartName="/ppt/diagrams/quickStyle1.xml" ContentType="application/vnd.openxmlformats-officedocument.drawingml.diagramStyle+xml"/><Override PartName="/ppt/diagrams/colors1.xml" ContentType="application/vnd.openxmlformats-officedocument.drawingml.diagramColors+xml"/></Types>"""

_ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>"""

_PRESENTATION_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:sldIdLst><p:sldId id="256" r:id="rId2"/></p:sldIdLst><p:sldSz cx="12192000" cy="6858000" type="screen16x9"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>"""

_PRESENTATION_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/></Relationships>"""

_SLIDE_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr><p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="4" name="Diagram 1"/><p:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></p:cNvGraphicFramePr><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="914400" y="914400"/><a:ext cx="10363200" cy="5029200"/></p:xfrm><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/diagram"><dgm:relIds xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" r:dm="rId2" r:lo="rId3" r:qs="rId4" r:cs="rId5"/></a:graphicData></a:graphic></p:graphicFrame></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"""

_SLIDE_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramData" Target="../diagrams/data1.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramLayout" Target="../diagrams/layout1.xml"/><Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramQuickStyle" Target="../diagrams/quickStyle1.xml"/><Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramColors" Target="../diagrams/colors1.xml"/></Relationships>"""

_THEME_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme"><a:themeElements><a:clrScheme name="Office"><a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1><a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="44546A"/></a:dk2><a:lt2><a:srgbClr val="E7E6E6"/></a:lt2><a:accent1><a:srgbClr val="5B9BD5"/></a:accent1><a:accent2><a:srgbClr val="ED7D31"/></a:accent2><a:accent3><a:srgbClr val="A5A5A5"/></a:accent3><a:accent4><a:srgbClr val="FFC000"/></a:accent4><a:accent5><a:srgbClr val="4472C4"/></a:accent5><a:accent6><a:srgbClr val="70AD47"/></a:accent6><a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme><a:fontScheme name="Office"><a:majorFont><a:latin typeface="Calibri Light"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont><a:minorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme><a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="6350" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="800000"/></a:ln><a:ln w="12700" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="800000"/></a:ln><a:ln w="19050" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/><a:miter lim="800000"/></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst><a:outerShdw blurRad="57150" dist="19050" dir="5400000" algn="ctr" rotWithShape="0"><a:srgbClr val="000000"><a:alpha val="63000"/></a:srgbClr></a:outerShdw></a:effectLst></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>"""

_SLIDE_MASTER_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst></p:sldMaster>"""

_SLIDE_MASTER_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>"""

_SLIDE_LAYOUT_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>"""

_SLIDE_LAYOUT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>"""


def _count_data_nodes(data_xml: bytes) -> int:
    """Count the untyped <dgm:pt> elements (regular + asst data nodes)."""
    import re
    text = data_xml.decode("utf-8")
    total = 0
    for m in re.finditer(r'<dgm:pt modelId="[^"]+"([^>]*)>', text):
        attrs = m.group(1)
        if "type=" not in attrs:
            total += 1
        elif 'type="asst"' in attrs:
            total += 1
    return total


def render(
    spec: dict[str, Any],
    output_dir: str | Path,
    output_name: str | None = None,
) -> RenderResult:
    """Render a pptx_native SmartArt graphic to an editable .pptx file."""
    if "graphic_type" not in spec:
        raise RenderError("spec is missing required key 'graphic_type'")
    if "data" not in spec:
        raise RenderError("spec is missing required key 'data'")

    graphic_type = spec["graphic_type"]

    # Allow caller to request a specific layout_id explicitly; otherwise
    # use the catalog's first match for the graphic_type.
    layout_id = spec.get("layout_id")
    if layout_id is None:
        layout_id = catalog.get_layout_id_for_graphic_type(graphic_type)
    if layout_id is None:
        raise RenderError(
            f"no pptx_native layout supports graphic_type {graphic_type!r}. "
            f"The extractor should not have routed this to pptx_native."
        )

    try:
        entry = catalog.get_entry(layout_id)
    except catalog.CatalogError as exc:
        raise RenderError(str(exc)) from exc

    layout_dir = catalog.resolve_layout_dir(entry)
    if not layout_dir.exists():
        raise RenderError(
            f"layout_dir missing for {layout_id!r}: {layout_dir}. "
            f"Run tools/extract_smartart_layouts.py to populate fixtures."
        )

    # Read the three opaque XML parts from the fixture directory
    try:
        layout_xml = (layout_dir / "layout.xml").read_bytes()
        quickstyle_xml = (layout_dir / "quickStyle.xml").read_bytes()
        colors_xml = (layout_dir / "colors.xml").read_bytes()
    except FileNotFoundError as exc:
        raise RenderError(
            f"layout directory {layout_dir} is missing a required file: {exc}"
        ) from exc

    # Dispatch to the generic builder for this data_shape
    data_shape = entry["data_shape"]
    image_refs = []  # populated only by the picture builder
    try:
        build_result = builders.build(data_shape, spec["data"], entry)
        # The picture builder returns (bytes, list[ImageRef]) when images
        # are present; all other builders return plain bytes.
        if isinstance(build_result, tuple):
            data_xml, image_refs = build_result
        else:
            data_xml = build_result
    except builders.UnsupportedDataShapeError as exc:
        raise RenderError(str(exc)) from exc

    # Compute output path
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if output_name is None:
        slide_n = spec.get("slide_number")
        if slide_n is not None:
            output_name = f"pptx_native_{layout_id}_slide{slide_n}.pptx"
        else:
            output_name = f"pptx_native_{layout_id}.pptx"
    output_path = output_dir / output_name
    if output_path.exists():
        output_path.unlink()

    # Build content types — may need image type extensions for picture layouts
    content_types = _CONTENT_TYPES
    if image_refs:
        # Add image content type defaults if not already present
        import re
        image_extensions = {ref.media_name.rsplit(".", 1)[-1].lower() for ref in image_refs}
        extra_types = []
        for ext in sorted(image_extensions):
            mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "gif": "image/gif", "webp": "image/webp", "svg": "image/svg+xml"}.get(ext, f"image/{ext}")
            if f'Extension="{ext}"' not in content_types:
                extra_types.append(f'<Default Extension="{ext}" ContentType="{mime}"/>')
        if extra_types:
            # Insert before closing </Types>
            content_types = content_types.replace(
                "</Types>", "".join(extra_types) + "</Types>"
            )

    # Build the carrier .pptx from scratch — no seed file needed
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
        # Package parts
        zout.writestr("[Content_Types].xml", content_types)
        zout.writestr("_rels/.rels", _ROOT_RELS)
        zout.writestr("ppt/presentation.xml", _PRESENTATION_XML)
        zout.writestr("ppt/_rels/presentation.xml.rels", _PRESENTATION_RELS)
        zout.writestr("ppt/theme/theme1.xml", _THEME_XML)
        zout.writestr("ppt/slideMasters/slideMaster1.xml", _SLIDE_MASTER_XML)
        zout.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", _SLIDE_MASTER_RELS)
        zout.writestr("ppt/slideLayouts/slideLayout1.xml", _SLIDE_LAYOUT_XML)
        zout.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", _SLIDE_LAYOUT_RELS)
        zout.writestr("ppt/slides/slide1.xml", _SLIDE_XML)
        zout.writestr("ppt/slides/_rels/slide1.xml.rels", _SLIDE_RELS)
        # Diagram parts — layout-specific
        zout.writestr("ppt/diagrams/data1.xml", data_xml)
        zout.writestr("ppt/diagrams/layout1.xml", layout_xml)
        zout.writestr("ppt/diagrams/quickStyle1.xml", quickstyle_xml)
        zout.writestr("ppt/diagrams/colors1.xml", colors_xml)
        # NB: drawing1.xml deliberately NOT written — PowerPoint regenerates
        # the presentation tree from layout1.xml on first open.

        # Picture SmartArt: embed image files + diagram data rels
        if image_refs:
            # Write each image file into ppt/media/
            for ref in image_refs:
                if ref.image_path.exists():
                    zout.write(str(ref.image_path), f"ppt/media/{ref.media_name}")

            # Write ppt/diagrams/_rels/data1.xml.rels with image relationships
            rels_parts = [
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
            ]
            for ref in image_refs:
                rels_parts.append(
                    f'<Relationship Id="{ref.rel_id}" '
                    f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
                    f'Target="../media/{ref.media_name}"/>'
                )
            rels_parts.append("</Relationships>")
            zout.writestr(
                "ppt/diagrams/_rels/data1.xml.rels",
                "".join(rels_parts),
            )

    return RenderResult(
        output_path=output_path,
        layout_id=layout_id,
        layout_uri=entry["layout_uri"],
        node_count=_count_data_nodes(data_xml),
    )
