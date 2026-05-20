---
name: verify
description: Meta-verify — discover all jack-tar engine plugins, call each verify, report aggregate pipeline capability and discipline-hook readiness.
allowed-tools: Bash(python *), Bash(python3 *), Bash(node *), Bash(echo *), Bash(test *), Skill
---

# /verify

Discover all installed jack-tar engine plugins, call each plugin's `:verify` skill, and report aggregate pipeline capability AND the status of the discipline hook (issue #76).

## Step 1: Check local dependencies

Check that Python and Node.js with pptxgenjs are available:

```bash
python3 --version
node -e "require('pptxgenjs'); console.log('pptxgenjs OK')" 2>/dev/null || echo "pptxgenjs NOT_FOUND"
```

## Step 2: Discover engine plugins

Call each engine plugin's verify skill. If the skill doesn't exist (plugin not installed), record as "Not installed".

Invoke each in sequence:
1. `jack-tar-ollama:verify`
2. `jack-tar-cloud:verify`
3. `jack-tar-msft-smartart:verify`
4. `jack-tar-custom-smartart:verify`

For each, extract the STATUS line from the output.

## Step 2.5: Detect optional external tool (paperbanana)

Paperbanana is an optional **external CLI tool** (like LaTeX or
ImageMagick) that handles the `academic_figure` rendering strategy —
publication-quality scientific figures via a multi-agent diagram
generation pipeline. It is **NOT a Claude Code plugin and NOT a
jack-tar engine plugin** — operators install it via
`pip install 'paperbanana[google]'` (or `pipx` / `uvx`), and jack-tar
shells out to its CLI on demand. See
`docs/architecture/paperbanana-integration-v2.md` for the full framing
rationale.

Detection runs in two layers: runnability + health.

### 2.5a — Runnability probe + doctor health-check + install guidance

```bash
PB_RUNNABLE=$(python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/src')
from paperbanana_dispatch import is_paperbanana_available
print('READY' if is_paperbanana_available() else 'NOT_FOUND')
" 2>/dev/null || echo "ERROR")

if [ "$PB_RUNNABLE" = "READY" ]; then
  PB_CLI_PATH=$(command -v paperbanana 2>/dev/null || echo "(import-only, not on PATH)")
  PB_DOCTOR=$(paperbanana doctor 2>&1 || echo "")
  if echo "$PB_DOCTOR" | grep -qE "GOOGLE_API_KEY[[:space:]]+set"; then
    echo "paperbanana CLI:           READY ($PB_CLI_PATH)"
    PB_FINAL="READY"
  else
    echo "paperbanana CLI:           PARTIAL ($PB_CLI_PATH — GOOGLE_API_KEY not set)"
    echo "  Get a free Gemini key at https://makersuite.google.com/app/apikey"
    echo "  Then: export GOOGLE_API_KEY=... && re-run /verify"
    PB_FINAL="PARTIAL"
  fi
else
  echo "paperbanana CLI:           NOT_FOUND"
  echo ""
  echo "  To install paperbanana (publication-tier academic figures):"
  echo "    pip install 'paperbanana[google]'           # simplest, in jack-tar venv"
  echo "    pipx install 'paperbanana[google]'          # global CLI"
  echo "    uvx --from 'paperbanana[mcp]' paperbanana-mcp   # MCP server (v1.4.1+)"
  echo ""
  echo "  After install, get a free Gemini key:"
  echo "    https://makersuite.google.com/app/apikey"
  echo "    export GOOGLE_API_KEY=..."
  echo "    paperbanana doctor   # smoke-test"
  echo "    /jack-tar-deckhand:verify   # re-run"
  PB_FINAL="NOT_FOUND"
fi
```

The Python helper (`paperbanana_dispatch.is_paperbanana_available`)
probes runnability via two paths:

1. `importlib.util.find_spec("paperbanana")` — covers
   pip-installed-in-jack-tar-venv (the common case for v1.4).
2. `shutil.which("paperbanana")` — covers pipx, system install, and
   any case where the CLI is on PATH but the Python package is not on
   jack-tar's `sys.path`.

When paperbanana is `NOT_FOUND`, the imagegen-bridge's `academic_figure`
branch falls back to Nano Banana Flash 1K with academic-figure-aware
prompting — the pipeline still produces a figure, just not at
publication tier.

When `PARTIAL` (CLI installed but `GOOGLE_API_KEY` not set),
paperbanana invocations would crash at first Gemini call; the bridge
also takes the fallback path so the deck still ships.

## Step 3: Determine pipeline capabilities

Based on engine plugin availability:
- **Draft images:** READY if jack-tar-ollama is FULLY_AVAILABLE or PARTIALLY_AVAILABLE
- **Production images:** READY if jack-tar-cloud is FULLY_AVAILABLE or PARTIALLY_AVAILABLE
- **Editable SmartArt:** READY if jack-tar-msft-smartart is FULLY_AVAILABLE
- **Custom graphics:** READY if jack-tar-custom-smartart is FULLY_AVAILABLE or PARTIALLY_AVAILABLE
- **Academic figures:** READY if `$PB_FINAL` is READY (paperbanana installed + `GOOGLE_API_KEY` set); PARTIAL if `$PB_FINAL` is PARTIAL (CLI installed, key missing — fallback active); FALLBACK if NOT_FOUND (cloud Flash 1K with academic-figure prompting still produces a figure, just not publication-tier)
- **Iterate-slide refinement:** READY if `$PB_FINAL` is READY (`/jack-tar-deckhand:iterate-slide` can refine academic_figure slides via paperbanana `--continue-run`); PARTIAL if `$PB_FINAL` is PARTIAL (CLI present but missing key); NOT_AVAILABLE if NOT_FOUND (skill cannot run — refinement requires a paperbanana_run_id which only paperbanana-rendered slides have)
- **Deck assembly:** READY if pptxgenjs is installed
- **QA checks:** always READY (built into this plugin)

