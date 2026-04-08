"""Sanity tests for committed seed .pptx fixtures.

The engine depends on hand-authored seed files stored in
`tests/fixtures/smartart_seeds/`. These tests guard against:

  - Seed files being accidentally deleted or corrupted in a refactor
  - Seed files being replaced with a different layout than the catalog
    expects (e.g. swapping process1_seed.pptx for a cycle layout)
  - PowerPoint version drift breaking the seed structure
  - Catalog entries pointing at the wrong seed

Each catalog entry listed as v1 MUST have a seed that passes these
checks, otherwise the engine will fail at runtime in Phase 2.

The blank_slide.pptx host fixture (used by the Phase 3 assembler
injection path) is tested separately — it's NOT a SmartArt seed and
has different structural expectations.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

import pytest

from src.smartart_pptx_native.layouts import catalog


REPO_ROOT = Path(__file__).resolve().parent.parent


def _get_v1_entries():
    return catalog.list_entries(v1_only=True)


@pytest.mark.parametrize(
    "entry",
    _get_v1_entries(),
    ids=lambda e: e["id"],
)
def test_seed_file_exists_and_is_valid_zip(entry):
    seed_path = catalog.resolve_seed_path(entry)
    assert seed_path.exists(), f"seed missing for {entry['id']}: {seed_path}"
    assert zipfile.is_zipfile(seed_path), f"not a valid zip: {seed_path}"


@pytest.mark.parametrize(
    "entry",
    _get_v1_entries(),
    ids=lambda e: e["id"],
)
def test_seed_contains_all_four_diagram_parts(entry):
    seed_path = catalog.resolve_seed_path(entry)
    with zipfile.ZipFile(seed_path, "r") as z:
        names = set(z.namelist())
    for required in [
        "ppt/diagrams/data1.xml",
        "ppt/diagrams/layout1.xml",
        "ppt/diagrams/quickStyle1.xml",
        "ppt/diagrams/colors1.xml",
    ]:
        assert required in names, (
            f"seed {entry['id']!r} missing {required} — cannot be a valid "
            f"SmartArt seed. Re-create from PowerPoint Mac per "
            f"docs/spikes/2026-04-08-pptx-native-smartart-injection.md §2."
        )


@pytest.mark.parametrize(
    "entry",
    _get_v1_entries(),
    ids=lambda e: e["id"],
)
def test_seed_doc_point_matches_catalog_layout_uri(entry):
    """The seed's doc point must declare the same loTypeId that the
    catalog entry lists. If these drift apart, the engine will emit
    a file with a mismatched layout binding and PowerPoint will
    either render incorrectly or repair-dialog the file."""
    seed_path = catalog.resolve_seed_path(entry)
    with zipfile.ZipFile(seed_path, "r") as z:
        data_xml = z.read("ppt/diagrams/data1.xml").decode("utf-8")

    m = re.search(r'type="doc"[^>]*?loTypeId="([^"]+)"', data_xml)
    if m is None:
        # Try alternate attribute ordering
        m = re.search(r'loTypeId="([^"]+)"[^>]*?type="doc"', data_xml)
    if m is None:
        # Last resort: look for any loTypeId in the doc-containing fragment
        m = re.search(r'loTypeId="([^"]+)"', data_xml)

    assert m is not None, (
        f"no loTypeId found in {entry['id']} seed's data1.xml — "
        f"cannot verify layout binding"
    )
    assert m.group(1) == entry["layout_uri"], (
        f"seed {entry['id']!r} binds to {m.group(1)!r} but catalog "
        f"entry declares {entry['layout_uri']!r}. Either update the "
        f"catalog to match the seed's actual layout, or re-create the "
        f"seed with the intended layout."
    )


@pytest.mark.parametrize(
    "entry",
    _get_v1_entries(),
    ids=lambda e: e["id"],
)
def test_seed_slide_references_diagram_not_flat_group(entry):
    """The slide must contain a `<p:graphicFrame>` with `<dgm:relIds>`
    — not a flat `<p:grpSp>` of baked shapes. Flattened SmartArt is
    not editable; the seed must be the real thing."""
    seed_path = catalog.resolve_seed_path(entry)
    with zipfile.ZipFile(seed_path, "r") as z:
        slide_xml = z.read("ppt/slides/slide1.xml").decode("utf-8")

    assert "<p:graphicFrame>" in slide_xml, (
        f"seed {entry['id']!r} has no graphicFrame — this is not a "
        f"real SmartArt seed. PowerPoint may have flattened it on save."
    )
    assert "dgm:relIds" in slide_xml, (
        f"seed {entry['id']!r} graphicFrame does not reference a "
        f"diagram via dgm:relIds"
    )


def test_blank_slide_host_exists_and_is_valid():
    """The injection host fixture (used in Phase 3) is NOT a SmartArt
    seed — it's a presentation with no diagram parts at all."""
    host_path = REPO_ROOT / "tests" / "fixtures" / "smartart_seeds" / "blank_slide.pptx"
    assert host_path.exists()
    assert zipfile.is_zipfile(host_path)

    with zipfile.ZipFile(host_path, "r") as z:
        names = set(z.namelist())

    # Host must NOT have any diagram parts — the whole point is that
    # it has no SmartArt, so Phase 3's injection path can add one.
    diagram_parts = [n for n in names if n.startswith("ppt/diagrams/")]
    assert diagram_parts == [], (
        f"blank_slide.pptx unexpectedly contains diagram parts: "
        f"{diagram_parts}. This fixture must be a clean host for "
        f"injection testing."
    )

    # Host must have exactly one slide.
    slides = [n for n in names if re.match(r"^ppt/slides/slide\d+\.xml$", n)]
    assert len(slides) == 1, f"expected exactly 1 slide, found {len(slides)}"


def test_every_catalog_v1_entry_has_a_seed():
    """Tripwire: if anyone adds a catalog entry without committing a
    seed, this test catches it immediately."""
    v1_entries = catalog.list_entries(v1_only=True)
    assert len(v1_entries) >= 1, "no v1 catalog entries"
    for entry in v1_entries:
        seed_path = catalog.resolve_seed_path(entry)
        assert seed_path.exists(), (
            f"catalog declares v1 entry {entry['id']!r} but the seed "
            f"{seed_path} doesn't exist"
        )


def test_future_layouts_present_as_fixtures_even_if_not_yet_in_catalog():
    """Belt-and-braces check: the four seed files we know we'll need
    for v1 (process, cycle, orgChart, blank host) must all exist in
    tests/fixtures/smartart_seeds/ even before their catalog entries
    land. Phase 0 spikes committed all four — if any goes missing,
    this test flags it before a later phase discovers it the hard way."""
    seeds_dir = REPO_ROOT / "tests" / "fixtures" / "smartart_seeds"
    expected = {
        "process1_seed.pptx",
        "cycle1_seed.pptx",
        "orgChart1_seed.pptx",
        "blank_slide.pptx",
    }
    present = {p.name for p in seeds_dir.glob("*.pptx")}
    missing = expected - present
    assert not missing, (
        f"required seed fixtures missing: {missing}. These were all "
        f"committed during Phase 0. If one was deleted, recover it "
        f"from git history or re-author per the spike report."
    )
