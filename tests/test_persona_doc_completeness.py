from pathlib import Path

DOC_PATH = Path(__file__).resolve().parents[1] / "docs" / "architecture" / "ai-personas" / "superpower-bridge-personas.md"


def test_doc_version_bumped_to_1_0():
    text = DOC_PATH.read_text()
    assert "v1.0" in text or "Status:** v1.0" in text


def test_doc_has_tripartite_owner_section():
    text = DOC_PATH.read_text()
    assert "Service Owner" in text
    assert "SOP Owner" in text
    assert "AI Risk Manager" in text or "AI RM" in text


def test_doc_nominates_owners_not_TBD():
    """v1.0 must nominate concrete owners (consolidated tripartite is fine for v1)."""
    text = DOC_PATH.read_text()
    assert "Steve Jones" in text
    # v0.1 had "TBD (jack-tar repo maintainer)"; v1.0 must not
    assert "TBD (jack-tar repo maintainer)" not in text


def test_doc_links_measurement_module():
    text = DOC_PATH.read_text()
    assert "src/measurement.py" in text


def test_doc_links_dogfooding_evidence():
    text = DOC_PATH.read_text()
    assert "dogfood" in text.lower()


def test_doc_covers_all_5_measurement_tiers():
    """Caveat #12 — measurement blueprint must distribute across Tiers 1–5,
    not cluster only at Tier 4 Activity."""
    text = DOC_PATH.read_text()
    for tier in ("Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"):
        assert tier in text, f"missing {tier} in measurement blueprint"


def test_doc_clarifies_recall_is_offline_only():
    """Recall has no per-run collection mechanism — must be explicitly demoted
    to offline analysis so the persona contract doesn't claim what isn't built."""
    text = DOC_PATH.read_text()
    assert "Recall" in text
    assert "offline" in text.lower()
