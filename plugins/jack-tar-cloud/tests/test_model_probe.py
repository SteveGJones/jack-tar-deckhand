"""Tests for live provider discovery (EPIC #125, issue #129).

Classification and candidate logic are pure functions over injected probe
results — no network. The probe functions themselves are tested only for
their graceful-skip paths (no credentials / SDK missing); live listing is
exercised manually via /verify.
"""
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from src.model_catalog import load_catalog  # noqa: E402
from src import model_probe  # noqa: E402

SHIPPED = PLUGIN_ROOT / "src" / "model-catalog.json"


@pytest.fixture
def catalog(tmp_path):
    return load_catalog(
        shipped_path=SHIPPED,
        cache_path=tmp_path / "no-cache.json",
        local_config_path=tmp_path / "no-local.json",
    )


def _verdict(entries, model_id):
    return next(e for e in entries if e["model"] == model_id)


class _FakeCatalog:
    """Minimal stand-in exposing only the ``entries()`` surface classify_entries
    and find_new_candidates need — lets local-provider retirement tests inject
    entries the real shipped catalog doesn't currently carry."""

    def __init__(self, entries):
        self._entries = entries

    def entries(self, role=None, provider=None, status="active"):
        out = self._entries
        if status is not None:
            out = [e for e in out if e["status"] == status]
        if role is not None:
            out = [e for e in out if role in e.get("roles", [])]
        if provider is not None:
            out = [e for e in out if e["provider"] == provider]
        return out


def _make_complete_snapshot(hub_dir, repo_id, revision="abc123"):
    """Build a minimal complete HF-cache snapshot for repo_id under hub_dir."""
    repo_dir = hub_dir / ("models--" + repo_id.replace("/", "--"))
    blobs_dir = repo_dir / "blobs"
    blobs_dir.mkdir(parents=True)
    blob_path = blobs_dir / "deadbeef"
    blob_path.write_bytes(b"weights")
    snapshot_dir = repo_dir / "snapshots" / revision
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "model.safetensors").symlink_to(blob_path)
    refs_dir = repo_dir / "refs"
    refs_dir.mkdir(parents=True)
    (refs_dir / "main").write_text(revision)
    return repo_dir


