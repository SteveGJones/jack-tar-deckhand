"""Process1 layout builder.

Emits the data model for PowerPoint's Basic Process SmartArt layout —
a flat sequence of N nodes rendered as a horizontal row of boxes with
chevron arrows between them.

Data shape: flat_list — `extracted_data` is a dict with a "steps" key
holding a list of string labels:

    {"steps": ["Research", "Design", "Build", "Test", "Ship"]}

Capacity and per-layout constants (seed path, layout URI, max_nodes,
max_label_chars) come from the catalog — this module does not hardcode
them. Validation is performed against the catalog at build time.

Verified by spike 1 (mutation) and spike 3 (host injection).
"""
from __future__ import annotations

from typing import Any

from src.smartart_pptx_native import data_model
from src.smartart_pptx_native.layouts import catalog

# Layout id — matches the catalog entry id.
LAYOUT_ID = "process1"


class ProcessBuildError(ValueError):
    """Raised when extracted data fails catalog-defined constraints."""


def _validate(extracted: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    """Check extracted data against the catalog entry's constraints.

    Returns the normalised list of step strings on success. Raises
    ProcessBuildError with a specific message on any violation.
    """
    if "steps" not in extracted:
        raise ProcessBuildError(
            "process1 builder requires 'steps' key in extracted data "
            f"(got keys: {sorted(extracted)})"
        )

    steps = extracted["steps"]
    if not isinstance(steps, list):
        raise ProcessBuildError(
            f"'steps' must be a list, got {type(steps).__name__}"
        )

    if not all(isinstance(s, str) for s in steps):
        bad_types = sorted({type(s).__name__ for s in steps if not isinstance(s, str)})
        raise ProcessBuildError(
            f"'steps' must contain only strings, found: {bad_types}"
        )

    n = len(steps)
    if n < entry["min_nodes"]:
        raise ProcessBuildError(
            f"process1 requires at least {entry['min_nodes']} steps, got {n}"
        )
    if n > entry["max_nodes"]:
        raise ProcessBuildError(
            f"process1 supports at most {entry['max_nodes']} steps, got {n}. "
            "Extractor should truncate or fall back to custom_svg."
        )

    max_chars = entry["max_label_chars"]
    long_steps = [s for s in steps if len(s) > max_chars]
    if long_steps:
        raise ProcessBuildError(
            f"process1 labels must be <= {max_chars} characters "
            f"(rationale: {entry['max_label_chars_rationale']}). "
            f"Too long: {long_steps}"
        )

    return [s.strip() for s in steps]


def build_data_model(extracted: dict[str, Any]) -> bytes:
    """Construct ppt/diagrams/data1.xml bytes for a process1 diagram.

    Args:
        extracted: Dict with a "steps" list (e.g.
            `{"steps": ["Research", "Design", "Build"]}`). Data must
            satisfy the catalog's min_nodes/max_nodes/max_label_chars
            constraints — the extractor should have already enforced
            these, but this function re-validates defensively.

    Returns:
        UTF-8 encoded XML bytes for data1.xml, ready to be written into
        a `.pptx` zip.

    Raises:
        ProcessBuildError: If extracted data fails validation.
        catalog.CatalogError: If the catalog is unreadable or lacks a
            process1 entry.
    """
    entry = catalog.get_entry(LAYOUT_ID)
    steps = _validate(extracted, entry)

    doc_id = data_model.gid()
    doc_prset = data_model.build_doc_prset(entry["layout_uri"])

    pts: list[str] = [data_model.make_doc_pt(doc_id, doc_prset)]
    cxns: list[str] = []

    for i, step_label in enumerate(steps):
        node_id = data_model.gid()
        par_id = data_model.gid()
        sib_id = data_model.gid()

        pts.append(data_model.make_node_pt(node_id, step_label))
        pts.append(data_model.make_par_trans(par_id))
        pts.append(data_model.make_sib_trans(sib_id))
        cxns.append(data_model.make_cxn(doc_id, node_id, i, par_id, sib_id))

    return data_model.wrap_data_model("".join(pts), "".join(cxns))


def get_layout_uri() -> str:
    """Return the layout URI for process1, from the catalog."""
    return catalog.get_entry(LAYOUT_ID)["layout_uri"]


def get_seed_path():
    """Return the absolute path to the process1 seed file."""
    return catalog.resolve_seed_path(catalog.get_entry(LAYOUT_ID))
