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


VALID_TIERS = ("public", "internal", "restricted")


class RestrictedTierError(RuntimeError):
    """Raised when a cloud call is attempted under the restricted tier."""


@dataclass
class PrivacyTierGate:
    """Privacy gate per the spec's Privacy tiering section.

    - public:     cloud allowed, no confirmation
    - internal:   cloud allowed, but the FIRST cloud call per run requires
                  the user to confirm (the orchestrator shows the prompt
                  and provider URL); subsequent calls in the same run are
                  pre-cleared
    - restricted: cloud disabled outright; only Ollama is allowed
    """
    tier: str
    confirmation_received: bool = False

    def __post_init__(self) -> None:
        if self.tier not in VALID_TIERS:
            raise ValueError(f"tier {self.tier!r} not in {VALID_TIERS}")

    def cloud_allowed(self) -> bool:
        return self.tier != "restricted"

    def requires_confirmation_before_cloud(self) -> bool:
        return self.tier == "internal" and not self.confirmation_received

    def mark_confirmation_received(self) -> None:
        self.confirmation_received = True

    def guard_cloud_call(self, *, provider: str) -> None:
        """Raise if the current state forbids a cloud call to `provider`."""
        if not self.cloud_allowed():
            raise RestrictedTierError(
                f"cloud provider {provider!r} forbidden under restricted tier"
            )
        if self.requires_confirmation_before_cloud():
            raise RuntimeError(
                f"internal tier requires user confirmation before first cloud call "
                f"to {provider!r}; orchestrator must call mark_confirmation_received()"
            )


from pathlib import Path
from typing import Callable, Optional

from src.measurement import record_cost_event


# ---------------------------------------------------------------------------
# Cycle data shapes
# ---------------------------------------------------------------------------

@dataclass
class ImageGenerationRequest:
    slide_index: int
    marker_id: str
    marker_kind: str          # IMAGE | BG
    prompt: str               # initial prompt; refined during the cycle
    output_path: Path
    width: int
    height: int
    brand_palette_hex: list[str] = field(default_factory=list)


@dataclass
class ImageGenerationResult:
    status: Literal["pass", "accepted_with_issues", "halted_budget", "halted_restricted"]
    tier_used: str            # ollama | nanobanana_flash | nanobanana_pro
    final_prompt: str
    iterations: int           # total review iterations performed
    final_summary: str        # last reviewer summary (the only thing the orchestrator keeps)
    review_costs_usd: float   # cumulative review cost
    generation_costs_usd: float  # cumulative generation cost (Ollama=0)


# Callables — injected so tests can mock without touching real models
OllamaGenerator = Callable[[ImageGenerationRequest, int], dict]
CloudGenerator = Callable[[ImageGenerationRequest, str, int], dict]
Reviewer = Callable[[ImageGenerationRequest, Path, str], dict]
PromptRefiner = Callable[[ImageGenerationRequest, str, dict, int], str]


