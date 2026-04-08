"""Post-assembly injection of pptx_native SmartArt into a host deck.

This module is the Python Stage 2 of the two-stage assembly described
in spec §3.4. Stage 1 is the PptxGenJS-based Node assembler
(`src/assembler/build_deck.js`), which builds the host .pptx with all
normal content — title, footer, body text, images — and places a
named placeholder rectangle on any slide that should host a
pptx_native SmartArt graphic.

Stage 2 (this module) runs after build_deck.js finishes. It:

  1. Opens the assembled host .pptx
  2. For each pptx_native entry in the SmartArt manifest:
     a. Opens the carrier .pptx produced by the engine
        (smartart_renderer's dispatch call)
     b. Extracts the four diagram parts from the carrier
     c. Finds the placeholder shape in the host slide by its name
     d. Captures the placeholder's offset + extents
     e. Allocates fresh rIds in the host slide's rels file
     f. Adds the four diagram parts to the host .pptx at a unique
        diagram-number (data1/data2/...) to avoid collision with
        existing diagrams
     g. Adds four content-type overrides to [Content_Types].xml
     h. Replaces the placeholder shape with a <p:graphicFrame>
        bound to the new rIds, inheriting the placeholder's xfrm

The host is modified in place. Slides with no pptx_native graphics
pass through untouched.

Spike 3 validated this pattern for a single diagram in a blank host
with no existing SmartArt. This module generalises to:

  - Hosts with existing diagrams (via diagram-number allocation)
  - Multiple pptx_native graphics per deck
  - Placeholder lookup by shape name rather than hardcoded coordinates
"""
from __future__ import annotations

import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants + regexes
# ---------------------------------------------------------------------------

PLACEHOLDER_NAME_PREFIX = "pptx_native_placeholder_"
"""Shape name prefix the JS assembler uses for pptx_native placeholder rects.

buildSmartArtSlide emits `pptx_native_placeholder_<slide_number>` as the
cNvPr name. This module looks for shapes matching that prefix to
identify placeholder targets for injection.
"""

_CONTENT_TYPE_OVERRIDES = [
    (
        "data",
        "application/vnd.openxmlformats-officedocument.drawingml.diagramData+xml",
    ),
    (
        "layout",
        "application/vnd.openxmlformats-officedocument.drawingml.diagramLayout+xml",
    ),
    (
        "quickStyle",
        "application/vnd.openxmlformats-officedocument.drawingml.diagramStyle+xml",
    ),
    (
        "colors",
        "application/vnd.openxmlformats-officedocument.drawingml.diagramColors+xml",
    ),
]

_REL_TYPES = {
    "data": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramData",
    "layout": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramLayout",
    "quickStyle": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramQuickStyle",
    "colors": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/diagramColors",
}


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class InjectionError(Exception):
    """Raised when the injection process cannot complete."""


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class InjectionRequest:
    """One pptx_native graphic to inject into the host.

    Attributes:
        slide_number: 1-based slide number in the host deck where the
            placeholder lives.
        carrier_pptx: Path to the pptx_native carrier file from which
            the diagram parts will be extracted.
        placeholder_name: Shape name to look for in the host slide's
            spTree. Defaults to PLACEHOLDER_NAME_PREFIX + slide_number.
    """

    slide_number: int
    carrier_pptx: Path
    placeholder_name: str | None = None

    def resolved_placeholder_name(self) -> str:
        if self.placeholder_name:
            return self.placeholder_name
        return f"{PLACEHOLDER_NAME_PREFIX}{self.slide_number}"


@dataclass
class InjectionResult:
    """Result of a single graphic injection."""

    slide_number: int
    diagram_number: int
    rids_allocated: list[str]
    offset: tuple[int, int]  # EMU
    extents: tuple[int, int]  # EMU


# ---------------------------------------------------------------------------
# Helpers — parsing + allocation
# ---------------------------------------------------------------------------

