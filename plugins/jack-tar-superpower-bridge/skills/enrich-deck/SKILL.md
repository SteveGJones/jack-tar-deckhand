---
name: enrich-deck
description: Phase 3 of the superpower bridge — analyse a /pptx-produced .pptx, present enrichment options, apply selected enrichments transactionally to a copy, and deliver presentation-enriched.pptx with a structured enrichment-report.md. Never modifies the original. Reuses image-reviewer and prompt-engineer agents and dispatches the new enrichment-cohesion-reviewer for deck-level visual review.
argument-hint: <pptx-path> [--brief <creative-brief.md>] [--budget-cap <usd>] [--confidentiality public|internal|restricted]
allowed-tools: Bash(python *), Bash(claude *), Read, Write, Skill, Agent
---

# /enrich-deck

Phase 3 of the superpower bridge. The user has run /pptx and has a .pptx + build.js. You analyse it, propose enrichments, get user approval, apply them transactionally, run a cohesion review, and deliver `presentation-enriched.pptx` plus `enrichment-report.md`.

You are NOT a creative persona — you orchestrate. The Narrative Brief Architect already shaped the brief; the per-image Image Reviewer assesses each image; the Prompt Engineer writes prompts; the Enrichment Cohesion Reviewer assesses the assembled deck. You dispatch each one at the right moment and act on their structured outputs.

## Parse arguments

- **<pptx-path>** (positional, required) — the .pptx the /pptx superpower produced
- **--brief <path>** (default: `creative-brief.md` in the same directory as the .pptx) — the brief from /bridge-brief
- **--budget-cap <usd>** (default: read from brief, else $1.00) — hard ceiling on cumulative cloud spend (covers BOTH generation AND review)
- **--confidentiality public|internal|restricted** (default: read from brief, else `public`)

## Locate the plugin

```bash
PLUGIN_ROOT=$(python3 -c "
from pathlib import Path
import sys, os
if os.environ.get('JACK_TAR_SUPERPOWER_BRIDGE_ROOT'):
    print(os.environ['JACK_TAR_SUPERPOWER_BRIDGE_ROOT']); sys.exit()
home = Path.home()
for base in [home / '.claude' / 'plugins' / 'cache']:
    # Note: Python 3.14 Path.rglob does not match multi-segment patterns reliably;
    # use a 2-segment pattern + parts filter so discovery works across versions.
    for p in base.rglob('.claude-plugin/plugin.json'):
        if 'jack-tar-superpower-bridge' in p.parts:
            print(str(p.parent.parent)); sys.exit()
dev = Path.cwd() / 'plugins' / 'jack-tar-superpower-bridge'
if dev.exists():
    print(str(dev)); sys.exit()
print('NOT_FOUND')
" 2>/dev/null)
if [ -z "$PLUGIN_ROOT" ] || [ "$PLUGIN_ROOT" = "NOT_FOUND" ]; then
  echo "ERROR: jack-tar-superpower-bridge not found"; exit 1
fi
RUN_DIR="$(dirname "$1")/bridge-run"
mkdir -p "$RUN_DIR/generated" "$RUN_DIR/carriers" "$RUN_DIR/slide-images"
```

`$RUN_DIR` is the per-run scratchpad. Image generation writes to `$RUN_DIR/generated/`; SmartArt carriers go to `$RUN_DIR/carriers/`; slide rasters used for cohesion review go to `$RUN_DIR/slide-images/`. The image-path allowlist in `src/security.py` is configured with `[$RUN_DIR/generated, $RUN_DIR/carriers]`.

