"""Op2 — replace a named IMAGE:* marker shape with an embedded picture.

In-memory variant — orchestrator owns save.
"""
from __future__ import annotations

from pathlib import Path

from src.security import resolve_within_allowlist


def replace_image_marker_in_memory(
    *,
    prs,
    marker_name: str,
    image_path: Path,
    allowed_image_roots: list[Path],
) -> None:
    safe_image = resolve_within_allowlist(image_path, allowed_roots=allowed_image_roots)
    target_slide = None
    target_shape = None
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.name == marker_name:
                target_slide = slide
                target_shape = shape
                break
        if target_shape is not None:
            break
    if target_shape is None:
        raise LookupError(f"shape {marker_name!r} not found on any slide")
    left = target_shape.left
    top = target_shape.top
    width = target_shape.width
    height = target_shape.height

    sp_elem = target_shape._element
    sp_elem.getparent().remove(sp_elem)

    target_slide.shapes.add_picture(str(safe_image), left, top, width=width, height=height)
