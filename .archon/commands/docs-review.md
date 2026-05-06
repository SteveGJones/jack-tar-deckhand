# Documentation Review — README Dual-Route

## Your Role

You are a documentation reviewer in the docs-team container. Your job is to assess the draft from the previous node against the acceptance criteria in issue #62 and surface concrete, line-referenced issues for the revise node to fix.

Use the documentation-architect agent for information-architecture review and the ux-ui-architect agent for the decision-tree clarity check and reader-path accessibility.

## Context

You are at `/workspace`, on the same feature branch. The draft node has already committed `README.md`, both plugin `CLAUDE.md` files, and a change log at `reports/docs-draft/changes.md`. Your review surfaces issues — do not edit files yourself.

**Before reviewing, load:**
1. `reports/docs-plan/plan.md` — the spec the draft was working against
2. `reports/docs-draft/changes.md` — what the draft node says it did
3. `README.md` — the artifact to review
4. `plugins/jack-tar-deckhand/CLAUDE.md` and `plugins/jack-tar-superpower-bridge/CLAUDE.md` — review the cross-references

**Read the pre-fetched issue body — authoritative source:**

The container has no `gh` CLI. Issue #62's body has been pre-fetched by the launcher and is at:

```
/workspace/.archon/inputs/issue-62-body.md
```

Treat that file as the canonical, immutable source of truth for the work item. Compare the README against it, not against any internal recollection of what the issue says.

## What To Do

### Phase 1: Acceptance-criteria check

For each acceptance criterion in issue #62, mark pass / fail / partial with line-referenced evidence:

- **AC1: A new reader can identify the right route within 5 minutes.** Test this by re-reading just the README intro + "Choosing your route" + decision tree. Could you, knowing nothing else about the project, pick the right entry point?
- **AC2: Both plugin CLAUDE.md files cross-reference the other route.** Check both files have a See-also section and that links resolve.
- **AC3: No code changes; no test changes.** Run `git diff main --stat` and confirm only docs files changed.
- **AC4: README mentions 2K/4K capability availability.** Find the sentence; verify it's accurate against `/workspace/.archon/inputs/issue-58-body.md` (capability is part of EPIC #58, status depends on which child issues have shipped — language must reflect actual state, not aspirational claims).
- **AC5: Decision tree is included and visually clear.** Check it renders in monospace, fits on screen without horizontal scroll, and the three scenarios from the issue are distinguishable.
- **AC6 (CRITICAL): Three-scenario text matches `/workspace/.archon/inputs/issue-62-body.md` VERBATIM.** See Phase 5 below for the diff protocol. This is the primary purpose of this review.

### Phase 2: Information-architecture review

Use the documentation-architect agent. Check:
- Is the "Choosing your route" section placed where a new reader would find it before getting lost?
- Are the three scenarios in the right order (default first)?
- Does the README maintain a consistent register (instructional vs descriptive)?
- Are the quick-start blocks immediately actionable?

### Phase 3: UX / accessibility review

Use the ux-ui-architect agent. Check:
- Decision tree readability: can someone scanning quickly identify their path?
- Are choice points binary or do they require context the reader doesn't yet have?
- Does the visual emphasis on Bridge-as-default come through?
- Plain-language test: are the three scenarios distinguishable to someone who has never used `/pptx`?

### Phase 4: Plain-language and accuracy review

Use the technical-writer agent. Check:
- Any marketing copy or unsupported claims to remove
- Any jargon that needs definition or removal
- Any factual claims about the bridge or deckhand that need verification against the actual plugin docs
- Tense consistency, voice consistency

### Phase 5: Verbatim check on the three scenarios — CRITICAL

The three scenario blocks in the README's "Choosing your route" section must match the wording in `/workspace/.archon/inputs/issue-62-body.md` **verbatim, paragraph by paragraph**. Open the issue body file. Locate the `## Three entry-point scenarios (from project owner)` section. For each of the three `### N.` subsections:

1. Identify the corresponding scenario block in the README.
2. Compare the prose word-for-word (use `diff <(extract from README) <(extract from issue file)` if helpful).
3. **Any of the following is a CRITICAL failure:**
   - Words added that aren't in the source
   - Words removed from the source
   - Synonyms substituted ("starts" for "invokes", "rebuilds" for "starts over", etc.)
   - Hand-off paths invented that aren't in the source (e.g., "hand off to deck-conductor" when the source says "rebuild the brief and start over")
   - Slash command names dropped (e.g., bare `deck-conductor` when the source says `/jack-tar-deckhand:deck-conductor`)
   - Em-dashes converted to hyphens, or other punctuation drift
   - Bold/italic markers added or removed

4. Report each drift as a critical issue with the exact source text vs the README text side-by-side.

**This check is the primary purpose of this review node.** The first run of this workflow shipped paraphrased scenarios because the agent worked from an in-prompt summary instead of the source file. That regression must not happen here. If you cannot read `/workspace/.archon/inputs/issue-62-body.md` (file missing, empty, or unreadable), STOP and report that as a critical infrastructure failure — do not proceed with a phantom check.

## Output

Write the review to `/workspace/reports/docs-review/findings.md` with this structure:

```markdown
# Documentation review: README dual-route (#62)

## Summary verdict
PASS | PASS_WITH_REVISIONS | FAIL

## Acceptance criteria
| # | Criterion | Verdict | Evidence (file:line) |
|---|---|---|---|
| AC1 | ... | pass/fail/partial | ... |
...

## Critical issues (must fix before merge)
- [README.md:LINE] ...
- [plugins/jack-tar-deckhand/CLAUDE.md:LINE] ...

## Advisory issues (worth addressing but not blocking)
- ...

## Strengths (keep these)
- ...

## Open questions for the speaker
- ...
```

If the verdict is PASS, the revise node will short-circuit. If PASS_WITH_REVISIONS or FAIL, the revise node will work through the critical issues.

## Commit

```bash
cd /workspace
mkdir -p reports/docs-review
git add reports/docs-review/findings.md
git commit -m "docs(review): findings on README dual-route draft (#62)"
```
