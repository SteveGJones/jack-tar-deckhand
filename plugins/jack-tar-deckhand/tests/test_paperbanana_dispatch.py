"""Tests for the paperbanana dispatch helper.

The helper is the testable boundary around the academic_figure dispatch
— the CLI subprocess invocation itself happens from SKILL.md, but
availability detection, args assembly, source_context synthesis,
fallback decisions, manifest shape, and run_id extraction are all pure
Python and covered here.

Paperbanana is treated as an external CLI tool (sibling orchestrator),
not a Claude Code plugin. See
``docs/architecture/paperbanana-integration-v2.md`` for the full
framing rationale.
"""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

import pytest

from src.paperbanana_dispatch import (  # noqa: E402
    PaperbananaDispatch,
    _build_caption_from_slide,
    _build_source_context_from_slide,
    _extract_run_id,
    build_dispatch_payload,
    build_manifest_entry,
    is_paperbanana_available,
)


# --- is_paperbanana_available --------------------------------------------


def test_available_via_find_spec(monkeypatch):
    """Module importable in the active venv → available."""
    import importlib.util as _ilu
    import shutil as _sh

    monkeypatch.setattr(
        _ilu, "find_spec", lambda name: object() if name == "paperbanana" else None
    )
    monkeypatch.setattr(_sh, "which", lambda _name: None)
    assert is_paperbanana_available() is True


def test_available_via_shutil_which(monkeypatch):
    """CLI on PATH but package not importable → available (pipx case)."""
    import importlib.util as _ilu
    import shutil as _sh

    monkeypatch.setattr(_ilu, "find_spec", lambda _name: None)
    monkeypatch.setattr(
        _sh,
        "which",
        lambda name: "/usr/local/bin/paperbanana" if name == "paperbanana" else None,
    )
    assert is_paperbanana_available() is True


def test_not_available_neither_route(monkeypatch):
    """Neither find_spec nor which find paperbanana → not available."""
    import importlib.util as _ilu
    import shutil as _sh

    monkeypatch.setattr(_ilu, "find_spec", lambda _name: None)
    monkeypatch.setattr(_sh, "which", lambda _name: None)
    assert is_paperbanana_available() is False


def test_find_spec_short_circuits_before_which(monkeypatch):
    """find_spec True → which is never called (no need to)."""
    import importlib.util as _ilu
    import shutil as _sh

    monkeypatch.setattr(_ilu, "find_spec", lambda _name: object())
    sentinel = {"called": False}

    def fake_which(_name):
        sentinel["called"] = True
        return "/should/not/be/reached"

    monkeypatch.setattr(_sh, "which", fake_which)
    is_paperbanana_available()
    assert sentinel["called"] is False, "which should not be called when find_spec succeeds"


# --- _build_source_context_from_slide ------------------------------------


def test_source_context_uses_explicit_methodology_context():
    """methodology_context (operator pre-annotation) wins over all else."""
    slide = {
        "methodology_context": "Explicit paper-style methodology paragraph.",
        "speaker_notes": "ignored even though substantial " * 20,
        "headline": "ignored",
        "body_points": ["ignored"],
    }
    assert (
        _build_source_context_from_slide(slide)
        == "Explicit paper-style methodology paragraph."
    )


def test_source_context_uses_speaker_notes_when_substantial():
    """speaker_notes ≥200 chars beat body_points + visual_direction."""
    notes = "This is paragraph-length speaker notes. " * 6  # ≈240 chars
    slide = {
        "speaker_notes": notes,
        "body_points": ["ignored bullet"],
        "visual_direction": "ignored direction",
    }
    assert _build_source_context_from_slide(slide) == notes.strip()


def test_source_context_ignores_thin_speaker_notes():
    """speaker_notes <200 chars fall through to body_points synthesis."""
    slide = {
        "speaker_notes": "Too short.",
        "body_points": ["Component A", "Component B"],
        "visual_direction": "System architecture diagram",
    }
    result = _build_source_context_from_slide(slide)
    assert "Too short" not in result
    assert "Component A" in result
    assert "System architecture" in result


def test_source_context_joins_body_points_and_visual_direction():
    """visual_direction + body_points → prose synthesis."""
    slide = {
        "visual_direction": "Encoder-decoder Transformer with 6 layers",
        "body_points": [
            "Multi-head attention (8 heads)",
            "Position-wise feed-forward (dim 2048)",
            "Sinusoidal positional encoding",
        ],
    }
    result = _build_source_context_from_slide(slide)
    assert "Encoder-decoder Transformer with 6 layers" in result
    assert "Multi-head attention" in result
    assert "Position-wise feed-forward" in result
    assert "positional encoding" in result.lower()
    assert result.endswith(".")


