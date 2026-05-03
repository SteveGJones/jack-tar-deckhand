#!/bin/bash
# .archon/launchers/docs-readme-dual-route.sh
#
# Pre-fetch GitHub artifacts that the docs-readme-dual-route workflow needs.
# Runs on the host (where `gh` is available); writes into .archon/inputs/.
# Idempotent — safe to re-run before each workflow execution.
#
# Usage:
#   bash .archon/launchers/docs-readme-dual-route.sh
#   /sdlc-workflows:workflows-run docs-readme-dual-route

set -euo pipefail

# Resolve repo root regardless of where this is invoked from.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INPUTS_DIR="$REPO_ROOT/.archon/inputs"

cd "$REPO_ROOT"

if ! command -v gh >/dev/null 2>&1; then
    echo "ERROR: gh CLI not found on PATH. Install: https://cli.github.com" >&2
    exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
    echo "ERROR: gh CLI not authenticated. Run: gh auth login" >&2
    exit 1
fi

mkdir -p "$INPUTS_DIR"

echo "Pre-fetching GitHub artifacts for docs-readme-dual-route…"

# Issue #62 — README dual-route docs (the work item itself)
echo "  fetching issue #62 body…"
gh issue view 62 --json body -q .body > "$INPUTS_DIR/issue-62-body.md"
gh issue view 62 --json number,title,body,labels,author,state \
    > "$INPUTS_DIR/issue-62.json"

# Issue #58 — EPIC: Cloud image resolution control
# README mentions 2K/4K capability via this EPIC; pre-fetch so the agent
# can describe scope accurately.
echo "  fetching EPIC #58 body…"
gh issue view 58 --json body -q .body > "$INPUTS_DIR/issue-58-body.md"
gh issue view 58 --json number,title,body,labels,author,state \
    > "$INPUTS_DIR/issue-58.json"

# Confirm what landed
echo ""
echo "Pre-fetched artifacts:"
ls -la "$INPUTS_DIR" | grep -v '^total' | grep -v 'README.md' | sed 's/^/  /'
echo ""
echo "Inputs ready. Next: /sdlc-workflows:workflows-run docs-readme-dual-route"
