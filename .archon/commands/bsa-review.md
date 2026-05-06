# BSA Update Review

## Your Role

Review the BSA update for methodology compliance and architectural correctness. Use compliance-auditor (governance gate), solution-architect (architectural soundness), and documentation-architect (info-architecture review).

The validate node already covered schema correctness and diff scope. Your job is the human-judgement layer: is this the RIGHT update? Does it follow the methodology? Are there structural concerns the draft node didn't anticipate?

## Context

You are at `/workspace`. Prior nodes committed:
- `reports/bsa-plan/plan.md` — the plan
- The actual BSA edits (`.bsa/models/jack-tar-deckhand.json`, `CLAUDE.md`, possibly `docs/architecture/...`)
- `reports/bsa-draft/changes.md` — what the draft says it did
- `reports/bsa-validate/findings.md` — schema/structural check

If the validate node returned FAIL, do NOT proceed. Surface the validate failures as critical and stop.

## What To Do

### Phase 1: Methodology compliance

Use compliance-auditor (via `Agent(subagent_type="sdlc-team-security:compliance-auditor")`) — yes, security agent, but it's the project's compliance specialist. Check:

- **Single-source-of-truth doctrine.** The canonical model is the SoT. Any change here must propagate to arch docs and CLAUDE.md. Verify that propagation happened.
- **Version semantics.** A contract addition is minor (X.Y.Z → X.Y.Z+1 patch, OR X.Y.Z → X.Y+1.0 minor depending on the project's policy). A new service or persona is major. Check the version bump matches the change scope.
- **Dependency register doctrine.** New external dependencies must have entries with unique IDs. Internal-only changes don't need register entries.
- **WHAT/HOW separation.** The canonical model captures WHAT (services, personas, contracts). Implementation details (HOW) belong in spec/plan docs, not the canonical model. Flag any HOW-leakage.
- **Cross-Domain SOP register.** If the change introduces a SOP that crosses domains, it needs a `crossDomainSopRegister` entry.

### Phase 2: Architectural soundness

Use solution-architect (via `Agent(subagent_type="sdlc-team-common:solution-architect")`):

- Does the canonical-model edit accurately reflect the code change?
- Are interaction contracts complete? (parameters, return shape, error semantics)
- Are dependency entries directional and accurate?
- Is the version bump justified by the scope?
- Are there architectural surfaces the diff TOUCHED but the canonical model edit MISSED?

### Phase 3: Documentation soundness

Use documentation-architect:

- Does the arch-doc update (if any) match the canonical model edit?
- Is CLAUDE.md's BSA Architecture entry consistent with the new model?
- Are any cross-references stale (e.g., old version numbers in `docs/architecture/architecture-overview.md`)?

### Phase 4: Forward consistency

Look at the spec/plan inputs the launcher pre-fetched. Anything in the spec that talks about architecture surfaces that the canonical model still doesn't cover? Anything in the dogfood report that revealed architectural reality the model doesn't reflect?

For #59 specifically: the dogfood report flagged the legacy-`src/` import collision. That's an HOW concern, not a WHAT concern, so it doesn't belong in the canonical model — but the FACT that it's flagged might warrant an ADR or a note. Use judgement.

## Output

Write the review to `/workspace/reports/bsa-review/findings.md`:

```markdown
# BSA Review Findings

## Summary verdict
PASS | PASS_WITH_REVISIONS | FAIL

## Methodology compliance
| Doctrine | Status | Evidence |
|---|---|---|
| Single source of truth | pass/fail | ... |
| Version semantics | pass/fail | scope was X, bump was Y, justified: yes/no |
| Dependency register | pass/fail | ... |
| WHAT/HOW separation | pass/fail | ... |
| Cross-Domain SOP | pass/fail/n.a. | ... |

## Architectural soundness
- Edits accurately reflect the code change: yes / no — <evidence>
- Interaction contracts complete: yes / no — <missing fields if any>
- Dependency entries directional: yes / no
- Version bump justified: yes / no
- Surfaces touched but missed: <list, or "none">

## Documentation soundness
- Arch docs match canonical model: yes / no
- CLAUDE.md BSA line matches: yes / no
- Stale cross-references: <list>

## Forward-consistency findings
<anything from the spec/dogfood that should but doesn't appear in the canonical model — or note "none">

## Critical issues (must fix before merge)
- ...

## Advisory issues (worth addressing but not blocking)
- ...

## Strengths (keep these)
- ...
```

## Commit

```bash
cd /workspace
mkdir -p reports/bsa-review
git add reports/bsa-review/findings.md
git commit -m "bsa(review): methodology + architectural + documentation review"
```
