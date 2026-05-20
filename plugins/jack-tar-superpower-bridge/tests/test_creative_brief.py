import pytest
from pathlib import Path
from textwrap import dedent

from src.creative_brief import (
    CreativeBrief,
    CreativeBriefValidationError,
    parse_brief_markdown,
    write_brief_markdown,
    extract_expected_text_for_marker,
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


# ---------------------------------------------------------------------------
# Expected-text extraction (Run 6 Findings #19/#20)
# ---------------------------------------------------------------------------
#
# The image-reviewer agent confabulates spelling correctness when it has no
# explicit reference list to compare against (Finding #19 — "INFORENCE" passed
# Phase A review on Run 6 slide 4). With an explicit list, it reliably catches
# misspellings (Finding #20). The narrative-brief-architect agent now writes
# Section C subject briefs with a per-marker block:
#
#     > Schematic integration diagram. Two ox-blood blocks side by side.
#     >
#     > EXACT spelled labels REQUIRED:
#     > - block-left: "Our Platform"
#     > - block-right: "Tessera Edge Stack"
#     > - top-arrow: "API Gateway"
#
# ``extract_expected_text_for_marker`` is the deterministic Python helper the
# /enrich-deck SKILL.md uses to lift those quoted strings out of the brief
# and inject them into the image-reviewer dispatch payload.


def _brief_with_section_c(section_c: str) -> str:
    """Build a minimally-valid brief whose Section C is the supplied text."""
    return dedent(
        """\
        # Creative Brief

        **Topic:** Project Cardinal
        **Audience:** Board
        **Duration:** 15 min
        **Confidentiality:** internal
        **Budget cap:** $5.00

        ## Section A — Narrative Architecture

        **Arc:** Investigation-Verdict

        narrative

        ## Section B — Communication & Visual Intent

        **Audience takeaway:** approve
        **Tone:** institutional
        **Visual personality:** ivory + ox-blood

        ## Section C — Placeholder Instructions

        """
    ) + section_c


def test_extract_expected_text_for_marker_blockquote_format():
    """The canonical agent-produced format — markdown blockquote, EXACT header,
    bulleted role-and-quoted-string lines."""
    section_c = dedent(
        """\
        Slide 9 — Strategic fit. `IMAGE:strategic-fit-diagram` at full content.

        > Schematic integration diagram. Two ox-blood burgundy blocks side by side, three labelled arrows between them.
        >
        > EXACT spelled labels REQUIRED:
        > - block-left: "Our Platform"
        > - block-right: "Tessera Edge Stack"
        > - top-arrow: "API Gateway"
        > - middle-arrow: "Model Registry"
        > - bottom-arrow: "Billing Layer"
        """
    )
    brief = _brief_with_section_c(section_c)
    expected = extract_expected_text_for_marker(brief, "IMAGE:strategic-fit-diagram")
    assert expected == [
        "Our Platform",
        "Tessera Edge Stack",
        "API Gateway",
        "Model Registry",
        "Billing Layer",
    ]


def test_extract_expected_text_for_marker_unblockquoted_format():
    """Authors who drop the `>` blockquote prefix should still parse cleanly."""
    section_c = dedent(
        """\
        Slide 7 — Customer footprint. `IMAGE:customer-logo-grid` at full content.

        Subject: 7-logo client grid (fintech + healthcare).

        EXACT spelled labels REQUIRED:
        - logo-1: "Halberd Capital"
        - logo-2: "Meridian Bank"
        - logo-3: "Procyon Pharma"
        - logo-4: "Nivera Diagnostics"
        """
    )
    brief = _brief_with_section_c(section_c)
    expected = extract_expected_text_for_marker(brief, "IMAGE:customer-logo-grid")
    assert expected == [
        "Halberd Capital",
        "Meridian Bank",
        "Procyon Pharma",
        "Nivera Diagnostics",
    ]


def test_extract_expected_text_for_marker_returns_empty_when_no_label_block():
    """Markers without an EXACT block (atmospheric backgrounds, etc.) return []
    so the SKILL.md can decide whether to dispatch the reviewer with or
    without expected_text_content."""
    section_c = dedent(
        """\
        Slide 10 — Pivot. `BG:pivot-moment` full-bleed.

        Atmospheric warm vellum texture, no overlaid text.
        """
    )
    brief = _brief_with_section_c(section_c)
    assert extract_expected_text_for_marker(brief, "BG:pivot-moment") == []


def test_extract_expected_text_for_marker_isolates_to_target_marker():
    """When two markers each have an EXACT block, extraction must stop at the
    next marker reference rather than spilling into the following block."""
    section_c = dedent(
        """\
        Slide 6 — Edge Stack architecture. `IMAGE:edge-stack-architecture`.

        > EXACT spelled labels REQUIRED:
        > - node-1: "Client Edge Nodes"
        > - node-2: "Inference Layer"

        Slide 9 — Strategic fit. `IMAGE:strategic-fit-diagram`.

        > EXACT spelled labels REQUIRED:
        > - block-left: "Our Platform"
        > - block-right: "Tessera Edge Stack"
        """
    )
    brief = _brief_with_section_c(section_c)
    edge = extract_expected_text_for_marker(brief, "IMAGE:edge-stack-architecture")
    assert edge == ["Client Edge Nodes", "Inference Layer"]
    fit = extract_expected_text_for_marker(brief, "IMAGE:strategic-fit-diagram")
    assert fit == ["Our Platform", "Tessera Edge Stack"]


def test_extract_expected_text_for_marker_unknown_marker_returns_empty():
    """A marker_id not present anywhere in the brief returns [] without
    raising — Section C may legitimately omit a marker if /pptx authored it
    but the brief never described it (degraded but recoverable case)."""
    section_c = dedent(
        """\
        Slide 1 — Title only.
        """
    )
    brief = _brief_with_section_c(section_c)
    assert extract_expected_text_for_marker(brief, "IMAGE:nowhere") == []


def test_extract_expected_text_for_marker_only_searches_section_c():
    """An EXACT block elsewhere in the brief (e.g. quoted in Section A as an
    example) must NOT be picked up when the marker isn't actually defined in
    Section C — preventing false positives from narrative prose."""
    brief = dedent(
        """\
        # Creative Brief

        **Topic:** t
        **Audience:** a
        **Duration:** 15 min
        **Confidentiality:** public
        **Budget cap:** $1.00

        ## Section A — Narrative Architecture

        **Arc:** x

        Reference example: an `IMAGE:foo` marker might use:

        > EXACT spelled labels REQUIRED:
        > - example: "Should Not Match"

        ## Section B — Communication & Visual Intent

        **Audience takeaway:** x
        **Tone:** x
        **Visual personality:** x

        ## Section C — Placeholder Instructions

        Slide 1 — Title only.
        """
    )
    assert extract_expected_text_for_marker(brief, "IMAGE:foo") == []


# ---------------------------------------------------------------------------
# Issue #93 — strap_style field
# ---------------------------------------------------------------------------


def test_strap_style_defaults_to_none():
    """Persona chooses when the speaker doesn't pin it."""
    brief = CreativeBrief(
        topic="t", audience="a", duration_minutes=10, narrative_arc="x",
        narrative_detail="x", audience_takeaway="x", tone="x",
        visual_personality="x", placeholder_instructions="x",
    )
    assert brief.strap_style is None


def test_strap_style_accepts_prose_sentence():
    brief = CreativeBrief(
        topic="t", audience="a", duration_minutes=10, narrative_arc="x",
        narrative_detail="x", audience_takeaway="x", tone="x",
        visual_personality="x", placeholder_instructions="x",
        strap_style="prose-sentence",
    )
    assert brief.strap_style == "prose-sentence"


def test_strap_style_accepts_all_caps_three_beat():
    brief = CreativeBrief(
        topic="t", audience="a", duration_minutes=10, narrative_arc="x",
        narrative_detail="x", audience_takeaway="x", tone="x",
        visual_personality="x", placeholder_instructions="x",
        strap_style="all-caps-three-beat",
    )
    assert brief.strap_style == "all-caps-three-beat"


def test_strap_style_rejects_unknown_value():
    with pytest.raises(CreativeBriefValidationError, match="strap_style"):
        CreativeBrief(
            topic="t", audience="a", duration_minutes=10, narrative_arc="x",
            narrative_detail="x", audience_takeaway="x", tone="x",
            visual_personality="x", placeholder_instructions="x",
            strap_style="title-case",
        )


def test_strap_style_omitted_from_markdown_when_none():
    """Absence signals 'persona chooses' — must not bake a default into the file."""
    brief = CreativeBrief(
        topic="t", audience="a", duration_minutes=10, narrative_arc="x",
        narrative_detail="x", audience_takeaway="x", tone="x",
        visual_personality="x", placeholder_instructions="x",
    )
    assert "Strap style:" not in brief.to_markdown()


def test_strap_style_emitted_in_markdown_when_set():
    brief = CreativeBrief(
        topic="t", audience="a", duration_minutes=10, narrative_arc="x",
        narrative_detail="x", audience_takeaway="x", tone="x",
        visual_personality="x", placeholder_instructions="x",
        strap_style="all-caps-three-beat",
    )
    md = brief.to_markdown()
    assert "Strap style: all-caps-three-beat" in md
    # Sanity — line sits in the header block before Section A
    assert md.index("Strap style:") < md.index("## Section A")


def test_strap_style_roundtrips_through_markdown():
    brief = CreativeBrief(
        topic="agents", audience="devs", duration_minutes=15,
        narrative_arc="Hero's Journey", narrative_detail="hero starts naive",
        audience_takeaway="empathy unlocks design", tone="warm",
        visual_personality="cinematic, golden-hour palette",
        placeholder_instructions="three IMAGE markers max",
        strap_style="prose-sentence",
    )
    parsed = parse_brief_markdown(brief.to_markdown())
    assert parsed.strap_style == "prose-sentence"


def test_legacy_brief_without_strap_style_parses_to_none():
    """Briefs written before #93 (no Strap style line) parse unchanged."""
    legacy = dedent(
        """\
        # Creative Brief

        Topic: legacy deck
        Audience: speakers
        Duration: 10 min
        Confidentiality: public
        Budget cap: $1.00

        ## Section A — Narrative Architecture

        Arc: Problem-Solution

        Open with a question.

        ## Section B — Communication & Visual Intent

        Audience takeaway: x
        Tone: warm
        Visual personality: clean

        ## Section C — Placeholder Instructions

        Use IMAGE markers sparingly.
        """
    )
    parsed = parse_brief_markdown(legacy)
    assert parsed.strap_style is None


def test_strap_style_parser_ignores_section_a_prose_match():
    """A Section A narrative line that mentions 'Strap style: prose-sentence'
    must NOT be picked up as the header field — the parser scopes its search
    to the pre-Section-A header region."""
    text = dedent(
        """\
        # Creative Brief

        Topic: t
        Audience: a
        Duration: 10 min
        Confidentiality: public
        Budget cap: $1.00

        ## Section A — Narrative Architecture

        Arc: Problem-Solution

        We considered Strap style: prose-sentence vs all-caps but
        decided to let the persona pick.

        ## Section B — Communication & Visual Intent

        Audience takeaway: x
        Tone: x
        Visual personality: x

        ## Section C — Placeholder Instructions

        Use IMAGE markers sparingly.
        """
    )
    parsed = parse_brief_markdown(text)
    assert parsed.strap_style is None


def test_strap_style_parser_accepts_bold_label():
    """The label may be **bold** like the other header fields."""
    text = dedent(
        """\
        # Creative Brief

        **Topic:** t
        **Audience:** a
        **Duration:** 10 min
        **Confidentiality:** public
        **Budget cap:** $1.00
        **Strap style:** all-caps-three-beat

        ## Section A — Narrative Architecture

        **Arc:** Problem-Solution

        prose.

        ## Section B — Communication & Visual Intent

        **Audience takeaway:** x
        **Tone:** x
        **Visual personality:** x

        ## Section C — Placeholder Instructions

        Use IMAGE markers sparingly.
        """
    )
    parsed = parse_brief_markdown(text)
    assert parsed.strap_style == "all-caps-three-beat"