def generate_with_review_cycle(
    *,
    request: ImageGenerationRequest,
    budget: BudgetCap,
    privacy: PrivacyTierGate,
    cwd: Path,
    ollama_generate: OllamaGenerator,
    cloud_generate: CloudGenerator,
    review: Reviewer,
    refine_prompt: PromptRefiner,
    max_ollama_iterations: int = 3,
    max_cloud_flash_iterations: int = 3,
) -> ImageGenerationResult:
    """Run the spec's draft/review cycle for one image.

    Step structure (Spec Section 3.3):
      Phase A — Ollama drafts: up to 3 free iterations; review each; refine prompt
      Phase B — Cloud Flash: only if Ollama didn't pass and privacy + budget allow;
                up to 3 Flash iterations with prompt refinement
      Phase C — Cloud Pro: ONE shot if Flash converged on a passing prompt

    Both generation AND review costs are charged against `budget` (caveat #6).
    """
    prompt = request.prompt
    iterations = 0
    last_summary = ""
    review_cost_total = 0.0
    gen_cost_total = 0.0
    last_reviewer_feedback: dict = {}

    # --- Phase A: Ollama drafts (free generation; review still costs) -------
    for attempt in range(1, max_ollama_iterations + 1):
        ollama_generate(request, attempt)
        iterations += 1
        verdict_payload = review(request, request.output_path, last_summary)
        review_cost = float(verdict_payload.get("cost_usd", 0.0))
        if not budget.can_afford(review_cost):
            # We reviewed but cannot pay — refuse to charge (overdraft)
            # and return what we have.
            return ImageGenerationResult(
                status="halted_budget", tier_used="ollama",
                final_prompt=prompt, iterations=iterations,
                final_summary=verdict_payload.get("summary", "halted before charging"),
                review_costs_usd=review_cost_total,
                generation_costs_usd=gen_cost_total,
            )
        budget.charge(kind="review", provider="haiku", cost_usd=review_cost)
        record_cost_event(cwd=cwd, kind="review", provider="haiku",
                           cost_usd=review_cost,
                           slide_index=request.slide_index,
                           marker_id=request.marker_id)
        review_cost_total += review_cost
        last_summary = verdict_payload.get("summary", "")
        last_reviewer_feedback = verdict_payload
        if verdict_payload.get("verdict") == "pass":
            return ImageGenerationResult(
                status="pass", tier_used="ollama",
                final_prompt=prompt, iterations=iterations,
                final_summary=last_summary,
                review_costs_usd=review_cost_total,
                generation_costs_usd=gen_cost_total,
            )
        # refine for next attempt
        prompt = refine_prompt(request, prompt, last_reviewer_feedback, attempt)
        request.prompt = prompt

    # --- Phase A failed; check if we may escalate to cloud --------------
    if not privacy.cloud_allowed():
        return ImageGenerationResult(
            status="halted_restricted", tier_used="ollama",
            final_prompt=prompt, iterations=iterations,
            final_summary=last_summary,
            review_costs_usd=review_cost_total,
            generation_costs_usd=gen_cost_total,
        )
    if privacy.requires_confirmation_before_cloud():
        # Orchestrator must mark confirmation; treat unconfirmed as halt
        return ImageGenerationResult(
            status="accepted_with_issues", tier_used="ollama",
            final_prompt=prompt, iterations=iterations,
            final_summary=last_summary + " (cloud escalation pending user confirmation)",
            review_costs_usd=review_cost_total,
            generation_costs_usd=gen_cost_total,
        )

    # --- Phase B: Cloud Flash with prompt refinement -------------------
    flash_model = "gemini-3.1-flash-image-preview"
    flash_cost = 0.067
    for flash_attempt in range(1, max_cloud_flash_iterations + 1):
        if not budget.can_afford(flash_cost):
            return ImageGenerationResult(
                status="halted_budget", tier_used="ollama",
                final_prompt=prompt, iterations=iterations,
                final_summary=last_summary,
                review_costs_usd=review_cost_total,
                generation_costs_usd=gen_cost_total,
            )
        gen_payload = cloud_generate(request, flash_model, flash_attempt)
        gen_cost = float(gen_payload.get("cost_usd", flash_cost))
        budget.charge(kind="generation", provider="nanobanana_flash", cost_usd=gen_cost)
        record_cost_event(cwd=cwd, kind="generation", provider="nanobanana_flash",
                           cost_usd=gen_cost,
                           slide_index=request.slide_index,
                           marker_id=request.marker_id)
        gen_cost_total += gen_cost
        iterations += 1
        verdict_payload = review(request, request.output_path, last_summary)
        review_cost = float(verdict_payload.get("cost_usd", 0.0))
        # Caveat #6 — review charge MUST be unconditional.
        # If we cannot afford the review, we have already paid for the
        # generation; halt cleanly so callers cannot escalate to Pro on
        # an unpaid verdict.
        if not budget.can_afford(review_cost):
            return ImageGenerationResult(
                status="halted_budget", tier_used="nanobanana_flash",
                final_prompt=prompt, iterations=iterations,
                final_summary=verdict_payload.get("summary",
                    "halted before charging Phase B review"),
                review_costs_usd=review_cost_total,
                generation_costs_usd=gen_cost_total,
            )
        budget.charge(kind="review", provider="haiku", cost_usd=review_cost)
        record_cost_event(cwd=cwd, kind="review", provider="haiku",
                           cost_usd=review_cost,
                           slide_index=request.slide_index,
                           marker_id=request.marker_id)
        review_cost_total += review_cost
        last_summary = verdict_payload.get("summary", "")
        last_reviewer_feedback = verdict_payload
        if verdict_payload.get("verdict") == "pass":
            # Optional Phase C — Pro single-shot when Flash converged on a proven prompt
            pro_model = "gemini-3-pro-image-preview"
            pro_cost = 0.134
            if budget.can_afford(pro_cost):
                gen_payload = cloud_generate(request, pro_model, 1)
                gen_cost = float(gen_payload.get("cost_usd", pro_cost))
                budget.charge(kind="generation", provider="nanobanana_pro", cost_usd=gen_cost)
                record_cost_event(cwd=cwd, kind="generation", provider="nanobanana_pro",
                                   cost_usd=gen_cost,
                                   slide_index=request.slide_index,
                                   marker_id=request.marker_id)
                gen_cost_total += gen_cost
                # Pro gets ONE shot — no re-review-and-refine.
                # Caveat #6 — review charge MUST be unconditional. If we cannot
                # afford the Pro review, the Flash version is the final accepted
                # output and we report halted_budget on the review (Pro generation
                # already happened).
                pro_verdict = review(request, request.output_path, last_summary)
                pro_review_cost = float(pro_verdict.get("cost_usd", 0.0))
                if not budget.can_afford(pro_review_cost):
                    return ImageGenerationResult(
                        status="halted_budget", tier_used="nanobanana_pro",
                        final_prompt=prompt, iterations=iterations + 1,
                        final_summary=pro_verdict.get("summary",
                            "halted before charging Pro review"),
                        review_costs_usd=review_cost_total,
                        generation_costs_usd=gen_cost_total,
                    )
                budget.charge(kind="review", provider="haiku", cost_usd=pro_review_cost)
                record_cost_event(cwd=cwd, kind="review", provider="haiku",
                                   cost_usd=pro_review_cost,
                                   slide_index=request.slide_index,
                                   marker_id=request.marker_id)
                review_cost_total += pro_review_cost
                return ImageGenerationResult(
                    status="pass", tier_used="nanobanana_pro",
                    final_prompt=prompt, iterations=iterations + 1,
                    final_summary=pro_verdict.get("summary", last_summary),
                    review_costs_usd=review_cost_total,
                    generation_costs_usd=gen_cost_total,
                )
            return ImageGenerationResult(
                status="pass", tier_used="nanobanana_flash",
                final_prompt=prompt, iterations=iterations,
                final_summary=last_summary,
                review_costs_usd=review_cost_total,
                generation_costs_usd=gen_cost_total,
            )
        prompt = refine_prompt(request, prompt, last_reviewer_feedback, flash_attempt)
        request.prompt = prompt

    return ImageGenerationResult(
        status="accepted_with_issues", tier_used="nanobanana_flash",
        final_prompt=prompt, iterations=iterations,
        final_summary=last_summary,
        review_costs_usd=review_cost_total,
        generation_costs_usd=gen_cost_total,
    )
