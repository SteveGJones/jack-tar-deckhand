"""Edit-tier dispatch helpers — issue #143 PR D.

The $0 local mflux edit tier (wrapper + catalog fields shipped in PR C,
issue #143) slots into two critique loops: ``iterate-slide`` (for
``academic_figure`` slides) and the ``creative_vision`` cascade. This
module is the **testable boundary** for the edit-vs-regenerate decision
and the manifest provenance it produces — the subprocess invocation of
``jack-tar-mlx``'s ``edit_image.py`` happens from SKILL.md, everything
around it is pure Python and covered here.

See ``docs/superpowers/plans/2026-07-23-edit-tier.md`` §4.2 for the
design this module implements.

Design load-bearing calls (all FIRM, smokes executed 2026-07-23):

- **D8 — base provenance.** ``edit_channel_available`` does NOT gate on
  which backend produced the base image (mflux / ollama / cloud are ALL
  allowed — S5a/S5b both PASSed). The provenance class is still READ
  (from the manifest entry's ``backend`` field) and recorded on the
  ``edit_chain`` entry for audit by ``record_edit``, but it is not a
  gating condition.
- **D9 — text carve-out (HARD-EXCLUDE).** ``classify_edit_locality``
  applies the text carve-out FIRST: feedback that names in-image TEXT
  never routes to edit, regardless of spatial locality (S1 FAIL — the
  simplest word-for-word edit garbled "NOTICE" -> "NOBTICE"). Returns
  ``"text_excluded"``, not a warned-but-offered path.
- **F-06 — stale-cache shadowing.** ``model_catalog.py`` replaces the
  shipped baseline WHOLESALE with any valid cached remote catalog, no
  version comparison. An operator whose ``~/.jack-tar/model-catalog.json``
  predates the ``image_edit`` role silently loses the edit channel with
  no error. ``edit_channel_unavailable_reason`` distinguishes this
  condition from a plain "no local edit backend" and surfaces the
  remediation (re-run ``refresh-models`` or delete the stale cache).
- **F-08 — seed always resolved.** ``build_edit_args`` always populates
  ``seed`` (explicit or generated) — an unseeded edit is unreplayable
  (S3: zero trace in stdout/stderr/sidecar).
"""
from __future__ import annotations

import logging
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

try:
    from .model_catalog import UnknownModelError as _UnknownModelError
    from .model_catalog import get_catalog as _get_model_catalog
except ImportError:  # pragma: no cover - direct-script execution path
    from src.model_catalog import UnknownModelError as _UnknownModelError
    from src.model_catalog import get_catalog as _get_model_catalog

try:
    from .paperbanana_dispatch import (
        LocalBackend,
        _extra_dir_has_weights,
        _hf_snapshot_complete,
        _physical_ram_gb,
        _resolve_hf_hub_dir,
    )
except ImportError:  # pragma: no cover - direct-script execution path
    from src.paperbanana_dispatch import (
        LocalBackend,
        _extra_dir_has_weights,
        _hf_snapshot_complete,
        _physical_ram_gb,
        _resolve_hf_hub_dir,
    )

logger = logging.getLogger(__name__)


# --- F-06 remediation messages ---------------------------------------------

_STALE_CATALOG_NO_EDIT_ROLES_REASON = (
    "No image_edit-capable model found in the currently loaded model "
    "catalog. model_catalog.py replaces the shipped baseline WHOLESALE "
    "with any valid cached remote catalog, with no version comparison — "
    "if mlx edit-capable weights ARE installed, this usually means the "
    "operator's ~/.jack-tar/model-catalog.json cache predates the "
    "image_edit role (catalog < 1.2.0). Remediation: re-run the catalog "
    "refresh (/jack-tar-deckhand:refresh-models) or delete the stale "
    "~/.jack-tar/model-catalog.json, then retry."
)

_NO_EDIT_BACKEND_REASON = (
    "No local mlx edit backend detected — check mflux is installed "
    "(`uv tool install --upgrade mflux`) and edit-capable weights are "
    "cached for at least one of mlx/flux2-klein-4b or mlx/qwen-image "
    "(`/jack-tar-mlx:verify`)."
)


