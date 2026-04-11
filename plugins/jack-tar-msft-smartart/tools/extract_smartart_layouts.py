"""Extract SmartArt layout definitions from .pptx / .potx files.

For each diagram found in each input file, this script extracts the three
layout definition parts (`layout{N}.xml`, `quickStyle{N}.xml`,
`colors{N}.xml`) plus the three URIs from the doc point of
`data{N}.xml` (`loTypeId`, `qsTypeId`, `csTypeId`) and writes them to
`tests/fixtures/smartart_layouts/<layout_id>/`.

`layout_id` is derived from `loTypeId`:
    urn:microsoft.com/office/officeart/2005/8/layout/process1#1 → process1

Variant suffixes (`#1`, `#2`, ...) are stripped so multiple variants of
the same base layout collapse to one directory. When multiple fixtures
supply the same base layout, the first one encountered wins (and a
warning is printed).

Usage:

    python tools/extract_smartart_layouts.py INPUT_FILE [INPUT_FILE ...]

    python tools/extract_smartart_layouts.py --sdk

The `--sdk` flag downloads the 29 known SmartArt-containing files from
the MIT-licensed `dotnet/Open-XML-SDK` repo and extracts from all of them
in one pass.

Rerunning the script is safe — existing layout directories are
overwritten.

Output per layout:

    tests/fixtures/smartart_layouts/<id>/
        layout.xml          <- the dgm:layoutDef content
        quickStyle.xml      <- the dgm:styleDef content
        colors.xml          <- the dgm:colorsDef content
        meta.json           <- { layout_uri, qs_type_id, cs_type_id, source_file, category_hint, base_name }

The script does NOT modify catalog.json — adding a new extracted layout
to the catalog is a separate, manual step (see
`src/smartart_pptx_native/layouts/catalog.json`).

Legal: the MIT license of dotnet/Open-XML-SDK covers the extracted
content. See tests/fixtures/smartart_layouts/LICENSING.md.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "tests" / "fixtures" / "smartart_layouts"

# ---------------------------------------------------------------------------
# Known SmartArt-containing files in the dotnet/Open-XML-SDK repo
# ---------------------------------------------------------------------------
# Identified by scanning all 224 .pptx/.potx test fixtures for
# `ppt/diagrams/layout1.xml` presence. 29 files contained SmartArt.
# Commit at scan time: main branch, 2026-04-08.
SDK_REPO = "dotnet/Open-XML-SDK"
SDK_BRANCH = "main"
SDK_FILES = [
    "test/DocumentFormat.OpenXml.Tests.Assets/assets/TestDataStorage/v2FxTestFiles/presentation/O12 templates/CycleDiagram_TP10174326.potx",
    "test/DocumentFormat.OpenXml.Tests.Assets/assets/TestDataStorage/v2FxTestFiles/presentation/O12 templates/HierarchyDiagram_TP10174325.potx",
    "test/DocumentFormat.OpenXml.Tests.Assets/assets/TestDataStorage/v2FxTestFiles/presentation/O12 templates/ListDiagram_TP10174331.potx",
    "test/DocumentFormat.OpenXml.Tests.Assets/assets/TestDataStorage/v2FxTestFiles/presentation/O12 templates/MatrixDiagram_TP10174328.potx",
    "test/DocumentFormat.OpenXml.Tests.Assets/assets/TestDataStorage/v2FxTestFiles/presentation/O12 templates/ProcessDiagram_TP10174324.potx",
    "test/DocumentFormat.OpenXml.Tests.Assets/assets/TestDataStorage/v2FxTestFiles/presentation/O12 templates/PyramidDiagram_TP10174330.potx",
    "test/DocumentFormat.OpenXml.Tests.Assets/assets/TestDataStorage/v2FxTestFiles/presentation/O12 templates/RelationshipDiagram_TP10174327.potx",
    "test/DocumentFormat.OpenXml.Tests.Assets/assets/TestDataStorage/v2FxTestFiles/presentation/SmartArt_OrgChart1+Animation (Fly In, as one object).pptx",
    "test/DocumentFormat.OpenXml.Tests.Assets/assets/TestDataStorage/v2FxTestFiles/presentation/SmartArt_OrgChart1+Animation (Fly In, by level one by one).pptx",
    "test/DocumentFormat.OpenXml.Tests.Assets/assets/TestDataStorage/v2FxTestFiles/presentation/SmartArt_OrgChart1.pptx",
    "test/DocumentFormat.OpenXml.Tests.Assets/assets/TestDataStorage/v2FxTestFiles/presentation/SmartArt_OrgChart1_3D+Animation (Fly In, as one object).pptx",
    "test/DocumentFormat.OpenXml.Tests.Assets/assets/TestDataStorage/v2FxTestFiles/presentation/SmartArt_OrgChart1_3D+Animation (Fly In, by level one by one).pptx",
    "test/DocumentFormat.OpenXml.Tests.Assets/assets/TestDataStorage/v2FxTestFiles/presentation/SmartArt_OrgChart1_3D.pptx",
]
# In addition to the explicitly SmartArt-named files above, our earlier
# scan identified these generic-named fixtures that also contain SmartArt.
# This list was produced by
# `scan.py` (see git history) against all 224 .pptx/.potx files in the
# SDK repo at main/HEAD.
SDK_FILES_DISCOVERED = [
    # Populated dynamically by --sdk mode via repo tree walk.
]


def _raw_url(path: str) -> str:
    encoded = urllib.parse.quote(path, safe="/")
    return f"https://raw.githubusercontent.com/{SDK_REPO}/{SDK_BRANCH}/{encoded}"


def _download(url: str, cache_dir: Path) -> bytes:
    """Download a URL, caching the response in cache_dir."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", url.rsplit("/", 1)[-1])
    cache_path = cache_dir / safe_name
    if cache_path.exists():
        return cache_path.read_bytes()
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = resp.read()
    cache_path.write_bytes(data)
    return data


