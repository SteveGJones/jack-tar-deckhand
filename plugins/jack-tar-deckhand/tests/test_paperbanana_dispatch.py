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

import logging
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

import pytest

import src.paperbanana_dispatch as _pbd_module  # noqa: E402
from src.paperbanana_dispatch import (  # noqa: E402
    LocalBackend,
    PaperbananaDispatch,
    _build_caption_from_slide,
    _build_local_prompt,
    _build_source_context_from_slide,
    _extract_run_id,
    _hf_snapshot_complete,
    _resolve_hf_hub_dir,
    build_dispatch_payload,
    build_manifest_entry,
    detect_any_local_backend,
    detect_local_backend,
    detect_mlx_backend,
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
        local_backend=False,
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
        local_backend=False,
    )
    assert dispatch.args["caption"] == "Loss curve"
    assert "Training loss decreases" in dispatch.args["source_context"]


def test_dispatch_payload_hard_codes_aspect_ratio_16_9():
    """v1.4 hard-codes 16:9 to match slide canvas. Future versions may flex."""
    dispatch = build_dispatch_payload(
        {"slide_number": 1, "headline": "x"},
        output_dir="/tmp/x",
        paperbanana_available=True,
        local_backend=False,
    )
    assert dispatch.args["aspect_ratio"] == "16:9"


def test_dispatch_payload_iterations_defaults_to_1():
    """Cost-control default: 1 iteration per academic_figure slide."""
    dispatch = build_dispatch_payload(
        {"slide_number": 1, "headline": "x"},
        output_dir="/tmp/x",
        paperbanana_available=True,
        local_backend=False,
    )
    assert dispatch.args["iterations"] == 1


def test_dispatch_payload_iterations_honours_slide_override():
    """Speakers opt high-stakes slides up via slide['paperbanana_iterations']."""
    dispatch = build_dispatch_payload(
        {"slide_number": 1, "headline": "x", "paperbanana_iterations": 3},
        output_dir="/tmp/x",
        paperbanana_available=True,
        local_backend=False,
    )
    assert dispatch.args["iterations"] == 3


def test_dispatch_payload_records_output_dir():
    """output_dir (not output_path — paperbanana writes its own subdirectory)."""
    dispatch = build_dispatch_payload(
        {"slide_number": 1, "headline": "x"},
        output_dir="/tmp/deck/images",
        paperbanana_available=True,
        local_backend=False,
    )
    assert dispatch.output_dir == "/tmp/deck/images"


def test_dispatch_payload_records_slide_number_on_struct():
    """slide_number stays on the struct (for manifest accounting), NOT in args."""
    dispatch = build_dispatch_payload(
        {"slide_number": 42, "headline": "x"},
        output_dir="/tmp/x",
        paperbanana_available=True,
        local_backend=False,
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
        local_backend=False,
    )
    assert dispatch.available is False
    assert dispatch.args == {}
    assert dispatch.fallback_provider == "google"
    assert dispatch.fallback_model == "gemini-3.1-flash-image"
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
        local_backend=False,
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
        local_backend=False,
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
        local_backend=False,
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
        local_backend=False,
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
        local_backend=False,
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
        local_backend=False,
    )
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=True,
        output_path="/tmp/deck/images/slide-06-academic-figure.png",
    )
    assert entry["backend"] == "cloud_fallback"
    assert entry["model_used"] == "gemini-3.1-flash-image"
    assert "fallback_reason" in entry
    assert "paperbanana CLI not on PATH" in entry["fallback_reason"]
    assert "paperbanana_run_id" not in entry
    assert "paperbanana_args" not in entry


