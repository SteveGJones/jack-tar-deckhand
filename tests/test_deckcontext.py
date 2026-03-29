"""Tests for DeckContext directory and state management."""

import json
import os
import shutil
import pytest

DECK_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'test-deck')


@pytest.fixture(autouse=True)
def clean_deck_dir():
    """Remove and recreate test deck directory for each test."""
    if os.path.exists(DECK_DIR):
        shutil.rmtree(DECK_DIR)
    yield
    if os.path.exists(DECK_DIR):
        shutil.rmtree(DECK_DIR)


class TestInit:
    def test_init_creates_directory_structure(self):
        from src.deckcontext import init_deck
        init_deck(DECK_DIR)
        assert os.path.isdir(DECK_DIR)
        assert os.path.isdir(os.path.join(DECK_DIR, 'images'))
        assert os.path.isdir(os.path.join(DECK_DIR, 'output'))

    def test_init_creates_pipeline_state(self):
        from src.deckcontext import init_deck
        init_deck(DECK_DIR)
        state_path = os.path.join(DECK_DIR, 'pipeline-state.json')
        assert os.path.isfile(state_path)
        with open(state_path) as f:
            state = json.load(f)
        assert state['status'] == 'running'
        assert 'steps' in state

    def test_init_is_idempotent(self):
        from src.deckcontext import init_deck
        init_deck(DECK_DIR)
        marker = os.path.join(DECK_DIR, 'images', 'test.txt')
        with open(marker, 'w') as f:
            f.write('keep me')
        init_deck(DECK_DIR)
        assert os.path.isfile(marker)


class TestReadWrite:
    def test_write_and_read_contract(self):
        from src.deckcontext import init_deck, write_contract, read_contract
        init_deck(DECK_DIR)
        brief = {"topic": "Test Talk", "audience": "Testers", "duration_minutes": 30}
        write_contract(DECK_DIR, 'talk-brief', brief)
        loaded = read_contract(DECK_DIR, 'talk-brief')
        assert loaded == brief

    def test_write_validates_against_schema(self):
        from src.deckcontext import init_deck, write_contract
        from jsonschema import ValidationError
        init_deck(DECK_DIR)
        invalid = {"audience": "Testers"}
        with pytest.raises(ValidationError):
            write_contract(DECK_DIR, 'talk-brief', invalid)

    def test_read_nonexistent_returns_none(self):
        from src.deckcontext import init_deck, read_contract
        init_deck(DECK_DIR)
        result = read_contract(DECK_DIR, 'talk-brief')
        assert result is None

    def test_write_skips_validation_when_no_schema(self):
        from src.deckcontext import init_deck, write_contract, read_contract
        init_deck(DECK_DIR)
        data = {"custom": "data"}
        write_contract(DECK_DIR, 'custom-data', data, validate=False)
        assert read_contract(DECK_DIR, 'custom-data') == data


class TestChecksum:
    def test_compute_file_checksum(self):
        from src.deckcontext import init_deck, write_contract, compute_checksum
        init_deck(DECK_DIR)
        brief = {"topic": "Test Talk", "audience": "Testers", "duration_minutes": 30}
        write_contract(DECK_DIR, 'talk-brief', brief)
        checksum = compute_checksum(os.path.join(DECK_DIR, 'talk-brief.json'))
        assert len(checksum) == 64
        checksum2 = compute_checksum(os.path.join(DECK_DIR, 'talk-brief.json'))
        assert checksum == checksum2


class TestPipelineState:
    def test_update_step_status(self):
        from src.deckcontext import init_deck, update_step, read_contract
        init_deck(DECK_DIR)
        update_step(DECK_DIR, 'slide-stylist', 'running')
        state = read_contract(DECK_DIR, 'pipeline-state')
        assert state['steps']['slide-stylist']['status'] == 'running'
        assert state['current_step'] == 'slide-stylist'

    def test_complete_step(self):
        from src.deckcontext import init_deck, update_step, read_contract
        init_deck(DECK_DIR)
        update_step(DECK_DIR, 'slide-stylist', 'running')
        update_step(DECK_DIR, 'slide-stylist', 'completed',
                    output_file='style-guide.json')
        state = read_contract(DECK_DIR, 'pipeline-state')
        step = state['steps']['slide-stylist']
        assert step['status'] == 'completed'
        assert step['output_file'] == 'style-guide.json'
        assert 'completed_at' in step
