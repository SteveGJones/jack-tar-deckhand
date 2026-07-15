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

try:
    from .model_catalog import get_catalog as _get_model_catalog
except ImportError:  # pragma: no cover - direct-script execution path
    from model_catalog import get_catalog as _get_model_catalog

_catalog = _get_model_catalog()

# Cost per router-facing model key (USD), derived from the model catalog
# (EPIC #125). This table previously drifted from the cloud plugin's
# pricing — it carried a fourth divergent FLUX-2-Pro figure ($0.050 flat)
# and retired gpt-image-1-mini ids. Deriving from the catalog makes that
# drift structurally impossible; the short keys stay because the router
# and manifests use them.
MODEL_COSTS = {
    # OpenAI (1024x1024 reference size per quality tier)
    'gpt-image-1.5-low': _catalog.cost('gpt-image-1.5', size='1024x1024', quality='low'),
    'gpt-image-1.5-medium': _catalog.cost('gpt-image-1.5', size='1024x1024', quality='medium'),
    'gpt-image-1.5-high': _catalog.cost('gpt-image-1.5', size='1024x1024', quality='high'),
    # Google Imagen (1K; Developer-API backend as the conservative rate)
    'imagen-4-fast': _catalog.cost('imagen-4-fast', resolution='1K', backend='developer'),
    'imagen-4-standard': _catalog.cost('imagen-4-standard', resolution='1K', backend='developer'),
    # FAL.ai — typical deck slide is 1920x1080 (~2.07 MP) on tiered pricing
    'flux-2-pro': round(_catalog.cost('flux-2-pro', megapixels=2.0736), 3),
    'ideogram-3': _catalog.cost('ideogram-3'),
    # Recraft: svg = icon tier rate; png = raster standard 1K
    'recraft-v4-svg': _catalog.cost('recraft-v4-svg', tier='standard'),
    'recraft-v4-png': _catalog.cost('recraft-v4-standard', resolution='1K'),
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