def test_manifest_entry_failed_dispatch_records_error():
    dispatch = build_dispatch_payload(
        {"slide_number": 8, "headline": "Edge case", "methodology_context": "y"},
        output_dir="/tmp/x",
        paperbanana_available=True,
        local_backend=False,
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
        local_backend=False,
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
    assert dispatch.fallback_model == "gemini-3.1-flash-image"
    assert dispatch.args == {}
    assert dispatch.fallback_reason == ""


# --- detect_local_backend (local Ollama tier, 2026-07-10) ----------------


class _FakeTagsResponse:
    """Minimal context-manager stand-in for urllib's response object."""

    def __init__(self, payload: bytes):
        self._payload = payload
        self._pos = 0

    def read(self, size=-1):
        if size is None or size < 0:
            chunk = self._payload[self._pos:]
            self._pos = len(self._payload)
            return chunk
        chunk = self._payload[self._pos:self._pos + size]
        self._pos += len(chunk)
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


def _patch_ollama_tags(monkeypatch, models):
    import json as _json
    import urllib.request as _ur

    payload = _json.dumps({"models": [{"name": n} for n in models]}).encode()
    monkeypatch.setattr(
        _ur, "urlopen", lambda *_a, **_k: _FakeTagsResponse(payload)
    )


def test_detect_local_backend_prefers_flux2_klein(monkeypatch):
    """flux2-klein wins over z-image-turbo when both are installed."""
    _patch_ollama_tags(
        monkeypatch, ["x/z-image-turbo:latest", "x/flux2-klein:4b", "gemma4:12b"]
    )
    backend = detect_local_backend()
    assert backend == LocalBackend(provider="ollama", model="x/flux2-klein:4b")


def test_detect_local_backend_returns_exact_installed_tag(monkeypatch):
    """The installed tag (e.g. :4b) is returned verbatim — never a bare name."""
    _patch_ollama_tags(monkeypatch, ["x/flux2-klein:4b"])
    assert detect_local_backend().model == "x/flux2-klein:4b"


def test_detect_local_backend_prefers_largest_variant_in_family(monkeypatch):
    """klein 9b beats 4b regardless of Ollama listing order (2026-07-11 review)."""
    _patch_ollama_tags(monkeypatch, ["x/flux2-klein:4b", "x/flux2-klein:9b"])
    assert detect_local_backend().model == "x/flux2-klein:9b"
    _patch_ollama_tags(monkeypatch, ["x/flux2-klein:9b", "x/flux2-klein:4b"])
    assert detect_local_backend().model == "x/flux2-klein:9b"


def test_detect_local_backend_sized_variant_beats_unsized(monkeypatch):
    """A parameter-sized tag outranks 'latest'/quant tags within a family."""
    _patch_ollama_tags(monkeypatch, ["x/flux2-klein:latest", "x/flux2-klein:4b"])
    assert detect_local_backend().model == "x/flux2-klein:4b"


def test_detect_local_backend_family_priority_beats_size(monkeypatch):
    """A small klein still beats a big z-image-turbo — family first, size second."""
    _patch_ollama_tags(monkeypatch, ["x/z-image-turbo:12b", "x/flux2-klein:4b"])
    assert detect_local_backend().model == "x/flux2-klein:4b"


def test_detect_local_backend_falls_back_to_z_image_turbo(monkeypatch):
    _patch_ollama_tags(monkeypatch, ["x/z-image-turbo:fp8", "nomic-embed-text:latest"])
    assert detect_local_backend().model == "x/z-image-turbo:fp8"


def test_detect_local_backend_none_when_no_image_models(monkeypatch):
    """Text/embedding-only Ollama installs are not an image backend."""
    _patch_ollama_tags(monkeypatch, ["gemma4:12b", "nomic-embed-text:latest"])
    assert detect_local_backend() is None


def test_detect_local_backend_none_when_server_down(monkeypatch):
    """Probe failures degrade to None — never raise into the bridge."""
    import urllib.error as _ue
    import urllib.request as _ur

    def boom(*_a, **_k):
        raise _ue.URLError("connection refused")

    monkeypatch.setattr(_ur, "urlopen", boom)
    assert detect_local_backend() is None


def test_detect_local_backend_honours_preferred_model(monkeypatch):
    """local-config.json's academic_figure_model override wins over priority."""
    _patch_ollama_tags(monkeypatch, ["x/flux2-klein:4b", "x/z-image-turbo:latest"])
    backend = detect_local_backend(preferred_model="x/z-image-turbo")
    assert backend.model == "x/z-image-turbo:latest"


def test_detect_local_backend_preferred_model_matches_exact_tag(monkeypatch):
    _patch_ollama_tags(monkeypatch, ["x/flux2-klein:4b"])
    backend = detect_local_backend(preferred_model="x/flux2-klein:4b")
    assert backend.model == "x/flux2-klein:4b"


def test_detect_local_backend_uninstalled_preference_falls_through(monkeypatch):
    """A preferred model that isn't installed falls back to the priority list."""
    _patch_ollama_tags(monkeypatch, ["x/flux2-klein:4b"])
    backend = detect_local_backend(preferred_model="x/qwen-image")
    assert backend.model == "x/flux2-klein:4b"


# --- _build_local_prompt ---------------------------------------------------


def test_local_prompt_carries_caption_context_and_style():
    prompt = _build_local_prompt(
        "We propose a 6-layer Transformer encoder.", "Transformer architecture"
    )
    assert "Transformer architecture" in prompt
    assert "6-layer Transformer encoder" in prompt
    assert "publication-quality academic paper figure" in prompt
    assert "16:9" in prompt


def test_local_prompt_truncates_long_source_context():
    long_ctx = "word " * 400  # ≈2000 chars
    prompt = _build_local_prompt(long_ctx, "Caption")
    # Style block must survive truncation intact at the tail.
    assert prompt.endswith("no watermark.")
    # 800-char context cap + caption sentence + fixed style block ≈ 1.2k.
    assert len(prompt) < 1300
    assert "…" in prompt


def test_local_prompt_skips_context_when_identical_to_caption():
    """Headline-only slides: don't repeat the same sentence twice."""
    prompt = _build_local_prompt("Loss curve", "Loss curve")
    assert prompt.count("Loss curve") == 1


# --- build_dispatch_payload (local-first ladder) ---------------------------


_KLEIN = LocalBackend(provider="ollama", model="x/flux2-klein:4b")


def test_dispatch_local_first_when_backend_detected():
    """Ollama first, always — even when paperbanana is installed (F10)."""
    dispatch = build_dispatch_payload(
        {"slide_number": 3, "headline": "Ablation results", "methodology_context": "We ablate."},
        output_dir="/tmp/deck/images",
        paperbanana_available=True,
        local_backend=_KLEIN,
    )
    assert dispatch.backend == "ollama"
    assert dispatch.local_provider == "ollama"
    assert dispatch.local_model == "x/flux2-klein:4b"
    assert sorted(dispatch.local_args.keys()) == [
        "caption", "height", "iterations", "prompt", "width",
    ]
    assert dispatch.local_args["width"] == 1024
    assert dispatch.local_args["height"] == 576
    assert dispatch.local_args["iterations"] == 3  # ladder mode budget
    # Paperbanana escalation args ride along for the post-gate tier.
    assert dispatch.available is True
    assert dispatch.args["source_context"] == "We ablate."


def test_dispatch_local_first_without_paperbanana_keeps_cloud_escalation():
    """Local draft + cloud escalation info when paperbanana is absent."""
    dispatch = build_dispatch_payload(
        {"slide_number": 4, "headline": "ROC curve"},
        output_dir="/tmp/x",
        paperbanana_available=False,
        local_backend=_KLEIN,
    )
    assert dispatch.backend == "ollama"
    assert dispatch.available is False
    assert dispatch.args == {}
    assert dispatch.fallback_model == "gemini-3.1-flash-image"
    assert "paperbanana CLI not on PATH" in dispatch.fallback_reason


def test_dispatch_backend_paperbanana_when_no_local():
    dispatch = build_dispatch_payload(
        {"slide_number": 1, "headline": "x"},
        output_dir="/tmp/x",
        paperbanana_available=True,
        local_backend=False,
    )
    assert dispatch.backend == "paperbanana"
    assert dispatch.local_model == ""
    assert dispatch.local_args == {}


def test_dispatch_backend_cloud_fallback_when_nothing_local():
    dispatch = build_dispatch_payload(
        {"slide_number": 1, "headline": "x"},
        output_dir="/tmp/x",
        paperbanana_available=False,
        local_backend=False,
    )
    assert dispatch.backend == "cloud_fallback"


def test_dispatch_local_backend_none_triggers_autodetect(monkeypatch):
    """local_backend=None probes Ollama; a hit routes local-first."""
    _patch_ollama_tags(monkeypatch, ["x/flux2-klein:4b"])
    dispatch = build_dispatch_payload(
        {"slide_number": 2, "headline": "x"},
        output_dir="/tmp/x",
        paperbanana_available=False,
    )
    assert dispatch.backend == "ollama"
    assert dispatch.local_model == "x/flux2-klein:4b"


# --- build_dispatch_payload (local_only mode) ------------------------------


def test_local_only_never_assembles_paid_escalation():
    """local_only strips paperbanana args even when paperbanana is installed."""
    dispatch = build_dispatch_payload(
        {"slide_number": 3, "headline": "x", "local_only": True},
        output_dir="/tmp/x",
        paperbanana_available=True,
        local_backend=_KLEIN,
    )
    assert dispatch.local_only is True
    assert dispatch.backend == "ollama"
    assert dispatch.available is False  # paid tier does not exist for this slide
    assert dispatch.args == {}
    assert dispatch.fallback_reason == ""  # no install nag — cloud is opted out


def test_local_only_iteration_budget_is_5():
    """Baseline 5 free loops in local_only (creative_vision ollama cap parity)."""
    dispatch = build_dispatch_payload(
        {"slide_number": 3, "headline": "x", "local_only": True},
        output_dir="/tmp/x",
        paperbanana_available=False,
        local_backend=_KLEIN,
    )
    assert dispatch.local_args["iterations"] == 5


def test_local_iterations_slide_override():
    dispatch = build_dispatch_payload(
        {"slide_number": 3, "headline": "x", "local_only": True, "local_iterations": 8},
        output_dir="/tmp/x",
        paperbanana_available=False,
        local_backend=_KLEIN,
    )
    assert dispatch.local_args["iterations"] == 8


def test_local_only_param_overrides_slide_absence():
    """Bridge passes the machine-wide local-config value via the param."""
    dispatch = build_dispatch_payload(
        {"slide_number": 3, "headline": "x"},
        output_dir="/tmp/x",
        paperbanana_available=True,
        local_backend=_KLEIN,
        local_only=True,
    )
    assert dispatch.local_only is True
    assert dispatch.args == {}


def test_local_only_blocked_when_no_local_backend():
    """local_only + Ollama down → hard stop, NEVER cloud fallback."""
    dispatch = build_dispatch_payload(
        {"slide_number": 3, "headline": "x", "local_only": True},
        output_dir="/tmp/x",
        paperbanana_available=True,
        local_backend=False,
    )
    assert dispatch.backend == "local_only_blocked"
    assert dispatch.local_only is True
    assert "Cloud dispatch is FORBIDDEN" in dispatch.fallback_reason


def test_local_only_false_keeps_ladder_defaults():
    dispatch = build_dispatch_payload(
        {"slide_number": 3, "headline": "x"},
        output_dir="/tmp/x",
        paperbanana_available=True,
        local_backend=_KLEIN,
    )
    assert dispatch.local_only is False
    assert dispatch.local_args["iterations"] == 3
    assert dispatch.available is True
    assert dispatch.args != {}


def test_manifest_entry_carries_local_only_flag():
    dispatch = build_dispatch_payload(
        {"slide_number": 3, "headline": "x", "local_only": True},
        output_dir="/tmp/x",
        paperbanana_available=False,
        local_backend=_KLEIN,
    )
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=True,
        output_path="/tmp/x/slide-03-academic-figure-ollama.png",
    )
    assert entry["local_only"] is True
    assert entry["backend"] == "ollama_local"


