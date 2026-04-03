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

## Step 0: Read Local Config

Before any image generation, read `local-config.json` from the project root to get machine-specific Ollama model tags and timeouts. This file is gitignored — it contains the exact model identifiers installed on this machine (e.g., `x/z-image-turbo:fp8` not `x/z-image-turbo`).

```bash
python3 -c "
import json
with open('local-config.json') as f:
    config = json.load(f)
print(json.dumps(config, indent=2))
"
```

Use `config.ollama.default_image_model` for hero/background/element images and `config.ollama.default_diagram_model` for diagrams. **Never hardcode Ollama model names** — always read from this file.

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

4. After Stage 1 (Ollama), **view the generated image** (Read tool) and assess it using the per-image review criteria in Step 7. If not acceptable, refine the prompt and retry (up to 10 iterations — Ollama is free). Save each attempt as `slide-NN-hero-vN.png`.
5. After Stage 2 (cloud_low), view and assess. If acceptable, proceed to Stage 3 (cloud_full). If not, refine and retry (up to 3 iterations — cloud costs money).

## Step 5: Check Cache for Each Image

**Production mode:** If `production-upgrade-plan.json` exists in the deck directory, skip this step and use Step 9A instead. The upgrade plan takes precedence over the routing matrix for production renders.

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

### Simple backgrounds: prefer Ollama

For atmospheric dark backgrounds, subtle textures, and neutral surfaces (strategy: `background` or `pragmatic_composition` background), prefer Ollama over cloud providers. Cloud models (especially Nanobanana) over-generate from vague atmospheric prompts, adding unwanted complexity, objects, and even text. Ollama produces cleaner, subtler results for this use case — and it's free.

Reserve cloud providers for images that need:
- Specific complex subjects (product photography, conceptual illustrations)
- Text-in-image accuracy
- High-resolution photorealistic detail

## Step 7: Generate Images With Review-and-Refine Loop

For each slide that needs generation, invoke the appropriate skill. Process slides sequentially.

**IMPORTANT: Store the prompt.** After generating each image, you MUST include the `source_prompt` field in the image manifest entry. This is the translated prompt that was actually sent to the model. The production upgrade plan needs these prompts to re-render at higher quality without regenerating them. Without `source_prompt`, the production pipeline cannot function.

### Per-image review cycle (MANDATORY)

After generating EVERY image, dispatch the `image-reviewer` agent to assess it. This keeps images out of the main orchestration context.

1. **Generate** the image with the current prompt
2. **Dispatch** the `image-reviewer` agent with:
   - Image path: the just-generated file
   - Visual direction: from outline.json for this slide
   - Brand palette: hex values from brand-profile.json
   - Strategy: from strategy-map.json for this slide
   - Element ID: from strategy-map element_layout (if applicable)
   - Iteration: current attempt number out of max (e.g., "3 of 10")

   Example dispatch:
   ```
   Review this generated image for quality.
   Image: ./tmp/deck/images/slide-10-scene-v3.png
   Visual direction: "Side profile view of two heads facing each other..."
   Brand palette: #006B5E, #5CDBC0, #0E1513, #F5FBF7
   Strategy: backdrop
   Iteration: 3 of 10
   ```

3. **Parse the JSON verdict** returned by the agent
4. **If verdict is "pass":** proceed to next image, log the summary
5. **If verdict is "refine":** use the `issues` array to guide prompt refinement, regenerate, and dispatch a new agent review
6. **Escalation:** after 3 consecutive "refine" verdicts, re-dispatch the image-reviewer at Sonnet tier for a more nuanced assessment
7. **Hard stop:** after 10 iterations total, accept the best version. Set status to `"accepted_with_issues"` in the manifest and store the final summary in `"review_summary"`
8. **Save versions** as `slide-NN-TYPE-vN.png` so the Speaker can review alternatives if needed. The final accepted version overwrites `slide-NN-TYPE.png`.

**Context savings:** The main context keeps only the `summary` string (~50 chars) per review, not the image itself. A 17-slide deck with 3 iterations each accumulates ~17 short strings instead of ~51 images.

**Never skip review.** A broken image that reaches the assembled deck wastes the Speaker's time and undermines confidence in the pipeline.

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

## Step 9A: Production Mode — Execute Upgrade Plan

