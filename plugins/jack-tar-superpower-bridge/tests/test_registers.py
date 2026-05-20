"""Tests for register preset loading + brief integration (issue #87).

Four canonical v1 presets bundle a palette + typography + layout typology +
default strap_style so a speaker can pin a single high-level register on the
brief and pull in coherent defaults. These tests verify:

1. KNOWN_REGISTERS matches the actual files on disk and the
   creative_brief.VALID_REGISTERS enum.
2. Each preset parses cleanly and carries the four load-bearing fields.
3. Brief integration — the `register` field validates, round-trips, and
   doesn't collide with `strap_style` parsing.
"""
from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

import pytest

from src.creative_brief import (  # noqa: E402
    CreativeBrief,
    CreativeBriefValidationError,
    VALID_REGISTERS,
    parse_brief_markdown,
)
from src.registers import (  # noqa: E402
    KNOWN_REGISTERS,
    Preset,
    PresetNotFoundError,
    list_preset_names,
    load_preset,
)
from src.registers.loader import _PRESETS_DIR, iter_all_presets  # noqa: E402


# --- Catalogue + filesystem coherence --------------------------------------


def test_known_registers_matches_brief_valid_registers():
    """The single source of truth (registers.loader.KNOWN_REGISTERS) and the
    duplicated set in creative_brief.VALID_REGISTERS must stay in sync."""
    assert set(KNOWN_REGISTERS) == VALID_REGISTERS


def test_every_known_register_has_a_markdown_file():
    for name in KNOWN_REGISTERS:
        path = _PRESETS_DIR / f"{name}.md"
        assert path.exists(), f"missing preset file: {path}"


def test_no_extra_markdown_files_in_presets_dir():
    """If a .md file exists under presets/ but isn't in KNOWN_REGISTERS, the
    loader will fail to discover it — keep them in sync."""
    files = {p.stem for p in _PRESETS_DIR.glob("*.md")}
    assert files == set(KNOWN_REGISTERS), (
        f"presets dir vs KNOWN_REGISTERS drift: "
        f"only_in_files={files - set(KNOWN_REGISTERS)!r}, "
        f"only_in_set={set(KNOWN_REGISTERS) - files!r}"
    )


def test_list_preset_names_sorted():
    names = list_preset_names()
    assert names == sorted(names)
    assert len(names) == 4


# --- Per-preset structural tests ------------------------------------------


@pytest.mark.parametrize("name", sorted(KNOWN_REGISTERS))
def test_each_preset_loads_with_required_fields(name):
    preset = load_preset(name)
    assert isinstance(preset, Preset)
    assert preset.name == name
    assert preset.default_strap_style in {"all-caps-three-beat", "prose-sentence"}
    assert preset.palette_rows, f"{name}: palette table is empty"
    assert preset.typography, f"{name}: typography section is empty"
    assert preset.layout_typology, f"{name}: layout typology section is empty"
    assert preset.when_to_reach, f"{name}: when-to-reach section is empty"


@pytest.mark.parametrize("name", sorted(KNOWN_REGISTERS))
def test_each_preset_palette_has_load_bearing_rows(name):
    """The bridge's brand-palette-injection heuristic depends on Surface and
    Structural / Primary fill rows. Every preset must declare them."""
    preset = load_preset(name)
    roles = {row["role"] for row in preset.palette_rows}
    assert "Surface" in roles, f"{name}: missing Surface row"
    assert any("Structural" in r or "Primary" in r for r in roles), (
        f"{name}: missing Structural / Primary fill row"
    )


@pytest.mark.parametrize("name", sorted(KNOWN_REGISTERS))
def test_each_preset_palette_rows_have_valid_hex(name):
    preset = load_preset(name)
    for row in preset.palette_rows:
        assert row["hex"].startswith("#"), f"{name}: {row['role']!r} hex missing #"
        assert len(row["hex"]) == 7, f"{name}: {row['role']!r} hex {row['hex']!r} not 7 chars"


def test_editorial_mixed_case_declares_prose_sentence_strap():
    """Plan §2.2: editorial-mixed-case is the canonical home of prose-sentence."""
    preset = load_preset("editorial-mixed-case")
    assert preset.default_strap_style == "prose-sentence"


