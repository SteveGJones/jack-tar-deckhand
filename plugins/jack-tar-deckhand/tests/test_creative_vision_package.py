"""Confirms the creative_vision package and its modules are importable."""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))


def test_package_imports():
    from src.creative_vision import brief, cascade, critic, manifest, orchestrator, prompt_reviewer  # noqa: F401


def test_top_level_dispatch_imports():
    from src import creative_vision_dispatch  # noqa: F401
