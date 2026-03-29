"""Integration test: full DeckContext lifecycle from init to QA report."""

import json
import os
import shutil
import pytest

DECK_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'test-deck-integration')
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.fixture(autouse=True)
def clean_deck_dir():
    if os.path.exists(DECK_DIR):
        shutil.rmtree(DECK_DIR)
    yield
    if os.path.exists(DECK_DIR):
        shutil.rmtree(DECK_DIR)


def load_fixture(name):
    path = os.path.join(FIXTURE_DIR, f'{name}.json')
    with open(path) as f:
        return json.load(f)


def test_full_pipeline_lifecycle():
    """Simulate a complete pipeline run through DeckContext."""
    from src.deckcontext import (
        init_deck, write_contract, read_contract,
        update_step, compute_checksum,
    )

    # 1. Init
    init_deck(DECK_DIR)
    state = read_contract(DECK_DIR, 'pipeline-state')
    assert state['status'] == 'running'

    # 2. Write TalkBrief
    brief = load_fixture('valid_talk_brief')
    write_contract(DECK_DIR, 'talk-brief', brief)
    update_step(DECK_DIR, 'validate-brief', 'completed', output_file='talk-brief.json')

    # 3. Write StyleGuide
    update_step(DECK_DIR, 'slide-stylist', 'running')
    guide = load_fixture('valid_style_guide')
    write_contract(DECK_DIR, 'style-guide', guide)
    update_step(DECK_DIR, 'slide-stylist', 'completed', output_file='style-guide.json')

    # 4. Write SlideOutline
    update_step(DECK_DIR, 'narrative-architect', 'running')
    outline = load_fixture('valid_slide_outline')
    write_contract(DECK_DIR, 'outline', outline)
    update_step(DECK_DIR, 'narrative-architect', 'completed', output_file='outline.json')

    # 5. Write SpeakerNotes
    update_step(DECK_DIR, 'speaker-notes-writer', 'running')
    notes = load_fixture('valid_speaker_notes')
    write_contract(DECK_DIR, 'speaker-notes', notes)
    update_step(DECK_DIR, 'speaker-notes-writer', 'completed', output_file='speaker-notes.json')

    # 6. Write ImageManifest
    update_step(DECK_DIR, 'imagegen-bridge', 'running')
    manifest = load_fixture('valid_image_manifest')
    write_contract(DECK_DIR, 'image-manifest', manifest)
    update_step(DECK_DIR, 'imagegen-bridge', 'completed', output_file='image-manifest.json')

    # 7. Write ChartManifest
    update_step(DECK_DIR, 'chart-renderer', 'running')
    charts = load_fixture('valid_chart_manifest')
    write_contract(DECK_DIR, 'chart-manifest', charts)
    update_step(DECK_DIR, 'chart-renderer', 'completed', output_file='chart-manifest.json')

    # 8. Write QAReport
    update_step(DECK_DIR, 'deck-qa', 'running')
    report = load_fixture('valid_qa_report')
    write_contract(DECK_DIR, 'qa-report', report)
    update_step(DECK_DIR, 'deck-qa', 'completed', output_file='qa-report.json')

    # Verify final state
    final_state = read_contract(DECK_DIR, 'pipeline-state')
    completed_steps = [
        name for name, step in final_state['steps'].items()
        if step.get('status') == 'completed'
    ]
    assert len(completed_steps) == 7

    # Verify all contract files exist and have valid checksums
    expected_files = [
        'talk-brief.json', 'style-guide.json', 'outline.json',
        'speaker-notes.json', 'image-manifest.json',
        'chart-manifest.json', 'qa-report.json', 'pipeline-state.json',
    ]
    for filename in expected_files:
        filepath = os.path.join(DECK_DIR, filename)
        assert os.path.isfile(filepath), f'Missing: {filename}'
        checksum = compute_checksum(filepath)
        assert len(checksum) == 64, f'Invalid checksum for {filename}'

    # Verify each contract can be read back
    assert read_contract(DECK_DIR, 'talk-brief') == brief
    assert read_contract(DECK_DIR, 'style-guide') == guide
    assert read_contract(DECK_DIR, 'outline') == outline
    assert read_contract(DECK_DIR, 'speaker-notes') == notes
    assert read_contract(DECK_DIR, 'image-manifest') == manifest
    assert read_contract(DECK_DIR, 'chart-manifest') == charts
    assert read_contract(DECK_DIR, 'qa-report') == report
