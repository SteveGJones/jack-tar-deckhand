"""Compute actual USD cost from API-returned usage metadata.

Pure functions; no I/O, no SDK imports. Token rates are sourced from the
official provider pricing pages — see docs/spikes/2026-05-21-actual-token-pricing/
token-pricing-rates.md for current values and source URLs.
"""

# Source: https://ai.google.dev/gemini-api/docs/pricing (captured 2026-05-21)
_NANO_BANANA_RATES = {
    "gemini-3.1-flash-image-preview": {
        "text_input_per_mtok": 0.50,
        "image_output_per_mtok": 60.00,
    },
    "gemini-3-pro-image-preview": {
        "text_input_per_mtok": 2.00,
        "image_output_per_mtok": 120.00,
    },
}


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


# UNVERIFIED_ESTIMATE — all OpenAI pricing URLs (openai.com/api/pricing/,
# platform.openai.com/docs/pricing, help.openai.com, web.archive.org)
# returned 403/404 during the 2026-05-21 spike. These placeholder rates
# ($5.00/MTok input, $40.00/MTok output) are widely-cited in community
# discussions but have NOT been verified against an authoritative source.
#
# MUST re-validate via a logged-in browser session or the OpenAI dashboard
# (https://platform.openai.com/settings/organization/billing/overview) before
# this function is used in Phase 2 production cost-tracking code.
# See docs/spikes/2026-05-21-actual-token-pricing/token-pricing-rates.md.
_OPENAI_IMAGE_RATES = {
    # UNVERIFIED_ESTIMATE — see module comment above
    "gpt-image-1": {
        "input_per_mtok": 5.00,
        "output_per_mtok": 40.00,
    },
    # UNVERIFIED_ESTIMATE — gpt-image-1.5 rates unknown; sharing gpt-image-1
    # placeholders until verified. These two models may differ in production.
    "gpt-image-1.5": {
        "input_per_mtok": 5.00,
        "output_per_mtok": 40.00,
    },
}


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
