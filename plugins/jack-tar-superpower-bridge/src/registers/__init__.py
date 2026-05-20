"""Register presets — bundle of palette + typography + layout + strap_style defaults.

Speakers may declare ``register: "<preset-name>"`` in the brief header to pull
in a coherent set of defaults that match a particular audience / visual mode.
Per-deck overrides (Section B palette table, ``strap_style:`` header field)
still win — registers establish defaults that the operator can override
piecewise.
"""
from .loader import (  # noqa: F401
    KNOWN_REGISTERS,
    Preset,
    PresetNotFoundError,
    list_preset_names,
    load_preset,
)