In production mode, the imagegen-bridge reads `production-upgrade-plan.json` instead of computing routing decisions. The image-generation-expert agent has already determined the optimal engine for each slide.

```bash
source .venv/bin/activate && python3 -c "
from src.image_router import load_upgrade_plan, execute_upgrade_plan_entry
import json

plan = load_upgrade_plan('./tmp/deck')
for entry in plan['entries']:
    params = execute_upgrade_plan_entry(entry)
    print(f'Slide {entry[\"slide_number\"]}: {params[\"skill\"]} via {params[\"provider\"]} ({params[\"model\"]})')
"
```

For each entry:

### raster_upscale entries

Invoke `cloud-generate-image` with the plan's provider, model, and dimensions:

```bash
/cloud-generate-image "DRAFT_PROMPT" --provider PROVIDER --model MODEL --width WIDTH --height HEIGHT --output ./tmp/deck/images/slide-NN-hero.png
```

The draft prompt is carried from the draft ImageManifest via the plan's `draft_prompt` field. Use it directly — it was already validated during drafting.

### vector_conversion entries

Invoke `cloud-generate-icon` with Recraft:

```bash
/cloud-generate-icon "DRAFT_PROMPT" --provider recraft --output ./tmp/deck/images/slide-NN-diagram.svg
```

The output is SVG. After generation, rasterise it to PNG using `src/process_image.py`, passing the slide's background colour to fix Recraft's default white backgrounds:

```python
from src.process_image import rasterize_svg

# Get slide background colour from the StyleGuide's slidePalette:
#   title slides:   slidePalette.title_slide.background   (or palette.primary)
#   content slides: slidePalette.content_slides.background (or palette.background)
#   code slides:    slidePalette.code_slides.background    (or '#0E1513')
result = rasterize_svg(
    'tmp/deck/images/slide-NN-diagram.svg',
    'tmp/deck/images/slide-NN-diagram.png',
    width=1920,
    background_color=slide_bg_color,  # e.g. '#F5FBF7' or '#0E1513'
)
```

This replaces Recraft's near-white SVG backgrounds with the actual slide background colour, preventing visible white rectangles on assembled slides.

### Recraft prompt patterns (learned from production)

Recraft V4 interprets prompts differently from raster models. Follow these rules:

1. **Enumerate every element explicitly** — "Rectangle 1: labeled 'Brief'. Rectangle 2: labeled 'Brand'." not "8 connected stages flowing left to right"
2. **Specify the topology** — "snake pattern with 3 rows" or "single horizontal row" or "2x2 grid" not just "flow diagram"
3. **Forbid extras explicitly** — "No title. No subtitle. No footer. No annotations. No sub-labels. Only the N elements described above."
4. **Describe layout geometry** — "wide horizontal bar spanning full width at top" not just "orchestrator across the top"
5. **Consider slide aspect ratio** — 8 items in a horizontal line on a 16:9 slide will be tiny. Use snake/grid layouts for >4 nodes.
6. **Use design vocabulary** — "rounded rectangle filled with deep teal (#006B5E)" not "clean geometric node in brand teal"

These patterns reduced Recraft iterations from 3+ to 1-2 per diagram.

### Prompt selection for production upgrades

For slides with a single image, use the outline's `visual_direction` as the prompt (it may have been refined during drafting).

For slides with multiple element images (pragmatic_composition, three_across layouts), use the `draft_prompt` from the production upgrade plan entry for each element — NOT the outline's `visual_direction`. The outline has one visual_direction per slide but element images each need their own distinct prompt. Using the slide-level prompt for all elements produces identical images.

**Rule:** If `image_id` contains `elem-`, always use the production plan's `draft_prompt` for that entry.

### no_upgrade entries

Skip — the existing draft image is already production quality (matplotlib chart or similar).

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

Each image entry in `$IMAGES_LIST` MUST include `source_prompt` — the translated prompt that was sent to the generation model. Example entry:
```json
{
  "slide_number": 1,
  "file_path": "./tmp/deck/images/slide-01-hero.png",
  "status": "generated",
  "content_hash": "abc123...",
  "dimensions": {"width": 1024, "height": 576},
  "alt_text": "Headline text",
  "image_id": "slide-01-hero",
  "model_used": "x/z-image-turbo",
  "source_prompt": "A dramatic teal wave cresting over..."
}
```

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
