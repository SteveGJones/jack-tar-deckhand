"""Structured enrichment-report.md writer.

Schema enforced — required sections in canonical order, fixed table columns.
The format is parseable for regression tests and aggregate-cost analysis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class EnrichmentLedgerEntry:
    slide_index: int
    kind: str               # background | image | smartart
    marker_id: str
    engine_provider: str    # e.g. "ollama→nanobanana_flash" or "pptx_native (process1)"
    iterations: str         # "2→1" or "n/a"
    cost_usd: float
    verdict: str            # pass | flag_contrast | etc.


@dataclass
class EnrichmentReport:
    deck_name: str
    source_pptx: Path
    output_pptx: Path
    bridge_version: str
    confidentiality: str
    budget_cap_usd: float
    ledger: list[EnrichmentLedgerEntry]
    cohesion_summary: dict[str, Any]
    contains_smartart: bool
    run_timestamp: datetime


def _format_summary(report: EnrichmentReport, total_cost: float) -> str:
    return (
        f"## Summary\n\n"
        f"- Slides enriched: {len(report.ledger)} of (deck total)\n"
        f"- Enrichments applied: "
        f"backgrounds={sum(1 for e in report.ledger if e.kind == 'background')}, "
        f"images={sum(1 for e in report.ledger if e.kind == 'image')}, "
        f"smartart={sum(1 for e in report.ledger if e.kind == 'smartart')}\n"
        f"- Total cost: ${total_cost:.2f}\n"
        f"- Budget cap: ${report.budget_cap_usd:.2f} "
        f"(${report.budget_cap_usd - total_cost:.2f} unused)\n"
        f"- Confidentiality tier: {report.confidentiality}\n"
        f"- Cohesion review: pass={report.cohesion_summary.get('pass_count', 0)}, "
        f"suggestions={report.cohesion_summary.get('suggestion_count', 0)}, "
        f"blocking={report.cohesion_summary.get('blocking_count', 0)}\n\n"
    )


def _format_ledger_table(ledger: list[EnrichmentLedgerEntry]) -> str:
    header = (
        "| Slide | Type | Marker | Engine/Provider | Iterations | Cost | Verdict |\n"
        "|-------|------|--------|-----------------|------------|------|---------|\n"
    )
    rows = "".join(
        f"| {e.slide_index} | {e.kind} | {e.marker_id} | {e.engine_provider} "
        f"| {e.iterations} | ${e.cost_usd:.3f} | {e.verdict} |\n"
        for e in ledger
    )
    return f"## Per-enrichment ledger\n\n{header}{rows}\n"


def _format_flags(cohesion_summary: dict[str, Any]) -> str:
    actions = cohesion_summary.get("actions", [])
    if not actions:
        return "## Flags for user attention\n\n_No flags raised by the cohesion reviewer._\n\n"
    lines = "## Flags for user attention\n\n"
    for a in actions:
        lines += (
            f"- Slide {a['slide_index']} ({a['verdict']}, {a['severity']}): "
            f"{a['reason']}. Action: {a['action']} — {a['guidance']}\n"
        )
    return lines + "\n"


def _format_powerpoint_note(contains_smartart: bool, output_pptx: Path) -> str:
    if not contains_smartart:
        return ("## PowerPoint rendering note\n\n"
                "_No SmartArt enrichments — LibreOffice PDF export should render the deck faithfully._\n")
    return (
        "## PowerPoint rendering note\n\n"
        "This deck contains injected SmartArt. LibreOffice's PDF export does not render "
        "SmartArt correctly; for an authoritative PDF, open the deck in PowerPoint Mac, "
        "Save (forces SmartArt cache regen), then export to PDF. The repo helper:\n\n"
        f"```bash\ntools/pptx_to_pdf.sh {output_pptx}\n```\n"
    )


def write_report(report: EnrichmentReport, out_path: Path) -> None:
    total_cost = sum(e.cost_usd for e in report.ledger)
    body = (
        f"# Enrichment Report — {report.deck_name}\n\n"
        f"**Source:** {report.source_pptx}\n"
        f"**Output:** {report.output_pptx}\n"
        f"**Run timestamp:** {report.run_timestamp.isoformat()}\n"
        f"**Bridge version:** {report.bridge_version}\n\n"
        + _format_summary(report, total_cost)
        + _format_ledger_table(report.ledger)
        + _format_flags(report.cohesion_summary)
        + _format_powerpoint_note(report.contains_smartart, report.output_pptx)
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body)
