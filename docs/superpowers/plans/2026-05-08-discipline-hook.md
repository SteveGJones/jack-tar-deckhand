# Plan — Image-review discipline hook (auto-installed via plugin manifest)

**Status:** ready to execute
**Created:** 2026-05-08
**Source:** [2026-05-07 blog-post asset run dogfood retrospective](../dogfooding/2026-05-07-blog-post-asset-run.md) — failure #1 (operator pulled 9 PNGs into orchestration context)
**Issue:** #76
**Sibling plan:** [2026-05-08 blog-post bug batch](2026-05-08-blog-post-bug-batch.md) — independent code paths, **coordinated release**.

## Why

During the 2026-05-07 dogfood the operator's `Read` tool pulled nine generated PNGs directly into the orchestration context before the user spotted it and corrected. Each PNG carries thousands of tokens that compound across every subsequent turn — that single failure burned more context than the rest of the run combined.

Memory updates alone are insufficient: the rule was already in `feedback_review_every_visual.md` at the start of the run, and I broke it anyway. Soft constraints don't bind; the harness has to.

The fix is a `PreToolUse` hook that intercepts `Read` calls on image files and **blocks** them, with a clear escape hatch for the rare legitimate case (the image IS the user-facing answer). Hooks declared in a plugin manifest are auto-registered when the plugin is installed — no separate setup skill, no manual settings.json edit. Plugin install IS the install.

## Architecture

| Layer | Mechanism |
|---|---|
| Hook script | `plugins/jack-tar-deckhand/hooks/block-png-read.sh` — reads tool input from stdin, blocks on image extensions unless `ALLOW_PNG_READ=1` is set. |
| Manifest declaration | `plugins/jack-tar-deckhand/.claude-plugin/plugin.json` gains a `hooks.PreToolUse` entry pointing at the script with matcher `Read`. |
| Verify check | `/jack-tar-deckhand:verify` extended to confirm the hook is registered and (synthetically) fires correctly. |
| Documentation | Top-level `CLAUDE.md` "MANDATORY" section gets a short note: rule is enforced automatically; bypass via env var. |

## Phase 1 — Write the hook script

**File:** `plugins/jack-tar-deckhand/hooks/block-png-read.sh`

```bash
#!/usr/bin/env bash
# block-png-read.sh — PreToolUse hook for Read.
# Blocks Read on image files (PNG, JPG, GIF, WEBP, BMP) to prevent
# orchestration-context burn. Operators dispatch image-reviewer
# (or general-purpose) subagents instead — those return JSON verdicts
# without pulling pixel bytes into the main conversation.
#
# Bypass: set ALLOW_PNG_READ=1 in the env when the image IS the user-facing
# answer (e.g. user said "show me X").

set -euo pipefail

# Claude Code's hook protocol: tool input arrives as JSON on stdin.
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c 'import json, sys; d = json.load(sys.stdin); print(d.get("tool_input", {}).get("file_path", ""))')

# Bypass for explicit operator override.
if [[ "${ALLOW_PNG_READ:-}" == "1" ]]; then
  exit 0
fi

# Block Read on image extensions (case-insensitive).
shopt -s nocasematch
if [[ "$FILE_PATH" =~ \.(png|jpe?g|gif|webp|bmp|tiff?)$ ]]; then
  cat >&2 <<EOF
BLOCKED by jack-tar-deckhand discipline hook: Read on image file would
burn orchestration context. Image files carry thousands of tokens each
and compound across every subsequent turn.

Path: $FILE_PATH

Use one of these instead:
  • Dispatch the jack-tar-deckhand:image-reviewer agent (Haiku, cheap)
    with the path + intent, capture a JSON verdict.
  • Dispatch the general-purpose agent (Sonnet/Opus) for higher visual
    accuracy on complex scenes.

Both subagents read the image into THEIR context and return text —
your orchestration stays lean.

Bypass: set ALLOW_PNG_READ=1 in env when the image IS the user-facing
answer (rare — e.g. user said "show me X"). Treat the bypass as a
deliberate signal, not a workaround.
EOF
  exit 1
fi

shopt -u nocasematch
exit 0
```

The script is bash for portability across the project's existing tooling. Python is available in the runtime so the JSON parse is a one-liner. The bypass variable + the explanatory message are the load-bearing UX details.

## Phase 2 — Manifest declaration

**File:** `plugins/jack-tar-deckhand/.claude-plugin/plugin.json`