class TestClassification:
    def test_upstream_listed_model_is_verified(self, catalog):
        probes = {"google": {"status": "ok", "models": {
            "gemini-3.1-flash-image", "gemini-3-pro-image", "gemini-3.5-flash",
        }}}
        entries = model_probe.classify_entries(catalog, probes)
        assert _verdict(entries, "gemini-3.1-flash-image")["verdict"] == "verified"

    def test_unlisted_active_model_is_suspect_retired(self, catalog):
        """The issue #123 failure mode, caught before a deck build 404s."""
        probes = {"google": {"status": "ok", "models": {"gemini-3.5-flash"}}}
        entries = model_probe.classify_entries(catalog, probes)
        flash = _verdict(entries, "gemini-3.1-flash-image")
        assert flash["verdict"] == "suspect_retired"
        assert "refresh-models" in flash["note"]

    def test_retired_and_unlisted_is_confirmed(self, catalog):
        probes = {"google": {"status": "ok", "models": {"gemini-3.5-flash"}}}
        entries = model_probe.classify_entries(catalog, probes)
        assert _verdict(entries, "gemini-2.0-flash")["verdict"] == "confirmed_retired"

    def test_retired_but_still_listed_flags_unretire(self, catalog):
        probes = {"google": {"status": "ok", "models": {"gemini-2.0-flash"}}}
        entries = model_probe.classify_entries(catalog, probes)
        verdict = _verdict(entries, "gemini-2.0-flash")
        assert verdict["verdict"] == "verified"
        assert "un-retiring" in verdict["note"]

    def test_alias_match_counts_as_verified(self, catalog):
        """An API still listing only the old '-preview' alias verifies the entry."""
        probes = {"google": {"status": "ok",
                             "models": {"gemini-3.1-flash-image-preview"}}}
        entries = model_probe.classify_entries(catalog, probes)
        assert _verdict(entries, "gemini-3.1-flash-image")["verdict"] == "verified"

    def test_ollama_tag_prefix_matches(self, catalog):
        probes = {"ollama": {"status": "ok", "models": {"x/flux2-klein:9b"}}}
        entries = model_probe.classify_entries(catalog, probes)
        assert _verdict(entries, "x/flux2-klein")["verdict"] == "verified"
        # x/z-image-turbo is an ollama (LOCAL_PROVIDERS) entry not in the
        # probe set — issue #124 review M3: local absence means "not pulled
        # here", never "retired". Updated from suspect_retired.
        assert _verdict(entries, "x/z-image-turbo")["verdict"] == "not_installed"

    def test_ollama_entry_not_installed_when_not_pulled(self, catalog):
        """LOCAL_PROVIDERS classification (issue #124 review M3): an ollama
        model not present in the probe set is not_installed, with a
        remediation note naming the exact pull command — never
        suspect_retired."""
        probes = {"ollama": {"status": "ok", "models": {"x/flux2-klein:9b"}}}
        entries = model_probe.classify_entries(catalog, probes)
        verdict = _verdict(entries, "x/z-image-turbo")
        assert verdict["verdict"] == "not_installed"
        assert "ollama pull x/z-image-turbo" in verdict["note"]

    def test_mlx_entry_matches_on_hf_repo(self, catalog):
        """mlx catalog ids (mlx/flux2-klein-4b) don't appear upstream — the
        probe returns HF repo ids, so classify_entries must match on
        sdk.hf_repo/sdk.hf_repo_fallback instead (design §4.2)."""
        probes = {"mlx": {"status": "ok",
                          "models": {"Runpod/FLUX.2-klein-4B-mflux-4bit"}}}
        entries = model_probe.classify_entries(catalog, probes)
        assert _verdict(entries, "mlx/flux2-klein-4b")["verdict"] == "verified"

    def test_mlx_entry_not_installed_when_repo_absent(self, catalog):
        """REPLACES the previously-designed test_mlx_entry_suspect_when_repo_absent
        (review M3 ruling pinned the wrong behaviour) — a catalogued mlx
        entry whose hf_repo is absent from the probe set is simply not
        cached locally, never suspect_retired."""
        probes = {"mlx": {"status": "ok", "models": set()}}
        entries = model_probe.classify_entries(catalog, probes)
        verdict = _verdict(entries, "mlx/flux2-klein-4b")
        assert verdict["verdict"] == "not_installed"
        assert "hf download Runpod/FLUX.2-klein-4B-mflux-4bit" in verdict["note"]

    def test_local_retired_entry_still_confirmed_retired(self):
        """Retirement status is checked BEFORE the LOCAL_PROVIDERS branch —
        a retired local entry stays confirmed_retired, never not_installed."""
        catalog = _FakeCatalog([
            {"id": "x/some-old-model", "provider": "ollama",
             "status": "retired", "aliases": [], "roles": []},
        ])
        entries = model_probe.classify_entries(
            catalog, {"ollama": {"status": "ok", "models": set()}})
        assert _verdict(entries, "x/some-old-model")["verdict"] == "confirmed_retired"

    def test_fal_recraft_always_unprobed(self, catalog):
        entries = model_probe.classify_entries(catalog, {})
        assert _verdict(entries, "fal-ai/flux-2-pro")["verdict"] == "unprobed"
        assert _verdict(entries, "recraft-v4-svg")["verdict"] == "unprobed"

    def test_skipped_probe_yields_unprobed_with_reason(self, catalog):
        probes = {"google": {"status": "skipped", "reason": "no key"}}
        entries = model_probe.classify_entries(catalog, probes)
        verdict = _verdict(entries, "gemini-3-pro-image")
        assert verdict["verdict"] == "unprobed"
        assert verdict["note"] == "no key"


class TestCandidates:
    def test_unknown_relevant_model_is_candidate(self, catalog):
        probes = {"google": {"status": "ok", "models": {
            "gemini-3.1-flash-image",       # known
            "gemini-4.0-flash-image",       # NEW — candidate
            "text-embedding-004",           # irrelevant — filtered out
        }}}
        candidates = model_probe.find_new_candidates(catalog, probes)
        assert candidates == {"google": ["gemini-4.0-flash-image"]}

    def test_alias_covered_model_is_not_candidate(self, catalog):
        probes = {"google": {"status": "ok",
                             "models": {"gemini-3-pro-image-preview"}}}
        assert model_probe.find_new_candidates(catalog, probes) == {}

    def test_installed_tag_of_known_prefix_is_not_candidate(self, catalog):
        probes = {"ollama": {"status": "ok",
                             "models": {"x/flux2-klein:4b", "x/new-model:7b"}}}
        candidates = model_probe.find_new_candidates(catalog, probes)
        assert candidates == {"ollama": ["x/new-model:7b"]}

    def test_skipped_probes_contribute_nothing(self, catalog):
        probes = {"openai": {"status": "skipped", "reason": "no key"}}
        assert model_probe.find_new_candidates(catalog, probes) == {}

    def test_mlx_candidate_filter_matches_mflux_suffix(self, catalog):
        """A cached mflux-quantized repo no catalog entry covers is a
        candidate under the mlx provider (design §4.4 substring filter)."""
        probes = {"mlx": {"status": "ok", "models": {"Foo/Bar-mflux-8bit"}}}
        candidates = model_probe.find_new_candidates(catalog, probes)
        assert candidates == {"mlx": ["Foo/Bar-mflux-8bit"]}

    def test_mlx_hf_repo_not_reported_as_candidate(self, catalog):
        """A catalogued mlx hf_repo (primary) must never be reported as a
        new candidate even though it matches the -mflux- substring filter."""
        probes = {"mlx": {"status": "ok",
                          "models": {"Runpod/FLUX.2-klein-4B-mflux-4bit"}}}
        assert model_probe.find_new_candidates(catalog, probes) == {}


