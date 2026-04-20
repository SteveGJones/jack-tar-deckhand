"""Generic builder for flat-list SmartArt layouts.

Handles any layout whose data model is a flat sequence of N items —
which covers the vast majority of PowerPoint SmartArt categories:
Process, Cycle, List, Matrix, Pyramid, Relationship (Venn, Funnel,
Target). The layout algorithm in `layout.xml` is what actually turns
the flat list into a 2x2 grid, a ring, a funnel, or a horizontal row —
the data model itself is always the same: doc point + N nodes + N
parTrans/sibTrans pairs + N untyped cxn connections.

Input shape:

    {"items": ["Research", "Design", "Build", "Test", "Ship"]}

The extractor can produce this shape for any flat-list graphic type.
Legacy keys (`steps`, `stages`, `phases`, etc.) are accepted for
backward compatibility with Phase 1-7 tests.

Validation is catalog-driven — min_nodes, max_nodes, max_label_chars
come from the entry dict.
"""
from __future__ import annotations

from typing import Any

from src.smartart_pptx_native import data_model


class FlatListBuildError(ValueError):
    """Raised when extracted data fails the catalog constraints."""


# Legacy key aliases accepted in addition to the canonical "items" key.
# Each alias is the per-layout vocabulary we used in Phase 1-7 builders.
_LEGACY_ALIASES = ("items", "steps", "stages", "phases", "nodes", "labels")


def _extract_items(extracted: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    """Find the list of strings in the extracted data and normalise.

    Accepts any of {items, steps, stages, phases, nodes, labels} as the
    key. Strips whitespace from each item.
    """
    for key in _LEGACY_ALIASES:
        if key in extracted:
            value = extracted[key]
            break
    else:
        # No recognised key
        raise FlatListBuildError(
            f"flat_list builder for layout {entry.get('id', '?')!r} requires "
            f"an items list under one of {list(_LEGACY_ALIASES)}; "
            f"got keys {sorted(extracted)}"
        )

    if not isinstance(value, list):
        raise FlatListBuildError(
            f"flat_list value must be a list, got {type(value).__name__}"
        )

    items = []
    for item in value:
        if isinstance(item, str):
            items.append(item.strip())
        elif isinstance(item, dict):
            label = item.get("text") or item.get("label") or ""
            if not isinstance(label, str):
                raise FlatListBuildError(
                    f"flat_list dict item 'text'/'label' must be a string, "
                    f"got {type(label).__name__}"
                )
            items.append(label.strip())
        else:
            raise FlatListBuildError(
                f"flat_list items must be strings or dicts with 'text'/'label' key; "
                f"found {type(item).__name__!r}"
            )

    return items


def _check_constraints(items: list[str], entry: dict[str, Any]) -> None:
    n = len(items)
    layout_id = entry.get("id", "?")

    if n < entry["min_nodes"]:
        raise FlatListBuildError(
            f"layout {layout_id!r} requires at least "
            f"{entry['min_nodes']} items, got {n}"
        )
    if n > entry["max_nodes"]:
        raise FlatListBuildError(
            f"layout {layout_id!r} supports at most "
            f"{entry['max_nodes']} items, got {n}. "
            "Extractor should truncate or fall back to custom_svg."
        )

    max_chars = entry["max_label_chars"]
    long = [i for i in items if len(i) > max_chars]
    if long:
        raise FlatListBuildError(
            f"layout {layout_id!r} labels must be <= {max_chars} chars "
            f"(rationale: {entry['max_label_chars_rationale']}). "
            f"Too long: {long}"
        )


def build(extracted: dict[str, Any], entry: dict[str, Any]) -> bytes:
    """Build data1.xml bytes for a flat-list layout.

    Args:
        extracted: Dict with an items list under any of the accepted
            keys (items / steps / stages / phases / nodes / labels).
        entry: The catalog entry for the target layout. Used for
            layout_uri (which becomes the doc point's loTypeId),
            qs_type_id, cs_type_id, and capacity constraints.

    Returns:
        UTF-8 encoded data1.xml bytes.

    Raises:
        FlatListBuildError: If extracted data fails validation.
    """
    items = _extract_items(extracted, entry)
    _check_constraints(items, entry)

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

    for i, label in enumerate(items):
        node_id = data_model.gid()
        par_id = data_model.gid()
        sib_id = data_model.gid()
        pts.append(data_model.make_node_pt(node_id, label))
        pts.append(data_model.make_par_trans(par_id))
        pts.append(data_model.make_sib_trans(sib_id))
        cxns.append(data_model.make_cxn(doc_id, node_id, i, par_id, sib_id))

    return data_model.wrap_data_model("".join(pts), "".join(cxns))
