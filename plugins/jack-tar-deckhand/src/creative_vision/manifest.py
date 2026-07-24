"""CreativeVisionManifest persistence module. Issue #105."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone


def create_run_id(slide_number: int) -> str:
    """Return a fresh run_id of shape ``cv-YYYY-MM-DD-HHMMSS-<rand>-slide-N``."""
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    return f"cv-{stamp}-{suffix}-slide-{slide_number}"


def initialise_manifest(slide_number: int, vision_prose: str, budget_usd: float) -> dict:
    """Build a fresh CreativeVisionManifest for a slide that has not yet rendered.

    Stashes ``_initial_budget_usd`` on the manifest so subsequent
    ``append_attempt`` calls (Task 8) can recompute remaining_budget_usd
    from cumulative cost without losing the original budget envelope.
    """
    now = datetime.now(timezone.utc).isoformat()
    manifest = {
        "run_id": create_run_id(slide_number),
        "slide_number": slide_number,
        "strategy": "creative_vision",
        "prose_history": [
            {"version": 1, "timestamp": now, "prose": vision_prose}
        ],
        "attempts": [],
        "final": None,
        "iterate_slide_hooks": {
            "can_revise_prose": True,
            "can_refine_prompt": True,
            "can_escalate_tier": True,
            # Edit tier (issue #143): flips True once an attempt with an
            # on-disk render exists — see append_attempt. Independent of
            # budget/ceiling: an edit is a $0 delta on the last rendered
            # image regardless of which tier produced it.
            "can_edit": False,
            "current_tier": "ollama",
            "next_tier_available": "flash_1k",
            "remaining_budget_usd": budget_usd,
        },
        "_initial_budget_usd": budget_usd,
    }
    return manifest


def _manifest_dir(deck_dir: str, slide_number: int) -> str:
    return os.path.join(deck_dir, "creative-vision", str(slide_number))


def _manifest_path(deck_dir: str, slide_number: int) -> str:
    return os.path.join(_manifest_dir(deck_dir, slide_number), "manifest.json")


def save_manifest(deck_dir: str, manifest: dict) -> None:
    """Persist a manifest under <deck_dir>/creative-vision/<slide_number>/manifest.json.

    Also ensures the sibling runs/ subdirectory exists.
    """
    mdir = _manifest_dir(deck_dir, manifest["slide_number"])
    os.makedirs(mdir, exist_ok=True)
    os.makedirs(os.path.join(mdir, "runs"), exist_ok=True)
    with open(_manifest_path(deck_dir, manifest["slide_number"]), "w") as f:
        json.dump(manifest, f, indent=2)


def load_manifest(deck_dir: str, slide_number: int) -> dict:
    path = _manifest_path(deck_dir, slide_number)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"No creative_vision manifest at {path}")
    with open(path) as f:
        return json.load(f)


def revise_prose(manifest: dict, new_prose: str, revised_by: str, reason: str) -> None:
    """Append a new prose version to manifest['prose_history'] in-place.

    Bumps the version number; preserves prior versions for audit.

    Raises:
        ValueError: when new_prose is empty.
    """
    if not new_prose:
        raise ValueError("new_prose must not be empty")
    next_version = manifest["prose_history"][-1]["version"] + 1
    manifest["prose_history"].append({
        "version": next_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prose": new_prose,
        "revised_by": revised_by,
        "reason": reason,
    })


def _next_tier(current: str, ladder: list[str]) -> str | None:
    if current not in ladder:
        return None
    idx = ladder.index(current)
    return ladder[idx + 1] if idx + 1 < len(ladder) else None


def append_attempt(manifest: dict, attempt: dict, ladder: list[str]) -> None:
    """Append an attempt record and update iterate_slide_hooks accordingly.

    The `ladder` is the cascade tier order — the manifest module is
    intentionally decoupled from cascade.LADDER_DEFAULT so cascade can be
    tested independently. The caller (orchestrator) passes the correct
    ladder based on brand_fidelity routing.

    Reads `manifest['_initial_budget_usd']` (stashed by `initialise_manifest`)
    and recomputes `remaining_budget_usd` as `initial - cumulative`. When
    remaining hits zero, `can_escalate_tier` is flipped off.

    Edit tier (issue #143, F-10/T8): an `mlx_edit` attempt is NOT a rung
    on the cascade ladder — it must not reset `current_tier` /
    `next_tier_available`, or a later escalate_tier would compute "next
    after mlx_edit" instead of resuming from wherever the ladder actually
    was. `can_edit` flips True the first time any attempt (edit or
    regular) carries a rendered image — an edit only ever needs a prior
    on-disk image to work from, independent of budget or tier ceiling.
    """
    manifest["attempts"].append(attempt)
    hooks = manifest["iterate_slide_hooks"]
    if attempt["tier"] != "mlx_edit":
        hooks["current_tier"] = attempt["tier"]
        hooks["next_tier_available"] = _next_tier(attempt["tier"], ladder)
    initial_budget = manifest["_initial_budget_usd"]
    hooks["remaining_budget_usd"] = max(0.0, initial_budget - attempt["cumulative_cost_usd"])
    if hooks["remaining_budget_usd"] <= 0.001:
        hooks["can_escalate_tier"] = False
    render = attempt.get("render") or {}
    if render.get("image_path") or render.get("output_path"):
        hooks["can_edit"] = True


def finalise_manifest(manifest: dict, image_path: str, final_verdict: dict) -> None:
    """Stamp the final block from the manifest's last attempt and final verdict."""
    last = manifest["attempts"][-1]
    manifest["final"] = {
        "image_path": image_path,
        "accepted_at_tier": last["tier"],
        "total_cost_usd": last["cumulative_cost_usd"],
        "total_iterations": len(manifest["attempts"]),
        "final_verdict": final_verdict,
    }