# --- build_manifest_entry (local tier) -------------------------------------


def _local_dispatch(slide_number=7):
    return build_dispatch_payload(
        {
            "slide_number": slide_number,
            "headline": "Encoder stack",
            "methodology_context": "Six identical layers with residual connections.",
        },
        output_dir="/tmp/deck/images",
        paperbanana_available=True,
        local_backend=_KLEIN,
    )


def test_manifest_entry_for_local_ollama_render():
    dispatch = _local_dispatch()
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=True,
        output_path="/tmp/deck/images/slide-07-academic-figure-ollama.png",
        content_hash="abc",
    )
    assert entry["backend"] == "ollama_local"
    assert entry["model_used"] == "x/flux2-klein:4b"
    assert entry["local_provider"] == "ollama"
    assert entry["source_prompt"] == dispatch.local_args["prompt"]
    assert entry["caption"] == "Encoder stack"
    assert entry["local_args"]["width"] == 1024
    assert "paperbanana_run_id" not in entry
    assert "paperbanana_args" not in entry
    assert "fallback_reason" not in entry


def test_manifest_entry_escalated_to_paperbanana_after_gate():
    """backend_used override: operator escalated past the local draft."""
    dispatch = _local_dispatch()
    real_path = "/tmp/deck/images/run_20260710_120000_abc123/final_output.png"
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=True,
        output_path=real_path,
        backend_used="paperbanana",
    )
    assert entry["backend"] == "paperbanana"
    assert entry["model_used"] == "paperbanana"
    assert entry["paperbanana_run_id"] == "run_20260710_120000_abc123"
    assert entry["paperbanana_args"]["source_context"] == (
        "Six identical layers with residual connections."
    )


