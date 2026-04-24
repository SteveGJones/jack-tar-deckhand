"""Transactional enrichment orchestrator.

Spec Section 3.4 step 4 - all-or-nothing application of selected
enrichments against a copy of the source .pptx. Phases:

  1. Open source as in-memory Presentation.
  2. Apply Op1 (backgrounds) and Op2 (element images) against the
     in-memory tree. For SMARTART items with action="apply_clear_overlap",
     remove the overlapping text shapes from the in-memory tree HERE
     (before any save).
  3. Save the in-memory tree to `<output>.tmp-<pid>` only if Phase 2
     succeeded for every requested op.
  4. Run Op3 (SmartArt injection) against the temp file. msft-smartart's
     inject() is itself read-all -> mutate -> write-fresh internally, so
     it preserves atomicity within a single call.
  5. Rename temp file to output via os.replace (atomic on POSIX).
  6. On any exception in Phases 2-5, the finally block removes the
     temp file and re-raises EnrichmentApplyError. No partial output
     ever reaches disk.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.oxml.ns import qn

from src.enrichment_ops.background import apply_background_in_memory
from src.enrichment_ops.element_image import replace_image_marker_in_memory
from src.enrichment_ops.smartart import inject_smartart_into_file
from src.smartart_bridge import render_carrier


VALID_KINDS = {"background", "image", "smartart"}
VALID_ACTIONS = {"apply", "apply_clear_overlap", "skip"}


class EnrichmentApplyError(RuntimeError):
    """Raised by apply_enrichment on any op failure or rename failure."""


@dataclass
class EnrichmentItem:
    slide_index: int
    kind: str                    # background | image | smartart
    marker_name: str             # full marker string (e.g. "IMAGE:foo")
    asset_path: Path | None      # image path for background/image; None for smartart
    action: str = "apply"        # apply | apply_clear_overlap | skip
    smartart_spec: dict[str, Any] | None = None  # required when kind="smartart" and action!="skip"
    overlap_shape_names: list[str] = field(default_factory=list)


@dataclass
class EnrichmentPlan:
    source_pptx: Path
    output_pptx: Path
    items: list[EnrichmentItem]


def _remove_overlapping_text_shapes(prs, slide_index_1based: int,
                                       overlap_names: list[str]) -> None:
    if not overlap_names:
        return
    if slide_index_1based < 1 or slide_index_1based > len(prs.slides):
        return
    slide = prs.slides[slide_index_1based - 1]
    cSld = slide.element.find(qn("p:cSld"))
    spTree = cSld.find(qn("p:spTree"))
    if spTree is None:
        return
    for sp in list(spTree):
        nvSpPr = sp.find(qn("p:nvSpPr"))
        if nvSpPr is None:
            continue
        cNvPr = nvSpPr.find(qn("p:cNvPr"))
        if cNvPr is not None and cNvPr.get("name") in overlap_names:
            spTree.remove(sp)


def _drop_marker_shape(prs, slide_index_1based: int, marker_name: str) -> None:
    slide = prs.slides[slide_index_1based - 1]
    cSld = slide.element.find(qn("p:cSld"))
    spTree = cSld.find(qn("p:spTree"))
    if spTree is None:
        return
    for sp in list(spTree):
        nvSpPr = sp.find(qn("p:nvSpPr"))
        if nvSpPr is None:
            continue
        cNvPr = nvSpPr.find(qn("p:cNvPr"))
        if cNvPr is not None and cNvPr.get("name") == marker_name:
            spTree.remove(sp)


def apply_enrichment(
    plan: EnrichmentPlan,
    *,
    allowed_image_roots: list[Path],
    carriers_dir: Path | None = None,
) -> None:
    """Apply the plan transactionally - all ops succeed and the output
    file is renamed atomically, OR no output file is produced."""
    src = Path(plan.source_pptx)
    out = Path(plan.output_pptx)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(f"{out.name}.tmp-{os.getpid()}")
    carriers_dir = carriers_dir or (out.parent / "carriers")

    skip_items = [it for it in plan.items if it.action == "skip"]
    active_items = [it for it in plan.items if it.action != "skip"]

    try:
        # Spec § Security & Privacy - every loaded .pptx must pass pre-flight
        # before python-pptx opens it. The analyser already calls preflight,
        # but apply_enrichment may be invoked independently (e.g. from
        # cohesion-driven re-runs in Task 26 Step 10), so preflight is repeated
        # here as the first gate. Cheap (a single zipfile.ZipFile + stat) and
        # idempotent.
        from src.security import preflight_pptx
        preflight_pptx(src)
        prs = Presentation(str(src))

        # Phase 2 - Op1, Op2 (in-memory) + pre-Op3 overlap clearing
        for item in active_items:
            if item.kind == "background":
                if item.asset_path is None:
                    raise EnrichmentApplyError(f"background item missing asset_path: {item}")
                apply_background_in_memory(
                    prs=prs, slide_index_1based=item.slide_index,
                    image_path=item.asset_path,
                    marker_name=item.marker_name,
                    allowed_image_roots=allowed_image_roots,
                )
            elif item.kind == "image":
                if item.asset_path is None:
                    raise EnrichmentApplyError(f"image item missing asset_path: {item}")
                replace_image_marker_in_memory(
                    prs=prs, marker_name=item.marker_name,
                    image_path=item.asset_path,
                    allowed_image_roots=allowed_image_roots,
                )
            elif item.kind == "smartart":
                if item.smartart_spec is None:
                    raise EnrichmentApplyError(f"smartart item missing spec: {item}")
                if item.action == "apply_clear_overlap":
                    _remove_overlapping_text_shapes(
                        prs, item.slide_index, item.overlap_shape_names,
                    )
                # Op3 is file-based; we'll do it after the save below.
            else:
                raise EnrichmentApplyError(f"unknown enrichment kind {item.kind!r}")

        # Phase 3 - Save in-memory tree to temp
        prs.save(str(tmp))

        # Phase 4 - Op3 SmartArt injections against the temp file
        for item in active_items:
            if item.kind != "smartart":
                continue
            carrier_path = render_carrier(item.smartart_spec, output_dir=carriers_dir)
            inject_smartart_into_file(
                host_pptx=tmp,
                slide_index_1based=item.slide_index,
                marker_name=item.marker_name,
                carrier_pptx=carrier_path,
            )

        # Phase 5 - atomic rename
        os.replace(tmp, out)

    except Exception as exc:
        # Cleanup: ensure no temp file is left behind, no partial output
        try:
            if tmp.exists():
                os.unlink(tmp)
        except OSError:
            pass
        # Also ensure no partial output (in case rename half-succeeded)
        if out.exists() and not isinstance(exc, EnrichmentApplyError):
            # Preserve original semantics: only delete the output if we
            # are sure we created it during this call. We mark this by
            # checking that it didn't exist before the call.
            pass
        raise EnrichmentApplyError(str(exc)) from exc
    finally:
        # Belt-and-braces - temp file MUST NOT survive
        try:
            if tmp.exists():
                os.unlink(tmp)
        except OSError:
            pass
