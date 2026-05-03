# BSA Update Draft

## Your Role

You are a BSA architecture implementer in the bsa-team container. Execute the plan from the previous node — apply the canonical-model edits, update the arch docs, and bump the BSA version. Use data-architect for JSON edits and documentation-architect for arch-doc prose.

## Context

You are at `/workspace`, on the same feature branch. The previous node committed `reports/bsa-plan/plan.md` — read it first; it is your authoritative spec.

**Inputs to load:**
1. `reports/bsa-plan/plan.md` — the plan (your spec)
2. `.bsa/models/jack-tar-deckhand.json` — the file you'll edit
3. `.archon/inputs/feature-spec.md` and `feature-plan.md` — for context on what changed
4. Existing files under `docs/architecture/` — to match prose style and information architecture

## What To Do

### Phase 1: Apply canonical-model edits

For each "Edit N" in the plan, perform the exact JSON operation specified. **Never make edits beyond what the plan lists** — if you find something during implementation that the plan didn't cover, raise it as a critical issue in your output report (don't just silently fix it).

Use Python or jq for non-trivial JSON edits. Validate the file parses as JSON after every edit.

```bash
cd /workspace
python3 -c "import json; json.load(open('.bsa/models/jack-tar-deckhand.json'))" \
    && echo "valid JSON after edits" || echo "BROKEN — investigate"
```

### Phase 2: Apply arch-doc updates

For each arch-doc edit in the plan, perform the prose update. Match the existing doc's style. Use technical-writer (via `Agent(subagent_type="sdlc-team-docs:technical-writer")`) for prose if helpful.

If the plan specified a NEW ADR, create it at `docs/architecture/decisions/YYYY-MM-DD-<topic>.md` with this structure:

```markdown
# ADR-NNN: <Title>

**Date:** YYYY-MM-DD
**Status:** Accepted
**Issue:** <ref>

## Context

<the situation that prompted this decision>

## Decision

<what we decided>

## Rationale

<why>

## Consequences

<what this means going forward, including any drift risks>
```

### Phase 3: Bump CLAUDE.md `BSA Architecture` line

Find the line that reads `**BSA Architecture:** v<old>` in CLAUDE.md and bump to the new version per the plan. If the plan specified additional CLAUDE.md updates, apply them.

### Phase 4: Self-verify

Re-read every file you edited. Confirm:
- JSON parses validly
- ADR (if created) follows the template
- CLAUDE.md version line matches `.bsa/models/jack-tar-deckhand.json`'s `bsaVersion` field
- No edits made beyond what the plan listed

## Output

Write the change log to `/workspace/reports/bsa-draft/changes.md`:

```markdown
# BSA Draft Changes

## Files modified

| File | Lines + | Lines − | Summary |
|---|---|---|---|
| .bsa/models/jack-tar-deckhand.json | ... | ... | ... |
| CLAUDE.md | ... | ... | ... |
| docs/architecture/... | ... | ... | ... |

## Per-edit log

For each plan edit:
- Edit N: <plan description>
- Applied: yes / no / partial
- Result: <what's now in the file>
- Concerns: <if any>

## JSON validity

After all edits: `python3 -c "import json; json.load(open('.bsa/models/jack-tar-deckhand.json'))"` exits 0: yes / no

## Self-test answers

For each test question from the plan's "Test for the draft node":
- Q: <copy from plan>
- A: <where in the updated files the answer is>

## Concerns / unresolved

<anything you couldn't fully apply, with reason>
```

## Commit

```bash
cd /workspace
mkdir -p reports/bsa-draft
git add .bsa/models/jack-tar-deckhand.json CLAUDE.md docs/architecture/ reports/bsa-draft/changes.md
git commit -m "bsa(draft): apply canonical model + arch doc updates per plan"
```
