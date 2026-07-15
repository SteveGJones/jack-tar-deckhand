"""Model catalog loader — single source of truth for AI model identity,
capability, and pricing (EPIC #125).

Model IDs, aliases, retirement pointers, resolution capability, and cost
tables live in ``model-catalog.json``, NOT in code. This loader merges three
layers, lowest precedence first:

1. **Shipped baseline** — the ``model-catalog.json`` vendored next to this
   module (or the repo-level ``model-catalog/`` directory in development).
2. **Cached remote** — ``~/.jack-tar/model-catalog.json``, written by the
   refresh-models skill (issue #128). Replaces the baseline wholesale when
   present, valid, and loader-compatible; a bad cache falls back to shipped.
3. **Local overrides** — the ``model_catalog`` key in the project's
   ``local-config.json`` (gitignored). Entries merge per-model by id;
   ``role_defaults`` merge per-key.

Stdlib-only. Schema-level validation lives in
``model-catalog/model-catalog.schema.json`` (enforced by tests/CI); this
module performs structural validation sufficient to reject a broken cache
at runtime without a jsonschema dependency.
"""

from __future__ import annotations

import copy
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

#: Bump when the loader's expectations of the catalog shape change.
#: A catalog whose ``min_loader_version`` exceeds this is rejected.
LOADER_VERSION = 1

CATALOG_FILENAME = "model-catalog.json"

#: Env var pointing at an explicit catalog file (highest-priority baseline).
CATALOG_PATH_ENV = "JACK_TAR_MODEL_CATALOG"

#: Env var overriding the cached-remote location.
CATALOG_CACHE_ENV = "JACK_TAR_CATALOG_CACHE"

_DEFAULT_CACHE_PATH = Path.home() / ".jack-tar" / CATALOG_FILENAME

_ENTRY_REQUIRED_FIELDS = ("id", "provider", "status", "roles")
_VALID_STATUSES = frozenset({"active", "deprecated", "retired"})
_RESOLUTION_ALIASES = {"512": "512", "1K": "1K", "2K": "2K", "4K": "4K"}


class CatalogError(Exception):
    """Catalog missing, unparseable, or structurally invalid."""


class UnknownModelError(KeyError):
    """No catalog entry (id or alias) matches the requested model."""


class PricingError(ValueError):
    """The entry has no price for the requested parameters."""


def _normalise_resolution(resolution):
    key = str(resolution).strip().upper()
    if key in _RESOLUTION_ALIASES:
        return _RESOLUTION_ALIASES[key]
    raise PricingError(
        f"resolution={resolution!r} not recognised. "
        f"Valid values: {sorted(_RESOLUTION_ALIASES)}"
    )


def validate_catalog(doc):
    """Structurally validate a catalog document. Raises CatalogError.

    This is the runtime gate (cheap, stdlib-only). Full JSON-Schema
    validation runs in the test suite against model-catalog.schema.json.
    """
    if not isinstance(doc, dict):
        raise CatalogError("catalog root must be an object")
    for key in ("catalog_version", "min_loader_version", "updated", "models"):
        if key not in doc:
            raise CatalogError(f"catalog missing required key: {key}")
    min_loader = doc["min_loader_version"]
    if not isinstance(min_loader, int) or min_loader < 1:
        raise CatalogError("min_loader_version must be a positive integer")
    if min_loader > LOADER_VERSION:
        raise CatalogError(
            f"catalog requires loader version >= {min_loader}; "
            f"this loader is version {LOADER_VERSION} — update the plugin"
        )
    models = doc["models"]
    if not isinstance(models, list) or not models:
        raise CatalogError("models must be a non-empty list")

    seen = {}
    for entry in models:
        if not isinstance(entry, dict):
            raise CatalogError("every model entry must be an object")
        for field in _ENTRY_REQUIRED_FIELDS:
            if field not in entry:
                raise CatalogError(
                    f"model entry {entry.get('id', '<no id>')!r} missing "
                    f"required field: {field}"
                )
        status = entry["status"]
        if status not in _VALID_STATUSES:
            raise CatalogError(
                f"model {entry['id']!r} has invalid status {status!r}"
            )
        if status == "retired" and not entry.get("replacement"):
            raise CatalogError(
                f"retired model {entry['id']!r} must name a replacement"
            )
        for name in [entry["id"], *entry.get("aliases", [])]:
            if name in seen:
                raise CatalogError(
                    f"duplicate model id/alias {name!r} "
                    f"(in {entry['id']!r} and {seen[name]!r})"
                )
            seen[name] = entry["id"]

    # Replacements and role defaults must resolve to real ids/aliases.
    for entry in models:
        replacement = entry.get("replacement")
        if replacement and replacement not in seen:
            raise CatalogError(
                f"model {entry['id']!r} names unknown replacement "
                f"{replacement!r}"
            )
    for role, value in (doc.get("role_defaults") or {}).items():
        ids = [value] if isinstance(value, str) else list(value)
        for model_id in ids:
            if model_id not in seen:
                raise CatalogError(
                    f"role_defaults[{role!r}] names unknown model {model_id!r}"
                )


