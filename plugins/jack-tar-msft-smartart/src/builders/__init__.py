"""Generic data-shape builders for pptx_native SmartArt.

Each catalog entry declares its `data_shape` (`flat_list`,
`hierarchical`, `picture`, etc.). The engine looks up the matching
builder from BUILDER_BY_DATA_SHAPE and calls its `build` function with
the extracted data and the catalog entry.

This replaces the per-layout modules (process.py, cycle.py,
org_chart.py) that were nearly-identical copies with different
LAYOUT_ID constants. Adding a new SmartArt layout is now a pure
catalog.json change — zero Python code per layout.
"""
from __future__ import annotations

from src.builders import flat_list, hierarchical, picture

BUILDER_BY_DATA_SHAPE = {
    "flat_list": flat_list.build,
    "hierarchical": hierarchical.build,
    # Picture builder handles both text-only (delegates to flat_list)
    # and image-enriched (returns data_xml + image_refs tuple) cases.
    # The engine checks the return type to decide whether to embed
    # media files in the carrier .pptx.
    "picture": picture.build,
}


class UnsupportedDataShapeError(Exception):
    """Raised when a catalog entry specifies a data_shape with no builder."""


def build(data_shape: str, extracted_data: dict, entry: dict) -> bytes:
    """Dispatch to the generic builder matching the catalog entry's data_shape.

    Args:
        data_shape: The data_shape string from the catalog entry.
        extracted_data: The extractor's output (shape depends on data_shape).
        entry: The catalog entry dict.

    Returns:
        UTF-8 encoded data1.xml bytes.

    Raises:
        UnsupportedDataShapeError: If no builder is registered for the shape.
    """
    builder = BUILDER_BY_DATA_SHAPE.get(data_shape)
    if builder is None:
        raise UnsupportedDataShapeError(
            f"no builder registered for data_shape {data_shape!r} "
            f"(layout id: {entry.get('id', '?')})"
        )
    return builder(extracted_data, entry)
