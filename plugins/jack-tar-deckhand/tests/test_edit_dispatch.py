"""Tests for the edit-tier dispatch helper (issue #143 PR D).

Mirrors the ``test_paperbanana_dispatch.py`` conventions for MLX backend
detection fixtures (HF-cache snapshot builder + repo constants), since
``detect_mlx_edit_backend`` reuses the same ``_hf_snapshot_complete`` /
``_physical_ram_gb`` machinery.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

import src.edit_dispatch as _ed_module  # noqa: E402
from src.edit_dispatch import (  # noqa: E402
    LocalBackend,
    build_edit_args,
    classify_edit_locality,
    detect_mlx_edit_backend,
    edit_channel_available,
    edit_channel_unavailable_reason,
    record_edit,
)


# --- fixtures shared with test_paperbanana_dispatch.py's MLX conventions ---


def _make_complete_snapshot(hub_dir: Path, repo_id: str, revision: str = "abc123def0"):
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


_KLEIN_HF_REPO = "Runpod/FLUX.2-klein-4B-mflux-4bit"
_QWEN_HF_REPO = "OsaurusAI/Qwen-Image-mflux-4bit"


# --- detect_mlx_edit_backend -------------------------------------------------


def test_detect_mlx_edit_backend_returns_none_when_no_cli(monkeypatch):
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: None)
    assert detect_mlx_edit_backend() is None


def test_detect_mlx_edit_backend_returns_none_when_cli_but_no_weights(monkeypatch, tmp_path):
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_ed_module, "_physical_ram_gb", lambda: 64.0)
    assert detect_mlx_edit_backend(hf_home=str(tmp_path)) is None


def test_detect_mlx_edit_backend_returns_catalog_id_when_weights_complete(monkeypatch, tmp_path):
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_ed_module, "_physical_ram_gb", lambda: 64.0)
    _make_complete_snapshot(tmp_path / "hub", _KLEIN_HF_REPO)

    backend = detect_mlx_edit_backend(hf_home=str(tmp_path))
    assert backend == LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")


def test_detect_mlx_edit_backend_ram_gate_uses_edit_min_ram_not_generate_min_ram(
    monkeypatch, tmp_path
):
    """qwen-image's generate min_ram_gb (32) would pass on a 40GB machine,
    but its edit_min_ram_gb (64) must not — the edit RAM gate is a
    SEPARATE, heavier field (mflux #420)."""
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_ed_module, "_physical_ram_gb", lambda: 40.0)
    _make_complete_snapshot(tmp_path / "hub", _QWEN_HF_REPO)

    assert detect_mlx_edit_backend(hf_home=str(tmp_path)) is None


def test_detect_mlx_edit_backend_qwen_selectable_at_64gb(monkeypatch, tmp_path):
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_ed_module, "_physical_ram_gb", lambda: 64.0)
    _make_complete_snapshot(tmp_path / "hub", _KLEIN_HF_REPO)
    _make_complete_snapshot(tmp_path / "hub", _QWEN_HF_REPO)

    # Klein is catalogued first — catalog order wins absent a preference.
    backend = detect_mlx_edit_backend(hf_home=str(tmp_path))
    assert backend == LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")


def test_detect_mlx_edit_backend_honours_preferred_model(monkeypatch, tmp_path):
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_ed_module, "_physical_ram_gb", lambda: 64.0)
    _make_complete_snapshot(tmp_path / "hub", _QWEN_HF_REPO)

    backend = detect_mlx_edit_backend(preferred_model="mlx/qwen-image", hf_home=str(tmp_path))
    assert backend == LocalBackend(provider="mlx", model="mlx/qwen-image")


def test_detect_mlx_edit_backend_preferred_model_bypasses_ram_gate_with_warning(
    monkeypatch, tmp_path, caplog
):
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_ed_module, "_physical_ram_gb", lambda: 16.0)
    _make_complete_snapshot(tmp_path / "hub", _QWEN_HF_REPO)

    with caplog.at_level(logging.WARNING):
        backend = detect_mlx_edit_backend(preferred_model="mlx/qwen-image", hf_home=str(tmp_path))

    assert backend == LocalBackend(provider="mlx", model="mlx/qwen-image")
    assert any("edit RAM gate" in r.message for r in caplog.records)


