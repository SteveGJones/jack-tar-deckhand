"""Image bridge — draft/review cycle, budget tracking, privacy tiering.

Phase 4 task 14 of the implementation plan adds BudgetCap. Tasks 15
and 16 add the privacy tier gate and the full draft/review cycle.

Spec Section 3.3 + Security & Privacy. Caveat #6 — budget cap covers
both generation and review costs; the cheapest "next call" must be
affordable across both kinds.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


VALID_COST_KINDS = ("generation", "review")


class BudgetExhaustedError(RuntimeError):
    """Raised when the BudgetCap cannot fund a requested charge."""


@dataclass
class CostEvent:
    kind: str        # generation | review
    provider: str
    cost_usd: float


@dataclass
class BudgetCap:
    """Hard ceiling on cumulative cloud spend within a single /enrich-deck run.

    Both `kind="generation"` and `kind="review"` deduct from the same pool
    (caveat #6 — earlier drafts of the spec only counted generation).
    """
    usd: float
    spent: float = 0.0
    history: list[CostEvent] = field(default_factory=list)

    @property
    def remaining(self) -> float:
        return max(0.0, self.usd - self.spent)

    def can_afford(self, cost_usd: float) -> bool:
        return cost_usd <= self.remaining + 1e-9

    def charge(self, *, kind: str, provider: str, cost_usd: float) -> None:
        if kind not in VALID_COST_KINDS:
            raise ValueError(f"kind {kind!r} not in {VALID_COST_KINDS}")
        if not self.can_afford(cost_usd):
            raise BudgetExhaustedError(
                f"charge ${cost_usd:.4f} for {kind}/{provider} exceeds remaining "
                f"${self.remaining:.4f} (cap ${self.usd:.4f})"
            )
        self.spent += cost_usd
        self.history.append(CostEvent(kind=kind, provider=provider, cost_usd=cost_usd))
