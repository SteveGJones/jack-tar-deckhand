---
name: strategy-map
description: Classify each slide's rendering strategy (full_render, backdrop_render, composed) and generate image prompts via the prompt-engineer agent.
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
   - **backdrop_render** — AI background with programmatic text overlay (dense content slides)
   - **composed** — standard PptxGenJS assembly (data charts, diagrams, code)

2. Presents the strategy map to the Speaker with rationale per slide
3. Accepts Speaker overrides for individual slides
4. Saves the approved strategy map to `./tmp/deck/strategy-map.json`

## Usage

```bash
source .venv/bin/activate && python3 -c "
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
| 2 | content | backdrop_render | 4 bullets — AI background + text overlay |
| 4 | diagram | composed | Precise labels require programmatic rendering |

Ask: "Would you like to override any slide strategies?"

If overrides are provided, rebuild with the overrides dict and save again.

## Output

`./tmp/deck/strategy-map.json` conforming to the StrategyMap schema.