def test_detect_mlx_edit_backend_skips_non_edit_capable_model(monkeypatch, tmp_path):
    """z-image-turbo has weights + entrypoint on PATH but no edit CLI —
    must never be selected even when preferred (mflux ships no z-image
    edit entry point)."""
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_ed_module, "_physical_ram_gb", lambda: 64.0)
    _make_complete_snapshot(tmp_path / "hub", "filipstrand/Z-Image-Turbo-mflux-4bit")

    backend = detect_mlx_edit_backend(
        preferred_model="mlx/z-image-turbo", hf_home=str(tmp_path)
    )
    assert backend is None


def test_detect_mlx_edit_backend_ram_gate_disabled_when_ram_unknown(monkeypatch, tmp_path):
    import shutil as _sh

    monkeypatch.setattr(_sh, "which", lambda _name: "/usr/bin/x")
    monkeypatch.setattr(_ed_module, "_physical_ram_gb", lambda: None)
    _make_complete_snapshot(tmp_path / "hub", _QWEN_HF_REPO)

    backend = detect_mlx_edit_backend(preferred_model="mlx/qwen-image", hf_home=str(tmp_path))
    assert backend == LocalBackend(provider="mlx", model="mlx/qwen-image")


# --- edit_channel_unavailable_reason (F-06) ---------------------------------


class _FakeCatalogNoEditRoles:
    def entries(self, role=None, provider=None, status="active"):
        return []


def test_edit_channel_unavailable_reason_empty_when_backend_present():
    backend = LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")
    assert edit_channel_unavailable_reason(backend) == ""


def test_edit_channel_unavailable_reason_flags_stale_catalog():
    reason = edit_channel_unavailable_reason(None, catalog=_FakeCatalogNoEditRoles())
    assert "stale" in reason.lower() or "predates" in reason.lower()
    assert "refresh-models" in reason or "model-catalog.json" in reason


def test_edit_channel_unavailable_reason_generic_when_catalog_has_edit_roles():
    # Real catalog on main carries image_edit entries — generic message.
    reason = edit_channel_unavailable_reason(None)
    assert "mflux" in reason.lower()
    assert "predates" not in reason.lower()


# --- edit_channel_available (D8) --------------------------------------------


def test_edit_channel_available_true_when_base_exists_and_backend_present(tmp_path):
    base = tmp_path / "slide-04.png"
    base.write_bytes(b"fake-png")
    backend = LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")
    entry = {"file_path": str(base), "backend": "ollama_local"}
    assert edit_channel_available(entry, backend) is True


def test_edit_channel_available_false_when_no_backend(tmp_path):
    base = tmp_path / "slide-04.png"
    base.write_bytes(b"fake-png")
    entry = {"file_path": str(base)}
    assert edit_channel_available(entry, None) is False


def test_edit_channel_available_false_when_base_missing_on_disk(tmp_path):
    backend = LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")
    entry = {"file_path": str(tmp_path / "does-not-exist.png")}
    assert edit_channel_available(entry, backend) is False


def test_edit_channel_available_false_when_no_manifest_entry():
    backend = LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")
    assert edit_channel_available(None, backend) is False


@pytest.mark.parametrize("provenance", ["ollama_local", "mlx_local", "cloud_fallback", "paperbanana"])
def test_edit_channel_available_allows_all_three_provenance_classes(tmp_path, provenance):
    """D8 FIRM: mflux, ollama, AND cloud bases are all allowed — the
    provenance class is recorded, not gated."""
    base = tmp_path / "slide-04.png"
    base.write_bytes(b"fake-png")
    backend = LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")
    entry = {"file_path": str(base), "backend": provenance}
    assert edit_channel_available(entry, backend) is True


# --- classify_edit_locality (D9 hard carve-out + local/global/ambiguous) ---


@pytest.mark.parametrize(
    "feedback",
    [
        "fix the third label",
        "correct the spelling",
        "the title should read Publish",
        "there's a typo in the caption",
        "the wording on the second box is wrong",
    ],
)
def test_classify_edit_locality_text_carve_out_is_hard_exclude(feedback):
    """D9/S1: text-targeting feedback NEVER classifies as edit-eligible,
    regardless of spatial locality language elsewhere in the string."""
    result = classify_edit_locality(feedback)
    assert result["locality"] == "text_excluded"
    assert result["confidence"] == 1.0


