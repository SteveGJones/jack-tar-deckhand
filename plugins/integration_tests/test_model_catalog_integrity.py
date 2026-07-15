"""Model catalog integrity — EPIC #125, issue #126.

Three guarantees:

1. **Copy identity** — the canonical catalog + loader at the repo top level
   and the vendored copies inside each consumer plugin are byte-identical.
   (Same pattern as the router capability drift test: the canonical artifact
   is authoritative; plugin copies are distribution details.)
2. **Schema validity** — the catalog validates against
   model-catalog/model-catalog.schema.json (full JSON-Schema, not just the
   loader's structural check).
3. **Price agreement** — while the legacy hardcoded tables still exist
   (until issue #127 deletes them), the catalog and the cloud module's
   estimators must agree. The catalog's alias resolution bridges the old
   '-preview' ids the cloud module still uses.
"""
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

WORKTREE = Path(__file__).resolve().parents[2]
CANONICAL_DIR = WORKTREE / "model-catalog"
CANONICAL_CATALOG = CANONICAL_DIR / "model-catalog.json"
CANONICAL_SCHEMA = CANONICAL_DIR / "model-catalog.schema.json"
CANONICAL_LOADER = WORKTREE / "src" / "model_catalog.py"

CLOUD_ROOT = WORKTREE / "plugins" / "jack-tar-cloud"
DECKHAND_ROOT = WORKTREE / "plugins" / "jack-tar-deckhand"

VENDORED_CATALOGS = [
    CLOUD_ROOT / "src" / "model-catalog.json",
    DECKHAND_ROOT / "src" / "model-catalog.json",
]
VENDORED_LOADERS = [
    CLOUD_ROOT / "src" / "model_catalog.py",
    DECKHAND_ROOT / "src" / "model_catalog.py",
]

CANONICAL_REFRESH = WORKTREE / "src" / "model_catalog_refresh.py"
VENDORED_REFRESH = [
    CLOUD_ROOT / "src" / "model_catalog_refresh.py",
]

PLUGIN_ROOT = CLOUD_ROOT  # for the conftest src-namespace isolation fixture


class TestCopyIdentity:
    @pytest.mark.parametrize("vendored", VENDORED_CATALOGS, ids=lambda p: p.parts[-3])
    def test_catalog_copies_identical(self, vendored):
        assert vendored.read_bytes() == CANONICAL_CATALOG.read_bytes(), (
            f"{vendored} has drifted from {CANONICAL_CATALOG} — edit the "
            f"canonical file and re-copy: cp {CANONICAL_CATALOG} {vendored}"
        )

    @pytest.mark.parametrize("vendored", VENDORED_LOADERS, ids=lambda p: p.parts[-3])
    def test_loader_copies_identical(self, vendored):
        assert vendored.read_bytes() == CANONICAL_LOADER.read_bytes(), (
            f"{vendored} has drifted from {CANONICAL_LOADER} — edit the "
            f"canonical file and re-copy: cp {CANONICAL_LOADER} {vendored}"
        )

    @pytest.mark.parametrize("vendored", VENDORED_REFRESH, ids=lambda p: p.parts[-3])
    def test_refresh_copies_identical(self, vendored):
        assert vendored.read_bytes() == CANONICAL_REFRESH.read_bytes(), (
            f"{vendored} has drifted from {CANONICAL_REFRESH} — edit the "
            f"canonical file and re-copy: cp {CANONICAL_REFRESH} {vendored}"
        )


