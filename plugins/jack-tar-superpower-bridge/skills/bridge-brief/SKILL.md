---
name: bridge-brief
description: Phase 1 of the superpower bridge — collaborative narrative pre-brief for the /pptx superpower. Dispatches the Narrative Brief Architect persona to propose arcs, capture communication intent, and produce a creative-brief.md that guides /pptx to build a well-structured deck with placeholder markers where visual enrichment will live.
argument-hint: "<topic>" [--duration <minutes>] [--audience "<audience>"] [--confidentiality public|internal|restricted] [--budget-cap <usd>]
allowed-tools: Bash(python *), Read, Skill, Agent
---

# /bridge-brief

Phase 1 of the superpower bridge workflow. The user invokes this skill, you collaboratively shape a creative brief, and you save the result to `creative-brief.md` for the user to hand to `/pptx`.

You are NOT the persona — you are the orchestrator. The Narrative Brief Architect persona does the creative reasoning; you handle dispatch, parsing, and file I/O.

## Parse arguments

Parse `$ARGUMENTS` as a single quoted topic followed by optional flags:

- **<topic>** (positional, required) — the talk topic, e.g. "AI agent architectures"
- **--duration <minutes>** (default: 20) — talk length in minutes
- **--audience "<audience>"** (default: "developers") — who the audience is
- **--confidentiality public|internal|restricted** (default: ask the user)
- **--budget-cap <usd>** (default: 1.00)

If `<topic>` is missing, prompt the user for it before dispatching the agent.

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
```

## Step 1 — confirm confidentiality if not supplied

If `--confidentiality` was not supplied, ask the user:

> The brief carries a confidentiality tier that controls whether Phase 3 image generation can use cloud providers:
>
> - **public** — full Ollama → cloud pipeline (default for conference content)
> - **internal** — cloud allowed but confirm before each first call (company-internal material)
> - **restricted** — cloud disabled, Ollama only (sensitive material)
>
> Which tier? (public / internal / restricted)

Capture the answer.

## Step 2 — dispatch the Narrative Brief Architect agent

Use the `Agent` tool with `subagent_type="jack-tar-superpower-bridge:narrative-brief-architect"`. Plugin agents are registered under the plugin namespace; bare names resolve to "agent type not found".

The dispatch prompt MUST contain the topic, duration, audience, confidentiality, and budget cap. Pass through every collaborative round — when the user requests a revision, dispatch a new agent turn including the prior draft and the revision request.

Example dispatch prompt:

```
Topic: AI agent architectures
Duration: 20 minutes
Audience: developers
Confidentiality: public
Budget cap: $1.00

Propose 2-3 narrative arcs with trade-offs and a recommendation. Wait for my choice before drafting Section A.
```

The agent runs in collaborative mode — it proposes, you relay to the user, the user picks or adjusts, you re-dispatch with the updated context. Loop until the user approves a complete draft. (Target: ≤ 2 revision rounds per the persona's measurement hooks.)

**Split-dispatch pattern — codified working pattern (Findings #3 + #7).** The persona is reliable on small scoped dispatches but drifts on whole-brief drafts and surgical-edit-of-prior-output. Six dogfood runs (2026-04-23 → 2026-04-29) have validated this; **Runs 3 / 4 / 5 / 6 each completed in 4 dispatches with zero persona drift**. Use the four-dispatch pattern from the start, never collapse it:

1. **R1 — propose 2–3 arcs** with trade-offs; wait for Speaker selection.
2. **R2 — propose communication intent (2–3 takeaway phrasings) + 2–3 visual personalities;** wait for Speaker selection. **Issue #93 — at R2 also propose a `strap_style` choice** (`prose-sentence` vs `all-caps-three-beat`) tuned to the audience and register, and surface the trade-off so the Speaker can pin or defer. The Speaker's decision becomes the brief's `Strap style:` header field. When the Speaker declines to pin (defers to the persona), leave the field absent in the saved brief — the persona will choose contextually in R3a.
3. **R3a — Sections A and B only.** Lock the arc, takeaway, and personality decisions explicitly in the prompt; if R2 produced a `strap_style` decision, lock it too so R3a's Section B narrative explicitly mentions the strap cadence. Use hard scope rules: "Begin your output with `## Section A — Narrative Architecture`. End your output with the close of the Section B palette table." Do NOT include Section C.
4. **R3b — Section C only.** Use hard scope rules: "Begin your output with `## Section C — Placeholder Instructions`. End your output with the closing ``` of the API note." Do NOT repeat Sections A or B.

**Why split:** the persona's reasoning quality scales inversely with output scope. R3a (Sections A+B) and R3b (Section C) carry different decisions (narrative arc + visual personality vs. per-marker subject briefs + sub-page scale typology + EXACT label lists); merging them dilutes both. The dogfood evidence is consistent across 4 consecutive runs.

**Anti-patterns surfaced and to avoid:**