def test_classify_edit_locality_text_carve_out_wins_over_local_cues():
    """Even when local-sounding cues (sky, darken) are ALSO present, a
    text cue anywhere in the feedback forces text_excluded — the carve-out
    is applied FIRST and is unconditional."""
    result = classify_edit_locality("darken the sky and fix the label spelling")
    assert result["locality"] == "text_excluded"


def test_classify_edit_locality_local_region_colour():
    result = classify_edit_locality("darken the sky, keep the ships and horizon")
    assert result["locality"] == "local"
    assert "sky" in result["cues"]


def test_classify_edit_locality_global_composition_redo():
    result = classify_edit_locality("redo the whole scene, wrong number of ships")
    assert result["locality"] == "global"


def test_classify_edit_locality_ambiguous_when_no_cues_match():
    result = classify_edit_locality("make it look nicer overall")
    assert result["locality"] == "ambiguous"


def test_classify_edit_locality_empty_feedback_is_ambiguous():
    result = classify_edit_locality("")
    assert result["locality"] == "ambiguous"


def test_classify_edit_locality_reads_critic_verdict_issues():
    """The classifier also scans the Director's Critic verdict's
    recommended_action + issue details, per design §4.1."""
    verdict = {
        "recommended_action": "darken the sky region",
        "issues": [{"axis": "style_fidelity", "detail": "sky too bright"}],
    }
    result = classify_edit_locality("", critic_verdict=verdict)
    assert result["locality"] == "local"


def test_classify_edit_locality_critic_verdict_text_gap_hard_excludes():
    verdict = {
        "recommended_action": "fix the misspelled label",
        "issues": [],
    }
    result = classify_edit_locality("looks close", critic_verdict=verdict)
    assert result["locality"] == "text_excluded"


# --- build_edit_args (F-08 seed always resolved; no dims keys, S7) --------


def test_build_edit_args_shape():
    backend = LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")
    args = build_edit_args("base.png", "darken the sky", backend, seed=42, guidance=3.5)
    assert args["model"] == "mlx/flux2-klein-4b"
    assert args["image_paths"] == ["base.png"]
    assert args["prompt"] == "darken the sky"
    assert args["steps"] == 4  # catalog edit_render_steps for klein
    assert args["seed"] == 42
    assert args["guidance"] == 3.5


def test_build_edit_args_no_width_height_keys():
    backend = LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")
    args = build_edit_args("base.png", "darken the sky", backend)
    assert "width" not in args
    assert "height" not in args


def test_build_edit_args_seed_always_populated_when_omitted():
    backend = LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")
    args = build_edit_args("base.png", "darken the sky", backend)
    assert isinstance(args["seed"], int)


def test_build_edit_args_reference_paths_appended():
    backend = LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")
    args = build_edit_args(
        "base.png", "match the palette of the second image", backend,
        reference_paths=("anchor.png",),
    )
    assert args["image_paths"] == ["base.png", "anchor.png"]


def test_build_edit_args_guidance_omitted_when_not_given():
    backend = LocalBackend(provider="mlx", model="mlx/flux2-klein-4b")
    args = build_edit_args("base.png", "darken the sky", backend)
    assert "guidance" not in args


def test_build_edit_args_qwen_edit_steps():
    backend = LocalBackend(provider="mlx", model="mlx/qwen-image")
    args = build_edit_args("base.png", "darken the sky", backend, seed=1)
    assert args["steps"] == 8


# --- record_edit (D5 provenance chain) --------------------------------------


def _base_entry(**overrides):
    entry = {
        "slide_number": 4,
        "file_path": "/deck/images/slide-04-draft.png",
        "content_hash": "sha256:base",
        "backend": "ollama_local",
        "model_used": "x/flux2-klein:9b",
        "cost_usd": 0.0,
    }
    entry.update(overrides)
    return entry