## Step 1 — Read the brief if available, derive brand palette

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from pathlib import Path
from src.creative_brief import parse_brief_markdown, DEFAULT_BUDGET_CAP_USD
from src.colors_xml_builder import derive_palette_from_brief_text
brief_path = Path("$BRIEF_PATH")
if brief_path.exists():
    brief = parse_brief_markdown(brief_path.read_text())
    print(f"BUDGET={brief.budget_cap_usd}")
    print(f"CONFIDENTIALITY={brief.confidentiality}")
    print(f"VISUAL_PERSONALITY={brief.visual_personality}")
    # Derive brand palette so SmartArt graphics render in brief colours
    # (Contract 1 / Finding #10). When the brief's Section B includes a
    # palette table with role keywords (structural / surface / body text /
    # accent), the heuristic returns a BrandPalette to use in Step 7.
    palette = derive_palette_from_brief_text(brief.visual_personality or "")
    if palette is not None:
        print(f"BRAND_PALETTE_PRIMARY={palette.primary_fill_hex}")
        print(f"BRAND_PALETTE_TEXT_ON_PRIMARY={palette.text_on_primary_hex}")
        print(f"BRAND_PALETTE_TEXT_ON_SURFACE={palette.text_on_surface_hex}")
    else:
        print("BRAND_PALETTE_PRIMARY=")
        print("BRAND_PALETTE_TEXT_ON_PRIMARY=")
        print("BRAND_PALETTE_TEXT_ON_SURFACE=")
else:
    print(f"BUDGET={DEFAULT_BUDGET_CAP_USD}")
    print("CONFIDENTIALITY=public")
    print("VISUAL_PERSONALITY=")
    print("BRAND_PALETTE_PRIMARY=")
    print("BRAND_PALETTE_TEXT_ON_PRIMARY=")
    print("BRAND_PALETTE_TEXT_ON_SURFACE=")
PY
```

CLI flags override brief values when both supplied.

If the heuristic could not derive a palette (the brief omits role-keyworded hex values, or the brief is absent), `BRAND_PALETTE_PRIMARY` is empty and Step 7 will skip palette injection. SmartArt slides in that case will render in default Microsoft palette — log this as a degraded outcome and recommend the user add palette hex values to the brief's Section B if their deck contains SmartArt.

## Step 2 — Run the analyser

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from pathlib import Path
import json
from src.analyser import analyse_pptx
result = analyse_pptx(Path("$PPTX_PATH"))
print(json.dumps({
    "total_slides": result.total_slides,
    "total_markers": result.total_markers,
    "duplicate_marker_ids": result.duplicate_marker_ids,
    "overlap_warnings": [
        {"slide": w.slide_index, "marker": w.marker_id,
          "overlapping": w.overlapping_shape_names}
        for w in result.overlap_warnings
    ],
    "js_fallback_used": result.js_fallback_used,
    "notes": result.notes,
    "slides": [s.to_dict() for s in result.slides],
}, indent=2))
PY
```

Surface the analyser's output to the user as a structured summary:

```
Analysed <N> slides.
Markers detected: <M>  (JS fallback used: yes/no)

Marked enrichments:
  Slide 3: IMAGE:agent-architecture — element image (right 40%)
  Slide 5: SMARTART:flowchart — 4-step process from bullets
  Slide 8: BG:dramatic-contrast — atmospheric background

Suggested unmarked enrichments:
  Slide 10: text-heavy, no visuals — AI background candidate
  Slide 12: 5-item comparison list — SmartArt venn candidate

Already rich (no changes proposed):
  Slide 1 (title), Slide 4 (chart), Slide 14 (closing)

Overlap warnings:
  Slide 5 SMARTART:flowchart overlaps shapes: ["Body 1", "Body 2"]
   → choose: proceed | clear_overlap | drop

Duplicate marker ids: <list> — must be resolved before enrichment.
```

If duplicates exist, halt and ask the user to fix them in /pptx output before re-running.

## Step 3 — Build the enrichment menu and get user approval

For each marked + suggested enrichment, ask the user which to apply. Default offer is to apply all marked + none of the suggestions; the user can opt in or out per item.

For SMARTART markers that have overlap warnings, present the three options:
- **proceed anyway** — accept faint residual text behind the SmartArt
- **clear overlapping text** (`apply_clear_overlap`) — remove the overlapping shapes during enrichment
- **drop this enrichment** — skip the SmartArt op entirely; marker stays in the deck for re-running later

