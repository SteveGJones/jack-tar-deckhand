import shutil
from pathlib import Path

import pytest
from pptx import Presentation
from pptx.oxml.ns import qn

from src.enrichment_ops.background import apply_background_in_memory
from src.security import AllowedPathError


def test_applies_blipfill_and_removes_marker(tmp_path, seed_variant_a, placeholder_png):
    work = tmp_path / "deck.pptx"
    shutil.copy(seed_variant_a, work)
    img_dir = tmp_path / "generated"
    img_dir.mkdir()
    img = img_dir / "bg.png"
    shutil.copy(placeholder_png, img)

    prs = Presentation(str(work))
    apply_background_in_memory(
        prs=prs,
        slide_index_1based=1,
        image_path=img,
        marker_name="BG:title-hero-dark-grid",
        allowed_image_roots=[img_dir],
    )
    # Assert the in-memory tree carries a <p:bg> with a <a:blip>
    slide = prs.slides[0]
    cSld = slide.element.find(qn("p:cSld"))
    bg = cSld.find(qn("p:bg"))
    assert bg is not None
    blip = bg.find(".//" + qn("a:blip"))
    assert blip is not None
    # Marker shape removed
    names = [s.name for s in slide.shapes]
    assert "BG:title-hero-dark-grid" not in names


def test_image_path_outside_allowlist_raises(tmp_path, seed_variant_a, placeholder_png):
    work = tmp_path / "deck.pptx"
    shutil.copy(seed_variant_a, work)
    rogue = tmp_path / "rogue.png"
    shutil.copy(placeholder_png, rogue)

    prs = Presentation(str(work))
    allowed = tmp_path / "generated"
    allowed.mkdir()
    with pytest.raises(AllowedPathError):
        apply_background_in_memory(
            prs=prs, slide_index_1based=1, image_path=rogue,
            marker_name=None, allowed_image_roots=[allowed],
        )


def test_idempotent_when_no_existing_bg(tmp_path, seed_variant_a, placeholder_png):
    """Calling apply_background twice on the same slide replaces, doesn't stack."""
    work = tmp_path / "deck.pptx"
    shutil.copy(seed_variant_a, work)
    img_dir = tmp_path / "generated"; img_dir.mkdir()
    img = img_dir / "bg.png"; shutil.copy(placeholder_png, img)

    prs = Presentation(str(work))
    apply_background_in_memory(prs=prs, slide_index_1based=1, image_path=img,
                                marker_name=None, allowed_image_roots=[img_dir])
    apply_background_in_memory(prs=prs, slide_index_1based=1, image_path=img,
                                marker_name=None, allowed_image_roots=[img_dir])
    cSld = prs.slides[0].element.find(qn("p:cSld"))
    bgs = cSld.findall(qn("p:bg"))
    assert len(bgs) == 1
