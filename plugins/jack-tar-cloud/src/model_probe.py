"""Live provider discovery — verify catalog entries against provider APIs
(EPIC #125, issue #129).

Where a provider exposes a list-models API, probe it on request and classify
every catalog entry:

- ``verified``          — the model id exists upstream right now
- ``suspect_retired``   — catalog says active/deprecated but the provider no
                          longer lists it (the gemini-2.0-flash failure mode,
                          issue #123, caught BEFORE a 404 in a deck build)
- ``confirmed_retired`` — catalog already says retired and upstream agrees
- ``unprobed``          — the provider has no list API (FAL, Recraft) or no
                          credentials are configured; catalog-driven only

Upstream models that no catalog entry covers are reported as
``new_candidates``. Live discovery attests EXISTENCE, never price — a
candidate is not routable until a catalog entry prices it (the budget
tracker cannot cost an uncataloged model), so candidates require explicit
operator opt-in via a local-config override or a catalog update.

Probes degrade gracefully: a provider with no API key is skipped with a
reason, never an exception.
"""

from __future__ import annotations

import logging
import os

try:
    from .model_catalog import get_catalog
except ImportError:  # pragma: no cover - direct-script execution path
    from model_catalog import get_catalog

logger = logging.getLogger(__name__)

#: Providers with no list-models API — their entries are always unprobed.
UNPROBEABLE_PROVIDERS = frozenset({"fal", "recraft"})


def probe_google_models(timeout=30):
    """List model ids the Google API serves right now.

    Returns {'status': 'ok', 'models': set[str]} or
    {'status': 'skipped', 'reason': str}.
    """
    if not (os.environ.get("GOOGLE_API_KEY")
            or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")):
        return {"status": "skipped", "reason": "no Google credentials configured"}
    try:
        from google import genai
    except ImportError:
        return {"status": "skipped", "reason": "google-genai SDK not installed"}
    try:
        client_kwargs = {}
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            client_kwargs["api_key"] = api_key
        client = genai.Client(**client_kwargs)
        names = set()
        for model in client.models.list():
            name = getattr(model, "name", "") or ""
            # API returns "models/gemini-..." — strip the resource prefix.
            names.add(name.removeprefix("models/"))
        return {"status": "ok", "models": names}
    except Exception as exc:  # network/auth errors must not break verify
        return {"status": "skipped", "reason": f"probe failed: {exc}"}


def probe_openai_models(timeout=30):
    """List model ids the OpenAI API serves right now."""
    if not os.environ.get("OPENAI_API_KEY"):
        return {"status": "skipped", "reason": "OPENAI_API_KEY not set"}
    try:
        from openai import OpenAI
    except ImportError:
        return {"status": "skipped", "reason": "openai SDK not installed"}
    try:
        client = OpenAI()
        return {
            "status": "ok",
            "models": {m.id for m in client.models.list()},
        }
    except Exception as exc:
        return {"status": "skipped", "reason": f"probe failed: {exc}"}


def probe_ollama_models(endpoint="http://localhost:11434"):
    """List locally installed Ollama model tags."""
    import requests

    try:
        response = requests.get(f"{endpoint}/api/tags", timeout=5)
        data = response.json()
        return {
            "status": "ok",
            "models": {m["name"] for m in data.get("models", [])},
        }
    except Exception as exc:
        return {"status": "skipped", "reason": f"Ollama not reachable: {exc}"}


def _entry_upstream_match(entry, upstream):
    """True when any name of this entry exists upstream.

    Ollama catalog ids are tag-prefixes (``x/flux2-klein`` matches the
    installed ``x/flux2-klein:9b``); other providers match exactly.
    """
    names = [entry["id"], *entry.get("aliases", [])]
    if entry["provider"] == "ollama":
        return any(
            tag == name or tag.startswith(f"{name}:")
            for name in names
            for tag in upstream
        )
    return any(name in upstream for name in names)


def classify_entries(catalog, probes):
    """Classify every catalog entry against the probe results.

    Args:
        catalog: a ModelCatalog.
        probes: {provider: {'status': 'ok'|'skipped', 'models': set, ...}}

    Returns:
        list of {model, provider, status, verdict[, note]}.
    """
    results = []
    for entry in catalog.entries(status=None):
        provider = entry["provider"]
        probe = probes.get(provider)
        if provider in UNPROBEABLE_PROVIDERS:
            verdict = {"verdict": "unprobed",
                       "note": "provider has no list-models API; catalog-driven"}
        elif probe is None or probe.get("status") != "ok":
            reason = (probe or {}).get("reason", "provider not probed")
            verdict = {"verdict": "unprobed", "note": reason}
        elif _entry_upstream_match(entry, probe["models"]):
            if entry["status"] == "retired":
                verdict = {"verdict": "verified",
                           "note": "catalog says retired but upstream still "
                                   "lists it — consider un-retiring"}
            else:
                verdict = {"verdict": "verified"}
        else:
            if entry["status"] == "retired":
                verdict = {"verdict": "confirmed_retired"}
            else:
                verdict = {"verdict": "suspect_retired",
                           "note": "not listed upstream — update the catalog "
                                   "(or run refresh-models) before relying "
                                   "on this model"}
        results.append({
            "model": entry["id"],
            "provider": provider,
            "status": entry["status"],
            **verdict,
        })
    return results


# Substring filters for candidate relevance per provider — the list APIs
# return every model family; only image/vision-relevant ones are useful
# candidates for this pipeline.
_CANDIDATE_FILTERS = {
    "google": ("image", "imagen", "flash", "pro"),
    "openai": ("image", "dall-e"),
    "ollama": ("x/",),
}


def find_new_candidates(catalog, probes):
    """Upstream models no catalog entry covers, filtered to relevant kinds.

    Candidates are NOT routable: existence is provable, price is not. They
    surface for the operator to add to the catalog (or a local-config
    override) before use.
    """
    known = set()
    for entry in catalog.entries(status=None):
        known.add(entry["id"])
        known.update(entry.get("aliases", []))

    candidates = {}
    for provider, probe in probes.items():
        if probe.get("status") != "ok":
            continue
        filters = _CANDIDATE_FILTERS.get(provider, ())
        found = []
        for name in sorted(probe["models"]):
            if any(name == k or name.startswith(f"{k}:") for k in known):
                continue
            if filters and not any(f in name for f in filters):
                continue
            found.append(name)
        if found:
            candidates[provider] = found
    return candidates


def probe_report(catalog=None, probes=None):
    """Full live-discovery report for /verify and refresh-models.

    Args:
        catalog: ModelCatalog (defaults to the effective loaded catalog).
        probes: pre-computed probe results (tests / callers that already
            probed); defaults to probing google + openai + ollama live.

    Returns:
        {catalog_version, probes: {provider: status/reason},
         entries: [classification...], new_candidates: {provider: [id...]}}
    """
    catalog = catalog or get_catalog()
    if probes is None:
        probes = {
            "google": probe_google_models(),
            "openai": probe_openai_models(),
            "ollama": probe_ollama_models(),
        }
    return {
        "catalog_version": catalog.version,
        "probes": {
            provider: {k: v for k, v in probe.items() if k != "models"}
            for provider, probe in probes.items()
        },
        "entries": classify_entries(catalog, probes),
        "new_candidates": find_new_candidates(catalog, probes),
    }