def test_record_edit_first_edit_seeds_chain():
    prior = _base_entry()
    edit_args = {"model": "mlx/flux2-klein-4b", "steps": 4, "seed": 42,
                 "image_paths": [prior["file_path"]]}
    new_entry = record_edit(
        prior,
        new_file_path="/deck/images/slide-04-edit-1.png",
        new_content_hash="sha256:new1",
        edit_instruction="darken the sky, keep the ships and horizon",
        edit_args=edit_args,
        parent_content_hash="sha256:base",
    )
    assert new_entry["file_path"] == "/deck/images/slide-04-edit-1.png"
    assert new_entry["content_hash"] == "sha256:new1"
    assert new_entry["backend"] == "mlx_edit"
    assert new_entry["cost_usd"] == 0.0
    assert len(new_entry["edit_chain"]) == 1
    chain0 = new_entry["edit_chain"][0]
    assert chain0["iteration"] == 1
    assert chain0["parent_content_hash"] == "sha256:base"
    assert chain0["parent_file_path"] == prior["file_path"]
    assert chain0["parent_backend"] == "ollama_local"
    assert chain0["instruction"] == "darken the sky, keep the ships and horizon"
    assert chain0["edit_args"]["seed"] == 42
    assert chain0["cost_usd"] == 0.0
    assert "timestamp" in chain0


def test_record_edit_does_not_mutate_input():
    prior = _base_entry()
    original = dict(prior)
    record_edit(
        prior, "/x.png", "sha256:new",
        edit_instruction="i", edit_args={"seed": 1, "model": "mlx/flux2-klein-4b"},
        parent_content_hash="sha256:base",
    )
    assert prior == original


def test_record_edit_second_edit_appends_chain():
    prior = _base_entry()
    first = record_edit(
        prior, "/x1.png", "sha256:new1",
        edit_instruction="edit 1", edit_args={"seed": 1, "model": "mlx/flux2-klein-4b"},
        parent_content_hash="sha256:base",
    )
    second = record_edit(
        first, "/x2.png", "sha256:new2",
        edit_instruction="edit 2", edit_args={"seed": 2, "model": "mlx/flux2-klein-4b"},
        parent_content_hash="sha256:new1",
    )
    assert len(second["edit_chain"]) == 2
    assert [c["iteration"] for c in second["edit_chain"]] == [1, 2]
    assert second["edit_chain"][1]["parent_content_hash"] == "sha256:new1"
    assert second["edit_chain"][1]["parent_file_path"] == "/x1.png"
    # A subsequent edit's own parent_backend is the PRIOR edit's backend
    # (mlx_edit), correctly recording that the chain's second hop edited
    # an already-edited image.
    assert second["edit_chain"][1]["parent_backend"] == "mlx_edit"
    assert second["file_path"] == "/x2.png"
    assert second["content_hash"] == "sha256:new2"


def test_record_edit_seed_present_in_every_chain_entry():
    prior = _base_entry()
    first = record_edit(
        prior, "/x1.png", "sha256:new1",
        edit_instruction="edit 1", edit_args={"seed": 7, "model": "mlx/flux2-klein-4b"},
        parent_content_hash="sha256:base",
    )
    second = record_edit(
        first, "/x2.png", "sha256:new2",
        edit_instruction="edit 2", edit_args={"seed": 8, "model": "mlx/flux2-klein-4b"},
        parent_content_hash="sha256:new1",
    )
    for chain_entry in second["edit_chain"]:
        assert "seed" in chain_entry["edit_args"]


def test_record_edit_records_cloud_provenance():
    prior = _base_entry(backend="cloud_fallback")
    new_entry = record_edit(
        prior, "/x.png", "sha256:new",
        edit_instruction="darken sky", edit_args={"seed": 1, "model": "mlx/flux2-klein-4b"},
        parent_content_hash="sha256:base",
    )
    assert new_entry["edit_chain"][0]["parent_backend"] == "cloud_fallback"


def test_record_edit_model_used_reflects_edit_model():
    prior = _base_entry(model_used="x/flux2-klein:9b")
    new_entry = record_edit(
        prior, "/x.png", "sha256:new",
        edit_instruction="darken sky", edit_args={"seed": 1, "model": "mlx/flux2-klein-4b"},
        parent_content_hash="sha256:base",
    )
    assert new_entry["model_used"] == "mlx/flux2-klein-4b"
