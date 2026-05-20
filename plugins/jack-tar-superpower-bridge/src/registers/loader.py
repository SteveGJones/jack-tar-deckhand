"""Register-preset loader (issue #87).

A *register preset* bundles a palette + typography + layout typology +
default strap_style so a speaker can pin a single high-level register on
the brief and pull in coherent defaults across all four axes. The presets
themselves are markdown files under :mod:`src.registers.presets`; this
module enumerates and parses them.

Borrow note: the venue-loader pattern is adapted from paperbanana's
``methodology.py`` venue loader — a fixed canonical set of named profiles
loaded from disk on demand and validated against an enum. MIT-licensed.
The preset content + schema are original to jack-tar.

Preset file format (markdown with simple labelled sections)::

    # <preset-name>

    Default strap_style: <prose-sentence|all-caps-three-beat>

    ## Palette

    | Role | Hex | Usage |
    |---|---|---|
    | Surface | `#XXXXXX` | <description> |
    | ... | ... | ... |

    ## Typography

    <prose paragraph describing display/body type voice>

    ## Layout typology

    <prose paragraph describing default sub-page scales and marker patterns>

    ## When to reach for this register

    <prose paragraph helping the persona match subjects to this register>

The parser is forgiving — missing optional sections leave the corresponding
field empty. Default strap_style is required (it's the whole point of the
bundle) and must be one of the values accepted by :mod:`creative_brief`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

VALID_STRAP_STYLES = {"all-caps-three-beat", "prose-sentence"}

# The four v1 presets — enumerated here so unknown register values can be
# rejected without touching the filesystem. Adding a fifth preset means
# adding to this set AND dropping a new .md file in presets/.
KNOWN_REGISTERS: frozenset[str] = frozenset(
    {
        "infographic-narrative",
        "atmospheric-photo",
        "schematic-diagram",
        "editorial-mixed-case",
    }
)


class PresetNotFoundError(KeyError):
    """Raised when a register name is requested that isn't in KNOWN_REGISTERS."""


@dataclass
class Preset:
    """In-memory shape of a parsed register preset."""

    name: str
    default_strap_style: str
    palette_rows: list[dict[str, str]] = field(default_factory=list)
    typography: str = ""
    layout_typology: str = ""
    when_to_reach: str = ""


_PRESETS_DIR = Path(__file__).parent / "presets"


def list_preset_names() -> list[str]:
    """Return sorted list of canonical preset names known to the bridge."""
    return sorted(KNOWN_REGISTERS)


def load_preset(name: str) -> Preset:
    """Load and parse a preset by canonical name.

    Args:
        name: one of :data:`KNOWN_REGISTERS`.

    Returns:
        Preset: parsed structure.

    Raises:
        PresetNotFoundError: ``name`` is not in :data:`KNOWN_REGISTERS`.
        FileNotFoundError: preset directory is missing the ``.md`` file.
        ValueError: the file's metadata block is malformed.
    """
    if name not in KNOWN_REGISTERS:
        raise PresetNotFoundError(
            f"register preset {name!r} not in KNOWN_REGISTERS={sorted(KNOWN_REGISTERS)}"
        )
    md_path = _PRESETS_DIR / f"{name}.md"
    if not md_path.exists():
        raise FileNotFoundError(
            f"register preset {name!r} declared in KNOWN_REGISTERS but file "
            f"missing at {md_path}"
        )
    text = md_path.read_text(encoding="utf-8")
    return _parse_preset(name, text)


_STRAP_RE = re.compile(
    r"^Default strap_style:\s+(?P<strap>all-caps-three-beat|prose-sentence)\s*$",
    re.MULTILINE,
)


def _parse_preset(name: str, text: str) -> Preset:
    strap_match = _STRAP_RE.search(text)
    if not strap_match:
        raise ValueError(
            f"preset {name!r} missing required 'Default strap_style:' line "
            f"with one of {VALID_STRAP_STYLES}"
        )
    strap_style = strap_match.group("strap")

    sections = _split_sections(text)
    palette_rows = _parse_palette_rows(sections.get("Palette", ""))
    return Preset(
        name=name,
        default_strap_style=strap_style,
        palette_rows=palette_rows,
        typography=sections.get("Typography", "").strip(),
        layout_typology=sections.get("Layout typology", "").strip(),
        when_to_reach=sections.get("When to reach for this register", "").strip(),
    )


def _split_sections(text: str) -> dict[str, str]:
    """Return a dict of ``## Heading`` → body content (excluding the heading line)."""
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_lines: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = match.group(1)
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)
    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()
    return sections


def _parse_palette_rows(palette_section: str) -> list[dict[str, str]]:
    """Parse the markdown palette table into a list of {role, hex, usage} dicts."""
    rows: list[dict[str, str]] = []
    for line in palette_section.splitlines():
        # Match | role | `#hex` | usage |
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        role, hex_cell, usage = cells[0], cells[1], cells[2]
        # Skip header / separator rows
        if role.lower() in {"role", "---"} or set(role) <= set("-: "):
            continue
        if not hex_cell.startswith("`#") or not hex_cell.endswith("`"):
            continue
        rows.append(
            {
                "role": role,
                "hex": hex_cell.strip("`"),
                "usage": usage,
            }
        )
    return rows


def iter_all_presets() -> Iterable[Preset]:
    """Yield every known preset in canonical name order."""
    for name in list_preset_names():
        yield load_preset(name)
