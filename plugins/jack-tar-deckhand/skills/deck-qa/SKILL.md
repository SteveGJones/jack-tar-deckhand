---
name: deck-qa
description: Run 30 automated anti-pattern checks on an assembled .pptx and produce a QAReport with verdict and per-slide findings.
argument-hint: [--pptx-path PATH] [--deck-dir PATH] [--duration MINUTES]
allowed-tools: Bash(python *), Read, Glob
---

# /deck-qa

Run 25 automated quality assurance checks against an assembled .pptx file. Produces a QAReport JSON at `./tmp/deck/qa-report.json`.

## Plugin Setup

```bash
PLUGIN_ROOT=$(python3 -c "
from pathlib import Path
import sys, os
if os.environ.get('JACK_TAR_DECKHAND_ROOT'):
    print(os.environ['JACK_TAR_DECKHAND_ROOT']); sys.exit()
home = Path.home()
for base in [home / '.claude' / 'plugins' / 'cache']:
    for p in base.rglob('jack-tar-deckhand/.claude-plugin/plugin.json'):
        print(str(p.parent.parent)); sys.exit()
dev = Path.cwd() / 'plugins' / 'jack-tar-deckhand'
if dev.exists():
    print(str(dev)); sys.exit()
print('NOT_FOUND')
" 2>/dev/null)
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then echo "ERROR: jack-tar-deckhand not found" && exit 1; fi
```

## Usage

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -m src.qa.run_qa --pptx-path ./tmp/deck/output/presentation.pptx --deck-dir ./tmp/deck --duration 30
```

## What It Checks

**Structural (fast, no rendering):**
- AP-01: Wall of Text (>40 words/textbox, >75 words/slide)
- AP-02: Font Size Below Projection Minimum (<18pt body, <24pt title)
- AP-05: Orphan/Widow Lines
- AP-06: Elements Outside 5% Safe Margins
- AP-09: Missing Speaker Notes (<50% of content slides)
- AP-10: Slide Count vs Talk Duration Mismatch
- AP-11: Placeholder Residue (TODO, Lorem ipsum, Click to add)
- AP-14: Too Many Bullet Points (>6 per slide)
- AP-16: Missing Title Slide
- AP-17: Missing Closing/CTA Slide
- AP-19: Text Overflow/Clipping (auto-shrunk below 90%)
- AP-20: Element Overlap (>25%)
- AP-24: Dead/Empty Slides

**Contrast & Colour:**
- AP-07: Low Contrast Text-on-Background (<7:1 for projection)
- AP-08: Clashing Colours (complementary at high saturation, red-green)
- AP-25: Colourblind Safety (deuteranopia simulation)

**Cross-Slide Consistency:**
- AP-03: Too Many Font Families (>2)
- AP-04: Inconsistent Bullet Styles
- AP-15: Consecutive Bullet-Heavy Slides (>3 in a row)
- AP-18: Inconsistent Heading Sizes
- AP-23: Branding/Logo Inconsistency

**Image Quality:**
- AP-12: Image Resolution Too Low for Placement Size
- AP-13: Image Aspect Ratio Distortion (>5%)

**Keynote Slide Checks (strategy-aware):**
- AP-26: Palette Drift — dominant colours in full_render/backdrop_render images compared against brand palette (RGB distance threshold)

When `strategy-map.json` exists in the deck directory, QA routes checks per slide:
- **full_render** slides: skip text checks (AP-01, AP-02, etc.), run image quality + palette drift
- **backdrop_render** slides: run all standard checks + palette drift
- **composed** slides: standard 25 checks (unchanged)

**Animations & Charts:**
- AP-21: Excessive Animation/Transition Types (>2)
- AP-22: Poor Data-Ink Ratio (3D charts, minor gridlines)

## Output

QAReport JSON with:
- `verdict`: pass | pass_with_warnings | fail
- `summary`: counts of errors, warnings, info
- `findings`: per-finding entries with slide_number, severity, category, description, suggested_fix, auto_fixable

## Verdict Rules

- **fail**: any finding with severity 'error'
- **pass_with_warnings**: no errors, but warnings exist
- **pass**: no errors, no warnings
