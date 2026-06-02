"""Cascade state machine — tier ladders, plateau detection, budget enforcement.

Implements §5 of the spec. Issue #105.

Cost-table reconciliation (issue #113 AC6): the canonical pricing source is
``plugins/jack-tar-cloud/src/generate_cloud_image.py``'s ``estimate_google_cost``
and ``estimate_recraft_cost``. ``TIER_COSTS`` below is the cascade-tier-keyed
projection of that pricing, and ``TIER_TO_PROVIDER_MODEL_RESOLUTION`` maps each
cascade tier to the (provider, model, resolution) tuple that the cloud module
uses. The cross-plugin reconciliation test in
``plugins/integration_tests/test_cost_reconciliation.py`` asserts the two stay
in sync — if the cloud table moves (Google drops pricing, Recraft changes a
tier), the integration test fails and ``TIER_COSTS`` here is updated to match.
"""
from __future__ import annotations

LADDER_DEFAULT: list[str] = [
    "ollama", "flash_1k", "flash_2k", "flash_4k",
    "pro_1k", "pro_2k", "pro_4k",
]

LADDER_RECRAFT: list[str] = [
    "ollama", "recraft_standard_1k", "recraft_pro_2k", "recraft_pro_4k",
]

# Canonical mapping from cascade tier name to (provider, model, resolution).
# ``ollama`` maps to ``(None, None, None)`` — local, no cloud call. The cloud
# module's ``estimate_google_cost`` / ``estimate_recraft_cost`` are keyed by
# (model, resolution); this mapping is what lets the reconciliation test bridge
# the two namespaces without coupling the modules at import time.
TIER_TO_PROVIDER_MODEL_RESOLUTION: dict[str, tuple[str | None, str | None, str | None]] = {
    "ollama": (None, None, None),
    "flash_1k": ("google", "gemini-3.1-flash-image-preview", "1K"),
    "flash_2k": ("google", "gemini-3.1-flash-image-preview", "2K"),
    "flash_4k": ("google", "gemini-3.1-flash-image-preview", "4K"),
    "pro_1k": ("google", "gemini-3-pro-image-preview", "1K"),
    "pro_2k": ("google", "gemini-3-pro-image-preview", "2K"),
    "pro_4k": ("google", "gemini-3-pro-image-preview", "4K"),
    "recraft_standard_1k": ("recraft", "recraft-v4-standard", "1K"),
    "recraft_pro_2k": ("recraft", "recraft-v4-pro", "2K"),
    "recraft_pro_4k": ("recraft", "recraft-v4-pro", "4K"),
}

# Per-tier cost in USD. Mirrors the cloud module's pricing tables; the
# reconciliation test pins them together. When updating, also update the
# integration test's expected values OR update the cloud module if that is the
# moved source of truth.
TIER_COSTS: dict[str, float] = {
    "ollama": 0.0,
    "flash_1k": 0.067,
    "flash_2k": 0.101,
    "flash_4k": 0.151,
    "pro_1k": 0.134,
    # Issue #113 AC6: reconciled 2026-05-24. Google Nano Banana Pro 2K is
    # priced identically to Pro 1K ($0.134); cascade previously had $0.193
    # which produced inflated cost estimates at strategy approval.
    "pro_2k": 0.134,
    "pro_4k": 0.240,
    "recraft_standard_1k": 0.04,
    "recraft_pro_2k": 0.25,
    "recraft_pro_4k": 0.50,
}

DEFAULT_ITERATION_CAPS: dict[str, int] = {
    "ollama": 5,
    "flash_1k": 3, "flash_2k": 3, "flash_4k": 3,
    "pro_1k": 2, "pro_2k": 2, "pro_4k": 1,
    "recraft_standard_1k": 3, "recraft_pro_2k": 2, "recraft_pro_4k": 1,
}

DEFAULT_BUDGET_USD: float = 1.00


def ladder_for(brand_fidelity: str) -> list[str]:
    """Return the cascade tier ladder for the given brand_fidelity value.

    'exact' routes through the Recraft ladder; everything else through the
    default Nano Banana ladder. The two ladders are mutually exclusive per
    slide — mixing within one cascade would shift style mid-iteration.
    """
    if brand_fidelity == "exact":
        return LADDER_RECRAFT
    return LADDER_DEFAULT


_AXES = ("entity_fidelity", "spatial_fidelity", "style_fidelity", "quality", "composition")

PLATEAU_THRESHOLD = 5  # points per axis
PLATEAU_WINDOW = 2     # number of prior iterations to look back


def detect_plateau(score_history: list[dict]) -> bool:
    """Return True if no axis has improved by ≥PLATEAU_THRESHOLD across the last PLATEAU_WINDOW iterations.

    Requires at least PLATEAU_WINDOW+1 entries (current + that many priors).
    Returns False when there's insufficient history to judge.
    """
    if len(score_history) < PLATEAU_WINDOW + 1:
        return False
    window = score_history[-(PLATEAU_WINDOW + 1):]
    earliest = window[0]
    latest = window[-1]
    for axis in _AXES:
        if latest[axis] - earliest[axis] >= PLATEAU_THRESHOLD:
            return False
    return True


def can_afford(remaining_budget_usd: float, tier: str) -> bool:
    """Return True when the budget has room for one more render at the given tier."""
    return remaining_budget_usd >= TIER_COSTS[tier] or TIER_COSTS[tier] == 0.0


def next_tier(current: str, ladder: list[str], allowed_ceiling: str | None = None) -> str | None:
    """Return the next tier above ``current`` in the ladder, or None if at top/ceiling."""
    if current not in ladder:
        return None
    idx = ladder.index(current)
    if idx + 1 >= len(ladder):
        return None
    candidate = ladder[idx + 1]
    if allowed_ceiling is not None and allowed_ceiling in ladder:
        if ladder.index(candidate) > ladder.index(allowed_ceiling):
            return None
    return candidate
