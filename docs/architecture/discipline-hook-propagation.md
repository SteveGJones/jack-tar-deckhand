# Discipline hook propagation — investigation and mitigation

**Issue**: [#86](https://github.com/SteveGJones/jack-tar-deckhand/issues/86)
**Date**: 2026-05-17 (v1.4 Phase 0)
**Status**: harness-level gap confirmed; soft-policy mitigation in force

## The question

Does the `jack-tar-deckhand` plugin's PreToolUse hook (issue #76, PR #79) — which blocks `Read` on image files in the orchestration session — also block `Read` when a Task-dispatched subagent (e.g. `general-purpose`, `image-reviewer`) attempts it?

This matters because v1.4 work delegates implementation to subagents that may handle generated images. If the hook does not propagate, the discipline relies entirely on every delegated prompt restating the rule.

## The test

Synthetic Phase 0 test, 2026-05-17 during Ralph iteration 1:

1. Create a small benign PNG at `/tmp/test-discipline.png` (10×10 red square, 76 bytes) via `Pillow`.
2. Dispatch a `general-purpose` subagent at Haiku.
3. Instruct the subagent to attempt `Read` on `/tmp/test-discipline.png` and report verbatim whether the call succeeded, was blocked, or the tool was unavailable.

The subagent returned:

```json
{
  "attempt_made": true,
  "outcome": "READ_SUCCEEDED",
  "verbatim_message": "The image was successfully read and displayed as a small red square (10x10 PNG)",
  "subagent_model": "haiku",
  "subagent_type": "general-purpose"
}
```

The Read tool call **succeeded** inside the subagent's context. The PreToolUse hook registered by the parent plugin did not fire.

## The finding

PreToolUse hooks declared in a plugin's `plugin.json` (and registered into the operator's `settings.json` via plugin activation) operate at the orchestration-session level. **They do not propagate into Task-dispatched subagent sessions.** The subagent runs in a fresh session with its own tool permissions and no inherited hook chain.

This is a harness-level behaviour — not a plugin bug we can patch. The hook script (`plugins/jack-tar-deckhand/hooks/block-png-read.sh`) does the right thing when it fires; it just never fires for subagents.

## Why the plan's env-var fallback isn't viable

The v1.4 plan suggested a fallback shape: `JACK_TAR_BLOCK_PNG_READ=1` env var + bash-wrapper script that intercepts Read tool calls.

This pattern works for Bash tool calls — the wrapper script is a subprocess that inherits parent env and can refuse to run. It does **not** work for `Read`, which is a built-in tool whose dispatch never crosses a subprocess boundary. No subprocess means no wrapper invocation means no enforcement point. The hook mechanism is the only way for a plugin to intercept Read; we've just shown that mechanism is per-session.

## The mitigation (soft policy)

For v1.4 and until the harness changes, the enforcement contract for delegated image work is **prompt-level discipline**:

1. **Every delegated implementation prompt that may touch generated images MUST inline the rule.** A reminder at the top of the prompt: "Do not Read PNG / JPG / GIF / WEBP / BMP / TIFF files directly. If you need to verify an image, dispatch the `jack-tar-deckhand:image-reviewer` subagent (Haiku, JSON verdict) or the `general-purpose` subagent (Sonnet, higher accuracy). Both subagents pull the image into THEIR context and return text."

2. **The root `CLAUDE.md` MANDATORY rule (issue #76, reaffirmed 2026-05-07) governs the orchestration session.** The PreToolUse hook enforces it at that level.

3. **Subagent dispatches inherit the discipline by prompt content, not by harness mechanism.** This is fragile. Operators reviewing v1.4 PRs should verify that delegated implementation prompts include the inline rule.

4. **`image-reviewer` and `general-purpose` agents themselves are exempt** — the whole point of dispatching them is to give them the image. Their job is to return a text verdict, keeping the orchestration context lean.

## What would close this gap fully

Either:

- **Harness change**: Claude Code starts propagating PreToolUse hooks (or at least Read-targeted ones) into Task subagent sessions. Out of plugin scope.

- **Subagent-level hook declaration**: a future Claude Code feature where a plugin can register hooks that fire inside subagent sessions it dispatches. Not currently available.

Neither is on the v1.4 critical path. The soft-policy mitigation is sufficient for the planned v1.4 delegated work because:

- The bulk of v1.4 changes are mechanical (schema additions, exception classes, agent prompt edits) and do not require image handling in dispatched subagents.
- The two verification gates that handle images directly (Phase 5a, Phase 5b, final dogfood) all dispatch `image-reviewer` explicitly — that's the correct delegation pattern, not the violating one.
- The only risk is that a future Ralph iteration delegates a prompt that incidentally tries to Read a PNG. The mitigation policy catches that at prompt-authoring time.

## Updates to project conventions

- The `MANDATORY: Image-review discipline` section in root `CLAUDE.md` is extended with a "Delegated subagent prompts" subsection that requires the inline rule reminder.
- The `MANDATORY: Agent Definition Reloading` and `MANDATORY: Image-review discipline` rules together cover the two known classes of harness-cache and harness-scope behaviour we have to work around in v1.4.

## Recommended `image-reviewer` agent prompt enhancement (future)

The dispatched `image-reviewer` agent's own definition could include the rule in its instructions: "You MAY Read the image at the path I give you; that is your job. Do not Read any other image files; if asked, refuse."

This tightens the gap further: even if a future caller mis-prompts the image-reviewer, the agent itself enforces the discipline. Not a v1.4 deliverable but tracked for v1.5.

## Closure for issue #86

Closing as "harness-level gap; soft-policy mitigation in force". Cite this doc and the test evidence in the issue comment.
