---
name: imagegen-bridge
description: Top-level image orchestrator. Routes all slide image generation to the appropriate skill (jack-tar-ollama:image, jack-tar-ollama:icon, jack-tar-ollama:pattern, jack-tar-ollama:diagram, jack-tar-cloud:image, jack-tar-cloud:icon, render_chart). Produces ImageManifest and ChartManifest. Also reads strategy-map.json to determine per-slide rendering approach (full_render, backdrop_render, composed).
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

## Step 1: Discover Engine Plugins

Call each engine plugin's verify skill to discover what's available. Extract the STATUS line from each response.

Call in sequence:
1. `/jack-tar-ollama:verify`
2. `/jack-tar-cloud:verify`

Parse each response:
- For jack-tar-ollama: STATUS line tells you if Ollama is FULLY_AVAILABLE (has image models), PARTIALLY_AVAILABLE, or NOT_AVAILABLE. If FULLY_AVAILABLE or PARTIALLY_AVAILABLE, parse the MODELS section to get available model names.
- For jack-tar-cloud: STATUS line and PROVIDERS section tells you which cloud providers are ready.

Build the `available_providers` dict:
```python
{
    "ollama": {
        "available": True/False,
        "models": ["x/z-image-turbo", ...]  # from MODELS section
    },
    "openai": {"available": True/False},
    "google": {"available": True/False},
    "fal": {"available": True/False},
    "recraft": {"available": True/False}
}
```

If jack-tar-ollama is not installed or returns NOT_AVAILABLE, set `ollama.available = False`.
If jack-tar-cloud is not installed or returns NOT_AVAILABLE, set all cloud providers to False.

Report the findings:
- Which providers are available
- Which Ollama models are installed (if Ollama is available)
- Whether any cloud providers are configured

If NO providers are available, warn that all images will be placeholders but continue — the deck must always be completable.

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
- **academic_figure** slides: Route through the paperbanana CLI subprocess dispatch — see **Step 4.6** below.
- **composed** slides: Use the standard routing matrix (unchanged).

Use the image router to determine which skill handles each slide:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
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
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
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
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
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

### Step 4.6: Academic Figure Dispatch (paperbanana CLI subprocess route)

For slides whose strategy is `academic_figure` (set by the strategy
classifier — see `src/strategy_classifier.py`), the bridge renders a
**free local draft via Ollama first** whenever a local image model is
detected (`x/flux2-klein`, `x/z-image-turbo`), then holds at the F10
operator gate before any paid tier. Paid escalation goes to the
**paperbanana CLI via subprocess** when paperbanana is installed, and
falls back to a cloud render with academic-figure-aware prompting when
it is not. With no local model, the ladder starts at paperbanana/cloud
exactly as before.

Paperbanana is treated as an external CLI tool (sibling orchestrator),
not a Claude Code plugin or a cross-skill dispatch target. See
`docs/architecture/paperbanana-integration-v2.md` for the framing
rationale.

The dispatch decision is built by `src/paperbanana_dispatch.py`. Use
it from the bridge as the single source of truth — do NOT duplicate
the availability check inline.

1. **Build the dispatch payload**:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.paperbanana_dispatch import build_dispatch_payload

with open('./tmp/deck/outline.json') as f:
    outline = json.load(f)

slide = next(s for s in outline['slides'] if s['slide_number'] == $SLIDE_NUMBER)

# Honour the operator's model override from local-config.json when present.
preferred = None
try:
    with open('local-config.json') as f:
        preferred = json.load(f).get('ollama', {}).get('academic_figure_model')
except FileNotFoundError:
    pass

from src.paperbanana_dispatch import detect_local_backend
# local_only: slide-level key wins; otherwise the machine-wide config
# value (ollama.academic_figure_local_only) applies.
machine_local_only = False
try:
    with open('local-config.json') as f:
        machine_local_only = bool(
            json.load(f).get('ollama', {}).get('academic_figure_local_only', False)
        )
except FileNotFoundError:
    pass

