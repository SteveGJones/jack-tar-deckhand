"""Discover and import the jack-tar-msft-smartart plugin's surface.

The bridge needs three named symbols from the SmartArt plugin:

  - engine.render(spec, output_dir) -> RenderResult
  - InjectionRequest(slide_number, carrier_pptx, placeholder_name)
  - inject(host_pptx, requests) -> list[InjectionResult]

We resolve the plugin root via three sources in order:

  1. JACK_TAR_SUPERPOWER_BRIDGE_FORCE_MSFT_ROOT (test override)
  2. ~/.claude/plugins/cache/**/jack-tar-msft-smartart (production install)
  3. <worktree>/plugins/jack-tar-msft-smartart (local dev)

After locating, we mutate sys.path and clear sys.modules['src.*'] so the
SmartArt plugin's `from src import ...` resolves correctly even when the
bridge's own `src.*` is already imported. The import surface is named
explicitly via ALLOWED_SYMBOLS — any expansion requires a spec amendment
(supply-chain mitigation).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

ALLOWED_SYMBOLS = ("engine.render", "InjectionRequest", "inject")


class MsftSmartArtNotFoundError(RuntimeError):
    """Raised when the jack-tar-msft-smartart plugin cannot be located."""


@dataclass
class MsftSmartArtAPI:
    engine: ModuleType
    InjectionRequest: type
    inject: callable


def _candidate_roots() -> list[Path]:
    candidates: list[Path] = []
    forced = os.environ.get("JACK_TAR_SUPERPOWER_BRIDGE_FORCE_MSFT_ROOT")
    if forced:
        candidates.append(Path(forced))
        return candidates

    home = Path.home()
    cache_root = home / ".claude" / "plugins" / "cache"
    if cache_root.exists():
        for plugin_json in cache_root.rglob(
            "jack-tar-msft-smartart/.claude-plugin/plugin.json"
        ):
            candidates.append(plugin_json.parent.parent)
            break

    # Local dev — walk upwards looking for plugins/jack-tar-msft-smartart
    for parent in [Path.cwd(), *Path.cwd().parents]:
        candidate = parent / "plugins" / "jack-tar-msft-smartart"
        if candidate.exists():
            candidates.append(candidate)
            break

    return candidates


def load_msft_smartart_api() -> MsftSmartArtAPI:
    """Locate, import, and return the named SmartArt surface.

    Cross-plugin sys.modules safety: the loader snapshots the caller's
    `src.*` modules + sys.path[0] BEFORE swapping in the msft-smartart plugin
    path, then restores them after the imports complete. The returned
    MsftSmartArtAPI holds direct module references, so callers can use them
    after restoration. Subsequent `from src import ...` calls in the caller
    resolve to the caller's `src.*` (the bridge), not msft-smartart's.

    Raises MsftSmartArtNotFoundError if the plugin is missing.
    """
    candidates = _candidate_roots()
    plugin_root: Path | None = None
    for candidate in candidates:
        if (candidate / "src" / "engine.py").exists():
            plugin_root = candidate
            break
    if plugin_root is None:
        raise MsftSmartArtNotFoundError(
            "jack-tar-msft-smartart plugin not found. Install via marketplace, set "
            "JACK_TAR_SUPERPOWER_BRIDGE_FORCE_MSFT_ROOT, or run from a worktree that "
            "contains plugins/jack-tar-msft-smartart."
        )

    plugin_str = str(plugin_root)

    # Snapshot caller's state so we can restore after the import swap
    caller_path0 = sys.path[0] if sys.path else None
    caller_src_modules: dict[str, object] = {
        k: sys.modules[k] for k in list(sys.modules)
        if k == "src" or k.startswith("src.")
    }

    # Clear caller's src.* and put msft-smartart's plugin path at the front
    for key in caller_src_modules:
        del sys.modules[key]
    if plugin_str in sys.path:
        sys.path.remove(plugin_str)
    sys.path.insert(0, plugin_str)

    try:
        from src import engine as engine_mod  # type: ignore
        from src import assembler_patch as ap_mod  # type: ignore
        api = MsftSmartArtAPI(
            engine=engine_mod,
            InjectionRequest=ap_mod.InjectionRequest,
            inject=ap_mod.inject,
        )
    finally:
        # Restore caller's state — drop msft-smartart from sys.path[0],
        # delete msft-smartart's src.* (now in sys.modules under those names),
        # and put caller's src.* modules back.
        if sys.path and sys.path[0] == plugin_str:
            sys.path.pop(0)
        for key in list(sys.modules):
            if key == "src" or key.startswith("src."):
                del sys.modules[key]
        for key, mod in caller_src_modules.items():
            sys.modules[key] = mod
        # Restore caller's path[0] if it was displaced
        if caller_path0 is not None and (not sys.path or sys.path[0] != caller_path0):
            if caller_path0 in sys.path:
                sys.path.remove(caller_path0)
            sys.path.insert(0, caller_path0)
    return api
