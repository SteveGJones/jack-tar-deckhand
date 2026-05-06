# Documentation Synthesis — README Dual-Route

## Your Role

You are a synthesis agent producing the final report for speaker review. Your job is to consolidate the plan, draft, review, and revise outputs into a single decision-ready document the speaker can read in 5 minutes to decide whether to merge.

You are NOT making editorial changes — the writing work is done. You are summarising what shipped, what was reviewed, what was changed, and what the speaker still needs to decide.

## Context

You are at `/workspace`, same feature branch. All previous nodes have committed:
- `reports/docs-plan/plan.md`
- `reports/docs-draft/changes.md`
- `reports/docs-review/findings.md`
- `reports/docs-revise/changes.md`
- The actual edits to README.md and both plugin CLAUDE.md files

**Before synthesising, load all of the above plus:**
1. `git diff main --stat` — to confirm only docs files changed
2. `git log main..HEAD --oneline` — to see the commit sequence

## What To Do

### Phase 1: Diff verification

```bash
cd /workspace
git diff main --stat
```

Confirm:
- Only `README.md`, `plugins/jack-tar-deckhand/CLAUDE.md`, `plugins/jack-tar-superpower-bridge/CLAUDE.md`, and `reports/**` are modified
- No code files, no test files
- No accidental edits to other plugins

If the diff includes anything outside docs, flag it as a critical concern in the synthesis.

### Phase 2: Trace the deltas

For each docs file modified, summarise:
- What changed (sections rewritten, sections added, sections removed)
- Why (which acceptance criterion or review finding drove the change)
- Reference the commit hash that made the change

### Phase 3: Outstanding items

Pull together:
- **Open questions for the speaker** from review and revise reports
- **Unresolved critical issues** (should be empty; if not, this is a NO-GO signal)
- **Advisory issues deferred** with the deferral reasons
- **Decision-tree iteration history** if the tree went through more than one pass

### Phase 4: Speaker decision aid

End the synthesis with a clear three-line decision aid:

```
SPEAKER REVIEW VERDICT NEEDED:
  GO    — merge as-is to main via gh pr merge --merge
  REVISE — request specific changes (cite findings.md or changes.md sections)
  STOP  — fundamental issue, drop the branch
```

## Output

Write `/workspace/reports/docs-synthesis/findings.md`:

```markdown
# Synthesis report: README dual-route (#62)

## Summary
<2-3 sentences: what shipped, what was reviewed, what verdict the review gave>

## Files changed
| File | Lines + | Lines - | Summary |
|---|---|---|---|
| README.md | ... | ... | ... |
| plugins/jack-tar-deckhand/CLAUDE.md | ... | ... | added See-also |
| plugins/jack-tar-superpower-bridge/CLAUDE.md | ... | ... | added See-also |

## Acceptance criteria status
| AC | Status | Notes |
|---|---|---|
| AC1 (5-min readability) | pass/fail/partial | ... |
| AC2 (cross-references) | ... | ... |
| AC3 (docs-only) | ... | ... |
| AC4 (2K/4K mention) | ... | ... |
| AC5 (decision tree) | ... | ... |

## Review verdict and how it was addressed
<from findings.md and changes.md>

## Open questions for the speaker
- ... (copied verbatim from review)

## Decision aid

  SPEAKER REVIEW VERDICT NEEDED:
    GO    — merge as-is to main via gh pr merge --merge
    REVISE — request specific changes (cite findings.md or changes.md sections)
    STOP  — fundamental issue, drop the branch

## Branch / PR info
- Branch: <current branch name>
- Commits: <count>
- Suggested merge commit message: "docs: README dual-route + plugin cross-references (#62)"
```

## Commit

```bash
cd /workspace
mkdir -p reports/docs-synthesis
git add reports/docs-synthesis/findings.md
git commit -m "docs(synthesis): final report for speaker review (#62)"
```

After this commit, the workflow is complete. The speaker reads `reports/docs-synthesis/findings.md` and decides GO / REVISE / STOP.