def _read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _find_shipped_catalog(shipped_path=None):
    """Locate the shipped baseline catalog.

    Search order: explicit arg -> JACK_TAR_MODEL_CATALOG env var -> file
    next to this module (vendored plugin layout) -> repo-level
    model-catalog/ directory walking up from this module (dev layout).
    """
    if shipped_path:
        return Path(shipped_path)
    env_path = os.environ.get(CATALOG_PATH_ENV)
    if env_path:
        return Path(env_path)
    module_dir = Path(__file__).resolve().parent
    candidate = module_dir / CATALOG_FILENAME
    if candidate.exists():
        return candidate
    for ancestor in module_dir.parents[:3]:
        candidate = ancestor / "model-catalog" / CATALOG_FILENAME
        if candidate.exists():
            return candidate
    raise CatalogError(
        f"shipped {CATALOG_FILENAME} not found next to {module_dir} "
        f"or in an ancestor model-catalog/ directory"
    )


def _load_cached_remote(cache_path=None):
    """Return (doc, path) for a valid cached remote catalog, else None.

    A missing cache is normal (install has never refreshed). An invalid
    or loader-incompatible cache logs a warning and is ignored — the
    shipped baseline always keeps the pipeline running.
    """
    path = Path(
        cache_path
        or os.environ.get(CATALOG_CACHE_ENV)
        or _DEFAULT_CACHE_PATH
    )
    if not path.exists():
        return None
    try:
        doc = _read_json(path)
        validate_catalog(doc)
        return doc, path
    except (OSError, json.JSONDecodeError, CatalogError) as exc:
        logger.warning(
            "ignoring invalid cached model catalog at %s: %s "
            "(falling back to shipped baseline)", path, exc,
        )
        return None


def _apply_local_overrides(doc, local_config_path):
    """Merge local-config.json's ``model_catalog`` key into the catalog.

    ``models`` entries merge per-model by id (shallow field update; unknown
    ids append as new entries). ``role_defaults`` merge per-key. The merged
    document is re-validated so a broken override fails loudly — local
    overrides are operator-authored and should not degrade silently.
    """
    path = Path(local_config_path) if local_config_path else Path("local-config.json")
    if not path.exists():
        return doc, False
    try:
        local = _read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("ignoring unreadable local-config.json: %s", exc)
        return doc, False
    overrides = local.get("model_catalog")
    if not isinstance(overrides, dict):
        return doc, False

    merged = copy.deepcopy(doc)
    by_id = {entry["id"]: entry for entry in merged["models"]}
    for patch in overrides.get("models", []):
        target = by_id.get(patch.get("id"))
        if target is not None:
            target.update(copy.deepcopy(patch))
        else:
            merged["models"].append(copy.deepcopy(patch))
    if "role_defaults" in overrides:
        merged.setdefault("role_defaults", {}).update(overrides["role_defaults"])
    validate_catalog(merged)
    return merged, True


