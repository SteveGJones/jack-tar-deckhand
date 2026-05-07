"""Security primitives.

Three concerns covered here, all surfaced as hard contracts in the
spec's Security & Privacy section:

  1. Image-path allowlist — paths passed to python-pptx image APIs
     must resolve inside an explicit set of allowed roots; symlinks
     are rejected outright. Default callers pass ['<run>/generated',
     '<run>/carriers'].
  2. .pptx pre-flight — refuse files exceeding decompressed-size,
     part-count, per-part-size, or compression-ratio ceilings before
     python-pptx opens them.
  3. Hardened XML parser — every place the bridge parses XML directly
     uses this parser config so XXE / DTD-expansion / huge-tree
     attacks cannot land.
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Iterable

from lxml import etree


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class AllowedPathError(ValueError):
    """Raised when an image path resolves outside the allowlist or is a symlink."""


class PptxPreflightError(ValueError):
    """Raised when a .pptx fails any of the pre-flight resource ceilings."""


class XmlSecurityError(ValueError):
    """Raised when XML parsing cannot proceed under the safe parser config."""


# ---------------------------------------------------------------------------
# Image-path allowlist
# ---------------------------------------------------------------------------

def resolve_within_allowlist(path: Path | str, allowed_roots: Iterable[Path]) -> Path:
    """Return `path.resolve()` if it is inside any allowed_root and not a symlink.

    Raises AllowedPathError otherwise.
    """
    p = Path(path)
    if p.is_symlink():
        raise AllowedPathError(f"path is a symlink and is rejected: {p}")
    resolved = p.resolve()
    for root in allowed_roots:
        root_resolved = Path(root).resolve()
        try:
            resolved.relative_to(root_resolved)
            return resolved
        except ValueError:
            continue
    raise AllowedPathError(
        f"path is outside the image-path allowlist: {p} (allowed roots: "
        f"{[str(r) for r in allowed_roots]})"
    )


# ---------------------------------------------------------------------------
# .pptx pre-flight
# ---------------------------------------------------------------------------

# Raising any of these ceilings weakens zip-bomb / resource-exhaustion
# protection. The defaults are calibrated for typical conference decks
# (1-200 slides, ~50-100 parts, <50MB compressed). Override only with
# an explicit threat-model justification.
DEFAULT_DECOMPRESSED_CEILING_BYTES = 200 * 1024 * 1024     # 200 MB
DEFAULT_PART_COUNT_CEILING = 2000
DEFAULT_PER_PART_CEILING_BYTES = 50 * 1024 * 1024          # 50 MB
DEFAULT_RATIO_CEILING = 100                                # decompressed / compressed


def preflight_pptx(
    path: Path | str,
    *,
    decompressed_ceiling_bytes: int = DEFAULT_DECOMPRESSED_CEILING_BYTES,
    part_count_ceiling: int = DEFAULT_PART_COUNT_CEILING,
    per_part_ceiling_bytes: int = DEFAULT_PER_PART_CEILING_BYTES,
    ratio_ceiling: int = DEFAULT_RATIO_CEILING,
) -> None:
    """Refuse the .pptx if any resource ceiling is exceeded.

    Raises PptxPreflightError on any failure with a diagnostic message
    naming the specific check that failed.
    """
    p = Path(path)
    if not p.is_file():
        raise PptxPreflightError(f"not a file: {p}")
    compressed_size = p.stat().st_size

    try:
        with zipfile.ZipFile(p, "r") as zf:
            infos = zf.infolist()
    except zipfile.BadZipFile as exc:
        raise PptxPreflightError(f"not a valid zip archive: {p}") from exc

    if len(infos) > part_count_ceiling:
        raise PptxPreflightError(
            f"part count {len(infos)} exceeds ceiling {part_count_ceiling}"
        )

    total_decompressed = 0
    for info in infos:
        if info.file_size > per_part_ceiling_bytes:
            raise PptxPreflightError(
                f"part size {info.file_size} for {info.filename!r} exceeds "
                f"ceiling {per_part_ceiling_bytes}"
            )
        total_decompressed += info.file_size

    if total_decompressed > decompressed_ceiling_bytes:
        raise PptxPreflightError(
            f"total decompressed size {total_decompressed} exceeds ceiling "
            f"{decompressed_ceiling_bytes}"
        )

    if compressed_size > 0:
        ratio = total_decompressed / compressed_size
        if ratio > ratio_ceiling:
            raise PptxPreflightError(
                f"compression ratio {ratio:.1f} exceeds ceiling {ratio_ceiling} "
                f"(zip-bomb signal)"
            )


# ---------------------------------------------------------------------------
# Hardened XML parser
# ---------------------------------------------------------------------------

def safe_xml_parser() -> etree.XMLParser:
    """Return an XMLParser configured to disable the common attack vectors.

    - resolve_entities=False  → no XXE / DTD expansion
    - no_network=True         → external DTDs cannot be fetched
    - huge_tree=False         → reject deeply-nested or pathologically large trees
    - load_dtd=False          → avoid pulling DTDs altogether

    THREAT-MODEL BOUNDARY: the bridge does NOT parse user-supplied .pptx XML
    directly with lxml — all OOXML reads go through python-pptx (`Presentation`,
    `slide.element.find(...)`), which has its own lxml configuration. python-pptx
    1.0.2 is treated as the threat-model boundary for OOXML parsing: vulnerabilities
    in python-pptx's parser config are tracked upstream, not patched in the bridge.
    `safe_xml_parser` IS used everywhere the bridge constructs lxml elements
    directly (e.g. `enrichment_ops/background.py`'s _build_bg_element via
    etree.fromstring on bridge-emitted strings — bridge-controlled, not user-
    controlled, so the parser config matters less but is still applied).

    If the bridge ever needs to parse user-supplied raw XML directly (e.g. a
    future "validate the carrier .pptx parts" feature), this is the parser to
    use. Adding a new direct-parse path requires a spec amendment and a security
    review per the Security & Privacy section.
    """
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        huge_tree=False,
        load_dtd=False,
    )