def test_manifest_entry_escalated_to_cloud_after_gate():
    dispatch = build_dispatch_payload(
        {"slide_number": 9, "headline": "PR curves"},
        output_dir="/tmp/x",
        paperbanana_available=False,
        local_backend=_KLEIN,
    )
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=True,
        output_path="/tmp/x/slide-09-academic-figure.png",
        backend_used="cloud_fallback",
    )
    assert entry["backend"] == "cloud_fallback"
    assert entry["model_used"] == "gemini-3.1-flash-image"
    assert "fallback_reason" in entry


def test_manifest_entry_legacy_dispatch_without_backend_field():
    """Direct PaperbananaDispatch constructions (SKILL.md step 2) keep working."""
    dispatch = PaperbananaDispatch(
        available=True,
        slide_number=5,
        output_dir="/tmp/x",
        args={"source_context": "y", "caption": "z", "aspect_ratio": "16:9", "iterations": 1},
    )
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=True,
        output_path="/tmp/x/run_20260518_120000_def95c/final_output.png",
    )
    assert entry["backend"] == "paperbanana"
    assert entry["model_used"] == "paperbanana"


# --- MLX backend detection (issue #124, T3) --------------------------------


def _make_complete_snapshot(hub_dir: Path, repo_id: str, revision: str = "abc123def0"):
    """Build a minimal-but-complete HF-cache snapshot tree for repo_id.

    Layout: ``<hub_dir>/models--<org>--<name>/{blobs,snapshots/<rev>,refs}``,
    with a single symlinked file resolving into blobs/ and refs/main naming
    the revision — the shape ``_hf_snapshot_complete`` inspects.
    """
    repo_dir = hub_dir / ("models--" + repo_id.replace("/", "--"))
    blobs_dir = repo_dir / "blobs"
    blobs_dir.mkdir(parents=True, exist_ok=True)
    blob_path = blobs_dir / "0123456789abcdef"
    blob_path.write_text("weights", encoding="utf-8")

    snapshot_dir = repo_dir / "snapshots" / revision
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / "config.json").symlink_to(blob_path)

    refs_dir = repo_dir / "refs"
    refs_dir.mkdir(parents=True, exist_ok=True)
    (refs_dir / "main").write_text(revision, encoding="utf-8")
    return repo_dir


