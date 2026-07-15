"""Tests for the model catalog loader (EPIC #125, issue #126).

The catalog is the single source of truth for model identity, capability,
and pricing. These tests pin the loader's behaviour: alias resolution,
retired-model substitution, role selection, the pricing shapes, and the
three-layer precedence merge (shipped -> cached remote -> local overrides).
"""
import json
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from src.model_catalog import (  # noqa: E402
    LOADER_VERSION,
    CatalogError,
    ModelCatalog,
    PricingError,
    UnknownModelError,
    load_catalog,
    validate_catalog,
)

SHIPPED = PLUGIN_ROOT / "src" / "model-catalog.json"


@pytest.fixture
def catalog(tmp_path):
    """Shipped catalog with the remote cache pointed at a non-existent file
    so a developer's real ~/.jack-tar cache can never leak into tests."""
    return load_catalog(
        shipped_path=SHIPPED,
        cache_path=tmp_path / "no-cache.json",
        local_config_path=tmp_path / "no-local-config.json",
    )


def minimal_doc(**overrides):
    doc = {
        "catalog_version": "1.0.0",
        "min_loader_version": 1,
        "updated": "2026-07-15",
        "models": [
            {
                "id": "m1",
                "provider": "test",
                "status": "active",
                "replacement": None,
                "roles": ["image_gen"],
                "pricing": {
                    "currency": "USD",
                    "verified": "2026-07-15",
                    "estimate": False,
                    "flat": 0.01,
                },
            }
        ],
    }
    doc.update(overrides)
    return doc


class TestValidation:
    def test_shipped_catalog_is_valid(self):
        validate_catalog(json.loads(SHIPPED.read_text()))

    def test_missing_top_key_rejected(self):
        doc = minimal_doc()
        del doc["updated"]
        with pytest.raises(CatalogError, match="updated"):
            validate_catalog(doc)

    def test_future_loader_version_rejected(self):
        doc = minimal_doc(min_loader_version=LOADER_VERSION + 1)
        with pytest.raises(CatalogError, match="loader version"):
            validate_catalog(doc)

    def test_duplicate_alias_rejected(self):
        doc = minimal_doc()
        doc["models"].append(
            {
                "id": "m2",
                "provider": "test",
                "aliases": ["m1"],
                "status": "active",
                "roles": ["image_gen"],
            }
        )
        with pytest.raises(CatalogError, match="duplicate"):
            validate_catalog(doc)

    def test_retired_without_replacement_rejected(self):
        doc = minimal_doc()
        doc["models"][0]["status"] = "retired"
        doc["models"][0]["replacement"] = None
        with pytest.raises(CatalogError, match="replacement"):
            validate_catalog(doc)

    def test_unknown_replacement_rejected(self):
        doc = minimal_doc()
        doc["models"][0]["status"] = "retired"
        doc["models"][0]["replacement"] = "ghost"
        with pytest.raises(CatalogError, match="ghost"):
            validate_catalog(doc)

    def test_role_default_naming_unknown_model_rejected(self):
        doc = minimal_doc(role_defaults={"image_gen": "ghost"})
        with pytest.raises(CatalogError, match="ghost"):
            validate_catalog(doc)


class TestLookup:
    def test_get_by_id(self, catalog):
        entry = catalog.get("gemini-3.1-flash-image")
        assert entry["provider"] == "google"
        assert "resolved_from" not in entry

    def test_deprecated_preview_alias_resolves(self, catalog):
        """Issue #123: '-preview' ids retired upstream; callers holding the
        old name must land on the current one."""
        entry = catalog.get("gemini-3.1-flash-image-preview")
        assert entry["id"] == "gemini-3.1-flash-image"
        assert entry["resolved_from"] == "gemini-3.1-flash-image-preview"

    def test_retired_model_substitutes_replacement(self, catalog):
        """Issue #123: gemini-2.0-flash 404s upstream — the loader routes
        callers to the verified working replacement."""
        entry = catalog.get("gemini-2.0-flash")
        assert entry["id"] == "gemini-3.5-flash"
        assert entry["resolved_from"] == "gemini-2.0-flash"

    def test_retired_model_reachable_without_substitution(self, catalog):
        entry = catalog.get("gemini-2.0-flash", follow_replacement=False)
        assert entry["id"] == "gemini-2.0-flash"
        assert entry["status"] == "retired"

    def test_unknown_model_raises(self, catalog):
        with pytest.raises(UnknownModelError):
            catalog.get("gpt-99-vision-max")

    def test_get_returns_copy(self, catalog):
        catalog.get("gemini-3.1-flash-image")["provider"] = "mutated"
        assert catalog.get("gemini-3.1-flash-image")["provider"] == "google"


