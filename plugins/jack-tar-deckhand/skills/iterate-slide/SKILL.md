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

> Do not `Read` PNG / JPG / GIF / WEBP / BMP / TIFF files directly. If you need to verify an image, dispatch the `jack-tar-deckhand:image-reviewer` subagent (Haiku, JSON verdict) or the `general-purpose` subagent (Sonnet, higher accuracy). Both subagents pull the image into THEIR context and return text.