dispatch = build_dispatch_payload(
    slide,
    output_dir='./tmp/deck/images',
    local_backend=detect_local_backend(preferred_model=preferred),
    local_only=bool(slide.get('local_only', machine_local_only)),
)
print(json.dumps({
    'backend': dispatch.backend,
    'local_only': dispatch.local_only,
    'available': dispatch.available,
    'args': dispatch.args,
    'local_provider': dispatch.local_provider,
    'local_model': dispatch.local_model,
    'local_args': dispatch.local_args,
    'output_dir': dispatch.output_dir,
    'slide_number': dispatch.slide_number,
    'fallback_provider': dispatch.fallback_provider,
    'fallback_model': dispatch.fallback_model,
    'fallback_reason': dispatch.fallback_reason,
}))
"
```

2. **If `dispatch.backend` is `"ollama"`** — render the free local
   draft first. `local_args` carries the composed academic-figure
   prompt and dimensions; `local_model` is the exact installed tag
   (never hardcode one):

```bash
OLLAMA_PLUGIN_ROOT=$(dirname "$PLUGIN_ROOT")/jack-tar-ollama
LOCAL_PROMPT=$(echo "$DISPATCH_JSON" | jq -r '.local_args.prompt')
LOCAL_MODEL=$(echo "$DISPATCH_JSON" | jq -r '.local_model')
OUT_PNG=$(echo "$DISPATCH_JSON" | jq -r '.output_dir')/slide-$(printf '%02d' $SLIDE_NUMBER)-academic-figure-ollama.png

python3 "$OLLAMA_PLUGIN_ROOT/src/generate_image.py" \
  --prompt "$LOCAL_PROMPT" \
  --model "$LOCAL_MODEL" \
  --width $(echo "$DISPATCH_JSON" | jq -r '.local_args.width') \
  --height $(echo "$DISPATCH_JSON" | jq -r '.local_args.height') \
  --output "$OUT_PNG"
```

   Then dispatch the `image-reviewer` agent on `$OUT_PNG` and run the
   **free critique loop**. The render budget per gate visit comes from
   `dispatch.local_args.iterations` — **3 in ladder mode, 5 in
   local_only mode** (validated 2026-07-11, see
   `docs/superpowers/dogfooding/2026-07-11-ollama-academic-figure-model-comparison.md`):

   - If the reviewer's verdict is `refine` or `fail` with **text
     corruption or structure drift** as the cause, rebuild the prompt
     as a **simplified label list** (F11 radical simplification):
     distil the caption + source_context into **≤8 short quoted
     labels** plus a one-line structure directive (e.g. five flow
     boxes labelled exactly "Conductor", "Narrative", …; three tier
     boxes under "Images"; "Critic" return arrow), keep the flat
     vector / white background / no-people style block, drop ALL
     prose. Re-render with the same model and re-review. The
     2026-07-11 loop took Klein 9b from REFINE (dense prose, ~85%
     label fidelity) to PASS (9/9 labels correct) in one iteration.
   - Stop early on a `pass` verdict, or when two consecutive renders
     show no reviewer-scored improvement (plateau — mirrors
     `creative_vision.cascade.detect_plateau`).

   **local_only mode** (`dispatch.local_only` true — set per-slide via
   `slide.local_only` or machine-wide via `local-config.json` →
   `ollama.academic_figure_local_only`): paid tiers DO NOT EXIST for
   this slide. Exhausting the budget surfaces best-so-far at the
   operator gate with exactly three choices: **accept**, **loop again**
   (another free budget — it costs nothing but time), or **hand-edit**.
   Never offer or dispatch paperbanana/cloud. If the dispatch came back
   `backend: "local_only_blocked"` (Ollama down), surface
   `fallback_reason` to the operator and mark the slide skipped — do
   NOT fall through to cloud.

   In **ladder mode**, apply the **F10 operator gate** on the best
   render — this is a free→cost boundary, so the gate is MANDATORY
   (see CLAUDE.md root):

   1. Open the draft for the operator (`open "$OUT_PNG"` on macOS).
   2. State the prospective paid escalation and its cost: paperbanana
      (~$0.14, when `dispatch.available` is true) or Nano Banana Flash
      1K ($0.067, `fallback_model`).
   3. WAIT for explicit operator go-ahead before ANY paid render. The
      image-reviewer's verdict is advisory — it does not authorise
      spend.

   If the operator **accepts the local draft**, write the manifest
   entry and stop here for this slide:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.paperbanana_dispatch import build_manifest_entry
# dispatch reconstructed from \$DISPATCH_JSON as in the other branches
entry = build_manifest_entry(
    dispatch,
    dispatch_succeeded=True,
    output_path='$OUT_PNG',
    content_hash='$SHA',
)  # backend_used defaults to the dispatch's own backend → 'ollama_local'
print(json.dumps(entry))
" >> ./tmp/deck/image-manifest.json
```

   If the operator **escalates**, continue to step 3 (paperbanana,
   when `dispatch.available` is true) or step 4 (cloud fallback) and
   pass `backend_used='paperbanana'` / `backend_used='cloud_fallback'`
   to `build_manifest_entry` so the manifest records the tier that
   actually produced the accepted image.

