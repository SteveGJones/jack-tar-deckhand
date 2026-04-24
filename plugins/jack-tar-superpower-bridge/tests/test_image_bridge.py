import pytest

from src.image_bridge import BudgetCap, BudgetExhaustedError


def test_budget_cap_initial_state():
    cap = BudgetCap(usd=1.00)
    assert cap.spent == 0.0
    assert cap.remaining == 1.00
    assert cap.can_afford(0.50) is True


def test_charge_generation_deducts_from_remaining():
    cap = BudgetCap(usd=1.00)
    cap.charge(kind="generation", provider="nanobanana_flash", cost_usd=0.067)
    assert cap.spent == pytest.approx(0.067)
    assert cap.remaining == pytest.approx(0.933)


def test_charge_review_also_deducts():
    """Caveat #6 — budget cap MUST cover image review, not just generation."""
    cap = BudgetCap(usd=1.00)
    cap.charge(kind="generation", provider="nanobanana_flash", cost_usd=0.067)
    cap.charge(kind="review", provider="haiku", cost_usd=0.005)
    assert cap.spent == pytest.approx(0.072)


def test_can_afford_returns_false_when_below_threshold():
    cap = BudgetCap(usd=0.10)
    cap.charge(kind="generation", provider="x", cost_usd=0.05)
    cap.charge(kind="generation", provider="x", cost_usd=0.04)
    assert cap.can_afford(0.02) is False
    assert cap.can_afford(0.005) is True


def test_charge_raises_when_overdraft():
    cap = BudgetCap(usd=0.10)
    with pytest.raises(BudgetExhaustedError, match="exceeds remaining"):
        cap.charge(kind="generation", provider="x", cost_usd=0.20)


def test_charge_invalid_kind_raises():
    cap = BudgetCap(usd=1.00)
    with pytest.raises(ValueError, match="kind"):
        cap.charge(kind="other", provider="x", cost_usd=0.01)


def test_history_records_each_charge():
    cap = BudgetCap(usd=1.00)
    cap.charge(kind="generation", provider="nanobanana_flash", cost_usd=0.067)
    cap.charge(kind="review", provider="haiku", cost_usd=0.005)
    assert len(cap.history) == 2
    assert cap.history[0].kind == "generation"
    assert cap.history[1].kind == "review"
