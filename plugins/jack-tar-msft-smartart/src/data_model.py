"""XML construction primitives for ppt/diagrams/data1.xml.

These are the building blocks every layout module composes to emit
its data1.xml bytes. The primitives are layout-agnostic — the
flat-list layouts (process1, cycle2, basicTimeline1) and the
hierarchical layout (orgChart1) all use the same points and
connections, differing only in HOW they traverse their input data
to emit them.

The primitives were empirically validated across four spikes:

  Spike 1 — process1 (lin algorithm)
  Spike 2 — cycle2  (cycle algorithm)
  Spike 3 — injection into a blank host
  Spike 4 — orgChart1 (hierChild algorithm) + assistant nodes

The surprising finding from spike 4 is that PowerPoint distinguishes
assistant nodes (which render sideways from their parent) from
regular subordinates (which render below) purely by the `type="asst"`
attribute on the destination point. The connection structure is
identical for both kinds. So `make_node_pt` takes a single
`is_asst=False` parameter and everything else in the data model is
unchanged.

Another finding across all four spikes: the minimal data model is
sufficient. PowerPoint regenerates the presentation tree (type="pres"
points + presOf / presParOf connections) from layout1.xml on first
open. The engine emits the doc point, data nodes, parTrans/sibTrans
pairs, and untyped cxn elements — nothing else.
"""
from __future__ import annotations

import uuid
import xml.sax.saxutils as saxutils