3. **If `dispatch.available` is true** (and there was no local draft,
   or the operator escalated past it) — dispatch paperbanana via
   subprocess. Write the `source_context` to a tmp file (paperbanana's
   CLI takes `--input <file>`, not inline text), then invoke the CLI:

```bash
# Write source_context to tmp file (jq extracts the field from the
# dispatch JSON saved above as $DISPATCH_JSON)
SRC_TMP=$(mktemp -t paperbanana-src.XXXXXX.txt)
echo "$DISPATCH_JSON" | jq -r '.args.source_context' > "$SRC_TMP"

# Build the CLI invocation from dispatch.args
CAPTION=$(echo "$DISPATCH_JSON" | jq -r '.args.caption')
ASPECT=$(echo "$DISPATCH_JSON" | jq -r '.args.aspect_ratio')
ITERS=$(echo "$DISPATCH_JSON" | jq -r '.args.iterations')
OUTPUT_DIR=$(echo "$DISPATCH_JSON" | jq -r '.output_dir')

# Run paperbanana. Pass explicit models (avoids paperbanana's deprecated
# defaults — upstream issue llmsresearch/paperbanana#214) and set a
# CLI-side budget guard ($0.25 cap per slide; jack-tar's own accounting
# is the authoritative gate since paperbanana's pricing table is
# incomplete — upstream #213).
PB_OUTPUT=$(paperbanana generate \
  --input "$SRC_TMP" \
  --caption "$CAPTION" \
  --aspect-ratio "$ASPECT" \
  --iterations "$ITERS" \
  --vlm-provider gemini --vlm-model gemini-2.5-flash \
  --image-provider google_imagen \
  --image-model gemini-3.1-flash-image-preview \
  --output "$OUTPUT_DIR" \
  --budget 0.25 2>&1)

# Parse paperbanana's stdout for the actual output path. The --output
# flag's parent-directory hint is NOT reliably honoured by current
# paperbanana versions (it sometimes writes to /tmp/run_*/ instead of
# $OUTPUT_DIR/run_*/) — see dogfooding/2026-05-18 finding F1. Always
# read paperbanana's `Output: <path>` line as authoritative.
PB_FILE=$(echo "$PB_OUTPUT" | grep -oE 'Output: [^ ]+' | head -1 | cut -d' ' -f2)

# Compute sha256 and build the manifest entry
SHA=$(shasum -a 256 "$PB_FILE" | cut -d' ' -f1)

PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.paperbanana_dispatch import PaperbananaDispatch, build_manifest_entry

dispatch = PaperbananaDispatch(
    available=True,
    slide_number=$SLIDE_NUMBER,
    output_dir='$OUTPUT_DIR',
    args=json.loads('''$DISPATCH_ARGS_JSON'''),
)
entry = build_manifest_entry(
    dispatch,
    dispatch_succeeded=True,
    output_path='$PB_FILE',
    content_hash='$SHA',
)
print(json.dumps(entry))
" >> ./tmp/deck/image-manifest.json
```

   After the CLI returns, dispatch the `image-reviewer` agent on the
   parsed `$PB_FILE` to verify quality (single pass — paperbanana does
   its own internal Critic-driven iteration up to `--iterations`).

4. **If `dispatch.available` is false** (and any local draft was
   escalated past) — log a warning containing
   `dispatch.fallback_reason` and fall back to the cloud path with
   `--provider $FALLBACK_PROVIDER --model $FALLBACK_MODEL`. Generate
   the image, run it through the standard `image-reviewer` cycle
   (Step 7), and record the manifest entry via
   `build_manifest_entry(dispatch, dispatch_succeeded=…, output_path=<jack-tar-conventional path>)`
   so the `backend: "cloud_fallback"` marker survives into the
   manifest. This is the **documented expected degradation path** when
   paperbanana is not installed locally — not an error. The verify
   skill's NOT_FOUND output already gives operators the install
   commands; we just take the fallback path silently in pipeline
   terms.

