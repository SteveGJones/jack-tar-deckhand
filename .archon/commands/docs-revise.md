# Documentation Revise — README Dual-Route

## Your Role

You are a technical writer revising the draft based on the review findings. Your job is to address every critical issue from `reports/docs-review/findings.md`, address the advisory issues you reasonably can, and re-verify the result.

Use the technical-writer agent for prose fixes. Use the documentation-architect agent if a critical issue requires structural change (re-ordering sections, moving content). Use the ux-ui-architect agent if the decision-tree needs rework.

## Context

You are at `/workspace`, same feature branch. The previous nodes have committed:
- The draft (README.md + plugin CLAUDE.md edits + change log)
- The review findings (`reports/docs-review/findings.md`)

**Before revising, load:**
1. `reports/docs-review/findings.md` — your authoritative work list
2. The current state of the files you'll edit (README.md, both plugin CLAUDE.md files)
3. `reports/docs-draft/changes.md` — context on what the draft node intended

## What To Do

### Phase 1: Triage the findings

Read `findings.md`. Categorise:
- **Critical** — must address all of these. If you cannot, mark them in your output as unresolved with a reason.
- **Advisory** — address if straightforward; defer the rest with a note.
- **Open questions for the speaker** — DO NOT answer these yourself. Flag them for the synthesise node to surface.

If the review verdict was PASS with no critical issues, your job is light: write a one-line confirmation to the output report and commit.

### Phase 1.5: Verify deferred-items resolution

Read `/workspace/.archon/inputs/run-2-deferred-items.md` if it exists. The file's Verification section lists checkbox items the README and plugin docs must satisfy after this run. For each item:

1. Locate the corresponding edit in the README or plugin CLAUDE.md (cite line).
2. Confirm it matches the Direction in the deferred-items file.
3. If any item is missing or wrong, treat it as a CRITICAL issue and fix it in this revise pass — do NOT defer to the speaker, the deferred-items file is the speaker's direction.

Record the verification outcome (item-by-item) in the revise change log.

### Phase 2: Apply edits

For each critical issue:
- Read the cited line in context
- Apply the smallest fix that resolves the issue
- Do not rewrite sections that weren't flagged
- Do not introduce new content beyond what the fix requires

For each advisory issue you choose to address: same approach, smaller diffs.

### Phase 3: Re-verify

After all edits:
- Re-run the markdown sanity check from the draft phase (balanced fences, links resolve)
- Re-read the three reader-test questions from the plan and confirm the answers are still findable
- Diff the scenario text against issue #62 once more

### Phase 4: Decision tree iteration

If the review flagged the decision tree, iterate on it specifically. The tree should:
- Fit on screen in monospace
- Have no more than two levels of branching
- Use language a new reader would understand without prior project knowledge

If after one iteration the tree still feels unclear, leave it as-is and flag in the output that this is a candidate for speaker-level review.

## Output

Write the revision report to `/workspace/reports/docs-revise/changes.md`:

```markdown
# Revision change log

## Critical issues addressed
- [issue ID or finding excerpt] - [what you changed in which file]

## Advisory issues addressed
- ...

## Advisory issues deferred (and why)
- ...

## Unresolved critical issues (if any)
- ...

## Open questions still pending for speaker
- (copy from review findings — do not invent answers)

## Re-verification
- Markdown sanity: pass/fail
- Three reader-test questions still answerable: yes/no
- Scenario text faithful to issue #62: yes/no
```

## Commit

```bash
cd /workspace
mkdir -p reports/docs-revise
git add README.md plugins/jack-tar-deckhand/CLAUDE.md plugins/jack-tar-superpower-bridge/CLAUDE.md reports/docs-revise/changes.md
git commit -m "docs(revise): address review findings on README dual-route (#62)"
```
