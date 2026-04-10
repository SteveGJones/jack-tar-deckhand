"""Phase 4.5 catalog consolidation tests.

These tests enforce catalog quality beyond the schema-level checks in
test_pptx_native_catalog.py:

  - Drift detection: the committed Markdown catalog must match what
    the generator would produce from the current catalog.json
  - Rationale template linting: selector_rationale_templates must use
    sensible placeholder formats and not be empty
  - Per-entry coverage: every v1 catalog entry must have a builder
    module that imports successfully and exposes a build_data_model
    function, plus a seed file that exists and is valid
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
COMMITTED_MARKDOWN = REPO_ROOT / "docs" / "pptx-native-smartart-catalog.md"


# ---------------------------------------------------------------------------
# Drift detection
# ---------------------------------------------------------------------------

def test_committed_markdown_matches_generator_output():
    """The committed docs/pptx-native-smartart-catalog.md must be an
    exact byte-for-byte match with what catalog_markdown.generate()
    would produce right now. If this test fails, run:

        python -m src.smartart_pptx_native.layouts.catalog_markdown

    and commit the regenerated file.
    """
    from src.smartart_pptx_native.layouts import catalog_markdown

    assert COMMITTED_MARKDOWN.exists(), (
        "committed catalog markdown missing — run "
        "`python -m src.smartart_pptx_native.layouts.catalog_markdown` "
        "to generate it"
    )

    generated = catalog_markdown.generate()
    committed = COMMITTED_MARKDOWN.read_text(encoding="utf-8")

    assert generated == committed, (
        "catalog markdown has drifted from catalog.json — regenerate "
        "with `python -m src.smartart_pptx_native.layouts.catalog_markdown`"
    )


def test_generator_is_deterministic():
    """Running the generator twice in the same process must produce
    identical output."""
    from src.smartart_pptx_native.layouts import catalog_markdown

    first = catalog_markdown.generate()
    second = catalog_markdown.generate()
    assert first == second


# ---------------------------------------------------------------------------
# Rationale template linting
# ---------------------------------------------------------------------------

def test_every_v1_entry_has_non_trivial_selector_rationale_template():
    from src.smartart_pptx_native.layouts import catalog

    for entry in catalog.list_entries(v1_only=True):
        tmpl = entry["selector_rationale_template"]
        assert tmpl, f"entry {entry['id']} has empty rationale template"
        assert len(tmpl) > 40, (
            f"entry {entry['id']} rationale template is too short "
            f"({len(tmpl)} chars) — should explain when to use"
        )
        # Must mention editability (the selling point)
        lowered = tmpl.lower()
        assert "editable" in lowered or "edit" in lowered, (
            f"entry {entry['id']} rationale template should mention "
            f"editability — it's the whole point of pptx_native"
        )


def test_rationale_templates_use_valid_placeholders():
    """Allowed placeholders: {n}, {first}, {last}, {depth}. Any other
    placeholder in braces should be flagged — it's probably a typo."""
    import re
    from src.smartart_pptx_native.layouts import catalog

    valid = {"{n}", "{first}", "{last}", "{depth}"}

    for entry in catalog.list_entries(v1_only=True):
        tmpl = entry["selector_rationale_template"]
        placeholders = re.findall(r"\{[a-z_]+\}", tmpl)
        for p in placeholders:
            assert p in valid, (
                f"entry {entry['id']} uses unknown placeholder {p!r} "
                f"in selector_rationale_template (valid: {sorted(valid)})"
            )


def test_when_to_use_and_when_not_to_use_are_actionable():
    from src.smartart_pptx_native.layouts import catalog

    for entry in catalog.list_entries(v1_only=True):
        # Phase 8 relaxed: some categories have fewer items in their
        # default templates but the total guidance must still be useful.
        assert len(entry["when_to_use"]) >= 1, (
            f"entry {entry['id']} needs at least 1 'when to use' item"
        )
        assert len(entry["when_not_to_use"]) >= 1, (
            f"entry {entry['id']} needs at least 1 'when NOT to use' item"
        )
        # Each item must be a sentence, not a single word
        for item in entry["when_to_use"] + entry["when_not_to_use"]:
            assert len(item) > 10, (
                f"entry {entry['id']} has too-short guidance: {item!r}"
            )


# ---------------------------------------------------------------------------
# Per-entry coverage audit
# ---------------------------------------------------------------------------

def test_every_v1_entry_has_supported_data_shape():
    """Phase 8: builders are keyed by data_shape, not per-layout modules.
    Every v1 entry must declare a data_shape the generic builders
    dispatcher knows how to handle.
    """
    from src.smartart_pptx_native import builders
    from src.smartart_pptx_native.layouts import catalog

    for entry in catalog.list_entries(v1_only=True):
        data_shape = entry["data_shape"]
        assert data_shape in builders.BUILDER_BY_DATA_SHAPE, (
            f"entry {entry['id']!r} declares data_shape {data_shape!r} "
            f"but no builder is registered for it "
            f"(registered: {sorted(builders.BUILDER_BY_DATA_SHAPE)})"
        )


def test_every_v1_entry_can_render_its_example_input_end_to_end():
    """Exercise the full path for every v1 entry using its committed
    example_input. If any layout can't render its own example, the
    catalog is lying and something is broken.

    Phase 8: uses explicit layout_id in the spec to force the target
    layout — many graphic_types map to multiple layouts, but the
    example_input is for THIS specific layout.
    """
    import tempfile
    from src.smartart_pptx_native import engine
    from src.smartart_pptx_native.layouts import catalog

    for entry in catalog.list_entries(v1_only=True):
        graphic_type = entry["integration"]["smartart_type_mappings"][0]
        spec = {
            "graphic_type": graphic_type,
            "layout_id": entry["id"],  # force the specific layout
            "data": entry["example_input"],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                result = engine.render(spec, tmpdir)
            except Exception as exc:
                pytest.fail(
                    f"entry {entry['id']} could not render its own "
                    f"example_input: {exc}"
                )
            assert result.output_path.exists()
            assert result.layout_id == entry["id"]


def test_every_v1_entry_has_documented_capacity_rationale():
    from src.smartart_pptx_native.layouts import catalog

    for entry in catalog.list_entries(v1_only=True):
        rationale = entry["max_label_chars_rationale"]
        assert len(rationale) >= 30, (
            f"entry {entry['id']} max_label_chars_rationale is too "
            f"short ({len(rationale)} chars) — explain why the limit "
            f"is what it is"
        )


def test_layout_xml_files_are_not_empty_or_trivial():
    """The extracted layout.xml files must contain real layout
    definitions — a stub file < 1 KB is suspicious."""
    from src.smartart_pptx_native.layouts import catalog

    for entry in catalog.list_entries(v1_only=True):
        layout_dir = catalog.resolve_layout_dir(entry)
        layout_xml = layout_dir / "layout.xml"
        size = layout_xml.stat().st_size
        assert size > 1_000, (
            f"entry {entry['id']!r} layout.xml is suspiciously small "
            f"({size} bytes) — expected at least 1 KB for a real layout definition"
        )
