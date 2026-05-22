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
