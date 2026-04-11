---
name: smartart-selector
description: Orchestrates the SmartArt type selection negotiation. Dispatches the smartart-selector agent to recommend graphic types and enrichment tiers, then runs approval/rejection loop with the narrative-architect. Writes smartart-recommendations.json.
allowed-tools: Bash(python *), Read, Glob, Agent
---

# /smartart-selector

Orchestrate the SmartArt graphic type and enrichment tier selection for all slides in a deck. You dispatch the `smartart-selector` agent to propose recommendations, then evaluate them as the narrative-architect (considering narrative arc, audience, and adjacency) to approve or reject.

## Prerequisites

Before running, these DeckContext files must exist:
- `./tmp/deck/outline.json` — SlideOutline with optional `visual_intent` fields
- `./tmp/deck/style-guide.json` — StyleGuide for design token feasibility
- `./tmp/deck/talk-brief.json` — TalkBrief for audience and tone context
- `./tmp/deck/pipeline-state.json` — PipelineState for budget state

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

## Step 1: Read DeckContext

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
with open('./tmp/deck/outline.json') as f:
    outline = json.load(f)
with open('./tmp/deck/style-guide.json') as f:
    style_guide = json.load(f)
with open('./tmp/deck/talk-brief.json') as f:
    talk_brief = json.load(f)
print(f'Slides: {len(outline[\"slides\"])}')
candidates = [s for s in outline['slides'] if s.get('visual_intent')]
print(f'SmartArt candidates (explicit visual_intent): {len(candidates)}')
"
```

## Step 2: Dispatch SmartArt Selector Agent

Use the Agent tool to dispatch the `smartart-selector` agent. Provide:
- The full SlideOutline (all slides, for adjacency context)
- StyleGuide palette and typography
- TalkBrief audience and tone
- Current budget state from pipeline-state.json

The agent returns JSON with 2-3 ranked recommendations per candidate slide.

## Step 3: Evaluate Recommendations (as Narrative Architect)

For each candidate slide, evaluate the agent's recommendations against:
1. **Narrative arc** — does this graphic type serve the story at this point?
2. **Audience context** — is the enrichment level appropriate for this audience?
3. **Adjacent slides** — would this create visual repetition with neighbouring slides?
4. **Content fit** — does the data in body_points actually suit this graphic type?

**Approve** the best recommendation or **reject all** with specific feedback.

## Step 4: Handle Rejections (max 2 rounds)

If rejecting, provide clear feedback:
- "The data is comparative, not sequential — suggest a matrix or radar instead"
- "Too many flowcharts in sequence — try a different visual for variety"

Re-dispatch the agent with the feedback. After 2 rejection rounds, fall back to `composed` strategy for that slide.

## Step 5: Write SmartArtRecommendations

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.deckcontext import write_contract, validate_contract
recommendations = {
    'slides': [...]  # approved recommendations
}
validate_contract('smartart-recommendations', recommendations)
write_contract('./tmp/deck', 'smartart-recommendations', recommendations)
print('SmartArtRecommendations written')
"
```

## Output

- File: `./tmp/deck/smartart-recommendations.json`
- Schema: `src/schemas/smartart_recommendations.schema.json`
- Each slide entry has `approval_status: "approved"` and `selected_index` pointing to the chosen recommendation
