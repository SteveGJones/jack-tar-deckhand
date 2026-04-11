"""Pipeline integration for pptx_native.

The functions in this module are the glue between:

  (a) The existing Python smartart_renderer, which produces per-slide
      "carrier" .pptx files when it encounters engine='pptx_native'
      spec entries, and writes their paths into smartart-manifest.json

  (b) The Node `src/assembler/build_deck.js`, which reads the manifest
      and places a named placeholder rect on each pptx_native slide
      (see Phase 3.2)

  (c) The Phase 3.1 `assembler_patch.inject()` module, which grafts
      the carrier diagram parts into the assembled deck .pptx

Orchestration skills / scripts should call `run_injection_step()`
AFTER `build_deck.js` has finished writing
`<deck_dir>/output/presentation.pptx`. It reads the smartart manifest,
finds every pptx_native entry, and runs `inject()` with one
InjectionRequest per entry.

Slides that don't use pptx_native (or decks with no smartart at all)
are no-ops — `run_injection_step` returns an empty list cleanly.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.assembler_patch import (
    InjectionError,
    InjectionRequest,
    InjectionResult,
    inject,
)

DEFAULT_OUTPUT_RELPATH = "output/presentation.pptx"
SMARTART_MANIFEST_RELPATH = "smartart-manifest.json"


@dataclass
class InjectionStepResult:
    """Summary of running run_injection_step on a deck directory."""

    deck_dir: Path
    assembled_pptx: Path
    injected_count: int
    results: list[InjectionResult]
    skipped_non_pptx_native: int


def _load_manifest(deck_dir: Path) -> dict[str, Any]:
    path = deck_dir / SMARTART_MANIFEST_RELPATH
    if not path.exists():
        return {"graphics": []}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_requests(
    manifest: dict[str, Any], deck_dir: Path
) -> list[InjectionRequest]:
    """Walk the manifest and construct one InjectionRequest per
    pptx_native entry that has status='rendered'.

    Paths in the manifest's `file_path` field can be absolute
    (typical — the renderer writes an absolute path) or relative to
    the deck directory. Both are handled.
    """
    requests: list[InjectionRequest] = []
    for entry in manifest.get("graphics", []):
        if entry.get("engine_used") != "pptx_native":
            continue
        if entry.get("status") != "rendered":
            # Failed or partially-rendered entries cannot be injected
            continue
        file_path = entry.get("file_path", "")
        if not file_path:
            continue
        carrier_path = Path(file_path)
        if not carrier_path.is_absolute():
            carrier_path = (deck_dir / carrier_path).resolve()
        requests.append(
            InjectionRequest(
                slide_number=entry["slide_number"],
                carrier_pptx=carrier_path,
            )
        )
    return requests


def run_injection_step(
    deck_dir: str | Path,
    assembled_pptx: str | Path | None = None,
) -> InjectionStepResult:
    """Run the pptx_native injection step against an assembled deck.

    This is the function orchestration scripts call after
    `build_deck.js` has finished writing the deck .pptx. It reads
    the smartart manifest, collects pptx_native entries with
    status='rendered', and injects each one's diagram parts into
    the assembled deck.

    Args:
        deck_dir: Path to the DeckContext directory containing
            smartart-manifest.json.
        assembled_pptx: Optional override for the assembled .pptx
            path. Defaults to `<deck_dir>/output/presentation.pptx`.

    Returns:
        InjectionStepResult summarising what was injected.

    Raises:
        InjectionError: If the manifest is unreadable, the assembled
            .pptx is missing, or any single injection fails.
    """
    deck_dir = Path(deck_dir)
    if assembled_pptx is None:
        assembled_pptx = deck_dir / DEFAULT_OUTPUT_RELPATH
    else:
        assembled_pptx = Path(assembled_pptx)

    manifest = _load_manifest(deck_dir)
    requests = build_requests(manifest, deck_dir)
    skipped = sum(
        1 for g in manifest.get("graphics", [])
        if g.get("engine_used") != "pptx_native"
    )

    if not requests:
        return InjectionStepResult(
            deck_dir=deck_dir,
            assembled_pptx=assembled_pptx,
            injected_count=0,
            results=[],
            skipped_non_pptx_native=skipped,
        )

    if not assembled_pptx.exists():
        raise InjectionError(
            f"assembled .pptx missing: {assembled_pptx}. "
            "Run build_deck.js first."
        )

    results = inject(host_pptx=assembled_pptx, requests=requests)

    return InjectionStepResult(
        deck_dir=deck_dir,
        assembled_pptx=assembled_pptx,
        injected_count=len(results),
        results=results,
        skipped_non_pptx_native=skipped,
    )


# ---------------------------------------------------------------------------
# Phase 6 — delivery messaging
# ---------------------------------------------------------------------------

def format_delivery_message(
    deck_dir: str | Path,
    manifest: dict[str, Any] | None = None,
) -> str | None:
    """Format a speaker-facing delivery status message if the deck
    contains pptx_native SmartArt.

    The conductor / orchestration script prints this after the deck
    is finalised so the speaker knows to open the file in PowerPoint
    Mac for visual verification (spec §7). pptx_native slides cannot
    be previewed by the automated pipeline — LibreOffice can't render
    them — so PowerPoint Mac open is the only meaningful pre-delivery
    check.

    Args:
        deck_dir: Path to the DeckContext directory. Used to read
            smartart-manifest.json (or outline.json for headlines)
            if manifest is not provided directly.
        manifest: Optional pre-loaded manifest dict. If None, the
            function reads from `<deck_dir>/smartart-manifest.json`.

    Returns:
        A multi-line string ready to print, OR None if the deck has
        no pptx_native slides (no message needed). Returning None
        lets the caller skip the print entirely without conditional
        logic on message truthiness.
    """
    deck_dir = Path(deck_dir)

    if manifest is None:
        manifest = _load_manifest(deck_dir)

    pptx_native_entries = [
        g for g in manifest.get("graphics", [])
        if g.get("engine_used") == "pptx_native"
        and g.get("status") in ("rendered", "compared")
    ]

    if not pptx_native_entries:
        return None

    # Try to pair each entry with its slide headline from outline.json
    headlines: dict[int, str] = {}
    outline_path = deck_dir / "outline.json"
    if outline_path.exists():
        try:
            outline = json.loads(outline_path.read_text(encoding="utf-8"))
            for slide in outline.get("slides", []):
                sn = slide.get("slide_number")
                if sn is not None:
                    headlines[sn] = slide.get("headline", "")
        except (OSError, json.JSONDecodeError):
            pass  # fall through — headlines just become empty

    n = len(pptx_native_entries)
    plural = "s" if n != 1 else ""
    lines: list[str] = []
    lines.append(
        f"{n} slide{plural} use{'s' if n == 1 else ''} editable PowerPoint "
        f"SmartArt (pptx_native engine)."
    )
    lines.append(
        "These were not pre-rendered — please open the .pptx in PowerPoint "
        "Mac to verify visual quality before presenting."
    )
    lines.append("")
    lines.append(f"Slide{plural} with editable SmartArt:")

    # Sort by slide number for deterministic output
    sorted_entries = sorted(
        pptx_native_entries, key=lambda e: e.get("slide_number", 0)
    )
    for entry in sorted_entries:
        sn = entry.get("slide_number", "?")
        graphic_type = entry.get("graphic_type", "unknown")
        node_count = entry.get("node_count", 0)
        headline = headlines.get(sn, "").strip()

        # Format: "  Slide  4: process diagram (5 nodes) — Our Method"
        headline_suffix = f" — {headline}" if headline else ""
        # node_count unit depends on graphic_type
        if graphic_type == "flowchart":
            unit = "step" if node_count == 1 else "steps"
        elif graphic_type == "cycle":
            unit = "stage" if node_count == 1 else "stages"
        elif graphic_type == "org_chart":
            unit = "node" if node_count == 1 else "nodes"
        else:
            unit = "node" if node_count == 1 else "nodes"

        type_label = {
            "flowchart": "process diagram",
            "cycle": "cycle diagram",
            "org_chart": "org chart",
        }.get(graphic_type, graphic_type)

        lines.append(
            f"  Slide {sn:>2}: {type_label} ({node_count} {unit})"
            f"{headline_suffix}"
        )

    return "\n".join(lines)
