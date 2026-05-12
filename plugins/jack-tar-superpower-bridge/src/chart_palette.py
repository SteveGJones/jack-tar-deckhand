"""Chart series colour derivation from BrandPalette (issue #55).

Derives a list of hex series colours for a native python-pptx chart, given
the brief's BrandPalette, a palette role, and the number of series to colour.

Three roles are supported:

- ``"default"`` — a single-hue family derived from the primary fill by
  stepping lightness in HSL space. First colour is the primary fill itself;
  successive colours are lighter (higher lightness, same hue + saturation).
  Works for any series count; the colour family reads as "variations on the
  brand colour".

- ``"vital_and_mourning"`` — exactly two colours: the primary fill (the
  "vital" / emphasis series) and a desaturated, darkened derivative (the
  "mourning" / de-emphasis series). Intended for 2-series charts where one
  series is the focus and the other is context. If n_series != 2, the
  function logs a warning and falls back to ``"default"``.

- ``"data_categorical"`` — n_series distinct hues, evenly distributed around
  the HSL colour wheel, all sharing the primary fill's saturation and
  lightness. The first hue is the primary fill's own hue; subsequent hues
  are rotated by ``360 / n_series`` degrees. Produces visually distinct
  colours suitable for 3+ unrelated data series.

Explicit override:

  If the caller supplies ``explicit: list[str]``, it always wins regardless
  of ``role``. The list is normalised (6-char uppercase hex without ``#``).
  If ``len(explicit) < n_series`` the last colour is repeated to pad; if
  ``len(explicit) > n_series`` the list is truncated. This lets operators
  specify exact hex values for each series when brand-governance matters.

Soft failure:

  If n_series > 6 for any role, a warning is logged (to stderr) and a
  best-effort palette is returned — derive_chart_palette never raises for a
  large n_series.
"""
from __future__ import annotations

import colorsys
import re
import sys
import warnings

from src.colors_xml_builder import BrandPalette

_HEX_NORM_RE = re.compile(r"^#?([0-9A-Fa-f]{6})$")
_N_SERIES_WARN_THRESHOLD = 6


def _hex_to_rgb(hex_str: str) -> tuple[float, float, float]:
    """Return (r, g, b) each in [0, 1] from a 6-char hex string (no leading #)."""
    h = hex_str.lstrip("#")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    return r, g, b


def _rgb_to_hex(r: float, g: float, b: float) -> str:
    """Return an uppercase 6-char hex string from (r, g, b) each in [0, 1]."""
    ri = max(0, min(255, round(r * 255)))
    gi = max(0, min(255, round(g * 255)))
    bi = max(0, min(255, round(b * 255)))
    return f"{ri:02X}{gi:02X}{bi:02X}"


def _normalise_hex(value: str) -> str:
    """Normalise a hex colour to 6-char uppercase without leading ``#``."""
    m = _HEX_NORM_RE.match(value.strip())
    if m is None:
        raise ValueError(
            f"Invalid hex colour for explicit series_colours: {value!r}. "
            "Expected a 6-character hex string (with or without leading '#')."
        )
    return m.group(1).upper()


def _default_palette(primary_hex: str, n: int) -> list[str]:
    """Lightness-stepped single-hue family from primary_hex.

    Series 0 is the primary fill colour exactly (no round-trip conversion).
    Subsequent series step toward a lighter shade by increasing HSL lightness.
    """
    r, g, b = _hex_to_rgb(primary_hex)
    h, base_l, s = colorsys.rgb_to_hls(r, g, b)
    # colorsys.rgb_to_hls returns (h, l, s) — note L is index 1.
    result: list[str] = []
    for i in range(n):
        if i == 0:
            # Return the primary fill exactly — no round-trip rounding.
            result.append(primary_hex)
            continue
        # Step lightness toward 0.85 (near-white) across the series count.
        if n == 1:
            step_l = base_l
        else:
            max_l = min(0.85, base_l + 0.40)
            step_l = base_l + (max_l - base_l) * (i / (n - 1))
        # Clamp to [0.1, 0.92] to avoid near-black or near-white extremes.
        step_l = max(0.10, min(0.92, step_l))
        rr, gg, bb = colorsys.hls_to_rgb(h, step_l, s)
        result.append(_rgb_to_hex(rr, gg, bb))
    return result


