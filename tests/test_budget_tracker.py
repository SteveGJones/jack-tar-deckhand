"""Tests for budget tracker module."""

import pytest


class TestBudgetState:
    def test_initial_state_is_allow(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=2.00)
        assert bt.state == 'allow'
        assert bt.spent == 0.0
        assert bt.remaining == 2.00
        assert bt.utilisation == 0.0

    def test_allow_under_70_percent(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=1.00)
        bt.log_api_call('imagen-4-fast', 0.69, 'img-1')
        assert bt.state == 'allow'

    def test_allow_with_caps_at_70_percent(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=1.00)
        bt.log_api_call('flux-2-pro', 0.71, 'img-1')
        assert bt.state == 'allow_with_caps'

    def test_degrade_at_90_percent(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=1.00)
        bt.log_api_call('gpt-image-1.5-high', 0.91, 'img-1')
        assert bt.state == 'degrade'

    def test_typography_only_at_100_percent(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=1.00)
        bt.log_api_call('gpt-image-1.5-high', 1.01, 'img-1')
        assert bt.state == 'typography_only'

    def test_zero_budget_is_typography_only(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=0.0)
        assert bt.state == 'typography_only'

    def test_negative_remaining_clamped_to_zero(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=1.00)
        bt.log_api_call('test', 1.50, 'img-1')
        assert bt.remaining == 0.0


class TestCanSpend:
    def test_can_spend_within_budget(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=2.00)
        assert bt.can_spend(1.00) is True

    def test_cannot_spend_over_budget(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=1.00)
        bt.log_api_call('test', 0.80, 'img-1')
        assert bt.can_spend(0.50) is False
        assert bt.can_spend(0.20) is True

    def test_can_spend_exact_remainder(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=1.00)
        bt.log_api_call('test', 0.50, 'img-1')
        assert bt.can_spend(0.50) is True


class TestLogging:
    def test_log_api_call_tracks_cost(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=2.00)
        bt.log_api_call('imagen-4-fast', 0.02, 'slide-01-bg')
        bt.log_api_call('recraft-v4-svg', 0.04, 'slide-03-icon')
        assert bt.spent == 0.06
        assert bt.remaining == 1.94

    def test_log_cache_hit(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=2.00)
        bt.log_cache_hit('cache-key-1', 0.04)
        bt.log_cache_hit('cache-key-2', 0.02)
        assert bt.spent == 0.0  # cache hits don't cost money
        assert bt._cache_hits == 2
        assert bt._cache_savings == 0.06


class TestEstimateCost:
    def test_known_model(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=2.00)
        assert bt.estimate_cost('imagen-4-fast') == 0.020
        assert bt.estimate_cost('gpt-image-1.5-high') == 0.133

    def test_unknown_model_returns_zero(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=2.00)
        assert bt.estimate_cost('unknown-model') == 0.0


class TestSerialisation:
    def test_to_dict_has_required_fields(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=2.00)
        bt.log_api_call('imagen-4-fast', 0.02, 'img-1')
        bt.log_cache_hit('key-1', 0.04)
        d = bt.to_dict()
        assert d['total_budget_usd'] == 2.00
        assert d['spent_usd'] == 0.02
        assert d['budget_state'] == 'allow'
        assert len(d['api_calls']) == 1
        assert d['cache_hits'] == 1
        assert d['cache_savings_usd'] == 0.04

    def test_api_call_entry_has_fields(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=2.00)
        bt.log_api_call('imagen-4-fast', 0.02, 'slide-01-bg')
        entry = bt.to_dict()['api_calls'][0]
        assert entry['model'] == 'imagen-4-fast'
        assert entry['cost_usd'] == 0.02
        assert entry['cumulative_usd'] == 0.02
        assert 'timestamp' in entry
        assert entry['image_id'] == 'slide-01-bg'


class TestCostSummary:
    def test_markdown_includes_key_info(self):
        from src.budget_tracker import BudgetTracker
        bt = BudgetTracker(total_budget_usd=2.00)
        bt.log_api_call('imagen-4-fast', 0.02, 'img-1')
        bt.log_api_call('recraft-v4-svg', 0.04, 'img-2')
        bt.log_cache_hit('key-1', 0.04)
        md = bt.cost_summary_markdown()
        assert '$2.00' in md  # budget
        assert '$0.06' in md  # spent
        assert '$1.94' in md  # remaining
        assert 'allow' in md.lower()  # state
        assert '1' in md  # cache hits
