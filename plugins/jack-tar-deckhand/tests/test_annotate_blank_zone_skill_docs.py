"""Drift-pin test for the blank-zone vocabulary across both SKILL.mds
(issue #142, final scope item, BZ-9).

The four zone names and their anchor-pass phrase fractions live in
THREE places: ``annotate_figure.BLANK_ZONE_RECTS`` (code), imagegen-
bridge SKILL.md (native flow, §4.8 step 2's amended anchor contract),
and annotate-figure SKILL.md (raster/standalone flow, §2's amended
anchor contract). This test greps both SKILL.mds for the four zone
names and the 0.67/0.33/0.25/0.75 phrase fractions and asserts they
match BLANK_ZONE_RECTS, so an edit to one location that isn't mirrored
in the others fails CI loudly instead of silently drifting (repo
precedent: the pptx_native SmartArt catalog-markdown CI drift check).
"""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.annotate_figure import BLANK_ZONE_RECTS  # noqa: E402

BRIDGE_SKILL = PLUGIN_ROOT / "skills" / "imagegen-bridge" / "SKILL.md"
ANNOTATE_SKILL = PLUGIN_ROOT / "skills" / "annotate-figure" / "SKILL.md"

# The zone-phrase text expresses each zone's boundary as a single
# threshold: side zones as an x fraction, strips as a y fraction. These
# are derived directly from BLANK_ZONE_RECTS so the two can never
# silently diverge without this test noticing.
_EXPECTED_FRACTIONS = {
    "right_third": BLANK_ZONE_RECTS["right_third"][0],    # x > 0.67
    "left_third": BLANK_ZONE_RECTS["left_third"][2],       # x < 0.33
    "top_strip": BLANK_ZONE_RECTS["top_strip"][3],         # y < 0.25
    "bottom_strip": BLANK_ZONE_RECTS["bottom_strip"][1],   # y > 0.75
}


def test_skill_docs_blank_zone_vocabulary_drift_pin():
    for skill_path in (BRIDGE_SKILL, ANNOTATE_SKILL):
        text = skill_path.read_text()
        for zone in BLANK_ZONE_RECTS:
            assert zone in text, f"{zone!r} missing from {skill_path}"
        for zone, frac in _EXPECTED_FRACTIONS.items():
            phrase = f"{frac:.2f}"
            assert phrase in text, (
                f"phrase fraction {phrase!r} for zone {zone!r} missing from {skill_path}"
            )


def test_expected_fractions_match_blank_zone_rects_exactly():
    """Sanity pin on the test's own derivation logic (not just presence
    in the docs) — catches a future BLANK_ZONE_RECTS fraction change
    (§8.4 dogfood calibration) that isn't reflected here."""
    assert _EXPECTED_FRACTIONS == {
        "right_third": 0.67,
        "left_third": 0.33,
        "top_strip": 0.25,
        "bottom_strip": 0.75,
    }
