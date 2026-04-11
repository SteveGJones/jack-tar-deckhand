"""Budget tracker — cloud API spend tracking with graceful degradation.

Tracks cumulative cloud API cost per pipeline session. Implements a
4-state budget state machine:
  ALLOW (0-70%)            → Full multi-model routing
  ALLOW_WITH_CAPS (70-90%) → Switch heroes to cheap models, skip decorative images
  DEGRADE (90-100%)        → All remaining images via Ollama (free)
  TYPOGRAPHY_ONLY (100%+)  → No image generation at all

Budget state is persisted to pipeline-state.json via deckcontext.
"""

from datetime import datetime, timezone

# Cost constants per model and quality tier (USD)
MODEL_COSTS = {
    # OpenAI
    'gpt-image-1-mini-low': 0.005,
    'gpt-image-1-mini-medium': 0.007,
    'gpt-image-1.5-low': 0.009,
    'gpt-image-1.5-medium': 0.040,
    'gpt-image-1.5-high': 0.133,
    # Google
    'imagen-4-fast': 0.020,
    'imagen-4-standard': 0.040,
    # FAL.ai
    'flux-2-pro': 0.050,
    'ideogram-3': 0.080,
    # Recraft
    'recraft-v4-svg': 0.040,
    'recraft-v4-png': 0.080,
}

# State thresholds
_THRESHOLD_ALLOW_WITH_CAPS = 0.70
_THRESHOLD_DEGRADE = 0.90
_THRESHOLD_TYPOGRAPHY_ONLY = 1.00


class BudgetTracker:
    """Per-session budget tracker with graceful degradation."""

    def __init__(self, total_budget_usd: float):
        """Initialise with a budget cap in USD."""
        self._total_budget_usd = total_budget_usd
        self._spent: float = 0.0
        self._api_calls: list[dict] = []
        self._cache_hits: int = 0
        self._cache_savings: float = 0.0

    @property
    def spent(self) -> float:
        """Total USD spent so far."""
        return self._spent

    @property
    def remaining(self) -> float:
        """USD remaining, clamped to zero."""
        return max(0.0, self._total_budget_usd - self._spent)

    @property
    def utilisation(self) -> float:
        """Fraction of budget consumed. Returns 1.0 when budget is zero."""
        if self._total_budget_usd == 0.0:
            return 1.0
        return self._spent / self._total_budget_usd

    @property
    def state(self) -> str:
        """Current budget state.

        Returns one of: 'allow', 'allow_with_caps', 'degrade', 'typography_only'.
        """
        u = self.utilisation
        if u >= _THRESHOLD_TYPOGRAPHY_ONLY:
            return 'typography_only'
        if u >= _THRESHOLD_DEGRADE:
            return 'degrade'
        if u >= _THRESHOLD_ALLOW_WITH_CAPS:
            return 'allow_with_caps'
        return 'allow'

    def can_spend(self, amount_usd: float) -> bool:
        """Return True if spending this amount stays within budget."""
        return self._spent + amount_usd <= self._total_budget_usd

    def log_api_call(self, model_key: str, cost_usd: float, image_id: str) -> None:
        """Record a cloud API call and its cost."""
        self._spent += cost_usd
        self._api_calls.append({
            'model': model_key,
            'cost_usd': cost_usd,
            'cumulative_usd': self._spent,
            'image_id': image_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })

    def log_cache_hit(self, cache_key: str, saved_usd: float) -> None:
        """Record a cache hit and the cost it saved."""
        self._cache_hits += 1
        self._cache_savings += saved_usd

    def estimate_cost(self, model_key: str) -> float:
        """Look up estimated cost for a model from MODEL_COSTS.

        Returns 0.0 for unknown models.
        """
        return MODEL_COSTS.get(model_key, 0.0)

    def to_dict(self) -> dict:
        """Serialise budget state for pipeline-state.json."""
        return {
            'total_budget_usd': self._total_budget_usd,
            'spent_usd': self._spent,
            'remaining_usd': self.remaining,
            'utilisation': self.utilisation,
            'budget_state': self.state,
            'api_calls': list(self._api_calls),
            'cache_hits': self._cache_hits,
            'cache_savings_usd': self._cache_savings,
        }

    def cost_summary_markdown(self) -> str:
        """Generate a Markdown cost summary for Speaker review."""
        lines = [
            '## Budget Summary',
            '',
            '| Metric | Value |',
            '|--------|-------|',
            f'| Budget | ${self._total_budget_usd:.2f} |',
            f'| Spent | ${self._spent:.2f} |',
            f'| Remaining | ${self.remaining:.2f} |',
            f'| State | {self.state} |',
            f'| API Calls | {len(self._api_calls)} |',
            f'| Cache Hits | {self._cache_hits} |',
            f'| Cache Savings | ${self._cache_savings:.2f} |',
        ]
        return '\n'.join(lines)