_MLX_KLEIN = LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")

_KLEIN_HF_REPO = "Runpod/FLUX.2-klein-4B-mflux-4bit"
_Z_IMAGE_HF_REPO = "filipstrand/Z-Image-Turbo-mflux-4bit"
_QWEN_HF_REPO = "OsaurusAI/Qwen-Image-mflux-4bit"


# --- _resolve_hf_hub_dir (review m7) ----------------------------------------


def test_resolve_hf_hub_dir_precedence(monkeypatch, tmp_path):
    """explicit arg > $HF_HUB_CACHE > $HF_HOME/hub > ~/.cache/huggingface/hub."""
    monkeypatch.setenv("HF_HUB_CACHE", str(tmp_path / "cache_dir"))
    monkeypatch.setenv("HF_HOME", str(tmp_path / "home_dir"))

    # Explicit arg wins over both env vars.
    assert _resolve_hf_hub_dir(str(tmp_path / "explicit")) == (
        tmp_path / "explicit" / "hub"
    )

    # HF_HUB_CACHE (used directly as the hub dir) beats HF_HOME.
    assert _resolve_hf_hub_dir() == tmp_path / "cache_dir"

    monkeypatch.delenv("HF_HUB_CACHE", raising=False)
    assert _resolve_hf_hub_dir() == tmp_path / "home_dir" / "hub"

    monkeypatch.delenv("HF_HOME", raising=False)
    assert _resolve_hf_hub_dir() == Path.home() / ".cache" / "huggingface" / "hub"


# --- _hf_snapshot_complete (review m8) ---------------------------------------


def test_hf_snapshot_complete_true_for_full_snapshot(tmp_path):
    hub_dir = tmp_path / "hub"
    _make_complete_snapshot(hub_dir, "org/name")
    assert _hf_snapshot_complete("org/name", hub_dir) is True


def test_hf_snapshot_complete_false_for_incomplete_blob_in_resolved_revision(tmp_path):
    hub_dir = tmp_path / "hub"
    repo_dir = _make_complete_snapshot(hub_dir, "org/name")
    blob_path = repo_dir / "blobs" / "0123456789abcdef"
    (blob_path.parent / (blob_path.name + ".incomplete")).write_text(
        "", encoding="utf-8"
    )
    assert _hf_snapshot_complete("org/name", hub_dir) is False


def test_hf_snapshot_complete_false_for_unreferenced_incomplete_blob(tmp_path):
    """Field finding (2026-07-15 live download): mid-download, the in-flight
    file has a blobs/<hash>.incomplete but NO snapshot symlink yet, so a
    revision-scoped check sees only resolving symlinks and passes. Any
    .incomplete anywhere in blobs/ must block readiness."""
    hub_dir = tmp_path / "hub"
    repo_dir = _make_complete_snapshot(hub_dir, "org/name")
    (repo_dir / "blobs" / "ffffffffffffffff.incomplete").write_text(
        "", encoding="utf-8"
    )
    assert _hf_snapshot_complete("org/name", hub_dir) is False


def test_hf_snapshot_complete_false_for_dangling_symlink(tmp_path):
    hub_dir = tmp_path / "hub"
    repo_dir = _make_complete_snapshot(hub_dir, "org/name")
    (repo_dir / "blobs" / "0123456789abcdef").unlink()
    assert _hf_snapshot_complete("org/name", hub_dir) is False