class ModelCatalog:
    """Immutable view over a validated catalog document."""

    def __init__(self, doc, source="shipped"):
        self._doc = doc
        self.source = source
        self._by_name = {}
        for entry in doc["models"]:
            self._by_name[entry["id"]] = entry
            for alias in entry.get("aliases", []):
                self._by_name[alias] = entry

    @property
    def version(self):
        return self._doc["catalog_version"]

    @property
    def updated(self):
        return self._doc["updated"]

    def ids(self):
        return [entry["id"] for entry in self._doc["models"]]

    def get(self, id_or_alias, follow_replacement=True):
        """Return a copy of the entry for a model id or alias.

        Retired entries resolve to their replacement when
        ``follow_replacement`` (the substitution is logged and recorded in
        the returned dict's ``resolved_from``). Deprecated entries return
        themselves with a warning. Unknown names raise UnknownModelError.
        """
        entry = self._by_name.get(id_or_alias)
        if entry is None:
            raise UnknownModelError(
                f"model {id_or_alias!r} not in catalog "
                f"(version {self.version}); known ids: {self.ids()}"
            )
        resolved_from = None
        if id_or_alias != entry["id"]:
            resolved_from = id_or_alias
        hops = 0
        while follow_replacement and entry["status"] == "retired":
            replacement = entry["replacement"]
            logger.info(
                "model %s is retired — substituting %s (catalog %s)",
                entry["id"], replacement, self.version,
            )
            resolved_from = resolved_from or entry["id"]
            entry = self._by_name[replacement]
            hops += 1
            if hops > len(self._doc["models"]):
                raise CatalogError(
                    f"replacement cycle detected at {entry['id']!r}"
                )
        if entry["status"] == "deprecated":
            logger.warning(
                "model %s is deprecated%s", entry["id"],
                f" — prefer {entry['replacement']}" if entry.get("replacement") else "",
            )
        result = copy.deepcopy(entry)
        if resolved_from:
            result["resolved_from"] = resolved_from
        return result

    def entries(self, role=None, provider=None, status="active"):
        """Return copies of entries filtered by role/provider/status.

        ``status=None`` disables the status filter.
        """
        out = []
        for entry in self._doc["models"]:
            if status is not None and entry["status"] != status:
                continue
            if role is not None and role not in entry["roles"]:
                continue
            if provider is not None and entry["provider"] != provider:
                continue
            out.append(copy.deepcopy(entry))
        return out

    def role_default(self, role):
        """Return the raw role_defaults value: a model id or preference list."""
        defaults = self._doc.get("role_defaults") or {}
        if role not in defaults:
            raise UnknownModelError(
                f"no role_default for {role!r}; defined roles: "
                f"{sorted(defaults)}"
            )
        return copy.deepcopy(defaults[role])

    def default_model(self, role):
        """Return the resolved entry for a role's default.

        For preference-list defaults (e.g. local_draft) the first entry
        wins — callers that can probe availability should use
        ``role_default`` and filter the list themselves.
        """
        value = self.role_default(role)
        model_id = value if isinstance(value, str) else value[0]
        return self.get(model_id)

    def resolutions(self, id_or_alias):
        entry = self.get(id_or_alias)
        return list((entry.get("capabilities") or {}).get("resolutions", []))

    def supports(self, id_or_alias, resolution):
        return _normalise_resolution(resolution) in self.resolutions(id_or_alias)

    def has_quirk(self, id_or_alias, quirk):
        return quirk in self.get(id_or_alias).get("quirks", [])

    def cost(self, id_or_alias, resolution=None, backend=None, size=None,
             quality=None, tier=None, megapixels=None):
        """Return the USD cost for one generation with the given parameters.

        Dispatches across the pricing shapes:
          flat                     -> no parameters needed
          per_resolution           -> ``resolution``
          backends                 -> ``resolution`` + ``backend`` (Google
                                      Imagen: 'vertex' when
                                      GOOGLE_APPLICATION_CREDENTIALS is set,
                                      else 'developer' — auto-detected when
                                      backend is None)
          per_size_quality         -> ``size`` + ``quality`` (OpenAI)
          per_tier                 -> ``tier`` (icons)
          tiered_megapixel         -> ``megapixels`` (FAL FLUX 2 Pro)

        The upscale_chain_4k quirk (Recraft Pro) applies the documented
        env override to the upscale component of the 4K chain price.
        """
        entry = self.get(id_or_alias)
        pricing = entry.get("pricing")
        if pricing is None:
            raise PricingError(
                f"model {entry['id']!r} has no pricing data in the catalog"
            )

        if "flat" in pricing and resolution is None and size is None \
                and tier is None and megapixels is None:
            return pricing["flat"]

        if "per_resolution" in pricing and resolution is not None:
            res = _normalise_resolution(resolution)
            table = pricing["per_resolution"]
            if res not in table:
                raise PricingError(
                    f"model {entry['id']!r} has no {res} price; "
                    f"priced resolutions: {sorted(table)}"
                )
            if res == "4K" and "upscale_chain_4k" in entry.get("quirks", []):
                return self._chained_4k_cost(entry, table, pricing)
            return table[res]

        if "backends" in pricing and resolution is not None:
            res = _normalise_resolution(resolution)
            if backend is None:
                backend = (
                    "vertex"
                    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
                    else "developer"
                )
            table = pricing["backends"].get(backend)
            if table is None:
                raise PricingError(
                    f"model {entry['id']!r} has no backend {backend!r}; "
                    f"priced backends: {sorted(pricing['backends'])}"
                )
            if res not in table:
                raise PricingError(
                    f"model {entry['id']!r} has no {res} price on "
                    f"backend {backend!r}; priced: {sorted(table)}"
                )
            return table[res]

        if "per_size_quality" in pricing and size is not None:
            key = f"{size}|{quality}"
            table = pricing["per_size_quality"]
            if key not in table:
                raise PricingError(
                    f"model {entry['id']!r} has no price for "
                    f"size/quality {key!r}; priced: {sorted(table)}"
                )
            return table[key]

        if "per_tier" in pricing and tier is not None:
            table = pricing["per_tier"]
            if tier not in table:
                raise PricingError(
                    f"model {entry['id']!r} has no tier {tier!r}; "
                    f"priced tiers: {sorted(table)}"
                )
            return table[tier]

        if "tiered_megapixel" in pricing and megapixels is not None:
            rates = pricing["tiered_megapixel"]
            extra = max(0.0, float(megapixels) - 1.0)
            return rates["first_mp"] + extra * rates["per_extra_mp"]

        if "flat" in pricing:
            return pricing["flat"]

        raise PricingError(
            f"model {entry['id']!r}: no pricing shape matches the given "
            f"parameters (resolution={resolution!r}, size={size!r}, "
            f"quality={quality!r}, tier={tier!r}, megapixels={megapixels!r}); "
            f"available shapes: {sorted(set(pricing) - {'currency', 'verified', 'estimate', 'notes', 'env_override'})}"
        )

    @staticmethod
    def _chained_4k_cost(entry, table, pricing):
        """4K = 2K generation + upscale; env override adjusts the upscale part.

        Override is only honoured when it parses to a positive float —
        guards against accidentally pricing a paid API at $0 or negative
        (mirrors the historical RECRAFT_UPSCALE_COST_USD behaviour).
        """
        base = table.get("2K", 0.0)
        upscale = table["4K"] - base
        env_var = (pricing.get("env_override") or {}).get("upscale")
        if env_var:
            raw = os.environ.get(env_var)
            if raw:
                try:
                    value = float(raw)
                    if value > 0:
                        upscale = value
                except ValueError:
                    pass
        return base + upscale


def load_catalog(shipped_path=None, cache_path=None, local_config_path=None):
    """Load the catalog with full precedence merging. Returns ModelCatalog.

    Precedence (low to high): shipped baseline -> cached remote ->
    local-config.json ``model_catalog`` overrides. See module docstring.
    """
    source = "shipped"
    cached = _load_cached_remote(cache_path)
    if cached is not None:
        doc, path = cached
        source = f"cached:{path}"
    else:
        path = _find_shipped_catalog(shipped_path)
        try:
            doc = _read_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            raise CatalogError(f"cannot read shipped catalog at {path}: {exc}")
        validate_catalog(doc)

    doc, overridden = _apply_local_overrides(doc, local_config_path)
    if overridden:
        source += "+local"
    catalog = ModelCatalog(doc, source=source)
    logger.debug(
        "model catalog loaded: version=%s source=%s models=%d",
        catalog.version, source, len(doc["models"]),
    )
    return catalog


_catalog_singleton = None


def get_catalog(reload=False):
    """Process-wide cached catalog. ``reload=True`` re-reads from disk."""
    global _catalog_singleton
    if _catalog_singleton is None or reload:
        _catalog_singleton = load_catalog()
    return _catalog_singleton
