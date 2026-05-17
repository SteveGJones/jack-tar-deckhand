"""Tests for the paperbanana dispatch helper (paperbanana E2).

The helper is the testable boundary around the academic_figure
dispatch — the Skill invocation itself happens from SKILL.md, but
availability detection, args assembly, fallback decisions, and
manifest shape are all covered here with mocked filesystem / env.
"""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

import pytest

from src.paperbanana_dispatch import (  # noqa: E402
    PAPERBANANA_ROOT_ENV,
    PAPERBANANA_SKILL_NAME,
    PaperbananaDispatch,
    build_dispatch_payload,
    build_manifest_entry,
    is_paperbanana_available,
)


# --- Availability detection ---------------------------------------------


def test_availability_override_env_var_present():
    """$PAPERBANANA_ROOT pointing at a valid plugin dir → available."""

    def fake_exists(path: Path) -> bool:
        return str(path).endswith("/paperbanana-dev/.claude-plugin/plugin.json")

    env = {PAPERBANANA_ROOT_ENV: "/opt/paperbanana-dev"}
    assert is_paperbanana_available(env=env, fs_exists=fake_exists) is True


def test_availability_override_env_var_missing_manifest():
    """$PAPERBANANA_ROOT set but plugin.json absent → not available."""

    def fake_exists(_path: Path) -> bool:
        return False

    env = {PAPERBANANA_ROOT_ENV: "/opt/empty"}
    assert is_paperbanana_available(env=env, fs_exists=fake_exists) is False


def test_availability_direct_install_in_claude_plugins():
    """~/.claude/plugins/paperbanana/.claude-plugin/plugin.json → available."""

    def fake_exists(path: Path) -> bool:
        return str(path).endswith(
            "/.claude/plugins/paperbanana/.claude-plugin/plugin.json"
        )

    assert is_paperbanana_available(env={}, fs_exists=fake_exists) is True


def test_availability_no_paperbanana_anywhere():
    """No env override AND no filesystem hit → not available."""

    def fake_exists(_path: Path) -> bool:
        return False

    assert is_paperbanana_available(env={}, fs_exists=fake_exists) is False


# --- Dispatch payload (paperbanana available) ---------------------------


def test_dispatch_payload_when_available_carries_subject_and_palette():
    slide = {
        "slide_number": 7,
        "visual_direction": "Transformer encoder stack with 6 layers",
        "headline": "Attention is all you need",
    }
    style_guide = {
        "palette": {
            "primary": "#006B5E",
            "accent": "#5CDBC0",
            "background": "#F5FBF7",
            "ink": "#0E1513",
        }
    }

    dispatch = build_dispatch_payload(
        slide,
        output_dir="./tmp/deck/images",
        style_guide=style_guide,
        paperbanana_available=True,
    )

    assert dispatch.available is True
    assert dispatch.skill == PAPERBANANA_SKILL_NAME
    assert dispatch.args["subject"] == "Transformer encoder stack with 6 layers"
    assert dispatch.args["slide_number"] == 7
    assert dispatch.args["palette_hex"] == [
        "#006B5E",
        "#5CDBC0",
        "#F5FBF7",
        "#0E1513",
    ]
    assert dispatch.output_path.endswith("slide-07-academic-fig.png")


def test_dispatch_payload_uses_headline_when_visual_direction_missing():
    slide = {
        "slide_number": 3,
        "headline": "Confusion matrix for the ResNet50 classifier",
    }
    dispatch = build_dispatch_payload(
        slide,
        output_dir="./tmp/deck/images",
        paperbanana_available=True,
    )
    assert (
        dispatch.args["subject"]
        == "Confusion matrix for the ResNet50 classifier"
    )


def test_dispatch_payload_falls_through_to_body_points():
    slide = {
        "slide_number": 4,
        "body_points": ["Ablation: -head", "Ablation: -ffn", "Ablation: -norm"],
    }
    dispatch = build_dispatch_payload(
        slide,
        output_dir="./tmp/deck/images",
        paperbanana_available=True,
    )
    assert "Ablation: -head" in dispatch.args["subject"]
    assert "·" in dispatch.args["subject"]  # joiner