def _extract_placeholder_xfrm(
    slide_xml: str, placeholder_name: str
) -> tuple[tuple[int, int], tuple[int, int]] | None:
    """Find a <p:sp> by cNvPr name and return its (offset, extents) in EMU.

    Returns None if no shape with that name exists or its xfrm cannot
    be parsed.
    """
    # Find the <p:sp> element containing our placeholder name. We do
    # this by locating the cNvPr with name=<placeholder_name>, then
    # walking backwards to the enclosing <p:sp> start tag.
    name_pattern = re.compile(
        rf'<p:cNvPr[^>]*\bname="{re.escape(placeholder_name)}"'
    )
    m = name_pattern.search(slide_xml)
    if not m:
        return None

    # Walk backwards to find the enclosing <p:sp> start.
    sp_start = slide_xml.rfind("<p:sp>", 0, m.start())
    if sp_start == -1:
        return None

    sp_end = slide_xml.find("</p:sp>", m.end())
    if sp_end == -1:
        return None

    sp_xml = slide_xml[sp_start : sp_end + len("</p:sp>")]

    off_match = re.search(r'<a:off x="(\d+)" y="(\d+)"/>', sp_xml)
    ext_match = re.search(r'<a:ext cx="(\d+)" cy="(\d+)"/>', sp_xml)

    if off_match and ext_match:
        return (
            (int(off_match.group(1)), int(off_match.group(2))),
            (int(ext_match.group(1)), int(ext_match.group(2))),
        )
    return None


def _remove_placeholder_sp(slide_xml: str, placeholder_name: str) -> str:
    """Return slide_xml with the <p:sp> whose cNvPr name matches removed."""
    name_pattern = re.compile(
        rf'<p:cNvPr[^>]*\bname="{re.escape(placeholder_name)}"'
    )
    m = name_pattern.search(slide_xml)
    if not m:
        return slide_xml

    sp_start = slide_xml.rfind("<p:sp>", 0, m.start())
    if sp_start == -1:
        return slide_xml
    sp_end = slide_xml.find("</p:sp>", m.end())
    if sp_end == -1:
        return slide_xml

    return slide_xml[:sp_start] + slide_xml[sp_end + len("</p:sp>") :]


def _allocate_rids(existing_rels_xml: str, count: int) -> list[str]:
    """Allocate `count` fresh rIds not currently in use."""
    existing = {int(m) for m in re.findall(r'Id="rId(\d+)"', existing_rels_xml)}
    next_id = (max(existing) + 1) if existing else 1
    return [f"rId{next_id + i}" for i in range(count)]


def _next_free_diagram_number(host_names: set[str]) -> int:
    """Pick the next available diagram file number in the host.

    The host may already contain data1.xml / layout1.xml / etc. from
    other SmartArt graphics. This function finds the smallest N
    (starting at 1) such that `ppt/diagrams/data{N}.xml` is NOT
    already present in the host.
    """
    for n in range(1, 10000):  # sane upper bound
        if f"ppt/diagrams/data{n}.xml" not in host_names:
            return n
    raise InjectionError("exhausted diagram numbering at 10000")


def _next_free_shape_id(slide_xml: str) -> int:
    """Return the next unused cNvPr id in the slide (1 + max existing)."""
    ids = [int(m) for m in re.findall(r'<p:cNvPr id="(\d+)"', slide_xml)]
    return (max(ids) + 1) if ids else 1


# ---------------------------------------------------------------------------
# Core injection
# ---------------------------------------------------------------------------

