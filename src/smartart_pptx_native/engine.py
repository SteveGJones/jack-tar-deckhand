"""pptx_native engine entry point.

`render(spec, output_dir)` is the single function this module exposes.
Given a spec describing a graphic type and its extracted data, it
produces a complete editable `.pptx` file at `output_dir` and returns
a dict describing the output.

In Phase 1 this function is called directly by tests and any dev tool.
In Phase 2 it gets wired into `src.smartart_renderer._ENGINE_DISPATCH`
so the main pipeline can dispatch to it.

The render operation is the **mutation** pattern (spike 1/2/4): copy
a seed `.pptx`, rewrite `ppt/diagrams/data1.xml`, delete the cached
`ppt/diagrams/drawing1.xml`, strip the drawing relationship from the
slide's `.rels`, strip the content-type override for drawing1. The
**injection** pattern for adding SmartArt to a host `.pptx` that had
none comes in Phase 3 (assembler_patch.py, spike 3).

The engine does not write `drawing1.xml`. PowerPoint regenerates the
presentation tree and the cached render from `layout1.xml` on first
open — validated by all four Phase 0 spikes.
"""
from __future__ import annotations

import importlib
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.smartart_pptx_native.layouts import catalog


class RenderError(Exception):
    """Raised when the engine cannot produce an editable output."""


@dataclass
class RenderResult:
    """Structured result of a render call.

    Attributes:
        output_path: Absolute path to the produced .pptx file.
        layout_id: Catalog entry id used (e.g. "process1").
        layout_uri: OOXML layout URI bound to the graphic.
        node_count: Number of data nodes in the produced diagram.
        engine: Always "pptx_native" for this engine.
    """

    output_path: Path
    layout_id: str
    layout_uri: str
    node_count: int
    engine: str = "pptx_native"


# Regex patterns for the four surgical mutations applied to a seed copy.
_DRAWING_OVERRIDE_RE = re.compile(
    r'<Override PartName="/ppt/diagrams/drawing1\.xml" ContentType="[^"]*"/>'
)
_DRAWING_REL_RE = re.compile(
    r'<Relationship Id="[^"]*" '
    r'Type="http://schemas\.microsoft\.com/office/2007/relationships/diagramDrawing" '
    r'Target="\.\./diagrams/drawing1\.xml"/>'
)


def _strip_drawing_override(xml: bytes) -> bytes:
    text = xml.decode("utf-8")
    new_text, n = _DRAWING_OVERRIDE_RE.subn("", text)
    if n != 1:
        raise RenderError(
            f"expected exactly 1 drawing1 content-type override in "
            f"[Content_Types].xml, found {n}. Seed may be corrupt or "
            f"from a different PowerPoint version."
        )
    return new_text.encode("utf-8")


def _strip_drawing_rel(xml: bytes) -> bytes:
    text = xml.decode("utf-8")
    new_text, n = _DRAWING_REL_RE.subn("", text)
    if n != 1:
        raise RenderError(
            f"expected exactly 1 diagramDrawing relationship in "
            f"slide1.xml.rels, found {n}. Seed may be corrupt."
        )
    return new_text.encode("utf-8")


def _load_builder_module(entry: dict[str, Any]):
    """Dynamically import the builder module for a catalog entry."""
    module_name = entry["builder_module"]
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        raise RenderError(
            f"cannot import builder module {module_name!r} "
            f"for layout {entry['id']!r}: {exc}"
        ) from exc


