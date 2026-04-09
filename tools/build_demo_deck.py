"""Build the pptx_native demo deck: "Building AI Agents That Actually Work"

A 15-slide conference talk that showcases pptx_native SmartArt across
8 categories, mixed with full_render, composed, and background
strategies. The SmartArt serves the narrative — each layout is chosen
because it reinforces the shape of the idea, not because we want to
demo a layout.

Usage:
    python tools/build_demo_deck.py [--deck-dir PATH]

Produces a DeckContext at the specified directory (default:
tmp/demo_deck/) with all contracts, runs the Node assembler,
runs pptx_native injection, and reports the output path.

For background slides, uses placeholder PNGs (solid colour rectangles)
unless real Ollama-generated images are available. The backgrounds
can be upgraded to production quality later via the image pipeline.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DECK_DIR = REPO_ROOT / "tmp" / "demo_deck"


# ---------------------------------------------------------------------------
# Slide content
# ---------------------------------------------------------------------------

TALK_BRIEF = {
    "title": "Building AI Agents That Actually Work",
    "speaker": "Steve Jones",
    "event": "Jack-Tar Deckhand SmartArt Demo",
    "duration_minutes": 15,
    "audience": "Engineering leaders considering agent-based architecture",
    "key_message": "Agents are loops not pipelines — start simple, iterate fast, let speakers edit the result",
}

SLIDES = [
    {
        "slide_number": 1,
        "slide_type": "title",
        "headline": "Building AI Agents That Actually Work",
        "body_points": [],
        "strategy": "full_render",
        "visual_direction": "Dark stage with a single spotlight on a futuristic robot assistant",
    },
    {
        "slide_number": 2,
        "slide_type": "content",
        "headline": "Editable SmartArt — Your Deck, Your Way",
        "body_points": [
            "Add and rename nodes",
            "28 built-in layouts",
            "Mac, Windows, and Web",
            "Speaker-controlled design",
        ],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "list1",
        "graphic_type": "list",
    },
    {
        "slide_number": 3,
        "slide_type": "content",
        "headline": "Agents Are Loops, Not Pipelines",
        "body_points": ["Plan", "Act", "Observe", "Reflect"],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "cycle2",
        "graphic_type": "cycle",
    },
    {
        "slide_number": 4,
        "slide_type": "content",
        "headline": "When to Build an Agent vs a Pipeline",
        "body_points": ["Deterministic + Single", "Deterministic + Multi", "Non-deterministic + Single", "Non-deterministic + Multi"],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "matrix2",
        "graphic_type": "matrix",
    },
    {
        "slide_number": 5,
        "slide_type": "content",
        "headline": "Our Five-Stage Development Process",
        "body_points": ["Research", "Prototype", "Validate", "Harden", "Ship"],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "chevron1",
        "graphic_type": "chevron_list",
    },
    {
        "slide_number": 6,
        "slide_type": "content",
        "headline": "System Architecture",
        "body_points": [
            "Platform",
            "  Agent Framework",
            "    Domain Agents",
            "      Skills & Tools",
        ],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "hierarchy5",
        "graphic_type": "hierarchy",
    },
    {
        "slide_number": 7,
        "slide_type": "content",
        "headline": "Six Specialists, One Conductor",
        "body_points": [
            "Deck Conductor",
            "  Executive Assistant (asst)",
            "  Narrative Architect",
            "  SmartArt Selector",
            "  Image Generator",
            "  Quality Reviewer",
            "  Prompt Engineer",
        ],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "orgChart1",
        "graphic_type": "org_chart",
    },
    {
        "slide_number": 8,
        "slide_type": "content",
        "headline": "Three Lines of Defence",
        "body_points": ["Automated Checks", "Agent Review", "Human Gate"],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "pyramid2",
        "graphic_type": "pyramid",
        "enrichment_tier": "ai_background",
        "bg_prompt": "Medieval castle with three concentric defensive walls, dramatic lighting, aerial view, painterly style",
    },
    {
        "slide_number": 9,
        "slide_type": "content",
        "headline": "What We Learned the Hard Way",
        "body_points": ["Ship small, iterate fast", "Fail forward, not backward", "Test everything automatically", "Trust the speaker"],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "vList4",
        "graphic_type": "list",
    },
    {
        "slide_number": 10,
        "slide_type": "content",
        "headline": "Where AI Meets Human Judgement",
        "body_points": ["AI Capability", "Human Expertise"],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "venn1",
        "graphic_type": "venn",
        "enrichment_tier": "ai_background",
        "bg_prompt": "Two hands reaching toward each other, Michelangelo Creation of Adam style, digital art, warm golden lighting",
    },
    {
        "slide_number": 11,
        "slide_type": "content",
        "headline": "From Brief to Deck in 90 Minutes",
        "body_points": ["Brief", "Draft", "Review", "Refine", "Deliver"],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "process1",
        "graphic_type": "flowchart",
    },
    {
        "slide_number": 12,
        "slide_type": "content",
        "headline": "Adoption Across the Organisation",
        "body_points": ["Awareness", "Interest", "Pilot", "Adoption", "Advocacy"],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "funnel1",
        "graphic_type": "pipeline_funnel",
    },
    {
        "slide_number": 13,
        "slide_type": "content",
        "headline": "The People Behind the Agents",
        "body_points": ["Platform Lead", "AI Architect", "UX Designer", "QA Engineer"],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "pList1",
        "graphic_type": "picture_list",
    },
    {
        "slide_number": 14,
        "slide_type": "content",
        "headline": "Three Approaches Compared",
        "body_points": ["Build from Scratch", "Use a Framework", "Use Jack-Tar"],
        "strategy": "smartart",
        "engine": "pptx_native",
        "layout_id": "hList6",
        "graphic_type": "list",
    },
    {
        "slide_number": 15,
        "slide_type": "closing",
        "headline": "Start With the Simplest Agent That Could Work",
        "body_points": [],
        "strategy": "background",
        "visual_direction": "Rocket launch at dawn over the ocean, cinematic wide shot, inspirational",
    },
]


def _create_placeholder_image(path: Path, color: tuple = (50, 50, 80)):
    """Create a simple placeholder PNG for background slides."""
    try:
        from PIL import Image
        img = Image.new("RGB", (1920, 1080), color=color)
        img.save(path)
    except ImportError:
        # If PIL not available, create a minimal 1x1 PNG
        import struct
        import zlib

        def _minimal_png(w, h, r, g, b):
            raw = b""
            for _ in range(h):
                raw += b"\x00" + bytes([r, g, b]) * w
            compressed = zlib.compress(raw)

            def _chunk(ctype, data):
                c = ctype + data
                return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

            return (
                b"\x89PNG\r\n\x1a\n"
                + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + _chunk(b"IDAT", compressed)
                + _chunk(b"IEND", b"")
            )

        path.write_bytes(_minimal_png(100, 56, *color))


def build_deck_context(deck_dir: Path) -> Path:
    """Create the full DeckContext directory with all contracts."""
    deck_dir.mkdir(parents=True, exist_ok=True)
    (deck_dir / "output").mkdir(exist_ok=True)
    (deck_dir / "images").mkdir(exist_ok=True)

    # --- talk-brief.json ---
    (deck_dir / "talk-brief.json").write_text(json.dumps(TALK_BRIEF, indent=2))

    # --- style-guide.json ---
    style_guide = {
        "palette": {
            "primary": "1a73e8",
            "accent": "e8710a",
            "background": "ffffff",
            "text_primary": "1a1a1a",
            "chart_series": ["2B6CB0", "ED8936", "38A169", "E53E3E", "805AD5", "DD6B20"],
        },
        "typography": {
            "heading_font": "Calibri",
            "body_font": "Calibri",
            "heading_sizes": {"slide_heading": 28},
        },
        "layout": {
            "slide_width_inches": 13.333,
            "slide_height_inches": 7.5,
            "margin_inches": 0.5,
        },
    }
    (deck_dir / "style-guide.json").write_text(json.dumps(style_guide, indent=2))

    # --- outline.json ---
    outline = {
        "narrative_arc": "problem-solution",
        "estimated_duration_minutes": 15,
        "total_slides": len(SLIDES),
        "slides": [],
    }
    for s in SLIDES:
        outline_slide = {
            "slide_number": s["slide_number"],
            "slide_type": s["slide_type"],
            "headline": s["headline"],
            "body_points": s["body_points"],
            "narrative_beat": "content",
            "visual_type": "diagram" if s["strategy"] == "smartart" else "hero_image",
            "layout_template": s["slide_type"],
        }
        if "visual_direction" in s:
            outline_slide["visual_direction"] = s["visual_direction"]
        outline["slides"].append(outline_slide)
    (deck_dir / "outline.json").write_text(json.dumps(outline, indent=2))

    # --- strategy-map.json ---
    strategy_map = {"created_at": "2026-04-09T00:00:00Z", "approval_mode": "auto", "slides": []}
    for s in SLIDES:
        entry = {
            "slide_number": s["slide_number"],
            "strategy": s["strategy"],
            "rationale": s["headline"],
            "render_funnel": ["ollama"],
            "speaker_override": None,
        }
        if s["strategy"] == "background":
            entry["backdrop_variant"] = "center_float"
        strategy_map["slides"].append(entry)
    (deck_dir / "strategy-map.json").write_text(json.dumps(strategy_map, indent=2))

    # --- speaker-notes.json ---
    notes = {"target_pace_wpm": 130, "total_estimated_minutes": 15, "notes": []}
    for s in SLIDES:
        notes["notes"].append({
            "slide_number": s["slide_number"],
            "text": f"[Speaker notes for: {s['headline']}]",
            "estimated_seconds": 60,
            "timing_marker": f"~{s['slide_number']}:00",
            "cues": [],
        })
    (deck_dir / "speaker-notes.json").write_text(json.dumps(notes, indent=2))

    # --- chart-manifest.json (empty) ---
    (deck_dir / "chart-manifest.json").write_text(json.dumps({"charts": []}, indent=2))

    # --- image-manifest.json ---
    # Background slides need image entries; SmartArt slides don't
    image_manifest = {"generated_at": "2026-04-09T00:00:00Z", "images": []}
    for s in SLIDES:
        if s["strategy"] == "full_render":
            img_path = deck_dir / "images" / f"slide{s['slide_number']}-hero.png"
            _create_placeholder_image(img_path, color=(30, 30, 60))
            image_manifest["images"].append({
                "image_id": f"img-slide-{s['slide_number']}",
                "slide_number": s["slide_number"],
                "file_path": str(img_path),
                "strategy": "full_render",
                "dimensions": {"width": 1920, "height": 1080},
                "alt_text": s.get("visual_direction", s["headline"]),
            })
        elif s["strategy"] == "background":
            img_path = deck_dir / "images" / f"slide{s['slide_number']}-bg.png"
            _create_placeholder_image(img_path, color=(40, 50, 70))
            image_manifest["images"].append({
                "image_id": f"img-slide-{s['slide_number']}",
                "slide_number": s["slide_number"],
                "file_path": str(img_path),
                "strategy": "background",
                "dimensions": {"width": 1920, "height": 1080},
                "alt_text": s.get("visual_direction", s["headline"]),
            })
        elif s.get("enrichment_tier") == "ai_background":
            # SmartArt slide with background enrichment
            img_path = deck_dir / "images" / f"slide{s['slide_number']}-bg.png"
            _create_placeholder_image(img_path, color=(60, 40, 30))
            image_manifest["images"].append({
                "image_id": f"img-slide-{s['slide_number']}",
                "slide_number": s["slide_number"],
                "file_path": str(img_path),
                "strategy": "background",
                "smartart_ref": f"sa-slide-{s['slide_number']}-{s['graphic_type']}",
                "dimensions": {"width": 1920, "height": 1080},
                "alt_text": s.get("bg_prompt", s["headline"]),
            })
    (deck_dir / "image-manifest.json").write_text(json.dumps(image_manifest, indent=2))

    # --- Generate pptx_native carriers ---
    sys.path.insert(0, str(REPO_ROOT))
    from src.smartart_pptx_native import engine
    from src.smartart_pptx_native.layouts import catalog

    catalog.load_catalog.cache_clear()

    smartart_manifest = {"generated_at": "2026-04-09T00:00:00Z", "graphics": []}
    carriers_dir = deck_dir / "carriers"
    carriers_dir.mkdir(exist_ok=True)

    for s in SLIDES:
        if s["strategy"] != "smartart":
            continue

        layout_id = s.get("layout_id")
        graphic_type = s.get("graphic_type", "list")
        enrichment_tier = s.get("enrichment_tier", "pure_programmatic")

        # Build the data for this slide
        entry = catalog.get_entry(layout_id)
        data_shape = entry["data_shape"]

        if data_shape == "hierarchical":
            # Parse indented body_points into tree
            from src.smartart_extractor import _body_points_to_tree
            tree = _body_points_to_tree(s["body_points"])
            if tree is None:
                labels = [bp.strip() for bp in s["body_points"] if bp.strip()]
                tree = {"title": labels[0], "children": [{"title": l} for l in labels[1:]]}
            spec_data = {"tree": tree}
        else:
            # Flat list
            labels = [bp.strip() for bp in s["body_points"] if bp.strip()]
            spec_data = {"items": labels}

        spec = {
            "graphic_type": graphic_type,
            "layout_id": layout_id,
            "slide_number": s["slide_number"],
            "data": spec_data,
        }

        try:
            result = engine.render(spec, str(carriers_dir))
            status = "rendered"
            file_path = str(result.output_path)
            node_count = result.node_count
        except Exception as exc:
            print(f"  WARN: slide {s['slide_number']} render failed: {exc}", file=sys.stderr)
            status = "failed"
            file_path = ""
            node_count = 0

        smartart_manifest["graphics"].append({
            "smartart_id": f"sa-slide-{s['slide_number']}-{graphic_type}",
            "slide_number": s["slide_number"],
            "graphic_type": graphic_type,
            "engine_used": "pptx_native",
            "enrichment_tier": enrichment_tier,
            "file_path": file_path,
            "svg_source_path": "",
            "status": status,
            "dimensions": {"width": 1920, "height": 1080},
            "node_count": node_count,
            "alt_text": s["headline"],
            "content_hash": f"demo{s['slide_number']:02d}",
        })

    (deck_dir / "smartart-manifest.json").write_text(
        json.dumps(smartart_manifest, indent=2)
    )

    print(f"DeckContext created at {deck_dir}")
    print(f"  slides: {len(SLIDES)}")
    print(f"  smartart carriers: {len(smartart_manifest['graphics'])}")
    print(f"  background images: {len(image_manifest['images'])}")

    return deck_dir


def run_assembler(deck_dir: Path) -> bool:
    """Run build_deck.js to assemble the deck."""
    result = subprocess.run(
        ["node", "src/assembler/build_deck.js", "--deck-dir", str(deck_dir)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        print(f"Assembler failed:\n{result.stderr}", file=sys.stderr)
        return False
    pptx = deck_dir / "output" / "presentation.pptx"
    if pptx.exists():
        print(f"Assembled: {pptx} ({pptx.stat().st_size} bytes)")
    return pptx.exists()


def run_injection(deck_dir: Path) -> bool:
    """Run pptx_native injection post-process."""
    sys.path.insert(0, str(REPO_ROOT))
    from src.smartart_pptx_native.pipeline import run_injection_step

    try:
        result = run_injection_step(deck_dir)
        print(f"Injected: {result.injected_count} pptx_native graphics")
        return True
    except Exception as exc:
        print(f"Injection failed: {exc}", file=sys.stderr)
        return False


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deck-dir", default=str(DEFAULT_DECK_DIR))
    args = parser.parse_args()

    deck_dir = Path(args.deck_dir)

    print("=== Building Demo Deck: Building AI Agents That Actually Work ===")
    print()

    # Step 1: Create DeckContext
    build_deck_context(deck_dir)

    # Step 2: Run assembler
    print()
    if not run_assembler(deck_dir):
        print("FAILED: assembler did not produce output", file=sys.stderr)
        return 1

    # Step 3: Run injection
    if not run_injection(deck_dir):
        print("FAILED: injection step failed", file=sys.stderr)
        return 1

    pptx = deck_dir / "output" / "presentation.pptx"
    print()
    print(f"=== Demo deck ready ===")
    print(f"  {pptx}")
    print(f"  {pptx.stat().st_size} bytes")
    print()
    print("To export as PDF (requires PowerPoint Mac):")
    print(f"  tools/pptx_to_pdf.sh {pptx}")
    print()
    print("To open directly in PowerPoint:")
    print(f"  open {pptx}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