def detect_mlx_edit_backend(
    *,
    preferred_model: str | None = None,
    hf_home: str | None = None,
    extra_model_dirs: tuple = (),
    timeout_seconds: float = 2.0,
) -> "LocalBackend | None":
    """Probe for a runnable local MLX (mflux) EDIT backend.

    Like ``paperbanana_dispatch.detect_mlx_backend`` but filters to
    ``image_edit``-capable entries specifically (design D1 rationale:
    a dedicated detector keeps the academic_figure dispatch's most-tested
    function untouched rather than widening it with a ``require_role``
    param — see design doc §4.2 / open question 4).

    A candidate entry must:

    (a) carry ``"image_edit"`` in ``roles``;
    (b) have its ``sdk.edit_entrypoint`` on PATH (``shutil.which``);
    (c) pass the EDIT ram gate — ``capabilities.edit_min_ram_gb`` (a
        SEPARATE, sometimes higher, field than the generate
        ``min_ram_gb`` — qwen-edit is a 64GB tier vs qwen-generate's 32GB,
        upstream mflux #420);
    (d) have a complete cached weights snapshot for its ``sdk.hf_repo``
        / ``sdk.hf_repo_fallback`` (edit reuses the SAME cached weights
        as generate — no separate edit weight download, PoC fact).

    ``preferred_model`` (a catalog id) bypasses the RAM gate with a
    logged warning, mirroring ``detect_mlx_backend``'s review-m11 ruling
    — the operator who names a model owns the consequence.

    Any failure on any path degrades to None — a broken/partial MLX
    install can never block the pipeline (and the caller falls back to
    the standard re-roll paths).
    """
    import shutil

    try:
        hub_dir = _resolve_hf_hub_dir(hf_home)
        ram_gb = _physical_ram_gb()
        catalog = _get_model_catalog()

        def _weights_present(sdk: Mapping) -> bool:
            for repo_key in ("hf_repo", "hf_repo_fallback"):
                repo = sdk.get(repo_key)
                if repo and _hf_snapshot_complete(repo, hub_dir):
                    return True
            return _extra_dir_has_weights(sdk, extra_model_dirs)

        def _candidate_available(entry: Mapping) -> bool:
            if "image_edit" not in (entry.get("roles") or []):
                return False
            sdk = entry.get("sdk") or {}
            edit_entrypoint = sdk.get("edit_entrypoint")
            if not edit_entrypoint or shutil.which(edit_entrypoint) is None:
                return False
            return _weights_present(sdk)

        if preferred_model:
            preferred_entry = None
            try:
                candidate = catalog.get(preferred_model, follow_replacement=False)
            except _UnknownModelError:
                candidate = None
            if candidate is not None and candidate.get("provider") == "mlx":
                preferred_entry = candidate

            if preferred_entry is not None and _candidate_available(preferred_entry):
                capabilities = preferred_entry.get("capabilities") or {}
                min_ram = capabilities.get("edit_min_ram_gb")
                if min_ram is not None and ram_gb is not None and ram_gb < min_ram:
                    logger.warning(
                        "mlx preferred_model %s declares edit_min_ram_gb=%s but "
                        "detected physical RAM is %.1fGB — operator override "
                        "bypasses the edit RAM gate (issue #143, mirrors #124 "
                        "review m11)",
                        preferred_entry["id"], min_ram, ram_gb,
                    )
                return LocalBackend(provider="mlx", model=preferred_entry["id"])

        for entry in catalog.entries(role="image_edit", provider="mlx", status="active"):
            capabilities = entry.get("capabilities") or {}
            min_ram = capabilities.get("edit_min_ram_gb")
            if min_ram is not None and ram_gb is not None and ram_gb < min_ram:
                continue
            if _candidate_available(entry):
                return LocalBackend(provider="mlx", model=entry["id"])

        return None
    except Exception:  # noqa: BLE001 - any MLX probe failure must degrade to None
        logger.debug("detect_mlx_edit_backend failed; degrading to None", exc_info=True)
        return None


