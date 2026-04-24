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
    for p in base.rglob('jack-tar-superpower-bridge/.claude-plugin/plugin.json'):
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

Use the `Agent` tool with `subagent_type="narrative-brief-architect"`.

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
