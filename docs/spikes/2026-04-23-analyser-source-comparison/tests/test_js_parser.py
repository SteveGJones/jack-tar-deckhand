import sys
from pathlib import Path
SPIKE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE / "parsers"))

from js_parser import parse_js
from slide_facts import SlideFacts

VARIANT_A_JS = (Path(__file__).resolve().parents[2]
                / "2026-04-23-pptx-marker-adherence/outputs/variant-a/build.js")


def test_parses_all_slides():
    facts = parse_js(VARIANT_A_JS)
    assert len(facts) == 10
    assert all(isinstance(f, SlideFacts) for f in facts)


def test_finds_objectname_markers_in_variant_a():
    facts = parse_js(VARIANT_A_JS)
    all_markers = [m for f in facts for m in f.markers]
    kinds = sorted(m.kind for m in all_markers)
    assert kinds.count("IMAGE") >= 2
    assert kinds.count("SMARTART") >= 1
    assert kinds.count("BG") >= 1


def test_variant_c_finds_no_objectname_markers_but_text_labels_present():
    # Variants B and C used `name:` (dropped by PptxGenJS) — but the JS literal
    # strings "IMAGE:..." / "SMARTART:..." / "BG:..." appear in addText calls.
    # This test documents that the JS parser CAN find marker intent via text scan
    # even when objectName is missing. Key question for the spike.
    VARIANT_C_JS = (Path(__file__).resolve().parents[2]
                    / "2026-04-23-pptx-marker-adherence/outputs/variant-c/build.js")
    facts = parse_js(VARIANT_C_JS)
    # addShape name missing but addText strings present
    all_text = "\n".join(f.text_content for f in facts)
    assert "IMAGE:" in all_text
    assert "SMARTART:" in all_text or "BG:" in all_text


def test_resolves_helper_function_marker_calls_in_variant_a():
    # Variant A wraps addShape in a helper (addMarker / addMarkerRect).
    # Pure AST walk that only follows slide.addShape(...) will miss these.
    # Key empirical test: does helper-resolved JS parsing match OOXML's 8 markers?
    facts = parse_js(VARIANT_A_JS)
    marker_counts: dict[str, int] = {}
    for f in facts:
        for m in f.markers:
            marker_counts[m.kind] = marker_counts.get(m.kind, 0) + 1
    # Spike 1's analyser found 8 markers in Variant A via OOXML — JS parser
    # should find the same count (helper-indirection resolved).
    # If this fails, that's itself a data point for the spike's findings,
    # but the parser should at least try.
    assert sum(marker_counts.values()) == 8
