"""Bridge LAYOUT_BULLET_CAPS must match the msft-smartart catalog.

Run 7 Finding #22: the bridge's `select_layout_for_bullets` patch declared
``LAYOUT_BULLET_CAPS["vList2"] = 60`` while the msft-smartart catalog had
``vList2.max_label_chars = 30``. The mismatch crashed ``apply_enrichment``
when bullets fell in the 31-60 char band — the engine's constraint check
was the load-bearing truth, the bridge's table was a fictional claim.

This test asserts the two systems agree at patch time. Adding or modifying
an entry in either system without updating the other will fail this test
loudly — preventing the same class of two-system contract drift from
recurring.

The test reads the msft-smartart catalog directly via JSON to avoid
runtime cache-version dependencies; it validates that the bridge source
agrees with the msft-smartart source.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.enrichment_ops.smartart_from_list import LAYOUT_BULLET_CAPS


def _msft_catalog_path() -> Path:
    """Locate the msft-smartart plugin's catalog.json (source, not cache).

    The plugin lives as a sibling of the bridge plugin in the monorepo.
    """
    bridge_root = Path(__file__).resolve().parents[1]
    candidate = bridge_root.parent / "jack-tar-msft-smartart" / "src" / "layouts" / "catalog.json"
    if not candidate.exists():
        pytest.skip(f"msft-smartart catalog source not found at {candidate}")
    return candidate


@pytest.fixture(scope="module")
def catalog_caps() -> dict[str, int]:
    """Read the msft-smartart source catalog and index max_label_chars by id."""
    catalog = json.loads(_msft_catalog_path().read_text())
    return {
        entry["id"]: entry["max_label_chars"]
        for entry in catalog["entries"]
        if "max_label_chars" in entry
    }


@pytest.mark.parametrize("layout_id,bridge_cap", list(LAYOUT_BULLET_CAPS.items()))
def test_bridge_layout_cap_matches_catalog(
    layout_id: str, bridge_cap: int, catalog_caps: dict[str, int]
) -> None:
    """Two-system contract test (Finding #22 root cause).

    The bridge declares per-layout bullet caps for its routing decisions in
    ``LAYOUT_BULLET_CAPS`` (process1 / list1 / vList2). The msft-smartart
    engine enforces per-layout ``max_label_chars`` constraints from
    ``catalog.json``. When the two values disagree, ``apply_enrichment``
    crashes mid-transaction with ``FlatListBuildError`` — Run 7 evidence.

    This test asserts both systems agree at patch time. If you change one,
    you must change the other (or this test fails loudly).
    """
    catalog_cap = catalog_caps.get(layout_id)
    assert catalog_cap is not None, (
        f"bridge LAYOUT_BULLET_CAPS references {layout_id!r}, but the "
        f"msft-smartart catalog has no entry for that layout. Either add "
        f"the layout to the catalog, or remove it from LAYOUT_BULLET_CAPS."
    )
    assert bridge_cap == catalog_cap, (
        f"bridge LAYOUT_BULLET_CAPS[{layout_id!r}]={bridge_cap} contradicts "
        f"msft-smartart catalog max_label_chars={catalog_cap}. "
        f"The two systems must agree (Run 7 Finding #22). "
        f"Either bump the catalog max_label_chars or reduce the bridge cap; "
        f"see docs/superpowers/dogfooding/2026-05-01-bridge-dogfood-run-7.md."
    )


def test_layout_bullet_caps_table_is_nonempty() -> None:
    """Defensive: the bridge table must have at least one entry.

    If the table empties (e.g. accidentally cleared during refactor), the
    parametric test above silently passes with zero cases. This guard
    asserts the table isn't empty.
    """
    assert len(LAYOUT_BULLET_CAPS) >= 1, (
        "LAYOUT_BULLET_CAPS is empty — the bridge's SMARTART-FROM-LIST "
        "routing has no layouts to choose from."
    )


def test_layout_bullet_caps_are_strictly_ascending() -> None:
    """The table is implicitly ordered narrowest-to-widest.

    ``select_layout_for_bullets`` falls through caps in dict iteration
    order, picking the first layout whose cap accommodates the longest
    bullet. If the caps were not strictly ascending, the routing would
    produce a non-optimal layout (wider than necessary) for some inputs.
    """
    caps = list(LAYOUT_BULLET_CAPS.values())
    assert caps == sorted(caps), (
        f"LAYOUT_BULLET_CAPS values {caps} are not strictly ascending. "
        f"The table must be ordered narrowest-to-widest so the routing "
        f"picks the smallest layout that fits."
    )
    assert len(set(caps)) == len(caps), (
        f"LAYOUT_BULLET_CAPS values {caps} contain duplicates. Each cap "
        f"must be distinct so the routing is deterministic."
    )
