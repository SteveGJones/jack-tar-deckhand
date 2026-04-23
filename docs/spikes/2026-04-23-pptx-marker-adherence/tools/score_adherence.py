"""Score marker adherence: emitted vs. requested by kind."""
from __future__ import annotations

from typing import Any


def score(requested: dict[str, int], emitted: dict[str, int]) -> dict[str, Any]:
    total_requested = sum(requested.values())
    total_counted = 0
    missing: dict[str, int] = {}
    extra: dict[str, int] = {}
    for kind, want in requested.items():
        have = emitted.get(kind, 0)
        counted = min(have, want)
        total_counted += counted
        if have < want:
            missing[kind] = want - have
        elif have > want:
            extra[kind] = have - want
    rate = (total_counted / total_requested) if total_requested else 0.0
    if rate >= 0.95:
        verdict = "full"
    elif rate > 0:
        verdict = "partial"
    else:
        verdict = "none"
    return {
        "requested": requested,
        "emitted": emitted,
        "overall_rate": rate,
        "verdict": verdict,
        "missing": missing,
        "extra": extra,
    }