- **Whole-brief dispatch (one R3 covering A+B+C)** — drifts on Section C marker assignments. Surfaced Run 1; avoided since Run 3.
- **Surgical-edit-of-prior-output dispatch** ("change line 47 to X") — the persona regenerates the whole prior output and frequently mutates unrelated content. If the Speaker requests changes after R3a or R3b, re-dispatch the FULL section with the revision instruction folded into the scope rules, not as an edit-of-prior-output.
- **Combining R1 and R2 into a single dispatch** — proposing arcs and personalities together suppresses the Speaker's choice ladder; the persona anchors on its own first proposal. R1 commit precedes R2 proposals.

The R1→R2→R3a→R3b sequence is the contract; treat it as load-bearing.

**Section C lead pattern (Contracts 1 + 2 default behaviour):** the persona's Section C should lead with `SMARTART-FROM-LIST:` as the preferred SmartArt pattern (preserves slide structure, picks layout from list content, brand-palette inherited from Section B automatically). `SMARTART:` (full content zone) is the secondary "graphic-only divider" pattern. The persona contract documents this; if R3b drifts back toward leading with `SMARTART:`, redispatch with explicit "lead with SMARTART-FROM-LIST" instruction.

**Section C must include sub-page scale typology + chart routing + BG-on-pivot guidance + EXACT spelled labels for text-bearing IMAGE markers + SMARTART-FROM-LIST bullet-length constraint** (Runs 5+6 evidence — without these, /pptx defaults to content-zone-width markers, routes chart-shaped subjects to IMAGE markers where Ollama text rendering corrupts them, ships images with misspellings, or fails apply on long bullets):
- **Sub-page scale typology** with explicit inch coordinates for SMARTART-FROM-LIST (side-accent ~3.5×3.5 / inline ~3.0×3.0 / banner ~10.0×2.0) and IMAGE (side-accent ~4.0×3.5 / inline ~3.0×3.0 / banner ~10.0×1.8).
- **Native chart routing language** explicitly redirecting chart-shaped subjects (X-vs-Y, time series, projection) to `addChart()`, NOT IMAGE markers.
- **BG marker default to 0–1 per deck**, on the single structural register-shift pivot if the arc has one.
- **Build.js BG marker authoring caveat**: rect only with `objectName="BG:slug"`, NO standalone `addText` label (Finding #17 — addText survives enrichment as residual cosmetic).
- **EXACT spelled labels REQUIRED list for any text-bearing IMAGE marker** (Run 6 Findings #19/#20 — without an explicit expected-text reference in the subject brief, the `jack-tar-deckhand:image-reviewer` agent confabulates spelling correctness and ships misspellings). The persona's Section C subject brief MUST list every expected wordmark, label, named block, and named arrow verbatim. /enrich-deck extracts this list and passes it on reviewer dispatch so the reviewer can compare every rendered word against the expected list.
- **SMARTART-FROM-LIST bullets ≤24 chars** for the bridge's default `process1` layout (Run 4/5/6 Finding #13 reaffirmed) — longer items either truncate at apply or fail outright. If the deck's argument requires longer prose-style bullets, the slide is better served by a native bulleted list or table than by a SmartArt graphic.

The persona's agent definition codifies all of these. **Run 6's brief** at `output/dogfood-bridge-run-6/creative-brief.md` is the canonical example for institutional / board / M&A registers. **Run 5's brief** at `output/dogfood-bridge-run-5/creative-brief.md` is canonical for senior-leadership strategy. **Run 4's brief** at `output/dogfood-bridge-run-4/creative-brief.md` is canonical for engineering-leadership / data-led decks. Direct the persona toward the closest example when in doubt.

**Section B palette table is REQUIRED for any deck containing SmartArt** (Contract 1 / Run 4 Finding #12). The persona's agent definition templates the table; reject any draft where Section B omits it for a SmartArt-bearing deck. Two rows are load-bearing for `derive_palette_from_brief_text`:

- **"Structural / Primary fill"** (or "Brand colour") — the dark token bridge fills SmartArt shapes with.
- **"Text on Brand colour"** (v0.2 #24) — the contrasting label colour for text INSIDE those shapes. Without it, bridge infers from surface (v0.1.x fallback). Decks where surface ≠ desired text-on-primary contrast (e.g. vellum surface but white SmartArt labels) should declare it explicitly.

## Step 3 — show the draft to the user and request approval

When the agent returns a complete brief draft, present it to the user verbatim and ask:

> Here is the draft creative brief. Approve to save to `creative-brief.md`, or describe what to change.

If the user approves, proceed to Step 4. If they request changes, dispatch the agent again with the revision instructions.

## Step 4 — save via the Python writer

Once approved, parse the agent's draft markdown and write it via the bridge's writer (so format consistency is preserved across runs):

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<'PY'
from pathlib import Path
from src.creative_brief import parse_brief_markdown, write_brief_markdown
draft_text = open('/tmp/bridge-brief-draft.md').read()  # written by orchestrator from agent output
brief = parse_brief_markdown(draft_text)
write_brief_markdown(brief, Path.cwd() / 'creative-brief.md')
print("OK")
PY
```

Before running, write the agent's approved markdown to `/tmp/bridge-brief-draft.md` (or any session-temp path you choose) so the Python writer can parse and re-emit it in canonical form.

If `parse_brief_markdown` raises `CreativeBriefValidationError`, surface the error to the user — the agent's output is malformed; ask them to re-dispatch the agent.

### Step 4b — brief-save lint (v0.2 #25)

After `write_brief_markdown` succeeds, run the brief-save lint to verify every text-bearing IMAGE marker in Section C has an EXACT-labels block the extractor can parse. Run 7 + Run 8 both shipped briefs with format-flattened EXACT blocks (`- text` instead of `- role: "exact text"`) — the extractor returned 0 labels per marker, /enrich-deck dispatched the reviewer without expected text, and Haiku confabulated correctness on misspelled images. The lint catches this at brief-save time before /enrich-deck ever runs.

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<'PY'
from pathlib import Path
from src.creative_brief import lint_brief_for_extract_compatibility
brief_text = (Path.cwd() / 'creative-brief.md').read_text()
errors = lint_brief_for_extract_compatibility(brief_text)
if errors:
    print("BRIEF_LINT_FAILED")
    for err in errors:
        print(f"  - {err}")
else:
    print("BRIEF_LINT_OK")
PY
```

If the lint reports errors:

> ⚠ Brief saved, but the lint found IMAGE markers without parseable EXACT-labels blocks:
>
> - `IMAGE:emblematic-thylacine`: no EXACT-labels block found in Section C. If this marker carries text content, add an `EXACT spelled labels REQUIRED:` blockquote with `- role: "exact text"` bullets. If atmospheric, say so in the subject brief.
>
> The brief is technically valid (parse_brief_markdown succeeded), but /enrich-deck will dispatch the `jack-tar-deckhand:image-reviewer` agent WITHOUT expected text for these markers, and Haiku may confabulate spelling correctness on misspelled images. Recommended: re-dispatch the `jack-tar-superpower-bridge:narrative-brief-architect` with explicit instructions to add EXACT-labels for these markers, OR mark them atmospheric ("vignette", "no text") if they carry no visible text.

Operator may proceed if confident the lint is over-flagging (e.g. atmospheric markers whose subject brief used a non-standard opt-out phrasing). The lint is a guard rail, not a hard gate — proceed-anyway is allowed but should be conscious.

## Step 5 — record measurement hooks

After writing the file, append a one-line entry to `creative-brief-measurement.jsonl` in the same directory:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<'PY'
from pathlib import Path
from src.measurement import record_brief_run
record_brief_run(
    cwd=Path.cwd(),
    approval_turns=$APPROVAL_TURNS,        # how many revision rounds you went through
    structural_complete=True,              # parse_brief_markdown succeeded
    confidentiality="$CONFIDENTIALITY",
)
PY
```

`$APPROVAL_TURNS` is the integer count of agent dispatches you ran before the user approved (1 if approved on first draft).

**Phase 1 cost ledger (Finding #8 — extended in v0.1.x).** When you have an approximate cost figure for the Phase 1 dispatches (Sonnet token spend on the four `jack-tar-superpower-bridge:narrative-brief-architect` rounds), append a brief_authoring cost event so the Phase 3 enrichment-report ledger reflects total bridge spend, not just Phase 3 image generation. Enterprise speakers asked for this after Run 2 to give a complete cost picture per deck:

```bash
PYTHONPATH="$PLUGIN_ROOT" python3 - <<'PY'
from pathlib import Path
from src.measurement import record_cost_event
# Approximate Phase 1 LLM cost — sum of token costs across the four
# brief-authoring dispatches (jack-tar-superpower-bridge:narrative-brief-architect).
# Calibrate from the harness's reported per-call cost when available;
# the typical figure is ~$0.03–$0.06 per Sonnet brief authoring round,
# so 4 rounds ≈ $0.12–$0.24.
record_cost_event(
    cwd=Path.cwd(),
    kind="brief_authoring",
    provider="sonnet",
    cost_usd=$BRIEF_AUTHORING_COST_USD,
    slide_index=None,
    marker_id=None,
)
PY
```

If the harness does not surface per-call costs, omit this step rather than logging fabricated numbers — the absence of a `brief_authoring` event is a known-gap signal for downstream cost-summarisation tools.

## Step 6 — report

Print a summary:

```
Creative brief saved to creative-brief.md
- Topic: <topic>
- Duration: <N> min
- Audience: <audience>
- Confidentiality: <tier>
- Budget cap: $<X.XX>
- Approval turns: <N>

Next: invoke /pptx with this brief as context. Then run /enrich-deck on the resulting .pptx.
```

Stop. Do NOT auto-invoke /pptx — that is a separate user step.