# ---------------------------------------------------------------------------
# Layout URI helpers
# ---------------------------------------------------------------------------

_URI_RE = re.compile(
    r"^urn:microsoft\.com/office/officeart/\d{4}/\d+/layout/([A-Za-z][A-Za-z0-9]*)"
    r"(#\d+)?$"
)


def _parse_layout_uri(uri: str) -> tuple[str, str | None]:
    """Return (base_name, variant) from a full layout URI.

    base_name is the short identifier (e.g. 'process1').
    variant is the '#N' suffix if present (e.g. '#1'), else None.
    """
    m = _URI_RE.match(uri)
    if not m:
        raise ValueError(f"unexpected layout URI format: {uri}")
    return m.group(1), m.group(2)


def _category_hint_from_base_name(base: str) -> str:
    """Guess a SmartArt category from the layout base name."""
    # Case-insensitive substring matching with ordered priorities
    lower = base.lower()
    if "orgchart" in lower or "hierarchy" in lower:
        return "Hierarchy"
    if "cycle" in lower:
        return "Cycle"
    if "pyramid" in lower:
        return "Pyramid"
    if "matrix" in lower:
        return "Matrix"
    if "venn" in lower or "funnel" in lower or "target" in lower:
        return "Relationship"
    if "process" in lower or "chevron" in lower:
        return "Process"
    if "list" in lower:
        return "List"
    if "pic" in lower:  # pList1, pPictGrid, etc.
        return "Picture"
    return "Unknown"


# ---------------------------------------------------------------------------
# Diagram extraction
# ---------------------------------------------------------------------------

def _extract_urn_attr(data_xml: str, attr: str) -> str | None:
    """Grep a URI-valued attribute from the doc point's prSet."""
    m = re.search(rf'{attr}="([^"]+)"', data_xml)
    return m.group(1) if m else None


def _find_diagram_numbers(zf: zipfile.ZipFile) -> list[int]:
    """Return all diagram indices N such that ppt/diagrams/data{N}.xml exists."""
    numbers: list[int] = []
    for name in zf.namelist():
        m = re.match(r"^ppt/diagrams/data(\d+)\.xml$", name)
        if m:
            numbers.append(int(m.group(1)))
    return sorted(numbers)