def edit_channel_unavailable_reason(backend: "LocalBackend | None", catalog=None) -> str:
    """Human-readable reason the edit channel is unavailable.

    Distinguishes the F-06 stale-cache shadowing failure mode (the
    loaded catalog carries ZERO ``image_edit``-role entries — almost
    certainly a stale ``~/.jack-tar/model-catalog.json`` predating the
    edit fields) from the plain "no local edit backend detected" case.

    Returns the empty string when ``backend`` is not None (nothing to
    explain).
    """
    if backend is not None:
        return ""
    cat = catalog if catalog is not None else _get_model_catalog()
    if not cat.entries(role="image_edit", status="active"):
        return _STALE_CATALOG_NO_EDIT_ROLES_REASON
    return _NO_EDIT_BACKEND_REASON


def edit_channel_available(manifest_entry: Mapping | None, backend: "LocalBackend | None") -> bool:
    """True when a base raster exists on disk for this slide AND
    ``backend`` is an mlx edit backend.

    Base-provenance taxonomy (D8/F-04) — RESOLVED FIRM by smokes §8.1:
    ALL THREE classes are allowed —

      - mflux-produced   (``"mlx_local"``/``"mlx_edit"``)       [FIRM]
      - ollama-produced  (``"ollama_local"``)                   [FIRM — S5a
                          PASS, flawless, no cross-backend artifacts; the
                          dominant real academic_figure base class]
      - cloud-produced   (``"cloud_fallback"``/paperbanana/cloud
                          tier names)                           [FIRM — S5b
                          PASS, 6/6 labels preserved verbatim, cloud
                          crispness maintained; single-scenario evidence,
                          broader evidence accrues in dogfood]

    The provenance class is still READ (from the entry's ``backend``
    field) and recorded on the edit_chain entry for audit (see
    ``record_edit``), but it no longer gates availability.
    """
    if backend is None or not isinstance(backend, LocalBackend):
        return False
    if not manifest_entry:
        return False
    file_path = manifest_entry.get("file_path")
    if not file_path:
        return False
    return Path(file_path).is_file()


# --- classify_edit_locality (D4/D9) -----------------------------------------
#
# Pure-Python heuristic — keyword/imperative-shape based. The text
# carve-out (D9, S1 FAIL) is applied FIRST and is a HARD EXCLUSION: any
# text-targeting cue routes to "text_excluded" regardless of any
# region/colour cue also present. Deliberately over-inclusive on the
# text side — a false-positive text exclusion just costs a re-roll
# instead of a $0 edit; a false-negative risks shipping "NOBTICE".

_TEXT_CUES: tuple[str, ...] = (
    "text", "label", "labels", "caption", "captions", "title", "titles",
    "spelling", "spelled", "misspell", "misspelled", "typo", "typos",
    "wording", "letter", "letters", "word", "words", "read", "reads",
    "font", "legend",
)

_GLOBAL_CUES: tuple[str, ...] = (
    "redo", "instead", "wrong idea", "start over", "start from scratch",
    "completely different", "different composition", "recompose",
    "restyle the whole", "restyle the entire", "whole scene",
    "entire image", "whole image", "how many", "layout", "rethink",
    "different concept", "wrong number of", "add another", "one more",
    "remove one of the", "different scene", "subject count",
)

_LOCAL_CUES: tuple[str, ...] = (
    "sky", "background", "arrow", "colour", "color", "darken", "lighten",
    "brighten", "shadow", "lighting", "highlight", "seagull",
    "left corner", "right corner", "top corner", "bottom corner",
    "single", "ship", "hue", "tint", "shade", "reflection",
    "remove the", "make the", "recolour", "recolor",
)


def _contains_any(text: str, cues: tuple[str, ...]) -> list[str]:
    hits = []
    for cue in cues:
        if re.search(r"\b" + re.escape(cue) + r"\b", text):
            hits.append(cue)
    return hits


