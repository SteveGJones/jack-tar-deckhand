"""Markdown generator for the pptx_native layout catalog.

Produces docs/pptx-native-smartart-catalog.md from catalog.json. The
markdown file is committed and CI tests enforce that it matches what
this generator would produce (drift detection).

Run manually:

    python -m src.smartart_pptx_native.layouts.catalog_markdown

Or programmatically:

    from src.smartart_pptx_native.layouts.catalog_markdown import generate
    print(generate())

The output is deterministic: same catalog.json in, same markdown out.
"""
from __future__ import annotations

from pathlib import Path

from src.smartart_pptx_native.layouts import catalog

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_PATH = REPO_ROOT / "docs" / "pptx-native-smartart-catalog.md"


def _bulleted(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _entry_section(entry: dict) -> str:
    """Render a single catalog entry as a markdown section."""
    lines: list[str] = []

    lines.append(f"## {entry['display_name']} (`{entry['id']}`)")
    lines.append("")
    lines.append(f"- **Category:** {entry['category']}")
    lines.append(f"- **Engine:** `{entry['engine']}`")
    lines.append(f"- **Layout URI:** `{entry['layout_uri']}`")
    lines.append(f"- **Data shape:** `{entry['data_shape']}`")

    node_caps = entry.get("node_type_capabilities", [])
    if node_caps:
        lines.append(
            f"- **Special node types:** {', '.join(f'`{c}`' for c in node_caps)}"
        )
    else:
        lines.append("- **Special node types:** none (only regular nodes)")

    lines.append(
        f"- **Capacity:** {entry['min_nodes']}-{entry['max_nodes']} nodes, "
        f"max {entry['max_label_chars']} chars per label"
    )
    lines.append(f"- **Layout directory:** `{entry['layout_dir']}`")
    lines.append(f"- **Quick style URI:** `{entry['qs_type_id']}`")
    lines.append(f"- **Colors URI:** `{entry['cs_type_id']}`")
    lines.append("")

    lines.append("### Visual character")
    lines.append("")
    lines.append(entry["visual_character"])
    lines.append("")

    lines.append("### When to use")
    lines.append("")
    lines.append(_bulleted(entry["when_to_use"]))
    lines.append("")

    lines.append("### When NOT to use")
    lines.append("")
    lines.append(_bulleted(entry["when_not_to_use"]))
    lines.append("")

    lines.append("### Capacity rationale")
    lines.append("")
    lines.append(entry["max_label_chars_rationale"])
    lines.append("")

    lines.append("### Selector rationale template")
    lines.append("")
    lines.append(f"> {entry['selector_rationale_template']}")
    lines.append("")

    lines.append("### Backs these graphic types")
    lines.append("")
    mappings = entry["integration"]["smartart_type_mappings"]
    lines.append(
        _bulleted([f"`{m}` (when conditions met)" for m in mappings])
    )
    lines.append("")
    lines.append(
        "**Selector routes to this layout when:** "
        f"{entry['integration']['replaces_custom_svg_when']}"
    )
    lines.append("")

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def generate() -> str:
    """Generate the full markdown catalog as a single string.

    Deterministic output — given a fixed catalog.json, always returns
    the same bytes. Used both for manual generation and for CI drift
    detection.
    """
    cat = catalog.load_catalog()

    lines: list[str] = []
    lines.append("# pptx_native SmartArt Layout Catalog")
    lines.append("")
    lines.append(
        "> This file is auto-generated from "
        "`src/smartart_pptx_native/layouts/catalog.json`. "
        "Do not edit by hand — run "
        "`python -m src.smartart_pptx_native.layouts.catalog_markdown` "
        "to regenerate."
    )
    lines.append("")
    lines.append(f"**Catalog version:** `{cat['version']}`")
    lines.append("")

    v1_entries = [e for e in cat["entries"] if e.get("v1")]
    other_entries = [e for e in cat["entries"] if not e.get("v1")]

    lines.append(
        f"**v1 layouts:** {len(v1_entries)} — "
        f"{', '.join(e['display_name'] for e in v1_entries)}"
    )
    if other_entries:
        lines.append(
            f"**Future layouts (non-v1):** {len(other_entries)} — "
            f"{', '.join(e['display_name'] for e in other_entries)}"
        )
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append(
        "| Layout | Category | Data shape | Max nodes | "
        "Max label chars | Backs |"
    )
    lines.append("|---|---|---|---:|---:|---|")
    for entry in v1_entries:
        mappings = ", ".join(
            f"`{m}`"
            for m in entry["integration"]["smartart_type_mappings"]
        )
        lines.append(
            f"| **{entry['display_name']}** "
            f"(`{entry['id']}`) | "
            f"{entry['category']} | "
            f"`{entry['data_shape']}` | "
            f"{entry['max_nodes']} | "
            f"{entry['max_label_chars']} | "
            f"{mappings} |"
        )
    lines.append("")

    lines.append("---")
    lines.append("")

    # Detailed entry sections
    lines.append("# Layouts in Detail")
    lines.append("")
    for entry in v1_entries:
        lines.append(_entry_section(entry))

    if other_entries:
        lines.append("# Future (non-v1) Layouts")
        lines.append("")
        for entry in other_entries:
            lines.append(_entry_section(entry))

    # Ensure file ends with a single newline
    content = "\n".join(lines).rstrip() + "\n"
    return content


def write_to_default_path() -> Path:
    """Write the generated markdown to OUTPUT_PATH, creating parent dirs."""
    content = generate()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(content, encoding="utf-8")
    return OUTPUT_PATH


if __name__ == "__main__":
    path = write_to_default_path()
    print(f"wrote {path}")
