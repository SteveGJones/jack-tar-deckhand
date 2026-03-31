---
name: imagegen-bridge
description: Top-level image orchestrator. Routes all slide image generation to the appropriate skill (ollama-image, ollama-icon, ollama-pattern, ollama-diagram, cloud-generate-image, cloud-generate-icon, render_chart). Produces ImageManifest and ChartManifest. Also reads strategy-map.json to determine per-slide rendering approach (full_render, backdrop_render, composed).
argument-hint: --mode draft|production
allowed-tools: Bash(python *), Bash(curl *), Read, Glob, Skill
---

# /imagegen-bridge

Orchestrate ALL image generation for a presentation deck. This skill is invoked by the Deck Conductor after the SlideOutline and StyleGuide have been produced.

You are the routing orchestrator. You NEVER generate images directly. You read the DeckContext, classify each slide's image needs, route to the appropriate generation skill, track budget and cache, post-process results, and write the ImageManifest and ChartManifest.

Consult the `image-generation-expert` agent for prompt translation advice when generating production-quality hero images.

## Parse Arguments

Parse `$ARGUMENTS` for:
- **--mode MODE**: `draft` or `production` (default: `draft`)

## Step 1: Run Provider Discovery

Discover which image generation providers are available for this run.

```bash
python3 -c "
import json
from src.provider_discovery import discover_providers
providers = discover_providers(config_path='provider_config.json')
print(json.dumps(providers, indent=2))
"
```

Parse the JSON output into an `available_providers` dict. Report the findings:
- Which providers are available (Ollama, OpenAI, Google, FAL.ai, Recraft)
- Which Ollama models are installed (if Ollama is available)
- Whether any cloud providers are configured

If NO providers are available at all (no Ollama, no cloud), warn that all images will be placeholders but continue -- the deck must always be completable.

## Step 2: Read DeckContext Inputs

Read the required DeckContext files:

1. Read `./tmp/deck/outline.json` (SlideOutline) using the Read tool
2. Read `./tmp/deck/style-guide.json` (StyleGuide) using the Read tool
3. Read `./tmp/deck/talk-brief.json` (TalkBrief) using the Read tool -- needed for data_sources (charts)
4. Read `./tmp/deck/strategy-map.json` (StrategyMap) if it exists — determines per-slide rendering strategy
5. Read `./tmp/deck/brand-profile.json` (BrandProfile) if it exists — provides palette for prompt constraints

Verify all three required files exist. If any is missing, report the error and stop.

Parse the JSON content of each file.

## Step 3: Initialise Budget Tracker

Read or initialise the budget state:

```bash
python3 -c "
import json, os
budget_path = './tmp/deck/budget-state.json'
if os.path.exists(budget_path):
    with open(budget_path) as f:
        budget = json.load(f)
    print(json.dumps(budget))
else:
    print(json.dumps({'state': 'allow', 'spent': 0.0, 'total_budget': 2.0}))
"
```

Parse the budget state. The `state` field is one of: `allow`, `allow_with_caps`, `degrade`, `typography_only`.

## Step 4: Route All Slides

If a strategy map exists, check each slide's strategy before routing:
- **full_render** or **backdrop_render** slides: Use the three-stage render funnel. Dispatch the `prompt-engineer` agent (Haiku model) with a structured brief from `assemble_brief()`, then render through Ollama → cloud_low → cloud_full stages.
- **composed** slides: Use the standard routing matrix (unchanged).

Use the image router to determine which skill handles each slide:

```bash
python3 -c "
import json
from src.image_router import route_all_slides, get_chart_slides

with open('./tmp/deck/outline.json') as f:
    outline = json.load(f)

providers = $PROVIDERS_DICT
budget_state = '$BUDGET_STATE'
mode = '$MODE'

decisions = route_all_slides(outline, mode, providers, budget_state)
charts = get_chart_slides(outline)

result = {
    'image_decisions': [d._asdict() for d in decisions],
    'chart_slides': charts,
}
print(json.dumps(result, indent=2))
"
```

Review the routing decisions. Report a summary table:

| Slide | Visual Type | Skill | Provider | Model | Est. Cost | Fallback? |
|-------|-------------|-------|----------|-------|-----------|-----------|

### Step 4.5: Render Funnel (for keynote slides)

For slides with strategy `full_render` or `backdrop_render`:

1. Assemble a structured brief:
```bash
source .venv/bin/activate && python3 -c "
from src.slide_prompt_composer import assemble_brief
import json
with open('./tmp/deck/outline.json') as f:
    outline = json.load(f)
with open('./tmp/deck/style-guide.json') as f:
    style_guide = json.load(f)
brief = assemble_brief(outline['slides'][SLIDE_INDEX], 'STRATEGY', style_guide, brand_profile, 'FUNNEL_STAGE')
print(json.dumps(brief, indent=2))
"
```

