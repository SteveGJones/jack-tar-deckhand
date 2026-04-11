#!/usr/bin/env python3
"""
build_plugin_demo_deck.py — Proves the jack-tar plugin marketplace works end-to-end.

Uses plugin infrastructure (not monorepo src/) to build a complete PowerPoint deck
demonstrating the 5-plugin architecture. Imports exclusively from the plugin directories
to validate that the plugin distribution is self-contained.

Architecture note: Both jack-tar-deckhand and jack-tar-msft-smartart have a top-level
`src/` package. To avoid Python namespace conflicts, msft-smartart steps (carrier render
+ injection) are run as subprocesses, accurately modelling plugin isolation in production.

Run from the repo root:
    python tools/build_plugin_demo_deck.py

Output: output/jack-tar-plugin-demo.pptx
"""
from __future__ import annotations

import json
import shutil
import struct
import subprocess
import sys
import zlib
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve plugin roots.
# Only the deckhand plugin root is added to sys.path (for direct imports).
# msft-smartart is invoked via subprocess to avoid the `src` namespace clash.
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
DECKHAND_ROOT = REPO_ROOT / "plugins" / "jack-tar-deckhand"
MSFT_ROOT = REPO_ROOT / "plugins" / "jack-tar-msft-smartart"

# Add deckhand plugin root to sys.path so `from src.X import Y` resolves there.
_deckhand_str = str(DECKHAND_ROOT)
if _deckhand_str not in sys.path:
    sys.path.insert(0, _deckhand_str)

# Import from the deckhand plugin — validates the plugin's import chain.
from src.conductor import init_pipeline  # noqa: E402
from src.deckcontext import init_deck, write_contract  # noqa: E402

# ---------------------------------------------------------------------------
# Output location
# ---------------------------------------------------------------------------

DEFAULT_OUTPUT = REPO_ROOT / "output" / "jack-tar-plugin-demo.pptx"
DEFAULT_DECK_DIR = REPO_ROOT / "tmp" / "plugin-demo"

# Detect the Python interpreter to use for subprocess calls.
# Prefer the same interpreter that's running this script.
PYTHON_EXE = sys.executable

# ---------------------------------------------------------------------------
# Deck content — "The Jack-Tar Plugin Marketplace"
# ---------------------------------------------------------------------------

TALK_BRIEF = {
    "title": "The Jack-Tar Plugin Marketplace",
    "speaker": "Steve Jones",
    "event": "Jack-Tar Plugin Demo",
    "duration_minutes": 10,
    "audience": "Developers evaluating Claude Code presentation plugins",
    "key_message": "Five focused plugins, one complete pipeline — install only what you need",
}

