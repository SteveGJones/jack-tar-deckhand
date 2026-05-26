"""Cost-table reconciliation: cascade.TIER_COSTS must agree with the cloud
plugin's canonical pricing tables for every Google / Recraft tier.

Issue #113 AC6. Surfaced by the 2026-05-23 Agentic Naval Academy dogfood
(see ``docs/superpowers/dogfooding/2026-05-23-creative-vision-agentic-naval-academy.md``)
where Pro 2K was billed at $0.134 by the cloud module while ``cascade.TIER_COSTS``
declared $0.193 — a $0.06/render delta that produced inflated strategy-approval
estimates.

The cloud module's ``estimate_google_cost`` and ``estimate_recraft_cost`` are the
authoritative source. This test pins ``cascade.TIER_COSTS`` to those functions
via the explicit ``TIER_TO_PROVIDER_MODEL_RESOLUTION`` mapping. If cloud pricing
changes, this test fails and ``cascade.TIER_COSTS`` is updated to match.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[2]
DECKHAND = WORKTREE / "plugins" / "jack-tar-deckhand"
CLOUD = WORKTREE / "plugins" / "jack-tar-cloud"


def _clear_src_modules():
    """Drop cached ``src`` / ``src.*`` so a fresh import resolves against the
    plugin we just put on sys.path."""
    for key in list(sys.modules.keys()):
        if key == "src" or key.startswith("src."):
            del sys.modules[key]


@pytest.fixture
def cascade_tables():
    _clear_src_modules()
    sys.path.insert(0, str(DECKHAND))
    try:
        from src.creative_vision.cascade import (
            TIER_COSTS,
            TIER_TO_PROVIDER_MODEL_RESOLUTION,
        )
        return {
            "TIER_COSTS": dict(TIER_COSTS),
            "TIER_TO_PROVIDER_MODEL_RESOLUTION": dict(TIER_TO_PROVIDER_MODEL_RESOLUTION),
        }
    finally:
        sys.path.remove(str(DECKHAND))
        _clear_src_modules()


@pytest.fixture
def cloud_estimators():
    _clear_src_modules()
    sys.path.insert(0, str(CLOUD))
    try:
        from src.generate_cloud_image import (
            estimate_google_cost,
            estimate_recraft_cost,
        )
        return {
            "estimate_google_cost": estimate_google_cost,
            "estimate_recraft_cost": estimate_recraft_cost,
        }
    finally:
        sys.path.remove(str(CLOUD))
        _clear_src_modules()


def _google_tiers(mapping: dict) -> list[tuple[str, str, str]]:
    """Return (tier, model, resolution) for every Google-routed cascade tier."""
    return [
        (tier, model, resolution)
        for tier, (provider, model, resolution) in mapping.items()
        if provider == "google"
    ]


def _recraft_tiers(mapping: dict) -> list[tuple[str, str, str]]:
    """Return (tier, model, resolution) for every Recraft-routed cascade tier."""
    return [
        (tier, model, resolution)
        for tier, (provider, model, resolution) in mapping.items()
        if provider == "recraft"
    ]


def test_ollama_tier_is_free(cascade_tables):
    """Sanity check: the local-free tier must remain $0.00 regardless of cloud."""
    assert cascade_tables["TIER_COSTS"]["ollama"] == 0.0


def test_google_tier_costs_match_cloud_estimator(cascade_tables, cloud_estimators):
    """For every Google-routed cascade tier, cascade.TIER_COSTS[tier] must
    equal cloud's estimate_google_cost(model, resolution)."""
    estimate = cloud_estimators["estimate_google_cost"]
    mapping = cascade_tables["TIER_TO_PROVIDER_MODEL_RESOLUTION"]
    costs = cascade_tables["TIER_COSTS"]

    mismatches = []
    for tier, model, resolution in _google_tiers(mapping):
        expected = estimate(model=model, resolution=resolution)
        actual = costs[tier]
        if expected != actual:
            mismatches.append((tier, model, resolution, actual, expected))

    assert not mismatches, (
        "cascade.TIER_COSTS disagrees with cloud's estimate_google_cost for: "
        + "; ".join(
            f"{tier} ({model} @ {res}): cascade={actual} cloud={expected}"
            for tier, model, res, actual, expected in mismatches
        )
    )


def test_recraft_tier_costs_match_cloud_estimator(cascade_tables, cloud_estimators):
    """For every Recraft-routed cascade tier, cascade.TIER_COSTS[tier] must
    equal cloud's estimate_recraft_cost(tier, resolution).

    Recraft uses ``tier`` (standard / pro), not model name — the cascade tier's
    second tuple element is the model name, but we recover Recraft's notion of
    tier from the cascade tier prefix.
    """
    estimate = cloud_estimators["estimate_recraft_cost"]
    mapping = cascade_tables["TIER_TO_PROVIDER_MODEL_RESOLUTION"]
    costs = cascade_tables["TIER_COSTS"]

    cascade_tier_to_recraft_tier = {
        "recraft_standard_1k": "standard",
        "recraft_pro_2k": "pro",
        "recraft_pro_4k": "pro",
    }

    mismatches = []
    for tier, _model, resolution in _recraft_tiers(mapping):
        recraft_tier = cascade_tier_to_recraft_tier[tier]
        expected = estimate(tier=recraft_tier, resolution=resolution)
        actual = costs[tier]
        if expected != actual:
            mismatches.append((tier, recraft_tier, resolution, actual, expected))

    assert not mismatches, (
        "cascade.TIER_COSTS disagrees with cloud's estimate_recraft_cost for: "
        + "; ".join(
            f"{tier} (recraft {rt} @ {res}): cascade={actual} cloud={expected}"
            for tier, rt, res, actual, expected in mismatches
        )
    )


def test_pro_2k_specifically_reconciled(cascade_tables, cloud_estimators):
    """Regression pin for the Naval Academy dogfood surprise (#113 AC6).

    cascade.TIER_COSTS['pro_2k'] historically said $0.193; cloud reported
    $0.134. The reconciliation MUST land on the cloud value.
    """
    estimate = cloud_estimators["estimate_google_cost"]
    cloud_pro_2k = estimate(model="gemini-3-pro-image-preview", resolution="2K")
    cascade_pro_2k = cascade_tables["TIER_COSTS"]["pro_2k"]

    assert cascade_pro_2k == cloud_pro_2k, (
        f"pro_2k mismatch — cascade={cascade_pro_2k}, cloud={cloud_pro_2k}. "
        f"This is the exact disagreement issue #113 AC6 was filed to resolve."
    )
