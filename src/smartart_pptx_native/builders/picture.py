"""Builder for Picture SmartArt layouts with image embedding.

Extends the flat_list data model with per-node image bindings. When
items carry `image_path` fields, each node's `<dgm:spPr>` gets an
`<a:blipFill>` referencing an image via an r:embed relationship.

Input shapes accepted:

  Text-only (delegated to flat_list builder):
    {"items": ["Alpha", "Beta", "Gamma"]}

  With images:
    {"items": [
        {"label": "AI Strategy", "image_path": "/path/to/image1.png"},
        {"label": "Data Pipeline", "image_path": "/path/to/image2.png"},
        {"label": "Model Training"}  # no image — gets placeholder
    ]}

When all items are strings, this builder delegates to flat_list.build()
unchanged. When any item is a dict with an `image_path` field, the
builder produces:

  1. data1.xml bytes with <a:blipFill> on nodes that have images
  2. A list of (rId, image_path) tuples that the engine must embed
     as ppt/diagrams/_rels/data1.xml.rels relationships + ppt/media/ files

The engine calls `build()` which returns `(data_xml_bytes, image_refs)`.
The engine is responsible for writing the media files and rels file
into the carrier .pptx — this builder only produces the data model XML.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.smartart_pptx_native import data_model
from src.smartart_pptx_native.builders import flat_list


class PictureBuildError(ValueError):
    """Raised when extracted picture data fails validation."""


@dataclass
class ImageRef:
    """One image reference for the engine to embed in the carrier.

    Attributes:
        rel_id: The rId used in the data1.xml blipFill (e.g. "rId1")
        image_path: Absolute path to the source image file.
        media_name: Filename to use inside the carrier's ppt/media/
            (e.g. "image1.png").
    """

    rel_id: str
    image_path: Path
    media_name: str


def _extract_items(
    extracted: dict[str, Any], entry: dict[str, Any]
) -> tuple[list[dict[str, Any]], bool]:
    """Parse extracted data into normalised item dicts.

    Returns (items, has_images) where:
      - items is a list of {"label": str, "image_path": str|None} dicts
      - has_images is True if at least one item has an image_path

    Handles both plain string items and dict items.
    """
    # Find the items list using the same aliases as flat_list
    raw = None
    for key in flat_list._LEGACY_ALIASES:
        if key in extracted:
            raw = extracted[key]
            break

    if raw is None:
        raise PictureBuildError(
            f"picture builder for layout {entry.get('id', '?')!r} requires "
            f"an items list under one of {list(flat_list._LEGACY_ALIASES)}; "
            f"got keys {sorted(extracted)}"
        )

    if not isinstance(raw, list):
        raise PictureBuildError(f"items must be a list, got {type(raw).__name__}")

    items: list[dict[str, Any]] = []
    has_images = False

    for item in raw:
        if isinstance(item, str):
            items.append({"label": item.strip(), "image_path": None})
        elif isinstance(item, dict):
            label = item.get("label", "")
            if not isinstance(label, str):
                raise PictureBuildError(
                    f"item label must be a string, got {type(label).__name__}"
                )
            image_path = item.get("image_path")
            if image_path is not None:
                image_path = str(image_path)
                has_images = True
            fill_mode = item.get("image_fill_mode")
            entry_dict = {"label": label.strip(), "image_path": image_path}
            if fill_mode:
                entry_dict["image_fill_mode"] = fill_mode
            items.append(entry_dict)
        else:
            raise PictureBuildError(
                f"items must be strings or dicts, got {type(item).__name__}"
            )

    return items, has_images


def build(
    extracted: dict[str, Any], entry: dict[str, Any]
) -> bytes | tuple[bytes, list[ImageRef]]:
    """Build data1.xml bytes for a Picture layout.

    When items are all plain strings (no image_path fields), delegates
    to flat_list.build() and returns plain bytes.

    When any item has an image_path, returns a tuple of
    (data_xml_bytes, image_refs) where image_refs is a list of ImageRef
    objects the engine must embed into the carrier .pptx.

    The engine checks the return type to decide whether to create a
    ppt/diagrams/_rels/data1.xml.rels file and copy media files.
    """
    items, has_images = _extract_items(extracted, entry)

    if not has_images:
        # Text-only — delegate to flat_list (no image rels needed)
        return flat_list.build(extracted, entry)

    # Validate constraints
    n = len(items)
    layout_id = entry.get("id", "?")
    if n < entry["min_nodes"]:
        raise PictureBuildError(
            f"layout {layout_id!r} requires at least {entry['min_nodes']} items, got {n}"
        )
    if n > entry["max_nodes"]:
        raise PictureBuildError(
            f"layout {layout_id!r} supports at most {entry['max_nodes']} items, got {n}"
        )

    max_chars = entry["max_label_chars"]
    long = [i["label"] for i in items if len(i["label"]) > max_chars]
    if long:
        raise PictureBuildError(
            f"layout {layout_id!r} labels must be <= {max_chars} chars. Too long: {long}"
        )

    doc_id = data_model.gid()
    doc_prset = data_model.build_doc_prset(
        entry["layout_uri"],
        qs_type_id=entry.get("qs_type_id",
            "urn:microsoft.com/office/officeart/2005/8/quickstyle/simple1"),
        cs_type_id=entry.get("cs_type_id",
            "urn:microsoft.com/office/officeart/2005/8/colors/accent1_2"),
    )

    pts: list[str] = [data_model.make_doc_pt(doc_id, doc_prset)]
    cxns: list[str] = []
    image_refs: list[ImageRef] = []
    next_image_rid = 1

    # Child-node architecture (validated by spike 6b iteration):
    #
    # BlipFill on a PARENT data point renders as a background fill on
    # the composite shape (compNode) — bleeds behind all sub-shapes
    # including text. To put images in picture placeholders only:
    #
    #   Parent node: text label + empty spPr (no background bleed)
    #   Child node:  blipFill + empty text → layout's pictRect reads
    #                via presOf axis="ch"
    #
    # Items without images get no child node → pictRect shows the
    # default placeholder icon (blipPhldr="1" camera/mountain).
    #
    # Requires modified layout.xml where:
    #   pictRect: presOf axis="ch" ptType="node" cnt="1"
    #   textRect: presOf axis="self" (not desOrSelf, to exclude child text)

    for i, item in enumerate(items):
        # Parent node — carries the text label, NO blipFill
        item_id = data_model.gid()
        par_id = data_model.gid()
        sib_id = data_model.gid()
        pts.append(data_model.make_node_pt(item_id, item["label"]))
        pts.append(data_model.make_par_trans(par_id))
        pts.append(data_model.make_sib_trans(sib_id))
        cxns.append(data_model.make_cxn(doc_id, item_id, i, par_id, sib_id))

        # Child node — carries the image, no text
        if item["image_path"]:
            img_id = data_model.gid()
            img_par = data_model.gid()
            img_sib = data_model.gid()

            rel_id = f"rId{next_image_rid}"
            image_path = Path(item["image_path"])
            suffix = image_path.suffix.lstrip(".") or "png"
            media_name = f"image{next_image_rid}.{suffix}"
            image_refs.append(ImageRef(
                rel_id=rel_id,
                image_path=image_path,
                media_name=media_name,
            ))
            next_image_rid += 1

            # Child node: blipFill in spPr, empty text body
            fill_mode = item.get("image_fill_mode", "fit")

            # Compute image aspect ratio for correct fit/fill insets
            img_ar = 1.0  # default square
            try:
                from PIL import Image as PILImage
                with PILImage.open(image_path) as img:
                    w, h = img.size
                    img_ar = w / h if h > 0 else 1.0
            except Exception:
                pass

            pts.append(data_model.make_node_pt(
                img_id, "",
                image_rel_id=rel_id,
                image_fill_mode=fill_mode,
                image_aspect_ratio=img_ar,
            ))
            pts.append(data_model.make_par_trans(img_par))
            pts.append(data_model.make_sib_trans(img_sib))
            # Connect child to parent (not to doc)
            cxns.append(data_model.make_cxn(item_id, img_id, 0, img_par, img_sib))

    data_xml = data_model.wrap_data_model("".join(pts), "".join(cxns))
    return data_xml, image_refs
