#!/usr/bin/env bash
# block-png-read.sh — PreToolUse hook for the Read tool.
#
# Issue #76 — discipline hook for the jack-tar-deckhand plugin.
#
# Why this exists:
#   Reading an image file (PNG/JPG/GIF/WEBP/BMP/TIFF) directly into the
#   orchestration context burns thousands of tokens that compound across
#   every subsequent turn. During the 2026-05-07 blog-post asset run
#   the operator pulled 9 PNGs into context before the user spotted it
#   — one slip wasted more context than the rest of the run combined.
#
#   Memory alone doesn't bind: the rule was already in feedback memory
#   at the start of that run and was broken anyway. The harness has to
#   enforce.
#
# What this hook does:
#   Intercepts every Read tool call, parses the file path from the
#   hook-protocol JSON on stdin, and exits non-zero (blocking the call)
#   if the path ends in an image extension. The block message names
#   the alternatives — image-reviewer / general-purpose subagent —
#   so the orchestrator has a clear remediation.
#
# Bypass:
#   Set ALLOW_PNG_READ=1 in the environment when the image IS the
#   user-facing answer (rare — e.g. user explicitly said "show me X").
#   The bypass is a deliberate signal, not a workaround.
#
# Composability:
#   Multiple PreToolUse-Read hooks compose in registration order. This
#   hook only blocks; it does not unblock anything other hooks might
#   block. As long as no hook unblocks what this one blocks, the
#   stronger constraint wins.
#
# Platform: macOS / Linux (uses python3 stdlib).

set -euo pipefail

# Bypass for explicit operator override.
if [[ "${ALLOW_PNG_READ:-}" == "1" ]]; then
  exit 0
fi

# Read tool input JSON from stdin and extract file_path.
INPUT="$(cat)"
FILE_PATH="$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get("tool_input", {}).get("file_path", ""))
except Exception:
    # If the payload is malformed, do not block — let the tool call
    # through and let downstream layers report the malformation.
    print("")
')"

# Block on image extensions (case-insensitive).
shopt -s nocasematch
if [[ "$FILE_PATH" =~ \.(png|jpe?g|gif|webp|bmp|tiff?)$ ]]; then
  cat >&2 <<EOF
BLOCKED by jack-tar-deckhand discipline hook (issue #76):

Read on image file would burn orchestration context. Image files
carry thousands of tokens each and compound across every subsequent
turn.

  Path: $FILE_PATH

Use one of these instead:
  • Dispatch the jack-tar-deckhand:image-reviewer agent (Haiku, cheap)
    with the path + intent, capture a JSON verdict.
  • Dispatch the general-purpose agent (Sonnet/Opus) for higher visual
    accuracy on complex scenes.

Both subagents read the image into THEIR context and return text —
your orchestration stays lean.

Bypass: set ALLOW_PNG_READ=1 in env when the image IS the user-facing
answer (rare — e.g. user said "show me X"). The bypass is a
deliberate signal, not a workaround.
EOF
  exit 1
fi

shopt -u nocasematch
exit 0