2. Dispatch the `prompt-engineer` agent with the brief to generate the image prompt.

3. Execute the funnel stage:
```bash
source .venv/bin/activate && python3 -c "
from src.render_funnel import execute_funnel_stage
result = execute_funnel_stage(
    deck_dir='./tmp/deck',
    slide_number=N,
    strategy='STRATEGY',
    prompt='GENERATED_PROMPT',
    funnel_stage='STAGE',
    model='MODEL',
    output_path='./tmp/deck/images/slide-NN-hero.png',
)
import json; print(json.dumps(result, indent=2))
"
```

4. After Stage 1 (Ollama), review the result. If acceptable, proceed to Stage 2 (cloud_low). If not, refine the prompt and retry (up to 3 iterations).
5. After Stage 2 (cloud_low), if acceptable, proceed to Stage 3 (cloud_full). This is the final render -- no iteration at this tier.

## Step 5: Check Cache for Each Image

For each routing decision where `skill` is not `skip` and not `placeholder`:

```bash
python3 -c "
from src.cache_manager import ImageCacheManager

cache = ImageCacheManager()
cache_key = cache.compute_cache_key('$VISUAL_DIRECTION', ($WIDTH, $HEIGHT), 'presentation', '$MODEL', $PALETTE_LIST)
cached = cache.get(cache_key)
print(f'CACHE_HIT:{cache_key}' if cached is not None else f'CACHE_MISS:{cache_key}')
cache.close()
"
```

Track which slides have cache hits and which need generation.

## Step 6: Construct Prompts

For each slide that needs generation (cache miss), construct the model-specific prompt:

```bash
python3 -c "
from src.prompt_translator import translate_prompt
import json

translated = translate_prompt(
    visual_direction='''$VISUAL_DIRECTION''',
    model='$MODEL_NAME',
    style_guide=$STYLE_GUIDE_DICT,
)
print(json.dumps(translated, indent=2))
"
```

For production-mode hero images, consult the `image-generation-expert` agent before finalising the prompt.

### Background colour in element prompts (pragmatic_composition)

For `pragmatic_composition` slides that do NOT have a separate background image, include the target background colour in every element image prompt. Use descriptive language alongside hex values since Ollama models approximate hex colours rather than interpreting them precisely:

> "on a very dark background, almost black with slight teal tint, hex #0E1513"

Use **identical** background description text across all element prompts for that slide. This is critical because the assembler samples the corner pixel of the first element image to set the slide background colour. If one element has a noticeably different background, it will create visible seams where the element image meets the slide background.

## Step 7: Generate Images

For each slide that needs generation, invoke the appropriate skill. Process slides sequentially.

### Element image aspect ratios (pragmatic_composition)

For `pragmatic_composition` slides, calculate the target aspect ratio from the strategy map's `element_layout` dimensions before generating each element image. For each element: `aspect_ratio = element.w / element.h` (normalised coordinates). Then set `--width` and `--height` to match this ratio at the desired resolution. For example, for a 2.79:1 ratio at 1024px wide: `--width 1024 --height 368`. Do NOT generate square images for non-square placement boxes -- the image will be stretched or cropped by the assembler, degrading quality.

### For ollama-image (hero_image in draft mode):
```
/ollama-image "TRANSLATED_PROMPT" --output ./tmp/deck/images/slide-NN-hero.png --width 1024 --height 576 --model x/z-image-turbo
```

### For ollama-pattern (pattern_background in draft mode):
```
/ollama-pattern "TRANSLATED_PROMPT" --output ./tmp/deck/images/slide-NN-pattern.png --width 1024 --height 1024
```

### For ollama-diagram (diagram in any mode):
```
/ollama-diagram "TRANSLATED_PROMPT" --type TYPE --output ./tmp/deck/images/slide-NN-diagram.png --width 1024 --height 768
```

### For cloud-generate-image (hero/pattern in production mode):
```
/cloud-generate-image "TRANSLATED_PROMPT" --output ./tmp/deck/images/slide-NN-TYPE.png --provider PROVIDER --quality QUALITY_TIER
```

### For cloud-generate-icon (icon_set in any mode):
```
/cloud-generate-icon "TRANSLATED_PROMPT" --output ./tmp/deck/images/slide-NN-icon --provider PROVIDER --colors PALETTE_HEX
```

### For render_chart (chart type):
```bash
python3 -c "
from src.render_chart import render_chart
result = render_chart(chart_type='$CHART_TYPE', data=$DATA, output_path='./tmp/deck/images/slide-NN-chart.png', style_guide=$STYLE_GUIDE)
import json; print(json.dumps(result))
"
```

### For placeholder:
```bash
python3 -c "
from src.process_image import generate_placeholder
generate_placeholder(width=1920, height=1080, colour='$HEX', output_path='./tmp/deck/images/slide-NN-placeholder.png')
"
```