def classify_edit_locality(feedback: str, critic_verdict: Mapping | None = None) -> dict:
    """Classify operator feedback (and optionally a Director's Critic
    verdict) as ``'local'`` | ``'global'`` | ``'ambiguous'`` |
    ``'text_excluded'``.

    The text carve-out (D9, S1 FAIL) is applied FIRST and is a hard
    exclusion: text-targeting feedback returns ``'text_excluded'`` and
    the edit channel is never proposed for it — not even offered with a
    warning.

    Returns ``{'locality': ..., 'confidence': float, 'cues': [...]}``.
    """
    parts = [feedback or ""]
    if critic_verdict:
        recommended = critic_verdict.get("recommended_action")
        if recommended:
            parts.append(str(recommended))
        for issue in critic_verdict.get("issues") or []:
            detail = issue.get("detail") if isinstance(issue, Mapping) else None
            if detail:
                parts.append(str(detail))
    text = " ".join(parts).lower()

    text_hits = _contains_any(text, _TEXT_CUES)
    if text_hits:
        return {"locality": "text_excluded", "confidence": 1.0, "cues": text_hits}

    global_hits = _contains_any(text, _GLOBAL_CUES)
    local_hits = _contains_any(text, _LOCAL_CUES)

    if global_hits and not local_hits:
        return {
            "locality": "global",
            "confidence": min(1.0, 0.5 + 0.15 * len(global_hits)),
            "cues": global_hits,
        }
    if local_hits and not global_hits:
        return {
            "locality": "local",
            "confidence": min(1.0, 0.5 + 0.15 * len(local_hits)),
            "cues": local_hits,
        }
    if local_hits and global_hits:
        if len(local_hits) > len(global_hits):
            return {"locality": "local", "confidence": 0.4, "cues": local_hits + global_hits}
        if len(global_hits) > len(local_hits):
            return {"locality": "global", "confidence": 0.4, "cues": local_hits + global_hits}
        return {"locality": "ambiguous", "confidence": 0.3, "cues": local_hits + global_hits}

    return {"locality": "ambiguous", "confidence": 0.2, "cues": []}


def build_edit_args(
    base_image_path: str,
    instruction: str,
    backend: "LocalBackend",
    catalog=None,
    *,
    reference_paths: tuple = (),
    seed: int | None = None,
    guidance: float | None = None,
) -> dict:
    """Build the argument dict for an ``edit_image.py`` dispatch.

    NO width/height keys — the wrapper exposes no dims flags (S7 ruling);
    output always inherits the base image's dimensions.

    ``seed`` is ALWAYS resolved (F-08): explicit when given, otherwise
    generated here — an unseeded edit leaves zero trace of itself (S3),
    so the caller must always have a concrete seed to persist via
    ``record_edit``.
    """
    cat = catalog if catalog is not None else _get_model_catalog()
    entry = cat.get(backend.model)
    capabilities = entry.get("capabilities") or {}
    args: dict = {
        "model": backend.model,
        "image_paths": [base_image_path, *reference_paths],
        "prompt": instruction,
        "steps": capabilities.get("edit_render_steps"),
        "seed": seed if seed is not None else random.randrange(2**32),
    }
    if guidance is not None:
        args["guidance"] = guidance
    return args


def record_edit(
    prior_entry: Mapping,
    new_file_path: str,
    new_content_hash: str,
    *,
    edit_instruction: str,
    edit_args: Mapping,
    parent_content_hash: str,
) -> dict:
    """Return a NEW manifest entry with edit provenance appended (§4.3).

    ``edit_chain`` is seeded on first edit (parent = the pre-edit
    ``content_hash``/``file_path``) and appended on subsequent edits.
    Top-level ``file_path``/``content_hash`` are always overwritten with
    the newest. A regeneration (not an edit) does NOT go through this
    helper — it starts a fresh lineage via the ordinary manifest-write
    path.

    The parent entry's OWN ``backend`` (its provenance class — e.g.
    ``"ollama_local"``, ``"mlx_local"``, ``"cloud_fallback"``) is
    recorded on the new chain entry as ``parent_backend`` for audit
    (D8/F-04 — provenance is read, not gated).
    """
    updated = dict(prior_entry)
    edit_chain = list(updated.get("edit_chain") or [])
    parent_file_path = updated.get("file_path")
    parent_backend = updated.get("backend")

    chain_entry = {
        "iteration": len(edit_chain) + 1,
        "parent_content_hash": parent_content_hash,
        "parent_file_path": parent_file_path,
        "parent_backend": parent_backend,
        "instruction": edit_instruction,
        "edit_args": dict(edit_args),
        "backend": "mlx_edit",
        "cost_usd": 0.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    edit_chain.append(chain_entry)

    updated["edit_chain"] = edit_chain
    updated["file_path"] = new_file_path
    updated["content_hash"] = new_content_hash
    updated["backend"] = "mlx_edit"
    updated["model_used"] = edit_args.get("model")
    updated["cost_usd"] = 0.0
    return updated
