import pytest
from src.actual_cost_calculator import compute_nano_banana_actual_cost, compute_openai_image_actual_cost


def test_nano_banana_flash_minimal_prompt():
    """A short prompt billed at Flash rates returns expected cost."""
    usage = {
        "prompt_token_count": 100,
        "candidates_token_count": 1290,  # one 1K image at Flash rate
        "total_token_count": 1390,
    }
    cost = compute_nano_banana_actual_cost("gemini-3.1-flash-image-preview", usage)
    # Flash text input $0.50/MTok, image output $60/MTok (per token-pricing-rates.md)
    # 100/1e6 * 0.50 + 1290/1e6 * 60 = 0.00005 + 0.0774 = 0.07745
    assert cost == pytest.approx(0.07745, rel=1e-3)


def test_nano_banana_pro_higher_image_token_rate():
    """Pro charges more per image-output token than Flash."""
    usage = {
        "prompt_token_count": 100,
        "candidates_token_count": 1290,
        "total_token_count": 1390,
    }
    pro_cost = compute_nano_banana_actual_cost("gemini-3-pro-image-preview", usage)
    flash_cost = compute_nano_banana_actual_cost("gemini-3.1-flash-image-preview", usage)
    assert pro_cost > flash_cost


def test_nano_banana_unknown_model_raises():
    usage = {"prompt_token_count": 100, "candidates_token_count": 1290, "total_token_count": 1390}
    with pytest.raises(ValueError, match="Unknown Nano Banana model"):
        compute_nano_banana_actual_cost("gemini-99-fictional", usage)


# ---------------------------------------------------------------------------
# OpenAI gpt-image-1 actual-cost tests
# RATES NOTE: placeholder rates ($5.00/MTok input, $40.00/MTok output) are
# UNVERIFIED_ESTIMATE as of 2026-05-21 — all OpenAI pricing URLs returned
# 403/404 during the spike. Must be re-validated via a live browser session or
# the OpenAI dashboard before Phase 2 production code ships.
# ---------------------------------------------------------------------------

def test_openai_gpt_image_token_based():
    """compute_openai_image_actual_cost returns a positive float for valid usage."""
    usage = {"input_tokens": 100, "output_tokens": 4160, "total_tokens": 4260}
    cost = compute_openai_image_actual_cost("gpt-image-1", usage)
    assert cost > 0


def test_openai_image_unknown_model_raises():
    with pytest.raises(ValueError, match="Unknown OpenAI image model"):
        compute_openai_image_actual_cost(
            "gpt-image-99",
            {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        )
