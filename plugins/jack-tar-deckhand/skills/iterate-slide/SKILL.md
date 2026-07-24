---
name: iterate-slide
description: Single-slide critique-driven refinement for academic_figure slides. Three modes — auto (Critic-driven, for flow diagrams), enumerate (operator-checklist, for completeness artefacts), draft (hybrid). Wraps paperbanana's --continue-run via subprocess with manifest update + failsafe rollback.
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Skill
  - Edit
  - Write
---

# /jack-tar-deckhand:iterate-slide

Refine an existing `academic_figure` slide via paperbanana's `--continue-run` pattern. Cheap (~$0.07–$0.15 per refinement) compared to a full re-render (~$0.14 baseline + the methodology re-parse). Validated end-to-end in the 2026-05-18 multi-tier dogfood.

This skill is only useful when (a) the slide's manifest entry records a `paperbanana_run_id` (i.e. it was originally rendered via paperbanana, not via the cloud-fallback path), and (b) paperbanana is installed locally — check with `/jack-tar-deckhand:verify` first.

## Background

The skill implements three refinement modes derived from the dogfood findings. Each suits a different figure type — pick by what the figure communicates, not by what you're refining.

- **`--mode auto`** — Critic-driven convergence with no operator-supplied enumeration. Best for **flow / explanatory diagrams** (body-of-talk slides where what matters is "how do components relate" not "are all components listed"). Paperbanana's Critic optimises for visual coherence + flow semantics, so `--auto` reaches richer arrow labels + cleaner hierarchy than operator-iteration on these subjects. Cheapest mode at ~$0.07/iter.

- **`--mode enumerate`** — operator supplies structured input (`--must-mention`, `--must-be-visually-prominent`, `--keep-from-prior`); the skill assembles a strong-imperative feedback with explicit enumeration + permission-to-shrink + KEEP header. Best for **completeness / specification artefacts** (system overview, what-is-in-scope, team roster, API surface — figures where "every X is listed" is the value). The Critic can't infer "list all N by name" from caption text; explicit enumeration is the only convergence path here.

- **`--mode draft`** — hybrid: try `--auto` first (cheap exploration), fall through to `--mode enumerate` if Critic isn't satisfied at the safety cap. Use when you're not sure which axis the figure sits on.

## Args

```
/jack-tar-deckhand:iterate-slide \
  --slide N \
  --manifest <path-to-image-manifest.json> \
  [--mode auto|enumerate|draft] \
  [--feedback "<one-paragraph critique>"] \
  [--must-mention ITEM ...] \
  [--must-be-visually-prominent PROP ...] \
  [--keep-from-prior ITEM ...] \
  [--iterations N] \
  [--review/--no-review] \
  [--budget USD]
```

| Arg | Required | Default | Notes |
|---|---|---|---|
| `--slide N` | yes | — | Slide number to refine. The skill looks this up in the manifest. |
| `--manifest <path>` | yes | — | Path to the deck's `image-manifest.json`. |
| `--mode` | no | `enumerate` | One of `auto`, `enumerate`, `draft`. |
| `--feedback "..."` | mode-dependent | empty | `auto`: free-text passed through. `enumerate`: optional preamble before the structured sections. `draft`: passed through to auto phase + treated as preamble in fallthrough. |
| `--must-mention ITEM` | enumerate / draft | empty | Repeatable. Items that MUST appear in the refined figure. |
| `--must-be-visually-prominent PROP` | enumerate / draft | empty | Repeatable. Visual properties that must hold (e.g. "outer boundary solid 2px dark grey"). |
| `--keep-from-prior ITEM` | enumerate / draft | empty | Repeatable. Properties from the previous iteration that must NOT regress. |
| `--iterations N` | no | `4` (auto) / `2` (enumerate/draft) | Override the mode default. |
| `--review` / `--no-review` | no | `--review` for enumerate/draft, `--no-review` for auto | Whether to dispatch `image-reviewer` after paperbanana returns. Auto's Critic already evaluates, so default-off there. |
| `--budget USD` | no | `0.25` | Paperbanana `--budget` cap. Belt-and-braces; jack-tar's own accounting is authoritative. |

## Step 1: Locate the manifest entry

Read the manifest and find the entry for the specified slide. Confirm the entry was produced by paperbanana (has `paperbanana_run_id`) — otherwise this skill doesn't apply.

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.iterate_slide_dispatch import find_manifest_entry

with open('$MANIFEST_PATH') as f:
    manifest = json.load(f)

