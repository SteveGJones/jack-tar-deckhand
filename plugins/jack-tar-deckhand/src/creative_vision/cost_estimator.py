"""Creative-vision cost estimator — per-slide cost bands and deck-level summary.

Issue #113 AC1. The strategy-map skill calls these helpers when presenting the
strategy map for operator approval, so the operator sees explicit per-creative-
vision-slide cost line items before authorising the deck.

Historical dogfood envelope (the basis for the gate-count band):

- Sun-phases (2026-05-21): $0.067, 3 attempts × ~3 operator gates.
- Data supply chain (2026-05-22→23): $1.016, 14 attempts × ~10 operator gates
  (pre-F10 — multiple gates were skipped; F10 reins this in).
- Agentic Naval Academy (2026-05-23): $0.268, 7 attempts × 6 operator gates
  (post-F10 — every gate fired).

Post-F10 the typical envelope is **3-7 operator gates per slide and
$0.20-$1.50 of cloud spend**, depending on ``allowed_ceiling`` and slide
complexity. The cost band returned here is the structural upper / lower
bound derived from the cascade ladder and per-tier iteration caps; the gate
band is the dogfood-observed range pinned at 3-7.
"""
from __future__ import annotations

from .cascade import (
    DEFAULT_ITERATION_CAPS,
    TIER_COSTS,
    ladder_for,
)

# Dogfood-observed gate count band. Held as a module-level constant so tests
# and the strategy-map skill cite the same source.
TYPICAL_GATE_BAND: tuple[int, int] = (3, 7)


def estimate_creative_vision_slide_cost(
    *,
    allowed_ceiling: str,
    brand_fidelity: str = "none",
    cost_table: dict[str, float] | None = None,
    iteration_caps: dict[str, int] | None = None,
) -> dict:
    """Return min/typical/max cost band for one creative_vision slide.

    The band has two structural bounds:

    - **min_cost_usd** — the operator's best case at this ceiling: one free
      Ollama draft followed by one paid render at ``allowed_ceiling``. When
      the ceiling is ``ollama``, this is $0.00.
    - **max_cost_usd** — the structural worst case: every tier in the ladder
      up to (and including) ``allowed_ceiling`` exhausts its per-tier
      iteration cap. Real dogfood spends are usually well below this — the
      Critic + budget logic typically stops the loop earlier — but it is the
      true ceiling if every tier needs maximum refinement.

    The gate band is fixed at ``TYPICAL_GATE_BAND`` from dogfood evidence
    (post-F10). It is independent of ``allowed_ceiling`` — even a Flash 1K
    ceiling deck needs 3-7 operator gates per slide because most of the
    gating happens at Ollama before any escalation.

    Args:
        allowed_ceiling: One of the cascade tier names. The ceiling of the
            cascade for this slide (e.g. ``flash_1k`` for budget cap,
            ``pro_4k`` for hero slides).
        brand_fidelity: Slide-level brand fidelity. ``exact`` routes through
            the Recraft ladder; everything else through the default Nano
            Banana ladder. Determines which ladder we iterate up.
        cost_table: Override for ``TIER_COSTS`` (mostly for tests).
        iteration_caps: Override for ``DEFAULT_ITERATION_CAPS`` (mostly for
            tests).

    Returns:
        A dict with min_cost_usd, max_cost_usd, typical_gates (the band
        as a (min, max) tuple), cost_band_str (human-readable
        ``"$X.XX - $Y.YY"``), gate_band_str (``"N-M"``), and ladder_summary
        listing each reachable tier with its unit cost and iteration cap.

    Raises:
        ValueError: If ``allowed_ceiling`` is absent from the resolved ladder
            (e.g. asking for a Recraft tier when ``brand_fidelity`` routes
            through Nano Banana). The error message includes the ladder for
            context.
    """
    costs = cost_table if cost_table is not None else TIER_COSTS
    caps = iteration_caps if iteration_caps is not None else DEFAULT_ITERATION_CAPS

    ladder = ladder_for(brand_fidelity)
    if allowed_ceiling not in ladder:
        raise ValueError(
            f"allowed_ceiling={allowed_ceiling!r} is not reachable under "
            f"brand_fidelity={brand_fidelity!r}. Ladder is {ladder}."
        )

    ceiling_index = ladder.index(allowed_ceiling)
    reachable = ladder[: ceiling_index + 1]

    min_cost = costs[allowed_ceiling]
    max_cost = sum(costs[tier] * caps[tier] for tier in reachable)

    ladder_summary = [
        {
            "tier": tier,
            "unit_cost_usd": round(costs[tier], 3),
            "iteration_cap": caps[tier],
        }
        for tier in reachable
    ]

    return {
        "allowed_ceiling": allowed_ceiling,
        "min_cost_usd": round(min_cost, 3),
        "max_cost_usd": round(max_cost, 3),
        "typical_gates": TYPICAL_GATE_BAND,
        "cost_band_str": f"${min_cost:.2f} - ${max_cost:.2f}",
        "gate_band_str": f"{TYPICAL_GATE_BAND[0]}-{TYPICAL_GATE_BAND[1]}",
        "ladder_summary": ladder_summary,
    }


