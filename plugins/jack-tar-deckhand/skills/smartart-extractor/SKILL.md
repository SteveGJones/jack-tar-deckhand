---
name: smartart-extractor
description: Transforms approved slide content into engine-specific structured data for SmartArt rendering. Reads SmartArtRecommendations, extracts data from SlideOutline body_points, validates against target engine schemas, handles overflow. Writes smartart-spec.json.
allowed-tools: Bash(python *), Read, Glob
---

# /smartart-extractor

Extract structured data from slide content for SmartArt rendering. This skill is invoked after `smartart-selector` has produced approved recommendations and after `strategy-map` has classified slides.

You run the Python extractor module for each approved SmartArt slide, validate the output, and write the SmartArtSpec contract.

## Prerequisites

Before running, these DeckContext files must exist:
- `./tmp/deck/smartart-recommendations.json` — approved graphic types and tiers
- `./tmp/deck/outline.json` — SlideOutline with body_points content
- `./tmp/deck/strategy-map.json` — StrategyMap with smartart_config
- `./tmp/deck/style-guide.json` — StyleGuide for token extraction

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

## Step 1: Read Inputs

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
with open('./tmp/deck/smartart-recommendations.json') as f:
    recs = json.load(f)
approved = [s for s in recs['slides'] if s.get('approval_status') == 'approved']
print(f'Approved SmartArt slides: {len(approved)}')
for s in approved:
    idx = s.get('selected_index', 0)
    r = s['recommendations'][idx]
    print(f'  Slide {s[\"slide_number\"]}: {r[\"graphic_type\"]} ({r[\"engine\"]}, {r[\"enrichment_tier\"]})')
"
```

## Step 2: Extract Data for Each Slide

For each approved slide, run the extractor:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.smartart_extractor import extract

with open('./tmp/deck/outline.json') as f:
    outline = json.load(f)
with open('./tmp/deck/smartart-recommendations.json') as f:
    recs = json.load(f)
with open('./tmp/deck/style-guide.json') as f:
    style_guide = json.load(f)

specs = []
for rec_slide in recs['slides']:
    if rec_slide.get('approval_status') != 'approved':
        continue
    slide_num = rec_slide['slide_number']
    slide = next(s for s in outline['slides'] if s['slide_number'] == slide_num)
    idx = rec_slide.get('selected_index', 0)
    selection = rec_slide['recommendations'][idx]
    selection['slide_number'] = slide_num

    spec = extract(slide, selection, style_guide)
    specs.append(spec)
    print(f'Slide {slide_num}: {spec[\"graphic_type\"]} ({spec[\"engine\"]}) — {spec[\"validation_status\"]}')

result = {'specs': specs}
with open('./tmp/deck/smartart-spec.json', 'w') as f:
    json.dump(result, f, indent=2)
print(f'Wrote {len(specs)} specs to smartart-spec.json')
"
```

## Step 3: Validate Output

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.deckcontext import validate_contract
with open('./tmp/deck/smartart-spec.json') as f:
    spec = json.load(f)
validate_contract('smartart-spec', spec)
print('SmartArtSpec validates against schema')
"
```

## Step 4: Review Extraction Results

Check each spec for:
- `validation_status: "valid"` — extraction succeeded
- `overflow_applied: "none"` — or appropriate overflow policy applied
- Data structure matches the target engine's expectations

If any spec has `validation_status: "invalid"`, report the issue and suggest the conductor re-run the selector for that slide.

## Output

- File: `./tmp/deck/smartart-spec.json`
- Schema: `src/schemas/smartart_spec.schema.json`
