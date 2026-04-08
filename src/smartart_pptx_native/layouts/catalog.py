"""Layout catalog loader.

Single source of truth for the per-layout metadata the pptx_native
engine, extractor, selector, QA checks, and manual-gate tooling all
consume. See spec §5 for the schema definition.

Usage:

    from src.smartart_pptx_native.layouts import catalog
    entry = catalog.get_entry("process1")
    entry["layout_uri"]   # -> "urn:.../layout/process1"
    entry["max_nodes"]    # -> 9
"""
from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Any

_CATALOG_DIR = Path(__file__).resolve().parent
_CATALOG_PATH = _CATALOG_DIR / "catalog.json"
_SCHEMA_PATH = _CATALOG_DIR / "catalog.schema.json"

# Repo root = three levels up from this file
# (src/smartart_pptx_native/layouts/catalog.py → repo root).
REPO_ROOT = Path(__file__).resolve().parents[3]


class CatalogError(Exception):
    """Raised when the catalog fails to load or validate."""


@functools.lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    """Load and validate the catalog. Cached — safe to call repeatedly.

    Returns:
        Parsed catalog dict with schema already validated. Raises
        CatalogError on any load or validation failure.
    """
    import jsonschema

    if not _CATALOG_PATH.exists():
        raise CatalogError(f"catalog.json not found at {_CATALOG_PATH}")
    if not _SCHEMA_PATH.exists():
        raise CatalogError(f"catalog.schema.json not found at {_SCHEMA_PATH}")

    try:
        with _CATALOG_PATH.open("r", encoding="utf-8") as f:
            catalog = json.load(f)
    except json.JSONDecodeError as exc:
        raise CatalogError(f"catalog.json is not valid JSON: {exc}") from exc

    try:
        with _SCHEMA_PATH.open("r", encoding="utf-8") as f:
            schema = json.load(f)
    except json.JSONDecodeError as exc:
        raise CatalogError(f"catalog.schema.json is not valid JSON: {exc}") from exc

    # Use an explicit validator class so we don't depend on jsonschema's
    # metaschema lookup, which emits a DeprecationWarning on recent versions.
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(catalog), key=lambda e: e.path)
    if errors:
        first = errors[0]
        raise CatalogError(
            f"catalog.json fails schema validation: {first.message} "
            f"at path {list(first.absolute_path)}"
        )

    # Extra semantic checks not expressible in JSONSchema alone.
    ids = [entry["id"] for entry in catalog["entries"]]
    if len(ids) != len(set(ids)):
        raise CatalogError(f"catalog.json has duplicate entry ids: {ids}")

    for entry in catalog["entries"]:
        if entry["min_nodes"] > entry["max_nodes"]:
            raise CatalogError(
                f"entry {entry['id']!r}: min_nodes "
                f"({entry['min_nodes']}) > max_nodes ({entry['max_nodes']})"
            )

    return catalog


def get_entry(layout_id: str) -> dict[str, Any]:
    """Look up a single entry by id.

    Args:
        layout_id: The entry's `id` field (e.g. "process1").

    Returns:
        The entry dict.

    Raises:
        CatalogError: If no entry with that id exists.
    """
    catalog = load_catalog()
    for entry in catalog["entries"]:
        if entry["id"] == layout_id:
            return entry
    available = ", ".join(e["id"] for e in catalog["entries"])
    raise CatalogError(
        f"no catalog entry with id {layout_id!r} (available: {available})"
    )


def list_entries(v1_only: bool = False) -> list[dict[str, Any]]:
    """Return all entries, optionally filtered to v1 scope."""
    catalog = load_catalog()
    if v1_only:
        return [e for e in catalog["entries"] if e.get("v1", False)]
    return list(catalog["entries"])


def resolve_seed_path(entry: dict[str, Any]) -> Path:
    """Resolve a catalog entry's seed_path to an absolute Path.

    seed_path in the catalog is relative to the repo root.
    """
    return REPO_ROOT / entry["seed_path"]


def get_layout_id_for_graphic_type(graphic_type: str) -> str | None:
    """Find which layout (if any) backs a given graphic_type.

    Walks the catalog looking for an entry whose
    `integration.smartart_type_mappings` includes the given
    graphic_type. Returns the first matching layout id, or None.
    """
    for entry in load_catalog()["entries"]:
        if graphic_type in entry["integration"]["smartart_type_mappings"]:
            return entry["id"]
    return None
