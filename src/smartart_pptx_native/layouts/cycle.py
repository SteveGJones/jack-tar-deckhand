"""Cycle2 layout builder — Basic Cycle SmartArt.

Emits the data model for PowerPoint's Basic Cycle layout — a ring of
N nodes with directional arrows flowing clockwise from a 12 o'clock
starting position.

Data shape: flat_list — `extracted_data` is a dict with a "stages" key:

    {"stages": ["Plan", "Build", "Test", "Deploy", "Monitor", "Learn"]}

The data model is structurally IDENTICAL to process1 — a flat list of
untyped nodes with parTrans/sibTrans pairs, parented to the doc point.
The only difference is the `loTypeId` on the doc point, which binds
the diagram to cycle2's layout algorithm rather than process1's lin
algorithm. Spike 2 proved this generalisation empirically.

Verified by spike 2 (mutation of a cycle seed with 6 hardcoded phases).
"""
from __future__ import annotations

from typing import Any

from src.smartart_pptx_native import data_model
from src.smartart_pptx_native.layouts import catalog

LAYOUT_ID = "cycle2"


class CycleBuildError(ValueError):
    """Raised when extracted data fails catalog-defined constraints."""


def _validate(extracted: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    """Check extracted data against the catalog entry's constraints."""
    if "stages" not in extracted:
        raise CycleBuildError(
            "cycle2 builder requires 'stages' key in extracted data "
            f"(got keys: {sorted(extracted)})"
        )

    stages = extracted["stages"]
    if not isinstance(stages, list):
        raise CycleBuildError(
            f"'stages' must be a list, got {type(stages).__name__}"
        )

    if not all(isinstance(s, str) for s in stages):
        bad_types = sorted({type(s).__name__ for s in stages if not isinstance(s, str)})
        raise CycleBuildError(
            f"'stages' must contain only strings, found: {bad_types}"
        )

    n = len(stages)
    if n < entry["min_nodes"]:
        raise CycleBuildError(
            f"cycle2 requires at least {entry['min_nodes']} stages, got {n}"
        )
    if n > entry["max_nodes"]:
        raise CycleBuildError(
            f"cycle2 supports at most {entry['max_nodes']} stages, got {n}. "
            "Extractor should truncate or fall back to custom_svg."
        )

    max_chars = entry["max_label_chars"]
    long_stages = [s for s in stages if len(s) > max_chars]
    if long_stages:
        raise CycleBuildError(
            f"cycle2 labels must be <= {max_chars} characters "
            f"(rationale: {entry['max_label_chars_rationale']}). "
            f"Too long: {long_stages}"
        )

    return [s.strip() for s in stages]


def build_data_model(extracted: dict[str, Any]) -> bytes:
    """Construct ppt/diagrams/data1.xml bytes for a cycle2 diagram.

    Args:
        extracted: Dict with a "stages" list.

    Returns:
        UTF-8 encoded XML bytes ready to be written into a .pptx zip.

    Raises:
        CycleBuildError: If extracted data fails validation.
        catalog.CatalogError: If the catalog lacks a cycle2 entry.
    """
    entry = catalog.get_entry(LAYOUT_ID)
    stages = _validate(extracted, entry)

    doc_id = data_model.gid()
    doc_prset = data_model.build_doc_prset(entry["layout_uri"])

    pts: list[str] = [data_model.make_doc_pt(doc_id, doc_prset)]
    cxns: list[str] = []

    for i, stage_label in enumerate(stages):
        node_id = data_model.gid()
        par_id = data_model.gid()
        sib_id = data_model.gid()

        pts.append(data_model.make_node_pt(node_id, stage_label))
        pts.append(data_model.make_par_trans(par_id))
        pts.append(data_model.make_sib_trans(sib_id))
        cxns.append(data_model.make_cxn(doc_id, node_id, i, par_id, sib_id))

    return data_model.wrap_data_model("".join(pts), "".join(cxns))


def get_layout_uri() -> str:
    return catalog.get_entry(LAYOUT_ID)["layout_uri"]


def get_seed_path():
    return catalog.resolve_seed_path(catalog.get_entry(LAYOUT_ID))
