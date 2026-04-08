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
        assert len(entry["when_to_use"]) >= 3, (
            f"entry {entry['id']} needs at least 3 'when to use' items"
        )
        assert len(entry["when_not_to_use"]) >= 3, (
            f"entry {entry['id']} needs at least 3 'when NOT to use' items"
        )
        # Each item must be a sentence, not a single word
        for item in entry["when_to_use"] + entry["when_not_to_use"]:
            assert len(item) > 15, (
                f"entry {entry['id']} has too-short guidance: {item!r}"
            )


# ---------------------------------------------------------------------------
# Per-entry coverage audit
# ---------------------------------------------------------------------------

def test_every_v1_entry_has_importable_builder():
    """Every v1 catalog entry's builder_module must:
    - be importable
    - expose a build_data_model callable
    - expose get_layout_uri returning the catalog entry's layout_uri
    """
    from src.smartart_pptx_native.layouts import catalog

    for entry in catalog.list_entries(v1_only=True):
        module_name = entry["builder_module"]
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            pytest.fail(
                f"entry {entry['id']!r} builder_module {module_name} "
                f"cannot be imported: {exc}"
            )

        assert hasattr(module, "build_data_model"), (
            f"{module_name} is missing build_data_model"
        )
        assert callable(module.build_data_model), (
            f"{module_name}.build_data_model is not callable"
        )

        assert hasattr(module, "get_layout_uri"), (
            f"{module_name} is missing get_layout_uri"
        )
        assert module.get_layout_uri() == entry["layout_uri"], (
            f"{module_name}.get_layout_uri() returned "
            f"{module.get_layout_uri()!r} but catalog declares "
            f"{entry['layout_uri']!r}"
        )


def test_every_v1_entry_can_render_its_example_input_end_to_end():
    """Exercise the full path for every v1 entry using its committed
    example_input. If any layout can't render its own example, the
    catalog is lying and something is broken."""
    import tempfile
    from src.smartart_pptx_native import engine
    from src.smartart_pptx_native.layouts import catalog

    for entry in catalog.list_entries(v1_only=True):
        graphic_type = entry["integration"]["smartart_type_mappings"][0]
        spec = {
            "graphic_type": graphic_type,
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


def test_seed_files_are_not_empty_or_trivial():
    """Seeds under 10 KB are suspicious — an empty PowerPoint .pptx
    template is typically 30+ KB. If a seed is tiny, it's probably
    corrupt or missing its diagram parts."""
    from src.smartart_pptx_native.layouts import catalog

    for entry in catalog.list_entries(v1_only=True):
        seed = catalog.resolve_seed_path(entry)
        size = seed.stat().st_size
        assert size > 10_000, (
            f"entry {entry['id']!r} seed is suspiciously small "
            f"({size} bytes) — expected 30+ KB for a real SmartArt seed"
        )
