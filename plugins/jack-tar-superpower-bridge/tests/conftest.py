"""Shared test fixtures for the superpower-bridge plugin."""
from __future__ import annotations
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PLUGIN_ROOT / "src"
FIXTURE_DIR = PLUGIN_ROOT / "tests" / "fixtures"

# Ensure the bridge plugin's src is on sys.path at conftest load time so test
# modules can `from src.X import Y` at collection time. The autouse fixture
# below clears any sibling-plugin caches per test.
_PLUGIN_STR = str(PLUGIN_ROOT)
if _PLUGIN_STR in sys.path:
    sys.path.remove(_PLUGIN_STR)
sys.path.insert(0, _PLUGIN_STR)

# Spikes hold the real /pptx output we use as test seeds. Resolved once.
WORKTREE_ROOT = PLUGIN_ROOT.parents[1]
SPIKE1_DIR = WORKTREE_ROOT / "docs" / "spikes" / "2026-04-23-pptx-marker-adherence"
SPIKE2_DIR = WORKTREE_ROOT / "docs" / "spikes" / "2026-04-23-python-pptx-enrichment"


@pytest.fixture(autouse=True)
def _ensure_plugin_src_on_path():
    """Put the bridge plugin's src on sys.path; clear sibling-plugin src caches."""
    plugin_str = str(PLUGIN_ROOT)
    for key in list(sys.modules):
        if key == "src" or key.startswith("src."):
            del sys.modules[key]
    if plugin_str in sys.path:
        sys.path.remove(plugin_str)
    sys.path.insert(0, plugin_str)
    yield


@pytest.fixture
def seed_variant_a() -> Path:
    """Real /pptx-produced deck with `objectName` markers (Spike 1 Variant A)."""
    return SPIKE1_DIR / "outputs" / "variant-a" / "presentation.pptx"


@pytest.fixture
def seed_variant_a_build() -> Path:
    """Spike 1 Variant A build.js — used for analyser orchestrator JS-fallback tests."""
    return SPIKE1_DIR / "outputs" / "variant-a" / "build.js"


@pytest.fixture
def seed_variant_b() -> Path:
    """Real /pptx-produced deck where `name:` was dropped (Spike 1 Variant B)."""
    return SPIKE1_DIR / "outputs" / "variant-b" / "presentation.pptx"


@pytest.fixture
def seed_variant_b_build() -> Path:
    """Spike 1 Variant B build.js — used for JS-fallback marker-recovery tests."""
    return SPIKE1_DIR / "outputs" / "variant-b" / "build.js"


@pytest.fixture
def seed_no_buildjs() -> Path:
    """Hand-built control deck with one named marker shape and no build.js (Spike 3 control)."""
    return SPIKE2_DIR.parent / "2026-04-23-analyser-source-comparison" / "fixtures" / "control.pptx"


@pytest.fixture
def placeholder_png() -> Path:
    """Stand-in image for background / element-image enrichment tests."""
    return SPIKE2_DIR / "seed" / "placeholder.png"