def _build_graphic_frame(
    shape_id: int,
    name: str,
    offset: tuple[int, int],
    extents: tuple[int, int],
    rids: dict[str, str],
) -> str:
    """Build a <p:graphicFrame> element bound to the given rIds."""
    x, y = offset
    cx, cy = extents
    return (
        "<p:graphicFrame>"
        "<p:nvGraphicFramePr>"
        f'<p:cNvPr id="{shape_id}" name="{name}"/>'
        '<p:cNvGraphicFramePr>'
        '<a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'noChangeAspect="1"/>'
        "</p:cNvGraphicFramePr>"
        "<p:nvPr/>"
        "</p:nvGraphicFramePr>"
        "<p:xfrm>"
        f'<a:off xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        f'x="{x}" y="{y}"/>'
        f'<a:ext xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        f'cx="{cx}" cy="{cy}"/>'
        "</p:xfrm>"
        '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/diagram">'
        '<dgm:relIds xmlns:dgm="http://schemas.openxmlformats.org/drawingml/2006/diagram" '
        f'r:dm="{rids["data"]}" r:lo="{rids["layout"]}" '
        f'r:qs="{rids["quickStyle"]}" r:cs="{rids["colors"]}"/>'
        "</a:graphicData>"
        "</a:graphic>"
        "</p:graphicFrame>"
    )


def _patch_slide_rels(
    rels_xml: str, rids: dict[str, str], diagram_number: int
) -> str:
    """Insert four new Relationship entries before </Relationships>."""
    new_rels = "".join(
        f'<Relationship Id="{rids[part]}" '
        f'Type="{_REL_TYPES[part]}" '
        f'Target="../diagrams/{part_to_filename(part, diagram_number)}"/>'
        for part, _type in _REL_TYPES.items()
    )
    if "</Relationships>" not in rels_xml:
        raise InjectionError("slide rels file has no </Relationships>")
    return rels_xml.replace("</Relationships>", new_rels + "</Relationships>")


def _patch_content_types(
    ct_xml: str, diagram_number: int
) -> str:
    """Insert four content-type overrides for the new diagram parts."""
    overrides = "".join(
        f'<Override PartName="/ppt/diagrams/{part_to_filename(part, diagram_number)}" '
        f'ContentType="{ctype}"/>'
        for part, ctype in _CONTENT_TYPE_OVERRIDES
    )
    if "</Types>" not in ct_xml:
        raise InjectionError("[Content_Types].xml has no </Types>")
    return ct_xml.replace("</Types>", overrides + "</Types>")


def part_to_filename(part: str, diagram_number: int) -> str:
    """Map a part kind + diagram number to the canonical filename.

    ('data', 1)       -> 'data1.xml'
    ('quickStyle', 3) -> 'quickStyle3.xml'
    """
    return f"{part}{diagram_number}.xml"


def _read_carrier_diagram_parts(carrier_pptx: Path) -> dict[str, bytes]:
    """Read the four diagram parts from a pptx_native carrier .pptx."""
    if not carrier_pptx.exists():
        raise InjectionError(f"carrier .pptx missing: {carrier_pptx}")
    parts: dict[str, bytes] = {}
    with zipfile.ZipFile(carrier_pptx, "r") as z:
        for part in ("data", "layout", "quickStyle", "colors"):
            name = f"ppt/diagrams/{part}1.xml"
            try:
                parts[part] = z.read(name)
            except KeyError:
                raise InjectionError(
                    f"carrier {carrier_pptx.name} missing {name}"
                )
    return parts


