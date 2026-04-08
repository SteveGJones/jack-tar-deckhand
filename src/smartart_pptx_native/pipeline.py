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

from src.smartart_pptx_native.assembler_patch import (
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
