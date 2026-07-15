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
        assert _verdict(entries, "x/z-image-turbo")["verdict"] == "suspect_retired"

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