## Step 4: Discipline hook readiness (issue #76)

Verify the `block-png-read.sh` PreToolUse hook is installed and fires correctly. Three checks:

### 4a — Hook script presence + executability

```bash
HOOK_SCRIPT="${CLAUDE_PLUGIN_ROOT}/hooks/block-png-read.sh"
if [ -x "$HOOK_SCRIPT" ]; then
  echo "Hook script:         OK ($HOOK_SCRIPT)"
else
  echo "Hook script:         MISSING (expected at $HOOK_SCRIPT)"
fi
```

### 4b — Synthetic fire test

Pipe three test payloads through the hook script and assert exit codes:

- PNG path → exit 1 (block) + stderr contains "BLOCKED"
- PNG path with `ALLOW_PNG_READ=1` → exit 0 (bypass)
- Non-image path → exit 0 (pass-through)

```bash
HOOK_SCRIPT="${CLAUDE_PLUGIN_ROOT}/hooks/block-png-read.sh"

# Test 1: PNG should block
echo '{"tool_input":{"file_path":"/tmp/x.png"}}' | "$HOOK_SCRIPT" >/dev/null 2>&1
PNG_EXIT=$?
[ "$PNG_EXIT" = "1" ] && echo "  PNG block:         OK" || echo "  PNG block:         FAILED (exit $PNG_EXIT, expected 1)"

# Test 2: bypass should pass
ALLOW_PNG_READ=1 bash -c "echo '{\"tool_input\":{\"file_path\":\"/tmp/x.png\"}}' | \"$HOOK_SCRIPT\"" >/dev/null 2>&1
BYPASS_EXIT=$?
[ "$BYPASS_EXIT" = "0" ] && echo "  Bypass works:      OK" || echo "  Bypass works:      FAILED (exit $BYPASS_EXIT, expected 0)"

# Test 3: non-image should pass
echo '{"tool_input":{"file_path":"/tmp/x.md"}}' | "$HOOK_SCRIPT" >/dev/null 2>&1
NONIMG_EXIT=$?
[ "$NONIMG_EXIT" = "0" ] && echo "  Non-image pass:    OK" || echo "  Non-image pass:    FAILED (exit $NONIMG_EXIT, expected 0)"
```

### 4c — Hook registration

Plugins-managed hooks are registered automatically when the plugin is enabled. The verify skill cannot reliably introspect harness state across all platforms, so this check is informational: if the synthetic fire test passes (4b), the hook script is functional. Whether the harness has actually wired it up to the Read tool is observable by attempting a Read on a PNG within the session — that will block (or bypass with the env var) once registered.

## Step 5: Report status

Example output:

```
PLUGIN: jack-tar-deckhand
VERSION: 1.0.0

DEPENDENCIES:
  Python:          READY (3.12.x)
  Node.js:         READY (22.x)
  pptxgenjs:       READY

ENGINE PLUGINS:
  jack-tar-ollama:           FULLY_AVAILABLE
  jack-tar-cloud:            PARTIALLY_AVAILABLE
  jack-tar-msft-smartart:    FULLY_AVAILABLE
  jack-tar-custom-smartart:  NOT_AVAILABLE

EXTERNAL TOOLS:
  paperbanana CLI:           NOT_FOUND

  To install paperbanana (publication-tier academic figures):
    pip install 'paperbanana[google]'           # simplest, in jack-tar venv
    pipx install 'paperbanana[google]'          # global CLI
    uvx --from 'paperbanana[mcp]' paperbanana-mcp   # MCP server (v1.4.1+)

  After install, get a free Gemini key:
    https://makersuite.google.com/app/apikey
    export GOOGLE_API_KEY=...
    paperbanana doctor   # smoke-test
    /jack-tar-deckhand:verify   # re-run

PIPELINE CAPABILITY:
  Draft images:           READY (ollama available)
  Production images:      READY (cloud partially available)
  Editable SmartArt:      READY (msft-smartart available)
  Custom graphics:        NOT_READY (custom-smartart not available)
  Academic figures:       FALLBACK (paperbanana not installed — Flash 1K fallback active)
  Iterate-slide refine:   NOT_AVAILABLE (paperbanana required — install per EXTERNAL TOOLS above)
  Deck assembly:          READY (pptxgenjs installed)
  QA checks:              READY

DISCIPLINE HOOK (issue #76):
  Hook script:         OK (${CLAUDE_PLUGIN_ROOT}/hooks/block-png-read.sh)
  PNG block:           OK
  Bypass works:        OK
  Non-image pass:      OK

STATUS: PARTIALLY_AVAILABLE
REASON: jack-tar-custom-smartart not available
```

Overall STATUS rules:
- `STATUS: FULLY_AVAILABLE` — pptxgenjs installed + at least one image plugin + at least one SmartArt plugin
- `STATUS: PARTIALLY_AVAILABLE` — pptxgenjs installed but some engine plugins missing
- `STATUS: NOT_AVAILABLE` — pptxgenjs not installed (can't assemble decks at all)