def test_source_context_falls_back_to_headline_when_thin():
    """When only a headline exists, use it (thin but graceful)."""
    slide = {"headline": "Loss curve over 100 epochs"}
    assert _build_source_context_from_slide(slide) == "Loss curve over 100 epochs"


def test_source_context_falls_back_to_title_when_no_headline():
    slide = {"title": "Confusion matrix"}
    assert _build_source_context_from_slide(slide) == "Confusion matrix"


def test_source_context_empty_when_slide_carries_nothing():
    """No content fields → empty string (caller decides whether to dispatch)."""
    assert _build_source_context_from_slide({"slide_number": 1}) == ""


def test_source_context_strips_whitespace():
    slide = {"methodology_context": "  padded paragraph  "}
    assert _build_source_context_from_slide(slide) == "padded paragraph"


# --- _build_caption_from_slide -------------------------------------------


def test_caption_explicit_field_wins():
    slide = {
        "caption": "Figure 3: ResNet50 attention maps",
        "headline": "ignored",
        "title": "ignored",
    }
    assert _build_caption_from_slide(slide) == "Figure 3: ResNet50 attention maps"


def test_caption_falls_back_to_headline():
    slide = {"headline": "Attention is all you need"}
    assert _build_caption_from_slide(slide) == "Attention is all you need"


def test_caption_falls_back_to_title():
    slide = {"title": "ResNet50 baseline results"}
    assert _build_caption_from_slide(slide) == "ResNet50 baseline results"


def test_caption_falls_back_to_first_body_point():
    slide = {"body_points": ["First bullet", "Second bullet"]}
    assert _build_caption_from_slide(slide) == "First bullet"


def test_caption_empty_when_slide_carries_nothing():
    assert _build_caption_from_slide({"slide_number": 1}) == ""


# --- _extract_run_id -----------------------------------------------------


def test_extract_run_id_from_png_path():
    path = "/tmp/deck/images/run_20260518_120000_def95c/final_output.png"
    assert _extract_run_id(path) == "run_20260518_120000_def95c"


def test_extract_run_id_from_mcp_jpg_path():
    """MCP transport re-compresses PNGs >3.75MB to .mcp.jpg — run_id still extractable."""
    path = "/tmp/deck/images/run_20260518_120000_def95c/final_output.mcp.jpg"
    assert _extract_run_id(path) == "run_20260518_120000_def95c"


def test_extract_run_id_returns_empty_for_non_paperbanana_path():
    """Cloud fallback paths have no run_id."""
    assert _extract_run_id("/tmp/deck/images/slide-07-academic-figure.png") == ""


def test_extract_run_id_returns_empty_for_empty_string():
    assert _extract_run_id("") == ""


def test_extract_run_id_returns_empty_for_garbled_run_format():
    """Don't false-match strings that look run-ish but aren't paperbanana's format."""
    # Missing the short-hash suffix
    assert _extract_run_id("/foo/run_20260518_120000/final.png") == ""
    # Date wrong length
    assert _extract_run_id("/foo/run_2026_120000_abc/final.png") == ""


# --- build_dispatch_payload (paperbanana available) ----------------------


def test_dispatch_payload_when_available_has_four_key_args():
    """Args dict must match paperbanana's real contract exactly."""
    slide = {
        "slide_number": 7,
        "headline": "Transformer encoder architecture",
        "methodology_context": "We propose a 6-layer Transformer encoder.",
    }
    dispatch = build_dispatch_payload(
        slide,
        output_dir="/tmp/deck/images",
        paperbanana_available=True,
    )
    assert dispatch.available is True
    assert sorted(dispatch.args.keys()) == [
        "aspect_ratio",
        "caption",
        "iterations",
        "source_context",
    ]


def test_dispatch_payload_carries_synthesised_source_context_and_caption():
    slide = {
        "slide_number": 7,
        "headline": "Loss curve",
        "methodology_context": "Training loss decreases from 2.3 to 0.7 over 100 epochs.",
    }
    dispatch = build_dispatch_payload(
        slide,
        output_dir="/tmp/x",
        paperbanana_available=True,
    )
    assert dispatch.args["caption"] == "Loss curve"
    assert "Training loss decreases" in dispatch.args["source_context"]


