# BSA Update Synthesis

## Your Role

Consolidate plan + draft + validate + review into a decision-ready report for the speaker. You are NOT making editorial changes — the BSA work is done. You are summarising what shipped and what the speaker needs to decide.

## Context

You are at `/workspace`. All previous nodes committed:
- `reports/bsa-plan/plan.md`
- BSA edits (`.bsa/models/jack-tar-deckhand.json`, `CLAUDE.md`, `docs/architecture/...`)
- `reports/bsa-draft/changes.md`
- `reports/bsa-validate/findings.md`
- `reports/bsa-review/findings.md`

## What To Do

### Phase 1: Diff verification

```bash
cd /workspace
git diff main --stat
git log main..HEAD --oneline
```

Confirm only expected files changed (canonical model, CLAUDE.md, optionally arch docs, plus the reports/). Flag any out-of-scope edits.

### Phase 2: Trace the architectural deltas

For each architectural surface that moved (interactions, dependencies, contract fields, version), produce a one-line summary of:
- What changed in the canonical model
- Which commit made the change
- What it reflects in the code

### Phase 3: Outstanding items

Pull together:
- **Critical issues** from review (should be empty; if not, NO-GO signal)
- **Advisory issues** deferred from review with reasons
- **Forward-consistency gaps** the review surfaced
- **Open questions** for the speaker, copied verbatim from review

### Phase 4: Speaker decision aid

End with a clear three-line decision aid:

```
SPEAKER REVIEW VERDICT NEEDED:
  GO     — accept BSA update, ship with the feature PR
  REVISE — request specific changes (cite review findings)
  STOP   — fundamental issue, drop the BSA commits and re-plan
```

## Output

Write `/workspace/reports/bsa-synthesis/findings.md`:

```markdown
# BSA Update Synthesis Report: <feature> (<issue ref>)

## Summary
<2-3 sentences: what BSA edits shipped, what the review found, what verdict is recommended>

## Files changed
| File | Lines + | Lines − | Summary |
|---|---|---|---|
| .bsa/models/jack-tar-deckhand.json | ... | ... | bsaVersion bump + contract field + ... |
| CLAUDE.md | ... | ... | BSA version line bump + status entry |
| docs/architecture/... | ... | ... | <if any> |

## Architectural deltas
<from Phase 2>

## Validate node verdict
<from reports/bsa-validate/findings.md — Verdict line + any critical>

## Review node verdict
<from reports/bsa-review/findings.md — verdict + any critical>

## Methodology compliance
<copy compliance table from review>

## Open questions for speaker
<from review, verbatim>

## Decision aid

  SPEAKER REVIEW VERDICT NEEDED:
    GO     — accept BSA update, ship with the feature PR
    REVISE — request specific changes (cite review findings.md sections)
    STOP   — fundamental issue, drop the BSA commits and re-plan

**Recommended verdict:** <GO/REVISE/STOP, with one-line rationale>

## Branch / merge info
- Branch: <current>
- BSA commits ahead of feature-PR head before this run: 0
- BSA commits added by this run: <count>
- Suggested merge: BSA commits ride along with the feature PR (single PR for code + BSA in lockstep)
```

## Commit

```bash
cd /workspace
mkdir -p reports/bsa-synthesis
git add reports/bsa-synthesis/findings.md
git commit -m "bsa(synthesis): final report for speaker review"
```
