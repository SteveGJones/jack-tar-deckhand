"""Model catalog integrity — EPIC #125, issue #126.

Three guarantees:

1. **Copy identity** — the canonical catalog + loader at the repo top level
   and the vendored copies inside each consumer plugin are byte-identical.
   (Same pattern as the router capability drift test: the canonical artifact
   is authoritative; plugin copies are distribution details.)
2. **Schema validity** — the catalog validates against
   model-catalog/model-catalog.schema.json (full JSON-Schema, not just the
   loader's structural check).
3. **Price agreement** — the cloud module's tables are DERIVED from the
   catalog since #127; these tests now guard the derivation logic (a
   derivation bug would desynchronise them). The alias assertions also
   prove the retired '-preview' ids still resolve.
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

CANONICAL_PROBE = WORKTREE / "src" / "model_probe.py"
VENDORED_PROBE = [
    CLOUD_ROOT / "src" / "model_probe.py",
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

    @pytest.mark.parametrize("vendored", VENDORED_PROBE, ids=lambda p: p.parts[-3])
    def test_probe_copies_identical(self, vendored):
        assert vendored.read_bytes() == CANONICAL_PROBE.read_bytes(), (
            f"{vendored} has drifted from {CANONICAL_PROBE} — edit the "
            f"canonical file and re-copy: cp {CANONICAL_PROBE} {vendored}"
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


class TestEditCapability:
    """Issue #143 (edit tier, PR C) — every model advertising the
    image_edit role must carry a working sdk.edit_entrypoint, and its
    edit RAM floor must never be cheaper than its generate RAM floor
    (qwen-edit is a materially heavier 64 GB tier per upstream mflux
    #420 — edit_min_ram_gb encodes that asymmetry as a separate field,
    never a reuse of min_ram_gb)."""

    @pytest.fixture
    def catalog(self):
        return json.loads(CANONICAL_CATALOG.read_text())

    def test_image_edit_role_entries_have_edit_entrypoint(self, catalog):
        offenders = []
        for entry in catalog["models"]:
            if "image_edit" in entry.get("roles", []):
                sdk = entry.get("sdk", {})
                if not sdk.get("edit_entrypoint"):
                    offenders.append(entry["id"])
        assert not offenders, (
            f"image_edit-role entries missing sdk.edit_entrypoint: {offenders}"
        )

    def test_edit_min_ram_not_below_generate_min_ram(self, catalog):
        for entry in catalog["models"]:
            if "image_edit" not in entry.get("roles", []):
                continue
            caps = entry.get("capabilities", {})
            min_ram = caps.get("min_ram_gb")
            edit_min_ram = caps.get("edit_min_ram_gb")
            assert min_ram is not None and edit_min_ram is not None, (
                f"{entry['id']}: image_edit role requires both min_ram_gb "
                f"and edit_min_ram_gb"
            )
            assert edit_min_ram >= min_ram, (
                f"{entry['id']}: edit_min_ram_gb ({edit_min_ram}) is below "
                f"min_ram_gb ({min_ram}) — the edit path can never be "
                f"cheaper than the generate path"
            )

    def test_non_edit_capable_entries_have_no_edit_entrypoint(self, catalog):
        """z-image-turbo ships no mflux edit CLI — the absence of
        edit_entrypoint (not a stray/unused one) is the contract."""
        for entry in catalog["models"]:
            if entry["provider"] != "mlx":
                continue
            if "image_edit" in entry.get("roles", []):
                continue
            sdk = entry.get("sdk", {})
            assert "edit_entrypoint" not in sdk, (
                f"{entry['id']}: has sdk.edit_entrypoint but is missing "
                f"the image_edit role — roles/sdk have drifted"
            )


class TestPriceAgreementWithLegacyTables:
    """The cloud module's tables derive from the catalog (#127); these
    assertions guard the derivation — a bug in the derivation loops would
    desynchronise catalog.cost() from the module tables. Alias-keyed
    assertions also prove retired '-preview' ids still resolve."""

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