def test_dispatch_payload_no_palette_when_style_guide_missing():
    slide = {"slide_number": 1, "visual_direction": "Loss landscape"}
    dispatch = build_dispatch_payload(
        slide,
        output_dir="./tmp/deck/images",
        paperbanana_available=True,
    )
    assert "palette_hex" not in dispatch.args


# --- Dispatch payload (paperbanana NOT available — fallback) ------------


def test_dispatch_payload_when_unavailable_populates_fallback():
    slide = {"slide_number": 9, "visual_direction": "Receiver operating curve"}
    dispatch = build_dispatch_payload(
        slide,
        output_dir="./tmp/deck/images",
        paperbanana_available=False,
    )

    assert dispatch.available is False
    assert dispatch.skill == ""
    assert dispatch.args == {}
    assert dispatch.fallback_provider == "google"
    assert dispatch.fallback_model == "gemini-3.1-flash-image-preview"
    assert "paperbanana plugin not detected" in dispatch.fallback_reason
    assert dispatch.output_path.endswith("slide-09-academic-fig.png")


def test_dispatch_payload_detects_availability_when_not_provided():
    """When paperbanana_available is None, fall back to is_paperbanana_available."""

    def fake_exists(_path: Path) -> bool:
        return False  # nothing present anywhere

    dispatch = build_dispatch_payload(
        {"slide_number": 2, "visual_direction": "x"},
        output_dir="./tmp/deck/images",
        availability_env={},
        fs_exists=fake_exists,
    )
    assert dispatch.available is False


# --- Manifest entry shape -----------------------------------------------


def test_manifest_entry_for_successful_paperbanana_render():
    dispatch = build_dispatch_payload(
        {"slide_number": 5, "visual_direction": "Latent space PCA"},
        output_dir="./tmp/deck/images",
        paperbanana_available=True,
    )
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=True,
        content_hash="abc123",
    )
    assert entry["slide_number"] == 5
    assert entry["status"] == "generated"
    assert entry["backend"] == "paperbanana"
    assert entry["model_used"] == PAPERBANANA_SKILL_NAME
    assert entry["source_prompt"] == "Latent space PCA"
    assert entry["content_hash"] == "abc123"
    assert "fallback_reason" not in entry


def test_manifest_entry_for_fallback_cloud_render():
    dispatch = build_dispatch_payload(
        {"slide_number": 6, "visual_direction": "Training loss curves"},
        output_dir="./tmp/deck/images",
        paperbanana_available=False,
    )
    entry = build_manifest_entry(dispatch, dispatch_succeeded=True)
    assert entry["backend"] == "cloud_fallback"
    assert entry["model_used"] == "gemini-3.1-flash-image-preview"
    assert "fallback_reason" in entry
    assert "paperbanana plugin not detected" in entry["fallback_reason"]


def test_manifest_entry_failed_dispatch_records_error():
    dispatch = build_dispatch_payload(
        {"slide_number": 8, "visual_direction": "Edge case"},
        output_dir="./tmp/deck/images",
        paperbanana_available=True,
    )
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=False,
        error="paperbanana raised TimeoutError after 120s",
    )
    assert entry["status"] == "failed"
    assert entry["error"] == "paperbanana raised TimeoutError after 120s"


# --- Integration with classifier (smoke) --------------------------------


def test_dispatch_dataclass_default_fallback_values():
    """Dataclass defaults survive a roundtrip with no overrides."""
    dispatch = PaperbananaDispatch(
        available=False,
        slide_number=1,
        output_path="./out.png",
    )
    assert dispatch.fallback_provider == "google"
    assert dispatch.fallback_model == "gemini-3.1-flash-image-preview"
    assert dispatch.args == {}


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
