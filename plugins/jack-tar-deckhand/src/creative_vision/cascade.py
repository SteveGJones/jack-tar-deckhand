"""Cascade state machine — tier ladders, plateau detection, budget enforcement.

Implements §5 of the spec. Issue #105.
"""
from __future__ import annotations

LADDER_DEFAULT: list[str] = [
    "ollama", "flash_1k", "flash_2k", "flash_4k",
    "pro_1k", "pro_2k", "pro_4k",
]

LADDER_RECRAFT: list[str] = [
    "ollama", "recraft_standard_1k", "recraft_pro_2k", "recraft_pro_4k",
]

TIER_COSTS: dict[str, float] = {
    "ollama": 0.0,
    "flash_1k": 0.067,
    "flash_2k": 0.101,
    "flash_4k": 0.151,
    "pro_1k": 0.134,
    "pro_2k": 0.193,
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
