"""Tests for the Picture SmartArt builder (child-node architecture).

The picture builder uses a parent-child node structure where:
  - Parent node: carries the text label with empty <dgm:spPr/> (no fill)
  - Child node: carries <a:blipFill> with the image reference
  - Items without images: parent only, no child (placeholder shows)

This architecture was discovered through spike 6b iteration:
putting blipFill on the parent node caused background bleed (image
rendered behind ALL sub-shapes including text). The child-node
approach isolates the image to the pictRect layout shape via
presOf axis="ch" on the modified pList1 layout.xml.
"""
from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

DGM_NS = "{http://schemas.openxmlformats.org/drawingml/2006/diagram}"
A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


@pytest.fixture
def test_images(tmp_path):
    """Create small test images for picture builder tests."""
    from PIL import Image

    img1 = tmp_path / "blue.png"
    Image.new("RGB", (100, 100), color=(70, 130, 180)).save(img1)

    img2 = tmp_path / "red.png"
    Image.new("RGB", (100, 100), color=(180, 70, 70)).save(img2)

    return {"blue": img1, "red": img2}


def test_text_only_delegates_to_flat_list():
    """When all items are strings (no image_path), picture builder
    delegates to flat_list and returns plain bytes."""
    from src.smartart_pptx_native.builders import picture
    from src.smartart_pptx_native.layouts import catalog

    catalog.load_catalog.cache_clear()
    entry = catalog.get_entry("pList1")

    result = picture.build({"items": ["Alpha", "Beta", "Gamma"]}, entry)
    # flat_list returns bytes, not a tuple
    assert isinstance(result, bytes)
    root = ET.fromstring(result)
    # Should be a regular flat list — no child nodes
    nodes = [p for p in root.findall(f"{DGM_NS}ptLst/{DGM_NS}pt")
             if p.get("type") is None]
    assert len(nodes) == 3  # 3 data nodes, no children


def test_mixed_items_return_tuple_with_image_refs(test_images):
    """When any item has image_path, builder returns (bytes, image_refs)."""
    from src.smartart_pptx_native.builders import picture
    from src.smartart_pptx_native.layouts import catalog

    catalog.load_catalog.cache_clear()
    entry = catalog.get_entry("pList1")

    data = {
        "items": [
            {"label": "With Image", "image_path": str(test_images["blue"])},
            {"label": "No Image"},
            {"label": "Also Image", "image_path": str(test_images["red"])},
        ]
    }
    result = picture.build(data, entry)
    assert isinstance(result, tuple)
    data_xml, image_refs = result
    assert isinstance(data_xml, bytes)
    assert len(image_refs) == 2  # only items with images


def test_child_nodes_created_for_items_with_images(test_images):
    """Items with images should have parent+child node pairs."""
    from src.smartart_pptx_native.builders import picture
    from src.smartart_pptx_native.layouts import catalog

    catalog.load_catalog.cache_clear()
    entry = catalog.get_entry("pList1")

    data = {
        "items": [
            {"label": "Has Image", "image_path": str(test_images["blue"])},
            {"label": "No Image"},
        ]
    }
    data_xml, _ = picture.build(data, entry)
    root = ET.fromstring(data_xml)

    # Count all non-typed points (regular data nodes)
    data_nodes = [p for p in root.findall(f"{DGM_NS}ptLst/{DGM_NS}pt")
                  if p.get("type") is None]
    # "Has Image" (parent) + its child (image node) + "No Image" (parent only) = 3
    assert len(data_nodes) == 3

    # Count connections
    cxns = root.findall(f"{DGM_NS}cxnLst/{DGM_NS}cxn")
    # doc→parent1, parent1→child1, doc→parent2 = 3 connections
    assert len(cxns) == 3


