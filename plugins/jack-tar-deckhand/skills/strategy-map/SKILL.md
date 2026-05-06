---
name: strategy-map
description: Classify each slide's rendering strategy (full_render, background, backdrop, pragmatic_composition, composed) and generate image prompts via the prompt-engineer agent.
argument-hint: [--deck-dir PATH] [--approval-mode review|one_shot]
allowed-tools: Bash(python *), Read, Glob, Agent(prompt-engineer)
---

# /strategy-map

Classify rendering strategies for each slide and produce the StrategyMap contract. This is Step 3.5 in the pipeline — invoked after the SlideOutline is finalised and before image generation.

## Prerequisites

- `./tmp/deck/outline.json` (SlideOutline)
- `./tmp/deck/style-guide.json` (StyleGuide)
- `./tmp/deck/brand-profile.json` (BrandProfile) — optional

## What It Does

1. Reads the SlideOutline and classifies each slide into a rendering strategy:
   - **full_render** — entire slide generated as one AI image (title, section divider, closing, sparse content)
   - **background** — atmospheric AI background + text in template zones (5 variants: left_panel, right_panel, bottom_bar, top_band, center_float)
   - **backdrop** — structured AI scene + vision post-analysis for text positioning (Claude Code vision-analyst agent)
   - **pragmatic_composition** — individual AI-generated elements assembled at exact positions with text labels
   - **composed** — standard PptxGenJS assembly (diagrams, charts, code)
   - _`backdrop_render` retained for backward compatibility (maps to `background` with `left_panel`)_

2. Presents the strategy map to the Speaker with rationale per slide
3. Accepts Speaker overrides for individual slides
4. Saves the approved strategy map to `./tmp/deck/strategy-map.json`

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
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
from src.slide_prompt_composer import build_strategy_map, save_strategy_map
import json
with open('./tmp/deck/outline.json') as f:
    outline = json.load(f)
strategy_map = build_strategy_map(outline)
save_strategy_map('./tmp/deck', strategy_map)
print(json.dumps(strategy_map, indent=2))
"
```

## Speaker Interaction

Present the strategy map as a table:

| Slide | Type | Strategy | Rationale |
|-------|------|----------|-----------|
| 1 | title | full_render | Short text, dramatic visual |
| 2 | content | background | 4 bullets — AI background + text overlay in bottom_bar zone |
| 3 | content | pragmatic_composition | 4 labeled elements in grid — independent images + precise positioning |
| 4 | diagram | composed | Precise labels require programmatic rendering |
| 5 | content | backdrop | Rich scene with vision-detected text placement |

Ask: "Would you like to override any slide strategies?"

If overrides are provided, rebuild with the overrides dict and save again.

## Strategy Selection Guidance

### Pragmatic composition for grid content

When a slide has 4+ labeled elements in a grid layout, recommend `pragmatic_composition` over `backdrop`. Pragmatic composition gives precise control over element sizing and alignment since each image is independently generated and placed at exact coordinates. Backdrop relies on vision-detected positions from a single scene image, which produces inconsistent element sizes and misaligned text labels.

### body_layout option for background slides

Background strategy slides support `body_layout: "grid_2x2"` in the strategy map entry. This renders body points in a 2-column, 2-row grid using column-first reading order instead of a single bullet list. Use this when a background slide has 4 bullet points that would overflow the standard bottom_bar or panel zone.

### Column-first reading order

All `grid_2x2` element layouts MUST use column-first (N-pattern) reading order: TL=body_points[0], BL=body_points[1], TR=body_points[2], BR=body_points[3]. This matches natural presentation reading: audiences read down the left column before moving right. AP-30 QA check enforces this.

### Element image aspect ratios

When specifying element_layout dimensions, calculate the target aspect ratio (w/h) and include it in the strategy map entry so the imagegen-bridge generates images at the correct dimensions. Don't assume square — element images should match their target placement box exactly to avoid letterboxing or cropping artefacts.

### Diagram layout guidance

When classifying diagram slides, consider the slide's 16:9 aspect ratio when recommending layout in the visual_direction:

| Element count | Recommended layout | Rationale |
|---|---|---|
| 2-4 nodes | Single horizontal row | Fits comfortably in 16:9 |
| 5-8 nodes | Snake pattern (2-3 rows) | Fills the vertical space instead of a tiny horizontal line |
| 9+ nodes | Grid (3x3 or similar) | Maximises use of slide area |
| Hierarchy (1 + N) | Wide bar at top, row below | Shows orchestration clearly |

Include layout direction in the visual_direction prompt. For example: "Snake pattern: Row 1 left-to-right (Brief → Brand → Style → Narrative), curve down, Row 2 right-to-left (Images → Assembly), curve down, Row 3 left-to-right (QA → Deck)."

## Resolution selection

By default every slide renders at `1K` — economical, sufficient for most slides on a projector. The speaker may opt specific slides into `2K` or `4K` via the `resolution` field in the StrategyMap entry.

**When to choose 4K:**
- Hero opener with detailed photographic imagery
- Closing slide that will be photographed by attendees and shared on social
- Slides where text rendering at small body sizes is critical (Nano Banana Pro 4K renders text noticeably better than Flash 1K)

**When to choose 2K:**
- Section dividers with mid-detail imagery
- Diagrams that may be projected on very large screens (>120")

**Cost implications (per slide, single Pro escalation):**
- `1K` (default): ~$0.13 (Nano Banana Pro)
- `2K`: ~$0.13 (Nano Banana Pro — same flat rate within tier)
- `4K`: ~$0.24 (Nano Banana Pro). Plus an optional Flash 4K pre-test at $0.151.

Mark a slide for 2K/4K by including `"resolution": "4K"` in its StrategyMap entry. Confirm the cost with the speaker before proceeding — a deck with three 4K hero slides is ~$2 of generation spend.

## Output

`./tmp/deck/strategy-map.json` conforming to the StrategyMap schema.