def test_dispatch_payload_hard_codes_aspect_ratio_16_9():
    """v1.4 hard-codes 16:9 to match slide canvas. Future versions may flex."""
    dispatch = build_dispatch_payload(
        {"slide_number": 1, "headline": "x"},
        output_dir="/tmp/x",
        paperbanana_available=True,
    )
    assert dispatch.args["aspect_ratio"] == "16:9"


def test_dispatch_payload_iterations_defaults_to_1():
    """Cost-control default: 1 iteration per academic_figure slide."""
    dispatch = build_dispatch_payload(
        {"slide_number": 1, "headline": "x"},
        output_dir="/tmp/x",
        paperbanana_available=True,
    )
    assert dispatch.args["iterations"] == 1


def test_dispatch_payload_iterations_honours_slide_override():
    """Speakers opt high-stakes slides up via slide['paperbanana_iterations']."""
    dispatch = build_dispatch_payload(
        {"slide_number": 1, "headline": "x", "paperbanana_iterations": 3},
        output_dir="/tmp/x",
        paperbanana_available=True,
    )
    assert dispatch.args["iterations"] == 3


def test_dispatch_payload_records_output_dir():
    """output_dir (not output_path — paperbanana writes its own subdirectory)."""
    dispatch = build_dispatch_payload(
        {"slide_number": 1, "headline": "x"},
        output_dir="/tmp/deck/images",
        paperbanana_available=True,
    )
    assert dispatch.output_dir == "/tmp/deck/images"


def test_dispatch_payload_records_slide_number_on_struct():
    """slide_number stays on the struct (for manifest accounting), NOT in args."""
    dispatch = build_dispatch_payload(
        {"slide_number": 42, "headline": "x"},
        output_dir="/tmp/x",
        paperbanana_available=True,
    )
    assert dispatch.slide_number == 42
    assert "slide_number" not in dispatch.args


# --- build_dispatch_payload (paperbanana NOT available — fallback) -------


def test_dispatch_payload_when_unavailable_populates_fallback():
    slide = {"slide_number": 9, "headline": "Receiver operating curve"}
    dispatch = build_dispatch_payload(
        slide,
        output_dir="/tmp/deck/images",
        paperbanana_available=False,
    )
    assert dispatch.available is False
    assert dispatch.args == {}
    assert dispatch.fallback_provider == "google"
    assert dispatch.fallback_model == "gemini-3.1-flash-image-preview"
    assert "paperbanana CLI not on PATH" in dispatch.fallback_reason
    assert "pip install" in dispatch.fallback_reason


def test_dispatch_payload_detects_availability_when_not_provided(monkeypatch):
    """When paperbanana_available is None, calls is_paperbanana_available."""
    import importlib.util as _ilu
    import shutil as _sh

    monkeypatch.setattr(_ilu, "find_spec", lambda _name: None)
    monkeypatch.setattr(_sh, "which", lambda _name: None)

    dispatch = build_dispatch_payload(
        {"slide_number": 2, "headline": "x"},
        output_dir="/tmp/x",
    )
    assert dispatch.available is False


def test_dispatch_payload_short_circuits_when_available_provided(monkeypatch):
    """paperbanana_available=True/False bypasses is_paperbanana_available entirely."""
    import importlib.util as _ilu
    import shutil as _sh

    called = {"find_spec": 0, "which": 0}

    def fake_find_spec(_name):
        called["find_spec"] += 1
        return None

    def fake_which(_name):
        called["which"] += 1
        return None

    monkeypatch.setattr(_ilu, "find_spec", fake_find_spec)
    monkeypatch.setattr(_sh, "which", fake_which)

    build_dispatch_payload(
        {"slide_number": 1, "headline": "x"},
        output_dir="/tmp/x",
        paperbanana_available=True,
    )
    assert called == {"find_spec": 0, "which": 0}


# --- build_manifest_entry ------------------------------------------------


def test_manifest_entry_for_successful_paperbanana_render():
    dispatch = build_dispatch_payload(
        {
            "slide_number": 5,
            "headline": "Latent space PCA",
            "methodology_context": "PCA over 1M embeddings.",
        },
        output_dir="/tmp/deck/images",
        paperbanana_available=True,
    )
    real_path = "/tmp/deck/images/run_20260518_120000_def95c/final_output.png"
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=True,
        output_path=real_path,
        content_hash="abc123",
    )
    assert entry["slide_number"] == 5
    assert entry["file_path"] == real_path
    assert entry["status"] == "generated"
    assert entry["image_id"] == "slide-05-academic-figure"
    assert entry["backend"] == "paperbanana"
    assert entry["model_used"] == "paperbanana"
    assert entry["source_prompt"] == "PCA over 1M embeddings."
    assert entry["caption"] == "Latent space PCA"
    assert entry["content_hash"] == "abc123"
    assert entry["paperbanana_run_id"] == "run_20260518_120000_def95c"
    assert entry["paperbanana_args"]["aspect_ratio"] == "16:9"
    assert "fallback_reason" not in entry
    assert "error" not in entry


