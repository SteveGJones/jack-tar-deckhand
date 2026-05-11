---
name: verify
description: Meta-verify — discover all jack-tar engine plugins, call each verify, report aggregate pipeline capability and discipline-hook readiness.
allowed-tools: Bash(python *), Bash(node *), Bash(echo *), Bash(test *), Skill
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

## Step 3: Determine pipeline capabilities

Based on engine plugin availability:
- **Draft images:** READY if jack-tar-ollama is FULLY_AVAILABLE or PARTIALLY_AVAILABLE
- **Production images:** READY if jack-tar-cloud is FULLY_AVAILABLE or PARTIALLY_AVAILABLE
- **Editable SmartArt:** READY if jack-tar-msft-smartart is FULLY_AVAILABLE
- **Custom graphics:** READY if jack-tar-custom-smartart is FULLY_AVAILABLE or PARTIALLY_AVAILABLE
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

PIPELINE CAPABILITY:
  Draft images:      READY (ollama available)
  Production images: READY (cloud partially available)
  Editable SmartArt: READY (msft-smartart available)
  Custom graphics:   NOT_READY (custom-smartart not available)
  Deck assembly:     READY (pptxgenjs installed)
  QA checks:         READY

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
