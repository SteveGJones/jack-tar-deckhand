"""Tests for the model catalog refresh mechanism (EPIC #125, issue #128).

Pins the release-decoupling safety properties: validated-before-write,
atomic swap with rollback copy, operator-gate diff correctness, and
graceful rejection of bad/incompatible remotes.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from src.model_catalog import (  # noqa: E402
    LOADER_VERSION,
    CatalogError,
    load_catalog,
)
from src import model_catalog_refresh as refresh  # noqa: E402

SHIPPED = PLUGIN_ROOT / "src" / "model-catalog.json"


@pytest.fixture
def shipped_doc():
    return json.loads(SHIPPED.read_text())


@pytest.fixture
def cache(tmp_path, monkeypatch):
    """Isolated cache path — tests never touch the real ~/.jack-tar."""
    path = tmp_path / "cache" / "model-catalog.json"
    monkeypatch.setenv("JACK_TAR_CATALOG_CACHE", str(path))
    return path


class TestDiff:
    def test_no_changes_yields_empty_diff(self, shipped_doc):
        diff = refresh.diff_catalogs(shipped_doc, copy.deepcopy(shipped_doc))
        assert diff["price_changes"] == []
        assert diff["added_models"] == []
        assert diff["removed_models"] == []
        assert diff["status_changes"] == []

    def test_price_change_detected(self, shipped_doc):
        new_doc = copy.deepcopy(shipped_doc)
        for entry in new_doc["models"]:
            if entry["id"] == "gemini-3-pro-image":
                entry["pricing"]["per_resolution"]["4K"] = 0.26
        diff = refresh.diff_catalogs(shipped_doc, new_doc)
        assert diff["price_changes"] == [{
            "model": "gemini-3-pro-image",
            "component": "per_resolution.4K",
            "old": 0.24,
            "new": 0.26,
        }]

    def test_status_change_carries_replacement(self, shipped_doc):
        new_doc = copy.deepcopy(shipped_doc)
        for entry in new_doc["models"]:
            if entry["id"] == "gemini-2.5-flash":
                entry["status"] = "retired"
        diff = refresh.diff_catalogs(shipped_doc, new_doc)
        assert diff["status_changes"] == [{
            "model": "gemini-2.5-flash",
            "old": "deprecated",
            "new": "retired",
            "replacement": "gemini-3.5-flash",
        }]

    def test_added_and_removed_models(self, shipped_doc):
        new_doc = copy.deepcopy(shipped_doc)
        new_doc["models"] = [
            e for e in new_doc["models"] if e["id"] != "fal-ai/ideogram/v3"
        ]
        new_doc["models"].append({
            "id": "mlx/flux-dev", "provider": "mlx", "status": "active",
            "replacement": None, "roles": ["local_draft"],
        })
        diff = refresh.diff_catalogs(shipped_doc, new_doc)
        assert diff["added_models"] == ["mlx/flux-dev"]
        assert diff["removed_models"] == ["fal-ai/ideogram/v3"]


class TestFetch:
    def test_fetch_validates_remote(self, monkeypatch, shipped_doc):
        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return shipped_doc

        import requests
        monkeypatch.setattr(requests, "get", lambda url, timeout: FakeResponse())
        doc = refresh.fetch_remote_catalog(url="https://example.test/catalog.json")
        assert doc["catalog_version"] == shipped_doc["catalog_version"]

    def test_fetch_rejects_incompatible_remote(self, monkeypatch, shipped_doc):
        bad = copy.deepcopy(shipped_doc)
        bad["min_loader_version"] = LOADER_VERSION + 1

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return bad

        import requests
        monkeypatch.setattr(requests, "get", lambda url, timeout: FakeResponse())
        with pytest.raises(CatalogError, match="loader version"):
            refresh.fetch_remote_catalog(url="https://example.test/catalog.json")

    def test_fetch_wraps_network_errors(self, monkeypatch):
        import requests

        def boom(url, timeout):
            raise requests.ConnectionError("no route to host")

        monkeypatch.setattr(requests, "get", boom)
        with pytest.raises(CatalogError, match="cannot fetch"):
            refresh.fetch_remote_catalog(url="https://example.test/catalog.json")


class TestApplyAndRollback:
    def test_apply_writes_cache_and_loader_prefers_it(self, cache, shipped_doc, tmp_path):
        new_doc = copy.deepcopy(shipped_doc)
        new_doc["catalog_version"] = "1.1.0"
        summary = refresh.apply_refresh(new_doc, cache_path=cache)
        assert summary["version"] == "1.1.0"
        assert summary["previous_kept"] is False

        catalog = load_catalog(
            shipped_path=SHIPPED, cache_path=cache,
            local_config_path=tmp_path / "none.json",
        )
        assert catalog.version == "1.1.0"
        assert catalog.source.startswith("cached:")

    def test_apply_rejects_invalid_doc_without_touching_cache(self, cache):
        with pytest.raises(CatalogError):
            refresh.apply_refresh({"not": "a catalog"}, cache_path=cache)
        assert not cache.exists()

    def test_second_apply_keeps_previous_for_rollback(self, cache, shipped_doc):
        v1 = copy.deepcopy(shipped_doc)
        v1["catalog_version"] = "1.1.0"
        refresh.apply_refresh(v1, cache_path=cache)

        v2 = copy.deepcopy(shipped_doc)
        v2["catalog_version"] = "1.2.0"
        summary = refresh.apply_refresh(v2, cache_path=cache)
        assert summary["previous_kept"] is True
        assert json.loads(cache.read_text())["catalog_version"] == "1.2.0"

        restored = refresh.rollback(cache_path=cache)
        assert restored["version"] == "1.1.0"
        assert json.loads(cache.read_text())["catalog_version"] == "1.1.0"

    def test_rollback_without_previous_raises(self, cache):
        with pytest.raises(CatalogError, match="no previous catalog"):
            refresh.rollback(cache_path=cache)


class TestCheckRemote:
    def test_check_remote_is_read_only(self, cache, monkeypatch, shipped_doc, tmp_path):
        new_doc = copy.deepcopy(shipped_doc)
        new_doc["catalog_version"] = "2.0.0"
        for entry in new_doc["models"]:
            if entry["id"] == "gemini-3.1-flash-image":
                entry["pricing"]["per_resolution"]["1K"] = 0.07

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return new_doc

        import requests
        monkeypatch.setattr(requests, "get", lambda url, timeout: FakeResponse())
        result = refresh.check_remote(
            url="https://example.test/catalog.json",
            cache_path=cache,
            local_config_path=tmp_path / "none.json",
        )
        assert result["diff"]["version"]["new"] == "2.0.0"
        assert any(
            c["component"] == "per_resolution.1K" and c["new"] == 0.07
            for c in result["diff"]["price_changes"]
        )
        assert not cache.exists()  # nothing written


class TestStaleness:
    def test_staleness_on_shipped_baseline(self, cache, tmp_path):
        report = refresh.staleness_report(
            cache_path=cache, local_config_path=tmp_path / "none.json",
        )
        assert report["source"] == "shipped"
        assert "cache_age_days" not in report

    def test_staleness_reports_cache_age(self, cache, shipped_doc, tmp_path):
        v1 = copy.deepcopy(shipped_doc)
        v1["catalog_version"] = "1.1.0"
        refresh.apply_refresh(v1, cache_path=cache)
        report = refresh.staleness_report(
            cache_path=cache, local_config_path=tmp_path / "none.json",
        )
        assert report["version"] == "1.1.0"
        assert report["cache_age_days"] >= 0.0