def test_manifest_entry_accepts_mcp_jpg_path():
    """When MCP re-compresses, file_path captures the .mcp.jpg extension."""
    dispatch = build_dispatch_payload(
        {"slide_number": 5, "headline": "x", "methodology_context": "y"},
        output_dir="/tmp/x",
        paperbanana_available=True,
    )
    mcp_path = "/tmp/x/run_20260518_120000_def95c/final_output.mcp.jpg"
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=True,
        output_path=mcp_path,
        content_hash="def",
    )
    assert entry["file_path"] == mcp_path
    assert entry["paperbanana_run_id"] == "run_20260518_120000_def95c"


def test_manifest_entry_no_run_id_when_path_lacks_pattern():
    """Defensive: if paperbanana wrote somewhere unexpected, manifest has no run_id."""
    dispatch = build_dispatch_payload(
        {"slide_number": 5, "headline": "x", "methodology_context": "y"},
        output_dir="/tmp/x",
        paperbanana_available=True,
    )
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=True,
        output_path="/tmp/x/nonstandard.png",
    )
    assert "paperbanana_run_id" not in entry


def test_manifest_entry_for_fallback_cloud_render():
    dispatch = build_dispatch_payload(
        {"slide_number": 6, "headline": "Training loss curves"},
        output_dir="/tmp/deck/images",
        paperbanana_available=False,
    )
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=True,
        output_path="/tmp/deck/images/slide-06-academic-figure.png",
    )
    assert entry["backend"] == "cloud_fallback"
    assert entry["model_used"] == "gemini-3.1-flash-image-preview"
    assert "fallback_reason" in entry
    assert "paperbanana CLI not on PATH" in entry["fallback_reason"]
    assert "paperbanana_run_id" not in entry
    assert "paperbanana_args" not in entry


def test_manifest_entry_failed_dispatch_records_error():
    dispatch = build_dispatch_payload(
        {"slide_number": 8, "headline": "Edge case", "methodology_context": "y"},
        output_dir="/tmp/x",
        paperbanana_available=True,
    )
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=False,
        output_path="",
        error="paperbanana subprocess exit 1",
    )
    assert entry["status"] == "failed"
    assert entry["error"] == "paperbanana subprocess exit 1"
    assert "content_hash" not in entry


def test_manifest_entry_omits_content_hash_when_none():
    dispatch = build_dispatch_payload(
        {"slide_number": 1, "headline": "x", "methodology_context": "y"},
        output_dir="/tmp/x",
        paperbanana_available=True,
    )
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=True,
        output_path="/tmp/x/run_20260518_120000_abc123/final_output.png",
    )
    assert "content_hash" not in entry


# --- Dataclass defaults --------------------------------------------------


def test_dispatch_dataclass_default_fallback_values():
    """Dataclass defaults survive a roundtrip with no overrides."""
    dispatch = PaperbananaDispatch(
        available=False,
        slide_number=1,
        output_dir="./out",
    )
    assert dispatch.fallback_provider == "google"
    assert dispatch.fallback_model == "gemini-3.1-flash-image-preview"
    assert dispatch.args == {}
    assert dispatch.fallback_reason == ""


# --- Claude-critic path helpers (#113 Path B) -----------------------------

import pytest  # noqa: E402

from src.paperbanana_dispatch import (  # noqa: E402
    build_continue_run_dispatch_args,
    build_initial_dispatch_args_for_claude_critic,
    get_figure_type,
    get_iteration_cap,
    is_claude_critic_path,
    should_log_paperbanana_verdict,
)


def test_is_claude_critic_path_default_false_when_no_academic_figure_block():
    """Legacy slide without academic_figure block → paperbanana-critic path."""
    slide = {"slide_number": 5, "strategy": "academic_figure"}
    assert is_claude_critic_path(slide) is False


def test_is_claude_critic_path_default_false_when_critic_field_omitted():
    """academic_figure block present but no critic field → defaults to paperbanana."""
    slide = {
        "slide_number": 5,
        "strategy": "academic_figure",
        "academic_figure": {"figure_type": "plot"},
    }
    assert is_claude_critic_path(slide) is False


