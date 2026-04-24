"""Analyser orchestrator — HYBRID OOXML + JS fallback + overlap verifier.

Orchestration order:
  1. preflight_pptx() — refuse oversized / suspicious files.
  2. parse_pptx() — OOXML primary path.
  3. If 0 markers AND build.js exists alongside, parse_js() to recover markers.
  4. find_overlaps() — SMARTART marker-adjacent text check.
  5. find_duplicate_marker_ids() — flag deck-wide identifier dupes.

Returns an AnalyserResult; raises PptxPreflightError on preflight failure
(propagated, not swallowed).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.analyser.js_parser import JsParseError, parse_js
from src.analyser.overlap_verifier import find_overlaps
from src.analyser.pptx_parser import parse_pptx
from src.placeholder import find_duplicate_marker_ids
from src.security import preflight_pptx
from src.slide_facts import AnalyserResult


@dataclass
class AnalyserOptions:
    enable_js_fallback: bool = True


def analyse_pptx(
    pptx_path: Path | str,
    *,
    options: AnalyserOptions | None = None,
) -> AnalyserResult:
    """Run the full HYBRID analyser pipeline against a .pptx.

    Raises PptxPreflightError if the file fails security pre-flight.
    """
    opts = options or AnalyserOptions()
    p = Path(pptx_path)

    # Step 1 — security pre-flight (propagates PptxPreflightError)
    preflight_pptx(p)

    # Step 2 — OOXML primary
    slides = parse_pptx(p)
    notes: list[str] = []
    js_fallback_used = False

    # Step 3 — JS fallback when OOXML found zero markers AND build.js exists
    total_markers = sum(len(s.markers) for s in slides)
    build_js = p.with_name("build.js")
    if (
        opts.enable_js_fallback
        and total_markers == 0
        and build_js.exists()
    ):
        try:
            js_facts = parse_js(build_js)
        except JsParseError as exc:
            notes.append(f"JS fallback failed; reporting no markers ({exc})")
        else:
            js_fallback_used = True
            # Merge JS-recovered markers onto matching slide indices.
            # If JS produces more or fewer slides than OOXML, align by index.
            for js_slide in js_facts:
                idx = js_slide.slide_index
                if 1 <= idx <= len(slides):
                    slides[idx - 1].markers = js_slide.markers
            notes.append(f"JS fallback recovered {sum(len(s.markers) for s in slides)} markers")

    # Step 4 — overlap verifier (only meaningful for slides with SMARTART markers)
    overlap_warnings = find_overlaps(p)

    # Step 5 — duplicate marker id detection
    duplicates = find_duplicate_marker_ids(slides)

    return AnalyserResult(
        slides=slides,
        duplicate_marker_ids=duplicates,
        overlap_warnings=overlap_warnings,
        js_fallback_used=js_fallback_used,
        notes=notes,
    )
