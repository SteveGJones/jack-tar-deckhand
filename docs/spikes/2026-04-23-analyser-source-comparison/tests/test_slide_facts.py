# tests/test_slide_facts.py
import sys
from pathlib import Path
SPIKE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SPIKE / "parsers"))

from slide_facts import SlideFacts, Marker

def test_slide_facts_roundtrip_dict():
    sf = SlideFacts(
        slide_index=1,
        text_content="Hello world",
        markers=[Marker(kind="IMAGE", identifier="hero", left_emu=0, top_emu=0, width_emu=914400, height_emu=914400)],
        background_kind="solid",
        element_types={"text": 2, "shape": 1},
    )
    as_dict = sf.to_dict()
    back = SlideFacts.from_dict(as_dict)
    assert back == sf

def test_marker_validates_kind():
    import pytest
    with pytest.raises(ValueError):
        Marker(kind="BOGUS", identifier="x", left_emu=0, top_emu=0, width_emu=1, height_emu=1)