def _extract_from_pptx(
    pptx_bytes: bytes,
    source_label: str,
    output_dir: Path,
    already_written: set[str],
) -> list[dict[str, Any]]:
    """Open a .pptx/.potx in memory, extract each SmartArt diagram's
    parts, and write them to output_dir/<layout_base>/.

    Returns a list of extraction summaries (one per layout written).
    """
    summaries: list[dict[str, Any]] = []
    try:
        with zipfile.ZipFile(io.BytesIO(pptx_bytes)) as zf:
            names = set(zf.namelist())
            numbers = _find_diagram_numbers(zf)
            if not numbers:
                return summaries
            for n in numbers:
                data_name = f"ppt/diagrams/data{n}.xml"
                layout_name = f"ppt/diagrams/layout{n}.xml"
                qs_name = f"ppt/diagrams/quickStyle{n}.xml"
                colors_name = f"ppt/diagrams/colors{n}.xml"
                if not all(name in names for name in (layout_name, qs_name, colors_name)):
                    continue
                data_content = zf.read(data_name).decode("utf-8", errors="replace")
                layout_uri = _extract_urn_attr(data_content, "loTypeId")
                qs_uri = _extract_urn_attr(data_content, "qsTypeId")
                cs_uri = _extract_urn_attr(data_content, "csTypeId")
                if not layout_uri:
                    continue
                try:
                    base_name, variant = _parse_layout_uri(layout_uri)
                except ValueError:
                    continue

                if base_name in already_written:
                    # Already extracted from an earlier file. Record but skip.
                    summaries.append({
                        "layout_uri": layout_uri,
                        "base_name": base_name,
                        "variant": variant,
                        "source_file": source_label,
                        "written": False,
                        "reason": "duplicate — base already extracted",
                    })
                    continue

                layout_dir = output_dir / base_name
                layout_dir.mkdir(parents=True, exist_ok=True)
                (layout_dir / "layout.xml").write_bytes(zf.read(layout_name))
                (layout_dir / "quickStyle.xml").write_bytes(zf.read(qs_name))
                (layout_dir / "colors.xml").write_bytes(zf.read(colors_name))
                meta = {
                    "base_name": base_name,
                    "variant": variant,
                    "layout_uri": layout_uri,
                    "qs_type_id": qs_uri,
                    "cs_type_id": cs_uri,
                    "category_hint": _category_hint_from_base_name(base_name),
                    "source_file": source_label,
                }
                (layout_dir / "meta.json").write_text(
                    json.dumps(meta, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                already_written.add(base_name)
                summaries.append({**meta, "written": True})
    except zipfile.BadZipFile:
        pass
    return summaries


# ---------------------------------------------------------------------------
# SDK mode — scan repo, find all .pptx/.potx with SmartArt, extract
# ---------------------------------------------------------------------------

def _sdk_discover_and_extract(output_dir: Path, cache_dir: Path) -> list[dict[str, Any]]:
    """Walk the SDK repo tree, download every .pptx/.potx, scan each for
    SmartArt diagrams, and extract.

    Returns the full list of extraction summaries.
    """
    import subprocess

    print("Discovering .pptx/.potx files in the SDK repo...")
    result = subprocess.run(
        [
            "gh", "api",
            f"repos/{SDK_REPO}/git/trees/{SDK_BRANCH}?recursive=1",
            "--jq",
            '.tree[] | select(.path | test("\\\\.(pptx|potx)$")) | .path',
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    all_files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    print(f"  found {len(all_files)} .pptx/.potx files in the SDK repo")

    summaries: list[dict[str, Any]] = []
    already_written: set[str] = set()
    smartart_files = 0

    for i, path in enumerate(all_files, 1):
        if i % 25 == 0:
            print(f"  {i}/{len(all_files)} scanned, {len(already_written)} layouts extracted so far")
        try:
            data = _download(_raw_url(path), cache_dir)
        except Exception as exc:
            print(f"  WARN: download failed for {path}: {exc}", file=sys.stderr)
            continue
        per_file = _extract_from_pptx(data, source_label=path, output_dir=output_dir, already_written=already_written)
        if any(s.get("written") for s in per_file):
            smartart_files += 1
        summaries.extend(per_file)

    print()
    print(f"  files containing SmartArt: {smartart_files}")
    print(f"  unique layouts extracted:  {len(already_written)}")
    return summaries


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inputs",
        nargs="*",
        help="One or more .pptx/.potx file paths to extract from.",
    )
    parser.add_argument(
        "--sdk",
        action="store_true",
        help="Discover and extract from all .pptx/.potx files in the Open XML SDK repo.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory to write extracted layouts to (default: tests/fixtures/smartart_layouts).",
    )
    parser.add_argument(
        "--cache-dir",
        default=str(REPO_ROOT / "tmp" / "sdk_fixture_cache"),
        help="Directory to cache downloaded SDK files (default: tmp/sdk_fixture_cache).",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    cache_dir = Path(args.cache_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summaries: list[dict[str, Any]] = []

    if args.sdk:
        summaries.extend(_sdk_discover_and_extract(output_dir, cache_dir))

    already_written = {s["base_name"] for s in summaries if s.get("written")}

    for path_str in args.inputs:
        path = Path(path_str)
        if not path.exists():
            print(f"WARN: file not found: {path}", file=sys.stderr)
            continue
        data = path.read_bytes()
        summaries.extend(_extract_from_pptx(
            data,
            source_label=str(path),
            output_dir=output_dir,
            already_written=already_written,
        ))

    written = [s for s in summaries if s.get("written")]
    skipped = [s for s in summaries if not s.get("written")]

    print()
    print("=== EXTRACTION SUMMARY ===")
    print(f"Wrote {len(written)} layout directories:")
    for s in sorted(written, key=lambda x: x["base_name"]):
        print(f"  {s['base_name']:20s}  {s['category_hint']:15s}  {s['layout_uri']}")
    if skipped:
        print(f"Skipped {len(skipped)} duplicate entries (base layout already seen)")

    # Emit a full manifest alongside the extracted directories
    manifest_path = output_dir / "_extraction_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "extracted_at": "2026-04-08",
                "source_repo": SDK_REPO,
                "source_branch": SDK_BRANCH,
                "layouts": sorted(
                    [s for s in summaries if s.get("written")],
                    key=lambda x: x["base_name"],
                ),
            },
            indent=2,
        )
        + "\n"
    )
    print()
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
