"""Model catalog refresh — release-decoupled catalog updates (EPIC #125, #128).

Fetches the canonical model catalog from the repository's main branch,
validates it against the installed loader, surfaces a pricing/model diff
for the operator gate, and atomically swaps it into the local cache that
``model_catalog.load_catalog`` prefers over the shipped baseline.

Design constraints:

- **The operator gate is load-bearing** (CLAUDE.md F10): cost figures drive
  the free→cost cascade gates, so a refresh that changes any price MUST be
  surfaced to the operator before it takes effect. ``diff_catalogs`` is the
  gate's evidence; the refresh-models skill presents it and waits for
  explicit go-ahead. Refresh is on-request, never silent.
- **A bad remote can never brick an install**: the remote document is
  validated (structure + min_loader_version) BEFORE it touches the cache;
  the previous cache is kept alongside for one-command rollback; and the
  loader independently re-validates the cache on every load, falling back
  to the shipped baseline if it is somehow corrupt.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

try:
    from .model_catalog import (
        CATALOG_CACHE_ENV,
        CatalogError,
        load_catalog,
        validate_catalog,
    )
except ImportError:  # pragma: no cover - direct-script execution path
    from model_catalog import (
        CATALOG_CACHE_ENV,
        CatalogError,
        load_catalog,
        validate_catalog,
    )

logger = logging.getLogger(__name__)

#: Canonical published location — the repo's main branch. A catalog-only
#: commit to main is picked up by every install on next refresh, no plugin
#: release required.
DEFAULT_REMOTE_URL = (
    "https://raw.githubusercontent.com/SteveGJones/jack-tar-deckhand/"
    "main/model-catalog/model-catalog.json"
)

REMOTE_URL_ENV = "JACK_TAR_CATALOG_URL"

_DEFAULT_CACHE_PATH = Path.home() / ".jack-tar" / "model-catalog.json"
_PREV_SUFFIX = ".prev"


def _cache_path(cache_path=None):
    return Path(
        cache_path
        or os.environ.get(CATALOG_CACHE_ENV)
        or _DEFAULT_CACHE_PATH
    )


def fetch_remote_catalog(url=None, timeout=15):
    """Fetch and parse the remote catalog document. Raises CatalogError.

    The document is structurally validated (including min_loader_version
    against the installed loader) before being returned — callers never
    see an unusable catalog.
    """
    import requests

    target = url or os.environ.get(REMOTE_URL_ENV) or DEFAULT_REMOTE_URL
    try:
        response = requests.get(target, timeout=timeout)
        response.raise_for_status()
        doc = response.json()
    except requests.RequestException as exc:
        raise CatalogError(f"cannot fetch remote catalog from {target}: {exc}")
    except ValueError as exc:
        raise CatalogError(f"remote catalog at {target} is not valid JSON: {exc}")
    validate_catalog(doc)
    return doc


def diff_catalogs(current_doc, new_doc):
    """Diff two catalog documents for the operator gate.

    Returns a dict:
        price_changes: [{model, component, old, new}]  — GATE-RELEVANT
        added_models: [id]
        removed_models: [id]
        status_changes: [{model, old, new, replacement}]
        version: {old, new}
    """
    def _by_id(doc):
        return {e["id"]: e for e in doc["models"]}

    def _flatten_pricing(entry):
        flat = {}
        pricing = entry.get("pricing") or {}
        for key in ("flat",):
            if key in pricing:
                flat[key] = pricing[key]
        for res, cost in (pricing.get("per_resolution") or {}).items():
            flat[f"per_resolution.{res}"] = cost
        for backend, table in (pricing.get("backends") or {}).items():
            for res, cost in table.items():
                flat[f"backends.{backend}.{res}"] = cost
        for key, cost in (pricing.get("per_size_quality") or {}).items():
            flat[f"per_size_quality.{key}"] = cost
        for tier, cost in (pricing.get("per_tier") or {}).items():
            flat[f"per_tier.{tier}"] = cost
        tiered = pricing.get("tiered_megapixel")
        if tiered:
            flat["tiered_megapixel.first_mp"] = tiered["first_mp"]
            flat["tiered_megapixel.per_extra_mp"] = tiered["per_extra_mp"]
        for component, rate in (pricing.get("token_rates") or {}).items():
            flat[f"token_rates.{component}"] = rate
        return flat

    current = _by_id(current_doc)
    new = _by_id(new_doc)

    price_changes = []
    status_changes = []
    for model_id in sorted(set(current) & set(new)):
        old_prices = _flatten_pricing(current[model_id])
        new_prices = _flatten_pricing(new[model_id])
        for component in sorted(set(old_prices) | set(new_prices)):
            old_value = old_prices.get(component)
            new_value = new_prices.get(component)
            if old_value != new_value:
                price_changes.append({
                    "model": model_id,
                    "component": component,
                    "old": old_value,
                    "new": new_value,
                })
        if current[model_id]["status"] != new[model_id]["status"]:
            status_changes.append({
                "model": model_id,
                "old": current[model_id]["status"],
                "new": new[model_id]["status"],
                "replacement": new[model_id].get("replacement"),
            })

    return {
        "price_changes": price_changes,
        "added_models": sorted(set(new) - set(current)),
        "removed_models": sorted(set(current) - set(new)),
        "status_changes": status_changes,
        "version": {
            "old": current_doc["catalog_version"],
            "new": new_doc["catalog_version"],
        },
    }


def check_remote(url=None, cache_path=None, local_config_path=None):
    """Fetch the remote catalog and diff it against the effective catalog.

    Read-only: nothing is written. Returns {remote_doc, diff, current_version,
    current_source} — the refresh-models skill renders the diff for the
    operator gate and only calls apply_refresh after explicit go-ahead.
    """
    current = load_catalog(
        cache_path=cache_path, local_config_path=local_config_path
    )
    remote_doc = fetch_remote_catalog(url=url)
    return {
        "remote_doc": remote_doc,
        "diff": diff_catalogs(current.doc, remote_doc),
        "current_version": current.version,
        "current_source": current.source,
    }


def apply_refresh(new_doc, cache_path=None):
    """Atomically install a validated catalog document into the cache.

    The previous cache (if any) is preserved at ``<cache>.prev`` for
    rollback. Returns {cache_path, previous_kept, version}.
    """
    validate_catalog(new_doc)
    path = _cache_path(cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    previous_kept = False
    if path.exists():
        path.with_suffix(path.suffix + _PREV_SUFFIX).write_bytes(path.read_bytes())
        previous_kept = True

    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(new_doc, f, indent=2)
            f.write("\n")
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise

    logger.info(
        "model catalog cache updated: %s (version %s)",
        path, new_doc["catalog_version"],
    )
    return {
        "cache_path": str(path),
        "previous_kept": previous_kept,
        "version": new_doc["catalog_version"],
    }


def rollback(cache_path=None):
    """Restore the previous cached catalog. Returns the restored version.

    Raises CatalogError when there is no previous copy to restore.
    """
    path = _cache_path(cache_path)
    prev = path.with_suffix(path.suffix + _PREV_SUFFIX)
    if not prev.exists():
        raise CatalogError(
            f"no previous catalog to roll back to at {prev} — "
            f"delete {path} instead to fall back to the shipped baseline"
        )
    doc = json.loads(prev.read_text())
    validate_catalog(doc)
    os.replace(prev, path)
    logger.info("model catalog cache rolled back to version %s", doc["catalog_version"])
    return {"cache_path": str(path), "version": doc["catalog_version"]}


def staleness_report(cache_path=None, local_config_path=None):
    """Non-blocking staleness hint for /verify: current catalog identity.

    Does NOT hit the network — reports what is loaded and from where, plus
    the cache file's age in days when a cache is in use.
    """
    catalog = load_catalog(
        cache_path=cache_path, local_config_path=local_config_path
    )
    report = {
        "version": catalog.version,
        "updated": catalog.updated,
        "source": catalog.source,
    }
    path = _cache_path(cache_path)
    if path.exists():
        import time
        age_days = (time.time() - path.stat().st_mtime) / 86400
        report["cache_age_days"] = round(age_days, 1)
    return report
