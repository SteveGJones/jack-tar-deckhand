"""Verify the v1.5.0 canonical model delta from superpower-bridge-personas.md."""
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = REPO_ROOT / ".bsa" / "models" / "jack-tar-deckhand.json"


@pytest.fixture
def model() -> dict:
    return json.loads(MODEL_PATH.read_text())


def test_version_bumped_to_1_5_0(model):
    assert model["modelMetadata"]["version"] == "1.5.0"


def test_bridge_services_l1_present(model):
    services = {s["id"]: s for s in model.get("services", [])}
    assert "bridge-services" in services
    assert services["bridge-services"]["level"] == 1


def test_two_new_l2_personas_present(model):
    services = {s["id"]: s for s in model.get("services", [])}
    assert "bridge-narrative-brief-architect-ai" in services
    assert "bridge-enrichment-cohesion-reviewer-ai" in services


def test_two_new_l2_skills_present(model):
    services = {s["id"]: s for s in model.get("services", [])}
    assert "bridge-narrative-prebrief" in services
    assert "bridge-deck-enrichment" in services


def test_at_least_nine_new_interactions(model):
    interactions = model.get("interactions", [])
    bridge_interactions = [i for i in interactions
                            if "bridge-" in (i.get("source", "") + i.get("target", ""))]
    assert len(bridge_interactions) >= 9


def test_cross_domain_sop_register_entry(model):
    sops = model.get("crossDomainSopRegister", [])
    smartart_injection_entry = [
        s for s in sops if s.get("sopId") == "smartart-injection"
    ]
    assert len(smartart_injection_entry) == 1
    entry = smartart_injection_entry[0]
    assert entry["owner"] == "jack-tar-msft-smartart"
    assert "jack-tar-superpower-bridge" in entry["consumers"]
    assert entry["archetype"] == "Collaborator"
    # Chapter 8 — Cross-Domain SOP entries MUST name a Change Advisory Circle
    # composition + change-trigger so consumer/provider know who reviews changes.
    assert "cac" in entry, "Cross-Domain SOP entry missing CAC composition"
    assert "consumer_rep" in entry["cac"]
    assert "provider_rep" in entry["cac"]
    assert "ai_rm" in entry["cac"]
    assert "changeTrigger" in entry, "Cross-Domain SOP entry missing CAC change trigger"


def test_dependency_register_entries(model):
    deps = model.get("dependencyRegister", [])
    dep_ids = {d.get("id") for d in deps}
    for required in (
        "DEP-BRIDGE-SMARTART-01",
        "DEP-BRIDGE-OLLAMA-01",
        "DEP-BRIDGE-CLOUD-01",
        "DEP-BRIDGE-PPTXGENJS-01",
        "DEP-BRIDGE-PYTHON-PPTX-01",
    ):
        assert required in dep_ids, f"missing dependency register entry {required}"
