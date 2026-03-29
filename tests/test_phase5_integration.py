"""End-to-end integration test for Phase 5: Assembly & QA.

Simulates the full pipeline:
1. Set up a DeckContext directory with all required contracts
2. Run deck-assembler to produce a .pptx
3. Run deck-qa to produce a QAReport
4. Validate the QAReport against the JSON schema
5. Verify the presentation-reviewer agent file exists
"""

import json
import os
import shutil
import subprocess
import pytest
from jsonschema import validate

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..')
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures', 'minimal_deck')
TEST_DECK_DIR = os.path.join(PROJECT_ROOT, 'tmp', 'test-phase5-e2e')
SCHEMA_DIR = os.path.join(PROJECT_ROOT, 'src', 'schemas')


@pytest.fixture(autouse=True)
def setup_teardown():
    """Set up test DeckContext and clean up after."""
    if os.path.exists(TEST_DECK_DIR):
        shutil.rmtree(TEST_DECK_DIR)
    os.makedirs(os.path.join(TEST_DECK_DIR, 'images'), exist_ok=True)
    os.makedirs(os.path.join(TEST_DECK_DIR, 'output'), exist_ok=True)
    for fname in os.listdir(FIXTURE_DIR):
        src = os.path.join(FIXTURE_DIR, fname)
        dst = os.path.join(TEST_DECK_DIR, fname)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
    yield
    if os.path.exists(TEST_DECK_DIR):
        shutil.rmtree(TEST_DECK_DIR)


def test_assembler_then_qa_pipeline():
    """Full pipeline: assemble -> QA -> validate report."""
    # Step 1: Assemble
    result = subprocess.run(
        ['node', os.path.join(PROJECT_ROOT, 'src', 'assembler', 'build_deck.js'),
         '--deck-dir', TEST_DECK_DIR],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, f"Assembly failed: {result.stderr}"
    pptx_path = os.path.join(TEST_DECK_DIR, 'output', 'presentation.pptx')
    assert os.path.isfile(pptx_path)

    # Step 2: QA
    from src.qa.run_qa import run_qa
    report = run_qa(pptx_path, TEST_DECK_DIR)

    # Step 3: Validate report structure
    assert report['verdict'] in ('pass', 'pass_with_warnings', 'fail')
    assert 'summary' in report
    assert 'findings' in report
    assert isinstance(report['findings'], list)

    # Step 4: Validate against schema
    schema_path = os.path.join(SCHEMA_DIR, 'qa_report.schema.json')
    if os.path.exists(schema_path):
        with open(schema_path) as f:
            schema = json.load(f)
        validate(instance=report, schema=schema)


def test_presentation_reviewer_agent_exists():
    """The presentation-reviewer agent definition must exist."""
    agent_path = os.path.join(PROJECT_ROOT, '.claude', 'agents', 'presentation-reviewer.md')
    assert os.path.isfile(agent_path), "presentation-reviewer.md not found"
    with open(agent_path) as f:
        content = f.read()
    assert 'Presentation Reviewer' in content
    assert 'advisory' in content.lower() or 'Advisory' in content
    assert 'NEVER modify' in content or 'never modif' in content.lower()