def _count_nodes_in_data_xml(xml_bytes: bytes) -> int:
    """Count the untyped <dgm:pt> elements (regular + asst data nodes).

    Doc, parTrans, and sibTrans points all have `type=` attributes.
    Only regular nodes and assistant nodes are the user-facing data
    nodes we want to report in RenderResult.node_count.
    """
    text = xml_bytes.decode("utf-8")
    # Untyped: <dgm:pt modelId="..."> with no type= attribute, or
    # explicitly type="asst" (assistants count as data nodes).
    total = 0
    for match in re.finditer(r'<dgm:pt modelId="[^"]+"([^>]*)>', text):
        attrs = match.group(1)
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
    """Render a pptx_native SmartArt graphic to an editable .pptx file.

    Args:
        spec: Dict with the following required keys:
            - graphic_type (str): A graphic type the catalog knows how
              to back. Looked up via catalog.get_layout_id_for_graphic_type.
            - data (dict): Extracted data in the shape the chosen
              layout's builder expects. For process1 this is
              `{"steps": [...]}`.
          Optional keys:
            - slide_number (int): For filename disambiguation in
              output_name.
        output_dir: Directory to write the output file to. Created if
            it doesn't exist.
        output_name: Optional override for the output filename. Defaults
            to `pptx_native_<layout_id>_slide<n>.pptx` (or
            `pptx_native_<layout_id>.pptx` if no slide number).

    Returns:
        RenderResult describing the output.

    Raises:
        RenderError: If spec is invalid, the layout is unsupported, the
            seed is missing, or any of the surgical mutations fail.
        The underlying layout builder may also raise its own error
        subclass (e.g. ProcessBuildError) — those propagate up to the
        caller unchanged.
    """
    # 1. Parse + validate the spec shape.
    if "graphic_type" not in spec:
        raise RenderError("spec is missing required key 'graphic_type'")
    if "data" not in spec:
        raise RenderError("spec is missing required key 'data'")

    graphic_type = spec["graphic_type"]
    layout_id = catalog.get_layout_id_for_graphic_type(graphic_type)
    if layout_id is None:
        raise RenderError(
            f"no pptx_native layout supports graphic_type {graphic_type!r}. "
            f"The extractor should not have routed this to pptx_native."
        )

    entry = catalog.get_entry(layout_id)
    seed_path = catalog.resolve_seed_path(entry)
    if not seed_path.exists():
        raise RenderError(
            f"seed file missing for layout {layout_id!r}: {seed_path}"
        )

    # 2. Dispatch to the layout builder.
    builder = _load_builder_module(entry)
    if not hasattr(builder, "build_data_model"):
        raise RenderError(
            f"builder module {entry['builder_module']} has no "
            f"build_data_model() function"
        )
    new_data_bytes = builder.build_data_model(spec["data"])

    # 3. Compute output path.
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

    # 4. Copy the seed and apply the four surgical mutations.
    with zipfile.ZipFile(seed_path, "r") as zin, zipfile.ZipFile(
        output_path, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        patched = {"data": False, "content_types": False, "slide_rels": False}

        for item in zin.infolist():
            name = item.filename

            if name == "ppt/diagrams/drawing1.xml":
                # Drop the cached drawing — PowerPoint regenerates.
                continue

            if name == "ppt/diagrams/data1.xml":
                zout.writestr(item, new_data_bytes)
                patched["data"] = True
                continue

            if name == "[Content_Types].xml":
                zout.writestr(item, _strip_drawing_override(zin.read(name)))
                patched["content_types"] = True
                continue

            if name == "ppt/slides/_rels/slide1.xml.rels":
                zout.writestr(item, _strip_drawing_rel(zin.read(name)))
                patched["slide_rels"] = True
                continue

            # Pass-through for all other files (layout1, quickStyle1,
            # colors1, slide1, theme, etc.).
            zout.writestr(item, zin.read(name))

        missing = [k for k, v in patched.items() if not v]
        if missing:
            raise RenderError(
                f"seed {seed_path.name} is missing expected parts: {missing}. "
                "Seed may be from a different PowerPoint version or corrupt."
            )

    # 5. Return structured result.
    return RenderResult(
        output_path=output_path,
        layout_id=layout_id,
        layout_uri=entry["layout_uri"],
        node_count=_count_nodes_in_data_xml(new_data_bytes),
    )
