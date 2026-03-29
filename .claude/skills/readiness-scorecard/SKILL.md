---
name: readiness-scorecard
description: Generates a green/amber/red deployment readiness assessment for an AI Persona using the 8-checkpoint scorecard. Use this before any AI Persona deployment to validate governance, testing, and accountability gates.
---

# Readiness Scorecard

This skill produces a deployment readiness assessment for an AI Persona using the methodology's 8-checkpoint scorecard. Each checkpoint is rated green (proceed), amber (proceed with conditions), or red (halt and remediate).

## When to Use

- At the end of Chapter 8 (architecture completion) before entering execution
- Before any Chapter 9 release gate
- When assessing whether an AI Persona is ready for production
- During Change Advisory Circle reviews

## Template Reference

The scorecard template is at: `methodology_draft/templates/readiness-scorecard.md`

Related templates:
- Delegation package checklist: `methodology_draft/templates/delegation-package-checklist.md`
- Vanilla-Agent test log: `methodology_draft/templates/vanilla-agent-log.md`

## Instructions

### 1. Gather Evidence

For each checkpoint, collect the required evidence before scoring:

| # | Checkpoint | Required Evidence |
|---|-----------|-------------------|
| 1 | Delegation package complete | Completed persona template (19 sections) + SOP summary |
| 2 | Cross-domain register updated | Entry in cross-domain SOP register with dependency IDs |
| 3 | MCP deployment approved | MCP endpoint documented + access manifest + rollback plan |
| 4 | Vanilla-Agent dry run passed | Completed vanilla-agent-log.md with pass verdict |
| 5 | Change Advisory Circle sign-off | Meeting minutes with attendees and decisions (if cross-domain) |
| 6 | Measurement hooks wired | KPI dashboard URL + telemetry schema confirmed |
| 7 | Training/comms delivered | Attendance log for affected team members |
| 8 | Release ticket opened | Backlog item ID in delivery tool |

### 2. Score Each Checkpoint

Apply the scoring criteria:

**Green** — Evidence is complete, reviewed, and approved. No outstanding issues.

**Amber** — Evidence exists but has minor gaps or conditions:
- Template is 90%+ complete with remaining items tracked
- Vanilla-Agent dry run passed with conditions (non-blocking issues noted)
- Training scheduled but not yet delivered (delivery date confirmed)
- Measurement hooks partially wired (remaining hooks have delivery dates)

**Red** — Evidence is missing, incomplete, or failed:
- No delegation package or major sections missing
- Vanilla-Agent dry run failed
- No Change Advisory Circle review for cross-domain persona
- No measurement blueprint
- Tripartite accountability not confirmed

### 3. Complete the Scorecard

Fill in the scorecard table:

```markdown
| Checkpoint | Persona Status | SOP Status | Evidence / Link | Owner | Notes |
|---|---|---|---|---|---|
| Delegation package complete | [colour] | [colour] | [link] | Service owner | |
| Cross-domain register updated | [colour] | [colour] | [link] | AI RM steward | |
| MCP deployment approved | [colour] | [colour] | [link] | SOP owner | |
| Vanilla-Agent dry run | [colour] | [colour] | [link] | AI RM lab lead | |
| Change Advisory Circle sign-off | [colour] | [colour] | [link] | Facilitator | |
| Measurement hooks wired | [colour] | [colour] | [link] | Analytics lead | |
| Training / comms delivered | [colour] | [colour] | [link] | Change lead | |
| Release ticket opened | [colour] | [colour] | [link] | Delivery manager | |
```

### 4. Apply Gate Rules

| Condition | Decision |
|-----------|----------|
| All 8 green | **Proceed** — deploy to production |
| Any amber, no red | **Proceed with conditions** — document conditions and remediation dates |
| Any red | **Halt** — remediate red items before re-assessment |

### 5. Document the Decision

Record:
- Assessment date
- Assessor name and role
- Gate decision (proceed / proceed with conditions / halt)
- For amber items: specific conditions and remediation deadlines
- For red items: specific remediation actions and re-assessment date
- Store alongside Change Advisory Circle minutes

## Output

A completed readiness scorecard with:
- 8 checkpoints scored green/amber/red
- Evidence links for each checkpoint
- Gate decision with rationale
- Remediation actions for any non-green items