def test_blipfill_only_on_child_nodes_never_parents(test_images):
    """BlipFill must appear ONLY on child (image) nodes, never on
    parent (text) nodes. This is the core guarantee of the child-node
    architecture — violating it causes background bleed."""
    from src.smartart_pptx_native.builders import picture
    from src.smartart_pptx_native.layouts import catalog

    catalog.load_catalog.cache_clear()
    entry = catalog.get_entry("pList1")

    data = {
        "items": [
            {"label": "Parent A", "image_path": str(test_images["blue"])},
            {"label": "Parent B", "image_path": str(test_images["red"])},
        ]
    }
    data_xml, _ = picture.build(data, entry)
    xml_str = data_xml.decode("utf-8")

    # Parse and check each node
    root = ET.fromstring(data_xml)
    for pt in root.findall(f"{DGM_NS}ptLst/{DGM_NS}pt"):
        if pt.get("type") is not None:
            continue  # skip doc, parTrans, sibTrans

        text_elem = pt.find(f"{DGM_NS}t/{A_NS}p/{A_NS}r/{A_NS}t")
        has_text = text_elem is not None and text_elem.text and text_elem.text.strip()
        sp_pr = pt.find(f"{DGM_NS}spPr")
        has_blip = sp_pr is not None and sp_pr.find(f"{A_NS}blipFill") is not None

        if has_text:
            # Parent node (has label text) — must NOT have blipFill
            assert not has_blip, (
                f"parent node with text '{text_elem.text}' has blipFill — "
                f"this would cause background bleed"
            )
        elif has_blip:
            # Child node (has blipFill) — should have empty or no text
            pass  # correct: image node with blipFill and no text


def test_image_refs_track_correct_rel_ids_and_media_names(test_images):
    from src.smartart_pptx_native.builders import picture
    from src.smartart_pptx_native.layouts import catalog

    catalog.load_catalog.cache_clear()
    entry = catalog.get_entry("pList1")

    data = {
        "items": [
            {"label": "A", "image_path": str(test_images["blue"])},
            {"label": "B"},
            {"label": "C", "image_path": str(test_images["red"])},
        ]
    }
    _, image_refs = picture.build(data, entry)

    assert len(image_refs) == 2
    assert image_refs[0].rel_id == "rId1"
    assert image_refs[0].media_name == "image1.png"
    assert image_refs[0].image_path == test_images["blue"]

    assert image_refs[1].rel_id == "rId2"
    assert image_refs[1].media_name == "image2.png"
    assert image_refs[1].image_path == test_images["red"]


