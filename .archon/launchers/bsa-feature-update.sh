#!/bin/bash
# .archon/launchers/bsa-feature-update.sh
#
# Pre-fetch authoritative inputs that the bsa-feature-update workflow needs.
# Runs on the host (where `gh` and the worktree's git history are available);
# writes into .archon/inputs/. Idempotent — safe to re-run before each
# workflow execution.
#
# Usage (from the FEATURE BRANCH worktree where you want the BSA update to land):
#   bash .archon/launchers/bsa-feature-update.sh <issue-or-pr-ref> [<base-branch>]
#
# Args:
#   <issue-or-pr-ref>  — issue or PR number (e.g. "59") to fetch as authoritative
#   <base-branch>      — optional, default "main", used for diff baseline
#
# Examples:
#   bash .archon/launchers/bsa-feature-update.sh 59
#   bash .archon/launchers/bsa-feature-update.sh 59 main

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INPUTS_DIR="$REPO_ROOT/.archon/inputs"

ISSUE_REF="${1:-}"
BASE_BRANCH="${2:-main}"

if [ -z "$ISSUE_REF" ]; then
    echo "ERROR: issue-or-pr-ref is required as the first argument" >&2
    echo "Usage: bash .archon/launchers/bsa-feature-update.sh <issue-or-pr-ref> [<base-branch>]" >&2
    exit 1
fi

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

echo "Pre-fetching inputs for bsa-feature-update against #$ISSUE_REF (base: $BASE_BRANCH)…"

# 1. The issue / PR body
echo "  fetching issue/PR #$ISSUE_REF body…"
gh issue view "$ISSUE_REF" --json body -q .body > "$INPUTS_DIR/issue-${ISSUE_REF}-body.md" 2>/dev/null \
    || gh pr view "$ISSUE_REF" --json body -q .body > "$INPUTS_DIR/issue-${ISSUE_REF}-body.md"
gh issue view "$ISSUE_REF" --json number,title,body,labels,author,state \
    > "$INPUTS_DIR/issue-${ISSUE_REF}.json" 2>/dev/null \
    || gh pr view "$ISSUE_REF" --json number,title,body,labels,author,state \
    > "$INPUTS_DIR/issue-${ISSUE_REF}.json"

# 2. The diff stat + full diff against base branch
echo "  capturing diff vs ${BASE_BRANCH}…"
git diff "$BASE_BRANCH...HEAD" --stat > "$INPUTS_DIR/feature-pr-diff.txt"
echo "" >> "$INPUTS_DIR/feature-pr-diff.txt"
echo "=== Full diff ===" >> "$INPUTS_DIR/feature-pr-diff.txt"
git diff "$BASE_BRANCH...HEAD" >> "$INPUTS_DIR/feature-pr-diff.txt"

# 3. Commit log
echo "  capturing commit log…"
git log --reverse --format='%h%n%s%n%n%b%n---' "$BASE_BRANCH...HEAD" \
    > "$INPUTS_DIR/feature-commits.txt"

# 4. Spec + plan + dogfood — locate by filename pattern
echo "  locating spec/plan/dogfood docs in this branch…"
SPEC=$(git diff "$BASE_BRANCH...HEAD" --name-only | grep -E '^docs/superpowers/specs/.*\.md$' | head -1 || true)
PLAN=$(git diff "$BASE_BRANCH...HEAD" --name-only | grep -E '^docs/superpowers/plans/.*\.md$' | head -1 || true)
DOGFOOD=$(git diff "$BASE_BRANCH...HEAD" --name-only | grep -E '^docs/superpowers/dogfooding/.*\.md$' | head -1 || true)

if [ -n "$SPEC" ] && [ -f "$SPEC" ]; then
    cp "$SPEC" "$INPUTS_DIR/feature-spec.md"
    echo "    spec: $SPEC"
else
    echo "    spec: <none found>"
    : > "$INPUTS_DIR/feature-spec.md"
fi

if [ -n "$PLAN" ] && [ -f "$PLAN" ]; then
    cp "$PLAN" "$INPUTS_DIR/feature-plan.md"
    echo "    plan: $PLAN"
else
    echo "    plan: <none found>"
    : > "$INPUTS_DIR/feature-plan.md"
fi

if [ -n "$DOGFOOD" ] && [ -f "$DOGFOOD" ]; then
    cp "$DOGFOOD" "$INPUTS_DIR/feature-dogfood.md"
    echo "    dogfood: $DOGFOOD"
else
    echo "    dogfood: <none found>"
    : > "$INPUTS_DIR/feature-dogfood.md"
fi

# 5. Snapshot of current canonical model — informational; the workflow reads
# the live file, but this is useful for "what was it before this run?" diffs.
if [ -f .bsa/models/jack-tar-deckhand.json ]; then
    cp .bsa/models/jack-tar-deckhand.json "$INPUTS_DIR/canonical-model-snapshot.json"
    echo "    canonical model snapshot captured"
fi

echo ""
echo "Pre-fetched artifacts for bsa-feature-update:"
ls -la "$INPUTS_DIR" | grep -v '^total' | grep -v 'README.md' | sed 's/^/  /'
echo ""
echo "Inputs ready. Next: /sdlc-workflows:workflows-run bsa-feature-update"