class TestRoles:
    def test_thinking_model_not_vlm_json_eligible(self, catalog):
        """Issue #122: gemini-2.5-flash's reasoning tokens break strict-JSON
        parsers — it must never come back from a vlm_json role query."""
        ids = [e["id"] for e in catalog.entries(role="vlm_json")]
        assert "gemini-2.5-flash" not in ids
        assert "gemini-3.5-flash" in ids

    def test_vlm_json_default(self, catalog):
        assert catalog.default_model("vlm_json")["id"] == "gemini-3.5-flash"

    def test_local_draft_preference_order(self, catalog):
        prefs = catalog.role_default("local_draft")
        assert prefs == ["x/flux2-klein", "x/z-image-turbo"]
        assert catalog.default_model("local_draft")["id"] == "x/flux2-klein"

    def test_icon_default(self, catalog):
        assert catalog.default_model("icon")["id"] == "recraft-v4-svg"

    def test_entries_filter_by_provider(self, catalog):
        assert all(
            e["provider"] == "ollama"
            for e in catalog.entries(provider="ollama")
        )


class TestCapabilities:
    def test_resolutions(self, catalog):
        assert catalog.resolutions("gemini-3.1-flash-image") == ["512", "1K", "2K", "4K"]
        assert catalog.resolutions("imagen-4.0-fast-generate-001") == ["1K"]

    def test_supports_normalises_case(self, catalog):
        assert catalog.supports("gemini-3-pro-image", "4k")
        assert not catalog.supports("fal-ai/flux-2-klein", "4K")

    def test_quirks(self, catalog):
        # Deprecated (not retired) entries are inspected directly — 2.5-flash
        # itself carries the thinking quirk that disqualifies it from vlm_json.
        assert catalog.has_quirk("gemini-2.5-flash", "thinking")
        assert catalog.has_quirk("imagen-4.0-fast-generate-001", "fixed_resolution")
        assert not catalog.has_quirk("gemini-3.5-flash", "thinking")

    def test_nano_banana_sdk_config_field_is_image_size(self, catalog):
        """Issue #121 ground truth: google-genai 2.11.0 accepts
        ImageConfig(image_size=...) — verified 2026-07-15. The catalog must
        carry the verified field name, not the misreported aspectRatio."""
        assert catalog.get("gemini-3.1-flash-image")["sdk"]["config_field"] == "image_size"


class TestCost:
    def test_per_resolution(self, catalog):
        assert catalog.cost("gemini-3.1-flash-image", resolution="1K") == 0.067
        assert catalog.cost("gemini-3-pro-image", resolution="4K") == 0.24

    def test_per_resolution_via_alias(self, catalog):
        assert catalog.cost("gemini-3.1-flash-image-preview", resolution="2K") == 0.101

    def test_unpriced_resolution_raises(self, catalog):
        with pytest.raises(PricingError):
            catalog.cost("gemini-3-pro-image", resolution="512")

    def test_imagen_backend_pricing(self, catalog, monkeypatch):
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        assert catalog.cost("imagen-4.0-generate-001", resolution="2K") == 0.101
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/adc.json")
        assert catalog.cost("imagen-4.0-generate-001", resolution="2K") == 0.04
        assert catalog.cost(
            "imagen-4.0-generate-001", resolution="2K", backend="developer"
        ) == 0.101

    def test_openai_size_quality(self, catalog):
        assert catalog.cost("gpt-image-1.5", size="1536x1024", quality="medium") == 0.051

    def test_icon_per_tier(self, catalog):
        assert catalog.cost("recraft-v4-svg", tier="standard") == 0.08
        assert catalog.cost("recraft-v4-svg", tier="pro") == 0.3

    def test_flat(self, catalog):
        assert catalog.cost("fal-ai/flux-2-klein") == 0.014

    def test_flat_wins_even_with_resolution_param(self, catalog):
        assert catalog.cost("x/flux2-klein", resolution="1K") == 0.0

    def test_tiered_megapixel(self, catalog):
        cost = catalog.cost("fal-ai/flux-2-pro", megapixels=2.0736)
        assert cost == pytest.approx(0.03 + 1.0736 * 0.015)

    def test_recraft_4k_chain_default(self, catalog, monkeypatch):
        monkeypatch.delenv("RECRAFT_UPSCALE_COST_USD", raising=False)
        assert catalog.cost("recraft-v4-pro", resolution="4K") == 0.5

    def test_recraft_4k_chain_env_override(self, catalog, monkeypatch):
        monkeypatch.setenv("RECRAFT_UPSCALE_COST_USD", "0.10")
        assert catalog.cost("recraft-v4-pro", resolution="4K") == pytest.approx(0.35)

    def test_recraft_4k_chain_rejects_bad_override(self, catalog, monkeypatch):
        monkeypatch.setenv("RECRAFT_UPSCALE_COST_USD", "-1")
        assert catalog.cost("recraft-v4-pro", resolution="4K") == 0.5
        monkeypatch.setenv("RECRAFT_UPSCALE_COST_USD", "banana")
        assert catalog.cost("recraft-v4-pro", resolution="4K") == 0.5

    def test_model_without_pricing_raises(self, catalog):
        with pytest.raises(PricingError):
            catalog.cost("gemini-3.5-flash", resolution="1K")