**SMARTART-FROM-LIST bullet length pre-flight (Finding #13 — repeated across Runs 4, 5, 6):** for each `SMARTART-FROM-LIST` marker, inspect the marker shape's text frame and check the longest bullet item against the layout cap of the default routing target (`process1` = 24 chars; `list1` = 30 chars). If any bullet exceeds the cap, surface a warning to the Speaker BEFORE Step 7 apply (which would otherwise raise `EnrichmentApplyError` mid-transaction):

```
⚠ Slide N — SMARTART-FROM-LIST:<slug> has 2 bullet(s) exceeding process1's 24-char cap:
  - "Edge inference for our regulated-vertical customers"  (52 chars)
  - "Customer overlap: 3 of 7 already on our platform"     (48 chars)

Options:
  (1) shorten the bullets in the source build.js and re-run /pptx, then re-run /enrich-deck
  (2) drop this enrichment from the plan; marker stays in deck for later
  (3) accept auto-truncation to 24 chars (text will be clipped — degraded outcome)

Recommended: (1). Run 4/5/6 dogfood pattern is hand-shortened bullets ≤24 chars.
```

Capture the user's selections as a list of `EnrichmentItem` records.

## Step 4 — Initialise budget + privacy gate

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from src.image_bridge import BudgetCap, PrivacyTierGate
import json
budget = BudgetCap(usd=$BUDGET_CAP_USD)
gate = PrivacyTierGate(tier="$CONFIDENTIALITY_TIER")
print(json.dumps({"remaining": budget.remaining,
                   "cloud_allowed": gate.cloud_allowed(),
                   "needs_confirmation": gate.requires_confirmation_before_cloud()}))
PY
```

If `internal` tier and the user has approved at least one enrichment that may go cloud (i.e., any IMAGE or BG enrichment), ask the user once before the first cloud call:

> Confidentiality tier is `internal`. The first cloud image generation will send the prompt and any visual brief context to <provider>. Confirm cloud escalation for this run? (yes/no)

If no, the gate stays unconfirmed and image generation will only use Ollama (cycle returns `accepted_with_issues`).

If `restricted` tier, do not even ask — cloud is disabled.

## Step 5 — Generate AI images (background + element image enrichments)

This step is SKILL.md-driven, not Python-driven, because the cycle requires Agent dispatches between iterations and Python heredocs cannot dispatch Claude subagents. The Python module `src/cycle_state.py` (Task 17) provides pure-functional state primitives the SKILL.md calls between dispatches.

For each background and element-image enrichment, run the loop:

### Step 5a — Compose the initial prompt

Dispatch the `jack-tar-deckhand:prompt-engineer` agent (existing persona, namespaced under jack-tar-deckhand) with a structured brief containing:
- `mode: "compose"`
- `marker_kind`: `IMAGE` or `BG`
- `marker_id`: full marker string
- `slide_content`: text from the analyser's SlideFacts for this slide
- `visual_direction`: visual_personality from the brief's Section B (or empty string if no brief)
- `brand_constraints`: palette + style tokens from creative-brief if available
- `funnel_stage`: `"ollama"` (Phase A starts at Ollama)
- `source: "enrichment-bridge"` (persona contract extension)

Capture the returned prompt string as the initial `prompt` for this enrichment.

### Step 5b — Initialise the cycle state

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
import json
from pathlib import Path
from src.cycle_state import CycleState, Phase
from src.image_bridge import ImageGenerationRequest
req = ImageGenerationRequest(
    slide_index=$SLIDE_INDEX,
    marker_id="$MARKER_ID",
    marker_kind="$MARKER_KIND",
    prompt="""$PROMPT""",
    output_path=Path("$RUN_DIR/generated/slide-${SLIDE_INDEX}-${MARKER_SLUG}.png"),
    width=$WIDTH, height=$HEIGHT,
    brand_palette_hex=$PALETTE_LIST,
)
state = CycleState(request=req, phase=Phase.PHASE_A_OLLAMA, attempt=1)
print(json.dumps({"slide": req.slide_index, "marker_id": req.marker_id,
                   "phase": state.phase.value, "attempt": state.attempt,
                   "output_path": str(req.output_path)}))
PY
```

### Step 5c — Loop: generate → charge review → dispatch reviewer → advance state

Repeat until `decision.kind` starts with `terminate_`:

**(i) Generate the image** based on current `state.phase`:

- `phase_a_ollama` → invoke `/jack-tar-ollama:image "$PROMPT" --output $OUTPUT --width $WIDTH --height $HEIGHT --model $OLLAMA_MODEL` (free; no budget charge)
- `phase_b_cloud_flash` → invoke `/jack-tar-cloud:image "$PROMPT" --provider google --model gemini-3.1-flash-image-preview --output $OUTPUT --width $WIDTH --height $HEIGHT` then charge `kind="generation", provider="nanobanana_flash", cost_usd=0.067`
- `phase_c_cloud_pro` → invoke `/jack-tar-cloud:image "$PROMPT" --provider google --model gemini-3-pro-image-preview --output $OUTPUT --width $WIDTH --height $HEIGHT` then charge `kind="generation", provider="nanobanana_pro", cost_usd=0.134`

Cloud-tier charges go through:
```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from pathlib import Path
from src.image_bridge import BudgetCap, BudgetExhaustedError
from src.measurement import record_cost_event
budget_state = $BUDGET_STATE_DICT  # serialised before/after each charge
budget = BudgetCap(usd=budget_state["usd"], spent=budget_state["spent"])
budget.charge(kind="generation", provider="$PROVIDER", cost_usd=$COST)
record_cost_event(cwd=Path("$RUN_DIR"), kind="generation",
                   provider="$PROVIDER", cost_usd=$COST,
                   slide_index=$SLIDE, marker_id="$MARKER_ID")
print(budget.spent)
PY
```

If `BudgetExhaustedError` raises before generation, the SKILL.md halts this enrichment with status `halted_budget` and proceeds to the next.

**(ii) View and dispatch the `jack-tar-deckhand:image-reviewer` agent**

VIEW the generated image with the Read tool (mandatory per CLAUDE.md "MANDATORY: Visual Output Review"). Then dispatch the `jack-tar-deckhand:image-reviewer` agent (existing persona, contract-extended, namespaced under jack-tar-deckhand) with:

```
Review this generated image for quality.
Image: $OUTPUT_PATH
Visual direction: <brief Section B or analyser context>
Brand palette: <hex values>
Strategy: enrichment_$MARKER_KIND_lower    # enrichment_image OR enrichment_bg
Iteration: $ATTEMPT of $MAX_FOR_PHASE
Source: enrichment-bridge
```

**For text-bearing IMAGE markers, ALWAYS append `expected_text_content`** (Run 6 Findings #19/#20 — the reviewer's text-rendering check is unreliable without an explicit comparison reference). Extract the expected strings from the marker's subject brief in the creative brief's Section C per-slide marker assignment table (e.g. for `IMAGE:edge-stack-architecture`, extract `["Client Edge Nodes", "Inference Layer", "Orchestration Bus", "Cloud Sync Endpoint", "Regulator Engagement"]`). Append:

```
**Expected text content:**
  - "Client Edge Nodes"
  - "Inference Layer"
  - "Orchestration Bus"
  - "Cloud Sync Endpoint"
  - "Regulator Engagement"
**Critical check:** Read every word in the image and compare against the expected list above.
Report rendered-vs-expected mismatches as issues; do not confabulate correctness.
```

Heuristic for whether a marker is text-bearing: look in the brief's Section C subject brief for any of these patterns — a quoted multi-word string, the word "label", the word "wordmark", a proper-noun-style company/product name, a list of named blocks/arrows. When in doubt, include `expected_text_content` — it never hurts to provide it for non-text-bearing markers (the agent will treat it as no-op when no text is rendered).

Capture the agent's JSON envelope.

**(iii) Charge the review (UNCONDITIONAL — caveat #6)**

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from pathlib import Path
from src.image_bridge import BudgetCap, BudgetExhaustedError
from src.measurement import record_cost_event
budget = BudgetCap(usd=$BUDGET_USD, spent=$BUDGET_SPENT)
review_cost = 0.005  # Haiku per-call estimate
try:
    budget.charge(kind="review", provider="haiku", cost_usd=review_cost)
    record_cost_event(cwd=Path("$RUN_DIR"), kind="review",
                       provider="haiku", cost_usd=review_cost,
                       slide_index=$SLIDE, marker_id="$MARKER_ID")
    print(f"OK {budget.spent}")
except BudgetExhaustedError as exc:
    print(f"HALT_BUDGET {exc}")
PY
```

If the review charge raises BudgetExhaustedError, halt this enrichment with `halted_budget`. Do NOT call `advance_after_review` on an unpaid verdict — caveat #6 demands the cycle stops here.

**(iv) Advance the state machine**

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
import json
from src.cycle_state import advance_after_review, CycleState, Phase
from src.image_bridge import BudgetCap, PrivacyTierGate, ImageGenerationRequest
req = ImageGenerationRequest($REQ_DICT)
state = CycleState(request=req, phase=Phase("$PHASE"), attempt=$ATTEMPT)
budget = BudgetCap(usd=$BUDGET_USD, spent=$BUDGET_SPENT)
privacy = PrivacyTierGate(tier="$TIER", confirmation_received=$CONFIRMATION)
verdict = $VERDICT_PAYLOAD_DICT
decision = advance_after_review(state=state, verdict_payload=verdict,
                                  budget=budget, privacy=privacy)
print(json.dumps({
    "kind": decision.kind,
    "tier_used": decision.tier_used,
    "reason": decision.reason,
    "next_phase": decision.next_state.phase.value if decision.next_state else None,
    "next_attempt": decision.next_state.attempt if decision.next_state else None,
}))
PY
```

**(v) Act on the decision**

- `refine_and_retry` → dispatch the `jack-tar-deckhand:prompt-engineer` agent in `mode: "refine"` with the reviewer's `strengths`, `issues`, `composition_notes`, the prior prompt, and the iteration number. The agent returns a refined prompt string. Update `$PROMPT` and loop back to (i) with `state = decision.next_state`.
- `escalate_to_cloud` → dispatch `jack-tar-deckhand:prompt-engineer` in `mode: "refine"` once to incorporate the Phase A reviewer's last feedback at higher fidelity. Update `state = decision.next_state` and loop back to (i).
- `escalate_to_pro` → keep the prompt unchanged (the Flash-passing prompt is the proven prompt). Update `state = decision.next_state` and loop back to (i).
- `terminate_pass` → record final image, exit loop. Use `decision.tier_used` for the manifest.
- `terminate_accepted_with_issues` → keep the last image, record `status: accepted_with_issues`, surface to user.
- `terminate_halt_budget` / `terminate_halt_restricted` / `terminate_pending_confirmation` → record status, surface to user.

### Step 5d — Internal tier confirmation handshake

If any image's first cloud escalation hits `terminate_pending_confirmation` (privacy tier `internal`, no confirmation yet), prompt the user once:

> Confidentiality tier is `internal`. The first cloud image generation will send the prompt and any visual brief context to <provider>. Confirm cloud escalation for this run? (yes/no)

If yes, call `gate.mark_confirmation_received()` (state stored in $CONFIRMATION between iterations). Then re-attempt the failed enrichment from `decision.next_state` (which is None — restart the cycle from the prior `state` re-asserted with attempt = MAX_PHASE_A_ATTEMPTS so the next decision escalates to Phase B). If no, mark the enrichment `halted_pending_confirmation` and continue to the next.

### Step 5e — Save accepted images

For every `terminate_pass` result, the image at `$OUTPUT_PATH` is final. The path is already inside the allowlist (`$RUN_DIR/generated/`), so the enrichment ops in Step 7 will accept it.

For `accepted_with_issues` and other halt states, surface the slide-image and reason to the user before Step 7. The user may drop the enrichment from the plan.

## Step 6 — Build SmartArt specs (for SMARTART enrichments)

For each SMARTART enrichment NOT marked `skip`:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from pathlib import Path
import json
from src.smartart_bridge import select_layout_for_slide, build_spec_from_slide
from src.slide_facts import SlideFacts, Marker
slide = SlideFacts(slide_index=$SLIDE_INDEX,
                    text_content=$SLIDE_TEXT_REPR)
slide.markers.append(Marker(kind="SMARTART", identifier="$MARKER_IDENT",
                              left_emu=0, top_emu=0, width_emu=0, height_emu=0))
layout_id = select_layout_for_slide(slide, marker_id="$MARKER_ID")
spec = build_spec_from_slide(slide, marker_id="$MARKER_ID", layout_id=layout_id)
print(json.dumps(spec))
PY
```

The spec is held in memory and passed to the orchestrator; carriers are rendered inside `apply_enrichment` via `render_carrier`.

## Step 7 — Apply enrichments transactionally

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from pathlib import Path
from src.enrichment import EnrichmentPlan, EnrichmentItem, apply_enrichment
from src.colors_xml_builder import BrandPalette

items = [
    # one EnrichmentItem per user-approved enrichment, populated from prior steps.
    # For markers detected as SMARTART-FROM-LIST, set kind="smartart_from_list"
    # and leave smartart_spec=None — the bridge will extract bullet items from
    # the marker shape's text frame at apply time. For traditional SMARTART
    # markers (full content zone), set kind="smartart" and supply smartart_spec.
]

# Construct BrandPalette if Step 1 derived one. When all three slots are
# populated, brand-native rendering is the default; otherwise SmartArt falls
# back to Microsoft default palette (degraded but functional).
brand_palette = None
if "$BRAND_PALETTE_PRIMARY" and "$BRAND_PALETTE_TEXT_ON_PRIMARY" and "$BRAND_PALETTE_TEXT_ON_SURFACE":
    brand_palette = BrandPalette(
        primary_fill_hex="$BRAND_PALETTE_PRIMARY",
        text_on_primary_hex="$BRAND_PALETTE_TEXT_ON_PRIMARY",
        text_on_surface_hex="$BRAND_PALETTE_TEXT_ON_SURFACE",
    )

plan = EnrichmentPlan(
    source_pptx=Path("$PPTX_PATH"),
    output_pptx=Path("$PPTX_PATH").with_name("presentation-enriched.pptx"),
    items=items,
)
apply_enrichment(
    plan,
    allowed_image_roots=[Path("$RUN_DIR/generated"), Path("$RUN_DIR/carriers")],
    brand_palette=brand_palette,
)
PY
```

If `apply_enrichment` raises `EnrichmentApplyError`, surface the message to the user. The output file does not exist; the user can re-run after fixing the cause (e.g. an image path outside the allowlist, a missing marker name).

**Brand palette default (Contract 1 / Finding #10):** when Step 1 derived a `brand_palette`, Step 7 passes it to `apply_enrichment`, which patches every SmartArt carrier's `colors1.xml` with brand hex values before injection. SmartArt slides therefore render in the brief's palette by default. When the brief omits role-keyworded hex values, `brand_palette` is `None` and SmartArt falls back to Microsoft default palette — mention this in the per-deck report so the speaker can fix the brief if needed.

**SMARTART-FROM-LIST default (Contract 2 / Finding #9):** for analyser-detected markers of kind `SMARTART-FROM-LIST`, construct `EnrichmentItem(kind="smartart_from_list", marker_name="SMARTART-FROM-LIST:<slug>", smartart_spec=None, ...)`. The bridge extracts bullet items from the marker shape's text frame at apply time and replaces the list with the rendered SmartArt at the same coordinates. Title and surrounding prose on the slide remain untouched. This is the **preferred authoring pattern** — only fall back to traditional `SMARTART:` (full content zone, explicit `smartart_spec`) for graphic-only divider slides where the bridge owns the entire content area.

## Step 8 — Render slide images for cohesion review

```bash
soffice --headless --convert-to pdf --outdir "$RUN_DIR" "$RUN_DIR/presentation-enriched.pptx" 2>&1
pdftoppm -r 100 -png "$RUN_DIR/presentation-enriched.pdf" "$RUN_DIR/slide-images/slide"
```

(The /pptx superpower already establishes the LibreOffice + pdftoppm toolchain expectations; the bridge follows the same.)

## Step 9 — Dispatch the Enrichment Cohesion Reviewer

Build the manifest:

```json
{
  "enriched_slides": [
    {"slide_index": 1, "enrichment_kind": "background"},
    {"slide_index": 3, "enrichment_kind": "image"},
    {"slide_index": 5, "enrichment_kind": "smartart"}
  ],
  "rendered_images": [
    "/path/to/bridge-run/slide-images/slide-01.png",
    "/path/to/bridge-run/slide-images/slide-03.png",
    "/path/to/bridge-run/slide-images/slide-05.png"
  ],
  "visual_personality": "<from creative-brief Section B>"
}
```

Dispatch the `jack-tar-superpower-bridge:enrichment-cohesion-reviewer` agent with this manifest. Plugin agents are registered under the plugin namespace; bare names resolve to "agent type not found". It returns the JSON envelope defined in its agent definition.

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
import json
from src.cohesion_review import parse_reviewer_envelope, aggregate_for_report
envelope = json.loads(open("$REVIEWER_OUTPUT").read())
deck = parse_reviewer_envelope(envelope)
summary = aggregate_for_report(deck.slide_verdicts)
print(json.dumps({"deck": {"aggregate": deck.aggregate_verdict},
                   "summary": summary}, indent=2))
PY
```

## Step 10 — Act on cohesion verdicts (caveat #2 decision table)

For each `AutoAction` returned by `decide_action`:

- `no_action` — skip
- `record_only` — append to the report's flags section (nothing else)
- `regenerate` — re-run the per-image generate_with_review_cycle ONCE for that slide with the issue threaded into the prompt; if still flagged, surface to user
- `retry_clear_overlap` — re-run `apply_enrichment` for just that SMARTART item with `action="apply_clear_overlap"` (this is a separate apply call; the original transactional gate is preserved by re-running against a fresh source copy)
- `surface_to_user` — present the slide image and the verdict reason; ask the user whether to drop, regenerate manually, or accept

Track every action taken so the report reflects what actually happened.

## Step 11 — Write the enrichment report

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from datetime import datetime
from pathlib import Path
from src.enrichment_report import EnrichmentReport, EnrichmentLedgerEntry, write_report
from src.measurement import read_cost_ledger
from importlib.metadata import version

ledger_events = read_cost_ledger(Path("$RUN_DIR"))
ledger_entries = [
    EnrichmentLedgerEntry(
        slide_index=$ITEM_SLIDE,
        kind="$ITEM_KIND",
        marker_id="$ITEM_MARKER",
        engine_provider="$ITEM_PROVIDER",
        iterations="$ITEM_ITERATIONS",
        cost_usd=$ITEM_COST,
        verdict="$ITEM_VERDICT",
    ),
    # one per applied enrichment
]
report = EnrichmentReport(
    deck_name=Path("$PPTX_PATH").stem,
    source_pptx=Path("$PPTX_PATH"),
    output_pptx=Path("$PPTX_PATH").with_name("presentation-enriched.pptx"),
    bridge_version="0.1.0",
    confidentiality="$CONFIDENTIALITY_TIER",
    budget_cap_usd=$BUDGET_CAP_USD,
    ledger=ledger_entries,
    cohesion_summary=$COHESION_SUMMARY,
    contains_smartart=$CONTAINS_SMARTART,
    run_timestamp=datetime.now(),
)
write_report(report, Path("$PPTX_PATH").with_name("enrichment-report.md"))
PY
```

## Step 12 — Record measurement run (caveat #3)

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<PY
from pathlib import Path
from src.measurement import record_enrichment_run
record_enrichment_run(
    cwd=Path("$RUN_DIR"),
    adherence_rate=$ADHERENCE_RATE,                # markers requested vs delivered
    first_pass_acceptance=$FIRST_PASS_ACCEPT,      # cohesion reviewer aggregate == "pass"
    slides_enriched=$SLIDES_ENRICHED,
    slides_total=$TOTAL_SLIDES,
)
PY
```

## Step 13 — Deliver

Present to the user:

```
Enriched deck: <output>/presentation-enriched.pptx
Report:        <output>/enrichment-report.md

Slides enriched: N of M
Total cost:     $X.XX (budget cap $Y.YY)
Cohesion:       pass=A, suggestions=B, blocking=C

Next: open the deck in PowerPoint to verify SmartArt rendering.
```

Stop. Do NOT auto-open the file or run further skills.

## Failure paths

- **Analyser returns 0 markers AND no unmarked candidates** — surface the diagnostic, recommend the user re-run /pptx with the `objectName` API note included in the brief, halt.
- **`apply_enrichment` raises** — surface the error verbatim; the cause is usually a missing marker on a slide the analyser did find; ask the user whether to retry without that item.
- **Budget exhausted mid-run** — `BudgetExhaustedError` is raised inside the cycle. Catch it in the orchestrator and report what was applied so far; include the cost ledger in the report.
- **Restricted tier blocks Phase 2** — `RestrictedTierError` from the cycle. Report which enrichments were dropped and why.