Add a `hooks` block:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read",
        "command": "${CLAUDE_PLUGIN_ROOT}/hooks/block-png-read.sh"
      }
    ]
  }
}
```

`${CLAUDE_PLUGIN_ROOT}` is the standard Claude Code variable that resolves to the installed plugin's root directory. The hook script is referenced relatively to that.

The matcher `Read` ensures the hook only fires for `Read` tool calls — `Write`, `Edit`, and other tools are unaffected. PNG operations that LEGITIMATELY happen (writing a PNG, editing a manifest that references a PNG path) pass through.

## Phase 3 — Version bump (coordinated release)

This phase is **shared with the bug-batch plan**. Do NOT bump versions independently — see [Coordinated release](#coordinated-release) below. All three plugins (`jack-tar-cloud`, `jack-tar-ollama`, `jack-tar-deckhand`) bump together as a single release once all PRs from both plans have landed code-only.

## Phase 4 — Extend `jack-tar-deckhand:verify`

The verify skill currently does meta-discovery of engine plugins and reports aggregate pipeline capability. Add a new section: **discipline hook readiness**.

Three checks:

1. **Hook script exists**: `$PLUGIN_ROOT/hooks/block-png-read.sh` is present and executable.
2. **Hook is registered in operator settings**: parse `~/.claude/settings.json` (or the project-scoped `.claude/settings.local.json`) and confirm a `PreToolUse` entry references the deckhand hook. Plugins-managed hooks should auto-register; this check confirms registration succeeded.
3. **Synthetic fire test**: invoke the hook script with a fake stdin payload simulating `Read` on a `.png` file. Assert exit code 1 and the BLOCKED message in stderr. Then invoke with `ALLOW_PNG_READ=1` and assert exit 0. Then with a non-image path and assert exit 0.

Output addition to the verify report:

```
DISCIPLINE HOOK:
  Hook script:         OK ($PLUGIN_ROOT/hooks/block-png-read.sh)
  Registration:        OK (PreToolUse → Read in settings.json)
  Synthetic fire test: OK (PNG blocked, ALLOW_PNG_READ bypassed, non-image passed)

STATUS: FULLY_AVAILABLE  (was previously: PARTIALLY_AVAILABLE)
```

If any check fails, the verify skill emits a clear remediation hint:
- Script missing → reinstall the plugin.
- Registration missing → "Run `/plugin enable jack-tar-deckhand` to re-register hooks."
- Synthetic test fails → "Hook script may be corrupted; re-extract from source."

## Phase 5 — CLAUDE.md note

Top-level `CLAUDE.md` already has a "MANDATORY" section housing Article 9.4 and Agent-definition-reload rules. Add a short third entry:

```markdown
## MANDATORY: Image-review discipline (Constitution Article 9.4 — enforced)

The `jack-tar-deckhand` plugin installs a `PreToolUse` hook that BLOCKS
`Read` on image files (PNG, JPG, GIF, WEBP, BMP, TIFF). PNGs in
orchestration context burn tokens that compound across every subsequent
turn — review must happen out-of-context via subagent dispatch.

For every image generated:
- Dispatch `jack-tar-deckhand:image-reviewer` (Haiku, returns compact JSON)
- Or `general-purpose` (Sonnet/Opus, higher visual accuracy)
- Capture the verdict; never `Read` the PNG yourself.

Bypass: set `ALLOW_PNG_READ=1` only when the image IS the user-facing
answer (the user explicitly said "show me X"). The bypass is a
deliberate signal, not a workaround.