def test_is_claude_critic_path_true_when_critic_claude():
    """Explicit opt-in via critic: claude."""
    slide = {
        "slide_number": 5,
        "strategy": "academic_figure",
        "academic_figure": {"critic": "claude"},
    }
    assert is_claude_critic_path(slide) is True


def test_is_claude_critic_path_false_for_non_academic_figure_strategies():
    """Even with academic_figure block, wrong strategy → False (schema would also reject)."""
    slide = {
        "slide_number": 5,
        "strategy": "composed",
        "academic_figure": {"critic": "claude"},
    }
    assert is_claude_critic_path(slide) is False


def test_build_initial_dispatch_args_for_claude_critic_forces_iterations_1():
    """Iterations MUST be 1 — jack-tar owns the loop, paperbanana does one render per call."""
    slide = {
        "slide_number": 5,
        "strategy": "academic_figure",
        "headline": "Figure 3",
        "visual_direction": "three-block encoder architecture",
        "body_points": ["encoder", "attention", "decoder"],
        "academic_figure": {
            "critic": "claude",
            "iteration_cap": 6,
        },
        # Even if the slide had paperbanana_iterations set high, claude-critic
        # forces 1 — the operator-tunable cap lives in jack-tar's loop, not in
        # paperbanana's internal loop.
        "paperbanana_iterations": 9,
    }
    args = build_initial_dispatch_args_for_claude_critic(slide)
    assert args["iterations"] == 1
    assert "source_context" in args
    assert args["caption"] == "Figure 3"
    assert args["aspect_ratio"] == "16:9"


def test_build_continue_run_dispatch_args_happy_path():
    args = build_continue_run_dispatch_args(
        paperbanana_run_id="run_20260527_120000_abc123",
        feedback="Make the encoder block 30% taller. Add a labelled arrow.",
    )
    assert args["continue_run"] == "run_20260527_120000_abc123"
    assert "encoder block 30% taller" in args["feedback"]
    assert args["iterations"] == 1


def test_build_continue_run_dispatch_args_rejects_empty_run_id():
    with pytest.raises(ValueError, match="paperbanana_run_id"):
        build_continue_run_dispatch_args(paperbanana_run_id="", feedback="x")


def test_build_continue_run_dispatch_args_rejects_whitespace_run_id():
    with pytest.raises(ValueError, match="paperbanana_run_id"):
        build_continue_run_dispatch_args(paperbanana_run_id="   ", feedback="x")


def test_build_continue_run_dispatch_args_rejects_empty_feedback():
    """figure-critic is contractually required to provide non-empty refinement
    feedback on a refine verdict. Empty feedback would mean a corrupt critic
    verdict slipped through; this catch is a belt-and-braces."""
    with pytest.raises(ValueError, match="feedback must be non-empty"):
        build_continue_run_dispatch_args(paperbanana_run_id="run_x", feedback="")


def test_get_iteration_cap_default_4():
    """Default cap matches schema default."""
    assert get_iteration_cap({"academic_figure": {}}) == 4
    assert get_iteration_cap({}) == 4


def test_get_iteration_cap_honours_per_slide_override():
    assert get_iteration_cap({"academic_figure": {"iteration_cap": 7}}) == 7


def test_get_figure_type_default_other():
    assert get_figure_type({"academic_figure": {}}) == "other"
    assert get_figure_type({}) == "other"


def test_get_figure_type_returns_specified_type():
    assert get_figure_type({"academic_figure": {"figure_type": "plot"}}) == "plot"


def test_should_log_paperbanana_verdict_false_when_not_claude_critic():
    """Side-by-side logging only meaningful in claude-critic path."""
    slide = {
        "slide_number": 5,
        "strategy": "academic_figure",
        "academic_figure": {
            "critic": "paperbanana",
            "log_paperbanana_verdict_for_comparison": True,
        },
    }
    assert should_log_paperbanana_verdict(slide) is False


def test_should_log_paperbanana_verdict_true_when_claude_critic_and_opted_in():
    slide = {
        "slide_number": 5,
        "strategy": "academic_figure",
        "academic_figure": {
            "critic": "claude",
            "log_paperbanana_verdict_for_comparison": True,
        },
    }
    assert should_log_paperbanana_verdict(slide) is True


def test_should_log_paperbanana_verdict_default_false_under_claude_critic():
    """Equivalence-testing is opt-in even on the claude-critic path."""
    slide = {
        "slide_number": 5,
        "strategy": "academic_figure",
        "academic_figure": {"critic": "claude"},
    }
    assert should_log_paperbanana_verdict(slide) is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
