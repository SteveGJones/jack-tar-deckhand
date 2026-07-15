"""Compute actual USD cost from API-returned usage metadata.

Pure functions; no I/O, no SDK imports. Token rates come from the model
catalog's ``pricing.token_rates`` (EPIC #125) — provenance and source URLs
live in the catalog entry notes and
docs/spikes/2026-05-21-actual-token-pricing/token-pricing-rates.md.
"""

try:
    from .model_catalog import get_catalog as _get_model_catalog
except ImportError:  # pragma: no cover - direct-script execution path
    from model_catalog import get_catalog as _get_model_catalog


def _rates_by_name(provider, api=None):
    """Token-rate table keyed by every id AND alias of matching entries."""
    table = {}
    for entry in _get_model_catalog().entries(role='image_gen', provider=provider):
        if api and (entry.get('sdk') or {}).get('api') != api:
            continue
        rates = (entry.get('pricing') or {}).get('token_rates')
        if not rates:
            continue
        for name in [entry['id'], *entry.get('aliases', [])]:
            table[name] = dict(rates)
    return table


_NANO_BANANA_RATES = _rates_by_name('google', api='generate_content')


def compute_nano_banana_actual_cost(model: str, usage: dict) -> float:
    """Compute actual cost for a Nano Banana image generation call.

    Args:
        model: Gemini image model name.
        usage: Verbatim usage_metadata dict from the API response with keys
            'prompt_token_count', 'candidates_token_count', 'total_token_count'.

    Returns:
        Cost in USD.

    Raises:
        ValueError: If the model has no rate entry.
    """
    if model not in _NANO_BANANA_RATES:
        raise ValueError(f"Unknown Nano Banana model: {model}")
    rates = _NANO_BANANA_RATES[model]
    text_cost = usage["prompt_token_count"] / 1_000_000 * rates["text_input_per_mtok"]
    image_cost = usage["candidates_token_count"] / 1_000_000 * rates["image_output_per_mtok"]
    return text_cost + image_cost


# UNVERIFIED_ESTIMATE — the OpenAI token rates in the catalog are
# community-cited placeholders; every OpenAI pricing URL 403/404'd during
# the 2026-05-21 spike. The catalog entry's pricing notes carry the flag;
# re-validate via the OpenAI dashboard before production cost-tracking.
# See docs/spikes/2026-05-21-actual-token-pricing/token-pricing-rates.md.
_OPENAI_IMAGE_RATES = _rates_by_name('openai')


def compute_openai_image_actual_cost(model: str, usage: dict) -> float:
    """Compute actual cost for an OpenAI image generation call.

    Args:
        model: OpenAI image model name (e.g. 'gpt-image-1', 'gpt-image-1.5').
        usage: Verbatim usage dict from response.usage with keys
            'input_tokens', 'output_tokens', 'total_tokens'.

    Returns:
        Cost in USD.

    Raises:
        ValueError: If the model has no rate entry.

    Warning:
        Rates in _OPENAI_IMAGE_RATES are UNVERIFIED_ESTIMATE as of 2026-05-21.
        See token-pricing-rates.md and the module-level comment above
        _OPENAI_IMAGE_RATES before relying on these values for production billing.
    """
    if model not in _OPENAI_IMAGE_RATES:
        raise ValueError(f"Unknown OpenAI image model: {model}")
    rates = _OPENAI_IMAGE_RATES[model]
    input_cost = usage["input_tokens"] / 1_000_000 * rates["input_per_mtok"]
    output_cost = usage["output_tokens"] / 1_000_000 * rates["output_per_mtok"]
    return input_cost + output_cost
