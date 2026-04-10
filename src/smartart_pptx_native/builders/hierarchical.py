"""Generic builder for hierarchical SmartArt layouts.

Handles any layout whose data model is a tree of N nodes —
orgChart1 and its variants, hierarchy2/4/5/6, and future hierarchical
additions.

Input shape:

    {
        "tree": {
            "title": "CEO",
            "children": [
                {"title": "Executive Assistant", "asst": true},
                {"title": "CTO", "children": [...]},
                {"title": "CFO", "children": [...]},
            ],
        },
    }

Each node dict has:
  - "title" (str, required): the label text
  - "asst" (bool, optional): True to render sideways as an assistant.
    Only meaningful when the catalog entry declares `"asst"` in
    `node_type_capabilities`. Ignored on layouts without asst support.
  - "children" (list[dict], optional): nested subtree.

Traversal is depth-first. Each node emits a point (with optional
`type="asst"`), a parTrans, a sibTrans, and a cxn linking it to its
parent.

Verified by spike 4 for orgChart1. Other hierarchical layouts
(hierarchy2/4/5/6) use the same data-model shape — only the layout
algorithm (in layout.xml) differs.
"""
from __future__ import annotations

from typing import Any

from src.smartart_pptx_native import data_model


class HierarchicalBuildError(ValueError):
    """Raised when extracted data fails the catalog constraints."""


def _count_nodes(node: dict[str, Any]) -> int:
    return 1 + sum(_count_nodes(c) for c in node.get("children", []))


def _max_depth(node: dict[str, Any]) -> int:
    children = node.get("children", [])
    if not children:
        return 1
    return 1 + max(_max_depth(c) for c in children)


def _collect_labels(node: dict[str, Any]) -> list[str]:
    labels = [node["title"]]
    for c in node.get("children", []):
        labels.extend(_collect_labels(c))
    return labels


def _validate_node(node: Any, path: str, layout_id: str) -> None:
    if not isinstance(node, dict):
        raise HierarchicalBuildError(
            f"layout {layout_id!r}: node at {path} must be a dict, "
            f"got {type(node).__name__}"
        )
    if "title" not in node:
        raise HierarchicalBuildError(
            f"layout {layout_id!r}: node at {path} is missing 'title'"
        )
    if not isinstance(node["title"], str):
        raise HierarchicalBuildError(
            f"layout {layout_id!r}: node at {path} has non-string title: "
            f"{type(node['title']).__name__}"
        )
    if "asst" in node and not isinstance(node["asst"], bool):
        raise HierarchicalBuildError(
            f"layout {layout_id!r}: node at {path} has non-bool 'asst': "
            f"{type(node['asst']).__name__}"
        )
    children = node.get("children", [])
    if not isinstance(children, list):
        raise HierarchicalBuildError(
            f"layout {layout_id!r}: node at {path} has non-list 'children': "
            f"{type(children).__name__}"
        )
    for i, child in enumerate(children):
        _validate_node(child, f"{path}.children[{i}]", layout_id)


def _check_constraints(tree: dict[str, Any], entry: dict[str, Any]) -> None:
    layout_id = entry.get("id", "?")

    total = _count_nodes(tree)
    if total < entry["min_nodes"]:
        raise HierarchicalBuildError(
            f"layout {layout_id!r} requires at least "
            f"{entry['min_nodes']} nodes, got {total}"
        )
    if total > entry["max_nodes"]:
        raise HierarchicalBuildError(
            f"layout {layout_id!r} supports at most "
            f"{entry['max_nodes']} nodes, got {total}. "
            "Extractor should truncate or fall back to custom_svg."
        )

    max_chars = entry["max_label_chars"]
    long = [l for l in _collect_labels(tree) if len(l) > max_chars]
    if long:
        raise HierarchicalBuildError(
            f"layout {layout_id!r} labels must be <= {max_chars} chars "
            f"(rationale: {entry['max_label_chars_rationale']}). "
            f"Too long: {long}"
        )

    # Warn if asst is used on a layout that doesn't support it. We silently
    # ignore rather than error because the layout algorithm will just treat
    # the node as a regular subordinate — still valid, just not styled as
    # an assistant.


def _extract_tree(extracted: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    if "tree" not in extracted:
        raise HierarchicalBuildError(
            f"hierarchical builder for layout {entry.get('id', '?')!r} "
            f"requires a 'tree' key in extracted data; "
            f"got keys {sorted(extracted)}"
        )
    tree = extracted["tree"]
    _validate_node(tree, "root", entry.get("id", "?"))
    return tree


def build(extracted: dict[str, Any], entry: dict[str, Any]) -> bytes:
    """Build data1.xml bytes for a hierarchical layout.

    Args:
        extracted: Dict with a "tree" key holding a recursive node dict.
        entry: The catalog entry for the target layout.

    Returns:
        UTF-8 encoded data1.xml bytes.

    Raises:
        HierarchicalBuildError: If extracted data fails validation.
    """
    tree = _extract_tree(extracted, entry)
    _check_constraints(tree, entry)

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

    # Whether the entry supports assistant node types. If not, the asst
    # flag on tree nodes is ignored (rendered as regular subordinates).
    asst_capable = "asst" in entry.get("node_type_capabilities", [])

    def walk(node: dict[str, Any], parent_id: str, sib_ord: int) -> None:
        node_id = data_model.gid()
        par_id = data_model.gid()
        sib_id = data_model.gid()

        is_asst = asst_capable and bool(node.get("asst", False))
        pts.append(data_model.make_node_pt(node_id, node["title"].strip(), is_asst=is_asst))
        pts.append(data_model.make_par_trans(par_id))
        pts.append(data_model.make_sib_trans(sib_id))
        cxns.append(data_model.make_cxn(parent_id, node_id, sib_ord, par_id, sib_id))

        for i, child in enumerate(node.get("children", [])):
            walk(child, node_id, i)

    walk(tree, doc_id, 0)

    return data_model.wrap_data_model("".join(pts), "".join(cxns))