def summarise_creative_vision_spend(
    strategy_map: dict,
    *,
    default_brand_fidelity: str = "none",
    cost_table: dict[str, float] | None = None,
    iteration_caps: dict[str, int] | None = None,
) -> dict:
    """Aggregate the per-slide bands into a deck-level summary.

    Walks every slide in ``strategy_map['slides']`` and, for each slide whose
    ``strategy == 'creative_vision'``, computes the per-slide band and sums
    them into a deck-level total. Slides without ``creative_vision`` strategy
    are skipped.

    Args:
        strategy_map: A loaded StrategyMap contract (the dict produced by
            ``slide_prompt_composer.build_strategy_map`` and saved by
            ``save_strategy_map``).
        default_brand_fidelity: Fallback brand fidelity when a slide does not
            declare its own. Most decks set this once at the deck level.
        cost_table: Override for ``TIER_COSTS`` (tests).
        iteration_caps: Override for ``DEFAULT_ITERATION_CAPS`` (tests).

    Returns:
        A dict with:

        - ``entries`` — list of per-slide bands (one per creative_vision
          slide), each including ``slide_number`` and the
          per-slide ``estimate_creative_vision_slide_cost`` output.
        - ``slide_count`` — number of creative_vision slides found.
        - ``total_min_cost_usd`` / ``total_max_cost_usd`` — sum of per-slide
          bounds across the deck.
        - ``total_gate_band`` — ``(slide_count * 3, slide_count * 7)`` —
          operator-gate touchpoint count, again from dogfood-observed
          envelope.
        - ``summary_markdown`` — operator-facing markdown table of the per-
          slide line items, ready to render at strategy-map approval.

        If the deck has no creative_vision slides, ``entries`` is empty and
        all totals are zero — the caller can short-circuit the operator
        prompt entirely.
    """
    costs = cost_table if cost_table is not None else TIER_COSTS
    caps = iteration_caps if iteration_caps is not None else DEFAULT_ITERATION_CAPS

    entries: list[dict] = []
    total_min = 0.0
    total_max = 0.0

    for slide in strategy_map.get("slides", []):
        if slide.get("strategy") != "creative_vision":
            continue
        cv_config = slide.get("creative_vision", {})
        allowed_ceiling = cv_config.get("allowed_ceiling", "pro_4k")
        slide_brand_fidelity = slide.get("brand_fidelity", default_brand_fidelity)
        band = estimate_creative_vision_slide_cost(
            allowed_ceiling=allowed_ceiling,
            brand_fidelity=slide_brand_fidelity,
            cost_table=costs,
            iteration_caps=caps,
        )
        entries.append({"slide_number": slide["slide_number"], **band})
        total_min += band["min_cost_usd"]
        total_max += band["max_cost_usd"]

    slide_count = len(entries)
    total_gate_band = (
        slide_count * TYPICAL_GATE_BAND[0],
        slide_count * TYPICAL_GATE_BAND[1],
    )

    return {
        "entries": entries,
        "slide_count": slide_count,
        "total_min_cost_usd": round(total_min, 2),
        "total_max_cost_usd": round(total_max, 2),
        "total_gate_band": total_gate_band,
        "summary_markdown": format_spend_summary_markdown(
            entries=entries,
            slide_count=slide_count,
            total_min_cost_usd=round(total_min, 2),
            total_max_cost_usd=round(total_max, 2),
            total_gate_band=total_gate_band,
        ),
    }


def format_spend_summary_markdown(
    *,
    entries: list[dict],
    slide_count: int,
    total_min_cost_usd: float,
    total_max_cost_usd: float,
    total_gate_band: tuple[int, int],
) -> str:
    """Format the deck-level creative_vision spend table for the operator.

    Empty entries → a one-line "No creative_vision slides in this strategy
    map" message so the strategy-map skill can show the same surface
    regardless of slide composition.

    Otherwise: a markdown table with per-slide line items (slide number,
    allowed_ceiling, cost band, gate band) plus a deck-level totals row at
    the bottom. The operator reads this and either confirms or asks for
    fallback strategies on the over-budget slides.
    """
    if not entries:
        return "No creative_vision slides in this strategy map."

    lines = [
        "| Slide | Ceiling | Cost band | Operator gates |",
        "| ----- | ------- | --------- | -------------- |",
    ]
    for e in entries:
        lines.append(
            f"| {e['slide_number']} | `{e['allowed_ceiling']}` | "
            f"{e['cost_band_str']} | {e['gate_band_str']} |"
        )
    lines.append(
        f"| **Total ({slide_count} slide{'s' if slide_count != 1 else ''})** "
        f"| — | **${total_min_cost_usd:.2f} - ${total_max_cost_usd:.2f}** "
        f"| **{total_gate_band[0]}-{total_gate_band[1]}** |"
    )
    lines.append("")
    lines.append(
        "Cost bands reflect the structural worst case at each ``allowed_ceiling`` "
        "(every tier in the cascade ladder exhausting its iteration cap). Real "
        "dogfood spends are usually well below the upper bound — the F10 operator "
        "gate and the Director's Critic typically stop the loop earlier. The "
        "gate-count band (3-7 per slide) reflects post-F10 dogfood evidence."
    )
    return "\n".join(lines)