class TestGracefulSkips:
    def test_google_skips_without_credentials(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        result = model_probe.probe_google_models()
        assert result["status"] == "skipped"
        assert "credentials" in result["reason"]

    def test_openai_skips_without_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        result = model_probe.probe_openai_models()
        assert result["status"] == "skipped"

    def test_ollama_skips_when_unreachable(self):
        result = model_probe.probe_ollama_models(endpoint="http://localhost:1")
        assert result["status"] == "skipped"

    def test_probe_mlx_skipped_when_cli_absent(self, monkeypatch):
        monkeypatch.setattr(model_probe.shutil, "which", lambda name: None)
        result = model_probe.probe_mlx_models()
        assert result["status"] == "skipped"
        assert "mflux" in result["reason"]

    def test_probe_mlx_lists_complete_snapshot_repos(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            model_probe.shutil, "which", lambda name: f"/usr/local/bin/{name}")
        hub_dir = tmp_path / "hub"
        hub_dir.mkdir(parents=True)
        _make_complete_snapshot(hub_dir, "Runpod/FLUX.2-klein-4B-mflux-4bit")
        result = model_probe.probe_mlx_models(hf_home=tmp_path)
        assert result["status"] == "ok"
        assert "Runpod/FLUX.2-klein-4B-mflux-4bit" in result["models"]

    def test_probe_mlx_honours_hf_hub_cache_env(self, tmp_path, monkeypatch):
        """HF_HUB_CACHE IS the hub dir directly (review m7) — no ``hub/``
        child appended, unlike the ``hf_home`` arg / HF_HOME precedence."""
        monkeypatch.setattr(
            model_probe.shutil, "which", lambda name: f"/usr/local/bin/{name}")
        hub_dir = tmp_path / "custom-hub"
        hub_dir.mkdir(parents=True)
        _make_complete_snapshot(hub_dir, "Runpod/FLUX.2-klein-4B-mflux-4bit")
        monkeypatch.setenv("HF_HUB_CACHE", str(hub_dir))
        monkeypatch.delenv("HF_HOME", raising=False)
        result = model_probe.probe_mlx_models()
        assert result["status"] == "ok"
        assert "Runpod/FLUX.2-klein-4B-mflux-4bit" in result["models"]


class TestReport:
    def test_report_shape_with_injected_probes(self, catalog):
        probes = {
            "google": {"status": "ok", "models": {"gemini-3.5-flash"}},
            "openai": {"status": "skipped", "reason": "no key"},
        }
        report = model_probe.probe_report(catalog=catalog, probes=probes)
        assert report["catalog_version"] == catalog.version
        # probe summaries never leak the full model sets into the report
        assert "models" not in report["probes"]["google"]
        assert report["probes"]["openai"]["reason"] == "no key"
        assert any(e["verdict"] == "suspect_retired" for e in report["entries"])

    def test_report_includes_mlx_probe(self, catalog, monkeypatch):
        """probe_report()'s default probes dict gains an mlx entry (§4.4) —
        checked here with the default (no injected probes) path so the
        wiring itself, not just injected-probe plumbing, is covered."""
        monkeypatch.setattr(
            model_probe, "probe_google_models",
            lambda: {"status": "skipped", "reason": "no key"})
        monkeypatch.setattr(
            model_probe, "probe_openai_models",
            lambda: {"status": "skipped", "reason": "no key"})
        monkeypatch.setattr(
            model_probe, "probe_ollama_models",
            lambda: {"status": "skipped", "reason": "unreachable"})
        monkeypatch.setattr(
            model_probe, "probe_mlx_models",
            lambda: {"status": "skipped", "reason": "no mflux"})
        report = model_probe.probe_report(catalog=catalog)
        assert "mlx" in report["probes"]
        assert report["probes"]["mlx"]["reason"] == "no mflux"
