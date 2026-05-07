"""Op3: inject a pptx_native SmartArt carrier into a slide, replacing a SMARTART marker.

Discovered from inspecting the real plugin API:
  - engine.render(spec, output_dir, output_name=None) -> RenderResult with .output_path
  - assembler_patch.inject(host_pptx, [InjectionRequest(slide_number, carrier_pptx,
    placeholder_name)]) -> list[InjectionResult]
  - InjectionRequest accepts placeholder_name directly, so no shape-renaming is needed.

Plugin import strategy: add `plugins/jack-tar-msft-smartart` to sys.path so that
`from src import ...` resolves to the plugin's own src/ package. If the host
process already has a different `src` package imported (e.g. jack-tar-deckhand's
root src/), this function forces a fresh import by clearing matching entries
from sys.modules before the plugin imports run.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Union


def _load_plugin_api():
    """Import engine, assembler_patch, and InjectionRequest from the msft-smartart plugin.

    Returns a tuple (engine_module, assembler_patch_module, InjectionRequest_class).
    """
    # Repo root: this file is at
    # <root>/docs/spikes/2026-04-23-python-pptx-enrichment/prototypes/op3_inject_smartart.py
    repo_root = Path(__file__).resolve().parents[4]
    plugin_dir = repo_root / "plugins" / "jack-tar-msft-smartart"
    if not plugin_dir.exists():
        raise RuntimeError(f"msft-smartart plugin not found at {plugin_dir}")

    # Ensure the plugin's src/ wins over the repo-root src/ during import
    plugin_str = str(plugin_dir)
    if plugin_str not in sys.path:
        sys.path.insert(0, plugin_str)
    # Clear any previously-cached `src.*` modules so the plugin's src is loaded fresh
    for mod in list(sys.modules):
        if mod == "src" or mod.startswith("src."):
            del sys.modules[mod]

    from src import engine as engine_mod  # type: ignore
    from src import assembler_patch as ap_mod  # type: ignore
    return engine_mod, ap_mod, ap_mod.InjectionRequest


def inject_smartart(
    pptx_path: Union[str, Path],
    marker_name: str,
    slide_index_1based: int,
    spec: dict[str, Any],
    carriers_dir: Union[str, Path],
) -> None:
    pptx_path = Path(pptx_path)
    carriers_dir = Path(carriers_dir)
    carriers_dir.mkdir(parents=True, exist_ok=True)

    engine_mod, ap_mod, InjectionRequest = _load_plugin_api()

    # Render the carrier .pptx (single slide with one SmartArt graphic)
    render_result = engine_mod.render(spec, carriers_dir)
    carrier_path = Path(render_result.output_path)

    # Inject the carrier's diagram parts into the host, replacing the marker shape
    requests = [
        InjectionRequest(
            slide_number=slide_index_1based,
            carrier_pptx=carrier_path,
            placeholder_name=marker_name,
        )
    ]
    ap_mod.inject(pptx_path, requests)


if __name__ == "__main__":
    import json

    if len(sys.argv) != 6:
        print("usage: op3_inject_smartart.py <pptx> <marker_name> <slide_1based> <spec.json> <carriers_dir>")
        sys.exit(2)
    with open(sys.argv[4]) as f:
        spec = json.load(f)
    inject_smartart(sys.argv[1], sys.argv[2], int(sys.argv[3]), spec, sys.argv[5])
    print("ok")