Verify the hook is alive: `/jack-tar-deckhand:verify` reports the
"DISCIPLINE HOOK" section.
```

This makes the rule discoverable without depending on memory.

## Phase 6 — Test

Three tests, added to `plugins/jack-tar-deckhand/tests/`:

1. **`test_block_png_read_hook.py`** — invoke the bash script via subprocess with three test payloads:
   - PNG path → exit 1, stderr contains "BLOCKED"
   - PNG path with `ALLOW_PNG_READ=1` → exit 0
   - `.md` path → exit 0
   - Case-insensitive `.PNG`, `.JPG` → exit 1
2. **`test_verify_discipline_section.py`** — invoke the verify skill, assert the discipline-hook section is present in the output.
3. **(Optional integration test)** Confirm that within a fresh Claude Code session with the plugin installed, the hook actually fires on a real `Read` call. Hard to automate; ship as a manual gate in `tests/manual/` documenting the verification step.

## Phase 7 — Cross-cut: marketplace doc

`.claude-plugin/marketplace.json` already lists deckhand. After this lands, update the deckhand description in the marketplace manifest (and the project README's plugin table) to mention "ships a discipline hook that prevents image-Read from burning context".

## Risk register

| Risk | Mitigation |
|---|---|
| The hook breaks legitimate workflows that need to inspect a PNG (e.g. an SVG-rasterisation debug step) | The `ALLOW_PNG_READ=1` env-var escape is documented prominently. The verify skill mentions it. |
| Operators who don't install deckhand miss the rule | Acceptable — they're not using the deckhand pipeline so the failure mode is less prevalent. They can install deckhand at any point to acquire the rule. |
| The hook fires on hooks-test PNG paths the test suite uses | Tests use the `ALLOW_PNG_READ=1` bypass; document this clearly in test fixtures. |
| Claude Code changes its hook protocol JSON shape, breaking the script | The hook script's JSON parsing is one Python line; pin the parse to `tool_input.file_path` (which is the documented field) and add a fallback for missing keys. |
| Plugin manifest hook auto-registration doesn't propagate to existing installations until `/reload-plugins` is run | First-run experience: when the operator updates the plugin, settings.json gets the hook entry on next plugin reload. The verify skill catches stale-registration cases. |
| Other plugins also declare PreToolUse-Read hooks, leading to fire-order ambiguity | Hooks compose; multiple PreToolUse-Read hooks fire in registration order. As long as none unblocks what the discipline hook blocks, behaviour is correct. Document in the script header. |

## Deliverable summary

| File | Action | Lines (approx) |
|---|---|---|
| `plugins/jack-tar-deckhand/hooks/block-png-read.sh` | new | 40 |
| `plugins/jack-tar-deckhand/.claude-plugin/plugin.json` | edit | +8 (hooks block) |
| `plugins/jack-tar-deckhand/.claude-plugin/plugin.json` | edit | version bump 1.3.0 → 1.3.1 |
| `.claude-plugin/marketplace.json` | edit | version sync |
| `plugins/jack-tar-deckhand/skills/verify/SKILL.md` | edit | +30 (new section) |
| `plugins/jack-tar-deckhand/tests/test_block_png_read_hook.py` | new | 60 |
| `plugins/jack-tar-deckhand/tests/test_verify_discipline_section.py` | new | 30 |
| `CLAUDE.md` | edit | +15 (MANDATORY entry) |
| `tests/manual/MANUAL_GATE.md` | edit | +10 (manual hook-fire verification step) |

**Total:** ~200 lines of net-new code/docs across 9 file changes.

## Coordinated release

This plan and the [bug-batch plan](2026-05-08-blog-post-bug-batch.md) (#72-#75) ship as a **single coordinated release**. Three plugins bump together:

| Plugin | Current | Next | Driving issue(s) |
|---|---|---|---|
| `jack-tar-cloud` | 1.3.1 | **1.3.2** | #72 + #73 + #74 |
| `jack-tar-ollama` | 1.1.0 | **1.1.1** | #75 |
| `jack-tar-deckhand` | 1.3.0 | **1.3.1** | #76 (this plan) |
| `.claude-plugin/marketplace.json` | — | sync all three | — |

**Sequencing within the release:**

1. Bug-batch PRs land (cloud + ollama, code-only — no version bumps).
2. Discipline-hook PR lands (deckhand, code-only — no version bump).
3. **Single "release" PR** bumps all three plugin manifests, syncs marketplace.json, updates root CLAUDE.md "Current Status", tags the release.

The two plans have **no file overlap** — bug-batch lives in `plugins/jack-tar-cloud/` and `plugins/jack-tar-ollama/`; this plan lives in `plugins/jack-tar-deckhand/`. They can develop in parallel branches without conflict.

Suggested ordering of the code-only PRs: discipline hook first because it changes orchestration behaviour and validating it on a fresh session is easier when the bug-batch fixes haven't moved the cost-per-call yet. But order is loose — none block any other.

## Acceptance

- A fresh Claude Code session with `jack-tar-deckhand` plugin installed cannot `Read` a `.png` file. The block message names the alternatives.
- A session with `ALLOW_PNG_READ=1` set bypasses the block.
- `/jack-tar-deckhand:verify` reports `DISCIPLINE HOOK: OK` for all three checks.
- The 2026-05-07 dogfood failure mode is structurally impossible to repeat — no operator (or future me) can complete a Read-on-PNG without deliberately bypassing.
- `CLAUDE.md` makes the rule discoverable from the project root.

## Estimated effort

**~1 hour** including TDD, docs, and version coordination. Single-session work.
