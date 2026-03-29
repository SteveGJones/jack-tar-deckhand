---
name: deck-assembler
description: Assemble a .pptx presentation from all DeckContext contracts (SlideOutline, StyleGuide, ImageManifest, ChartManifest, SpeakerNotes) via PptxGenJS.
argument-hint: [--deck-dir PATH]
allowed-tools: Bash(node *), Bash(npm *), Read, Glob
---

# /deck-assembler

Assemble a complete PowerPoint presentation from the DeckContext contracts in `./tmp/deck/`.

## Prerequisites

All of these DeckContext files must exist before running:
- `./tmp/deck/outline.json` (SlideOutline)
- `./tmp/deck/style-guide.json` (StyleGuide)
- `./tmp/deck/image-manifest.json` (ImageManifest)
- `./tmp/deck/chart-manifest.json` (ChartManifest)
- `./tmp/deck/speaker-notes.json` (SpeakerNotes)
- `./tmp/deck/images/` directory with referenced image files

## Usage

```bash
node src/assembler/build_deck.js --deck-dir ./tmp/deck
```

Default deck-dir is `./tmp/deck` if not specified.

## Output

`./tmp/deck/output/presentation.pptx`

## What It Does

1. Reads all DeckContext JSON contracts
2. Validates that referenced image assets exist
3. Creates PptxGenJS slide masters for all 12 slide types based on StyleGuide
4. Iterates through SlideOutline, building each slide with:
   - Correct master/layout per slide_type
   - Headline and body points with StyleGuide typography
   - Images from ImageManifest placed in correct zones
   - Chart images from ChartManifest for data_chart slides
   - Speaker notes from SpeakerNotes contract
5. Generates progressive build slides for bullets with build_animation cues
6. Writes the assembled .pptx to the output directory
7. Reports file size and any asset warnings

## Design Rules (from existing pptx skill)

- 0.5" minimum margins on all sides
- Never use `#` prefix on hex colours (PptxGenJS convention)
- Do not reuse option objects (PptxGenJS mutates them)
- Left-align body text, centre only titles
- Do not place accent lines under titles

## Limitations

- No native animations (PptxGenJS v4.0.1 limitation) -- uses progressive builds for ~80% coverage
- No gradient fills on shapes -- use pre-rendered gradient images as backgrounds
- Cannot import existing .pptx templates -- defines masters programmatically
