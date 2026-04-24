from datetime import datetime
from pathlib import Path

import pytest

from src.enrichment_report import (
    EnrichmentLedgerEntry,
    EnrichmentReport,
    write_report,
)


def _sample_entries():
    return [
        EnrichmentLedgerEntry(
            slide_index=1, kind="background", marker_id="BG:dramatic-opening",
            engine_provider="ollama→nanobanana_flash", iterations="2→1",
            cost_usd=0.067, verdict="pass",
        ),
        EnrichmentLedgerEntry(
            slide_index=3, kind="image", marker_id="IMAGE:agent-architecture",
            engine_provider="ollama", iterations="1", cost_usd=0.00, verdict="pass",
        ),
        EnrichmentLedgerEntry(
            slide_index=5, kind="smartart", marker_id="SMARTART:three-pillars",
            engine_provider="pptx_native (process1)", iterations="n/a",
            cost_usd=0.00, verdict="pass",
        ),
    ]


def test_report_contains_required_sections(tmp_path):
    report = EnrichmentReport(
        deck_name="my-talk",
        source_pptx=tmp_path / "src.pptx",
        output_pptx=tmp_path / "out.pptx",
        bridge_version="0.1.0",
        confidentiality="public",
        budget_cap_usd=1.00,
        ledger=_sample_entries(),
        cohesion_summary={"pass_count": 3, "suggestion_count": 0,
                           "blocking_count": 0, "actions": []},
        contains_smartart=True,
        run_timestamp=datetime(2026, 4, 23, 12, 0, 0),
    )
    out_path = tmp_path / "enrichment-report.md"
    write_report(report, out_path)
    text = out_path.read_text()
    assert "# Enrichment Report — my-talk" in text
    assert "## Summary" in text
    assert "## Per-enrichment ledger" in text
    assert "## Flags for user attention" in text
    assert "## PowerPoint rendering note" in text


def test_report_summary_counts_correct(tmp_path):
    report = EnrichmentReport(
        deck_name="t", source_pptx=tmp_path / "s.pptx", output_pptx=tmp_path / "o.pptx",
        bridge_version="0.1.0", confidentiality="public", budget_cap_usd=1.00,
        ledger=_sample_entries(),
        cohesion_summary={"pass_count": 3, "suggestion_count": 0,
                           "blocking_count": 0, "actions": []},
        contains_smartart=False,
        run_timestamp=datetime(2026, 4, 23, 12, 0, 0),
    )
    out = tmp_path / "report.md"
    write_report(report, out)
    text = out.read_text()
    assert "Slides enriched: 3" in text
    assert "Total cost: $0.07" in text
    assert "Confidentiality tier: public" in text


def test_report_ledger_table_columns(tmp_path):
    report = EnrichmentReport(
        deck_name="t", source_pptx=tmp_path / "s.pptx", output_pptx=tmp_path / "o.pptx",
        bridge_version="0.1.0", confidentiality="public", budget_cap_usd=1.00,
        ledger=_sample_entries(),
        cohesion_summary={"pass_count": 3, "suggestion_count": 0,
                           "blocking_count": 0, "actions": []},
        contains_smartart=False,
        run_timestamp=datetime(2026, 4, 23, 12, 0, 0),
    )
    out = tmp_path / "r.md"
    write_report(report, out)
    text = out.read_text()
    # Required column headers in canonical order
    assert "| Slide | Type | Marker | Engine/Provider | Iterations | Cost | Verdict |" in text


def test_report_smartart_flag_includes_powerpoint_command(tmp_path):
    report = EnrichmentReport(
        deck_name="t", source_pptx=tmp_path / "s.pptx", output_pptx=tmp_path / "o.pptx",
        bridge_version="0.1.0", confidentiality="public", budget_cap_usd=1.00,
        ledger=_sample_entries(),
        cohesion_summary={"pass_count": 3, "suggestion_count": 0,
                           "blocking_count": 0, "actions": []},
        contains_smartart=True,
        run_timestamp=datetime(2026, 4, 23, 12, 0, 0),
    )
    out = tmp_path / "r.md"
    write_report(report, out)
    text = out.read_text()
    assert "tools/pptx_to_pdf.sh" in text


def test_cohesion_actions_reproduced_in_flags_section(tmp_path):
    report = EnrichmentReport(
        deck_name="t", source_pptx=tmp_path / "s.pptx", output_pptx=tmp_path / "o.pptx",
        bridge_version="0.1.0", confidentiality="public", budget_cap_usd=1.00,
        ledger=_sample_entries(),
        cohesion_summary={
            "pass_count": 2, "suggestion_count": 1, "blocking_count": 0,
            "actions": [{
                "slide_index": 5, "verdict": "flag_contrast",
                "severity": "suggestion", "action": "record_only",
                "guidance": "borderline contrast", "reason": "borderline",
            }],
        },
        contains_smartart=False,
        run_timestamp=datetime(2026, 4, 23, 12, 0, 0),
    )
    out = tmp_path / "r.md"
    write_report(report, out)
    text = out.read_text()
    assert "slide 5" in text.lower() or "Slide 5" in text
    assert "flag_contrast" in text
