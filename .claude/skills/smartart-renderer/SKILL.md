---
name: smartart-renderer
description: Renders SmartArt graphics from specs using three engines (Mermaid CLI, Vega-Lite CLI, custom SVG). Runs draft-phase comparator, handles enrichment compositing, writes SmartArtManifest. Dispatches image-reviewer for quality scoring.
argument-hint: --mode draft|production
allowed-tools: Bash(python *), Bash(npx *), Bash(node *), Read, Glob, Agent
---

# /smartart-renderer

Render SmartArt graphics from structured specs. This skill is invoked after `smartart-extractor` has produced specs and after `imagegen-bridge` has generated any enrichment images (T1/T2/T3).

## Parse Arguments

Parse `$ARGUMENTS` for:
- **--mode MODE**: `draft` or `production` (default: `draft`)

In **draft** mode: run comparator (multiple engines) when `comparator_engines` has >1 entry.
In **production** mode: render via winning engine only (from previous draft's manifest).

## Prerequisites

Before running:
- `./tmp/deck/smartart-spec.json` — SmartArtSpec with per-slide rendering data
- `./tmp/deck/style-guide.json` — StyleGuide for design tokens
- `./tmp/deck/image-manifest.json` — ImageManifest (for enrichment images with `smartart_ref`)
- `./tmp/deck/pipeline-state.json` — PipelineState for phase determination
- `./tmp/deck/smartart/` directory exists

## Step 1: Read Inputs

```bash
.venv/bin/python3 -c "
import json
with open('./tmp/deck/smartart-spec.json') as f:
    spec = json.load(f)
print(f'SmartArt specs to render: {len(spec[\"specs\"])}')
for s in spec['specs']:
    engines = s.get('comparator_engines', [])
    cmp = f' (comparator: {engines})' if len(engines) > 1 else ''
    print(f'  Slide {s[\"slide_number\"]}: {s[\"graphic_type\"]} via {s[\"engine\"]}{cmp}')
"
```

## Step 2: Render Each Spec

```bash
.venv/bin/python3 -c "
import json, os
from src.smartart_renderer import render

with open('./tmp/deck/smartart-spec.json') as f:
    specs = json.load(f)
with open('./tmp/deck/style-guide.json') as f:
    style_guide = json.load(f)

output_dir = './tmp/deck/smartart'
os.makedirs(output_dir, exist_ok=True)

phase = 'draft'  # or 'production' based on --mode argument
entries = []
for spec in specs['specs']:
    entry = render(spec, style_guide, phase, output_dir)
    entries.append(entry)
    print(f'Slide {spec[\"slide_number\"]}: {entry[\"status\"]} via {entry[\"engine_used\"]}')

manifest = {'graphics': entries}
with open('./tmp/deck/smartart-manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)
print(f'Wrote {len(entries)} entries to smartart-manifest.json')
"
```

## Step 3: Review Quality (Draft Phase)

For each rendered graphic, dispatch the `image-reviewer` agent with SmartArt-specific context:

- `review_context: "smartart_comparator"` — for comparator candidates (score both, pick winner)
- `review_context: "smartart_enrichment"` — for T1/T2 enrichment images
- `review_context: "smartart_full_render"` — for T3 full AI renders (check data fidelity)

The reviewer uses adapted criteria:
- Data legibility (0.35 weight)
- Layout clarity (0.25 weight)
- Aesthetic quality (0.20 weight)
- Style compliance (0.20 weight)

## Step 4: Handle Comparator Results

If the comparator ran (draft phase, multiple engines):
1. Collect reviewer scores for each candidate
2. Select winner by highest weighted score
3. Update manifest entry with comparator_results
4. Log to render-log.json

## Step 5: Enrichment Compositing

For T1 (ai_background): composite SmartArt PNG over background image.
For T2 (ai_elements): composite element icons into SmartArt at node positions.
For T3: if data fidelity fails 3x, auto-downgrade to T1.

Enrichment images come from ImageManifest entries with matching `smartart_ref`.

## Step 6: Validate Output

```bash
.venv/bin/python3 -c "
import json
from src.deckcontext import validate_contract
with open('./tmp/deck/smartart-manifest.json') as f:
    manifest = json.load(f)
validate_contract('smartart-manifest', manifest)
print(f'SmartArtManifest validates: {len(manifest[\"graphics\"])} graphics')
"
```

## Output

- File: `./tmp/deck/smartart-manifest.json`
- Schema: `src/schemas/smartart_manifest.schema.json`
- SVG sources: `./tmp/deck/smartart/*.svg`
- Rendered PNGs: `./tmp/deck/smartart/*.png`