def test_hf_snapshot_complete_false_for_missing_repo(tmp_path):
    hub_dir = tmp_path / "hub"
    hub_dir.mkdir(parents=True, exist_ok=True)
    assert _hf_snapshot_complete("org/does-not-exist", hub_dir) is False


def test_hf_snapshot_complete_resolves_revision_via_refs_main(tmp_path):
    """With two snapshot dirs, the refs/main-named revision is checked —
    not simply the newest-by-mtime one (review m8)."""
    hub_dir = tmp_path / "hub"
    repo_dir = _make_complete_snapshot(hub_dir, "org/name", revision="main-rev")

    # A second, later-created (hence newer-mtime) snapshot dir that is
    # INCOMPLETE — if mtime fallback were used instead of refs/main, this
    # dangling snapshot would be picked and the check would (wrongly) fail.
    bogus_dir = repo_dir / "snapshots" / "newer-bogus-rev"
    bogus_dir.mkdir(parents=True)
    (bogus_dir / "config.json").symlink_to(repo_dir / "blobs" / "does-not-exist")

    assert _hf_snapshot_complete("org/name", hub_dir) is True


# --- detect_mlx_backend (issue #124) -----------------------------------------


def test_detect_mlx_backend_returns_none_when_no_cli(monkeypatch):
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: None)
    assert detect_mlx_backend() is None


def test_detect_mlx_backend_checks_selected_entrys_entrypoint(monkeypatch, tmp_path):
    """Only mflux-generate-qwen on PATH → klein/z-image skipped, qwen selectable
    (review m12) — even though klein/z-image ALSO have complete weights cached."""
    import shutil as _sh

    monkeypatch.setattr(
        _sh, "which", lambda name: "/usr/bin/x" if name == "mflux-generate-qwen" else None
    )
    monkeypatch.setattr(_pbd_module, "_physical_ram_gb", lambda: 64.0)
    hub_dir = tmp_path / "hub"
    _make_complete_snapshot(hub_dir, _KLEIN_HF_REPO)
    _make_complete_snapshot(hub_dir, _Z_IMAGE_HF_REPO)
    _make_complete_snapshot(hub_dir, _QWEN_HF_REPO)

    backend = detect_mlx_backend(hf_home=str(tmp_path))
    assert backend == LocalBackend(provider="mlx", model="mlx/qwen-image")


def test_detect_mlx_backend_returns_none_when_cli_but_no_weights(monkeypatch, tmp_path):
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_pbd_module, "_physical_ram_gb", lambda: 64.0)
    assert detect_mlx_backend(hf_home=str(tmp_path)) is None


def test_detect_mlx_backend_returns_catalog_id_when_weights_complete(monkeypatch, tmp_path):
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_pbd_module, "_physical_ram_gb", lambda: 64.0)
    _make_complete_snapshot(tmp_path / "hub", _KLEIN_HF_REPO)

    backend = detect_mlx_backend(hf_home=str(tmp_path))
    assert backend == LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")


def test_detect_mlx_backend_honours_preferred_model(monkeypatch, tmp_path):
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_pbd_module, "_physical_ram_gb", lambda: 64.0)
    hub_dir = tmp_path / "hub"
    _make_complete_snapshot(hub_dir, _KLEIN_HF_REPO)
    _make_complete_snapshot(hub_dir, _Z_IMAGE_HF_REPO)

    backend = detect_mlx_backend(preferred_model="mlx/z-image-turbo", hf_home=str(tmp_path))
    assert backend == LocalBackend(provider="mlx", model="mlx/z-image-turbo")


def test_detect_mlx_backend_ram_gate_skips_qwen_in_catalog_order(monkeypatch, tmp_path):
    """min_ram_gb 32 > 16GB machine → qwen skipped during catalog-order
    auto-selection (review m11); no other candidate has weights → None."""
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_pbd_module, "_physical_ram_gb", lambda: 16.0)
    _make_complete_snapshot(tmp_path / "hub", _QWEN_HF_REPO)

    assert detect_mlx_backend(hf_home=str(tmp_path)) is None


def test_detect_mlx_backend_preferred_model_bypasses_ram_gate_with_warning(
    monkeypatch, tmp_path, caplog
):
    """An explicit preferred_model bypasses the RAM gate — with a logged
    warning (review m11 ruling: the operator who names a model owns the
    consequence)."""
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_pbd_module, "_physical_ram_gb", lambda: 16.0)
    _make_complete_snapshot(tmp_path / "hub", _QWEN_HF_REPO)

    with caplog.at_level(logging.WARNING):
        backend = detect_mlx_backend(preferred_model="mlx/qwen-image", hf_home=str(tmp_path))

    assert backend == LocalBackend(provider="mlx", model="mlx/qwen-image")
    assert any("RAM gate" in r.message for r in caplog.records)