class TestGeneratedDoc:
    def test_docs_model_catalog_md_is_current(self):
        """docs/model-catalog.md is a build artifact of the catalog — it must
        be regenerated in the same commit that edits model-catalog.json
        (same pattern as the SmartArt catalog markdown drift check)."""
        result = subprocess.run(
            [sys.executable, str(CANONICAL_DIR / "catalog_markdown.py"), "--check"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr


class TestNoStaleModelIds:
    """Retired model ids must not reappear in source or operational docs.

    The retired '-preview' Gemini ids and the thinking-model VLM config
    (issues #121/#122/#123) live ONLY as catalog aliases/entries now. This
    guard walks every plugin's src and skills tree so a stale id cannot
    silently return in a future edit.
    """

    FORBIDDEN = (
        "gemini-3.1-flash-image-preview",
        "gemini-3-pro-image-preview",
        "--vlm-model gemini-2.5-flash",
        "--vlm-model gemini-2.0-flash",
    )

    # The catalog itself legitimately carries retired names as aliases.
    EXEMPT_NAMES = {"model-catalog.json"}

    def test_no_stale_ids_in_plugin_sources_or_skills(self):
        offenders = []
        for pattern in ("plugins/*/src/**/*.py", "plugins/*/skills/**/*.md",
                        "plugins/*/agents/*.md", "plugins/*/CLAUDE.md"):
            for path in WORKTREE.glob(pattern):
                if path.name in self.EXEMPT_NAMES:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                for needle in self.FORBIDDEN:
                    if needle in text:
                        offenders.append(f"{path.relative_to(WORKTREE)}: {needle}")
        assert not offenders, (
            "Stale model ids found — the catalog is the only place retired "
            "names may live (as aliases):\n" + "\n".join(offenders)
        )


class TestSchemaValidity:
    def test_catalog_validates_against_schema(self):
        catalog = json.loads(CANONICAL_CATALOG.read_text())
        schema = json.loads(CANONICAL_SCHEMA.read_text())
        jsonschema.validate(catalog, schema)

    def test_schema_itself_is_valid_draft07(self):
        schema = json.loads(CANONICAL_SCHEMA.read_text())
        jsonschema.Draft7Validator.check_schema(schema)


class TestPriceAgreementWithLegacyTables:
    """Until #127 deletes the hardcoded tables, catalog and code must agree.

    The cloud module still keys its tables by the retired '-preview' ids;
    the catalog resolves those via aliases — asserting through the alias
    proves both the price AND the alias mapping.
    """

    @pytest.fixture
    def catalog(self, tmp_path):
        sys.path.insert(0, str(CLOUD_ROOT))
        from src.model_catalog import load_catalog
        return load_catalog(
            shipped_path=CLOUD_ROOT / "src" / "model-catalog.json",
            cache_path=tmp_path / "no-cache.json",
            local_config_path=tmp_path / "no-local.json",
        )

    def test_nano_banana_costs_match(self, catalog):
        from src.generate_cloud_image import _NANO_BANANA_COSTS
        for (legacy_model, resolution), expected in _NANO_BANANA_COSTS.items():
            assert catalog.cost(legacy_model, resolution=resolution) == expected, (
                f"{legacy_model}@{resolution}: catalog disagrees with "
                f"_NANO_BANANA_COSTS"
            )

    def test_imagen_costs_match_both_backends(self, catalog):
        from src.generate_cloud_image import (
            _IMAGEN_DEVELOPER_COSTS,
            _IMAGEN_VERTEX_COSTS,
        )
        for backend, table in [
            ("vertex", _IMAGEN_VERTEX_COSTS),
            ("developer", _IMAGEN_DEVELOPER_COSTS),
        ]:
            for (model, resolution), expected in table.items():
                assert catalog.cost(
                    model, resolution=resolution, backend=backend
                ) == expected

    def test_openai_costs_match(self, catalog):
        from src.generate_cloud_image import _OPENAI_COSTS
        for (size, quality), expected in _OPENAI_COSTS.items():
            assert catalog.cost("gpt-image-1.5", size=size, quality=quality) == expected

    def test_fal_flat_costs_match(self, catalog):
        from src.generate_cloud_image import _FAL_FLAT_COSTS
        for model, expected in _FAL_FLAT_COSTS.items():
            assert catalog.cost(model) == expected

    def test_fal_tiered_costs_match(self, catalog):
        from src.generate_cloud_image import _FAL_TIERED_COSTS
        for model, (first_mp, per_extra) in _FAL_TIERED_COSTS.items():
            entry = catalog.get(model)
            rates = entry["pricing"]["tiered_megapixel"]
            assert (rates["first_mp"], rates["per_extra_mp"]) == (first_mp, per_extra)

    def test_recraft_costs_match(self, catalog, monkeypatch):
        monkeypatch.delenv("RECRAFT_UPSCALE_COST_USD", raising=False)
        from src.generate_cloud_image import estimate_recraft_cost
        assert catalog.cost("recraft-v4-standard", resolution="1K") == \
            estimate_recraft_cost(tier="standard", resolution="1K")
        assert catalog.cost("recraft-v4-pro", resolution="2K") == \
            estimate_recraft_cost(tier="pro", resolution="2K")
        assert catalog.cost("recraft-v4-pro", resolution="4K") == \
            estimate_recraft_cost(tier="pro", resolution="4K")

    def test_model_resolutions_match(self, catalog):
        from src.generate_cloud_image import _MODEL_RESOLUTIONS
        for legacy_model, expected in _MODEL_RESOLUTIONS.items():
            assert catalog.resolutions(legacy_model) == expected, (
                f"{legacy_model}: catalog capability disagrees with "
                f"_MODEL_RESOLUTIONS"
            )

    def test_icon_costs_match(self, catalog):
        from src.generate_cloud_icon import _ICON_COSTS
        for (provider, tier), expected in _ICON_COSTS.items():
            assert catalog.cost("recraft-v4-svg", tier=tier) == expected, (
                f"icon {provider}/{tier}: catalog disagrees with _ICON_COSTS"
            )

    def test_cascade_tier_costs_match(self, catalog, monkeypatch):
        """cascade.py TIER_COSTS is the deckhand projection of cloud pricing;
        the catalog must agree with every cascade tier."""
        monkeypatch.delenv("RECRAFT_UPSCALE_COST_USD", raising=False)
        sys.path.insert(0, str(DECKHAND_ROOT))
        for key in [k for k in list(sys.modules) if k == "src" or k.startswith("src.")]:
            del sys.modules[key]
        from src.creative_vision.cascade import (
            TIER_COSTS,
            TIER_TO_PROVIDER_MODEL_RESOLUTION,
        )
        deckhand_catalog_path = DECKHAND_ROOT / "src" / "model-catalog.json"
        from src.model_catalog import load_catalog as deckhand_load
        deckhand_catalog = deckhand_load(
            shipped_path=deckhand_catalog_path,
            cache_path=Path("/nonexistent/no-cache.json"),
            local_config_path=Path("/nonexistent/no-local.json"),
        )
        for tier, (provider, model, resolution) in TIER_TO_PROVIDER_MODEL_RESOLUTION.items():
            if provider is None:
                continue
            assert deckhand_catalog.cost(model, resolution=resolution) == \
                TIER_COSTS[tier], f"cascade tier {tier}: catalog disagrees"
