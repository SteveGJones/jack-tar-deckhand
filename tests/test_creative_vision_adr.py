"""Smoke test confirming the creative_vision ADR exists and covers required sections."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ADR = REPO_ROOT / "docs" / "architecture" / "creative-vision-renderer.md"


def test_adr_exists():
    assert ADR.is_file()


def test_adr_covers_required_sections():
    text = ADR.read_text()
    for heading in (
        "# Creative Vision Renderer", "## 1. Context", "## 2. Decision",
        "## 3. Architecture", "## 4. Contracts", "## 5. Cascade",
        "## 6. Operator surface", "## 7. Risks", "## 8. Related decisions",
    ):
        assert heading in text, f"ADR missing heading: {heading!r}"


def test_adr_references_companion_documents():
    text = ADR.read_text()
    assert "paperbanana-integration-v2.md" in text
    assert "#88" in text  # full_bleed
    assert "#105" in text
