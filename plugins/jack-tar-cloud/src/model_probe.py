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
- ``not_installed``     — LOCAL providers only (Ollama, MLX): the model is
                          simply not pulled/downloaded on this machine yet.
                          Never means "retired" — local absence says nothing
                          about upstream existence (issue #124 review M3).

MLX probing scans the Hugging Face cache for complete weight snapshots;
there is no server API (mflux is a CLI, not a daemon) but "installed" is
directly observable on disk, so mlx is probeable like ollama, not
unprobeable like FAL/Recraft.

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
import shutil
from pathlib import Path

try:
    from .model_catalog import get_catalog
except ImportError:  # pragma: no cover - direct-script execution path
    from model_catalog import get_catalog

logger = logging.getLogger(__name__)

#: Providers with no list-models API — their entries are always unprobed.
UNPROBEABLE_PROVIDERS = frozenset({"fal", "recraft"})

#: Providers whose probe reflects LOCAL installation state, not upstream
#: existence — absence means "not installed here", never "retired" (issue
#: #124 review M3 ruling).
LOCAL_PROVIDERS = frozenset({"ollama", "mlx"})


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


def _resolve_hf_hub_dir(hf_home=None):
    """HF hub cache dir per huggingface_hub precedence (issue #124 review m7).

    ``hf_home`` (root; hub is ``<hf_home>/hub``) > ``$HF_HUB_CACHE`` (IS the
    hub dir directly) > ``$HF_HOME/hub`` > ``~/.cache/huggingface/hub``.

    Private copy — see design doc §10 OQ-C on the accepted duplication
    trade-off (the same rule also lives in ``paperbanana_dispatch.py`` and
    the mlx wrapper's ``--check-weights`` mode).
    """
    if hf_home is not None:
        return Path(hf_home) / "hub"
    env_cache = os.environ.get("HF_HUB_CACHE")
    if env_cache:
        return Path(env_cache)
    env_home = os.environ.get("HF_HOME")
    if env_home:
        return Path(env_home) / "hub"
    return Path.home() / ".cache" / "huggingface" / "hub"


def _hf_snapshot_complete(repo_id, hub_dir):
    """True when ``repo_id`` has a complete HF-cache snapshot under hub_dir.

    Private copy of the same completeness predicate used by
    ``paperbanana_dispatch.detect_mlx_backend`` (design doc §2.2 / §10
    OQ-C) — revision resolved via ``refs/main`` when present, else the
    newest-by-mtime ``snapshots/`` dir; every symlink under the resolved
    revision must resolve to an existing path with no ``.incomplete``
    sibling blob. Any doubt (missing dirs, OSError) returns False so
    detection under-reports rather than risking a download.
    """
    try:
        repo_dir = hub_dir / ("models--" + repo_id.replace("/", "--"))
        if not repo_dir.is_dir():
            return False
        snapshots_dir = repo_dir / "snapshots"
        if not snapshots_dir.is_dir():
            return False

        revision_dir = None
        refs_main = repo_dir / "refs" / "main"
        if refs_main.is_file():
            revision = refs_main.read_text().strip()
            candidate = snapshots_dir / revision
            if candidate.is_dir():
                revision_dir = candidate
        if revision_dir is None:
            candidates = [d for d in snapshots_dir.iterdir() if d.is_dir()]
            if not candidates:
                return False
            revision_dir = max(candidates, key=lambda d: d.stat().st_mtime)

        entries = list(revision_dir.iterdir())
        if not entries:
            return False

        for link in revision_dir.rglob("*"):
            if not link.is_symlink():
                continue
            if not link.exists():
                return False
            target = link.resolve()
            if (target.parent / f"{target.name}.incomplete").exists():
                return False
        return True
    except OSError:
        return False


def probe_mlx_models(hf_home=None, extra_model_dirs=()):
    """List HF-cached mlx/mflux image-weight repos with COMPLETE snapshots.

    Server-less analogue of ``probe_ollama_models``: "installed" == weights
    fully cached (mflux has no list API). Returns
    ``{'status': 'ok', 'models': set[str]}`` of HF repo ids (e.g.
    ``'Runpod/FLUX.2-klein-4B-mflux-4bit'``) with a complete snapshot under
    the hub dir resolved per huggingface_hub precedence (``hf_home`` arg ->
    ``$HF_HUB_CACHE`` -> ``$HF_HOME/hub`` -> ``~/.cache/huggingface/hub``),
    plus any non-empty ``mflux-save`` dir basenames from
    ``extra_model_dirs``; or ``{'status': 'skipped', 'reason': ...}`` when
    no catalogued mflux entry point is on PATH (mflux CLI not installed).

    Never raises; scan errors -> skipped with the reason string.
    """
    try:
        catalog = get_catalog()
        entrypoints = {
            (entry.get("sdk") or {}).get("entrypoint")
            for entry in catalog.entries(provider="mlx", status=None)
        }
        entrypoints.discard(None)
    except Exception as exc:  # catalog load must not break verify
        return {"status": "skipped", "reason": f"catalog unavailable: {exc}"}

    if not entrypoints or not any(shutil.which(ep) for ep in entrypoints):
        return {"status": "skipped",
                "reason": "mflux CLI not installed (no catalogued mlx "
                          "entrypoint on PATH)"}

    try:
        hub_dir = _resolve_hf_hub_dir(hf_home)
        models = set()
        if hub_dir.is_dir():
            for child in hub_dir.iterdir():
                if not child.is_dir() or not child.name.startswith("models--"):
                    continue
                repo_id = child.name[len("models--"):].replace("--", "/", 1)
                if _hf_snapshot_complete(repo_id, hub_dir):
                    models.add(repo_id)
        for extra_dir in extra_model_dirs:
            path = Path(extra_dir)
            if path.is_dir() and any(path.iterdir()):
                models.add(path.name)
        return {"status": "ok", "models": models}
    except OSError as exc:
        return {"status": "skipped", "reason": f"scan failed: {exc}"}


def _entry_upstream_match(entry, upstream):
    """True when any name of this entry exists upstream.

    Ollama catalog ids are tag-prefixes (``x/flux2-klein`` matches the
    installed ``x/flux2-klein:9b``); mlx catalog ids are ``mlx/<slug>`` but
    the probe returns HF repo ids, so mlx entries match on
    ``sdk.hf_repo``/``sdk.hf_repo_fallback`` instead; other providers match
    exactly.
    """
    names = [entry["id"], *entry.get("aliases", [])]
    if entry["provider"] == "ollama":
        return any(
            tag == name or tag.startswith(f"{name}:")
            for name in names
            for tag in upstream
        )
    if entry["provider"] == "mlx":
        sdk = entry.get("sdk") or {}
        repos = [r for r in (sdk.get("hf_repo"), sdk.get("hf_repo_fallback")) if r]
        return any(repo in upstream for repo in repos)
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
            elif provider in LOCAL_PROVIDERS:
                if provider == "mlx":
                    sdk = entry.get("sdk") or {}
                    repo = sdk.get("hf_repo") or entry["id"]
                    note = f"weights not cached locally — run: hf download {repo}"
                else:  # ollama
                    note = (f"not installed locally — run: ollama pull "
                            f"{entry['id']}")
                verdict = {"verdict": "not_installed", "note": note}
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
    "mlx": ("-mflux-",),
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
        if entry["provider"] == "mlx":
            sdk = entry.get("sdk") or {}
            for repo in (sdk.get("hf_repo"), sdk.get("hf_repo_fallback")):
                if repo:
                    known.add(repo)

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
            probed); defaults to probing google + openai + ollama + mlx
            live.

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
            "mlx": probe_mlx_models(),
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
