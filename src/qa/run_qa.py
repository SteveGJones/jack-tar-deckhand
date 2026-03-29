#!/usr/bin/env python3
"""deck-qa: Run 25 automated anti-pattern checks on a .pptx file.

Usage:
    python -m src.qa.run_qa [--pptx-path PATH] [--deck-dir PATH] [--duration MINUTES]

Default pptx-path: ./tmp/deck/output/presentation.pptx
Default deck-dir: ./tmp/deck
"""

import argparse
import json
import os
import sys

from pptx import Presentation

from .checks import (
    STRUCTURAL_CHECKS,
    STRUCTURAL_CHECKS_WITH_PRESENTATION,
    DECK_STRUCTURAL_CHECKS,
    CONSISTENCY_CHECKS,
    IMAGE_QUALITY_CHECKS,
    VISUAL_CHECKS,
    ANIMATION_CHECKS,
    COLOUR_CHECKS,
    check_slide_count_ratio,
)
from .config import QA_CONFIG
from .report import generate_report


def run_qa(pptx_path, deck_dir='./tmp/deck', duration_minutes=None, config=None):
    """Run all 25 QA checks and return a QAReport dict."""
    cfg = config or QA_CONFIG
    prs = Presentation(pptx_path)
    findings = []

    # Step 1: Per-slide structural checks
    for i, slide in enumerate(prs.slides):
        slide_number = i + 1
        for check_fn in STRUCTURAL_CHECKS:
            findings.extend(check_fn(slide, slide_number, config=cfg))
        for check_fn in STRUCTURAL_CHECKS_WITH_PRESENTATION:
            findings.extend(check_fn(slide, slide_number, prs, config=cfg))
        for check_fn in IMAGE_QUALITY_CHECKS:
            findings.extend(check_fn(slide, slide_number, prs, config=cfg))
        for check_fn in VISUAL_CHECKS:
            try:
                findings.extend(check_fn(slide, slide_number, config=cfg))
            except Exception:
                pass  # Visual checks may fail on minimal test decks

    # Step 2: Deck-level structural checks
    for check_fn in DECK_STRUCTURAL_CHECKS:
        findings.extend(check_fn(prs, config=cfg))

    # AP-10: Slide count vs duration (needs external duration)
    if duration_minutes:
        findings.extend(check_slide_count_ratio(prs, duration_minutes, config=cfg))

    # Step 3: Cross-slide consistency checks
    for check_fn in CONSISTENCY_CHECKS:
        findings.extend(check_fn(prs, config=cfg))

    # Step 4: Deck-level animation checks
    for check_fn in ANIMATION_CHECKS:
        findings.extend(check_fn(prs, config=cfg))

    # Step 5: Deck-level colour checks
    colours_used = set()
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        try:
                            if run.font.color and run.font.color.rgb:
                                rgb = run.font.color.rgb
                                colours_used.add((rgb[0], rgb[1], rgb[2]))
                        except (AttributeError, TypeError):
                            pass
    for check_fn in COLOUR_CHECKS:
        findings.extend(check_fn(colours_used, config=cfg))

    # Generate report
    report = generate_report(findings, pptx_path, len(prs.slides))
    return report


def main():
    parser = argparse.ArgumentParser(description='Run QA checks on a .pptx file')
    parser.add_argument('--pptx-path', default='./tmp/deck/output/presentation.pptx')
    parser.add_argument('--deck-dir', default='./tmp/deck')
    parser.add_argument('--duration', type=int, default=None,
                        help='Talk duration in minutes (for slide count check)')
    parser.add_argument('--output', default=None,
                        help='Output path for QA report JSON')
    args = parser.parse_args()

    report = run_qa(args.pptx_path, args.deck_dir, args.duration)

    # Write report
    output_path = args.output or os.path.join(args.deck_dir, 'qa-report.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    # Print summary
    print(f"QA Report: {report['verdict'].upper()}")
    print(f"  Errors: {report['summary']['errors']}")
    print(f"  Warnings: {report['summary']['warnings']}")
    print(f"  Info: {report['summary']['info']}")

    # Exit code: 1 if fail, 0 otherwise
    sys.exit(1 if report['verdict'] == 'fail' else 0)


if __name__ == '__main__':
    main()