def test_detect_mlx_backend_ram_gate_disabled_when_ram_unknown(monkeypatch, tmp_path):
    """_physical_ram_gb() -> None disables the RAM gate (fail-open) — qwen
    is offered in catalog order despite its min_ram_gb requirement."""
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_pbd_module, "_physical_ram_gb", lambda: None)
    _make_complete_snapshot(tmp_path / "hub", _QWEN_HF_REPO)

    backend = detect_mlx_backend(hf_home=str(tmp_path))
    assert backend == LocalBackend(provider="mlx", model="mlx/qwen-image")


def test_detect_mlx_backend_honours_hf_hub_cache_env(monkeypatch, tmp_path):
    """Weights under an HF_HUB_CACHE-pointed dir are found (m7 acceptance)."""
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_pbd_module, "_physical_ram_gb", lambda: 64.0)
    hub_dir = tmp_path / "custom_hub"
    _make_complete_snapshot(hub_dir, _KLEIN_HF_REPO)
    monkeypatch.setenv("HF_HUB_CACHE", str(hub_dir))
    monkeypatch.delenv("HF_HOME", raising=False)

    backend = detect_mlx_backend()
    assert backend == LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")


# --- detect_any_local_backend (composed probe, issue #124) -------------------


def test_detect_any_local_backend_prefers_ollama_by_default(monkeypatch, tmp_path):
    """Both up, provider_order=None -> ollama wins (default order)."""
    import shutil as _sh

    _patch_ollama_tags(monkeypatch, ["x/flux2-klein:4b"])
    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_pbd_module, "_physical_ram_gb", lambda: 64.0)
    _make_complete_snapshot(tmp_path / "hub", _KLEIN_HF_REPO)

    backend = detect_any_local_backend(hf_home=str(tmp_path))
    assert backend == LocalBackend(provider="ollama", model="x/flux2-klein:4b")


def test_detect_any_local_backend_falls_through_to_mlx_when_ollama_down(monkeypatch, tmp_path):
    """Issue #124 acceptance case: Ollama down + mflux+weights present."""
    import urllib.error as _ue
    import urllib.request as _ur
    import shutil as _sh

    def boom(*_a, **_k):
        raise _ue.URLError("connection refused")

    monkeypatch.setattr(_ur, "urlopen", boom)
    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_pbd_module, "_physical_ram_gb", lambda: 64.0)
    _make_complete_snapshot(tmp_path / "hub", _KLEIN_HF_REPO)

    backend = detect_any_local_backend(hf_home=str(tmp_path))
    assert backend == LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")


def test_detect_any_local_backend_honours_provider_order(monkeypatch, tmp_path):
    """order=('mlx','ollama') -> mlx wins even with ollama up."""
    import shutil as _sh

    _patch_ollama_tags(monkeypatch, ["x/flux2-klein:4b"])
    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_pbd_module, "_physical_ram_gb", lambda: 64.0)
    _make_complete_snapshot(tmp_path / "hub", _KLEIN_HF_REPO)

    backend = detect_any_local_backend(
        provider_order=("mlx", "ollama"), hf_home=str(tmp_path)
    )
    assert backend == LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")


def test_detect_any_local_backend_none_when_no_provider(monkeypatch):
    import urllib.error as _ue
    import urllib.request as _ur
    import shutil as _sh

    def boom(*_a, **_k):
        raise _ue.URLError("connection refused")

    monkeypatch.setattr(_ur, "urlopen", boom)
    monkeypatch.setattr(_sh, "which", lambda _name: None)
    assert detect_any_local_backend() is None


def test_detect_any_local_backend_does_no_file_io(monkeypatch):
    """Review m16 pin: monkeypatch builtins.open/Path.open to raise; the
    seam function still runs on injected params — it never reads
    local-config.json (or any other file) itself."""
    import builtins
    import urllib.error as _ue
    import urllib.request as _ur
    import shutil as _sh

    def boom_open(*_a, **_k):
        raise AssertionError("detect_any_local_backend must not open files")

    monkeypatch.setattr(builtins, "open", boom_open)
    monkeypatch.setattr(Path, "open", boom_open)

    def boom_urlopen(*_a, **_k):
        raise _ue.URLError("connection refused")

    monkeypatch.setattr(_ur, "urlopen", boom_urlopen)
    monkeypatch.setattr(_sh, "which", lambda _name: None)

    assert detect_any_local_backend() is None


# --- build_dispatch_payload / build_manifest_entry (MLX provider) -----------


