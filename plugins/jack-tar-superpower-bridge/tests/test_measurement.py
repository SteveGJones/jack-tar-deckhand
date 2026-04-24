import json
from pathlib import Path

import pytest

from src.measurement import (
    MEASUREMENT_FILENAME,
    COST_LEDGER_FILENAME,
    record_brief_run,
    record_enrichment_run,
    record_cost_event,
    read_measurements,
    read_cost_ledger,
)


def test_record_brief_run_creates_file(tmp_path):
    record_brief_run(cwd=tmp_path, approval_turns=2, structural_complete=True,
                     confidentiality="public")
    f = tmp_path / MEASUREMENT_FILENAME
    assert f.exists()
    lines = f.read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["kind"] == "brief"
    assert entry["approval_turns"] == 2
    assert entry["structural_complete"] is True
    assert entry["confidentiality"] == "public"
    assert "timestamp" in entry


def test_brief_runs_append(tmp_path):
    record_brief_run(cwd=tmp_path, approval_turns=1, structural_complete=True,
                     confidentiality="public")
    record_brief_run(cwd=tmp_path, approval_turns=3, structural_complete=False,
                     confidentiality="internal")
    entries = read_measurements(tmp_path)
    assert len(entries) == 2
    assert entries[1]["approval_turns"] == 3


def test_record_enrichment_run_captures_personas(tmp_path):
    record_enrichment_run(
        cwd=tmp_path,
        adherence_rate=0.875,                # markers requested vs delivered
        first_pass_acceptance=True,           # cohesion reviewer didn't block
        slides_enriched=4,
        slides_total=10,
    )
    entries = read_measurements(tmp_path)
    assert len(entries) == 1
    e = entries[0]
    assert e["kind"] == "enrichment"
    assert e["adherence_rate"] == 0.875
    assert e["first_pass_acceptance"] is True
    assert e["slides_enriched"] == 4


def test_record_cost_event_writes_ledger(tmp_path):
    record_cost_event(cwd=tmp_path, kind="generation",
                       provider="nanobanana_flash", cost_usd=0.067,
                       slide_index=3, marker_id="IMAGE:foo")
    record_cost_event(cwd=tmp_path, kind="review",
                       provider="haiku", cost_usd=0.001,
                       slide_index=3, marker_id="IMAGE:foo")
    ledger = read_cost_ledger(tmp_path)
    assert len(ledger) == 2
    assert ledger[0]["kind"] == "generation"
    assert ledger[1]["kind"] == "review"
    total = sum(e["cost_usd"] for e in ledger)
    assert total == pytest.approx(0.068)


def test_cost_event_kinds_validated(tmp_path):
    with pytest.raises(ValueError, match="kind"):
        record_cost_event(cwd=tmp_path, kind="dance",
                           provider="x", cost_usd=0, slide_index=1, marker_id=None)


def test_read_returns_empty_when_no_file(tmp_path):
    assert read_measurements(tmp_path) == []
    assert read_cost_ledger(tmp_path) == []