def inject(
    host_pptx: Path,
    requests: list[InjectionRequest],
) -> list[InjectionResult]:
    """Graft pptx_native SmartArt graphics into a host .pptx in place.

    Args:
        host_pptx: Path to the host .pptx file. Modified in place.
        requests: One InjectionRequest per graphic to inject.

    Returns:
        List of InjectionResult, one per successful injection, in the
        same order as `requests`.

    Raises:
        InjectionError: If any injection fails. The host file is left
            in whatever state the partial injection reached — callers
            should keep a backup if rollback matters.
    """
    host_pptx = Path(host_pptx)
    if not host_pptx.exists():
        raise InjectionError(f"host .pptx missing: {host_pptx}")

    results: list[InjectionResult] = []

    # Strategy: read the whole host zip into memory, apply all
    # mutations, then write a fresh zip. This gives us atomic
    # "all or nothing" semantics within a single call.
    with zipfile.ZipFile(host_pptx, "r") as zin:
        contents: dict[str, bytes] = {
            info.filename: zin.read(info.filename) for info in zin.infolist()
        }
        # Preserve ZipInfo for each original entry so we keep dates/compression
        infos: dict[str, zipfile.ZipInfo] = {
            info.filename: info for info in zin.infolist()
        }

    names = set(contents.keys())

    for req in requests:
        slide_xml_name = f"ppt/slides/slide{req.slide_number}.xml"
        slide_rels_name = f"ppt/slides/_rels/slide{req.slide_number}.xml.rels"
        if slide_xml_name not in contents:
            raise InjectionError(
                f"slide {req.slide_number} not found in host .pptx"
            )
        if slide_rels_name not in contents:
            raise InjectionError(
                f"slide {req.slide_number} rels not found in host .pptx"
            )

        slide_xml = contents[slide_xml_name].decode("utf-8")
        slide_rels_xml = contents[slide_rels_name].decode("utf-8")
        ct_xml = contents["[Content_Types].xml"].decode("utf-8")

        placeholder_name = req.resolved_placeholder_name()
        xfrm = _extract_placeholder_xfrm(slide_xml, placeholder_name)
        if xfrm is None:
            raise InjectionError(
                f"no placeholder shape with name {placeholder_name!r} "
                f"found in slide {req.slide_number}"
            )
        offset, extents = xfrm

        # Read carrier diagram parts
        carrier_parts = _read_carrier_diagram_parts(req.carrier_pptx)

        # Allocate diagram number + rIds
        diagram_number = _next_free_diagram_number(names)
        rids_list = _allocate_rids(slide_rels_xml, count=4)
        rids = {
            "data": rids_list[0],
            "layout": rids_list[1],
            "quickStyle": rids_list[2],
            "colors": rids_list[3],
        }

        # Patch slide XML: remove placeholder, append graphicFrame
        slide_without_placeholder = _remove_placeholder_sp(slide_xml, placeholder_name)
        shape_id = _next_free_shape_id(slide_without_placeholder)
        graphic_frame = _build_graphic_frame(
            shape_id=shape_id,
            name=f"Diagram {diagram_number}",
            offset=offset,
            extents=extents,
            rids=rids,
        )
        # Insert before </p:spTree>
        if "</p:spTree>" not in slide_without_placeholder:
            raise InjectionError(
                f"slide {req.slide_number} has no </p:spTree>"
            )
        new_slide_xml = slide_without_placeholder.replace(
            "</p:spTree>", graphic_frame + "</p:spTree>"
        )

        # Patch slide rels
        new_slide_rels_xml = _patch_slide_rels(slide_rels_xml, rids, diagram_number)

        # Patch content types
        new_ct_xml = _patch_content_types(ct_xml, diagram_number)

        # Write everything back into contents map
        contents[slide_xml_name] = new_slide_xml.encode("utf-8")
        contents[slide_rels_name] = new_slide_rels_xml.encode("utf-8")
        contents["[Content_Types].xml"] = new_ct_xml.encode("utf-8")

        for part, part_bytes in carrier_parts.items():
            filename = f"ppt/diagrams/{part_to_filename(part, diagram_number)}"
            contents[filename] = part_bytes
            names.add(filename)

        results.append(InjectionResult(
            slide_number=req.slide_number,
            diagram_number=diagram_number,
            rids_allocated=rids_list,
            offset=offset,
            extents=extents,
        ))

    # Write the modified zip back over the host
    tmp_path = host_pptx.with_suffix(".tmp.pptx")
    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in contents.items():
            info = infos.get(name)
            if info is not None:
                zout.writestr(info, data)
            else:
                # New file — use default ZipInfo
                zout.writestr(name, data)
    tmp_path.replace(host_pptx)

    return results
