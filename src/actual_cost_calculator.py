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