NSMAP = {
    "dgm": "http://schemas.openxmlformats.org/drawingml/2006/diagram",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def gid() -> str:
    """Return a brace-wrapped uppercase GUID, matching Mac PowerPoint's format.

    Mac PowerPoint emits modelIds like `{746B57E5-417C-5B4A-85C3-56BF87D83488}`.
    Other OOXML producers use unbraced lowercase, which PowerPoint accepts on
    read. We emit the brace-wrapped form to minimise diffs against
    PowerPoint-authored baselines (useful during manual-gate verification).
    """
    return "{" + str(uuid.uuid4()).upper() + "}"


def build_doc_prset(
    layout_uri: str,
    qs_type_id: str = "urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1",
    cs_type_id: str = "urn:microsoft.com/office/officeart/2005/8/colors/accent1_2",
) -> str:
    """Build the prSet attribute string for the doc point.

    The doc point's <dgm:prSet> carries the layout binding — three URIs
    telling PowerPoint which layout1.xml, quickStyle1.xml, and colors1.xml
    to apply to this diagram. These URIs are extracted verbatim from the
    seed during engine startup (they're authoritative for the seed) and
    must match what the seed's layout1.xml/quickStyle1.xml/colors1.xml
    internally declare.

    Default qs/cs URIs are the "simple1 / accent1_2" pair PowerPoint Mac
    picks when you first insert a SmartArt graphic via the menu. Most
    seeds will use these defaults.
    """
    return (
        f'loTypeId="{layout_uri}" '
        f'loCatId="" '
        f'qsTypeId="{qs_type_id}" '
        f'qsCatId="simple" '
        f'csTypeId="{cs_type_id}" '
        f'csCatId="accent1" '
        f'phldr="0"'
    )


def make_doc_pt(doc_id: str, prset_attrs: str) -> str:
    """Return the XML fragment for the document (root) point.

    Every data1.xml has exactly one doc point. It carries the layout
    binding in its prSet and has no text body.
    """
    return (
        f'<dgm:pt modelId="{doc_id}" type="doc">'
        f"<dgm:prSet {prset_attrs}/>"
        f"<dgm:spPr/>"
        f"</dgm:pt>"
    )


def make_node_pt(
    node_id: str,
    text: str,
    is_asst: bool = False,
    image_rel_id: str | None = None,
    image_fill_mode: str = "fit",
    image_aspect_ratio: float | None = None,
    box_aspect_ratio: float = 0.5,
) -> str:
    """Return the XML fragment for a data node (regular or assistant).

    Args:
        node_id: modelId for this point. Use gid().
        text: The visible label text. XML-escaped automatically.
        is_asst: If True, emits `type="asst"` — PowerPoint renders this
            node sideways from its parent (assistant). If False, the
            node has no type attribute and renders as a regular
            subordinate below its parent.
        image_rel_id: If set (e.g. "rId1"), emits a `<a:blipFill>` inside
            `<dgm:spPr>` binding this node to an image via an r:embed
            relationship. The relationship must exist in
            `ppt/diagrams/_rels/data1.xml.rels` pointing at a media file
            in `ppt/media/`. Used by Picture SmartArt layouts (pList1 etc.)
            where each node has an associated image.
            If None, emits `<dgm:spPr/>` (empty — no image binding).
    """
    type_attr = ' type="asst"' if is_asst else ""
    escaped = saxutils.escape(text)

    if image_rel_id:
        # Picture SmartArt image binding — validated by spike 6 inspection
        # of the SDK's 5.9.3.7(unfinished).pptx fixture. The pattern is:
        #   <dgm:spPr bwMode="auto">
        #     <a:blipFill rotWithShape="0">
        #       <a:blip r:embed="rIdN"/>
        #       <a:tile tx="0" ty="0" sx="100000" sy="100000" flip="none" algn="tl"/>
        #     </a:blipFill>
        #   </dgm:spPr>
        # Picture SmartArt image binding with configurable fill mode.
        #
        # Four modes available (OOXML a:blipFill):
        #   "crop"    — scale to cover the box, crop overflow (preserves
        #               aspect ratio). PowerPoint's "Fill" mode. Best default.
        #   "stretch" — stretch to exactly fill the box (may distort aspect ratio)
        #   "center"  — place image at original size, centered in the box
        #   "tile"    — tile the image across the shape surface
        blip_elem = f'<a:blip xmlns:r="{NSMAP["r"]}" r:embed="{image_rel_id}"/>'

        # Fill mode for Picture SmartArt images. Reverse-engineered from
        # PowerPoint Mac's "Format Shape → Picture → Fit/Fill" output.
        #
        # PowerPoint uses:
        #   dpi="0" rotWithShape="0" + <a:srcRect/> as common attributes
        #   Positive fillRect insets = FIT (letterbox, preserve aspect)
        #   Negative fillRect insets = FILL (scale to cover, crop overflow)
        #   Zero insets = STRETCH (distorts aspect ratio)
        #
        # Inset calculation requires image aspect ratio vs box aspect ratio.
        # image_aspect_ratio = width/height of the source image
        # box_aspect_ratio = width/height of the target layout shape

        blip_elem = f'<a:blip xmlns:r="{NSMAP["r"]}" r:embed="{image_rel_id}"/>'

        if image_fill_mode == "stretch":
            fill_xml = f'{blip_elem}<a:stretch><a:fillRect/></a:stretch>'
            sp_pr = f'<dgm:spPr bwMode="auto"><a:blipFill rotWithShape="0">{fill_xml}</a:blipFill></dgm:spPr>'
        elif image_fill_mode == "tile":
            fill_xml = f'{blip_elem}<a:tile tx="0" ty="0" sx="100000" sy="100000" flip="none" algn="ctr"/>'
            sp_pr = f'<dgm:spPr bwMode="auto"><a:blipFill rotWithShape="0">{fill_xml}</a:blipFill></dgm:spPr>'
        elif image_fill_mode == "fill":
            # FILL: scale to cover, crop overflow. Negative insets.
            img_ar = image_aspect_ratio or 1.0
            box_ar = box_aspect_ratio or 0.5
            if img_ar > box_ar:
                # Image wider than box → crop left/right
                excess = int(((img_ar / box_ar) - 1) / 2 * 100000)
                fill_rect = f'<a:fillRect l="-{excess}" r="-{excess}"/>'
            else:
                # Image taller than box → crop top/bottom
                excess = int(((box_ar / img_ar) - 1) / 2 * 100000)
                fill_rect = f'<a:fillRect t="-{excess}" b="-{excess}"/>'
            sp_pr = f'<dgm:spPr bwMode="auto"><a:blipFill dpi="0" rotWithShape="0">{blip_elem}<a:srcRect/><a:stretch>{fill_rect}</a:stretch></a:blipFill></dgm:spPr>'
        else:  # "fit" (default)
            # FIT: scale to fit inside box, letterbox. Positive insets.
            img_ar = image_aspect_ratio or 1.0
            box_ar = box_aspect_ratio or 0.5
            if img_ar > box_ar:
                # Image wider than box → add left/right margins
                margin = int((1 - box_ar / img_ar) / 2 * 100000)
                fill_rect = f'<a:fillRect l="{margin}" r="{margin}"/>'
            else:
                # Image taller than box → add top/bottom margins
                margin = int((1 - img_ar / box_ar) / 2 * 100000)
                fill_rect = f'<a:fillRect t="{margin}" b="{margin}"/>'
            sp_pr = f'<dgm:spPr bwMode="auto"><a:blipFill dpi="0" rotWithShape="0">{blip_elem}<a:srcRect/><a:stretch>{fill_rect}</a:stretch></a:blipFill></dgm:spPr>'
    else:
        sp_pr = "<dgm:spPr/>"

    return (
        f'<dgm:pt modelId="{node_id}"{type_attr}>'
        f'<dgm:prSet phldrT="[Text]"/>'
        f"{sp_pr}"
        f"<dgm:t><a:bodyPr/><a:lstStyle/>"
        f'<a:p><a:r><a:rPr lang="en-GB" dirty="0"/>'
        f"<a:t>{escaped}</a:t></a:r></a:p>"
        f"</dgm:t>"
        f"</dgm:pt>"
    )


def make_par_trans(par_id: str) -> str:
    """Return the XML fragment for a parent-transition point.

    Every non-doc node has a parTrans point associated with it. It
    represents the connector arriving at the node from its parent.
    Referenced by `parTransId` on the corresponding cxn.
    """
    return (
        f'<dgm:pt modelId="{par_id}" type="parTrans">'
        f"<dgm:prSet/><dgm:spPr/>"
        f"<dgm:t><a:bodyPr/><a:lstStyle/>"
        f'<a:p><a:endParaRPr lang="en-GB"/></a:p></dgm:t>'
        f"</dgm:pt>"
    )


def make_sib_trans(sib_id: str) -> str:
    """Return the XML fragment for a sibling-transition point.

    Every non-doc node also has a sibTrans point. It represents the
    connector/spacer between this node and its next sibling.
    Referenced by `sibTransId` on the corresponding cxn.
    """
    return (
        f'<dgm:pt modelId="{sib_id}" type="sibTrans">'
        f"<dgm:prSet/><dgm:spPr/>"
        f"<dgm:t><a:bodyPr/><a:lstStyle/>"
        f'<a:p><a:endParaRPr lang="en-GB"/></a:p></dgm:t>'
        f"</dgm:pt>"
    )


def make_cxn(
    src_id: str,
    dst_id: str,
    src_ord: int,
    par_id: str,
    sib_id: str,
) -> str:
    """Return the XML fragment for a parent→child connection.

    `src_id` can be the doc (for top-level nodes) or any other node (for
    nested trees in hierarchical layouts). `src_ord` is the ordinal
    position of this child under the parent — 0, 1, 2, ... as they should
    appear. `par_id` and `sib_id` are the modelIds of the parTrans and
    sibTrans points that correspond to this edge.

    The connection has no type attribute — it's an untyped data
    connection, which encodes a parent→child relationship in the data
    model. PowerPoint's layout algorithm then interprets the tree/list
    shape and generates the presentation tree (pres points + presOf /
    presParOf) at open time.
    """
    return (
        f'<dgm:cxn modelId="{gid()}" '
        f'srcId="{src_id}" destId="{dst_id}" '
        f'srcOrd="{src_ord}" destOrd="0" '
        f'parTransId="{par_id}" sibTransId="{sib_id}"/>'
    )


def wrap_data_model(points_xml: str, connections_xml: str) -> bytes:
    """Wrap a ptLst body and cxnLst body in the full data1.xml envelope.

    Returns the UTF-8 encoded complete XML document ready to be written
    as `ppt/diagrams/data1.xml`.

    Args:
        points_xml: Concatenated <dgm:pt> elements. Typically starts with
            the output of make_doc_pt, followed by make_node_pt/
            make_par_trans/make_sib_trans for each data node.
        connections_xml: Concatenated <dgm:cxn> elements from make_cxn.
    """
    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<dgm:dataModel '
        f'xmlns:dgm="{NSMAP["dgm"]}" '
        f'xmlns:a="{NSMAP["a"]}">',
        "<dgm:ptLst>",
        points_xml,
        "</dgm:ptLst>",
        "<dgm:cxnLst>",
        connections_xml,
        "</dgm:cxnLst>",
        "<dgm:bg/>",
        "<dgm:whole/>",
        "</dgm:dataModel>",
    ]
    return "".join(parts).encode("utf-8")