def test_atmospheric_photo_declares_all_caps_three_beat():
    """Plan §6.2b: atmospheric-photo is the keynote/visual-led register
    and defaults to all-caps-three-beat."""
    preset = load_preset("atmospheric-photo")
    assert preset.default_strap_style == "all-caps-three-beat"


def test_iter_all_presets_yields_four():
    presets = list(iter_all_presets())
    assert len(presets) == 4
    assert [p.name for p in presets] == sorted(KNOWN_REGISTERS)


# --- Unknown-name error path ----------------------------------------------


def test_load_preset_rejects_unknown_name():
    with pytest.raises(PresetNotFoundError):
        load_preset("not-a-real-preset")


# --- Brief integration ----------------------------------------------------


def test_brief_register_defaults_to_none():
    brief = CreativeBrief(
        topic="t", audience="a", duration_minutes=10, narrative_arc="x",
        narrative_detail="x", audience_takeaway="x", tone="x",
        visual_personality="x", placeholder_instructions="x",
    )
    assert brief.register is None


@pytest.mark.parametrize("name", sorted(KNOWN_REGISTERS))
def test_brief_register_accepts_every_known_name(name):
    brief = CreativeBrief(
        topic="t", audience="a", duration_minutes=10, narrative_arc="x",
        narrative_detail="x", audience_takeaway="x", tone="x",
        visual_personality="x", placeholder_instructions="x",
        register=name,
    )
    assert brief.register == name


def test_brief_register_rejects_unknown_name():
    with pytest.raises(CreativeBriefValidationError, match="register"):
        CreativeBrief(
            topic="t", audience="a", duration_minutes=10, narrative_arc="x",
            narrative_detail="x", audience_takeaway="x", tone="x",
            visual_personality="x", placeholder_instructions="x",
            register="velvet-ledger",
        )


def test_brief_register_omitted_from_markdown_when_none():
    brief = CreativeBrief(
        topic="t", audience="a", duration_minutes=10, narrative_arc="x",
        narrative_detail="x", audience_takeaway="x", tone="x",
        visual_personality="x", placeholder_instructions="x",
    )
    assert "Register:" not in brief.to_markdown()


def test_brief_register_emitted_in_markdown_when_set():
    brief = CreativeBrief(
        topic="t", audience="a", duration_minutes=10, narrative_arc="x",
        narrative_detail="x", audience_takeaway="x", tone="x",
        visual_personality="x", placeholder_instructions="x",
        register="infographic-narrative",
    )
    md = brief.to_markdown()
    assert "Register: infographic-narrative" in md
    assert md.index("Register:") < md.index("## Section A")


def test_brief_register_roundtrips_through_markdown():
    brief = CreativeBrief(
        topic="t", audience="a", duration_minutes=10, narrative_arc="x",
        narrative_detail="x", audience_takeaway="x", tone="x",
        visual_personality="x", placeholder_instructions="x",
        register="schematic-diagram",
        strap_style="prose-sentence",
    )
    parsed = parse_brief_markdown(brief.to_markdown())
    assert parsed.register == "schematic-diagram"
    assert parsed.strap_style == "prose-sentence"


def test_brief_register_and_strap_style_independent():
    """A brief may pin register without strap_style, or vice versa."""
    brief = CreativeBrief(
        topic="t", audience="a", duration_minutes=10, narrative_arc="x",
        narrative_detail="x", audience_takeaway="x", tone="x",
        visual_personality="x", placeholder_instructions="x",
        register="atmospheric-photo",
    )
    parsed = parse_brief_markdown(brief.to_markdown())
    assert parsed.register == "atmospheric-photo"
    assert parsed.strap_style is None


def test_brief_legacy_text_without_register_parses_to_none():
    legacy = dedent(
        """\
        # Creative Brief

        Topic: legacy
        Audience: people
        Duration: 10 min
        Confidentiality: public
        Budget cap: $1.00

        ## Section A — Narrative Architecture

        Arc: Problem-Solution

        prose

        ## Section B — Communication & Visual Intent

        Audience takeaway: x
        Tone: x
        Visual personality: x

        ## Section C — Placeholder Instructions

        Use IMAGE markers sparingly.
        """
    )
    parsed = parse_brief_markdown(legacy)
    assert parsed.register is None