SLIDES = [
    # 1 — Title
    {
        "slide_number": 1,
        "slide_type": "title",
        "headline": "The Jack-Tar Plugin Marketplace",
        "body_points": [],
        "strategy": "composed",
    },
    # 2 — Why plugins?
    {
        "slide_number": 2,
        "slide_type": "content",
        "headline": "Why a Plugin Architecture?",
        "body_points": [
            "Install only what you need — no heavyweight dependencies",
            "Swap rendering engines without touching the pipeline",
            "Combine local (free) and cloud (production) in one run",
        ],
        "strategy": "composed",
    },
    # 3 — The 5 plugins (process SmartArt)
    {
        "slide_number": 3,
        "slide_type": "content",
        "headline": "Five Plugins, One Pipeline",
        "body_points": [
            "jack-tar-deckhand",
            "jack-tar-ollama",
            "jack-tar-cloud",
            "jack-tar-msft-smartart",
            "jack-tar-custom-smartart",
        ],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "process1",
        "graphic_type": "flowchart",
    },
    # 4 — Ollama capabilities (list SmartArt)
    {
        "slide_number": 4,
        "slide_type": "content",
        "headline": "jack-tar-ollama: Local AI Images",
        "body_points": [
            "Image generation",
            "Icon generation",
            "Pattern generation",
            "Technical diagrams",
            "Quick presentations",
        ],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "list1",
        "graphic_type": "list",
    },
    # 5 — Cloud providers (cycle SmartArt)
    {
        "slide_number": 5,
        "slide_type": "content",
        "headline": "jack-tar-cloud: Provider Cycle",
        "body_points": [
            "OpenAI GPT Image",
            "Google Nanobanana",
            "FAL.ai FLUX",
            "Recraft V4 SVG",
        ],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "cycle2",
        "graphic_type": "cycle",
    },
    # 6 — SmartArt editable vs rasterised (composed comparison slide)
    {
        "slide_number": 6,
        "slide_type": "content",
        "headline": "Editable vs Rasterised SmartArt",
        "body_points": [
            "pptx_native: editable nodes, rename, add/remove, switch layouts",
            "custom-smartart: SVG/Mermaid/Vega — rasterised PNG, AI-quality graphics",
            "Choose by speaker need: editing post-delivery vs visual fidelity",
        ],
        "strategy": "composed",
    },
    # 7 — Deckhand pipeline (process SmartArt, pipeline stages)
    {
        "slide_number": 7,
        "slide_type": "content",
        "headline": "The Deckhand Pipeline",
        "body_points": [
            "Brand",
            "Style",
            "Narrative",
            "Strategy",
            "SmartArt",
            "Images",
            "Assemble",
            "QA",
        ],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "hProcess4",
        "graphic_type": "flowchart",
    },
    # 8 — Getting started (closing)
    {
        "slide_number": 8,
        "slide_type": "closing",
        "headline": "Get Started in 60 Seconds",
        "body_points": [
            "claude plugin install SteveGJones/jack-tar",
            "/jack-tar-deckhand:verify",
            "Ask the conductor to build your deck",
        ],
        "strategy": "composed",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_png(w: int, h: int, r: int, g: int, b: int) -> bytes:
    """Generate a minimal solid-colour PNG without PIL dependency."""
    raw = b""
    for _ in range(h):
        raw += b"\x00" + bytes([r, g, b]) * w
    compressed = zlib.compress(raw)

    def _chunk(ctype: bytes, data: bytes) -> bytes:
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", compressed)
        + _chunk(b"IEND", b"")
    )


def _run_python(script: str, *, cwd: Path, plugin_root: Path,
                timeout: int = 120) -> subprocess.CompletedProcess:
    """Run a Python snippet as a subprocess against a specific plugin root."""
    return subprocess.run(
        [PYTHON_EXE, "-c", script],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(plugin_root),
        env={**__import__("os").environ, "PYTHONPATH": str(plugin_root)},
    )


# ---------------------------------------------------------------------------
# Step 1: Build DeckContext contracts (deckhand plugin — in-process)
# ---------------------------------------------------------------------------


def build_deck_context(deck_dir: Path) -> None:
    """Create all DeckContext contracts in deck_dir."""
    deck_dir.mkdir(parents=True, exist_ok=True)
    (deck_dir / "output").mkdir(exist_ok=True)
    (deck_dir / "images").mkdir(exist_ok=True)
    (deck_dir / "carriers").mkdir(exist_ok=True)

    # talk-brief.json
    (deck_dir / "talk-brief.json").write_text(json.dumps(TALK_BRIEF, indent=2))

    # style-guide.json
    style_guide = {
        "palette": {
            "primary": "1a3a5c",
            "accent": "e8710a",
            "background": "f8f9fa",
            "text_primary": "1a1a1a",
            "chart_series": ["1a3a5c", "e8710a", "2d8a4e", "c0392b", "7b2d8b", "e67e22"],
        },
        "typography": {
            "heading_font": "Calibri",
            "body_font": "Calibri",
            "heading_sizes": {"slide_heading": 28},
        },
        "layout": {
            "slide_width_inches": 13.333,
            "slide_height_inches": 7.5,
            "margin_inches": 0.6,
        },
    }
    (deck_dir / "style-guide.json").write_text(json.dumps(style_guide, indent=2))

    # outline.json
    outline = {
        "narrative_arc": "problem-solution",
        "estimated_duration_minutes": TALK_BRIEF["duration_minutes"],
        "total_slides": len(SLIDES),
        "slides": [],
    }
    for s in SLIDES:
        slide_entry = {
            "slide_number": s["slide_number"],
            "slide_type": s["slide_type"],
            "headline": s["headline"],
            "body_points": s["body_points"],
            "narrative_beat": "content",
            "visual_type": "diagram" if s["strategy"] == "smartart" else "text",
            "layout_template": s["slide_type"],
        }
        outline["slides"].append(slide_entry)
    (deck_dir / "outline.json").write_text(json.dumps(outline, indent=2))

    # strategy-map.json
    strategy_map = {
        "created_at": "2026-04-10T00:00:00Z",
        "approval_mode": "auto",
        "slides": [],
    }
    for s in SLIDES:
        entry = {
            "slide_number": s["slide_number"],
            "strategy": s["strategy"],
            "rationale": s["headline"],
            "render_funnel": ["ollama"],
            "speaker_override": None,
        }
        strategy_map["slides"].append(entry)
    (deck_dir / "strategy-map.json").write_text(json.dumps(strategy_map, indent=2))

    # speaker-notes.json
    notes = {
        "target_pace_wpm": 130,
        "total_estimated_minutes": TALK_BRIEF["duration_minutes"],
        "notes": [],
    }
    for s in SLIDES:
        notes["notes"].append({
            "slide_number": s["slide_number"],
            "text": f"Speaker notes for: {s['headline']}",
            "estimated_seconds": 75,
            "timing_marker": f"~{s['slide_number']}:15",
            "cues": [],
        })
    (deck_dir / "speaker-notes.json").write_text(json.dumps(notes, indent=2))

    # chart-manifest.json (empty — no charts in this demo)
    (deck_dir / "chart-manifest.json").write_text(json.dumps({"charts": []}, indent=2))

    # image-manifest.json (empty — composed slides only, no background images)
    (deck_dir / "image-manifest.json").write_text(
        json.dumps({"generated_at": "2026-04-10T00:00:00Z", "images": []}, indent=2)
    )

    print(f"DeckContext created at {deck_dir}")
    print(f"  slides: {len(SLIDES)}")


# ---------------------------------------------------------------------------
# Step 2: Render SmartArt carriers (msft-smartart plugin — subprocess)
# ---------------------------------------------------------------------------

_CARRIER_SCRIPT = """\
import json
import sys
from pathlib import Path

deck_dir = Path(sys.argv[1])
carriers_dir = deck_dir / "carriers"
carriers_dir.mkdir(exist_ok=True)

from src.engine import render as engine_render
from src.layouts import catalog
catalog.load_catalog.cache_clear()

slides_json = json.loads(sys.argv[2])
smartart_manifest = {"generated_at": "2026-04-10T00:00:00Z", "graphics": []}

for s in slides_json:
    if s["strategy"] != "smartart":
        continue
    layout_id = s["layout_id"]
    graphic_type = s["graphic_type"]
    labels = [bp.strip() for bp in s["body_points"] if bp.strip()]
    spec = {
        "graphic_type": graphic_type,
        "layout_id": layout_id,
        "slide_number": s["slide_number"],
        "data": {"items": labels},
    }
    try:
        result = engine_render(spec, str(carriers_dir))
        status = "rendered"
        file_path = str(result.output_path)
        node_count = result.node_count
        print(f"  Slide {s['slide_number']}: {layout_id} ({node_count} nodes) -> {result.output_path.name}")
    except Exception as exc:
        print(f"  WARN slide {s['slide_number']}: {exc}", file=sys.stderr)
        status = "failed"
        file_path = ""
        node_count = 0

    smartart_manifest["graphics"].append({
        "smartart_id": f"sa-slide-{s['slide_number']}-{graphic_type}",
        "slide_number": s["slide_number"],
        "graphic_type": graphic_type,
        "engine_used": "pptx_native",
        "enrichment_tier": "pure_programmatic",
        "file_path": file_path,
        "svg_source_path": "",
        "status": status,
        "dimensions": {"width": 1920, "height": 1080},
        "node_count": node_count,
        "alt_text": s["headline"],
        "content_hash": f"plugin-demo-{s['slide_number']:02d}",
    })

(deck_dir / "smartart-manifest.json").write_text(json.dumps(smartart_manifest, indent=2))
rendered = sum(1 for g in smartart_manifest["graphics"] if g["status"] == "rendered")
failed = sum(1 for g in smartart_manifest["graphics"] if g["status"] == "failed")
print(f"SmartArt: {rendered} rendered, {failed} failed")
"""

_INJECTION_SCRIPT = """\
import sys
from pathlib import Path

deck_dir = Path(sys.argv[1])
from src.pipeline import run_injection_step
result = run_injection_step(deck_dir)
print(f"Injected: {result.injected_count} pptx_native graphics, {result.skipped_non_pptx_native} non-native skipped")
"""


def render_smartart_carriers(deck_dir: Path) -> bool:
    """Render pptx_native carrier files via msft-smartart plugin (subprocess)."""
    import os
    env = {**os.environ, "PYTHONPATH": str(MSFT_ROOT)}
    result = subprocess.run(
        [PYTHON_EXE, "-c", _CARRIER_SCRIPT, str(deck_dir), json.dumps(SLIDES)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(MSFT_ROOT),
        env=env,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode != 0:
        print(f"Carrier render failed (exit {result.returncode}):", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return False
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    return True


# ---------------------------------------------------------------------------
# Step 3: Assemble the deck (jack-tar-deckhand build_deck.js)
# ---------------------------------------------------------------------------


def run_assembler(deck_dir: Path) -> bool:
    """Run build_deck.js from the deckhand plugin."""
    assembler_js = DECKHAND_ROOT / "src" / "assembler" / "build_deck.js"
    result = subprocess.run(
        ["node", str(assembler_js), "--deck-dir", str(deck_dir)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(DECKHAND_ROOT),
    )
    if result.returncode != 0:
        print(f"Assembler failed (exit {result.returncode}):", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        return False
    if result.stdout:
        print(result.stdout.rstrip())
    pptx = deck_dir / "output" / "presentation.pptx"
    if pptx.exists():
        print(f"Assembled: {pptx.name} ({pptx.stat().st_size:,} bytes)")
    return pptx.exists()


# ---------------------------------------------------------------------------
# Step 4: Inject SmartArt (jack-tar-msft-smartart pipeline — subprocess)
# ---------------------------------------------------------------------------


def run_injection(deck_dir: Path) -> bool:
    """Run pptx_native injection from the msft-smartart plugin (subprocess)."""
    import os
    env = {**os.environ, "PYTHONPATH": str(MSFT_ROOT)}
    result = subprocess.run(
        [PYTHON_EXE, "-c", _INJECTION_SCRIPT, str(deck_dir)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(MSFT_ROOT),
        env=env,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode != 0:
        print(f"Injection failed (exit {result.returncode}):", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return False
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    return True


# ---------------------------------------------------------------------------
# Step 5: Run QA checks (jack-tar-deckhand deck-qa — in-process)
# ---------------------------------------------------------------------------


def run_qa_checks(deck_dir: Path) -> dict:
    """Run QA checks using the deckhand plugin's QA module (in-process)."""
    from src.qa.run_qa import run_qa  # type: ignore[import]

    pptx_path = deck_dir / "output" / "presentation.pptx"
    if not pptx_path.exists():
        print("QA skipped: no presentation.pptx found", file=sys.stderr)
        return {"status": "skipped"}

    try:
        report = run_qa(
            pptx_path=str(pptx_path),
            deck_dir=str(deck_dir),
            duration_minutes=TALK_BRIEF["duration_minutes"],
        )
        summary = report.get("summary", {})
        verdict = report.get("verdict", "unknown")
        errors = summary.get("errors", 0)
        warnings = summary.get("warnings", 0)
        info = summary.get("info", 0)
        print(f"QA verdict: {verdict.upper()} — {errors} errors, {warnings} warnings, {info} info")
        return report
    except Exception as exc:
        print(f"QA failed: {exc}", file=sys.stderr)
        return {"status": "error", "message": str(exc)}


# ---------------------------------------------------------------------------
# Step 6: Copy to final output location
# ---------------------------------------------------------------------------


def copy_to_output(deck_dir: Path, output_path: Path) -> bool:
    """Copy the assembled (and injected) deck to the output destination."""
    src = deck_dir / "output" / "presentation.pptx"
    if not src.exists():
        print(f"Cannot copy — {src} does not exist", file=sys.stderr)
        return False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, output_path)
    print(f"Copied to: {output_path} ({output_path.stat().st_size:,} bytes)")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deck-dir", default=str(DEFAULT_DECK_DIR),
                        help="Working DeckContext directory (default: tmp/plugin-demo)")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT),
                        help="Final .pptx output path (default: output/jack-tar-plugin-demo.pptx)")
    args = parser.parse_args()

    deck_dir = Path(args.deck_dir)
    output_path = Path(args.output)

    print("=" * 60)
    print("Jack-Tar Plugin Marketplace Demo Deck")
    print(f"  deckhand plugin:      {DECKHAND_ROOT}")
    print(f"  msft-smartart plugin: {MSFT_ROOT}")
    print(f"  Python interpreter:   {PYTHON_EXE}")
    print(f"  deck dir:  {deck_dir}")
    print(f"  output:    {output_path}")
    print("=" * 60)
    print()

    # Step 1: Contracts (deckhand — in-process)
    print("Step 1: Building DeckContext contracts (jack-tar-deckhand)...")
    build_deck_context(deck_dir)
    print()

    # Step 2: SmartArt carriers (msft-smartart — subprocess)
    print("Step 2: Rendering SmartArt carriers (jack-tar-msft-smartart)...")
    if not render_smartart_carriers(deck_dir):
        print("FAILED: SmartArt carrier render failed", file=sys.stderr)
        return 1
    print()

    # Step 3: Assemble deck (deckhand build_deck.js)
    print("Step 3: Assembling deck (jack-tar-deckhand build_deck.js)...")
    if not run_assembler(deck_dir):
        print("FAILED: assembler did not produce output", file=sys.stderr)
        return 1
    print()

    # Step 4: Inject SmartArt (msft-smartart — subprocess)
    print("Step 4: Injecting SmartArt (jack-tar-msft-smartart pipeline)...")
    if not run_injection(deck_dir):
        print("FAILED: injection step failed", file=sys.stderr)
        return 1
    print()

    # Step 5: QA (deckhand — in-process)
    print("Step 5: Running QA checks (jack-tar-deckhand deck-qa)...")
    qa_report = run_qa_checks(deck_dir)
    print()

    # Step 6: Copy to output
    print("Step 6: Copying to output...")
    if not copy_to_output(deck_dir, output_path):
        return 1
    print()

    # Summary
    pptx = output_path
    print("=" * 60)
    print("Demo deck complete.")
    print(f"  Output: {pptx}")
    print(f"  Size:   {pptx.stat().st_size:,} bytes ({pptx.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"  Slides: {len(SLIDES)}")
    smartart_count = sum(1 for s in SLIDES if s["strategy"] == "smartart")
    print(f"  SmartArt slides: {smartart_count} (pptx_native, editable)")
    print()

    qa_verdict = qa_report.get("verdict", "unknown")
    qa_summary = qa_report.get("summary", {})
    print(f"QA result: {qa_verdict.upper()}")
    if qa_summary:
        print(f"  Errors: {qa_summary.get('errors', 0)}, "
              f"Warnings: {qa_summary.get('warnings', 0)}, "
              f"Info: {qa_summary.get('info', 0)}")
    qa_errors = [f for f in qa_report.get("findings", []) if f.get("severity") == "error"]
    if qa_errors:
        print(f"  Error details (first 5):")
        for e in qa_errors[:5]:
            print(f"    [{e.get('check_id', '?')}] {e.get('message', '')}")
    print()
    print("To open in PowerPoint:")
    print(f"  open {pptx}")
    print()
    print("Note: pptx_native SmartArt slides render in PowerPoint — open the")
    print("file to verify visual quality before presenting.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
