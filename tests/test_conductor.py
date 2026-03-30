"""Tests for deck-conductor pipeline utilities."""

import json
import os
import shutil
import pytest

from src.conductor import (
    init_pipeline,
    get_pipeline_state,
    set_phase,
    advance_draft_cycle,
    increment_qa_cycle,
    can_correct,
    save_budget_snapshot,
    load_budget_tracker,
    save_provider_snapshot,
    log_speaker_approval,
    has_draft_approval,
    pipeline_summary_markdown,
)
from src.budget_tracker import BudgetTracker

TEST_DECK_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'test-conductor')


@pytest.fixture(autouse=True)
def clean_deck_dir():
    os.makedirs(TEST_DECK_DIR, exist_ok=True)
    yield
    if os.path.exists(TEST_DECK_DIR):
        shutil.rmtree(TEST_DECK_DIR)


class TestInitPipeline:
    def test_creates_pipeline_state(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        state = get_pipeline_state(TEST_DECK_DIR)
        assert state is not None
        assert state['phase'] == 'draft'
        assert state['draft_cycle'] == 0
        assert state['qa_correction_cycle'] == 0
        assert state['status'] == 'running'

    def test_initialises_budget(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=10.0)
        state = get_pipeline_state(TEST_DECK_DIR)
        assert state['budget']['total_budget_usd'] == 10.0
        assert state['budget']['spent_usd'] == 0.0

    def test_initialises_step_order(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        state = get_pipeline_state(TEST_DECK_DIR)
        assert 'brand-manager' in state['step_order']
        assert 'deck-qa' in state['step_order']


class TestPhaseManagement:
    def test_set_phase_to_production(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        set_phase(TEST_DECK_DIR, 'production')
        state = get_pipeline_state(TEST_DECK_DIR)
        assert state['phase'] == 'production'

    def test_advance_draft_cycle(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        advance_draft_cycle(TEST_DECK_DIR)
        state = get_pipeline_state(TEST_DECK_DIR)
        assert state['draft_cycle'] == 1
        assert state['qa_correction_cycle'] == 0

    def test_advance_resets_step_statuses(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        state = get_pipeline_state(TEST_DECK_DIR)
        state['steps']['brand-manager']['status'] = 'completed'
        with open(os.path.join(TEST_DECK_DIR, 'pipeline-state.json'), 'w') as f:
            json.dump(state, f)
        advance_draft_cycle(TEST_DECK_DIR)
        state = get_pipeline_state(TEST_DECK_DIR)
        assert state['steps']['brand-manager']['status'] == 'pending'


class TestQACycles:
    def test_can_correct_initially(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        assert can_correct(TEST_DECK_DIR) is True

    def test_increment_qa_cycle(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        count = increment_qa_cycle(TEST_DECK_DIR)
        assert count == 1
        assert can_correct(TEST_DECK_DIR) is True

    def test_cannot_correct_after_max(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        increment_qa_cycle(TEST_DECK_DIR)
        increment_qa_cycle(TEST_DECK_DIR)
        assert can_correct(TEST_DECK_DIR) is False

    def test_increment_raises_at_max(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        increment_qa_cycle(TEST_DECK_DIR)
        increment_qa_cycle(TEST_DECK_DIR)
        with pytest.raises(ValueError):
            increment_qa_cycle(TEST_DECK_DIR)


class TestBudgetPersistence:
    def test_save_and_load_budget(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=10.0)
        tracker = BudgetTracker(10.0)
        tracker.log_api_call('gpt-image-1.5-low', 0.009, 'test-img-1')
        save_budget_snapshot(TEST_DECK_DIR, tracker)
        loaded = load_budget_tracker(TEST_DECK_DIR)
        assert loaded.spent == pytest.approx(0.009, abs=0.001)
        assert loaded._total_budget_usd == 10.0

    def test_budget_state_preserved(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=10.0)
        tracker = BudgetTracker(10.0)
        save_budget_snapshot(TEST_DECK_DIR, tracker)
        state = get_pipeline_state(TEST_DECK_DIR)
        assert state['budget']['budget_state'] == 'allow'


class TestProviderSnapshot:
    def test_save_providers(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        providers = {'ollama': {'available': True}, 'openai': {'available': False}}
        save_provider_snapshot(TEST_DECK_DIR, providers)
        state = get_pipeline_state(TEST_DECK_DIR)
        assert state['available_providers']['ollama']['available'] is True
        assert state['available_providers']['openai']['available'] is False


class TestSpeakerApprovals:
    def test_log_approval(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        log_speaker_approval(TEST_DECK_DIR, 'budget_confirmed', '$5 budget approved')
        state = get_pipeline_state(TEST_DECK_DIR)
        assert len(state['speaker_approvals']) == 1
        assert state['speaker_approvals'][0]['decision'] == 'budget_confirmed'

    def test_has_draft_approval_false(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        assert has_draft_approval(TEST_DECK_DIR) is False

    def test_has_draft_approval_true(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        log_speaker_approval(TEST_DECK_DIR, 'draft_approved', 'Looks good')
        assert has_draft_approval(TEST_DECK_DIR) is True

    def test_multiple_approvals(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        log_speaker_approval(TEST_DECK_DIR, 'budget_confirmed', 'OK')
        log_speaker_approval(TEST_DECK_DIR, 'providers_confirmed', 'OK')
        state = get_pipeline_state(TEST_DECK_DIR)
        assert len(state['speaker_approvals']) == 2


class TestSummary:
    def test_produces_markdown(self):
        init_pipeline(TEST_DECK_DIR, budget_usd=5.0)
        md = pipeline_summary_markdown(TEST_DECK_DIR)
        assert '## Pipeline Status' in md
        assert 'draft' in md.lower()
        assert 'brand-manager' in md

    def test_get_nonexistent_returns_none(self):
        result = get_pipeline_state('/nonexistent/path')
        assert result is None
