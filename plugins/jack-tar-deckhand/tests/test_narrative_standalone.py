"""Tests for narrative-standalone path — outline and notes generation without style-guide."""
import json
import sys
from pathlib import Path

import jsonschema
import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

SPEAKER_NOTES_SCHEMA = json.loads(
    (PLUGIN_ROOT / "src/schemas/speaker_notes.schema.json").read_text()
)


@pytest.fixture
def narrative_only_brief(tmp_path):
    """A minimal TalkBrief with no style-guide or brand-profile dependency."""
    brief = {
        "topic": "Building Resilient Distributed Systems",
        "audience": "Senior engineers",
        "duration_minutes": 30,
        "tone": "technical",
        "key_takeaways": [
            "Understand failure modes in distributed systems",
            "Apply the CAP theorem in practice",
            "Design for graceful degradation",
        ],
    }
    brief_path = tmp_path / "talk-brief.json"
    brief_path.write_text(json.dumps(brief))
    return brief_path


def test_narrative_architect_runs_without_style_guide(narrative_only_brief, tmp_path):
    deck_dir = tmp_path / "deck"
    deck_dir.mkdir(parents=True)

    # Copy talk-brief.json into deck_dir (where deckcontext.read_contract looks for it)
    import shutil
    shutil.copy(narrative_only_brief, deck_dir / "talk-brief.json")

    from src.deckcontext import init_deck
    init_deck(str(deck_dir))

    # Confirm style-guide is absent
    assert not (deck_dir / "style-guide.json").exists()

    from src.narrative_standalone import generate_outline_from_brief_only
    outline = generate_outline_from_brief_only(str(deck_dir))

    from src.content_validation import validate_outline_schema
    errors = validate_outline_schema(outline)
    assert errors == [], f"Outline schema errors: {errors}"

    assert len(outline["slides"]) >= 3


def test_speaker_notes_from_standalone_outline(narrative_only_brief, tmp_path):
    deck_dir = tmp_path / "deck2"
    deck_dir.mkdir(parents=True)

    import shutil
    shutil.copy(narrative_only_brief, deck_dir / "talk-brief.json")

    from src.deckcontext import init_deck
    init_deck(str(deck_dir))

    from src.narrative_standalone import generate_outline_from_brief_only
    outline = generate_outline_from_brief_only(str(deck_dir))
    (deck_dir / "outline.json").write_text(json.dumps(outline))

    from src.content_validation import generate_speaker_notes_from_outline
    notes = generate_speaker_notes_from_outline(outline, tone="technical")

    # Schema conformance — catches future drift automatically
    jsonschema.validate(notes, SPEAKER_NOTES_SCHEMA)

    assert len(notes["notes"]) == len(outline["slides"])
    for item in notes["notes"]:
        assert "text" in item, f"Missing 'text' in note: {item}"
        assert "estimated_seconds" in item, f"Missing 'estimated_seconds' in note: {item}"
