"""Structural validation of /enrich-deck SKILL.md."""
from pathlib import Path
import re

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = PLUGIN_ROOT / "skills" / "enrich-deck" / "SKILL.md"


def _frontmatter(content: str) -> dict[str, str]:
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    out: dict[str, str] = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip()
    return out


def test_skill_exists():
    assert SKILL_PATH.exists()


def test_frontmatter_minimal():
    fm = _frontmatter(SKILL_PATH.read_text())
    assert fm["name"] == "enrich-deck"
    assert "argument-hint" in fm and "<pptx-path>" in fm["argument-hint"]
    assert len(fm.get("description", "")) > 60


def test_skill_invokes_required_modules():
    text = SKILL_PATH.read_text()
    for module in ("src.analyser", "src.enrichment", "src.image_bridge",
                    "src.smartart_bridge", "src.cohesion_review",
                    "src.enrichment_report", "src.measurement",
                    "src.cycle_state"):  # state primitives the skill drives
        assert module in text, f"{module} missing from /enrich-deck skill"


def test_skill_drives_loop_via_cycle_state_not_via_overrides():
    """Caveat #1 fix — SKILL.md must NOT claim to 'override the review callable'
    because Python heredocs cannot dispatch Claude subagents."""
    text = SKILL_PATH.read_text()
    assert "override the `review` callable" not in text
    assert "advance_after_review" in text


def test_skill_invokes_image_reviewer_and_cohesion_reviewer_agents():
    text = SKILL_PATH.read_text()
    assert "image-reviewer" in text
    assert "enrichment-cohesion-reviewer" in text
    assert "prompt-engineer" in text


def test_skill_documents_three_phase_flow_and_user_choices():
    text = SKILL_PATH.read_text().lower()
    # Mentions analyser, menu, draft/review, deliver
    assert "analyse" in text or "analyser" in text
    assert "menu" in text or "select" in text
    assert "deliver" in text


def test_skill_handles_overlap_branches():
    text = SKILL_PATH.read_text()
    # The SMARTART overlap user-choice options
    assert "apply_clear_overlap" in text or "clear overlapping text" in text
    assert "proceed anyway" in text.lower() or "proceed" in text.lower()
    assert "drop" in text.lower()


def test_skill_writes_two_outputs():
    text = SKILL_PATH.read_text()
    assert "presentation-enriched.pptx" in text
    assert "enrichment-report.md" in text


def test_skill_default_budget_cap_documented():
    text = SKILL_PATH.read_text()
    assert "$1.00" in text or "1.00" in text
