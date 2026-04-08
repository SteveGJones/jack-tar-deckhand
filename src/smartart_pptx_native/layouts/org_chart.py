"""OrgChart1 layout builder — Organization Chart SmartArt.

Emits the data model for PowerPoint's Organization Chart layout — a
hierarchical tree of roles with optional assistant nodes that render
sideways from their parent (rather than below as regular subordinates).

Data shape: hierarchical — `extracted_data` is a dict with a "tree" key
pointing at the root node of a nested dict structure:

    {
        "tree": {
            "title": "CEO",
            "children": [
                {"title": "Executive Assistant", "asst": true},
                {
                    "title": "CTO",
                    "children": [
                        {"title": "Backend Lead"},
                        {"title": "Frontend Lead"}
                    ]
                }
            ]
        }
    }

Each node dict has:
  - "title" (str, required): the label text
  - "asst" (bool, optional): True to render as an assistant — sideways
    from parent with a right-angle connector. Default False.
  - "children" (list[dict], optional): nested subtree.

Verified by spike 4 (recursive tree builder with assistants at two
levels, validated in PowerPoint Mac).

The data model differs from process/cycle only in the traversal
pattern: instead of iterating a flat list with doc→node connections,
we recurse over the tree emitting parent→child connections where the
parent can be any intermediate node, not just doc. The primitives
(make_node_pt, make_par_trans, make_sib_trans, make_cxn) are
identical.
"""
from __future__ import annotations

from typing import Any

from src.smartart_pptx_native import data_model
from src.smartart_pptx_native.layouts import catalog

LAYOUT_ID = "orgChart1"


class OrgChartBuildError(ValueError):
    """Raised when extracted data fails catalog-defined constraints."""


def _count_nodes(node: dict[str, Any]) -> int:
    """Count all nodes in the tree (including the root)."""
    return 1 + sum(_count_nodes(c) for c in node.get("children", []))


def _max_depth(node: dict[str, Any]) -> int:
    """Return the maximum depth of the tree (root = 1)."""
    children = node.get("children", [])
    if not children:
        return 1
    return 1 + max(_max_depth(c) for c in children)


def _collect_labels(node: dict[str, Any]) -> list[str]:
    """Return all node titles as a flat list for length validation."""
    labels = [node["title"]]
    for c in node.get("children", []):
        labels.extend(_collect_labels(c))
    return labels


def _validate_node(node: Any, path: str = "root") -> None:
    """Recursively validate that every node in the tree has a title
    (string) and that children are a list of dicts."""
    if not isinstance(node, dict):
        raise OrgChartBuildError(
            f"node at {path} must be a dict, got {type(node).__name__}"
        )
    if "title" not in node:
        raise OrgChartBuildError(f"node at {path} is missing 'title'")
    if not isinstance(node["title"], str):
        raise OrgChartBuildError(
            f"node at {path} has non-string title: {type(node['title']).__name__}"
        )
    if "asst" in node and not isinstance(node["asst"], bool):
        raise OrgChartBuildError(
            f"node at {path} has non-bool 'asst': {type(node['asst']).__name__}"
        )
    children = node.get("children", [])
    if not isinstance(children, list):
        raise OrgChartBuildError(
            f"node at {path} has non-list 'children': {type(children).__name__}"
        )
    for i, child in enumerate(children):
        _validate_node(child, f"{path}.children[{i}]")


def _validate(extracted: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    """Check extracted tree against the catalog entry's constraints.

    Returns the root tree dict on success.
    """
    if "tree" not in extracted:
        raise OrgChartBuildError(
            "orgChart1 builder requires 'tree' key in extracted data "
            f"(got keys: {sorted(extracted)})"
        )

    tree = extracted["tree"]
    _validate_node(tree, "root")

    total = _count_nodes(tree)
    if total < entry["min_nodes"]:
        raise OrgChartBuildError(
            f"orgChart1 requires at least {entry['min_nodes']} nodes total, got {total}"
        )
    if total > entry["max_nodes"]:
        raise OrgChartBuildError(
            f"orgChart1 supports at most {entry['max_nodes']} nodes, got {total}. "
            "Extractor should truncate or fall back to custom_svg."
        )

    max_chars = entry["max_label_chars"]
    labels = _collect_labels(tree)
    long_labels = [l for l in labels if len(l) > max_chars]
    if long_labels:
        raise OrgChartBuildError(
            f"orgChart1 labels must be <= {max_chars} characters "
            f"(rationale: {entry['max_label_chars_rationale']}). "
            f"Too long: {long_labels}"
        )

    return tree


def build_data_model(extracted: dict[str, Any]) -> bytes:
    """Construct ppt/diagrams/data1.xml bytes for an orgChart1 diagram.

    Args:
        extracted: Dict with a "tree" key holding the recursive tree.

    Returns:
        UTF-8 encoded XML bytes ready to be written into a .pptx zip.

    Raises:
        OrgChartBuildError: If extracted data fails validation.
        catalog.CatalogError: If the catalog lacks an orgChart1 entry.
    """
    entry = catalog.get_entry(LAYOUT_ID)
    tree = _validate(extracted, entry)

    doc_id = data_model.gid()
    doc_prset = data_model.build_doc_prset(entry["layout_uri"])

    pts: list[str] = [data_model.make_doc_pt(doc_id, doc_prset)]
    cxns: list[str] = []

    def walk(node: dict[str, Any], parent_id: str, sib_ord: int) -> None:
        """Emit this node + its transitions + its cxn to parent, then recurse."""
        node_id = data_model.gid()
        par_id = data_model.gid()
        sib_id = data_model.gid()

        is_asst = bool(node.get("asst", False))
        pts.append(data_model.make_node_pt(node_id, node["title"].strip(), is_asst=is_asst))
        pts.append(data_model.make_par_trans(par_id))
        pts.append(data_model.make_sib_trans(sib_id))
        cxns.append(data_model.make_cxn(parent_id, node_id, sib_ord, par_id, sib_id))

        for i, child in enumerate(node.get("children", [])):
            walk(child, node_id, i)

    # Walk the tree — root is child-of-doc at sib_ord 0.
    walk(tree, doc_id, 0)

    return data_model.wrap_data_model("".join(pts), "".join(cxns))


def get_layout_uri() -> str:
    return catalog.get_entry(LAYOUT_ID)["layout_uri"]


def get_seed_path():
    return catalog.resolve_seed_path(catalog.get_entry(LAYOUT_ID))