def _vital_and_mourning_palette(primary_hex: str) -> list[str]:
    """Two-colour pair: primary fill (vital) + desaturated+darkened (mourning)."""
    r, g, b = _hex_to_rgb(primary_hex)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    # colorsys.rgb_to_hls returns (h, l, s).
    # Mourning: reduce saturation to ~20% of original, darken by 25%.
    mourning_s = s * 0.20
    mourning_l = max(0.10, l * 0.75)
    mr, mg, mb = colorsys.hls_to_rgb(h, mourning_l, mourning_s)
    return [primary_hex, _rgb_to_hex(mr, mg, mb)]


def _data_categorical_palette(primary_hex: str, n: int) -> list[str]:
    """n evenly-spaced hues around the colour wheel, sharing primary's S and L."""
    r, g, b = _hex_to_rgb(primary_hex)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    # colorsys.rgb_to_hls returns (h, l, s).
    result: list[str] = []
    for i in range(n):
        rotated_h = (h + i / n) % 1.0
        rr, gg, bb = colorsys.hls_to_rgb(rotated_h, l, s)
        result.append(_rgb_to_hex(rr, gg, bb))
    return result


def derive_chart_palette(
    brand: BrandPalette,
    role: str,
    n_series: int,
    explicit: list[str] | None = None,
) -> list[str]:
    """Return a list of ``n_series`` hex strings for chart series colouring.

    Parameters
    ----------
    brand:
        The brief's BrandPalette. ``primary_fill_hex`` is the anchor colour.
    role:
        One of ``"default"``, ``"vital_and_mourning"``, or
        ``"data_categorical"``. Unrecognised values are treated as
        ``"default"`` with a warning.
    n_series:
        Number of series colours required. Must be >= 1. Values > 6 trigger a
        soft warning but produce a best-effort result.
    explicit:
        When supplied, overrides role-based derivation entirely. Each entry
        must be a 6-char hex string (with or without leading ``#``). The list
        is padded (last colour repeated) or truncated to match ``n_series``.

    Returns
    -------
    list[str]
        Exactly ``n_series`` uppercase 6-char hex strings without leading
        ``#``.
    """
    if n_series < 1:
        raise ValueError(f"n_series must be >= 1, got {n_series!r}")

    # Explicit override — normalise and pad/truncate to n_series.
    if explicit is not None:
        normalised = [_normalise_hex(c) for c in explicit]
        if len(normalised) < n_series:
            # Pad by repeating the last colour.
            normalised = normalised + [normalised[-1]] * (n_series - len(normalised))
        return normalised[:n_series]

    if n_series > _N_SERIES_WARN_THRESHOLD:
        warnings.warn(
            f"derive_chart_palette: n_series={n_series} exceeds recommended "
            f"maximum ({_N_SERIES_WARN_THRESHOLD}). Producing best-effort palette; "
            "consider supplying explicit series_colours for large series counts.",
            stacklevel=2,
        )

    primary = brand.primary_fill_hex  # already normalised uppercase no-#

    if role == "vital_and_mourning":
        if n_series != 2:
            warnings.warn(
                f"derive_chart_palette: role='vital_and_mourning' is designed for "
                f"exactly 2 series but n_series={n_series}. Falling back to 'default'.",
                stacklevel=2,
            )
            return _default_palette(primary, n_series)
        return _vital_and_mourning_palette(primary)
    elif role == "data_categorical":
        return _data_categorical_palette(primary, n_series)
    else:
        if role != "default":
            warnings.warn(
                f"derive_chart_palette: unrecognised role {role!r}; using 'default'.",
                stacklevel=2,
            )
        return _default_palette(primary, n_series)
