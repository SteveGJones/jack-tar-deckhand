"""Cross-plugin drift guard: jack-tar-mlx wrapper vs the CANONICAL model
catalog (issue #124, design review M2).

``plugins/jack-tar-mlx/tests/test_generate_image.py`` already pins
``MLX_MODEL_REGISTRY`` against the VENDORED deckhand catalog copy
(``plugins/jack-tar-deckhand/src/model-catalog.json``). That test lives
inside the jack-tar-mlx plugin's own suite so the plugin has zero
cross-plugin import dependency.

This integration test is the complementary belt-and-braces check named in
the design (§7.5): it drifts-guards the SAME registry against the
CANONICAL catalog at ``model-catalog/model-catalog.json`` directly,
independent of the vendored-copy byte-identity guarantee already covered
by ``test_model_catalog_integrity.py::TestCopyIdentity``. If that identity
guarantee were ever weakened, this test would still catch a real
registry/catalog field mismatch.
"""
import importlib
import json
import sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parents[2]
CANONICAL_CATALOG_PATH = WORKTREE / "model-catalog" / "model-catalog.json"
MLX_SRC_DIR = WORKTREE / "plugins" / "jack-tar-mlx" / "src"

# For the conftest src-namespace isolation fixture (unused here — the mlx
# wrapper has no 'src' package, it's imported as a bare top-level module).
PLUGIN_ROOT = None


def _load_generate_image_module():
    """Import the mlx wrapper's generate_image module fresh, isolated from
    any other plugin's same-named module that may already be cached."""
    for key in list(sys.modules.keys()):
        if key == "generate_image":
            del sys.modules[key]
    src_path = str(MLX_SRC_DIR)
    inserted = src_path not in sys.path
    if inserted:
        sys.path.insert(0, src_path)
    try:
        module = importlib.import_module("generate_image")
        importlib.reload(module)
        return module
    finally:
        if inserted:
            sys.path.remove(src_path)


def _canonical_mlx_entries():
    catalog = json.loads(CANONICAL_CATALOG_PATH.read_text())
    return {
        m["id"]: m for m in catalog["models"]
        if m["provider"] == "mlx" and m.get("status") == "active"
    }


def test_canonical_catalog_has_mlx_entries():
    entries = _canonical_mlx_entries()
    assert entries, "Expected at least one active mlx/* entry in the canonical catalog"
    assert "mlx/flux2-klein-4b" in entries


def test_mlx_registry_matches_canonical_catalog_full_value():
    """Full per-field equality (review M2) — not just matching keys.

    For every active mlx/* entry in the CANONICAL catalog, the wrapper's
    MLX_MODEL_REGISTRY entry must carry identical entrypoint, hf_repo,
    hf_repo_fallback, default_steps, quantize, and timeout
    (<- capabilities.timeout_seconds) values. Key sets must match exactly
    too — no registry entry without a catalog backer, no catalog entry
    missing from the registry.
    """
    generate_image = _load_generate_image_module()
    mlx_entries = _canonical_mlx_entries()

    assert set(generate_image.MLX_MODEL_REGISTRY.keys()) == set(mlx_entries.keys()), (
        "MLX_MODEL_REGISTRY keys have drifted from the canonical catalog's "
        "active mlx/* entry ids"
    )

    for entry_id, entry in mlx_entries.items():
        sdk = entry["sdk"]
        capabilities = entry["capabilities"]
        expected = {
            "entrypoint": sdk["entrypoint"],
            "hf_repo": sdk["hf_repo"],
            "hf_repo_fallback": sdk.get("hf_repo_fallback"),
            "default_steps": sdk["default_steps"],
            "quantize": sdk["quantize"],
            "timeout": capabilities["timeout_seconds"],
        }
        actual = generate_image.MLX_MODEL_REGISTRY[entry_id]
        assert actual == expected, (
            f"{entry_id}: MLX_MODEL_REGISTRY drifted from the canonical "
            f"catalog.\n  registry: {actual}\n  catalog:  {expected}"
        )


def test_mlx_registry_default_model_is_a_valid_catalog_entry():
    generate_image = _load_generate_image_module()
    mlx_entries = _canonical_mlx_entries()
    assert generate_image.DEFAULT_MODEL in mlx_entries