## Step 8: Handle Failures and Fallbacks

If any skill invocation fails:
1. Log the failure: slide number, skill, error message
2. Re-run route_slide with the failed provider removed from available_providers
3. Retry with the fallback skill
4. If all fallbacks exhausted, generate a placeholder
5. Record with `status: "failed"` or `status: "placeholder"`

## Step 9: Track Budget

After each cloud generation, update the budget tracker:

```bash
python3 -c "
from src.budget_tracker import BudgetTracker
import json

budget_path = './tmp/deck/budget-state.json'
with open(budget_path) as f:
    budget_data = json.load(f)

bt = BudgetTracker(total_budget_usd=budget_data['total_budget'])
bt.log_api_call('$MODEL', $COST, '$IMAGE_ID')
budget_data['spent'] = bt.spent
budget_data['state'] = bt.state

with open(budget_path, 'w') as f:
    json.dump(budget_data, f, indent=2)
print(f'Budget: \${bt.spent:.3f} / \${budget_data[\"total_budget\"]:.2f} ({bt.state})')
"
```

If budget state changes, re-route remaining slides with the new budget state.

## Step 9.5: Realign Detected Positions (backdrop / pragmatic_composition slides)

After generating or regenerating any image for a slide whose strategy is `backdrop` or `pragmatic_composition`, you MUST re-run vision alignment to update `detected_positions` in the ImageManifest. The old coordinates are stale the moment the image changes.

1. Read the strategy map to check if the slide uses `backdrop` or `pragmatic_composition`.
2. If yes, dispatch the `vision-analyst` agent with:
   - The newly generated image path
   - The element descriptions from the strategy map's `element_layout.elements`
   - The expected element count
3. Map the returned `elem_N` IDs back to the element IDs from the strategy map (in left-to-right, top-to-bottom order).
4. Write the updated `detected_positions` array into the slide's ImageManifest entry.

This step is **not optional**. Skipping it will cause text labels to misalign with the visual elements on the assembled slide.

**When to trigger:** Any time an image is generated, regenerated, or replaced for a position-dependent slide — including manual re-runs, prompt tuning, and production upgrades.

## Step 10: Post-Process Generated Images

For each generated image (not cached, not placeholder):

```bash
python3 -c "
from src.process_image import resize, crop_to_aspect, compute_content_hash
resize('$PATH', $WIDTH, $HEIGHT)
crop_to_aspect('$PATH', '16:9')
content_hash = compute_content_hash('$PATH')
print(f'hash:{content_hash}')
"
```

## Step 11: Cache Generated Images

```bash
python3 -c "
from src.cache_manager import ImageCacheManager
cache = ImageCacheManager()
cache.put('$CACHE_KEY', open('$IMAGE_PATH', 'rb').read())
cache.close()
"
```

## Step 12: Build and Write ImageManifest

```bash
python3 -c "
import json
from datetime import datetime, timezone
from src.deckcontext import write_contract

images = $IMAGES_LIST
manifest = {
    'generated_at': datetime.now(timezone.utc).isoformat(),
    'image_backend': 'multi-model',
    'images': images,
    'summary': {
        'total_images': len(images),
        'generated_count': sum(1 for i in images if i['status'] == 'generated'),
        'cached_count': sum(1 for i in images if i['status'] == 'cached'),
        'placeholder_count': sum(1 for i in images if i['status'] == 'placeholder'),
        'failed_count': sum(1 for i in images if i['status'] == 'failed'),
        'total_generation_seconds': round(sum(i.get('generation_time_seconds', 0) for i in images), 2),
    },
}
write_contract('./tmp/deck', 'image-manifest', manifest)
print(json.dumps(manifest['summary'], indent=2))
"
```

## Step 13: Build and Write ChartManifest

```bash
python3 -c "
import json
from src.deckcontext import write_contract
charts = $CHARTS_LIST
write_contract('./tmp/deck', 'chart-manifest', {'charts': charts})
print(f'Charts rendered: {len(charts)}')
"
```

## Step 14: Report Generation Summary

```
=== Image Generation Summary ===
Mode: draft|production
Provider availability: Ollama (yes/no), OpenAI (yes/no), Google (yes/no), FAL (yes/no), Recraft (yes/no)

Images:
  Total: N
  Generated: N (N via Ollama, N via cloud)
  Cached: N (saved $X.XX)
  Placeholders: N
  Failed: N

Charts:
  Total: N
  Rendered: N

Budget:
  Spent: $X.XX / $X.XX (NN%)
  Budget state: allow|allow_with_caps|degrade|typography_only

Timing:
  Total generation time: Xs
  Average per image: Xs
```

Do not ask follow-up questions. Report and stop.
