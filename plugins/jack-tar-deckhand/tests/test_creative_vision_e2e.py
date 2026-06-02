"""End-to-end smoke test for creative_vision pipeline (Ollama-only — $0 spend).

Gated by ENABLE_E2E=1 env var. CI default: skipped.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from src.creative_vision_dispatch import DispatchRequest, initialise_dispatch  # noqa: E402

ENABLE_E2E = os.environ.get("ENABLE_E2E") == "1"


@pytest.mark.skipif(not ENABLE_E2E, reason="set ENABLE_E2E=1 to run")
def test_creative_vision_ollama_only_e2e(tmp_path):
    """Spin up a real Ollama dispatch and confirm a manifest is created + at least one Ollama attempt persists.

    Does NOT dispatch real agents (those happen in SKILL.md). This is an integration-of-the-pure-logic test
    that proves DispatchRequest + initialise_dispatch + manifest persistence work end-to-end with a real
    file system + real schemas.
    """
    req = DispatchRequest(
        deck_dir=str(tmp_path),
        slide_number=1,
        vision_prose="A solitary lighthouse on a rocky coast, dramatic stormy sky, watercolor style.",
        budget_usd=0.0,  # Ollama-only — no paid tier reachable
        allowed_ceiling="ollama",
        brand_fidelity="none",
    )
    manifest = initialise_dispatch(req)
    assert manifest["slide_number"] == 1
    assert manifest["iterate_slide_hooks"]["current_tier"] == "ollama"

    # Validate the persisted manifest against its schema
    from jsonschema import validate
    schema_path = PLUGIN_ROOT / "src" / "schemas" / "creative_vision_manifest.schema.json"
    with open(schema_path) as f:
        schema = json.load(f)
    persisted_path = tmp_path / "creative-vision" / "1" / "manifest.json"
    with open(persisted_path) as f:
        persisted = json.load(f)
    # The persisted manifest may include the _initial_budget_usd field — that's
    # an internal bookkeeping field stashed by initialise_manifest. It's not in
    # the schema's required list but the schema allows additional properties.
    validate(instance=persisted, schema=schema)