def test_dispatch_payload_mlx_local_args_carry_render_steps():
    """review M4c: local_args['steps'] always carries the catalog's
    capabilities.render_steps for an MLX dispatch."""
    dispatch = build_dispatch_payload(
        {
            "slide_number": 3,
            "headline": "Ablation results",
            "methodology_context": "We ablate the components one at a time.",
        },
        output_dir="/tmp/deck/images",
        paperbanana_available=False,
        local_backend=_MLX_KLEIN,
    )
    assert dispatch.local_args["steps"] == 20


def test_build_dispatch_payload_mlx_backend_sets_backend_and_local_model():
    dispatch = build_dispatch_payload(
        {"slide_number": 2, "headline": "x"},
        output_dir="/tmp/x",
        paperbanana_available=False,
        local_backend=_MLX_KLEIN,
    )
    assert dispatch.backend == "mlx"
    assert dispatch.local_provider == "mlx"
    assert dispatch.local_model == "mlx/flux2-klein-4b"


def test_manifest_entry_for_local_mlx_render():
    """The :647 regression guard: an mlx_local backend_used enriches the
    manifest entry exactly as ollama_local does."""
    dispatch = build_dispatch_payload(
        {
            "slide_number": 7,
            "headline": "Encoder stack",
            "methodology_context": "Six identical layers with residual connections.",
        },
        output_dir="/tmp/deck/images",
        paperbanana_available=True,
        local_backend=_MLX_KLEIN,
    )
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=True,
        output_path="/tmp/deck/images/slide-07-academic-figure-mlx.png",
        content_hash="abc",
    )
    assert entry["backend"] == "mlx_local"
    assert entry["model_used"] == "mlx/flux2-klein-4b"
    assert entry["local_provider"] == "mlx"
    assert entry["source_prompt"] == dispatch.local_args["prompt"]
    assert entry["caption"] == "Encoder stack"
    assert entry["local_args"]["steps"] == 20
    assert "paperbanana_run_id" not in entry
    assert "paperbanana_args" not in entry
    assert "fallback_reason" not in entry


def test_manifest_entry_escalated_from_mlx_to_paperbanana_after_gate():
    """backend_used override: operator escalated past the MLX draft."""
    dispatch = build_dispatch_payload(
        {
            "slide_number": 9,
            "headline": "Ablation results",
            "methodology_context": "We ablate the components one at a time to measure impact.",
        },
        output_dir="/tmp/deck/images",
        paperbanana_available=True,
        local_backend=_MLX_KLEIN,
    )
    real_path = "/tmp/deck/images/run_20260710_120000_abc123/final_output.png"
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=True,
        output_path=real_path,
        backend_used="paperbanana",
    )
    assert entry["backend"] == "paperbanana"
    assert entry["model_used"] == "paperbanana"
    assert entry["paperbanana_run_id"] == "run_20260710_120000_abc123"


def test_manifest_entry_legacy_ollama_local_without_provider_takes_fallback_branch():
    """Review m15 — INTENTIONAL BEHAVIOUR CHANGE: a legacy caller passing
    backend_used="ollama_local" explicitly on a dispatch whose
    local_provider is EMPTY previously took the enrichment branch (emitting
    empty source_prompt/caption/local_args, since there was nothing to
    enrich from); after the :647 guard generalisation it falls to the
    fallback (else) branch instead. This is correct — such a dispatch
    carries no local_args to enrich from — but it is a behaviour change,
    pinned here per issue #124 T3."""
    dispatch = PaperbananaDispatch(
        available=False,
        slide_number=4,
        output_dir="/tmp/x",
        # local_provider left at its default "" — simulates a legacy direct
        # construction that never set the provider.
    )
    entry = build_manifest_entry(
        dispatch,
        dispatch_succeeded=True,
        output_path="/tmp/x/slide-04-academic-figure-ollama.png",
        backend_used="ollama_local",
    )
    assert entry["backend"] == "ollama_local"
    assert entry["model_used"] == "gemini-3.1-flash-image"
    assert "local_provider" not in entry
    assert "local_args" not in entry
    assert "fallback_reason" in entry
    assert entry["fallback_reason"] == ""


def test_local_only_blocked_message_names_both_providers():
    """review §2.6: the local_only_blocked message names Ollama AND MLX
    remediation, not just Ollama, so an MLX-only operator gets actionable
    guidance."""
    dispatch = build_dispatch_payload(
        {"slide_number": 3, "headline": "x", "local_only": True},
        output_dir="/tmp/x",
        paperbanana_available=True,
        local_backend=False,
    )
    assert dispatch.backend == "local_only_blocked"
    assert "ollama" in dispatch.fallback_reason.lower()
    assert "mlx" in dispatch.fallback_reason.lower()
    assert "Cloud dispatch is FORBIDDEN" in dispatch.fallback_reason


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