5. **Skip Step 5 (cache) and Step 6 (prompt translation)** for
   academic_figure slides. The cache key composition is paperbanana-
   specific and the prompt translation is owned by paperbanana itself
   (or by the cloud-fallback path's own prompt assembly).

6. **The `source_prompt` field carries the methodology text** (paperbanana's
   `source_context` arg) and the `caption` field carries the
   communicative intent — `build_manifest_entry` populates both
   automatically from `dispatch.args`. The iterate-slide skill (#89)
   will use the manifest's `paperbanana_run_id` + `paperbanana_args`
   to call `paperbanana generate --continue-run <id> --feedback "..."`
   for cheap critique-driven refinement (~$0.07 per refinement vs
   ~$0.14 for a full 2-iteration re-run from scratch).

> Do not `Read` PNG / JPG / GIF / WEBP / BMP / TIFF files directly.
> If you need to verify an image, dispatch the
> `jack-tar-deckhand:image-reviewer` subagent (Haiku, JSON verdict) or
> the `general-purpose` subagent (Sonnet, higher accuracy). Both
> subagents pull the image into THEIR context and return text.

### Step 4.7: Creative Vision Dispatch (multi-agent cascade loop)

For slides whose strategy is `creative_vision` (set by the strategy classifier or
operator override in `strategy-map.json`), the bridge drives a **multi-agent
orchestration loop** — not a single render call. The loop runs Director's Brief →
Prompt Reviewer → Render → image-reviewer → Director's Critic in sequence for each
cascade tier, escalating tiers until the Critic accepts or the budget is exhausted.

#### When to enter this branch

A slide has `strategy: creative_vision` in `strategy-map.json` AND a populated
`creative_vision.vision_prose` field. Skip slides flagged
`pending_vision_prose: true` — they are waiting for operator-provided prose and
must not enter the loop.

#### Pre-flight: initialise the dispatch manifest

```python
from src.creative_vision_dispatch import DispatchRequest, initialise_dispatch

req = DispatchRequest(
    deck_dir=deck_dir,
    slide_number=entry["slide_number"],
    vision_prose=entry["creative_vision"]["vision_prose"],
    budget_usd=entry["creative_vision"].get("budget_usd", 1.00),
    allowed_ceiling=entry["creative_vision"].get("allowed_ceiling", "pro_4k"),
    brand_fidelity=entry.get("brand_fidelity", "none"),
)
manifest = initialise_dispatch(req)
```

This creates `<deck_dir>/creative-vision/<slide_number>/manifest.json` and returns
the manifest dict. The manifest records every attempt, cost, and verdict so the
session can be resumed if interrupted.

#### The orchestration loop

Pull the cascade ladder and start at index 0 (`ollama`):

```python
from src.creative_vision.cascade import ladder_for, DEFAULT_ITERATION_CAPS
ladder = ladder_for(req.brand_fidelity)
current_tier_index = 0
per_tier_iteration_count = 0
cumulative_cost = 0.0
```

For each tier, run the following per-tier loop:

**Step A — Director's Brief (generate approved prompt)**

1. **Load deck-level creative anchors (issue #113 AC4).** Before building
   the brief input, check whether the deck has a ``creative_anchors.json``
   file at the deck root and, if so, pull the eligible anchors for this
   slide number:

   ```python
   from src.creative_vision.anchors import (
       load_anchors,
       anchors_for_slide,
       format_anchors_for_brief,
   )
   anchors_doc = load_anchors(req.deck_dir)  # None if no file
   anchors_section = ""
   if anchors_doc is not None:
       eligible = anchors_for_slide(anchors_doc, req.slide_number)
       anchors_section = format_anchors_for_brief(
           eligible, deck_brief=anchors_doc.get("deck_brief")
       )
   ```

   When ``creative_anchors.json`` is absent (the common case for single-slide
   decks), ``anchors_section`` stays empty and the Brief input is shaped
   exactly as it was pre-AC4.

2. Build the brief input via ``brief.build_brief_input(..., anchors_section=anchors_section)``.
3. Dispatch the `directors-brief` agent (Sonnet) with that input.
4. Parse via `brief.parse_brief_output(response)` → `(parsed_vision, prompt)`.

**Step B — Text-side gate (Brief ↔ Prompt Reviewer)**

Track loop state with `TextLoopState`:

```python
from src.creative_vision.orchestrator import TextLoopState, advance_text_loop
text_state = TextLoopState()
```

Loop:
- Build reviewer input via
  `prompt_reviewer.build_reviewer_input(original_prose, prompt, parsed_vision)`.
- Dispatch the `prompt-reviewer` agent (Haiku).
- Parse via `prompt_reviewer.parse_reviewer_output(response)` → `(verdict, issues)`.
- Advance state: `text_state = advance_text_loop(text_state, reviewer_verdict=verdict, reviewer_issues=issues, current_prompt=prompt)`.
- If `text_state.terminal` is False: re-dispatch `directors-brief` with
  `accumulated_feedback` extended by the reviewer's issues. Get a new prompt. Loop back.
- When `text_state.terminal` is True, the prompt is approved
  (`text_state.approved_prompt`). If `text_state.forced_pass` is True, log a
  warning but proceed — the gate reached its cap and the best available prompt
  advances.

**Step C — Render at the current tier**

Pick the render skill based on the cascade tier:

- `ollama` tier → dispatch `/jack-tar-ollama:image` with the approved prompt.
- `flash_1k` / `flash_2k` / `flash_4k` tiers → dispatch `/jack-tar-cloud:image`
  with `--provider google --model gemini-3.1-flash-image-preview` and the
  matching `--resolution` flag.
- `pro_1k` / `pro_2k` / `pro_4k` tiers → dispatch `/jack-tar-cloud:image` with
  `--provider google --model gemini-3-pro-image-preview` at the matching
  `--resolution`.
- `recraft_*` tiers → dispatch `/jack-tar-cloud:recraft-image` with the matching
  `--tier` and `--resolution` flags.

Save the output PNG path. Cost: `TIER_COSTS[current_tier]` USD (zero for Ollama).
Accumulate into `cumulative_cost`.

**Step D — image-reviewer verdict**

Dispatch the `image-reviewer` agent (Haiku) on the rendered PNG. If verdict is
`refine`, build new accumulated feedback (visual-quality issues) and return to
Step A — the Director's Brief regenerates the prompt incorporating the visual
feedback. Do NOT re-render with the same prompt; the text gate (Step B) fires
again before any retry render.

**Step E — Director's Critic**

Dispatch the `directors-critic` agent (Sonnet) via
`critic.build_critic_input(...)`. Parse via
`critic.parse_critic_output(response)` (which schema-validates the JSON response).

**Step F — Append attempt to manifest**

```python
from src.creative_vision.manifest import append_attempt, save_manifest
attempt = {
    "attempt_index": len(manifest["attempts"]) + 1,
    "prose_version": manifest["prose_history"][-1]["version"],
    "tier": current_tier,
    "text_iterations": text_state.iterations,
    "render": {
        "output_path": render_output_path,
        "model": tier_model,
    },
    "image_reviewer_verdict": ir_verdict,
    "directors_critic_verdict": critic_verdict,
    "cumulative_cost_usd": cumulative_cost,
}
append_attempt(manifest, attempt, ladder)
save_manifest(req.deck_dir, manifest)
```

**Step G — Decide next action**

```python
from src.creative_vision.orchestrator import decide_next_action
action = decide_next_action(
    critic_verdict=critic_verdict,
    current_tier=current_tier,
    ladder=ladder,
    remaining_budget_usd=manifest["iterate_slide_hooks"]["remaining_budget_usd"],
    per_tier_iteration_count=per_tier_iteration_count,
    per_tier_cap=DEFAULT_ITERATION_CAPS[current_tier],
    allowed_ceiling=req.allowed_ceiling,
)
```

**Step H — Branch on action.kind**

- `accept` → call `finalise_manifest(...)`. Loop ends. Use this image as the final.
- `refine_at_tier` → increment `per_tier_iteration_count`; loop back to Step A at
  the SAME tier. Carry over any accumulated feedback.
- `escalate_tier` → **OPERATOR GATE REQUIRED if and only if** the current tier
  has `TIER_COSTS[current_tier] == 0` AND `TIER_COSTS[action.next_tier] > 0`
  (i.e., the escalation crosses the free→cost boundary). See Step H.1 below
  before proceeding. If the gate passes, set `current_tier = action.next_tier`;
  reset `per_tier_iteration_count = 0`; loop back to Step A at the new tier.
- `abort` → call `finalise_manifest(...)` with the best-so-far image. Log the
  reason. Pipeline continues with whatever image was last accepted (or a
  placeholder if no image was accepted).

**Step H.1 — Operator gate at free→cost transition (MANDATORY, issue #105 F10)**

This step is the load-bearing economic checkpoint of the cascade. When `action.kind == "escalate_tier"` AND the boundary being crossed is free→cost (current is Ollama, next is any cloud tier), the loop MUST:

1. Open the most recent free-tier render for the operator:
   ```bash
   open <render_output_path>
   ```
   (Use `open` on macOS, `xdg-open` on Linux, `start` on Windows. The native viewer pulls the image into the operator's eye, NOT into orchestration context — no `Read` of the PNG inside the orchestrator.)

2. State the prospective cloud spend to the operator. Format:
   > Free→cost gate. The Ollama draft is at `<path>`. Rendering at `<next_tier>` will cost `$<TIER_COSTS[next_tier]>`. Cumulative slide spend after this render will be `$<cumulative + tier_cost>` of the `$<budget>` envelope. Say "go" to render, or describe what's wrong with the draft and I'll iterate the prompt instead.

3. **Pause the loop.** Do not invoke the cloud render. Wait for an explicit affirmative signal from the operator ("go", "yes", "render", "proceed", "render at <tier>"). Negative or descriptive feedback ("no", "still wrong", "the customer is missing") means the operator wants prompt iteration at the free tier — return to Step A WITH the operator's feedback added to `accumulated_feedback`.

4. **F11 — Simplification offer.** When the cascade has accumulated ≥3 refinement iterations at the same prose version AND the prompt has grown >400 words, ALSO offer the operator a simplified prompt as an alternative at the gate. Heuristic: drop contradictory unifiers, embrace the model's natural framing, ≤200 words. Let the operator pick between the elaborated prompt and the simplified one.

5. Only after explicit operator affirmation do you proceed to set `current_tier = action.next_tier` and dispatch the cloud render in Step C.

**Why this step exists**: during the 2026-05-22 dogfood (issue #105), this gate was skipped three times across the v2/v3/diptych rounds, leading to $0.480 of un-gated Pro 4K spend that was both methodologically wrong (gate-skipping) AND tier-inappropriate (Pro 1K would have sufficed — F9). The gate is the only checkpoint where the operator can apply their own visual judgement before money is spent. The Critic's `escalate_tier` verdict is advisory — it evaluates against the prose, not against operator intent. Skipping the gate turns the cascade from "human-in-the-loop with a free preview" into "agent loop that bills the operator."

**Creative_vision elevated gate cadence (F12, issue #113 GA-blocker)**: when the slide's strategy is `creative_vision`, the gate fires at EVERY iteration regardless of cost transition — not just at free→cost. The operator MUST see every render of a creative_vision image, including iterations at the same cost tier (e.g., Flash 1K → Flash 1K, Pro 1K → Pro 1K), because the image IS the slide's deliverable and only the operator can judge whether each render matches the creative intent. The image-reviewer + Director's Critic verdicts are advisory; only operator acceptance closes a creative_vision slide. This elevated cadence does NOT apply to standard composed / backdrop / full_render strategies — for those, the standard free→cost gate is sufficient.

The deck-conductor will further refine this in issue #113 by introducing a pre-deck creative_vision sprint phase, per-slide cost estimates surfaced at strategy approval, and deck-level creative anchors for cross-slide character/style consistency. Until that ships, creative_vision is not GA — but the per-iteration gate is in force now as the minimum interim methodology guard.

**Bypass conditions — narrow:**
- The cascade is wholly within free tiers (no cost transition — gate does not apply).
- The operator has explicitly pre-authorised cost up to a stated cap for the session AND `cumulative_cost + tier_cost <= cap`.

Cost-to-cost transitions (e.g., Flash 1K → Pro 1K) do not require this gate — the operator already committed to spending at the first free→cost transition. They MAY still be surfaced as informational ("rendering at Pro 1K will cost an additional $0.067"), but no pause is required.

#### Post-loop integration

When the loop terminates, fold the final image into the standard ImageManifest
entry for this slide so deck-assembler (Step 8 of the conductor pipeline) treats
it as a normal image bound for full-bleed assembly:

```python
image_manifest["images"].append({
    "image_id": f"slide-{slide_number}-creative-vision",
    "slide_number": slide_number,
    "file_path": manifest["final"]["image_path"],
    "placement_zone": "full_bleed",  # always full_bleed for creative_vision
    "status": (
        "generated"
        if manifest["final"]["final_verdict"]["verdict"] == "pass"
        else "accepted_with_issues"
    ),
    "source_prompt": manifest["final"]["approved_prompt"],
    "model_used": manifest["final"]["tier"],
    "creative_vision_manifest_path": str(
        Path(req.deck_dir) / "creative-vision" / str(slide_number) / "manifest.json"
    ),
})
```

Skip Step 5 (cache lookup) and Step 6 (prompt translation) for `creative_vision`
slides — the Director's Brief owns prompt authorship and the manifest owns
iteration history.

#### Discipline-hook rule (in force — do not bypass)

Never `Read` a generated PNG in this orchestration session. Always dispatch the
`jack-tar-deckhand:image-reviewer` subagent or the `general-purpose` subagent to
evaluate the image — they read the PNG into THEIR context and return text. The
`ALLOW_PNG_READ=1` bypass is for cases where the image IS the user-facing answer;
the cascade loop never satisfies that condition.

> Do not `Read` PNG / JPG / GIF / WEBP / BMP / TIFF files directly.
> If you need to verify an image, dispatch the
> `jack-tar-deckhand:image-reviewer` subagent (Haiku, JSON verdict) or
> the `general-purpose` subagent (Sonnet, higher accuracy). Both
> subagents pull the image into THEIR context and return text.

#### Reference

- Spec: `docs/superpowers/specs/2026-05-21-creative-vision-renderer-design.md`
- Manifest module: `plugins/jack-tar-deckhand/src/creative_vision/manifest.py`
- Cascade module: `plugins/jack-tar-deckhand/src/creative_vision/cascade.py`
- Orchestrator module: `plugins/jack-tar-deckhand/src/creative_vision/orchestrator.py`
- Director's Brief agent: `plugins/jack-tar-deckhand/agents/directors-brief.md`
- Prompt Reviewer agent: `plugins/jack-tar-deckhand/agents/prompt-reviewer.md`
- Director's Critic agent: `plugins/jack-tar-deckhand/agents/directors-critic.md`

## Step 5: Check Cache for Each Image

**Production mode:** If `production-upgrade-plan.json` exists in the deck directory, skip this step and use Step 9A instead. The upgrade plan takes precedence over the routing matrix for production renders.

For each routing decision where `skill` is not `skip` and not `placeholder`:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
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
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
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

### For jack-tar-ollama:image (hero_image in draft mode):
```
/jack-tar-ollama:image "TRANSLATED_PROMPT" --output ./tmp/deck/images/slide-NN-hero.png --width 1024 --height 576 --model x/z-image-turbo
```

### For jack-tar-ollama:pattern (pattern_background in draft mode):
```
/jack-tar-ollama:pattern "TRANSLATED_PROMPT" --output ./tmp/deck/images/slide-NN-pattern.png --width 1024 --height 1024
```

### For jack-tar-ollama:diagram (diagram in any mode):
```
/jack-tar-ollama:diagram "TRANSLATED_PROMPT" --type TYPE --output ./tmp/deck/images/slide-NN-diagram.png --width 1024 --height 768
```

### For jack-tar-cloud:image (hero/pattern in production mode):
```bash
/jack-tar-cloud:image "TRANSLATED_PROMPT" --output ./tmp/deck/images/slide-NN-TYPE.png --provider PROVIDER --model MODEL
```

When provider is `google`, the `--model` parameter selects the tier:
- Draft/budget: `--model imagen-4.0-fast-generate-001` ($0.02)
- Standard production: `--model gemini-3.1-flash-image-preview` ($0.067)
- Premium (text-heavy, complex): `--model gemini-3-pro-image-preview` ($0.134)

The routing matrix and production-upgrade-plan already specify the correct model. Use the model from the plan entry directly — do NOT hardcode model names in the bridge.

### For jack-tar-cloud:icon (icon_set in any mode):
```
/jack-tar-cloud:icon "TRANSLATED_PROMPT" --output ./tmp/deck/images/slide-NN-icon --provider PROVIDER --colors PALETTE_HEX
```

### For render_chart (chart type):
```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
from src.render_chart import render_chart
result = render_chart(chart_type='$CHART_TYPE', data=$DATA, output_path='./tmp/deck/images/slide-NN-chart.png', style_guide=$STYLE_GUIDE)
import json; print(json.dumps(result))
"
```

### For placeholder:
```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
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
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
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
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
from src.image_router import load_upgrade_plan, execute_upgrade_plan_entry
import json

plan = load_upgrade_plan('./tmp/deck')
for entry in plan['entries']:
    params = execute_upgrade_plan_entry(entry)
    print(f'Slide {entry[\"slide_number\"]}: {params[\"skill\"]} via {params[\"provider\"]} ({params[\"model\"]})')
"
```

For each entry:

**Resolution-aware cost projection.** Before Phase 1, compute the projected spend for each entry using the slide's declared resolution from the strategy map (`slide.resolution`, default `"1K"`):

| Tier | Flash draft (up to 3) | Pro escalation | Total (best case) | Total (worst case) |
|------|------------------------|----------------|-------------------|--------------------|
| 1K | $0.067 × 1-3 | $0.134 | $0.201 | $0.335 |
| 2K | $0.101 × 1-3 | $0.134 | $0.235 | $0.437 |
| 4K | $0.151 × 1-3 (Flash 4K pre-test) | $0.240 | $0.391 | $0.693 |

Surface the per-slide projection to the speaker before Step 9A executes. A deck with three 4K hero slides represents up to ~$2.08 of generation spend. Compare against `budget_tracker.remaining_usd` and surface a warning if projected spend exceeds remaining budget.

### raster_upscale entries

For entries where `image_id` contains `elem-`, skip the refinement loop — use `draft_prompt` directly with a single Pro call (element images are already validated during drafting).

For all other `raster_upscale` entries, execute the cross-tier refinement loop:

**Phase 1 — Flash draft and refinement (up to 3 iterations)**

1. Generate a Flash draft using `gemini-3.1-flash-image-preview` with the plan's `draft_prompt`:
   ```
   /jack-tar-cloud:image "DRAFT_PROMPT" --provider google --model gemini-3.1-flash-image-preview --width WIDTH --height HEIGHT --output ./tmp/deck/images/slide-NN-hero-flash-v1.png
   ```

2. Dispatch the `image-reviewer` agent on the Flash output. If verdict is `pass`, skip Phase 2 entirely — Flash quality is sufficient and no Pro spend is needed. Store the Flash image as the final output.

3. If verdict is `refine`, dispatch `prompt-engineer` in refinement mode:
   ```json
   {
     "mode": "refine",
     "original_prompt": "<draft_prompt>",
     "iteration": 1,
     "reviewer_feedback": {
       "strengths": ["<from reviewer strengths[]>"],
       "issues": ["<from reviewer issues[]>"],
       "composition_notes": {"<from reviewer composition_notes{}>"}
     },
     "brand_constraints": {"palette_hex": ["<from brand-profile.json>"]},
     "funnel_stage": "cloud_low"
   }
   ```

4. Generate Flash v2 with the refined prompt → re-review. If pass, use Flash as final; skip Pro.

5. If still refine after v2, do a third Flash iteration (total: 3 Flash calls max). Flash iterations are cheap (~$0.067 each) — iterate freely.

6. If all 3 Flash iterations return `refine`, escalate to Speaker:
   - Present all 3 Flash attempts with their reviewer feedback
   - Ask Speaker to confirm whether to proceed to Pro or accept the best Flash version
   - Do not auto-escalate to Pro after 3 Flash failures

**Phase 2 — Pro escalation (single shot, resolution-aware)**

7. Read `slide.resolution` from the strategy map (defaults to `"1K"` if absent). If the slide opted into `"2K"` or `"4K"`, the Pro escalation uses that tier — not always `"1K"`.

8. **Optional Flash 4K pre-test** (only when `slide.resolution == "4K"`) — before paying for Pro 4K ($0.240), do a Flash 4K validation render at $0.151:
   ```
   /jack-tar-cloud:google-image "REFINED_PROMPT" --model gemini-3.1-flash-image-preview --resolution 4K --output ./tmp/deck/images/slide-NN-hero-flash4k.png
   ```
   Dispatch `image-reviewer`. If pass: stop, use Flash 4K as final. If refine: proceed to Pro 4K. (This pattern was validated by the resolution smoke test in #59 — Flash 4K caught prompt issues that 1K Flash missed because text rendering scales differently at 4K.)

9. If Flash passes (on any iteration in Phase 1) and the slide opted into `"2K"` or `"4K"`, take the prompt that produced the passing Flash result and generate once with Pro at the requested tier:
   ```
   /jack-tar-cloud:google-image "REFINED_PROMPT" --model gemini-3-pro-image-preview --resolution {slide.resolution} --output ./tmp/deck/images/slide-NN-hero.png
   ```
   For 1K slides (the default), keep the existing single-shot Pro 1K behaviour with `--resolution 1K`.

10. Dispatch `image-reviewer` on the Pro output. Pro gets ONE shot — no iterations.
    - If pass: use Pro as final output.
    - If refine: flag for Speaker with `status: "flag_for_speaker"` in the manifest. Include both the Pro and best Flash versions so the Speaker can choose. Do not retry Pro.

**Manifest recording**

Always store the `source_prompt` used for the final accepted image — this may be the original `draft_prompt` or a refined version. Record the iteration count and which tier produced the final image (`flash_v1`, `flash_v2`, `flash_v3`, `pro`) in `review_summary`.

### vector_conversion entries

Invoke `jack-tar-cloud:icon` with Recraft:

```bash
/jack-tar-cloud:icon "DRAFT_PROMPT" --provider recraft --output ./tmp/deck/images/slide-NN-diagram.svg
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
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
from src.process_image import resize, crop_to_aspect, compute_content_hash
resize('$PATH', $WIDTH, $HEIGHT)
crop_to_aspect('$PATH', '16:9')
content_hash = compute_content_hash('$PATH')
print(f'hash:{content_hash}')
"
```

## Step 11: Cache Generated Images

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
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
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
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
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
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