entry = find_manifest_entry(manifest, $SLIDE_NUMBER)
if entry is None:
    print('ERROR: No manifest entry for slide $SLIDE_NUMBER')
    raise SystemExit(1)
if 'paperbanana_run_id' not in entry:
    print('ERROR: slide $SLIDE_NUMBER was not rendered via paperbanana (no paperbanana_run_id)')
    print('Use /jack-tar-deckhand:imagegen-bridge to refine non-paperbanana slides.')
    raise SystemExit(1)

print(json.dumps(entry))
"
```

Capture the output as `$PRIOR_ENTRY_JSON`. Extract `paperbanana_run_id` and the original output path (`file_path`).

## Step 2: F7 workaround — ensure run dir is local

Paperbanana's `--continue-run` looks for the run dir under `<cwd>/outputs/`, not at the original write path (upstream issue [llmsresearch/paperbanana#217](https://github.com/llmsresearch/paperbanana/issues/217)). The dispatch helper's `ensure_run_dir_local` copies it locally if needed.

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import os
from pathlib import Path
from src.iterate_slide_dispatch import ensure_run_dir_local

run_id = '$RUN_ID'
prior_path = '$PRIOR_FILE_PATH'  # from manifest

# Source root = the dir containing run_<id>/. Derived from the prior
# file path: <root>/run_<id>/final_output.png → <root>
prior_dir = Path(prior_path).parent
source_root = str(prior_dir.parent)

local_dir = ensure_run_dir_local(run_id, source_root)
print(local_dir)
"
```

Capture the local run dir path. If this step fails with FileNotFoundError, the original run dir has been deleted — refinement isn't possible, fall back to a fresh paperbanana invocation.

## Step 3: Build the refinement plan

Convert the operator args into an `IterateSlidePlan`:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.iterate_slide_dispatch import (
    IterateSlideRefinementRequest, plan_refinement, cli_args_to_argv,
)

# Args from the skill invocation
request = IterateSlideRefinementRequest(
    feedback='''$FEEDBACK''',
    must_mention=$MUST_MENTION_JSON_LIST,
    must_be_visually_prominent=$MUST_BE_VISUALLY_PROMINENT_JSON_LIST,
    keep_from_prior=$KEEP_FROM_PRIOR_JSON_LIST,
)

plan = plan_refinement(
    mode='$MODE',
    run_id='$RUN_ID',
    request=request,
    iterations=$ITERATIONS,
    budget_usd=$BUDGET,
)

print(json.dumps({
    'mode': plan.mode.value,
    'run_id': plan.run_id,
    'iterations': plan.iterations,
    'feedback_chars': len(plan.feedback),
    'cli_argv': cli_args_to_argv(plan.cli_args),
    'budget_usd': plan.budget_usd,
}))
"
```

Capture the plan JSON as `$PLAN_JSON`. Inspect the `cli_argv` array — that's exactly what we'll pass to paperbanana.

## Step 4: Invoke paperbanana via subprocess

Use the plan's `cli_argv` as the argv array. Write the feedback to a tmp file isn't needed (continue-run carries the feedback inline via `--feedback`).

```bash
# Read argv from plan JSON via jq
ARGV=$(echo "$PLAN_JSON" | jq -r '.cli_argv | @sh')

# Invoke. eval is necessary to expand the @sh-quoted argv.
PB_OUTPUT=$(eval paperbanana generate $ARGV 2>&1)
PB_EXIT=$?

if [ "$PB_EXIT" != "0" ]; then
  echo "ERROR: paperbanana exited $PB_EXIT"
  echo "$PB_OUTPUT" | tail -30
  exit 1