def test_engine_produces_carrier_with_media_files(test_images):
    """End-to-end: engine.render with picture items produces a carrier
    containing ppt/media/ files and data1.xml.rels image relationships."""
    from src.smartart_pptx_native import engine
    from src.smartart_pptx_native.layouts import catalog

    catalog.load_catalog.cache_clear()

    spec = {
        "graphic_type": "list",
        "layout_id": "pList1",
        "data": {
            "items": [
                {"label": "Blue", "image_path": str(test_images["blue"])},
                {"label": "Plain"},
                {"label": "Red", "image_path": str(test_images["red"])},
            ]
        },
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = engine.render(spec, tmpdir)
        assert result.output_path.exists()

        with zipfile.ZipFile(result.output_path, "r") as z:
            names = set(z.namelist())

            # Media files present
            assert "ppt/media/image1.png" in names
            assert "ppt/media/image2.png" in names

            # Data rels file with image relationships
            assert "ppt/diagrams/_rels/data1.xml.rels" in names
            rels_xml = z.read("ppt/diagrams/_rels/data1.xml.rels").decode("utf-8")
            assert "rId1" in rels_xml
            assert "rId2" in rels_xml
            assert "image/png" in z.read("[Content_Types].xml").decode("utf-8") or \
                   'Extension="png"' in z.read("[Content_Types].xml").decode("utf-8")

            # data1.xml has blipFill references
            data_xml = z.read("ppt/diagrams/data1.xml").decode("utf-8")
            assert data_xml.count("blipFill") >= 2  # open + close tags per image


def test_engine_produces_carrier_without_media_for_text_only():
    """Text-only picture items should NOT produce media files or data rels."""
    from src.smartart_pptx_native import engine
    from src.smartart_pptx_native.layouts import catalog

    catalog.load_catalog.cache_clear()

    spec = {
        "graphic_type": "list",
        "layout_id": "pList1",
        "data": {"items": ["Alpha", "Beta", "Gamma"]},
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = engine.render(spec, tmpdir)

        with zipfile.ZipFile(result.output_path, "r") as z:
            names = set(z.namelist())
            media = [n for n in names if "media" in n]
            data_rels = [n for n in names if "data1.xml.rels" in n]
            assert media == [], "text-only should have no media files"
            assert data_rels == [], "text-only should have no data rels"


def test_picture_builder_rejects_too_many_items():
    from src.smartart_pptx_native.builders import picture
    from src.smartart_pptx_native.layouts import catalog

    catalog.load_catalog.cache_clear()
    entry = catalog.get_entry("pList1")

    items = [{"label": f"Item {i}", "image_path": "/fake.png"} for i in range(20)]
    with pytest.raises(picture.PictureBuildError, match="at most"):
        picture.build({"items": items}, entry)


def test_picture_builder_rejects_long_labels():
    from src.smartart_pptx_native.builders import picture
    from src.smartart_pptx_native.layouts import catalog

    catalog.load_catalog.cache_clear()
    entry = catalog.get_entry("pList1")

    with pytest.raises(picture.PictureBuildError, match="chars"):
        picture.build({
            "items": [
                {"label": "X" * 50, "image_path": "/fake.png"},
                {"label": "OK"},
            ]
        }, entry)


def test_picture_builder_accepts_text_key():
    """Items with 'text' key should work the same as 'label' key."""
    from src.smartart_pptx_native.builders.picture import _extract_items

    catalog_entry = {
        "id": "vList3", "min_nodes": 2, "max_nodes": 8, "max_label_chars": 30,
    }
    extracted = {
        "items": [
            {"text": "Alpha", "image_path": "/tmp/fake.png"},
            {"text": "Beta", "image_path": "/tmp/fake2.png"},
        ]
    }
    items, has_images = _extract_items(extracted, catalog_entry)
    assert items[0]["label"] == "Alpha"
    assert items[1]["label"] == "Beta"
    assert has_images is True


def test_picture_builder_label_key_still_works():
    """Existing 'label' key must still work (regression check)."""
    from src.smartart_pptx_native.builders.picture import _extract_items

    catalog_entry = {
        "id": "vList3", "min_nodes": 2, "max_nodes": 8, "max_label_chars": 30,
    }
    extracted = {
        "items": [
            {"label": "Gamma", "image_path": "/tmp/fake.png"},
            {"label": "Delta", "image_path": "/tmp/fake2.png"},
        ]
    }
    items, has_images = _extract_items(extracted, catalog_entry)
    assert items[0]["label"] == "Gamma"
    assert items[1]["label"] == "Delta"


def test_picture_builder_default_fill_mode(test_images):
    """Items without explicit fill mode should default to 'fill' in build()."""
    from src.smartart_pptx_native.builders import picture
    from src.smartart_pptx_native.layouts import catalog

    catalog.load_catalog.cache_clear()
    entry = catalog.get_entry("pList1")

    data = {
        "items": [
            {"label": "A", "image_path": str(test_images["blue"])},
            {"label": "B", "image_path": str(test_images["red"])},
        ]
    }
    data_xml, _ = picture.build(data, entry)
    xml_str = data_xml.decode("utf-8")
    # "fill" mode produces negative fillRect insets (crop overflow):
    #   <a:fillRect l="-50000" r="-50000"/>
    # "fit" mode produces positive fillRect insets (letterbox):
    #   <a:fillRect l="25000" r="25000"/>
    # With 100x100 square images (ar=1.0) and box_ar=0.5, "fill" gives
    # negative insets. Default should be "fill", so we expect "-".
    assert 'l="-' in xml_str, (
        "default fill mode should be 'fill' (negative insets), not 'fit' (positive)"
    )
