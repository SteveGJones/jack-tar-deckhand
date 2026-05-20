"""Strategy classifier — rule-based per-slide strategy heuristics (paperbanana E1).

The strategy-map step is normally driven by Claude reasoning over the
narrative arc + slide content; this module provides deterministic
fallback heuristics for cases where rule-based classification suffices
and saves a model dispatch. It is also the entry point for the
``academic_figure`` strategy (paperbanana integration, plan §6 Phase 3
E1) — slides whose subject is a publication-quality scientific figure
(architecture diagram with formal notation, equations, citations,
academic-style schematic) route through paperbanana's ``generate-diagram``
skill when the plugin is installed, falling back to the regular cloud
image path when it is not.

Design goals:

- **Conservative**: the classifier returns ``"academic_figure"`` only
  when the signal is unambiguous. Borderline cases return ``None`` and
  let the upstream Claude pass decide.
- **Composable**: the function is pure and takes only the slide's
  outline / content text plus optional metadata. No side effects.
- **Testable**: every heuristic has a corresponding test case.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


# Words / phrases that signal a slide is academic-figure-shaped. Each
# entry is a regex pattern compiled against a lowercased version of the
# slide's content text. Conservative — these must be unambiguous.
_ACADEMIC_FIGURE_SIGNALS: list[tuple[str, str]] = [
    # Explicit "Figure N:" / "Fig N." captions are the strongest signal.
    (r"\bfigure\s+\d+[:.]", "explicit figure caption (Figure N:)"),
    (r"\bfig\.\s*\d+[:.]", "explicit fig caption (Fig N.)"),
    # Equation / formula content (LaTeX-style or unicode math)
    (r"\$\$.+?\$\$", "block equation"),
    (r"\\(?:frac|sum|int|alpha|beta|gamma|theta|sigma|lambda)\b", "LaTeX math command"),
    # Citation-style references in the slide body
    (r"\[\d+\]", "numbered citation"),
    (r"\bet al\.", "author citation"),
    # Algorithmic / pseudocode signals
    (r"\balgorithm\s+\d+", "Algorithm N heading"),
    (r"\bpseudocode\b", "pseudocode label"),
    # Common academic-figure subject keywords
    (r"\bsystem architecture\b.*\b(model|encoder|decoder|layer|head)\b", "ML architecture subject"),
    (r"\bablation\s+study\b", "ablation study figure"),
    (r"\bconfusion matrix\b", "confusion matrix figure"),
]


# Words that strongly signal the slide is NOT academic-figure-shaped even
# when a weak signal matches (e.g. "Figure" in a non-caption sense).
_NEGATIVE_SIGNALS: list[str] = [
    "executive summary",
    "go-to-market",
    "fundraising",
    "press release",
    "thank you",
]


@dataclass
class StrategyClassification:
    """Result of classifying a slide's content."""

    strategy: str | None
    """The classified strategy, or None when the heuristics don't fire."""

    rationale: str
    """Human-readable explanation of why this strategy was selected (or not)."""

    matched_signals: list[str]
    """List of signal labels that fired during classification."""


def classify_strategy(
    slide_text: str,
    *,
    paperbanana_available: bool = False,
) -> StrategyClassification:
    """Return a strategy classification for a slide.

    Args:
        slide_text: concatenated outline + body content of the slide.
        paperbanana_available: whether the paperbanana plugin is installed
            and reachable. Currently only affects the rationale text —
            the classification returns ``"academic_figure"`` even when
            paperbanana is unavailable, so the upstream imagegen-bridge
            can decide whether to fall back to cloud generation.

    Returns:
        StrategyClassification with one of:
        - strategy="academic_figure" when 2+ academic signals fire and no
          negative signal does.
        - strategy=None when signals are absent, ambiguous, or
          contradicted by a negative signal — defer to the upstream
          Claude pass.
    """
    if not slide_text:
        return StrategyClassification(
            strategy=None,
            rationale="empty slide text — defer to upstream classifier",
            matched_signals=[],
        )

    lowered = slide_text.lower()

    # Check negative signals first — any single negative signal vetoes
    # the academic_figure classification.
    for negative in _NEGATIVE_SIGNALS:
        if negative in lowered:
            return StrategyClassification(
                strategy=None,
                rationale=(
                    f"negative signal {negative!r} indicates this is a "
                    "business/executive slide, not an academic figure"
                ),
                matched_signals=[f"negative:{negative}"],
            )

    matched: list[str] = []
    for pattern, label in _ACADEMIC_FIGURE_SIGNALS:
        if re.search(pattern, lowered, flags=re.IGNORECASE | re.DOTALL):
            matched.append(label)

    # Require at least 2 positive signals for an academic_figure
    # classification. A single match could be coincidental ("Figure 1"
    # in a narrative slide title); two independent signals together are
    # strong evidence.
    if len(matched) >= 2:
        availability_note = (
            "paperbanana plugin reachable; will dispatch to /generate-diagram"
            if paperbanana_available
            else "paperbanana plugin not detected; upstream will fall back to "
            "cloud image generation with academic-figure-aware prompting"
        )
        return StrategyClassification(
            strategy="academic_figure",
            rationale=(
                f"{len(matched)} academic-figure signals matched: "
                f"{', '.join(matched)}. {availability_note}."
            ),
            matched_signals=matched,
        )

    if len(matched) == 1:
        return StrategyClassification(
            strategy=None,
            rationale=(
                f"single signal {matched[0]!r} is insufficient — academic_figure "
                "requires 2+ signals to avoid false positives"
            ),
            matched_signals=matched,
        )

    return StrategyClassification(
        strategy=None,
        rationale="no academic-figure signals matched — defer to upstream classifier",
        matched_signals=[],
    )
