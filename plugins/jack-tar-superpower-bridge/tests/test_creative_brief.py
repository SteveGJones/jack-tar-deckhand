import pytest
from pathlib import Path

from src.creative_brief import (
    CreativeBrief,
    CreativeBriefValidationError,
    parse_brief_markdown,
    write_brief_markdown,
    DEFAULT_BUDGET_CAP_USD,
)


def test_default_confidentiality_is_public():
    brief = CreativeBrief(
        topic="AI agents",
        audience="developers",
        duration_minutes=20,
        narrative_arc="Problem-Solution",
        narrative_detail="open with provocative question",
        audience_takeaway="agents need explicit architecture",
        tone="confident but approachable",
        visual_personality="dark, atmospheric, architectural metaphors",
        placeholder_instructions="describes IMAGE/SMARTART/BG marker types only",
    )
    assert brief.confidentiality == "public"
    assert brief.budget_cap_usd == DEFAULT_BUDGET_CAP_USD


def test_validation_rejects_unknown_confidentiality():
    with pytest.raises(CreativeBriefValidationError, match="confidentiality"):
        CreativeBrief(
            topic="x", audience="x", duration_minutes=5, narrative_arc="x",
            narrative_detail="x", audience_takeaway="x", tone="x",
            visual_personality="x", placeholder_instructions="x",
            confidentiality="confidential",
        )


def test_validation_rejects_negative_budget():
    with pytest.raises(CreativeBriefValidationError, match="budget_cap_usd"):
        CreativeBrief(
            topic="x", audience="x", duration_minutes=5, narrative_arc="x",
            narrative_detail="x", audience_takeaway="x", tone="x",
            visual_personality="x", placeholder_instructions="x",
            budget_cap_usd=-0.5,
        )


def test_validation_rejects_zero_duration():
    with pytest.raises(CreativeBriefValidationError, match="duration_minutes"):
        CreativeBrief(
            topic="x", audience="x", duration_minutes=0, narrative_arc="x",
            narrative_detail="x", audience_takeaway="x", tone="x",
            visual_personality="x", placeholder_instructions="x",
        )


def test_to_markdown_contains_all_sections():
    brief = CreativeBrief(
        topic="AI agents", audience="developers", duration_minutes=20,
        narrative_arc="Problem-Solution",
        narrative_detail="Open with a provocative question",
        audience_takeaway="agents need explicit architecture",
        tone="confident",
        visual_personality="dark backgrounds, accent teal",
        placeholder_instructions="IMAGE for hero illustrations; SMARTART for processes; BG for atmospheric backgrounds. Use objectName property in PptxGenJS.",
    )
    md = brief.to_markdown()
    assert "## Section A — Narrative Architecture" in md
    assert "## Section B — Communication & Visual Intent" in md
    assert "## Section C — Placeholder Instructions" in md
    assert "objectName" in md
    assert "Confidentiality: public" in md


def test_roundtrip_through_markdown():
    brief = CreativeBrief(
        topic="agents", audience="devs", duration_minutes=15,
        narrative_arc="Hero's Journey", narrative_detail="hero starts naive",
        audience_takeaway="empathy unlocks design",
        tone="warm",
        visual_personality="cinematic, golden-hour palette",
        placeholder_instructions="three IMAGE markers max",
        confidentiality="internal",
        budget_cap_usd=2.50,
    )
    parsed = parse_brief_markdown(brief.to_markdown())
    assert parsed.topic == "agents"
    assert parsed.confidentiality == "internal"
    assert parsed.budget_cap_usd == 2.50
    assert parsed.narrative_arc == "Hero's Journey"


def test_write_and_read_brief_file(tmp_path):
    brief = CreativeBrief(
        topic="t", audience="a", duration_minutes=10, narrative_arc="x",
        narrative_detail="x", audience_takeaway="x", tone="x",
        visual_personality="x", placeholder_instructions="x",
    )
    out = tmp_path / "creative-brief.md"
    write_brief_markdown(brief, out)
    assert out.exists()
    parsed = parse_brief_markdown(out.read_text())
    assert parsed.topic == "t"


def test_parse_rejects_missing_section():
    incomplete = (
        "# Creative Brief\n\n"
        "**Topic:** x\n**Audience:** y\n**Duration:** 10 min\n"
        "**Confidentiality:** public\n**Budget cap:** $1.00\n\n"
        "## Section A — Narrative Architecture\n\n"
        "**Arc:** x\n\nx\n\n"
        "## Section B — Communication & Visual Intent\n\n"
        "**Audience takeaway:** x\n**Tone:** x\n**Visual personality:** x\n"
    )
    with pytest.raises(CreativeBriefValidationError, match="Section C"):
        parse_brief_markdown(incomplete)
