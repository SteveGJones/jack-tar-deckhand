import sys
from pathlib import Path
SPIKE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE / "parsers"))

from pptx_parser import parse_pptx
from slide_facts import SlideFacts

VARIANT_A = (Path(__file__).resolve().parents[2]
             / "2026-04-23-pptx-marker-adherence/outputs/variant-a/presentation.pptx")


def test_parses_all_slides():
    facts = parse_pptx(VARIANT_A)
    assert len(facts) == 10
    assert all(isinstance(f, SlideFacts) for f in facts)


def test_finds_objectname_markers_in_variant_a():
    facts = parse_pptx(VARIANT_A)
    all_markers = [m for f in facts for m in f.markers]
    kinds = sorted(m.kind for m in all_markers)
    assert kinds.count("IMAGE") >= 2
    assert kinds.count("SMARTART") >= 1
    assert kinds.count("BG") >= 1


def test_records_text_content_per_slide():
    facts = parse_pptx(VARIANT_A)
    # slide 1 is the title slide — should contain "AI Agents"
    assert "AI Agents" in facts[0].text_content


def test_counts_element_types():
    facts = parse_pptx(VARIANT_A)
    for f in facts:
        assert "text" in f.element_types
        assert f.element_types["text"] >= 0