fi
```

## Step 5: Parse paperbanana's stdout for the new output path

```bash
PB_NEW_FILE=$(PYTHONPATH="$PLUGIN_ROOT" python3 -c "
from src.iterate_slide_dispatch import parse_output_path_from_stdout
print(parse_output_path_from_stdout('''$PB_OUTPUT'''))
")

if [ -z "$PB_NEW_FILE" ]; then
  echo "ERROR: couldn't extract output path from paperbanana stdout"
  echo "$PB_OUTPUT" | tail -10
  exit 1
fi

# Make absolute (paperbanana sometimes prints relative paths)
PB_NEW_FILE=$(cd $(dirname "$PB_NEW_FILE") && pwd)/$(basename "$PB_NEW_FILE")
```

## Step 6: Compute sha256 of new file

```bash
NEW_SHA=$(shasum -a 256 "$PB_NEW_FILE" | cut -d' ' -f1)
```

## Step 7: Failsafe rollback — dispatch image-reviewer

If `--review` is on (default for enumerate / draft modes), dispatch `image-reviewer` with the new image AND the operator's feedback. The reviewer's job is to detect whether the refinement actually addressed the critique.

```
Dispatch jack-tar-deckhand:image-reviewer with:
  - image: $PB_NEW_FILE
  - intent: "$FEEDBACK"
  - prior_image (optional): $PRIOR_FILE_PATH
```

Capture the verdict. If `pass`: proceed to Step 8 (manifest update). If `refine` or `fail`: log a warning, do NOT update the manifest (the prior file stays bound), and surface the verdict to the operator with the explicit instruction to either re-iterate with stronger feedback or accept the prior version.

```bash
if [ "$REVIEWER_VERDICT" = "fail" ] || [ "$REVIEWER_VERDICT" = "refine" ]; then
  echo "Refinement verdict: $REVIEWER_VERDICT — preserving prior file binding."
  echo "Prior file: $PRIOR_FILE_PATH"
  echo "Refined file (NOT bound): $PB_NEW_FILE"
  echo "Reviewer notes: $REVIEWER_NOTES"
  echo "Consider re-running with stronger feedback or --mode enumerate."
  # Log to cost ledger anyway — we paid for the refinement even if rolled back
  exit 0  # not an error; failsafe-as-designed
fi
```

`auto` mode default-skips this step (paperbanana's Critic already evaluates). Operator can `--review` it explicitly.

## Step 7.5: Annotation refresh guard (annotate-figure v2 native slides, F4)

**Runs whenever Step 7 accepted a replacement image, regardless of mode.** Before the manifest is updated (Step 8), check whether this slide is contracted `annotation_mode: native` in `strategy-map.json`. If so, the anchor pass + `build_annotation_payload` rewrite is **mandatory** before reassembly — the prior payload's `base_image_hash` no longer matches the new image, and both the assembler's hash-gate and QA's AN-01 will refuse a stale overlay (design doc §6.3, F4).

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.slide_prompt_composer import load_strategy_map
from src.iterate_slide_dispatch import (
    find_strategy_map_entry, annotation_refresh_required, annotation_refresh_notice,
)

strategy_map = load_strategy_map('$DECK_DIR')
slide_entry = find_strategy_map_entry(strategy_map, $SLIDE_NUMBER)

if annotation_refresh_required(slide_entry):
    print(json.dumps(annotation_refresh_notice($SLIDE_NUMBER), indent=2))
else:
    print(json.dumps({'annotation_refresh_required': False}))
"
```

If `annotation_refresh_required` is `false` — the slide has no strategy-map entry, or its `annotation_mode` is `none`/`raster`/absent — skip straight to Step 8; there is nothing to refresh (raster annotations are baked into the pixels at generation time, not tracked by a separate payload).

If `annotation_refresh_required` is `true`, print the `instructions` field to the operator and, before proceeding to Step 8:

1. Re-run the anchor pass against `$PB_NEW_FILE` (the new base image) — dispatch `image-reviewer` / `general-purpose` with the annotate-figure vision-anchor contract, exactly as the imagegen-bridge native sub-step does (imagegen-bridge SKILL.md §4.8, step 2).
2. On a valid anchor result, rebuild the payload:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
from src.annotation_payload import build_annotation_payload, write_annotation_payload

payload = build_annotation_payload(
    slide_number=$SLIDE_NUMBER,
    source='generated',
    base_image_path='$PB_NEW_FILE',
    image_dimensions=None,
    placement_zone='$PLACEMENT_ZONE',   # from the manifest entry
    anchors=$ANCHORS_JSON,              # validated {label: [x, y]} from the anchor pass
)
path = write_annotation_payload('$DECK_DIR', $SLIDE_NUMBER, payload)
print(path)
"
```

3. **On anchor-pass failure — including a failed re-dispatch — apply the F5 three-way operator choice** (same vocabulary as the imagegen-bridge sub-step, `annotation_refresh_notice`'s `downgrade_choices`): **(a) retry** the anchor pass fresh (optionally at Sonnet tier); **(b) raster_with_manual_anchors** — the operator supplies `{label: [x, y]}` by hand and the v1 `annotate()` flow bakes them into a fresh raster image, replacing this native slide's flow entirely; **(c) ship_unlabeled** — the new base image goes in as a plain figure and no payload is written for it. Whichever choice is taken, record `status: accepted_with_issues` (minimum) on the Step 8 manifest update and note the anchor-pass failure in the operator-facing summary (Step 10).

**Never proceed to Step 8/reassembly with a stale or absent payload for a native-annotated slide bound to a just-replaced image.** The hash-gate makes a skipped refresh fail *safe* (the overlay is refused); this step is what makes it fail *correct* (anchors match the shipped image).

**Composed native slides (v2.1, §2.6).** The guard's predicate is
`annotation_mode == "native"` alone — it does not read the slide's base
`strategy` at all, so it already fires identically for a `composed`
annotated slide as it does for a full-slide one. No code change was needed
for v2.1; this is a reminder for the operator reading this SKILL, not a new
behaviour.

**Headline opt-in is chrome-only (v2.1, §3.5).** Toggling
`annotation.show_headline` or editing the slide's outline headline text
changes chrome, not the base image — the base image's content hash is
unaffected, so the existing annotations payload stays valid. This does
**not** trigger the F4 guard above (which fires only on a base-image
replacement, Step 7's `$PB_NEW_FILE`); a headline-only edit just needs
reassembly (Step 9), no anchor-pass re-run, no payload rewrite.

**Blank-zone variant (issue #142 final scope item, BZ-4).** The guard's
predicate is unaffected by `blank_zone` — it fires on every
`annotation_mode: native` image replacement regardless of placement zone.
But for a slide whose `annotation` object carries `blank_zone`, the plain
rebuild sketched in step 2 above (no `blank_zone` / `blank_zone_clear`
kwargs) is a LEGAL v2-shaped payload that silently reverts this slide's
labels from the reserved zone back to the margin bands — a new base image
means new anchors AND a fresh zone verdict, so re-run the FULL blank-zone
sub-steps of imagegen-bridge SKILL.md §4.8 (the amended anchor-pass
contract including the zone question) and pass `blank_zone` /
`blank_zone_clear` through to `build_annotation_payload`. See
`ANNOTATION_REFRESH_INSTRUCTIONS` in `iterate_slide_dispatch.py`, which
now surfaces this verbatim.

## Step 8: Update manifest entry

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.iterate_slide_dispatch import update_manifest_entry

with open('$MANIFEST_PATH') as f:
    manifest = json.load(f)

prior_entry = json.loads('''$PRIOR_ENTRY_JSON''')
plan = json.loads('''$PLAN_JSON''')
refinement_args = {
    'mode': plan['mode'],
    'iterations': plan['iterations'],
    'feedback_chars': plan['feedback_chars'],
    'budget_usd': plan['budget_usd'],
}

new_entry = update_manifest_entry(
    prior_entry,
    new_file_path='$PB_NEW_FILE',
    new_content_hash='$NEW_SHA',
    refinement_args=refinement_args,
)

# Replace the entry in the manifest
entries = manifest.get('entries') or manifest.get('images')
for i, entry in enumerate(entries):
    if entry.get('slide_number') == $SLIDE_NUMBER:
        entries[i] = new_entry
        break

with open('$MANIFEST_PATH', 'w') as f:
    json.dump(manifest, f, indent=2)

print(json.dumps(new_entry, indent=2))
"
```

## Step 9: Log to the bridge cost ledger

Append a single-line JSON record to `bridge-cost-ledger.jsonl` (in the deck dir, alongside the manifest). One line per refinement; downstream tooling reads this for cumulative-cost rollups.

```bash
COST_USD=$(echo "$PB_OUTPUT" | grep -oE 'Cost:\s+\$[0-9.]+' | head -1 | grep -oE '[0-9.]+')

# Paperbanana's tracked cost is typically ~5% of true (image pricing
# missing from its table — upstream #213). Compute true cost from
# jack-tar's pricing data instead.
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json, datetime
plan = json.loads('''$PLAN_JSON''')
iters = plan['iterations']
# Flash 1K is $0.067 per image; VLM calls ~$0.001 × 2 critics × iters
image_cost = 0.067 * iters
vlm_cost = 0.002 * iters
true_cost = image_cost + vlm_cost
record = {
    'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
    'skill': 'iterate-slide',
    'slide_number': $SLIDE_NUMBER,
    'mode': plan['mode'],
    'iterations': iters,
    'paperbanana_tracked_cost_usd': float('$COST_USD' or '0'),
    'estimated_true_cost_usd': round(true_cost, 4),
    'run_id': '$RUN_ID',
    'verdict': '$REVIEWER_VERDICT',
}
with open('$LEDGER_PATH', 'a') as f:
    f.write(json.dumps(record) + '\n')
print('Logged: {} mode, {} iters, ~\${:.2f} true cost'.format(plan['mode'], iters, true_cost))
"
```

## Step 10: Report to operator

Print a final summary:

```
Iterate-slide complete for slide $SLIDE_NUMBER:
  Mode:              $MODE
  Iterations:        $ITERATIONS
  New file:          $PB_NEW_FILE
  New sha256:        $NEW_SHA
  Reviewer verdict:  $REVIEWER_VERDICT (skipped if --no-review)
  Estimated cost:    $TRUE_COST_USD
  Manifest updated:  $MANIFEST_PATH

Next:
  - Re-assemble the deck if the slide is mid-pipeline:
    /jack-tar-deckhand:deck-assembler --manifest $MANIFEST_PATH
  - Or just open the refined image to confirm:
    open $PB_NEW_FILE
```

## Notes for the orchestrator

- **`paperbanana_run_id` must be present** in the manifest entry for this skill to apply. The dispatch refactor (issue #94) ensures this is written for every academic_figure slide.
- **Auto-mode regret:** `--auto` can produce a figure that's qualitatively different from what the operator wanted (the dogfood F10 finding). When the operator's feedback names specific items to add, `--mode enumerate` is the right choice; `--mode auto` is for "make it look better" feedback.
- **Cost discipline:** check the cost ledger after a refinement. If cumulative-spend is approaching the deck's budget envelope, escalate to the operator before launching another refinement.
- **Annotate-figure v2 native slides (F4, §6.3):** Step 7.5 is not optional for `annotation_mode: native` slides — a refined image without a refreshed annotations payload will be refused by the assembler's hash-gate and flagged `error` by deck-qa's AN-01. Always run the guard check before Step 8.

## Creative vision feedback (#105)

The three modes above (`auto` / `enumerate` / `draft`) apply to `academic_figure` slides rendered via paperbanana. For `creative_vision` slides — slides whose image was produced by the CreativeVision orchestrator — a different feedback model applies: the **three-channel branch**.

### Detect creative_vision

Before entering the standard paperbanana flow, call `is_creative_vision_slide`:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import sys
from src.iterate_slide_dispatch import is_creative_vision_slide
result = is_creative_vision_slide('$DECK_DIR', $SLIDE_NUMBER)
print('yes' if result else 'no')
"
```

If the result is `yes`, the slide has a manifest at `<deck_dir>/creative-vision/<slide_number>/manifest.json` and the three-channel branch applies. Do NOT invoke the paperbanana `--continue-run` path for creative_vision slides.

### Determine available channels

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.iterate_slide_dispatch import available_channels_for_creative_vision
channels = available_channels_for_creative_vision('$DECK_DIR', $SLIDE_NUMBER)
print(json.dumps(channels))
"
```

`available_channels_for_creative_vision` reads `iterate_slide_hooks` from the manifest. The three channels are:

| Channel | When available |
|---|---|
| `revise_prose` | Always (`can_revise_prose` — always True in v1, reserved for future deprecation) |
| `refine_prompt` | When `can_refine_prompt` is True |
| `escalate_tier` | When `can_escalate_tier` is True — flipped to False when `remaining_budget_usd` ≤ 0 or the cascade ceiling has been reached |

### Channel semantics

#### Channel 1 — revise prose

Use when the operator believes the **root vision is wrong or under-specified** — the image rendered faithfully to the prose, but the prose itself didn't capture the intent.

1. Read `manifest["prose_history"][-1]["prose"]` and display it to the operator.
2. If the most recent attempt has a Director's Critic verdict, show the `gap_location` field (especially when it equals `"prose"`).
3. Prompt: _"The current vision is: [prose]. The rendered image showed [recent critic diagnosis]. Update the prose to be more specific or correct any misunderstanding:"_
4. Collect `new_prose` and `reason` from the operator.
5. Call `revise_prose_action`:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
import json
from src.iterate_slide_dispatch import revise_prose_action
m = revise_prose_action(
    '$DECK_DIR',
    slide_number=$SLIDE_NUMBER,
    new_prose='''$NEW_PROSE''',
    reason='''$REASON''',
)
print(json.dumps({'prose_history_len': len(m['prose_history'])}))
"
```

6. After the manifest is updated, re-invoke `creative_vision_dispatch.initialise_dispatch(...)` and run the full orchestration loop with the new prose. The manifest preserves the full prose history for audit.

#### Channel 2 — refine prompt

Use when the **prose is correct** but the Director's Brief missed a specific element or the Visualizer produced an off-target composition. Same tier, same prose; adds one more text-side iteration.

1. Read the most recent attempt's Director's Critic verdict. Extract `issues` and `recommended_action`.
2. Prompt: _"The renderer's interpretation missed [specific gap from issues]. Add a note for the Director's Brief to address:"_
3. Collect the operator's note.
4. Pass the note as an entry in the Brief's `accumulated_feedback` list on the next dispatch. The Brief's feedback list grows by one entry each time this channel is used; the accumulation is the mechanism that drives convergence without resetting tier.

The implementation is entirely in the `creative_vision_dispatch` layer — this channel does NOT call any helper in `iterate_slide_dispatch.py`. The SKILL.md orchestrator adds the note to the dispatch call and re-runs the loop.

#### Channel 3 — escalate tier

Use when the current tier has **plateaued** (multiple iterations, no score gain) and the operator wants to pay for a higher-fidelity model tier.

1. Read `iterate_slide_hooks`:
   - `current_tier` — where we are now
   - `next_tier_available` — next step up the cascade (None if at ceiling)
   - `remaining_budget_usd` — what's left

2. Look up the cost from `cascade.TIER_COSTS`:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 -c "
from src.creative_vision.cascade import TIER_COSTS
import json, sys
tier = '$NEXT_TIER'
cost = TIER_COSTS.get(tier, 0)
print(json.dumps({'tier': tier, 'cost_usd': cost}))
"
```

3. Confirm with the operator: _"Current tier `[current_tier]` plateaued. Escalate to `[next_tier]` (cost ~\$[cost])? Remaining budget: \$[remaining]."_

4. On operator confirmation: bump `iterate_slide_hooks.current_tier` to `next_tier`, reset the per-tier iteration counter, and resume the orchestration loop at the new tier. The manifest's `can_escalate_tier` will be flipped to False by the next `append_attempt` call when budget hits zero.

### Mode mapping

The existing iterate-slide modes map onto the three channels:

| Mode | Behaviour for creative_vision slides |
|---|---|
| `enumerate` | Read manifest, call `available_channels_for_creative_vision`, annotate each channel with the Director's Critic's `recommended_action`. Present to operator; operator selects. |
| `auto` | Read `directors_critic_verdict.gap_location`. If `gap_location: "prose"` AND Critic's `recommended_action` explicitly suggests prose revision → prompt operator to revise prose (channel 1 ALWAYS requires explicit operator confirmation — auto never autonomously rewrites prose). If `gap_location: "prompt"` → route to refine_prompt automatically. If `gap_location: "tier"` → route to escalate_tier if budget allows; otherwise present to operator. |
| `draft` | Operator writes a free-form note. Classify heuristically: if the note is a substantial rewrite of the vision → route to revise_prose; if it is a targeted correction naming a specific element → route to refine_prompt. **Confirm routing with operator before taking action.** |

### Manifest hooks read here

The SKILL.md reads these specific fields from `manifest["iterate_slide_hooks"]`:

| Field | Type | Meaning |
|---|---|---|
| `can_revise_prose` | boolean | Always True in v1; reserved for future |
| `can_refine_prompt` | boolean | Whether channel 2 is open |
| `can_escalate_tier` | boolean | Flipped False when budget ≤ 0 or ceiling reached |
| `current_tier` | string | Current cascade tier (e.g. `"flash_1k"`) |
| `next_tier_available` | string \| null | Next tier up, or null at ceiling |
| `remaining_budget_usd` | float | Budget remaining after all attempts so far |

### Cross-references

- Manifest module: `plugins/jack-tar-deckhand/src/creative_vision/manifest.py`
- Dispatch entry: `plugins/jack-tar-deckhand/src/creative_vision_dispatch.py`
- Cascade costs: `plugins/jack-tar-deckhand/src/creative_vision/cascade.py` (`TIER_COSTS`)
- Spec: `docs/superpowers/specs/2026-05-21-creative-vision-renderer-design.md`

> Do not `Read` PNG / JPG / GIF / WEBP / BMP / TIFF files directly. If you need to verify an image, dispatch the `jack-tar-deckhand:image-reviewer` subagent (Haiku, JSON verdict) or the `general-purpose` subagent (Sonnet, higher accuracy). Both subagents pull the image into THEIR context and return text.
