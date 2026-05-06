"""Measurement instrumentation for the bridge personas (caveat #3, P0).

Two record kinds emitted to a single newline-delimited JSON file:
  - brief    — one row per /bridge-brief run (approval_turns, structural_complete, confidentiality)
  - enrichment — one row per /enrich-deck run (adherence_rate, first_pass_acceptance, slides_enriched, slides_total)

Cost ledger is a separate file, one row per cloud event. The image_bridge
records both generation AND review events here (caveat #6: budget cap
covers review, not just generation).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MEASUREMENT_FILENAME = "bridge-measurements.jsonl"
COST_LEDGER_FILENAME = "bridge-cost-ledger.jsonl"

VALID_COST_KINDS = {
    "generation",       # cloud image gen (Phase B Flash, Phase C Pro)
    "review",           # per-image image-reviewer (Haiku)
    "cohesion",         # deck-level enrichment-cohesion-reviewer (Sonnet) — Run 5 Finding #18
    "brief_authoring",  # Phase 1 narrative-brief-architect dispatches — Run 2 Finding #8
}
VALID_CONFIDENTIALITY = {"public", "internal", "restricted"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append(path: Path, entry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def record_brief_run(
    *,
    cwd: Path,
    approval_turns: int,
    structural_complete: bool,
    confidentiality: str,
) -> None:
    if confidentiality not in VALID_CONFIDENTIALITY:
        raise ValueError(f"confidentiality {confidentiality!r} not in {VALID_CONFIDENTIALITY}")
    _append(cwd / MEASUREMENT_FILENAME, {
        "kind": "brief",
        "timestamp": _now_iso(),
        "approval_turns": approval_turns,
        "structural_complete": structural_complete,
        "confidentiality": confidentiality,
    })


def record_enrichment_run(
    *,
    cwd: Path,
    adherence_rate: float,
    first_pass_acceptance: bool,
    slides_enriched: int,
    slides_total: int,
) -> None:
    _append(cwd / MEASUREMENT_FILENAME, {
        "kind": "enrichment",
        "timestamp": _now_iso(),
        "adherence_rate": adherence_rate,
        "first_pass_acceptance": first_pass_acceptance,
        "slides_enriched": slides_enriched,
        "slides_total": slides_total,
    })


def record_cost_event(
    *,
    cwd: Path,
    kind: str,
    provider: str,
    cost_usd: float,
    slide_index: int | None,
    marker_id: str | None,
) -> None:
    if kind not in VALID_COST_KINDS:
        raise ValueError(f"kind {kind!r} not in {VALID_COST_KINDS}")
    _append(cwd / COST_LEDGER_FILENAME, {
        "kind": kind,
        "timestamp": _now_iso(),
        "provider": provider,
        "cost_usd": cost_usd,
        "slide_index": slide_index,
        "marker_id": marker_id,
    })


def read_measurements(cwd: Path) -> list[dict[str, Any]]:
    p = cwd / MEASUREMENT_FILENAME
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def read_cost_ledger(cwd: Path) -> list[dict[str, Any]]:
    p = cwd / COST_LEDGER_FILENAME
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