class TestPrecedence:
    def test_valid_cache_wins_over_shipped(self, tmp_path):
        doc = json.loads(SHIPPED.read_text())
        doc["catalog_version"] = "9.9.9"
        cache = tmp_path / "cache.json"
        cache.write_text(json.dumps(doc))
        catalog = load_catalog(
            shipped_path=SHIPPED,
            cache_path=cache,
            local_config_path=tmp_path / "none.json",
        )
        assert catalog.version == "9.9.9"
        assert catalog.source.startswith("cached:")

    def test_invalid_cache_falls_back_to_shipped(self, tmp_path):
        cache = tmp_path / "cache.json"
        cache.write_text("{not json")
        catalog = load_catalog(
            shipped_path=SHIPPED,
            cache_path=cache,
            local_config_path=tmp_path / "none.json",
        )
        assert catalog.source == "shipped"

    def test_incompatible_cache_falls_back_to_shipped(self, tmp_path):
        doc = json.loads(SHIPPED.read_text())
        doc["min_loader_version"] = LOADER_VERSION + 1
        cache = tmp_path / "cache.json"
        cache.write_text(json.dumps(doc))
        catalog = load_catalog(
            shipped_path=SHIPPED,
            cache_path=cache,
            local_config_path=tmp_path / "none.json",
        )
        assert catalog.source == "shipped"

    def test_local_override_patches_price(self, tmp_path):
        local = tmp_path / "local-config.json"
        local.write_text(json.dumps({
            "model_catalog": {
                "models": [{
                    "id": "fal-ai/flux-2-klein",
                    "pricing": {
                        "currency": "USD",
                        "verified": "2026-07-15",
                        "estimate": False,
                        "flat": 0.02,
                    },
                }],
            },
        }))
        catalog = load_catalog(
            shipped_path=SHIPPED,
            cache_path=tmp_path / "none.json",
            local_config_path=local,
        )
        assert catalog.cost("fal-ai/flux-2-klein") == 0.02
        assert catalog.source.endswith("+local")

    def test_local_override_adds_model(self, tmp_path):
        """The MLX seam (#124): an operator can register a locally-served
        model without waiting for a catalog release."""
        local = tmp_path / "local-config.json"
        local.write_text(json.dumps({
            "model_catalog": {
                "models": [{
                    "id": "mlx/flux-dev-q8",
                    "provider": "mlx",
                    "status": "active",
                    "replacement": None,
                    "roles": ["image_gen", "local_draft"],
                }],
                "role_defaults": {
                    "local_draft": ["mlx/flux-dev-q8", "x/flux2-klein"],
                },
            },
        }))
        catalog = load_catalog(
            shipped_path=SHIPPED,
            cache_path=tmp_path / "none.json",
            local_config_path=local,
        )
        assert catalog.get("mlx/flux-dev-q8")["provider"] == "mlx"
        assert catalog.default_model("local_draft")["id"] == "mlx/flux-dev-q8"

    def test_broken_local_override_fails_loudly(self, tmp_path):
        local = tmp_path / "local-config.json"
        local.write_text(json.dumps({
            "model_catalog": {
                "models": [{"id": "half-entry"}],
            },
        }))
        with pytest.raises(CatalogError):
            load_catalog(
                shipped_path=SHIPPED,
                cache_path=tmp_path / "none.json",
                local_config_path=local,
            )

    def test_local_config_without_catalog_key_ignored(self, tmp_path):
        local = tmp_path / "local-config.json"
        local.write_text(json.dumps({"ollama": {"model": "x/flux2-klein:9b"}}))
        catalog = load_catalog(
            shipped_path=SHIPPED,
            cache_path=tmp_path / "none.json",
            local_config_path=local,
        )
        assert catalog.source == "shipped"


class TestReplacementCycle:
    def test_cycle_detected(self):
        doc = minimal_doc()
        doc["models"] = [
            {"id": "a", "provider": "t", "status": "retired",
             "replacement": "b", "roles": ["image_gen"]},
            {"id": "b", "provider": "t", "status": "retired",
             "replacement": "a", "roles": ["image_gen"]},
        ]
        catalog = ModelCatalog(doc)
        with pytest.raises(CatalogError, match="cycle"):
            catalog.get("a")
