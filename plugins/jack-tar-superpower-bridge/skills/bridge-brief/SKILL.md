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

**Working dispatch pattern (Run 2/3 dogfood evidence — Finding #7):** the persona is reliable on small scoped dispatches but drifts on whole-brief drafts and surgical-edit-of-prior-output. Use the four-dispatch pattern from the start:

1. **R1 — propose 2–3 arcs** with trade-offs; wait for Speaker selection.
2. **R2 — propose communication intent (2–3 takeaway phrasings) + 2–3 visual personalities;** wait for Speaker selection.
3. **R3a — Sections A and B only.** Lock the arc, takeaway, and personality decisions explicitly in the prompt. Use hard scope rules: "Begin your output with `## Section A — Narrative Architecture`. End your output with the close of the Section B palette table." Do NOT include Section C.
4. **R3b — Section C only.** Use hard scope rules: "Begin your output with `## Section C — Placeholder Instructions`. End your output with the closing ``` of the API note." Do NOT repeat Sections A or B.

Whole-brief dispatches and surgical-edit-of-prior-output dispatches drift unpredictably. Avoid them.

**Section C lead pattern (Contracts 1 + 2 default behaviour):** the persona's Section C should lead with `SMARTART-FROM-LIST:` as the preferred SmartArt pattern (preserves slide structure, picks layout from list content, brand-palette inherited from Section B automatically). `SMARTART:` (full content zone) is the secondary "graphic-only divider" pattern. The persona contract documents this; if R3b drifts back toward leading with `SMARTART:`, redispatch with explicit "lead with SMARTART-FROM-LIST" instruction.

**Section C must include sub-page scale typology + chart routing + BG-on-pivot guidance + EXACT spelled labels for text-bearing IMAGE markers + SMARTART-FROM-LIST bullet-length constraint** (Runs 5+6 evidence — without these, /pptx defaults to content-zone-width markers, routes chart-shaped subjects to IMAGE markers where Ollama text rendering corrupts them, ships images with misspellings, or fails apply on long bullets):
- **Sub-page scale typology** with explicit inch coordinates for SMARTART-FROM-LIST (side-accent ~3.5×3.5 / inline ~3.0×3.0 / banner ~10.0×2.0) and IMAGE (side-accent ~4.0×3.5 / inline ~3.0×3.0 / banner ~10.0×1.8).
- **Native chart routing language** explicitly redirecting chart-shaped subjects (X-vs-Y, time series, projection) to `addChart()`, NOT IMAGE markers.
- **BG marker default to 0–1 per deck**, on the single structural register-shift pivot if the arc has one.
- **Build.js BG marker authoring caveat**: rect only with `objectName="BG:slug"`, NO standalone `addText` label (Finding #17 — addText survives enrichment as residual cosmetic).
- **EXACT spelled labels REQUIRED list for any text-bearing IMAGE marker** (Run 6 Findings #19/#20 — without an explicit expected-text reference in the subject brief, the image-reviewer confabulates spelling correctness and ships misspellings). The persona's Section C subject brief MUST list every expected wordmark, label, named block, and named arrow verbatim. /enrich-deck extracts this list and passes it on reviewer dispatch so the reviewer can compare every rendered word against the expected list.
- **SMARTART-FROM-LIST bullets ≤24 chars** for the bridge's default `process1` layout (Run 4/5/6 Finding #13 reaffirmed) — longer items either truncate at apply or fail outright. If the deck's argument requires longer prose-style bullets, the slide is better served by a native bulleted list or table than by a SmartArt graphic.

The persona's agent definition codifies all of these. **Run 6's brief** at `output/dogfood-bridge-run-6/creative-brief.md` is the canonical example for institutional / board / M&A registers. **Run 5's brief** at `output/dogfood-bridge-run-5/creative-brief.md` is canonical for senior-leadership strategy. **Run 4's brief** at `output/dogfood-bridge-run-4/creative-brief.md` is canonical for engineering-leadership / data-led decks. Direct the persona toward the closest example when in doubt.

**Section B palette table is REQUIRED for any deck containing SmartArt** (Contract 1 / Run 4 Finding #12). The persona's agent definition templates the table; reject any draft where Section B omits it for a SmartArt-bearing deck. The "Structural / Primary fill" row pins the bridge's `derive_palette_from_brief_text` heuristic.

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
